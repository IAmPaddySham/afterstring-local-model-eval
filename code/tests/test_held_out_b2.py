"""D-043: held-out batch 2 (18 items, approved by Paddy 2026-10-28) and the opt-in retrieval v1 run option.

Batch 2 is loaded, never run here. Batch 1 (held_out.py, held-out-v0.md) and the v0 retrieval default are unchanged.
No test opens anything under runs/.
"""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals import held_out, held_out_b2, items
from harness import config
from harness.retrieval import Retriever

ROOT = config.PROJECT_ROOT
B2 = held_out_b2.HELD_OUT_B2
EXPECTED = [("HO2-01", "MISTRAL-01"), ("HO2-02", "CHATGPT-01"), ("HO2-03", "GEMINI-02"), ("HO2-04", "CHATGPT-02"),
            ("HO2-05", "CHATGPT-03"), ("HO2-06", "META-03"), ("HO2-07", "META-04"), ("HO2-08", "DEEPSEEK-04"),
            ("HO2-09", "CHATGPT-05"), ("HO2-10", "MISTRAL-05"), ("HO2-11", "MISTRAL-06"), ("HO2-12", "GEMINI-06"),
            ("HO2-13", "MISTRAL-07"), ("HO2-14", "CHATGPT-07"), ("HO2-15", "CHATGPT-08"), ("HO2-16", "DEEPSEEK-08"),
            ("HO2-17", "OP-01"), ("HO2-18", "OP-02")]
# Pinned before batch 2 was filed (2026-10-28, HEAD 94e4029).
BATCH1_FILE_SHA = "05a5a20689e19778ae605eadc10afe058d99e4d652b985438f44cb8d0dd3c133"
BATCH1_LOADER_SHA = "be9e098f3ba1dd8ac0b2909df8163365ab11098c815d8194203f129c668848a1"
BATCH1_LOAD_JSON_SHA = "37ec953ec10b7f845f8eb4ddeb02e911823aa38ae21b845a273a36bf3191dbde"
MANIFEST_V0_SHA = "621be560f4acb068e77bd654853bc858bc9ac7121f5bbe011dade8db73ead1fa"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Batch2Loads(unittest.TestCase):
    def test_loads_18_in_order_with_original_ids(self):
        got = held_out_b2.load()
        self.assertEqual([(i["id"], i["original_id"]) for i in got], EXPECTED)
        for i in got:
            self.assertTrue(i["text"].strip(), i["id"])
            self.assertFalse(i["text"].startswith('"') or i["text"].endswith('"'), i["id"])

    def test_approvals_are_exactly_18(self):
        text = B2.read_text(encoding="utf-8")
        self.assertEqual(text.count(held_out_b2.APPROVAL_LINE), 18)
        self.assertEqual(len(held_out_b2.APPROVED), 18)
        self.assertEqual(sorted(i["approval"] for i in held_out_b2.load()),
                         sorted(t for _, t in held_out_b2.APPROVED.values()))

    def test_extra_or_missing_approval_refused(self):
        text = B2.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "b2.md"
            p.write_text(text.replace(held_out_b2.APPROVAL_LINE + ", t846u", "- removed", 1), encoding="utf-8")
            with self.assertRaises(held_out_b2.NotApproved):
                held_out_b2.load(p)
            p.write_text(text + "\n" + held_out_b2.APPROVAL_LINE + ", t999u\n", encoding="utf-8")
            with self.assertRaises(held_out_b2.NotApproved):
                held_out_b2.load(p)
            p.write_text(text.replace(held_out_b2.APPROVAL_LINE + ", t847u", held_out_b2.APPROVAL_LINE + ", t846u", 1),
                         encoding="utf-8")
            with self.assertRaises(held_out_b2.NotApproved):
                held_out_b2.load(p)

    def test_written_by_and_manifest(self):
        got = {i["original_id"]: i for i in held_out_b2.load()}
        self.assertEqual(got["OP-01"]["written_by"], "Operator-written")
        self.assertEqual(got["OP-02"]["written_by"], "Operator-written")
        self.assertTrue(all(i["written_by"].startswith("Model-written") for k, i in got.items() if not k.startswith("OP-")))
        self.assertEqual(got["OP-02"]["manifest"], "v1")
        self.assertEqual([k for k, i in got.items() if i["manifest"] != "v0"], ["OP-02"])
        self.assertIn("Mistral", got["MISTRAL-01"]["written_by"])
        self.assertIn("GLM-01", got["MISTRAL-01"]["aliases"])

    def test_context_lines_split_from_quoted_words(self):
        got = {i["original_id"]: i for i in held_out_b2.load()}
        self.assertTrue(got["DEEPSEEK-04"]["context_note"])
        self.assertNotIn("(context:", got["DEEPSEEK-04"]["text"])
        self.assertIn("ℰ₁₃", got["OP-02"]["text"])
        self.assertTrue(got["CHATGPT-02"]["text"].startswith("According to my published files"))

    def test_batch1_loader_refuses_batch2_and_vice_versa(self):
        with self.assertRaises(held_out.NotApproved):
            held_out.load(B2)
        with self.assertRaises(held_out_b2.NotApproved):
            held_out_b2.load(held_out.HELD_OUT)

    def test_eval_parser_ignores_batch2(self):
        self.assertEqual(items.parse(B2), [])

    def test_batch2_never_in_prompts_or_retrieval(self):
        words = [i["text"] for i in held_out_b2.load()]
        for p in list(config.FULL_PROMPTS.values()) + [config.RETRIEVAL_ALLOWLIST,
                                                        config.RETRIEVAL_MANIFESTS["v1"].with_name("allowlist-v1.txt")]:
            body = Path(p).read_text(encoding="utf-8")
            self.assertNotIn("held-out-b2", body)
            for w in words:
                self.assertNotIn(w, body)


