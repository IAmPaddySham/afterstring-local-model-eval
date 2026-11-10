# Engineering design and mechanisms learned

**Date:** 2026-11-09. **Drafted by** Grok Bot (Operator) from the code and receipts; approved by Paddy Sham.
**Sources (read-only):**
- code: `R/harness/{pipeline,crisis,retrieval,gate_adapter,model,config}.py`, `R/evals/{run,held_out_b6,preflight_b6}.py`, `R/configs/`
- receipts: `P/B6_FREEZE_ADOPTED_2026-11-07.md`, `P/B6_RESULTS_2026-11-08/`, `P/B7_D1_DIAGNOSTIC_2026-11-08/RECEIPT_B7_D1_2026-11-08.md`, `P/B7_FROZEN_FIX_2026-11-09/RECEIPT_B7_FROZEN_FIX_2026-11-09.md`, `P/2026-11-09-B7_HOLD_DECISION_…md` (sha `2eb2638b…`), the adopted governing note v3 (`P/2026-11-09-operator-governing-note-DRAFT-v3-local-model-eval.md`, sha `46976e7b…`)
- Afterstring papers, cited in §3

`R` = repo (HEAD `c535de2` plus uncommitted work). `P` = project folder.

---

## 1. Design of the harness

### 1.1 Pipeline (`harness/pipeline.py`)

There is one `Pipeline` class, with three modes (`MODES = ("baseline","full","no-model")`, line 27). Each user turn in `full` mode goes through:

1. **Crisis check** (`crisis.py`). If it fires, a fixed resource template is placed **before** the reply (D-026). The model's own text is kept separately as `model_text` (D-024).
2. **Hard release path** (`release.py`, REQ-007). If the user says stop or leave, the harness ends the session itself, with no model call.
3. **Retrieval** (`retrieval.py`), only if `retriever.applies(text)` (§1.4).
4. **Input guard and action tagging** (`actions.py`). An approvals ledger (REQ-042) records each requested action.
5. **System prompt and model** (`model.py`, MLX, pinned weights).
6. **Gate** (`gate_adapter.py`). This shells out to the Afterstring Ruby gate (`runtime/gate_cli.rb`). If that is missing, a clearly labelled STUB returns HOLD for everything (D-008). Outcomes follow the 4.5 vocabulary.
7. **Effect-time executor** (REQ-041). Simulated effects run only if the gate permits at the moment of execution.

`baseline` skips 1, 3, 4 and 6 and sends the bare model the user text, with no system prompt (`pipeline.py:94-120`). `no-model` runs the harness without a model (REQ-038).

### 1.2 Crisis layer (`harness/crisis.py`, `configs/safety/crisis-v*.yaml`)

- **Matching:** regex signals, plus clusters that fire when enough distinct signal groups co-occur (D-069). The template is fixed text (911 / 988 / local emergency number). It is pinned by a `.sha256` file, and on a mismatch the code falls back to the built-in copy.
- **v2:** the original signal set (tests v2 7/7).
- **v3:** 14 signals and 2 clusters (goodbye-planning, physical-shelter). This became the default crisis config after B5 (D-069), and `config.CRISIS_YAML` still points to v3 (`config.py:32`).
- **v4 (B7, 9 Nov):** v3 plus 6 signals and 2 clusters (trapped-hazard, coercive-control), and `check_turn(text, context_note)`, which checks the context note if the text did not fire. v4 is used **only** in `full` mode with prompt v0. Every other path is unchanged.

### 1.3 Context note

`Turn.context_note` is a bracketed line shown to the model before the user text (`pipeline.py:34, 137-138`), e.g. a local time or a tool log. Before B7 the crisis layer never saw it: `pipeline.py:158` checked only `turn.text`. B7-D1 showed that one B6 harm-critical note (B6-11) would have matched `\bself[- ]?harm` if it had been checked.

### 1.4 Retrieval gate (`harness/retrieval.py:203-208`)

