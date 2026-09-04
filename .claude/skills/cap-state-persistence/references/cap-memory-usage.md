# cap-memory: the caller's view

Proposed. Folded in from the former `cap-memory-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-memory` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-memory states the contract and cap-memory-implement builds it; this facet reduces both to two things a caller does - write one claim, recall at a scope - so remembering across runs is two calls on a step rather than a store you own.  
  _sourced_ - `T-t3-01`, `X-cap-memory-003` "It has to be simple to use."

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| remember (the whole of what a step writes) | scope, one claim, and an expiry - and nothing else; the provenance, the correlation id and the actor come from the run you are already in (proposed) | a memory_id. You do not choose an index, an embedding or a key format (proposed) | proposed | `X-end-to-end-002` |
| recall (the whole of what a step reads) | a scope selector naming at least one dimension you hold, your need in words or an explicit key, and a limit (proposed) | items with their provenance and their age, plus the scope that was applied; zero items is a normal answer, not a failure (proposed) | proposed | `X-cap-memory-002`, `X-cap-memory-004` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-memory` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a person's run remembers, an agent's later run recalls - TARGET T1's first two ways in

_proposed_ - sources: `T-t1-01`, `T-t1-02`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:memory:example:human-and-agent",
  "title": "One claim written in run A, recalled in run B by something else",
  "description": "Only the produced_by subject differs between a human-initiated write and an agent's. Neither writer named an index, and the reader named a scope and a need.",
  "examples": [
    {
      "remember": {
        "scope": {
          "principal": "user:corey"
        },
        "kind": "semantic",
        "body": {
          "claim": "Release notes for this repo are reviewed by the release-reviewer agent before publication, not by the author."
        },
        "provenance": {
          "produced_by": "user:corey",
          "observed_at": "2026-09-03T09:12:00Z",
          "correlation_id": "corr-a-0001"
        },
        "staleness": {
          "expires_at": null,
          "review_after": "2026-12-03T00:00:00Z",
          "policy": "pinned"
        }
      }
    },
    {
      "remember": {
        "scope": {
          "agent": "agent:release-reviewer"
        },
        "kind": "procedural",
        "body": {
          "claim": "Coupon pricing tests need the tier fixture loaded first; without it they fail on a missing key rather than on the change under test."
        },
        "provenance": {
          "produced_by": "agent:release-reviewer",
          "observed_at": "2026-09-03T09:40:00Z",
          "correlation_id": "corr-a-0002"
        },
        "staleness": {
          "expires_at": "2026-12-02T00:00:00Z",
          "policy": "ttl"
        }
      }
    },
    {
      "recall": {
        "query": {
          "scope": {
            "agent": "agent:release-reviewer"
          },
          "need": "anything to know before running the pricing tests",
          "limit": 5
        },
        "result": {
          "scope_applied": {
            "agent": "agent:release-reviewer"
          },
          "items": [
            "mem-2f9c-tier-fixture"
          ],
          "age_seconds": [
            86400
          ]
        }
      }
    }
  ]
}
```

### Worked example 2 (proposed): an event and a schedule reach the same two calls - TARGET T1's third way in

_proposed_ - sources: `T-t1-03`, `T-t6-02`.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:memory:example:event",
  "title": "Nothing about the calls changes when no person is present",
  "description": "An external event writes what it observed, and a scheduled run recalls at the same scope the next morning. The subject prefix is the only difference from example 1.",
  "examples": [
    {
      "remember": {
        "scope": {
          "org": "org:platform"
        },
        "kind": "episodic",
        "body": {
          "claim": "The nightly index rebuild failed twice this week on the same shard; the retry succeeded both times."
        },
        "provenance": {
          "produced_by": "service:deploy-webhook",
          "observed_at": "2026-09-03T02:14:00Z",
          "correlation_id": "corr-evt-0007"
        },
        "staleness": {
          "expires_at": "2026-10-03T00:00:00Z",
          "policy": "ttl"
        }
      }
    },
    {
      "recall": {
        "query": {
          "scope": {
            "org": "org:platform"
          },
          "need": "recent failures on the nightly rebuild",
          "limit": 10
        },
        "result": {
          "scope_applied": {
            "org": "org:platform"
          },
          "items": [
            "mem-71aa-rebuild-flap"
          ],
          "age_seconds": [
            25200
          ]
        },
        "requested_by": "schedule:morning-triage"
      }
    }
  ]
}
```

### The failure shape (proposed): a recall at a scope the caller does not hold

_proposed_ - sources: `F-b3-13`.  Also carried in the body of `cap-memory` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:memory:example:scope-denied",
  "title": "The scope is not yours",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Media type application/problem+json. A recall at a scope the actor does not hold is a deterministic pre-execution refusal, which is exactly the registered `policy-denied` row in docs/decomposition.md section 2.1.6, so this example carries that type and its rule_id member rather than a memory-specific suffix cap-errors' closed registry has no row for. This is not the same as an empty result: empty means nothing was learned at a scope you hold, denied means you asked at a scope you do not.",
  "examples": [
    {
      "type": "urn:agentic:problem:policy-denied",
      "title": "The scope is not yours",
      "status": 403,
      "detail": "recall named principal user:dana; the run's actor is user:corey and holds principal user:corey, agent agent:release-reviewer and org org:platform.",
      "retryable": false,
      "correlation_id": "corr-b-0003",
      "rule_id": "memory.scope.not-held"
    }
  ]
}
```

