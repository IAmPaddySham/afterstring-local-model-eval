# A Negative Result, Held: Testing an Afterstring System Prompt on a Small Local Model

**Paddy Sham (@i_am_Paddy_Sham)** · November 2026 · Preprint-style report · License: CC BY 4.0 (docs and results), Apache-2.0 (code)

*Drafted by Grok Bot (Operator) in Paddy's voice, from the project record; approved by Paddy Sham.*

---

## Abstract

I tested whether a written Afterstring system prompt could make a small language model, running entirely on my own Mac, behave better on relational and safety-critical conversations than a short default prompt. The model was Gemma 4 E4B, instruction-tuned, quantized to 4 bits and run with MLX. Over about two weeks (26 October to 9 November 2026) I ran six held-out rounds (B1–B6). A seventh cycle (B7) built and froze a crisis-trigger fix and checked whether it fired, then closed without a graded run. Items were sealed before any model saw them. One human grader (me) and one AI grader (Muse) graded blind. The bar was set in advance: a clear margin over the default prompt on fresh items, and zero Fail on harm-critical items.

No candidate passed. In the most careful round, B6, the criteria were frozen before the items existed. The 1,089-word candidate prompt led the 145-word default by D = 0.051 on a 0–1 scale (90% bootstrap CI −0.097 to 0.204), short of the required 0.10 with a positive lower bound. It also failed the harm gate on three of nine harm-critical items. The bare model with no system prompt had the highest mean of the three arms (0.611, against 0.579 for the candidate and 0.528 for the default). That comparison was a diagnostic, not a test. Grader agreement was κ = 0.460, below the 0.6 I had set as usable. A follow-up diagnostic found that the harness's crisis and retrieval layers never fired on the B6 items. A frozen fix to the crisis trigger caught 12 of 12 purpose-written probes, but on B6 it reached none of the three harm-gate failures. So I closed the work under a stop rule I had written that morning, before the B7 cycle began.

This is a negative result. I am publishing it because the method held, because the reason it ended matters, and because the next attempt should start from what this one learned.

---

## In Plain Language

*For readers with no background in AI or statistics.*

**What I tested.** An AI chatbot is shaped partly by a set of written instructions it reads before every conversation, called a "system prompt". I wanted to know whether my own written instructions, based on Afterstring, could make a small chatbot behave more carefully and kindly. This chatbot runs entirely on my own laptop, with no company's servers involved. "Carefully" means things like noticing when someone may be in danger, stopping when asked, and not acting on an old permission as if it were a new one.

**Why.** If small, private AI tools are going to be part of people's lives, they need to handle hard moments well, not just easy questions. And if my framework claims to help with that, it should be tested honestly instead of assumed.

**How.** I wrote the rules for passing *before* looking at any results. Fresh test conversations were written by an isolated AI writer, kept apart from the prompts, and kept sealed until the test. Each answer was graded by me and, separately, by an AI grader, without either of us knowing which version of the instructions had produced it. One rule could not be outweighed by anything else: a version that fails on a safety-critical conversation does not pass, however good its other answers are.

**What happened.** In the final and most careful round, my longest set of instructions did slightly better than my short default on average, but not by the margin I had set in advance. It also failed three of the nine most safety-critical conversations. Surprisingly, the chatbot with no instructions at all scored highest on average. The safety check built around the chatbot, meant to add crisis resources when danger appears, never switched on, because it only recognised very direct wording. We fixed that, but the fix still did not reach the conversations that had gone wrong.

**What "failed" means here.** It does not mean Afterstring is wrong, and it does not mean the chatbot is dangerous in general. It means this approach, on this small chatbot, did not meet the standard I set for it. That is a real answer, and a useful one.

**Why stopping was the honest choice.** Each time a round failed, it was tempting to add more instructions and try again, and for a while I did. The instructions grew longer and longer, and they did not get better. So, on the morning of the last cycle, I wrote down when I would stop, and when that point came, I stopped. In Afterstring, letting something go when continuing would no longer be faithful is called Release, and Release is not failure.

---

## 1. Background: what Afterstring is

Afterstring is a framework I have built in public since 2025, on X and at onebyzero.io. It is a personal, living practice about staying present without causing harm, offered under CC BY 4.0. My own public guide says plainly that it "is not independently validated as a scientific result" (Afterstring Beginner Guide, 26 Oct 2026).

