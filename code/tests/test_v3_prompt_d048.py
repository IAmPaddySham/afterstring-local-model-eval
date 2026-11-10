import unittest
from harness import config
class TestV3OptIn(unittest.TestCase):
    def test_v3_selectable(self):
        self.assertIn("v3", config.FULL_PROMPTS)
        self.assertEqual(config.sha256_file(config.FULL_PROMPTS["v3"]), "d109521254d156290d0ce6690b1b2b0d31fa533522349395151653da84f071b1")
    def test_default_still_v0(self):
        self.assertEqual(config.DEFAULT_PROMPT_VERSION, "v0")
        self.assertEqual(config.FULL_PROMPT, config.FULL_PROMPTS["v0"])
if __name__ == "__main__": unittest.main()
