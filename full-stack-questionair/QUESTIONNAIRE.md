# Future-State Conformance Questionnaire

**Generated file — do not edit.** It is produced from a property list; edits here are overwritten and, worse, silently diverge from what the checker grades.

**144 questions over 42 properties.** Every property is examined from three or four independent angles. That is deliberate and it is the core of the method: **a single question is not a measurement.** Three questions answerable from one paragraph are one question wearing three hats, so each angle below is answered by a *different artifact* — a contract, a worked case, a breaking input, a second adapter.

## The angles, and why each exists

| Angle | Asks | Fails when |
|---|---|---|
| **Declaration** | Where does the deliverable state the contract for **⟨this property⟩**? Quote the contract, not a description of it. | the property is named but never specified |
| **Demonstration** | Show one worked case of **⟨this property⟩** in operation, including what it refuses or how it fails. A happy path alone does not answer this. | the property is specified but never exercised, so its edges are unknown |
| **Falsification** | What observation would prove **⟨this property⟩** is not true of this design, and what in the deliverable could be inspected or run to attempt it? | the property is unfalsifiable, which makes it an intention rather than a contract |
| **Substitution** | Name a second adapter for **⟨this property⟩** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know. | the interface is shaped around its current implementation and only looks swappable |

## How to answer

**A bare yes, no, or maybe is not an answer.** Every question takes one verdict, and no verdict may be recorded without evidence.

| Verdict | Means | What it must carry |
|---|---|---|
| `CONFORMS` | The design does this | The evidence: a quote, a contract, a named section |
| `DEVIATES` | The design knowingly does not do this | What is given up, and why that was acceptable |
| `SUPERSEDES` | **The design does something better than what was asked** | What the asked-for version buys, what this version preserves instead, and what it costs. This is the highest bar in the instrument |
| `ABSENT` | No basis in the deliverable | Nothing — but say so rather than leaving it blank |
| `UNANSWERABLE` | The question is malformed against this design | Why. **This is logged against the questionnaire, not against the design** |

`SUPERSEDES` exists because an instrument that only accepts conformance punishes the outcome it wanted. A better answer than the one asked for is a good result — it simply carries a heavier burden of proof than agreement does.

`UNANSWERABLE` exists because questionnaires are wrong sometimes. When this instrument's ancestor was run at scale, **two of four rejections turned out to be defects in the checker rather than in the work** — a 50% false-positive rate on the one signal meant to be authoritative. Without an escape hatch, a bad question becomes a false finding about a good design.

### Evidence tiers, and the rule that makes them bite

| Tier | Is |
|---|---|
| `E1` | A quoted contract, schema, or interface signature |
| `E2` | A named section plus a worked example |
| `E3` | A claim in prose |
| `E4` | An inference drawn by the reader |

**A `CONFORMS` supported only by `E3` or `E4` is not a `CONFORMS`.** It records as asserted-but-unproven. This is the difference between claimed and measured, made mechanical rather than left to judgement.

### Answer format

One JSON object per line, in a file named `answers.jsonl`. One line per question, all questions present:

```json
{"qid": "S2-F", "verdict": "CONFORMS", "evidence_tier": "E1", "evidence": "State contract, section 4.2: 'Two payload shapes cross this boundary: Node and LedgerRow. Nothing else.' Payload registry lists exactly those two.", "falsifier": "Enumerate contracts referenced by any inbound seam; a third distinct schema would falsify it.", "cost_statement": null, "note": ""}
```

`cost_statement` is required when and only when the verdict is `SUPERSEDES`. `falsifier` is required on every `CONFORMS`: if you cannot say what would disprove it, you have described an intention.

---

## Design rules

### R1 — the core importing interfaces and never implementations

*Source: brief B1 rule 1. Answered by: the core's import surface, module boundary, or dependency declaration.*

**R1-D · Declaration**

Where does the deliverable state the contract for **the core importing interfaces and never implementations**? Quote the contract, not a description of it.

**R1-M · Demonstration**

Show one worked case of **the core importing interfaces and never implementations** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**R1-F · Falsification**

