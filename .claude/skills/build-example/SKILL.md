---
name: "build-example"
description: "Author one of the seven user-view example areas as a runnable artifact: a six-part README, the four doors, dry-run cells whose call shape matches live, visible checks inside and deciding checks outside, provenance per example, and the litmus sections it moves. Load it before adding or changing anything under examples/, or when showing how the platform is consumed."
---

# build-example

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make every element's example a thing a builder can actually run, inside the end-to-end example or beside it, so the platform's user view is demonstrated and graded rather than described. | sourced | `T-t10-07` "Every element has an example and an integration guide that a builder can run, inside the end-to-end example or beside it." |

## Entities

| Entity |
|---|
| `E-standard-json-schema-2020-12` |
| `E-standard-rfc-9457-problem-details` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | - | `F-b3-09`, `X-litmus-b-009` |
| `E-standard-rfc-9457-problem-details` | RFC 9457 | unverified | - | `F-b3-13`, `X-litmus-b-022` |

- `E-standard-json-schema-2020-12` version note: The dialect an example's four entry documents validate against; unverified because no specification was fetched by this session. cap-document-validation owns the row; what this skill requires is only that the four documents pass one published validator, which a language-agnostic conformance suite makes a measurable question rather than a preference.
- `E-standard-rfc-9457-problem-details` version note: The shape of the worked rejection an example shows in its what-the-user-sees table; unverified, no specification fetched here. cap-errors owns the closed registry of types, and an example reuses a registered one rather than minting a suffix of its own.

### Shapes (JSON Schema 2020-12)

