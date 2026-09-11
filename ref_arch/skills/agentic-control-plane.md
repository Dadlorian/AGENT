# Skill: Agentic Control Plane UI

Use when designing or extending any surface that monitors or steers agent fleets in this project. Companion files: `Style Guide.dc.html` (human handoff: tokens both themes, type, states, glyphs, ladders, components, views, geometry), `cellplane-tokens.css` (the `--*` tokens, dark on body, light on body[data-theme="light"]), `cellplane-data.js` (ICONS paths, LADDERS, LADDER_HUMAN, LENSES, STATUS, PROBLEM_TYPE), `Control Plane v3.dc.html` (live implementation), `Control Plane API Guide.dc.html#router1` (integration contract), `Reference Model.dc.html` (MVP-SCALE platform reference architecture, 1672×941, source `uploads/MVP-SCALE-AGENT-REF-MODEL.png`).

## Job to be done
The user triages, not codes. Every screen answers, in order: how many are stuck → why → what one action fixes it. Fleet scale is hundreds of tasks; the phone is a first-class client.

## Vocabulary (verbatim from the platform, never softened)
Task (one microVM running one unit of work) · Task specification (intent + acceptance criteria + steps) · Planner · Evaluator (verdict PASS/FAIL) · Ledger · Dispatch · model classes `f-` free local, `i-` interactive metered, `b-` batch, `cli-` coding CLI · `i-escalate` · `session/cancel` · approve.service · ceiling (budget).

## States (fixed hue, fixed meaning)
running `--run` muted green · waiting `--wait` amber (self-resolving) · stuck `--stuck` orange (needs operator) · parked `--park` muted blue (approval gate) · done/cancelled `--done` grey. Orange `--accent` is the one attention hue: stuck, blocked stage, primary action, "n need you" pill. Selection = `--text` border. Colour is never decorative.

## Stuck reason → suggested action
Tool timeout → Restart sandbox · Evaluation FAIL repeated / identical output → Redefine · No progress / loop → Nudge, then Escalate · Budget ceiling → Extend · Policy refusal or approval gate → Approve / Return / Reject. Show the single mapped action on the card; the full set lives in the detail sheet.

## Recovery model (self-healing, bounded)
Every problem type has a ladder in `LADDERS`: ordered rungs with a max per task (tool-timeout: restart×2 → reassign; budget-ceiling: extend×1 → split; no-progress: nudge → escalate; evaluation-failed: nudge → rollback; stalled: nudge → restart; governance types: no rungs). Rungs fire automatically per workflow (toggle in Playbooks), are logged as actor `ladder:<type/verb>`, never spend past the budget ceiling except the single Extend rung, and are scored resolved/recurred after `OUTCOME_AFTER` ticks. When rungs are spent the task is `exhausted` and shows the person glyph; the human verb for that type (`LADDER_HUMAN`) is highlighted in the sheet. A human action resets the ladder. Outcomes accumulate in `effect` and surface as "What worked" on Loop and per-type stats on Playbooks; that is the input to the self-improvement loop.

## Action set and mechanism copy
Nudge (re-send intent + acceptance criteria as a new turn) · Redefine (edit Task specification, replan, resume from checkpoint) · Escalate (class `i-escalate`) · Raise ceiling (+50%) · Restart sandbox (fresh sandbox (microVM), same step) · Reassign (another model class) · Cancel (`session/cancel`) · Approve / Reject / Return with note (parked only) · Rollback (previous checkpoint, redo step) · Split (two children, half ceiling) · Skip dependency (decouple) · Grant scope (one-time, on policy denial) · Answer (agent asked a question). Every button shows label + one-line consequence.