Name one implementation type that appears anywhere in the core's own signatures. If none does, state how that is enforced rather than merely intended.

> **Why this is asked.** An architecture diagram showing interfaces is not evidence; the import surface is. A rule with no enforcement point degrades on the first deadline.

### R2 — each interface naming the standard that governs it

*Source: brief B1 rule 2. Answered by: the capability table's standard column, with version.*

**R2-D · Declaration**

Where does the deliverable state the contract for **each interface naming the standard that governs it**? Quote the contract, not a description of it.

**R2-M · Demonstration**

Show one worked case of **each interface naming the standard that governs it** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**R2-F · Falsification**

For each interface where a standard is cited, was the standard's relevant section actually read, and which section? For each where none is cited, what was searched?

> **Why this is asked.** A standard named but unread is a citation, not an adoption. Sixty-six novelty claims in a comparable exercise turned out to be recall rather than retrieval, and one genuine fetch overturned a claim outright.

### R3 — swappability as a tested property rather than an intention

*Source: brief B1 rule 3. Answered by: a second adapter design per interface, not a list of candidate product names.*

**R3-D · Declaration**

Where does the deliverable state the contract for **swappability as a tested property rather than an intention**? Quote the contract, not a description of it.

**R3-M · Demonstration**

For one interface, show the second adapter in enough detail that its differences from the first are visible. Naming a product is not a second adapter.

> **Why this is asked.** The brief's own table already lists swap candidates. Restating that list proves nothing that was not already true before the work started.

**R3-F · Falsification**

Which interface would be hardest to re-adapt, and what specifically about its shape makes that so?

> **Why this is asked.** A design where every interface is claimed equally swappable has not been tested against any of them.

### R4 — a caller needing no client library we wrote

*Source: brief B1 rule 4. Answered by: the integration surface a third party would code against.*

**R4-D · Declaration**

Where does the deliverable state the contract for **a caller needing no client library we wrote**? Quote the contract, not a description of it.

**R4-M · Demonstration**

Show one worked case of **a caller needing no client library we wrote** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**R4-F · Falsification**

What observation would prove **a caller needing no client library we wrote** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### R5 — cost being knowable before commitment, with planning as a pure function

*Source: brief B1 rule 5. Answered by: the planner's signature and its declared side-effect freedom.*

**R5-D · Declaration**

Where does the deliverable state the contract for **cost being knowable before commitment, with planning as a pure function**? Quote the contract, not a description of it.

**R5-M · Demonstration**

Show one worked case of **cost being knowable before commitment, with planning as a pure function** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**R5-F · Falsification**

What would a planner call have to do for the purity claim to be false, and does anything in the design prevent it? Name the enforcement, not the convention.

> **Why this is asked.** Purity asserted in prose and unenforced in the type or call surface is a comment. The first probe added for convenience breaks it silently.

### R6 — the grader never being visible to the graded

*Source: brief B1 rule 6. Answered by: the dispatch payload's field list, shown to contain no criterion-shaped field.*

**R6-D · Declaration**

Where does the deliverable state the contract for **the grader never being visible to the graded**? Quote the contract, not a description of it.

**R6-M · Demonstration**

Show one worked case of **the grader never being visible to the graded** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**R6-F · Falsification**

List every field that reaches an executing agent. Which of them could carry, hint at, or be used to infer the criterion it will be judged against?

> **Why this is asked.** This invariant spans the whole architecture rather than sitting inside one boundary, so it fails by accumulation: one convenience field at a time. The moment the executing side can infer its criterion, every verdict produced afterwards stops being held out.

### R7 — cross-cutting guarantees being applied by the platform, not requested by the caller

*Source: brief B1 rule 7. Answered by: the call surface, shown to have no opt-out parameter for any cross-cutting concern.*

**R7-D · Declaration**

Where does the deliverable state the contract for **cross-cutting guarantees being applied by the platform, not requested by the caller**? Quote the contract, not a description of it.

**R7-M · Demonstration**

Show one worked case of **cross-cutting guarantees being applied by the platform, not requested by the caller** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**R7-F · Falsification**

