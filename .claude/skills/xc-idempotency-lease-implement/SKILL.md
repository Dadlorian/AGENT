---
name: xc-idempotency-lease-implement
description: How to make the idempotency lease real on this stack: today's provider, which carries the key on the envelope and into the append-only chained store without ever claiming it, a second provider that takes a keyed compare-and-set with a store-evaluated expiry, the key-derivation rule each one publishes, how to migrate from one to both without a window in which two copies can both execute, where the lease attaches to correlation, identity, provenance and typed failures, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that stops a repeat, when a key is recorded but nothing was claimed, when a duplicate lands while the first copy is still running, when a crashed owner has left a key held, or when deciding what the second provider should be.
---

# xc-idempotency-lease-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the placement xc-idempotency-lease fixes into something that runs here: two lease providers behind one acquisition point, each publishing its key-derivation rule, migrated in without a window in which a repeat can execute twice. | sourced | `F-b4-08`, `F-b3-16` "key on the wire, no lease" |

## Entities

| Entity |
|---|
| `E-concern-idempotency` |
| `E-capability-idempotency` |
| `E-adapter-key-on-the-wire` |
| `E-adapter-no-lease` |
| `E-swap-candidate-any-keyed-lease-store` |
| `E-capability-state-persistence` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this pair (proposed instance of the shape build-adapter-pair defines)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:idempotency:pair-axes:0.1",
  "title": "LeasePairAxes",
  "description": "Proposed. The three axes on which the two lease providers differ, stated as properties rather than as product names. measured stays false until the swap has been executed and recorded.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "unit_of_conditionality",
        "today_value": "a position in one ordered append-only log: the append is conditional on the expected head",
        "second_value": "one key: the write is conditional on that key alone and keys do not contend with each other",
        "measured": false
      },
      {
        "axis": "who_evaluates_expiry",
        "today_value": "a reader, comparing a timestamp in a record it has just read",
        "second_value": "the store itself, which stops answering for the key when its own expiry elapses",
        "measured": false
      },
      {
        "axis": "processes_required_for_progress",
        "today_value": "the single writer that owns the log must be up for any key to be claimed",
        "second_value": "any process can claim its own key with no writer in the middle",
        "measured": false
      }
    ]
  ]
}
```

**key-derivation rule, published per entry adapter (proposed; the fold-in this skill owns at code level)** (proposed; sources: `X-entry-composition-047`, `X-entry-composition-002`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:idempotency:derivation-rule:0.1",
  "title": "KeyDerivationRule",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. One record per entry adapter per provider, published beside the adapter and read by the acquisition point. It is data because two providers must derive identically or the swap changes which arrivals are duplicates.",
  "required": [
    "entry_adapter",
    "protocol_carries_key",
    "derivation",
    "scope_expression",
    "rule_version"
  ],
  "properties": {
    "entry_adapter": {
      "type": "string"
    },
    "protocol_carries_key": {
      "type": "boolean"
    },
    "derivation": {
      "enum": [
        "caller_supplied",
        "payload_fingerprint"
      ]
    },
    "fingerprint_fields": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "description": "JSON pointers into the envelope, in declared order. Required when derivation is payload_fingerprint."
    },
    "scope_expression": {
      "type": "string",
      "description": "How the scope the key must be unique within is computed for this adapter."
    },
    "rule_version": {
      "type": "integer",
      "minimum": 1,
      "description": "Bumped when the selection changes; the bump starts a new key namespace so yesterday's action cannot look fresh."
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "derivation": {
            "const": "payload_fingerprint"
          }
        },
        "required": [
          "derivation"
        ]
      },
      "then": {
        "required": [
          "fingerprint_fields"
        ]
      }
    }
  ]
}
```

