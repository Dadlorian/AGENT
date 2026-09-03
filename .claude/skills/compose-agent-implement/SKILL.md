---
name: compose-agent-implement
description: How compose-agent is actually wired on this repository's substrate: one microVM per agent running the agent-runtime adapter over the Agent Client Protocol as today's admission, a remote agent protocol server as the second, the three ways today's admission is not yet conformant to compose-agent's contract, where the tool-list, capability-set, criterion-absence and identity-chain checks attach to a unit, and a definition of done whose breakage is in the tool-registration binding rather than in the contract. Load it when writing or reviewing the code that admits an agent unit, when wiring a profile registry to the microVM launcher, when deciding what the second adapter should be, when a delegation call has nowhere to record an actor because no identity field exists yet, or when asking why this repository's own agent admission cannot yet prove the tool list it bound.
---

# compose-agent-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Proposed: build compose-agent's contract on the one-microVM-per-agent substrate that already runs, and stage the migration from a substrate whose tool endpoint has zero tools registered and whose identity field does not exist. | proposed | `F-a6-03`, `F-a6-05`, `F-b1-04` |

## Entities

| Entity |
|---|
| `E-capability-agent-runtime` |
| `E-capability-tool-access` |
| `E-capability-isolation` |
| `E-capability-capability-packaging` |
| `E-not-running-mcp-endpoint` |
| `E-not-running-identity` |
| `E-rule-b1-3` |

## Contract

### Shapes (JSON Schema 2020-12)

