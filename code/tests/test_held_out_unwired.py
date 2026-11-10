"""The held-out DRAFT must stay out of runs until Paddy approves it (2026-10-27)."""
import unittest
from pathlib import Path
from evals import items
from harness import config

DRAFT = Path(config.PROJECT_ROOT) / "evals/drafts/2026-10-27-held-out-v0-DRAFT.md"


class HeldOutUnwiredTests(unittest.TestCase):
    def test_marked_draft(self):
        self.assertIn("DRAFT — pending Paddy approval, never used for prompt tuning", DRAFT.read_text(encoding="utf-8"))

    def test_not_parsed_and_not_the_eval_set(self):
        self.assertEqual(items.parse(DRAFT), [])
        self.assertNotEqual(Path(config.EVAL_ITEMS).resolve(), DRAFT.resolve())

    def test_not_in_prompts(self):
        for p in config.FULL_PROMPTS.values():
            self.assertNotIn("HO-", Path(p).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
