# Crew brief for STATUS row 71: polish one part of the folded skills

Read first: OWNER.md (the owner's rules, newest last), then this file, then docs/fold/plan.json (what folded into what). Do not commit or push. Touch only the skill directories your part lists. Your label is `71-polish-<part>`.

What happened: 103 skills were folded into 28 by tools/fold_skills.py. Each target keeps its base skill's body; every other former skill sits whole under the target's `folded` object in skill.json and renders to references/<former-name>.md. Nothing was rewritten yet. Your job, per skill in your part:

1. **Description, at most 60 words.** Say what the skill does and when to load it, in the "pushy" style the Agent Skills guidance asks for (name the situations and the words a caller would use), and name the folded former skills' subjects so a search for them still lands here. No product names. Strict YAML is enforced by the validator; the renderer quotes the value.
2. **Body under 500 lines.** `wc -l SKILL.md` after rendering. If over, move the longest table section of the body into a folded reference: the schema allows moving rows only by cutting them from the body's list and appending them, unchanged, to the matching list of the folded skill they belong with (or to a new `folded` entry named `<skill>-details` copying the base's name, layer, purpose, provenance and empty required lists). Never delete a sourced row.
3. **Warnings to zero.** `python3 tools/validate_skills.py --only <skill>` prints restatement warnings where two rows (body or folded) cite the same quote without naming each other. Fix by naming the sibling in the later row ("`<former-name>` (references/<former-name>.md) already states F-nnn; what this adds: ...") or by deleting the later row when it adds nothing. Deleting a row that adds nothing is preferred.
4. **composes_with stays as folded** (already remapped and symmetric). Do not touch definition_of_done, adapters, or any quote.
5. After every edit: `python3 tools/render_skill.py .claude/skills/<skill> && python3 tools/validate_skills.py --only <skill>` at zero errors and zero warnings under the skill's name.

Parts:
| Part | Skills |
|---|---|
| a | agentic-stack, core-components, seam-dispatch, seam-state, build-skill-authoring, build-evidence, build-ceremony |
| b | cap-isolation, cap-model-access, cap-durable-execution, cap-agent-runtime, cap-tool-access, cap-capability-packaging, cap-work-intake |
| c | cap-document-validation, cap-telemetry, cap-policy, cap-provenance, cap-errors, cap-identity, cap-scheduling |
| d | cap-idempotency, cap-state-persistence, cap-evaluation, cap-human-interaction, xc-guarantees, compose-workflow, compose-improvement-loop |

Record: kb/ceremonies/71-polish-<part>.json with status_row 71, agent, per skill: description_words, body_lines, warnings_before, warnings_after, rows_deleted, rows_moved. Ledger: python3 tools/kb.py ledger '{"kind":"ceremony","status_row":71,"ceremony":"71-polish-<part>","agent":"<model>","result":"<skills> skills, descriptions <= 60 words, bodies <= 500 lines, 0 warnings","status":"measured"}'.

Reply in under 60 words: skills done, max description words, max body lines, warnings after.
