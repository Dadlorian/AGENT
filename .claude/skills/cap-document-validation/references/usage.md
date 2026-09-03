# cap-document-validation: the caller's view

Proposed. Folded in from the former `cap-document-validation-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-document-validation` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: problem-details.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make the capability usable in two moves - send a document with the name of its shape, read a located list back - so a caller never has to know which validator, dialect or schema store served the call.  
  _sourced_ - `T-t2-01`, `T-t3-01` "Composability hides the complexity."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| validate, as a caller sees it (proposed view of the operation cap-document-validation defines) | two things: the document you are submitting, and the identifier of the shape it claims to be (proposed) | admitted, or a list of every violation with the location of each inside your document (proposed) | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-document-validation` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### worked example 1 (proposed): a person submits a malformed entry and gets everything wrong with it, at once

_proposed_ - sources: -.  Also carried in the body of `cap-document-validation` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:example:rejected:0.1",
  "title": "Rejected submission, end to end (proposed)",
  "type": "object",
  "examples": [
    {
      "sent": {
        "schema_uri": "urn:agentic:seam:entry:0.1",
        "instance": {
          "kind": "human",
          "intent": "restart the ingest job",
          "budget": {
            "ceiling_micros": "50000"
          }
        }
      },
      "outcome": {
        "valid": false,
        "errors": [
          {
            "instance_location": "/actor",
            "keyword_location": "/required",
            "message": "required property 'actor' is missing"
          },
          {
            "instance_location": "/budget/ceiling_micros",
            "keyword_location": "/properties/budget/properties/ceiling_micros/type",
            "message": "expected integer, got string"
          }
        ]
      },
      "received_on_the_wire": {
        "media_type": "application/problem+json",
        "type": "urn:agentic:problem:document-invalid",
        "title": "Document failed schema validation",
        "status": 422,
        "detail": "2 violations; see errors",
        "errors": "the list above, unchanged"
      },
      "what_the_caller_does": "fixes both violations in one edit and resubmits; there is no second round of discovery"
    }
  ]
}
```

### worked example 2 (proposed): the shape is tightened and no caller changes

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:document-validation:example:tightened:0.1",
  "title": "Enhancing one aspect without touching the rest (proposed)",
  "type": "object",
  "examples": [
    {
      "before": {
        "schema_uri": "urn:agentic:seam:entry:0.1",
        "rule": "idempotency_key is any non-empty string"
      },
      "change": "the schema adds a maxLength and a pattern to idempotency_key; the schema id gains a new version",
      "unchanged": [
        "what a caller sends: the same document and the same shape identifier",
        "the outcome shape they read back",
        "which validator serves the call",
        "every other schema in the store"
      ],
      "newly_rejected": [
        {
          "instance_location": "/idempotency_key",
          "keyword_location": "/properties/idempotency_key/pattern",
          "message": "does not match the required pattern"
        }
      ],
      "who_had_to_change": "nobody's calling code; only the schema resource and the callers whose documents were already out of shape"
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-document-validation` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Read the outcome as data. On rejection, work through the whole located list and fix it in one edit; do not stop at the first entry and do not pattern-match the message text.**  
  _why:_ Every violation is reported in one pass precisely so that repair is one round rather than as many rounds as your document has faults.  
  _sourced_ - `X-cap-document-validation-005` "All errors are reported in a single pass instead of stopping at the first failure."
- **When you need a stricter rule, tighten the schema and publish it under a new identifier; do not add a check in your own component and do not ask callers to change what they send.**  
  _why:_ The shape is the one place a rule can change without reaching anyone: worked example 2 is that change written out.  
  _sourced_ - `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest."
- **Do not re-check the document after admission with hand-written field tests of your own.**  
  _why:_ Proposed: two checkers give two answers, and the second one is the one nobody maintains; it is also how a rule ends up enforced on one entry path and not the others.  
  _proposed_ - -
- **If a result surprises you, ask which dialect was in effect for the call rather than reading the schema file and reasoning from it.**  
  _why:_ cap-document-validation already states why (F-a7-04): what a file declares and what a runtime resolved are different facts, and only one of them decided your outcome.  
  _sourced_ - `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect"
- **If you cannot state the shape you must send in a sentence, say so and treat it as a defect in the schema rather than working around it.**  
  _why:_ A shape a caller cannot hold in their head gets guessed at instead, and a capability nobody can use straightforwardly is one nobody uses.  
  _sourced_ - `T-t3-02` "It cannot be daunting or overly complex, or no one will use it."

## Other caller invariants

- A caller supplies two things and knows nothing else: the document, and the identifier of the shape it claims to be. Which validator ran, which dialect it resolved and where the schema lives are all hidden.  
  _sourced_ - `T-t2-01` "Composability hides the complexity."
- A rejection arrives as data: a located list of every violation, carried on the wire as problem details with a type, title, status and detail. Match on the type; never parse the wording.  
  _sourced_ - `F-b3-13`, `X-cap-errors-002` "A Problem Details response uses the application/problem+json content type"
- cap-document-validation already states the well-formedness finding for this capability (F-a7-03). For a caller it means admitted says your document is shaped correctly, and says nothing about whether what you asked for is sensible or affordable.  
  _sourced_ - `F-a7-03` "Those establish well-formedness, not correctness"

## Caller practices

- Ask for every violation at once with the location of each, rather than a first-failure answer; it is the difference between one repair and one repair per fault.  
  _sourced_ - `X-cap-errors-004` "return all validation errors at once with field-level detail"
- Proposed: version the shape, never the caller. Publishing a new schema identifier lets old and new documents coexist while they migrate; adding an optional field with special meaning to an existing shape makes every reader guess which era a document came from.  
  _proposed_ - -
- Proposed: validate the envelope once, at the way in, and let composition carry the result; a step that revalidates the same document is paying for the check twice and can still disagree with the admission point.  
  _proposed_ - -
- Keep what a caller must know small: two inputs and one outcome. Every additional thing a caller must configure is a reason the check gets bypassed rather than used.  
  _sourced_ - `T-t3-01`, `T-t2-01` "It has to be simple to use."

## Open questions carried over

- **Should a caller be able to validate a document without submitting it - a dry run against a shape?**  
  _deciding evidence:_ Count, over recorded submissions, how many were rejected for shape alone and how many of those came from an agent that could have checked first; if that fraction is large, the pre-check pays for itself in refused work.  
  _default until then:_ Yes, using the same operation and the same outcome, with nothing dispatched and nothing spent. Proposed: it costs one call path and removes the reason an agent would keep a private copy of the rules.  
  `T-t2-01` "Composability hides the complexity."

