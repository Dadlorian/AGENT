# Captain brief (crew pattern, owner rule 2026-09-03)

You are the captain for one ceremony step on one STATUS row. You start with a small context and you keep it small: you are the shared prefix every crew member inherits, so read only what every crew member needs and nothing else.

WHY, measured, because this rule was written 2026-09-03 and did not hold on 2026-09-04: cache_read is
re-billed on every assistant turn at the full prefix size. Run wf_8d4230e8-999 spent 1,110,376,052
tokens of which 97.8% was cache_read and 2.1% was cache_creation -- the average token was re-billed
46 times (opus 54, sonnet 39, haiku 14, tracking turn-heaviness, not model price). Forking does NOT
avoid that: a fork pays your whole prefix on every one of its own turns, so three forks off a large
captain cost three times that prefix. Fork saves rediscovery, not carriage. Keeping this context
small is the half that saves tokens, and it is the half nothing checks. See state/briefs/one-three-one.md.

1. Read state/briefs/<step>.md (the step's method) and the launch message's list of skills and parts. Read nothing else unless every crew member would need it.
2. Claim scopes: python3 tools/scopes.py claim <row>-<layer>-<step>-<part> <paths...> for each part (labels start with the STATUS row id).
3. Fan out: launch one crew member per part with the Agent tool using subagent_type "fork" (so it inherits this context and re-reads nothing), run_in_background true, and a prompt of at most five lines: the part label, its skill list, its record path, and "follow the step brief already in your context". If "fork" is refused, fall back to subagent_type "general-purpose" and put the brief path in the prompt.
4. Collect every reply. For each part: python3 tools/validate_skills.py --only <skill> for its skills (zero errors), then python3 tools/scopes.py release <label>.
5. Write kb/ceremonies/<row>-<layer>-<step>.json: status_row, step, parts, per-part totals copied from the crew replies, validator results. Append one ledger record for the step. Do not commit or push.
6. Reply in under 80 words: parts done, totals, anything refused or failed.
