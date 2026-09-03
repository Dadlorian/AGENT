# AGENT

The target architecture in `PASS.md` Part B, built as a set of linked Claude Code skills.

`PASS.md` is the source of truth. Part A is what runs today, verified. Part B is the greenfield target: a five-piece core, sixteen capability interfaces each governed by a published standard, seven cross-cutting guarantees the platform applies, and two seams (Dispatch and State) that have to be designed rather than adopted. Part C is the ask: a decomposition strategy.

## What is here

| Path | What it is |
|---|---|
| `PASS.md` | Current state and target architecture |
| `docs/decomposition.md` | The Part C decomposition strategy: build order, Dispatch and State designs, definitions of done with their breakages, second adapters, open questions |
| `docs/skill-manifest.json` | Every skill, its layer, wave, links, and definition of done. The contract the skills are built from |
| `docs/skill-graph.md` | Generated map of how the skills compose |
| `.claude/skills/agentic-stack/` | The root contract: vocabulary, the seven rules as tests, claimed versus measured, definition of done, layering |
| `.claude/skills/core-*` | One skill per core component: Document, Planner, Graph, Judge, Ledger |
| `.claude/skills/cap-*` | One skill per capability interface, naming its standard, today's adapter, and a second adapter |
| `.claude/skills/xc-*` | Cross-cutting guarantees: budget, identity, policy, provenance, telemetry, errors, idempotency |
| `.claude/skills/seam-*` | Dispatch and State |
| `.claude/skills/compose-*` | Assembling workflows, loops, and agents from the layers below |
| `.claude/skills/build-*` | Disciplines every author uses: definition of done with breakage, adapter pairs, evidence recording |
| `tools/` | Validator and graph generator |

## Using it

Open Claude Code in this repo. Skills load on demand: `agentic-stack` first, then the layer skill for the piece you are working on, then the neighbors it names under Composes with. Ask for a workflow, a loop, an adapter, or a component and the matching skills bring the platform's rules with them.

## Checking it

```bash
python3 tools/validate_skills.py     # links symmetric, no products outside adapter sections, manifest matches
python3 tools/skill_graph.py         # regenerate docs/skill-graph.md
```
