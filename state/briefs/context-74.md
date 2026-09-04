# Context for STATUS row 74: the unit (captain's context for the advisor; read this, the files it names, and the web)

## The owner's direction (2026-09-04, distilled): intent to improve past, not a phrase to preserve; mark where you went further as proposed, with why
- A container is a protected unit: a Firecracker microVM here, chosen for start-up speed over a VM or a container; a sandbox or a container elsewhere. Most agentic work is a wrapper around a harness calling a model API, manipulating code, persisting to GitHub, solving a problem and sending code back for review.
- Break the features up so the thing can be called composably; easy to use is the art, composability gives the depth for workflows, loops and fan-out. Which model is called (LiteLLM: local GPUs or frontier) is universal; models work a problem and work together across problems.
- Token economics is first-class: smart ways to save time and tokens to solve the same thing.
- Inside the protected unit: a systematic start that reads an immutable mounted structure (a seeded context such as system.md, the tool list, the skills it needs); that structure is the permissioning, so the agent has to do the thing it was told. With a measurable definition of done, smart models can evaluate and less smart models (the GPU fleet) can attempt; the attempt count is measured externally ("I finished my 10 or 20 attempts, do something"); the blind oracle applies: sometimes a separate call, sometimes a frontier model makes the call, but measuring done is structured tests and byte checks, not AI where it can be avoided. This framework inside the unit sets the tone for everything downstream that monitors the unit of work.
- An advisor should do the solutioning; a light form exists where the microVM is not needed; "agent" is the wrong name for the fully qualified thing.

## Names fixed so far (from PASS.md: F-b5-01 "Dispatch — one unit of agent work executes and returns one result"; the host service is firecracker-cell@)
- cell: the protected runtime (microVM today; gVisor, Kata, hosted sandbox, or a plain capability-granted process in the light form).
- unit: the fully qualified thing: contract + cell + harness + model door + measure step + ledger record.
- agent: only the model-driven harness inside the cell.

## The sketch to test, extend or overturn (captain, proposed)
Mounts: /contract read-only immutable hashed (system.md, intent, visible checks, tool list, skills, policy, attempt ceiling); /repo read-only snapshot at a ref; /work the only writable place; /out append-only, sealed at exit. The contract hash is ledgered before start. No credential inside the cell: GitHub, models and tools reached through the host-side gateway under a short-lived mandate.
States: declared, admitted, seeded, attempting (turn n of N), measured, then done | exhausted | refused | cancelled, then sealed, then destroyed | snapshotted.
Checks: visible (in /contract, the unit may run them) and hidden (host only: held-out tests, byte assertions, a frontier rubric only when mechanical checks cannot decide). Measured happens outside the cell against /work; the unit is told pass or fail per check and nothing else.
Advisor: on the host side of the boundary: seeds the harness from /contract, drives it turn by turn over the agent protocol, runs measure, counts attempts, applies the escalation policy (higher model class, a person, or stop). Inside the cell only the harness and a seed reader.
Open decisions: escalation default; whether system.md is authored per task or generated from the document plus named skills.

## What exists (read these, nothing else in the repo)
- examples/end-to-end/schemas/entry.schema.json and entries/*.json: the one envelope every door produces.
- harness/containment/README.md and harness/containment/call.py: the nine-line contained turn (admit, session over the agent protocol, dispatch under a ceiling, cancel, finish, containment report from the host); adapters dryrun / live (Firecracker + goose) / second (capability-granted process, no cancellation).
- harness/gateway/README.md: one completion by model class under a ceiling (LiteLLM live).
- harness/workflow/README.md and harness/linked/README.md: durable steps, parked approval, bounded loop; and the composed path through every component.
- .claude/skills/seam-dispatch/SKILL.md, .claude/skills/cap-isolation/SKILL.md, .claude/skills/core-components/SKILL.md (Document and Judge), .claude/skills/compose-workflow/SKILL.md, .claude/skills/xc-guarantees/SKILL.md: the contracts these compose from.
- docs/fold/maturity-gaps.json: what the two questionnaires found below the future state.

## Research (web search; one record per result you rely on, kb/research/unit-design.jsonl, ids X-unit-design-NNN, lens unit-design, status search-only, date 2026-09-04)
Current practice, inside the window 2026-03 to 2026-09, for: sandboxed coding agents (microVM snapshots and restore for warm starts; read-only context mounts; capability-granted processes); how agent harnesses take their system context and tool lists from files; attempt ceilings and escalation between model tiers; held-out tests and mechanical grading of agent work; token accounting per attempt.

## Output: docs/consumption/unit-design.json, then docs/consumption/unit-design.md rendered from it by you (tables only)
{ "origin": ..., "names": {...}, "forms": {"full": ..., "light": ...}, "mounts": [...], "states": [...], "transitions": [...], "checks": {"visible": ..., "hidden": ...},
  "advisor": {"where": ..., "loop": [...]}, "escalation": {"options": [...], "recommended": ..., "why": ...}, "seed": {"options": [...], "recommended": ...},
  "one_call": {"shell": "...", "event": "...", "schedule": "...", "agent": "..."}, "token_economics": [...], "composition": {...},
  "gaps": [{"claim": ..., "research_query": ...}], "first_example": {"name": ..., "does": ..., "measured_by": ..., "steps": [...]}, "cites": [...] }
Every statement is origin sourced with a kb id or X- id and a verbatim quote, or says proposed. Cite the owner's direction as origin "owner" for where an idea came from; that mark is never a ceiling: where you can make the idea better, do, and say why. Run `python3 tools/kb.py merge-research` is NOT yours to run; leave the jsonl for the captain.
