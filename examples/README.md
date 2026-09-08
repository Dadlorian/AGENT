# Examples

Eight runnable folders. Seven follow one piece of work the way its user meets it, in order: ask, run, watch, steer, progress, done, improve. The eighth, `end-to-end`, is the original reference that the seven build on. Every folder is dependency-free Python 3.11 plus bash, runs without a network, and enters through the same four doors: a person at a shell or IDE (`entries/human.json`), an event (`entries/event.json`), a schedule (`entries/schedule.json`), and an external agent or partner system (`entries/external.json`). The cells are simulated (dry-run adapters), and the call shape is identical to live.

Start with `run`, because everything else calls it. Each folder's README carries the same six tables: the ideal for its area, the standards holding it, the one call at each door and the document behind it, what the user sees, how it composes from units and the six operators, and the extension points and gaps. `docs/examples/index.md` is the seven-by-four-door matrix with the check results.

| Folder | The user's question | Focus | Run | Last line |
|---|---|---|---|---|
| `ask/` | I have intent; how do I hand it over from where I am, and what do I get back at once? | Four producers (shell, event, schedule, agent) become one work envelope at intake; the caller gets an immediate acknowledgement carrying the idempotency key and the correlation id. | `bash examples/ask/test.sh` | `passed 63, failed 0` |
| `run/` | What happens in the sandbox on my behalf, and what if fifty of them run at once? | One unit of agent work in a contained cell: the contract mount hashed and ledgered, ceilings enforced from outside the cell, typed refusals, one class escalation, sealed output, repeated fifty times. | `bash examples/run/test.sh` | `passed 50, failed 0` |
| `watch/` | How do I see it from where I am? | The correlated trail a unit leaves: typed events, spans, metrics, logs and problem objects readable on any declared surface, without choosing a backend or where an attribute lives. | `bash examples/watch/test.sh` | `passed 73, failed 0` |
| `steer/` | How do I intervene, and how does an operator recover a stuck unit? | Policy decides before every autonomous action, every decision logged and pinned to a rule version and replayable; human approval, edit and rejection; escalation; operator verbs for reconnect, restart and replace. | `bash examples/steer/test.sh` | `passed 96, failed 0` |
| `progress/` | Work is not done when a unit stops; how does it reach production? | One change through five gated stages: a bounded loop drafts it, a fan-out tests it, a human gate releases it, the irreversible effect declares its undo before firing, and the run survives a real process death and resumes at the right step. | `bash examples/progress/test.sh` | `passed 131, failed 0` |
| `done/` | How do I know it is finished, and what happens next? | Closing a unit: attestations verified before promotion, an append-only record with inclusion proofs, the notification back through the door the work came in by. Parked on two hidden assertions (see `docs/night/parked.json`). | `bash examples/done/test.sh` | `passed 81, failed 0` |
| `improve/` | What did the platform learn? | The improvement loop over templates: which revision passed the gates, attempts and spend per attempt, which template held; measured by `tools/improvement_loop.py` rather than a litmus section. | `bash examples/improve/test.sh` | `passed 88, failed 0` |
| `end-to-end/` | The original reference: one fault through all four doors | A fault report enters four ways, becomes one envelope, is triaged by agents, looped on until the fix passes, parked for a human, and recorded in a hash-chained ledger under a budget ceiling. Dry-run by default; live dispatch needs gateway variables. | `bash examples/end-to-end/test.sh` | `passed 30, failed 0` |

## Which litmus sections each example moves

| Folder | Sections |
|---|---|
| `ask/` | work-intake, document-validation, identity, idempotency, concern-identity, concern-idempotency |
| `run/` | isolation, agent-runtime, tool-access, model-access, capability-packaging, errors |
| `watch/` | telemetry, concern-telemetry, concern-errors |
| `steer/` | policy, concern-policy |
| `progress/` | durable-execution, scheduling, concern-budget |
| `done/` | provenance, state-persistence, concern-provenance |
| `improve/` | none; measured by the improvement plan |

## The gap each one records first

| Folder | Gap |
|---|---|
| `ask/` | no subscription, streaming or cancellation operation on the intake lifecycle it advertises |
| `run/` | the errors registry lacks the isolation-operation-unsupported and runtime-unavailable types the isolation interface raises |
| `watch/` | no capability operation returns task status; the runner projects it from the event stream |
| `steer/` | policy bundles are versioned by digest but never cryptographically signed or verified |
| `progress/` | both executors run in-process, so the crash is a real process death but not a distributed one |
| `done/` | nothing is delivered; the notification is a record naming surface and recipient, no surface adapter is called |
| `improve/` | no operation applies a revision to a named template with slots; only checkpoints and metrics move |
| `end-to-end/` | no real agent is dispatched by default |

## Checks

Two per folder. `test.sh` is the visible check the author could see and run. `docs/night/hidden/<folder>.sh` is the hidden check an isolated reviewer wrote and the author never saw, run only at close; it is the blind-oracle half of the definition of done. Every `test.sh` writes under its own `out/`, which git ignores; do not run two invocations of the same folder's suite at once.
