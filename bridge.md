# Bridge — 2026-09-10

Handoff. Supersedes the 2026-09-08/09 version entirely. `HANDOFF.md` covers the same ground from
one session earlier and is now redundant with this file.

**Every figure here was measured when written. Re-run the command before trusting it.** The most
expensive mistakes of the last two sessions were confident restatements of numbers that had moved.

---

## 1. Where the system is

### Measured state

| | |
|---|---|
| Research corpus | **932 records — 158 fetched, 767 search-only, 7 blocked** |
| Reference model | 40 cards, 19 built / 21 planned, **15 recorded corrections** |
| Card profiles | **27 of 40**, 365 individually verified citations, 119 recorded gaps |
| Knowledge pool | **25 documented · 2 unread · 13 undocumented** |
| Examples | `archived/` (the old seven), `reference/` (empty, structure defined), `end-to-end/` |
| STATUS | 11 live rows, 0 stale |

### Gates — all green except two, both recorded

```
python3 tools/validate_skills.py            29 skills, 0 errors, 0 warnings
python3 tools/kb.py verify                  chains intact, rebuild identical
python3 tools/kb.py ledger-verify           322 records
python3 tools/validate_card_profiles.py     27 profiles, 0 errors
python3 tools/card_profile_test.py          10/10 (9 planted defects caught)
python3 tools/check_card_example_map.py     40 entries, 0 errors
python3 tools/extract_reference_model.py --check   14/14
python3 tools/reconcile_egress.py           RECONCILED
python3 tools/status_check.py --freshness   11 rows, 0 stale
python3 tools/knowledge_pool.py             regenerates the pool view
python3 tools/standards.py check            10 errors  <- row 77, journey names archived paths
python3 tools/verify_snippets.py --check    drift 39   <- all `read`-field only, no citation uses them
```

---

## 2. What was found, and why it matters

Two sessions of building checks that had never existed. Every defect below was found by a machine
check, not by suspicion — and none of it was visible before.

**Research records were misrepresenting their sources at scale.**

- **30 of 101 `fetched` snippets were not verbatim.** One presented invented statistics as a quote
  from an arXiv abstract. Cause: WebFetch returns a language model's *rendering* of a page, not the
  page. All repaired.
- **17 of 68 `search-only` records checked contradicted their own page** — one in four. Failure
  modes: a fabricated comparison and metric attributed to a real Microsoft URL
  (`X-litmus-c-016`); a source stating the **opposite** of its claim — an unimplemented feature
  request cited as evidence of graceful degradation (`X-xc-budget-004`); and **snippets carrying
  verbatim text from a different record's page** (`X-end-to-end-058`, `X-cap-evaluation-003`).
- **767 search-only records remain unchecked.** At the observed rate that is roughly 190 records
  carrying claims their pages do not support.

**Citations were unverifiable by construction.**

- `validate_skills.py` fell back to `json.dumps(record)` for research records, making the
  agent-written `claim` field quotable. **18 of 946 skill citations were the repo quoting itself.**
- **1,079 of 3,024 skill citations still have no quote of their own** — one quote standing in for
  several cited ids (row 78). Of those, 171 are `E-` entity ids that structurally cannot be quoted.

**The reference model contradicted the repo's own documents.**

Found by writing a profile per card, which forced two documents to be compared for the first time.
7 cards moved built → planned on evidence — `harness/work-intake/test.sh` at passed 4 / failed 24,
`F-a6-02` recording Temporal's server as not listening, `F-a6-05` recording no identity field
anywhere. One card moved planned → **built** because `F-a7-03` is a measured fact.

---

## 3. The process that works

Proven over ~40 agent runs. Do not improvise around it.

### Capture

**Never use WebFetch to capture a quote.** It returns a model's rendering of a page. Use:

```
python3 tools/capture.py <url>      # api -> markdown -> service -> html
```

Record which rung succeeded in `fetch_tool`. `service` uses pure.md / urltomarkdown, both keyless.
A snippet must be a **byte-for-byte** substring of what capture returns — no tidying punctuation,
no joining fragments across an ellipsis.

### Search before researching

```
python3 tools/kb_index.py search "<terms>"     # ~2,400 citable records
python3 tools/kb.py show <id>
```

`merge-research` dedupes on **id only**, so nothing stops the same question being researched twice
under a new id. The index is the only thing that prevents it.

### The three rules adopted, now in `build-skill-authoring`

1. **A citation is typed by what the record is.** `F`/`T`/`X`/`REF` are documents and carry a
   verbatim quote from their own source text. `E`/`A`/`R` name things and relations, have no text
   to quote, and belong in a skill's `entities` array — never a row's `sources`. Of 184 `E-`
   records only 9 carry text at all.
2. **Profile before you constrain.** Measure what the records actually carry before writing a rule
   about them. Three rules were written and rejected in one session for skipping this.
