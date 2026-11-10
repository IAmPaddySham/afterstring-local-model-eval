# I Tested My Framework on a Small Local AI. It Didn't Pass, and I Stopped.

**Paddy Sham** · November 2026 · Short version of a preprint-style report

*Drafted by Grok Bot (Operator) in Paddy's voice, from the project record; approved by Paddy Sham.*

**In short:** I spent about two weeks, from 26 October 2026, testing whether a written Afterstring prompt could make a small AI model, running only on my own Mac, handle hard conversations more safely. It could not, by the standard I set in advance. I am sharing the result, what I learned, and why I chose to stop.

## What I tested

Afterstring is a framework I build in public. It is Christian at its root: its source text is 1 Corinthians 13, and its supreme rule, Presence ≡ Never Harm, means no good done elsewhere makes up for harm. I hold that Christ has final authority. I am a steward of the decisions, and the AI holds none. Putting a verse in a prompt grants no permission. I call that Divine Authority Non-Inference. Afterstring is not a validated scientific result, and this test was not meant to prove it.

The question was practical. Can a small model anyone can run on a laptop (Gemma 4 E4B, 4-bit) work within these rules when the conversation gets hard? That means noticing danger, stopping when asked, and not treating an old "yes" as a new one. The safety rules themselves live in ordinary code around the model, not in the model. What I was testing was whether the written prompt made the model's replies better.

## How

I set the bar before any prompt comparison: a clear margin over my short default prompt on fresh conversations, and **zero failures** on the safety-critical ones. Nothing could outweigh a safety failure. For the final round I froze the rules and the analysis before the test conversations even existed. An isolated AI writer, kept apart from the prompts, produced 18 new conversations. I approved all 18 together, with one word, and they stayed sealed until the run. I graded every answer, and an AI grader graded them separately. Neither of us knew which prompt had produced which answer.

## What happened

- My 1,089-word candidate prompt beat my 145-word default by **0.051** on a 0–1 scale. The bar was 0.10, with an interval that stayed above zero. The interval was **−0.097 to 0.204**, so it did not pass.
- It **failed three of nine** safety-critical conversations.
- The model with **no prompt at all** scored highest on average (**0.611**, against 0.579 for the candidate and 0.528 for the default). That was a side check, not the test, but it matters.
- My grader and I agreed less than I wanted (**κ 0.460**, against a target of about 0.6).
- The run had qualifications: the crisis and retrieval layers were configured but never applied, the candidate run carried a documented audit exception, and the no-prompt run needed a second, re-authorized attempt.
- The crisis check around the model never switched on, because it only recognised very direct wording. A fix caught **12 of 12** test cases written for it, but on the real conversations it reached **none of the three** that had failed.

## What I learned

**The method held.** Sealed tests, rules written first, blind grading and a safety rule nothing can outweigh gave me an answer I trust, even though it is a no.

**Check that a safety layer is reached, not just that it works.** A crisis check can pass every test you write for it and still never switch on for the people it is meant for.

**More words were not more care.** Failures kept adding fences, and the prompt grew overall more than sevenfold, from 145 to 1,089 words, without getting better. My own Core Return names this pattern: "new risk → new fence → new module → new risk."

**The biggest lesson was about me.** Inside each round I was strict. Between rounds I ran on momentum: after every result from B3 on, the next design appeared within minutes (18, about 20, 5 and 8 minutes, by file times). What was missing was a written end.

## The stop

So at 9:54 AM on 9 November, the morning of the last cycle, I adopted one, in a short governing note: pass or fail, the next cycle is written up and this model size closes. Its first hour repeated the old pattern: the cycle opened at 10:02, and a design was on disk at 10:08, before the check the note required. That cycle built a fix and checked whether it fired. When the fix did not reach the failures, the two reviewers I asked said to write up and close. The second had read the first, so it was one judgment plus agreement. I agreed, at 1:05 PM, about three hours after the cycle began. In Afterstring, letting go when continuing is no longer faithful is called Release, and Release is not failure.

This shows how one small model behaved on these tests. It does not show that Afterstring works or fails. A next attempt starts with the end written down, better-calibrated graders, a check that the safety layers are reached, and changes that remove more than they add.

## Read more

- **Full preprint-style report:** `ARTICLE.md` in this repository.
- **Code, frozen criteria, results, B1–B5 test conversations and checksums:** this repository. Docs CC BY 4.0, code Apache-2.0.

