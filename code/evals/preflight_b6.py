"""Integrated B6 metadata/routing + SYNTHETIC release checks; no backend imports.

Run only with separate authority: python -B -m evals.preflight_b6.
Shared B6 argument/directory functions are also used by the real runner; that
runner is never imported here. This is not a model/answer run or a safety proof.
"""
import argparse
from contextlib import AbstractContextManager
import hashlib
import json
import os
import sys

FORBIDDEN = ("harness.model", "harness.pipeline", "evals.run", "mlx", "mlx_lm",
             "torch", "transformers", "huggingface_hub", "tensorflow", "jax")


class PreflightError(ValueError):
    pass


class BackendExcluded(PreflightError):
    pass


def _forbidden(name):
    return any(name == p or name.startswith(p + ".") for p in FORBIDDEN)


class BackendFree(AbstractContextManager):
    """Fail closed on preloaded/backdoor backend imports, network, spawn or writes.

    Active for this invocation only; no environment/package/backend changes.
    CLI imports project modules only after entering this guard.
    """
    def __init__(self):
        self.active = False
        self.denied_imports = []

    def check(self):
        if any(_forbidden(name) for name in sys.modules):
            raise BackendExcluded("backend module already present")

    def find_spec(self, fullname, path=None, target=None):
        if self.active and _forbidden(fullname):
            self.denied_imports.append(fullname)
            raise BackendExcluded("backend import excluded")
        return None

    def audit(self, event, args):
        if not self.active:
            return
        if event == "import" and _forbidden(args[0]):
            self.denied_imports.append(args[0])
            raise BackendExcluded("backend import excluded")
        if event.startswith("socket.") or event in ("subprocess.Popen", "os.system", "os.posix_spawn", "os.exec"):
            raise BackendExcluded("network/process operation excluded")
        if event == "open" and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            raise BackendExcluded("file write excluded")
        if event in ("os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.symlink", "os.link", "os.truncate"):
            raise BackendExcluded("filesystem mutation excluded")

    def __enter__(self):
        self.check()
        if not sys.dont_write_bytecode:
            raise PreflightError("bytecode must be disabled")
        self.active = True
        sys.meta_path.insert(0, self)
        sys.addaudithook(self.audit)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self.check()
        finally:
            self.active = False
            if self in sys.meta_path:
                sys.meta_path.remove(self)
        return False


def arm_plan(mode, prompt):
    if mode not in ("baseline", "full") or prompt not in ("v0", "v5.2.8"):
        raise PreflightError("not a frozen B6 arm")
    full = mode == "full"
    return {"mode": mode, "selected_prompt_version": prompt,
            "routing_plan": {"system_prompt": full, "retrieval_eligible": full,
                             "crisis": full, "gate": full, "release_path": full,
                             "history_user_context_only": not full},
            "crisis_version": "v3" if full else None,
            "retrieval_version": "v0" if full else None}


def validate_run_args(args):
    """Exact existing B6 CLI restrictions, shared with evals.run; no defaults changed."""
    if (args.mode not in ("baseline", "full") or args.items or args.only or args.no_retrieval
            or args.retrieval != "v0" or args.no_weight_check
            or args.samples != 5 or args.seed != 20261027 or args.max_tokens != 400
            or args.model not in (None, "gemma4-e4b-it-4bit-mlx")
            or args.prompt not in ("v0", "v5.2.8")):
        raise SystemExit("B6 requires frozen baseline/full, v0/v5.2.8, retrieval v0, pinned E4B, "
                         "greedy + 5 samples, seed 20261027, max_tokens 400; no subsets or weight-check bypass")
    return arm_plan(args.mode, args.prompt)


def base_dirname(stamp, prompt):
    if prompt not in ("v0", "v5.2.8"):
        raise PreflightError("not a frozen B6 prompt selection")
    return f"{stamp}-held-out-b6-{prompt}-SEALED"


def planned_dirname(stamp, mode, prompt):
    arm_plan(mode, prompt)
    name = base_dirname(stamp, prompt)
    return name[:-len("-SEALED")] + "-baseline-SEALED" if mode == "baseline" else name


def sample_seed(base, item_id, k):
    """Same unchanged D-027 formula as evals.run; tested by AST comparison."""
    return int(hashlib.sha256(f"{base}:{item_id}:{k}".encode()).hexdigest()[:8], 16)


