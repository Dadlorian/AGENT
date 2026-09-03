# cap-tool-access: the caller's view

Proposed. Folded in from the former `cap-tool-access-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-tool-access` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 6 row(s) of that kind were dropped in the fold: ambient-guarantees, compose-upward, config-not-argument, correlation-id, problem-details, size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make reaching a tool a two-line decision: name the tools this unit may call, then call one by name. Discovery, schemas, authorization, retries and which server holds the tool are all below the call, because composability hides the complexity.  
  _sourced_ - `T-t2-01`, `T-t3-01`, `E-capability-tool-access` "Composability hides the complexity."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| declare (proposed) | the list of tool names this unit may call | a binding. The list is checked against what is actually published at bind time, so a name that no longer exists fails here rather than in the middle of the work (proposed) | proposed | `T-t3-01` |
| list (proposed) | the binding | what this unit can call: a name, one line of description and whether calling it changes anything. Not the schemas, not the transport, not the server (proposed) | proposed | - |
| call (proposed) | the binding, a tool name from your declared list, and the arguments | one result: ok plus content, or ok false plus a typed problem. Arguments are checked against the tool's own schema before anything leaves, so a bad argument is a problem you get back, never a half-done call (proposed) | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-tool-access` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked call 1 (proposed): a human asks for work and the unit reads a file through a tool

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:example:read-only",
  "title": "One read-only call",
  "description": "Declared two tools, called one. Nothing was discovered, negotiated, authorized or retried by the caller.",
  "examples": [
    {
      "declared": [
        "read_file",
        "list_dir"
      ],
      "sent": {
        "tool": "read_file",
        "arguments": {
          "path": "src/ledger/fold.py"
        },
        "correlation_id": "run-2026-09-03-0011"
      },
      "returned": {
        "tool": "read_file",
        "ok": true,
        "content": [
          {
            "kind": "text",
            "media_type": "text/x-python",
            "digest": "sha256:0f2b"
          }
        ],
        "correlation_id": "run-2026-09-03-0011"
      }
    }
  ]
}
```

### Worked call 2 (proposed): an event triggers a call that changes something, twice

_proposed_ - sources: -.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:example:mutating",
  "title": "One mutating call, delivered twice",
  "description": "The caller sent nothing about replay safety. The tool is declared mutating, so the platform leased the key and the second delivery returned the first result instead of doing the work again.",
  "examples": [
    {
      "declared": [
        "incident_search",
        "open_incident"
      ],
      "sent": {
        "tool": "open_incident",
        "arguments": {
          "title": "disk-io latency above ceiling",
          "severity": 3
        },
        "correlation_id": "evt-2026-09-03-0042"
      },
      "returned": {
        "tool": "open_incident",
        "ok": true,
        "content": [
          {
            "kind": "json",
            "value": {
              "incident": "INC-4471"
            }
          }
        ],
        "replayed": true,
        "correlation_id": "evt-2026-09-03-0042"
      }
    }
  ]
}
```

### What a failure looks like (proposed): problem details, not prose

_proposed_ - sources: -.  Also carried in the body of `cap-tool-access` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:example:not-declared",
  "title": "A tool the unit did not declare",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Refused before anything was dispatched. Branch on type; read detail only to report it. `urn:agentic:problem:tool-not-declared` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `policy-denied`, which is also 403 and not retryable, with the called name and the declared surface in detail and a rule_id naming the declaration rule.",
  "examples": [
    {
      "type": "urn:agentic:problem:tool-not-declared",
      "title": "Tool is not in this unit's declared surface",
      "status": 403,
      "detail": "called 'delete_branch'; declared surface is read_file, list_dir",
      "retryable": false,
      "correlation_id": "run-2026-09-03-0011"
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-tool-access` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Declare the smallest list that does the job, and add to it when a call is refused rather than in advance.**  
  _why:_ Proposed. A list written wide 'just in case' is indistinguishable from a list that was thought about, and it is the one thing in this call that cannot be tightened later without finding out which entries were real.  
  _proposed_ - `T-t2-03`
- **Branch on ok and, when ok is false, on the problem's type. Treat content as data to pass on, not as something to parse for signs of failure.**  
  _why:_ cap-tool-access requires this boundary to map every failure onto a typed problem, including a tool that reports its own failure inside a successful envelope (F-b4-07); what this adds for a caller is that reading the content for the word 'error' is exactly the parsing that mapping exists to remove.  
  _sourced_ - `F-b4-07` "Typed and machine-readable. Never parsed from prose"
- **Send the same call again if you have to. Do not invent your own deduplication, do not check first whether the work was already done, and do not add a flag saying this is a retry.**  
  _why:_ cap-tool-access-implement wires the key and the lease around every mutating call (F-b4-08). What this adds for a caller: writing your own deduplication on top produces two mechanisms that disagree at exactly the moment one of them matters.  
  _sourced_ - `F-b4-08` "Every externally-triggered action is safe to replay"
- **Ask for read-only data by reading a resource, not by calling a tool that returns it.**  
  _why:_ Proposed. A read costs nothing to repeat and a call may not be repeatable at all, so modelling a read as a call spends a mutating-call budget, a policy decision and a lease on something that changed nothing.  
  _proposed_ - `T-t2-03`

## Other caller invariants

- Proposed: two things go in - the declared list and the call - and one field is branched on. Discovery, input schemas, meta-schema checks, authorization, transports, catalogue changes and the identity of the server are all below the call, and a caller that never mentions them still gets every one of them handled.  
  _proposed_ - `T-t3-01`, `T-t2-01`
- Proposed: the declared list is the whole of what this unit can reach. It is checked when the binding opens and again on every call, so a tool that appears in the catalogue tomorrow does not silently become something this unit can do.  
  _proposed_ - `F-b4-04`

## Caller practices

- cap-tool-access already states that an empty catalogue answers every check and does nothing (F-a6-03). What it adds for a caller: if a binding opens and your declared list resolves to nothing, stop rather than proceeding without tools, because a unit that silently does less looks exactly like one that had nothing to do.  
  _sourced_ - `F-a6-03` "zero tools registered"
- Proposed: keep whatever a partially completed sequence of calls produced. A refused call in the middle is a stopping point, not a reason to discard the results of the calls that succeeded, which the platform has already recorded.  
  _proposed_ - -
- Proposed: write the declared list where a reviewer can read it next to what the unit is for. It is the only place in the system that answers 'what could this unit actually do', and a list assembled at run time answers it for nobody.  
  _proposed_ - `T-t2-02`

## Open questions carried over

- **Should a caller ever be allowed to name the server it wants a tool from?**  
  _deciding evidence:_ Count the cases where a composition genuinely cannot proceed without a specific server rather than a specific tool name. If every such case turns out to be a tool that exists in one catalogue and not another, the declared list already covers it and no server selector is needed.  
  _default until then:_ No server selector on the call. A caller declares tool names and the platform resolves them; adding a selector later is cheaper than removing one after callers depend on it.  
  `T-t2-01` "Composability hides the complexity"