Is there any path by which a caller obtains execution without one of these guarantees attached? Include internal callers, retries, and administrative paths.

> **Why this is asked.** Guarantees are usually skippable through the back door built for testing, and that door becomes the fast path under pressure.

## Owned core

### K1 — Document as declared intent, definition of done, and steps

*Source: brief B2 Document. Answered by: the document schema.*

**K1-D · Declaration**

Where does the deliverable state the contract for **Document as declared intent, definition of done, and steps**? Quote the contract, not a description of it.

**K1-M · Demonstration**

Show one worked case of **Document as declared intent, definition of done, and steps** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**K1-F · Falsification**

What observation would prove **Document as declared intent, definition of done, and steps** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### K2 — Planner as a pure function from document to plan and cost

*Source: brief B2 Planner. Answered by: the planner's signature and cost model.*

**K2-D · Declaration**

Where does the deliverable state the contract for **Planner as a pure function from document to plan and cost**? Quote the contract, not a description of it.

**K2-M · Demonstration**

Show one document priced, including a case the planner refuses to price and what it returns instead.

> **Why this is asked.** A planner that prices everything has no failure mode, which means it has no opinion about what it cannot know.

**K2-F · Falsification**

What observation would prove **Planner as a pure function from document to plan and cost** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### K3 — Graph as typed nodes and typed edges of existence, interface and implementation

*Source: brief B2 Graph. Answered by: the node and edge type definitions.*

**K3-D · Declaration**

Where does the deliverable state the contract for **Graph as typed nodes and typed edges of existence, interface and implementation**? Quote the contract, not a description of it.

**K3-M · Demonstration**

Show one worked case of **Graph as typed nodes and typed edges of existence, interface and implementation** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**K3-F · Falsification**

Construct an edge the type system should reject, and show what rejects it.

> **Why this is asked.** A type system described but not exercised against an illegal case is a naming convention.

### K4 — Judge as a pure function from result and criterion to verdict

*Source: brief B2 Judge. Answered by: the judge's signature and verdict vocabulary.*

**K4-D · Declaration**

Where does the deliverable state the contract for **Judge as a pure function from result and criterion to verdict**? Quote the contract, not a description of it.

**K4-M · Demonstration**

Show one worked case of **Judge as a pure function from result and criterion to verdict** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**K4-F · Falsification**

Show a result the judge must fail, and confirm it does. Then show that the criterion was not derivable from the result itself.

> **Why this is asked.** A check whose expectation is derived from the thing it checks asserts a constant. It passes forever and is indistinguishable from a working check until it matters.

### K5 — Ledger as append-only across runs and the deduplication authority

*Source: brief B2 Ledger. Answered by: the ledger row shape and its duplicate-key behaviour.*

**K5-D · Declaration**

State the deduplication key exactly, and what happens on a second write at that key.

> **Why this is asked.** Without a stated key a retry either double-charges or skips work it never did, and both outcomes look like success from outside.

**K5-M · Demonstration**

Show one worked case of **Ledger as append-only across runs and the deduplication authority** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**K5-F · Falsification**

What observation would prove **Ledger as append-only across runs and the deduplication authority** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

## Capability interfaces

### C01 — isolation of a unit of work

*Source: brief B3 Isolation. Answered by: the isolation interface contract and its adapter table.*

**C01-D · Declaration**

Where does the deliverable state the contract for **isolation of a unit of work**? Quote the contract, not a description of it.

**C01-M · Demonstration**

Show one worked case of **isolation of a unit of work** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C01-F · Falsification**

Separate the authority required to start an isolated unit from the authority required to communicate with it. Are they the same? If the design assumes they are, what makes that true?

> **Why this is asked.** On a comparable stack these are different gates. A policy rule granted a privilege-free start while the process binding the control socket refused to run unprivileged, producing units that boot cleanly and cannot be driven. Both halves read as complete answers on their own.

**C01-S · Substitution**

Name a second adapter for **isolation of a unit of work** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C02 — model access behind a completions-shaped interface

