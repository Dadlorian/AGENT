# Agentic work ontology (owner-supplied reference, 2026-09-04)

Supplied by the owner from an outside assistant, as direction: separate the work requested, its execution, the artifacts produced, and whether the intended outcome was achieved, so that "task", "run" and "success" stop being overloaded. Recorded as a reference, like `composable-plan.md`: an example to align to, never a fact. Where a term below already has a home in PASS.md or a standard on file, the mapping table says so; where the industry uses a word at several granularities, the pin says which one this platform means.

## The ten first-class objects (industry-aligned; kept as entities, not labels)

| Object | Meaning | This platform's home |
|---|---|---|
| Task | the semantic objective | the Document's intent (core-components) |
| Task Specification | machine-readable task: prompt, repository, policy, limits, validators | the Document plus the contract mount (unit design) |
| Execution Context | everything needed to execute: ref, branch, environment, tools, credentials | the contract mount plus the workspace declaration |
| Attempt | one try at the task, `attempt-003` | the advisor's attempt counter (unit design) |
| Execution | the running instance of an attempt | one contained turn in a cell (seam-dispatch) |
| Trajectory | the recorded path: prompts, actions, tool outputs | the typed event stream over the agent protocol, correlated (cap-telemetry) |
| Artifact | anything produced: patch, test, report, log | `/out` at seal time |
| Evaluation | the process judging a candidate | the Judge and the hidden checks (core-components, cap-evaluation) |
| Result | the evaluation's output | the typed verdict |
| Disposition | what happens next: accept, retry, reject, escalate | the escalation policy on the contract |

## Success is a ladder, never one word

| Term | Means | Measured by |
|---|---|---|
| Execution Success | the cell and harness ran correctly | stop reason and containment report |
| Instruction Completion | the agent finished the procedure it was given | the harness's own stop |
| Candidate Completion | a work product exists | `/out` non-empty |
| Validation Success | the visible checks passed | the contract's checks |
| Task Success | the success criteria were met | the hidden checks, outside the cell |
| Outcome Success | the underlying problem is solved | the caller's acceptance, or production measurement |
| Promotion Success | the accepted artifact entered the downstream lifecycle | branch merged, released, deployed |

An agent that edits code, runs the tests and exits normally has execution success and instruction completion and nothing above them. This ladder is the platform's claimed-versus-measured rule applied to a run.

## The cell lifecycle as verbs

Provision, Instantiate, Materialize (workspace), Hydrate (checkout), Bootstrap (dependencies), Configure, Bind Tools, Apply Policy, Dispatch, Launch, Execute, Validate, Collect, Dispose. The containment interface's operations map onto these one for one; an adapter that cannot name which verb it is performing is not conformant.

## Three identities of the work

Work Item (administrative, schedulable: the envelope), Task (the objective), Work Product (what was produced). One task, many attempts, each attempt a different candidate.

## Pins where the industry uses a word at several sizes

- **Run** in this platform is one execution of one attempt: one harness invocation in one cell. Not the whole job, not the workflow. The user-view area named "run" asks what happens in the sandbox; its examples use attempt, execution and trajectory for the parts.
- **Task** carries the published task lifecycle (submitted, working, input-required, completed, failed, cancelled), which is the state of the execution of the current attempt, not of the objective.
- **Unit** (PASS.md's word) is the fully qualified thing: task specification, execution context, cell, harness, attempts, evaluation, disposition and the ledger record. **Cell** is the execution environment. **Harness** is the agent control loop inside it.

## Alignment notes

Trajectory, episode, step and attempt are the terms of the agent-evaluation literature; promotion, provision, bootstrap and dispose are the terms of delivery and infrastructure; trace, span and event are OpenTelemetry's; provenance, lineage and attestation are in-toto's and SLSA's. A research record per term is owed before any of this is cited as sourced (research query: primary definitions of trajectory, episode and attempt in agent benchmarks; of promotion in delivery pipelines).
