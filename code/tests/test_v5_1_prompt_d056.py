"""D-056: v5.1 prompt opt-in by name; v0 default; v0-v5 bytes pinned."""
import unittest
from harness import config

V51 = "0323f092eb0178f8892b346697ee56a5dc645b82a9ac23b92ed830a28fb4c3ba"
PINS = {"v0": "a4de3c9fd69098802a84247892150df57dc3e631e92392c76d6b0ff1185adc69",
        "v1": "c44ef347fad7e9bbcd6d117b44a9e36070b56b7c7a11516b9e5076a2e4221558",
        "v2": "254665ad5ad5183a26a745143124b35c7158c837107dddbf5a2e372cf8a7a3c0",
        "v3": "d109521254d156290d0ce6690b1b2b0d31fa533522349395151653da84f071b1",
        "v4": "6ff75cfa917bd3bd79aac5901a8029579af25a940a4e2f16e9cb4ea63a3fb010",
        "v5": "5310a45d7da2d1c33a5f7fd04986406f4b3b27d0d95952c1b3d7ae067a64faba"}


class TestV51(unittest.TestCase):
    def test_file_exists_and_sha(self):
        p = config.FULL_PROMPTS["v5.1"]
        self.assertEqual(p.name, "full-v5.1.txt")
        self.assertTrue(p.exists())
        self.assertEqual(config.sha256_file(p), V51)

    def test_opt_in_default_unchanged(self):
        self.assertEqual(config.DEFAULT_PROMPT_VERSION, "v0")
        self.assertEqual(config.FULL_PROMPT, config.FULL_PROMPTS["v0"])
        self.assertNotEqual(config.FULL_PROMPT, config.FULL_PROMPTS["v5.1"])

    def test_v0_v5_pinned(self):
        for v, sha in PINS.items():
            self.assertEqual(config.sha256_file(config.FULL_PROMPTS[v]), sha, v)


if __name__ == "__main__":
    unittest.main()
