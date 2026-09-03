#!/usr/bin/env python3
"""The linked conformance run: the same cases against any set of adapters.

    python3 harness/linked/conformance.py --report out/report.json

Selection is configuration - ADAPTER_CONTAINMENT, ADAPTER_GATEWAY,
ADAPTER_TRACE and ADAPTER_WORKFLOW - so the swap proof is this same file run
twice with different environment values and nothing edited.

Three groups of cases. A is the cross-door check: one document, four doors, one
subject and one resolved plan, with identity and the ceiling attaching per
door. B is the linkage: one contained turn, one completion by class, one trace
per run, three durable steps. C, D and E are the guarantees a caller never
asked for: the ceiling aggregated across the nested calls and refused when it
cannot pay, a replay that is a no-op, a malformed entry that is one typed
refusal at every door, and no product name in any file above the adapters.

Counters and the four markers are reported with the verdict, because a run that
did not exercise four doors is inconclusive and never green (F-a7-03).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import doors                                                       # noqa: E402
from interface import DOOR_FIELDS, Problem, Result                 # noqa: E402
from linked import FLOW, Linked                                    # noqa: E402

# Every product any of the four component harnesses may name inside adapters/.
# None of them may appear in a file of this harness.
PRODUCTS = re.compile(r"(litellm|openrouter|gemini|sglang|vllm|openai|anthropic|cursor|goose|"
                      r"firecracker|langfuse|temporal|gvisor|kata|hypervisor|restate|dbos|"
                      r"inngest|phoenix|braintrust)", re.I)
EXPECT_HOPS = {"human": 1, "event": 2, "schedule": 2, "external": 3}
EXPECT_STEPS = len(FLOW["steps"])
LEVELS = 3


def subject_for(kind: str, break_door_budget: bool) -> dict:
    """One document for every door. The breakage gives one door a ceiling of
    its own - the defect a per-door run cannot see, because each door alone
    still completes."""
    subject = dict(doors.SUBJECT)
    if break_door_budget and kind == "event":
        subject["budget"] = {**subject["budget"], "ceiling_micros": 2_000_000}
    return subject


def drive(out_dir: str, break_door_budget: bool = False) -> dict:
    """One document through the four doors, then the replay of each, then a
    malformed entry at each. Everything a check reads is collected here."""
    place = Linked(out_dir)
    runs, replays, refusals, problems = [], [], [], []
    for door in doors.DOORS:
        env = door.envelope(subject_for(door.kind, break_door_budget))
        answer = place.submit(env.dict())
        if isinstance(answer, Problem):
            problems.append(answer.body)
            runs.append({"door": door, "envelope": env, "problem": answer.body})
            continue
        runs.append({"door": door, "envelope": env, "result": answer,
                     "receipt": place.receipts[answer.run_id]})

        before = (place.durable_records(), place.gw.dispatches, place.units_admitted)
        again = place.submit(env.dict())                       # the same key, the same body
        after = (place.durable_records(), place.gw.dispatches, place.units_admitted)
        replays.append({"door": door, "answer": again, "delta": [a - b for a, b in zip(after, before)]})

        bad = env.dict()
        bad["payload"] = "a document is an object, not a string"   # malformed at this door
        durable_before = place.durable_records()
        refused = place.submit(bad)
        refusals.append({"door": door, "answer": refused,
                         "durable_delta": place.durable_records() - durable_before})
        if isinstance(refused, Problem):
            problems.append(refused.body)

    # the ceiling that cannot pay for the resolved plan, at its own store
    low = Linked(os.path.join(out_dir, "low"))
    tight = subject_for("human", False)
    tight["budget"] = {**tight["budget"], "ceiling_micros": 20_000}
    poor = low.submit(doors.DOORS[0].envelope(tight).dict())
    if isinstance(poor, Problem):
        problems.append(poor.body)
    return {"place": place, "runs": runs, "replays": replays, "refusals": refusals,
            "problems": problems, "poor": poor,
            "poor_state": (low.durable_records(), low.gw.dispatches, low.units_admitted)}


def scan(root: str) -> list[str]:
    hits = []
    for name in sorted(os.listdir(root)):
        if not name.endswith(".py"):
            continue
        for i, line in enumerate(open(os.path.join(root, name)), 1):
            found = PRODUCTS.search(line)
            if found and "PRODUCTS = " not in line and not line.lstrip().startswith("r\""):
                hits.append(f"{name}:{i}: {found.group(0)}")
    return hits


def conform(out_dir: str, break_door_budget: bool = False) -> dict:
    got = drive(out_dir, break_door_budget)
    place, runs = got["place"], got["runs"]
    checks: list[tuple[str, bool, str]] = []

    def chk(name: str, ok, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    done = [r for r in runs if "result" in r]
    results: list[Result] = [r["result"] for r in done]
    receipts = [r["receipt"] for r in done]
    subjects = {r["envelope"].subject_digest() for r in runs}
    plans = {a.plan_digest for a in results}

    # -- A. the cross-door check --------------------------------------------
    chk("A1 four doors were driven", len(runs) == 4, f"doors_checked={len(runs)}")
    chk("A2 one subject document across the four doors", len(subjects) == 1,
        f"subjects_distinct={len(subjects)}")
    chk("A3 one resolved plan across the four doors", len(plans) == 1 and len(results) == 4,
        f"manifests_distinct={len(plans)} over {len(results)} completed doors")
    chk("A4 identity attaches per door: four distinct actors",
        len({a.actor_subject for a in results}) == len(results),
        str(sorted({a.actor_subject for a in results})))
    chk("A5 correlation is minted per door, never shared",
        len({a.run_id for a in results}) == len(results)
        and len({a.correlation_id for a in results}) == len(results),
        f"{len({a.run_id for a in results})} run ids")
    differing = {f for f in doors.SUBJECT
                 if len({json.dumps(getattr(r["envelope"], f), sort_keys=True) for r in runs}) > 1}
    chk("A6 the envelopes differ only on the declared door fields", not differing,
        f"door fields {list(DOOR_FIELDS)}; non-door members that differ: {sorted(differing) or 'none'}")
    chk("A7 the delegation chain is the door's own",
        all(a.identity_hops == EXPECT_HOPS[a.kind] for a in results),
        str({a.kind: a.identity_hops for a in results}))
    chk("A8 one ceiling, applied per door and not supplied by any of them",
        len({a.ceiling_micros for a in results}) == 1 and len(results) == 4,
        f"ceilings={sorted({a.ceiling_micros for a in results})}")

    # -- B. the linkage ------------------------------------------------------
    chk("B1 one contained unit per run, marked from inside it",
        all(n.units_admitted == 1 and n.containment["marker"].startswith("contained-by:")
            for n in receipts),
        str({n.containment.get("marker") for n in receipts}))
    chk("B2 no secret inside a unit and every egress attempt blocked",
        all(n.containment["secrets_seen_inside"] == 0
            and n.containment["egress_attempts_made"] == n.containment["egress_attempts_blocked"]
            and n.containment["egress_attempts_made"] > 0
            and n.containment["observed_from"] == "host" for n in receipts),
        str([(n.containment["egress_attempts_made"], n.containment["egress_attempts_blocked"])
             for n in receipts]))
    chk("B3 one completion by model class per run, and no name of a server in the answer",
        all(n.gateway_dispatches == 1 for n in receipts)
        and not PRODUCTS.search(json.dumps([a.dict() for a in results])),
        f"dispatches={[n.gateway_dispatches for n in receipts]}")
    chk("B4 every step was committed through the durable executor",
        all(n.steps_committed == EXPECT_STEPS for n in receipts),
        f"steps_committed={[n.steps_committed for n in receipts]}")
    chk("B5 one trace per run, reassembled by grouping and not by parentage",
        all(n.trace["run_id_groups"] == 1 and n.trace["levels_covered"] == LEVELS
            and n.trace["distinct_trace_ids"] == LEVELS for n in receipts),
        f"groups={[n.trace['run_id_groups'] for n in receipts]} "
        f"distinct_trace_ids={[n.trace['distinct_trace_ids'] for n in receipts]}")
    chk("B6 every span carries the run id and the root dispatch id",
        all(n.trace["spans_missing_run_id"] == 0
            and n.trace["spans_missing_root_dispatch_id"] == 0 for n in receipts),
        f"missing={[n.trace['spans_missing_run_id'] for n in receipts]}")

    # -- C. the budget, aggregated across the nested calls -------------------
    chk("C1 spend is the sum of the nested step costs",
        all(a.spent_micros == sum(n.step_costs.values()) for a, n in zip(results, receipts)),
        f"spent={[a.spent_micros for a in results]}")
    chk("C2 the executor's own account of the spend agrees",
        all(a.spent_micros == n.executor_spent_micros for a, n in zip(results, receipts)),
        f"executor={[n.executor_spent_micros for n in receipts]}")
    chk("C3 the innermost call is capped at what is left of the ceiling",
        all(n.nested_ceiling_micros == a.ceiling_micros - n.step_costs["intake"]
            for a, n in zip(results, receipts)),
        f"nested_ceiling={[n.nested_ceiling_micros for n in receipts]}")
    poor, poor_state = got["poor"], got["poor_state"]
    chk("C4 a ceiling below the resolved plan is refused before anything runs",
        isinstance(poor, Problem) and poor.body["status"] == 402
        and poor.body["type"].endswith("budget-exhausted") and poor_state == (0, 0, 0),
        f"{getattr(poor, 'body', {}).get('type', poor)} · durable/dispatches/units after={poor_state}")

    # -- D. replay -----------------------------------------------------------
    same = all(isinstance(r["answer"], Result)
               and {k: v for k, v in r["answer"].dict().items() if k != "outcome"}
               == {k: v for k, v in a.dict().items() if k != "outcome"}
               and r["answer"].outcome == "replayed"
               for r, a in zip(got["replays"], results))
    chk("D1 a replay of every door returns the same result", same and len(got["replays"]) == 4,
        f"replay_noops={sum(1 for r in got['replays'] if getattr(r['answer'], 'outcome', '') == 'replayed')}")
    chk("D2 a replay writes nothing and reaches no component",
        all(r["delta"] == [0, 0, 0] for r in got["replays"]),
        f"durable/dispatch/unit deltas={[r['delta'] for r in got['replays']]}")

    # -- E. typed failures and no product name -------------------------------
    typed = [r for r in got["refusals"] if isinstance(r["answer"], Problem)
             and r["answer"].body["status"] == 422
             and r["answer"].body["type"].endswith("document-invalid")]
    chk("E1 a malformed entry at every door is one typed refusal that writes nothing",
        len(typed) == 4 and all(r["durable_delta"] == 0 for r in got["refusals"]),
        f"typed_refusals={len(typed)}")
    unregistered = [p["type"] for p in got["problems"] if not Problem.registered(p["type"])]
    chk("E2 every problem raised is in the closed registry", not unregistered,
        f"{len(got['problems'])} problems, unregistered: {unregistered or 'none'}")
    hits = scan(HERE)
    chk("F1 no product is named in any file of this harness", not hits, str(hits[:3]))

    failures = [name for name, ok, _ in checks if not ok]
    return {
        "subject_digest": sorted(subjects)[0],
        "client_shape": "raw-script",
        "doors": [{"kind": r["envelope"].kind,
                   "actor_subject": r["envelope"].actor_subject,
                   "manifest_digest": r["result"].plan_digest if "result" in r else "",
                   "subject_digest": r["envelope"].subject_digest(),
                   "identity_hops": r["envelope"].identity_hops,
                   "budget_source": "platform-default",
                   "spent_micros": r["result"].spent_micros if "result" in r else 0,
                   "stop_reason": r["result"].stop_reason if "result" in r else "",
                   "problem": r.get("problem", {}).get("type", "")} for r in runs],
        "counters": {"doors_checked": len(runs), "manifests_distinct": len(plans),
                     "subjects_distinct": len(subjects),
                     "typed_refusals": len(typed),
                     "replay_noops": sum(1 for r in got["replays"]
                                         if getattr(r["answer"], "outcome", "") == "replayed"),
                     "traces_reassembled": sum(1 for n in receipts if n.trace["run_id_groups"] == 1)},
        "adapters_selected": place.selected(),
        "markers": place.markers(),
        "checks": [list(c) for c in checks],
        "checks_total": len(checks),
        "failures": failures,
        "verdict": "pass" if not failures and len(runs) == 4 else
                   ("inconclusive" if len(runs) != 4 else "fail"),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(HERE, "out", "conformance"))
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--break-door-budget", action="store_true",
                    help="the deliberate breakage: one door carries a ceiling of its own")
    args = ap.parse_args(argv)
    shutil.rmtree(args.out, ignore_errors=True)
    report = conform(args.out, args.break_door_budget)
    print("adapters: " + "  ".join(f"{k}={v}" for k, v in report["adapters_selected"].items()))
    print("markers:  " + "  ".join(f"{k}={v}" for k, v in report["markers"].items()))
    for name, ok, detail in report["checks"]:
        print(f"  {'ok  ' if ok else 'FAIL'} {name}" + (f"  [{detail}]" if detail else ""))
    print("counters: " + json.dumps(report["counters"]))
    print(f"verdict {report['verdict']}: {report['checks_total'] - len(report['failures'])} "
          f"of {report['checks_total']} checks pass")
    if args.report:
        os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
        json.dump(report, open(args.report, "w"), indent=2, default=str)
    return 0 if report["verdict"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
