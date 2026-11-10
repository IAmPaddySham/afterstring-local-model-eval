import unittest
import harness.config as cfg


class TestV526(unittest.TestCase):
    def test_optin_and_crisis_clause(self):
        self.assertEqual(cfg.DEFAULT_PROMPT_VERSION, "v0")
        txt = cfg.FULL_PROMPTS["v5.2.6"].read_text()
        for s in ("giving away possessions", "goodbye letters", "strange calm", "do not chat casually past it",
                  "thinking about ending their life", "safe right now", "988", "911",
                  "do not invent other numbers", "Stay present"):
            self.assertIn(s, txt)

    def test_is_v525_plus_one_clause(self):
        a = cfg.FULL_PROMPTS["v5.2.5"].read_text().splitlines()
        b = cfg.FULL_PROMPTS["v5.2.6"].read_text().splitlines()
        self.assertEqual(len(b), len(a) + 1)
        extra = [l for l in b if l not in a]
        self.assertEqual(len(extra), 1)
        self.assertIn("988", extra[0])


if __name__ == "__main__":
    unittest.main()
