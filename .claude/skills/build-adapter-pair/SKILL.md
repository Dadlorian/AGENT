---
name: build-adapter-pair
description: The discipline of shipping two adapters behind one capability interface, where the second is chosen because it breaks a different assumption than the first. Load it when picking a second implementation for a boundary, when writing the conformance suite both implementations must pass, when wiring the swap into CI, or when auditing whether a contract has been quietly shaped around whatever runs today. Also load it when a boundary has only one implementation, when someone says the thing behind it can be changed later, when a review asks whether a field belongs to the capability or to the thing behind it, or when a proposed alternative is a different product of the same shape.
---

# build-adapter-pair

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make swappability a tested property rather than an intention: every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing and that the interface is not shaped around its current implementation. | sourced | `F-b1-04`, `F-part-c-05`, `E-rule-b1-3` "Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing" |

## Entities

| Entity |
|---|
| `E-rule-b1-3` |
| `E-ask_item-c-4` |
| `E-capability-isolation` |
| `E-standard-oci-runtime-spec` |
| `E-adapter-firecracker-microvm` |
| `E-swap_candidate-gvisor` |
| `E-capability-state-persistence` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap_candidate-object-store` |
| `E-finding-a7-2` |
| `E-finding-a7-3` |

## Contract

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The pair exists at all: an interface ships with at least two adapters. One adapter is an implementation, not a boundary. | sourced | `F-b1-04` "Every interface ships with at least two adapters" |
| The second adapter's job is proof, not redundancy: it is chosen to prove the interface is not shaped around its current implementation. | sourced | `F-part-c-05`, `F-b1-04` "chosen to prove the interface is not shaped around its current implementation" |
| Both adapters satisfy the same named standard, and what the core imports is the interface, never either implementation. | sourced | `F-b1-02`, `F-b1-03` "The core imports interfaces, never implementations" |
| The swap touches configuration and adapters only. If swapping the implementation requires touching the core, the boundary is drawn wrong and the pair has found the defect it exists to find. | sourced | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| The interface survives the swap and the implementation does not: the contract is stated as the capability plus its standard, so the adapter changes and the core does not. | sourced | `F-b3-18`, `F-b3-01` "the adapter changes and the core does not" |
| Proposed: every pair carries a non-empty, machine-readable differs_in_execution_model field naming the axis and both adapters' values on it; an empty field, or identical values, rejects the pair. | proposed | - |
| Neither adapter obliges a caller to take a client library we wrote; if integration requires our SDK, the boundary is bespoke and the pair is proving the wrong thing. | sourced | `F-b1-05` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| A pair is claimed until the swap has been executed and recorded; swappability is a tested property, not an intention, and the two labels are kept apart. | sourced | `F-b1-04`, `F-part-c-08` "Swappability is a tested property, not an intention." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Product names, versions and hostnames stay in the adapter rows. The interface, its invariants and its conformance suite name capabilities and standards only. | sourced | `F-part-c-09` "Products belong in the adapter column only" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the boundary as a capability plus the standard that governs it - 'a unit of work does X, per <standard>, version cited or unverified' - before naming any implementation, then check that today's implementation is only one of several ways to satisfy that sentence. | The Isolation row is the stated template for the whole table: the architecture names the capability and the standard, satisfies it with today's adapter, and when the workload changes the adapter changes and the core does not. | sourced | `F-b3-18`, `F-b1-03` "the adapter changes and the core does not" |
| 2 | Require two adapters per interface and treat the second as a proof obligation rather than a spare: it exists to prove the first is not load-bearing and that the interface is not shaped around its current implementation. | Design rule 3 makes swappability a tested property rather than an intention, and the ask names the second adapter's purpose as exactly that proof. | sourced | `F-b1-04`, `F-part-c-05` "Swappability is a tested property, not an intention." |
| 3 | Proposed: choose the second adapter by asking whether it breaks a different assumption, scoring candidates on execution-model axes - start and teardown cost, how many separate processes must run for work to progress, whether a call returns a result or a claim ticket, whether cancellation can be honoured promptly, where durability and verification live, what unit of resource is granted, and whether replay determinism is required. Reject any candidate scoring identically to the first on every axis. | Proposed, from docs/decomposition.md section 4. A candidate with the same execution model can be swapped in while the interface stays shaped around that shared model, so the swap succeeds and demonstrates nothing. | proposed | - |
| 4 | Proposed: record the answer in a machine-readable differs_in_execution_model field on the pair, naming the axis and both values. An empty field rejects the pair, and the author must find a different second adapter rather than argue for the one in hand. | Proposed, from docs/decomposition.md section 3.5 row B2. A judgement that lives only in prose cannot be checked, and the check is what lets this discipline fail. | proposed | - |
| 5 | Write one conformance suite against the interface and parameterise it over adapters: the suite imports the interface only, never an adapter type, and both adapters run the identical assertions with no per-adapter skips or per-adapter expected values. | The core imports interfaces, never implementations, so the contract, not either implementation, is what both adapters must satisfy. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| 6 | Give the conformance suite a deliberate breakage and run it: remove one interface guarantee from an adapter, or feed the suite a stub adapter that returns success for everything, and record which assertion fails. | A criterion nothing can fail is not a criterion, so a suite that has never been seen to fail is not yet evidence that either adapter conforms. | sourced | `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| 7 | Proposed: exercise the swap in CI rather than on paper. Run the full conformance suite once per adapter on every change, selecting the adapter by configuration alone with no code edit between runs, and fail the job if either run is skipped or reports zero behavioural assertions. | Proposed convention, with a measured reason: a gate can be structurally green because every behavioural stage skipped, so a swap job that runs but asserts nothing repeats that failure in a new place. | proposed | `F-a7-03` "Those establish well-formedness, not correctness" |
| 8 | Proposed: audit the interface for shaping. List every field, operation and error in the contract and ask, for each, which adapter's vocabulary named it. Anything only the first adapter's model can honour is that adapter's detail leaking into the contract: express it in the capability's own terms, make it an optional negotiated capability, or delete it. | Proposed procedure. If an implementation cannot be swapped without touching the core, the boundary is drawn wrong, and a field only one adapter can honour is how that happens quietly. | proposed | `F-meta-04` "If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong" |
| 9 | Check that integrating either adapter needs no client library we wrote, and fix the boundary before shipping the pair if it does. | If integration requires our SDK, a boundary is bespoke where a standard existed, and a pair behind a bespoke boundary proves only that we can swap our own code. | sourced | `F-b1-05` "If integration requires our SDK, a boundary is bespoke where a standard existed" |
| 10 | Assert in the conformance suite that telemetry, policy, provenance and budget hold identically under both adapters, instead of being supplied by one adapter's implementation. | Those guarantees are applied by the platform and not requested by the caller, so they belong to the platform around the pair and must survive the swap unchanged. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| 11 | Proposed: label the pair claimed until the swap has actually been executed and its result recorded, and never upgrade the label by rewording the description. | Proposed convention. The standing constraint is to distinguish claimed from measured throughout, and a pair described as swappable is an intention until a run says otherwise. | proposed | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 12 | When no candidate differs on any axis, record it as an open question with the measurement that would decide it and a default, instead of shipping a same-shape pair that satisfies the count of two. | What could not be decided is a required output, not an apology. | sourced | `F-part-c-06` "A required output, not an apology." |
| 13 | Proposed: read references/execution-model-axes.md before scoring a candidate when the second adapter feels different but you cannot name the axis, or when reviewing a pair whose difference field reads as a vendor name rather than a property. | Proposed reference material. It holds the axis catalogue, the three-part wrapper test, and a worked pair written by knowledge-base entity id, all of which are too long for this table. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| A swap job that is green because its behavioural assertions all skipped proves nothing; count the assertions that actually ran under each adapter, since only those establish correctness rather than well-formedness. | sourced | `F-a7-03`, `E-finding-a7-2` "Those establish well-formedness, not correctness" |
| Verify which adapter actually served the call at runtime rather than trusting the configuration that selected it: values written in the documented place have validated, reviewed correctly, and had no runtime effect. | sourced | `F-a7-04`, `E-finding-a7-3` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Correlation must ride on an explicit resource attribute set at dispatch, so the telemetry assertions in a conformance suite still hold under an adapter that mints its own root trace instead of inheriting one. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| Callers request a class, never a vendor: if selecting between the pair leaks a vendor name into caller code, the choice has escaped the adapter row and the swap is no longer a configuration change. | sourced | `F-a4-01`, `F-part-c-09` "Callers request a class, never a vendor" |
| Assume a de facto standard can itself be shaped around one implementation: a widely adopted route in the substrate branches only on a fixed list of names and refuses a provider actually in use, which is the mismatch a same-shape pair would never surface. | sourced | `F-a4-08` "route, which branches only on" |
| Name the property being preserved across the swap, not the container holding it: where the store changes, the chain is the valuable idea and should survive, the file is not. | sourced | `F-b5-05` "The chain is the valuable idea and should survive; the file is not" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `python3 tools/check_adapter_pairs.py --skills .claude/skills` (proposed tool, built alongside the first `cap-` skill in wave 3). For every `cap-` and `seam-` skill it asserts: exactly one adapter with role today, at least one with role second, a non-empty differs_in_execution_model naming an axis and both adapters' values, and at least one axis whose two values differ. |
| Expected | exit 0 with `pairs_checked > 0`, `single_adapter == 0`, `empty_axis == 0`, `same_model_pairs == 0` |
| Deliberate breakage | Add a `cap-` skill whose second adapter is a thin wrapper of the first: copy the today adapter's row, change only the entity id, and leave differs_in_execution_model empty. Then run it a second time with that field filled in by hand but carrying the same axis values as the first adapter. |
| Expected failure | First run exits 1 with `empty_axis == 1`, naming the skill and the adapter entity. Second run still exits 1 with `same_model_pairs == 1`, because no axis value differs - the case that counting two adapters cannot catch. Claimed: no `cap-` skill exists in wave 1 and the tool is not written, so neither run has been performed here. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b1-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: `cap-agent-runtime`, `cap-capability-packaging`, `cap-document-validation`, `cap-durable-execution`, `cap-errors`, `cap-idempotency`, `cap-identity`, `cap-isolation`, `cap-model-access`, `cap-policy`, `cap-provenance`, `cap-scheduling`, `cap-state-persistence`, `cap-telemetry`, `cap-tool-access`, `cap-work-intake`, `seam-dispatch`, `seam-state`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Does every capability admit a second adapter that differs in execution model, or do some admit only a narrower difference that still satisfies design rule 3? | For each capability, score its candidate second adapters on the axis list and record the widest true difference found. A capability where no candidate differs on any axis is recorded as an exception with its reason, and the count of such exceptions is the answer. | The pair is still required and the difference field records the narrowest true difference; a pair with no true difference is rejected rather than granted an exception. | `F-b1-04`, `F-part-c-05` "Every interface ships with at least two adapters" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 7cca7f9fb186c6c0527b8fdf909db9f0bd4facb97564a61cf3413e9a5abcdbdf |
| kb edges head | 53a86af888fe464b4fb87d747ea0f22e85ced7e132320b0ca046da5492a46536 |
| Author | session claude/build-adapter-pair 2831cb4f |
