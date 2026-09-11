# Is the card profile the spec?

Row 79 · R7 · bridge.md section 6 step 2.

`examples/reference/README.md` asserts it: *"The specification already exists: the card profile
under `docs/reference/cards/<address>.json` ... **Write the example from the profile.**"* That had
never been tested. This file is the test's output.

## The experiment

One area, `examples/reference/3-core-agent/`, built from exactly one profile,
`docs/reference/cards/3-3.json` (Runtime / Sandbox). Every question the profile could not answer
is written here **at the moment it was hit**, not reconstructed afterwards — a list assembled at
the end is a rationalisation, not a measurement.

## What counts as a profile gap

A question counts here only if its answer had to be *about card 3.3*. Repo-wide conventions — file
layout, test idiom, where a README lives — are `examples/reference/README.md` and
`docs/reference/build-principles.json`'s job, and a card profile that carried them would be the
wrong shape. Questions of that kind are recorded in the second table, "not the profile's job", so
the distinction is visible rather than assumed.

Verdict per row, typed rather than boolean — the same discipline `stamp_verification.py` uses for
quotes, for the same reason (bridge.md section 3b, *never narrate a boolean*):

| verdict | meaning |
|---|---|
| `answered` | the profile states it outright |
| `derivable` | not stated, but forced by a quote the profile already carries |
| `silent` | the profile does not address it and a builder must decide |
| `contradicts` | the profile says something the build showed to be wrong or unbuildable |

## Findings

### 1 · What are the legal values of `status`? — `silent`

3-3.json cites `X-maturity-c-010` for *"status (string, REQUIRED) is the runtime state of the
container."* That tells a builder the field exists and is mandatory. It does not say what may go in
it, and an example that inspects a sandbox has to return something.

The enumeration is in that same record's `snippet`, verbatim and unstamped: `creating`, `created`,
`running`, `stopped`. So the profile pointed at the right record and stopped one sentence short.

**Built anyway as:** the four values above, marked `proposed` in `cards.json` with this reasoning.
**What the profile would have had to say:** cite the enumeration, not only the field's existence.
A card that names a standard's field owes the example its domain, or the example invents one.

### 2 · Can the example's own citations be verified the way the profile's are? — `contradicts`

No, and this is structural rather than a wording gap. `tools/stamp_verification.py`'s
`cited_quotes()` walks `docs/reference/cards/` only — its docstring says *"id -> the set of quotes
card profiles actually draw from that record."* A quote is stamped because **a card profile cites
it**. Measured: of eleven quotes this build needed, the seven already cited by 3-3.json are stamped;
the three status-enumeration lines and one other are verbatim in their record's `snippet` and carry
no stamp, because no card asks for them.

So "write the example from the profile" holds only while the example says nothing the profile does
not already say. The moment it needs one more sentence off the same page, it leaves the
anti-fabrication chain — which is exactly the boundary bridge.md section 4 calls the strong part of
the tooling.

**Built anyway as:** `cards.json` cites only stamped quotes; everything else is `proposed`.
**What would close it:** `cited_quotes()` taking a second corpus, so an example's citations are
stamped by the same pass. One argument, and the guarantee extends. STATUS row 79.

### 3 · What must *not* be on the interface? — `answered`

The hardest design question was which knobs to leave off, and the profile answered it outright.
Its `usage` section cites REF-3-02 for the list of things the platform decides so the caller does
not: *"decide routing, isolation, retries, model tier, budget ceiling, deadline, telemetry,
provenance, the ledger"*. That is why no method in `interface.py` takes a runtime, an image
override, a network mode or a resource limit, and why `test.sh` can assert the caller names none
of them. Without that sentence the obvious interface is a sandbox spec object, which would have
been the wrong card entirely.

Recorded because a sufficiency note that lists only failures is not a measurement either.

### 4 · What makes a *second* adapter genuinely different? — `silent`

`examples/reference/README.md` requires a second adapter that is a different execution model, not
a relabelling. The profile's `tools[]` list looks like the menu for it and is the wrong place to
read: gVisor and Kata Containers are named there as swap candidates, and both are alternative OCI
runtimes — same lifecycle, same call shape, differing only in a string the caller never sees. An
adapter pair built from that list would pass a swap test while proving nothing.

The genuinely different model came out of `gaps[1]` instead: the warm-pool template/claim split,
*"The SandboxTemplate describes the pod the warm pool keeps ready"*. So the profile held the
answer, filed under what the repo has *not* built rather than under what fills the card.

**Built anyway as:** `adapters/second.py`, a warm pool whose template is prepared by `unpack`, so
a unit claimed from it never passes through `creating` and a cold-created one does. The difference
is a lifecycle the caller can read back, not a label — which is the test a `swap_axis` field would
have to pass.
**What the profile would have had to say:** which axis a second implementation must differ on.
`tools[]` is a list of things that fill the card; it does not rank them by how far apart they are.

