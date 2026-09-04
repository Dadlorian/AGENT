---
name: "xc-identity-delegation"
description: "The identity guarantee as a placement, not a request: every action names an actor, the actor and the chain behind it are stamped onto the entry envelope by the driving adapter that received the work, and every chain is acyclic and ends at a root that was attested rather than asserted. Load it when deciding where in the call path who-asked gets decided, when an agent hands work to another agent, when a later stage is about to reconstruct a requester from logs, when an entry arrives with no caller at all because a schedule or an event produced it, when an audit cannot say which agent actually did a thing, or when a review asks how a human, an agent and an event all end up with the same actor record. Also load it when a request object is about to grow a field that omits the actor, when a hop forwards a caller's token unchanged, or when a chain loops back on a name it already contains."
---

# xc-identity-delegation (folded into `cap-identity`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the identity guarantee as a placement: the actor and the delegation chain are bound at entry by each driving adapter, before any planning or spend, and every recorded action is then checkable for a non-null actor, an acyclic chain, and a chain that terminates at a root nobody asserted for themselves. | sourced | `F-b4-03`, `F-b4-01`, `E-concern-identity`, `E-platform-platform` "Every action names an actor" |

## Entities

| Entity |
|---|
| `E-concern-identity` |
| `E-capability-identity` |
| `E-platform-platform` |
| `E-not-running-identity` |
| `E-standard-oauth-2-0-token-exchange` |
| `E-standard-workload-identity` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-oauth-2-0-token-exchange` | RFC 8693 | unverified | https://datatracker.ietf.org/doc/html/rfc8693 | `F-b3-14`, `X-entry-composition-048`, `X-xc-identity-delegation-001` |
| `E-standard-workload-identity` | unverified | unverified | - | `F-b3-14`, `X-xc-identity-delegation-005` |

- `E-standard-oauth-2-0-token-exchange` version note: cap-identity owns this row and records the same RFC number; a search-only research record titles it RFC 8693: OAuth 2.0 Token Exchange and the specification was not fetched from this environment, so it stays unverified here too.
- `E-standard-workload-identity` version note: cap-identity owns this row: the recorded column names workload identity as a governing standard without naming a document, and nothing was fetched here. This guarantee depends on it only for what a root hop must be.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| bind_actor (proposed operation set; PASS.md states this concern as one sentence, not as a list of calls) | an inbound request as the driving adapter that received it sees it, plus whatever credential that adapter can present or attest for the caller (proposed) | the entry envelope with a non-null actor and a delegation chain whose first hop is the caller, or the registered typed refusal; there is no path in which the envelope is admitted with the actor left to a later stage (proposed) | proposed | `F-b4-03`, `X-entry-composition-042` |
| extend_chain (proposed) | an admitted envelope's chain and the agent or service about to act on it (proposed) | a chain one hop longer with the new actor as the current actor, or a refusal when that actor already appears in the chain (proposed) | proposed | `F-b4-03`, `X-cross-structure-037` |
| assert_chain (proposed) | a recorded action read back from the append-only store at a pinned head (proposed) | three decisions and nothing else - actor present, chain acyclic, chain rooted - as a pure re-runnable function of the record, so the same corpus always yields the same verdict (proposed) | proposed | `F-b4-03`, `F-b1-06` |

### Shapes (JSON Schema 2020-12)

**EntryActorBinding (proposed summary shape; cap-identity owns the ActorIdentity object this points at, and the full chain-validity schema is in references/xc-identity-delegation-identity-delegation-checks.md)** (proposed; sources: `F-b4-03`, `T-t2-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:identity:entry-binding:0.1",
  "title": "EntryActorBinding",
  "description": "Proposed. What a driving adapter must have written onto the entry envelope before validation admits it. actor is required with no default, and bound_at names the adapter that stamped it so that no later stage can be the first to know who asked.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "actor",
    "bound_at",
    "bound_before"
  ],
  "properties": {
    "actor": {
      "$ref": "urn:agentic:identity:actor:0.1"
    },
    "bound_at": {
      "type": "string",
      "minLength": 1,
      "description": "The driving adapter that performed the binding."
    },
    "bound_before": {
      "const": "planning",
      "description": "The binding precedes planning and therefore precedes every metered call. It is a const because there is no later moment to offer."
    }
  }
}
```

**ChainValidity (proposed; the three decisions docs/decomposition.md section 3.4 row X2 names, as a shape a report can carry)** (proposed; sources: `F-b4-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:identity:chain-validity:0.1",
  "title": "ChainValidity",
  "description": "Proposed. The verdict on one recorded action. repeated_actor is populated only when acyclic is false, and root_obtained_via records how the last hop was established rather than that it exists.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "actor_present",
    "acyclic",
    "rooted"
  ],
  "properties": {
    "actor_present": {
      "type": "boolean"
    },
    "acyclic": {
      "type": "boolean"
    },
    "rooted": {
      "type": "boolean"
    },
    "repeated_actor": {
      "type": "string"
    },
    "root_obtained_via": {
      "enum": [
        "workload_attestation",
        "direct"
      ]
    }
  }
}
```

**ActorBindingByWayIn (proposed worked instances, one per T6.2 door)** (proposed; sources: `T-t6-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:identity:ways-in:0.1",
  "title": "ActorBindingByWayIn",
  "description": "Proposed. One worked binding for each of T6.2's four doors, taken from the runnable reference in examples/end-to-end. The chain is current actor first and least recent last, the ordering cap-identity settled. Nothing downstream branches on which door produced the record.",
  "type": "array",
  "minItems": 4,
  "examples": [
    [
      {
        "way_in": "human",
        "actor": {
          "subject": "user:corey",
          "delegation_chain": [
            {
              "actor": "user:corey",
              "obtained_via": "direct"
            }
          ]
        }
      },
      {
        "way_in": "agent",
        "actor": {
          "subject": "agent:partner-sre-bot",
          "delegation_chain": [
            {
              "actor": "agent:partner-sre-bot",
              "obtained_via": "workload_attestation"
            },
            {
              "actor": "service:intake",
              "obtained_via": "token_exchange"
            },
            {
              "actor": "user:corey",
              "obtained_via": "direct"
            }
          ]
        }
      },
      {
        "way_in": "event",
        "actor": {
          "subject": "service:alerting",
          "delegation_chain": [
            {
              "actor": "service:alerting",
              "obtained_via": "workload_attestation"
            },
            {
              "actor": "service:intake",
              "obtained_via": "token_exchange"
            }
          ]
        }
      },
      {
        "way_in": "schedule",
        "actor": {
          "subject": "user:corey",
          "delegation_chain": [
            {
              "actor": "schedule:nightly-fault-sweep",
              "obtained_via": "workload_attestation"
            },
            {
              "actor": "user:corey",
              "obtained_via": "direct"
            }
          ]
        }
      }
    ]
  ]
}
```

**IdentityUntrustedInstance (proposed worked rejection; cap-errors owns the object and the closed registry the type comes from)** (proposed; sources: `F-b4-07`, `F-b4-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:identity:untrusted-instance:0.1",
  "title": "IdentityUntrustedInstance",
  "description": "Proposed. The one refusal this guarantee returns, shown rather than described. retryable is false because a chain that repeats an actor does not become acyclic on a second attempt.",
  "allOf": [
    {
      "$ref": "urn:agentic:problem:0.1"
    }
  ],
  "examples": [
    {
      "type": "urn:agentic:problem:identity-untrusted",
      "title": "Identity untrusted",
      "status": 401,
      "detail": "delegation chain for entry external-partner-agent-task repeats actor service:intake at hop 1 and hop 3",
      "retryable": false,
      "correlation": {
        "run_id": "run-external-0001",
        "correlation_id": "corr-external-0001",
        "depth": 1
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every action names an actor, and the check is over recorded actions rather than over the schema: a corpus in which one action has a null actor fails, however well-formed the field is everywhere else. | sourced | `F-b4-03`, `E-concern-identity` "Every action names an actor" |
| The guarantee is not declinable: there is no field, header, role or configuration value that admits an envelope with no actor or with a chain shorter than the hops that actually occurred, and an envelope missing one is refused rather than defaulted. | sourced | `F-b4-01`, `F-b1-08` "a caller cannot decline them" |
| cap-identity settles the chain's ordering and its mechanics (F-b3-14, and its open question on ordering): current actor first, least recent last. What this guarantee adds is that the ordering is load-bearing for the rooting assertion, since the root is then the last element and a checker written against the other ordering reports every chain as assembled backwards. | sourced | `X-entry-composition-048`, `F-b3-14` "The least recent actor is the most deeply nested." |
| The chain is a claim structure that dispatch carries and does not define. A dispatch adapter may move a chain, refuse one, and record one; it may not decide what a hop is, which is why swapping the dispatcher changes nothing about this guarantee. | sourced | `F-b5-03`, `F-b4-03` "This is the seam that decides whether agent execution is pluggable at all." |
| cap-errors owns the failure object and the closed registry (F-b4-07). What this guarantee adds is that its one refusal is the registered identity-untrusted row at status 401, so a caller branches on a type and never on the word untrusted appearing in a message. | sourced | `F-b4-07` "Never parsed from prose" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: nothing in the contract lets a caller supply its own chain and have it believed. A presented chain is input to verification, never the verified result, and the envelope that leaves the driving adapter carries what the adapter established rather than what the caller sent. Research query: is there a fetched source distinguishing a presented chain (input to verification) from a verified chain (the result) as a named security principle, or is that this row's own framing? | proposed | `F-b4-01`, `F-b4-03` |
| cap-identity states that prior actors are informational only. What this guarantee refuses to expose is the enforcement consequence: the policy gate and every other enforcement point are handed the current actor alone, while the whole chain goes to the audit corpus, so no rule can come to depend on a hop that a future exchange might legitimately remove. | sourced | `X-cross-structure-038` "the consumer of a token MUST only consider the token's top-level claims" |
| The criterion an actor's work will be judged against never appears in the actor object, in any hop of the chain, or in the refusal this guarantee returns. agentic-stack states design rule 6 (F-b1-07); what it forbids here is a detail string that explains a rejected chain by naming what the work was being graded for. | sourced | `F-b1-07` "The grader is never visible to the graded." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Bind the actor in the driving adapter that received the work, not in the core and not at dispatch: establish the caller, write actor and delegation_chain onto the entry envelope, and refuse the entry when neither a credential nor an attestation can establish one. | Every cross-cutting concern has to hold whichever entry point was used, and the entry point is the only place that still has the protocol-level evidence of who called. A stage further in sees an envelope and has to guess. | sourced | `T-t2-03`, `X-entry-composition-042` "every cross-cutting concern are managed across the entire structure" |
| 2 | Make actor required on the envelope schema with no default and no nullable variant, so an adapter that forgets to bind produces a refusal at admission rather than a run with an empty field. | A default invented at intake is an unattributable action wearing a name. The platform applies this concern rather than the caller requesting it, so the schema must offer nothing to leave out. | sourced | `F-b4-01`, `F-b4-03` "a caller cannot decline them" |
| 3 | Extend the chain at every hop by exchanging for a new credential and adding the acting agent as the new current actor; treat a hop that forwards the caller's credential unchanged as having added no hop at all. | The chain grows as each service calls the next, so the last consumer can still see who is acting on behalf of whom with the original actor named. cap-identity owns the exchange mechanics (F-b3-14); what matters here is that a forwarded credential leaves the chain the same length as the number of hops rises. | sourced | `X-cross-structure-037`, `X-cap-identity-004` "the delegation chain grows" |
| 4 | Refuse a hop whose actor already appears anywhere in the chain, at the moment the hop is added, and count the same condition again over the recorded corpus. | Proposed, and the reason the definition of done below breaks exactly here: a loop is cheap to create by re-exchanging back to a service that already acted, it looks like a longer and therefore better audit trail, and it destroys the one property the trail is read for. Research query: is there a fetched source recommending refusal-at-add-time for a repeated actor specifically, rather than this row's own reasoning about what a loop would do to the audit trail? | proposed | `F-b4-03` |
| 5 | Root every chain: the last hop is either a workload attested from facts about where it runs or an authenticated human principal, and an entry that can offer neither - a schedule firing, an event with no caller - is rooted at the attested identity of the adapter that raised it. | Proposed. An entry with no human behind it still has an actor, and the honest one is the workload that produced it; leaving such entries unrooted would make the rooting assertion pass only for the ways in that happen to carry a credential. Research query: is there a fetched source stating a schedule- or event-originated chain should root at the raising adapter's attested identity specifically, or is that this row's own extension of workload identity federation's general authentication mechanism? | proposed | `X-xc-identity-delegation-005`, `T-t1-03` |
| 6 | Carry the chain as data on the dispatch request and keep its definition out of the dispatch seam: a dispatcher moves, refuses and records a chain, and never decides what a hop is. | seam-dispatch states the row this reuses (F-b5-03): today there are three implementations and no contract between them, so a guarantee defined inside one of them would have to be redefined in the other two and would differ in all three. | sourced | `F-b5-03`, `F-b4-03` "Today there are three implementations and no contract between them." |
| 7 | Return the registered identity-untrusted problem object at status 401 with retryable false when a chain does not verify, and put the failing condition in detail without putting the credential in it. | cap-errors owns the object and the closed registry; this guarantee supplies one registered row of it. Repeating a verification that failed on the shape of the chain returns the same answer, so retryable false is a fact about the failure and not a policy. | sourced | `F-b4-07`, `F-b4-03` "Typed and machine-readable" |
| 8 | Wire the identical binding on all three ways in and prove it by replaying one corpus through each: a human entering the system, an agent entering the system, and an internal or external event entering the system. The three worked bindings in contract.shapes above are what each must produce. | TARGET T1 names those three ways in, and a guarantee wired only on the door someone remembered is declinable by choosing another door. Replaying one corpus through each is what turns cannot be declined into a count. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Read a chain that did not grow as the defect it is. cap-identity states the validate-then-exchange rule (X-cap-identity-004); what this adds, as this skill's own proposed consequence, is the detection: compare chain length against the number of recorded hops for the same action, because a forwarded credential produces a chain that is short rather than one that is wrong. | sourced | `X-cap-identity-004` "the next service in the chain will accept it" |
| Do not ask the chain to prove that a hop stayed inside the authority it was given. The records on file note that no token-local mechanism exists for proving downstream delegation intent remains consistent with the original scope, so attenuation belongs to the budget and policy concerns and is never inferred from the chain's shape. | sourced | `X-cap-mandate-broker-008` "does not define a token-local mechanism for proving that downstream delegation intent remains consistent" |
| agentic-stack and build-definition-of-done both state the structurally-green-gate finding (F-a7-03). What it costs here specifically: a corpus containing no delegated action passes every assertion this guarantee makes, so report delegated actions checked as its own number and fail the run when it is zero. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Keep the check inside the enforcement path rather than beside it. The inventory of what runs today already records a concern whose conformance checks exist and are not wired into the path that enforces them, which is the failure this layer exists to avoid repeating for identity. | sourced | `F-a6-04`, `E-not-running-policy-in-the-gate-path` "Conformance checks exist; not wired into the enforcement path" |
| Make the binding a step every envelope crosses rather than a call every adapter author must remember: the records on file describe an admission chain that modifies a request before anything validates or persists it, which is the shape that makes a guarantee non-optional without depending on discipline. | sourced | `X-cross-structure-023` "return JSON patches that modify the resource" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 harness/identity/conformance.py --adapter dryrun --adapter second |
| Expected | exit 0, last line `conformance PASSED: 32/32 cases, 2 binding(s), selected_by=configuration`, with one line per binding reading `cases=16 passed=16 actions_checked=50 short_chains=0 cyclic=0 executing_unit_mismatch=0 authority_calls=0 product_hits=0`: a 50-action corpus, so the acyclicity and rooting assertions had multi-hop chains to assert on. What this run stands in for: the criterion this facet carried before ceremony 61 (finding R61B-018) moved its prose out of the criterion field, which is the check this guarantee ultimately needs and which nothing on disk runs yet - docs/decomposition.md section 3.4 row X2, made precise. Proposed tool, built with the first implementation of this guarantee: `python3 tools/conformance_identity_delegation.py --corpus out/actions.jsonl --min-actions 100 --report out/identity-delegation.json`. Over a corpus of at least 100 recorded actions it asserts that no action has a null `actor`, that every `delegation_chain` is acyclic, that every chain terminates at a hop whose `obtained_via` is `workload_attestation` or `direct`, and that every action's actor is the one bound on its entry envelope rather than one stamped later. It reports `actions_checked`, `delegated_actions_checked`, `null_actor`, `cyclic`, `unrooted` and `bound_at_entry`. Expected of that check: exit 0 and one summary line `actions_checked=100 delegated_actions_checked=<k> null_actor=0 cyclic=0 unrooted=0 bound_at_entry=100`, with `delegated_actions_checked` greater than zero so the acyclicity and rooting assertions had multi-hop chains to assert on. |
| Deliberate breakage | sed -i 's/if any(hop.actor == actor for hop in chain):/if False:/' harness/identity/interface.py -- classify_chain never reports `cyclic`, so an exchange back to an actor already in the chain is issued instead of refused. Restore with git checkout harness/identity/interface.py. |
| Expected failure | exit 1 on both bindings at the cycle case, naming the action and the repeated actor, while short_chains stays 0 and actions_checked stays at 50 - which is what shows the loop went undetected rather than the corpus never being read. Status claimed: tools/measure.py has recorded neither run for this pair here. The breakage the prose criterion above stood for, and what it expected: Permit a `direct` hop to name an actor already present earlier in the chain: re-exchange one delegated action back to the intake service that already appears at hop 1, and change nothing else. The acyclicity check fails: `cyclic` becomes 1, the run exits non-zero naming that action and the repeated actor, while `null_actor` stays 0, `bound_at_entry` stays 100 and `actions_checked` stays at or above 100 - which is what shows the loop was detected rather than the corpus never being read. Claimed: PASS.md A6 records no identity field anywhere in the system, so neither the field, the binding nor the tool exists here and this check starts red by construction, which is the correct starting state rather than a defect to hide. |
| Status | claimed |
| Evidence | `F-a6-05`, `F-part-c-04` "No identity field anywhere in the system" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `cap-identity`

Used by: `seam-dispatch`, `xc-identity-delegation-implement`, `xc-tenancy`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| docs/decomposition.md section 2.1 describes delegation_chain as oldest hop first and section 3.4 row X2 says a chain terminates at a root workload identity, while the four entry files in examples/end-to-end put the current actor first. Which end does the rooting assertion read? | The edit cap-identity's ordering question names: one ordering holding in the runnable reference, in the dispatch shape and in the assertions. Until it lands, a checker written against either ordering reports every chain produced by the other as unrooted. | cap-identity applied 1-3-1 on 2026-09-03 and adopted current-actor-first; this guarantee follows that decision rather than re-deciding it, so the rooting assertion reads the last element and row X2's terminates at means the last element under that ordering. The alternative considered and declined here was to assert on both ends, which would let a chain rooted at neither pass. | `T-t5-02`, `X-entry-composition-048` "identify the three best possible solutions that align to the goal" |
| Row X2 says a chain terminates at a root workload identity, but the runnable human entry is a single `direct` hop naming a person, and no workload appears in it. Does a human-rooted chain satisfy the rooting assertion? | 1-3-1 applied on 2026-09-03. Options: (a) read root workload identity as a root established rather than asserted onward, covering both an attested workload and an authenticated human principal; (b) re-root every human entry at the intake workload, making the shortest chain two hops; (c) exempt human entries from the rooting assertion. Recommendation followed: (a), carried into the ChainValidity shape's root_obtained_via enum. Option (b) adds a hop that records nothing a reader did not already know, and (c) makes the assertion silent on the way in that carries the most authority. | A chain is rooted when its last hop's obtained_via is workload_attestation or direct. The question closes when row X2 is reworded or the human entry is re-rooted. | `T-t5-02`, `T-t1-01` "define the problem, identify the three best possible solutions" |
| Does a maximum chain depth belong to this guarantee or to the budget guarantee that already carries a maximum delegation depth? | A corpus with long but acyclic chains: if the depth that hurts is a cost and fan-out problem, the existing ceiling catches it first and a second bound here would only disagree with it. If long chains fail verification before they cost anything, the bound belongs here. | Depth stays with the budget ceiling and this guarantee asserts only actor presence, acyclicity and rooting. Two bounds on one number in two concerns is how they come to disagree. | `F-b4-02`, `F-b4-03` "Every unit of work carries a ceiling" |
| Where does the adapter pair for this guarantee live, given that PASS.md B3 records the Identity adapter as absent and every identity adapter entity belongs to the capability row rather than to this concern? | Whether a reviewer reading only this skill can say what would have to change for the enforcement point to move. If not, the pair belongs here as well as in the implement facet. | The pair, the axes their execution models differ on and the swap procedure are recorded once in xc-identity-delegation-implement, which builds on build-adapter-pair. This skill states only that the enforcement point is entry and that nothing implements it today, which is cap-identity's starting-point row rather than a new observation. | `F-b3-14`, `F-a6-05` "No identity field anywhere in the system" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-identity-delegation 2831cb4f, 2026-09-03 |
