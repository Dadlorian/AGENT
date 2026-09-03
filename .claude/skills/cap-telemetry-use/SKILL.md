---
name: cap-telemetry-use
description: How to use the Telemetry capability as a caller: send what you were going to send, get back a run identifier, and ask any question about the run by grouping on it. Load it when you want to see what a run actually did, when you are handing a run identifier to someone who has to investigate it, when a step happened inside an agent or a tool you did not write and you still need it in the picture, when a run looks like several unrelated pieces in a viewer, or when you are deciding what to keep after a run so it can be examined later. Also load it before adding a tracing call of your own to a step, and when someone asks which flag turns observability on.
---

# cap-telemetry-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| cap-telemetry states the contract this rests on (F-b4-06); this facet reduces it to what a caller does, which is almost nothing: one identifier comes back with the result and every question about the run is a group-by on it. | sourced | `F-b4-06`, `T-t3-01` "Correlation rides on explicit attributes, not trace parentage" |

## Entities

| Entity |
|---|
| `E-capability-telemetry` |
| `E-concern-telemetry` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| receive (proposed) | nothing extra; you send the envelope you were already sending, through whichever entry you already use | your result, plus the correlation block it came back with: a run identifier, a correlation identifier, and a depth if the work was delegated | proposed | `F-b4-06` |
| ask (proposed) | a run identifier | every span, metric and log the run produced, at every depth, grouped as one run however many trace trees the underlying runtimes minted | proposed | `F-a7-02` |
| hand over (proposed) | the run identifier alone | enough for someone else to ask the same question against whichever backend they have; the identifier is the whole handover, because it is an attribute on the telemetry rather than a key into a store of ours | proposed | `F-b1-05` |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): what comes back, and what you do with it** (proposed; sources: `F-b4-06`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:telemetry:example:result",
  "title": "What comes back",
  "description": "Send entries/human.json as usual. The result carries a correlation block; you keep the run identifier and ask with it later. Proposed: the correlation block is what the reference runner emits today on every record, and no span is emitted anywhere yet, which is what the definition of done below measures.",
  "examples": [
    {
      "run_id": "run-human-0001",
      "state": "completed",
      "correlation": {
        "run_id": "run-human-0001",
        "correlation_id": "corr-human-0001",
        "depth": 0
      },
      "your_next_step": "keep run_id; ask for the run by it, at any depth, from whichever backend you have"
    }
  ]
}
```

**Worked example 2 (proposed): the failure shape, when a run cannot be shown** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:telemetry:example:unavailable",
  "title": "A run with nothing to show",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Ask for a run whose retention window has passed, or one whose identifier never existed. The answer is RFC 9457 problem details with media type application/problem+json, the shape cap-errors owns. The type below is proposed and needs a row added to that registry before anything may raise it. Note what is not here: a failure to export is never raised at you, because a caller who could see one would start deciding whether telemetry mattered.",
  "examples": [
    {
      "type": "urn:agentic:problem:telemetry-unavailable",
      "title": "No telemetry is retained for that run",
      "status": 404,
      "detail": "run.id run-human-0001 has no retained telemetry; the retention window for this deployment is 30 days",
      "retryable": false,
      "correlation_id": "corr-human-0001"
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| All three of TARGET T1's ways in reach this the same way. A human must be able to enter the system, an agent must be able to enter the system, and an internal or external event must be able to enter the system; each gets the same correlation block back and each run answers the same group-by, and nothing about the telemetry depends on which of the three it was. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "3. An internal or external event must be able to enter the system." |
| Proposed: the caller's obligation is zero fields. There is no tracing call to make, no sampling rate to set, no flag that turns telemetry on and none that turns it off; cap-telemetry fixes the contract and cap-telemetry-implement wires the injection at dispatch, so a step that produced nothing is a defect to report rather than a setting to check. | proposed | `F-b1-08`, `F-b4-06` |
| One run is one group whatever the underlying runtimes did. cap-telemetry states why (F-a7-02): a depth-3 task tree produces three unrelated root traces, so a viewer that shows several disconnected trees for one run is showing the truth, and the run identifier is what puts them back together. Seeing more than one tree is never a reason to go looking for a missing parent. | sourced | `F-a7-02` "three unrelated root traces" |
| Enhancing one aspect leaves the rest untouched: the backend can be replaced, a redaction stage added to the pipeline, or the attribute vocabulary revised to a new version, and a caller holding a run identifier does nothing, because the identifier was never a key into any of those things. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The same run identifier covers every entry and every depth. cap-telemetry cites T-t2-03 for the placement of the concern; the caller-side consequence is that a workflow which calls an agent which calls a tool produces one group and not one per layer, because state, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used. | sourced | `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used." |
| The surface is one identifier because a contract that is daunting or overly complex will not be used; a caller asked to thread a context object through every call will thread it through most of them, and the run that matters will be the one that was missed. | sourced | `T-t3-02`, `T-t3-01` "It cannot be daunting or overly complex, or no one will use it." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: you never see which backend stored the run, which vocabulary version named the attributes, or where the pipeline redacted something. A caller that could tell one backend from another would encode the difference, and the swap would stop being free. | proposed | `F-b1-05` |
| Proposed: holding a run identifier does not entitle you to read what the run carried. The identifier groups the telemetry; who may read a payload, an attribute value or a stored artifact stays a matter for identity and policy. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Send what you were already sending. Do not add a tracing call, a span of your own, or a request to be observed; there is nothing to opt into. | Proposed usage of the placement cap-telemetry fixes. The platform applies this concern rather than offering it, so a caller-side switch would be a hole rather than a feature, and a span you mint yourself is the one thing in the run with no correlation attributes on it. | proposed | `F-b1-08` |
| 2 | Read the run identifier off the correlation block on the result and keep it next to whatever you do with the output. | Proposed. The identifier is the only handle you need and the only one that survives a backend change; a result kept without it can still be read, but nothing about how it was produced can be found again. | proposed | `F-b4-06` |
| 3 | Ask for a run by grouping on the run identifier. Do not start from a trace and walk up its parents, and do not treat several root traces in one run as a fault. | cap-telemetry states the contract that correlation rides on explicit attributes, not trace parentage (F-b4-06); for a caller the consequence is that the group-by is the supported query and the parent walk is the one that has already been measured to lose two thirds of a depth-3 run. | sourced | `F-b4-06`, `F-a7-02` "Correlation rides on explicit attributes, not trace parentage" |
| 4 | Hand over the run identifier alone when someone else has to investigate, rather than a link into a particular viewer. | Proposed. The identifier is an attribute carried on the telemetry itself, so it answers the same question in whichever backend the other person has; a viewer link answers it only while that viewer is the one running. | proposed | `F-b1-05` |
| 5 | Handle exactly one failure, the 404 in worked example 2, and handle it by saying the run cannot be shown rather than by retrying. Everything else that comes back is the ordinary answer or an ordinary typed failure. | Proposed. The failure shape, the media type and the closed registry belong to cap-errors, so a caller that already reads type and retryable needs no new branch beyond recognising one more registered type; a run outside its retention window will still be outside it on a second attempt. | proposed | `F-b4-07` |
| 6 | When you delegate, pass the correlation block along in the payload you send, and let the platform stamp it; do not copy a trace header by hand. | cap-telemetry-implement states the boundary rule (X-entry-composition-015): correlation IDs should be preserved at every boundary, and the payload is the carrier that survives a runtime whose instrumentation nobody here controls. A hand-copied header is the case PASS.md A7 finding 1 already measured failing. | sourced | `X-entry-composition-015`, `F-a7-02` "Correlation IDs should be preserved at every boundary" |
| 7 | Proposed: if you want to see the starting state, use examples/end-to-end. Every record it writes already carries the run and correlation identifiers, and it emits no span at all, which is exactly what the definition of done below measures. | Proposed, and it is the shortest route from this page to something running: the reference runner needs no services, and the gap it shows is the honest one rather than a rehearsed success. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: keep the run identifier with the output, not in a ticket. The identifier is what makes an output explainable six weeks later, and it is one string; a result filed without it is a result nobody can ever ask about again. | proposed | `F-b4-06` |
| Do not go looking for a single trace tree. Nine times out of ten when spans show up as disconnected root spans instead of forming a proper trace tree, the problem is a boundary that dropped the context, and here that boundary is expected and the grouping attribute is the answer. | sourced | `X-cross-structure-013` "when spans show up as disconnected root spans instead of forming a proper trace tree" |
| Proposed: report a step with no telemetry rather than working around it. Telemetry is applied by the platform, so a step that produced none means the injection was bypassed, and a caller who quietly tolerates it is the reason nobody notices. | proposed | `F-b1-08` |
| Ask for a single run identifier per unit of work you care about, and expect one where the whole run is the unit. There is no standard attribute that groups several runs into a session yet: the vocabulary's conversation attribute is designed for single conversation flows, not multi-conversation sessions, so a question spanning runs is a question you assemble from identifiers you kept. | sourced | `X-cross-structure-008` "designed for single conversation flows, not multi-conversation sessions" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `cd examples/end-to-end && bash test.sh` to produce the corpus, then the caller-side telemetry assertion over what it appended: `python3 -c "import json;r=[json.loads(l) for l in open('out/ledger.jsonl')];nc=[x for x in r if not x.get('run_id') or not x.get('correlation_id')];runs=sorted({x['run_id'] for x in r});spans=[x for x in r if x.get('kind')=='span-emitted'];sv=[x for x in r if x.get('semconv_version')];print(f'records={len(r)} runs={len(runs)} uncorrelated={len(nc)} spans_emitted={len(spans)} records_with_semconv_version={len(sv)}');raise SystemExit(1 if nc or not spans or not sv else 0)"`. It asserts what a caller is promised: every record of every run carries the correlation attributes the group-by depends on, and each run has telemetry emitted against a named attribute-mapping version. |
| Expected | test.sh exits 0 and prints `passed 29, failed 0`; the assertion prints `records=56 runs=4 uncorrelated=0 spans_emitted=0 records_with_semconv_version=0` and exits 1. That is the correct starting state, not a pass: the correlation half is delivered today for all four entries and the emission half is delivered nowhere, so this check starts red by construction and turns green only when cap-telemetry-implement's first exporter exists. |
| Deliberate breakage | In `examples/end-to-end/run.py`, delete the `correlation_id=c["correlation_id"],` argument from `Run.record`, which is what losing the explicit correlation attribute looks like from the caller's side. Change nothing else. |
| Expected failure | test.sh still exits 0 and still prints `passed 29, failed 0` - the existing suite asserts nothing about correlation, which is the useful half of this breakage - while the assertion prints `records=56 runs=4 uncorrelated=56 spans_emitted=0 records_with_semconv_version=0` and exits 1, the third counter having moved from 0 to 56. Measured in session cap-telemetry 2831cb4f on 2026-09-03: both runs were performed, the broken run against a copy of examples/end-to-end in this session's scratchpad, and the repository tree was left unmodified (run.py sha256 e54d31b921b707bc672c3ec6f680a7c0a77fdc9b70202ff56699e4f01d55f7e9). |
| Status | measured |
| Evidence | `F-b4-06`, `F-a7-02` "A depth-3 task tree produces three unrelated root traces." |

