# Known issues

*Drafted by Grok Bot (Operator) from the record; approved by Paddy Sham. Nothing here was fixed; a fix slice is Paddy's call.*

## Code and tests

1. **The full test suite fails before any edit.** `tests/test_held_out_b6.py` (lines 76–79) installs a process-wide audit hook and replaces `os.open` when imported. `./run_tests.sh` loads every module into one process, so the hook breaks other modules: 313 tests, **120 failures and 2 errors** on the untouched tree (9 Nov, 12:40 PM PST). Run one module per process instead, with `code/permod.py`; on the full private tree that gave 45 modules, 334 tests and 3 expected failures.
2. **Two stale-string tests.** `test_held_out_b2_flag.test_b2_full_mode_whole_set_only` and `test_held_out_wiring.test_run_flag_is_full_mode_only` expect "full mode only"; the code now says "full or opt-in baseline mode".
3. **One expected pin failure.** `test_new_pure_check_source_pins_match` fails because `harness/pipeline.py` changed after B6 (the B7 fix). The B6 preflight now refuses by design. The original file is preserved byte-for-byte (sha `73187c15…`).
4. **The run record would log the wrong crisis sha.** `evals/run.py:433` and `:651` record `crisis_template_sha256` from `config.CRISIS_YAML` (crisis-v3), so a full-v0 run on crisis-v4 would log the v3 sha. No such run happened. Any future run must fix this first.

## Record and reproducibility

5. **Uncommitted repository.** HEAD `c535de2` plus 171 uncommitted entries. Every run since 30 Oct used `--allow-dirty` with a saved `git-diff.patch`. The patches were not re-applied to verify.
6. **Stale `R/MANIFEST.sha256`.** Last written 5 Nov; 2,926 lines, including 390 `.bak` and `.DS_Store` entries. It does not describe the current tree and must be regenerated over the public tree at release.
7. **Record gaps.** D-049 and D-062 have no DECISIONS entries; `full-v5.2.2.txt` is missing; κ was not computed for B2–B5.
8. **Stale docs.** The repo README's update lines stop at 27 Oct; the beginners guide says "52 tests".
9. **External gate dependency.** The real gate is a Ruby file outside the repo; without it, a labelled stub answers HOLD for everything.
10. **Model license tags disagree.** The base model page is tagged `apache-2.0`, the MLX conversion `gemma` (checked 9 Nov). No weights are shipped.

## Review process

11. **The Bench "close" replies on B7 were not independent.** Muse read GrokBuild's reply before writing (12:57 → 13:00 PST, 9 Nov), so the advice to close was one judgment plus a concurrence. The same holds for the closeout review of these drafts: Muse disclosed reading GrokBuild's reply first.
12. **The shared Bench log kept changing during the closeout.** `BENCH.md` (not part of this release) was saved at 14:47:55 PST on 9 Nov and has changed since. It holds GrokBuild's closeout entry ("Sit 14:15 PT") and Muse's pointer to its closeout review ("Closeout review ~14:50 PT"). Its last block is `## Codex`, a Codex reading of the project. The record does not show who saved each change.
13. **Pace figures are upper bounds.** Result-to-next-design gaps are taken from file modification times, which mark when a file was last saved, not when work began.

## Data release

14. **B6 is published as per-item averages, not counts.** `B6_PER_ITEM_AVERAGES.md` gives average scores per arm; per-answer counts would need the sealed arm key. Only an average of 0 or 1 fixes the counts (all Fail or all Pass). Eight non-harm-critical items' families are in the sealed tags and are not shown.
15. **Provider terms: a known tension.** The B2–B4 test conversations were written by other AI models. OpenAI's and Google's terms restrict using outputs to train competing models; CC BY 4.0 does not. Meta AI's current terms page was not opened. Paddy accepted the tension and kept CC BY 4.0 (README, "Provider terms"). This was not a legal review.
16. **The full B6 RESULTS record and the B7 diagnostic records are not in this release.** The originals carry internal status lines and paths. B6 is represented by `B6_PER_ITEM_AVERAGES.md` and the figures in `ARTICLE.md`.
17. **One B2 item is redacted.** HO2-10 quoted an internal file reference; it now reads "[path removed]", so the item is not byte-identical to what the model saw.
18. **Some items name Paddy or touch health, family or crisis.** They are synthetic test conversations. Paddy reviewed them on 9 Nov 2026, kept them as written, and approved the use of his name. Each item file opens with a note saying so.

## Code snapshot

19. **The code in `code/` is a copy, not the repository.** It has no git history, run outputs, held-out files, grading files, retrieval corpus or weights, and it was not run after copying. Tests that look for files outside the snapshot will fail there. Issues 1–4 above apply to it. See `code/README.md`.
