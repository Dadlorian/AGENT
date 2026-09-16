# Intake Protocol 0.1 — bounded interrogation to a dispatchable package

**Status: proposed.** This spec is this repo's own design. Where a claim rests on PASS.md it
carries an `F-`/`E-` id; everything else is marked proposed, per `agentic-stack` instruction 4.
It supersedes no installed skill: the `intake-mcp` starter exposes `get_task`, `update_task`,
`finalize_task` and implements none of what follows.

A service asks questions. An agent relays them in ordinary language, maps replies back to stable
question ids, and submits them. The service decides what to ask next and when to stop. The output
is a requirements package another model turns into assignments. Intake and dispatch stay separate.

---

## 1. What this protocol proves, and what it does not

The protocol is two layers, and conflating them is the failure this spec exists to prevent.

| Layer | Content | Provable? |
|---|---|---|
| **L1 — the trace** | which question was asked, at which revision, what was submitted against it, by whom, in what order, and that each batch applied exactly once | **Yes.** Mechanically decidable from stored state alone |
| **L2 — the content** | whether an answer is true, whether coverage is complete, whether a requirement is right, whether the depth is genuinely ready | **No.** Assessed and recorded with its basis; never proven |

Measured over this protocol's twenty rules: **14 decidable, 2 partial, 4 not decidable server-side.**
The split is clean — every decidable rule governs L1, every undecidable one governs L2.

> A server "cannot deterministically prove meaning or completeness merely because fields exist."
> — requirements-intake guide, §Server versus agent

**Therefore:** a package is evidence of *how it was collected*, never evidence that it is correct.
Every consumer of a package MUST treat L2 fields as assertions carrying provenance, not as findings.
`readiness.executionAuthorized` is `false` in every package this protocol emits; authorization is a
decision taken outside intake.

This layering is why the protocol can be strict. L1 rules are enforced absolutely and reject on
violation. L2 rules are recorded with their basis and never reject.

---

## 2. Vocabulary

| Term | Meaning |
|---|---|
| **session** | one interrogation, pinned to a catalogue version and a policy version at creation |
| **revision** | monotonically increasing integer; every state-changing commit increments it exactly once |
| **template** | a reusable question form, identified by `templateId`, drawn from the pinned catalogue |
| **cell** | one `(stage, area)` coordinate of the pinned grid |
| **instance** | a template applied to a cell: `questionId = "{templateId}@{stage}/{area}"`. This is the persisted key |
| **batch** | up to three instances returned together, or the answers submitted against them |
| **correction** | a new answer for an already-answered `questionId`; appended, never overwriting |
| **package** | the terminal output: requirements, constraints, open questions, readiness, stop reason |

Display numbering is never a key. `questionId` is the key; `templateId` is recorded separately so
the same template instantiated across cells remains countable. (proposed)

---

## 3. The question space is finite by construction

This is the load-bearing decision of the spec. Everything in §4 follows from it.

At `start_intake` the server pins three things and records them in the session:

- **T** — the template catalogue at a fixed version
- **S × A** — the stage and area grid proposed by the agent and accepted into the session
- **K** — the correction budget, an integer

The question space is `Q = T × (S × A)`, of size `|T| · |S| · |A|`, fixed for the session.

Three rules keep it that way:

- **I1 — at most once.** Each `(templateId, cell)` pair instantiates at most once per session. A
  re-instantiation request returns the existing instance.
- **I2 — corrections are budgeted.** Each correction consumes one unit of K. At K=0 further
  corrections are refused with `urn:intake:problem:budget-exhausted`.
- **I3 — unknowns produce requirements, never questions.** An `unknown` answer to a required
  question yields a **discovery requirement in the package**. It MUST NOT instantiate new questions.

**I3 is the fix.** Without it the loop is a branching process: each asked question spawns new ones
with probability `p`, and it halts only while `p · spawn < 1`. Measured across seeds:

| p(unknown) | unbounded spawning (I1 off) | pinned grid (I1 on) |
|---|---|---|
| 0.20 | terminates 10/10, 68 rounds | 10/10, **40 rounds** |
| 0.35 | 10/10, 88 rounds | 10/10, **40** |
| 0.45 | 10/10, 243 rounds | 10/10, **40** |
| **0.50** | 9/10 | 10/10, **40** |
| 0.55 | **0/10** — hit the 5000-round cap | 10/10, **40** |
| 0.70 | **0/10** | 10/10, **40** |
| 0.85 | **0/10** | 10/10, **40** |

