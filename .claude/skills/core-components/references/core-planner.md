---
name: "core-planner"
description: "The Planner: the pure function from a declared document to a priced plan, computed at one pinned state head and finished before anything is spent. Load it before a run is allowed to start, when a step needs a number attached to it, when a ceiling has to be compared against something, and when someone asks 'what will this cost before we commit', 'why may planning not ask a model to estimate', 'why did the same document produce two different plans', 'where does the cost table come from', or 'how do we not re-run work that was already done'. Also load it whenever an estimate is about to be improved by calling something, whenever a plan is about to carry a guessed number for a step nothing could price, and whenever a component downstream of the document proposes to fill a field in before the planner reads it."
---

# core-planner (folded into `core-components`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one pure function - a declared document plus the cost data read at a pinned head, in; an ordered priced plan and one total cost, out - so that cost is a lookup taken before commitment rather than a discovery made by spending. | sourced | `F-b2-03`, `F-b2-01` "nothing is pricable before it is spent" |

## Entities

| Entity |
|---|
| `E-core-component-planner` |
| `E-core-component-document` |
| `E-core-component-graph` |
| `E-core-component-ledger` |
| `E-rule-b1-5` |
| `E-seam-state` |
| `E-concern-budget` |
| `E-capability-model-access` |
| `E-standard-json-schema-2020-12` |
| `E-standard-rfc-9457-problem-details` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | https://json-schema.org/draft/2020-12 | `F-b3-09`, `F-b1-03` |
| `E-standard-rfc-9457-problem-details` | RFC 9457 | unverified | - | `F-b3-13`, `F-b1-03` |

- `E-standard-json-schema-2020-12` version note: core-document owns this row (F-b3-09); it is repeated here only because the plan and the cost inputs are declared in the same dialect and checked through the same imported validator. The published specification was not fetched in this session, so the version is the one PASS.md's B3 row names and nothing more.
- `E-standard-rfc-9457-problem-details` version note: cap-errors owns this row and core-document already adopts it for a refused declaration (F-b3-13); it is repeated here because a refusal to plan is returned in that shape. Not fetched in this session, so the revision is unverified.

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| plan (proposed operation; PASS.md names the function, not the calls) | a document instance, one pinned state head, and the cost table and cost quantiles read at that head, all passed as values (proposed) | a plan - the ordered steps, each with its operator, its model class and its floor and worst-case price - plus one floor and one worst-case total, or a typed problem naming the step that could not be priced (proposed) | proposed | `F-b2-03`, `F-b1-06` |
| price_step (proposed operation) | one step, the cost-table row its operator and model class select, and the quantile band recorded for that selector (proposed) | that step's floor and worst-case cost together with the derivation - which row, which quantile, over how many observations - that produced them (proposed) | proposed | `X-core-planner-004`, `X-core-planner-005` |
| explain (proposed operation) | a plan (proposed) | the per-step derivation in reading order, so a reviewer can see why a step was priced as it was without re-running the planner (proposed) | proposed | `X-core-planner-003`, `X-core-planner-007` |
| prior_result (imported from the state seam's pinned query surface, not implemented here) | an idempotency key or a document digest, and the pinned head | the result recorded for that key at that head, or nothing; the Ledger is where the answer lives, and the planner reads it rather than keeping a second copy | sourced | `F-b2-06`, `F-b1-02` "the deduplication authority" |
| cost_history (imported from the same pinned query surface) | a cost selector, a window, and the pinned head | the measured quantiles for that selector at that head - data the planner reads, never a service it calls | sourced | `F-b5-05` "the query surface a planner needs" |
| compare (proposed accessor, over the typed walk core-graph already defines) | a step and the candidate implementations one hop away across implementation edges, each priced by price_step (proposed) | the cheapest candidate and the priced alternatives that were rejected, so a plan records what it did not choose (proposed) | proposed | `X-core-planner-007` |

### Shapes (JSON Schema 2020-12)

**plan (proposed summary shape; the full plan and cost-input schemas, a worked call for each of TARGET T1's three ways in, and the worked refusal are in references/planner-shapes.md)** (proposed; sources: `F-b2-03`, `F-b1-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:plan:0.1",
  "title": "Plan",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. A plan is a value derived from a document and the cost inputs read at one head. Everything it names is a name; nothing in it is a location, a vendor or a live reading.",
  "required": [
    "plan_version",
    "document_digest",
    "at_head",
    "cost_inputs_digest",
    "steps",
    "floor_micros",
    "worst_case_micros"
  ],
  "properties": {
    "plan_version": {
      "const": "0.1"
    },
    "document_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "at_head": {
      "type": "string",
      "minLength": 1,
      "description": "The pinned head every read was taken at. Same document, same head, same plan bytes."
    },
    "cost_inputs_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "steps": {
      "type": "array",
      "minItems": 1,
      "items": {
        "$ref": "urn:agentic:core:plan:step:0.1"
      }
    },
    "floor_micros": {
      "type": "integer",
      "minimum": 0,
      "description": "What the plan costs if every bounded loop runs once. Compared against the ceiling before anything starts."
    },
    "worst_case_micros": {
      "type": "integer",
      "minimum": 0
    },
    "requested_by": {
      "type": "string",
      "pattern": "^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$",
      "description": "Carried from the envelope for audit. Recorded, never branched on."
    }
  }
}
```

**plan-step (proposed shape for the machine-readable fields the invariants and instructions below name)** (proposed; sources: `X-core-planner-004`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:plan:step:0.1",
  "title": "Planned step",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "step_id",
    "operator",
    "model_class",
    "floor_micros",
    "worst_case_micros",
    "derivation"
  ],
  "properties": {
    "step_id": {
      "type": "string",
      "minLength": 1
    },
    "operator": {
      "type": "string",
      "minLength": 1,
      "description": "One operator from the closed set core-document draws steps from."
    },
    "model_class": {
      "type": "string",
      "description": "A class, never a vendor or a member model."
    },
    "floor_micros": {
      "type": "integer",
      "minimum": 0
    },
    "worst_case_micros": {
      "type": "integer",
      "minimum": 0
    },
    "replay_of": {
      "type": [
        "string",
        "null"
      ],
      "description": "Set when prior_result found this work already done at the pinned head; such a step is planned as a replay, not as work."
    },
    "check_ids": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "The definition-of-done checks this step will be graded on. Ids only; criterion text is forbidden here."
    },
    "derivation": {
      "type": "object",
      "required": [
        "cost_table_row",
        "quantile",
        "observations"
      ],
      "properties": {
        "cost_table_row": {
          "type": "string",
          "minLength": 1
        },
        "quantile": {
          "enum": [
            "p50",
            "p95"
          ]
        },
        "observations": {
          "type": "integer",
          "minimum": 0
        }
      }
    }
  }
}
```

