# Agent brief (read this file only; it digests OWNER.md, docs/acceptance/ceremony.json and the prior records)

# Owner feedback

Append one line per correction. Every agent reads this file before working. Newest last.

- 2026-09-03: Draw from the knowledge base; anything uncited is a gap to research, never an invented solution.
- 2026-09-03: STATUS.md is the view; keep it current in the same commit; Done rows go to the archive.
- 2026-09-03: Do not stop at ceremonies; on a problem use 1-3-1.
- 2026-09-03: Solve through the lens of usability and every state type, not in isolation.
- 2026-09-03: Name every task, agent, scope claim and ceremony record by its STATUS row id (42-sourcing-3a, never sourcing-03a).

Naming: your label, your record and your ledger entry start with the STATUS row id you serve (60-cap-review-a).
Never commit or push. Touch only the files your launch message lists. Never edit definition_of_done, adapters or composes_with unless your step says so.
After every skill edit: python3 tools/render_skill.py .claude/skills/<name> && python3 tools/validate_skills.py --only <name> -> zero errors, no new warnings under the skill's name.
Knowledge base lookups: python3 tools/kb.py show <id>; grep -i over kb/facts.jsonl (PASS.md, F-), kb/target-facts.jsonl (TARGET.md, T-), kb/reference-facts.jsonl (REF-), kb/research.jsonl (X-), kb/decisions.jsonl (D-), kb/architecture.jsonl (A-), kb/ledger.jsonl (L-).
Ledger at the end: python3 tools/kb.py ledger '{"kind":"ceremony","status_row":<row>,"ceremony":"<label>","agent":"<model>","result":"<one line>","status":"measured"}'.
Reply in under 80 words with the numbers your step names.

## Step 7: improve
Read the review record your launch message names. Every finding is applied or declined with a reason and the files touched.
Rules: restatements are fixed by a one-clause pointer naming the owner or by deletion, never rewording. Restate-and-extend rows are split so the uncited extension is its own proposed row, or the extension is deleted. A sourced quote must support the whole row. Definition-of-done status and measured_run come only from tools/measure.py; when a finding says the breakage text and the measured run disagree, rewrite the text to the exact command and re-measure. Findings the launch message marks as planted defects are recorded as applied by unplant after verifying the rows are gone. Aim for zero warnings per skill.
Record shape: {"status_row":<row>,"improver":"<label>","review_record":"...","applied":[{"id":"...","change":"...","files":[...]}],"declined":[{"id":"...","why":"..."}],"validator_after":{"<skill>":"n errors, n warnings"}}.
