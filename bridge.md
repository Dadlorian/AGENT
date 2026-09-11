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
| **Candidate source pool** | **3,537 usable URLs, addressed by card** | `python3 tools/index_sources.py --coverage` |
| Ready to build | **2 of 8** conditions | `python3 tools/ready_to_build.py` |

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

## 3b. Reading the pool without fooling yourself

Section 3 is how the pool is *built*. This is how it is *read* — and reading is where the damage
came from on 2026-09-10. Every figure below is a real mistake made that day, by the model, to the
owner, and then walked back.

**Report the number that needs a person, not a percentage.** `knowledge-pool.md` leads with
*"4 of 234 quotes need a human decision."* The share above it — 92.7% `exact` — is true and useless
for deciding anything. Every time a share was reported first, it was read as "we have evidence",
and every time it had to be qualified afterwards.

**Never narrate a boolean.** One failed check meant all of these on the same day: a trailing period;
a flattened bullet list; stripped line numbers in a code listing; `It` expanded to `MIG
(Multi-Instance GPU)`; a quote spanning a PDF body no tool here can read; and one genuine case of
this repo's own prose wearing a source's byline. Reported as a count it read as 23 defects. Graded
by kind it was **one**. If a check returns pass/fail, it cannot tell you what kind of problem you
have — so do not describe the problem from it.

**Give the denominator and the distribution. Never the worst case alone.** The 7.2 example in this
document is the worst of eight, and it was first presented without saying so; the owner had to ask
whether it was cherry-picked. The honest shape is: *308 external citations, 280 byte-identical on
their page, and here is the full breakdown of the other 28.*

**Check a heuristic against ground truth before reporting its output.** A quote-mark test for
"summary written into `read`" returned 19 hits and was one step from being reported as 19 laundered
citations. A fetch showed most were genuine excerpts whose *page* happened to use quotation marks.
A heuristic proposes; only a fetch decides — the same rule as *matching proposes, evidence decides*,
applied to our own tooling.

**`read` is structurally a second `claim` field.** `validate_card_profiles.py` forbids quoting
`claim` — there is an explicit guard and a comment recording 18 of 946 citations that exploited it.
But `read` can hold exactly the same repo prose, and `read` *is* an approved quote source. Worked
example: `X-refmodel-7-2-experiment-008`, whose `read` is a summary paragraph with page quotes
embedded in it; card 7.2 quotes the connective prose *between* those quotes, so a reader is told
agentforgehub.com said something it never said. Every gate was green. Treat `read` with the same
suspicion as `claim`: contiguous page text or nothing.

**When a number moves, say which measurement moved.** The counts in this document changed repeatedly
in one day — not because the corpus changed, but because what was being counted changed (record-level
→ quote-level, boolean → typed). A number without its measurement is not a fact.

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

## 4b. The source pool — where new evidence comes from

`docs/reference/REF-ARCH-INDEX.md` is 5,828 URLs that four model runs proposed against a
244-question questionnaire. Two properties make it the missing piece rather than another pile:

**It is already addressed by card.** Question ids are `<area>.<card>.<n>` — `3.1.1`…`3.1.10` are
ten questions about card 3.1 Harness — and the index's sections are the model's own areas
(`8` → `base`, `10` → `rail`). So it is not a corpus to map onto the architecture later; it is
research already pointed at it. That is why it closes the gap the previous sessions kept circling.

**It carries a trust band, and the band predicts whether the gate can use the source.**

| band | tier | rows | |
|---|---|---:|---|
| `core` | T1 | 435 | standards body / formal spec |
| `primary` | T2 | 1,702 | primary implementation / official docs |
| `research` | T3 | 2,045 | engineering or security research |
| `WILD` | U | 1,646 | **untiered, unknown — dropped** |

Measured on 2026-09-10: every citation that survived repair came from `core`/`primary`
(`modelcontextprotocol.io`, `datatracker.ietf.org`, `gvisor.dev`, `docs.litellm.ai`). All 23
entries in `citation-debt.json` came from the other end — blogs, Medium 403s, arXiv bodies.
Four `core` candidates for card 1.5 were fetched through the gate's own path and returned 132K,
35K, 157K and 5K of readable text.

