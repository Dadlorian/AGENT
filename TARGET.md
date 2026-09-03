# Desired future state — composability baseline

Stated by the platform owner on 2026-09-03 as the baseline target. PASS.md Part B is a starting list; this is the definition the end-to-end framework must satisfy, and gaps between the two are to be found and filled.

## T1. Entry

1. A human must be able to enter the system.
2. An agent must be able to enter the system.
3. An internal or external event must be able to enter the system.

## T2. What composability does

1. Composability hides the complexity.
2. Composability allows enhancing particular aspects of any element without touching the rest.
3. State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used.

## T3. Usability

1. It has to be simple to use.
2. It cannot be daunting or overly complex, or no one will use it.

## T4. Method

1. Treat this as a baseline target and improve on it.
2. Decompose it; add the skills, loops, and agents needed to reach it.
3. PASS.md's list is a limited baseline: understand what an end-to-end version is, make up for the gaps, and solve it.
4. Work through every item with a self-improvement loop: at the end of each section a ceremony re-reviews the output, improves the skills that produced it, and the loop continues.

## T5. Operating protocol

1. Do not stop at ceremonies; run them and continue.
2. When a problem comes up, use 1-3-1: define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation.
3. If no recommendation is found, drop the two lowest solutions, find two more, and repeat until solved.

## T6. Consumption

1. There is one way to consume the platform, shown as code end to end: what is called, with what, and what comes back.
2. Four entries cover nearly every situation: a human, an event, a schedule (time), and an external system or agent. All four enter through the same shape.
3. Any entry can call complex workflows, agents, and loops that run across the entire stack.
4. Multiple models are used through one gateway, and a fleet of GPUs serves local models; callers request a model class, not a vendor.
5. Each agent is defined up front by what it is good at, so callers know how to call it and how to sequence it.
6. The target scale is well over a hundred agents running at a time, working together, managing state, breaking problems down, and self-improving where they can.

## T7. Harness

1. The harness is an overlay that integrates across every component fluidly; it never pins the integration to a component.
2. Every harness call goes through the capability interface, and the component sits behind an adapter.
3. Each component has a minimal call in isolation, and the same calls are linked across the composable elements.
4. Standards will change, systems will change, and components will change; the harness shows where the impacts are.
5. Changing a component means swapping its adapter, and the conformance run proves the interface held.
6. This direction is a target toward perfection, not a fixed definition; improve on it.

## T8. Decisions

1. The twelve host-fact gaps in docs/architecture/gap-triage.json are absent on the host today and are design work, not facts to research.
2. Standard-version gaps and does-a-standard-exist gaps are closed by research with real search results, or recorded as none found.

## T9. Scorecard

1. The improvement loop works the metric furthest from its target and stops when every target holds or the owner says stop.
2. Sourced share: proposed rows are under 30 percent of all rows.
3. Restatement: the validator reports zero restatement warnings.
4. Measured done: at least half of all definitions of done have a measured run.
5. Load path: a builder reads at most 11 skills for one common task per door.
6. Swaps proven: every harness section executes one adapter swap with the conformance run before and after.
7. Review honesty: every review catches both planted defects, or it is discarded.
8. Freshness: zero status rows stale against the ledger at every checkpoint.
9. Verification: every standard has a fetched record when the environment allows fetch.