def synthetic_release_checks(mode, release):
    """Only fictional control strings/pending labels, never B6 item text."""
    if mode == "baseline":
        return {"status": "N/A", "scope": "bare baseline has no release path", "cases": 0}
    if mode != "full":
        raise PreflightError("invalid release-check mode")
    cases = (("stop", True), ("quit", True), ("cancel everything", True),
             ("Please stop. Stop now!", True), ("q", False),
             ("Stop, I need help", False), ("Even if I say stop, continue", False))
    pending = [("FICTIONAL cancellable", True), ("FICTIONAL external", False)]
    for text, expected in cases:
        r = release.handle(text, pending)
        if bool(r.released) != expected:
            raise PreflightError("synthetic release classification mismatch")
        if expected and (r.cancelled != ["FICTIONAL cancellable"]
                         or r.still_pending != ["FICTIONAL external"]
                         or r.path != "release.hard_path" or not r.text):
            raise PreflightError("synthetic release pending-state mismatch")
        if pending != [("FICTIONAL cancellable", True), ("FICTIONAL external", False)]:
            raise PreflightError("synthetic pending input mutated")
    return {"status": "PASS", "scope": "synthetic pure release.handle only; not Pipeline/model behavior",
            "cases": len(cases), "positive": 4, "negative": 3,
            "pending_cancellation_and_residual_checked": True, "q_not_release_checked": True}


def collect_preflight():
    """Called only within BackendFree; no outputs, answers or key material created."""
    from evals import held_out_b6 as hb
    from harness import release
    pins = hb.validate_frozen_inputs()
    items = hb.load()
    required = {"id", "kind", "text", "context_note", "manifest"}
    if (len(items) != 18 or len({i["id"] for i in items}) != 18
            or any(set(i) != required or not all(isinstance(v, str) for v in i.values())
                   or i["kind"] != "Model" or not i["text"].strip() for i in items)):
        raise PreflightError("sealed metadata shape mismatch")
    trace = [[i["id"], k, None if k == 0 else sample_seed(20261027, i["id"], k)]
             for i in items for k in range(6)]
    trace_hash = hashlib.sha256(json.dumps(trace, separators=(",", ":")).encode()).hexdigest()
    arms = []
    for mode, prompt in (("baseline", "v0"), ("full", "v0"), ("full", "v5.2.8")):
        args = argparse.Namespace(mode=mode, prompt=prompt, model=None, items=None, only="",
                                  no_retrieval=False, retrieval="v0", no_weight_check=False,
                                  samples=5, seed=20261027, max_tokens=400)
        plan = validate_run_args(args)
        plan.update({"planned_output_name": planned_dirname("PLANNED", mode, prompt),
                     "greedy_records": 18, "sampled_records": 90, "expected_records": len(trace),
                     "seed_schedule_sha256": trace_hash,
                     "release_checks": synthetic_release_checks(mode, release)})
        arms.append(plan)
    if len({a["planned_output_name"] for a in arms}) != 3:
        raise PreflightError("arm output namespace collision")
    return {"status": "PASS", "scope": "integrated backend-free routing/metadata + SYNTHETIC release checks",
            "not_ready": True, "model_behavior_validated": False, "pipeline_executed": False,
            "model_calls": 0, "arm_runs": 0, "answer_records_written": 0,
            "items": len(items), "unique_ids": len({i["id"] for i in items}),
            "field_names": sorted(required), "all_fields_strings": True,
            "nonempty_context_notes": sum(bool(i["context_note"]) for i in items),
            "manifest_counts": {m: sum(i["manifest"] == m for i in items) for m in ("v0", "none")},
            "arms": arms, "planned_total_records": sum(a["expected_records"] for a in arms),
            "sampling": {"base_seed": 20261027, "samples_per_item": 5, "max_tokens": 400,
                         "settings": pins["sampling"], "greedy_first_and_restore": "runner static contract; no decoding executed"},
            "frozen_inputs": pins, "item_sha256_verified": hb.ITEMS_SHA256,
            "item_bytes": hb.ITEMS_BYTES, "approval_sha256_verified": hb.APPROVAL_SHA256,
            "freeze_sha256_verified": hb.FREEZE_SHA256, "seal_manifest_sha256_verified": hb.MANIFEST_SHA256,
            "loader_sha256": hb.config.sha256_file(hb.__file__),
            "bytecode_disabled": sys.dont_write_bytecode}


def main(argv=None):
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    try:
        with BackendFree() as guard:
            result = collect_preflight()
            guard.check()
            result["backend_exclusion"] = {"forbidden_modules_loaded": [],
                "denied_import_attempts": list(guard.denied_imports),
                "import_guard_active_during_checks": guard.active,
                "network_process_and_file_write_guard_active": guard.active,
                "project_modules_imported": sorted(n for n in sys.modules if n == "harness" or
                    n.startswith("harness.") or n == "evals" or n.startswith("evals."))}
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        # Never print exception values/tracebacks that could expose sealed content.
        print(json.dumps({"status": "HOLD", "error_type": type(exc).__name__,
                          "message": "preflight failed closed; no answer/model run authorized"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
