"""B6 fictional-fixture tests only: no real sealed data, model, network or grading.

Every production loader path/pin is patched before loader calls. Every runner
backend/weight preflight is mocked before synthetic execution. Temporary files
stay in this wrapper's bak directory. An audit hook denies protected-data reads,
MLX/download imports, subprocesses and network operations in this test process.
"""
import contextlib
from contextvars import ContextVar
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from evals import held_out_b6 as hb
from evals import run as runner
from harness.pipeline import Pipeline, Turn, TurnResult

REAL_WRAPPER = Path(__file__).resolve().parents[2]
PROTECTED = [REAL_WRAPPER / "B6_SEALED_ITEMS_2026-11-07",
             REAL_WRAPPER / "repo/runs", REAL_WRAPPER / "repo/evals/held-out",
             REAL_WRAPPER / "repo/evals/grading"]


# Python's open audit event omits dir_fd. Preserve its actual target through the
# os.open call instead of guessing cwd during TemporaryDirectory's fd cleanup.
_OPEN_TARGET = ContextVar("b6_open_audit_target", default=None)
_ORIGINAL_OS_OPEN = os.open


def _open_with_audit_path(path, flags, mode=0o777, *, dir_fd=None):
    target = Path(os.fsdecode(path))
    if not target.is_absolute():
        if dir_fd is None:
            target = Path.cwd() / target
        else:
            if sys.platform != "darwin":
                raise AssertionError("B6 dir_fd audit resolution requires Darwin F_GETPATH")
            # Public Darwin sys/fcntl.h: F_GETPATH=50. Failure is closed, never
            # a fallback to cwd or an exception to protected-path checking.
            raw = fcntl.fcntl(dir_fd, getattr(fcntl, "F_GETPATH", 50), bytes(1024))
            base = Path(os.fsdecode(raw.split(b"\0", 1)[0]))
            if not base.is_absolute():
                raise AssertionError("B6 dir_fd audit resolution did not yield an absolute path")
            target = base / target
    target = target.resolve(strict=False)  # Normalize traversal/symlinks before checking.
    token = _OPEN_TARGET.set(target)
    try:
        _safety_audit("open", (str(target), None, flags))  # Deny before the underlying syscall.
        return _ORIGINAL_OS_OPEN(path, flags, mode, dir_fd=dir_fd)
    finally:
        _OPEN_TARGET.reset(token)


def _safety_audit(event, args):
    if event == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = _OPEN_TARGET.get() or Path(os.fsdecode(args[0])).resolve(strict=False)
        if args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            if not str(path).startswith(str(REAL_WRAPPER / "bak" / "b6-stub-")):
                raise AssertionError("B6 stub suite refuses writes outside fictional temp fixtures")
        if any(path == p or p in path.parents for p in PROTECTED) or ".cache/huggingface" in str(path):
            raise AssertionError("B6 stub suite refuses protected data/weights")
    if event.startswith("socket.") or event == "subprocess.Popen":
        raise AssertionError("B6 stub suite refuses network/subprocess operations")
    if event == "import" and args[0].split(".")[0] in {"mlx", "mlx_lm", "huggingface_hub"}:
        raise AssertionError("B6 stub suite refuses model/download imports")


