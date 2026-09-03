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

Keep each skill.json focused, and treat these as checked budgets, not aspirations: 6 to 10 instructions, 3 to 10 invariants, 3 to 8 best practices, and roughly 3 to 10 rows in any table. Long material - a full JSON Schema, a table of standards, worked examples - goes in references/<file>.md in the skill dir, with a proposed instruction saying when to open it and stating that the skill body is enough without it. A schema longer than about 25 rendered lines is long material: put a summary shape in contract.shapes and the full one in references/. These are checked: tools/validate_skills.py warns when instructions, invariants or best_practices fall outside the budget, so clear every warning naming your skills before you close them.

## Defects found in ceremonies 1-5 - do not repeat them

Review findings from waves 1, 1a, 2, 3a and 3b. Each cost a fix; none should recur. Items 2 and 4 recurred
across ceremonies, so both carry the sharper check that would have caught them.

1. There are SEVEN layers, not six: root, core, cap, xc, seam, compose, build. `root` is reserved for
   agentic-stack alone (the schema's enum and the validator both know it). Count them from the schema
   before you write a sentence that counts them.
2. Do not restate a fact a skill under your builds_on already states: cite the owning skill by name and the
   kb id, then add only what is new here. Compose by name, not by copy. The check is per citation, not per
   skill: before writing a row, grep the builds_on skill's skill.json for the id you are about to cite, and
   if it is there, open with "agentic-stack already states this (F-...)" and add only your consequence.
   tools/validate_skills.py warns whenever a row cites an id under the same verbatim quote as the root
   contract or a builds_on skill without naming it (adapter, open-question and operation rows included). A
   warning is not always a defect - a sibling may cite the same record for its own point - but read each one
   and either name the owner or convince yourself the row is your own.
3. Any machine-readable field you name in an invariant or an instruction gets a formal shape in the same
   skill's contract.shapes (JSON Schema 2020-12, proposed unless PASS.md gives the shape). Prose describing
   a field three times is not a specification: the next author has to code against it.
4. origin=sourced means every claim in the row is backed by the cited record, including its scope: do not
   widen one concrete fact into a claim about a class ("a de facto standard can be...") and leave it sourced.
   Run `python3 tools/kb.py show <id>` and read the whole sentence the quote sits in, subject included; if
   your row's subject is wider, the row is proposed and the fact is its example. The validator checks the
   quote, not the inference. F-part-c-03 says "a first-cut design for Dispatch and State", no more.
5. Write the description's trigger clauses so they fire on this skill's actual scope: "whenever you write
   down a result" fires on every sentence in the repo; name the artifact or the moment instead.
6. agentic-stack's composes_with is empty by design and the root is exempt from the used_by symmetry check.
   Do not "fix" it, and do not read "Builds on: -" in the root skill as unused.
7. Ceremony numbers are a counter global to the repository, never per-section and never reused: N is one more
   than the highest kb/ceremonies/ceremony-NN-review.json on disk. If a caller hands you a number that is
   already taken by another section, take the next unused one and say so - obeying it overwrites a closed
   ceremony. The same N ties the review, improve, lessons, ledger and known-issues records together, and
   `python3 tools/ceremony_check.py` reports a numbering problem when it does not. The number a runner hands
   you has now been stale four sections running: list the directory before you write anything.
8. State an enumeration ONCE per skill and have every other row point at that list rather than re-list it:
   cap-errors-use named three entry kinds in an invariant while asserting four in the same sentence.
   TARGET.md T1 lists three ways in (human, agent, event) and T6.2 lists four entries (human, event,
   schedule, external system or agent); they are different lists, so name which one you are citing.
9. A cap- ideal skill (no -implement or -use suffix) carries its own adapters[] pair and a definition_of_done
   that runs over both and asserts `adapters_run >= 2`. Defer the pair to -implement only when PASS.md's
   adapter-today column is literally *absent*, and then say so in an open_question citing that row, as
   cap-identity does; the validator warns when a cap ideal skill has neither.
10. When you adapt a sibling's near-identical template (the -use skills share a definition_of_done shape),
   reread the prose, not only the code-fenced strings, for a noun belonging to the donor skill - a "runtime"
   surviving into a durable-execution skill whose product is an orchestrator. The check still passes.
11. A cap- ideal skill STATES design rule 6, it does not merely satisfy it: carry a not_exposed row citing
   F-b1-07 saying what the grader rule forbids on this interface (the criterion never travels in a
   completion request, a document handle, a DecisionRequest's context object, a schedule declaration). The
   validator now warns when the row is missing, so no reader has to infer the rule by comparing siblings.
12. An E- id in an adapter row's sources belongs to the same capability row as the adapter: citing
   E-adapter-jsonl-hash-chain (State persistence, F-b3-17) in a Provenance adapter row sends a reader to the
   wrong row of the B3 table. Sibling entities of your own capability are fine; the validator now warns when
   a cited adapter or swap-candidate entity's kb sources do not overlap the row's.

## What worked in waves 1 to 3b - keep doing it

- Every sourced quote verified as a verbatim substring of its cited record: 73 for 73. Copy the quote out of
  `kb.py show`, never retype it.
- Definitions of done were honestly labelled: claimed where the tool does not exist yet, measured only where
  the exact error strings were produced in a run and the session and date are named.
- Each design rule is a pass/fail test stated once in the root contract and built on, not re-derived; that
  is the pattern to follow for every shared fact.
- Reviewers re-ran definitions of done in waves 1a, 3a and 3b and reproduced the recorded output and exit
  codes exactly, breakage included. Write the criterion so someone else can run it from the skill alone.
- Waves 3a and 3b held claimed-versus-measured under pressure: where the capability does not run at all
  today, the check is recorded as starting red rather than dressed up as passing, and wave 3b's four
  measured claims were each re-run by the reviewer and reproduced exactly, tree left clean.

## Reply

Reply in under 200 words: skills written, validator result for them, any manifest inconsistency found (report; do not edit the manifest), and any claim you wanted to make but could not source (list them as proposed items you added or omitted).

## When something blocks you (TARGET T5, cite T-t5-02)
Define the problem in one line. List the three best solutions that serve the goal. Pick the recommended one and proceed; record the choice as a proposed row or an open_question with the deciding evidence. If none is clearly best, drop the two weakest, find two more, repeat. Never stop and wait.

## Consumption reference (TARGET T6)
examples/end-to-end/ is the reference for how the platform is consumed: one entry envelope for human, event, schedule, and external entries; an agent registry keyed by what each agent is good at and its model class; workflows composed from operators; a runner. Skills in the seam-, compose-, and cap- layers must stay consistent with it or record the disagreement as an open_question with the change they propose.
