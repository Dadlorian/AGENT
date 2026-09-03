# Future-State Conformance Questionnaire — how the pieces fit

An instrument for grading a future-state architecture deliverable produced in response to the brief. It turns "is this good?" into a measurable definition, by attacking every property from several angles that fail for different reasons.

## The one idea

**A single question is not a measurement.** Three questions answerable from the same paragraph are one question wearing three hats. So every property is examined from three or four angles, each answered by a *different artifact*:

| Angle | Answered by | Fails when |
|---|---|---|
| **Declaration** | a contract, schema, or signature | the property is named but never specified |
| **Demonstration** | a worked case including a refusal | it is specified but never exercised, so its edges are unknown |
| **Falsification** | a named breaking input | it is unfalsifiable, making it an intention rather than a contract |
| **Substitution** | a second, materially different adapter | the interface is shaped around its current implementation |

That cross-product is also why coverage is guaranteed: you cannot forget a question, you can only fail to declare a property.

## Files, and which ones you edit

| File | Role | Edit? |
|---|---|---|
| `properties.json` | 42 properties, one per design rule / core component / capability / seam / required output | ✅ **the only source of truth** |
| `generate.py` | crosses properties with angles, emits the questionnaire | ✅ rarely |
| `QUESTIONNAIRE.md` | **what you send** — 144 questions, self-contained | ❌ generated; edits are overwritten |
| `answers.blank.jsonl` | **send this too** — one empty row per question | ❌ generated |
| `questions.json` | flattened question list the checker reads | ❌ generated |
| `SKILL.md` | the answering protocol: evidence before verdict | ✅ |
| `check_answers.py` | grades a returned sheet, rolls up per property | ✅ |
| `answers.test.jsonl` | a deliberately broken sheet proving the checker catches things | — |

Regenerate with `python3 generate.py`. Grade with `python3 check_answers.py answers.jsonl`.

## Why JSON drives it rather than a hand-written document

144 hand-written questions drift out of alignment, and adding a fourth angle later means 42 separate edits. Here the template guarantees uniform coverage and per-property **overrides** carry the sharpness — 34 of the 144 are sharpened by a specific recorded incident, and each of those lands as the angle it belongs to rather than as a separate section.

## What ships and what stays

**Send:** `QUESTIONNAIRE.md` and `answers.blank.jsonl`. Both are self-contained — no internal identifiers, no product names, capabilities and standards only. They travel to anyone.

**Keep:** `check_answers.py`, and the rollup it computes. The brief's own design rule 6 says the grader is never visible to the graded; that applies to this instrument as much as to the system it grades. The responder should not be able to see how the triangle rolls up while answering it.

## The answer contract, in one paragraph

Bare yes / no / maybe is not an answer. Five verdicts — `CONFORMS`, `DEVIATES`, `SUPERSEDES`, `ABSENT`, `UNANSWERABLE` — and none may be recorded without evidence. Evidence is tiered `E1`–`E4`, and **a `CONFORMS` resting only on prose or inference is mechanically downgraded to asserted-but-unproven**. Every `CONFORMS` carries a falsifier; every `SUPERSEDES` carries a cost statement. All of it is checked by script rather than by judgement.

`SUPERSEDES` exists so a genuinely better design is not punished as non-compliant — it is a good outcome that simply carries a heavier burden than agreement.

`UNANSWERABLE` exists because questionnaires are wrong sometimes. When this method's ancestor ran at scale, **two of four rejections were defects in the checker rather than the work** — a 50% false-positive rate on the signal meant to be authoritative. Without an escape hatch a bad question becomes a false finding about a good design, so `UNANSWERABLE` records against the questionnaire and is reported separately.

## Reading the result

Per property, not per total:

- `PROVEN` — declared, demonstrated, and falsifiable
- `SHOWN` — declared and demonstrated, but nothing could disprove it
- `ASSERTED` — declared only; a claim
- `DEVIATED` — knowingly not done, with a reason
- `ABSENT` — no basis in the deliverable

A single score would hide the only distinction worth having. *"17 asserted, 3 proven"* says what to do next; *"63%"* does not. Read the clusters: gaps spread evenly mean an immature design, gaps concentrated in one group mean a specific blind spot.