sys.addaudithook(_safety_audit)
os.open = _open_with_audit_path  # Test-process only; the hook remains enabled for every open.


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fictional_packet():
    return "# FICTIONAL packet PENDING\n" + "".join(
        f'### B6-{i:02d} · Model\n- Prompt / setup: "FICTIONAL user {i}" (context: FICTIONAL note)\n'
        f'- Retrieval manifest: {"none" if i == 1 else "v0"}\n'
        '- Tags: FICTIONAL ONLY\n- Approval (batch 6): PENDING\n\n'
        for i in range(1, 19))


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = Path(self.stack.enter_context(tempfile.TemporaryDirectory(
            prefix="b6-stub-", dir=REAL_WRAPPER / "bak")))
        self.packet = self.temp / "FICTIONAL-packet"
        self.packet.mkdir()
        self.root = self.temp / "repo"
        self.root.mkdir()
        self.items = self.packet / "B6_ITEMS_DRAFT.md"
        self.approval = self.packet / "APPROVAL_AND_SEAL_2026-11-07.md"
        self.manifest = self.packet / "SHA256SUMS"
        self.freeze = self.temp / "FICTIONAL-freeze.md"
        self.items.write_text(fictional_packet())
        self.approval.write_text("FICTIONAL external approved seal")
        self.freeze.write_text("FICTIONAL adopted freeze")
        for key, value in {"ROOT": self.root, "WRAPPER": self.temp, "PACKET": self.packet,
                           "HELD_OUT_B6": self.items, "APPROVAL": self.approval,
                           "MANIFEST": self.manifest, "FREEZE": self.freeze,
                           "ITEMS_SHA256": digest(self.items.read_bytes()),
                           "ITEMS_BYTES": self.items.stat().st_size,
                           "APPROVAL_SHA256": digest(self.approval.read_bytes()),
                           "FREEZE_SHA256": digest(self.freeze.read_bytes()),
                           "MANIFEST_SHA256": "FICTIONAL"}.items():
            self.patch(hb, key, value)
        self.repin()
        self.input = self.root / "FICTIONAL-input.bin"
        self.input.write_bytes(b"FICTIONAL frozen config")
        self.patch(hb, "FROZEN_FILES", {self.input.name: digest(self.input.read_bytes())})
        snapshot = self.temp / hb.MODEL_REVISION
        snapshot.mkdir()
        self.weight = snapshot / "model.safetensors"
        self.weight.write_bytes(b"FICTIONAL weights, NOT a real model")
        self.patch(hb, "WEIGHTS_SHA256", digest(self.weight.read_bytes()))
        self.entry = {"id": hb.MODEL_ID, "repo": hb.MODEL_REPO, "revision": hb.MODEL_REVISION,
                      "sampling": dict(hb.SAMPLING), "local_path": str(snapshot),
                      "weights": {"file": "model.safetensors", "bytes": self.weight.stat().st_size,
                                  "sha256": hb.WEIGHTS_SHA256}}
        self.entry_mock = self.patch(hb.config, "model_entry", mock.Mock(return_value=self.entry))
        self.console = self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def patch(self, obj, key, value):
        return self.stack.enter_context(mock.patch.object(obj, key, value))

    def repin(self):
        hb.ITEMS_SHA256 = digest(self.items.read_bytes())
        hb.ITEMS_BYTES = self.items.stat().st_size
        self.manifest.write_text(f"{hb.ITEMS_SHA256}  {self.packet.name}/{self.items.name}\n"
                                 f"{hb.APPROVAL_SHA256}  {self.packet.name}/{self.approval.name}\n")
        hb.MANIFEST_SHA256 = digest(self.manifest.read_bytes())

    def alter_packet(self, before, after):
        self.items.write_text(self.items.read_text().replace(before, after, 1))
        self.repin()  # Only fictional fixture pins are repinned, never production pins.


