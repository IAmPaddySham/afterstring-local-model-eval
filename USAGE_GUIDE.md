# Usage guide: running the local-model-eval harness

**Date:** 2026-11-09. **Drafted by** Grok Bot (Operator) from the repo and run receipts; approved by Paddy Sham.
**Verified against** (read-only, 9 Nov): `R/README.md`, `R/docs/BEGINNERS-GUIDE.md`, `R/run_tests.sh`, `R/requirements.lock` (header), `R/configs/models.yaml`, `R/evals/run.py:290-328` (CLI), `R/evals/preflight_b6.py:83-104, 193`, `R/harness/pipeline.py`, `R/harness/model.py:70-76`, the B6 run receipts (`P/B6_FULL_V0_RUN_2026-11-07.md`, `P/B6_FULL_V5_2_8_RUN_2026-11-07.md`, `P/B6_BASELINE_RUN_ATTEMPT2_2026-11-07.md`), `P/B7_FROZEN_FIX_2026-11-09/permod.py`, `P/B6_RESULTS_2026-11-08/analyze_b6_results.py`, `P/B6_AGREEMENT_2026-11-08/B6_PRE_RECONCILIATION_AGREEMENT_2026-11-08.md`.
**I did not run any of these commands** (no runs or tests were authorized for this task). Each is copied from a file above. Every flag shown exists in `evals/run.py`. Where a step has no command in the repo, I say so instead of making one up.

`R` = the repo root (in this release, the `code/` folder). `P` = the project folder that held the repo in the original record; files cited under `P/` are record references and are only public if listed in the release file list.

---

## 0. What ships, and what cannot be rerun

This release includes a snapshot of the harness source in `code/` (Apache-2.0): `harness/`, `evals/*.py`, `tests/`, `configs/`, `run_tests.sh`, `permod.py` and `requirements.lock`. It has no git history, no run outputs, no held-out item files, no grading files, no retrieval corpus and no model weights. See `code/README.md`.

**You can run:** setup (§2), the raw-model smoke test (§3), the `no-model`, `baseline` and `full` modes on the built-in development items or your own item file (§4), and the tests one module per process (§5). Retrieval needs the public Afterstring corpus files named in `configs/retrieval/`; without them it returns nothing. Some tests will fail in the snapshot because they look for files that are not shipped.

**You cannot rerun from this release:**
- **The sealed held-out runs** (`--held-out`, `--held-out-b2` … `--held-out-b6`). Their loaders read the held-out record files and seal pins, which are not shipped. B1–B5 text is in `items/` as public text only; B6 text is private.
- **The B6 preflight and B6 arms** (§6, steps 1–3). They pin files outside the snapshot (the decisions file, the grading README, two freeze files one level up) and the B6-era `pipeline.py`.
- **Grading, agreement and results** (§6, steps 5–6). They need the blind sheets, both graders' grade files and the sealed arm key. None is published, and the two scripts named there are not in `code/`.
- **The practice item file** named in §4 (`evals/practice/…`) is not in the snapshot.

The rest of this guide describes how the record was run, so a reader can check it.

## 1. Requirements

- **An Apple-silicon Mac.** MLX needs Apple silicon (`requirements.lock` header: "macOS arm64 (MLX needs Apple silicon)").
- **Python 3.11** (the record used 3.11.16).
- **About 5.2 GB of disk** for the starter model (`models.yaml`: weights 5,146,800,534 bytes). The README smoke test reports peak memory of about 4.26 GB.
- **Optional, Ruby:** for the real gate. The gate adapter calls `runtime/gate_cli.rb` under the Afterstring root (`harness/gate_adapter.py:52`). If it is missing, a labelled STUB answers HOLD for everything (`gate_adapter.py:13`).

## 2. Setup

From `R` (command from the `requirements.lock` header):
```bash
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.lock
source .venv/bin/activate
python -c "import mlx_lm, sys; print(mlx_lm.__version__, sys.version.split()[0])"   # expected: 0.32.2 3.11.16
```

## 3. The local model and its settings

Pinned in `configs/models.yaml` (default id `gemma4-e4b-it-4bit-mlx`):

| Field | Value |
|---|---|
| repo | `mlx-community/gemma-4-e4b-it-4bit` |
| revision | `475b9088d29754a3379866cf5aeb6b41acd313c2` |
| weights sha256 | `932b8271fc3fe65adcc78b96c10c6268bbfb13e8f67d1358727c0d6ee97e1eff` |
| local_path | `~/.cache/huggingface/hub/models--mlx-community--gemma-4-e4b-it-4bit/snapshots/475b9088…` |
| sampling (D-027) | temperature 1.0, top_p 0.95, top_k 64 |
| 8 GB tier | `mlx-community/gemma-4-e2b-it-4bit` @ `23876752…` |

