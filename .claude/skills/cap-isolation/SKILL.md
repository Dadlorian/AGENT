---
name: "cap-isolation"
description: "The ideal state of the Isolation capability: one unit of work runs with declared resources and declared egress, governed by the OCI Runtime Spec, with the operations the core imports, the declaration and containment-report shapes, what the boundary refuses to expose, and the criteria that decide whether a containment technology may serve the interface. Load it when deciding how a unit of work is contained, when a request field describes a machine instead of a resource declaration, when asking 'can this run somewhere we do not own hardware', 'what stops this unit reaching the network', or 'where does the real credential live', when a sandbox is about to be coupled to whatever runs inside it, and whenever containment is about to be trusted because the unit reported it rather than because something outside the unit asserted it."
---

# cap-isolation

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for running a unit of work under declared resources and declared egress, so that what runs inside is opaque to how it is contained and the containment technology is an adapter rather than the architecture. | sourced | `F-b3-02`, `F-b3-18`, `E-capability-isolation` "a unit of work runs isolated, per the OCI Runtime Spec" |

## Entities

| Entity |
|---|
| `E-capability-isolation` |
| `E-standard-oci-runtime-spec` |
| `E-sandbox-property-isolation` |
| `E-swap-candidate-gvisor` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-oci-runtime-spec` | v1.2 or later (unverified) | unverified | - | `F-b3-02`, `X-cap-isolation-001`, `X-cap-isolation-002` |

- `E-standard-oci-runtime-spec` version note: v1.2 or later; version unverified. Two search-only records describe the standard as the configuration interface for low-level container runtimes and report a v1.3.0 release, but the specification itself was not fetched from this environment.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| admit (call name is ours; egress-off-by-default is the sourced substrate behaviour) | one isolation declaration: a named resource profile, an egress policy that is none unless an allowlist is given, and a credential mode of broker-only | an admission handle, or the typed problem isolation-unavailable when no adapter can honour the declaration. Admission is where a declaration a given adapter cannot meet is refused, rather than being silently downgraded (proposed) | sourced | `F-a3-04` "Egress is a flag, default off" |
| run (call name is ours; the capability-not-technology framing is the sourced row) | an admission handle and a handle to the input document; never a filesystem path, an image reference the caller resolved, or a machine description | one unit result: exit status, output digests, resource usage and egress counters. Nothing in it identifies the containment technology (proposed) | sourced | `F-b3-18` "a unit of work runs isolated, per the OCI Runtime Spec" |
| terminate (call name is ours; the ceiling-terminates-the-unit rule is the sourced one) | an admission handle and a grace window | the unit destroyed, with the same result shape whether the stop was requested or forced. This is the operation every ceiling above the unit depends on (proposed) | sourced | `F-b4-02` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| inspect_containment (call name is ours; asserting from outside the unit is the sourced, verified-live property) | an admission handle | a containment report asserted from outside the unit: the jail directory's mode, whether the owning identity exists in the host account database, and egress attempts made against attempts blocked. The unit never reports on its own containment (proposed) | sourced | `F-a3-06` "owned by a per-VM uid with no passwd entry — verified live" |

### Shapes (JSON Schema 2020-12)

**isolation-declaration (the egress-off-by-default member reflects the sourced substrate behaviour; the full schema is in references/isolation-shapes.md)** (sourced; sources: `F-a3-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:declaration:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "profile",
    "egress"
  ],
  "description": "Proposed. Everything a caller may say about containment. There is no field here that only a hardware-virtualised adapter could honour, which is the property that makes the declaration portable.",
  "properties": {
    "profile": {
      "type": "string",
      "minLength": 1,
      "description": "A named resource envelope resolved by the adapter. A name, never a set of numbers: megabytes and vCPU counts are a machine description."
    },
    "egress": {
      "enum": [
        "none",
        "allowlist"
      ],
      "default": "none",
      "description": "Off unless the caller asks for it, and then only to named destinations."
    },
    "egress_allowlist": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1
      },
      "description": "Required when egress is allowlist. An empty or absent list with egress=allowlist is a malformed declaration, not an open unit."
    },
    "credentials": {
      "const": "broker_only",
      "default": "broker_only",
      "description": "A const, not an enum. No real secret enters the unit; it reaches a broker that holds the key."
    }
  },
  "allOf": [
    {
      "if": {
        "properties": {
          "egress": {
            "const": "allowlist"
          }
        },
        "required": [
          "egress"
        ]
      },
      "then": {
        "required": [
          "egress_allowlist"
        ]
      }
    }
  ]
}
```

**containment-report (the jail_mode and owner_in_host_passwd fields are the sourced, verified-live substrate property; asserted from outside the unit)** (sourced; sources: `F-a3-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:containment-report:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "jail_mode",
    "owner_in_host_passwd",
    "egress_attempts_made",
    "egress_attempts_blocked"
  ],
  "description": "Proposed. Every field is observed by the host about the unit. Nothing here is taken from anything the unit said about itself.",
  "properties": {
    "jail_mode": {
      "type": "string",
      "pattern": "^0[0-7]{3}$",
      "description": "Octal mode of the unit's own directory on the host."
    },
    "owner_in_host_passwd": {
      "type": "boolean",
      "description": "False is the passing value: the owning identity has no entry in the host account database."
    },
    "egress_attempts_made": {
      "type": "integer",
      "minimum": 0
    },
    "egress_attempts_blocked": {
      "type": "integer",
      "minimum": 0,
      "description": "Equal to egress_attempts_made when the declaration named no destinations. A suite where attempts_made is 0 asserted nothing."
    },
    "secrets_seen_inside": {
      "type": "integer",
      "minimum": 0,
      "maximum": 0
    }
  }
}
```

**What a refusal looks like (proposed): problem details, not prose [caller's view, folded from cap-isolation-use]** (proposed; sources: -)

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

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The capability is the contract and the containment technology is the adapter: what the core imports is that a unit of work runs isolated, per the OCI Runtime Spec, and what satisfies it today is one adapter among several. | sourced | `F-b3-18`, `F-b3-02`, `E-capability-isolation` "a unit of work runs isolated, per the OCI Runtime Spec" |
| Proposed: what runs inside the unit is opaque to how the unit is contained. The interface takes a document handle and a declaration, never an agent, a runtime or a tool surface, because a containment boundary coupled to one kind of payload is a sandbox that can only ever run that payload. Research query: is there a recorded PASS.md or TARGET.md fact stating isolation's contract in these exact opaque-payload terms, beyond the isolation-row template already cited? | proposed | `F-b3-18` |
| Egress is off by default and named when it is on. The substrate already carries this instinct: the guest has no network and egress is a flag, default off (recorded claimed). | sourced | `F-a3-04` "Egress is a flag, default off" |
| No real secret enters the unit. On the substrate the guest holds a dummy key and model egress leaves through a host broker that holds the real key and picks the endpoint (both recorded claimed); the interface keeps that as the credential mode rather than as a property of one sandbox. | sourced | `F-a3-05`, `F-a3-07` "No real secret inside the VM" |
| Containment is asserted from outside the unit. The one containment property the substrate records as verified live is the jail directory's mode and the fact that its owning identity has no entry in the host account database - an observation the host makes about the unit, not a statement the unit makes about itself. | sourced | `F-a3-06` "owned by a per-VM uid with no passwd entry — verified live" |
| The boundary must be able to destroy a unit on request, because that is what makes every ceiling above it enforceable: exceeding a budget terminates the unit, not the platform. An adapter that cannot be made to stop cannot serve this interface at any profile. | sourced | `F-b4-02` "Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform" |
| Proposed: every statement in this skill about how a unit behaves under containment is claimed except the jail row, which the knowledge base records as verified live. Nothing in this capability has been run in this repository. | proposed | `F-a3-06` |
| The three ways in that TARGET T1 lists - a human, an agent, an internal or external event - reach a contained unit through the same call. How the work arrived is not a field of it, so one caller-side handler covers all three. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| Enhancing one aspect leaves the rest untouched: replacing what contains the work, adding a resource profile, tightening an egress rule or moving where the unit runs changes nothing in a caller that reads exit status, outputs and usage. cap-errors states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| Proposed: a declaration no adapter can admit is refused, never admitted under a weaker profile. A silent downgrade turns a refusal into a unit that ran with less containment than was asked for, and nothing in the result would say so. Research query: unresearched; no prior-art search has been run for how sandbox and workload runtimes report a requested-but-unavailable containment level, as opposed to substituting the nearest profile that fits. | proposed | `F-b4-07` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: machine configuration in every form - guest kernel and its boot arguments, block-device or root-filesystem layout, host paths, hypervisor control sockets, vCPU and megabyte counts. A caller able to set one of these has bound the platform to hardware virtualisation and made the second adapter unbuildable. Research query: does the second adapter's own configuration surface (X-cap-isolation-004/005) name any of these fields as required, which would mean the exclusion list needs a documented exception rather than a flat ban? | proposed | `F-b3-18` |
| Which containment technology serves the unit, and at what version: agentic-stack states that products belong in the adapter column only (F-part-c-09), so neither the declaration nor the unit result carries anything a caller could branch on to learn what contained it. | sourced | `F-part-c-09` "Products belong in the adapter column only" |
| The real credential. The unit is given a broker to reach, and the broker holds the real key and picks the endpoint; the key itself is never a field of anything that crosses into the unit. | sourced | `F-a3-07`, `F-a3-05` "which holds the real key and picks the endpoint" |
| The criterion a unit's output will be judged against never travels in the isolation declaration, in the document handle the unit is given, or in anything readable from inside the jail: an agent sees its outcome, never the criterion it is judged against. agentic-stack states design rule 6 (F-b1-07); the consequence here (proposed) is that a contained unit is the one place where the graded work and its grading rule would otherwise share a filesystem, so inspect_containment asserts on containment from outside and the unit reads nothing about how its result will be scored. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | State the boundary as a capability plus its standard before any containment technology is named: 'a unit of work runs isolated, per the OCI Runtime Spec, version unverified'. Read this row as the table's own template row. | PASS.md names this row the template for the whole table: the architecture is the sentence about the capability, and what satisfies it today is an adapter. Getting that split wrong here gets it wrong everywhere else, because every other capability row is read against this one. | sourced | `F-b3-18`, `F-b3-02` "Read the Isolation row as the template for the whole table" |
| 2 | Express the unit as declared resources and declared egress. Before adding any field, ask whether an adapter with no kernel, no filesystem unless one is granted and no network stack could honour it; if it could not, the field is adapter detail and does not go in. | Proposed. This is the one test that keeps the contract portable: a declaration is something several execution models can satisfy, while a machine description is something only one can, and the difference is invisible until the second adapter is attempted. Research query: has this admit-time portability test been run against the second adapter's actual configuration surface to confirm it flags the right fields? | proposed | `F-b1-04`, `F-b3-18` |
| 3 | Set the two safe defaults at the boundary rather than in a profile: egress is none unless an allowlist is supplied, and the credential mode is broker-only. Make egress=allowlist with no allowlist a malformed declaration. | Both defaults already hold on the substrate - the guest network is none with egress a flag defaulting off, and the guest credential is a dummy key - and both translate to any adapter unchanged, which is why they belong to the interface rather than to one sandbox. | sourced | `F-a3-04`, `F-a3-05` "**None.** Egress is a flag, default off" |
| 4 | Assert containment from outside the unit: the jail directory's mode, whether its owning identity exists in the host account database, and the egress attempts made against the attempts blocked. Never accept a containment claim the unit made about itself. | The only containment property recorded as verified live is exactly of this kind, an observation the host makes about the unit; a self-report is a statement by the thing whose containment is in question. | sourced | `F-a3-06` "owned by a per-VM uid with no passwd entry" |
| 5 | Record the standard's version as unverified until the published specification has been read in an environment that can fetch it. The records naming a released version are search-only. | A version number nobody read is a fabrication with a decimal point in it, and every record on file for this standard is a search result rather than the specification text. | sourced | `X-cap-isolation-002`, `F-part-c-10` "The OCI Runtime Spec v1.3.0 was released on November 4, 2025" |
| 6 | Choose the second adapter on execution model, not on brand: one whose unit of resource granted is a set of capabilities rather than a machine, and whose start and teardown cost differs by orders of magnitude. Record the pair on those axes. | build-adapter-pair carries the rule that a second adapter is chosen to prove the interface is not shaped around its current implementation (F-b1-04), and the candidate recorded for this boundary is the one that has to run where we do not own hardware (F-b3-18). | sourced | `F-b1-04`, `F-b3-18` "needs to run somewhere we do not own hardware" |
| 7 | Return failures as the typed problem object cap-errors defines. When no adapter can admit a declaration, return the isolation-unavailable type as retryable rather than downgrading the declaration to one that fits. | cap-errors owns the failure shape (F-b4-07): typed and machine-readable, never parsed from prose, so a boundary that cannot admit a declaration answers with a type a caller can branch on. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 8 | Judge a candidate containment technology by the criterion in this skill's definition of done, run from one suite over both adapters, before deciding it may serve the interface. | agentic-stack and build-definition-of-done carry the rule that a criterion nothing can fail is not a criterion (F-part-c-04); the containment counters that make this skill's criterion able to fail are stated in its definition of done, and build-adapter-pair requires the one suite to run over both adapters (F-b1-04). | sourced | `F-part-c-04`, `F-b1-04` "A criterion nothing can fail is not a criterion" |
| 9 | Send the work, the document it runs on, and a correlation id you chose. Write no profile, no egress rule and no credential unless you have a reason. | It has to be simple to use, and every field you fill in is a decision you now own. The fields you leave alone are the ones the platform can change under you without breaking your call. | sourced | `T-t3-01` "It has to be simple to use." |
| 10 | Proposed: open references/isolation-shapes.md when implementing or reviewing the full declaration schema, the profile resolution rules or the containment-report fields. The body of this skill is enough to judge a candidate technology and to call the capability without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full schemas exceed the progressive-disclosure budget for a skill body, and a reader deciding whether a boundary is drawn correctly does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Read the containment actually in effect out of the running unit's report, never out of the profile that was requested: a profile that was silently widened validates and reviews exactly like one that took effect, which is the configuration finding agentic-stack records (F-a7-04) and build-adapter-pair applies to adapter selection. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| A unit that exits 0 proves the unit ran, not that it was contained, so containment carries assertions of its own that fail when containment is absent: agentic-stack records the green-gate finding (F-a7-03), where the structural stages establish well-formedness, not correctness. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Proposed: keep the resource profile a name that the adapter resolves, not a set of numbers the caller chose. The moment a caller writes megabytes and vCPU counts it has described a machine, and the profile stops being something a capability-granting adapter can interpret at all. Research query: what named-profile convention (e.g. small/medium/large) do existing sandbox-as-a-service offerings use, so the profile enum here is not invented from nothing? | proposed | `F-b3-18` |
| Proposed: keep the claimed and the verified apart in this capability specifically. One containment row on the substrate is recorded as verified live and the rest of that sandbox is recorded claimed, so a conformance suite that only re-asserts the verified row adds nothing and a design that treats the claimed rows as measured is overstating what is known. Research query: has the egress-blocking half of the definition_of_done fixture actually been run and recorded as measured, or does it remain claimed alongside the rest? | proposed | `F-a3-06`, `F-a3-04` |
| Proposed: judge a candidate second containment technology by what it would leave untested. One that still boots a kernel and exposes a filesystem agrees with today's adapter on every machine-shaped field in the contract, so the swap would show that the vendor can change and nothing about whether the execution model can. Research query: unresearched; no prior-art search has been run for execution-model axes specific to containment technologies, as opposed to the general adapter-pair axes build-adapter-pair records. | proposed | `F-b1-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-firecracker-microvm` | today | admit, run, terminate and inspect_containment served by a Firecracker microVM: hardware virtualisation rather than a container, with a jail directory at mode 0700 owned by a per-VM uid that has no passwd entry, no guest network unless egress is switched on, and a dummy key inside the guest while a host broker holds the real one. | Proposed: cannot start without booting a guest kernel from a block-device root, so its start and teardown cost is a floor no profile can lower, and its unit of resource granted is a machine rather than a capability set. Anything expressed as kernel or device configuration is unavailable to any adapter that is not a virtual machine. | Select the adapter by configuration, submit the same isolation declaration, and run the containment conformance suite over both adapters. No core change is expected, because the core imports the declaration and not the machine. | claimed | `F-b3-02`, `F-a3-01`, `F-a3-06` "OCI Runtime Spec \| Firecracker microVM" |
| `E-swap-candidate-gvisor` | second | the same declaration served by gVisor: a container sandbox that intercepts syscalls in userspace rather than booting a guest kernel, giving it no filesystem or network stack beyond what the runtime grants and no hardware-level isolation boundary. | cannot claim hardware-level isolation the way a virtual machine does, because it intercepts syscalls in userspace instead of booting a guest kernel from a block device; that is the execution-model axis this swap is chosen to test against Firecracker's hardware virtualisation. | Select the adapter by configuration, submit the same isolation declaration, and run the containment conformance suite over both adapters. The axis that must differ is unit_of_resource_granted and its isolation guarantee: a hardware-virtualised machine with a guest kernel and block-device root, versus a userspace syscall interceptor with no guest kernel and no hardware-level isolation claim. | claimed | `F-b3-02`, `F-b1-04`, `X-cap-isolation-004` "gVisor improves container security by intercepting syscalls in userspace, but it does not provide hardware-level isolation." |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/containment/test.sh |
| Expected | Proposed tool, built with the first implementation of this interface: `python3 tools/conformance_isolation.py --adapter today --adapter second --fixture fixtures/unit-egress-probe --report out/isolation-conformance.json`. It runs one fixture unit under both adapters from the same declaration (profile `small`, `egress: "none"`) and asserts: exit codes equal across adapters, output digests equal, `jail_mode == "0700"` with `owner_in_host_passwd == false`, a connect attempt from inside to an address outside the declared allowlist fails, `egress_attempts_blocked == egress_attempts_made`, `egress_attempts_made > 0`, and `adapters_run >= 2`. exit 0 and one line per adapter of the form `adapter=<entity> exit=0 digest=<equal across adapters> jail_mode=0700 owner_in_host_passwd=false egress_attempts_made=<above 0> egress_attempts_blocked=<equal to made>`, followed by `adapters_run=2`. Until that proposed tool exists, `bash harness/containment/test.sh` (owned by cap-isolation-implement) is the running gate: every check line reads ok and the script exits 0. |
| Deliberate breakage | Add `0.0.0.0/0` to the default `egress_allowlist` and change nothing else, then re-run both adapters. |
| Expected failure | The probe's connect attempts now succeed, so `egress_attempts_blocked` drops below `egress_attempts_made` under both adapters, the equality assertion fails for each, and the run exits non-zero naming both adapters. The jail and digest assertions still pass, which is the point: a green run on those alone would have said nothing about egress. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-a3-04`, `F-a3-06` "Egress is a flag, default off" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-skill-authoring`, `cap-errors`

Used by: `cap-isolation-implement`, `compose-agent`, `seam-dispatch`, `xc-tenancy`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Can the second adapter (E-swap-candidate-gvisor, a userspace-syscall-interception sandbox) honestly claim OCI Runtime Spec conformance, or only a documented subset of it? | Run the standard's own runtime validation suite against both adapters and record which assertions the shim cannot satisfy. If the failing set is small and unrelated to what the platform actually uses, a documented subset is the honest answer. | Declare the interface OCI-shaped with a written conformance subset, and label every conformance claim claimed until that suite has run. Overclaiming conformance is worse than documenting a subset. | `F-b3-02`, `X-cap-isolation-001` "The OCI Runtime Spec defines the behavior and the configuration interface of low-level container runtimes" |
| Resolved during reconciliation ceremony reconcile-01 (RP-005): which of PASS.md's four named isolation swap candidates should the second adapter be recorded against, now that the earlier component-sandbox description named in the Adapters row was found unsupported by any cited source? | The earlier row (see the Adapters section for the product it named) reasoned that every candidate on the Isolation row 'still boots or emulates a kernel', which X-cap-isolation-004 directly contradicts for the adapter now recorded: it intercepts syscalls in userspace and does not provide hardware-level isolation, a genuine execution-model difference from the today-adapter's hardware virtualisation. A real entity already exists for it (see the Adapters section), so no entity needed minting. | The second adapter is now the one recorded in the Adapters section above, the candidate whose cited source (X-cap-isolation-004) states a concrete, sourced execution-model difference from the today-adapter. The other two entities on the same Isolation row, E-swap-candidate-kata-containers and E-swap-candidate-cloud-hypervisor, remain named in F-b3-02 as further candidates, not yet adopted as the recorded second adapter. | `T-t5-02`, `F-b3-02`, `X-cap-isolation-004` "identify the three best possible solutions that align to the goal" |
| Who resolves the isolation declaration when the caller never writes one? The end-to-end consumption example's entry envelope carries no isolation field at all, while the first-cut dispatch request in docs/decomposition.md requires one. | Trace one entry of each kind through to a unit and record where the declaration is filled in. If every path fills it from the agent profile and the policy in force, the caller-facing field is dead weight and should not exist. | The declaration is resolved below the entry envelope, from the agent's profile and the policy in force, and no entry kind carries an isolation field. This is the reading that keeps the caller-facing surface small; it is recorded here as a disagreement with the dispatch request shape rather than settled. | `T-t3-02` "daunting or overly complex, or no one will use it" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-isolation 2831cb4f, 2026-09-03 |