class LoaderTests(FixtureCase):
    def test_external_seal_supersedes_fictional_pending(self):
        items = hb.load()
        self.assertEqual([x["id"] for x in items], list(hb.IDS))
        self.assertEqual(items[0]["text"], "FICTIONAL user 1")
        self.assertEqual(items[0]["context_note"], "FICTIONAL note")
        self.assertEqual(items[0]["manifest"], "none")
        self.assertNotIn("Tags", items[0])

    def test_wrong_item_hash_fails_closed(self):
        self.items.write_text("FICTIONAL tamper")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_wrong_approval_hash_fails_closed(self):
        self.approval.write_text("FICTIONAL tamper")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_wrong_freeze_hash_fails_closed(self):
        self.freeze.write_text("FICTIONAL tamper")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_wrong_manifest_hash_fails_closed(self):
        self.manifest.write_text("FICTIONAL tamper")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_missing_manifest_fails_closed(self):
        self.manifest.unlink()
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_duplicate_manifest_entries_fail_closed(self):
        self.manifest.write_text(self.manifest.read_text().splitlines()[0] + "\n" +
                                 self.manifest.read_text().splitlines()[0] + "\n")
        hb.MANIFEST_SHA256 = digest(self.manifest.read_bytes())
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_missing_id_fails_closed(self):
        text = self.items.read_text(); self.items.write_text(text[:text.rfind("### B6-18")]); self.repin()
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_duplicate_id_fails_closed(self):
        self.alter_packet("### B6-18", "### B6-17")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_unexpected_id_fails_closed(self):
        self.alter_packet("### B6-18", "### B6-99")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_incompatible_item_header_fails_closed(self):
        self.alter_packet("B6-01 · Model", "B6-01 · Harness")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_missing_prompt_fails_closed(self):
        self.alter_packet("- Prompt / setup:", "- FICTIONAL removed:")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_duplicate_retrieval_field_fails_closed(self):
        self.alter_packet("- Retrieval manifest: none", "- Retrieval manifest: none\n- Retrieval manifest: v0")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_incompatible_retrieval_fails_closed(self):
        self.alter_packet("- Retrieval manifest: none", "- Retrieval manifest: v1")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_invalid_quoted_prompt_fails_closed(self):
        self.alter_packet('"FICTIONAL user 1"', "FICTIONAL unquoted user")
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_wrong_size_fails_closed(self):
        hb.ITEMS_BYTES += 1
        with self.assertRaises(hb.NotApproved): hb.load()

    def test_frozen_input_and_fake_weight_verification(self):
        pins = hb.validate_frozen_inputs()
        self.assertEqual(pins["weights_sha256_verified"], digest(self.weight.read_bytes()))
        self.assertEqual(pins["sampling"], hb.SAMPLING)

    def test_changed_frozen_input_fails_before_model_entry(self):
        self.input.write_bytes(b"FICTIONAL changed config")
        with self.assertRaises(hb.NotApproved): hb.validate_frozen_inputs()
        self.entry_mock.assert_not_called()

    def test_missing_frozen_input_fails_closed(self):
        self.input.unlink()
        with self.assertRaises(hb.NotApproved): hb.validate_frozen_inputs()

    def test_changed_fake_weights_fail_closed(self):
        self.weight.write_bytes(b"FICTIONAL tamper")
        with self.assertRaises(hb.NotApproved): hb.validate_frozen_inputs()

    def test_incompatible_model_and_sampling_fail_closed(self):
        for key, bad in [("id", "FICTIONAL wrong model"), ("revision", "FICTIONAL wrong revision"),
                         ("sampling", {"temperature": 0.2}), ("local_path", "FICTIONAL absent snapshot")]:
            with self.subTest(key=key), mock.patch.dict(self.entry, {key: bad}):
                with self.assertRaises(hb.NotApproved): hb.validate_frozen_inputs()


class StubModel:
    loaded = True
    instances = []

    def __init__(self, model_id=None):
        self.entry = {"sampling": dict(hb.SAMPLING)}
        self.calls, self.seeds, self.restores = [], [], 0
        self.instances.append(self)

    def generate(self, messages, max_tokens):
        self.calls.append(([dict(m) for m in messages], max_tokens))
        return SimpleNamespace(text="FICTIONAL clean", to_dict=lambda: {
            "raw_text": "FICTIONAL raw", "finish_reason": "stop"})

    def use_sampling(self, seed, settings): self.seeds.append(seed)
    def use_greedy(self): self.restores += 1
    def identity(self): return {"backend": "FICTIONAL stub"}


class FullStub:
    def __init__(self, mode, model, max_tokens, **kw):
        assert mode == "full" and kw["gate"] is not None and kw["ledger"] is not None
        assert kw["retrieval"] is True and kw["retrieval_manifest"] is None
        self.mode, self.model = mode, model
        self.system_prompt = "FICTIONAL system " + kw["prompt_version"]
        self.retriever = SimpleNamespace(manifest_sha256="FICTIONAL", chunks=[], skipped=[], error=None)

    def run(self, turns):
        g = self.model.generate([{"role": "system", "content": self.system_prompt},
                                 {"role": "user", "content": turns[0].text}], 400)
        return [TurnResult(output=g.text + " FICTIONAL wrapper", model_text=g.text,
                           gen=g.to_dict(), path="model", gate={"decision": "HOLD"},
                           optics={"verdict": "ALLOW"}, crisis={"fired": True, "matched": "FICTIONAL"},
                           retrieval={"used": ["FICTIONAL source"]})]