### The trap, written down so it is not re-derived

Ordering is **three independent axes**. The index's `Bucket` column folds two of them together:

```
trust    core > primary > research; WILD dropped
dated    whether the page carries a date — A FACT, NOT A QUALITY
recency  only meaningful for a page that HAS a date
```

`Bucket` B3 means "older **or undated**". Filtering to B1/B2 is the obvious move and it is wrong:
it deletes **362 of the 435 `core` rows, and 317 of those are dropped purely for being undated**.
A living specification carries no dateline — that is what a current standard looks like. Undated
ranks *ahead* of dated-but-old and is never dropped. `tools/index_sources.py` encodes this.

```
python3 tools/index_sources.py 1.5            ordered candidates, unfetchable hosts flagged
python3 tools/index_sources.py --coverage     usable candidates per card
```

**Nothing in the index is evidence.** These are URLs a model suggested; no page has been opened.
They enter exactly like everything else: capture → record → `stamp_verification.py --fetch` → gate.
What the pool removes is the guessing about *which* URL to try, which is where the bad sources came
from in the first place.

### What it covers

Every card has a pool, and the cards we are blocked on are the best supplied. The 8 unprofiled:
1.5 (42 core) · rail.1 (18) · 6.1 (22) · 6.3 (15) · base.1 (2 core, 60 primary) · base.2 (5) ·
base.4 (2, 48) · 4.1 (6). The internal-heavy cards have external evidence waiting too — 1.2
Scheduled is 12-of-13 internal today and has 9 `core` + 19 `primary` available. Four cards have
**zero** `core`: 2.3, 4.3, 7.1, rail.5 — know that before leaning on them.

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
| R6 | The model's purpose is decided | `build-principles.json.model_purpose` | **met** |
| R7 | One example built from a profile, gaps written down | an area under `examples/reference/` + `profile-sufficiency.md` | none |
| R8 | Internal-heavy cards labelled | `build-principles.json.internal_share_policy` | **met** |

**2 of 8 met** as of 2026-09-10 evening (R6 and R8 closed by `build-principles.json`). Re-run the command; do not trust this line.

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

Ordered so each step protects the ones after it. `python3 tools/ready_to_build.py` is the
scoreboard; the R-numbers are its conditions. **R6 and R8 are already closed** — the owner's
decisions are recorded in `build-principles.json` and must not be reopened.

| # | Step | Why this order | Closes |
|---|---|---|---|
| 1 | **Build the prose gate** | The last hole. Nothing reads `text`/`role`/`covers`/`note`/`gaps`, so a fabricated figure with no quote attached passes every check — that is how "$47,000 / 264-hour", "28.7x-35.2x" and a Firecracker "5-30ms" survived, each caught by hand. Close it BEFORE mass-authoring or all 8 new cards inherit the class. | R4 |
| 2 | **Attempt ONE example from ONE profile** | The only step whose failure is informative. Write every question the profile could not answer into `docs/reference/profile-sufficiency.md`. If it answers everything, the profile IS the spec — a real finding. Can run alongside step 1. | R7 |
| 3 | **Profile the 8 unprofiled cards from the source pool** | Now unblocked: `python3 tools/index_sources.py <card>` gives ordered `core`/`primary` candidates per card. All 8 are marked `built` and every `built` card profiled so far produced a contradiction — expect the same. Capture-first: no citation to a record that was never fetched. | R1 |
| 4 | **Re-point or retire the five archived-facing artifacts** | `card-example-map.json` maps all 40 cards to the ARCHIVED seven while `build-principles.json` names nine, and `check_card_example_map.py` passes on the dead one. A build session following that map builds toward deleted work. | R5 |
| 5 | **Clear the residue** | 4 quotes needing a reader; 23 debt entries with no `owner_decision` — most can be re-sourced from the pool rather than decided, since 16 are blog-tier "quote not found" and the same question usually has a `core` candidate. | R2 · R3 |
| 6 | **Build the remaining areas** | Only once `ready_to_build.py` exits 0. Fan out here and nowhere earlier. | — |