Sharp transition at the predicted critical point `p · spawn = 1`, i.e. `p = 0.5`. An unknown-rate
above one half is exactly what an unfamiliar domain looks like — the case intake exists for. The
pinned arm is **flat at 40 rounds** across every rate: the bound does not depend on how much the
user knows. Reproduce with `python3 intake/termination.py --sweep`.

**Cost, stated plainly:** the pinned arm always walks its whole required set — 40 rounds at p=0.2,
where spawning needed 68 but could have needed 22 against a smaller required set. A guaranteed bound
is bought with a fixed floor: you ask every required question even when the user knows everything.
Tuning the floor means choosing a smaller required subset per depth, not relaxing I1. (proposed)

---

## 4. Termination

**Measure.** For session state `s`:

```
mu(s) = ( |Q| - |asked(s)| ,  K - |corrections(s)| )     ordered lexicographically over N x N
```

**Theorem.** Every session terminates in at most `ceil(|Q| / batch_size) + K` advancing rounds.

**Proof.** Each advancing round does at least one of: (a) instantiate one or more unasked members of
Q, strictly decreasing the first component; (b) apply one or more corrections, leaving the first
component unchanged and strictly decreasing the second. A round doing neither is an empty continue,
which rule E1 (§6) makes read-only and non-advancing — it commits nothing and does not increment the
revision. So every advancing round strictly decreases `mu` under lex order. `N x N` under lex order
is well-founded, so no infinite descending chain exists. ∎

**Depth changes re-pin.** Raising `targetDepth` pins a larger catalogue and a new bound; the prior
bound is retained in the session record. Depths are a closed set of three
(`outline`, `requirements`, `detailed_requirements`), so the total is the sum of at most three
bounds. Depth may not be raised after a package is sealed.

**Stop reasons — closed set.** Every session ends in exactly one. Each yields a package. None means
"keep going".

| Stop reason | Meaning |
|---|---|
| `satisfied` | every question required at `targetDepth` is answered, or unknown with a discovery requirement |
| `question-space-exhausted` | all of Q asked, still not satisfied; package carries the residual gaps |
| `correction-budget-exhausted` | K spent |
| `blocked` | a required answer is unknown and the offered resolution was declined |
| `user-stopped` | the user ended it |

Inventing a stop reason outside this set is a protocol violation, following `seam-dispatch`, which
fixes its stop vocabulary rather than letting each caller grow one.

---

## 5. The answer record

The agent maps natural language to question ids. That mapping is the one step nothing can check, and
in the guide's shape it is invisible: a value the agent paraphrased is stored under `source: "user"`.
The protocol's own rule already concedes that source labels are "provenance assertions; they are not
identity authentication or proof of correctness."

**Fix: separate the utterance from the mapping, and label each with its true author.** (proposed)

```json
{
  "questionId": "constraints@Venue/Budget",
  "templateId": "constraints",
  "status": "answered",
  "utterance": {
    "text": "Budget is $1,500. The date is undecided, but it must be a Saturday in October.",
    "turn": 4,
    "source": "user",
    "verbatim": true
  },
  "value": {
    "budget": {"amount": 1500, "currency": "USD"},
    "date_constraint": "Saturday in October",
    "year": null
  },
  "mapping": {
    "source": "agent",
    "model_class": "i-claude-sonnet",
    "catalogue_version": "1.4.0"
  },
  "layer": {"utterance": "L1", "value": "L2", "mapping": "L1"}
}
```

Rules:

- **A1.** `utterance.text` is verbatim and immutable. It is L1: what was said is a fact about the trace.
- **A2.** `value` is derived. Its author is the agent even when its content came from the user, so
  `mapping.source` is `agent`. **Never label a mapped value `user`.**
- **A3.** `status` ∈ `{answered, unknown, proposed, not_applicable}`. `unknown` requires `value: null`.
- **A4.** `not_applicable` requires a reason and is checked against the applicability rule that
  admits it. The rule firing is L1; whether the rule is *right* is L2.
- **A5.** A correction appends a new record for the same `questionId` under a new `requestId`. History
  is never rewritten.
- **A6.** Callers name a **model class**, never a vendor or model — `mapping.model_class` carries
  `i-claude-sonnet`, not a product. (`F-a4-01`: "Callers request a class, never a vendor")

A2 is what makes the trace audit-worthy: a reviewer can read the utterance and judge the mapping.
Without it, the provable dataset contains agent prose wearing a user label.

---

## 6. State

**The append-only event log is the source of truth. The cache is a projection.** Following
`seam-state`, which holds graph and ledger as "two projections of one append-only, tamper-evident
log". A cache that can evict, expire, or lose a second of writes cannot be the record a package
claims provenance from. (proposed, applying `E-seam-state`)

