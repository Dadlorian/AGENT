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

## 4. Definition of ready to build

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

## 5. Starter prompt

Copy this whole block into a fresh context.

```
Read bridge.md end to end, then docs/reference/knowledge-pool.md (what stands behind each of the 40
cards), docs/reference/cards/BRIEF.md (the authoring rule), and examples/reference/README.md (nine
proposed areas, unproven).

Re-run every number before repeating it. This repo's most repeated and most expensive mistake is
confident restatement of figures that had moved -- last session a model reported a corpus-wide
crisis that measurement did not support, and had to walk it back twice in one conversation. The
scoreboards are:
  python3 tools/ready_to_build.py     the definition of ready, 8 conditions, exits 1 until all hold
  python3 tools/knowledge_pool.py     what stands behind every card
  python3 tools/phase.py gates        11 gates; two are known-red and recorded

YOUR JOB
Get from 0 of 8 ready conditions to 8 of 8, then build ONE example area and stop.
Do not build nine areas. That is exactly how the previous seven ended up in examples/archived/.

START HERE, IN THIS ORDER
1. R6 is the owner's to answer, and it gates the rest: is the reference model an industry-aligned
   description, or a description of this platform? Ask them directly, in one question, with the
   consequence stated -- 31.7% of citations are this repo citing itself, and cards like 1.2
   Scheduled (12 of 13 internal) would demonstrate our own design rather than an industry pattern.
   Record the answer in docs/reference/build-principles.json.
2. R7 next, because its failure is the only informative one. Pick one card, attempt one example area
   from its profile alone, and write down every question the profile could not answer into
   docs/reference/profile-sufficiency.md. If it answers everything, the profile IS the spec and that
   is a real finding. Do not fix the profile schema before you have this list.
3. Then R4 (the prose gate -- the largest open hole: nothing reads text/role/covers/note, which is
   how two invented statistics survived every gate), R1 (the 8 unprofiled cards, capture-first),
   R2, R3, R5, R8.

NON-NEGOTIABLE -- every one of these was learned expensively; bridge.md section 3 has the incidents
- A claim carries a verbatim quote from a stamped record, or is marked proposed. Both are good.
- Citable means checked: run tools/stamp_verification.py --fetch before validating.
- Verdicts are typed, never boolean. `partial` means a person must read it, not that it failed.
- Capture with tools/capture.py, never WebFetch -- and build snippets from the GATE's fetch path,
  which is not the same text capture.py returns.
- Never patch a contradicted record to fit its claim. The contradiction is the finding.
- A subagent's report is not evidence. Check the artifact it produced; three subagent summaries
  miscounted their own output last session.
- Mint egress ids centrally after a batch, and re-derive every egress_ref after any rebuild.
- Nothing writes to citation-debt.json automatically. It is debt, not permission.

WHEN YOU FINISH A PIECE
python3 tools/phase.py open <name> ... close <name>. Green closes; two reds stop the phase and it
refuses to reopen -- when that happens, stop and leave the evidence. Then review, improve, ledger,
checkpoint, in that order. checkpoint.sh pushes to origin.

REPORT PROGRESS AS `python3 tools/ready_to_build.py` OUTPUT, NOT AS PROSE.
```