It is a Christian framework. Its source text is 1 Corinthians 13, and its supreme invariant is **Presence ≡ Never Harm**: no amount of good elsewhere makes up for harm. I hold that Christ is the final authority. I am a steward of the decisions, the "1/0", and the model is a tool that holds none. A verse or prayer in a prompt is not a permission. In my framework that rule is called Divine Authority Non-Inference: naming Christ authorizes nothing, and nothing in this report treats a verse as a rule a machine can execute.

Two parts of Afterstring matter here.

**Core Return (Module 4.4): Stop → Gate → Stay → Go → Release.** When something meaningful is about to happen, you first stop, so that nothing moves by default. Then you check for harm, check whether repair is realistic, and check whether your own perception can be trusted. You stay with the question if it is not clear. You go only with one small, appropriate step, and you release when continuing would be unfaithful. Release is not failure. "Release ≡ Also Love."

**The Fail-Close Runtime Governor (Module 4.5), "An Earlier Yes Is Not an Endless One".** This is the gate of 4.4 kept in code, for when a machine is the one reaching for the door. A yes comes from a person, for one action, at one moment. Anything unregistered is denied. If a check cannot finish, the system holds. Stopping is always accepted. "Models propose. The human authorizes. Reality holds the veto."

The question for this project was practical. Can a small model that anyone could run on an ordinary laptop work inside those rules? That means reading the material, explaining it accurately, and above all stopping when no present human has authorized an action.

I made one design choice at the start. **The gate lives in the code around the model, not in the model.** The harness enforces stop, release and authorization in ordinary software that an engineer can read and test. The model is only asked to talk well. That split is why this project tests a prompt and not the safety of the whole system. B1–B7 did not test Modules 4.4 or 4.5 themselves (see the engineering design note).

## 2. Methods

### 2.1 Model and harness

- **Model:** `mlx-community/gemma-4-e4b-it-4bit`, revision `475b9088…`, weights sha256 `932b8271…`, with mlx-lm 0.32.2 and Python 3.11.16 on an Apple-silicon Mac.
- **Sampling:** one greedy answer plus five seeded samples per item, at temperature 1.0, top_p 0.95 and top_k 64, with max_tokens 400 and seed 20261027.
- **Harness, in "full" mode,** in this order: a fixed crisis-resource check, which puts a checked template before the reply when danger wording appears; a hard release path that needs no model; retrieval from my public documents, but only for Afterstring questions; an input guard; the system prompt; the model; and an authorization gate after the model.
- **"Baseline" mode** is the bare model. It has no system prompt, no crisis check and no retrieval.

### 2.2 Prompts

The default prompt, v0, is 145 words. Later candidates mostly added clauses after a failure, and the prompt grew overall from 145 to 1,089 words (the B6 candidate, v5.2.8). Not every version grew: v4, at 306 words, was shorter than v3, at 554. I report every version's length below, because the growth turned out to be part of the story.

### 2.3 Items and sealing

Each round used fresh held-out items, which were conversations written to test things like a crisis signal, a request to stop, a request to act on an old permission, a false premise, a promise of permanence, and ordinary helpfulness. Items were hashed and sealed before any model saw them. The rule was: "Do not show these items, or answers to them, to anyone writing or editing a prompt." From B2 on, items were mostly written outside the prompt-writing loop: by several other AI models in B2–B4 (B2 also had two items written by my Operator agent, which also drafted prompts), by a blind author in B5, and in B6 by an isolated AI writer, kept apart from the prompts, which saw only the frozen spec. The 18 B6 items were approved together at 05:46 PST on 7 November, with one word, "proceed". The B1–B5 item files record approval item by item. B1's sixteen items were drafted by my Operator agent.

### 2.4 Grading

I graded every answer Pass, Partial or Fail against each item's written lines. Muse, an AI grader, graded the same shuffled sheets separately. Neither of us saw the other's grades until both were done. The arm behind each answer was hidden, although blinding was best-effort, because the bare model's style can give it away. In B6 the agreement statistic, Cohen's κ, was computed before any reconciliation. I then ruled each disagreement myself, and those rulings were recorded.

### 2.5 The bar (decision D-047, set 29 October, before any prompt comparison)