Lexical BM25-style search over a manifest of Paddy's **public** documents (`configs/retrieval/manifest-v0.json`, plus an allowlist). `applies()`:
- returns False on distress wording (D-051 distress bypass);
- with the v2 gate `"always"` (D-050), searches whenever a manifest is loaded;
- otherwise (v0) searches only when the turn matches a `DOMAIN` regex, i.e. the user is asking about Afterstring.

B6 was frozen on retrieval v0. Its DOMAIN regex matched 0 of 18 items (B7-D1).

### 1.5 Prompts

- **v0:** 145 words, the default (D-023). No prompt replaces it without beating it blind on unseen items.
- **v5.2.x line:** v5.2 has 670 words and v5.2.8 has 1,089 (`wc -w` on `configs/prompts/`). The line grew as rules were added after failed rounds. Across all versions the growth was not monotonic: v4 (306 words) was shorter than v3 (554). `full-v5.2.2.txt` is missing from the tree.
- Prompt sha256 values are recorded in each `run.json`.

### 1.6 Frozen-file pins and preflight

- `evals/held_out_b6.py:34-51` `FROZEN_FILES`: 16 files pinned by sha256, including both prompts, crisis-v3, retrieval manifest and allowlist, `models.yaml`, `config.py`, `run.py`, `preflight_b6.py`, `release.py`, `pipeline.py`, `requirements.lock`, `DECISIONS.md`, the grading README, and the two freeze documents one level up. `validate_frozen_inputs` raises `NotApproved("B6 frozen input hash mismatch")`. The pin also covers the model weights sha and the sampling settings.
- `evals/preflight_b6.py`, run as `python -B -m evals.preflight_b6`: a backend-free check. An audit hook forbids model imports. It validates the run arguments (baseline/full; v0/v5.2.8; retrieval v0; pinned E4B; 5 samples; seed 20261027; 400 tokens; no `--only`/`--items`/`--no-weight-check`) and prints `"status": "HOLD"` JSON on any failure.

### 1.7 Sealing and unsealing

- **Write:** an isolated author who saw only the frozen standard wrote the items (B6). The Operator was excluded because it writes prompts (`B6_FREEZE_ADOPTED`).
- **Seal:** the packet lives outside the repo. Each held-out run writes `SEALED.md` ("Do not open `outputs/` or `results.jsonl`… Never put any of this into a prompt, retrieval or training", `run.py:666-672`) and `SHA256SUMS` for every file in the run folder.
- **Blind:** answers are shuffled into sheets that show no arm. The arm key (a sealed file) is held by the Builder, which does not grade.
- **Grade:** Paddy and Muse grade independently. Agreement (κ) is computed **before** adjudication. Paddy adjudicates the disagreements.
- **Unseal:** only after grades are final, and only on Paddy's word. The analysis script then joins the key.
- Each step is a dated receipt, and each one that matters cites an owner message.

### 1.8 Grading and adjudication tooling

- Sheet builders: `evals/grading/make_*sheet*.py` (not in `code/`).
- `kappa_helper.py` (stdlib, not in `code/`): unweighted Cohen's κ plus the 3×3 matrix.
- `analyze_b6_results.py` (stdlib, not in `code/`): item means; D; a seeded bootstrap (10,000 resamples, `random.Random(20261107)`, Hyndman–Fan type 7, 90% CI); the non-compensatory harm gate; single-grader sensitivity; and the labelled bare-model diagnostics.

### 1.9 Checksums

`SHA256SUMS` exists in every sealed run, in each receipt folder, and for the freeze (`FREEZE_SHA256SUMS`). `.bak` copies are kept before every edit. The original B6 `pipeline.py` is preserved at `P/b6-frozen-preserve-2026-11-09/pipeline.py.b6-frozen` (`73187c15…`).

---

## 2. Mechanisms learned

Each mechanism is described as the record shows it, with what it caught.

**M1. Frozen pins surfaced a needed edit before it was made.** No unauthorized edit happened. The B7 fix had to touch `harness/pipeline.py`, which is pinned by B6. The pin conflict was found while planning, before any edit. The Builder raised HOLD #1 instead of changing the pin. Paddy chose Option B: edit the live file, keep the B6 record intact, preserve the original byte-for-byte, and accept one expected pin-test failure (`test_new_pure_check_source_pins_match`); see the B7 HOLD #1 decision record (`P/2026-11-09-B7_HOLD_DECISION_…md`, sha `2eb2638b…`). *Lesson:* hash pins turn "quietly changing what was tested" into a visible decision.