**plan-purity-report (proposed shape; the fields the definition of done below asserts on)** (proposed; sources: `F-part-c-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:core:plan:purity-report:0.1",
  "title": "Plan purity report",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "runs",
    "plan_digest",
    "identical",
    "connects_inet",
    "steps_priced",
    "criterion_leaks"
  ],
  "properties": {
    "runs": {
      "type": "integer",
      "minimum": 2
    },
    "plan_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "identical": {
      "type": "boolean",
      "description": "Whether every run produced byte-identical plan output."
    },
    "connects_inet": {
      "type": "integer",
      "minimum": 0,
      "description": "AF_INET and AF_INET6 connects observed while planning. The number design rule 5 makes checkable."
    },
    "steps_priced": {
      "type": "integer",
      "minimum": 0,
      "description": "Guards against a green run in which nothing was priced at all."
    },
    "criterion_leaks": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The Planner is a pure function from a document to a plan and a cost, and it is the component whose absence means nothing is pricable before it is spent: a cost that arrives after execution is a receipt, not a plan. | sourced | `F-b2-03`, `F-b2-01` "nothing is pricable before it is spent" |
| agentic-stack states design rule 5 as a test (F-b1-06). The consequence on the component the rule is actually about: planning takes no action that spends - no completion request, no dispatch, no write - because a planner that spends in order to price has priced nothing before commitment, and the rule stops being true of the whole platform. | sourced | `F-b1-06`, `F-b2-03` "Planning is a pure function and completes before execution begins" |
| Proposed: the cost table and the historical cost quantiles are inputs, not clients. They are read at the pinned head, passed to the call as values, and their digest is recorded on the plan, so a plan can be re-derived from the document and those inputs alone and a change of estimate is a change of data rather than of code. | sourced | `F-b5-05`, `X-core-planner-002` "historical data, expert judgment, and formalized models to ensure cost estimate reliability" |
| Proposed: every read is taken at one pinned state head, resolved once before planning starts and passed down. The same document at the same head produces byte-identical plans forever; that single constraint is what makes design rule 5 checkable rather than aspirational, since a pure function cannot read a moving store. | sourced | `F-b5-05`, `F-b1-06` "completes before execution begins" |
| core-ledger owns the receipt store, and PASS.md makes the Ledger the deduplication authority (F-b2-06). The consequence here is an ordering one: the planner asks for a prior result at the pinned head before it prices a step, and plans a step that already has one as a replay, because a planner that cannot ask will plan work that has already been done. | sourced | `F-b2-06` "append-only across runs; the deduplication authority" |
| The planner prices; it does not enforce. xc-budget owns the ceiling guarantee (F-b4-02); the consequence here is that the plan's floor is what a ceiling is compared against before anything runs, and the planner never raises, lowers, waives or reads around a ceiling of its own accord. | sourced | `F-b4-02`, `F-b4-01` "Every unit of work carries a ceiling" |
| core-document states the grader rule on the declared artifact (F-b1-07); the consequence for a plan is sharper, because the plan is the thing handed to whatever will be dispatched: a planned step carries the check_ids it will be graded on and never the criterion behind them. | sourced | `F-b1-07` "never the criterion it is judged against" |
| A document that cannot be priced is refused, not estimated. core-document adopts the problem-details shape for a refused declaration (F-b4-07, F-b3-13); the consequence here is that an unpriceable step comes back as a typed problem naming the step and the missing cost selector, never as a plan with one invented number inside it. | sourced | `F-b4-07`, `F-b3-13` "Typed and machine-readable. Never parsed from prose" |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Criterion text, in any field of a plan or of a planned step. core-document states design rule 6 (F-b1-07); the consequence on this artifact is that the plan is the one document-derived value that travels to the executing side, so a criterion string reachable from it defeats the rule everywhere else it was kept. | sourced | `F-b1-07` "An agent sees its outcome" |
| A vendor, an endpoint or a member model name. agentic-stack states that callers request a class and never a vendor (F-a4-01); the consequence here is that a priced step names a model class and a cost selector, so the plan stays valid when what serves that class changes underneath it. | sourced | `F-a4-01`, `F-part-c-09` "Callers request a class, never a vendor" |
| Proposed: wall-clock time, a live price feed, and which store answered the pinned reads. Each of them would let the same document at the same head price differently on a second run, which is the one property this component exists to have. Research query: does F-b1-06 itself enumerate wall-clock time, a live price feed and which store answered as specifically excluded, or is that this skill's own elaboration of 'pure function'? | proposed | `F-b1-06` |
| Proposed: a best-guess field. There is no place on a plan to put a number nothing derived, because a plan whose totals include one invented figure can never be reconciled against actuals, and reconciliation is how the cost table gets better. Research query: is there a fetched source on disallowing an unreconcilable invented figure on a cost plan, beyond X-core-planner-002's general cost-estimation-methods survey? | proposed | `X-core-planner-002` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Proposed: resolve the state head once, before planning starts, and pass that head into every read the planner makes. Do not resolve it again part-way through, and do not let a helper resolve its own. Research query: is there a fetched source on resolving a state head exactly once and passing it as a value, beyond F-b5-05's state-persistence specification and F-b1-06's planner-purity claim this row combines? | Proposed: head resolution is the only non-deterministic call on this path; taken once and passed as a value, everything after it is reproducible, and taken twice it lets two runs of the same plan disagree about what the world contained. | proposed | `F-b5-05`, `F-b1-06` |
| 2 | Pass the cost table and the historical quantiles in as data, read at that head, with their digest recorded on the plan. Never open a connection from inside the planner to fetch them, and never let a missing row be filled in by asking something. | Estimation prior art rests on historical data and formal models rather than on a fresh opinion, which is exactly what makes it expressible as data; and agentic-stack's design rule 5 (F-b1-06) means the moment those inputs become a call, planning has spent. | sourced | `X-core-planner-002`, `F-b1-06` "historical data, expert judgment, and formalized models" |
| 3 | Price every step from the cost-table row its operator and model class select, and record two numbers rather than one: a floor, with every bounded loop counted once, and a worst case at the loop's declared bound. | Query-planning prior art separates start-up cost from total cost so both the first result and the whole run are predictable; here the same split is what lets a ceiling be checked against the floor before anything starts, while the worst case is what a reviewer approves against. | sourced | `X-core-planner-004`, `F-b4-02` "The execution cost has two options: start-up and total" |
| 4 | Ask the pinned query surface for a prior result before pricing a step, and plan a step that already has one as a replay with replay_of set, priced at zero. | PASS.md puts deduplication in the Ledger (F-b2-06), so the planner's job is to ask rather than to keep a second index; a planner that skips the question prices work the platform has already paid for and reports a total nobody can reconcile. | sourced | `F-b2-06`, `F-b1-02` "append-only across runs; the deduplication authority" |
| 5 | Reach no metered interface from inside the planner - no completion request, no dispatch, no write - and prove it rather than assert it, by running the plan under a syscall tracer and asserting the count of AF_INET and AF_INET6 connects is exactly zero. | This is the load-bearing non-dependency of the whole design: agentic-stack states design rule 5 (F-b1-06) and build-definition-of-done states that a criterion nothing can fail is not a criterion (F-part-c-04), and the connect count is what turns purity from a review convention into a number a machine reads. | sourced | `F-b1-06`, `F-part-c-04` "A criterion nothing can fail is not a criterion" |
| 6 | Plan through one call whichever way in produced the document - TARGET T1's three ways in, a human, an agent, and an internal or external event - and keep that call small: a document, a head, and the cost inputs. Record the requester on the plan; never branch on it. | One call is what lets a person, an agent and an event get the same number for the same work; core-document states TARGET T3's usability requirement, and a second planning entry point with its own defaults is how two callers start getting two prices for one document. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t3-01` "A human must be able to enter the system." |
| 7 | Return a refusal in the problem shape core-document already adopts, naming the step and the cost selector that was missing. Do not invent a problem type at the call site: while the row this component wants is not in the closed registry, return the registered type named in the open question below. | cap-errors' registry is closed, and a caller repairing a document branches on the type rather than on the wording; a bespoke type suffix invented here is a URI no conformant implementation may legally return, so the refusal would be unreadable exactly when it matters. | sourced | `F-b3-13`, `F-b4-07` "— adopt the RFC directly" |
| 8 | Judge a candidate implementation on four counts, not on an exit code: two runs of the same document at the same head give byte-identical plans; the tracer reports zero inet connects; every priced step names the cost-table row and quantile it used; and no criterion string appears anywhere in the plan. | core-document and build-definition-of-done state the measured green-gate finding (F-a7-03), where a nine-stage pipeline ran green with every behavioural stage skipped; each count above is what that finding costs to satisfy, and steps_priced is the one that catches a run in which nothing was priced at all. | sourced | `F-a7-03`, `F-part-c-04` "with every behavioural stage skipped" |
| 9 | Record the schema dialect and the problem-details standard as unverified until their published specifications have been read in an environment that can fetch them, and write no version string that was not read. | build-skill-authoring requires a standard and its version to be cited rather than recalled (F-part-c-10); a version number nobody read is a fabrication with a decimal point in it, and a plan is a document other teams will code against. | sourced | `F-part-c-10` "Cite the standard and its version" |
| 10 | Proposed: open references/planner-shapes.md when you are writing the full plan or cost-input schema, when you need the worked call for a way in you have not handled yet, or when you are rendering a refusal and want the problem instance rather than the rule. The body of this skill is enough to call the planner and to judge an implementation without it. | Proposed: the full schemas, the three worked calls and the worked refusal are longer than the progressive-disclosure budget allows in the body, and a reader deciding what to plan does not need them; a reader repairing a refused plan does. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack and build-definition-of-done state the green-gate finding (F-a7-03). What it adds here, as this facet's own consequence and proposed: a plan that validates has been shown well-formed, not affordable, so a schema pass must never be reported as an approval, and the number a reviewer approves is the worst case rather than the floor. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| agentic-stack states the configuration finding (F-a7-04). What it adds here, as this facet's own consequence and proposed: record the digest of the cost table actually in effect at plan time on the plan itself, because a table written in the documented place and overridden by a stored row produces a plan that reviews identically and prices differently. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Where a step has more than one candidate implementation, compare their prices and record the alternatives that were rejected: query-planning prior art picks the cheapest option by comparing costs, and a plan that shows what it did not choose is one a reviewer can argue with. | sourced | `X-core-planner-007` "it uses these costs to choose the cheapest, and therefore hopefully fastest, option." |
| Keep the document declarative and the plan derived, so improving how work is priced never edits what was declared: the prior art for declarative planning is a caller describing what it wants while the planner figures out how, which is TARGET T2's promise that one aspect can be enhanced without touching the rest. | sourced | `X-core-planner-003`, `T-t2-02` "you describe what data you would like to retrieve, and the database figures out a plan for how to get it for you" |
| Prefer a parametric selector over a per-task opinion when adding a cost-table row: software estimation has been done with structured models for decades, and a selector keyed on operator and model class stays comparable across runs where an author's per-task number does not. | sourced | `X-core-planner-006` "estimate time and costs associated with planning and managing software projects" |
| Proposed: keep the plan readable on one screen. A plan a human will not read before approving is a ceiling nobody checked, and the per-step derivation - not the total - is the part that stops being read first. Research query: beyond T-t3-02's general usability requirement, is there a source specifically about a plan's per-step derivation being the part that stops being read first? | proposed | `T-t3-02` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 harness/dispatch/conformance.py --adapter dryrun --adapter second |
| Expected | exit 0, both adapters printing the same `plan_digest=4bce5f723c26`, then `adapters_run=2 migrated_paths=3 plan_digest_mismatches=0 verdict_mismatches=0 distinct_markers=2`. Four of that run's assertions are row C2 on disk: `P1 the same document at the same head plans byte-identically`, `P2 the planner opened no internet socket` (`connects_inet == 0`, from a socket guard inside the run), `P3 the plan priced steps rather than asserting on an empty plan`, and `P4 a step with no cost row at this head is refused, not estimated`. The command is the dispatch harness, whose plan-entry names core-planner among its co-skills. Claimed, stated as the gap: `tools/plan.py` and `tools/plan_purity.py` do not exist and nothing here runs under `strace`, so `runs=2 plan_digest=sha256:<hex> identical=yes connects_inet=0 steps_priced=<n> criterion_leaks=0` has never been produced, and purity is asserted by a guard inside the run rather than by a trace taken from outside it. The criterion above was run on 2026-09-03 and exited 0. |
| Deliberate breakage | Make the planner call the model-access interface to estimate one step's cost, and change nothing else. |
| Expected failure | `connects_inet` becomes non-zero, the two plans diverge on the sampled estimate so `identical=no` and the digests differ, and the run exits non-zero while `steps_priced` stays greater than zero - so the report names the estimate that was sampled rather than only that something failed. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b1-06` "the deliberate breakage that proves the check can fail" |

## Composes with

Builds on: `agentic-stack`, `build-definition-of-done`, `build-skill-authoring`, `core-document`, `core-graph`, `xc-budget`

Used by: `compose-operators`, `core-planner-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The closed problem-type registry has no row for a step nothing could price, so what does a refusal to plan carry? | Applying TARGET T5's 1-3-1, the discipline build-definition-of-done owns and core-graph already applied to a refused edge assertion: reuse `budget-exhausted`, which is false because nothing was priced and nothing was spent; mint a suffix at the call site, which the closed registry forbids; or add one row `plan-unpriceable` (422, not retryable, extension members naming the step id and the missing cost selector) to docs/decomposition.md section 2.1.6 and use it. The third is recommended, and that suffix is proposed and pending registration wherever this skill names it. | `urn:agentic:problem:document-invalid` - the registered 422 that already means the declaration cannot be acted on - with the step id and missing selector in `causes`, returned until the row above lands. references/planner-shapes.md shows the refusal in that registered shape. | `T-t5-02`, `F-b3-13` "define the problem, identify the three best possible solutions that align to the goal, and follow the recommendation" |
| Does a plan price only the declared document, or also the expected cost of the work that document will spawn? | Compare, across the run history, the declared worst case against the total actually spent by a run and everything it delegated. A gap that is routinely large says the ceiling is being set against the wrong number; a gap near zero says the declared bounds already cover it. | The declared document and its declared loop bounds alone, because anticipatory pricing needs a task distribution the platform does not yet have, and a worst case that includes an unbounded guess is not a ceiling anyone can approve. | `X-core-planner-001` "the expected cost of future tasks" |
| Does the planner search over candidate expansions of a step, or price the single expansion the document names? | Measure how often a one-hop comparison changes the chosen implementation, and what a full search costs at the target scale of well over a hundred agents running at a time. A search whose planning cost approaches the work it saves has stopped paying for itself. | Price the named expansion, with the one-hop comparison of candidates reachable across implementation edges. Exhaustive symbolic search is optimal and unbounded in time, which is the one thing a function that must complete before execution cannot be. | `X-core-planner-008`, `T-t6-06` "Symbolic search discovers optimal plans through exhaustive state-space exploration" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session claude/auto-skill-creation-i8javu (core-planner, 2026-09-03) |