## Composes with

Builds on: `cap-telemetry`, `cap-telemetry-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The reference runner delivers the correlation half of this capability and none of the emission half, so a caller can group records by run today and cannot ask for a span. | Measured on 2026-09-03: the corpus carries the run and correlation identifiers on all 56 records across 4 runs and emits 0 spans and 0 mapping versions. That is the honest state of the capability from a caller's side, not a defect in the runner. | Recorded as the starting state rather than resolved here. The change proposed: keep the correlation block exactly as it is, and add a span-emitted record kind carrying the mapping version once cap-telemetry-implement's transport emitter exists, so this check turns green without any caller-visible change. | `F-b4-06`, `T-t2-03` "Correlation rides on explicit attributes, not trace parentage" |
| Which problem type does an unavailable run raise, given that the first-cut registry in docs/decomposition.md section 2.1.6 has no telemetry row? | Whether any registered type fits: the closest are document-invalid, which is about schema validation, and identity-untrusted, which is about a delegation chain. Neither is about a run whose telemetry has aged out or never existed. | Proposed: add one row, telemetry-unavailable at 404 and not retryable, as worked example 2 shows. cap-errors owns the registry, so the row lands there and this skill cites it; until it does, the type in that example is proposed and unregistered. | `F-b4-07` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-telemetry 2831cb4f, 2026-09-03 |
