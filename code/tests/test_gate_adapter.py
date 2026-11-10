import unittest
from harness.gate_adapter import GateRb, decide, GateRequest, PERMIT, DENY, HOLD, ESCALATE
from harness.actions import text_only
from evals import fixtures_v0 as fx

EXPECT = {"T01": PERMIT, "T02": HOLD, "T03": DENY, "T04": DENY, "T05": DENY, "T06": DENY, "T09": DENY,
          "T17": DENY, "U2": DENY, "U5": DENY, "X01": DENY, "X04": ESCALATE, "X05": DENY,
          "X09": DENY, "X10": ESCALATE}


class FakeGate:
    backend = "fake"
    def __init__(self, word="PERMIT"): self.word = word
    def ask(self, *a, **k): return self.word, "FAKE", 0.0


class GateAdapterTests(unittest.TestCase):
    def test_fixtures_real_gate(self):
        g = GateRb()
        self.assertEqual(g.backend, "gate.rb", "gate_cli.rb not callable; adapter would be a HOLD stub")
        for case, want in EXPECT.items():
            req, _, _ = fx.gp_case(case)
            d = decide(req, g)
            self.assertEqual(d.decision, want, (case, d.reasons))
            self.assertEqual(d.side_effect_executed, d.decision == PERMIT and req.action.tier >= 2)
        req, _, _ = fx.gp_case("T06")
        self.assertTrue(decide(req, g).bypass_event)

    def test_no_confirmation_never_permits_consequential(self):
        req, _, _ = fx.gp_case("T02")
        self.assertNotEqual(decide(req, FakeGate("PERMIT")).decision, PERMIT)

    def test_stub_defaults_hold(self):
        g = GateRb(ruby="/nonexistent/ruby")
        self.assertTrue(g.backend.startswith("STUB"))
        self.assertEqual(decide(GateRequest(text_only()), g).decision, HOLD)

    def test_never_auto_sabbath(self):
        import inspect
        from harness import gate_adapter
        src = inspect.getsource(gate_adapter.GateRb.ask)
        self.assertIn('assert "--auto-sabbath" not in cmd', src)

    def test_text_only_permits(self):
        self.assertEqual(decide(GateRequest(text_only()), GateRb()).decision, PERMIT)


# ---------- D-013 / D-014 (Paddy pt723u) ----------
import subprocess
import yaml
from harness import config
from harness.actions import Action
from harness.gate_adapter import Confirmation, action_hash, CONFIRMATION_TTL_S, APPROVAL_CEILING_60MIN


def _send():
    return Action(verb="send", kind="external_transmit", tier=3,
                  params={"to": "sister@example.invalid", "subject": "test", "body": "hello"},
                  endpoint="agent.send", source="test")


def _delete():
    return Action(verb="delete", kind="destroy", tier=3, params={"path": "drafts/old"},
                  endpoint="agent.delete", source="test")


def _yes(a, age):
    return Confirmation(action_hash=action_hash(a), age_s=age)


class GateConfigTests(unittest.TestCase):
    """D-014: the numbers live in configs/gate-v0.yaml, not in code."""
    def test_numbers_come_from_config(self):
        cfg = config.load_gate_config()
        self.assertEqual(cfg["confirmation_ttl_s"], 120)
        self.assertEqual(cfg["approval_ceiling_60min"], 10)
        self.assertEqual(CONFIRMATION_TTL_S, cfg["confirmation_ttl_s"])
        self.assertEqual(APPROVAL_CEILING_60MIN, cfg["approval_ceiling_60min"])

    def test_ceiling_matches_or08(self):
        rules = yaml.safe_load(open(config.RULES_YAML))
        self.assertEqual(int(rules["thresholds"]["n_fatigue"]), APPROVAL_CEILING_60MIN)

    def test_window_boundary(self):
        req, _, _ = fx.gp_case("T01")
        a = req.action
        ok = decide(GateRequest(a, _yes(a, CONFIRMATION_TTL_S - 1)), FakeGate("PERMIT"))
        self.assertEqual(ok.decision, PERMIT, ok.reasons)
        stale = decide(GateRequest(a, _yes(a, CONFIRMATION_TTL_S + 1)), FakeGate("PERMIT"))
        self.assertEqual(stale.decision, DENY, stale.reasons)

    def test_ceiling_holds(self):
        req, _, _ = fx.gp_case("T01")
        a = req.action
        d = decide(GateRequest(a, _yes(a, 10), approvals_last_60min=APPROVAL_CEILING_60MIN), FakeGate("PERMIT"))
        self.assertEqual(d.decision, HOLD, d.reasons)


class SendDeleteTests(unittest.TestCase):
    """Sends and deletes against the real runtime/gate.rb (read-only).

    D-013 (Paddy pt723u): an approved send should be allowed. NOT implemented yet: gate.rb's
    DENY for external_transmit comes from the constitution blacklist on external_data_transmission
    (matrix-grokbuild.yaml and matrix-openweight.yaml), not from the LITE fallback rule, so the
    narrow override Paddy's decision was scoped to has nothing to apply to. These tests pin
    today's behavior; test_approved_send_* flips when Paddy chooses the route (see D-013).
    """
    g = GateRb()

    def test_approved_send_is_still_deny_today(self):
        a = _send()
        d = decide(GateRequest(a, _yes(a, 30)), self.g)
        self.assertTrue(d.approved_passed_to_gate_rb, d.reasons)   # every adapter check passed
        self.assertEqual(d.gate_rb_raw, "TRIGGER_RESONANCE_MODE")
        self.assertEqual(d.decision, DENY)
        self.assertFalse(d.side_effect_executed)

    def test_unapproved_send_never_permits(self):
        d = decide(GateRequest(_send(), None), self.g)
        self.assertIn(d.decision, (DENY, HOLD))
        self.assertFalse(d.side_effect_executed)

    def test_stale_send_denied(self):
        a = _send()
        d = decide(GateRequest(a, _yes(a, CONFIRMATION_TTL_S + 1)), self.g)
        self.assertEqual(d.decision, DENY)
        self.assertFalse(d.approved_passed_to_gate_rb)

    def test_stop_send_denied(self):
        a = _send()
        d = decide(GateRequest(a, _yes(a, 10), stop_pressed=True), self.g)
        self.assertEqual(d.decision, DENY)
        self.assertFalse(d.approved_passed_to_gate_rb)

    def test_approved_delete_still_deny(self):
        a = _delete()
        d = decide(GateRequest(a, _yes(a, 30)), self.g)
        self.assertEqual(d.decision, DENY)
        self.assertFalse(d.side_effect_executed)

    def test_send_deny_source_is_constitution_blacklist(self):
        """Read-only probe: which matrix policies gate.rb sees for external_transmit."""
        root = str(config.AFTERSTRING_ROOT)
        rb = ('require "./runtime/constitution_loader"; require "./runtime/gate"; '
              'c=Afterstring::Constitution.new(Dir.pwd); al=Afterstring::Gate::MATRIX_ALIASES[:external_transmit]; '
              '[c.matrix,c.matrix_rlm,c.matrix_grokbot,c.matrix_openweight].compact.each{|m| '
              '(m["matrix"]||[]).select{|r| al.include?(r["action"].to_s)}.each{|r| puts r["policy"]}}')
        out = subprocess.run(["/usr/bin/ruby", "-e", rb], cwd=root, capture_output=True, text=True, timeout=10)
        self.assertIn("blacklist", out.stdout.split(), out.stderr)


if __name__ == "__main__":
    unittest.main()
