# Bridge — standards vocabulary & reference model work

Handoff for continuing the work from session `session_01EJDuHajL33cqyQg6dvta3T` (2026-09-08/09).
Everything below is checked against the actual repo state at commit `6da1205`, not recalled from
conversation — a fact here is either on disk or explicitly marked as discussed-but-not-built.

## What's real and committed

- `standards/<id>/standard.json` — all 41 standards migrated out of the old
  `docs/standards/standards.json` monolith, one file per standard, verified byte-identical render
  of `STANDARDS.md`/`JOURNEY.md` before and after. `standards/registry.json` and
  `standards/journey.json` hold the shared top-level data. `tools/standards.py` reads from this
  tree now (`load_registry()`); its CLI (`check`/`render`) is unchanged.
- `standards/archive/` — frozen, hash-verified copies of the pre-migration
  `docs/standards/standards.json` and `docs/journey/journey.json`. The **originals are still on
  disk in `docs/`, untouched** — deleting them is a separate, later, explicitly-approved step,
  not done yet.
- `standards/agent-client-protocol/standard.json` has real `acronym` and `not_to_be_confused_with`
  fields (disambiguating Zed/JetBrains' Agent Client Protocol from IBM's now-archived Agent
  Communication Protocol, cited to two real URLs). This is the only standard with either field
  populated.
- Live `WebFetch` against real spec pages works in an interactive session — proven against
  `agentclientprotocol.com/protocol/v2/schema.md`, which returned ~90 real type/enum/method names
  (StopReason, RequestPermissionOutcome, ContentBlock types, ToolCall, etc.). This is the first
  evidence in this repo's history that `STATUS.md` rows 14 and 45 ("standard version fetch
  blocked") may not hold in every execution context — **scoped to this interactive session only**,
  not proven for the harness's own isolated environment.
- Governance/maturity research (real, from live web search, not yet written into any file):
  MCP and A2A are both foundation-governed under the Linux Foundation's Agentic AI Foundation
  (AAIF), broad independent multi-vendor adoption. AG-UI and Agent Skills specification have broad
  adoption but are still single-company-stewarded (CopilotKit; Anthropic) and young. ACP (Zed) is
  real and growing but its v2 spec is currently in Draft.
- A published reference-model Artifact —
  https://claude.ai/code/artifact/bdec9640-bd78-40f5-a6b6-81473ab10679 — showing this platform's
  real 27 named elements (18 `cap-` skills, 2 seams, `core-components`, `xc-guarantees`,
  `compose-workflow`, stripped of file-naming prefixes) as a hub-and-flanks diagram: **Entries**
  and **Reach** as peers either side of the **Agent** hub (split only where a real sequence exists:
  Plan & Orchestrate before a cell exists, Runtime & State once it does), **Guarantees &
  Observability** as one rail underneath. Not a layered depth stack — that was tried and rejected
  (see "What was tried and reverted" below).

## What was designed in conversation but never written to disk

- **No `vocabulary.json` file exists anywhere.** The ACP term extraction (StopReason, ToolCall,
  RequestPermissionOutcome, ContentBlock, session methods — from the real fetch above) was
  discussed and shown in chat but never saved to `standards/agent-client-protocol/vocabulary.json`.
  Vocabulary work for A2A, AG-UI, MCP, and Agent Skills specification was never started at all.
- **No `kb/research.jsonl` record has `status: "fetched"`** — confirmed by grep, count is 0. The
  fetched-status research record for ACP (which would be the first non-`search-only` record in
  this repo's history, and the actual evidence needed to reconsider STATUS rows 14/45) was never
  created. `tools/build_egress_log.py` already supports this mechanically the moment a record with
  `status: "fetched"` exists — this is a small, well-understood next step, not a design problem.
- **No `schemas/standard.schema.json` or `schemas/vocabulary.schema.json`.** No
  `tools/validate_standards.py`. Schema and validator work for the new folder structure hasn't
  started.
- **No `kb/edges.jsonl` records for the new relationship types** (`applies_to_step`, `aligns_with`,
  `implemented_by`) that were designed to replace the embedded `journey` field on `standard.json`
  and to model the cross-standard vocabulary alignment matrix. The `journey` field is still present
  on every `standard.json` (kept deliberately, to preserve the byte-identical render proof) and
  hasn't been migrated to edges yet.
- **`xc-guarantees` still cites no standard and is still not listed in `STANDARDS.md`'s own "Areas
  with no open standard" table** — confirmed by grep just now. `cap-state-persistence`,
  `cap-evaluation`, `cap-durable-execution`, and the `cap-isolation` cell-lifecycle gap are all
  honestly disclosed there; `xc-guarantees` is the one real, still-undisclosed gap this whole
  exercise surfaced. Independent of anything else here, this is a one-line fix worth doing.
- The real cross-domain standard connections identified by hand (not yet in any `aligns_with`
  edge): **A2A** connects Entries → Agent (Runtime & State) → Guarantees & Observability;
  **MCP** connects Reach → Guarantees & Observability; **GenAI semantic conventions** connects
  within Guarantees & Observability (Telemetry/Evaluation). Agent Client Protocol, AG-UI, and
  Agent Skills specification are real but stay inside one grouping each — not cross-cutting by the
  same test.

## What was tried and reverted (so it isn't retried)

1. A seven-column "journey" layout (Ask/Bound/Contain/Do/Evidence/Finish/Grow, then relabeled to
   industry terms like Admission Control/Provisioning/Execution) — dropped because it's a temporal
   axis, not a modularity axis, and real capabilities span multiple time-columns, producing false
   coupling.
2. `STANDARDS.md`'s own 11-axis registry categories (agent-protocol, tool-access, model-access,
   observability, isolation, identity, provenance, formats, policy, workflow, governance) as a
   capability grouping — dropped after checking the real data: 3 capabilities span multiple axes,
   3 have no axis at all (no standard cited), and the "workflow" axis contains one declined
   standard unrelated to `compose-workflow` itself. Legitimate for categorizing standards; wrong
   tool for grouping capabilities.
