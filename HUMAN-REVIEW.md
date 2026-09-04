# Human review checklist

One pass over every folder, in the order below. Each folder gets four things: what it holds, the command that checks it by machine, what only a person can judge, and what a problem looks like. Nothing here asks you to trust a markdown file: every claim points at a command or a record you can open.

Findings go where the last section says. Do not edit generated files by hand (every one says so in its first lines); change the data or the tool and regenerate.

## 1. Before you start: the whole repo in six commands

Run these from the repo root. If any last line differs, stop and start the review there.

| Command | Proves | Last line today |
|---|---|---|
| `python3 tools/validate_skills.py` | every skill conforms to the schema and every quote is in the knowledge base | `28 skills checked, 0 errors, 0 warnings` |
| `python3 tools/kb.py verify` | the knowledge base still matches `PASS.md`, `TARGET.md` and the reference doc line for line | `kb verified: chains intact, ...` |
| `python3 tools/kb.py ledger-verify` | no run record was altered or dropped | `ledger verified: 208 records, chain intact` |
| `python3 tools/final_acceptance.py` | every measuring stick in `TARGET.md` T9 and T10 holds; runs all 28 harnesses | `15 of 15 hold` |
| `python3 tools/status_check.py --freshness` | `STATUS.md` is one clean table and no agent claim is stale | `freshness: 5 live rows, 0 claims, 0 stale` |
| `bash examples/end-to-end/test.sh` | the consumption example runs end to end | `passed 30, failed 0` |

`final_acceptance.py` takes a few minutes because it runs every harness gate. Add `--write` only when you want `docs/acceptance/final.json` re-stamped at the current commit.

## 2. Root files

| File | What it is | Look at | A problem looks like |
|---|---|---|---|
| `PASS.md` | The source of truth. Part A is what runs today, Part B the target architecture, Part C the questions. Every `F-` record is one row or item of it. | Does Part A still describe what is actually running on the host? Does Part B still say what you want? | You change a line here and `python3 tools/kb.py verify` fails until `python3 tools/kb.py build` is run and the skills that cite the changed row are re-validated. |
| `TARGET.md` | The measuring sticks, T1 to T10. Every numbered item is a `T-` record. | Is each stick still the one you want held? T9 is the scorecard, T10 the acceptance order. | A stick you no longer agree with is still enforced by a tool (search `tools/` for its id). |
| `OWNER.md` | Your corrections, one line each. Every agent reads it before working. | Are the five lines still the rules you want? | A rule you gave verbally that is not here will be forgotten by the next agent. |
| `STATUS.md` | The single view. Five columns, one statement per cell, live rows only. | The five live rows (14, 21, 37, 45, 64) are all waiting on you. Decide each or leave it Blocked with the reason. | A row whose Result you cannot reproduce with a command. |
| `STATUS-ARCHIVE.md` | Every Done row with the date and commit it closed at. | Pick three archived rows and reproduce their Result from the commands in this checklist. | A Result that the command no longer reproduces at HEAD. |
| `README.md` | The map of the repo. | Every number in it should come from a command in section 1. | A count in the README that a command does not print. |

## 3. `.claude/skills/` (28 skills)

Each skill is a directory: `skill.json` (the data, the only thing authored), `SKILL.md` (rendered from it, never edited), and `references/`: registries and usage notes, plus one rendered file per former skill folded into it at STATUS row 71 (`docs/fold/plan.json` says what folded where).

Run first:

| Command | Proves |
|---|---|
| `python3 tools/validate_skills.py --only <skill>` | one skill against schema, knowledge base and root contract |
| `python3 tools/render_skill.py .claude/skills/<skill> && git diff --stat` | the rendered `SKILL.md` on disk is what the data produces (empty diff) |
| `python3 tools/check_adapter_pairs.py --skills .claude/skills` | every `cap-` and `seam-` skill has a today adapter and a second adapter that differ on at least one axis |
| `python3 tools/skill_graph.py` | every `builds_on` name exists (`0 dangling builds_on edges`) |

Sample at least one skill per layer (`agentic-stack`, `core-components`, two `cap-`, `xc-guarantees`, one `seam-`, one `compose-`, one `build-`) and open `SKILL.md`; then open one file under its `references/` and check it says what the body's pointer claims. Judge, in this order:

