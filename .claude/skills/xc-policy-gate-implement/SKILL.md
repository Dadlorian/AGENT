---
name: xc-policy-gate-implement
description: How to make the policy gate real on this stack: a first placement that consults the decision service synchronously on the dispatch path, a second placement that authorizes at the boundary every metered call crosses, the adoption path from a decision capability that exists and gates nothing, where correlation, provenance, budget and typed failures attach to an admission, and a definition of done with the breakage that makes it fail. Load it when writing or reviewing the code that admits or refuses a dispatch, when a metered surface can be reached without an admission token, when a check is about to be added beside the call path rather than on it, when a warn-only rollout is proposed, when deciding what the second placement should be, or when an ordering assertion passes on one placement and inverts on the other.
---

# xc-policy-gate-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the placement rule in xc-policy-gate into something that runs here: two gate placements behind one admission contract, the second authorizing at the boundary the metered call crosses so that calls the dispatcher never composed are gated too, adopted into the enforcement path without a window in which a dispatch runs ungated. | sourced | `F-b4-04`, `F-a6-04` "Conformance checks exist; not wired into the enforcement path" |

## Entities

| Entity |
|---|
| `E-concern-policy` |
| `E-capability-policy` |
| `E-adapter-opa` |
| `E-swap-candidate-cedar` |
| `E-not-running-policy-in-the-gate-path` |

## Contract

### Shapes (JSON Schema 2020-12)

