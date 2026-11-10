"""REQ-041 (D-034): the effect-time executor re-reads from fresh sources right before any effect."""
import tempfile
import unittest
from pathlib import Path

from harness.approvals import ApprovalsLedger
from harness.executor import EffectTimeExecutor, artifact_identity
from harness.gate_adapter import decide, GateRequest, Confirmation, action_hash, PERMIT, HOLD, \
    CONFIRMATION_TTL_S, APPROVAL_CEILING_60MIN
from harness.pipeline import Pipeline, Turn
from evals import fixtures_v0 as fx
from tests.test_approvals_req042 import Clock, FakeGate, PAY, _ledger, _yes


class EffectTimeTests(unittest.TestCase):
    def test_revoked_between_decision_and_effect_is_hold_no_effect(self):
        """The revocation is written to the ledger by a separate actor after decide(), not in the request."""
        clk = Clock(); L = _ledger(clk)
        seen = {}
        def revoke_after_decision(turn, d, ledger):
            seen["decided"] = d.decision
            ApprovalsLedger(ledger.path, clock=clk, create=False).revoke(turn.confirmation["id"])
        p = Pipeline("no-model", gate=FakeGate("PERMIT"), retrieval=False, ledger=L, clock=clk,
                     on_decided=revoke_after_decision)
        r = p.run([_yes(clk, 1)])[0]
        self.assertEqual(seen["decided"], PERMIT)          # the gate had said yes
        self.assertEqual(r.gate["decision"], HOLD)         # the effect-time re-read said no
        self.assertFalse(r.gate["side_effect_executed"])
        self.assertTrue(any("revoked after the gate decision" in x for x in r.gate["reasons"]))

    def test_unrevoked_passes(self):
        clk = Clock(); p = Pipeline("no-model", gate=FakeGate("PERMIT"), retrieval=False, ledger=_ledger(clk), clock=clk)
        r = p.run([_yes(clk, 1)])[0]
        self.assertEqual(r.gate["decision"], PERMIT)
        self.assertTrue(r.gate["executor_revalidated"] and r.gate["side_effect_executed"])

    def _hook_pipe(self, clk, L, hook):
        return Pipeline("no-model", gate=FakeGate("PERMIT"), retrieval=False, ledger=L, clock=clk, on_decided=hook)

    def test_goes_stale_before_effect(self):
        clk = Clock(); L = _ledger(clk)
        def wait(turn, d, ledger): clk.t += CONFIRMATION_TTL_S + 5
        r = self._hook_pipe(clk, L, wait).run([_yes(clk, 1)])[0]
        self.assertEqual(r.gate["decision"], HOLD)
        self.assertTrue(any("old at the moment of effect" in x for x in r.gate["reasons"]))

    def test_ceiling_reached_before_effect(self):
        clk = Clock(); L = _ledger(clk)
        def flood(turn, d, ledger):
            for i in range(APPROVAL_CEILING_60MIN):
                ledger.record_approval(f"other{i}", "h")
        r = self._hook_pipe(clk, L, flood).run([_yes(clk, 1)])[0]
        self.assertEqual(r.gate["decision"], HOLD)
        self.assertTrue(any("at the moment of effect" in x and "ceiling" in x for x in r.gate["reasons"]))

    def test_ledger_corrupted_before_effect(self):
        clk = Clock(); L = _ledger(clk)
        def corrupt(turn, d, ledger): ledger.path.write_text("x\n")
        r = self._hook_pipe(clk, L, corrupt).run([_yes(clk, 1)])[0]
        self.assertEqual(r.gate["decision"], HOLD)
        self.assertFalse(r.gate["side_effect_executed"])

    def test_artifact_identity_changed_before_effect(self):
        clk = Clock(); L = _ledger(clk)
        p = self._hook_pipe(clk, L, None)
        calls = {"n": 0}
        def ident():
            calls["n"] += 1
            return {"v": calls["n"]}          # differs on the second (effect-time) read
        p.executor.identity_fn = ident
        r = p.run([_yes(clk, 1)])[0]
        self.assertEqual(r.gate["decision"], HOLD)
        self.assertTrue(any("artifact identity changed" in x for x in r.gate["reasons"]))

    def test_action_changed_before_effect(self):
        clk = Clock(); L = _ledger(clk)
        a = fx._dana(); b = fx._dana(to="Unknown-account-991")
        L.record_approval("c1", action_hash(a), confirmed_at=clk.t)
        ex = EffectTimeExecutor(L, CONFIRMATION_TTL_S, APPROVAL_CEILING_60MIN, clk, lambda: {"x": 1})
        d = decide(GateRequest(a, Confirmation(action_hash(a), 1)), FakeGate("PERMIT"))
        self.assertEqual(d.decision, PERMIT)
        ex.execute(d, b, {"id": "c1", "action_hash": action_hash(a)}, {"x": 1})
        self.assertEqual(d.decision, HOLD)
        self.assertFalse(d.side_effect_executed)

    def test_identity_includes_pinned_artifacts(self):
        ident = artifact_identity(None, None)
        for k in ("RULES_YAML", "GATE_YAML", "CRISIS_YAML", "RETRIEVAL_MANIFEST"):
            self.assertTrue(ident[k])

    def test_non_permit_never_executes(self):
        clk = Clock(); L = _ledger(clk)
        ex = EffectTimeExecutor(L, CONFIRMATION_TTL_S, APPROVAL_CEILING_60MIN, clk, lambda: {})
        a = fx._dana()
        d = decide(GateRequest(a, None), FakeGate("PERMIT"))
        ex.execute(d, a, None, {})
        self.assertEqual(d.decision, HOLD)
        self.assertFalse(d.side_effect_executed)


if __name__ == "__main__":
    unittest.main()
