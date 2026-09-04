---
name: "build-litmus-questionnaire"
description: "The discipline of writing the litmus questionnaire: one section per capability interface and per cross-cutting concern, each stating the idealistic future state a build could reach inside the window and asking about it from several angles, so an answer can be scored on a closed scale. Load it before writing or reviewing a section, when deciding a standard's settledness, when a question needs an aligned-versus-misaligned pair so the score is decidable from evidence rather than opinion, when someone asks whether a standard is really in use or merely named, when a self-assessment is about to grade the build against itself instead of against a stated future state, and when the crew writing the questions has to stay isolated from what the repository built. Also load it before answering the questionnaire, when a score looks like an opinion, or when a claim in a section has no record behind it."
---

# build-litmus-questionnaire (folded into `build-ceremony`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| The measuring sticks walk down each stack element and the standards it interoperates with: one section per capability interface in PASS.md B3, whose middle column is the contract, and one per cross-cutting concern in B4. Each section states the idealistic future state a build could reach inside the window and asks about it from several angles, so that how the element is used is what gets measured. The frame that fixes the window, the closed scale, the six angles, the settledness classes and the isolation rule is the owner's; it is proposed here and recorded in docs/litmus/frame.json. | sourced | `T-t10-04`, `F-b3-01` "The measuring sticks walk down each stack element" |

## Entities

| Entity |
|---|
| `E-standard-json-schema-2020-12` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | - | `F-b3-09`, `E-standard-json-schema-2020-12` |

- `E-standard-json-schema-2020-12` version note: The dialect PASS.md's Document validation row (F-b3-09) names; no specification was fetched from this environment, so the version stays unverified. The interface row itself is owned by cap-document-validation; this skill only declares the dialect its record shapes are written in.

### Shapes (JSON Schema 2020-12)

