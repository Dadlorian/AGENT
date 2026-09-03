# cap-telemetry: the caller's view

Proposed. Folded in from the former `cap-telemetry-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-telemetry` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-telemetry states the contract this rests on (F-b4-06); this facet reduces it to what a caller does, which is almost nothing: one identifier comes back with the result and every question about the run is a group-by on it.  
  _sourced_ - `F-b4-06`, `T-t3-01` "Correlation rides on explicit attributes, not trace parentage"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| receive (proposed) | nothing extra; you send the envelope you were already sending, through whichever entry you already use | your result, plus the correlation block it came back with: a run identifier, a correlation identifier, and a depth if the work was delegated | proposed | `F-b4-06` |
| ask (proposed) | a run identifier | every span, metric and log the run produced, at every depth, grouped as one run however many trace trees the underlying runtimes minted | proposed | `F-a7-02` |
| hand over (proposed) | the run identifier alone | enough for someone else to ask the same question against whichever backend they have; the identifier is the whole handover, because it is an attribute on the telemetry rather than a key into a store of ours | proposed | `F-b1-05` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-telemetry` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): what comes back, and what you do with it

_proposed_ - sources: `F-b4-06`.

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

### Worked example 2 (proposed): the failure shape, when a run cannot be shown

_proposed_ - sources: `F-b4-07`.  Also carried in the body of `cap-telemetry` as the failure shape.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:telemetry:example:unavailable",
  "title": "A run with nothing to show",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Ask for a run whose retention window has passed, or one whose identifier never existed. The answer is RFC 9457 problem details with media type application/problem+json, the shape cap-errors owns. The type below is proposed and needs a row added to that registry before anything may raise it. Note what is not here: a failure to export is never raised at you, because a caller who could see one would start deciding whether telemetry mattered. The type is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns: until `urn:agentic:problem:telemetry-unavailable` has a row, an implementation returns the registered `adapter-unavailable` with the run id and the retention window in detail, accepting that it is 503 and retryable where a passed retention window is neither, which is itself the argument for the row.",
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

## What a caller does

Step 1 below is carried in the body of `cap-telemetry` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Read the run identifier off the correlation block on the result and keep it next to whatever you do with the output.**  
  _why:_ Proposed. The identifier is the only handle you need and the only one that survives a backend change; a result kept without it can still be read, but nothing about how it was produced can be found again.  
  _proposed_ - `F-b4-06`
- **Ask for a run by grouping on the run identifier. Do not start from a trace and walk up its parents, and do not treat several root traces in one run as a fault.**  
  _why:_ cap-telemetry states the contract that correlation rides on explicit attributes, not trace parentage (F-b4-06); for a caller the consequence is that the group-by is the supported query and the parent walk is the one that has already been measured to lose two thirds of a depth-3 run.  
  _sourced_ - `F-b4-06`, `F-a7-02` "Correlation rides on explicit attributes, not trace parentage"
- **Hand over the run identifier alone when someone else has to investigate, rather than a link into a particular viewer.**  
  _why:_ Proposed. The identifier is an attribute carried on the telemetry itself, so it answers the same question in whichever backend the other person has; a viewer link answers it only while that viewer is the one running.  
  _proposed_ - `F-b1-05`
- **Handle exactly one failure, the 404 in worked example 2, and handle it by saying the run cannot be shown rather than by retrying. Everything else that comes back is the ordinary answer or an ordinary typed failure.**  
  _why:_ Proposed. The failure shape, the media type and the closed registry belong to cap-errors, so a caller that already reads type and retryable needs no new branch beyond recognising one more registered type; a run outside its retention window will still be outside it on a second attempt.  
  _proposed_ - `F-b4-07`
- **When you delegate, pass the correlation block along in the payload you send, and let the platform stamp it; do not copy a trace header by hand.**  
  _why:_ cap-telemetry-implement states the boundary rule (X-entry-composition-015): correlation IDs should be preserved at every boundary, and the payload is the carrier that survives a runtime whose instrumentation nobody here controls. A hand-copied header is the case PASS.md A7 finding 1 already measured failing.  
  _sourced_ - `X-entry-composition-015`, `F-a7-02` "Correlation IDs should be preserved at every boundary"
- **Proposed: if you want to see the starting state, use examples/end-to-end. Every record it writes already carries the run and correlation identifiers, and it emits no span at all, which is exactly what the definition of done below measures.**  
  _why:_ Proposed, and it is the shortest route from this page to something running: the reference runner needs no services, and the gap it shows is the honest one rather than a rehearsed success.  
  _proposed_ - -

## Other caller invariants

- Proposed: the caller's obligation is zero fields. There is no tracing call to make, no sampling rate to set, no flag that turns telemetry on and none that turns it off; cap-telemetry fixes the contract and cap-telemetry-implement wires the injection at dispatch, so a step that produced nothing is a defect to report rather than a setting to check.  
  _proposed_ - `F-b1-08`, `F-b4-06`
- One run is one group whatever the underlying runtimes did. cap-telemetry states why (F-a7-02): a depth-3 task tree produces three unrelated root traces, so a viewer that shows several disconnected trees for one run is showing the truth, and the run identifier is what puts them back together. Seeing more than one tree is never a reason to go looking for a missing parent.  
  _sourced_ - `F-a7-02` "three unrelated root traces"
- The same run identifier covers every entry and every depth. cap-telemetry cites T-t2-03 for the placement of the concern; the caller-side consequence is that a workflow which calls an agent which calls a tool produces one group and not one per layer, because state, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used.  
  _sourced_ - `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used."

