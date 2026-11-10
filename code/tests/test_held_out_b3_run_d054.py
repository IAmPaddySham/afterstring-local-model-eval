"""D-054: --held-out-b3 is opt-in, full mode + retrieval v0 only, and leaves the b1/b2 paths alone."""
import contextlib
import inspect
import io
import unittest

from evals import run


class HeldOutB3RunD054(unittest.TestCase):
    def test_flag_exists(self):
        self.assertIn('"--held-out-b3"', inspect.getsource(run.main))
        self.assertTrue(hasattr(run, "run_held_out_b3"))

    def test_refused_combinations(self):
        for argv in (["--mode", "baseline", "--held-out-b3"],
                     ["--mode", "full", "--held-out-b3", "--no-retrieval"],
                     ["--mode", "full", "--held-out-b3", "--retrieval", "v1"],
                     ["--mode", "full", "--held-out-b3", "--only", "B3-01"],
                     ["--mode", "full", "--held-out-b3", "--held-out-b2"]):
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    run.main(argv)

    def test_b3_items_all_v0(self):
        from evals import held_out_b3
        items = held_out_b3.load()
        self.assertEqual(len(items), 18)
        self.assertEqual({i["manifest"] for i in items}, {"v0"})

    def test_b2_dirname_unchanged(self):
        from evals import held_out_b2
        self.assertEqual(held_out_b2.sealed_dirname("X"), "X-held-out-b2-SEALED")


if __name__ == "__main__":
    unittest.main()
