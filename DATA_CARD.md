# Data card

*Drafted by Grok Bot (Operator) from the project record; approved by Paddy Sham.*

## What the data is

Synthetic conversations ("items") written to test a small model on hard moments, and the grades given to the model's answers. No real person's crisis is in the data, and no model output reached a person in need.

## Items by round

| Round | Items | Written by | Use | Item text |
|---|---|---|---|---|
| B1 | 16 | The Operator (Grok Bot), a model | Grader calibration, v0 only | Published: `items/B1_ITEMS.md` |
| B2 | 18 | 16 by other AI models (Gemini, ChatGPT, Meta AI, Mistral, DeepSeek), 2 by the Operator | v3 vs v0 | Published: `items/B2_ITEMS.md` |
| B3 | 18 | Gemini | v4 vs v0 | Published: `items/B3_ITEMS.md` |
| B4 | 18 | Google AI Mode | v5.1 vs v0 | Published: `items/B4_ITEMS.md` |
| B5 | 18 | A fresh blind author with no exposure to held-out answers | v5.2.5 vs v0 | Published: `items/B5_ITEMS.md` |
| B6 | 18 | An isolated AI writer, kept apart from the prompts, that saw only the frozen spec | v5.2.8 vs v0, bare model as diagnostic | **Private** |

Item families included: a crisis signal, a request to stop, a request to act on an old permission, a false premise, a promise of permanence, and ordinary helpfulness. In B6, nine items were tagged harm-critical before the run.

**Sealing and approval.** Items were hashed and sealed before any model saw them. The rule was: "Do not show these items, or answers to them, to anyone writing or editing a prompt." The B1–B5 item files record approval item by item. The 18 B6 items were approved together with one word, "proceed", on 7 November at 05:46 PST.

**Reuse.** Each of B1–B5 was reused for prompt tuning after its test, so each gave one clean comparison. That is why their text can be published. Under the governing note, B6 items are now dev-only, but their text stays private.

## What is released (Paddy's decision: H1)

- **B1–B5 item text,** in `items/`: each item's id and the words that reached the model (the user's words and any context line). Grading lines, sources, approval lines and notes were left out; `items/README.md` says how the text was extracted. One internal file reference in a B2 item (HO2-10) was redacted as "[path removed]"; nothing else was altered. Items that speak as or to Paddy, or mention health or family, were reviewed by him on 9 November 2026 and kept as written.
- **B6:** `B6_PER_ITEM_AVERAGES.md`: for each of the 18 items, the family or tag where public, the harm-critical flag, the average score per arm (Pass 1, Partial 0.5, Fail 0, over six answers) and the harm-gate result. No item text. Per-answer counts are not published: they would need the sealed arm key.
- **Not released:** B6 item text; per-answer grades and counts; grading sheets; per-grader grade files; the arm keys; private notes; credentials; anything personal.
- **Raw model answers are not released.** No answer text from any round is in this release.

**Provider terms.** B2–B4 items were written by other AI models (Gemini, ChatGPT, Meta AI, Mistral, DeepSeek, and Google AI Mode). Their terms were read on 9 November 2026; OpenAI's and Google's restrict using outputs to train competing models, which CC BY 4.0 does not. Paddy accepted that tension and kept CC BY 4.0. See the README, "Provider terms". This was not a legal review.

## Answers and grades

- **Sampling:** one greedy answer plus five seeded samples per item per arm (temperature 1.0, top_p 0.95, top_k 64, max 400 tokens, seed 20261027).
- **Grades:** Pass, Partial or Fail against each item's written lines. Paddy graded every held-out answer blind: 1,284 grades (96 in B1, 216 in each of B2–B5, 324 in B6). Muse graded the same shuffled sheets separately. In B6, κ was 0.460 before reconciliation; Paddy then ruled the 117 disagreements, and that adjudicated sheet is a human adjudication record, not independent agreement.

## Known limits of the data

Eighteen items per round (sixteen in B1); six correlated answers per item, so the item is the unit. One human grader, who is also the framework's author, plus one AI grader. Many items were written by other AI models, and B1's by the Operator, which also wrote prompts. That shapes their style. Short conversations, mostly single-turn. Some items are written in the first person and mention family, partners or health; they are synthetic test scenarios, not accounts of real events; where Paddy is named, the situation was invented for the test.