3. **Matching proposes, evidence decides.** A similarity score or keyword hit produces a shortlist
   to read. It never settles a question and never drives a state change. Violated four times,
   caught four times; once a regex nearly flipped a card's status by matching a failure pattern
   against a **passing** test.

### Source text is not the `claim` field

A research record's `claim` is this repo's prose *about* a source. Only `snippet` and `read` are
source text. A quote matching `claim` is the repo citing itself.

### Egress is minted centrally

Research agents must **never** set `egress_ref` or append to `kb/egress-log.jsonl`. Two agents
appending concurrently mint the same `G-` id. The coordinator mints after the batch, then runs
`merge-research` and `reconcile_egress.py`.

**`G-` ids are positional, and `build_egress_log.py` renumbers from scratch.** It assigns
`G-00001..N` by walking `kb/research.jsonl` in sorted-id order, so inserting any record renumbers
every later decision. The `egress_ref` field on a research record is a back-reference *into* that
numbering, and **nothing checks it** — `reconcile_egress.py` matches on `research_id`, not on
`egress_ref`, and no tool verifies the egress log's hash chain at all. So a rebuild silently
invalidates every `egress_ref` for a record that sorts after the insertion point. This bit on
2026-09-10: a rebuild moved 5 of the 6 `egress_ref` values off their decisions, all green.
`build_egress_log.py` is a bootstrap tool, not an incremental one. STATUS row 82 tracks the fix.

The post-batch sequence is therefore fixed, and step 3 is not optional:

```
1. python3 tools/kb.py merge-research
2. python3 tools/build_egress_log.py
3. re-derive every egress_ref from the NEW log and rewrite the stale ones in kb/research/*.jsonl,
   then merge + rebuild again    <- skip this and the back-references rot silently
4. python3 tools/reconcile_egress.py
5. python3 tools/kb.py verify
```

---

## 4. The cycle that needs completing

Three loops, in dependency order. Each is independently runnable.

### Loop A — verify the search-only pile

767 records unchecked, ~190 expected to misrepresent their source. Highest value per token spent,
because it corrects claims already in use.

Priority order: records cited by a card profile first, then records cited by a skill, then the
rest. Batch by **source file** so agents never touch the same `kb/research/*.jsonl`.

A contradicted record is **left `search-only` and reported**, never patched to fit. That is the
finding.

### Loop B — profile the 13 undocumented cards

`1.5 · 2.3 · 3.1 · 3.2 · 3.4 · 3.5 · 4.1 · 6.1 · 6.3 · base.1 · base.2 · base.4 · rail.1`

**Core Agent is 4 of those 13** — Harness, Model Interface, Workspace, Tool Interface. The engine
of the model is its emptiest area, while Self-Improvement is 4-for-4 documented. Start there.

**`2.3 Planning` already has a 9-record research lens and no profile** — the research is done and
unattached. Cheapest card on the board.

Every one of these 13 is marked `built`. Every `built` card profiled so far produced a
contradiction. **Run the card's harness** where one exists; the two most damning findings came from
executing `test.sh`, not from reading.

Method: `docs/reference/cards/BRIEF.md`, gated by `validate_card_profiles.py`.

### Loop C — build the examples

`examples/reference/README.md` defines nine areas derived from the model, regions preserved
(spine / loop / base / rail). **It is empty on purpose.**

Do not start until Loop B is done and the 31 model-correction gaps are triaged. Building against a
model with 31 known-wrong things is precisely how the old seven areas ended up in
`examples/archived/`.

The card profile is the spec: write the example from it. If the profile does not say what a card
means, the profile is incomplete — that is not licence to write prose.

---

## 5. Overnight workflow

The failure mode when nobody is watching is not agents doing nothing. It is agents producing
confident, plausible, wrong output — which is exactly what the last two sessions kept catching by
hand. The ceremony discipline exists for this.

### The phase controller

`tools/phase.py` is the scriptable half of this. It runs the gates, counts failed attempts and
**stops** — an unattended run that keeps retrying a phase which will not go green burns a night and
leaves a mess.

```
python3 tools/phase.py gates        11 gates, a table, exit 1 on blocking red
python3 tools/phase.py open <name>  record that a phase started
python3 tools/phase.py close <name> run gates; green closes, red records an attempt
python3 tools/phase.py status       what is open, what stopped, and why
```

**Two failed attempts on the same phase marks it `stopped`, and it refuses to reopen.** Two
failures mean the problem is not something the loop can fix; the evidence is worth more than a
third attempt.

Gates that are red for recorded reasons (row 76's snippet drift, row 77's journey paths) are
carried as `known_red`: reported every run, never able to halt a phase that did not cause them.
Otherwise every phase fails on someone else's debt.

State is in `state/phases.json` and is written to be read: which gate went red, on which attempt,
at what time.