### 5 · What happens when it fails? — `silent`

Nothing in 3-3.json describes a failure. Not what an unpack does with an image that is not there,
not what a run does when the pool is exhausted, not whether a failure is typed, not what a caller
matches on. The card's whole evidence base is the happy path plus a status field.

**Built anyway as:** one error, `ClaimedNotMeasured`, for the one failure the profile *does*
describe — the live path that has never run. Every other failure mode is absent from this example
because inventing an error taxonomy is exactly the licence `examples/reference/README.md` refuses:
*"If the profile does not say it, either the profile is incomplete or the claim is not sourced."*
**What the profile would have had to say:** the card names a standard; that standard's error
behaviour is part of the contract the card claims to be checked against.

### 6 · Which operations are on the contract? — `silent`

`unpack`, `run`, `inspect`, `stop` are what the two cited quotes support. Whether pause, resume,
snapshot or fork belong is unanswerable from the profile — and the answer is sitting in the
`claim` field of `X-maturity-c-010`, which the repo's own rule forbids quoting, because a `claim`
is this repo's prose about a page rather than the page (bridge.md section 3b). The profile cites
that record twice and never for this.

**Built anyway as:** four methods, and no snapshot verb.
**What the profile would have had to say:** the operation set, cited. A card that defines a
boundary owes the example its verbs.

### 7 · Where do the caller's field names come from? — `derivable`, and uncomfortably

`Unit(unit_id, intent, profile)` is not arbitrary: `intent` and `profile` are named in the
profile's own `usage.text`, which describes a caller writing an intent and one word of profile.
But that phrase sits in the repo's *prose* around the REF-3-02 citation, not inside the quote. So
the field names of the public interface trace to text that no gate checks and no stamp covers.

It is the right answer and it arrived through the weakest link in the chain. Recorded rather than
resolved: the alternative was to invent names, which is worse.

## Verdict

Twelve questions. **Seven were hit by the author building the area; five more by an isolated
reviewer** who saw only the card and the contract and wrote the deciding check. Counted over all
twelve, by the typed verdicts above:

| verdict | count | which |
|---|---|---|
| `answered` | 1 | what must *not* be on the interface (3) |
| `derivable` | 1 | the caller's field names (7) — and only from uncited prose |
| `silent` | 9 | status domain (1) · swap axis (4) · failures (5) · operation set (6) · lifecycle order (8) · `stop`/`stopped` (9) · profile vocabulary and where it applies (10) · warm semantics (11) · what an unmeasured path returns (12) |
| `contradicts` | 1 | the example's citations cannot be stamped the way the profile's are (2) |

**Ten of twelve needed a decision the profile could not supply**, and an eleventh was answerable
only from prose no gate checks. The claim under test was `examples/reference/README.md`'s: *"Write
the example from the profile."*

**It does not hold.** The profile is a sound *evidence base* and an incomplete *specification*.
Every question it answered, it answered well and with a citation, and it never once said something
the build showed to be wrong about card 3.3. But the silences are all of one kind: the card
describes what a boundary **is** and cites a standard for it, and never what the boundary **does**
— its verbs, their order, its value domains, its failures, and where the caller's one knob applies.

Two things make this the cheaper of the two possible answers. The problem is coverage, not
accuracy. And the single most valuable sentence in the profile — the one that decided the whole
interface shape, finding 3 — was sourced, which is the part that would have been expensive to fix.

**The independent reader was worth more than the author's own list.** Five of the twelve findings
are theirs, including the one the area actually got *wrong* (finding 10) — a defect that eighteen
author-written assertions passed straight over. A hidden check is not a formality here; on this
single trial it was the only thing that caught a real defect.

### The denominator

**One card of forty, two readers, and a `built` infrastructure card at that.** Card 3.3 defines a boundary, so
the four things it failed to supply — verbs, value domains, failure modes, what makes a swap real
— are exactly the four a boundary card needs, and that is part of why they surfaced together. Say
which of the recommendations below travel, and which may be an artifact of this card's kind:

- `failures` and `swap_axis` generalise. Every card in the model names a seam that something can
  fail at and that something else could implement; both questions get asked again on card 3.1 and
  on card 6.1.
- `operations` and `domain` are sharper for a card that wraps a standard with an API surface.
  A card like 7.2, which describes a practice rather than an interface, may have nothing to put in
  them. Treat those two as *required where the card names a standard's field or verb*, not as
  required everywhere.

