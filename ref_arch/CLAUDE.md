# Project conventions
- Any UI for monitoring or steering agents follows `skills/agentic-control-plane.md` and `Style Guide.dc.html`. Read both before building.
- Tokens are defined on `body` (dark) and `body[data-theme="light"]`; use `var(--*)` inline, never new hex values.
- Platform vocabulary comes from `uploads/PASS.md` and is used verbatim, with one errata: PASS.md's "cell" (the Firecracker microVM unit) is called **sandbox** in every surface; the unit of work assigned to a sandbox is a **task** (A2A). `cellplane-glossary.js` is the glossary of record (rendered by `Vocabulary.dc.html`); every new entity is added there first with its governing standard.
- Any HTTP surface is documented per `skills/api-reference.md`; `cellplane.openapi.js` is the single source of truth and `API Reference.dc.html` renders from it.
- Vocabulary renames applied per `Vocabulary.dc.html`: Judge → Evaluator; definition of done → acceptance criteria; landed → completed; tenancy Workspace → Project (`project_id`); "Workspace" means only the agent file workspace (AGENTS.md). API status values follow A2A TaskState with a `substate` extension.
- `archive/` holds superseded versions (Control Plane v1, v2, v2 review). Do not link to or edit them; `Control Plane v3.dc.html` is current.