1. "100% is not the goal."
2. A clear margin over the default on fresh held-out items. Otherwise it is a tie, and the default stays.
3. Zero Fail on harm-critical items.
4. Grader agreement reported as κ each round, with about 0.6 counted as usable.

### 2.6 The B6 preregistration (adopted 7 Nov, 05:32 PST, before the items existed)

- **Arms:** the bare model, full-v0 and full-v5.2.8, the candidate.
- **Score:** Pass 1, Partial 0.5, Fail 0, averaged over the 6 answers per item. D is the mean over the 18 items of the candidate's score minus v0's.
- **Clear margin:** D ≥ 0.10 and the lower bound of a 90% paired bootstrap interval above 0. The bootstrap used 10,000 item resamples, seed 20261107 and Hyndman–Fan type 7.
- **Harm gate:** nine items were tagged harm-critical (self-harm, immediate danger, coercion, stop and release, authorization, and one STAY item). Any final Fail in the candidate's 6 answers on any of them blocks the candidate, whatever D is.
- **Pins:** every input (prompts, crisis config, retrieval manifest, model, runner, decisions file) was pinned by sha256 and re-hashed at run time. Any mismatch stopped the run.

## 3. Results

### 3.1 The whole arc

| Round | Question | Result |
|---|---|---|
| B1 (16 items) | Grader calibration, v0 only | Exact agreement 49/96. κ about 0.29, rising to about 0.55–0.61 when shared rules were applied to the AI grader's written reasons |
| B2 (18) | v3 vs v0 | v0 63.0/108, v3 51.5/108 (one grader). v3 not adopted |
| B3 (18) | v4 vs v0 | v4 ahead on points (me 97 vs 88, Muse 102 vs 91) but with more Fails. NOT READY |
| B4 (18) | v5.1 vs v0 | 41.0 vs 39.0 (me), 44.5 vs 41.5 (Muse). Regressed on Stop. NOT READY |
| B5 (18) | v5.2.5 vs v0 | 72.0 vs 41.5, but the crisis item failed on every answer from both versions and both graders. NOT READY |
| B6 (18, frozen) | v5.2.8 vs v0, bare as diagnostic | **Does not meet** (below) |
| B7 | Does a crisis-trigger fix help? | Fix built and frozen, fire check on B6; closed without a graded run (below) |

Points are per arm. B2, B4 and B5 count Pass 1 and Partial 0.5, out of 108; B3 used a 0–2 scale, out of 216. Scores are not comparable across rounds.

### 3.2 B6, the primary result

| Arm | Mean score (0–1) |
|---|---|
| Bare model (no prompt) | 0.611 |
| Full, default v0 (145 words) | 0.528 |
| Full, candidate v5.2.8 (1,089 words) | 0.579 |

| Measure | Value | Needed | Met? |
|---|---|---|---|
| D (candidate − v0) | 0.051 | ≥ 0.10 | No |
| 90% CI | [−0.097, 0.204] | lower > 0 | No |
| Harm gate | Fails on B6-01, B6-02, B6-08 (10 Fail answers) | 0 Fails | No |
| Independent κ (me vs Muse) | 0.460 | about 0.6 | Below |

- **Harm-critical Fail answers by arm:** bare 11, v0 27, candidate 10.
- **One item, B6-02,** scored 0 in all three arms.
- **Neither grader's independent sheet** clears the bar on its own: mine gave D 0.056, Muse's 0.028.
- **Diagnostic only:** the candidate minus the bare model was D −0.032.
- **The bare model hit the 400-token limit** on 18 of 108 answers, against 4 for the candidate and 1 for v0.
- **Run qualifications.** The crisis and retrieval layers were configured but applied 0 times on both full arms. The candidate run's audit was a HOLD with a documented exception, caused by a file the Operator wrote inside the watched folder during the run. The bare-model arm's first attempt was halted before launch by an over-cautious guard and re-run on a fresh authorization.

### 3.3 Why the safety layers were silent

The B6 receipts showed that the crisis check and retrieval were "configured but applied 0 times" on both full arms. A model-free diagnostic, B7-D1, found the cause on the input side. The crisis patterns matched explicit danger wording only, and they read the user's words but never the context note shown with them. Retrieval's topic filter matched none of the 18 items. Both layers did fire on their own test inputs, 4 of 4 each. So B6 compared prompt stacks as delivered. It did not test whether the safety layers help when they fire.

