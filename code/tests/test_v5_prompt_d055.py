"""D-055: v5 prompt opt-in by name; v0 default; v0-v4 bytes pinned; five-item diagnostic file off the held-out path."""
import re
import unittest
from harness import config
from evals import items as itemsmod, held_out_b3

PINS = {"v0": "a4de3c9fd69098802a84247892150df57dc3e631e92392c76d6b0ff1185adc69",
        "v1": "c44ef347fad7e9bbcd6d117b44a9e36070b56b7c7a11516b9e5076a2e4221558",
        "v2": "254665ad5ad5183a26a745143124b35c7158c837107dddbf5a2e372cf8a7a3c0",
        "v3": "d109521254d156290d0ce6690b1b2b0d31fa533522349395151653da84f071b1",
        "v4": "6ff75cfa917bd3bd79aac5901a8029579af25a940a4e2f16e9cb4ea63a3fb010",
        "v5": "5310a45d7da2d1c33a5f7fd04986406f4b3b27d0d95952c1b3d7ae067a64faba"}
DIAG = config.PROJECT_ROOT / "evals" / "diagnostic" / "2026-11-03-b3-diagnostic-five.md"
IDS = ["B3-01", "B3-02", "B3-12", "B3-13", "B3-15"]


class TestV5(unittest.TestCase):
    def test_v5_by_name(self):
        self.assertEqual(config.FULL_PROMPTS["v5"].name, "full-v5.txt")
        self.assertTrue(config.FULL_PROMPTS["v5"].exists())

    def test_default_v0(self):
        self.assertEqual(config.DEFAULT_PROMPT_VERSION, "v0")
        self.assertEqual(config.FULL_PROMPT, config.FULL_PROMPTS["v0"])

    def test_prompt_shas_pinned(self):
        for v, sha in PINS.items():
            self.assertEqual(config.sha256_file(config.FULL_PROMPTS[v]), sha, v)

    def test_run_choices_include_v5(self):
        src = (config.PROJECT_ROOT / "evals/run.py").read_text(encoding="utf-8")
        self.assertIn("choices=sorted(config.FULL_PROMPTS)", src)


class TestDiagnostic(unittest.TestCase):
    def test_exact_ids_and_not_held_out_path(self):
        its = itemsmod.parse(DIAG)
        self.assertEqual([i["id"] for i in its], IDS)
        self.assertNotIn("held-out", DIAG.parent.name)
        self.assertNotEqual(DIAG.resolve(), held_out_b3.HELD_OUT_B3.resolve())
        self.assertIn("DIAGNOSTIC", DIAG.read_text(encoding="utf-8").splitlines()[0])

    def test_blocks_verbatim_and_turns_match_sealed_loader(self):
        src = held_out_b3.HELD_OUT_B3.read_text(encoding="utf-8")
        diag = DIAG.read_text(encoding="utf-8")
        sealed = {h["id"]: h for h in held_out_b3.load()}
        for it in itemsmod.parse(DIAG):
            m = re.search(rf"^### {it['id']} .*?(?=^### |\Z)", src, re.M | re.S)
            block = m.group(0).rstrip().rstrip("-").rstrip()
            self.assertIn(block, diag)
            self.assertEqual(itemsmod.quoted_prompt(it["setup"]), sealed[it["id"]]["text"])
            self.assertEqual(it.get("context_note", ""), sealed[it["id"]]["context_note"])


if __name__ == "__main__":
    unittest.main()