Steps 1 and 2 are independent and can run together. Step 3 is the one worth agents; steps 4 and 5
are small. Nothing before step 6 should be fanned out to nine areas.

**The loop that works**, proven across three closed phases on 2026-09-10:

```
python3 tools/phase.py open <name>
   4-6 parallel agents, SPLIT BY FILE so no two touch the same one
python3 tools/phase.py close <name>      green closes; two reds stop the phase, leave the evidence
```

Then, always, the post-batch sequence from section 3 — merge-research → build_egress_log →
re-derive every `egress_ref` → merge+rebuild → reconcile → kb verify → `stamp_verification.py
--fetch` → `validate_card_profiles.py`. Skipping the re-derive rots the back-references silently.

---

## 7. Starter prompt

Copy from here. It is deliberately short: **you are the shared prefix every fork inherits, so what
you read costs what it costs times every agent times every turn.** Measured on run
`wf_8d4230e8-999`: cache_read was 97.8% of 1,110,376,052 tokens and the average token was re-billed
**46 times**. Read the five files below and nothing else until you need it.

```
Design-and-evidence repo for a target agentic platform. Nothing runs as an app.

READ EXACTLY THESE FIVE, ~13k tokens total. You are the prefix every fork inherits.
    NEXTSTEP.md                          the plan and which step is next
    bridge.md sections 3, 3b, 4b         the traps that cost real time
    state/briefs/one-three-one.md        the cost model and what fork/rewind actually do
    docs/reference/cards/3-3.json        the profile you are building from
    examples/reference/README.md         the nine areas and what an area is

Then, and only then:
    python3 tools/ready_to_build.py      8 conditions, exits 1 until all hold
    python3 tools/token_review.py        unoptimized patterns, before you fire anything

JOB: STATUS row 79 = R7 = bridge.md section 6 step 2. Build ONE area under
examples/reference/ from a card profile, and write every question the profile could NOT
answer into docs/reference/profile-sufficiency.md. That file is the deliverable; the
example is the instrument. Do NOT fan out to nine areas.

RUN IT AS A LOOP, NOT A TO-DO LIST:
    python3 tools/ceremony_next.py                    the number, read off disk
    python3 tools/phase.py open 79-reference-example
        build the area
    python3 tools/phase.py close 79-reference-example 16 gates decide; two reds STOP it
        ceremony review + improve records under kb/ceremonies/
        python3 tools/check_ceremony.py <the pair>
        ledger record, then bash tools/checkpoint.sh

TOKEN DISCIPLINE, MEASURED NOT ASSUMED
- cost = agents x turns x prefix. cache_read is re-billed EVERY turn at full prefix size.
- Fork saves rediscovery, NOT carriage. Three forks off a big captain cost 3x that prefix.
  Fork only after recon, only from a small captain.
- Put iterate-until-green work behind a subagent firebreak: it burns its own context and
  returns a short answer. Then verify the ARTIFACT yourself - a report is not evidence.
- Write findings to disk continuously. /rewind is interactive-only, owner-invoked, and
  discards anything living only in the transcript.
- Never pay a model to apply a category someone already discovered. Numbering, committing,
  validating, rendering are script work: ceremony_next.py, checkpoint.sh, phase.py.

THE RULES THAT ARE NOT NEGOTIABLE
- Citable means checked. A quote is valid only if the stamp found it on the page.
- Verdicts are typed, never boolean: exact / formatting / unretrievable / partial /
  stitched / absent. Report "N need a human", never a percentage.
- Source text is a record's snippet or read - never its claim.
- A contradicted record is left as it is and reported. Patching it destroys the finding.
- A subagent's report is not evidence. Check the artifact it produced.
- Undated is not old. Never filter a source out for having no date.
- Name every claim by its STATUS row id.

New evidence comes from the pool, never from search:
    python3 tools/index_sources.py <card>     ordered core/primary candidates
    python3 tools/index_glossary.py <card>    standards and API fields, areas 1-7 only
Nothing in either is evidence: capture -> record -> stamp_verification.py --fetch -> cite.

Decisions already made: docs/reference/build-principles.json - do not reopen them.
checkpoint.sh commits and pushes; set CLAUDE_SESSION_URL first.
```
