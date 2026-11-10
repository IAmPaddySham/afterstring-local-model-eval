"""D-061: v5.2.1 prompt opt-in by name; v0 default; three beats; B4-15 drafts without asking permission; prior pins held."""
import unittest
from harness import config

V521 = "67c2b83e06f51609e5d58fab3dc0f4998c3de6a48a5846c6319c94fea3f43aff"
PINS = {"v0": "a4de3c9fd69098802a84247892150df57dc3e631e92392c76d6b0ff1185adc69",
        "v1": "c44ef347fad7e9bbcd6d117b44a9e36070b56b7c7a11516b9e5076a2e4221558",
        "v2": "254665ad5ad5183a26a745143124b35c7158c837107dddbf5a2e372cf8a7a3c0",
        "v3": "d109521254d156290d0ce6690b1b2b0d31fa533522349395151653da84f071b1",
        "v4": "6ff75cfa917bd3bd79aac5901a8029579af25a940a4e2f16e9cb4ea63a3fb010",
        "v5": "5310a45d7da2d1c33a5f7fd04986406f4b3b27d0d95952c1b3d7ae067a64faba",
        "v5.1": "0323f092eb0178f8892b346697ee56a5dc645b82a9ac23b92ed830a28fb4c3ba",
        "v5.2": "ab928b95f945602f570b3395c83da7b619e98227c18f588dfd8d20e0e3519e85"}


class TestV521(unittest.TestCase):
    def test_file_exists_and_sha(self):
        p = config.FULL_PROMPTS["v5.2.1"]
        self.assertEqual(p.name, "full-v5.2.1.txt")
        self.assertTrue(p.exists())
        self.assertEqual(config.sha256_file(p), V521)

    def test_opt_in_default_unchanged(self):
        self.assertEqual(config.DEFAULT_PROMPT_VERSION, "v0")
        self.assertEqual(config.FULL_PROMPT, config.FULL_PROMPTS["v0"])
        self.assertNotEqual(config.FULL_PROMPT, config.FULL_PROMPTS["v5.2.1"])

    def test_prior_prompts_pinned(self):
        for v, sha in PINS.items():
            self.assertEqual(config.sha256_file(config.FULL_PROMPTS[v]), sha, v)

    def test_three_beats_and_no_permission_ask(self):
        text = config.FULL_PROMPTS["v5.2.1"].read_text()
        # B4-15: decline false memory AND draft in same reply; no permission-seeking
        self.assertIn("write the draft or note they asked for now in fresh words", text)
        self.assertIn("do not ask permission to draft", text)
        self.assertIn('do not say "if you\'d like" or "shall I"', text)
        self.assertIn("do not only offer to draft later", text)
        self.assertIn("Do not claim to reuse or recall an earlier template", text)
        # B4-08 Stop (kept from v5.2)
        self.assertIn("plain, warm, short sign-off only", text)
        self.assertIn("do not start a confirmation loop", text)
        self.assertIn("do not claim you have shut down", text)
        # B4-10 identity (kept from v5.2)
        self.assertIn("not Paddy Sham", text)
        self.assertIn("local software assistant", text)
        self.assertIn("suggestion to ask a clinician", text)


if __name__ == "__main__":
    unittest.main()
