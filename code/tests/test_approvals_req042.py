"""REQ-042 (D-033): a real approvals count, persistent for the run, used by OR-08 and the ceiling."""
import json
import tempfile
import unittest
from pathlib import Path

from harness.approvals import ApprovalsLedger, ApprovalsUnavailable, window_from_config
from harness.gate_adapter import APPROVAL_CEILING_60MIN, PERMIT, HOLD, DENY
from harness.pipeline import Pipeline, Turn
from harness import config

PAY = "Pay Dana $40 for the concert tickets"


class Clock:
    def __init__(self, t=1_000_000.0): self.t = t
    def __call__(self): return self.t


class FakeGate:
    backend = "fake"
    def __init__(self, word="PERMIT"): self.word = word
    def ask(self, *a, **k): return self.word, "FAKE", 0.0


def _ledger(clock):
    return ApprovalsLedger(Path(tempfile.mkdtemp()) / "approvals.jsonl", clock=clock)


def _pipe(clock, ledger, gate=None, **kw):
    return Pipeline("no-model", gate=gate or FakeGate("PERMIT"), retrieval=False, ledger=ledger, clock=clock, **kw)


def _yes(clock, i):
    return Turn(text=PAY, local_hour=14, confirmation={"id": f"c{i}", "confirmed_at": clock.t - 1})


class LedgerTests(unittest.TestCase):
    def test_window_is_config_and_matches_d014(self):
        cfg = config.load_gate_config()
        self.assertEqual(window_from_config(cfg), 3600.0)
        self.assertEqual(APPROVAL_CEILING_60MIN, 10)

    def test_count_persists_on_disk_and_rolls_off(self):
        clk = Clock(); L = _ledger(clk)
        for i in range(3):
            L.record_approval(f"c{i}", "h"); clk.t += 60
        again = ApprovalsLedger(L.path, clock=clk, create=False)   # a fresh reader sees the same count
        self.assertEqual(again.count(), 3)
        clk.t = 1_000_000.0 + 3600            # first approval is now exactly 60 min old: out of the window
        self.assertEqual(again.count(), 2)
        clk.t += 10_000
        self.assertEqual(again.count(), 0)

    def test_single_use(self):
        clk = Clock(); L = _ledger(clk)
        L.record_approval("c1", "h")
        with self.assertRaises(ApprovalsUnavailable):
            L.record_approval("c1", "h")

    def test_corrupt_or_missing_fails_closed(self):
        clk = Clock(); L = _ledger(clk)
        L.record_approval("c1", "h"); L.record_approval("c2", "h")
        lines = L.path.read_text().splitlines()
        cases = {
            "edited": lines[:1] + [lines[1].replace('"c1"', '"cX"')] + lines[2:],
            "dropped": [lines[0], lines[2]],
            "garbage": lines + ["{not json"],
            "no header": lines[1:],
            "empty": [],
        }
        for name, ls in cases.items():
            p = Path(tempfile.mkdtemp()) / "a.jsonl"; p.write_text("\n".join(ls) + ("\n" if ls else ""))
            with self.assertRaises(ApprovalsUnavailable, msg=name):
                ApprovalsLedger(p, clock=clk, create=False).count()
        with self.assertRaises(ApprovalsUnavailable):
            ApprovalsLedger(Path(tempfile.mkdtemp()) / "missing.jsonl", clock=clk, create=False).count()

    def test_future_record_fails_closed(self):
        clk = Clock(); L = _ledger(clk)
        L.record_approval("c1", "h", t=clk.t + 3600)
        with self.assertRaises(ApprovalsUnavailable):
            L.count()


class PipelineCountTests(unittest.TestCase):
    def test_ceiling_hit_in_pipeline_holds_next_consequential(self):
        clk = Clock(); L = _ledger(clk); p = _pipe(clk, L)
        decisions = []
        for i in range(APPROVAL_CEILING_60MIN + 1):
            r = p.run([_yes(clk, i)])[0]
            decisions.append(r.gate["decision"]); clk.t += 30
            self.assertEqual(r.approvals["count"], i)
        self.assertEqual(decisions[:APPROVAL_CEILING_60MIN], [PERMIT] * APPROVAL_CEILING_60MIN)
        self.assertEqual(decisions[-1], HOLD)
        self.assertIn("OR-08", [f["rule"] for f in r.optics["fired"]])
        self.assertTrue(any("approval frequency" in x for x in r.gate["reasons"]))
        self.assertFalse(r.gate["side_effect_executed"])

    def test_roll_off_frees_the_ceiling(self):
        clk = Clock(); L = _ledger(clk); p = _pipe(clk, L)
        for i in range(APPROVAL_CEILING_60MIN):
            p.run([_yes(clk, i)]); clk.t += 1
        self.assertEqual(p.run([_yes(clk, 100)])[0].gate["decision"], HOLD)
        clk.t += 3599                          # c0..c9 are now >= 60 min old; c100 is 59 min 59 s old
        r = p.run([_yes(clk, 101)])[0]
        self.assertEqual(r.approvals["count"], 1)        # only c100 (recorded at the HOLD) is still in the window
        self.assertEqual(r.gate["decision"], PERMIT)
        self.assertTrue(r.gate["side_effect_executed"])

    def test_corrupt_ledger_holds_consequential(self):
        clk = Clock(); L = _ledger(clk); p = _pipe(clk, L)
        L.path.write_text(L.path.read_text() + "corrupt\n")
        r = p.run([_yes(clk, 1)])[0]
        self.assertFalse(r.approvals["ok"])
        self.assertEqual(r.gate["decision"], HOLD)
        self.assertTrue(any("unavailable or corrupt" in x for x in r.gate["reasons"]))
        self.assertIn("OR-08", [f["rule"] for f in r.optics["fired"]])
        self.assertFalse(r.gate["side_effect_executed"])

    def test_missing_ledger_holds_consequential(self):
        clk = Clock(); L = _ledger(clk); p = _pipe(clk, L)
        L.path.unlink()
        r = p.run([_yes(clk, 1)])[0]
        self.assertEqual(r.gate["decision"], HOLD)
        self.assertFalse(r.gate["side_effect_executed"])

    def test_text_only_turn_unaffected_by_count(self):
        clk = Clock(); L = _ledger(clk); p = _pipe(clk, L)
        r = p.run([Turn(text="What is Afterstring?", local_hour=14)])[0]
        self.assertEqual(r.approvals["count"], 0)
        self.assertEqual(r.gate["decision"], PERMIT)
        self.assertFalse(r.gate["side_effect_executed"])

    def test_no_confirmation_still_holds(self):
        clk = Clock(); p = _pipe(clk, _ledger(clk))
        self.assertEqual(p.run([Turn(text=PAY, local_hour=14)])[0].gate["decision"], HOLD)

    def test_sends_stay_refused_with_real_gate(self):
        """D-020: an approved send is still refused by gate.rb (no allowlist entry added)."""
        clk = Clock(); p = Pipeline("no-model", retrieval=False, ledger=_ledger(clk), clock=clk)
        r = p.run([Turn(text="Send the email to Sam", local_hour=14,
                        confirmation={"id": "s1", "confirmed_at": clk.t - 1})])[0]
        self.assertNotEqual(r.gate["decision"], PERMIT)
        self.assertFalse(r.gate["side_effect_executed"])


if __name__ == "__main__":
    unittest.main()