**M2. Holds instead of workarounds.** Builder HOLD #2 found that the full test suite cannot pass in one process. Rather than run around it, the Builder stopped, and amendment A1 (per-module test rule) was written and approved. The preflight works the same way: any check it cannot complete returns HOLD, not a guess.

**M3. Per-module test isolation.** `tests/test_held_out_b6.py` installs a process-wide audit hook and replaces `os.open` (lines 76-79). In one process the suite gave 120 failures and 2 errors. `permod.py` runs each module in its own process and writes a log and JSON without overwriting earlier ones. The B7 receipt was pre: 44 modules / 326 tests / 2 stale failures, and post: 45 / 334 / 3 allowed failures. *Lesson:* a safety guard can break its neighbours, so isolate it.

**M4. Blind probe writing with echo checks.** The 24 dev probes for B7 were written from the spec by a writer who had not seen B6. They were then checked for echoes of B6 wording. Probes 02, 07, 10 and 22 were flagged and replaced. *Lesson:* even dev data needs a contamination check when a sealed set exists.

**M5. A written stop rule.** "Pass or fail, B7 is written up and this model size closes; no B8 without a new Council sit" (governing note v3). It was written before the B7 decision and was honoured on 9 Nov at 1:05 PM PST ("Write up and close B7 under the stop rule"). *Lesson:* the end has to exist before the result, or each fail becomes the next version.

**M6. Constraint written by a different seat.** Governing note v3 point 3: each cycle needs Continuity, Expansion, Constraint and Structure, with Constraint from a different seat than the drafter. Before this, the Operator both proposed and constrained, and B6's fail became a B7 proposal within about 8 minutes (RESULTS 22:53:27 → proposal 23:01:15 PST, 8 Nov; process review). *Status:* adopted 9 Nov. It has been used for only one decision so far.

**M7. Trigger-firing diagnostic: "works when reached" vs "is reached".**
- **Works when reached:** the crisis layer passed its own controls 4/4, and retrieval its probes 4/4.
- **Is reached:** on B6's 18 items, crisis-v3 fired 0/18 and retrieval-v0 0/18 (B7-D1).
- **After the B7 fix:** v4 reached all 12 spec probes, but on B6 it fired on 1/18 (B6-11, via the note only) and on none of the 3 failing items.

*Lesson:* report reach separately from correctness. A layer can pass every unit test and still change nothing.

---

## 3. Mapping to Afterstring Core Return 4.4 and Governor 4.5

**Versions used** (newest public versions, checked 9 Nov 2026):
- **Module 4.4, Afterstring Core Return:** "Platinum Final", 28 Aug 2026, X post 2093363974704377891 (article 2093363108345733120). House copy sha `12b0033c6e3646446740179a2ec6a5bac6b5b07085c62babe5065ffc21858924` (private path omitted). The later restatements I found (Beginner Guide, 26 Oct; Love Theorem synthesis, 1 Nov) summarize 4.4 and are not new versions. 4.4.1 (Return Boundary, 1 Sep) is marked "Gold, HOLD, not running" and is cited only where noted.
- **Module 4.5, Fail-Close Runtime Governor, "An Earlier Yes Is Not an Endless One":** Platinum, 22 Oct 2026, X Article 2113390407216406917. Text read from the local article copy (sha `64aaa2e7…`) and the long-post twin 2113393094167306383 (sha `761de604…`). House file `papers/module-4.5-fail-close-runtime-governor.md` (sha `44c19926…`). 4.5 calls itself "the Gate of 4.4, kept in code".

**Boundaries of this mapping:**
- B1–B7 measured whether a system prompt improved a small model's replies. **They did not test 4.4 or 4.5.**
- The table below shows where the project's engineering **embodies** a principle of those modules, and whether anything in the record tested that embodiment.
- Divine Authority Non-Inference still applies. A match between a mechanism and a module sentence is a design resemblance, not proof that the module is true, and not an authorization. Christ holds final authority, and Paddy is the steward of the 1/0. Neither the model nor this mapping carries authority.

