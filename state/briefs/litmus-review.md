# Reviewer brief for STATUS row 66: review the litmus questionnaire before the owner reads it

Read, in this order, and nothing else in the repo: state/briefs/context-66.md (the owner's frame and PASS.md Part B verbatim), docs/litmus/frame.json, docs/litmus/questionnaire.json. You did not write the questionnaire and you have not seen what this repo built; keep it that way. Do not commit or push. Touch only your record.

Your label is `66-litmus-review`. You are judging questions, not answering them. For every section, check:

1. Decidable: could an answerer with the evidence_expected in hand place the answer on the closed scale without opinion? A question whose aligned_looks_like and misaligned_looks_like are the same fact with opposite adjectives is not decidable.
2. Depth over presence: does the section ask how the standard is used, not only whether? A section whose questions all reduce to "is X present" fails, whatever their angle labels say.
3. Tool-agnostic: does a future_state or question depend on a product where a standard exists? Name the row.
4. Window: is the direction claim about the window (2026-03-03 to 2026-09-03) and cited to a research record that actually says it? Read the cited record's snippet.
5. Distinct: does the concern section (B4) ask what the capability section of the same name (B3) does not, and vice versa? Name any pair that asks the same thing twice.
6. Idealistic, not incremental: does the future state describe what a build could reach today at the front of the window, or does it describe common practice? Name the rows that settle for common practice.
7. Missing angle: is there an angle the section needed and did not ask (for example, a guarantees question on an element every concern rides on)?

Record: kb/ceremonies/66-litmus-review.json with status_row 66, reviewer (your model), sections_checked, findings (each: id R66-nnn, section, question id or field, severity block/fix/nit, kind from the list above, evidence, fix), and a summary with counts by severity. Every finding names its evidence from the questionnaire text; no finding rests on what you believe a repo should contain.

Reply in under 80 words with the counts by severity and the three most important findings.
