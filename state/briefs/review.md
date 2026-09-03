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

## Step 5: review
You change nothing; write only kb/ceremonies/<label>.json. Do not read other records for this row: you review independently.
For every row of every skill, record a finding for: (a) a sourced quote that is not a verbatim substring of the cited record, or a verbatim quote whose record does not support the row's claim; (b) a restatement of what another skill owns without naming it; (c) an uncited claim not marked proposed; (d) a definition of done that cannot fail, a measured_run that does not match its breakage text, or a criterion naming a missing path; run each measured criterion once (harness test.sh is safe) and confirm it passes; (e) a description whose trigger clauses do not fit the skill's scope; (f) proposed padding: generic advice or a reword of another row in the same skill; (g) a product named outside adapters, or a second adapter with the same execution model as the first. Include validate_skills.py --only output per skill.
Record shape: {"status_row":<row>,"reviewer":"<label>","skills":[...],"findings":[{"id":"R<row><part>-001","skill":"...","location":"best_practices[3]","severity":"high|medium|low","kind":"misquote|unsupported|restatement|uncited|dod|trigger|padding|adapter","evidence":"...","fix":"..."}],"metrics":{"rows_checked":n,"sourced":n,"proposed":n,"quotes_verified":n,"harness_runs":n},"summary":"..."}. Every finding names skill and location exactly. Reply in under 60 words: findings by severity and the two most important.