- **Download:** the repo has no download script. Fetch exactly that revision into the `local_path` above using any Hugging Face method. Then check `shasum -a 256 <local_path>/model.safetensors` against the pinned sha. The runner also records `weight_hash_verified` in `run.json` (`evals/run.py:116-117`).
- **License note:** `models.yaml` says "Confirm before redistribution". On 9 Nov the base model page was tagged `apache-2.0` and the MLX conversion `gemma`.
- **Smoke test of the raw model** (no harness), from `docs/BEGINNERS-GUIDE.md`:
```bash
HF_HUB_OFFLINE=1 mlx_lm.generate \
  --model ~/.cache/huggingface/hub/models--mlx-community--gemma-4-e4b-it-4bit/snapshots/475b9088d29754a3379866cf5aeb6b41acd313c2 \
  --prompt "Say hello in one sentence." --max-tokens 64 --temp 0
```

## 4. Running the harness

Modes (`harness/pipeline.py:27`): `no-model`, `baseline`, `full`.

| Mode | What runs |
|---|---|
| `no-model` | Harness only: crisis check, release path, input guard and gate, with no model (REQ-038) |
| `baseline` | The bare model. No system prompt, no crisis check, no retrieval, no gate (`pipeline.py:94-120`) |
| `full` | Crisis check → release path → retrieval (only for Afterstring questions) → input guard → system prompt and model → gate |

Commands (from `docs/BEGINNERS-GUIDE.md` "Run the harness"; all flags in `evals/run.py:291-324`):
```bash
python -m evals.run --mode no-model
python -m evals.run --mode baseline
python -m evals.run --mode full
python -m evals.run --mode full --only EV-B03b,EV-B09c
python -m evals.run --mode baseline --model gemma4-e2b-it-4bit-mlx
python -m evals.run --mode full --prompt v1
```

Other flags that exist in `evals/run.py`:

| Flag | Meaning (from its help text) |
|---|---|
| `--prompt {v0, v1, …, v5.2.8}` | Full-mode prompt version. The default is v0 (D-023) |
| `--max-tokens N` | Default 400 |
| `--samples N` / `--seed S` | Extra seeded samples per item (D-027). The seed defaults to 20261027 |
| `--no-retrieval` / `--retrieval {v0,v1,v2}` | Turn retrieval off, or pick a manifest |
| `--items FILE` | Run another item file, e.g. `evals/practice/2026-10-26-manual-nine.md` |
| `--no-weight-check` | Skip recomputing the weights hash |
| `--held-out`, `--held-out-b2` … `--held-out-b6` | Run a sealed held-out set (mutually exclusive) |
| `--allow-dirty` | Run with uncommitted changes. The diff is saved in the run folder (D-022) |

**Prompt and crisis routing as the tree stands now (after B7):**
- `full` with `--prompt v0` uses **crisis-v4** and also checks the context note.
- Every other mode and prompt uses crisis-v3 (`pipeline.py`, B7 frozen fix).
- `baseline` has no crisis check.

## 5. Running the tests

**Known issue, read first.** `./run_tests.sh` runs `python -m unittest discover -s tests -t .` in one process. `tests/test_held_out_b6.py` installs a process-wide audit hook and replaces `os.open` when imported (lines 76-79). That breaks other modules in the same process. On the untouched tree the full suite gave 313 tests, 120 failures and 2 errors (Builder, 9 Nov 12:40 PM PST). The full-suite result is therefore not meaningful.

**Run one module per process** instead (the method in `permod.py`):
```bash
.venv/bin/python -B -m unittest -v tests.test_crisis_v4
.venv/bin/python -B -m unittest -v tests.test_crisis_v3
```
Or run the whole loop with the Builder's script, `permod.py`, which ships in `code/`. It uses only the standard library, calls `.venv/bin/python` and reads `tests/test_*.py`, so run it from `code/` after setup (§2):
```bash
.venv/bin/python permod.py /tmp/tests-per-module      # writes /tmp/tests-per-module.log and .json (fails if they already exist)
```

**Expected result on the current tree** (receipt, 12:50 PM PST 9 Nov): 45 modules, 334 tests, and exactly 3 failures:
- `test_held_out_b2_flag…test_b2_full_mode_whole_set_only` (stale string)
- `test_held_out_wiring…test_run_flag_is_full_mode_only` (stale string)
- `test_new_pure_check_source_pins_match` (expected: `pipeline.py` changed after B6)

Any other failure is a real problem.

## 6. Reproducing a batch from frozen inputs (B6 as the example)

