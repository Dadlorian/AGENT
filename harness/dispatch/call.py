#!/usr/bin/env python3
"""The minimal call: plan one document, dispatch one unit, judge one result.

    ADAPTER=dryrun python3 harness/dispatch/call.py
    ADAPTER=second python3 harness/dispatch/call.py

Everything below the CALLER CODE marker is what a caller writes. The stamps the
platform applies - correlation id, budget ceiling, idempotency key, actor - are
put on the request here, not asked for by the caller (F-b4-01), and so are the
policy decision, the delegation check and the budget reservation, which happen
inside the seam in one fixed order before the first metered call.

Three calls are made: `plan` twice (a pure function of the document, the pinned
head and the cost inputs), `dispatch` once, and `judge` once against the
criterion the document's definition of done names by handle. The plan digest and
the verdict are the two things that must not move when the dispatcher is swapped.

Python 3.11 standard library only.
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import core  # noqa: E402
from interface import DispatchRequest, Problem, load_dispatcher  # noqa: E402

OUT = os.path.join(HERE, "out")
FIXTURES = os.path.join(HERE, "fixtures")


def build_request(envelope: dict, document: dict, dispatch_id="dsp-checkout-500s",
                  ceiling_micros=None) -> DispatchRequest:
    """One envelope in, one dispatch request out. The four stamps are applied
    here; the criterion is a handle and its body is nowhere in this object."""
    return DispatchRequest(
        dispatch_id=dispatch_id,
        idempotency_key=envelope["idempotency_key"],                    # idempotency
        document=document,
        criterion_ref=document["definition_of_done"]["criterion_ref"],  # a handle, not a body
        actor=envelope["actor"],                                        # identity
        budget={"ceiling_micros": ceiling_micros or envelope["budget"]["ceiling_micros"],
                "currency": "USD", "on_exceed": "terminate_unit"},      # budget
        deadline={"not_after": "2026-09-03T10:12:00Z", "max_duration_s": 60,
                  "cancel_grace_s": 10},
        isolation={"profile": "contained-unit", "egress": "broker-only"},
        correlation={"run_id": envelope["correlation"]["run_id"],       # correlation
                     "root_dispatch_id": dispatch_id,
                     "correlation_id": envelope["correlation"]["correlation_id"]},
        context={"receives": ["the document", "the plan's step ids"],
                 "folds_back": "one summary and the outputs' digests"})


def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + list(rows)) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def report(adapter, plan_a, plan_b, result, verdict) -> int:
    """Presentation. Every number came from the plan, the result or the verdict."""
    dispatched_plan = next(o for o in result.outputs if o.name == "plan")
    print(f"\nADAPTER={adapter}  dispatcher_marker={result.dispatcher_marker}")
    print(f"\nPLAN  {plan_a.document_id} at head {plan_a.head[:19]}...  "
          f"{len(plan_a.steps)} steps, floor {plan_a.floor_micros}, worst {plan_a.worst_micros}")
    table([(s.step_id, s.op, s.selector, s.floor_micros, s.worst_micros, s.derivation)
           for s in plan_a.steps[:6]] + [("...", "", "", "", "", "")],
          ("step", "op", "cost row", "floor", "worst", "derivation"))
    rows = [("plan run 1", plan_a.plan_digest[:26] + "...", "pure call, no clock, no network"),
            ("plan run 2", plan_b.plan_digest[:26] + "...",
             "identical" if plan_a.plan_digest == plan_b.plan_digest else "DIGESTS MOVED"),
            ("plan the dispatcher admitted on", dispatched_plan.digest[:26] + "...",
             "same document, same head, same digest"),
            ("dispatch", f"{result.state} / {result.stop_reason}",
             f"partial={result.partial}, {len(result.outputs)} outputs, "
             f"every head recorded={all(o.recorded_at_head for o in result.outputs)}"),
            ("usage", f"{result.usage.spend_micros} micros",
             f"{result.usage.steps_executed} steps executed, "
             f"{result.usage.steps_replayed} replayed"),
            ("judge", f"{verdict.verdict} ({verdict.checks_applied} checks)", verdict.detail),
            ("correlation", result.correlation["run_id"],
             f"root_dispatch_id={result.correlation['root_dispatch_id']}")]
    print()
    table(rows, ("what", "value", "note"))
    ok = (plan_a.plan_digest == plan_b.plan_digest == dispatched_plan.digest
          and result.state == "completed" and verdict.verdict == "pass")
    print("\n" + ("one plan digest, one result, one verdict" if ok else "SOMETHING MOVED"))
    return 0 if ok else 1


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# --------------------------------------------------------------------------
def main() -> int:
    adapter = os.environ.get("ADAPTER", "dryrun")          # configuration, not code
    out_dir = os.path.join(OUT, "call-" + adapter)
    document = json.load(open(os.path.join(FIXTURES, "document.json")))
    envelope = core.load_example("entries/human.json")     # the one entry envelope
    head = json.load(open(os.path.join(FIXTURES, "heads.json")))["head_full"]
    request = build_request(envelope, document)
    try:
        cost_inputs = core.cost_inputs_at(head)             # the cost table, as a value
        plan_a = core.plan(document, head, cost_inputs)     # pure: same inputs, same bytes
        plan_b = core.plan(document, head, cost_inputs)
        dispatcher = load_dispatcher(adapter, out_dir)      # one name, one binding
        result = dispatcher.dispatch(request)               # one unit, one result
        criterion = core.resolve_criterion(document["definition_of_done"]["criterion_ref"])
        verdict = core.judge(result.summary, criterion)     # pure: (result, criterion) -> verdict
    except Problem as problem:                              # one refusal shape, typed
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    return report(adapter, plan_a, plan_b, result, verdict)


if __name__ == "__main__":
    sys.exit(main())