1. **The description in the frontmatter.** It says when to load the skill. Would you load it for the task it names, and only then? A description that fires on every task is a defect; so is one that never fires.
2. **Two sourced rows.** Pick any two rows marked `sourced`. Run `python3 tools/kb.py show <id>` on the first id in the Evidence cell and confirm the quoted words appear in that record's `text`. The validator does this for every row; you are checking that the quote supports the statement, which no tool can.
3. **Two proposed rows.** A proposed row is this repo's own design. Does the text say so, and is it a design choice rather than a fact someone should have looked up? A proposed row that reads as a fact is a research gap.
4. **The definition of done.** Read `criterion`: it must be a command you can paste. `status: measured` means `tools/measure.py` ran it and `measured_run.commit` names the commit. Paste the criterion and compare with `expected`. `status: claimed` means nobody has run it; all 28 are measured, at commits before the fold; the next boundary re-runs them (STATUS row 37 says why live mode stays claimed).
5. **Adapters** (`cap-` and `seam-` only). The today adapter names what runs on the host per `PASS.md` B3; the second names a different execution model. `cannot` should be a real limitation, not a compliment.
6. **`builds_on` and `composes_with`.** Follow one link. The linked skill should add something this one does not restate.

A problem looks like: a quote not in the record; a proposed row written as a fact; a criterion with prose in it; a measured skill whose criterion fails at HEAD; a description that would load on any task; an ideal skill and its `-implement` sibling that say the same thing twice.

Open question for you: `state/grandfathered.json` lists every skill, which lets the validator keep restatement findings as warnings rather than errors, and lets `status: measured` stand without a run. Today no skill needs either exemption (0 warnings; every measured skill has a run). Emptying the list makes both rules hard errors from here on.

## 4. `kb/` (the knowledge base)

| File | Prefix | Holds | Rows |
|---|---|---|---|
| `facts.jsonl` | `F-` | one record per row of `PASS.md`, with its line range and hash | 109 |
| `target-facts.jsonl` | `T-` | one record per numbered item of `TARGET.md` | 47 |
| `reference-facts.jsonl` | `REF-` | `docs/reference/composable-plan.md`, an example, never a fact | 265 |
| `research.jsonl` | `X-` | web search records merged from `kb/research/*.jsonl` (60 files) | 660 |
| `entities.jsonl`, `edges.jsonl` | `E-`, `R-` | the things the facts name and the typed links between them | 184, 109 |
| `decisions.jsonl` | `D-` | decisions lifted from `docs/decomposition.md` by line | 110 |
| `architecture.jsonl` | `A-` | the blueprint imported as entities and edges | 803 |
| `ledger.jsonl` | `L-` | one hash-chained record per run, ceremony or phase close, with commit and dirty flag | 265 |
| `meta.json` | | source hashes and chain heads | |
| `ceremonies/` | | the review, improve, sourcing and measure records (section 5) | 98 |

Run first: `python3 tools/kb.py verify`, `python3 tools/kb.py ledger-verify`, `python3 tools/kb.py stats`.

Look at:

- **Research records.** Every `X-` record is `search-only`: a search result, never a fetched page. Open three (`python3 tools/kb.py show X-cap-errors-001`) and check the `url`, `title` and `query` look like a real search result and not an invention. Open the url in a browser; the environment could not. This is the gap behind STATUS rows 14 and 45.
- **The ledger.** `tail -3 kb/ledger.jsonl`. Each record names the git commit and whether the tree was dirty. A phase-close record with `dirty: true` means the close happened before the commit; the commit it names should be the parent of the closing commit.
- **`kb/research/`.** One file per skill or lens. A record without a `query` is one nobody searched for.

A problem looks like: `verify` fails (a `.jsonl` or `PASS.md` was edited by hand); a research record whose url does not resolve to the title recorded; a ledger gap.

## 5. `kb/ceremonies/` (the review records)

Every phase since row 59 ran the ceremony in `docs/acceptance/ceremony.json`: claim, source, measure, plant, review, plant check, improve, lessons, close. Records are named by the STATUS row they served (`61-review-c.json`). Older records (`ceremony-01` to `ceremony-11`, `reconcile-`, `consolidation-`, `architecture-`) predate that rule and the plant step.

Run first:

