# Bridge — 2026-09-10 (evening)

Handoff for a **design session, not a build session**. The corpus behind the reference model is
now sound enough to reason from; what is missing is the set of principles that decide how the
model becomes something alive. Supersedes the earlier 2026-09-10 bridge entirely.

**Every figure below was measured when written. Re-run the command before trusting it.** That
instruction has been in this file for three sessions and has been violated in all three — most
recently by the model that wrote this one, which reported "45 of 46 records failed" when the true
figure for genuine defects was closer to 1 in 300. Re-run first, then speak.

---

## 1. Measured state

| | | command |
|---|---|---|
| Research corpus | 977 records — 204 fetched, 766 search-only, 7 blocked | `python3 tools/kb.py stats` |
| Card profiles | **32 of 40** at 0 errors | `python3 tools/validate_card_profiles.py` |
| Citations | 451 — 292 read · 16 unread · 143 internal · 0 broken | `python3 tools/knowledge_pool.py` |
| Quotes typed | 234 — 217 exact · 7 formatting · 6 unretrievable · 3 partial · 1 stitched · 0 absent | same |
| **Needing a human decision** | **4** | same |
| Cards | 31 documented · 1 unread · **8 undocumented** | same |
| Citation debt | 23 recorded, 16 of them "page retrieved, quote not found" | `docs/reference/citation-debt.json` |
| Gates | 9 of 11 green; two known-red and recorded | `python3 tools/phase.py gates` |
| STATUS | 14 open rows | `python3 tools/status_check.py --freshness` |

Phases `B-core-agent`, `A-cited`, `A-repair` are closed green. `python3 tools/phase.py status` is
the authority.

---

## 2. Can you trust the knowledge pool? — the honest answer

**Yes, for what it is: a sourced description of 32 of the 40 elements.** 217 of 234 quotes are
byte-identical on their page, 7 more differ only in markdown or a flattened list, and the gate
refuses any citation to a record a capture pass proved unsupported. That is a real foundation and
it was not true this morning.

**No, not yet as a build specification.** Five reasons, each checkable:

1. **8 cards have no profile at all, and every one of them is marked `built`** — 1.5 Agent-to-Agent,
   4.1 Isolated Runtime Profiles, 6.1 Telemetry, 6.3 Lineage, base.1 Source Control, base.2 Artifact
   Storage, base.4 Metadata & State, rail.1 Security. Every `built` card profiled so far produced a
   contradiction. Assume these will too.
2. **31.7% of citations are this repo citing its own documents** (`F-`/`T-`/`REF-`/`A-`). Legitimate
   for "what runs here today" and for owner intent — but it is *not* evidence of industry practice.
   An example built from a mostly-internal card demonstrates our own design. 1.2 Scheduled is 12 of
   13 internal; 1.1, 3.2, rail.6, 1.3 are the next heaviest.
3. **Prose is still ungated.** Every checker reads `evidence` arrays. Nothing reads `text`, `role`,
   `covers`, `note` or `gaps`. A fabricated figure sitting in prose with no quote attached passes
   everything — that is how "$47,000 / 264-hour" and "28.7x-35.2x" survived, and they were caught by
   hand, three times, in one session. **This is the largest remaining hole and it should close before
   anything is built at scale**, or every example inherits the same class of defect.
4. **Nobody has ever built anything from a card profile.** "The profile is the spec" is an
   assertion, not a measured fact. A profile carries `definition`, `standards`, `tools`, `landscape`,
   `usage`, `gaps`; whether that is sufficient to write a runnable example is untested.
5. **`docs/reference/card-example-map.json` maps all 40 cards to the ARCHIVED seven areas**
   (`"areas": ["ask"]`, `origin: proposed`), while `examples/reference/README.md` plans **nine**
   areas by region. `tools/check_card_example_map.py` passes against the archived set. A build
   session following that map builds toward deleted work.

`docs/reference/knowledge-pool.md` is the single view. It used to be two documents that drifted;
one of them is why this repo spent a day repairing citations it had already called verified.

