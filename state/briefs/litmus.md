# Crew brief for STATUS row 66: write one part of the litmus questionnaire

Read, in this order, and nothing else in the repo: state/briefs/context-66.md (the owner's frame, PASS.md Part B verbatim with ids, the record shapes, the research rules), then docs/litmus/frame.json. Do not commit or push. Touch only your part file and your research file.

Your label is `66-litmus-<part>`. The parts:

| Part | Sections (source → fixed id) |
|---|---|
| a | F-b3-02 isolation · F-b3-03 model-access · F-b3-04 durable-execution · F-b3-05 agent-runtime · F-b3-06 tool-access · F-b3-07 capability-packaging |
| b | F-b3-08 work-intake · F-b3-09 document-validation · F-b3-10 telemetry · F-b3-11 policy · F-b3-12 provenance · F-b3-13 errors |
| c | F-b3-14 identity · F-b3-15 scheduling · F-b3-16 idempotency · F-b3-17 state-persistence · F-b4-02 concern-budget · F-b4-03 concern-identity |
| d | F-b4-04 concern-policy · F-b4-05 concern-provenance · F-b4-06 concern-telemetry · F-b4-07 concern-errors · F-b4-08 concern-idempotency |

Method, per section:
1. Research with web search (at least three searches per section: version and activity in the window, the mechanisms of deep use, the direction and alternatives). Write each result you rely on as one line in kb/research/litmus-<part>.jsonl before you cite it.
2. Decide the standard's settledness and say why, citing the records.
3. Write the future state: what a build inside the window should be doing with this element, tool-agnostic, in capabilities and standards. One paragraph, no more.
4. Write the direction: what is settling, what is being abandoned, what would be an error to build now.
5. Write 4 to 8 questions over at least 4 angles, always including depth and usage. Each question is answerable from evidence an answerer can produce; each says what aligned and what misaligned look like, so the score on the closed scale is decidable and not an opinion. A presence question alone is never enough; the owner's words: how you use it matters more than the fact that you used it.
6. Record every claim you could not source as a gap with the query that would source it.
7. Run `python3 tools/litmus_check.py check docs/litmus/parts/<part>.json` until it prints 0 errors.

Outputs: docs/litmus/parts/<part>.json as {"sections": [...]} and kb/research/litmus-<part>.jsonl. Ledger at the end: python3 tools/kb.py ledger '{"kind":"ceremony","status_row":66,"ceremony":"66-litmus-<part>","agent":"<model>","result":"<sections> sections, <questions> questions, <records> research records, 0 errors","status":"measured"}'.

Reply in under 80 words: sections, questions, research records, errors, and any section where research found no settled direction.
