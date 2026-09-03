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

## Step 2: source
Goal: proposed rows at most 30 percent of the skill's rows (T-t9-02). Levers in order:
1. Delete padding: a proposed row that restates what a sibling or another skill owns (replace with a one-clause pointer naming the owner), generic engineering advice, or a reword of another row in the same skill. List every deletion with its reason.
2. Convert: origin sourced only when a verbatim quote from one kb record supports the claim itself; copy the quote out of kb.py show, never retype. A quote already used by a sibling under the same id triggers a restatement warning: name the sibling in the row instead.
3. Leave genuinely-ours rows proposed and append "Research query: ..." naming what would source it.
Operations and shapes that the governing standard itself defines can usually be sourced from that standard's X- records.
Record: kb/ceremonies/<label>.json with status_row, per skill proposed_before, proposed_after, converted, deleted, share_before, share_after, and a deletions list.
