"""Synthetic stubs only. Written for a separately authorized future test run.

Never load real held-out packs, sealed outputs, keys, grades or MLX. All generated
artifacts, fake prompts/items and outputs below are synthetic temporary fixtures.
"""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from evals import run as runner
from harness.pipeline import Pipeline, Turn, TurnResult


class StubModel:
    loaded = True
    instances = []

    def __init__(self, model_id=None):
        self.entry = {"sampling": {"temperature": 1.0, "top_p": .95, "top_k": 64}}
        self.calls, self.sample_calls, self.greedy_restores = [], [], 0
        self.instances.append(self)

    def generate(self, messages, max_tokens):
        self.calls.append(([dict(m) for m in messages], max_tokens))
        return SimpleNamespace(text="SYNTHETIC clean", to_dict=lambda: {
            "raw_text": "SYNTHETIC raw", "finish_reason": "stop"})

    def use_sampling(self, seed, settings):
        self.sample_calls.append((seed, dict(settings)))

    def use_greedy(self):
        self.greedy_restores += 1

    def identity(self):
        return {"repo": "synthetic/repo", "revision": "synthetic-revision",
                "weights_sha256_pinned": "synthetic-weight-sha"}


class StubGate:
    backend = "synthetic-gate"


class StubLedger:
    def __init__(self, path):
        self.path = path

    def records(self):
        return []


class FullPipelineStub:
    """Checks runner full wiring only; not a substitute for existing full tests."""
    def __init__(self, mode, model, max_tokens, **kw):
        assert mode == "full"
        assert kw["gate"] is not None and kw["ledger"] is not None
        self.mode, self.model, self.max_tokens = mode, model, max_tokens
        self.system_prompt = "SYNTHETIC selected system"
        self.retriever = SimpleNamespace(manifest_sha256="synthetic", chunks=[], skipped=[], error=None)
        self.options = kw

    def run(self, turns):
        turn = turns[0]
        g = self.model.generate([{"role": "system", "content": self.system_prompt},
                                 {"role": "user", "content": turn.text}], self.max_tokens)
        return [TurnResult(output=g.text + " SYNTHETIC wrapper", path="model",
                           model_text=g.text, gen=g.to_dict(), gate={"decision": "HOLD"},
                           optics={"verdict": "ALLOW"},
                           crisis={"fired": True, "matched": "synthetic"},
                           retrieval={"used": ["synthetic-source"]})]


class SealedBaselineOptInTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="sealed-baseline-stub-")))
        self.runs = self.temp / "runs"
        self.prompt = self.temp / "synthetic-prompt.txt"
        self.prompt.write_text("SYNTHETIC selected system")
        self.items = self.temp / "synthetic-items.txt"
        self.items.write_text("SYNTHETIC fixture identity, not an evaluation pack")
        self.console = io.StringIO()
        self.stack.enter_context(contextlib.redirect_stdout(self.console))
        self.stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
        for key, value in {"PROJECT_ROOT": self.temp, "RUNS": self.runs,
                           "FULL_PROMPTS": {"v0": self.prompt}, "RULES_YAML": self.prompt,
                           "CRISIS_YAML": self.prompt}.items():
            self.stack.enter_context(mock.patch.object(runner.config, key, value))
        self.loader = self.stack.enter_context(mock.patch("harness.model.MLXBackend", StubModel))
        self.gate_ctor = self.stack.enter_context(mock.patch.object(runner, "GateRb", return_value=StubGate()))
        self.ledger_ctor = self.stack.enter_context(mock.patch("harness.approvals.ApprovalsLedger", StubLedger))
        self.stack.enter_context(mock.patch.object(runner, "tree_hash", return_value={"sha256": "synthetic", "files": 0}))
        self.identity = self.stack.enter_context(mock.patch.object(runner, "identity", return_value={
            "upstream_id": "synthetic/repo@synthetic-revision", "weight_hash": "synthetic-weight-sha"}))
        StubModel.instances = []

    def sealed(self, mode="baseline", samples=5, missing_mode=False):
        args = SimpleNamespace(model="synthetic", max_tokens=400, prompt="v0", no_retrieval=False,
                               samples=samples, seed=20261027, no_weight_check=False)
        if not missing_mode:
            args.mode = mode
        hs = [{"id": "SYN-01", "text": "SYNTHETIC user", "context_note": "SYNTHETIC note", "manifest": "none"}]
        name = "SYNTHETIC-held-out-b5-SEALED"
        cls = FullPipelineStub if mode == "full" else Pipeline
        with mock.patch.object(runner, "Pipeline", cls):
            runner._run_sealed(args, {"dirty": False}, hs, lambda stamp: name,
                               self.items, "SYNTHETIC set", "SYNTHETIC seal")
        out = self.runs / (name if mode == "full" else name[:-len("-SEALED")] + "-baseline-SEALED")
        run = json.loads((out / "run.json").read_text())
        rows = [json.loads(line) for line in (out / "results.jsonl").read_text().splitlines()]
        return out, run, rows, StubModel.instances[-1]

    def test_cli_baseline_opt_in_dispatches_all_existing_sealed_flags(self):
        pairs = [("--held-out", "run_held_out"), ("--held-out-b2", "run_held_out_b2"),
                 ("--held-out-b3", "run_held_out_b3"), ("--held-out-b4", "run_held_out_b4"),
                 ("--held-out-b5", "run_held_out_b5")]
        for flag, target in pairs:
            with self.subTest(flag=flag), mock.patch.object(runner, "git_info", return_value={"dirty": False}), \
                    mock.patch.object(runner, target, return_value="synthetic-dispatch") as dispatch:
                self.assertEqual(runner.main(["--mode", "baseline", flag]), "synthetic-dispatch")
                self.assertEqual(dispatch.call_args.args[0].mode, "baseline")

    def test_cli_full_dispatch_is_preserved(self):
        for flag, target in [("--held-out", "run_held_out"), ("--held-out-b2", "run_held_out_b2"),
                             ("--held-out-b3", "run_held_out_b3"), ("--held-out-b4", "run_held_out_b4"),
                             ("--held-out-b5", "run_held_out_b5")]:
            with self.subTest(flag=flag), mock.patch.object(runner, "git_info", return_value={"dirty": False}), \
                    mock.patch.object(runner, target, return_value="synthetic-full") as dispatch:
                self.assertEqual(runner.main(["--mode", "full", flag]), "synthetic-full")
                self.assertEqual(dispatch.call_args.args[0].mode, "full")

    def test_cli_no_model_sealed_remains_rejected(self):
        with mock.patch.object(runner, "git_info", return_value={"dirty": False}):
            for flag in ("--held-out", "--held-out-b2", "--held-out-b3", "--held-out-b4", "--held-out-b5"):
                with self.subTest(flag=flag), self.assertRaises(SystemExit):
                    runner.main(["--mode", "no-model", flag])

    def test_explicit_mode_still_required(self):
        with self.assertRaises(SystemExit):
            runner.main(["--held-out-b5"])

    def test_whole_set_restrictions_preserved(self):
        for flag in ("--held-out", "--held-out-b2", "--held-out-b3", "--held-out-b4", "--held-out-b5"):
            for option in ("--items", "--only"):
                with self.subTest(flag=flag, option=option), \
                        mock.patch.object(runner, "git_info", return_value={"dirty": False}), \
                        self.assertRaises(SystemExit):
                    runner.main(["--mode", "baseline", flag, option, "SYNTHETIC"])

    def test_default_prompt_is_still_v0(self):
        self.assertEqual(runner.config.DEFAULT_PROMPT_VERSION, "v0")

    def test_actual_baseline_pipeline_sends_history_and_user_note_only(self):
        model = StubModel()
        poison = {name: self.stack.enter_context(mock.patch("harness.pipeline." + name,
                  side_effect=AssertionError("baseline constructed " + name)))
                  for name in ("InputGuard", "GateRb", "CrisisResources", "Retriever", "ApprovalsLedger")}
        pipe = Pipeline("baseline", model, 400, prompt_version="v0")
        history = [("user", "SYNTHETIC prior"), ("assistant", "SYNTHETIC prior reply")]
        result = pipe.run([Turn("SYNTHETIC user", context_note="SYNTHETIC note")], history)[0]
        self.assertEqual(model.calls[0][0], [
            {"role": "user", "content": "SYNTHETIC prior"},
            {"role": "assistant", "content": "SYNTHETIC prior reply"},
            {"role": "user", "content": "[SYNTHETIC note]\nSYNTHETIC user"}])
        self.assertEqual(result.output, "SYNTHETIC clean")
        for name in ("guard", "gate", "crisis", "retriever", "ledger", "executor", "system_prompt"):
            self.assertIsNone(getattr(pipe, name))
        for constructor in poison.values(): constructor.assert_not_called()

    def test_baseline_sealed_directory_and_sealing_artifacts(self):
        out, run, rows, model = self.sealed()
        self.assertTrue(out.name.endswith("-held-out-b5-baseline-SEALED"))
        self.assertTrue((out / "SEALED.md").is_file())
        self.assertTrue((out / "SHA256SUMS").is_file())
        self.assertFalse((out / "approvals.jsonl").exists())
        self.assertEqual(run["mode"], "baseline")
        self.assertEqual(len(rows), 6)

    def test_baseline_does_not_construct_gate_or_ledger(self):
        with mock.patch.object(runner, "GateRb", side_effect=AssertionError("gate called")), \
                mock.patch("harness.approvals.ApprovalsLedger", side_effect=AssertionError("ledger called")):
            out, run, rows, model = self.sealed()
        self.assertIsNone(run["gate_backend"])
        self.assertIsNone(run["approvals_in_run"])
        for row in rows:
            for field in ("gate_detail", "optics_detail", "crisis_fired", "retrieval", "approvals"):
                self.assertFalse(row[field])
            self.assertFalse(row["input_delivery"]["system_prompt_sent"])
            self.assertFalse(row["input_delivery"]["retrieval_sent"])

    def test_selected_prompt_identity_is_not_a_sent_prompt_claim(self):
        out, run, rows, model = self.sealed()
        self.assertEqual(run["full_prompt_sha256"], hashlib.sha256(self.prompt.read_bytes()).hexdigest())
        self.assertEqual(run["full_prompt_version"], "v0")
        self.assertFalse(run["system_prompt_sent"])
        self.assertIsNone(run["full_prompt_sent_sha256"])
        self.assertFalse(run["retrieval_sent"])
        self.assertIn("selected", run["full_prompt_sha256_semantics"])

    def test_raw_model_output_is_separate_from_wrapper_and_legacy_field(self):
        out, run, rows, model = self.sealed()
        for row in rows:
            self.assertEqual(row["raw_model_text"], "SYNTHETIC raw")
            self.assertEqual(row["output"], "SYNTHETIC clean")
            self.assertIsNone(row["model_text"])  # Existing baseline field retained.

    def test_greedy_plus_five_seeded_samples_and_identity_are_traceable(self):
        out, run, rows, model = self.sealed()
        seeds = [int(hashlib.sha256(("20261027:SYN-01:%d" % k).encode()).hexdigest()[:8], 16)
                 for k in range(1, 6)]
        self.assertEqual(len(model.calls), 6)
        self.assertEqual([row["seed"] for row in rows], [None] + seeds)
        self.assertEqual([row["run"] for row in rows], ["greedy"] + [".s%02d" % k for k in range(1, 6)])
        self.assertEqual(run["sampling"]["seeds"], {"SYN-01": seeds})
        self.assertEqual(run["sampling"]["settings"], model.entry["sampling"])
        self.assertEqual(run["sampling"]["base_seed"], 20261027)
        self.assertEqual(run["max_tokens"], 400)
        self.assertEqual([s for s, _ in model.sample_calls], seeds)
        self.assertEqual(model.greedy_restores, 1)
        self.assertEqual(run["artifact_identity"]["weight_hash"], "synthetic-weight-sha")
        self.assertEqual(run["items_sha256"], hashlib.sha256(self.items.read_bytes()).hexdigest())

    def test_full_path_retains_name_wrappers_gate_and_selected_prompt(self):
        out, run, rows, model = self.sealed(mode="full")
        self.assertEqual(out.name, "SYNTHETIC-held-out-b5-SEALED")
        self.assertNotIn("baseline", (out / "SEALED.md").read_text())
        self.assertEqual(run["mode"], "full")
        self.assertEqual(run["gate_backend"], "synthetic-gate")
        self.assertEqual(run["approvals_in_run"], 0)
        self.assertTrue(run["system_prompt_sent"])
        self.assertTrue(run["retrieval_sent"])
        self.assertEqual(run["full_prompt_sent_sha256"], run["full_prompt_sha256"])
        for row in rows:
            self.assertEqual(row["output"], "SYNTHETIC clean SYNTHETIC wrapper")
            self.assertEqual(row["model_text"], "SYNTHETIC clean")
            self.assertEqual(row["raw_model_text"], "SYNTHETIC raw")

    def test_existing_direct_sealed_callers_without_mode_default_to_full(self):
        out, run, rows, model = self.sealed(mode="full", missing_mode=True, samples=0)
        self.assertEqual(run["mode"], "full")
        self.assertEqual(out.name, "SYNTHETIC-held-out-b5-SEALED")

    def test_no_generate_path_does_not_claim_system_prompt_was_sent(self):
        pipe = SimpleNamespace(mode="full", system_prompt="selected system")
        flags = runner._input_delivery(pipe, TurnResult("SYNTHETIC hold", "held_without_model"))
        record = runner._prompt_record("v0", [flags])
        self.assertFalse(record["system_prompt_sent"])
        self.assertIsNone(record["full_prompt_sent_sha256"])
        self.assertFalse(record["retrieval_sent"])

    def test_failed_baseline_call_has_no_raw_model_text_or_extras(self):
        with mock.patch.object(StubModel, "generate", side_effect=RuntimeError("synthetic failure")):
            out, run, rows, model = self.sealed(samples=0)
        self.assertEqual(rows[0]["path"], "held_model_error")
        self.assertIsNone(rows[0]["raw_model_text"])
        self.assertTrue(rows[0]["input_delivery"]["model_called"])
        self.assertFalse(run["system_prompt_sent"])

    def test_no_model_mode_is_not_reported_as_a_model_send(self):
        pipe = SimpleNamespace(mode="no-model", system_prompt=None)
        flags = runner._input_delivery(pipe, TurnResult("SYNTHETIC null", "model"))
        self.assertFalse(flags["model_called"])
        self.assertFalse(flags["system_prompt_sent"])

    def test_sealed_console_never_prints_generated_text(self):
        self.sealed()
        self.assertNotIn("SYNTHETIC clean", self.console.getvalue())
        self.assertNotIn("SYNTHETIC raw", self.console.getvalue())

    def test_baseline_leaves_existing_full_artifacts_untouched(self):
        full = self.runs / "SYNTHETIC-held-out-b5-SEALED"
        full.mkdir(parents=True)
        sentinel = full / "synthetic-preserve.txt"
        sentinel.write_bytes(b"SYNTHETIC preexisting full artifact")
        before = sentinel.read_bytes()
        out, run, rows, model = self.sealed()
        self.assertNotEqual(out, full)
        self.assertEqual(sentinel.read_bytes(), before)
        self.assertEqual(list(full.iterdir()), [sentinel])


if __name__ == "__main__":
    unittest.main()
