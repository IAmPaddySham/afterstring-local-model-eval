# Afterstring prompt on a small local model: a negative result

*Drafted by Grok Bot (Operator) in Paddy's voice, from the project record; approved by Paddy Sham.*

## What this is

This is the record of one test. The question was whether a written Afterstring system prompt makes a small language model, running entirely on one Mac, handle relational and safety-critical conversations better than a short default prompt. The model was Gemma 4 E4B, instruction-tuned, 4-bit, on MLX. The safety rules themselves (stop, release, authorization) live in ordinary code around the model. Only the prompt was under test.

The work ran from 26 October to 9 November 2026: six held-out rounds (B1–B6), then a seventh cycle (B7) that built a crisis-trigger fix, checked whether it fired, and closed without a graded run.

## The result: no

In the preregistered round (B6), with criteria frozen before the items existed:

| Measure | Value | Needed | Met? |
|---|---|---|---|
| D, candidate (v5.2.8, 1,089 words) minus default (v0, 145 words), 0–1 scale | 0.051 | ≥ 0.10 | No |
| 90% paired bootstrap CI | [−0.097, 0.204] | lower bound > 0 | No |
| Harm gate (9 harm-critical items) | Failed on 3 of 9 | 0 Fails | No |
| Arm means | bare 0.611 · candidate 0.579 · v0 0.528 | — | — |
| Cohen's κ, before reconciliation | 0.460 | about 0.6 | Below |

The bare model, with no prompt, had the highest mean. That was a diagnostic, not a test. The crisis and retrieval layers never fired on the B6 items. A frozen fix (crisis-v4) caught 12 of 12 purpose-written probes, but on B6 it reached 0 of the 3 harm-gate failures. The project then closed under a stop rule written that morning, before B7 began.

This shows how one small model behaved on these tests. It does not show that Afterstring works or fails as a framework. B1–B7 did not test Modules 4.4 or 4.5 themselves.

## Release

Platinum release, 9 November 2026. Approved by Paddy Sham after Bench sign-off (GrokBuild, Muse; Grok Bot as Operator). Bench sign-off is counsel, not a stamp. `GOVERNING_NOTE_v3.md` is version 3 of the governing note, the one that was adopted.

## Reading order

1. This README.
2. `ARTICLE_SHORT.md`: the short version as published on X, in third person (about 1,000 words).
3. `ARTICLE.md`: the full report, with methods, results, limits and sources.
4. `HUMAN_SIDE.md`: what the human steward did, and where it strained.
5. `LETTER_FROM_THE_OPERATOR.md`: a letter from the AI Operator to whoever finds this.
6. `GOVERNING_NOTE_v3.md`: the rule set adopted on 9 November that ended the project.
7. `TRACEABILITY_MAP.md`: every public figure, mapped to its source file and sha.
8. `DATA_CARD.md`, `B6_PER_ITEM_AVERAGES.md` and `items/`: the test conversations, the B6 per-item averages, and what is and is not released.
9. `KNOWN_ISSUES.md`: what is broken or stale, stated plainly.
10. `USAGE_GUIDE.md` and `ENGINEERING_DESIGN.md`: how to run it, and how it is built.
11. `code/`: a snapshot of the harness source, with its own `code/README.md`.

**Tests:** the shipped test suite does not pass as-is. Run in one process (`./run_tests.sh`), it gives 120 failures and 2 errors. Run one module per process, two stale-string tests and one pin test still fail, and more fail in this snapshot because some tests need files that are not shipped. `code/README.md` explains each. It is not a clean build.

## License

- **Docs, results and the published B1–B5 test conversations:** Creative Commons Attribution 4.0 International (CC BY 4.0). See `LICENSE-DOCS`.
- **Code:** Apache License 2.0, including the harness snapshot in `code/`. See `LICENSE` and `NOTICE`.
- **Copyright:** © 2026 Paddy Sham.
- **No model weights are shipped.** The model is named and pinned by revision and hash only; its own terms apply to anyone who downloads it.
- The B2–B4 test conversations were written by other AI models; see Provider terms below.

## Held-out data

Item text for **B1–B5** is published in `items/`: the user's words and context lines only. Those sets were already spent on prompt tuning. **B6 item text stays private.** The B6 items were written by an isolated AI writer, kept apart from the prompts. For B6, `B6_PER_ITEM_AVERAGES.md` gives each item's family or tag, harm-critical flag, average score per arm and harm-gate result, with no item text. Per-answer grades and counts, grading sheets, keys and raw model answers are not released. One internal file reference in a B2 item was redacted. See `DATA_CARD.md`.

## Records not in this release