## What a caller does

Step 1 below is carried in the body of `cap-memory` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Give every write an expiry you would actually accept, or mark it for review with a date. If you cannot name either, the item is not worth writing.**  
  _why:_ cap-memory requires the policy at write time precisely so it is not decided by whoever cleans up later. A store with no temporal validity model with no expiry dates or conflict detection is how a run acts confidently on last quarter's arrangement.  
  _sourced_ - `X-cap-memory-004` "no temporal validity model with no expiry dates or conflict detection"
- **Recall with a scope you hold and your need in words, then act on the items and their ages. Treat zero items as the normal answer on a first run, and continue.**  
  _why:_ The scope selector is what keeps another principal's items out of your context, and the age is what lets you, as cap-memory's step 5 requires of the interface, note this staleness rather than presenting the information as current. A caller that treats an empty recall as an error makes every first run look broken.  
  _sourced_ - `X-cap-memory-004`, `X-cap-memory-002` "note this staleness rather than presenting the information as current"
- **When something you remembered turns out to be wrong, supersede it with the corrected claim. Never write a second item that contradicts the first, and never edit in place.**  
  _why:_ cap-memory makes supersession the correction path so contradictions never accumulate; two live items that disagree turn every later recall into a coin toss, and the run that gets the wrong one has no way to tell.  
  _sourced_ - `X-cap-memory-008` "active supersession on every write so contradictions never accumulate"
- **Never write a grading criterion, a rubric, a secret or another principal's data into an item. If a judge needs to remember its criterion, it writes at its own scope.**  
  _why:_ agentic-stack states design rule 6 (F-b1-07); recall puts items straight into an agent's context, so an item is the shortest path there is from a criterion to the thing being judged by it.  
  _sourced_ - `F-b1-07` "An agent sees its outcome, never the criterion it is judged against"
- **Read a refusal as a problem-details object: check type, then retryable, then act on detail. A denied scope is fixed by asking at a scope you hold; an unavailable store is not fixed by asking again with different words.**  
  _why:_ Proposed usage of the failure shape above. The three refusals a caller actually meets are a denied scope, a write with no staleness policy, and an unreachable store, and only the last is ever worth a retry.  
  _proposed_ - `F-b3-13`

## Other caller invariants

- You never choose how an item is found. cap-memory keeps ranking out of the contract, and the consequence for a caller is that there is no index, no threshold and no k to tune: if a recall returns the wrong things, the fix is a narrower scope or a clearer claim, never a retrieval parameter.  
  _sourced_ - `X-cap-memory-001` "rank candidate memories by cosine similarity"
- Everything you write expires, and you say when. cap-memory requires a staleness policy on every write, so the question a caller answers at write time is not whether this should be forgotten but when - and a claim you would not defend in three months gets three months, not a pin.  
  _sourced_ - `X-cap-memory-005` "raw episodic data should always carry one"
- Empty and refused are different answers. cap-errors owns the closed registry of RFC 9457 problem details and cap-memory requires refusals to be typed; as a caller you read type first, then retryable, and you never treat a denied scope or an unreachable store as 'nothing learned'.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"

## Caller practices

- Proposed: say out loud, in whatever you produce, when you acted on a remembered item and how old it was. The item's age comes back with it, so the cost is one clause, and it is what lets a reader catch a stale arrangement that the run could not.  
  _proposed_ - `X-cap-memory-004` "An agent that retrieved a deployment guide last updated eighteen months ago"
- Proposed: write at the end of the work, not during it. A claim written mid-run records what you believed then; the same claim written after the outcome is known records what turned out to be true, and only the second is worth recalling.  
  _proposed_ - `X-cap-memory-008` "so contradictions never accumulate"
- Proposed: prefer an explicit key when you already know what you are looking for. cap-memory accepts a key as well as a need in words, and an exact key is the one query both stores answer identically - a need in words is answered well by the ranked store and only roughly by the file-backed one.  
  _proposed_ - `X-cap-memory-002` "which are tagging dimensions, not nested layers"

## Open questions carried over

- **Should a caller be able to recall at a scope it holds but did not write at - an agent reading its principal's items - by default, or only when the workflow declares it?**  
  _deciding evidence:_ Count, over real runs, how often an agent's useful recall came from its principal's scope rather than its own, against how often a principal's item reached an agent that should not have had it. If the second number is not near zero, the widening belongs in the workflow declaration where a reviewer can see it.  
  _default until then:_ Proposed: a recall names the dimensions it wants and the platform intersects them with what the actor holds, so reading the principal's scope is allowed but always explicit. An implicit union would make the scope applied to a recall something no caller wrote down.  
  `X-end-to-end-002` "user_id for facts that persist across sessions"