**Proven 2026-09-10** on phase `verify-search-only` — opened, went red on 94 stale citations,
self-improved, closed green on attempt 1.


### The phase plan

Six phases, three ceremonies. A ceremony every two phases, and at every section boundary — that is
where a reviewer who did not do the work checks it, and where the planted defects test the reviewer.

| # | Phase | Work | Batch |
|---|---|---|---|
| 1 | `B-core-agent` | Profile 3.1 Harness, 3.2 Model Interface, 3.4 Workspace, 3.5 Tool Interface, and 2.3 Planning (its 9-record lens already exists) | 5 agents, one card each |
| 2 | `B-remainder` | Profile the other 8: 1.5, 4.1, 6.1, 6.3, base.1, base.2, base.4, rail.1 | 4 agents, two cards each |
| — | **CEREMONY 1** | All 40 cards profiled. Review, improve, ledger, checkpoint | |
| 3 | `A-cited` | Verify search-only records cited by a skill or profile | 4-6 agents, split by source file |
| 4 | `A-remainder` | Verify the rest of the 767, highest-cited first | 4-6 agents, split by source file |
| — | **CEREMONY 2** | The corpus is verified. Review, improve, ledger, checkpoint | |
| 5 | `C-triage` | Triage the model-correction gaps into a decision list; apply what evidence settles, mark the rest for the owner | 1 agent + owner |
| 6 | `C-first-area` | Build one example area in `examples/reference/` from its corrected profiles | 2-3 agents |
| — | **CEREMONY 3** | First area built. Review, improve, ledger, checkpoint. **Stop and report** — do not build the other eight unattended | |

**Phase 1 is the right start.** Core Agent is the model's engine and its emptiest area: 4 of its 5
cards have no profile at all, while Self-Improvement is 4-for-4. And `2.3 Planning` is the cheapest
card on the board — the research is done and unattached.

**Do not run phase 6 more than once unattended.** Building the first example area is the test of
whether the structure works. Eight more built on an unproven structure is how the old seven ended
up in `examples/archived/`.

### Ceremony, concretely

```
python3 tools/plant.py plant <skill>          plant two known defects
  ... a reviewer agent that did NOT do the work reviews the phase ...
python3 tools/plant.py check <review.json>    exit 1 = the review missed them, DISCARD and re-run
python3 tools/check_ceremony.py <review.json> <improve.json>
python3 tools/kb.py ledger '<json>'
bash tools/checkpoint.sh "<phase>: <summary>" <paths>
python3 tools/plant.py unplant
```

A review that misses a planted defect is not a weak review, it is not a review. Discard it.

### Batch shape

```
1. plant          python3 tools/plant.py plant <skill>      (Loop B/C batches only)
2. work           4-6 parallel agents, split so no two touch the same file
3. gates          the definition of done below, all must be green
4. review         one agent that did NOT do the work reviews the batch
5. plant check    python3 tools/plant.py check <review.json> -- a review that misses both
                  planted defects is DISCARDED and re-run
6. improve        each finding applied or declined exactly once
7. ceremony       python3 tools/check_ceremony.py <review.json> <improve.json>
8. ledger         python3 tools/kb.py ledger '<json>'
9. checkpoint     bash tools/checkpoint.sh "<row>: <summary>" <paths>
```

Steps 4–5 are the ones that make unattended running safe. A batch that skips them is a batch
nobody checked.

### Definition of done per batch

```
python3 tools/verify_snippets.py --check
python3 tools/validate_card_profiles.py
python3 tools/card_profile_test.py
python3 tools/validate_skills.py
python3 tools/kb.py verify
python3 tools/reconcile_egress.py
python3 tools/knowledge_pool.py
```

**A red gate stops the batch. It does not get worked around.** `checkpoint.sh` already refuses on a
red `validate_skills` or `kb verify`.

### Concurrency limits, learned the hard way

- **4–6 agents per batch.** Beyond that they collide on shared files.
- **Split work by file, never by topic** — two agents editing one `.jsonl` corrupt it.
- The workflow engine caps at CPUs minus two (2 here) — run lanes as direct agents.
- **Never run assessors while examples or records are being edited.** That is what produced the 36
  litmus evidence errors on row 76.

### What must never happen unattended

- Editing a derived file by hand — `reference-model.json`, `entities.jsonl`, `SKILL.md`. Corrections
  go in `status-corrections.json` and are applied by the extractor.
- Weakening a checker to make a batch pass.
- Patching a contradicted record to fit its claim.
- Minting `G-` ids inside a research agent.

---

## 6. Open work (STATUS.md, 11 rows)

