"""Effect-time executor (REQ-041, D-034). Nothing real is executed in v0: the effect is simulated.

The gate decides; the effect happens later. Between the two, a confirmation can be revoked, can
go stale, the action can change, more approvals can arrive, or a pinned artifact can change. So
right before any consequential effect (tier >= 2) the executor re-reads, from fresh sources:
  1. the approvals ledger on disk (readable, chain intact)          -> else HOLD
  2. this confirmation is in the ledger with the same action hash  -> else HOLD
  3. it has not been revoked                                        -> else HOLD
  4. its age at the moment of effect is within confirmation_ttl_s  -> else HOLD
  5. the action's hash still equals the confirmed hash             -> else HOLD
  6. approvals in the window before this one are under the ceiling -> else HOLD
  7. artifact identity (rules, gate config, prompt, crisis, retrieval manifest, model) is unchanged
     since the decision                                             -> else HOLD
Any exception is HOLD. Only when every check passes is the (simulated) side effect marked executed.
"""
import json

from . import config
from .approvals import ApprovalsUnavailable
from .gate_adapter import HOLD, PERMIT, action_hash, _stricter

ARTIFACT_FILES = ("RULES_YAML", "GATE_YAML", "CRISIS_YAML", "RETRIEVAL_MANIFEST")


def artifact_identity(prompt_path=None, model=None, retrieval_manifest=None):
    ident = {name: config.sha256_file(getattr(config, name)) for name in ARTIFACT_FILES}
    if retrieval_manifest is not None:   # D-043: an opt-in manifest (v1) is the one checked at effect time
        ident["RETRIEVAL_MANIFEST"] = config.sha256_file(retrieval_manifest)
    ident["prompt"] = config.sha256_file(prompt_path) if prompt_path else None
    ident["model"] = json.dumps(model.identity(), sort_keys=True, default=str) if model is not None else None
    return ident


class EffectTimeExecutor:
    def __init__(self, ledger, ttl_s, ceiling, clock, identity_fn):
        self.ledger, self.ttl_s, self.ceiling = ledger, float(ttl_s), int(ceiling)
        self.clock, self.identity_fn = clock, identity_fn

    def _checks(self, action, conf, decided_identity):
        if conf is None:
            return "no confirmation to re-check at the moment of effect"
        try:
            rec = self.ledger.approval(conf["id"])
            if rec is None:
                return "confirmation not found in the approvals ledger"
            if rec.get("action_hash") != conf["action_hash"]:
                return "ledger action hash differs from the confirmation"
            if self.ledger.is_revoked(conf["id"]):
                return "confirmation revoked after the gate decision, before effect"
            now = float(self.clock())
            age = now - float(rec["confirmed_at"])   # from the ledger, not from the request
            if age > self.ttl_s or age < 0:
                return f"confirmation is {age:.0f} s old at the moment of effect (> {self.ttl_s:.0f} s or negative)"
            if action_hash(action) != conf["action_hash"]:
                return "action changed between decision and effect"
            n = self.ledger.count(now, exclude_id=conf["id"])
            if n >= self.ceiling:
                return f"approval frequency {n}/window >= ceiling {self.ceiling} at the moment of effect"
        except ApprovalsUnavailable as e:
            return f"approvals ledger unavailable at the moment of effect ({e})"
        except Exception as e:
            return f"effect-time check failed ({type(e).__name__})"
        try:
            if self.identity_fn() != decided_identity:
                return "artifact identity changed between decision and effect"
        except Exception as e:
            return f"artifact identity could not be re-read ({type(e).__name__})"
        return None

    def execute(self, d, action, conf, decided_identity):
        """d: GateDecision. Mutates and returns it. side_effect_executed only if every check passes."""
        d.side_effect_executed = False
        if d.decision != PERMIT or action.tier < 2:
            return d
        d.executor_revalidated = True
        why = self._checks(action, conf, decided_identity)
        if why:
            d.decision = _stricter(d.decision, HOLD)
            d.reasons.append(f"HOLD: effect-time executor (REQ-041): {why}")
            return d
        d.reasons.append("effect-time executor (REQ-041): all checks passed; simulated effect")
        d.side_effect_executed = True
        return d