*Source: brief B3 Model access. Answered by: the model access interface contract and its adapter table.*

**C02-D · Declaration**

Where does the deliverable state the contract for **model access behind a completions-shaped interface**? Quote the contract, not a description of it.

**C02-M · Demonstration**

Show one worked case of **model access behind a completions-shaped interface** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C02-F · Falsification**

Does the interface distinguish a call the gateway routes and reshapes from one it passes through to a provider's native API? State which capabilities and which authentication scheme exist on each.

> **Why this is asked.** A capability was once reported absent from an entire gateway after checking only the reshaping path; the native API had supported it all along through a passthrough route on the same gateway. Authentication also differs per route, and sending the wrong scheme returns an error indistinguishable from a bad credential.

**C02-S · Substitution**

Name a second adapter for **model access behind a completions-shaped interface** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C03 — durable execution of long-running work

*Source: brief B3 Durable execution. Answered by: the durable execution interface contract and its adapter table.*

**C03-D · Declaration**

Where does the deliverable state the contract for **durable execution of long-running work**? Quote the contract, not a description of it.

**C03-M · Demonstration**

Show one worked case of **durable execution of long-running work** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C03-F · Falsification**

Where do model calls and other nondeterministic operations sit relative to code the engine replays? Name the boundary that keeps them out.

> **Why this is asked.** A durable engine re-executes its own code to rebuild state. A nondeterministic call inside that code breaks replay, and the failure is intermittent and appears in production rather than in tests. This is the most common way a first design of this shape is wrong.

**C03-S · Substitution**

Name a second adapter for **durable execution of long-running work** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C04 — agent runtime behind an agent protocol

*Source: brief B3 Agent runtime. Answered by: the agent runtime interface contract and its adapter table.*

**C04-D · Declaration**

Where does the deliverable state the contract for **agent runtime behind an agent protocol**? Quote the contract, not a description of it.

**C04-M · Demonstration**

Show one worked case of **agent runtime behind an agent protocol** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C04-F · Falsification**

Is any state required to resume work keyed to one vendor's session format? And does a recorded result about the runtime carry the build version it was produced against?

> **Why this is asked.** A vendor resume key welds the runtime to one supplier regardless of what the adapter table claims. Separately, five recorded failures on a comparable stack all predated the installed build by five hours: the entire result was stale, nothing caught it, and no verdict recorded the version it was produced against.

**C04-S · Substitution**

Name a second adapter for **agent runtime behind an agent protocol** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C05 — tool access behind a tool protocol

*Source: brief B3 Tool access. Answered by: the tool access interface contract and its adapter table.*

**C05-D · Declaration**

Where does the deliverable state the contract for **tool access behind a tool protocol**? Quote the contract, not a description of it.

**C05-M · Demonstration**

Show one tool registered and reached through the interface, and one call the interface refuses.

> **Why this is asked.** An endpoint that is live, authenticated and has zero tools registered satisfies every structural check while delivering nothing. Reachability is the property, not availability.

**C05-F · Falsification**

What observation would prove **tool access behind a tool protocol** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

**C05-S · Substitution**

Name a second adapter for **tool access behind a tool protocol** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C06 — capability packaging behind a portable definition format

*Source: brief B3 Capability packaging. Answered by: the packaging interface contract and its adapter table.*

**C06-D · Declaration**

Where does the deliverable state the contract for **capability packaging behind a portable definition format**? Quote the contract, not a description of it.

**C06-M · Demonstration**

Show one worked case of **capability packaging behind a portable definition format** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C06-F · Falsification**

What observation would prove **capability packaging behind a portable definition format** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

**C06-S · Substitution**

Name a second adapter for **capability packaging behind a portable definition format** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C07 — work intake from conformant producers

*Source: brief B3 Work intake. Answered by: the intake interface contract and its adapter table.*

**C07-D · Declaration**

Where does the deliverable state the contract for **work intake from conformant producers**? Quote the contract, not a description of it.

**C07-M · Demonstration**

Show one worked case of **work intake from conformant producers** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C07-F · Falsification**

What observation would prove **work intake from conformant producers** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