---

## 3. The process that works — do not improvise around it

**Citable means checked.** A record is not citable because it exists. `tools/stamp_verification.py
--fetch` fetches each cited page through the same path the checker uses and stamps the record with
what it found; `tools/validate_card_profiles.py` refuses any citation whose quote is not in that
stamp. Proven by deliberate breakage in both directions.

**Verdicts are typed, never boolean.** `exact` · `formatting` · `unretrievable` · `partial` ·
`stitched` · `absent`. A bare true/false scored a flattened bullet list and an invented statistic
identically, and the difference got supplied from imagination — by the model, to the owner,
repeatedly. `partial` is deliberately a *needs-a-reader* bucket: no string test separates a faithful
paraphrase of a page from an invented quote, because both share the source's vocabulary.

**Capture, and mind which fetcher.** `tools/capture.py` walks api → markdown → service → html.
`tools/verify_snippets.py` re-fetches with a plain GET and strips HTML. **They do not return the
same text**, and a snippet copied faithfully from the markdown rung will drift. Build snippets from
the gate's path — `docs/reference/cards/BRIEF.md` carries the runnable check. Never WebFetch.

**A fabricated `read` is the most dangerous defect available.** `validate_card_profiles` accepts a
quote from `snippet` *or* `read`, so an invented `read` launders an invented quote past every
checker. Repair agents did this to their own output twice on 2026-09-10, both caught by review,
neither by tooling.

**Egress ids are positional.** `build_egress_log.py` renumbers from scratch, so inserting any record
invalidates every later `egress_ref`, and nothing checks it. The post-batch sequence is fixed:
merge-research → build_egress_log → **re-derive every `egress_ref`** → merge+rebuild → reconcile →
kb verify. Skipping step 3 rots the back-references silently. STATUS row 82.

**A subagent's report is not evidence.** Check the artifact. Three times this session a subagent's
own summary miscounted its own output (4 vs 5 findings, 9 vs 7 records). The artifacts were right
every time; the summaries were not.

**Nothing writes to `citation-debt.json` automatically.** An exemption list that grows quietly stops
being debt and becomes permission. STATUS row 84 burns it down.

---

## 4. What we have — the tooling

51 tools, 10 of them wired as gates in `tools/phase.py`. They fall into one healthy group and one
that has rotted, and the difference decides what the next session touches first.

**The anti-fabrication chain is the strong part, and it is new.** `capture.py` fetches ·
`stamp_verification.py` types each quote against the page · `validate_card_profiles.py` refuses a
citation whose quote is not stamped · `verify_snippets.py` re-checks records · `knowledge_pool.py`
reports · `kb.py` + `build_egress_log.py` + `reconcile_egress.py` keep the chain honest. Every link
is proven by a deliberate breakage. Trust this group; extend it rather than replacing it.

**The examples layer points at work that was deleted.** `examples/archived/` holds the old seven
(run · ask · watch · steer · progress · done · improve). Still describing them:

| artifact | what it says | gate? |
|---|---|---|
| `docs/reference/card-example-map.json` | maps all 40 cards to the archived seven, `origin: proposed` | **yes** — `check_card_example_map.py` passes on it |
| `JOURNEY.md` | names archived example paths | **yes** — `standards.py check`, 10 errors, STATUS row 77 |
| `tools/examples_index.py` | hardcodes the seven, writes `docs/examples/index.md` | no |
| `docs/examples/index.md` | the seven by four doors | no |
| `.claude/skills/build-example/SKILL.md` | says "seven" six times, "nine" once | authoring guidance |

Meanwhile `examples/reference/README.md` proposes **nine** region-based areas and contains nothing
else. So five artifacts describe one structure, one document proposes another, and a gate passes on
the dead one. **Re-point or retire these before building** — otherwise the next session builds nine
areas while the repo's own map, index, journey and authoring skill all describe seven different ones.

