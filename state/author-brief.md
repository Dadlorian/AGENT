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

Keep each skill.json focused, and treat these as checked budgets, not aspirations: 6 to 10 instructions, 3 to 10 invariants, 3 to 8 best practices, and roughly 3 to 10 rows in any table. Long material - a full JSON Schema, a table of standards, worked examples - goes in references/<file>.md in the skill dir, with a proposed instruction saying when to open it and stating that the skill body is enough without it. A schema longer than about 25 rendered lines is long material: put a summary shape in contract.shapes and the full one in references/.

## Defects found in ceremony 1 - do not repeat them

These are the review findings from wave 1. Each cost a fix; none should recur.

1. There are SEVEN layers, not six: root, core, cap, xc, seam, compose, build. `root` is reserved for
   agentic-stack alone (the schema's enum and tools/validate_skills.py both know it, and the validator
   rejects layer root on any other skill). Count them from the schema before you write a sentence that
   counts them.
2. Do not restate a fact that a skill under your builds_on already states. Cite the owning skill by
   name and the kb id, then add only what is new in your context. In wave 1 all four skills independently
   re-derived the same finding (F-a7-03) in their own words; a change to it would have had to land in four
   places. The rule: compose by name, not by copy.
3. Any machine-readable field you name in an invariant or an instruction must have a formal shape in the
   same skill's contract.shapes (JSON Schema 2020-12, origin proposed unless PASS.md gives the shape). Prose
   describing a field three times is not a specification: the next author has to code against it.
4. origin=sourced means every claim in the row is backed by the cited record, including its scope. Do not
   widen one concrete fact into a claim about a class of things ("a de facto standard can be...") and leave
   it marked sourced. Either narrow the row to what the record shows, or mark the generalization proposed
   and keep the fact as its example. The validator checks the quote, not the inference; that check is yours.
5. Write the description's trigger clauses so they fire on this skill's actual scope. "Load whenever you are
   about to write down a result" fires on nearly every sentence in the repo; name the artifact or the moment
   (a definition-of-done outcome, an entry in the evidence store) instead.
6. agentic-stack's own composes_with is empty by design and the validator exempts the root from the used_by
   symmetry check. Do not "fix" it, and do not read "Builds on: -" in the root skill as unused.

## What worked in wave 1 - keep doing it

- Every sourced quote verified as a verbatim substring of its cited record: 73 for 73. Copy the quote out of
  `kb.py show`, never retype it.
- Definitions of done were honestly labelled: claimed where the tool does not exist yet, measured only where
  the exact error strings were produced in a run and the session and date are named.
- Restating each design rule as a pass/fail test, once, in the root contract, and building on it rather than
  re-deriving it, is the pattern the other skills should follow for every shared fact.

## Reply

Reply in under 200 words: skills written, validator result for them, any manifest inconsistency found (report; do not edit the manifest), and any claim you wanted to make but could not source (list them as proposed items you added or omitted).