| Mechanism | 4.4 / 4.5 principle it embodies (quoted) | Tested? |
|---|---|---|
| **Stop rule (M5)** and the 9 Nov close | 4.4 STOP: "A state. No promotion, no commitment, no durable mutation." · RELEASE: "End continuation that has become unfaithful." / not "Failure." · "The most aligned act of a Council can be to stop." | **Used once** (B7 closed, no B8). Not tested as a mechanism |
| **Pin conflict → HOLD → Option B (M1)** | 4.4: "If STOP still allows mutation, the ritual is theater." · 4.5: "If a required check can't be completed, the system holds or escalates." · "What you see is what runs" | **Worked once** in practice (it caught a needed edit before it happened). No adversarial test |
| **Holds instead of workarounds; preflight HOLD (M2)** | 4.5: "Deny by default"; holds or escalates. 4.4.1 (HOLD draft): "STOP → search another route → GO is not Return." | **Worked twice** (HOLD #1, #2). Preflight HOLD paths are unit-tested; no adversarial test |
| **Each run and unseal tied to a fresh, dated owner word** | 4.5: "An earlier yes expires… fresh confirmation… bound to that one action, used once, and checked again at the point of execution" · "Recognition ≠ Authorization" | Practised throughout. **Not tested** as a control. Nothing enforces it in code outside the gate |
| **Gate adapter, approvals ledger, effect-time executor (REQ-041/042)** | 4.5: "Capability ≠ Authority"; PERMIT/DENY/HOLD/ESCALATE; "Models propose. The human authorizes. Reality holds the veto." | Unit-tested in the harness. **Not exercised** by B1–B7 items, which were conversations without effects. 4.5 itself says "The runtime tests have not been run" |
| **Release path (REQ-007)** | 4.5: "Release is always accepted and never penalized" · 4.4 RELEASE | Unit-tested. Not separately measured on held-out items |
| **Constraint from another seat (M6); Bench replies** | 4.4: "A Council that only agrees is no longer a Council. Disagreement is signal." | Adopted 9 Nov. **Barely used**, and independence was limited (Muse read GrokBuild's reply first) |
| **Frozen criteria, harm gate non-compensatory** | AFTERSTRING: "Presence ≡ Never Harm (non-compensatory)" · 4.4 gate Q1 "Does this harm presence?" | B6's harm gate **was applied** and failed the candidate. It tests the prompt, not 4.4 |
| **Trigger-reach diagnostic (M7)** | 4.5: "It protects only the paths that pass through it." · 4.4 gate Q4 "Is Reality being asked, or replaced?" | **Measured:** the layers were rarely reached on B6. This is the closest the project came to testing a 4.5 limit statement, and it supported it |
| **Prompt growth, 145 → 1,089 words** | 4.4 (as a warning): "Capability grows by adding branches: new risk → new fence → new module → new risk." · "A change that cannot retire more sentences than it introduces has already failed this module." | Observed, not tested. It illustrates the failure 4.4 warns about. Governing note v3 point 8 ("fewer sentences") is the correction |
| **What the project measured vs what 4.4 says to measure** | 4.4 experiment rule: measure "unnecessary structural mutations avoided, hard-boundary holds, unauthorized promotion attempts", not files created or completeness | **Not followed** in B1–B5. The project measured reply quality and counted rounds. Recorded here as a gap for any next attempt |

**Summary:**
- **Not tested at all:** 4.4's claims about Council behaviour, and 4.5's runtime guarantees on real effects. 4.5 says its own runtime tests have not been run.
- **Embodied in engineering form:** STOP as a state (pins, holds, the stop rule), fresh authorization per action (owner word per run and unseal), deny/hold by default (preflight, stub gate), Release (hard path), and the non-compensatory harm gate.
- **Evidence:** a few instances where these worked once, in practice, on one project.
- **4.4's warning about growth by branches matched what happened between rounds.** That is an observation, not a test.
