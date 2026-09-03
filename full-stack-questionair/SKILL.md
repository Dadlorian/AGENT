---
name: conformance-answer
description: Answer or grade one question of the Future-State Conformance Questionnaire against a deliverable. Forces evidence before verdict and refuses to emit an incomplete row. Use once per question, or in a pass over a group.
---

# conformance-answer — one question, one evidenced row

This skill is the **answering protocol**, not the questions. The questions live in `QUESTIONNAIRE.md`, generated from `properties.json`. This governs *how* an answer is produced so that 144 answers are comparable to each other.

## The order is the point

Evidence is located **before** a verdict is chosen. Reversing these two is the entire failure mode this skill exists to prevent: a reader forms an impression, then goes looking for support, and finds it — because prose can support almost anything if you have already decided what you are looking for.

| # | Stage | Output |
|---|---|---|
| 1 | **Locate** | Find the passage in the deliverable that bears on the question. Quote it. If nothing bears on it, that is the finding — go to 4 with `ABSENT` |
| 2 | **Tier** | Classify what you found: `E1` contract/schema/signature · `E2` named section + worked example · `E3` prose claim · `E4` your own inference |
| 3 | **Falsify** | State what observation would disprove the property. Do this *before* the verdict, because a property with no disproof is not conformant, it is merely asserted |
| 4 | **Verdict** | Choose one, constrained by what stages 1–3 produced |
| 5 | **Emit** | One JSONL row. Incomplete rows are not written |

## Choosing the verdict

- `CONFORMS` — the deliverable does this. **Requires** evidence at `E1` or `E2`, and a falsifier. A `CONFORMS` at `E3`/`E4` is downgraded by the checker to asserted-only, so recording one is not a shortcut.
- `DEVIATES` — the deliverable knowingly does not do this. Requires what is given up.
- `SUPERSEDES` — the deliverable does something better than the question asks. **Requires a cost statement**: what the asked-for version buys, what this version preserves instead, and what it costs. Highest bar in the instrument, deliberately — a better answer is a good outcome, but it carries more proof than agreement does.
- `ABSENT` — no basis in the deliverable. Say it plainly; a blank is not an `ABSENT`.
- `UNANSWERABLE` — the question is malformed against this design. Requires the reason. **This records against the questionnaire, not the deliverable.**

## Three rules that stop the common failures

1. **A quote is not a citation.** The passage must say what the answer claims it says. A pointer that resolves to the wrong passage reads exactly like a correct one, and it is the failure mode that survives after every other check is in place.
2. **Never answer two angles from one passage.** If the Declaration quote is also the Demonstration quote, the Demonstration is `ABSENT`. The angles are separate because they are answered by different artifacts; collapsing them turns three measurements back into one.
3. **`ABSENT` is never a skip.** A skipped question makes an omission indistinguishable from a non-issue, which is the reason this instrument exists rather than a reading of the document.

## When grading a group rather than one question

Answer every question of one property before moving to the next, and answer them in angle order — Declaration, Demonstration, Falsification, Substitution. The order matters: knowing what was declared is what lets you judge whether the worked case actually demonstrates it, and knowing both is what lets you say what would disprove it.

Do not read ahead to the next property. Cross-property impressions are what produce a sheet that grades the deliverable's tone rather than its contracts.

## Finishing

Run `python3 check_answers.py answers.jsonl`. It enforces the contract mechanically and rolls each property up to `PROVEN` / `SHOWN` / `ASSERTED` / `DEVIATED` / `ABSENT`.

Read the clusters, not the totals. Gaps spread evenly mean an immature design; gaps concentrated in one group mean a specific blind spot, and that is the far more useful finding.