| Row | What |
|---|---|
| 14 | 17 of 42 standards have a fetched research record |
| 21 | Improvement loop, not started |
| 37 | **Blocked on you** — live host credentials |
| 74, 75 | Superseded by 79, areas archived |
| 76 | 144 litmus answers, 36 errors from evidence drift. `NEXTSTEP.md` B.1 has the durable fix |
| 77 | `standards.py check` 10 errors — `JOURNEY.md` names archived example paths |
| 78 | 1,079 unquoted skill citations, 171 of them entity ids to relocate |
| 79 | Reference examples — structure defined, nothing built |
| 80 | 27 of 40 cards profiled |
| 81 | 31 model corrections recorded, none applied |

Also outstanding, no row: **SARIF** needs a `standards/` entry (the interchange format card 5.1
needs), and **DSSE** is cited by two skills with no fetched record.

---

## 7. Known limits

- **The gates do not validate prose.** `text`, `covers` and `note` fields in a card profile are
  never checked. A profile can pass every gate carrying a fabricated figure in its narrative, and
  several did — a "$47,000 / 264-hour runaway loop" and a "28.7x-35.2x" benchmark among them, both
  unsupported anywhere in the corpus, both repeated to the owner as verified before a second pass
  caught them. Extending the checker to prose is open work.
- **A subagent's report is not evidence.** Two figures were relayed to the owner as verified purely
  because an agent said so. Check the artifact, not the summary.
- **The gates validate form, not truth.** They prove a quote is genuine and from source text. They
  cannot tell whether it *supports* the claim it is attached to. One claim was found resting on a
  five-word quote backing a four-clause assertion. Closing this needs a reader.
- **39 `read` fields are non-verbatim** — stitched fragments, not fabrication. No citation depends
  on them.
- **Every reviewer to date has been a model.** `HUMAN-REVIEW.md` is the checklist for a first human
  pass.
- **An auto-commit hook is running.** Work lands in commits with unrelated messages (`saved`, "Add
  new usage entry…"). Ledger records point at commits whose messages do not describe them.

---

## 8. Starter prompt

Copy this whole block into a fresh context.

```
Read bridge.md end to end before doing anything. Then docs/reference/cards/BRIEF.md, which is the
authoring rule, and docs/reference/provenance-methodology.md, which is how sourcing works here.

Do not trust any number in those files without re-running the command that produced it. That is
this repo's most repeated lesson: three sessions of confident figures that had already moved.

GOAL
Complete the reference architecture and build its examples. The model is 40 cards in
docs/reference/reference-model.json. 27 have a profile; 13 do not. The research corpus is 932
records of which 767 have never been opened, and one in four of the last 68 checked turned out to
misrepresent its own page. examples/reference/ is empty and waiting. examples/archived/ is the
superseded approach - do not add to it.

HOW TO WORK
Follow the six-phase plan in bridge.md section 5. Start with phase 1, B-core-agent.

Run every phase as:
  python3 tools/phase.py open <phase-name>
  ... 4-6 parallel agents, split by FILE so no two touch the same one ...
  python3 tools/phase.py close <phase-name>

A green close moves to the next phase. A red close means self-improve and close again. TWO failed
closes marks the phase stopped and it refuses to reopen - when that happens, stop and leave the
evidence. Do not work around a red gate and do not weaken a checker to pass one.

Hold a ceremony after phases 2, 4 and 6, per bridge.md section 5. A reviewer agent that did not do
the work reviews it, and tools/plant.py tests the reviewer: a review that misses its planted
defects is discarded and re-run.

NON-NEGOTIABLE
- A claim carries a verbatim quote from a named record, or is marked proposed. Both are good
  answers. A stretched quote is not.
- Source text is a record's snippet or read. Never its claim field - that is this repo's own prose
  about a source, and quoting it is the repo citing itself.
- Capture pages with tools/capture.py. NEVER WebFetch: it returns a model's rendering of a page,
  which is how 30 snippets acquired invented statistics.
- Search tools/kb_index.py before researching anything. merge-research dedupes on id only, so
  nothing else stops the same question being answered twice.
- Profile the data before writing a rule about it.
- Matching proposes, evidence decides. Never flip a state on a keyword match.
- A subagent's report is not evidence. Check the artifact it produced, not its summary. Two
  fabricated figures reached the owner because this was skipped.
- Mint egress ids centrally after a batch, never inside a research agent - concurrent agents mint
  the same G- id.
- Never hand-edit a derived file: reference-model.json, entities.jsonl, SKILL.md. Corrections go in
  docs/reference/status-corrections.json and are applied by the extractor.

WHEN A SOURCE CONTRADICTS ITS CLAIM
Leave the record as search-only and report it. Do not patch it to fit. That contradiction is the
most valuable thing a verification pass produces.

REPORT PROGRESS AS MEASURED NUMBERS
python3 tools/knowledge_pool.py is the scoreboard. It reads 24 documented / 3 unread /
13 undocumented right now. python3 tools/phase.py status says what is open, closed or stopped.
```