## Caller practices

- Proposed: keep the run identifier with the output, not in a ticket. The identifier is what makes an output explainable six weeks later, and it is one string; a result filed without it is a result nobody can ever ask about again.  
  _proposed_ - `F-b4-06`
- Do not go looking for a single trace tree. Nine times out of ten when spans show up as disconnected root spans instead of forming a proper trace tree, the problem is a boundary that dropped the context, and here that boundary is expected and the grouping attribute is the answer.  
  _sourced_ - `X-cross-structure-013` "when spans show up as disconnected root spans instead of forming a proper trace tree"
- Proposed: report a step with no telemetry rather than working around it. Telemetry is applied by the platform, so a step that produced none means the injection was bypassed, and a caller who quietly tolerates it is the reason nobody notices.  
  _proposed_ - `F-b1-08`
- Ask for a single run identifier per unit of work you care about, and expect one where the whole run is the unit. There is no standard attribute that groups several runs into a session yet: the vocabulary's conversation attribute is designed for single conversation flows, not multi-conversation sessions, so a question spanning runs is a question you assemble from identifiers you kept.  
  _sourced_ - `X-cross-structure-008` "designed for single conversation flows, not multi-conversation sessions"

## Open questions carried over

- **The reference runner delivers the correlation half of this capability and none of the emission half, so a caller can group records by run today and cannot ask for a span.**  
  _deciding evidence:_ Measured on 2026-09-03: the corpus carries the run and correlation identifiers on all 56 records across 4 runs and emits 0 spans and 0 mapping versions. That is the honest state of the capability from a caller's side, not a defect in the runner.  
  _default until then:_ Recorded as the starting state rather than resolved here. The change proposed: keep the correlation block exactly as it is, and add a span-emitted record kind carrying the mapping version once cap-telemetry-implement's transport emitter exists, so this check turns green without any caller-visible change.  
  `F-b4-06`, `T-t2-03` "Correlation rides on explicit attributes, not trace parentage"
- **Which problem type does an unavailable run raise, given that the first-cut registry in docs/decomposition.md section 2.1.6 has no telemetry row?**  
  _deciding evidence:_ Whether any registered type fits: the closest are document-invalid, which is about schema validation, and identity-untrusted, which is about a delegation chain. Neither is about a run whose telemetry has aged out or never existed.  
  _default until then:_ Proposed: add one row, telemetry-unavailable at 404 and not retryable, as worked example 2 shows. cap-errors owns the registry, so the row lands there and this skill cites it; until it does, the type in that example is proposed and unregistered.  
  `F-b4-07`

