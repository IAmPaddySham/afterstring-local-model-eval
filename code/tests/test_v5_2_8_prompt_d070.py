import unittest
import harness.config as cfg


class TestV528(unittest.TestCase):
    def test_optin_and_clauses(self):
        self.assertEqual(cfg.DEFAULT_PROMPT_VERSION, "v0")
        txt = cfg.FULL_PROMPTS["v5.2.8"].read_text()
        for s in ("not a betrayal", "no guilt", "is not the Release Clause", "never invent what the Release Clause says",
                  "do not only ask them to paste it and stop", "cannot verify the exact wording here",
                  "check the public text", "Never invent quotes, pages, or post numbers"):
            self.assertIn(s, txt)

    def test_is_v527_plus_two_lines(self):
        a = cfg.FULL_PROMPTS["v5.2.7"].read_text().split("\n")
        b = cfg.FULL_PROMPTS["v5.2.8"].read_text().split("\n")
        self.assertEqual(b[:12], a[:12])
        self.assertEqual(b[14:], a[12:])
        self.assertEqual(len(b), len(a) + 2)


if __name__ == "__main__":
    unittest.main()
