# cap-isolation: the caller's view

Proposed. Folded in from the former `cap-isolation-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-isolation` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 6 row(s) of that kind were dropped in the fold: ambient-guarantees, compose-upward, config-not-argument, correlation-id, problem-details, size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make running one piece of work contained a call with nothing to configure: hand over the work, get back what it produced. Resource envelopes, egress rules, credential brokering and the containment technology itself all sit below the call, because composability hides the complexity.  
  _sourced_ - `T-t2-01`, `T-t3-01`, `E-capability-isolation` "Composability hides the complexity."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| run_contained (proposed) | the work: a handle to what should run and the document it runs on, plus a correlation id you choose. Optionally the destinations the work must reach, if any. Nothing else has to be supplied (proposed) | one unit result: the exit status, the outputs it produced with their digests, and what it used. There is no second call to make before you have an answer (proposed) | proposed | `T-t3-01` |
| read (proposed) | the unit result | exit status, outputs, usage. A refusal or a failure arrives instead as a typed problem, so there is no error text to parse and nothing in the result names what contained the work (proposed) | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-isolation` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked unit 1 (proposed): a human runs generated code and never mentions containment

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:example:contained-run",
  "title": "One unit of work, run to completion with no isolation fields supplied",
  "description": "Sent: the work and a correlation id. Returned: what it produced. The caller wrote no profile, no egress rule and no credential; all three were resolved below the call.",
  "examples": [
    {
      "sent": {
        "work": "unit://run-tests/v1",
        "document": "doc:sha256:1c04…",
        "correlation_id": "run-2026-09-03-0031"
      },
      "returned": {
        "exit_status": 0,
        "outputs": [
          {
            "digest": "sha256:9d17…",
            "media_type": "application/json"
          }
        ],
        "usage": {
          "wall_ms": 21400
        },
        "correlation_id": "run-2026-09-03-0031"
      }
    }
  ]
}
```

### Worked unit 2 (proposed): an event starts work that must reach exactly one destination

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:example:named-destination",
  "title": "One unit of work that names where it must reach, and reaches nowhere else",
  "description": "The only isolation field a caller ever writes is the list of destinations the work must reach. Everything the work tried that was not on that list was refused, and the counters say so.",
  "examples": [
    {
      "sent": {
        "work": "unit://fetch-and-summarise/v1",
        "document": "doc:sha256:44be…",
        "correlation_id": "evt-2026-09-03-0104",
        "reach": [
          "artifacts.internal"
        ]
      },
      "returned": {
        "exit_status": 0,
        "outputs": [
          {
            "digest": "sha256:0ab3…",
            "media_type": "text/markdown"
          }
        ],
        "usage": {
          "wall_ms": 8800
        },
        "containment": {
          "egress_attempts_made": 4,
          "egress_attempts_blocked": 3
        },
        "correlation_id": "evt-2026-09-03-0104"
      }
    }
  ]
}
```

### What a refusal looks like (proposed): problem details, not prose

_proposed_ - sources: -.  Also carried in the body of `cap-isolation` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:example:isolation-unavailable",
  "title": "Nothing could contain this work as asked",
  "$ref": "urn:agentic:problem:0.1",
  "description": "The work was refused before it ran, rather than run with weaker containment. Branch on type; read detail only to report it.",
  "examples": [
    {
      "type": "urn:agentic:problem:isolation-unavailable",
      "title": "No isolation adapter could admit the unit",
      "status": 503,
      "detail": "profile 'large-gpu' is not resolvable by any configured adapter on this host",
      "retryable": true,
      "retry_after_s": 60,
      "correlation_id": "evt-2026-09-03-0104"
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-isolation` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **If the work must reach something, name the destinations in `reach` and nothing more. Never ask for 'network', and never ask for a machine size, a kernel option or a filesystem path.**  
  _why:_ Naming destinations is a statement about the work that any containment technology can honour; asking for a machine is a statement about one of them, and it is the request that would stop your call working the day the platform runs it somewhere else.  
  _sourced_ - `T-t2-02` "enhancing particular aspects of any element without touching the rest"
- **Read exit status, outputs and usage. Do not branch on anything else in the result, and do not expect a field naming what contained the work, because there is not one.**  
  _why:_ Proposed. Those three answer every question a caller actually has - did it work, what did it make, what did it cost - and a branch on anything below them is the boundary leaking into your code.  
  _proposed_ - `T-t2-02`
- **To bound work that might not stop, set a deadline when you start it and let the platform end the unit. Do not reach into the unit, and do not write your own timer and killer.**  
  _why:_ Proposed. The boundary is the thing that can actually destroy a unit, and letting it do so means the same rules apply whichever entry started the work and whatever is containing it that day.  
  _proposed_ - `T-t2-03`

## Other caller invariants

- Proposed: in the ordinary case a caller writes no isolation fields at all. The resource profile, the credential mode and the containment technology are resolved below the call from the agent's profile and the policy in force, which is why the end-to-end consumption example's entry envelope carries no isolation field for any of its four entries.  
  _proposed_ - `T-t3-01`, `T-t2-01`
- The work gets no network unless you name where it must reach, and no real credential ever: cap-isolation makes both of these properties of the boundary (F-a3-04, F-a3-05), so a caller does not switch them on, off, or in.  
  _sourced_ - `F-a3-04`, `F-a3-05` "Egress is a flag, default off"
- Proposed: a refusal arrives as the typed problem object, which cap-isolation requires this boundary to return and cap-errors defines. Work that could not be contained as asked is refused before it runs, never run with weaker containment, so a result you receive at all is a result that was contained as asked.  
  _proposed_ - `F-b4-07`

## Caller practices

- Proposed: name the narrowest set of destinations that lets the work finish, and re-read it when the work changes. A `reach` list that grew for a step you removed is a permission nobody is using and nobody will notice.  
  _proposed_ - `T-t2-02`
- Proposed: never hand the work a secret. If it needs to call something authenticated, that is a destination to name, not a key to pass; cap-isolation makes the broker rather than the unit the holder of the real credential (F-a3-05, F-a3-07), and a key you pass in is the one thing that survives the containment.  
  _proposed_ - `F-a3-05`, `F-a3-07`
- cap-isolation already states the green-gate finding (F-a7-03). What it adds for a caller: an exit status of 0 means the work ran, not that the work was contained and not that the work was right - if you need to know whether the result is acceptable, ask the Judge.  
  _sourced_ - `F-a7-03` "Those establish well-formedness, not correctness"

## Open questions carried over

- **Should a caller ever be allowed to name a resource profile, or only the destinations the work must reach?**  
  _deciding evidence:_ Count the cases where a composition genuinely cannot proceed without a named envelope rather than without more of something the platform could give it anyway. If every such case is really a duration or a memory ceiling the platform already knows from the agent's profile, no caller-facing profile field is needed.  
  _default until then:_ No profile on the call. A caller states the destinations the work must reach and nothing else; adding a profile field later is cheaper than removing one after callers depend on it.  
  `T-t3-02` "It cannot be daunting or overly complex, or no one will use it."