**litmus-section (proposed summary of one section; the full record shape is schemas/litmus.schema.json and the frame it refers to is docs/litmus/frame.json)** (proposed; sources: `F-b3-09`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "litmus-section",
  "type": "object",
  "required": [
    "id",
    "kind",
    "source",
    "name",
    "standard",
    "future_state",
    "direction",
    "questions",
    "gaps"
  ],
  "properties": {
    "id": {
      "type": "string",
      "description": "the fixed id for this row"
    },
    "kind": {
      "enum": [
        "capability",
        "concern"
      ]
    },
    "source": {
      "type": "string",
      "pattern": "^F-b[34]-[0-9]{2}$"
    },
    "name": {
      "type": "string"
    },
    "standard": {
      "type": "object",
      "required": [
        "name",
        "settledness",
        "why",
        "cites"
      ],
      "properties": {
        "name": {
          "type": "string",
          "description": "as PASS.md names it; 'none' where the row has no standard"
        },
        "settledness": {
          "enum": [
            "baseline",
            "contested",
            "emerging",
            "none"
          ]
        },
        "why": {
          "type": "string",
          "description": "from the research; a product may be named here"
        },
        "cites": {
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      }
    },
    "future_state": {
      "$ref": "#/$defs/cited"
    },
    "direction": {
      "$ref": "#/$defs/cited",
      "description": "a product may be named here as evidence"
    },
    "questions": {
      "type": "array",
      "minItems": 4,
      "maxItems": 8,
      "items": {
        "type": "object",
        "required": [
          "id",
          "angle",
          "question",
          "evidence_expected",
          "aligned_looks_like",
          "misaligned_looks_like",
          "origin",
          "cites"
        ],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^[a-z0-9-]+-q[0-9]+$"
          },
          "angle": {
            "enum": [
              "presence",
              "depth",
              "boundary",
              "guarantees",
              "usage",
              "direction"
            ]
          },
          "question": {
            "type": "string"
          },
          "evidence_expected": {
            "type": "string",
            "description": "an artifact, a trace, a command output or a configuration, named tool-agnostically"
          },
          "aligned_looks_like": {
            "type": "string"
          },
          "misaligned_looks_like": {
            "type": "string"
          }
        },
        "description": "every question also carries its citation fields: an origin of sourced or proposed, a cites list, and, when sourced, a verbatim quote of one cited record"
      }
    },
    "gaps": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "claim",
          "research_query"
        ]
      }
    }
  },
  "$defs": {
    "cited": {
      "type": "object",
      "required": [
        "text",
        "origin",
        "cites"
      ],
      "description": "a statement with its citation: text, an origin of sourced or proposed, a cites list of kb ids, and, when sourced, a verbatim quote of one cited record"
    }
  }
}
```

**litmus-answer (proposed shape: one answer to one question, written later by the assessor, never inside a section)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "litmus-answer",
  "type": "object",
  "required": [
    "question_id",
    "score",
    "evidence",
    "assessor",
    "date"
  ],
  "properties": {
    "question_id": {
      "type": "string",
      "pattern": "^[a-z0-9-]+-q[0-9]+$"
    },
    "score": {
      "enum": [
        -1,
        0,
        1,
        2,
        3
      ],
      "description": "-1 misaligned, 0 absent, 1 exists, 2 aligned, 3 leading"
    },
    "evidence": {
      "type": "string",
      "description": "what was produced for this question: the artifact, trace, command output or configuration the question asked for"
    },
    "rationale": {
      "type": "string",
      "description": "why that evidence lands on that score, read against aligned_looks_like and misaligned_looks_like"
    },
    "correction": {
      "type": "string",
      "description": "required when score is -1: what to correct, since a misaligned score is an error rather than a gap"
    },
    "assessor": {
      "type": "string"
    },
    "date": {
      "type": "string",
      "format": "date"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed, and the owner's frame recorded in docs/litmus/frame.json: the scale is closed at five values, -1 misaligned, 0 absent, 1 exists, 2 aligned, 3 leading. A section author may not add, rename or reweight a score, and -1 is an error to correct rather than a gap to fill. | proposed | `F-b1-01` |
| Proposed, from the same frame: six angles - presence, depth, boundary, guarantees, usage, direction - of which a section uses at least four and always depth and usage, over four to eight questions. Presence alone is never sufficient, because how a standard is used matters more than whether it is used, and the angles are consequences of the design rules rather than a checklist invented for the questionnaire. | proposed | `F-b1-01`, `F-b1-02` |
| Where a standard exists it is adopted whole rather than modelled into our own shape, so the depth angle asks which of the standard's distinguishing mechanisms are in use; a section whose only evidence is that the standard is named has recorded presence, not depth. | sourced | `F-b1-03` "adopt it whole rather than modelling our own shape" |
| The boundary angle asks whether the element sits behind a capability interface with a second adapter that actually runs: every external dependency sits behind such an interface, swappability is a tested property rather than an intention, and the swap is proven by the conformance run, never asserted. | sourced | `T-t10-05`, `F-b1-02`, `F-b1-04` "the swap is proven by the conformance run, never asserted" |
| The guarantees angle asks which cross-cutting concerns ride on the element without the caller asking: cross-cutting guarantees are not optional, the platform applies each and a caller cannot decline them, and budget is among them because cost is knowable before commitment. | sourced | `F-b1-08`, `F-b4-01`, `F-b1-06` "Cross-cutting guarantees are not optional" |
| The usage angle asks how a caller reaches the element from every entry and how it composes with the others, held to the rule that a caller needs no client library we wrote: evidence that integration works only through a library of our own is a finding against the boundary, not proof of adoption. | sourced | `F-b1-05` "A caller needs no client library we wrote" |
| Proposed, and the owner's isolation rule in docs/litmus/frame.json: the crew that writes a section reads PASS.md Part B and the web and nothing this repository built from them, and the contamination check refuses any text naming a thing this repository built, or a product name outside standard.why and direction.text. It is the grader rule turned on ourselves - the grader is never visible to the graded (F-b1-07) - so the questions cannot be quietly shaped to whatever happens to exist. | proposed | `F-b1-07` |
| Every statement in a section is either sourced with a quote that is a verbatim substring of a record it cites, or marked proposed in its own words: all information is trust-linked to the knowledge base with a source reference, and there is no third kind of statement. | sourced | `T-t10-08` "All information is trust-linked to the knowledge base with a source reference" |
| Proposed, and the owner's four settledness classes in docs/litmus/frame.json: baseline, contested, emerging, none. A baseline standard is not shopped for a competitor - the question is how deeply it is used; a contested one has its future state name the property to hold rather than the winner; an emerging one names the direction and the exit if it changes; and where PASS.md records no standard, the future state is original design held to the specification Part B asks for. | proposed | `F-b5-01` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| A section holds questions and never answers: no score, no evidence and no verdict is written into it, because the crew that was kept away from the build cannot also grade it. The answer is a separate record, written later by the assessor in the litmus-answer shape above (proposed). | proposed | `F-b1-07` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Read docs/litmus/frame.json before writing anything, and take from it the window, the closed five-point scale, the six angles, the four settledness classes and the rules: four to eight questions per section, at least four angles, always including depth and usage. | Proposed: the frame is the owner's and fixed, so a section that invents its own scale, angle or question count cannot be scored beside the other twenty-two. | proposed | - |
| 2 | Take the sections from the fixed list rather than choosing them: one per capability interface row of PASS.md B3 (F-b3-02 to F-b3-17) and one per cross-cutting concern of B4 (F-b4-02 to F-b4-08), each with the id the checker fixes. Where the same word appears in both tables, write the capability section about the interface, its standard and its adapters, and the concern section about the guarantee riding on every unit of work. | The middle column is the contract and the right two columns prove it is swappable, so a capability section asks after the contract and its adapters while a concern section asks after a guarantee that is applied rather than requested. | sourced | `F-b3-01`, `F-b4-01` "The middle column is the contract" |
| 3 | Research each section before writing it - at least three searches: the standard's current version and activity inside the window, the mechanisms that separate deep use from nominal use, and where the ecosystem is heading with any credible alternative - and write each result you rely on as one research record before you cite it, in the fields build-research-record fixes (lens, topic, query, url, title, verbatim snippet, read, status search-only versus fetched). | Nothing is made up, and the knowledge structure controls the flow of information toward the future state; a claim about a standard's direction with no record behind it is an opinion the answerer will inherit. | sourced | `T-t10-08` "nothing is made up, and the knowledge structure controls the flow of information toward the future state" |
| 4 | Decide the standard's settledness from those records and say why in standard.why, which is one of only two fields where a product may be named; the other is direction.text. Everywhere else a section names capabilities and standards. | Proposed: the future state has to survive a swap of whatever holds the element today, so naming a product in a question would date the question and pre-judge the boundary it is asking about. | proposed | `T-t10-04` |
| 5 | Write the future state as one paragraph: the idealistic state a build could reach inside the window, stated in capabilities and standards, as modern as the window allows and no more engineered than that. | The desired future state is bounded on both sides - modern to the limit of what could be developed now, and no more engineered than that - so a section that asks for a research programme is as wrong as one that asks for what already ships. | sourced | `T-t10-02` "no more engineered than that" |
| 6 | Write the direction separately from the future state: what is settling, what is being abandoned, and what would be an error to build now. | Proposed: -1 on the scale is only reachable if the section has said what building toward the wrong thing would look like, so a section with no stated error case can never score misaligned and quietly loses the distinction the owner asked for. | proposed | - |
| 7 | Write four to eight questions across at least four angles, always including depth and usage, and give each one the evidence expected - an artifact, a trace, a command output, a configuration - together with what aligned and what misaligned look like. | Proposed: a score is decidable only when the question says in advance what evidence would land on which value. agentic-stack carries the A7 finding that configuration written in the documented place validated, reviewed correctly and had no runtime effect (F-a7-04), so ask for the observed effect rather than the file that declared it. | proposed | `F-a7-04` |
| 8 | Record every claim you could not source as a gap carrying the research query that would source it, instead of dropping the claim or letting it ride on a neighbouring citation. | Proposed: build-research-record keeps the same rule for a search that found nothing (F-part-c-03); here the gap is what tells a later reader that the question rests on an unsourced belief rather than on a record. | proposed | `F-part-c-03` |
| 9 | Run `python3 tools/litmus_check.py check docs/litmus/parts/<part>.json` until it prints 0 errors, then `python3 tools/litmus_check.py merge`, which re-checks every part together for coverage before it writes docs/litmus/questionnaire.json and renders the Markdown. | Proposed: the per-part run checks shape, angles, citations and contamination, but only the merge can see that every B3 row and every B4 concern has exactly one section, which is the property the questionnaire as a whole has to hold. | proposed | - |
| 10 | Hand the questionnaire on to be answered rather than answering it: one isolated assessor per section, one answer per question carrying the evidence the question asked for and a score on the closed scale, and a -1 raised as a correction to make rather than a gap to fill. | Proposed: separating the crew that asks from the assessor that answers is what keeps the questions independent of the build; and a misaligned score names work that is pointing the wrong way, which is a different obligation from work that is simply missing. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Read the Isolation row as the template for the whole table when writing any section: an excellent implementation is not what is being judged, so the question is whether the architecture names the standard and whether, when the workload changes, the adapter changes and the core does not. | sourced | `F-b3-18` "Read the Isolation row as the template for the whole table" |
| Two rows in B3 have no standard to adopt and are the only places original design effort is warranted: their sections score the design against the specification asked of it - the request shape, the result shape, cancellation semantics, timeout and budget enforcement, partial-result handling and what a failure returns for one; the write model, concurrency and single-writer guarantees, the integrity mechanism, retention and the query surface for the other - rather than against a standard's depth. | sourced | `F-b5-01`, `F-b5-03`, `F-b5-05` "the only places original design effort is warranted" |
| Judge the future state at production scale: it is consumable, composable, and running across every layer in production with hundreds of agents, so a question whose evidence could come from a single demonstration run is asking too little of the element. | sourced | `T-t10-02` "running across every layer in production with hundreds of agents" |
| Proposed: where the same word carries a capability section and a concern section, draft the pair together and delete the overlap, so one asks about the interface and its adapters and the other asks whether the guarantee rides on every unit of work through every entry without being requested. | proposed | `F-b3-01`, `F-b4-01` |
| Proposed: keep every question answerable by someone who has not read the section - name the mechanism, not the section's own vocabulary - because the assessor arrives with the build in front of them and only this questionnaire to read it against. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/litmus_check.py check |
| Expected | Exit 0, last line `23 sections, <n> questions, 0 errors`: one section for each capability interface row F-b3-02 to F-b3-17 and each cross-cutting concern F-b4-02 to F-b4-08, every section carrying four to eight questions over at least four angles including depth and usage, every cited id resolving in kb/, every sourced quote a verbatim substring of a cited record, and no text naming a thing this repository built or a product outside standard.why and direction.text. |
| Deliberate breakage | In docs/litmus/parts/a.json, add one question line to a section that has fewer than eight questions, whose `question` text names a file this repository built under tools/ (`kb.py`), then run `python3 tools/litmus_check.py check` again and restore the file afterwards. |
| Expected failure | Exit 1, with the line `ERROR isolation: questions[N].question names something this repo built: 'kb.py'` and a last line `23 sections, <n+1> questions, 1 errors`: the contamination check is what keeps the crew's isolation enforceable rather than promised. |
| Status | claimed |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-research-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does a section with an unresolved gap block the merge, or ship with the gap recorded? | The checker requires a claim and a research query on every gap but does not fail on the gap itself; a merge run with gaps present would show whether the owner wants the questionnaire complete or honest about what it could not source. | Proposed: it ships with the gap recorded, because a gap carrying its query is more useful to the assessor than a question quietly dropped. | `F-part-c-03` |
| Is the assessor bound by an isolation rule of its own - reading the build for its section but not the other sections' answers? | Two assessors scoring the same section independently, one having read a neighbouring section's answers and one not, and comparing the scores against the same evidence. | Proposed: one isolated assessor per section, carrying the frame and nothing else across, on the same reasoning that keeps the questions independent of the build. | `F-b1-07` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 |