The full B6 RESULTS record and the B7 diagnostic records are not in this release. B6 is represented by `B6_PER_ITEM_AVERAGES.md` and the figures in `ARTICLE.md`. The records are named here by their sha so the figures can be traced:

| Record | Path in the project record | sha256 (first 16) |
|---|---|---|
| B6 RESULTS | `B6_RESULTS_2026-11-08/B6_RESULTS_2026-11-08.md` and `.json` | `c8cccdd19d9e39f6` (md) |
| B7 write-up | `2026-11-09-B7_WRITEUP_DRAFT.md` | `77897b4c9bbceb4a` |
| B7 fix receipt | `B7_FROZEN_FIX_2026-11-09/RECEIPT_B7_FROZEN_FIX_2026-11-09.md` | `6ea4b73e1fce2a6a` |

## What sets this apart, and what doesn't

**"It's another harness."** Partly. There is a harness, but it is not the thing under test. The question was whether one written prompt changed a small model's replies; the harness is how that was asked fairly.

**"It's prompt injection."** No. Prompt injection hides instructions to hijack a model. Here the system prompt was stated openly, its text is part of the record, and it was tested as an intervention against a short default, with the bare model as a diagnostic.

**"It's another AI project" or "faith branding."** It is a small test that ended with a no. Afterstring is a Christian framework, and we say so. Christ holds final authority, the human is the steward of decisions, and the model holds none. A verse in a prompt grants no permission. The faith shaped what was asked. It did not shape how the answer was judged: the criteria were set in advance and the grading was blind.

**What is distinctive is the combination.** Each part is ordinary on its own: a values-framed prompt on a 4-bit local model; criteria frozen and 16 inputs pinned by hash before the items existed; sealed items and held keys; one human grading every held-out answer blind beside an AI grader, with κ reported before reconciliation even though it was low; a harm gate that no average can outweigh; the no, published, including that the bare model scored highest; a stop rule written before the last cycle and kept; and the human-and-AI-agent governance record disclosed, including which texts the Operator drafted. Among the neighbor projects named below, checked on 9 November 2026, we did not find this combination applied to this question at this scale. Nothing here is a first in hash-freezing, preregistration, local evaluation, or testing faith or values prompts.

**Where neighbors are stronger.** Projects such as VERA-MH, IatroBench, aipsy-bench and the JMIR "Between Help and Harm" study use more items, clinical grounding, longer conversations or more graders. Closer neighbors include a values constitution steered on a 4-bit local model (Sevi), a preregistered Catholic Catechism prompt study that includes small local models (faith-based-ai-alignment), and psalm-alignment. The neighbor projects were checked on 9 November 2026.

## Provider terms (advisory, not a legal review)

The B2–B4 test conversations were written by other AI models: Gemini, ChatGPT, Meta AI, Mistral, DeepSeek and Google AI Mode. Their terms were read on 9 November 2026:

- **OpenAI and Google.** OpenAI's usage policy (updated 21 October 2026, effective 20 November 2026) and Google's terms restrict using their outputs to develop or train competing models. CC BY 4.0 carries no such restriction, so the license is wider than those rules. Publishing the items is not itself building a training set. We note this tension; it was not resolved by a lawyer.
- **Mistral and DeepSeek.** Their terms assign output to the user.
- **Meta AI.** Its current terms page was not opened. The Google AI Mode page was not opened separately from Google's terms.
- **Copyright.** Copyright in model-written text is uncertain. For sentences a model wrote, CC BY 4.0 works as a permission and a request for attribution, not a claim of authorship. The selection, editing, redaction and reporting are Paddy's.

The license stays CC BY 4.0. Each item file names the model that wrote its items, and that attribution stays on the page.

## Authorship and roles

Paddy Sham designed the test, graded every held-out answer blind, and made every decision. Muse, an AI grader, graded separately. Grok Bot (the Operator) drafted prompts, records and these documents, and did not grade the held-out rounds. The Afterstring Builder wrote code in named slices, held the keys, and did not grade. GrokBuild and Muse reviewed these documents. Codex sat on the governing note and wrote a reading of the project; Codex did not review this release, which was optional. No model was given authority, and no result was promoted.

## Status and what is still open

Closed. Not promoted; v0 stays the default. Seat empty.

- **Not in this release:** the full B6 RESULTS record and the B7 diagnostic records (see above).
- **Codex** did not review this release; that review was optional.
- **Flagged items: reviewed.** Some B1–B5 items speak as or to Paddy, mention health or family, or refer to his past. Paddy reviewed them on 9 November 2026, kept them as written, and approved the use of his name in them.
