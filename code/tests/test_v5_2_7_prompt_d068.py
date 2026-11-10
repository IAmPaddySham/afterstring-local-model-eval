import unittest
import harness.config as cfg


class TestV527(unittest.TestCase):
    def test_optin_and_clauses(self):
        self.assertEqual(cfg.DEFAULT_PROMPT_VERSION, "v0")
        txt = cfg.FULL_PROMPTS["v5.2.7"].read_text()
        for s in ("a hotline number alone is not enough", "name the specific thing you noticed",
                  "thinking about ending their life", "safe right now", "988", "911",
                  "only for goodbye-planning signs", "get to safety", "do not lead with 988"):
            self.assertIn(s, txt)

    def test_only_line10_differs_from_v526(self):
        a = cfg.FULL_PROMPTS["v5.2.6"].read_text().split("\n")
        b = cfg.FULL_PROMPTS["v5.2.7"].read_text().split("\n")
        self.assertEqual(len(a), len(b))
        self.assertEqual([i for i in range(len(a)) if a[i] != b[i]], [9])


if __name__ == "__main__":
    unittest.main()