**C07-S · Substitution**

Name a second adapter for **work intake from conformant producers** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C08 — document validation against a published schema dialect

*Source: brief B3 Document validation. Answered by: the validation interface contract and its adapter table.*

**C08-D · Declaration**

Where does the deliverable state the contract for **document validation against a published schema dialect**? Quote the contract, not a description of it.

**C08-M · Demonstration**

Show one worked case of **document validation against a published schema dialect** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C08-F · Falsification**

What observation would prove **document validation against a published schema dialect** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

**C08-S · Substitution**

Name a second adapter for **document validation against a published schema dialect** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C09 — telemetry emitted on an open wire format

*Source: brief B3 Telemetry. Answered by: the telemetry interface contract and its adapter table.*

**C09-D · Declaration**

Where does the deliverable state the contract for **telemetry emitted on an open wire format**? Quote the contract, not a description of it.

**C09-M · Demonstration**

Show one worked case of **telemetry emitted on an open wire format** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C09-F · Falsification**

Is there one identifier that resolves in every plane a unit of work touches, and is correlation established at dispatch rather than reconstructed afterwards? Name the planes and confirm the identifier resolves in each.

> **Why this is asked.** An identifier present in three planes out of four answers no question, and the missing plane is always the one needed during an incident. Reconstruction from timing is a guess that is confidently wrong under concurrency, which is the only condition where it is needed.

**C09-S · Substitution**

Name a second adapter for **telemetry emitted on an open wire format** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C10 — policy decisions behind a decision API

*Source: brief B3 Policy. Answered by: the policy interface contract and its adapter table.*

**C10-D · Declaration**

Where does the deliverable state the contract for **policy decisions behind a decision API**? Quote the contract, not a description of it.

**C10-M · Demonstration**

Show the exact point in the execution path where a policy decision is consulted, and show one refusal occurring before any spend.

> **Why this is asked.** Policy engines are routinely present, conformant and not wired into the enforcement path. A named engine in a capability table is not a gate; the call site is.

**C10-F · Falsification**

What observation would prove **policy decisions behind a decision API** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

**C10-S · Substitution**

Name a second adapter for **policy decisions behind a decision API** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C11 — provenance as verifiable attestation

*Source: brief B3 Provenance. Answered by: the provenance interface contract and its adapter table.*

**C11-D · Declaration**

Where does the deliverable state the contract for **provenance as verifiable attestation**? Quote the contract, not a description of it.

**C11-M · Demonstration**

Show one worked case of **provenance as verifiable attestation** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C11-F · Falsification**

Can an artifact's attestation be verified by a tool the design's authors did not write? Name the tool.

> **Why this is asked.** Self-verified provenance is a log. The brief asks for verifiability with an independent tool, which is a materially stronger claim.

**C11-S · Substitution**

Name a second adapter for **provenance as verifiable attestation** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C12 — errors as typed, machine-readable values

*Source: brief B3 Errors. Answered by: the error interface contract and its adapter table.*

**C12-D · Declaration**

Where does the deliverable state the contract for **errors as typed, machine-readable values**? Quote the contract, not a description of it.

**C12-M · Demonstration**

Show one worked case of **errors as typed, machine-readable values** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C12-F · Falsification**

Is there any path where a caller must parse prose to determine what happened? Include timeouts, upstream provider errors and cancellation.

> **Why this is asked.** Error typing usually holds on the paths that were designed and fails on the ones inherited from an adapter, which are exactly the paths that fire in production.

**C12-S · Substitution**

Name a second adapter for **errors as typed, machine-readable values** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C13 — identity of actors, including delegated agent actors

*Source: brief B3 Identity. Answered by: the identity interface contract and its adapter table.*

**C13-D · Declaration**

State the field that carries actor identity, where it originates, and how a delegation chain is represented when an agent acts on behalf of a human.

> **Why this is asked.** Systems of this shape frequently have no identity field anywhere at all, and the absence is invisible because nothing fails without it until an audit asks who did something.

**C13-M · Demonstration**