class Batch1Unchanged(unittest.TestCase):
    def test_batch1_bytes_and_load(self):
        self.assertEqual(sha(held_out.HELD_OUT), BATCH1_FILE_SHA)
        self.assertEqual(sha(ROOT / "evals" / "held_out.py"), BATCH1_LOADER_SHA)
        got = held_out.load()
        self.assertEqual(len(got), 16)
        self.assertEqual(hashlib.sha256(json.dumps(got, sort_keys=True).encode()).hexdigest(), BATCH1_LOAD_JSON_SHA)


class RetrievalOption(unittest.TestCase):
    def test_default_is_v0_and_unchanged(self):
        self.assertEqual(config.DEFAULT_RETRIEVAL_VERSION, "v0")
        self.assertEqual(config.RETRIEVAL_MANIFESTS["v0"], config.RETRIEVAL_MANIFEST)
        self.assertEqual(config.RETRIEVAL_MANIFEST.name, "manifest-v0.json")
        self.assertEqual(sha(config.RETRIEVAL_MANIFEST), MANIFEST_V0_SHA)
        r = Retriever()
        self.assertEqual(r.manifest_sha256, MANIFEST_V0_SHA)

    def _parse_only(self, argv):
        """Run main() only up to argument checks: git_info is stubbed to stop there, so no run folder is made."""
        from evals import run

        class Stop(Exception):
            pass
        seen = {}
        real = run._retrieval_manifest

        def spy(args):
            seen["args"] = args
            seen["manifest"] = real(args)
            return seen["manifest"]
        with mock.patch.object(run, "git_info", side_effect=Stop()), \
                mock.patch.object(run, "_retrieval_manifest", side_effect=spy):
            with self.assertRaises(Stop):
                run.main(argv)
        return seen

    def test_run_default_is_v0_and_passes_no_manifest(self):
        seen = self._parse_only(["--mode", "no-model"])
        self.assertEqual(seen["args"].retrieval, "v0")
        self.assertIsNone(seen["manifest"])

    def test_run_v1_option_selects_manifest_v1(self):
        seen = self._parse_only(["--mode", "no-model", "--retrieval", "v1"])
        self.assertEqual(Path(seen["manifest"]).name, "manifest-v1.json")

    def test_main_passes_manifest_to_pipeline(self):
        import inspect
        from evals import run
        src = inspect.getsource(run.main)
        self.assertIn("retrieval_manifest=retrieval_manifest", src)
        self.assertLess(src.index("_retrieval_manifest(args)"), src.index("git_info()"))

    def test_v1_refused_with_held_out_or_no_retrieval(self):
        from evals import run

        class Stop(Exception):
            pass
        for argv in (["--mode", "full", "--held-out", "--retrieval", "v1"],
                     ["--mode", "no-model", "--no-retrieval", "--retrieval", "v1"]):
            with mock.patch.object(run, "git_info", side_effect=Stop()):
                with self.assertRaises(SystemExit):
                    run.main(argv)

    def test_pipeline_v1_loads_v1(self):
        from harness.pipeline import Pipeline
        v0 = Pipeline("no-model")
        v1 = Pipeline("no-model", retrieval_manifest=config.RETRIEVAL_MANIFESTS["v1"])
        self.assertEqual(v0.retriever.manifest_sha256, MANIFEST_V0_SHA)
        self.assertEqual(v1.retriever.manifest_sha256, sha(config.RETRIEVAL_MANIFESTS["v1"]))
        self.assertGreater(len(v1.retriever.chunks), len(v0.retriever.chunks))
        self.assertEqual(v1.executor.identity_fn()["RETRIEVAL_MANIFEST"], sha(config.RETRIEVAL_MANIFESTS["v1"]))
        self.assertEqual(v0.executor.identity_fn()["RETRIEVAL_MANIFEST"], MANIFEST_V0_SHA)


if __name__ == "__main__":
    unittest.main()