| Command | Proves |
|---|---|
| `python3 tools/check_ceremony.py kb/ceremonies/<row>-review-<part>.json kb/ceremonies/<row>-improve-<part>.json` | every finding was applied or declined exactly once and every touched file exists |
| `python3 tools/ceremony_check.py` | the eleven loop ceremonies validated and fed the loop; prints the findings-per-skill trend |

Two pairs print counts that are not defects, so you know them in advance: `28-harness-1` shows two unresolved findings, which were the two planted defects that record lists under `skipped_plants`; `62-improve-a` shows two unknown ids, `MECH-restate` and `MECH-criterion`, which are validator checks the improver applied beyond the review.

Look at, for one review and improve pair per phase (59, 60, 61, 62):

- **The reviewer and the improver.** The `reviewer` and `improver` fields name the model. Every reviewer to date is a model, not a person; this checklist is the first human pass.
- **Plants.** Each review record since row 59 has `plants_caught`. `61-review-c-discarded.json` is a review that missed both plants and was discarded; `61-review-c.json` is its re-run. A kept review that caught neither plant is a defect.
- **Findings.** Each has `evidence`. Pick two and check the evidence against the skill as it is now; the improve record's `applied` entry names the files that changed.
- **Declined findings.** Each `declined` entry has a `why`. Do you agree? A decline you disagree with is a finding for the record in section 11.
- **`64-structure-review.json`.** The independent review of the skill layout; STATUS row 64 waits on your choice among its options.

## 6. `harness/` (28 harnesses)

`harness/plan.json` is the list; `harness/README.md` describes the first five in depth and the shared caller-line measurement. Each harness directory holds `interface.py` (the capability interface, no product names), `adapters/dryrun.py`, `adapters/live.py`, `adapters/second.py`, `call.py` (the minimal caller), `conformance.py` (the cases every adapter passes), `test.sh` (the gate), `README.md` (a step table) and `provenance.json` (what is measured, what is claimed, which kb ids).

Run first, for any harness:

