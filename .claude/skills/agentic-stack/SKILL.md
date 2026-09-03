---
name: agentic-stack
description: Root contract for building the agentic platform described in PASS.md. Load this first whenever work touches the platform, its core (Document, Planner, Graph, Judge, Ledger), any capability interface or adapter, Dispatch, State, a workflow, loop, or agent composition, or any skill in this repo. Every other skill here assumes this one is loaded.
---

# Agentic Stack

This repo builds the target architecture in `PASS.md` Part B as a set of linked skills. Read `PASS.md` once per session; it is the source of truth and this skill only fixes the rules for turning it into work.

## The seven rules, restated as tests

Each rule in PASS.md B1 becomes a question you can answer about any artifact. If the answer is no, the artifact is wrong, whatever else it does well.

1. Does the core import only interfaces? A product name inside core code, core docs, or a core skill fails.
2. Does each interface name its governing standard and version? An interface without a cited standard is either mis-drawn or belongs in B5.
3. Does the interface ship with two adapters, and does the second one differ enough to prove the first is not load-bearing? One adapter is a prototype, not an interface.
4. Can a caller integrate with nothing we wrote? If a client library of ours is required, the boundary is bespoke.
5. Is cost known before execution starts? Planning that spends is not planning.
6. Is the grading criterion hidden from the thing being graded? A visible criterion is a target, not a test.
7. Are budget, identity, policy, provenance, telemetry, errors, and idempotency applied by the platform with no opt-out? A caller who can decline one has found a hole.

## Vocabulary

Use these words with exactly these meanings. Mixing them is how boundaries drift.

| Word | Means | Not |
|---|---|---|
| Capability | Something the platform needs, named by what it does | A product |
| Standard | The published spec, with version, that governs a capability's interface | Our own shape |
| Interface | The contract the core imports for a capability | An implementation |
| Adapter | An implementation of an interface using a specific product | Part of the core |
| Core | Document, Planner, Graph, Judge, Ledger | Anything with an outward dependency |
| Seam | Dispatch and State, the two boundaries with no standard | Any other interface |
| Substrate | What runs today (PASS.md Part A) | The architecture |
| Composition | A workflow, loop, or agent assembled from skills and interfaces | A new interface |

## Claimed versus measured

Every factual statement carries one of two labels. **Measured** means a command was run against a live system or a test executed and the output is quoted or referenced. **Claimed** means it is believed, documented, or inferred. PASS.md A7 shows why: three designs looked correct on paper and were wrong on the host. Never upgrade a claim to a measurement by rewording it.

## Definition of done

A piece of work is done when three things exist:

- a machine-checkable criterion (a command, test, or query with an expected result)
- a deliberate breakage that makes the criterion fail, showing the check has teeth
- the measured output of both

A criterion nothing can fail is not a criterion (PASS.md C3). Recording only the pass is how A7 finding 2 happened.

## Products belong in one place

Products, versions, and hostnames appear only in adapter skills and in Part A quotations. Core skills, interface skills, and composition skills speak of capabilities and standards. When you catch yourself writing "LiteLLM" in a core skill, you have written the adapter into the core.

## How skills in this repo link

Skills are flat directories under `.claude/skills/` with a layer prefix in the name: `core-`, `cap-`, `xc-` (cross-cutting), `seam-`, `compose-`, `build-`. Every skill except this one has a `## Composes with` section listing, by name, the skills it depends on and the skills that build on it. Those links are the architecture's graph made visible, so keep them accurate. `docs/skill-graph.md` is generated from them; do not edit it by hand.

Load skills in order: this one, then the layer skill for the piece you are working on, then only the neighbors it names. Loading everything at once is how the vocabulary blurs.

## Where the layering came from

`docs/decomposition.md` is the Part C decomposition strategy: the ordered build sequence, the Dispatch and State first-cut designs, per-piece definitions of done with their breakages, the second adapters, and the undecided list with the evidence that would decide each item. It fixes which skills exist and in what order they are built. Change it before changing the skills it governs.