Show one worked case of **identity of actors, including delegated agent actors** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C13-F · Falsification**

What observation would prove **identity of actors, including delegated agent actors** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

**C13-S · Substitution**

Name a second adapter for **identity of actors, including delegated agent actors** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C14 — scheduling on a published recurrence format

*Source: brief B3 Scheduling. Answered by: the scheduling interface contract and its adapter table.*

**C14-D · Declaration**

Where does the deliverable state the contract for **scheduling on a published recurrence format**? Quote the contract, not a description of it.

**C14-M · Demonstration**

Show one worked case of **scheduling on a published recurrence format** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C14-F · Falsification**

What starts a run? If the answer is a person, say so plainly.

> **Why this is asked.** A cadence with a human trigger is an intention rather than a mechanism, and it does not survive the first week nobody is looking.

**C14-S · Substitution**

Name a second adapter for **scheduling on a published recurrence format** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C15 — idempotency of externally-triggered actions

*Source: brief B3 Idempotency. Answered by: the idempotency interface contract and its adapter table.*

**C15-D · Declaration**

Where does the deliverable state the contract for **idempotency of externally-triggered actions**? Quote the contract, not a description of it.

**C15-M · Demonstration**

Show one worked case of **idempotency of externally-triggered actions** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C15-F · Falsification**

The brief records a key on the wire with no lease. What happens when two callers present the same key concurrently?

> **Why this is asked.** A key without a lease is a convention between well-behaved callers. Concurrency is precisely the case it was introduced to handle.

**C15-S · Substitution**

Name a second adapter for **idempotency of externally-triggered actions** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### C16 — state persistence behind a storage-neutral interface

*Source: brief B3 State persistence. Answered by: the persistence interface contract and its adapter table.*

**C16-D · Declaration**

Where does the deliverable state the contract for **state persistence behind a storage-neutral interface**? Quote the contract, not a description of it.

**C16-M · Demonstration**

Show one worked case of **state persistence behind a storage-neutral interface** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**C16-F · Falsification**

What observation would prove **state persistence behind a storage-neutral interface** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

**C16-S · Substitution**

Name a second adapter for **state persistence behind a storage-neutral interface** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

## Cross-cutting, applied not requested

### X1 — a budget ceiling on every unit, terminating the unit and not the platform

*Source: brief B4 Budget. Answered by: the enforcement point and what it does on breach.*

**X1-D · Declaration**

Where does the deliverable state the contract for **a budget ceiling on every unit, terminating the unit and not the platform**? Quote the contract, not a description of it.

**X1-M · Demonstration**

Show one worked case of **a budget ceiling on every unit, terminating the unit and not the platform** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**X1-F · Falsification**

Is spend observable on every route a unit can take, and how would the design detect a route where it is not?

> **Why this is asked.** A real, successful call on one stack's default lane moved recorded spend by exactly zero. The ceiling was proven on one route and unproven on the route actually in use, which makes the cap a claim rather than a control.

### X2 — every action naming an actor, with explicit delegation chains

*Source: brief B4 Identity. Answered by: the action record's actor field and chain representation.*

**X2-D · Declaration**

Where does the deliverable state the contract for **every action naming an actor, with explicit delegation chains**? Quote the contract, not a description of it.

**X2-M · Demonstration**

Show one worked case of **every action naming an actor, with explicit delegation chains** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**X2-F · Falsification**

What observation would prove **every action naming an actor, with explicit delegation chains** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### X3 — deterministic refusal before execution rather than after spend

*Source: brief B4 Policy. Answered by: the ordering of the policy check against the first billable operation.*

**X3-D · Declaration**

Where does the deliverable state the contract for **deterministic refusal before execution rather than after spend**? Quote the contract, not a description of it.

**X3-M · Demonstration**

Show one worked case of **deterministic refusal before execution rather than after spend** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**X3-F · Falsification**

What observation would prove **deterministic refusal before execution rather than after spend** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### X4 — every artifact attributable to code version, inputs and actor

*Source: brief B4 Provenance. Answered by: the artifact record's provenance fields.*

**X4-D · Declaration**