**example-provenance (proposed; one file per example, examples/<area>/provenance.json)** (proposed; sources: `X-litmus-d-005`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:build:example-provenance:0.1",
  "title": "example-provenance",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "area",
    "doors",
    "cites",
    "measured",
    "claimed",
    "litmus_sections"
  ],
  "properties": {
    "area": {
      "enum": [
        "run",
        "ask",
        "watch",
        "steer",
        "progress",
        "done",
        "improve"
      ]
    },
    "doors": {
      "type": "array",
      "minItems": 4,
      "uniqueItems": true,
      "items": {
        "enum": [
          "human",
          "event",
          "schedule",
          "external"
        ]
      }
    },
    "cites": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string",
        "pattern": "^(F|E|R|T|X|REF)-"
      }
    },
    "measured": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string"
      }
    },
    "claimed": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "litmus_sections": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string"
      }
    },
    "visible_checks_counted": {
      "type": "integer",
      "minimum": 1
    }
  }
}
```

**example-readme (proposed; the six-part shape stated once, so no other row re-lists it)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:build:example-readme:0.1",
  "title": "example-readme",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "area",
    "question",
    "sections"
  ],
  "properties": {
    "area": {
      "$ref": "urn:agentic:build:example-provenance:0.1#/properties/area"
    },
    "question": {
      "type": "string",
      "minLength": 1
    },
    "sections": {
      "type": "array",
      "minItems": 6,
      "maxItems": 6,
      "items": {
        "type": "object",
        "required": [
          "heading",
          "rows"
        ],
        "properties": {
          "heading": {
            "enum": [
              "ideal",
              "standards",
              "the-call",
              "what-the-user-sees",
              "composition",
              "extension-points"
            ]
          },
          "rows": {
            "type": "array",
            "minItems": 1
          }
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Four entries cover nearly every situation: a human, an event, a schedule (time), and an external system or agent, and all four enter through the same shape. agentic-stack states that rule and build-evidence tests it as entry conformance; an example is where it is exercised, so an area that shows one door has shown a feature, not the platform. | sourced | `T-t6-02`, `T-t10-07` "Four entries cover nearly every situation: a human, an event, a schedule (time), and an external system or agent." |
| Proposed: the four doors are on disk, not in prose. examples/<area>/entries/ carries one document per door, each validating against the entry schema the reference example already publishes, and the area's own check runs every one of them; a door described in the README and absent from entries/ is a claim, not an example. Research query: unresearched; this is our directory convention over the four-entry rule. | proposed | `T-t6-02` "All four enter through the same shape." |
| Proposed: an example's README carries exactly the six headings the example-readme shape enumerates, in that order, each rendered as a table. The enumeration is stated once in that shape and every other row points at it. A seventh heading means the area is carrying material that belongs in a skill or a design document, and a missing one means the example answers less than the area's question. Research query: unresearched; the six-part shape is this repo's own reading of what a consumer needs to see. | proposed | - |
| In an example's six tables, name capabilities and standards, never products: a product name may appear only in an adapter row or in the standards table, which is the rule agentic-stack fixes for the whole repository and which an example is unusually likely to break, because the thing a reader runs is always some particular implementation. | sourced | `F-part-c-09` "name capabilities and standards, never products" |
| Proposed: an example runs on dry-run cells selected by configuration, and the line a reader copies is the same line the live cell takes. Swappability is a tested property, and the example is the one place a reader can see both call shapes are one shape; build-evidence carries the adapter-pair discipline, and what fails here is subtler than a missing adapter - a call line that only works against the dry-run cell means the pair was never real. Research query: unresearched beyond the adapter-pair rule this rests on. | proposed | `F-b1-04` "Swappability is a tested property" |
| Most tasks provide a visible feedback surface for use during development while reserving stricter hidden checks for final scoring, and an example is built the same way: bash examples/<area>/test.sh is the visible check a reader runs, and the deciding check is held out, roughly a third to a half of the deciding set in current practice. | sourced | `X-unit-design-023`, `X-unit-design-022` "most tasks provide visible feedback surface for agent use during development while reserving stricter hidden checks for final scoring" |
| Proposed: a test.sh that counts zero checks is a defect, not a pass. The visible check prints passed N, failed 0 where N counts checks that actually ran, and the gate asserts on N rather than on the exit code - build-evidence owns that rule for every criterion in the repository, and the consequence for an example is that the index reports a gutted area as a count of zero instead of a green row. Research query: unresearched; our own reading of the structurally-green finding for example directories. | proposed | `F-a7-03` "A deterministic gate can be structurally green and mean nothing" |
| Proposed: every example carries a provenance.json in the example-provenance shape, naming the records it cites, what its test measures, what it only claims, and the litmus sections it must move. A provenance predicate names the producing identity, the instructions and parameters, and the digests of every input, and an example that cannot say which section it moved has produced a demonstration rather than evidence. Research query: unresearched; the litmus_sections member is this repo's addition to the predicate shape. | proposed | `X-litmus-d-006` "A provenance predicate names the producing identity, the instructions and parameters, and the digests of every input" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| The deciding check never lives inside examples/<area>/. The grader is never visible to the graded, so the held-out check and the criterion body sit outside the directory the example publishes; build-evidence carries the opaque criterion_ref this rests on, and the example's README may say that a hidden check exists and how many, never what it asserts. | sourced | `F-b1-07` "The grader is never visible to the graded." |
| Proposed: no live credential, live endpoint or vendor client is reachable from an example. The reader is given the call shape and a dry-run adapter chosen by configuration, so an example that would reach production by changing nothing but a key is a distribution channel for secrets rather than a demonstration. Research query: unresearched; our own convention for example directories. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Pick the area from the seven the example-provenance shape enumerates and write, in one line, the question its user is asking. If that line names a capability rather than something a person or a system is doing, you have grouped by capability again: rewrite it or pick a different area. | Proposed: the seven areas exist because a consumer arrives with an activity, not with an interface name, and an example indexed by capability sends them back to the very map the example was meant to replace. Research query: unresearched; the seven-area grouping is this repo's own decomposition of the user's view. | proposed | - |
| 2 | Fill the ideal and standards tables from the litmus questionnaire sections the area covers, quoting their future_state and standard rows and citing the record ids, and list those section ids in provenance.json under litmus_sections. | Proposed: the example's job is to move a named section, and a section is scored against its own future-state text, so a paraphrase cannot be scored at all. Naming the sections up front also makes the areas' coverage a count rather than a judgement. Research query: unresearched; the scoring scale is the questionnaire's own. | proposed | - |
| 3 | Build one entry document per door under examples/<area>/entries/ and validate all four with the reference example's own schema and validator; reuse its schemas, entries and runner rather than copying code you can call. | All four enter through the same shape, which is exactly the property a copied-and-edited runner destroys quietly: two runners drift and the four documents stop proving anything about one shape. agentic-stack states the rule and build-evidence tests it. | sourced | `T-t6-02` "All four enter through the same shape." |
| 4 | In the call table, write the one line a caller types at each door beside the document that line produces, and check that none of the four needs a client library this repository wrote. | A caller needs no client library we wrote; if integration requires our SDK a boundary is bespoke where a standard existed, and an example is where that shows up first, because the call line is the thing a reader copies. build-evidence cites the same rule for interface versioning. | sourced | `F-b1-05` "A caller needs no client library we wrote" |
| 5 | Select every adapter from the harnesses by configuration, keep the call shape identical to the live one, and keep each product name inside an adapter row or the standards table. | agentic-stack fixes that products belong in the adapter column only; an example breaks that rule more easily than a skill does, since the thing a reader actually runs is always one particular implementation and the temptation is to name it in the prose that explains the run. | sourced | `F-part-c-09` "name capabilities and standards, never products" |
| 6 | Write examples/<area>/test.sh as the visible check: dependency-free, offline, printing passed N, failed 0 with N counting the checks that actually ran, and gate on that count rather than on the exit code. | A deterministic gate can be structurally green and mean nothing, which build-evidence states as the repository-wide rule that a criterion asserts on a non-zero count of things actually checked. An example is the case where a green run is most persuasive and least examined, so the count is what the index reads. | sourced | `F-a7-03` "A deterministic gate can be structurally green and mean nothing" |
| 7 | Keep the deciding check outside examples/<area>/, and let the example's own directory hold only what the reader and the graded unit may both see. | Stronger agents can find exploitable weaknesses such as retrieving solution artifacts or tampering with tests, so a deciding check shipped beside the thing it grades is a check that has already been read. What the README may carry is that a hidden check exists and how many, never its content. | sourced | `X-unit-design-025`, `F-b1-07` "stronger agents can find exploitable weaknesses such as retrieving solution artifacts or tampering with tests" |
| 8 | Write examples/<area>/provenance.json in the example-provenance shape: the record ids cited, what the test measures, what is only claimed, the doors covered and the litmus sections moved. | A provenance predicate names the producing identity, the instructions and parameters, and the digests of every input; an example is a produced artifact like any other, and separating measured from claimed in the same file is what stops a run that printed green from being read later as a run that proved something. | sourced | `X-litmus-d-006` "A provenance predicate names the producing identity, the instructions and parameters, and the digests of every input" |
| 9 | Regenerate the index after every change, and record each gap the example exposed as a row in the extension-points table with the research query that would close it, never as an invented mechanism. | Proposed: an unbuilt area reports as not built and a gutted one reports its count, so the index is the standing answer to which areas are real; and a gap written as a query keeps the example honest about what it did not show, where a plausible invented mechanism would make the example read complete. Research query: unresearched; this is the owner's citation rule applied to example directories. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: reuse the reference example's entries, schemas and runner, and call the harnesses rather than copying them. Every copy is a second thing to keep true, and an example whose copy has drifted is worse than no example, because it is read as current. Research query: unresearched; our own reuse convention. | proposed | - |
| Proposed: grade an example by which distinguishing mechanisms it exercises, since deep use of a standard shows there and not in copying the required attribute names. The generalisation from one envelope standard to any standard an example demonstrates is ours. Research query: unresearched beyond the envelope-standard finding cited here. | proposed | `X-litmus-b-004` "not in copying the required attribute names" |
| In the what-the-user-sees table, model the whole unit of agent work with named lifecycle operations, not one span per model call: that is what deep use of the conventions means, and it is also what makes the table legible to a reader who has never seen the run. | sourced | `X-litmus-d-013` "the whole unit of agent work is modelled with named lifecycle operations, not one span per model call" |
| Show the run id as an explicit attribute wherever an example crosses a hop: trace parentage does not survive asynchronous and cross-process agent hops on its own, which is why correlation has to ride on explicit attributes, and an example that relies on parentage will look correct in one process and break in the reader's. | sourced | `X-litmus-b-014` "Trace parentage does not survive asynchronous and cross-process agent hops on its own, which is why correlation has to ride on explicit attributes" |
| Per door, name the lifecycle states the work passes through and whether the reader may subscribe to them or cancel: an explicit task lifecycle with terminal states, streaming subscription, and cancellation are the mechanisms that separate real adoption from a label, so an example that shows only a final answer has shown the least interesting half. | sourced | `X-litmus-b-003` "an explicit task lifecycle with terminal states, streaming subscription, and cancellation" |
| Proposed: keep the example dependency-free and offline, so the check a reader runs is byte-for-byte the check the index ran. A check that needs a network or a package the reader lacks degrades into a screenshot of a green run. Research query: unresearched; our own constraint for this repository's examples. | proposed | - |
| Proposed: name things with the ontology's terms - task and task specification, execution context, attempt and execution, trajectory, artifact, evaluation, result, disposition - and report success on its ladder rather than as one word, so an example that ran cleanly is not read as an example that solved the problem. Where the ontology and a standard already on file disagree, the standard wins and the example says which one it followed. Research query: unresearched; the ladder is the owner's reference vocabulary, not an external source. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/examples_index.py && bash examples/end-to-end/test.sh > /tmp/build-example-checks.txt && grep -qE '^passed [1-9][0-9]*, failed 0$' /tmp/build-example-checks.txt && echo "visible_checks_counted $(grep -c '^  ok ' /tmp/build-example-checks.txt)" |
| Expected | exit 0. docs/examples/index.md is regenerated with one row per area, and the last line reads visible_checks_counted 30, so the gate asserted a non-zero count of checks that actually ran rather than an exit code alone. |
| Deliberate breakage | Gut one example's visible check so it counts nothing while still reporting success: cp examples/end-to-end/test.sh /tmp/e2e-test.sh.bak && printf '#!/usr/bin/env bash\ncd "$(dirname "$0")"\necho\necho "passed 0, failed 0"\n' > examples/end-to-end/test.sh; restore with cp /tmp/e2e-test.sh.bak examples/end-to-end/test.sh. |
| Expected failure | exit 1 at the count assertion. The index still regenerates and the gutted test.sh still exits 0, but the last line captured is passed 0, failed 0, no visible_checks_counted line is printed, and the criterion fails on the count rather than on the exit code. |
| Status | claimed |
| Evidence | `T-t10-07`, `F-a7-03` "Every element has an example and an integration guide that a builder can run" |

## Composes with

Builds on: `agentic-stack`, `build-evidence`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should the criterion assert per area once more than one area is built, given that the index prints a row for every area but asserts nothing about any of them? | Build a second area, gut its test.sh the way the breakage gutts the reference example's, and run the criterion: if it still exits 0 the index row is decoration and the per-area assertion is required. Nothing but the reference example exists on disk today, so this has not been run. | Proposed: the criterion counts the reference example's checks, and a per-area assertion is added in the same change as the second area's test.sh rather than before it, so the assertion and the thing it asserts on land together. | - |
| Where does an area's hidden check live, and who may read it, given that the index already looks for one outside the example directory? | The generator reads a hidden check from a path outside examples/ and prints its last line beside the visible one, so the placement is already decided by a tool while no rule states it. Settle it by naming the directory in this skill and having the index fail rather than print a dash when an area has a README and no hidden check. | Proposed: hidden checks live outside examples/ entirely, the README states only that one exists and how many checks it holds, and an area with no hidden check is reported as incomplete rather than as passing. build-evidence owns the opaque criterion reference that keeps the check itself unreadable from the example. | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 |
