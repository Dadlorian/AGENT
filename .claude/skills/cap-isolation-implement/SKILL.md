---
name: cap-isolation-implement
description: How to build the Isolation capability on this stack: today's adapter over the per-agent microVM service that already runs, a second adapter that grants capabilities instead of a machine, how the two existing unit shapes become two profiles behind one declaration, where budget, policy, identity, telemetry and provenance attach around a unit rather than inside it, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that admits, runs, terminates or inspects a contained unit, when wiring a containment technology behind the declaration, when a resource profile has to be resolved or refused, when choosing what the second containment technology should be, or when a containment check passes under one adapter and cannot even be expressed under the other.
---

# cap-isolation-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-isolation into something that runs here: two containment technologies behind one declaration, the unit shapes that exist today brought in front of it as profiles rather than as separate interfaces, and every ceiling attached around the unit instead of inside it. | sourced | `F-a2-02`, `F-b3-02`, `E-capability-isolation` "One microVM per agent" |

## Entities

| Entity |
|---|
| `E-capability-isolation` |
| `E-standard-oci-runtime-spec` |
| `E-swap-candidate-hosted-sandbox-services` |

## Contract

### Shapes (JSON Schema 2020-12)

**IsolationAdapterBinding (proposed shape; what selects a containment technology, and the only place one is named)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:adapter-binding:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "profiles",
    "declared_gap"
  ],
  "description": "Proposed. Read by the isolation factory only. No core code and no caller reads this object or branches on adapter.",
  "properties": {
    "adapter": {
      "type": "string",
      "description": "Adapter entity id. Selecting a containment technology is configuration; there is no code path that chooses one."
    },
    "profiles": {
      "type": "object",
      "description": "Profile name to the envelope this adapter resolves it to. A name absent here is refused at admit, never approximated.",
      "additionalProperties": {
        "type": "object"
      }
    },
    "declared_gap": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "description": "What this adapter states it cannot do, written before the conformance run rather than discovered by it."
    },
    "containment_marker": {
      "type": "string",
      "description": "Observed by the host from the running unit at admit, and asserted against the adapter selected here, so a swap that never happened is visible."
    }
  }
}
```

**IsolationConformanceReport (proposed shape; the counters the definition of done below asserts on)** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:conformance-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapters_run",
    "per_adapter"
  ],
  "properties": {
    "adapters_run": {
      "type": "integer",
      "minimum": 2,
      "description": "Distinct containment technologies exercised from one declaration. Fewer than two means the swap was not tested."
    },
    "per_adapter": {
      "type": "array",
      "minItems": 2,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "adapter",
          "containment_marker",
          "exit_status",
          "output_digest",
          "containment",
          "declared_gap_honoured"
        ],
        "properties": {
          "adapter": {
            "type": "string"
          },
          "containment_marker": {
            "type": "string",
            "description": "Read from the running unit by the host, not from the binding record."
          },
          "exit_status": {
            "type": "integer"
          },
          "output_digest": {
            "type": "string"
          },
          "containment": {
            "$ref": "urn:agentic:cap:isolation:containment-report:0.1"
          },
          "declared_gap_honoured": {
            "type": "boolean",
            "description": "True when the adapter behaved as its declared gap says it will, including when the declared behaviour is to refuse a machine-shaped field."
          }
        }
      }
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two adapters differ on unit_of_resource_granted and on start_and_teardown_cost, in the sense build-adapter-pair defines. One grants a machine with a kernel and a root filesystem; the other grants a set of capabilities and has neither. A pair that agrees on both axes is rejected and a different second technology is found. | proposed | `F-b1-04` |
| What runs today becomes today's adapter and is not replaced; agentic-stack states this constraint (F-part-c-11), and the consequence here is that no instruction in this skill asks anyone to stop running agents in the microVM that already contains them. | sourced | `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| The substrate already produces one contained unit per agent, plus a long-lived variant with a larger runtime ceiling. These are two profiles behind one declaration, not two interfaces: the difference between them is an envelope the adapter resolves, and nothing above the boundary should be able to tell which was used. | sourced | `F-a2-02`, `F-a2-03` "Long-lived variant, larger runtime ceiling" |
| The cross-cutting guarantees attach around the unit, never inside it: the platform applies each and a caller cannot decline them, so a containment technology that offers its own budget or policy switch has offered an opt-out that must not be wired. | sourced | `F-b4-01` "The platform applies each; a caller cannot decline them" |
| The credential mode is enforceable from outside because the broker already drops model and destination overrides by name, so a unit that asks to be routed somewhere else does not get to decide the answer. This is what makes cap-isolation's broker-only credential mode (F-a3-05, F-a3-07) an enforced property rather than a convention. | sourced | `F-a3-08` "Model and destination overrides dropped by name at the broker" |
| The failure path starts red and must be built, not assumed: typed errors are recorded as absent on this stack, so the isolation-unavailable type cap-isolation requires has nowhere to land until cap-errors is implemented. An adapter that returns an untyped failure is not conformant. | sourced | `F-a6-06`, `F-b4-07` "Typed errors \| Absent" |
| Selecting the containment technology is configuration: agentic-stack states design rule 1, that the core imports interfaces and never implementations (F-b1-02); the consequence here is that no core code and no caller branches on which adapter contained a unit, and the conformance run is the only reader of the adapter identity at all. | sourced | `F-b1-02` "The core imports interfaces, never implementations." |
| Apply build-evidence-record: every statement here about how a containment technology behaves stays claimed until the conformance run and its evidence record exist, naming the code version and the tree hash under test; no adapter here has been run in this repository; proposed pointer, see that skill. | proposed | `F-a5-04`, `F-part-c-08` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build today's adapter as a thin translation over the per-agent microVM service that already starts one contained unit per agent: map the declaration's profile names onto the existing unit shapes, and add nothing to the declaration to accommodate them. | agentic-stack states that Part A is substrate and what runs is not to be replaced (F-part-c-11), and the substrate here is the service that already starts one contained unit per agent, startable without sudo (F-a2-02). | sourced | `F-a2-02`, `F-part-c-11` "One microVM per agent, startable without sudo" |
| 2 | Resolve profile names inside the adapter and refuse at admit what an adapter cannot resolve, returning the typed problem rather than approximating the nearest envelope that fits. | cap-isolation makes profile resolution the adapter's job and refuses silent downgrade (F-a6-06); a refusal at admission, before a unit exists, is a typed answer never parsed from prose (F-b4-07), and once the unit is running the weaker containment is already in force and nothing in the result records it. | sourced | `F-b4-07`, `F-a6-06` "Never parsed from prose" |
| 3 | Build the second adapter from an execution model that grants capabilities rather than a machine, reached through a shim that speaks the same runtime standard, and let it refuse machine-shaped fields instead of emulating them. | build-adapter-pair carries the rule that swappability is a tested property, not an intention (F-b1-04): emulating a kernel to make both adapters look alike would hide exactly the fields that are adapter detail, which is the failure the pair exists to expose. | sourced | `F-b1-04`, `F-b3-02` "Swappability is a tested property, not an intention." |
| 4 | Record the pair's differs_in_execution_model naming unit_of_resource_granted and start_and_teardown_cost, and write the second adapter's gaps into its binding as declared_gap before the conformance run rather than after it. | build-adapter-pair carries the swap test (F-meta-04): if Part B cannot swap an implementation without touching the core, the boundary is drawn wrong, and widening the declaration until both technologies satisfy every field is the quiet form of that failure. | sourced | `F-meta-04`, `F-b1-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| 5 | Enforce both ceilings outside the unit: a monotonic wall-clock timer and the spend reservation each end the unit through the boundary's own destroy path, and neither is ever handed to the unit to enforce for itself. | cap-isolation states that the boundary must be able to destroy a unit on request, because that is what makes a ceiling above it enforceable (F-b4-02), and a ceiling counts only where it is verified to terminate spend rather than merely record it (F-a4-07); a unit asked to enforce its own can decline to. | sourced | `F-b4-02`, `F-a4-07` "verified to terminate spend rather than merely record it" |
| 6 | Evaluate policy before admission and give the unit an owning identity at admission, so a refusal happens before a unit exists and every contained action has an actor. | Refusal is deterministic and happens before execution, not after spend, and a policy check placed after admission has already paid for the machine it exists to prevent; and every action names an actor, including the delegated agent actor a contained unit acts as. | sourced | `F-b4-04`, `F-b4-03` "Refusal is deterministic and happens before execution, not after spend" |
| 7 | Set the correlation attribute explicitly when the unit is admitted, on both adapters, and assert in the conformance run that it survives each of them. | agentic-stack records the trace-context finding (F-a7-02): correlation must ride on an explicit resource attribute set at dispatch, and a contained unit is a process boundary of exactly the kind that lost the context (F-b4-06). | sourced | `F-a7-02`, `F-b4-06` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 8 | Assert which adapter actually contained the unit by reading a marker the host observes from the running unit, never the adapter name written in the binding, and assert the containment report the same way. | cap-isolation records the configuration finding for the resource profile (F-a7-04), where values written to YAML validated, reviewed correctly, and had no runtime effect; at the adapter level the same failure mode yields two green conformance runs of the same technology, which reads as a proven swap and is not one (F-a3-06). | sourced | `F-a7-04`, `F-a3-06` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 9 | Apply build-definition-of-done: run the definition of done below and then its deliberate breakage, and record both outputs as an evidence record the way build-evidence-record fixes, before calling this facet done; proposed pointer, see those skills. | build-definition-of-done owns criterion plus deliberate breakage plus both recorded outputs, and build-evidence-record owns what the record names, so this row points at them instead of restating the sentence six sibling -implement skills had copied (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-part-c-04` "A criterion nothing can fail is not a criterion." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: implement terminate before implementing anything comfortable. Every ceiling above the unit resolves to destroying it, and it is the operation the definition of done and the budget guarantee both stand on. Research query: is there a recorded build order or evidence record on this stack showing terminate implemented and conformance-tested before any comfort feature, rather than this being an un-evidenced preference? | proposed | `F-b4-02` |
| Proposed: keep the profile table in configuration and let each adapter carry its own resolution of the same names, so a technology that cannot serve a profile shows up as a missing key refused at admit rather than as a unit that quietly ran smaller. Research query: is there a recorded profile table or refusal-at-admit implementation on this substrate that this row could cite directly instead of asserting the pattern from scratch? | proposed | `F-a2-03` |
| Apply build-adapter-pair: let the capability-granting adapter fail the machine-shaped cases it cannot serve honestly instead of emulating a kernel so both adapters look alike; a declared gap the conformance run asserts on beats a silent emulation that would not survive a real workload. proposed pointer, see that skill. | proposed | `F-b1-04` |
| The isolation adapter pins no model and no endpoint on the unit's behalf: agentic-stack states that callers request a class, never a vendor (F-a4-01), and the broker is where the endpoint is chosen (F-a3-07), so a second decision taken inside the sandbox would be invisible to the caller. | sourced | `F-a4-01`, `F-a3-07` "Callers request a class, never a vendor" |
| Proposed: at this boundary the vocabulary travels the wrong way. The risk is not that the running sandbox is replaced but that its machine vocabulary is imported into the declaration, after which every later containment technology has to imitate a virtual machine to satisfy the contract. Research query: unresearched; no prior-art search has been run for how a container or sandbox interface keeps a hypervisor's resource vocabulary out of the portable declaration. | proposed | `F-part-c-11` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-firecracker-microvm` | today | admit, run, terminate and inspect_containment built over the Firecracker microVM cells that already run on this host as systemd templates - one microVM per agent, startable without sudo via polkit, plus a long-lived variant with a larger runtime ceiling. The adapter owns jail creation at mode 0700 under a per-VM uid with no passwd entry, the guest network flag that is off by default, the dummy key inside the guest, and the vsock route to the host broker. | Proposed: cannot start a unit without booting a guest kernel from a block-device root, so its start and teardown cost is a floor no profile can lower; and its unit of resource granted is a machine, so it cannot express a grant smaller than one. | Point the binding at the other adapter, submit the same declaration, and re-run the containment conformance suite. No core change is expected. Assert the containment marker the host observes from the running unit, not the adapter name written in the binding. | claimed | `F-a2-02`, `F-a2-03`, `F-a3-01`, `F-b3-02` "One microVM per agent, startable without sudo via polkit" |
| `E-swap-candidate-hosted-sandbox-services` | second | the same declaration served by a WebAssembly component sandbox run through an OCI-conformant shim: no guest kernel, no filesystem unless one is granted, no network stack at all, and a capability-granted syscall surface. Profiles resolve to capability grants rather than to machine sizes. | Proposed: cannot honour boot arguments, block devices or a guest network interface, and cannot claim hardware-level isolation the way a virtual machine does; a search-only record notes that a userspace syscall-interception sandbox such as gVisor does not provide hardware-level isolation, and a component sandbox is further from a machine still. Whether the shim can claim full OCI Runtime Spec conformance is cap-isolation's first open question. | Proposed: the axes that differ are unit_of_resource_granted and start_and_teardown_cost. Select by configuration with no code edit between runs, then compare both containment reports against the same declaration and against each adapter's declared_gap. The entity recorded here is the class-shaped swap candidate on PASS.md's Isolation row, because the knowledge base carries no entity for a component sandbox; cap-isolation records that choice as an open question. | claimed | `F-b3-02`, `F-b1-04`, `X-cap-isolation-004` "gVisor improves container security by intercepting syscalls in userspace, but it does not provide hardware-level isolation" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/containment/test.sh && python3 harness/containment/conformance.py --adapter dryrun --adapter second |
| Expected | The gate (25 checks) and the conformance run together prove: one contained unit runs one agent turn under each of two containment technologies from one declaration; jail mode is 0700 with no host passwd entry, the containment report is read from the host never the unit, egress attempts blocked equals egress attempts made, the output digest and exit status are equal across adapters, and the two adapters differ in execution model on at least one axis (adapters_run=2). Earlier criterion named tools/conformance_isolation.py, replaced by the harness on 2026-09-03. |
| Deliberate breakage | Add 0.0.0.0/0 to harness/containment/binding.json's default_declaration egress_allowlist (egress: allowlist) and change nothing else (the harness README's breakage A); restore with git checkout -- harness/containment/binding.json. |
| Expected failure | Both adapters' egress-attempt assertions fail (egress_blocked drops below egress_made) and the conformance run exits non-zero naming both adapters; the jail mode, digest and containment-marker assertions still pass, so the report is green on everything except the one property the breakage removed. |
| Status | measured |
| Evidence | `F-part-c-04`, `F-a3-06` "owned by a per-VM uid with no passwd entry" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-isolation`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Where does the containment marker come from on an adapter that has no long-lived unit to read it from? | Attempt to read a host-observed marker from a unit whose whole lifetime is shorter than the observation, and keep the outcome as an evidence record in the form build-evidence-record defines, which is where this finding about configuration that had no runtime effect is already stated. If the marker cannot be captured during the run, the assertion moves to admission and the report says so. | Capture the marker at admission from the host side and re-assert it at teardown, so a technology with no observable running unit is still distinguishable from the one it replaced. | `F-a7-04` "had no runtime effect" |
| Do the two unit shapes that run today collapse into two profiles, or does the long-lived variant need a distinct lifecycle above the boundary? | Count what actually differs between them once the declaration carries a resource profile and a duration ceiling. If nothing but the envelope and the ceiling differ, they are two profiles; if the long-lived variant is resumed or reattached rather than re-admitted, that is a lifecycle the declaration does not model. | Two profiles behind one declaration, with the duration ceiling as a field. Revisit if reattachment to a running unit turns out to be required, since that is a second operation rather than a second profile. | `F-a2-03`, `F-a2-02` "Long-lived variant, larger runtime ceiling" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-isolation 2831cb4f, 2026-09-03 |
