"""Gate adapter (D-008): Governor 4.5 decision words around runtime/gate.rb, read-only.

Two layers, stricter wins:
1. Harness-side 4.5 predicate checks (PLATINUM §5) on the request: confirmation
   freshness / exact binding / scope / revocation / Stop, registry and policy
   integrity, registered path, approval frequency, input-guard HOLD. Only when all
   of these pass is `--approved` handed to gate.rb.
2. runtime/gate.rb via runtime/gate_cli.rb in a subprocess (never --auto-sabbath,
   which writes). Its answer is mapped to the 4.5 words:
     PROCEED -> PERMIT, TRIGGER_REALITY_VETO -> HOLD, TRIGGER_RESONANCE_MODE -> DENY
   (no SAFE_TRANSITION is declared for any action class in v0, so blacklist = DENY).
   Error, timeout or unknown output -> HOLD.
If gate_cli.rb can't be run at all, a clearly labeled STUB answers HOLD for everything.

Outcome words (D-005): PERMIT · DENY · HOLD · ESCALATE · SAFE_TRANSITION.
This module never holds 1/0: PERMIT requires a human ConfirmationEvent that passes
the checks below and a PROCEED from gate.rb. decide() still re-checks the revocation fields on the
same request (X05, DENY). The pipeline then runs the effect-time executor (harness/executor.py, REQ-041,
D-034), which re-reads the approvals ledger, revocation, confirmation age, action hash, ceiling and
artifact identity at the moment of effect and HOLDs on any change or doubt.
`side_effect_executed` is a simulated flag: True only for a PERMIT on a consequential action
(tier >= 2). A PERMIT on a read or text-only action (tier 0-1) has no side effect to execute.
Nothing real is ever executed in v0.
Approval ceiling / OR-08: wired in the pipeline (REQ-042, D-033). The pipeline counts human approvals
in the run's ledger (harness/approvals.py) and passes the count here and to the input guard. If the
count can't be read or the ledger is corrupt, `approvals_count_ok` is False and any consequential
action is HOLD. GP fixtures still set `approvals_last_60min` directly.
"""
import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from typing import Optional, Set

from . import config
from .actions import Action

PERMIT, DENY, HOLD, ESCALATE, SAFE_TRANSITION = "PERMIT", "DENY", "HOLD", "ESCALATE", "SAFE_TRANSITION"
WORDS = (PERMIT, DENY, HOLD, ESCALATE, SAFE_TRANSITION)
# Stricter wins. SAFE_TRANSITION is never produced in v0.
_RANK = {PERMIT: 0, SAFE_TRANSITION: 1, HOLD: 2, ESCALATE: 3, DENY: 4}

# Numbers come from configs/gate-v0.yaml (D-014: Paddy-approved v0, pt723u; may increase
# later as the project scales and passes validation). Not hard-coded here.
_GATE_CFG = config.load_gate_config()
CONFIRMATION_TTL_S = float(_GATE_CFG["confirmation_ttl_s"])
APPROVAL_CEILING_60MIN = int(_GATE_CFG["approval_ceiling_60min"])
GATE_TIMEOUT_S = float(_GATE_CFG["gate_timeout_s"])
RUBY = "/usr/bin/ruby"
GATE_CLI = config.AFTERSTRING_ROOT / "runtime" / "gate_cli.rb"
DEFAULT_REGISTRY = frozenset({"ui.display", "bank.payments.v1", "agent.pay", "agent.send",
                              "agent.post", "agent.delete", "agent.schedule", "agent.approve"})
_MAP = {"PROCEED": PERMIT, "TRIGGER_REALITY_VETO": HOLD, "TRIGGER_RESONANCE_MODE": DENY}


def action_hash(action: Action):
    blob = json.dumps({"kind": action.kind, "verb": action.verb, "params": action.params,
                       "endpoint": action.endpoint}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


@dataclass
class Confirmation:
    """A human ConfirmationEvent as the harness received it."""
    action_hash: str
    age_s: float
    scope: str = "exact"                  # "exact" | "blanket"
    shown_params: Optional[dict] = None   # what the human saw
    revoked: bool = False
    revoked_after_decision_ms: Optional[float] = None   # revocation arriving before effect


@dataclass
class GateRequest:
    action: Action
    confirmation: Optional[Confirmation] = None
    stop_pressed: bool = False
    registry_status: str = "ok"           # "ok" | "failed" | "unreviewed_agent_change"
    registry: Set[str] = field(default_factory=lambda: set(DEFAULT_REGISTRY))
    policy_integrity_ok: bool = True
    policy_conflict: bool = False
    approvals_last_60min: int = 0
    approvals_count_ok: bool = True           # False = count unavailable/corrupt (REQ-042): HOLD
    governor_reachable: bool = True
    executor_fallback: Optional[str] = None   # e.g. "proceed_if_unreachable" (never honored)
    optics_verdict: Optional[str] = None
    signal_trust_low: bool = False
    target_ambiguous: bool = False


@dataclass
class GateDecision:
    decision: str
    reasons: list
    bypass_event: bool = False
    approved_passed_to_gate_rb: bool = False
    gate_rb_raw: Optional[str] = None
    gate_rb_ms: Optional[float] = None
    gate_rb_called: bool = False
    backend: str = "gate.rb"
    executor_revalidated: bool = False
    side_effect_executed: bool = False   # simulated; PERMIT on tier >= 2 only
    action_tier: Optional[int] = None

    def to_dict(self):
        return asdict(self)


class GateRb:
    """Calls runtime/gate_cli.rb read-only. Falls back to a labeled STUB (HOLD)."""

    def __init__(self, ruby=RUBY, cli=GATE_CLI, root=None, timeout=GATE_TIMEOUT_S):
        self.ruby, self.cli = str(ruby), str(cli)
        self.root = str(root or config.AFTERSTRING_ROOT)
        self.timeout = timeout
        self.available = os.path.exists(self.ruby) and os.path.exists(self.cli)
        self.backend = "gate.rb" if self.available else "STUB(default HOLD; gate_cli.rb not callable)"

    def ask(self, kind, tier, approved, ambiguous=False, signal_trust_low=False):
        if not self.available:
            return HOLD, "STUB", 0.0
        cmd = [self.ruby, self.cli, "--root", self.root, "--action", str(kind), "--tier", str(int(tier))]
        if approved:
            cmd.append("--approved")
        if ambiguous:
            cmd.append("--ambiguous")
        if signal_trust_low:
            cmd.append("--signal-trust-low")
        assert "--auto-sabbath" not in cmd
        t0 = time.perf_counter()
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout,
                               cwd=self.root)
            raw = (p.stdout or "").strip().splitlines()
            raw = raw[-1].strip() if raw else ""
        except Exception as e:
            return HOLD, f"ERROR:{type(e).__name__}", (time.perf_counter() - t0) * 1000
        ms = (time.perf_counter() - t0) * 1000
        # D-022: gate_cli.rb's contract is exit 0 = PROCEED, exit 2 = held / veto / resonance.
        # The printed word and the exit code must agree; any other combination (a crash, or
        # PROCEED with a non-zero exit) is not an answer, so it is HOLD.
        want = 0 if raw == "PROCEED" else 2
        if raw in _MAP and p.returncode != want:
            return HOLD, f"EXIT_MISMATCH(exit {p.returncode}):{raw}", ms
        return _MAP.get(raw, HOLD), raw or f"EMPTY(exit {p.returncode})", ms


