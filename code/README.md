# Code: a snapshot of the harness source

*Prepared by Grok Bot (Operator) on 9 Nov 2026; approved by Paddy Sham.*

**License:** Apache License 2.0 (see `../LICENSE` and `../NOTICE`). © 2026 Paddy Sham. The documents, results and item text elsewhere in this release are CC BY 4.0.

## What this is

A file-by-file copy of the harness source as it stood on 9 November 2026, after the B7 crisis-trigger fix. The repository it came from is at commit `c535de2` plus uncommitted work, so this snapshot does not match any single commit. Nothing was run, changed or reformatted to make it, apart from the scrub described below.

**Included (107 files, plus this README):**

| Path | Files | What |
|---|---|---|
| `harness/*.py` | 12 | The harness: pipeline, crisis check, release path, retrieval, input guard, gate adapter, model loader, config |
| `evals/*.py` | 12 | The runner (`run.py`), held-out loaders, B6 preflight, scoring, development items |
| `tests/*.py` | 46 | 45 test modules plus `__init__.py` |
| `configs/` | 34 | Prompts v0–v5.2.8, crisis configs v1–v4 with their sha files, retrieval allowlists and manifests, input-filter rules, gate config, `models.yaml`, a configs README |
| `run_tests.sh`, `requirements.lock` | 2 | Test runner and pinned dependencies |
| `permod.py` | 1 | The Builder's per-module test runner (B7 amendment A1), added 9 Nov 2026 on Paddy's word. Standard library only; it needs `.venv/bin/python` (see §2 of the usage guide) and `tests/`, and writes `<out>.log` and `<out>.json`, refusing to overwrite them |

**Not included:** git history; the virtual environment; backup files (`*.bak*`), `__pycache__` and `.DS_Store`; `runs/` (every run output, `results.jsonl` and `run.json`, which carry local paths); `evals/held-out/` (held-out record files with grading lines, and seal pins); `evals/grading/` (grade files, blind sheets and sealed keys); `evals/diagnostic/`, `drafts/`, `proposals/` and `practice/`; `docs/`, `notes/`, `research/`, `reports/` and `scratch/`; the repository README, CHANGELOG and `MANIFEST.sha256`; anything from the project folder above the repository (including the sealed B6 packet); the retrieval corpus; the Ruby gate; and model weights.

**Scrub.** Every copied file was searched for the local home path and user name: none was found, so no placeholder was needed (the record's local paths live in run folders, which are excluded). No `.env` file, key or token is included. Words such as "diary", "family" and "tesla" appear only in deny-lists that keep such material out of retrieval, in crisis patterns, in model metadata ("family: Gemma 4") and in test fixtures.

## Known issues (read before running anything)

1. **The full test suite fails.** `tests/test_held_out_b6.py` installs a process-wide audit hook and replaces `os.open` when it is imported (lines 76–79). `./run_tests.sh` loads every module into one process, so the hook breaks other modules: 313 tests, **120 failures and 2 errors** on the untouched tree (9 Nov, 12:40 PM PST). Run one module per process instead, for example `.venv/bin/python -B -m unittest -v tests.test_crisis_v4`, or all of them with `.venv/bin/python permod.py /tmp/tests-per-module`.
2. **Two stale-string tests.** `test_held_out_b2_flag.test_b2_full_mode_whole_set_only` and `test_held_out_wiring.test_run_flag_is_full_mode_only` expect "full mode only"; the code now says "full or opt-in baseline mode".
3. **One expected pin failure.** `test_new_pure_check_source_pins_match` fails because `harness/pipeline.py` changed after B6 (the B7 fix). The B6 preflight refuses for the same reason, by design.
4. **`run.py` would log the wrong crisis sha.** `evals/run.py:433` and `:651` record `crisis_template_sha256` from `config.CRISIS_YAML` (crisis-v3). A full-mode v0 run now uses crisis-v4, so its `run.json` would show the v3 sha. No such run happened. Fix this before any run.
5. **More tests fail in this snapshot than in the record.** On the full private tree, one module per process gave 45 modules, 334 tests and exactly the 3 failures above (9 Nov, 12:50 PM PST). Tests that read held-out files, run folders, `docs/DECISIONS.md` or files above the repository will also fail here. This snapshot was not re-tested.
6. **Retrieval reads outside the repository.** `harness/config.py:9` sets the corpus root to an ancestor folder of the repository (`PROJECT_ROOT.parents[4]`). In a clone it will not exist, so retrieval finds nothing until the public corpus files listed in `configs/retrieval/allowlist-v*.txt` are placed there.
7. **The real gate is not here.** It is a Ruby file outside the repository; without it, a labelled stub answers HOLD for everything.
8. **MLX only, Apple silicon only.** See `../USAGE_GUIDE.md` §0 for what cannot be rerun from this release.
