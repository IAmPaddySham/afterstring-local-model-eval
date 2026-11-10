# The Human Side: what the steward did, and where it strained

*Drafted by Grok Bot (Operator) from the record; approved by Paddy Sham. Times are as recorded (PDT to 31 Oct, PST after). Grading-file times are file modification times, so they are upper bounds.*

This evaluation was run with AI agents in separate roles, but the judgment in it was one person's. This note records what Paddy did, with the evidence, and where the human side was under strain. Strain is part of an honest account of rigor.

## The work, by the record

**He graded every held-out answer himself, blind.**

| Round | Paddy's grades | Sheet → final grades | Source (grade files are not public) |
|---|---|---|---|
| B1 | 96 (16 items × 6) | sheet 28 Oct 21:41 → grades 29 Oct 12:56 | Paddy's grade file (not public) |
| B2 | 216 | 30 Oct 18:43 → paused after 5 items (~20:06) → finished 31 Oct 23:07 | Paddy's grade file (not public), sha `73c8d490…`, 18 saved backups |
| B3 | 216 | sheet 1 Nov 19:42 → final 3 Nov 21:23 | Paddy's grade file (not public) |
| B4 | 216 | 4 Nov 17:30 → finished ~21:37 | Paddy's grade file (not public), sha `d318cb3e…`, 12 backups |
| B5 | 216 | 5 Nov 10:50 → finished ~20:39 | Paddy's grade file (not public), sha `6c2e61ac…` (independent set), 19 backups |
| B6 | 324 | bundle 7 Nov 10:04 → grading folder 8 Nov 08:32 | B6 grading folder (not public) |

That is **1,284 held-out grades** (96 + 4 × 216 + 324), given between 29 October and 8 November, plus earlier development grading on 27 Oct. Each round's count matches its results or agreement file (B1 49/96; B2–B5 108 answers per arm, two arms; B6 N = 324). Every grade was given without knowing which prompt wrote the answer. The keys stayed sealed until he unsealed them: for example, the B4 key `a0cee69b…` and the B5 key `7a0cdcf5…` were still sealed after his grades were in.

**He froze the criteria before the runs.**
- D-047, the pass bar, was accepted on 29 Oct (`R/docs/DECISIONS.md`) before any prompt comparison.
- The B6 freeze was adopted on 7 Nov at 05:32 PST (`P/B6_FREEZE_ADOPTED_2026-11-07.md`, sha `ef0cb937…`), before any B6 item existed.

**He let agreement be measured before he ruled.**
- In B6, κ was computed first (0.460, `P/B6_AGREEMENT_2026-11-08/…`, sha `e4449e28…`, 8 Nov 10:30).
- He then adjudicated the 117 disagreements, finishing the evening of 8 Nov (adjudication merge handoff 22:39).
- In B3–B5 he reconciled under written rules, and moved his own grades where the rules said he should.

**He answered every hold with a decision.**

| Hold | His decision |
|---|---|
| B6 baseline pre-launch halt (7 Nov 06:43) | Fresh authorization at 06:50 (`P/B6_BASELINE_RUN_ATTEMPT2_2026-11-07.md`, sha `50bf6758…`) |
| Candidate audit HOLD | Documented exception, 08:28 (`P/B6_CANDIDATE_AUDIT_DISPOSITION_2026-11-07.md`, sha `e49e3b73…`) |
| B7 pin conflict (HOLD #1) | Option B, 12:36 (B7 HOLD #1 decision record, sha `2eb2638b…`) |
| Test-suite fault (HOLD #2) | Amendment A1, 12:45 (sha `ea7a7e4d…`) |

No hold was worked around.

**He kept the standard.**
- B5 led 72.0 to 41.5 on points and was still recorded NOT READY, because the crisis item failed. He accepted that.
- After B6, his B7 frame decision records that "standards are not lowered" (`P/2026-11-08-paddy-decision-b7-frame.md`, sha `a81d1132…`).
- Under D-023 the 145-word default stayed throughout.

**He named the drift.** On the morning of 9 Nov, he identified the pattern as an expansion loop in the Council Engine, before any Bench seat did. He said that Stop and Stay had drifted outside the project. He then decided the order himself:
1. Stay first.
2. A one-page governing note with one question per cycle, a four-engine check at each hand-off, a stop rule frozen before runs, and only he opens a next cycle.
3. Then, at most, one final B7.

**He set the governing note's terms; others wrote the words.**
- The Operator drafted the note.
- The Bench cut it.
- The stop rule's two sentences came from GrokBuild and Codex.
- Paddy approved the cuts at 9:29 AM and adopted v3 at 9:54 AM (`P/2026-11-09-ADOPTED_governing-note-v3.md`, sha `8f3dd0c2…`). The note is in this release as `GOVERNING_NOTE_v3.md`.

**He honoured the stop.**
- At 13:05 PST he chose "Write up and close B7 under the stop rule" (`P/2026-11-09-B7_CLOSE_DECISION.md`, sha `60d5a7c5…`), with a frozen fix ready to run.
- At 1:15 PM he asked for the negative result to be written up for release.

**He paced himself, sometimes.**
- He stopped grading B2 partway and resumed the next day.
- He closed nights rather than finish a round tired.
- On 9 Nov he asked for a pause and a reading of the core before B7 design went further (10:44 AM).

## Where it strained

These belong in the record as much as the above.

- **Fast approvals.**
  - All 18 B6 items were approved together at 05:46 PST with one word, "proceed" (`P/B6_SEALED_ITEMS_2026-11-07/APPROVAL_AND_SEAL_2026-11-07.md`, sha `c6ded746…`), although the frozen spec had said items and tags would be approved one by one.
  - The B6 freeze was adopted ten minutes after the preparation plan's mtime.
  - Several next-step slices were approved within about 20 minutes of a result.
- **Pace in minutes, not hours.** After every result from B3 on, the next design appeared within minutes: 18, about 20, 5 and 8 minutes, by file times. The B6 candidate's last three versions and the crisis-v3 config were written in the 24 minutes after B5's results.
- **The governing note's first hour.** The note was adopted at 9:54 AM on 9 Nov. Its first hour repeated the pattern it was written to stop: the Stay ended for design at 10:02, and a B7 design was on disk at 10:08, six minutes later, before the check the note required.
- **The Bench close replies were not independent.** Muse read GrokBuild's reply before writing (12:57 → 13:00 PST, 9 Nov), so the advice to close B7 was one judgment plus a concurrence.
- **Late hours.**
  - B2 grades closed at 23:07, B4 grading at ~21:37, and B6 RESULTS at 22:53.
  - The B7 frame was approved at 23:10, before the diagnostic that would have changed it.
- **His own rule not enforced.** D-047 asked for κ every round. It was not computed for B2–B5, and he did not ask for it.
- **Rules after grades.** B5's reconciliation rules were written after both grade sets were in, though before unblinding.
- **One human, who is also the author.** He was the only human grader of his own framework. His independence from it cannot be assumed, only disclosed.
- **Delegated checking.** On 31 Oct he waived line-by-line review of the Operator's end-of-day notes. This is reasonable for load, but it is less oversight.

## What this adds up to

The discipline here was real and costly in time: 1,284 blind grades, four answered holds, a held standard, and a stop he wrote down and kept. It was also one person's attention stretched across fourteen days, often late at night, with approvals that sometimes moved as fast as the agents. Both are true. The method's strength came from his rules. Its weak points are where those rules depended on a tired human acting quickly.