Where does the deliverable state the contract for **every artifact attributable to code version, inputs and actor**? Quote the contract, not a description of it.

**X4-M · Demonstration**

Show one worked case of **every artifact attributable to code version, inputs and actor** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**X4-F · Falsification**

What observation would prove **every artifact attributable to code version, inputs and actor** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### X5 — correlation riding on explicit attributes rather than trace parentage

*Source: brief B4 Telemetry. Answered by: the attribute set carried at dispatch.*

**X5-D · Declaration**

Where does the deliverable state the contract for **correlation riding on explicit attributes rather than trace parentage**? Quote the contract, not a description of it.

**X5-M · Demonstration**

Show one worked case of **correlation riding on explicit attributes rather than trace parentage** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**X5-F · Falsification**

What observation would prove **correlation riding on explicit attributes rather than trace parentage** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### X6 — errors never parsed from prose

*Source: brief B4 Errors. Answered by: the error value shape at every boundary.*

**X6-D · Declaration**

Where does the deliverable state the contract for **errors never parsed from prose**? Quote the contract, not a description of it.

**X6-M · Demonstration**

Show one worked case of **errors never parsed from prose** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**X6-F · Falsification**

What observation would prove **errors never parsed from prose** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

### X7 — every externally-triggered action safe to replay

*Source: brief B4 Idempotency. Answered by: the replay behaviour per entry point.*

**X7-D · Declaration**

Where does the deliverable state the contract for **every externally-triggered action safe to replay**? Quote the contract, not a description of it.

**X7-M · Demonstration**

Show one worked case of **every externally-triggered action safe to replay** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**X7-F · Falsification**

What observation would prove **every externally-triggered action safe to replay** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

## Seams with no standard to adopt

### S1 — Dispatch, where one unit of agent work executes and returns one result

*Source: brief B5 Dispatch. Answered by: the dispatch contract: request shape, result shape, cancellation, timeout and budget enforcement, partial results, failure return.*

**S1-D · Declaration**

State all six parts the brief names: request shape, result shape, cancellation semantics, timeout and budget enforcement, partial-result handling, and what a failure returns. Missing parts are the answer, so name them.

> **Why this is asked.** The brief calls this one of two places where original design effort is warranted. A partial contract here is the difference between agent execution being pluggable and not.

**S1-M · Demonstration**

Show one worked case of **Dispatch, where one unit of agent work executes and returns one result** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**S1-F · Falsification**

What exactly does cancellation guarantee: that a signal was delivered, or that no further output will arrive? And what happens to work already in flight?

> **Why this is asked.** Those are different promises and only one is useful to a caller. On a comparable stack the stronger guarantee held, with a cancel landing at eight seconds against a forty-five second tool call and no frames afterwards, but it had to be measured. A design saying it supports cancellation has said almost nothing.

**S1-S · Substitution**

Name a second adapter for **Dispatch, where one unit of agent work executes and returns one result** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

### S2 — State, where the graph and the ledger persist

*Source: brief B5 State. Answered by: the state contract: write model, concurrency and single-writer guarantee, integrity mechanism, retention, query surface.*

**S2-D · Declaration**

State all five parts the brief names: write model, concurrency and single-writer guarantee, integrity mechanism, retention, and the query surface a planner needs. Missing parts are the answer, so name them.

> **Why this is asked.** The brief calls this the second of two places warranting original design. The hash chain is named as the valuable idea and the file as disposable, so a design that keeps the file and loses the chain has inverted the brief.

**S2-M · Demonstration**

Show one worked case of **State, where the graph and the ledger persist** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**S2-F · Falsification**

Count the distinct payload contracts that cross this boundary, and compare that to the number the boundary's own contract declares. Do they match?

> **Why this is asked.** This is the check that found a real defect in a comparable corpus: a durability layer declaring two payload shapes, stating in as many words that nothing else crossed it, while a third shape crossed it anyway. Every individual document was valid; the disagreement appears only when both sides are read together.

**S2-S · Substitution**

Name a second adapter for **State, where the graph and the ledger persist** that is materially different from the first, and state what about the interface would have to change if it were adopted. If nothing would change, say how you know.

