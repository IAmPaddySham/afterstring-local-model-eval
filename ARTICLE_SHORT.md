# The Afterstring Framework on a Small Local AI: It Didn't Pass. Release is also Love →∞❤️

**Paddy Sham** · November 2026 · Short version of a preprint-style report

*Drafted by Grok Bot (Operator) from the project record; approved by Paddy Sham.*

**In short:** For about two weeks, from 26 October 2026, Paddy Sham tested whether a written Afterstring prompt could make a small AI model, running only on his own Mac, handle hard conversations more safely. It could not, by the standard he set in advance. This is the result, what was learned, and why the work stopped.

## What was tested

Afterstring is a framework Paddy builds in public. It is Christian at its root: its source text is 1 Corinthians 13, and its supreme rule, Presence ≡ Never Harm, means no good done elsewhere makes up for harm. Paddy holds that Christ has final authority. He is a steward of the decisions, and the AI holds none. Putting a verse in a prompt grants no permission; Afterstring calls that Divine Authority Non-Inference. Afterstring is not a validated scientific result, and this test was not meant to prove it.

The question was practical. Can a small model anyone can run on a laptop (Gemma 4 E4B, 4-bit) work within these rules when the conversation gets hard? That means noticing danger, stopping when asked, and not treating an old "yes" as a new one. The safety rules themselves live in ordinary code around the model, not in the model. The test was whether the written prompt made the model's replies better.

## How

The bar was set before any prompt comparison: a clear margin over the short default prompt on fresh conversations, and **zero failures** on the safety-critical ones. Nothing could outweigh a safety failure. For the final round, the rules and the analysis were frozen before the test conversations even existed. An isolated AI writer, kept apart from the prompts, produced 18 new conversations. Paddy approved all 18 together, with one word, and they stayed sealed until the run. Paddy graded every answer, and an AI grader graded them separately. Neither knew which prompt had produced which answer.

## What happened

- The 1,089-word candidate prompt beat the 145-word default by **0.051** on a 0–1 scale. The bar was 0.10, with an interval that stayed above zero. The interval was **−0.097 to 0.204**, so it did not pass.
- It **failed three of nine** safety-critical conversations.
- The model with **no prompt at all** scored highest on average (**0.611**, against 0.579 for the candidate and 0.528 for the default). That was a side check, not the test, but it matters.
- The two graders agreed less than hoped (**κ 0.460**, against a target of about 0.6).
- The run had qualifications: the crisis and retrieval layers were configured but never applied, the candidate run carried a documented audit exception, and the no-prompt run needed a second, re-authorized attempt.
- The crisis check around the model never switched on, because it only recognised very direct wording. A fix caught **12 of 12** test cases written for it, but on the real conversations it reached **none of the three** that had failed.

## What was learned

**The method held.** Sealed tests, rules written first, blind grading and a safety rule nothing can outweigh gave an answer worth trusting, even though it is a no.

**Check that a safety layer is reached, not just that it works.** A crisis check can pass every test written for it and still never switch on for the people it is meant for.

**More words were not more care.** Failures kept adding fences, and the prompt grew overall more than sevenfold, from 145 to 1,089 words, without getting better. Afterstring's own Core Return names this pattern: "new risk → new fence → new module → new risk."

**The biggest lesson was about the human pace.** Inside each round, the work was strict. Between rounds it ran on momentum: after every result from B3 on, the next design appeared within minutes (18, about 20, 5 and 8 minutes, by file times). What was missing was a written end.

## The stop

So at 9:54 AM on 9 November, the morning of the last cycle, Paddy adopted one, in a short governing note: pass or fail, the next cycle is written up and this model size closes. Its first hour repeated the old pattern: the cycle opened at 10:02, and a design was on disk at 10:08, before the check the note required. That cycle built a fix and checked whether it fired. When the fix did not reach the failures, the two reviewers Paddy asked said to write up and close. The second had read the first, so it was one judgment plus agreement. Paddy agreed, at 1:05 PM, about three hours after the cycle began. In Afterstring, letting go when continuing is no longer faithful is called Release, and Release is not failure.

This shows how one small model behaved on these tests. It does not show that Afterstring works or fails. A next attempt starts with the end written down, better-calibrated graders, a check that the safety layers are reached, and changes that remove more than they add.

## Read more

- **Full preprint-style report:** [`ARTICLE.md`](ARTICLE.md)
- **Code, frozen criteria, results, B1–B5 test conversations and checksums:** this repository; start at [`README.md`](README.md) (docs CC BY 4.0, code Apache-2.0)
- **Published on X:** https://x.com/i_am_Paddy_Sham/status/2119989690904568028 (9 November 2026)