**differs_in_execution_model for this pair (proposed instance of the shape build-adapter-pair defines)** (proposed; sources: `F-b1-04`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:policy-gate:pair-axes:0.1",
  "title": "PolicyGatePairAxes",
  "description": "Proposed. The three axes on which the two gate placements differ, stated as properties rather than as product names. measured stays false until the swap has been executed and recorded.",
  "type": "array",
  "minItems": 3,
  "examples": [
    [
      {
        "axis": "locus_of_enforcement",
        "today_value": "inside the process that is about to dispatch, which must remember to ask",
        "second_value": "at the boundary every metered call crosses, which refuses whoever made the call",
        "measured": false
      },
      {
        "axis": "processes_required_for_progress",
        "today_value": "a decision service must be reachable for any dispatch to be admitted",
        "second_value": "a pinned policy set is evaluated in-process at the boundary with no network hop",
        "measured": false
      },
      {
        "axis": "unit_gated",
        "today_value": "one dispatch admitted once, by an admission token",
        "second_value": "every metered call authorized individually against the same pinned version",
        "measured": false
      }
    ]
  ]
}
```

**gate-conformance report (proposed; the fields the definition of done asserts on, written per placement and once across placements)** (proposed; sources: `F-a7-03`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:policy-gate:implement-report:0.1",
  "title": "PolicyGateImplementReport",
  "type": "object",
  "additionalProperties": false,
  "description": "Proposed. Written per placement so a green run names what it actually checked, and once across placements so a swap that never ran cannot report as two.",
  "required": [
    "placement",
    "dispatches_checked",
    "metered_dispatches",
    "denied",
    "missing_decision",
    "inversions",
    "placement_observed"
  ],
  "properties": {
    "placement": {
      "type": "string",
      "description": "The entity id of the gate placement under test."
    },
    "dispatches_checked": {
      "type": "integer",
      "minimum": 0
    },
    "metered_dispatches": {
      "type": "integer",
      "minimum": 0
    },
    "denied": {
      "type": "integer",
      "minimum": 0
    },
    "missing_decision": {
      "type": "integer",
      "minimum": 0
    },
    "inversions": {
      "type": "integer",
      "minimum": 0
    },
    "spend_delta_micros_on_denied": {
      "type": "integer",
      "minimum": 0
    },
    "ungated_calls_found": {
      "type": "integer",
      "minimum": 0,
      "description": "Metered calls reached with no admission token. The shadow step's whole output: the calls one placement refuses and the other never saw."
    },
    "placement_observed": {
      "type": "string",
      "description": "Read from the refusal that came back, never from the binding that selected the placement."
    },
    "placements_run": {
      "type": "integer",
      "minimum": 0
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the two placements differ on three of build-adapter-pair's axes - locus_of_enforcement, processes_required_for_progress and unit_gated - recorded in the shape above. A different decision engine consulted the same way from the same process would agree with today's on all three, so swapping to it would test a vendor rather than the placement. | proposed | `F-b1-04` "Swappability is a tested property, not an intention." |
| xc-policy-gate states the ordering rule and the zero-spend rule (F-b4-04). What this adds on this stack: both placements must satisfy the same assertion over the same corpus, so a placement that cannot show a zero inversion count is not an alternative implementation, it is an unfinished one. | sourced | `F-b4-04`, `E-concern-policy` "Refusal is deterministic and happens before execution, not after spend" |
| agentic-stack states design rule 1 as a test (F-b1-02). Its consequence here: which placement refused is configuration. No core code, no workflow and no caller branches on it; the placement appears in the conformance report, never in a field a caller can read and route on. | sourced | `F-b1-02` "The core imports interfaces, never implementations" |
| agentic-stack states that what runs is substrate (F-part-c-11). Its consequence here: the decision capability already provisioned on this host is not replaced. It becomes the first placement, moved from beside the path onto it, and the boundary placement is added next to it rather than instead of it. | sourced | `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| xc-policy-gate records the state this work starts from (F-a6-04). What this adds: the move is adoption into the enforcement path, not migration within it, so the shadow step is deliberately the present state made explicit and time-boxed - a decision taken and recorded while the dispatch proceeds - and it ends on a date rather than when someone notices. | sourced | `F-a6-04`, `E-not-running-policy-in-the-gate-path` "Conformance checks exist; not wired into the enforcement path" |
| Apply build-evidence-record: every statement here about how a placement behaves stays claimed until the conformance run and its evidence record exist, naming the code version and the tree hash under test, and rewording a sentence never upgrades a label; proposed pointer, see that skill. | proposed | `F-a5-04`, `F-part-c-08` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Build the first placement by moving the decision capability that is already provisioned onto the dispatch path: the dispatcher calls its decision API synchronously, writes the policy-decided record, and only then mints the admission token every metered surface demands. | xc-policy-gate records why this layer exists (F-a6-04): the capability is defined and the enforcement path does not consult it. Moving what already runs onto the path is the smaller change and it starts the pair from a real refusal rather than an intention. | sourced | `F-a6-04`, `F-b3-11` "Conformance checks exist; not wired into the enforcement path" |
| 2 | Proposed: build the second placement at the boundary every metered call crosses - the model gateway, the tool surface, the isolation admission and the egress point - evaluating a pinned, precompiled policy set in-process at that boundary and refusing any call that arrives without a valid admission token. | Proposed: this breaks the assumption that the dispatcher is the only thing that starts metered work. A boundary placement refuses calls composed by code that never asked, and it removes the decision service from the critical path, so the two placements fail for different reasons rather than together. | proposed | `F-b3-11`, `F-b1-04` |
| 3 | Apply build-adapter-pair: record differs_in_execution_model from the shape above, leave measured false until the swap has actually been run, and write each placement's gaps down as gaps rather than as caveats; proposed pointer, see that skill. | differs_in_execution_model, its axes and the rule that measured stays false until the swap has run belong to build-adapter-pair; four sibling skills carried the sentence verbatim (consolidation part B, kb/ceremonies/implement-clusters.json). | proposed | `F-b1-04` "Swappability is a tested property, not an intention." |
| 4 | Adopt in three steps with no window in which a dispatch runs ungated: shadow, where both placements decide and record while the dispatch proceeds and ungated_calls_found is counted; compare, where the two refusal sets are reconciled over one corpus; then enforce, where the token check is switched on at every metered surface at once. | agentic-stack states that what runs is substrate (F-part-c-11), and the shadow step is the only stage in which a disagreement between the two placements is cheap: it is where the calls the dispatch-path gate never sees are first counted. Switching one surface at a time leaves the others open while the report already reads green. | sourced | `F-a6-04`, `F-part-c-11` "Part A is substrate, not scope. Do not propose replacing what runs." |
| 5 | Stamp the run identifier and the root dispatch identifier as explicit attributes on every decision request, every policy-decided record and every admission token, rather than relying on the trace the calling process is inside. | agentic-stack states that correlation must ride on an explicit attribute set at dispatch (F-a7-02) because parentage did not survive the agent boundary. A decision whose run cannot be identified cannot be ordered against that run's first metered call, which is the whole assertion. | sourced | `F-a7-02` "Correlation must ride on an explicit resource attribute set at dispatch" |
| 6 | Append the policy-decided record and the admission it produced through the append-only chained store, and let the ordering assertion read them at a pinned head rather than from the gate's own memory or logs. | agentic-stack states why the chain is there (F-a5-03): a later edit is detectable. An ordering claim read out of the process that made the decision is a claim that process is honest about itself; read out of a chained log at a pinned head, it is a fact anyone can recheck. | sourced | `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| 7 | Read which placement refused from the refusal that actually came back and put that value in placement_observed, never from the binding or the configuration that selected the placement. | agentic-stack states the silently-discarded-configuration finding (F-a7-04), measured on this host: values written where the documentation says were overlaid by a stored row. A gate believed installed because it was configured is that failure with an enforcement decision attached. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| 8 | Run the definition of done below over both placements and over each of TARGET T1's three ways in, then run its breakage, and record both outputs as evidence records naming the script hash, the commit, the tree hash under test and whether the tree was dirty. | build-evidence-record fixes what a record contains (F-a5-04); a result from a dirty tree is not reproducible and may not be labelled measured. Running the breakage is what shows the ordering assertion can fail rather than that it merely passed. | sourced | `F-a5-04`, `F-part-c-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the structurally-green-gate finding (F-a7-03), and xc-policy-gate draws the consequence for an inversion count. What this adds at the code level: report metered_dispatches per placement, because one corpus replayed through two placements can leave the boundary placement with nothing to authorize and still exit green. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| agentic-stack already states the silently-discarded-configuration finding (F-a7-04). What this adds here: test the gate by watching a dispatch be blocked on the live path, not by reading the policy bundle that was loaded or the decision-point registry that was published; a loaded bundle and an enforced bundle are indistinguishable from the file. | sourced | `F-a7-04` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Expect the two placements to disagree during the shadow step and treat the difference as the finding rather than as noise. xc-policy-gate cites the same records for the boundary pattern; what this adds is where the difference lands in code, as ungated_calls_found - metered calls that reached a surface with no admission token, which is precisely the set a dispatch-path gate can never report. | sourced | `X-xc-policy-gate-007` "intercepts every agent-tool call at the gateway boundary and authorizes against a policy set" |
| Proposed: choose the boundary placement's evaluation model for its constraints, not its expressiveness, since it runs on every metered call. xc-policy-gate already prefers default-deny, order-independent, side-effect-free evaluation on this path; what this adds is the code-level cost, that a language flexible enough to fetch, branch on time or mutate makes the boundary gate itself a source of the non-determinism it exists to remove. | proposed | `X-xc-policy-gate-002`, `X-xc-policy-gate-006` "default-deny, forbid-wins-over-permit, order-independent evaluation, no side effects" |
| Proposed: keep the conformance run on the same code path a live dispatch takes rather than beside it, replaying the corpus through the real admission call. A suite that reads a stored corpus and never touches the admission code reproduces exactly the state this layer exists to leave: a check that exists and an enforcement path that does not consult it. | proposed | `F-a6-04` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-opa` | today | gate, record and attest_ordering served by the decision engine PASS.md B3 names in the policy row as today's adapter and PASS.md A5 records as the provisioned policy role on this host, called synchronously from the dispatching process: gate is one decision-API request per dispatch, record is the policy-decided record the dispatcher appends before minting the admission token, and attest_ordering reads those records back at a pinned head. | Proposed: cannot gate a metered call made by a process that does not call it, so any code path composed outside the dispatcher stays open; binds only while the decision service is reachable, which makes an outage a choice between refusing everything and admitting everything; and its evaluation model is the flexible kind the research records associate with runtime exceptions and non-determinism, which on this path is a source of inversions rather than of expressiveness. | Select the placement by configuration with no code edit between runs, replay the same corpus through both, and compare: assert every refusal this placement produced is also produced by the boundary placement, and record the metered calls the boundary placement refused that this one never saw as ungated_calls_found. Read the placement from the refusal, not from the binding. | claimed | `F-b3-11`, `F-a5-05`, `F-a6-04` "Rego / OPA \| OPA" |
| `E-swap-candidate-cedar` | second | the same three operations served at the boundary every metered call crosses, with a pinned, precompiled policy set evaluated in-process there: gate is an authorization per metered call rather than per dispatch, record is the same policy-decided record written through the state seam, and attest_ordering is unchanged because it reads records rather than call sites. PASS.md B3's policy row names this engine and, more generally, any policy engine with a decision API as the swap candidates. | Proposed: cannot express rules outside typical access control, so a decision that needs a computed aggregate or an external lookup has to stay on the dispatch-path placement; cannot see a dispatch that never reaches a boundary, so it can never report missing_decision on its own; and it adds per-call latency to every metered call rather than once per dispatch. | Proposed: the axes that differ are locus_of_enforcement (inside the dispatching process versus at the boundary the call crosses), processes_required_for_progress (a reachable decision service versus in-process evaluation of a pinned set) and unit_gated (one dispatch admitted once versus every metered call authorized). Select by configuration, run the same corpus through both, and compare both reports against the same declared gaps. | claimed | `F-b3-11`, `F-b1-04` "Cedar · any policy engine with a decision API" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.4 row X3, made precise and run over the placement pair above: `python3 tools/conformance/policy_gate.py --placement today --placement second --corpus out/dispatches.jsonl --min-dispatches 100 --ways-in human,agent,event --report out/policy-gate.json` (proposed tool, built with the first enforcing placement), the placement selected by configuration with no code edit between runs. Per placement it asserts that every dispatch has a `policy-decided` record with a non-empty `rule_id` whose `(decided_at, decided_seq)` precedes that dispatch's first metered call, that every denied dispatch has `spend_delta_micros == 0`, and that `placement_observed` was read from the refusal rather than from the binding. Across placements it asserts `placements_run >= 2`, `inversions == 0`, `missing_decision == 0`, `dispatches_checked >= 100`, `metered_dispatches > 0` and that all three ways in were covered. |
| Expected | exit 0 and one line per placement of the form `placement=<entity> dispatches_checked=100 metered_dispatches=<m> denied=<d> missing_decision=0 inversions=0 ungated_calls_found=<u> placement_observed=<entity>`, followed by `placements_run=2 ways_in=human,agent,event`, with `metered_dispatches` and `denied` greater than zero on both so the ordering and zero-spend assertions each had something to assert on. |
| Deliberate breakage | Consult policy asynchronously in parallel with the first call: start the decision and the first metered call together and await the decision afterwards, on the dispatch-path placement only, changing nothing else. |
| Expected failure | exit 1 with `inversions` non-zero for the dispatch-path placement and still 0 for the boundary placement, naming the dispatch ids whose first metered call started before their `policy-decided` record, while `placements_run` stays 2, `missing_decision` stays 0 and `dispatches_checked` stays at or above 100 - which is what shows one placement lost the ordering rather than the corpus having gone unread or a placement having failed to run. |
| Status | claimed |
| Evidence | `F-part-c-04`, `F-b4-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `xc-policy-gate`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The gate is a placement, not a capability row, so it has no adapter or swap-candidate entity of its own, and the pair here is recorded against the policy capability's entities. Should the placement get its own entity pair? | 1-3-1 applied (TARGET T5): (a) add entities for a dispatch-path placement and a boundary placement, which needs a knowledge-base rebuild and would invalidate the provenance heads of every skill already written; (b) record the pair against the policy capability's existing adapter and swap-candidate entities and say so in the rows, which is what this skill does and which keeps the citation inside the capability the placement gates; (c) defer the pair to a later wave, which would leave this guarantee with one placement and nothing to prove swappability. Recommendation followed: (b). The question closes when a ceremony rebuilds the knowledge base and the two entities exist. | Keep the pair on the policy capability's entities, with the reason stated in each adapter row so a reader is not sent to the wrong capability's row. | `F-b3-11`, `T-t5-02` "When a problem comes up, use 1-3-1" |
| Should the boundary placement authorize every metered call individually, or accept the per-dispatch admission token and only re-check when the pinned policy version changes? | Measure the added per-call latency of in-process evaluation against the number of metered calls that a per-dispatch token would have admitted without a second look, over the shadow corpus. If ungated_calls_found stays zero under token acceptance, the per-call check is buying latency and nothing else. | Authorize every metered call. The axis that makes this placement worth having is that it refuses whoever made the call, and accepting a token minted elsewhere reintroduces the assumption that the dispatcher is the only thing that starts metered work. | `F-b1-04`, `F-b4-04` |
| What is the time box on the shadow step, and what evidence ends it? | Count ungated_calls_found per day during shadow. The step ends when the count is stable across a full corpus replay and every call site it named has either acquired a token check or been recorded as a declared exception with an owner; a shadow step with no end date is the present state with a new name. | Proposed: end the shadow step on a stated date rather than on a metric alone, since the metric can be held at zero by a corpus that exercises nothing, and record the date in the evidence record for the shadow run. | `F-a6-04`, `F-a7-03` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session xc-policy-gate 2831cb4f, 2026-09-03 |
