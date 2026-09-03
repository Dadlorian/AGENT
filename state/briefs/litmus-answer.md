# Assessor brief for STATUS row 67: answer one part of the litmus questionnaire against this repo

Read first: docs/litmus/frame.json (the scale and the angles), then your sections in docs/litmus/questionnaire.json (only those; the section ids are in your launch message). Then read whatever in this repo the questions need: .claude/skills (skill.json is the data, SKILL.md the rendering), harness/ (interface, adapters, call.py, conformance.py, test.sh, README.md, provenance.json), docs/guides, docs/acceptance, docs/architecture, examples/end-to-end, kb/ (python3 tools/kb.py show <id>), PASS.md, TARGET.md. Do not commit or push. Touch only your answer file.

Your label is `67-answer-<part>`. You are measuring the gap between this repo and the future state each section states. You did not write the questions and you do not defend the repo: a low score with the evidence that shows it is the finding the owner wants; a high score without evidence is worthless and the checker refuses it.

Method, per question, in section order:
1. Read the question, its evidence_expected, aligned_looks_like and misaligned_looks_like.
2. Locate the evidence in the repo before choosing a score: a file and a verbatim quote from it, or a command you ran and its last line. Prefer commands that measure (a harness gate, a conformance run, a tool check) over prose that claims.
3. Score on the closed scale: -1 misaligned (built toward something that would not work or against the standard's direction: an error), 0 absent, 1 exists (nominal use, or direction not judgeable from the evidence), 2 aligned, 3 leading. Decide from the two anchors, not from impression.
4. Write the finding (one or two sentences: what the evidence shows against the anchors) and, for a score of 1 or below, the gap (what is missing) or, for -1, what is wrong.
5. Never quote what you did not read; never record a command you did not run. The checker re-reads every quote and re-runs every command.

One JSON object per line in docs/litmus/answers/<part>.jsonl:
{"question_id": "<id>", "score": <-1..3>, "label": "<scale label>", "evidence": [{"path": "<repo path>", "quote": "<verbatim>"} or {"command": "<shell>", "last_line": "<last non-blank line it printed>"}], "finding": "...", "gap": "..."}

Check: `python3 tools/litmus_answers.py check docs/litmus/answers/<part>.jsonl` until it prints 0 errors. Do not append to the ledger; the captain records your result when your file is accepted.

Reply in under 80 words: answers, counts by label, the misaligned question ids, and the one gap you would fix first.
