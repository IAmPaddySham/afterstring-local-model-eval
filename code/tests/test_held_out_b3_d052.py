"""D-052: held-out batch 3 (18 items, approved by Paddy 2026-11-01) is filed and loads. Blind: nothing is run.
No test opens anything under runs/ or evals/grading/."""
import hashlib
import re
import unittest
from pathlib import Path

from evals import held_out, held_out_b2, held_out_b3, items
from evals.run import model_turns
from harness import config

SRC = config.AFTERSTRING_ROOT / "council/inbox/projects/2026-11-01-eval-batch3-codex"
GEMINI = SRC / "GEMINI_PASS2_2026-11-01_verbatim.md"
GEMINI_SHA = "472966d6"
DEV = [config.PROJECT_ROOT / "evals/drafts/2026-10-25-eval-items-v0.md",
       config.PROJECT_ROOT / "evals/practice/2026-10-26-manual-nine.md"]
# What each wired citation must contain (checked against the live file).
MUST = {"B3-03": ["pause_and_reassess"], "B3-04": ["Release ≡ Also Love"],
        "B3-06": ["earlier yes", "expired for state changes"], "B3-07": ["fresh, human-present confirmation"],
        "B3-10": ["not a guarantee of outcomes"], "B3-13": ["not a guarantee of outcomes"],
        "B3-16": ["| 0 |", "| 5 |"], "B3-18": ["Love is not a feeling"]}


def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()


def lines(rel):
    return (config.AFTERSTRING_ROOT / rel).read_text(encoding="utf-8").splitlines()


class Batch3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b3 = held_out_b3.load()

    def test_loads_18_in_order(self):
        self.assertEqual([i["id"] for i in self.b3], [f"B3-{n:02d}" for n in range(1, 19)])
        for i in self.b3:
            self.assertTrue(i["text"].strip(), i["id"])
            self.assertEqual(i["manifest"], "v0")

    def test_prompts_verbatim_from_gemini(self):
        g = GEMINI.read_text(encoding="utf-8")
        if hashlib.sha256(GEMINI.read_bytes()).hexdigest()[:8] != GEMINI_SHA:
            self.skipTest("source file changed")
        for i in self.b3:
            self.assertIn(f'- Prompt / setup: "{i["text"]}" (context: {i["context_note"]})', g, i["id"])

    def test_no_overlap_with_batch1_batch2_dev(self):
        other = [i["text"] for i in held_out.load()] + [i["text"] for i in held_out_b2.load()]
        for p in DEV:
            for it in items.parse(p):
                turns, _, _ = model_turns(it)
                other += [t.text for t in turns]
        self.assertGreater(len(other), 50)
        other = {norm(t) for t in other if t}
        for i in self.b3:
            n = norm(i["text"])
            self.assertNotIn(n, other, i["id"])
            self.assertFalse(any(n in o or o in n for o in other if len(o) > 20), i["id"])

    def test_wired_citations_exist_and_say_it(self):
        for i in self.b3:
            for path, a, b in i["citations"]:
                ls = lines(path)
                self.assertTrue(1 <= a <= b <= len(ls), (i["id"], path, a, b))
                self.assertTrue(any(ls[k - 1].strip() for k in range(a, b + 1)), (i["id"], path, a, b))
            if i["id"] in MUST:
                txt = "\n".join(lines(p)[k - 1] for p, a, b in i["citations"] for k in range(a, b + 1))
                for s in MUST[i["id"]]:
                    self.assertIn(s, txt, i["id"])

    def test_wiring_notes_applied(self):
        d = {i["id"]: i for i in self.b3}
        g = "projects/fail-close-governor/drafts/governor-PLATINUM-public-2026-10-22-r2.md"
        self.assertEqual(d["B3-04"]["citations"], [("papers/release-clause-v4-guardrails.md", 17, 17)])
        self.assertEqual(d["B3-06"]["citations"], [(g, 19, 19), (g, 75, 75)])
        self.assertEqual((d["B3-08"]["sources"], d["B3-08"]["citations"]), ("none", []))
        self.assertIn("papers/the-bench.md:L4", d["B3-05"]["wiring_note"])
        self.assertIn("Module 14", lines("papers/the-bench.md")[3])
        self.assertIn("published posts", d["B3-11"]["wiring_note"])
        self.assertIn("pointer to people", d["B3-12"]["wiring_note"])
        for k in ("B3-14", "B3-15"):
            self.assertIn("stays Fail", d[k]["wiring_note"])
        self.assertIn("papers/module-4.2-optics-layer.md", d["B3-17"]["wiring_note"])
        self.assertTrue((config.AFTERSTRING_ROOT / "papers/module-4.2-optics-layer.md").exists())
        text = held_out_b3.HELD_OUT_B3.read_text(encoding="utf-8")
        self.assertIn("**Warmth rule (approval, all items).**", text)

    def test_other_loaders_refuse_b3(self):
        with self.assertRaises(Exception):
            held_out.load(held_out_b3.HELD_OUT_B3)
        with self.assertRaises(Exception):
            held_out_b2.load(held_out_b3.HELD_OUT_B3)
        with self.assertRaises(held_out_b3.NotApproved):
            held_out_b3.load(held_out_b2.HELD_OUT_B2)

    def test_blind_not_wired_no_keys(self):
        # D-054 (Paddy t1259u) wired batch 3 as opt-in --held-out-b3 and allows its sealed runs, blind sheets and
        # SEALED key. Still blind: no grades, no unsealed key, no results file for batch 3.
        run_src = (config.PROJECT_ROOT / "evals/run.py").read_text(encoding="utf-8")
        self.assertIn('"--held-out-b3"', run_src)
        # D-055: Paddy's batch-3 grades and RESULTS (2026-11-03) now exist by design; still no unsealed key file.
        self.assertFalse(any("b3" in p.name.lower() and "unsealed" in p.name.lower()
                             for p in (config.PROJECT_ROOT / "evals/grading").iterdir()))
        self.assertTrue(all(p.name.endswith("-SEALED") for p in (config.PROJECT_ROOT / "runs").iterdir()
                            if "b3" in p.name.lower()))

if __name__ == "__main__":
    unittest.main()
