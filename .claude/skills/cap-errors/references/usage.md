# cap-errors: the caller's view

Proposed. Folded in from the former `cap-errors-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-errors` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make the failure half of the platform usable in three members: read type to know what happened, read retryable to know whether to try again, read detail to fix it. Nothing else is required of a caller.  
  _sourced_ - `F-b4-07`, `T-t3-01` "Typed and machine-readable. Never parsed from prose"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| read (proposed) | whatever came back when something failed, from any entry kind | the type member, which is a registered URI; branch on it, never on title or detail | proposed | `F-b4-07` |
| retry (proposed) | the same problem body | the retryable boolean and, where present, retry_after_s; a caller never derives either from the status code | proposed | `X-cap-errors-004` |
| explain (proposed) | the same problem body | detail for a person, and causes innermost-last when the failure was delegated; neither is ever parsed by a machine | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-errors` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a human submits an entry envelope with no budget

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:problem:example:document-invalid",
  "title": "Envelope failed schema validation",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Exit code 2, body on stdout with media type application/problem+json, nothing written to the ledger.",
  "examples": [
    {
      "type": "urn:agentic:problem:document-invalid",
      "title": "Envelope failed schema validation",
      "status": 422,
      "detail": "missing required property 'budget'",
      "retryable": false,
      "correlation_id": "run-2026-09-03-0007"
    }
  ]
}
```

### Worked example 2 (proposed): an agent's next step would cross the ceiling

_proposed_ - sources: -.  Also carried in the body of `cap-errors` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:problem:example:budget-exhausted",
  "title": "A step would cross the budget ceiling",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Exit code 2, refused before the step ran, so the ledger shows no dispatch for it.",
  "examples": [
    {
      "type": "urn:agentic:problem:budget-exhausted",
      "title": "A step would cross the budget ceiling",
      "status": 402,
      "detail": "step fix#2 estimated 120000 micros, 41000 remain of a 400000 ceiling",
      "retryable": false,
      "step_id": "fix#2",
      "correlation_id": "run-2026-09-03-0008"
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-errors` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Read retryable from the body rather than deciding from the status code, and honour retry_after_s when it is present.**  
  _why:_ The wait for a rate-limited or temporarily unavailable call is knowable at the source and not at the caller: best practice for this standard is to include Retry-After on 429 and 503 responses, and two 503s can differ on whether retrying helps at all.  
  _sourced_ - `X-cap-errors-004` "Include Retry-After on 429 and 503 responses"
- **Show detail to a person and stop there. Do not parse it, log it as the failure identity, or key metrics on it.**  
  _why:_ The detail field should help developers fix the problem without contacting support, which means it is prose written for a reader and is free to change whenever a clearer sentence is found.  
  _sourced_ - `X-cap-errors-004` "The detail field should help developers fix the problem without contacting support."
- **Write one failure handler for all four entry kinds - a human, an event, a schedule, and an external system or agent - instead of one per intake path.**  
  _why:_ All four enter through the same shape, so a per-entry handler is duplicated work that will drift the moment one path gets a new failure type.  
  _sourced_ - `T-t6-02`, `T-t1-03` "All four enter through the same shape."
- **When a failure was delegated, read causes innermost-last to find the origin, and report the outer type as what happened to you.**  
  _why:_ Proposed. The outer type is the contract the caller was promised; the inner chain is context. Reporting the innermost type outward makes a caller's own interface change whenever a component it never named changes.  
  _proposed_ - -
- **Treat an unfamiliar type as a hard failure and use the retryable member, rather than failing closed on the whole response or guessing from the status.**  
  _why:_ Proposed. New registry rows are added over time; a caller that rejects anything it does not recognise turns every registry addition into a client outage, which is exactly the coupling that composability is meant to remove.  
  _proposed_ - `T-t2-02`
- **Read the two worked examples above before writing the handler, then read cap-errors only if you need the full member set or the registry, and cap-errors-implement only if you are producing failures rather than consuming them.**  
  _why:_ Proposed. Three members and two examples are the whole consuming surface; loading the contract and the build guidance to write a caller is the kind of weight that stops a platform from being used.  
  _proposed_ - `T-t3-02`

## Other caller invariants

- Proposed: there is nothing to switch on. A caller does not request typed errors, cannot decline them, and has no error-handling configuration to get wrong; agentic-stack states the no-opt-out rule (F-b1-08) and cap-errors states the shape (F-b4-07).  
  _proposed_ - `F-b1-08`, `F-b4-07`
- Proposed: an unrecognised type is safe to treat as a hard failure with retryable read from the body. cap-errors states that the registry is closed (see its Invariants), so a type a caller has not seen is new, not malformed, and the retry decision is still on the wire.  
  _proposed_ - -

## Caller practices

- Proposed: log the type and the correlation identifier together. cap-errors states why the correlation identifier is on the body; what it buys a caller is that one identifier finds the platform-side record of the same failure without a timestamp search.  
  _proposed_ - `X-cap-errors-006`
- Proposed: when a validation failure comes back, fix every field it names before resubmitting. The platform returns all validation errors at once with field-level detail, so a resubmit that fixes one field is a round trip spent learning what you were already told.  
  _proposed_ - `X-cap-errors-004`
- Proposed: do not build a retry loop around a refusal. A policy denial and a budget exhaustion are deterministic, arrive before any spend, and carry retryable false; retrying them burns the caller's own budget and changes nothing.  
  _proposed_ - `F-b4-04`

## Open questions carried over

- **Should a caller ever see causes, or is the delegated chain internal?**  
  _deciding evidence:_ Count, across recorded failures, how often the innermost cause changes what a caller does. If it never does, causes is diagnostic material that belongs in the platform-side record keyed by correlation identifier rather than in the body a caller receives.  
  _default until then:_ Keep causes on the body and tell callers to read it only for reporting, never for branching. Removing a member later is cheaper than adding one after clients exist.  
  `T-t2-01` "Composability hides the complexity."

