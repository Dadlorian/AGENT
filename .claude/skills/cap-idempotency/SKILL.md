---
name: "cap-idempotency"
description: "Idempotency contract and build, including the lease: one claim over a key and payload digest turns a repeated request into one execution and one answer. Load it when a retry, redelivery or re-fire could run twice, when two copies race for one key, when choosing a retention window, or when judging whether a store deduplicates or merely records keys."
---

# cap-idempotency

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract that makes a repeated externally-triggered request produce one execution and one answer, so that replay safety is a property the platform delivers rather than a convention each caller reimplements. | sourced | `F-b4-08`, `F-b3-16`, `E-concern-idempotency`, `E-capability-idempotency` "Every externally-triggered action is safe to replay" |

## Entities

| Entity |
|---|
| `E-capability-idempotency` |
| `E-concern-idempotency` |
| `E-standard-idempotency-key-convention` |
| `E-adapter-key-on-the-wire` |
| `E-adapter-no-lease` |
| `E-swap-candidate-any-keyed-lease-store` |
| `E-core-component-ledger` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-idempotency-key-convention` | draft-ietf-httpapi-idempotency-key-header-07 | unverified | https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-07 | `F-b3-16`, `X-cap-idempotency-001`, `X-cap-idempotency-002`, `X-cross-structure-041` |

- `E-standard-idempotency-key-convention` version note: draft-ietf-httpapi-idempotency-key-header-07 (search-only research records place it in the IETF httpapi working group and say it expired without becoming an RFC; the draft text was not fetched from this environment)

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| claim (call name is ours; the uniqueness-and-conflict rule it enforces is the draft's own MUST) | an idempotency key, the digest of the payload the key belongs to, and the scope the key must be unique within | fresh, meaning this caller now owns the one execution; duplicate carrying a reference to the first result; or conflict, meaning the key is held under a different payload digest | sourced | `F-b4-08`, `X-cap-idempotency-002` "The idempotency key MUST be unique and MUST NOT be reused with another request with a different request payload." |
| complete (call name is ours; the replay-safety obligation it seals is the platform's own) | a key currently held by a fresh claim, and a reference to the result that execution produced | the claim sealed against that reference, after which every later claim of the key answers duplicate with the same reference for as long as the retention window lasts | sourced | `F-b4-08` "Every externally-triggered action is safe to replay" |
| resolve (call name is ours; the Ledger's own deduplication-authority role is the sourced fact) | an idempotency key and its scope | the prior result reference and whether that execution has finished, or null when the key has never been claimed; this is the read a planner needs before it plans work that has already been done; cap-state-persistence states F-b2-06 under this quote for the record store, and this row names the read the claim needs | sourced | `F-b2-06` "append-only across runs; the deduplication authority" |
| expire (call name is ours; that retention windows are provider-declared and vary is the sourced fact) | a claim whose declared retention window has elapsed | the claim removed, after which the same key is claimable again and replay safety for it has ended; the window is therefore part of the contract, not an implementation detail | sourced | `X-cap-idempotency-007`, `X-cap-idempotency-008` "Despite consistent header names, idempotency implementations vary by provider in retention windows and parameter handling." |

### Shapes (JSON Schema 2020-12)

**IdempotencyClaim (proposed shape; the full schema, the outcome state machine and the retention table are in references/idempotency-claim.md)** (sourced; sources: `X-cap-idempotency-002`, `X-cap-idempotency-005`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:idempotency:claim:0.1",
  "title": "IdempotencyClaim",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "idempotency_key",
    "payload_digest",
    "scope",
    "claimed_at",
    "retention_s"
  ],
  "properties": {
    "idempotency_key": {
      "type": "string",
      "minLength": 8,
      "maxLength": 255
    },
    "payload_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$",
      "description": "Digest of the canonical payload. The payload itself is never held here."
    },
    "scope": {
      "type": "string",
      "description": "The resource owner within which the key must be unique."
    },
    "claimed_at": {
      "type": "string",
      "format": "date-time"
    },
    "retention_s": {
      "type": "integer",
      "minimum": 1,
      "description": "Declared window. After it elapses the key is claimable again."
    },
    "result_ref": {
      "type": [
        "string",
        "null"
      ],
      "description": "Set by complete; null while the one execution is still in flight."
    }
  }
}
```