def _stricter(a, b):
    return a if _RANK[a] >= _RANK[b] else b


def decide(req: GateRequest, gate: Optional[GateRb] = None) -> GateDecision:
    gate = gate or GateRb()
    a = req.action
    reasons, word, bypass = [], PERMIT, False

    def add(w, why):
        nonlocal word
        reasons.append(f"{w}: {why}")
        word = _stricter(word, w)

    if not req.governor_reachable:
        add(DENY, "governor unreachable: no decision means no permit"
                  + (f"; executor fallback {req.executor_fallback!r} is not honored" if req.executor_fallback else ""))
        return GateDecision(word, reasons, backend=gate.backend)
    if req.stop_pressed:
        add(DENY, "human pressed Stop before execution (release wins)")
    if req.registry_status == "failed":
        add(DENY, "registry failed to load: no path can be shown to be registered (fail closed, reads included)")
    elif req.registry_status == "unreviewed_agent_change":
        add(ESCALATE, "registry changed by an agent-authored edit merged without review (REQ-034)")
    if not req.policy_integrity_ok:
        add(DENY, "policy integrity check failed")
    if req.policy_conflict:
        add(ESCALATE, "two active policies conflict")
    if req.registry_status != "failed" and a.endpoint not in req.registry:
        bypass = True
        add(DENY, f"unregistered path {a.endpoint!r} (bypass event raised)")

    confirmation_ok = False
    if a.consequential:
        c = req.confirmation
        if c is None:
            add(HOLD, "no confirmation yet: waiting for a present yes to the exact action")
        else:
            bad = False
            if c.scope != "exact":
                add(DENY, f"confirmation scope {c.scope!r} is not single-use and exact"); bad = True
            if c.age_s > CONFIRMATION_TTL_S:
                add(DENY, f"confirmation is {c.age_s:.0f} s old (> {CONFIRMATION_TTL_S} s): not fresh"); bad = True
            if c.action_hash != action_hash(a):
                add(DENY, "action changed after confirmation (material parameter change voids it)"); bad = True
            if c.shown_params is not None and c.shown_params != a.params:
                add(DENY, f"what the human saw {c.shown_params} differs from the payload {a.params}"); bad = True
            if c.revoked:
                add(DENY, "confirmation revoked"); bad = True
            confirmation_ok = not bad
        if not req.approvals_count_ok:
            add(HOLD, "approvals count unavailable or corrupt (REQ-042): fail closed")
        if req.approvals_last_60min >= APPROVAL_CEILING_60MIN:
            add(HOLD, f"approval frequency {req.approvals_last_60min}/60 min >= ceiling {APPROVAL_CEILING_60MIN}")
    if req.optics_verdict == "HOLD":
        add(HOLD, "input guard returned HOLD (held even after approval, REQ-034)")

    approved = confirmation_ok and word == PERMIT
    g_word, raw, ms = gate.ask(a.kind, a.tier, approved, req.target_ambiguous, req.signal_trust_low)
    reasons.append(f"gate.rb[{gate.backend}] {raw} -> {g_word}")
    word = _stricter(word, g_word)

    d = GateDecision(word, reasons, bypass_event=bypass, approved_passed_to_gate_rb=approved,
                     gate_rb_raw=raw, gate_rb_ms=ms, gate_rb_called=True, backend=gate.backend)
    # Executor-side revalidation just before the effect (REQ-034, X05).
    if d.decision == PERMIT and a.consequential:
        d.executor_revalidated = True
        c = req.confirmation
        if c is not None and (c.revoked_after_decision_ms is not None or c.revoked):
            d.decision = DENY
            d.reasons.append("DENY: executor revalidation: confirmation revoked after the gate decision, before effect")
    d.action_tier = a.tier
    # Simulated executor; nothing real is executed. Only a consequential action (tier >= 2) has an effect.
    d.side_effect_executed = (d.decision == PERMIT and a.tier >= 2)
    return d
