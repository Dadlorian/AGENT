# Improver brief for STATUS row 66: apply the review to the litmus questionnaire

Read, in this order, and nothing else in the repo: state/briefs/context-66.md, docs/litmus/frame.json, kb/ceremonies/66-litmus-review.json, then the four part files docs/litmus/parts/{a,b,c,d}.json. You have not seen what this repository built and you must not look; the questionnaire stays a reflection on PASS.md Part B and the web. Do not commit or push. Touch only the part files, kb/research/litmus-<part>.jsonl (to add or correct a research record, with web search, never by retyping a fact) and your record.

Your label is `66-litmus-improve`. For every finding in the review, in id order:
- apply it: edit the part file (and a research file if the fix needs a record), and list the files touched; or
- decline it with a reason drawn from the frame or the context, never from convenience.
A block finding is applied unless applying it would contradict the frame. A duplicated question across a B3 and a B4 pair is resolved by rewriting one side to ask what the other does not (the concern side asks whether the guarantee rides on every unit of work through every entry unrequested; the capability side asks about the interface, the standard and the adapters), not by deleting a question below the frame's minimum. A missing angle is added as a new question with the section's next id. An anchor that readmits what it forbids is rewritten so aligned_looks_like and misaligned_looks_like exclude each other. A future_state marked sourced whose own gap disclaims it becomes proposed, with the word proposed in the text. A conflicting date is settled by a research record whose snippet states the date; the losing text is corrected and its record left in place.

After every part edit: `python3 tools/litmus_check.py check docs/litmus/parts/<part>.json` at 0 errors. At the end: `python3 tools/litmus_check.py check` (all parts, coverage on) at 0 errors.

Record: kb/ceremonies/66-litmus-improve.json with status_row 66, improver (your model), review_record "kb/ceremonies/66-litmus-review.json", applied (each: finding <review id>, change, files), declined (each: finding, reason), checker_after (the last line of the full check). Every review finding id appears exactly once across applied and declined. Ledger: python3 tools/kb.py ledger '{"kind":"ceremony","status_row":66,"ceremony":"66-litmus-improve","agent":"<model>","result":"<applied> applied, <declined> declined, <questions> questions, 0 errors","status":"measured"}'.

Reply in under 80 words: applied, declined, questions after, checker line.
