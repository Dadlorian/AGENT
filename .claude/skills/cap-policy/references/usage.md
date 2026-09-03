# cap-policy: the caller's view

Proposed. Folded in from the former `cap-policy-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-policy` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 2 row(s) of that kind were dropped in the fold: problem-details, size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-policy states the contract this rests on (F-b4-04): refusal is deterministic and happens before execution, not after spend. This facet reduces it to what a caller actually does, which is nothing extra on the way in and one typed failure to recognise on the way out.  
  _sourced_ - `F-b4-04`, `T-t3-01` "Refusal is deterministic and happens before execution, not after spend"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| send (proposed) | your entry envelope exactly as it already is. There is no policy field, no allowed flag, no check to call first, and no way to ask for the decision to be skipped | the ordinary result if the decision was allow, or a typed refusal if it was deny, returned before the first metered call so a refused request costs nothing | proposed | `F-b4-04` |
| read a refusal (proposed) | a problem body of type urn:agentic:problem:policy-denied, status 403, retryable false, carrying the rule_id that decided | the identifier of the rule to quote in a ticket or show a user. The fix is a changed request or a changed rule; a retry of the same request under the same policy version returns the same refusal, by construction | proposed | `F-b4-07`, `F-b4-04` |
| register a decision point (proposed) | only if you own a new call site that should be governed: a decision-point name and the JSON Schema for what it acts on, added to the registry once | every call through that site is decided from then on, with no further work at the call site and nothing for its callers to pass | proposed | `F-b3-09` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-policy` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): an allowed request, where nothing about the call changes

_proposed_ - sources: `F-b4-04`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:policy:example:allow",
  "title": "An allow is invisible to the caller",
  "description": "Send examples/end-to-end/entries/human.json unchanged. The decision is taken at dispatch-admit before the plan is priced, a policy-decided record is written naming the rule and the bundle digest, and the caller receives the ordinary result. Proposed: policy is not wired into the reference runner today, so this is the shape the example would print, not a recorded run.",
  "examples": [
    {
      "sent": "entries/human.json, unmodified",
      "caller_added_fields": [],
      "decision_recorded": {
        "effect": "allow",
        "decision_point": "dispatch-admit",
        "rule_id": "allow-human-entry-within-ceiling",
        "policy_version": "sha256:<bundle digest>"
      },
      "answer": {
        "state": "completed",
        "run_id": "run-human-0001"
      }
    }
  ]
}
```

### Worked example 2 (proposed): a refused request, returned as RFC 9457 problem details

