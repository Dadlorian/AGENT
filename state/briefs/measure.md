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

## Step 3: measure
Only python3 tools/measure.py <skill> --breakage-cmd "<shell>" --restore-cmd "<shell>" may set status measured; never write status or measured_run by hand.
The criterion is one pure shell command chain run from the repo root (no prose, no backticks); prose moves to expected. When a harness serves the skill (harness/plan.json owner_skill or co_skills), the criterion is its gate plus its conformance swap, e.g. bash harness/<name>/test.sh && python3 harness/<name>/conformance.py --adapter dryrun --adapter second (read the README for the real flags).
The breakage is a real edit to the harness or fixture that makes the criterion fail (sed on one line), restored with git checkout <path>; the breakage text describes exactly that command. measure.py marks measured only if the clean run exits 0 and the broken run exits non-zero; if the broken run still passes, the breakage did not break: choose another.
Run measure.py commands one at a time. No harness for the skill: leave claimed and append "Gap: no harness covers this capability yet (STATUS row <row>)" to the criterion.
Record: kb/ceremonies/<label>.json with per skill status before and after, criterion, breakage command, measure.py last line.
