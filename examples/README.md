# Examples

**`examples/reference/` is the live structure: nine areas, one per reference-model area, of which
one is built.** `examples/end-to-end/` is the reference walk across all of them and is not one of
them. `examples/archived/` holds the seven journey folders (ask, run, watch, steer, progress, done,
improve) that this structure replaced on 2026-09-09; they are kept as evidence, not as work, and
nothing should be added to them.

Every folder is dependency-free Python 3 plus bash and runs without a network. Adapters are
dry-run, and the call shape is identical to live.

An area demonstrates the cards it holds and says so in its `cards.json`: what it `demonstrates`,
and what it records as a gap with the card's address. `docs/reference/card-example-map.json` is the
join, derived from the reference model, and `tools/check_card_example_map.py` proves every card is
accounted for. Read `examples/reference/README.md` before adding one, and
`docs/reference/profile-sufficiency.md` for what the card profile will and will not tell you.

| Folder | Area | Focus | Run | Last line |
|---|---|---|---|---|
| `1-invocation/` | Invocation / Entry Points | How work enters the platform | - | not built yet |
| `2-orchestration/` | Orchestration & Control Plane | Turn requests into work, apply policy, and coordinate agents | - | not built yet |
| `3-core-agent/` | Core Agent | One worker, one job | `bash examples/reference/3-core-agent/test.sh` | `passed 19, failed 0` |
| `4-execution/` | Execution & Runtime | Run agents in isolated, repeatable, production-safe environments | - | not built yet |
| `5-assurance/` | Assurance & Completion | Validate results, admit outputs, and hand back to the caller | - | not built yet |
| `6-observe/` | Observe | spans the journey rather than sitting in it | - | not built yet |
| `7-self-improvement/` | Self-Improvement | spans the journey rather than sitting in it | - | not built yet |
| `base-shared-services/` | Shared Platform Services | Open source only · no per-seat or metered platform cost | - | not built yet |
| `rail-cross-cutting/` | Cross-Cutting Concerns | spans the journey rather than sitting in it | - | not built yet |
| `end-to-end/` | The reference walk across all of them, not one of them | A fault report enters four ways, becomes one envelope, is triaged, looped on until the fix passes, parked for a human, and recorded in a hash-chained ledger under a budget ceiling. | `bash examples/end-to-end/test.sh` | `passed 30, failed 0` |

## Checks

Two per area. `test.sh` is the visible check its author could see and tune. `docs/night/hidden/<area>.sh`
is the hidden check an isolated reviewer wrote and the author never saw; it is the deciding half of
the definition of done, and on the first area it earned that name by finding a defect eighteen
author-written assertions had passed over. `tools/grader_isolation.py` checks the two are kept
apart. Every `test.sh` writes under its own `out/`, which git ignores; do not run two invocations
of the same area's suite at once.

## The archived seven

They are described in `examples/archived/README.md` and measured in
`docs/reference/card-example-gaps.md`, which is the measurement that justified replacing them:
eight cards had no example under that structure and nothing said so.
