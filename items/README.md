# Held-out items: what is published here

*Drafted by Grok Bot (Operator) from the record; approved by Paddy Sham.*

Paddy's decision for held-out data is **H1**: publish the item text for rounds B1–B5, and keep B6 item text private.

| File | Round | Items | Source file in the record | sha256 (16) |
|---|---|---|---|---|
| `B1_ITEMS.md` | B1 | 16 | `R/evals/held-out/held-out-v0.md` | `05a5a20689e19778` |
| `B2_ITEMS.md` | B2 | 18 | `R/evals/held-out/held-out-b2.md` | `044b0adcc2eb8ff0` |
| `B3_ITEMS.md` | B3 | 18 | `R/evals/held-out/held-out-b3.md` | `fe0f896f1e960b4f` |
| `B4_ITEMS.md` | B4 | 18 | `R/evals/held-out/held-out-b4.md` (matches its seal file) | `d6da34d5a01494a4` |
| `B5_ITEMS.md` | B5 | 18 | `R/evals/held-out/held-out-b5.md` (matches its seal file) | `1a9ee644c59dcd13` |

**Why B1–B5 can be published.** Each of these sets was reused for prompt tuning after its test, so none of them is a clean held-out set any more.

**How the text was extracted.** The record files mix item text with grading lines. For each item, only its id and its "Prompt / setup" text were copied, unchanged. That text is the user's words plus any "(context: …)" line, and the record states that only these reach the model. Everything else was left out: Pass, Partial and Fail lines; grading rules; source quotes and internal file paths; requirement references; approval lines and message references; author and Operator notes; and earlier wordings that were replaced before the run. Each prompt was checked to appear verbatim in its source file.

**One redaction.** One internal file reference inside a B2 item (HO2-10) was replaced with "[path removed]". Nothing else in any item was altered.

**Not here:** model answers, grades, grading sheets, keys, and any B6 item text. Raw model answers are not released.

**These are synthetic test conversations.** Some are written in the first person, mention family members, partners or health, or address "Paddy" by name. They are test scenarios, not accounts of real events; where Paddy is named, the situation was invented for the test. They were written to test how a model handles such moments.

**Flagged items: reviewed.** Paddy reviewed the items that speak as or to him, mention health or family, or refer to his past, on 9 November 2026. He kept them as written and approved the use of his name in them.

**Provider terms.** B2–B4 items were written by other AI models (Gemini, ChatGPT, Meta AI, Mistral, DeepSeek, and Google AI Mode). Their terms were read on 9 November 2026, not by a lawyer; see the main README, "Provider terms". Each file names the model that wrote its items.