Events: `session.started`, `questions.issued`, `answers.submitted`, `correction.applied`,
`readiness.assessed`, `package.sealed`. Each carries `sessionId`, `revision`, `requestId`, actor, and
the digest of the previous event.

**Commit rules — all L1, all enforced absolutely:**

- **E1 — empty continue is read-only.** A continue with no answers commits nothing, does not increment
  the revision, and MUST NOT treat unanswered questions as answered or advance past a required gap.
- **E2 — one transaction.** Revision compare-and-set, answer append, replay-index write, and readiness
  recompute commit together or not at all. In a cache-backed implementation this is one script, not a
  sequence of commands; issued separately, a crash mid-batch violates E3.
- **E3 — atomic batch.** A validation failure saves no part of a batch.
- **E4 — replay before staleness.** Check `requestId` first: a replayed request with an identical
  payload returns the original response; the same `requestId` with a different payload is
  `urn:intake:problem:replay-conflict`. Checking staleness first would reject a legitimate retry.
- **E5 — the replay index commits inside E2's transaction.** Written afterwards, a crash between the
  two turns a replay into a double-apply.
- **E6 — no eviction.** Session keys carry no TTL and are exempt from eviction until the package is
  sealed. An evicted session silently voids the trace.
- **E7 — pinned reads.** A readiness assessment reads at one revision, so the same question answers
  the same way twice.

---

## 7. The seam to dispatch: acceptance must be runnable

A package is where intake hands off, and it is where the instrument leaks. The guide's own example
acceptance reads *"Both scenarios are included in the readiness assessment"* — prose. No dispatcher
can judge that done, and a decomposition predicate built on fields alone accepts it: measured against
ground truth, a field-only predicate passed **4 of 7** undispatchable units (**57% false accept**).

Acceptance is therefore typed, not free text:

```json
"acceptance": [
  {"kind": "command", "text": "python3 tools/check_roster.py", "expect_exit": 0},
  {"kind": "file",    "text": "docs/roster.json"},
  {"kind": "prose",   "text": "Attendees report the session was useful"}
]
```

- **D1.** A requirement is **dispatch-ready** only if it carries at least one acceptance of kind
  `command` or `file`.
- **D2.** `prose` acceptance is permitted and recorded, but never satisfies D1. Each one is emitted in
  `openQuestions` as an unresolved acceptance.
- **D3.** `package.readiness.dispatchReady` is the conjunction of D1 across requirements. It is
  computed, never asserted.
- **D4.** `executionAuthorized` is always `false`. Outline readiness is not execution readiness.

**Four clauses the server cannot decide.** Whether a `command` acceptance is *meaningful* requires
running it in the consumer's environment, which a remote service cannot do. Measured: of eleven
predicate clauses, five need the client's filesystem, and **all four clauses that cut the false-accept
rate from 57% to 0% are client-side**:

| Clause | Decided where | Why |
|---|---|---|
| `red-now` — the check currently fails | **client** | must execute it |
| `attributed` — its failure names this unit's own output | **client** | must read stderr |
| `skip-clean` — it does not exit 0 while reporting a skip | **client** | must execute and read output |
| `precondition` — its environment prerequisites hold | **split** | server owns probe definitions, client owns results |

A client submits these as a **transcript** — command, exit code, output, repo digest. The server
validates shape and **cannot verify truth**; it has no repo to reproduce against. It detects
disagreement rather than proving correctness: two clients in one environment reporting different exit
codes for one command flags one of them. Say this plainly in any claim about the package — detection
by redundancy is not verification.

`skip-clean` is not hypothetical. In this repo, `bash harness/containment/test.sh --live` exits **0**
while printing `SKIP live mode`. Its task is blocked on credentials never granted; its definition of
done passes anyway. Any readiness keyed on "did the check go green" scores it complete.
(`F-a7-03`: "Those establish well-formedness, not correctness")

---

## 8. Tool surface

`cap-tool-access` draws the line this surface follows: *"A read that changes nothing is not a tool
call, and keeping the two apart is what lets policy and idempotency above treat them differently."*

**Resources** (read-only; no state change, no revision, no idempotency key):

| URI | Returns |
|---|---|
| `intake://catalogue/{version}` | the pinned template catalogue |
| `intake://session/{id}/questions` | the current outstanding batch |
| `intake://session/{id}/package` | the current package or readiness assessment |
| `intake://session/{id}/trace` | the L1 event log for audit |

**Tools** (state-changing; every call carries `requestId`):

