You are authoring skills for /home/user/AGENT. Skills here are DATA, not prose. Do not commit or push.

Read fully, in order:
1. /home/user/AGENT/.claude/skills/agentic-stack/SKILL.md   (root contract, rendered; read its skill.json too to see the format in use)
2. /home/user/AGENT/schemas/skill.schema.json                (the schema you must conform to; read every field and $defs)
3. /home/user/AGENT/docs/skill-manifest.json                 (your assigned skills' layer, wave, purpose, links, notes_for_author)
4. /home/user/AGENT/docs/decomposition.md                    (build order, Dispatch/State designs, definitions of done with breakages, second adapters, open questions)
5. /home/user/AGENT/PASS.md                                  (the source; you will cite it only through kb ids)
6. skill.json of every skill your assigned skills build on (under /home/user/AGENT/.claude/skills/<name>/skill.json)

The knowledge base is the only source of truth you may cite:
  python3 tools/kb.py verify                  must pass before you start
  python3 tools/kb.py tree                    all entities with their edges and source fact ids
  python3 tools/kb.py show <id>               one record: exact text, line range, status
  grep -n '"section": "B3"' kb/facts.jsonl    find facts by section; grep entity names in kb/entities.jsonl
Read kb/meta.json and copy source.sha256 and heads into each skill's provenance.

Your assigned skills: __ASSIGNED__

For each, write /home/user/AGENT/.claude/skills/<name>/skill.json conforming to the schema, then render and validate:
  python3 tools/render_skill.py .claude/skills/<name>
  python3 tools/validate_skills.py

Rules the validator enforces (fix every error naming your skills; ignore only "not written yet" warnings about other skills):
- Every statement is either origin=sourced with sources (kb ids) AND a quote that is a verbatim substring of one cited record, or origin=proposed with the word "proposed" in its text. There is no third kind. If you cannot find a kb record for a claim, it is proposed, and you say so.
- composes_with.builds_on / used_by must equal the manifest exactly.
- Product names (LiteLLM, Firecracker, goose, Langfuse, Temporal, Postgres, Redis, gVisor, Restate, and so on) only in adapters[]. Everywhere else: capability and standard names. Adapter entities are E-adapter-* (today) and E-swap-candidate-* (second); find them with kb.py tree.
- Standards: contract.standards[] entries reference E-standard-* entities; version_status is "unverified" unless you fetched the spec (WebFetch is likely blocked; do not guess versions). url may be null.
- definition_of_done: concrete command/test, expected output, a concrete breakage, expected failure, status "claimed" (you cannot run the platform here). Take it from decomposition.md's row for your piece and make it precise.
- SKILL.md must be the render; never edit it by hand.
- description: 40..1024 chars, says what the skill covers and the situations that should load it, including phrasings that do not use the obvious keyword.

Content expectations per layer:
- core-: contract.operations (inputs/outputs, purity), contract.invariants (from B2 row and B1 rules), instructions for building and testing it, best_practices citing A7 findings where they bite.
- cap-: contract.standards, contract.operations the core imports, contract.shapes (JSON Schema 2020-12 sketches, origin proposed unless PASS.md gives the shape), contract.not_exposed, adapters[] with role today and role second (from manifest), instructions, best_practices, open_questions from decomposition.md that touch it.
- xc-: the guarantee as invariants, where the platform applies it, why a caller cannot decline it, instructions for wiring it, definition_of_done that proves it cannot be declined.
- seam-: the decomposition.md design refined into operations, shapes, invariants; adapters[] for today's implementation and the second; open_questions.
- compose-: instructions are the recipe for assembling lower layers; invariants are what a composition must preserve (rules 5, 6, 7); best_practices are the composer's judgment.
- build-: instructions are the discipline as steps with the reason for each; the definition_of_done proves the discipline itself can fail.

Two facets per item, not three. `<item>` is the ideal definition and also carries the usability section (how a human, an agent and an event reach it; minimal inputs and outputs; a worked call per way in; a worked rejection), with anything long in `<item>/references/usage.md` behind one proposed instruction saying when to open it; `<item>-implement` is how it is built here. There is no `-use` facet: the 21 planned ones were folded into their ideal skills on 2026-09-03 (kb/ceremonies/consolidation-review.json). The caller doctrine identical across all of them - the four entries of T6.2 through one envelope, one result or one problem object, compose upward, change configuration rather than adding an argument - is stated once in `cap-consumption`, the shared consumption contract: read it before writing a usability section, and name it instead of restating it.

Keep each skill.json focused, and treat these as checked budgets, not aspirations: 6 to 15 instructions on an ideal skill that carries the usability section and 6 to 10 on any other (tools/validate_skills.py still warns above 10; on those ideals the warning is expected and the reference file is the answer), 3 to 10 invariants, 3 to 8 best practices, and roughly 3 to 10 rows in any table. Long material - a full JSON Schema, a table of standards, worked examples - goes in references/<file>.md in the skill dir, with a proposed instruction saying when to open it and stating that the skill body is enough without it. A schema longer than about 25 rendered lines is long material: put a summary shape in contract.shapes and the full one in references/; if the material was dropped or never needed, delete the references/ directory rather than shipping an empty one. These are checked: tools/validate_skills.py warns when instructions, invariants or best_practices fall outside the budget, so clear every warning naming your skills before you close them.

## Defects found in ceremonies 1-11 - do not repeat them

Findings from waves 1 through 5 and ceremony 11's three fan-out groups (compose, xc, round2). Each cost a fix; none should recur. Items 2, 4, 8 and 14 recurred across ceremonies, so each carries the sharper check that would have caught it.

1. There are SEVEN layers, not six: root, core, cap, xc, seam, compose, build. `root` is reserved for
   agentic-stack alone (schema enum and validator both know it); count them there before you write the count.
2. Do not restate a fact a skill under your builds_on already states: grep that skill's skill.json for the id first, and open with "agentic-stack already states this (F-...)" and add only your consequence. Compose by
   name, not by copy - per citation, not per skill; warns when a row cites an id under the same quote as the root or a builds_on skill without naming it. A later-wave formalizing skill (an enforcement-chain, a
   placement skill) gets composed by name into every earlier skill restating its placement once it lands, not left for each to rediscover (C11X-002).
3. Any machine-readable field you name in an invariant or an instruction gets a formal shape in the same skill's
   contract.shapes (JSON Schema 2020-12, proposed unless PASS.md gives the shape). Prose thrice is not a spec.
4. origin=sourced covers the scope of the claim, not only its wording: do not widen one concrete fact into a claim
   about a class ("a de facto standard can be...") and leave it sourced. Run `python3 tools/kb.py show <id>` and read
   the whole sentence, subject included; if your row's subject is wider the row is proposed and the fact is its
   example. The validator checks the quote, not the inference.
5. Write the description's trigger clauses so they fire on this skill's actual scope: "whenever you write down
   a result" fires on every sentence in the repo; name the artifact or the moment instead.
6. agentic-stack's composes_with is empty by design and the root is exempt from the used_by symmetry check; do
   not "fix" it, and do not read "Builds on: -" in the root skill as unused.
7. Ceremony numbers are a counter global to the repository, never per-section, never reused: N is one more than
   the highest kb/ceremonies/ceremony-NN-review.json on disk; take the next unused one and say so. Same N ties
   review, improve, lessons, ledger, known-issues (`ceremony_check.py`); list first, every time - eleven sections running with a stale hint from the caller.
8. State an enumeration ONCE per skill and have every other row point at that list rather than re-list it. TARGET.md T1 lists three ways in (human, agent, event) and T6.2 four entries (human, event, schedule, external system or agent); they are different lists, so name which one you are citing. Where a skill's own shape already implies the wider door (a scan on a schedule, a worked example under a schedule actor), its definition_of_done and worked-entries section must assert T6.2's four, not T1's narrower three, and say what a schedule entry changes (starts root work) against an event (steers only). Four xc skills asserted only three (C11X-001); a fifth sibling not in that batch, xc-tenancy, carried the identical gap and was found only when a separate group reviewed it (C11R-003) - a fix landed on the skills a finding names does not clear the pattern from every skill that shares it; sweep siblings at the same layer, not only the batch under review.
9. A cap- ideal skill (no -implement suffix) carries its own adapters[] pair and a definition_of_done asserting
   `adapters_run >= 2`; defer to -implement only when PASS.md's adapter-today column is literally *absent*, in an open_question citing that row, as cap-identity does.
10. Adapting a sibling's template: reread the prose, not only the code fences, for a noun belonging to the donor skill (a "runtime" in a durable-execution skill). Nothing checks it.
11. A cap- ideal skill STATES design rule 6, it does not merely satisfy it: carry a not_exposed row citing
   F-b1-07 saying what the grader rule forbids on this interface (the criterion never travels in a completion
   request, a document handle, a DecisionRequest's context). Warns when the row is missing.
12. An E- id in an adapter row's sources belongs to the same capability row as the adapter: E-adapter-jsonl-hash-
   chain (State persistence, F-b3-17) in a Provenance row sends a reader to the wrong B3 row; siblings are fine, warns when the entity's kb sources do not overlap the row's.
13. Every ideal facet carries the usability section, so meet its bar: a worked instance for EACH of TARGET T1's
   three ways in (declared_by / actor `user:`, `agent:`, `service:` or `schedule:`) and a worked rejection as an
   actual `urn:agentic:problem:` object, not prose pointing at cap-errors. Both may live in usage.md. Warns.
14. A problem `type` is not yours to invent. Before writing `urn:agentic:problem:<suffix>` anywhere, check the
   ten-row closed registry in docs/decomposition.md 2.1.6 and reuse the row that fits (a scope refusal IS
   `policy-denied`). If none fits, do what core-graph did: an open_question naming the row to add, "proposed and
   pending registration" where stated, and the registered type returned meanwhile. Warns per suffix.
15. A contract.standards row's `version` is a value a reader scans, not the sentence explaining it: put the
   version a record names, or "unverified", in `version`, and which record named it, whether the spec was
   fetched and which skill owns the row in `version_note`, rendered as a footnote. Warns above 60 characters.
16. An adapters[].entity id is not yours to mint quietly. Run `python3 tools/kb.py tree` for your capability first:
   reuse a real entity of the same B3 row where one exists; where none exists (wave-4c's xc--implement skills),
   record the gap as a 1-3-1 open_question and say in maps_to the id is proposed, never under `entities`. Warns per unmarked minted id.
17. An `-implement` facet's breakage breaks something the BUILD owns - the wiring, one migration stage, a
   binding, the gate - never a repeat of its ideal facet's contract violation: two identical breakages prove
   one failure mode twice. seam-dispatch/-implement is the worked pair. Warns on an outright copy.
18. Two skills at the same layer can embed one concept independently with no builds_on link between them (an
   operator's approval/loop shape re-derived inside compose-operators versus the owning gate/loop skill's own
   shape). Reuse the owning skill's names and enum values verbatim and name it in prose regardless of builds_on -
   compose-operators's termination and approval shapes did not, until ceremony 11 (C11C-001, C11C-002).
19. A REF- id alone never grounds origin=sourced, even though the Reference example section below already says so: the validator now errors on it ("reference-only citation"), and it recurred in three rows across two skills in one small batch anyway (C11R-002) - grep every row whose `sources` is REF- only and mark it proposed before you call a skill done.
20. A composition that names a cited skill's operation as "reused unchanged" or its vocabulary as reused "verbatim" is a claim to verify, not a fact to trust: compose-improvement-loop claimed compose-loop's terminated_by enum verbatim, then declared a fourth value (verdict_fail) neither that enum nor this skill's own instructions ever produced, leaving its definition_of_done's expected output unreachable from the contract (C11R-001, block). Diff the enum, not just the citation.

## What worked in waves 1 to 5 and ceremony 11's compose/xc/round2 groups - keep doing it

- Every sourced quote verified as a verbatim substring of its cited record: 73/73 in wave 1, 430/430 in wave 4a, 122/122 in wave 4c, ~60 ids in wave 5, 60 ids in the wave-7 compose ceremony and 96 rows in round2 (178 rows total, 6 skills), no invented problem types since 4b. Copy quotes out of `kb.py show`, never retype them.
- Definitions of done were honestly labelled: claimed where the tool does not exist yet, measured only where the exact error strings were produced in a run and the session and date are named; the wave-7 compose ceremony re-ran compose-operators' claimed measurement and reproduced it exactly.
- Each design rule is a pass/fail test stated once in the root contract and built on, not re-derived - check that across siblings at the same layer too, not only up to a builds_on parent (item 18).

## Reply

Reply in under 200 words: skills written, validator result for them, any manifest inconsistency found (report; do not edit the manifest), and any claim you wanted to make but could not source (list them as proposed items you added or omitted).

## When something blocks you (TARGET T5, cite T-t5-02)
Define the problem in one line. List the three best solutions that serve the goal. Pick the recommended one and proceed; record the choice as a proposed row or an open_question with the deciding evidence. If none is clearly best, drop the two weakest, find two more, repeat. Never stop and wait.

## Consumption reference (TARGET T6)
examples/end-to-end/ is the reference for how the platform is consumed: one entry envelope for human, event, schedule, and external entries; an agent registry keyed by what each agent is good at and its model class; workflows composed from operators; a runner. Skills in the seam-, compose-, and cap- layers must stay consistent with it or record the disagreement as an open_question with the change they propose.

## Reference example (owner-supplied, not a definition)
docs/reference/composable-plan.md is one worked answer to the problems this platform solves. It is citable as REF- ids (kb/reference-facts.jsonl; grep that file). A REF- citation is an example followed, not a source: rows that rest on it are origin=proposed and cite the REF- id. Section 12 of the reference (REF-12-*) maps its concepts to our skills and names a gap per skill; if your skill is in that table, address its gap row. Take the shapes and the failures; leave its field names, layer count and engines. Composition skills (compose-loop, compose-operators, compose-approval, compose-agent) must state the stop-versus-cap distinction (REF-5-3-*), the depth bound at resolve time (REF-5-2-*), cost summed up the tree, and that internal events steer but never start (REF-3-4-*).

## STATUS.md is the owner's view
Every commit that changes a work item's state updates its STATUS.md row in the same commit. Run python3 tools/status_check.py before committing.
Done rows are archived by python3 tools/status_archive.py in the same commit; row numbers never change.
Read OWNER.md first: one line per owner correction; each line overrides anything here that contradicts it.
Before launching an agent the orchestrator claims its file scope with python3 tools/scopes.py; an overlapping claim is refused.
Every checkpoint runs python3 tools/status_check.py --freshness and fails on a stale row.

## Naming (owner rule, 2026-09-03)
Every task, agent label, scope claim and ceremony record starts with the STATUS.md row id it serves: 42-sourcing-3a, 28-harness-1-review. scopes.py refuses any other label. Records carry "status_row".

## Lesson 59 (build layer acceptance, 2026-09-03)
A definition_of_done.criterion is one shell command chain, nothing else; prose goes in expected. The breakage text names exactly the command measure.py runs. Only measure.py sets status measured.

## Agent briefs (2026-09-03)
Launch messages point an agent at one file under state/briefs/ (source, measure, review, improve) instead of the six records it used to read; the brief digests OWNER.md, the ceremony template and the method notes. Regenerate the briefs when a rule changes.