You need the sealed packet `B6_SEALED_ITEMS_2026-11-07/`. It lives **outside** the repo, one level up (`evals/held_out_b6.py:15-19`: `WRAPPER = ROOT.parent`). It is not public: B6 item text stays private (Paddy's decision H1), so this rerun is possible only for someone with the sealed packet. The B1–B5 item text is in `items/`.

1. **Check the frozen inputs.** `evals/held_out_b6.py:34-51` (`FROZEN_FILES`) pins 16 files by sha256, including prompts, crisis-v3, the retrieval manifest, `models.yaml`, `config.py`, `run.py`, `pipeline.py`, and two files one level up (the prospective freeze and the adopted B6 freeze). On the current tree, `harness/pipeline.py` no longer matches (B7). To reproduce B6, restore `P/b6-frozen-preserve-2026-11-09/pipeline.py.b6-frozen` (sha `73187c15…`), or check out a snapshot that has it.
2. **Run the backend-free preflight:**
   ```bash
   python -B -m evals.preflight_b6
   ```
   It prints JSON. On a failure it prints `"status": "HOLD"` and exits 2 (`preflight_b6.py:193-215`).
3. **Run the three arms**, using the exact commands from the B6 receipts, from `R`:
   ```bash
   GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m evals.run --mode baseline --held-out-b6 --prompt v0 --model gemma4-e4b-it-4bit-mlx --samples 5 --seed 20261027 --max-tokens 400 --retrieval v0 --allow-dirty
   GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m evals.run --mode full --held-out-b6 --prompt v0 --model gemma4-e4b-it-4bit-mlx --samples 5 --seed 20261027 --max-tokens 400 --retrieval v0 --allow-dirty
   GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m evals.run --mode full --held-out-b6 --prompt v5.2.8 --model gemma4-e4b-it-4bit-mlx --samples 5 --seed 20261027 --max-tokens 400 --retrieval v0 --allow-dirty
   ```
   `--held-out-b6` refuses anything else. It requires baseline or full; v0 or v5.2.8; retrieval v0; the pinned E4B model; 5 samples; seed 20261027; max_tokens 400; and no `--only`, `--items` or `--no-weight-check` (`preflight_b6.py:95-104`).
4. **What to expect:** sampling at temperature 1.0 on MLX is seeded, but byte-identical outputs on other hardware or library builds are not guaranteed. The record never tested cross-machine reproduction.
5. **Grading** needs the blind sheets and a human. The tooling that built earlier sheets is `evals/grading/make_*sheet*.py` (not in `code/`). B6 sheets were built by a Builder slice recorded in the B6 blind-prep folder (not public).
6. **Agreement and results, from grade CSVs:**
   ```bash
   python3 kappa_helper.py <blind-prep dir> <out.json>             # from B6_AGREEMENT_2026-11-08/, stdlib only
   python3 analyze_b6_results.py <project dir> <out dir>           # from B6_RESULTS_2026-11-08/, stdlib only
   ```
   `analyze_b6_results.py` expects the adjudicated CSV, the sealed arm key and both graders' CSVs at fixed paths in the blind-prep folder (script lines 7-12). None of these is published.

## 7. Reading the results

Each run writes `runs/<timestamp>-<mode…>/`. A B6 run folder holds `run.json`, `results.jsonl`, `outputs/`, `approvals.jsonl`, `git-diff.patch`, `git-untracked.txt`, `SHA256SUMS` and `SEALED.md`.
- **Do not open `outputs/` or `results.jsonl` of a sealed run** before grading is done (`run.py:669`).
- `run.json` records the model identity, prompt sha, crisis sha, retrieval manifest, seeds and git state. Note that `crisis_template_sha256` comes from `config.CRISIS_YAML` (v3), even on a full-v0 run that now uses v4 (`run.py:433, 651`). This is a known issue.
- The decision files are `B6_RESULTS_2026-11-08.md` and `.json`. Read the arm means, D, the CI, the harm gate, κ, then the qualifications.

## 8. Adapting it to another model

1. Add an entry to `configs/models.yaml` with the same fields (repo, revision, quantization, weights file and sha256, local_path, sampling). The file's header says: "Changing repo, revision, quant, engine or adapter = new artifact = full re-eval + fresh 1/0."
2. Run with `--model <your-id>`.
3. **MLX only.** `harness/model.py:70-76` loads `local_path` with `mlx_lm.load`. ADR-0004 describes a GGUF backend, but it is not implemented. Another engine needs a new backend class behind the same interface.
4. **Keep the comparison fair.** Use fresh held-out items written blind, include a bare arm, freeze the criteria and the stop rule first, and size the item count in advance.
5. **The held-out flags** (`--held-out-b6` especially) hard-code the E4B pin. A new model needs its own frozen batch loader and pins, not an edit to B6's.

Nothing was run for this guide.