| Tool | Input | Output |
|---|---|---|
| `start_intake` | `requestId`, `request`, `targetDepth`, `intendedUse`, proposed grid | session id, revision 1, first batch, **and the computed bound** |
| `continue_intake` | `sessionId`, `requestId`, `expectedRevision`, `answers[]`, `command` | next batch, or package with stop reason |

This is a deliberate change from the guide: **`get_intake` becomes a resource read, not a tool.**
Resuming a session changes nothing, and modelling it as a tool call puts it on the wrong side of the
policy and idempotency boundary.

`start_intake` returning the bound is what makes the stopping point inspectable before the first
question rather than discovered at the end. (proposed)

**Idempotency.** `requestId` keys the replay index per E4/E5. This is not optional bookkeeping: without
it a retried submission reads as a second independent answer, and any agreement measured across
answerers is corrupted by its own retries.

**Identity.** Every event names its actor with a delegation chain. Agreement across answerers is
uncomputable without it — one agent answering twice is indistinguishable from consensus.

---

## 9. Errors

One typed problem object per failure, RFC 9457, from a closed registry. A caller never parses prose.

| Type URI | Raised when |
|---|---|
| `urn:intake:problem:stale-revision` | `expectedRevision` is behind |
| `urn:intake:problem:replay-conflict` | `requestId` reused with a different payload |
| `urn:intake:problem:unknown-question` | `questionId` not instantiated in this session |
| `urn:intake:problem:duplicate-answer` | same `questionId` twice in one batch |
| `urn:intake:problem:answer-type` | `value` does not match the template's `answerType` |
| `urn:intake:problem:budget-exhausted` | correction budget spent |
| `urn:intake:problem:not-applicable-unsupported` | `not_applicable` without a reason or admitting rule |
| `urn:intake:problem:depth-after-seal` | `targetDepth` raised after the package sealed |
| `urn:intake:problem:mapping-source` | a mapped value labelled `source: user` (violates A2) |
| `urn:intake:problem:missing-utterance` | an `answered` row carrying no verbatim utterance (violates A1) |

Every problem object carries the `sessionId` and `revision` as explicit attributes, per
`F-a7-02`: "Correlation must ride on an explicit resource attribute set at dispatch."

---

## 10. Definition of done

Per `F-part-c-04` — "A criterion nothing can fail is not a criterion" — with a deliberate breakage.

| Field | Value |
|---|---|
| **Criterion** | `python3 intake/check_vectors.py && python3 intake/termination.py --prove` |
| **Expected** | measured 2026-09-16: vectors `18 passed, 0 failed`, exit 0; termination `TERMINATION PROVEN: every seed x rate halted within 52 advancing rounds`, exit 0 |
| **Deliberate breakage 1** | `python3 intake/termination.py --break-i1` — drops rule I1, restoring unbounded spawning |
| **Expected failure 1** | measured: exit 1, `TERMINATION NOT PROVEN: 7 of 7 rates violate the bound`; 0/25 terminate at p ≥ 0.55 |
| **Deliberate breakage 2** | `python3 intake/check_vectors.py --break-order` — checks staleness before replay, violating E4 |
| **Expected failure 2** | measured: exit 1, `17 passed, 1 failed -> ['V03']` — isolates exactly the ordering vector |
| **Status** | **measured** for L1. Every L2 claim in this spec remains assessed, never proven — see §1 and §11 |

---

## 11. Open questions and declared gaps

| Gap | Why it stands |
|---|---|
| **Inter-answerer agreement is unmeasured.** | Every measurement in this spec used one answerer. If two answerers decompose one root into different frontiers, §7's predicate measures noise. This is the largest untested assumption here, and the cheapest to close: one root, two isolated answerers, diff the packages. |
| **A wrong probe is a false blocker.** | §7's precondition register converts an unfalsifiable claim into a probe result — but a badly written probe reports a blocker that isn't real. One such probe was written and caught during this session's measurement. The register makes the error global and visible instead of local and silent; it does not remove it. |
| **The grid is chosen by an agent.** | `|Q|` is only finite because someone fixes S and A. A grid too coarse to hold the problem terminates early and calls it `satisfied`. No mechanical check catches this; it is an L2 judgement. |
| **MCP mechanics here are proposed, not sourced.** | This repo records the Model Context Protocol revision as **unverified, search-only** — no specification was fetched from this environment (`cap-tool-access`, standards note). Transport and tool-definition details in §8 must be checked against the published spec before implementation. |
| **Redis is named nowhere above.** | Per `F-part-c-09` — "Products belong in the adapter column only" — §6 specifies an append-only log with a projection. A cache product is one adapter for the projection and belongs in an adapter table, not in this spec. |