**lease-conformance report (proposed; the fields the definition of done asserts on, written per provider and once across providers)** (proposed; sources: `F-a7-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:idempotency:conformance-report:0.1",
  "title": "LeaseConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A green run names what it actually checked rather than only its exit code, and names the provider it observed rather than the one it selected.",
  "required": [
    "provider",
    "keys_checked",
    "unleased_actions",
    "owners_missing",
    "expiries_missing",
    "duplicate_executions",
    "attached_in_flight",
    "reclaimed",
    "ways_in_covered",
    "provider_observed"
  ],
  "properties": {
    "provider": {
      "type": "string",
      "description": "The entity id of the lease provider selected by configuration."
    },
    "keys_checked": {
      "type": "integer",
      "minimum": 0
    },
    "unleased_actions": {
      "type": "integer",
      "minimum": 0
    },
    "owners_missing": {
      "type": "integer",
      "minimum": 0
    },
    "expiries_missing": {
      "type": "integer",
      "minimum": 0
    },
    "duplicate_executions": {
      "type": "integer",
      "minimum": 0
    },
    "attached_in_flight": {
      "type": "integer",
      "minimum": 0
    },
    "reclaimed": {
      "type": "integer",
      "minimum": 0
    },
    "stale_token_seals_refused": {
      "type": "integer",
      "minimum": 0
    },
    "ways_in_covered": {
      "type": "integer",
      "minimum": 0
    },
    "provider_observed": {
      "type": "string",
      "description": "Read from the granted lease record, never from the binding that selected the provider."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two providers differ on three of build-adapter-pair's axes - unit_of_conditionality, who_evaluates_expiry and processes_required_for_progress - recorded in the shape above. Another append-only file of the same shape would agree with today's on all three, so swapping to it would test a file format and not the guarantee. | proposed | `F-b1-04` "the second exists to prove the first is not load-bearing" |
| agentic-stack states design rule 1 (F-b1-02). Its consequence here: which provider granted a lease is configuration, and no core code, no workflow and no caller branches on it. The provider appears in the conformance report, never in a field a caller can read and route on. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| agentic-stack states that what runs is substrate (F-part-c-11). Its consequence here: the key already carried on the envelope is not replaced, it becomes the input the derivation rule reads, and the acquisition point is added in front of execution rather than the wire format being changed. | sourced | `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| xc-idempotency-lease fixes the placement and cap-idempotency the claim it calls (F-b3-16). What this adds on this stack: what runs today records the key and takes nothing before execution, so the work is to add an acquisition point, not a field, and the concurrent half of the criterion is the half today's provider is expected to fail. | sourced | `F-b3-16`, `F-b4-08` "key on the wire, no lease" |
| Proposed: both providers derive the key from the same published rule record, so the swap changes where the claim is held and never which arrivals are duplicates. A provider that derives its own keys would make the pair incomparable, and the conformance report would be comparing two different corpora. | proposed | `X-entry-composition-047`, `F-b1-04` |
| Proposed: the migration never has a window in which two copies of one action can both execute. The lease is acquired in shadow first, recording what it would have refused while nothing is gated on it, and only then does it gate - first at entry, then at the later boundaries where an action can re-enter. | proposed | `F-b3-16`, `T-t2-03` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's provider as a thin binding onto the append-only chained store the platform already writes: acquire appends a lease record conditional on the expected head, seal appends a second record referencing it, and expiry is a field a reader compares against its own clock. | agentic-stack and build-evidence-record already state the chained-store property (F-a5-03); its consequence here is that a later edit to a lease record is detectable, so this starts the pair from something that runs rather than from an intention. It also makes the gap explicit: everything here serialises behind the one writer that owns the log. | sourced | `F-a5-03`, `F-b3-16` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| 2 | Proposed: build the second provider as a keyed compare-and-set with an expiry the store evaluates itself, one key per lease, with the fencing token as the value the set increments. | Proposed: this breaks the assumption that acquisition is an append to one ordered log. Keys stop contending with each other, a claim no longer needs the log's writer to be up, and a stuck key clears without a reader having to notice that it should have. | proposed | `F-b3-16`, `X-xc-idempotency-lease-002` |
| 3 | Publish one key-derivation rule record per entry adapter in the shape above, read it from the acquisition point rather than from code in the adapter, and have both providers read the identical record. | xc-idempotency-lease states the derivation rule (X-entry-composition-047, X-entry-composition-002): only some protocols carry a key, so the fallback has to be a fingerprint over fields selected in advance; putting the selection in a versioned record instead of in adapter code is what lets a change start a new key namespace instead of silently re-deriving old keys. It is also what keeps the two providers comparable. | sourced | `X-entry-composition-047`, `X-entry-composition-002` "An idempotency fingerprint MAY be used in conjunction with an idempotency key" |
| 4 | Implement the attach path on both providers: a duplicate arriving against a held lease with the same payload digest waits on the first execution and receives its result, rather than being refused or starting a second run. | xc-idempotency-lease states the attach rule (X-cross-structure-042, X-entry-composition-027); at code level it is the half of the behaviour that a key without a claim cannot have at all, and it is what makes a retry storm cost one execution. Implementing it on both providers is also what stops the conformance suite from being shaped around whichever one was built first. | sourced | `X-cross-structure-042`, `X-entry-composition-027` "duplicate requests will return the same result as the original request" |
| 5 | Migrate in three steps with no gap: acquire in shadow while nothing is gated and record the would-be refusals; then gate at entry; then gate at the later boundaries where an action re-enters, a resumed step, a delivered approval, a re-fired recurrence. Keep the key on the wire throughout. | xc-idempotency-lease states that the claim is applied across the whole structure (T-t2-03); the shadow step is the only one in which a disagreement about that is cheap, and it is what shows the derivation rule produces the same key for two arrivals that are genuinely the same action. Gating everywhere in one move would put an untested claim in front of every side effect the platform has. | sourced | `F-part-c-11`, `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure" |
| 6 | Wire the cross-cutting attachments on both providers: stamp the run and correlation identifiers as explicit attributes on every acquire, seal and reclaim; carry the entering actor and its delegation chain onto the lease record; append every one of those events through the persistence interface; and return the registered conflict type rather than a message. | agentic-stack states that correlation must ride on an explicit attribute set at dispatch (F-a7-02) because parentage did not survive the agent boundary, and a lease event whose run cannot be identified cannot be attributed to the action it bounded. Every action naming an actor is the identity contract, and an unattributable reclaim is a lease nobody can be asked about. | sourced | `F-a7-02`, `F-b4-03` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 7 | Read the provider from the granted lease record that actually came back and put that value in the conformance report, never the binding that selected it. | agentic-stack and build-evidence-record state the silently-discarded-configuration finding (F-a7-04): values written in the documented place validated, reviewed correctly and had no runtime effect. A lease believed to be held because a provider was configured is that same failure with duplicate side effects behind it. | sourced | `F-a7-04` "had no runtime effect" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Test with the clock, not only with concurrency: kill the owner mid-execution and assert the key becomes claimable once its expiry passes, and that the returning owner's seal is refused. A suite that only fires copies in parallel never exercises the reclaim path, which is the path the breakage below attacks. | sourced | `X-xc-idempotency-lease-005` "A handler can update the database successfully but fail before acknowledgment" |
| Expect the two providers to disagree under contention in the shadow step and treat the difference as the finding rather than as noise. xc-idempotency-lease states that acquisition must be one atomic act (X-xc-idempotency-lease-002); an ordered log serialises claims and a per-key set does not, so the order in which two near-simultaneous copies are granted may differ; what must not differ is which of them executed. | sourced | `F-b1-04`, `X-xc-idempotency-lease-002` "Race conditions between the idempotency check and the mutation must be atomic" |
| agentic-stack already states the structurally-green-gate finding (F-a7-03), and xc-idempotency-lease draws the consequence for a lease corpus. What this adds at code level: report the counts per provider, because one corpus replayed through two providers can leave one of them with nothing to attach and still exit green. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: do not let the lease record become the result store, which is the code-level face of the two-clocks practice xc-idempotency-lease states (X-cap-idempotency-008). Seal writes a reference and the result stays where results live, or the provider that was chosen for a keyed compare-and-set inherits a size limit and a retention policy it was never picked for. | proposed | `X-cap-idempotency-008` "to balance deduplication coverage with storage costs" |
| Keep the acquisition on the same path a live action takes. xc-idempotency-lease states this for the guarantee (F-a6-04) and the inventory of what runs today already records a concern whose checks exist and sit outside the path that enforces them, and a lease suite that replays a stored corpus can pass while the live dispatcher claims nothing at all. | sourced | `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-key-on-the-wire` | today | The key rides on the entry envelope and is written into the append-only chained store the platform already keeps, so derive_key and an after-the-fact lookup are served and nothing else is. Built out as a lease provider it serves acquire as an append conditional on the expected head, renew and seal as further appends, and reclaim as a reader comparing an expiry field against its own clock. | Proposed: as it stands it claims nothing before execution, so it cannot answer a duplicate while the first copy is still running and cannot stop two concurrent copies from both executing. Built out, it still cannot let a claim proceed while the log's single writer is down, cannot stop keys from contending with each other, and cannot expire a lease without a reader noticing that it should have. | Select the provider by configuration only, with no code edit between runs, and replay the identical corpus through both from the same published key-derivation rule records. xc-idempotency-lease owns the placement this pair realises and cap-idempotency the claim it calls; this row records only the roles PASS.md B3 fixes and the axes the pair differs on. | claimed | `F-b3-16`, `F-a5-03` "key on the wire, no lease" |
| `E-swap-candidate-any-keyed-lease-store` | second | The same operations served by a keyed compare-and-set with a store-evaluated expiry: acquire is a set that succeeds only if the key is absent or reclaimable, renew moves the expiry the store itself enforces, seal writes the result reference under the current fencing token, and reclaim is the store ceasing to answer for an elapsed key. One key per lease, no ordered log in the middle. | Proposed: cannot make progress when its own store is unreachable, where today's provider needs nothing beyond the log the platform already writes; cannot give a total order over claims, so it cannot answer which of two near-simultaneous copies arrived first; and cannot by itself make an edit to a sealed lease detectable, so the seal is mirrored into the chained store for that. | Proposed: the axes that differ are unit_of_conditionality (a position in one ordered log versus one key), who_evaluates_expiry (a reader comparing a timestamp versus the store itself) and processes_required_for_progress (the log's single writer must be up versus any process claiming its own key). Run the identical suite against each and require the merged report to show adapters_run at least 2. agentic-stack and build-adapter-pair already state design rule 3 (F-b1-04); what is new here is the axes, not the rule. | claimed | `F-b3-16`, `F-b1-04` "any keyed lease store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.4 row X7, made precise and run over the provider pair above: `python3 tools/conformance/lease_placement.py --provider today --provider second --entries examples/end-to-end/entries --corpus out/actions.jsonl --concurrency 100 --kill-owner-at 0.5 --report out/lease.json` (proposed tool, built with the first claiming provider), the provider selected by configuration with no code edit between runs. Per provider it asserts that every externally-triggered action has a lease record with a non-null owner and a non-null expires_at, that no two executions share a key within a scope, that a duplicate answered while the first execution was still running was attached rather than executed, that a lease whose owner was killed mid-execution is reclaimable once its expiry has passed and that the returning owner's seal is refused on a stale fencing token, and that `provider_observed` was read from the granted lease record rather than from the binding. It asserts per provider `keys_checked > 0`, `unleased_actions == 0`, `owners_missing == 0`, `expiries_missing == 0`, `duplicate_executions == 0`, `attached_in_flight >= 1`, `reclaimed >= 1`, `stale_token_seals_refused >= 1` and `ways_in_covered == 3`, and across providers `adapters_run >= 2`. |
| Expected | exit 0 with one line per provider of the form `provider=<entity> keys_checked=<n> unleased_actions=0 owners_missing=0 expiries_missing=0 duplicate_executions=0 attached_in_flight=<k> reclaimed=<r> stale_token_seals_refused=<s> ways_in_covered=3 provider_observed=<entity>`, followed by `adapters_run=2`, with `k`, `r` and `s` greater than zero on both providers so each assertion had something to assert on. |
| Deliberate breakage | Let the lease expiry be unbounded on one of the two providers: set `expires_at` to null at acquisition there, leave the owner, the fencing token and the other provider untouched, and re-run the same command. |
| Expected failure | exit non-zero for that provider with `expiries_missing` equal to the number of leases it took, `reclaimed == 0` and `stale_token_seals_refused == 0`: the owner killed mid-execution never releases its key, so the reclaimability assertion fails and that key is held forever, while the other provider still passes and `adapters_run` still reports 2 - a run that fails both, or neither, has not tested the swap. Claimed: nothing claims a key before execution today and this tool is not written, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b3-16` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `xc-idempotency-lease`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Idempotency's recorded row names an adapter today that claims nothing, so the pair here is one entity built out into a provider and one swap candidate. Should the built-out provider get an entity of its own? | 1-3-1 applied (TARGET T5) the same way xc-idempotency-lease records its own entity gap (T-t5-02): (a) add an entity for the chained-store lease provider, which needs a knowledge-base rebuild and would invalidate the provenance heads of every skill already written; (b) record it against the recorded adapter entity and say in the row what was built out, which is what this skill does; (c) leave the first provider unnamed, which would leave the pair with one member. Recommendation followed: (b). The question closes when a ceremony rebuilds the knowledge base and the entity exists. | Proposed: keep the pair on the recorded entities and state in the adapter row which part is what runs today and which part is the build-out, so a reader is not told that a lease exists today. | `F-b3-16`, `T-t5-02` "When a problem comes up, use 1-3-1" |
| Does the second provider's seal need to be mirrored into the chained store, and if so does the mirror sit on the acquisition path or behind it? | build-evidence-record states the chained-store property this mirror is for (F-a5-03). Measure how often a seal succeeds in the keyed store and the mirror fails, and what a duplicate arriving in that gap is answered. If the gap is observable at all, the mirror belongs on the path and the seal is not acknowledged until both have landed. | Proposed: mirror on the path, because a sealed result nobody can prove was not edited afterwards is weaker than what today's provider already gives, and a swap must not lose a property. | `F-a5-03` "a manual edit between runs is detectable" |
| How long a lease should each entry adapter take by default, given that the duration bounds how long a crashed owner blocks its key and how long a live one must keep renewing? | xc-idempotency-lease states the durability requirement behind this (X-xc-idempotency-lease-001). Measure the distribution of execution times per entry adapter and set the duration above the tail, then measure how many renewals a normal execution issues. A duration so short that healthy owners lose leases and one so long that a crash blocks a key for an hour are both visible in that pair of numbers. | Proposed: a duration per entry adapter rather than one global value, renewed from the owner, with the value carried in the derivation rule record so it changes as data. No number is proposed here because none has been measured on this stack. | `X-xc-idempotency-lease-001` "Storage for deduplication checks needs to be durable" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-idempotency-lease 2831cb4f, 2026-09-03 |
