"""D-058: --held-out-b4 is opt-in, full mode + retrieval v0, per-item none for B4-03/B4-07; leaves b1/b2/b3 alone."""
import contextlib
import inspect
import io
import unittest

from evals import run
from harness.pipeline import Pipeline, Turn


class HeldOutB4RunD058(unittest.TestCase):
    def test_flag_exists(self):
        self.assertIn('"--held-out-b4"', inspect.getsource(run.main))
        self.assertTrue(hasattr(run, "run_held_out_b4"))

    def test_refused_combinations(self):
        for argv in (["--mode", "baseline", "--held-out-b4"],
                     ["--mode", "full", "--held-out-b4", "--no-retrieval"],
                     ["--mode", "full", "--held-out-b4", "--retrieval", "v1"],
                     ["--mode", "full", "--held-out-b4", "--only", "B4-01"],
                     ["--mode", "full", "--held-out-b4", "--held-out-b3"],
                     ["--mode", "full", "--held-out-b4", "--held-out-b2"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    run.main(argv)

    def test_b4_item_manifests(self):
        from evals import held_out_b4
        items = held_out_b4.load()
        self.assertEqual(len(items), 18)
        self.assertEqual({i["id"] for i in items if i["manifest"] == "none"}, {"B4-03", "B4-07"})
        self.assertEqual(sum(1 for i in items if i["manifest"] == "v0"), 16)

    def test_skip_retrieval_on_turn(self):
        """Per-item override: skip_retrieval=True yields no retrieval dict even when the Pipeline has a retriever."""
        pipe = Pipeline("no-model", retrieval=True)
        self.assertIsNotNone(pipe.retriever)
        # Afterstring question that would otherwise apply retrieval.
        text = "Can you explain what Paddy means by the '1/0 = To Stay' zero-gate singularity in Afterstring?"
        self.assertTrue(pipe.retriever.applies(text))
        with_skip = pipe.run([Turn(text=text, skip_retrieval=True)])[0]
        self.assertIsNone(with_skip.retrieval)
        without = pipe.run([Turn(text=text, skip_retrieval=False)])[0]
        self.assertIsNotNone(without.retrieval)
        self.assertTrue(without.retrieval.get("applied"))

    def test_b3_dirname_unchanged(self):
        from evals import held_out_b3
        # b3 path untouched by this slice
        self.assertTrue(hasattr(held_out_b3, "HELD_OUT_B3"))


if __name__ == "__main__":
    unittest.main()
