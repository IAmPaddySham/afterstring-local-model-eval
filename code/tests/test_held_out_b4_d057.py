"""D-057/D-058: held-out batch 4 (18 items, approved by Paddy 2026-11-04) loads against the sealed pin.
Blind: nothing is graded here. No test opens anything under runs/ or evals/grading/."""
import hashlib
import re
import unittest
from pathlib import Path

from evals import held_out, held_out_b2, held_out_b3, held_out_b4, items
from evals.run import model_turns
from harness import config

R2 = config.PROJECT_ROOT / "notes/2026-11-03-batch4-GOOGLE-AI-MODE-r2-verbatim.md"
R2_SHA = "2ea9ebb1"
DEV = [config.PROJECT_ROOT / "evals/drafts/2026-10-25-eval-items-v0.md",
       config.PROJECT_ROOT / "evals/practice/2026-10-26-manual-nine.md"]


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


class Batch4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b4 = held_out_b4.load()

    def test_loads_18_in_order_against_sealed_pin(self):
        self.assertEqual([i["id"] for i in self.b4], [f"B4-{n:02d}" for n in range(1, 19)])
        digest = hashlib.sha256(held_out_b4.HELD_OUT_B4.read_bytes()).hexdigest()
        self.assertEqual(digest, held_out_b4.ITEMS_SHA256)
        sealed = held_out_b4.SEALED_SHA.read_text(encoding="utf-8")
        self.assertIn(held_out_b4.ITEMS_SHA256, sealed)
        self.assertIn("192c998f", sealed)
        self.assertIn("2ea9ebb1", sealed)

    def test_per_item_retrieval_override(self):
        d = {i["id"]: i["manifest"] for i in self.b4}
        self.assertEqual(d["B4-03"], "none")
        self.assertEqual(d["B4-07"], "none")
        self.assertEqual({i["id"] for i in self.b4 if i["manifest"] == "none"}, {"B4-03", "B4-07"})
        self.assertEqual({i["manifest"] for i in self.b4 if i["id"] not in ("B4-03", "B4-07")}, {"v0"})
        for i in self.b4:
            self.assertTrue(i["text"].strip(), i["id"])
            self.assertTrue(i["sources"].startswith("none"), i["id"])

    def test_prompts_verbatim_from_r2_second_half(self):
        raw = R2.read_text(encoding="utf-8")
        if hashlib.sha256(R2.read_bytes()).hexdigest()[:8] != R2_SHA:
            self.skipTest("r2 source file changed")
        # revised second half starts at B4-01 around line 177; use the last occurrence of each prompt.
        for i in self.b4:
            needle = f'Prompt / setup: "{i["text"]}" (context: {i["context_note"]})'
            self.assertIn(needle, raw, i["id"])

    def test_no_overlap_with_batch1_2_3_dev(self):
        other = ([i["text"] for i in held_out.load()]
                 + [i["text"] for i in held_out_b2.load()]
                 + [i["text"] for i in held_out_b3.load()])
        for p in DEV:
            for it in items.parse(p):
                turns, _, _ = model_turns(it)
                other += [t.text for t in turns]
        self.assertGreater(len(other), 50)
        other = {norm(t) for t in other if t}
        for i in self.b4:
            n = norm(i["text"])
            self.assertNotIn(n, other, i["id"])
            self.assertFalse(any(n in o or o in n for o in other if len(o) > 20), i["id"])

    def test_other_loaders_refuse_b4(self):
        with self.assertRaises(Exception):
            held_out.load(held_out_b4.HELD_OUT_B4)
        with self.assertRaises(Exception):
            held_out_b2.load(held_out_b4.HELD_OUT_B4)
        with self.assertRaises(Exception):
            held_out_b3.load(held_out_b4.HELD_OUT_B4)
        with self.assertRaises(held_out_b4.NotApproved):
            held_out_b4.load(held_out_b3.HELD_OUT_B3)

    def test_wired_opt_in_sealed_key_kept(self):
        # D-058 wired batch 4 as opt-in --held-out-b4.
        # D-059: after Paddy t1665u unseal, an UNSEALED companion exists by design; SEALED key file must remain.
        run_src = (config.PROJECT_ROOT / "evals/run.py").read_text(encoding="utf-8")
        self.assertIn('"--held-out-b4"', run_src)
        grading = config.PROJECT_ROOT / "evals/grading"
        sealed_keys = [p for p in grading.iterdir()
                       if "b4" in p.name.lower() and "blind-key-sealed" in p.name.lower()
                       and not p.name.endswith(".bak") and ".bak-" not in p.name]
        self.assertTrue(sealed_keys, "SEALED blind key must remain after unseal")
        self.assertTrue(all(p.name.endswith("-SEALED") for p in (config.PROJECT_ROOT / "runs").iterdir()
                            if "b4" in p.name.lower()))


if __name__ == "__main__":
    unittest.main()