**profile-registry-binding (proposed shape; the configuration that selects which registry resolves declare_agent, and the only place either adapter is named)** (proposed; sources: `T-t2-02`, `F-b1-02`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:compose:agent:registry-binding:0.1",
  "title": "AgentRegistryBinding",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A profile declaration carries none of this: swapping the registry is a configuration edit, so the conformance suite runs the same profile twice by changing one value.",
  "required": [
    "registry",
    "tool_registration",
    "identity_hop"
  ],
  "properties": {
    "registry": {
      "type": "string",
      "description": "The adapter id from this skill's Adapters table."
    },
    "tool_registration": {
      "enum": [
        "endpoint_call",
        "none_yet"
      ],
      "description": "endpoint_call: admit_agent registers the declared tools[] with the tool-access endpoint before starting the unit. none_yet: the migration stage this repository is in today - the endpoint has zero tools registered (F-a6-03), so the tool-list-exactness assertion cannot yet be tested for real."
    },
    "identity_hop": {
      "enum": [
        "threaded",
        "absent"
      ],
      "description": "threaded: delegate appends a chain hop to a real actor field. absent: today's migration stage - no identity field exists anywhere in the system (F-a6-05), so a delegation call has nowhere to record its actor."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| compose-agent already states that a composition introduces no new interface and reaches isolation, tools, packaging and the runtime turn through capability interfaces only. What this skill adds: the profile declaration is byte-identical on both registries and names neither, exactly as agentic-stack's rule 1 test requires (F-b1-02) - if a profile had to change to move registries, the boundary would be drawn wrong. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| Today's admission is non-conformant to compose-agent's contract on exactly three counts, and each is a migration stage rather than an excuse. First, there is no profile registry: the substrate starts one microVM per agent but nothing resolves a name to good_at, not_for, model_class, tools, cost_class or max_concurrency before it does. Second, the tool-access endpoint is live and authenticated but has zero tools registered, so admit_agent's tool-list-exactness assertion is vacuously true today only because both sides are empty. Third, no identity field exists anywhere in the system, so delegate's chain-hop requirement and xc-identity-delegation's actor requirement are both unimplementable until an actor field is threaded from entry through to admission. | sourced | `F-a6-03`, `F-a6-05` "zero tools registered" |
| One unit per isolation admission, which compose-agent already states as its containment invariant, is already true of the substrate: one microVM starts per agent, startable without sudo. What this skill adds is that the migration needs no new isolation work to satisfy that row - it needs the registry, the tool registration and the identity field wired in front of an isolation boundary that already exists. | sourced | `F-a2-02` "One microVM per agent, startable without sudo" |
| agentic-stack already states the trace-context finding: the runtime that serves cap-agent-runtime's turn today mints its own root trace and ignores an injected trace-context header (F-a7-02). What compose-agent-implement adds: an agent unit's correlation attribute has to be re-stamped at admission, not inherited from whatever the microVM's own process tree carries, or a depth-3 delegation tree produces unrelated root traces exactly as A7 finding 1 already describes. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Bind compose-agent's contract to the isolation boundary that already runs: one unit per microVM, admitted exactly as the substrate admits one microVM per agent today. Add nothing new here - this row of the migration is already satisfied. | F-a2-02 already states one microVM per agent; duplicating that mechanism to satisfy compose-agent's containment invariant would be building a second isolation boundary this repository does not need. | sourced | `F-a2-02` "One microVM per agent, startable without sudo" |
| 2 | Proposed: build the profile registry first. Nothing today resolves a name to good_at, not_for, model_class, tools, cost_class and max_concurrency before a microVM starts. Add a file shaped like examples/end-to-end/agents.json as declare_agent's backing store, and have admit_agent read it before requesting a unit. | This is the first of the three non-conformance gaps this skill's invariants name, and it blocks every other assertion: there is nothing to check a bound tool list or a loaded capability set against without a declared list to compare to first. | proposed | `T-t6-05` |
| 3 | Close the tool-registration gap second: register each admitted unit's declared tools[] with the tool-access endpoint before the unit starts, rather than leaving the endpoint at zero tools registered while the admission plan claims a list. Only once this is wired can the tool-list-exactness assertion fail on a real mismatch instead of passing vacuously. | F-a6-03 records the endpoint as live and authenticated but with zero tools registered; a suite run against that state cannot fail the assertion it exists to check, which is the same well-formedness trap agentic-stack already names. | sourced | `F-a6-03` "zero tools registered" |
| 4 | Close the identity gap third: thread an actor field from the entry envelope through to admission, so a delegate call has a chain to append its hop to. Until this lands, record every delegation as unimplementable rather than silently allowing an actor-less chain hop. | F-a6-05 records that no identity field exists anywhere in the system today; xc-identity-delegation's rule that every action names an actor cannot be honoured by a system with no field to name one in. | sourced | `F-a6-05` "No identity field anywhere in the system" |
| 5 | Proposed: build the second registry on a remote agent protocol server. A profile becomes a signed, network-addressable entry, and admitting a unit means a token exchange against that server instead of a local file read. Record the axis the pair differs on - network round trip and no shared identity authority - in the registry-binding shape. | build-adapter-pair requires the second adapter to break a different assumption than the first; an in-process file and a network-addressed server disagree on exactly the assumption a caller might otherwise bake in - that resolving a profile never fails for a reason the first adapter cannot have. | proposed | `F-b1-04` |
| 6 | Write one conformance suite against compose-agent's own definition of done - criterion_leaks, tool_mismatches, undeclared_skills - and parameterise it over both registries so the same 20 profiles run against each with only the registry-binding's `registry` field changed. | build-definition-of-done already states that a criterion nothing can fail is not a criterion; a suite that only ever runs against the in-process registry has never shown the remote one can pass or fail the same checks. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion." |
| 7 | Wire the cross-cutting concerns to the unit, not to the process: re-stamp the correlation attribute at admission rather than trusting the microVM's own process tree, attach the budget slice when the plan resolves, and record the identity chain hop once step 4's field exists. | agentic-stack already states the trace-context finding (F-a7-02): the runtime that serves this composition's turn mints its own root trace and ignores an injected trace-context header, so correlation has to be an explicit attribute this skill sets, not one it inherits. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the trace-context finding (F-a7-02). What it adds here: do not trust cancel or completion timing measured from inside the microVM's own process tree either, since the same boundary that loses trace parentage is the boundary a naive timer would cross. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| agentic-stack already states the well-formedness finding (F-a7-03). What it adds here: a conformance run against an endpoint with zero tools registered cannot fail the tool-mismatch check no matter how the binding is written, so treat a green run recorded before step 3 lands as evidence of nothing. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: measure max_concurrency against how many microVMs the host can actually keep live at once before publishing a profile's declared ceiling, rather than assuming the number the profile author picked is honoured underneath. | proposed | `F-a2-02` |
| Proposed: stage the three migration gaps in the order this skill's instructions give - registry, then tool registration, then identity - because the second and third assertions cannot be tested for real until the first exists to declare something for them to check against. | proposed | `F-a6-03`, `F-a6-05` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-firecracker-goose-unit` | today | admit_agent and invoke_turn served by one Firecracker microVM per agent (F-a2-02), running goose over the Agent Client Protocol as JSON-RPC on stdio (F-a3-01, F-a3-02, F-a3-03), with no guest network by default and a dummy in-guest credential. declare_agent has no backing registry yet and the tool-access endpoint this unit would bind to is live and authenticated with zero tools registered (F-a6-03); no identity field exists to carry a delegation chain (F-a6-05). Proposed entity id: the knowledge base has no capability row for agent composition, so there is no E- record for the assembled unit and this id is ours, minted the way compose-operators already minted its own today-adapter id for the same reason. | Cannot yet prove the tool-list-exactness or undeclared-skill assertions for real, since both the registry and the tool registration this skill's migration stages exist to add are absent; cannot record a delegation chain, since no identity field exists to hold one; and cannot survive the loss of the host, since nothing about a unit's admission is checkpointed anywhere an executor could resume from. | Point declare_agent at the remote registry adapter instead of the (currently absent) in-process file, admit through the same isolation boundary either way, and run the conformance suite with only the registry-binding's `registry` field changed. agentic-stack states design rule 3 - every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing - and this pair is that test applied once the registry exists to test at all. | claimed | `F-a2-02`, `F-a6-03` "One microVM per agent, startable without sudo via polkit" |
| `E-swap-candidate-remote-agent-protocol-server` | second | the same declare_agent and admit_agent served by a remote agent protocol server: a profile is a signed, network-addressable registry entry, and admitting a unit means authenticating to that server over the network instead of instantiating a process in the same container. Proposed entity id, carried over rather than re-minted: compose-agent's own ideal facet already mints this id for the same shape, and the knowledge base still has no capability row for agent composition to record it against instead. | Cannot resolve a profile without a network round trip, so declare_agent fails for reasons the in-process file never can; cannot assume its identity chain and the composer's are issued by the same authority, so its hop must be a token exchange; and inherits every migration gap the in-process adapter has today, since neither adapter yet has a registry, a tool registration or an identity field to test against. | Publish one profile to both the in-process file and a conformant remote registry once both exist, run declare_agent against each for the same task, and assert adapters_run >= 2 with identical required admission fields even though the network round trip and the identity hop differ. | claimed | `F-b1-04` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing." |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/linked/test.sh && ADAPTER_CONTAINMENT=second ADAPTER_GATEWAY=second ADAPTER_TRACE=second ADAPTER_WORKFLOW=second python3 harness/linked/conformance.py --report out/linked-swap.json |
| Expected | Measured by tools/measure.py at eaca633: exit 0; last lines: counters: {"doors_checked": 4, "manifests_distinct": 1, "subjects_distinct": 1, "typed_refusals": 4, "replay_noops": 4, "traces_reassembled": 4} \| verdict pass: 23 of 23 checks pass |
| Deliberate breakage | In harness/linked/linked.py, break the replay check submit() makes against the ledger so a prior completion is never recognised: sed -i 's/prior = self.ledger.completed(env.idempotency_key)/prior = None/' harness/linked/linked.py. A replay of any door then re-runs the whole unit (re-dispatches the agent turn, re-calls the gateway, writes new durable records) instead of returning the stored result with zero new spend. Restore with git checkout -- harness/linked/linked.py. |
| Expected failure | Measured by tools/measure.py at eaca633: exit 1; last lines:   FAIL the same suite passes again once the door is restored (expected 0, got 1) \| passed 20, failed 12 |
| Status | measured |
| Evidence | `F-a6-03` "zero tools registered" |

## Composes with

Builds on: `compose-agent`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should the profile registry this skill's step 2 adds live as a file in this repository, or should it be the first real consumer of cap-capability-registry once that capability is built, given cap-capability-registry is not in this skill's builds_on? | cap-capability-registry's own definition of done running against a profile resolved by name and version constraint, compared against the file-based registry's resolution for the same profile. | Start with a file, shaped like examples/end-to-end/agents.json, and revisit once cap-capability-registry has an adapter that runs. | `F-b1-04` |
| Which entity should this skill's today adapter be recorded against, given the knowledge base has no capability row for an assembled agent-composition unit? | 1-3-1 applied (TARGET T5): the three options were to record it against one of the four component capabilities alone (isolation, tool access, packaging or agent runtime), to mint a new entity for the assembled unit, or to leave the adapters[] pair absent. Recording against one component alone would misattribute a four-capability composition to a single B3 row; leaving the pair absent would leave the round's instruction to describe the real substrate unaddressed. Recommendation taken: mint the entity, the way compose-agent's own ideal facet and compose-operators both already did for the same reason. | The today adapter's entity id is recorded as proposed and pending a knowledge-base entity if PASS.md ever grows a composition-layer row. | `T-t5-02` |
| Does closing the identity gap in step 4 belong to this skill, or to a future xc-identity-delegation-implement stage that this skill should instead depend on? | A manifest revision adding xc-identity-delegation-implement to this skill's builds_on once that skill exists, or a decision that the identity field is generic enough to land once and be reused rather than staged per composition. | Stage it here as this skill's step 4, since compose-agent's own delegate operation is blocked without it and no xc-identity-delegation-implement skill exists yet to own the field. | `F-a6-05` "No identity field anywhere in the system" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation compose-agent-implement 2026-09-03 |