3. A 5-layer "Consumers → Experience/Orchestration → Core → Data & Integration → Infrastructure"
   depth stack with Governance/Security as edge bars — a generic enterprise-architecture template,
   force-fit onto a system that doesn't have that shape. An agent is a loop (plan → act → observe →
   replan), not a one-directional request pipeline through discrete depth tiers; forcing it into
   one produced "arbitrary layers" that didn't reflect real dependency structure. Superseded by the
   hub-and-flanks model above, which matches both Cloudflare's own agent-platform diagram and the
   classical sense→decide→act framing in agent architecture literature.
4. Three hand-coded raw-SVG diagram attempts with manually computed pixel coordinates — abandoned
   for CSS Grid/Flexbox after two confirmed overlap/text-bleed bugs from hand arithmetic. The
   published Artifact is CSS-laid-out, not SVG-positioned.

## Known-good facts worth not re-deriving

- 18 `cap-` skills + 2 seams (`seam-dispatch`, `seam-state`) + `core-components` +
  `xc-guarantees` + `compose-workflow` = 23 framework-runtime elements (`compose-improvement-loop`
  and the 4 `build-*` skills are excluded — they're the meta-engine that authors this repo's own
  skills, not part of the platform they describe).
- Real dependency depth (`builds_on`, filtered to drop `agentic-stack`/`build-*` authoring-only
  deps): zero-dependency leaves are `cap-errors` (used by 20 of 23 others), `cap-model-access`,
  `cap-document-validation`. Most framework-coupled: `seam-dispatch` (11 real deps),
  `compose-workflow` and `xc-guarantees` (8 each).
- Real per-capability standard citations (from each skill's own `contract.standards`), already
  separated into agentic-specific (Agent Client Protocol, A2A, MCP, AG-UI, Agent Skills
  specification, GenAI semantic conventions) versus table-stakes (JSON Schema, RFC 9457,
  CloudEvents, OpenAPI/AsyncAPI, RFC 5545, OAuth2 token exchange, SPIFFE, OCI Runtime Spec,
  Idempotency-Key convention, RFC 9162, RFC 8785, in-toto/DSSE/SLSA, Rego/OPA, OTLP) — the
  agentic/table-stakes split is real and worth preserving in any future work, it's not a stylistic
  choice.

## Starter prompt for a new session

```
Read bridge.md at the repo root first — it's a handoff from a prior session covering standards
vocabulary research and a reference-model diagram for this platform's real architecture. Don't
re-derive anything it already states as verified; do re-verify anything it flags as "designed but
not written to disk" before building on it, since none of that exists yet.

Pick up with whichever of these you want to prioritize, they're independent:

1. Close the fetched-status gap: write standards/agent-client-protocol/vocabulary.json (the ACP
   term extraction is described in bridge.md, re-fetch agentclientprotocol.com/protocol/v2/schema.md
   to get it fresh rather than trusting the bridge doc's paraphrase), add the matching
   kb/research.jsonl record with status "fetched" (schema at schemas/research.schema.json already
   supports this), run tools/build_egress_log.py to generate its egress-log entry, then decide
   with the owner whether STATUS.md rows 14/45 should change given this is the first fetched
   (not search-only) record in the repo's history.

2. Extend vocabulary.json + governance/maturity research (bridge.md has the findings already) to
   A2A, AG-UI, MCP, and Agent Skills specification, the same way ACP was done.

3. Fix the xc-guarantees disclosure gap in STANDARDS.md's "Areas with no open standard" table --
   small, independent, one line.

4. Build schemas/standard.schema.json, schemas/vocabulary.schema.json, and
   tools/validate_standards.py (mirror tools/validate_skills.py's hand-rolled style, no jsonschema
   package available).

5. Model the real cross-domain standard connections (listed in bridge.md) as kb/edges.jsonl
   records with new rel types (applies_to_step, aligns_with, implemented_by), replacing the
   embedded `journey` field on standard.json once the edges are proven equivalent.

Whatever you pick, verify against the actual files before asserting anything is done -- this
session's main lesson, repeated many times, was catching claims that sounded right but weren't
checked against what's actually on disk.
```
