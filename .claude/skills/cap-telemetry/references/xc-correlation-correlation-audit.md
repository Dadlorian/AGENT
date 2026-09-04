# Correlation: per-boundary stamping notes and the depth-3 audit walkthrough

Proposed unless a row says otherwise. Open this only when wiring a new boundary or building the audit
fixture; the skill body is enough to judge an implementation without it. Every id resolves with
`python3 tools/kb.py show <id>`.

## 1. Why this is a guarantee and not a convention

`F-a7-02` (measured): "W3C trace context does not survive the agent boundary." The remedy named in the
same record is an explicit resource attribute set at dispatch. `F-b4-06` states the concern's contract,
and `cap-telemetry` owns it; this layer owns only the scope (every span, every log record, every problem
object) and the enforcement (zero omissions, counted, per signal kind).

## 2. Boundaries and what has to happen at each (proposed)

| Boundary crossed | What is stamped | What is never relied on | Failure that shows up if skipped |
|---|---|---|---|
| Entry into the platform | The whole `CorrelationRecord`, depth 0, `root_dispatch_id` equal to the entry's dispatch | Any header the producer sent | The run has no grouping key at all and every later stamp invents one |
| Dispatch of a child unit | `derive_child`: same `run_id` and `root_dispatch_id`, new `parent_dispatch_id`, depth + 1 | The parent's ambient trace context | The child subtree groups separately; this is the X5 breakage |
| Into an isolated unit | The record travels as an explicit request field, not as an environment variable a runtime may drop | The runtime honouring an injected trace header | A depth-3 tree yields unrelated roots (`F-a7-02`) |
| Onto an event bus | The record travels as declared envelope members, one per identifier | In-band trace headers surviving the broker | Events land uncorrelated and look like fresh entries |
| Into a model call | The record is attached to the emission context around the call, never to the prompt | The provider echoing anything back | The call's span joins nothing |
| Out as a failure | The record is a declared member of the problem object (`F-b4-07`) | A run identifier mentioned in `detail` prose | The failure cannot be joined to the run that produced it |

## 3. The depth-3 audit walkthrough (proposed)

The fixtures are the four worked instances in the `StampedAtEntry` shape in the skill body; the audit runs
three of them, one per way in from TARGET T1 (`T-t1-01`, `T-t1-02`, `T-t1-03`), and the schedule instance
is carried as the fourth entry of TARGET T6.2 for the envelope skill to use.

1. Enter with the fixture. Record `run_id`, `root_dispatch_id`, `entry_kind`.
2. Level 1 does work and dispatches two children; level 2 does the same; level 3 is a leaf.
3. Collect, for that `run_id`: every span, every log record, every problem object.
4. Per signal kind, count records with a missing or empty `run_id`, and separately with a missing or empty
   `root_dispatch_id`. Both counts must be 0, and `signals_checked` must be greater than 0 for each kind,
   so an audit that collected nothing cannot report success.
5. Group the collected records by `run_id`. Exactly one group.
6. Count distinct trace identifiers. Report the number. Assert nothing about it.
7. Confirm `levels_covered == 3` by the distinct `depth` values present.

The breakage in row X5 is applied at step 2: the level-2 unit emits without re-stamping and relies on
parentage. `missing_run_id` becomes the count of its spans and `run_id_groups` rises above 1.

## 4. Failure shape

A rejection at entry uses the registered problem type `urn:agentic:problem:document-invalid` (422, not
retryable), because an envelope with no correlation record is an envelope that fails document validation.
No new type is minted here; the registry in `docs/decomposition.md` section 2.1.6 is closed and the row
that fits is reused. The worked instance is in the `CorrelationRejection` shape in the skill body.

An omission found *after* execution is not a caller-facing problem object at all: it is a conformance
failure of the emitting adapter, counted by the audit, and it is reported through the definition of done
rather than returned to anyone.

## 5. What the cited research records do and do not establish

Every record below is `status: search-only`. None was fetched and read, so each is evidence about what was
written on a page, not about what a specification says.

| Record | Establishes | Does not establish |
|---|---|---|
| `X-xc-correlation-001` | That a trace identifier has a fixed 128-bit hexadecimal form on the page quoted | Any specification version this platform has verified |
| `X-xc-correlation-002` | That automatic propagation links child spans to a parent by default | That it works across an agent boundary; `F-a7-02` measured that it does not |
| `X-xc-correlation-003` | That several propagator options exist per hop | Which one any boundary here uses |
| `X-xc-correlation-004` | The distinction between a flat correlation identifier and a trace identifier, and the common advice to merge them | That merging them is safe here; it is the design `F-a7-02` rules out |
| `X-xc-correlation-005` | That the correlation model rests on trace context, span context and resource attributes | Which surface this platform's audit reads; that is open question 8 |
| `X-xc-correlation-006` | A second-hand restatement of the agent-boundary failure | Anything `F-a7-02` does not already state as measured |
| `X-cross-structure-005` | The propagated carrier's declared bounds, 64 entries and 8192 bytes | That any carrier here is within them |
| `X-cross-structure-006` | That the carrier adds overhead and must not hold secrets, tokens or PII | Any measurement of that overhead here |
