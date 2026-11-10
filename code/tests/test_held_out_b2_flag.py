"""D-044 (Paddy t874u): the `--held-out-b2` run switch. No model is called and nothing under the real runs/ is
opened or written: argument tests stop at git_info, and the one sealing test uses a fake backend and a temp RUNS."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import held_out, held_out_b2, run
from harness import config
from harness.model import GenResult

V0_IDS = [f"HO2-{i:02d}" for i in range(1, 18)]


class Stop(Exception):
    pass


def parse_only(argv):
    """main() up to the argument checks; git_info is stubbed to stop there and no run function may be reached."""
    seen = {}
    real = run._retrieval_manifest

    def spy(args):
        seen["args"] = args
        seen["manifest"] = real(args)
        return seen["manifest"]
    with mock.patch.object(run, "git_info", side_effect=Stop()), \
            mock.patch.object(run, "_retrieval_manifest", side_effect=spy), \
            mock.patch.object(run, "run_held_out", side_effect=AssertionError("batch 1 must not run")), \
            mock.patch.object(run, "run_held_out_b2", side_effect=AssertionError("batch 2 must not run")):
        try:
            run.main(argv)
        except Stop:
            seen["reached_git"] = True
    return seen


def refused(testcase, argv, text=None):
    with mock.patch.object(run, "git_info", side_effect=AssertionError("checks must refuse before git")), \
            mock.patch.object(run, "run_held_out", side_effect=AssertionError("batch 1 must not run")), \
            mock.patch.object(run, "run_held_out_b2", side_effect=AssertionError("batch 2 must not run")), \
            contextlib.redirect_stderr(io.StringIO()):
        with testcase.assertRaises(SystemExit) as cm:
            run.main(argv)
    if text:
        testcase.assertIn(text, str(cm.exception.code))
    return cm.exception


class Parsing(unittest.TestCase):
    def test_flag_parses_default_v0(self):
        seen = parse_only(["--mode", "full", "--held-out-b2"])
        self.assertTrue(seen["reached_git"])
        self.assertTrue(seen["args"].held_out_b2)
        self.assertFalse(seen["args"].held_out)
        self.assertEqual(seen["args"].retrieval, "v0")
        self.assertIsNone(seen["manifest"])

    def test_flag_with_v1_selects_manifest_v1(self):
        seen = parse_only(["--mode", "full", "--held-out-b2", "--retrieval", "v1"])
        self.assertTrue(seen["reached_git"])
        self.assertEqual(Path(seen["manifest"]).name, "manifest-v1.json")

    def test_off_by_default(self):
        seen = parse_only(["--mode", "no-model"])
        self.assertFalse(seen["args"].held_out_b2)


class Refusals(unittest.TestCase):
    def test_batch1_and_batch2_mutually_exclusive(self):
        e = refused(self, ["--mode", "full", "--held-out", "--held-out-b2"])
        self.assertEqual(e.code, 2)   # argparse usage error, before anything else

    def test_b2_full_mode_whole_set_only(self):
        for argv in (["--mode", "no-model"], ["--mode", "baseline"], ["--mode", "full", "--only", "HO2-01"],
                     ["--mode", "full", "--items", "evals/held-out/held-out-b2.md"]):
            refused(self, argv + ["--held-out-b2"], "--held-out-b2 runs full mode only")

    def test_b2_refuses_no_retrieval(self):
        for extra in ([], ["--retrieval", "v1"]):
            refused(self, ["--mode", "full", "--held-out-b2", "--no-retrieval"] + extra, "--no-retrieval is not allowed")

    def test_existing_refusals_intact(self):
        refused(self, ["--mode", "full", "--held-out", "--retrieval", "v1"], "--held-out (batch 1) stays on retrieval v0")
        refused(self, ["--mode", "no-model", "--no-retrieval", "--retrieval", "v1"], "contradict each other")


class Dispatch(unittest.TestCase):
    def _dispatch(self, argv):
        git = {"dirty": False}
        with mock.patch.object(run, "git_info", return_value=git), mock.patch.object(run, "check_tree", return_value=None), \
                mock.patch.object(run, "run_held_out", side_effect=AssertionError("batch 1 must not run")), \
                mock.patch.object(run, "run_held_out_b2", return_value="b2") as m:
            self.assertEqual(run.main(argv), "b2")
        return m.call_args.args

    def test_v0_dispatch(self):
        args, git, manifest = self._dispatch(["--mode", "full", "--held-out-b2"])
        self.assertIsNone(manifest)
        self.assertEqual(args.retrieval, "v0")

    def test_v1_dispatch(self):
        args, git, manifest = self._dispatch(["--mode", "full", "--held-out-b2", "--retrieval", "v1"])
        self.assertEqual(Path(manifest).name, "manifest-v1.json")


class Ho218Handling(unittest.TestCase):
    def test_v0_runs_17_and_leaves_out_ho2_18(self):
        chosen, left = held_out_b2.select(held_out_b2.load(), "v0")
        self.assertEqual([i["id"] for i in chosen], V0_IDS)
        self.assertEqual(left, ["HO2-18"])

    def test_v1_runs_only_ho2_18(self):
        chosen, left = held_out_b2.select(held_out_b2.load(), "v1")
        self.assertEqual([(i["id"], i["original_id"]) for i in chosen], [("HO2-18", "OP-02")])
        self.assertEqual(left, V0_IDS)

    def test_unknown_manifest_refused(self):
        with self.assertRaises(ValueError):
            held_out_b2.select(held_out_b2.load(), "v9")
        with self.assertRaises(ValueError):
            held_out_b2.sealed_dirname("20261028-200000", "v9")


class SealedNames(unittest.TestCase):
    def test_names(self):
        self.assertEqual(held_out_b2.sealed_dirname("20261028-200000"), "20261028-200000-held-out-b2-SEALED")
        self.assertEqual(held_out_b2.sealed_dirname("20261028-200000", "v1"), "20261028-200000-held-out-b2-v1-SEALED")
        self.assertEqual(held_out.sealed_dirname("20261028-200000"), "20261028-200000-held-out-SEALED")


class FakeBackend:
    """Not a model: returns a fixed string so the sealing code can be checked without loading anything."""
    loaded = True
    name = "fake"
    entry = {}

    def __init__(self, *a, **k):
        self.calls = 0

    def generate(self, messages, max_tokens=400):
        self.calls += 1
        t = "[fake backend: no model]"
        return GenResult(text=t, raw_text=t, finish_reason="stop", backend="fake")

    def identity(self):
        return {"backend": "fake"}


class SealingWithFakeBackend(unittest.TestCase):
    def _run(self, extra):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.object(config, "RUNS", Path(tmp.name)), \
                mock.patch("harness.model.MLXBackend", FakeBackend), \
                mock.patch.object(run, "identity", return_value={"note": "fake"}), \
                mock.patch.object(run, "git_info", return_value={"dirty": False}), \
                mock.patch.object(run, "check_tree", return_value=None), \
                contextlib.redirect_stdout(io.StringIO()):
            run.main(["--mode", "full", "--held-out-b2", "--no-weight-check"] + extra)
        dirs = list(Path(tmp.name).iterdir())
        self.assertEqual(len(dirs), 1)
        return dirs[0]

    def _check_sealed(self, d, ids):
        self.assertTrue((d / "SEALED.md").is_file())
        self.assertTrue((d / "SHA256SUMS").is_file())
        self.assertFalse((d / "summary.md").exists())
        self.assertEqual(sorted(p.stem for p in (d / "outputs").iterdir()), ids)
        listed = (d / "SHA256SUMS").read_text()
        for name in ("run.json", "results.jsonl", "SEALED.md"):
            self.assertIn(name, listed)
        rj = json.loads((d / "run.json").read_text())
        self.assertEqual(rj["batch"], 2)
        self.assertEqual(rj["items"], len(ids))
        self.assertEqual(rj["items_file"], "evals/held-out/held-out-b2.md")
        self.assertTrue(rj["read_only_check"]["unchanged"])
        return rj

    def test_v0_run_is_sealed_and_skips_ho2_18(self):
        d = self._run([])
        self.assertTrue(d.name.endswith("-held-out-b2-SEALED"))
        self.assertNotIn("-v1-", d.name)
        rj = self._check_sealed(d, V0_IDS)
        self.assertEqual(rj["retrieval_version"], "v0")
        self.assertEqual(rj["not_in_this_run"]["ids"], ["HO2-18"])
        self.assertEqual(rj["retrieval"]["manifest_sha256"], config.sha256_file(config.RETRIEVAL_MANIFESTS["v0"]))
        self.assertIn("Not in this run: HO2-18", (d / "SEALED.md").read_text())

    def test_v1_run_is_only_ho2_18(self):
        d = self._run(["--retrieval", "v1"])
        self.assertTrue(d.name.endswith("-held-out-b2-v1-SEALED"))
        rj = self._check_sealed(d, ["HO2-18"])
        self.assertEqual(rj["retrieval_version"], "v1")
        self.assertEqual(rj["retrieval"]["manifest_sha256"], config.sha256_file(config.RETRIEVAL_MANIFESTS["v1"]))

    def test_batch1_sealed_run_unchanged_by_refactor(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.object(config, "RUNS", Path(tmp.name)), \
                mock.patch("harness.model.MLXBackend", FakeBackend), \
                mock.patch.object(run, "identity", return_value={"note": "fake"}), \
                mock.patch.object(run, "git_info", return_value={"dirty": False}), \
                mock.patch.object(run, "check_tree", return_value=None), \
                contextlib.redirect_stdout(io.StringIO()):
            run.main(["--mode", "full", "--held-out", "--no-weight-check"])
        (d,) = list(Path(tmp.name).iterdir())
        self.assertTrue(d.name.endswith("-held-out-SEALED"))
        rj = json.loads((d / "run.json").read_text())
        self.assertEqual(rj["set"], "held-out (SEALED, D-035)")
        self.assertEqual(rj["items_file"], "evals/held-out/held-out-v0.md")
        self.assertEqual(rj["items"], 16)
        for k in ("batch", "retrieval_version", "item_manifests", "not_in_this_run"):
            self.assertNotIn(k, rj)
        self.assertEqual(rj["retrieval"]["manifest_sha256"], config.sha256_file(config.RETRIEVAL_MANIFESTS["v0"]))
        self.assertIn("\n\nSealed under D-035 (Paddy t813u). Do not open `outputs/`", (d / "SEALED.md").read_text())


if __name__ == "__main__":
    unittest.main()
