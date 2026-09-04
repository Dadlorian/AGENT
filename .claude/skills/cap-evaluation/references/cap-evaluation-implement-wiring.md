# cap-evaluation-implement — wiring, migration order, conformance command

Long material for `cap-evaluation-implement`. Everything here is **proposed** unless a kb id is
named beside it. The skill body is enough to build both bindings without this file; open it when
you are writing the cross-cutting wiring, planning the migration, or running the conformance
command for the first time.

`cap-evaluation` owns the interface, the CaseSet and EvaluationReport shapes, the adapter pair and
what is deliberately not exposed. Nothing here restates them.

---

## 1. Where each cross-cutting concern attaches

agentic-stack states design rule 7: these are applied by the platform, not requested by the
caller (`F-b1-08`). The column that matters is the second one — a corpus fans one call out into
many, so most of these attach twice.

| Concern | At the `evaluate` boundary | Per case | Why it cannot be once-only |
|---|---|---|---|
| Budget | ceiling for the whole evaluation, refused before case 1 | remaining ceiling checked before each metered call | one corpus can be hundreds of model calls; a single top-level check stops nothing once the run is under way |
| Policy | one decision before the first case runs, carrying the corpus id and the unit under test | no second decision | a per-case decision would let half a corpus run under a rule that then refused the rest, producing a report that is neither passed nor failed |
| Identity | actor and full delegation chain on the request | same chain carried onto every case and onto every replayed effect | a case that reaches a tool must present the evaluator's chain, not the unit's, or the tool cannot tell a test from production |
| Telemetry | one span for the evaluation, with the correlation id set explicitly at dispatch | one span per case, child of the evaluation span by explicit attribute | trace context does not survive the agent boundary here (`F-a7-02`); parentage alone loses the link |
| Provenance | the report appended to the chain, naming the tree it scored | each case's verdict inside the report body | a report that cannot name the tree is unreproducible the moment the tree moves |
| Idempotency | one key covering the whole evaluation | none | re-submitting the same evaluation must return the same report, not re-score; a per-case key would let a partial re-run silently mix two trees |

Refusals from any of these are problem objects, not `outcome` values. `cap-errors` owns the
object and the closed registry.

---

## 2. Migration order

What runs today is not an evaluation harness. It is a deterministic pipeline that has already
gone green with every behavioural stage skipped (`F-a7-03`), plus an evidence store and a trace
backend that between them already hold what a corpus needs. The order below goes from that to a
gate that can refuse.

| Step | What changes | Claimed or measured at this point |
|---|---|---|
| 1 | The five operations exist as the module the core imports; both bindings are stubs that raise. | claimed |
| 2 | Today's binding scores one harvested case end to end from the trace backend. | measured once a run prints a verdict |
| 3 | Six cases registered: three harvested from evidence-store runs paired with their stored trajectories, three synthetic and multi-turn. | claimed until the corpus digest is recorded |
| 4 | First baseline frozen from one report over that corpus. Promotion is its own call with its own actor. | claimed |
| 5 | The no-server binding scores the same corpus from fixtures. Conformance run diffs the two. | measured once `verdict_divergence=0` is printed |
| 6 | The pipeline's behavioural stage is replaced by one `evaluate` call; the stage copies `status` from `outcome`. | claimed until the gate blocks a real change |
| 7 | A deliberate regression is introduced and the gate refuses it. | measured; this is the definition of done |

Nothing above may be labelled measured before a run produced the output that names it.
`build-evidence-record` owns the labelling and the record shape.

The hardest step is 6, and not for technical reasons: a gate that has never refused anything is
indistinguishable from a gate that cannot. Step 7 exists to make that distinguishable.

---

## 3. The conformance command in full

```
python3 tools/conformance_evaluation.py \
  --binding config/eval/trace-scoring.json \
  --binding config/eval/local-fixture.json \
  --unit agent:release-reviewer@1.4.0 \
  --case-set corpus/cs-release-review \
  --baseline corpus/bl-2026-08-27.json \
  --report out/eval-conformance.json

python3 tools/gate.py \
  --stage evaluation \
  --report out/eval-conformance.json \
  --emit out/gate-stage.json
```

Assertions, in the order a reader should check them:

| Assertion | What it proves |
|---|---|
| `adapters_run == 2` | both bindings ran; one binding passing is not a result |
| `cases_executed == 6` | the corpus was not silently filtered to nothing |
| `outcome == passed` | the unit under test still matches the baseline |
| `transitions == 0` | no case moved, per case, not in aggregate |
| `verdict_divergence == 0` | the verdict belongs to the unit, not to the harness |
| `status` in the gate record | copied from `outcome`, never derived from an exit code |
| zero-case rerun gives `status=inconclusive`, exit 1 | the stage cannot go green having executed nothing |

The tool, both bindings, the corpus and the gate stage are all proposed and none of them exists
in this tree. The check is therefore red by construction, which is the honest state for it until
someone runs it.