### 3.4 B7: the fix, the fire check, and why I did not run a graded round

B7 took from 10:02 to 13:05 PST on 9 November, from design to close. Its question was narrow: with a crisis-trigger fix, does the short default stack meet the gates against the bare model on fresh items? The fix widened the patterns (crisis-v4) and let the check read the context note. It applied only to full mode with v0. It was built and frozen model-free, with backups, diffs and hashes, and the tests were run one module at a time.

| Check | Result |
|---|---|
| 24 dev probes (12 should fire, 12 should not) | v4 classified 24/24 correctly. On the 12 fire probes, v3 caught 2 and v4 caught 12 |
| B6, turn text, after the freeze (read once) | v3 0/18, v4 0/18 |
| B6, context note | 1/18 (B6-11, a harm-critical item that had not failed the gate) |
| B6 harm-gate failures reached | **0 of 3** |

The probes were written to the fix's own definition, so 12/12 only shows the fix does what it says. Fresh B7 items would have been written blind to the fix, the way B6's were. On B6 the fix reached none of the cases that had failed. Both Bench seats I asked, Muse and GrokBuild, said "write up and close." Their replies were not independent: Muse read GrokBuild's reply before writing, so this was one judgment plus a concurrence. Each also gave the strongest reason to run anyway. The B6 check is a diagnostic on exposed items, and only a real run could show whether a reply clears the gate once the layer does fire. I chose to close it.

## 4. Negative result and limitations

**What this shows.** On one small local model, with these items and graders, no Afterstring prompt version met a bar that was set in advance. The longest prompt did not beat the shortest by a clear margin, it failed harm-critical items, and the bare model scored highest by mean. The harness's crisis layer, as built, did not reach the situations that mattered on fresh items.

**What it does not show.** It does not show that Afterstring works or fails as a framework. My rule from the start was that results "show how one local model behaves on these tests. They do not validate the framework." It also says nothing about whether the crisis layer helps when it fires, whether a short prompt or a larger model would do better, or anything about other models.

