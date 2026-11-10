"""Held-out wiring (D-035, Paddy t813u): a separate loader; never merged, never in prompt context."""
import tempfile
import unittest
from pathlib import Path

from evals import held_out, items
from harness import config


class HeldOutWiringTests(unittest.TestCase):
    def test_loader_returns_16_model_items(self):
        hs = held_out.load()
        self.assertEqual([h["id"] for h in hs], [f"HO-{i:02d}" for i in range(1, 17)])
        self.assertTrue(all(h["kind"] == "Model" and h["text"] for h in hs))

    def test_separate_from_the_approved_eval_set(self):
        self.assertEqual(items.parse(held_out.HELD_OUT), [])
        ids = {i["id"] for i in items.parse()}
        self.assertFalse(any(i.startswith("HO-") for i in ids))

    def test_draft_or_unapproved_copy_refused(self):
        draft = Path(config.PROJECT_ROOT) / "evals/drafts/2026-10-27-held-out-v0-DRAFT.md"
        with self.assertRaises(held_out.NotApproved):
            held_out.load(draft)
        p = Path(tempfile.mkdtemp()) / "x.md"
        p.write_text(held_out.HELD_OUT.read_text().replace(held_out.APPROVAL_LINE, "- **Approval:** pending", 1))
        with self.assertRaises(held_out.NotApproved):
            held_out.load(p)

    def test_never_in_retrieval_or_prompts(self):
        allow = Path(config.RETRIEVAL_ALLOWLIST).read_text()
        self.assertNotIn("held-out", allow)
        self.assertNotIn("evals/", allow)
        man = Path(config.RETRIEVAL_MANIFEST).read_text()
        self.assertNotIn("held-out", man)
        for p in config.FULL_PROMPTS.values():
            t = Path(p).read_text()
            self.assertNotIn("HO-", t)
            for h in held_out.load():
                self.assertNotIn(h["text"], t)

    def test_sealed_dirname(self):
        self.assertEqual(held_out.sealed_dirname("20261027-220000"), "20261027-220000-held-out-SEALED")

    def test_run_flag_is_full_mode_only(self):
        from evals import run
        for argv in (["--mode", "no-model"], ["--mode", "baseline"], ["--mode", "full", "--only", "HO-01"]):
            with self.assertRaises(SystemExit) as cm:
                run.main(argv + ["--held-out", "--allow-dirty"])
            self.assertIn("--held-out runs full mode only", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
