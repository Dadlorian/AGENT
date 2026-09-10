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

## 4. What the next session is for

Not building. **Deciding how to build, then proving the decision on one thing before scaling it.**
The previous seven example areas were archived because they were built on an unproven structure;
repeating that at nine areas is the failure mode to avoid.

### Questions principles must settle first

1. **What is the reference model *for*?** An industry-aligned description, or a description of this
   platform? 31.7% internal citations means it is currently both, and the two lead to different
   examples. This is an owner decision, not a research question.
2. **What is an example?** A runnable demo of one card? A path across several? The four doors
   (human/event/schedule/external) on one envelope? `examples/reference/README.md` proposes nine
   region-based areas; the archived seven were user-journey based. Neither has been justified
   against the other.
3. **Is a card profile a specification?** If not, what is missing — a per-card interface contract,
   a call shape, a conformance case? Answer by attempting exactly one and seeing what is absent.
4. **What does "alive" mean here?** Today everything is dry-run. No harness has ever executed
   against a real host (STATUS row 37, blocked on owner credentials). "Alive" may mean real
   execution, or it may mean a faithful dry-run whose call shape matches live. Decide explicitly.
5. **How do the four parallel structures relate?** 40 cards, 29 skills, 28 harnesses, N example
   areas. The card→example map asserts one relationship and points at archived areas. Are these
   four views of one thing, or four things?
6. **Close the prose hole before scaling.** See §2.3.

### Sequence that respects what has been learned

- Settle 1–2 with the owner; they are intent, not evidence.
- Close the prose gate (§2.3) — mechanical, and it protects everything built afterward.
- Profile the 8 remaining cards **capture-first**, never against unverified records.
- Build **one** example area end to end. Ceremony it. Only then consider a workflow to fan out.
- `tools/phase.py open/close` around each; two red closes stops a phase and it refuses to reopen.

---

## 5. Starter prompt

```
Read bridge.md end to end. Then docs/reference/knowledge-pool.md (what stands behind each card),
docs/reference/cards/BRIEF.md (the authoring rule), and examples/reference/README.md (the nine
areas currently proposed, and unproven).

Re-run every number before repeating it. `python3 tools/knowledge_pool.py` and
`python3 tools/phase.py gates` are the scoreboards. This repo's most expensive and most repeated
mistake is confident restatement of figures that had moved -- including, last session, a model
reporting a corpus-wide crisis that measurement did not support.

YOUR JOB IS TO DESIGN, NOT TO BUILD.
The reference model is 40 cards, 32 profiled and sourced. examples/reference/ is empty on purpose.
Before anything is built, settle the six questions in bridge.md section 4 -- especially what the
reference model is FOR, and whether a card profile is actually a specification. Answer that last
one empirically: attempt one example, see what the profile does not tell you, and write that down.

Do not profile the 8 remaining cards against unverified records, and do not build nine areas on an
unproven structure -- that is exactly how the previous seven ended up in examples/archived/.

NON-NEGOTIABLE (all proven the hard way, see bridge.md section 3)
- A claim carries a verbatim quote from a stamped record, or is marked proposed. Both are good.
- Citable means checked: run tools/stamp_verification.py --fetch before validating.
- Verdicts are typed, never boolean. `partial` means a person must read it.
- Capture with tools/capture.py, never WebFetch -- and build snippets from the gate's fetch path.
- Never patch a contradicted record to fit. The contradiction is the finding.
- A subagent's report is not evidence. Check the artifact it produced.
- Mint egress ids centrally after a batch; re-derive every egress_ref after any rebuild.

WHEN YOU FINISH A PIECE
python3 tools/phase.py close <name>. Green closes. Two reds stop the phase and it will not reopen.
Then review, improve, ledger, checkpoint -- in that order.
```
