"""The approved held-out set stays held out: not parsed, not the eval set, not in prompts (D-029)."""
import unittest
from pathlib import Path
from evals import items
from harness import config

APPROVED = Path(config.PROJECT_ROOT) / "evals/held-out/held-out-v0.md"


class HeldOutApprovedTests(unittest.TestCase):
    def test_marked_approved_with_16_approval_lines(self):
        text = APPROVED.read_text(encoding="utf-8")
        self.assertIn("APPROVED by Paddy 2026-10-27", text)
        for i in range(1, 17):
            self.assertIn(f"### HO-{i:02d}", text)
        self.assertEqual(text.count("- **Approval:** APPROVED by Paddy 2026-10-27"), 16)

    def test_not_parsed_and_not_the_eval_set(self):
        self.assertEqual(items.parse(APPROVED), [])
        self.assertNotEqual(Path(config.EVAL_ITEMS).resolve(), APPROVED.resolve())

    def test_not_in_prompts(self):
        for p in config.FULL_PROMPTS.values():
            text = Path(p).read_text(encoding="utf-8")
            self.assertNotIn("HO-", text)
            self.assertNotIn("held-out", text)


if __name__ == "__main__":
    unittest.main()