| Command | Proves |
|---|---|
| `bash harness/<name>/test.sh` | the gate: last line `passed N, failed 0` |
| `ADAPTER=dryrun python3 harness/<name>/call.py` then `ADAPTER=second python3 harness/<name>/call.py` | the same caller code runs on two execution models |
| `python3 harness/<name>/conformance.py --adapter dryrun --adapter second` | both adapters pass the same cases |
| `grep -ril "firecracker\|temporal\|litellm\|langfuse\|goose" harness/<name> \| grep -v adapters/` | no product name outside the adapters (expect no output; `provenance.json` and `README.md` may name the product as today's tool) |

Look at:

- **`provenance.json`, `measured` against `claimed`.** Every harness records live mode as claimed: `adapters/live.py` has never run against the host from a session (STATUS row 37). Decide whether to grant that access.
- **The second adapter.** Open `adapters/second.py`. It should implement the interface a different way, not subclass today's adapter and override nothing.
- **The breakage.** `test.sh` applies one deliberate breakage to a copy and asserts the gate fails. Find that section and confirm it asserts failure rather than only printing.
- **`call.py`.** Below the `>>> CALLER CODE` marker is what a caller writes. If it names a file inside an adapter's storage, the interface leaked.

A problem looks like: a green gate whose conformance run has zero cases; a second adapter that is today's adapter renamed; a product import in `interface.py`.

## 7. `docs/`

| Path | Generated by | Check with | Look at |
|---|---|---|---|
| `acceptance/matrix.md`, `matrix.json` | `tools/acceptance_check.py` | `python3 tools/acceptance_check.py --check` | One row per stack element from `PASS.md` B3, five sticks each. The Standard stick reads `absent` on all 16 rows because `absent.json` records your decision that page fetch is blocked. Confirm you still accept that. |
| `acceptance/absent.json` | you | read it | Every entry is a stick you chose not to hold and the reason. |
| `acceptance/final.json` | `tools/final_acceptance.py --write` | compare its `commit` with `git rev-parse --short HEAD` | The scorecard at one commit. Re-run with `--write` after any change that could move a stick. |
| `acceptance/ceremony.json` | authored | read it | The nine steps every phase ran. Is any step missing from what you want a phase to prove? |
| `guides/<element>.md` (16) | `tools/render_guide.py` | `python3 tools/render_guide.py --check` | Pick one and follow its step table by hand. Every guide pulls from the skill data and the harness README; a step that fails is a harness defect. |
| `architecture/blueprint.json` | authored from the kb | `python3 tools/blueprint_check.py` | 288 entries, 276 sourced, 31 gaps. Read the `gaps` list: each is a place the knowledge base had nothing. |
| `architecture/load-path.md` | from `kb/ceremonies/reconcile-01-review-xc.json` | read it | The skills a task loads per door, against the budget of 11 (T9.5). Worst door today is 9. |
| `skill-graph.md` | `tools/skill_graph.py` | open it on GitHub | Each focal group states its edge count against the mermaid budget. A group that does not render is a defect. |
| `skill-manifest.json`, `decomposition.md` | authored | `python3 tools/manifest_facets.py check` | The plan the skills were built from: 101 manifest entries plus the root. `decomposition.md` is where `D-` records come from. |
| `research/*.json` | authored by research agents | read | The three lenses (cross-structure, end-to-end, entry-composition) and the gap lists. Historical; the `X-` records are the citable form. |
| `reference/composable-plan.md` | external | read | One team's example, cited as `REF-`. Never a fact. |

## 8. `examples/end-to-end/`

Run `bash examples/end-to-end/test.sh` (30 checks), then `python3 examples/end-to-end/run.py --entry examples/end-to-end/entries/human.json` and read `examples/end-to-end/out/ledger.jsonl`. `provenance.json` there lists the `T-` and `F-` ids the example claims to satisfy; pick two and judge whether it does. The four entries under `entries/` are the four doors; each should normalise into the one envelope in `schemas/entry.schema.json`.

## 9. `state/`

| File | What it is | Look at |
|---|---|---|
| `briefs/` | One-file briefs per ceremony step (`source`, `measure`, `review`, `improve`) and the `captain` brief that gathers context once for a crew. `context-61.md` and `context-62.md` are the captain's context for those rows. | Is the method in each brief the one you want? A brief is the only instruction a crew member gets. |
| `author-brief.md` | What every authoring agent reads, with lessons 59 to 61 folded in. | Rules here are the ones that actually shape skills. |
| `lessons.jsonl` | One row per ceremony: what recurred and the sharper check that now catches it. 17 rows. | Does each lesson name a check that exists in `tools/`? A lesson without a tool will recur. |
| `agent-scopes.json` | Live scope claims. | Must be `{}` when no agent is running. |
| `grandfathered.json` | Skills exempt from two validator rules (section 3). | Decide whether to empty it. |
| `loop.json`, `loop-args.json`, `loop-workflow.js`, `author-prompt-round.md` | The earlier section loop that built the first 99 skills. Historical. | Nothing to review; kept so the loop ceremonies can be read in context. |

`state/plants.json` is git-ignored and must not exist between ceremonies; if it does, a plant was never removed (`python3 tools/plant.py unplant`).

## 10. `tools/` and `schemas/`

Every tool prints its usage when run with no arguments. Read the docstring of each one you relied on above and confirm it does what this checklist says it does.

- `tools/measure.py` is the only writer of `status: measured`. Confirm with `grep -ln '"measured"' tools/*.py`; a second writer would be a defect.
- `schemas/skill.schema.json` is what the validator enforces; `schemas/research.schema.json` shapes every `X-` record. A change to either re-validates everything.
- `tools/scopes.py` refuses a claim whose label does not start with a live STATUS row id, which is how your naming rule is enforced.

## 11. Recording what you find

- **A rule the agents got wrong:** one line in `OWNER.md`, dated, newest last.
- **A finding against a skill, harness or record:** write it as a review record, `kb/ceremonies/<row>-human-review.json`, using the finding shape the model reviews use (`id`, `skill`, `location`, `severity` of block, fix or nit, `kind`, `evidence`, `fix`), and open a STATUS row for it. An agent then runs the improve step and `tools/check_ceremony.py` closes the pair.
- **A decision on a Blocked row** (14, 21, 37, 45, 64): change its Status and Result in `STATUS.md`. That is the whole mechanism; agents read the table.
- **A stick you no longer want held:** add it to `docs/acceptance/absent.json` with the reason, and rerun `python3 tools/acceptance_check.py`.