> **Narrowed on evidence, 2026-09-11.** Card 1.5 Agent-to-Agent was profiled with all five fields.
> It is a protocol entry point, not a boundary card — the second kind the hedge above asked for —
> and its source filled `operations` (eleven, named and binding-independent), `domain` (terminal and
> interrupted task states, quoted) and `failures` (nine typed errors, each with its condition)
> outright. Those are exactly the three 3.3 was silent on. So they are **not** artifacts of a
> boundary card, and the hedge now applies only to the remaining case: a card describing a practice
> rather than an interface. `swap_axis` and `vocabulary` stayed `proposed` on 1.5 — `swap_axis` for
> an administrative reason rather than an evidential one, since the reference stack names the pick
> at that port and cannot be cited until STATUS row 89 closes.

> **Narrowed again, 2026-09-11, on card 6.1 Telemetry** — the card this note named above as the
> re-test for `failures` and `swap_axis`. Both are sourced, and `swap_axis` is sourced *outright*
> for the first time, which 1.5 could not manage. The mechanism generalises, so it is worth stating:
> OTLP states its own **scope limit** — it guarantees delivery for one client/server hop and puts
> end-to-end delivery across intermediate nodes outside its scope. A scope limit is what a swap axis
> is made of. The sharper instruction is therefore not "what must a second implementation differ on"
> but **"where does this card's standard say what it does not guarantee"** — that is the boundary two
> implementations can sit on opposite sides of while both conform. On 6.1 it made the axis
> collector-in-path versus direct-export, and it ruled out both obvious candidates: the
> instrumentation library (the backend's own docs call that side interchangeable) and the backend
> vendor (two OTLP backends are, from the caller's side, exactly the relabelling the standard exists
> to permit).
>
> **The first measured limit of the five-field schema itself rather than of a card.** 6.1 has one
> operation, Export. So `operations`' second half — *and the order they occur in*, added because card
> 3.3's four-verb lifecycle made order the load-bearing question — has nothing to hold. A one-verb
> boundary has no verb order, and a reader who takes the empty half as a silence in the source will
> be wrong. The field wants rewording: the verb set, **and the order where there is more than one
> verb**, plus what a conformance check may assert instead when there is not.
>
> **`vocabulary`'s platform-mapping half is now 0 for 3.** On 3.3, 1.5 and 6.1 alike the standard
> supplies the configurable words and their legal values, and nothing supplies the join between those
> and this repo's own `intent:` / `profile:` vocabulary — because that join belongs to an adapter, and
> no adapter exists at any of the three cards. Three of three is a measurement rather than a hedge:
> that half stays `proposed` on every card until something is built, and it should be read as a
> statement about this repo rather than about the sources.
>
> **A tooling finding, recorded because no gate would have said it.**
> `schemas/card-profile.schema.json` declares `additionalProperties: false` and did not list the five
> fields, so the schema *forbade* exactly what `validate_card_profiles.py` had been checking since they
> were added — and 1-5.json was the only profile in violation. Nothing enforces that schema: it is
> referenced by `docs/reference/cards/BRIEF.md` and by no tool, so the contradiction sat green. The
> five fields plus `schema_note` were added to it as optional properties on 2026-09-11 — additive,
> `required` unchanged, all 33 prior profiles still conforming, checked by a plant that rejected
> 1-5.json against the old property set by all six field names. The finding to keep is not the fix:
> **this repo has a declared shape with no gate behind it**, which is the same shape of defect as a
> `KNOWN_RED` excuse — something that reads as coverage and is not.

A second area, built from a profile of a different kind, would settle it. That is one area of work,
not nine, and it is worth doing before eight profiles are authored against a schema this note
proposes on the strength of one.

## What the eight new profiles should carry — step 3 input

This is the reason step 2 was ordered before step 3. Adding these to the profile schema *before*
eight more are authored costs a schema change; adding them after costs forty rewrites.

| add | what it holds | from findings |
|---|---|---|
| `operations` | the verb set this boundary exposes **and the order they occur in**, cited. A card that defines a boundary owes the example its verbs; without the order, the check that decides whether two implementations differ has nothing to stand on. | 6 · 8 · 9 |
| `domain` | for every standard field the card names, its legal values — not only that the field is required | 1 |
| `failures` | the typed failures at this boundary, cited to the standard the card already claims to be checked against, **including what a path that has never run must return** | 5 · 12 |
| `swap_axis` | what a second implementation must differ on for the swap to be real. `tools[]` lists what fills the card and does not rank by distance; two entries there can be the same execution model. | 4 · 11 |
| `vocabulary` | for every configurable word the card grants a caller: its legal values **and the step it applies at**. A knob whose step is unstated is a knob that can be built unreachable — and was. | 10 |

The fifth row is the one to take most seriously, because it is the only one with a demonstrated
casualty rather than an argued one.

One change is not to the schema. `usage.text` is where the caller-facing vocabulary actually lives
(`intent:`, `profile:`) and it is uncited repo prose — the field names of a public interface should
not trace to the weakest link in the chain. Either cite it or move it into a claim that is cited.

And one is to the tooling, not the profiles: `tools/stamp_verification.py`'s `cited_quotes()`
should take a second corpus, so an example's own citations are stamped by the same pass that
stamps a card's. Until then, "write the example from the profile" is also a hard limit on what an
example may *say* — finding 2.

## Not the profile's job

- **Where files go, what a gate looks like, how an adapter is registered.** Answered by
  `examples/reference/README.md` and the archived areas' shape. A card profile carrying this would
  be the wrong artifact, and every card would carry the same copy.
- **`prose_gate.py --corpus <dir>` reports the wrong corpus.** It checks the directory it was
  given and then prints `corpus: docs/reference/cards only`. The check is right and the line under
  it is false, which is the exact shape of defect the gate exists to catch. Found while running it
  against this area; not fixed here, because it belongs to the tool's row and not to row 79.
- **A green prose gate can mean it read nothing.** The first run against this area reported
  `0 of 0 prose spans` — the claims embedded their sources as running prose with no quotation
  marks, so `QUOTE_RE` matched nothing and the gate passed without checking a single span.
  Quotation marks were added and the same run then reported `6 exact`. Worth knowing before a
  green from this tool is read as coverage.
- **This note's own structure nearly ate three of these.** Findings 3 to 7 were appended under
  this heading rather than under Findings, and the three bullets above were dropped by a
  replacement that silently matched nothing. Caught by reading the file back. A note written
  incrementally during a build needs the same read-back as the build.

## An independent reader's list

Findings 1 to 7 are the author's, hit while building. These are not. An isolated reviewer was
given card 3.3's profile and the area's contract, told explicitly not to open `test.sh`,
`README.md`, `cards.json` or this note, and asked to write the deciding check —
`docs/night/hidden/3-core-agent.sh`. They were also asked what the profile did not tell them.

They independently reported finding 1 (the status values are not in the card). The rest below are
theirs alone, and none had occurred to the author.

### 8 · In what order do the states occur? — `silent`

Nothing in the card says `creating` precedes `created` precedes `running`, or that a claim against
a warm pool may skip `creating`. Both the conformance check's ordering rule and the assertion that
decides whether the two adapters are a genuine swap rest on an order the card never states. The
reviewer called this the most load-bearing gap of the set, and they are right: it is the one that
the example's central claim depends on.

### 9 · Where do `stop` and `stopped` come from? — `silent`

The card's evidence yields `unpack` → `run` and a required `status`. It gives no `stop` verb and no
terminal state. Both are asserted by this area on `interface.py`'s authority alone. The same gap as
finding 6, found from the other side — which is some evidence it is real rather than a matter of
taste.

### 10 · What are the legal values of `profile`, and where does it apply? — `silent`

The card grants the caller *"one word of `profile:`"* and never says what words, nor at which step
it takes effect. That second half is not academic. **The reviewer's check failed the area on it.**
An earlier cut of this interface took `profile` only on `Unit`, which reaches `run` — while the
bundle is chosen in `unpack`. So the caller's one configurable word could never select anything,
and `Unit.profile` was dead as declared. Eighteen author-written checks passed over it; the first
run of the hidden check caught it (`h-10`, `hidden passed 9, failed 1`).

**Built anyway as:** `unpack(image, profile)`, with the bundle carrying the profile it was resolved
for, and a conformance check that two profiles must not return the same bundle.
**What the profile would have had to say:** where the caller's one configurable word applies. A
card that grants a knob owes the example the step it turns.

### 11 · Is a warm pool warmed ahead of demand, or on first use? — `silent`

The card's only warm-pool evidence is the one SandboxTemplate sentence, and its own `gaps[1]` says
the split is not built here. So what `warm` must *mean* came from this area's adapter docstring and
nothing else. The reviewer flagged the consequence: priming the pool inside `unpack` conflates
preparing a bundle with pre-warming a running instance, and it erases the "first claim pays, later
claims reuse" moment that a lazily-warmed pool would show.

Both readings fit the cited sentence. This area chose *ready ahead of demand*, because that is what
"the pod the warm pool keeps ready" says most plainly — but the card does not decide it, and a
different author would have built the other one and cited the same sentence.

### 12 · What must a path that has never run return? — `silent`

The card establishes that the live path is claimed rather than measured. It says nothing about what
such a path must *do* when called. `ClaimedNotMeasured` and the rule that it must refuse rather
than return a plausible value are this area's invention. They are, in the reviewer's words, not
something the card hands you to check against — which is uncomfortable, because it is the single
behaviour keeping a claimed path from reading as a measured one.
