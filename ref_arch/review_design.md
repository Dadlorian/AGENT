# Control Plane v2 — Review

Seven lenses, one pass each. Every item has an id. Reply with ids and a verdict (`yes` / `no` / `later`) and I'll apply the yeses in one turn. Defaults shown in brackets are what I'd do if you say "your call".

Severity: **H** breaks a rule in the style guide or blocks the operator · **M** friction or inconsistency · **L** polish · **D** delight (new)

---

## 1. Toast and undo noise

- **R01 · H** With self-healing on, rule toasts fire constantly ("Rule · Nudge · 1 cell" ×3 stacked in every screenshot). They cover the fleet map, board column and lens cards. Operators will learn to ignore all toasts, including their own. [Coalesce rule toasts into one live pill in the header ("Ladder · 3 fixes in the last minute") and reserve stacked toasts for operator actions.]
- **R02 · M** Undo bar and Select bulk bar occupy the same bottom-centre slot; when both are live the undo bar covers the bulk actions. [Stack undo above bulk, or move undo into the toast column.]
- **R03 · L** Toasts sit bottom-right at 360px max; on desktop they overlap the last board column. [Anchor to the header's right edge instead.]

## 2. Consistency with the style guide

- **C01 · H** Board column health bar and count layout differ from workload cards: number on the right of the bar in Board, below the bar in workload cards. [Match workload cards: stacked bar, then a mono meta row.]
- **C02 · M** Board "IN PROGRESS" pill wraps to two lines at column widths under 200px (see Intake, Build). [Shorten to `ACTIVE`; keep `n BLOCKED`, `n NEED YOU`, `LANDED`.]
- **C03 · M** Cost trend cards and Loop trend cards are the same component at two sizes (28px vs 22px sparkline). [One size, 24px, shared.]
- **C04 · M** Lens cards use a bar chart per workload with no labels; the Cost health cards use labelled mono stats. Same data density, different idiom. [Give lens bars a hover title and a faint workload initial under each bar, or drop the bars and show "top workload · n".]
- **C05 · L** "Nudge all" in a Board column is orange text inline with the spend; everywhere else a bulk fix is a button. [Make it a 28px outlined glyph button in the column header.]
- **C06 · L** Playbooks page subtitle is two lines; every other view is one. [Cut to "What the platform tries on its own per problem type, in order and bounded. Past the last rung the cell waits for you."]
- **C07 · L** Loop findings use a solid orange top rule; style guide reserves top rules for workload/lens cards and left rules for row/reason panels. [Left rule.]

## 3. Information hierarchy

- **H01 · H** The "n need you" pill (header, right) is the most important number on the page and is the furthest from the eye path; it's also off-screen at 900px because the header scrolls horizontally. [Pin it as the first element after the brand, before the nav groups.]
- **H02 · M** Status chips repeat on Cells, Board and Lenses with identical counts; on Lenses they duplicate the lens counts directly below. [Hide chips on Lenses.]
- **H03 · M** Cells page shows workload cards, group-by toolbar, fleet map, then the list. On a laptop the first cell row is below the fold. [Collapse the fleet map by default when a workload is selected; keep it for "All".]
- **H04 · L** Page title (26px) + one-line subtitle spends 60px per view repeating what the nav tab already says. [Drop the title, keep the subtitle as a 13px muted line under the breadcrumb row.]

## 4. Operator flow (stuck → fixed)

- **F01 · H** "Next stuck ›" in the sheet cycles through the current filter but doesn't tell you where you are ("3 of 12"). [Add position; disable when none left.]
- **F02 · M** After a bulk fix, selection clears and Select mode stays on with "0 selected". [Exit Select mode after a bulk action.]
- **F03 · M** Ladder history in the sheet shows RESOLVED for rungs that fired but the cell is still stalled ("Nudge · resolved", "Restart · resolved", yet exhausted). Reads as contradictory. [Label per-rung outcome as `held 12 ticks` / `recurred`, and only the final state as resolved.]
- **F04 · M** Redefine panel pre-fills the DoD but not the failed clause; the operator has to find it in the clauses list above. [Pre-select the failed clause's text in the textarea.]
- **F05 · L** Keyboard: Esc closes, ⌘Z undoes, but there's no `j/k` for next/prev stuck or `n` for nudge inside the sheet. [Add j/k/n/e/x with a one-line hint at the sheet footer.]

## 5. Mobile

- **M01 · H** Header row scrolls horizontally with nav groups, live pill, alerts, theme, Guide, API, "need you". Seven targets in a 390px viewport, most off-screen. [Two rows on mobile: brand + need-you + alerts; then nav as a segmented scroller. Move Guide/API/theme under a `…` menu.]
- **M02 · M** Swipe right = suggested fix is undiscoverable; the subtitle explains it once. [First-run hint on the first blocked card: a 2s peek animation of the glyph sliding out.]
- **M03 · M** Bottom sheet has no drag-to-dismiss; only the × and scrim. [Drag the grabber down 80px to close.]
- **M04 · L** Fleet map at 11px squares is a dense tap target on a phone. [Hide the map below 760px unless toggled.]

## 6. Data and honesty

- **D01 · M** Trend deltas are labelled "· 40 ticks"; ticks mean nothing to an operator. [Show wall-clock: "· last 56s" using tickMs.]
- **D02 · M** Cost health thresholds (err > 12%, p50 > 1600ms, queue > 12) are invisible; DEGRADED appears without saying why. [Show the breached metric in orange (already done) and add the threshold in the hint: "err 2.9% · limit 12%".]
- **D03 · L** Model-class health marks `f-` DEGRADED on latency alone; local GPU latency is expected to be higher. [Per-class thresholds.]
- **D04 · L** "$ per done" shows `—` until the first completion; fine, but "first-pass 91%" appears in Loop before any Document edit, which reads as the loop already working. [Label as "baseline" until the first Apply.]

## 7. Delight

- **X01 · D** When a stuck cell resolves (yours or ladder), pulse its row's left rule green once (600ms) before it re-sorts. Makes the fix visible without a toast.
- **X02 · D** Breadcrumb workload chips show a 6px blue square when held; add the same square in orange when a workload has ≥1 stuck cell so triage starts from the breadcrumb.
- **X03 · D** Fleet map: hovering a cell row highlights its square (outline) and vice versa. Already one-directional (open → outline); make it hover-linked.
- **X04 · D** "All clear" state: when need-you is 0, replace the Cells subtitle with "Nothing needs you. Last fix 4m ago · ladder handled 12 today." Operators should be able to see that idle is earned.
- **X05 · D** Sheet header: show the cell's workload as a tinted chip next to the id so you never lose context while cycling Next stuck.

---

### Suggested first batch (if you want my picks)
R01, H01, C01, C02, F01, F03, M01, D01, X01, X04.