## Views (one nav, seven views)
Grouped top nav — FLEET Tasks·Board / RUN Lenses·Activity / MONEY Cost / IMPROVE Loop·Rules — plus an orange "n need you" pill. Breadcrumb row: WORKLOAD chips (all, each workflow, saved groups) + counts. Tasks = card grid with fleet map and group-by (reason/stage/model). Board = kanban by plan stage Intake → Build → Verify → Gate → Done. Lenses = one failure mode per card (over ceiling, timed out, Evaluation FAIL, no progress, policy refused, awaiting approval, trace unlinked, waiting) with a fix-all. Cost = per class + per workflow against ceiling. Loop = observe→detect→propose→apply→measure over recurring stuck reasons; proposals edit the Task specification or dispatch config, never auto-apply; a recommendation can become a Rule. Activity = alerts (per-kind prefs) + command ledger (actor you|rule:<id>, policy, hash, compensated). Rules = standing responses to problem types, bounded fires per task, logged like operator commands, never edit a Task specification.

## States added in v2
stalled (amber, needs operator): a wait past STALL_AFTER; promoted from waiting. Dependency: task shows ⇠ upstream id; the lens "Blocked on a task" points at the upstream. Verdict detail: acceptance criteria rendered as clauses, failed clause marked ✕.

## Safety
Destructive bulk (cancel/reject on >1 task) requires a confirm sheet. Every non-destructive command gets an 8s Compensate bar (⌘Z). Pause/Resume pauses dispatch per workflow without cancelling. Offline: banner, stale age in the live pill, commands queue and log as policy=pending.

## Mobile additions
Swipe right on a card = suggested fix, left = cancel. URL carries view/wf/status/lens/q. Skeleton on load; explicit empty states with a clear-filters action.

## Density
Desktop (≥760px) renders tasks as 44px rows: dot · id · workflow + one line (reason when blocked, else step) · model · progress+spend · age · icon cluster. Mobile renders cards with the same icon cluster in the header. One glyph per row: the suggested action for the state, filled orange (stuck → mapped verb, stalled → nudge, parked → approve); healthy/done rows show only a faint open chevron. All other valid actions live in the detail sheet, each with the same glyph beside its label. Glyph paths are the single `ICONS` map in cellplane-data.js; never draw a second variant. Never repeat status as pill + strip + button on one card; the dot, the left rule and the line carry it. Board cards: one line for healthy tasks, two for blocked.

## Layout
Sticky: brand row, then status count chips (count first, label second, tap to filter, tap again to clear). Workflows as a horizontal card row with a stacked state bar. Toolbar: search, map toggle, Select, "Nudge all stuck · n". Fleet map: 12px squares per task, filtered-out at 12% opacity. Tasks: `auto-fill minmax(300px,1fr)` grid, sorted stuck → parked → waiting → running → done. Detail: side panel ≥760px, bottom sheet below; includes prev / "Next stuck" for continuous triage. Bulk: floating bottom bar when Select is on.

## Type and surfaces
Instrument Sans for prose (700 titles, 600 labels, 400 body). JetBrains Mono for ids, model classes, money, counts, acceptance criteria, and all uppercase tracked labels/pills (10px, .1em). Near-black `--bg`, surfaces `--surface / --surface2 / --surface3`, hairline `--border`, radius 4 inset / 5 control / 6 card / 8–10 sheet. Cards get a 2px top border in the attention hue when blocked; reason strips get a 2px left rule in the state hue. Pills: mono uppercase outlined. Shadow only on sheets and floating bars. No gradients, no icons for status, no emoji.

## Motion budget
Sheet 220–280ms ease-out · toast 200ms · live dot 1.6s pulse · running stripe 1s linear. State changes snap.

## Mobile rules
Hit targets ≥44px · actions reachable by thumb (bottom sheet, floating bar) · horizontal scroll rows instead of wrapping · safe-area insets respected · nothing depends on hover.

## Anti-slop checklist
No hero gradients · no card-per-stat dashboards with icons · no vanity metrics · reasons are measured ("timed out 3× against 45s ceiling"), not interpreted ("seems slow") · copy names the mechanism.

## Code
Any code, path, verb, id or JSON shown to the reader follows `skills/api-reference.md` § Code: inline `<code>`, blocks through `cellplane-code.js` with language label, line numbers and palette colouring. Never a plain grey slab.

## Tables
All tables use `.cp-table` from `cellplane-tokens.css`; all single-object descriptions use `.attr`. No page defines its own `table/th/td` rules. Body cells are UI 13; identifiers are `<code>`; a cell that is only identifiers is `td.fields`.