**Probably dead:** `migrate_standards.py` (self-described one-off, already run).
**Possibly superseded:** `resolve_reference_model.py` scores cards against evidence, but a score is a
shortlist and never a citation — the profiles now do this properly. Check before reusing.
**Confusingly paired:** `check_ceremony.py` (validates one record pair) and `ceremony_check.py`
(trend across ceremonies) are different tools with near-identical names.

---

## 5. Definition of ready to build

**Ready is a command, not an opinion.** `python3 tools/ready_to_build.py` prints these eight and
exits non-zero until all hold. Opinion is how the previous seven example areas got built on an
unproven structure and then archived.

| # | Condition | How it is checked | Now |
|---|---|---|---|
| R1 | Every card profiled, gate green | `validate_card_profiles.py` = 40 profiles, 0 errors | 32 of 40 |
| R2 | No quote still needs a reader | `knowledge_pool.py` → 0 need a person | 4 |
| R3 | No undecided citation debt | every `citation-debt.json` entry carries `owner_decision` | 23 undecided |
| R4 | Prose carries no unsourced quote or figure | `tools/prose_gate.py` exits 0 | tool does not exist |
| R5 | Card→example map names the areas we will build | map vs `build-principles.json` | map names the archived seven |
| R6 | The model's purpose is decided | `build-principles.json.model_purpose` | not recorded |
| R7 | One example built from a profile, gaps written down | an area under `examples/reference/` + `profile-sufficiency.md` | none |
| R8 | Internal-heavy cards labelled | `build-principles.json.internal_share_policy` | not recorded |

**0 of 8 met** as of 2026-09-10 evening.

Two of the eight are deliberately not machine-decidable:

- **R6 is owner intent.** Is the reference model an *industry-aligned description*, or a description
  of *this platform*? 31.7% of citations are this repo citing its own documents, so today it is both,
  and the answer changes which cards can carry an example at all. Ask; do not infer.
- **R7 is empirical, and it is the one that matters.** "The card profile is the spec" has never been
  tested. It may well hold — nobody has pulled the data to find out. The test is to build exactly one
  area from a profile and write down what the profile failed to tell you. If the answer is "nothing",
  R7 closes and the spec holds. If not, the missing pieces are named rather than guessed at.

R7 is the only condition whose failure is informative, so attempt it early even while others are open
— just do not fan out to nine areas on its result until R1–R6 and R8 hold.

---

## 6. The plan

Ordered so that each step protects the ones after it. `python3 tools/ready_to_build.py` is the
scoreboard; the R-numbers below are its conditions.

| # | Step | Why this order | Closes |
|---|---|---|---|
| 1 | **Owner decides the model's purpose and the area set** | Everything downstream depends on it, and neither is a research question. Industry description or platform description? Nine region areas or seven journey areas or something else? | R6 |
| 2 | **Attempt ONE example from ONE profile** | The only step whose failure is informative. Write every question the profile could not answer into `profile-sufficiency.md`. If it answers everything, the profile IS the spec — a real finding, and R7 closes cheaply. | R7 |
| 3 | **Build the prose gate** | The largest open hole: nothing reads `text`/`role`/`covers`/`note`, which is how two invented statistics passed every gate. Close it before mass-authoring, or every new area inherits the class. | R4 |
| 4 | **Re-point or retire the five archived-facing artifacts** | A passing gate on a dead mapping will silently validate the wrong thing. | R5 |
| 5 | **Profile the 8 remaining cards, capture-first** | All eight are marked `built`; every `built` card profiled so far produced a contradiction. | R1 |
| 6 | **Clear the residue** | 4 quotes needing a reader, 23 undecided debt entries, internal-share policy. | R2 · R3 · R8 |
| 7 | **Build the remaining areas** | Only once `ready_to_build.py` exits 0. A workflow can fan this out; nothing before step 7 should be fanned out. | — |

Steps 1 and 2 can run together — 2 needs only the area shape from 1. Steps 3–6 are independent of
each other. Step 7 is gated on all of them.

