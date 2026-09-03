---
name: seam-dispatch-implement
description: How to build the Dispatch seam on this stack: a shim over the per-agent virtualisation unit that runs today, a second dispatcher that has no session at all, how to bring three execution paths that share no contract in front of one interface without rewriting any of them, where the budget, policy, identity, telemetry, provenance and idempotency guarantees attach to a dispatch and to a resume, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that starts, cancels, resumes or replays a unit of agent work; when wiring an executor behind the dispatch interface; when deciding what the second executor should be; when a killed run has to continue where it stopped rather than from the beginning; when a repeated request must not spend twice; or when a conformance run reports untyped failures and you have to find which adapter produced them.
---

# seam-dispatch-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract seam-dispatch fixes into running code on this substrate: shim what executes today, build a second executor whose execution model differs, migrate the paths that share no contract onto one interface, and attach every cross-cutting guarantee where no dispatch can skip it. | sourced | `F-b5-03`, `E-seam-dispatch` "Today there are three implementations and no contract between them." |

## Entities

| Entity |
|---|
| `E-seam-dispatch` |
| `E-adapter-firecracker-microvm` |
| `E-swap-candidate-hosted-sandbox-services` |
| `E-host-unit-firecracker-cell-service` |

## Contract

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Nothing in this facet redefines a shape. The request, the result, the step record, the context contract, the stop-reason enum and the failure body are seam-dispatch's (F-b5-03), and this facet only says where each one is produced, validated and recorded on this stack. A field that exists here and not there is a defect here. | sourced | `F-b5-03` "the request shape, the result shape, cancellation semantics" |
| Migration is additive. Each execution path that runs today gets a shim that answers the seam's shapes; none of them is rewritten and none of them is switched off before its shim passes the suite. agentic-stack states the substrate rule (F-part-c-11); the consequence here is that a shim is the unit of migration. | sourced | `F-part-c-11`, `F-part-b-01` "Part A is substrate, not scope. Do not propose replacing what runs." |
| Every cross-cutting guarantee attaches at the dispatcher, outside the unit, because agentic-stack states that the platform applies them and a caller cannot decline them (F-b1-08). The order this facet fixes: claim the idempotency key, verify the delegation chain, record the policy decision, take the budget reservation, then execute; stamp correlation at dispatch; attest each output as it becomes durable. A guarantee applied inside the unit is a guarantee the unit could decline. | sourced | `F-b1-08`, `F-b4-01` "Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller" |
| Two of the suite's assertions start red by construction and must stay in the suite. There is no identity field anywhere in the system today and typed errors are absent, so the delegation-chain assertion and the untyped-failure count fail on the first run. A red assertion that names a missing guarantee is the correct output; deleting it would make the suite green and the platform no safer. | sourced | `F-a6-05`, `F-a6-06` "No identity field anywhere in the system" |
| Proposed: the durability record is written by the dispatcher, not by each executor - the step id and the idempotency key are allocated before execution and the checkpoint reference is written at the first durable output. seam-dispatch states the resume and replay rules (X-cross-structure-042, X-cross-structure-043); putting the record in the dispatcher is what lets an executor with no journal of its own satisfy them unchanged. | proposed | `X-cross-structure-043` |
| The two adapters differ in execution model, not in brand: one holds a session open on hardware we own for the life of the unit and can be stopped mid-call; the other is one request-response into someone else's sandbox and cannot be stopped once started. build-adapter-pair states that swappability is a tested property (F-b1-04); here the test is that one parameterised suite runs over both with no code edit between runs. | sourced | `F-b1-04` "Swappability is a tested property, not an intention." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: which shim answered a dispatch, and anything the shim needed to talk to its executor - socket paths, unit names, endpoint hostnames, session handles. These live in the adapter configuration and in the adapter rows below; they never reach a result, a problem object or a recorded step, because a caller that could read them would break on the swap this facet exists to make possible. | proposed | `F-part-c-09` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Publish the seam's schemas as files and make the dispatcher validate every request against them before anything else happens, refusing a failure with the registered `urn:agentic:problem:document-invalid` type and no side effect. Do not hand-write field checks inside a shim. | agentic-stack states that the core imports interfaces, never implementations (F-b1-02), and seam-dispatch fixes the shapes; a shim that validates by hand is a second, drifting copy of the contract, and the first assertion of the conformance suite is exactly this refusal. | sourced | `F-b5-03`, `F-b1-02` "The core imports interfaces, never implementations" |
| 2 | Wrap the executor that runs today in a shim instead of replacing it: keep the per-agent virtualisation unit, keep its control protocol, and map its turn onto dispatch and cancel. The shim owns the ceilings, the step record and the writes through the state seam; the unit keeps owning the sandbox. | Part A is substrate and stays. build-adapter-pair states the Isolation row as the template (F-b3-18): the isolation and cancellation behaviour is already good, and the only thing missing at this boundary is the contract - so the smallest correct change is a shim, not a rewrite that would put a working sandbox at risk to gain a shape. | sourced | `F-part-c-11`, `F-b3-18` "the adapter changes and the core does not" |
| 3 | Bring the remaining execution paths behind the same interface one at a time. Keep each path's native entry alive until its shim passes the suite, then make the seam the only supported entry and count the paths answering through it as `migrated_paths`. | seam-dispatch states why this seam matters (F-b5-03), and cutting three uncontracted paths over together would leave no working reference to compare a shim against. A counter is what turns 'we are migrating' into a number the definition of done can assert. | sourced | `F-b5-03` "This is the seam that decides whether agent execution is pluggable at all." |
| 4 | Build the second dispatcher with no session at all - one request-response into a hosted single-shot executor - and run the suite against it first after any shape change, before the adapter that runs today. | A second executor of the same interactive shape would leave every session assumption untested. Running the unlike one first means an accidental dependence on a held-open session, a callback or a host-side socket fails on the same day it is written, rather than at the swap. | sourced | `F-b1-04`, `F-b3-02`, `F-b3-18` "needs to run somewhere we do not own hardware" |
| 5 | Wire the cross-cutting guarantees into the dispatcher in one fixed order - idempotency claim, delegation verification, policy decision, budget reservation, execute - and emit the correlation members as resource attributes at dispatch rather than inheriting them. Attest each output as it becomes durable, not at the end of the run. | A guarantee applied after the first metered call is a guarantee that arrived too late: refusal is deterministic and happens before execution, not after spend. Attesting at the end would leave a cancelled or deadline-stopped run's partial outputs unattested, which is precisely the case that most needs provenance. | sourced | `F-b4-04`, `F-a7-02` "Refusal is deterministic and happens before execution, not after spend" |
| 6 | Allocate the step id and the idempotency key in the dispatcher before execution, write the checkpoint reference at the first durable output, and make the resume path read the step records to find the first step whose reference is null. Keep all of this out of the executors. | Proposed: this is what makes the durability obligation seam-dispatch states satisfiable by an executor that has no journal of its own. If each executor kept its own resume state, the seam's replay guarantee would be as strong as the weakest executor and the swap would change behaviour rather than only implementation. | proposed | `X-cross-structure-043`, `F-b3-04` |
| 7 | Record every conformance run as an evidence record naming the script digest, the commit, the tree hash under test and whether the tree was dirty, and label the outcome claimed until the run actually happened on a clean tree. | build-evidence-record owns this discipline and the substrate already has the store to hold it. A measurement taken from a dirty tree cannot be reproduced, so labelling it measured would put a number in the record that nobody can get back. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |
| 8 | Keep the identity and typed-error assertions in the suite from the first run, expect them red, and report them per adapter rather than dropping them until the guarantees exist. | There is no identity field anywhere in the system today and typed errors are absent, so a suite that omitted those assertions would be green while the platform had neither. A red assertion naming a missing guarantee is the definition of done doing its job. | sourced | `F-a6-05`, `F-a6-06` "Typed errors \| Absent" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Do not build the seam's durability on the orchestrator that is defined but not running: express the obligation as a step record the dispatcher writes, so it is satisfiable by a durable engine and equally by a queue plus a state machine. The orchestrator can then be an adapter rather than a precondition. | sourced | `F-a6-02`, `F-b3-04` "Durable workflow orchestration and human-in-the-loop signals are designed around it and it is currently down" |
| Reuse the spend mechanism that already exists rather than building a new meter: the scoped key with a hard cap was verified to terminate spend rather than merely record it, which is the property the seam's ceiling needs. Add only the reservation lease, so a unit that crashes without reconciling does not leave the ceiling permanently consumed. | sourced | `F-a4-07` "verified to terminate spend rather than merely record it" |
| Put the policy decision in the enforcement path, not beside it. The substrate's recorded failure mode is a set of conformance checks that exist and are not wired into the enforcement path, which is indistinguishable from having no policy at the moment it matters; assert the ordering between the recorded decision and the first metered call instead of asserting that a checker ran. | sourced | `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |
| Write the dispatcher's step records into a chained log so that a manual edit between runs is detectable - agentic-stack and build-evidence-record already cite the task store's chain (F-a5-03). The consequence here: the chain is the valuable idea in the store that runs today and should survive whatever replaces the file, because a resume that trusts an unchained record cannot tell a checkpoint from an edit. | sourced | `F-a5-03`, `F-b5-05` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-firecracker-microvm` | today | A dispatcher process holding the seam's shapes, driving one Firecracker microVM per dispatch through the Agent Client Protocol over a vsock channel, with the systemd template unit `firecracker-cell@.service` (and its long-lived variant) as the unit supervisor. Model egress leaves over vsock to the host broker that holds the real key, the guest network is off by default, and the shim - not the guest - owns the deadline timer, the budget reservation, the step record and every write through the state seam. cap-isolation owns this entity's capability row. | Proposed: cannot dispatch where we do not own the hardware, and cannot survive the loss of the host holding the vsock channel, so its resume path depends on the same machine. Its cancel floor is a property of the guest's own control loop, which is why the grace window is per request and stored beside the adapter. | Select the dispatcher by configuration only. Run `tools/conformance_dispatch.py` over both adapters from one parameterisation, with per-adapter assertion counts, and change no core code between runs. | claimed | `F-b3-02`, `F-a2-02`, `F-a3-03`, `F-a3-07` "One microVM per agent, startable without sudo via polkit" |
| `E-swap-candidate-hosted-sandbox-services` | second | The same dispatch and cancel served by an HTTP client into a hosted sandbox service: one request carrying the document, the ceilings and the context declaration, one response carrying the terminal result. No session is held, no vsock channel exists, no callback is possible, and the executor keeps no journal - so the dispatcher's own step record is the only thing that makes resume and replay work. seam-dispatch carries this pair at the ideal facet and cap-isolation owns the capability row both entities come from. | Proposed: cannot be cancelled mid-call, so its honest terminal on an expired grace window is cancel_timeout where the first adapter reports cancelled; cannot stream partial frames, so partial outputs appear only at checkpoints the shim wrote; and it has no host-side broker socket, so model egress must be reachable over the network or the isolation profile is unserveable - which is an open question of this facet rather than a solved detail. | Proposed: the axes that must differ are unit_lifetime (a session held open on our hardware for the life of the unit, versus one request-response on someone else's) and cancellation_reach (stoppable mid-call within the grace window, versus not stoppable once started). Run this adapter first after any shape change, so a new dependence on a held-open session fails the day it is written. | claimed | `F-b3-02`, `F-b1-04` "hosted sandbox services" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | Proposed tool: `python3 tools/conformance_dispatch.py --adapter today --adapter second --assert-migrated-paths 3 --report out/dispatch-conformance.json`. This is decomposition.md section 3.3 row S1 run against the two built adapters, with the migration counter added. Per adapter it asserts: a malformed request is refused with `urn:agentic:problem:document-invalid`; a cancel reaches a terminal state within `deadline.cancel_grace_s`; a request whose ceiling is exceeded terminates with `stop_reason: "budget_exhausted"` and a recorded spend that is non-zero and at most the ceiling; an interrupted run leaves `partial: true` with at least one output whose `recorded_at_head` is non-null; and every failure body is `application/problem+json` with a `type` in the closed registry. Across adapters it asserts `adapters_run >= 2`, `assertions_run > 0` per adapter, and `migrated_paths == 3`. |
| Expected | exit 0 and one line per adapter of the form `adapter=<today\|second> assertions_run=5 failed=0 untyped=0`, then `adapters_run=2 migrated_paths=3`. On the first real run the identity and typed-error assertions are expected red and named per adapter, because there is no identity field anywhere in the system and typed errors are absent today; that red is the correct first output and is recorded as such, not suppressed. |
| Deliberate breakage | In one adapter's shim, assemble the result before the state-seam write returns - move the write after the result is built - and change nothing else, then re-run the interrupted-run case. |
| Expected failure | That adapter's interrupted run comes back with `partial: true` and an output whose `recorded_at_head` is null, so the durability assertion fails for that adapter only, the run exits non-zero, and the report names it while the other adapter still reports `failed=0`. The failure is the seam's central promise breaking: a result naming an output no later reader can find. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b5-03` "a machine-checkable definition of done, plus the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `seam-dispatch`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The second dispatcher has no host-side broker socket, so how does a unit running in someone else's sandbox reach a model without a real secret entering the unit? | 1-3-1 applied. The three options: expose the broker on the private network and let the hosted unit reach it with a short-lived, per-dispatch credential; proxy model calls back through the dispatcher so the unit never talks to a model directly; or restrict the second adapter to profiles that need no model egress at all. The third would make the pair prove less, and the first widens the broker's exposure. Recommendation taken: proxy through the dispatcher, because it keeps the broker where it is and keeps the no-real-secret rule cap-isolation owns intact. Deciding evidence: a measured latency comparison of the proxied path against the direct one under a realistic turn. | The second adapter runs with the model call proxied through the dispatcher, and the isolation profile it advertises says so, until the latency measurement is taken. | `F-a3-05`, `T-t5-02` "identify the three best possible solutions that align to the goal" |
| Which of the three execution paths that share no contract migrates first, and does each have an owner who can retire its native entry? | An inventory naming each path, its current entry point, its owner, and the callers that would break if its native entry were retired. seam-dispatch cites the same record for the count and the absence of a contract (F-b5-03); what is missing is the identity of the three, which the knowledge base does not carry. | Migrate the path the microVM shim already covers first, because its shim is the one this facet specifies; keep every native entry alive and assert `migrated_paths` as a counter rather than a cutover date. | `F-b5-03` "Today there are three implementations and no contract between them." |
| Does the dispatcher's step record live in the state seam's log, or in the durable-execution capability's own store? | The two seams are deliberately independent, and dispatch is authored against a narrower 'durably record this output' obligation and wired to the state seam afterwards. The deciding evidence is whether a resume that reads step records at a pinned snapshot can be served by the state seam's query surface without adding a query shaped only for dispatch. | Write the step record through the state seam, since the outputs already go there and one log avoids a second store to keep consistent; revisit if the resume query turns out to need a projection the planner's query surface would not otherwise carry. | `F-b5-04`, `F-b5-05` "the write model, concurrency and single-writer guarantees" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session seam-dispatch 2831cb4f, 2026-09-03 |