**ClaimOutcome (proposed shape; the three answers claim may give)** (sourced; sources: `F-b4-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:idempotency:outcome:0.1",
  "title": "ClaimOutcome",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "outcome"
  ],
  "properties": {
    "outcome": {
      "enum": [
        "fresh",
        "duplicate",
        "conflict"
      ]
    },
    "result_ref": {
      "type": "string",
      "description": "Required when outcome is duplicate."
    },
    "in_flight": {
      "type": "boolean",
      "description": "True when a duplicate is answered while the first execution has not finished."
    },
    "problem": {
      "$ref": "urn:agentic:problem:0.1",
      "description": "Required when outcome is conflict. The failure shape belongs to cap-errors."
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "outcome": {
            "const": "duplicate"
          }
        },
        "required": [
          "outcome"
        ]
      },
      "then": {
        "required": [
          "result_ref"
        ]
      }
    },
    {
      "if": {
        "properties": {
          "outcome": {
            "const": "conflict"
          }
        },
        "required": [
          "outcome"
        ]
      },
      "then": {
        "required": [
          "problem"
        ]
      }
    }
  ]
}
```

**Worked example 2 (proposed): the same key with a different body [caller's view, folded from cap-idempotency-use]** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:idempotency:example:conflict",
  "title": "Same key, different envelope",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Change one field of the payload and re-send under the same key. Reproduced in examples/end-to-end on 2026-09-03: exit code 2, body on stdout with media type application/problem+json, nothing executed.",
  "examples": [
    {
      "type": "urn:agentic:problem:idempotency-conflict",
      "title": "Same idempotency key, different envelope",
      "status": 409,
      "detail": "key human-checkout-500s-2026-09-03 was completed at seq 13 with a different body",
      "retryable": false
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The contract this capability must deliver is one sentence: every externally-triggered action is safe to replay. | sourced | `F-b4-08`, `E-concern-idempotency` "Every externally-triggered action is safe to replay" |
| The recorded row for this capability names the idempotency-key convention as the standard, key on the wire, no lease as the adapter today, and any keyed lease store as the swap candidates. | sourced | `F-b3-16`, `E-capability-idempotency`, `E-adapter-key-on-the-wire`, `E-adapter-no-lease` "key on the wire, no lease" |
| A key carried on the wire deduplicates nothing by itself. The deduplicating act is claim(key, payload_digest), a conditional write that exactly one caller can win; a key that is recorded but never claimed leaves both copies of a duplicated request executing, which is the state the adapter-today column records. | sourced | `F-b3-16` "key on the wire, no lease" |
| The draft the convention comes from makes uniqueness normative rather than advisory: the idempotency key MUST be unique and MUST NOT be reused with another request with a different request payload. | sourced | `X-cap-idempotency-002`, `X-cross-structure-041` "The idempotency key MUST be unique and MUST NOT be reused with another request with a different request payload." |
| Consequence of that MUST: the same key under a different payload digest is a conflict, and a conflict is answered with a typed failure rather than with a silent second execution or a message. cap-errors owns that failure shape and the idempotency-conflict type (F-b4-07); this row only fixes when the type is raised. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| Consequence of TARGET T2.3: the claim is applied by the platform at every entry point, whichever entry point was used, and again at each recorded step boundary, so replay safety is never a property of one entry kind or of one caller's diligence. | sourced | `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure" |
| The core already owns a deduplication authority: the Ledger is append-only across runs and is the deduplication authority, and removing it means nothing survives the run. cap-state-persistence states the same record for the durable store beneath; on this interface the fact fixes which component answers whether a key has been claimed. | sourced | `F-b2-06`, `E-core-component-ledger` "append-only across runs; the deduplication authority" |
| This interface is nonetheless not defined in terms of the Ledger. A claim needs a keyed conditional write, a payload digest and a retention window, and any store offering those provides one; build-evidence (formerly build-adapter-pair) states design rule 3 (F-b1-04), and binding the claim to one projection of the log would leave the pair with nothing to swap. | sourced | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| The retention window is a declared field of the claim rather than an implementation detail, because the header name is consistent across the industry while retention windows, parameter-mismatch behaviour, and concurrency handling all differ between providers, so an undeclared window means an unknown contract. | sourced | `X-cap-idempotency-007` "Despite consistent header names, idempotency implementations vary by provider in retention windows and parameter handling." |
| All three of TARGET T1's ways in - a human, an agent, an internal or external event - reach this capability the same way, and enhancing one aspect of it leaves the rest untouched: changing the retention window, moving the claim from a log fold to a lease store, or adding a new entry kind changes nothing in a caller that sends one key per intent, because the key is the only thing it was ever asked for. cap-errors states the same record (T-t2-02) for its own boundary, and cap-state-persistence states T-t1-01 to T-t1-03 under this quote for the store; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the request payload is not exposed by this interface, only its digest. A claim must be answerable without the store keeping a copy of the caller's body, so that comparing two payloads never becomes a reason to retain caller data for the length of the retention window. Research query: does the Stripe idempotency-key documentation on file (X-cap-idempotency-003/004) say whether the provider retains the request body itself or only a digest for the retention window, which would confirm or contradict this design choice? | proposed | `X-cap-idempotency-002` |
| Proposed: claim returns a reference to the first result, never the result's contents. Who may read that result stays a matter for identity and policy; holding the key is not authorisation. Research query: is there a recorded fact from cap-policy or xc-guarantees (formerly xc-tenancy) stating that possessing a key or a lease reference never substitutes for an authorisation check, which this row could cite by name instead of asserting the rule fresh? | proposed | - |
| The criterion a result is judged against never travels on a claim, on a duplicate answer or on a conflict problem. agentic-stack states design rule 6 (F-b1-07) and cap-state-persistence states it for the store; the consequence here is that the duplicate path is caller-visible like any other. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Adopt the field name from the draft and write the lease semantics down yourself, in docs/decomposition.md section 2.1.6, rather than citing the draft as if it settled behaviour. | Proposed decision. The header is defined in an IETF draft in the httpapi working group and it has expired without becoming an RFC, so there is a name to inherit and no normative text to defer to; treating it as a specification would be citing a document that does not exist. | sourced | `X-cap-idempotency-001` "remains an expired IETF draft without normative status" |
| 2 | Proposed: make claim(key, payload_digest, scope) the single deduplicating call, with exactly the three outcomes in the ClaimOutcome shape above, and let no other code path decide that a request is a repeat. | Proposed design. Three outcomes are the smallest set that separates the three real cases: nobody has this key, somebody has it with this payload, somebody has it with a different payload. Any implementation that answers only yes or no has to guess at the third. Research query: does the Stripe or Adyen idempotency documentation on file (X-cap-idempotency-003/004/008) describe a third outcome distinct from hit/miss, confirming three states is an industry pattern rather than this interface's own design? | proposed | `F-b4-08`, `X-cap-idempotency-002` |
| 3 | Require an idempotency key on every externally-triggered entry and refuse an entry that arrives without one, instead of generating a key on the caller's behalf. | Proposed design, from the required idempotency_key field in docs/decomposition.md section 2.1.1 and the shared entry envelope in examples/end-to-end. A key the platform mints is unique per arrival, so it cannot recognise the second arrival of the same intent; only the originator knows that two requests are the same request. | sourced | `F-b4-08` "Every externally-triggered action is safe to replay" |
| 4 | Publish, per key-accepting boundary, the scope the key must be unique within, and tell clients to generate a UUID or a similar random identifier. | It is RECOMMENDED that a UUID or a similar random identifier be used as an idempotency key, and uniqueness of the key MUST be defined by the resource owner and MUST be implemented by the clients of the resource: an undocumented scope leaves clients to guess how far their key has to be unique. | sourced | `X-cap-idempotency-005` "It is RECOMMENDED that a UUID or a similar random identifier be used as an idempotency key. Uniqueness of the key MUST be defined by the resource owner and MUST be implemented by the clients of the resource." |
| 5 | Declare the retention window for every boundary that accepts a key, and say in the same place what happens to a key that arrives after its window has elapsed. | Published windows range widely: one platform expires keys after 24 hours to balance deduplication coverage with storage costs, while at another idempotency keys are valid for 7 to 14 days after first submission. A window inherited by assumption is a replay guarantee nobody has agreed to. | sourced | `X-cap-idempotency-008`, `X-cap-idempotency-004` "idempotency keys are valid for 7 to 14 days after first submission" |
| 6 | Layer the defence rather than resting on the entry check alone: start with idempotency keys at your API boundary to catch client-side retries, add message deduplication in your consumers to handle queue redeliveries, and use database constraints as your final safety net for critical operations. | Each layer catches a different duplicate. The boundary key catches a client that retried; consumer deduplication catches a redelivered message the client never re-sent; a uniqueness constraint catches the case where both of those were bypassed, which is the case that costs money. | sourced | `X-cap-idempotency-006` "Start with idempotency keys at your API boundary to catch client-side retries, add message deduplication in your consumers to handle queue redeliveries, and use database constraints as your final safety net for critical operations." |
| 7 | Return a conflict through the platform's failure shape as the registered idempotency-conflict type, and take the shape, the media type and the registry from cap-errors rather than defining a failure here. | Proposed composition. cap-errors already fixes what a failure looks like and holds the closed type registry; a second failure object minted at this boundary would be one more format every client has to learn, for a case that is not special. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 8 | Proposed: judge an implementation by the concurrent case, not the sequential one. Fire the same key many times at once and require exactly one execution, with at least one duplicate answered while the first execution is still in flight. | Proposed criterion. Concurrency handling is precisely what differs between providers of this convention, and a sequential replay passes on any implementation that records the key at all, including one with no lease. If the test never overlaps two requests, it has not tested the lease. Research query: has this definition_of_done's concurrent-fire test actually been run against a second, lease-based adapter and shown to fail on an implementation with no lease, or is the criterion still only reasoned about? | proposed | `X-cap-idempotency-007`, `F-b3-16` |
| 9 | Generate one random identifier per intent, at the moment you decide to do the thing, and store it with the intent rather than minting it at the moment of sending. | It is RECOMMENDED that a UUID or a similar random identifier be used as an idempotency key. A key generated at send time is new on every retry, so the retry looks like a new intent, which is the failure this field exists to prevent. | sourced | `X-cap-idempotency-005` "It is RECOMMENDED that a UUID or a similar random identifier be used as an idempotency key." |
| 10 | Proposed: open references/idempotency-claim.md when you need the full claim and outcome schemas, the outcome state machine, or the table of published retention windows. This skill body is enough to judge an implementation without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed, progressive disclosure. The state machine and the window table are long material, and inlining them would make the contract longer than the thing it governs. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Test every candidate design against the definition itself: idempotency is the ability to apply the same operation multiple times without changing the result beyond the first try. A design that returns a different answer to the second call has not achieved it, however few times it executes. | sourced | `X-cap-idempotency-003` "the ability to apply the same operation multiple times without changing the result beyond the first try" |
| A key names one operation attempt and nothing larger: don't use the same key across different user sessions or checkout attempts. A key scoped to a user, a workflow or a day silently merges two intents that were meant to happen twice. | sourced | `X-cap-idempotency-004` "Don't use the same key across different user sessions or checkout attempts." |
| Never inherit another system's semantics from the field name: while the header name is consistent across the industry, the semantics are whatever each provider decided. Two integrations that both speak this convention can still disagree about what a repeat means. | sourced | `X-cap-idempotency-007` "While the header name is consistent across the industry, the semantics are whatever each provider decided" |
| Proposed: an operation whose repetition costs nothing still needs a key, because the cheap case is where the habit is formed. The expensive cases are found by the same code path, and a boundary that accepts keys only sometimes is a boundary whose callers learn to omit them. Research query: does any of the researched idempotency conventions (X-cap-idempotency-002/003/006) recommend requiring a key unconditionally rather than only above a cost threshold, which would source this row's blanket requirement? | proposed | `X-cap-idempotency-003` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-key-on-the-wire` | today | The recorded adapter carries the idempotency key on the envelope and writes it into the log. It serves resolve after the fact - a reader can look a key up once the execution is over - and serves no part of claim, because nothing takes the key before execution begins. | Proposed: cannot answer duplicate while the first execution is still in flight, and cannot stop two concurrent copies of one request from both executing, because no conditional write happens before execution starts. It is the adapter the concurrent half of the criterion below is built to fail. | Introduce claim in front of execution and leave the wire format untouched: the envelope field does not change, only who reads it and when. cap-idempotency-implement owns the enforcing pair, the per-adapter conformance subsets and the full procedure; this row records only the roles PASS.md B3 fixes and the axis the pair differs on. | claimed | `F-b3-16`, `E-adapter-key-on-the-wire`, `E-adapter-no-lease` "key on the wire, no lease" |
| `E-swap-candidate-any-keyed-lease-store` | second | Any store offering a keyed conditional write serves claim as a compare-and-set taken before execution begins, holding the payload digest, the in-flight state and the declared retention window until complete seals the claim or expire releases it. | Proposed: cannot make progress when its own store is unreachable, where the recorded adapter needs nothing beyond the log the platform already writes. The axis the pair is chosen for is when the decision is taken - before the fact under contention, versus after the fact from a completed record - so a suite that passes over both has not been shaped around either. | Select the adapter by configuration only, with no code edit between runs, and run the identical race suite against each; the merged report must show adapters_run == 2. agentic-stack already states design rule 3 (F-b1-04): swappability is a tested property and the second adapter exists to prove the first is not load-bearing. What is new here is the axis, not the rule. | claimed | `F-b3-16`, `F-b1-04` "any keyed lease store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/idempotency/test.sh && python3 harness/idempotency/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 16d354c: exit 0; last lines:   adapter=conditional-write-lease cases=8 passed=8 supports_in_flight=True overlapped=19 \| conformance PASSED: 16/16 cases, 2 binding(s) |
| Deliberate breakage | In harness/idempotency/adapters/second.py, remove the `with self._lock:` guard around the conditional write in claim() (replacing it with an unlocked read that widens the race window) and change nothing else (the harness README's breakage); restore with git checkout -- harness/idempotency/adapters/second.py. |
| Expected failure | Measured by tools/measure.py at 16d354c: exit 1; last lines:   File "<stdin>", line 9, in <module> \| AssertionError: anchor block not found; second.py changed shape |
| Status | measured |
| Evidence | `F-b3-16`, `F-b1-04` "key on the wire, no lease" |

## Folded skills

Each was a skill of its own before STATUS row 71; its full content, with every citation, is rendered under `references/`.

| Was | Purpose | Read |
|---|---|---|
| `cap-idempotency-implement` | Turn the contract in cap-idempotency into something that runs here: one claim call, two adapters behind it whose execution models differ, and every externally-triggered entry and recorded step boundary going through it. | `references/cap-idempotency-implement.md` |
| `xc-idempotency-lease` | Fix the idempotency guarantee as a placement: one keyed lease, derived by the platform and acquired before execution begins at every way in, carrying an owner and an expiry, so a replay attaches to the one execution instead of starting a second. | `references/xc-idempotency-lease.md` |
| `xc-idempotency-lease-implement` | Turn the placement xc-idempotency-lease fixes into something that runs here: two lease providers behind one acquisition point, each publishing its key-derivation rule, migrated in without a window in which a repeat can execute twice. | `references/xc-idempotency-lease-implement.md` |

## Composes with

Builds on: `agentic-stack`, `build-evidence`, `build-skill-authoring`, `cap-errors`, `cap-state-persistence`

Used by: `cap-durable-execution`, `cap-human-interaction`, `seam-dispatch`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does the lease live in the Ledger, which the core already names as the deduplication authority, or in any store with a conditional write? | Measure whether a claim served from the persistence interface can meet the P15 race criterion without the Ledger being on the write path, and count how many components would have to import the Ledger if the answer were the Ledger. | Any store with a conditional write, per docs/decomposition.md's note that the Ledger is one implementation of the lease store rather than the interface. The Ledger stays the authority for what has been done; the lease is what decides who may do it. cap-state-persistence states F-b2-06 under this quote for the record store. | `F-b2-06`, `F-b1-04` "append-only across runs; the deduplication authority" |
| What retention window does this platform declare at its entry boundaries? | Measure the longest interval over which a producer in the current system can redeliver the same externally-triggered request, and the storage cost of holding claims for that interval. | Proposed: 24 hours at entry boundaries, matching the shorter published window, and the run's own retention for claims taken at step boundaries. Reversible by editing one declared field. | `X-cap-idempotency-008` "after 24 hours to balance deduplication coverage with storage costs" |
| When the one execution ends in a typed failure, does the key stay sealed so a replay returns that same failure, or is it released so a retry may succeed? | Across recorded failures, count how many were retried under the same key and how many of those retries would have succeeded; the retryable member of the failure already carries the platform's own answer per type. | Proposed: release the claim when the failure is retryable and seal it when it is not, so a caller cannot retry past a deterministic refusal by re-sending, and cannot be locked out by a transient one. | `F-b4-07` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-idempotency 2831cb4f, 2026-09-03 |
