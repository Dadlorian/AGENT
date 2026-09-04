# Context for STATUS row 75: the seven examples of the future state as its user meets it (read this, the files it names, nothing else)

Direction (owner, 2026-09-04; intent to improve past, never a wording to keep): show how the framework works from the user's side, grouped by what a person or system is doing, not by capability; simple on the surface, composable underneath; aligned to the standards; every call shown. Getting the sandbox (the unit) right is most of the success.

## The seven areas, each one example under examples/<area>/
| Area | The user's question | Capabilities it exercises | Litmus sections it must move |
|---|---|---|---|
| run | what happens in the sandbox on my behalf; fifty of them at once | isolation, agent runtime, tool access, model access, capability packaging, errors, correlation | isolation, agent-runtime, tool-access, model-access, capability-packaging, errors |
| ask | I have intent; how do I hand it over from an IDE, a shell, an event, a timer, a partner system; what do I get back at once | work intake, identity, idempotency, admission policy, document validation | work-intake, document-validation, identity, idempotency, concern-identity, concern-idempotency |
| watch | how I see it from where I am: stream, callbacks, task status, traces; and the steps inside a unit | telemetry, human interaction, errors as events | telemetry, concern-telemetry, concern-errors |
| steer | approve, edit, reject, retry, escalate; and the operator's reconnect, restart, replace of a stuck unit | human interaction, policy, dispatch, isolation | policy, concern-policy |
| progress | plan, develop, test, release, production as gated stages; fan-out, judge, loop, multi-day resume, budget stop | durable execution, scheduling, guarantees, compensation, evaluation, workflow operators | durable-execution, scheduling, concern-budget |
| done | how I know, and what happens next: checks met, branch or pull request, provenance, notification by my door, ledger line with cost | provenance, state persistence, identity, ledger | provenance, state-persistence, concern-provenance |
| improve | what the platform learned: tokens per done, attempts, which template held | evaluation, improvement loop | (none; measured by tools/improvement_loop.py) |

## The shape every example has (its README carries these six headings, each a table)
1. Ideal: the future-state statement for the area, from docs/litmus/questionnaire.json's future_state texts of its sections and docs/consumption/unit-design.json, cited.
2. Standards: the standards holding it, with version status, from the same records.
3. The call: the one line a caller writes at each of the four doors (human at a shell or IDE, event, schedule, external agent) and the document behind it (examples/<area>/entries/{human,event,schedule,external}.json, all conforming to examples/end-to-end/schemas/entry.schema.json).
4. What the user sees: the typed events, the receipt, the result, per door.
5. Composition: how the example is built from units and the six operators; a run step table (`bash examples/<area>/test.sh` then the door commands).
6. Extension points: where a builder adds without touching the core, and the gaps the example exposed (each with a research query).

## Vocabulary
Use the terms in docs/reference/ontology.md: task, task specification, execution context, attempt, execution, trajectory, step, tool call, artifact, work product, evaluation, result, disposition; the success ladder (execution, instruction, candidate, validation, task, outcome, promotion) instead of one word success; the cell lifecycle verbs (provision to dispose). Run means one execution of one attempt. Where a term is better than one you would have used, use it; where the ontology conflicts with a standard on file, the standard wins and say so.

## Rules
- Dry-run cells only: adapters from the harnesses under harness/ (containment, gateway, observability, workflow, linked, and the rest) selected by configuration; the call shape is identical to live. Never a product name outside an adapter or the standards table.
- Runnable, dependency-free Python 3.11 plus bash, no network. `bash examples/<area>/test.sh` is the visible check and prints `passed N, failed 0`. A test that runs nothing is a defect.
- provenance.json per example: kb ids and X- ids cited, what is measured by the test, what is claimed, the areas' litmus sections.
- Reuse examples/end-to-end (the four entries, the schemas, the runner) and the harnesses; do not copy code you can call.
- The run example follows docs/consumption/unit-design.json: contract mount hashed and ledgered, driver and assessor separated, visible checks in the contract and hidden checks outside, attempts counted outside the cell, the published task lifecycle (submitted, working, input-required, completed, failed, cancelled), escalation one class once.
- watch and steer also write docs/architecture/proposed/<area>.json: the two new future-state areas (inside-unit observability; fleet state management) as proposed blueprint rows with research queries, never invented mechanisms.
- Read: docs/consumption/unit-design.md, docs/litmus/questionnaire.json (your sections), docs/maturity/closures.md (mechanisms for your sections), examples/end-to-end/README.md and its files, the harness READMEs you call, .claude/skills/agentic-stack/SKILL.md and .claude/skills/build-evidence/SKILL.md, OWNER.md.