class RunnerTests(FixtureCase):
    def args(self, mode="baseline", prompt="v0"):
        return SimpleNamespace(mode=mode, model=None, prompt=prompt, items=None, only="",
                               no_retrieval=False, retrieval="v0", no_weight_check=False,
                               samples=5, seed=20261027, max_tokens=400, allow_dirty=False)

    def test_cli_dispatches_only_adopted_arms(self):
        for mode, prompt in [("baseline", "v0"), ("full", "v0"), ("full", "v5.2.8")]:
            with self.subTest(mode=mode, prompt=prompt), mock.patch.object(runner, "git_info", return_value={"dirty": False}),                     mock.patch.object(runner, "run_held_out_b6", return_value="FICTIONAL dispatch"):
                self.assertEqual(runner.main(["--mode", mode, "--prompt", prompt, "--held-out-b6", "--samples", "5"]),
                                 "FICTIONAL dispatch")

    def test_incompatible_args_fail_before_dispatch(self):
        invalid = [("mode", "no-model"), ("items", "FICTIONAL"), ("only", "B6-01"),
                   ("no_retrieval", True), ("retrieval", "v1"), ("no_weight_check", True),
                   ("samples", 0), ("samples", 6), ("seed", 1), ("max_tokens", 401),
                   ("model", "FICTIONAL"), ("prompt", "v5.2.5")]
        for key, value in invalid:
            with self.subTest(key=key):
                args = self.args(); setattr(args, key, value)
                with self.assertRaises(SystemExit): runner._validate_b6_args(args)

    def test_existing_sealed_flags_remain_exclusive(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for flag in ["--held-out", "--held-out-b2", "--held-out-b3", "--held-out-b4", "--held-out-b5"]:
                with self.subTest(flag=flag), self.assertRaises(SystemExit):
                    runner.main(["--mode", "baseline", "--held-out-b6", flag, "--samples", "5"])

    def test_existing_b1_to_b5_dispatch_preserved(self):
        for flag, target in [("--held-out", "run_held_out"), ("--held-out-b2", "run_held_out_b2"),
                             ("--held-out-b3", "run_held_out_b3"), ("--held-out-b4", "run_held_out_b4"),
                             ("--held-out-b5", "run_held_out_b5")]:
            for mode in ("baseline", "full"):
                with self.subTest(flag=flag, mode=mode), mock.patch.object(runner, "git_info", return_value={"dirty": False}),                         mock.patch.object(runner, target, return_value="FICTIONAL old dispatch"):
                    self.assertEqual(runner.main(["--mode", mode, flag]), "FICTIONAL old dispatch")

    def test_dirty_guard_not_bypassed(self):
        with mock.patch.object(runner, "git_info", return_value={"dirty": True, "changes": ["FICTIONAL dirty source"]}),                 mock.patch.object(runner, "run_held_out_b6") as dispatch:
            with self.assertRaises(SystemExit):
                runner.main(["--mode", "baseline", "--held-out-b6", "--samples", "5"])
            dispatch.assert_not_called()

    def test_pin_failure_never_reaches_sealed_runner(self):
        with mock.patch.object(hb, "validate_frozen_inputs", side_effect=hb.NotApproved("FICTIONAL mismatch")),                 mock.patch.object(hb, "load") as load, mock.patch.object(runner, "_run_sealed") as sealed:
            with self.assertRaises(hb.NotApproved): runner.run_held_out_b6(self.args(), {"dirty": False})
            load.assert_not_called(); sealed.assert_not_called()

    def execute_stub(self, mode, prompt="v0"):
        # Real loader is used only on patched fictional packet; no real packet is opened.
        items = hb.load()
        system = self.root / "FICTIONAL-system.txt"; system.write_text("FICTIONAL selected system")
        for key, value in {"PROJECT_ROOT": self.root, "RUNS": self.root / "runs",
                           "FULL_PROMPTS": {"v0": system, "v5.2.8": system},
                           "RULES_YAML": system, "CRISIS_YAML": system}.items():
            self.patch(runner.config, key, value)
        self.patch(runner, "tree_hash", mock.Mock(return_value={"sha256": "FICTIONAL", "files": 0}))
        self.patch(runner, "identity", mock.Mock(return_value={"weight_hash": "FICTIONAL"}))
        gate = self.patch(runner, "GateRb", mock.Mock(return_value=SimpleNamespace(backend="FICTIONAL")))
        ledger = self.stack.enter_context(mock.patch("harness.approvals.ApprovalsLedger", return_value=SimpleNamespace(records=lambda: [])))
        self.stack.enter_context(mock.patch("harness.model.MLXBackend", StubModel))
        self.patch(hb, "validate_frozen_inputs", mock.Mock(return_value={"FICTIONAL": True}))
        cls = FullStub if mode == "full" else Pipeline
        StubModel.instances = []
        with mock.patch.object(runner, "Pipeline", cls):
            runner.run_held_out_b6(self.args(mode, prompt), {"dirty": False})
        folders = list((self.root / "runs").iterdir()); self.assertEqual(len(folders), 1)
        out = folders[0]; run = json.loads((out / "run.json").read_text())
        rows = [json.loads(s) for s in (out / "results.jsonl").read_text().splitlines()]
        self.assertEqual(len(items), 18); self.assertEqual(len(rows), 108)
        model = StubModel.instances[0]
        self.assertEqual(len(model.calls), 108); self.assertEqual(len(model.seeds), 90)
        self.assertEqual(model.restores, 18)
        for item in items:
            subset = [r for r in rows if r["id"] == item["id"]]
            self.assertEqual([r["run"] for r in subset], ["greedy"] + [f".s{k:02d}" for k in range(1, 6)])
            self.assertEqual([r["seed"] for r in subset[1:]], [runner.sample_seed(20261027, item["id"], k) for k in range(1, 6)])
        self.assertEqual(run["items_file"], os.path.relpath(self.items, self.root))
        self.assertEqual(run["batch"], 6)
        return run, rows, model, gate, ledger

    def test_baseline_108_fake_answers_have_no_wrapper_inputs(self):
        run, rows, model, gate, ledger = self.execute_stub("baseline")
        gate.assert_not_called(); ledger.assert_not_called()
        self.assertTrue(all([m["role"] for m in messages] == ["user"] for messages, _ in model.calls))
        self.assertTrue(all(messages[0]["content"].startswith("[FICTIONAL note]\nFICTIONAL user") for messages, _ in model.calls))
        self.assertFalse(run["system_prompt_sent"]); self.assertFalse(run["retrieval_sent"])
        self.assertIsNone(run["full_prompt_sent_sha256"])
        self.assertTrue(all(r["gate"] is None and r["retrieval"] is None and not r["crisis_fired"] for r in rows))
        self.assertTrue(all(r["raw_model_text"] == "FICTIONAL raw" for r in rows))

    def test_full_v0_108_fake_answers_preserve_wiring(self):
        run, rows, model, gate, ledger = self.execute_stub("full")
        gate.assert_called_once(); ledger.assert_called_once()
        self.assertTrue(run["system_prompt_sent"]); self.assertTrue(run["retrieval_sent"])
        self.assertTrue(all(r["raw_model_text"] == "FICTIONAL raw" and r["model_text"] == "FICTIONAL clean"
                            and r["output"].endswith("FICTIONAL wrapper") for r in rows))

    def test_full_candidate_108_fake_answers_preserve_selection(self):
        run, rows, model, gate, ledger = self.execute_stub("full", "v5.2.8")
        self.assertEqual(run["full_prompt_version"], "v5.2.8")
        self.assertTrue(all(messages[0]["content"].endswith("v5.2.8") for messages, _ in model.calls))

    def test_baseline_history_plus_user_and_note_only(self):
        system = self.root / "FICTIONAL-system.txt"
        self.patch(runner.config, "FULL_PROMPTS", {"v0": system})
        model = StubModel()
        with mock.patch("harness.pipeline.InputGuard", side_effect=AssertionError("no guard")),                 mock.patch("harness.pipeline.CrisisResources", side_effect=AssertionError("no crisis")),                 mock.patch("harness.pipeline.Retriever", side_effect=AssertionError("no retrieval")),                 mock.patch("harness.pipeline.GateRb", side_effect=AssertionError("no gate")):
            pipe = Pipeline("baseline", model, prompt_version="v0")
            pipe.run([Turn("FICTIONAL user", context_note="FICTIONAL note")],
                     fixed_history=[("user", "FICTIONAL history"), ("assistant", "FICTIONAL prior")])
        self.assertEqual(model.calls[0][0], [{"role": "user", "content": "FICTIONAL history"},
                          {"role": "assistant", "content": "FICTIONAL prior"},
                          {"role": "user", "content": "[FICTIONAL note]\nFICTIONAL user"}])


class CleanupAuditRegressionTests(FixtureCase):
    """Probe denied paths before mocked syscalls; never open real run outputs."""

    def test_absolute_and_cwd_relative_real_runs_still_denied(self):
        paths = [REAL_WRAPPER / "repo/runs/FICTIONAL-not-opened",
                 Path("runs/FICTIONAL-not-opened")]
        with mock.patch.object(sys.modules[__name__], "_ORIGINAL_OS_OPEN") as underlying:
            for path in paths:
                for flags in (os.O_RDONLY, os.O_WRONLY | os.O_CREAT):
                    with self.subTest(path=str(path), flags=flags), self.assertRaises(AssertionError):
                        os.open(path, flags)
            underlying.assert_not_called()
        self.assertIsNone(_OPEN_TARGET.get())

    def test_dirfd_relative_real_runs_still_denied(self):
        # Fake descriptor metadata stands for the real repo; no protected fd is opened.
        raw = os.fsencode(REAL_WRAPPER / "repo") + b"\0"
        with mock.patch.object(fcntl, "fcntl", return_value=raw), \
                mock.patch.object(sys.modules[__name__], "_ORIGINAL_OS_OPEN") as underlying:
            for flags in (os.O_RDONLY, os.O_WRONLY | os.O_CREAT):
                with self.subTest(flags=flags), self.assertRaises(AssertionError):
                    os.open("runs/FICTIONAL-not-opened", flags, dir_fd=123)
            underlying.assert_not_called()
        self.assertIsNone(_OPEN_TARGET.get())

    def test_synthetic_dirfd_runs_allowed_and_cleanup_succeeds(self):
        nested = self.root / "runs"
        nested.mkdir()
        fd = os.open(self.root, os.O_RDONLY)
        try:
            child = os.open("runs", os.O_RDONLY, dir_fd=fd)
            os.close(child)
        finally:
            os.close(fd)
        # FixtureCase's ordinary TemporaryDirectory cleanup traverses this nested
        # runs directory through the same wrapper; no special cleanup bypass.
        self.assertIsNone(_OPEN_TARGET.get())

    def test_unresolvable_dirfd_fails_closed_without_syscall(self):
        with mock.patch.object(fcntl, "fcntl", side_effect=OSError("FICTIONAL unresolved fd")), \
                mock.patch.object(sys.modules[__name__], "_ORIGINAL_OS_OPEN") as underlying:
            with self.assertRaises(OSError):
                os.open("runs", os.O_RDONLY, dir_fd=123)
            underlying.assert_not_called()
        self.assertIsNone(_OPEN_TARGET.get())

    def test_dirfd_traversal_to_real_runs_still_denied(self):
        relative = os.path.relpath(REAL_WRAPPER / "repo/runs/FICTIONAL-not-opened", self.root)
        with mock.patch.object(fcntl, "fcntl", return_value=os.fsencode(self.root) + b"\0"), \
                mock.patch.object(sys.modules[__name__], "_ORIGINAL_OS_OPEN") as underlying:
            for flags in (os.O_RDONLY, os.O_WRONLY | os.O_CREAT):
                with self.subTest(flags=flags), self.assertRaises(AssertionError):
                    os.open(relative, flags, dir_fd=123)
            underlying.assert_not_called()
        self.assertIsNone(_OPEN_TARGET.get())