## The ask

### A1 — an ordered build sequence separating real dependencies from apparent ones

*Source: brief Part C output 1. Answered by: the sequence itself, with a stated reason per ordering constraint.*

**A1-D · Declaration**

Where does the deliverable state the contract for **an ordered build sequence separating real dependencies from apparent ones**? Quote the contract, not a description of it.

**A1-M · Demonstration**

Show one worked case of **an ordered build sequence separating real dependencies from apparent ones** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**A1-F · Falsification**

Name one ordering in the sequence that looks required and is not, and say what makes it merely apparent.

> **Why this is asked.** A sequence where every edge is claimed necessary has not been interrogated. The brief asks specifically for the separation, so producing only a list leaves the required work undone.

### A2 — a first-cut design for both seams, with the prior-art search stated

*Source: brief Part C output 2. Answered by: the two designs, plus what was searched where novelty is claimed.*

**A2-D · Declaration**

Where does the deliverable state the contract for **a first-cut design for both seams, with the prior-art search stated**? Quote the contract, not a description of it.

**A2-M · Demonstration**

Show one worked case of **a first-cut design for both seams, with the prior-art search stated** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**A2-F · Falsification**

Where novelty is claimed, was the search a retrieval or a recollection? Name what was fetched and which section was read.

> **Why this is asked.** In a comparable exercise sixty-six novelty claims were recall, because the processes producing them had no network access. When one was finally checked properly a published standard overturned it outright, specifying the structure the design claimed as new, with properties the new version could not provide.

### A3 — a machine-checkable definition of done per piece, with the deliberate breakage that proves the check can fail

*Source: brief Part C output 3. Answered by: per piece: the check, and the input that makes it fail.*

**A3-D · Declaration**

Where does the deliverable state the contract for **a machine-checkable definition of done per piece, with the deliberate breakage that proves the check can fail**? Quote the contract, not a description of it.

**A3-M · Demonstration**

For one piece, show the check failing on the deliberate breakage. Not the breakage described, the check failing.

> **Why this is asked.** The brief states it plainly: a criterion nothing can fail is not a criterion.

**A3-F · Falsification**

Is any definition of done already satisfied by the state of things before the work it grades has been done?

> **Why this is asked.** A batch of generated tasks on a comparable stack carried acceptance patterns that every one already matched in the target files. Each would have passed having changed nothing, while the surrounding machinery graded the criterion's shape and never evaluated it against the file.

### A4 — a second adapter for at least three capabilities, chosen to prove the interface is not shaped around its current implementation

*Source: brief Part C output 4. Answered by: three second-adapter designs, each materially different from the first.*

**A4-D · Declaration**

Where does the deliverable state the contract for **a second adapter for at least three capabilities, chosen to prove the interface is not shaped around its current implementation**? Quote the contract, not a description of it.

**A4-M · Demonstration**

Show one worked case of **a second adapter for at least three capabilities, chosen to prove the interface is not shaped around its current implementation** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**A4-F · Falsification**

For each of the three, what does the second adapter do differently enough that the interface had to accommodate it? If the answer is nothing, the interface was not tested.

> **Why this is asked.** The brief's own capability table already lists swap candidates. Restating those names satisfies the letter of the request and none of its purpose.

### A5 — what could not be decided, and what evidence would decide it

*Source: brief Part C output 5. Answered by: the list of undecided items, each with its deciding evidence.*

**A5-D · Declaration**

Where is the list of undecided items? The brief calls this a required output, not an apology, so an empty list is itself an answer that needs defending.

> **Why this is asked.** A deliverable with nothing undecided has either resolved every open question in the domain or has stopped noticing them. The second is far more common.

**A5-M · Demonstration**

Show one worked case of **what could not be decided, and what evidence would decide it** in operation, including what it refuses or how it fails. A happy path alone does not answer this.

**A5-F · Falsification**

What observation would prove **what could not be decided, and what evidence would decide it** is not true of this design, and what in the deliverable could be inspected or run to attempt it?

