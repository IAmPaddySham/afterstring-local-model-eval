"""Tightly scoped B6 integrated preflight tests; fictional packets only.

Never import evals.run/Pipeline/backend. The real sealed packet/model paths are
replaced before any loader invocation; no model or network operation is made.
"""
import ast
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest import mock

from evals import preflight_b6 as pf
from evals import held_out_b6 as hb
from harness import release

WRAPPER = Path(__file__).resolve().parents[2]


def digest(b):
    return hashlib.sha256(b).hexdigest()


class IntegratedPreflightTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack(); self.addCleanup(self.stack.close)
        self.temp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(
            prefix="b6-integrated-stub-", dir=WRAPPER / "bak")))
        packet = self.temp / "FICTIONAL-packet"; packet.mkdir()
        self.item = packet / "items.md"; approval = packet / "approval.md"
        freeze = self.temp / "freeze.md"; manifest = packet / "SHA256SUMS"
        text = "# FICTIONAL PENDING packet\n" + "".join(
            f'### B6-{i:02d} · Model\n- Prompt / setup: "FICTIONAL user {i}" (context: FICTIONAL note)\n'
            f'- Retrieval manifest: {"none" if i <= 2 else "v0"}\n' for i in range(1, 19))
        self.item.write_text(text); approval.write_text("FICTIONAL external approval")
        freeze.write_text("FICTIONAL adopted freeze")
        ih, ah = digest(self.item.read_bytes()), digest(approval.read_bytes())
        manifest.write_text(f"{ih}  {packet.name}/{self.item.name}\n{ah}  {packet.name}/{approval.name}\n")
        for key, value in {"PACKET": packet, "HELD_OUT_B6": self.item, "APPROVAL": approval,
                           "FREEZE": freeze, "MANIFEST": manifest, "ITEMS_SHA256": ih,
                           "ITEMS_BYTES": self.item.stat().st_size, "APPROVAL_SHA256": ah,
                           "FREEZE_SHA256": digest(freeze.read_bytes()),
                           "MANIFEST_SHA256": digest(manifest.read_bytes())}.items():
            self.stack.enter_context(mock.patch.object(hb, key, value))
        self.pins = {"files": {"FICTIONAL": "FICTIONAL"}, "model_repo": "FICTIONAL",
                     "model_revision": "FICTIONAL", "weights_sha256_verified": "FICTIONAL",
                     "sampling": {"temperature": 1.0, "top_p": .95, "top_k": 64}}
        self.validator = self.stack.enter_context(mock.patch.object(hb, "validate_frozen_inputs", return_value=self.pins))

    def collect(self):
        with pf.BackendFree():
            return pf.collect_preflight()

    def args(self):
        return SimpleNamespace(mode="baseline", prompt="v0", model=None, items=None, only="",
                               no_retrieval=False, retrieval="v0", no_weight_check=False,
                               samples=5, seed=20261027, max_tokens=400)

    def test_three_arms_metadata_and_no_answer_artifacts(self):
        r = self.collect()
        self.assertEqual(r["items"], 18); self.assertEqual(r["unique_ids"], 18)
        self.assertEqual(r["manifest_counts"], {"v0": 16, "none": 2})
        self.assertEqual(len(r["arms"]), 3)
        self.assertEqual(r["planned_total_records"], 324)
        self.assertEqual(r["answer_records_written"], 0); self.assertEqual(r["model_calls"], 0)
        self.assertEqual(r["arm_runs"], 0); self.assertFalse(r["pipeline_executed"])
        self.assertEqual(len(list(self.temp.rglob("results.jsonl"))), 0)
        self.assertNotIn("FICTIONAL user", json.dumps(r))
        self.assertNotIn("FICTIONAL note", json.dumps(r))

    def test_baseline_routing_excludes_all_wrapper_paths(self):
        plan = pf.arm_plan("baseline", "v0")["routing_plan"]
        self.assertTrue(plan.pop("history_user_context_only"))
        self.assertTrue(all(v is False for v in plan.values()))
        self.assertIsNone(pf.arm_plan("baseline", "v0")["crisis_version"])
        self.assertIsNone(pf.arm_plan("baseline", "v0")["retrieval_version"])

    def test_full_routing_retains_frozen_versions(self):
        for prompt in ("v0", "v5.2.8"):
            plan = pf.arm_plan("full", prompt)
            self.assertEqual(plan["crisis_version"], "v3"); self.assertEqual(plan["retrieval_version"], "v0")
            self.assertTrue(plan["routing_plan"]["system_prompt"])
            self.assertTrue(plan["routing_plan"]["release_path"])
            self.assertFalse(plan["routing_plan"]["history_user_context_only"])

    def test_output_names_separate_and_baseline_suffix_preserved(self):
        names = [pf.planned_dirname("PLANNED", m, p) for m, p in
                 [("baseline", "v0"), ("full", "v0"), ("full", "v5.2.8")]]
        self.assertEqual(len(set(names)), 3)
        self.assertEqual(names[0], "PLANNED-held-out-b6-v0-baseline-SEALED")
        self.assertEqual(names[1], "PLANNED-held-out-b6-v0-SEALED")
        self.assertEqual(names[2], "PLANNED-held-out-b6-v5.2.8-SEALED")

    def test_seed_formula_matches_unchanged_runner_ast(self):
        source = ast.parse((WRAPPER / "repo/evals/run.py").read_text())
        func = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "sample_seed")
        ours = next(n for n in ast.parse(Path(pf.__file__).read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == "sample_seed")
        self.assertEqual(ast.dump(func.body[-1]), ast.dump(ours.body[-1]))
        self.assertEqual(pf.sample_seed(20261027, "FICTIONAL", 1),
                         int(hashlib.sha256(b"20261027:FICTIONAL:1").hexdigest()[:8], 16))

    def test_108_record_schedules_traceable_and_matched_across_arms(self):
        r = self.collect()
        self.assertEqual(len({a["seed_schedule_sha256"] for a in r["arms"]}), 1)
        for a in r["arms"]:
            self.assertEqual((a["greedy_records"], a["sampled_records"], a["expected_records"]), (18, 90, 108))
        self.assertEqual(r["sampling"]["max_tokens"], 400)
        self.assertEqual(r["sampling"]["base_seed"], 20261027)

    def test_synthetic_release_positive_negative_and_pending_state(self):
        with pf.BackendFree():
            r = pf.synthetic_release_checks("full", release)
        self.assertEqual((r["cases"], r["positive"], r["negative"]), (7, 4, 3))
        self.assertTrue(r["q_not_release_checked"])
        self.assertTrue(r["pending_cancellation_and_residual_checked"])

    def test_baseline_never_calls_release_handler(self):
        never = SimpleNamespace(handle=mock.Mock(side_effect=AssertionError("must not call")))
        self.assertEqual(pf.synthetic_release_checks("baseline", never)["status"], "N/A")
        never.handle.assert_not_called()

    def test_release_mismatch_fails_closed(self):
        broken = SimpleNamespace(handle=lambda *a: SimpleNamespace(released=False))
        with self.assertRaises(pf.PreflightError): pf.synthetic_release_checks("full", broken)

    def test_pin_failure_stops_before_packet_load(self):
        self.validator.side_effect = hb.NotApproved("FICTIONAL mismatch")
        with mock.patch.object(hb, "load") as load:
            with self.assertRaises(hb.NotApproved): self.collect()
            load.assert_not_called()

    def test_malformed_fictional_packet_fails_closed(self):
        self.item.write_text("FICTIONAL changed packet")
        with self.assertRaises(hb.NotApproved): self.collect()

    def test_metadata_shape_failure_stops(self):
        with mock.patch.object(hb, "load", return_value=[]):
            with self.assertRaises(pf.PreflightError): self.collect()

    def test_frozen_cli_restrictions_unchanged(self):
        for key, value in [("mode", "no-model"), ("prompt", "v5.2.5"), ("no_retrieval", True),
                           ("no_weight_check", True), ("samples", 4), ("seed", 0), ("max_tokens", 401),
                           ("items", "FICTIONAL"), ("only", "FICTIONAL"), ("retrieval", "v1"), ("model", "FICTIONAL")]:
            args = self.args(); setattr(args, key, value)
            with self.subTest(key=key), self.assertRaises(SystemExit): pf.validate_run_args(args)
        self.assertEqual(pf.validate_run_args(self.args())["mode"], "baseline")

    def test_all_backend_imports_denied_before_loading(self):
        for name in ("harness.model", "harness.pipeline", "evals.run", "mlx", "mlx_lm", "torch"):
            with self.subTest(name=name), pf.BackendFree() as guard:
                with self.assertRaises(pf.BackendExcluded): importlib.import_module(name)
                self.assertNotIn(name, sys.modules)
                self.assertTrue(guard.denied_imports)

    def test_preloaded_backend_sentinel_rejected(self):
        sentinel = ModuleType("harness.model")  # Not a backend import or instance.
        guard = pf.BackendFree()
        with mock.patch.dict(sys.modules, {"harness.model": sentinel}):
            with self.assertRaises(pf.BackendExcluded): guard.__enter__()
        self.assertNotIn(guard, sys.meta_path)

    def test_network_spawn_and_mutation_events_denied_without_operations(self):
        with pf.BackendFree() as guard:
            for event, args in [("socket.connect", (None,)), ("subprocess.Popen", (None,)),
                                ("open", ("FICTIONAL", None, os.O_WRONLY | os.O_CREAT)),
                                ("os.mkdir", ("FICTIONAL",))]:
                with self.subTest(event=event), self.assertRaises(pf.BackendExcluded):
                    guard.audit(event, args)

    def test_main_reports_exclusion_and_only_metadata(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out): code = pf.main([])
        self.assertEqual(code, 0)
        r = json.loads(out.getvalue())
        self.assertEqual(r["backend_exclusion"]["forbidden_modules_loaded"], [])
        self.assertTrue(r["backend_exclusion"]["import_guard_active_during_checks"])
        self.assertTrue(r["backend_exclusion"]["network_process_and_file_write_guard_active"])
        self.assertNotIn("FICTIONAL user", out.getvalue())

    def test_main_error_does_not_leak_exception_content(self):
        out = io.StringIO()
        with mock.patch.object(pf, "collect_preflight", side_effect=ValueError("FICTIONAL sensitive body")), \
                contextlib.redirect_stdout(out):
            code = pf.main([])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(out.getvalue())["status"], "HOLD")
        self.assertNotIn("sensitive", out.getvalue())

    def test_runner_wiring_shared_but_generation_functions_unchanged(self):
        parse = lambda p: {n.name: n for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef)}
        current = parse(WRAPPER / "repo/evals/run.py")
        prior = parse(WRAPPER / "bak/run.py.bak-20261107-b6-integrated")
        changed = [k for k in prior if ast.dump(prior[k], include_attributes=False) !=
                   ast.dump(current[k], include_attributes=False)]
        self.assertEqual(changed, ["_validate_b6_args", "run_held_out_b6"])
        self.assertEqual(ast.dump(current["_run_sealed"]), ast.dump(prior["_run_sealed"]))
        self.assertTrue(any(isinstance(n, ast.Name) and n.id == "validate_run_args" for n in ast.walk(current["_validate_b6_args"])))
        self.assertTrue(any(isinstance(n, ast.Attribute) and n.attr == "base_dirname" for n in ast.walk(current["run_held_out_b6"])))

    def test_new_pure_check_source_pins_match(self):
        root = WRAPPER / "repo"
        for name in ("evals/run.py", "evals/preflight_b6.py", "harness/release.py", "harness/pipeline.py"):
            self.assertEqual(digest((root / name).read_bytes()), hb.FROZEN_FILES[name])