---

## 7. Starter prompt

Copy the block below into a fresh context. It is written to stand alone.

```
You are picking up a design-and-evidence repo for a target agentic platform. Nothing here
runs as an application: it is a 40-card reference model, 29 skills, 28 harnesses, and a
hash-chained knowledge base where every claim is either cited to a source with a verbatim
quote or explicitly marked proposed.

The goal is to take this future-state framework and make it alive -- decide where everything
belongs, prove the path works on one thing, then let a workflow build the rest. We are not
there yet, and the last attempt at examples was archived for being built on an unproven
structure. Your job is to make it ready to build. Not to build it.

FIRST COMMAND, BEFORE ANYTHING ELSE:

    python3 tools/ready_to_build.py

It prints 8 conditions and exits 1 until they all hold. It reads 0 of 8 today. That output is
your task list, your progress report, and how you end the session. Report it verbatim; never
paraphrase it into prose.

Then read bridge.md in full, then docs/reference/knowledge-pool.md (what stands behind each of
the 40 cards), then docs/reference/cards/BRIEF.md (the authoring rule).

THE JOB
Work bridge.md section 6, steps 1 through 6. Stop when ready_to_build.py exits 0, or when you
are blocked on the owner -- whichever comes first -- and report. Do not start step 7.

STEP 1 IS TWO QUESTIONS FOR THE OWNER. Ask both in one message, early. They are intent, not
research, and you cannot infer them:
  (a) Is the reference model an industry-aligned description, or a description of this
      platform? 31.7% of its citations are this repo citing its own documents, so today it is
      both. Card 1.2 Scheduled is 12 of 13 internal -- an example built from it would
      demonstrate our own design, not an industry pattern.
  (b) Which example-area set is real: the nine region-based areas proposed in
      examples/reference/README.md, the seven journey areas the rest of the repo still names,
      or neither?
Record both in docs/reference/build-principles.json. Steps 4 and 7 depend on (b).

STEP 2 IS THE ONE THAT TEACHES YOU SOMETHING. Start it as soon as (b) is answered. "The card
profile is the spec" has never been tested -- it may well hold; nobody has pulled the data.
Build ONE area from ONE profile using only that profile, and write every question the profile
could not answer into docs/reference/profile-sufficiency.md. An empty list is a real result.
Do not change the profile schema before you have the list.

TRAPS -- each cost a session to find. bridge.md section 3 carries the incidents.
  - Re-run any number before repeating it. Stale figures are this repo's most expensive habit.
  - Citable means checked: run tools/stamp_verification.py --fetch before validating a citation.
  - Quote verdicts are typed, never true/false. `partial` means a person must read it, not that
    it failed. A boolean is how a flattened bullet list and an invented statistic were reported
    with the same word.
  - Capture with tools/capture.py, never WebFetch -- and build snippets from the GATE's fetch
    path: verify_snippets.py does a plain GET and strips HTML, which is not what capture.py
    returns.
  - Never patch a contradicted record to fit its claim. The contradiction is the finding.
  - A subagent's report is not evidence. Open the artifact it produced. Three subagent summaries
    miscounted their own output last session; the artifacts were right every time.
  - Mint egress ids centrally after a batch, then re-derive every egress_ref after any rebuild.
  - Nothing writes to citation-debt.json automatically. It is debt, not permission.

CLOSING A STEP
    python3 tools/phase.py open <name>   ...   python3 tools/phase.py close <name>
Green closes it. Two reds stop the phase and it refuses to reopen -- when that happens, stop and
leave the evidence rather than forcing a third attempt. Then review, improve, ledger record,
checkpoint. tools/checkpoint.sh commits AND pushes to origin, so run it only when you mean to.

ENDING THE SESSION
Print python3 tools/ready_to_build.py. Say which conditions you closed, which you did not, and
what is still waiting on the owner. Update bridge.md so the next context starts where you
stopped.
```