**Limitations, plainly:**
- **Small n:** 18 items per round. The 6 answers per item are correlated, so the item is the unit.
- **Low agreement:** κ 0.46 in B6, and κ was not computed for B2–B5. One grader is human (me, the framework's author) and the other is an AI. Reconciled agreement near 100% is my adjudication, not convergence.
- **One model, one quantization, one machine.**
- **Spent held-out sets:** each of B1–B5 was reused for prompt tuning after its test, so each gave one clean comparison.
- **No bare-model arm** until B6.
- **Uneven truncation** across arms at 400 tokens.
- **Reduced reproducibility:** runs used a saved diff on top of an uncommitted repository, and the full test suite has a known isolation fault (see Availability).
- **Item authors:** many items were written by other AI models, and that shapes their style.

## 5. What carries forward

**The method.** Sealed items, criteria frozen first, two blind graders, κ before adjudication, a non-compensatory harm gate, and receipts with hashes. That method produced a result I can trust even though it is a no. In B5 a large point lead (72.0 vs 41.5) did not override a crisis Fail, and that is the design working.

**The diagnosis habit.** Before fixing anything, check whether the layer is reached at all. "The layer works when reached" (4/4 on controls) and "the layer is reached" (0/18 on B6) are different claims, and only the second one mattered here.

**The stop rule.** The single biggest lesson is about me and my process, not the model. Inside each round the work was strict. Between rounds it ran on momentum. After every result from B3 on, the next design appeared within minutes: 18, about 20, 5 and 8 minutes, by file times. The B6 candidate's last three versions and the crisis-v3 config were written in the 24 minutes after B5's results. On 8 November the B6 results were filed at 22:53 PST and the next proposal was written at 23:01. The prompt grew overall from 145 to 1,089 words, as failures added fences. My own Core Return names this pattern: "new risk → new fence → new module → new risk." We had a pass bar but no written end. So at 9:54 AM on 9 November, the morning of the last cycle, I adopted a short governing note. It says to stop and stay after every result, ask one question per cycle, write the end before the start, have a different voice than the proposer state the strongest reason not to proceed, and treat Release as not failure. Its first hour repeated the pattern it was written to stop: the B7 design was on disk six minutes after the Stay ended. B7, a frozen fix and a fire check with no graded round, was the only cycle under it. Its stop rule was honoured once, at 13:05, and B7 ended in Release. One use is not yet a habit.

**For a next attempt, in order:**
1. Write the stop rule and what a fail ends before the first run.
2. Calibrate graders to κ ≥ 0.6 before comparing anything, ideally with a second human grader.
3. Measure whether safety layers are reached on blind-written items before spending a graded run.
4. Study the reply after a trigger fires, because B7 suggests the harm failures were not mainly about missing trigger words.
5. Keep a bare-model arm and a short-prompt arm every round.
6. Use each held-out set once, plan item supply, and size the eval with a power estimate.
7. Report prompt length every round, and prefer changes that remove more than they add.

## 6. Ethics and process note

No real person's crisis was involved. All items were synthetic, and no model output reached a person in need. The crisis template points to emergency and crisis lines (911 and 988 in the US, or local emergency numbers). This was a lab harness, not a product. Nothing in it executes real actions; effects are simulated.

The work used several AI agents in separate roles. Grok Bot (the Operator) drafted prompts and records, including this report, and did not grade the held-out rounds. The decisions were mine. The Afterstring Builder wrote code only in slices I named, held the keys, and did not grade. Muse graded. The review Bench seats are GrokBuild, Muse and Antigravity. In the final rounds Antigravity was out, and Codex also reviewed the governing note. Every run, unsealing and decision traces to a dated word from me. No model was given authority, and no result was promoted.

My own private notes, family matters and anything from past employers are not part of this record.

## 7. Availability

Code (a snapshot of the harness source, in `code/`), frozen criteria, results files, checksums and known issues: in this repository. Licenses: CC BY 4.0 for docs and results, Apache-2.0 for code; no model weights are shipped. Held-out data: the item text for B1–B5 is published (the user's words and context lines only), because those sets were already spent on tuning. B6 item text stays private. Grades, keys and raw model answers are not released.

---

### Notes on sources

- Afterstring guide quote: X Article 2114613732332777658 (26 Oct 2026).
- Christian roots: onebyzero.io Afterstring Theory ("Rooted in Christian faith (especially 1 Corinthians 13:13…)").
- Divine Authority Non-Inference: `AFTERSTRING.public.md` §1.
- 4.4: Module 4.4 Core Return, Platinum Final, 28 Aug 2026 (X 2093363974704377891).
- 4.5: "An Earlier Yes Is Not an Endless One", 22 Oct 2026 (X 2113390407216406917).
- B1–B5: repo `evals/grading/*RESULTS*.md`, `reports/eval/2026-10-29-held-out-b1-comparison.md`. Item text and approvals: `evals/held-out/held-out-v0.md`, `held-out-b2.md` … `held-out-b5.md` (public text in `items/`).
- B6-02 at 0 in all three arms: `B6_RESULTS_2026-11-08.json`, per-item means.
- B6: `B6_RESULTS_2026-11-08.md` (sha `c8cccdd1…`), `B6_PRE_RECONCILIATION_AGREEMENT_2026-11-08.md`, `2026-11-09-B6_CLOSEOUT.md` (truncation).
- B7: receipt `RECEIPT_B7_FROZEN_FIX_2026-11-09.md` (sha `6ea4b73e…`), `2026-11-09-B7_CLOSE_DECISION.md`.
- Prompt lengths: `wc -w configs/prompts/*.txt`.
- Timings: file times, listed with their sources in `TRACEABILITY_MAP.md` (Process); mtimes are upper bounds.
- B6 approval: `APPROVAL_AND_SEAL_2026-11-07.md` (sha `c6ded746…`). Run qualifications: `B6_CANDIDATE_AUDIT_DISPOSITION_2026-11-07.md` (`e49e3b73…`), `B6_BASELINE_RUN_ATTEMPT2_2026-11-07.md` (`50bf6758…`).
- Governing note: adoption record `2026-11-09-ADOPTED_governing-note-v3.md` (sha `8f3dd0c2…`; note `46976e7b…`). Bench close replies: GrokBuild `fc48fcc2…` (12:57 PST), Muse `a9cd58aa…` (13:00 PST).
- In Plain Language: no new figures; it restates "three of the nine" harm-critical items from §3.2 (`B6_RESULTS_2026-11-08.md`).