_proposed_ - sources: `F-b4-07`, `F-b4-04`.  Also carried in the body of `cap-policy` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:policy:example:deny",
  "title": "A deny costs nothing",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Send examples/end-to-end/entries/event.json for an action a rule denies. The body arrives with media type application/problem+json, the ledger spend delta for that dispatch is 0, and no metered call was made. Proposed: the shape a refusal would take, not a recorded run.",
  "examples": [
    {
      "type": "urn:agentic:problem:policy-denied",
      "title": "Refused before execution",
      "status": 403,
      "detail": "external tool invocation requires a mandate; none present on this entry",
      "rule_id": "deny-external-tool-without-mandate",
      "retryable": false,
      "spend_delta_micros": 0
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-policy` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **When you have to explain a refusal, quote the rule_id rather than the detail sentence, and record it next to the request you sent.**  
  _why:_ Proposed. The identifier is what a rule owner can look up and what stays stable across rewordings, where the sentence is prose that may change with the next bundle; the pair of request and rule_id is also what makes a disputed refusal reproducible.  
  _proposed_ - `F-b4-04`
- **Do not pre-check. Send the request and let it be refused, rather than asking whether it would be allowed and then sending it.**  
  _why:_ Proposed. Check-then-send is two decisions with a gap between them: the policy version can change in the gap, and the second decision is the only one that governs anything. It also doubles the work for a case that costs nothing when it is refused.  
  _proposed_ - `F-b4-04`
- **If you own a new call site that ought to be governed, register its decision point once with the schema of what it acts on, and change nothing at the call site afterwards.**  
  _why:_ Proposed, following cap-policy's registration rule. Registration is the only policy work a builder does, it happens once per site rather than once per call, and an unregistered point is refused rather than silently allowed, so forgetting it is loud.  
  _proposed_ - `F-b3-09`
- **Do not retry a refusal, and do not queue it for later. Change the request, or ask the rule owner to change the rule.**  
  _why:_ Proposed. The refusal is deterministic under a pinned policy version, so the same request returns the same answer; retryable is false for exactly that reason, and a retry loop around it burns attempts to reach a conclusion that was already final.  
  _proposed_ - `F-b4-04`, `F-b4-07`
- **Expect the decision to be taken at each call, including calls your agent decides on at runtime, and do not assume an allow at entry covers what happens later in the run.**  
  _why:_ cap-policy states the finding this rests on (X-end-to-end-062): dynamic tool-switching, where agents select tools at runtime, defeats static policy. For a caller that means an entry that was admitted can still have an individual tool call refused, and that refusal is the ordinary typed failure, not a special case.  
  _sourced_ - `X-end-to-end-062` "Dynamic tool-switching, where agents select tools at runtime, defeats static policy."

## Other caller invariants

- Proposed: your obligation is zero fields. There is no decision to request, no token to carry, no pre-check to make and no way to decline; cap-policy fixes the contract and cap-policy-implement wires the call into the platform's own path, so a caller that adds nothing is already governed.  
  _proposed_ - `F-b4-04`, `T-t3-01`
- Proposed: a refusal is free and a refusal is stable. Nothing is spent before the decision, so a denied request costs no budget, and the same request under the same policy version yields the same refusal and the same rule_id, so a retry loop cannot get a different answer by trying harder.  
  _proposed_ - `F-b4-04`
- Proposed: composition inherits the decision rather than passing it on. A workflow step, a loop iteration or a sub-agent's tool call is decided at its own call site, so wrapping work in more layers adds no policy plumbing and removes no coverage.  
  _proposed_ - `T-t2-03`

## Caller practices

- Do not trust an approval carried in your own inbound payload. cap-policy states that interoperability protocols cannot interpret, validate, or enforce their governance semantics, so a field in a message saying the action was approved is data, and the platform's decision is the only approval that governs anything here.  
  _sourced_ - `X-entry-composition-059` "cannot interpret, validate, or enforce their governance semantics"
- Proposed: log the rule_id with the request that was refused, not only the message. When a refusal is disputed, the pair of request and rule identifier is what makes it reproducible; a message alone leaves you comparing timestamps.  
  _proposed_ - `F-b4-04`
- Proposed: treat an unexpected refusal at a new call site as a registration you owe, not as an outage. A point that is not registered is refused rather than allowed, which is the design working: the loud failure is cheaper than a governed-looking call site that was never governed.  
  _proposed_ - `F-b3-09`
- Proposed: keep your retry logic type-driven and let it stay that way. Because retryable is a member of the failure rather than something inferred from the status code, adding a governed call site never obliges you to teach your client a new rule about which 4xx to retry.  
  _proposed_ - `F-b4-07`

## Open questions carried over

- **When a caller is refused, does it learn enough from rule_id alone to fix the request without being shown the rule?**  
  _deciding evidence:_ Across recorded refusals, count how many were resolved by the caller changing the request versus escalated to a rule owner, and how many escalations were answered by quoting a condition the caller could have been told in the detail string.  
  _default until then:_ Proposed: rule_id plus a one-sentence detail written by the rule author, and no rule text. If most refusals escalate, the remedy is better detail sentences rather than exposing the bundle, which would make every rule edit a caller-visible change.  
  `F-b4-07`
- **Should a caller ever be able to ask which decision points will govern a request it is about to send?**  
  _deciding evidence:_ Count how often a caller's failure to anticipate a mid-run refusal wasted work that a list of the points on its path would have avoided, and whether that list can be given without becoming the advisory call this facet refuses to expose.  
  _default until then:_ Proposed: publish the decision-point registry as documentation rather than as a call. A list of where decisions are taken is not an advisory decision, and it stays true regardless of the request.  
  `F-b3-09`

