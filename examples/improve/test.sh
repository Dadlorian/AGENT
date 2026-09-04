#!/usr/bin/env bash
# The visible check for examples/improve. Everything here is measured, not claimed.
# It prints `passed N, failed 0` with N counting checks that actually ran; a run
# that counts nothing is a defect, not a pass, so the gate at the bottom has two
# halves: no failure, and a floor under the number of checks that ran. A gutted
# copy of this file counts zero and is refused there rather than exiting 0
# (F-a7-03 "A deterministic gate can be structurally green and mean nothing").
# FLOOR moves with provenance.json's visible_checks_counted.
#
# Every extension point and every declared value is proved by a differential run:
# the same door or the same specification twice, one declared value changed, the
# two receipts asserted different in the named way. A green run at the default
# value proves the default path and nothing else.
#
# The deciding check for this example is held out and is not in this directory.
set -u
FLOOR=88
cd "$(dirname "$0")"
ROOT=$(cd ../.. && pwd)
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
py()   { python3 - "$@"; }
run()  { python3 run.py "$@"; }

rm -rf out && mkdir -p out/mod

# --- the modified documents every differential below runs against -------------
# Each one is the shipped document with exactly one declared value changed.
py <<'PY' > out/mod/written.log
import json, os
u = json.load(open("units/improve-platform-scorecard.json"))
E = {d: json.load(open(f"entries/{d}.json")) for d in ("human", "event", "schedule", "external")}
def unit(name, mut):
    x = json.loads(json.dumps(u)); mut(x)
    json.dump(x, open(f"out/mod/{name}.json", "w"), indent=2)
def entry(name, door, mut):
    x = json.loads(json.dumps(E[door])); mut(x)
    json.dump(x, open(f"out/mod/{name}.json", "w"), indent=2)
def at(x, mid):
    return next(m for m in x["scorecard"]["metrics"] if m["metric_id"] == mid)
def cand(x, cid):
    return next(c for c in x["candidates"] if c["candidate_id"] == cid)

unit("u-scale1",           lambda x: at(x, "attempts_per_done").__setitem__("scale", 1.0))
unit("u-dirdown",          lambda x: at(x, "template_hold_rate").__setitem__("direction", "down"))
unit("u-mp01-good",        lambda x: cand(x, "rev-mp-01")["gate"].__setitem__("unit_version", "1.4.0"))
unit("u-ceiling2",         lambda x: x["loop"].__setitem__("iteration_ceiling", 2))
unit("u-ap01-target",      lambda x: cand(x, "rev-ap-01").__setitem__("value_if_promoted", 1.5))
unit("u-rollback-open",    lambda x: x["promotion"].__setitem__("rollback_to", "open_loop_checkpoint"))
unit("u-template-renamed", lambda x: cand(x, "rev-mp-02").__setitem__("template", "template:renamed-fix"))
unit("u-no-ap02",          lambda x: x.__setitem__("candidates", [c for c in x["candidates"]
                                                                  if c["candidate_id"] != "rev-ap-02"]))
unit("u-author-judgment",  lambda x: x["promotion"].__setitem__("authority", "author_judgment"))
unit("u-no-ceiling",       lambda x: x["loop"].pop("iteration_ceiling"))
unit("u-loopref",          lambda x: x["loop"].__setitem__("loop_ref", "compose-something-else"))
unit("u-half-micros",      lambda x: x["loop"].__setitem__("per_iteration_micros", 125000))
unit("u-renamed-unit",     lambda x: (x.__setitem__("unit_id", "totally-different-id"),
                                      x.__setitem__("template", "template:something-else"),
                                      x.__setitem__("note", "a different note on the same scorecard")))
for name in ("u-scale1", "u-dirdown", "u-mp01-good", "u-ceiling2", "u-ap01-target",
             "u-rollback-open", "u-template-renamed", "u-no-ap02", "u-author-judgment",
             "u-no-ceiling", "u-loopref", "u-half-micros", "u-renamed-unit"):
    entry("e-" + name, "human", lambda x, n=name: x["intent"].__setitem__("workflow_ref", f"out/mod/{n}.json"))
entry("e-ceiling-1m",   "human", lambda x: x["budget"].__setitem__("ceiling_micros", 1000000))
entry("e-ceiling-tiny", "human", lambda x: x["budget"].__setitem__("ceiling_micros", 500000))
entry("e-no-key",       "human", lambda x: x.pop("idempotency_key"))
entry("e-decision-rule", "human", lambda x: x["payload"]["improve"].__setitem__("decision_rule", "promote_regardless"))
entry("e-smuggled",     "human", lambda x: x["payload"]["improve"].__setitem__(
    "revision_offered", E["external"]["payload"]["improve"]["revision_offered"]))
entry("e-second-boundary", "schedule", lambda x: x["payload"]["improve"]["boundary"].__setitem__(
    "ref", "phase-12-answers-aligned"))
entry("e-fire-inproc",  "schedule", lambda x: x["payload"]["improve"].__setitem__("fire_mode", "in-one-process"))
entry("e-sched-tiny",   "schedule", lambda x: x["budget"].__setitem__("ceiling_micros", 500000))
entry("e-depth99",      "external", lambda x: x["correlation"].__setitem__("depth", 99))
entry("e-nofilter",     "external", lambda x: x["payload"]["improve"]["revision_offered"]["gate"].pop("case_filter"))
entry("e-partner-bare", "external", lambda x: x["payload"]["improve"].pop("revision_offered"))
entry("e-norevision",   "external", lambda x: (x["payload"]["improve"].pop("revision_offered"),
                                               x["payload"]["improve"]["boundary"].__setitem__("kind", "ceremony")))
print("modified documents written:", len(os.listdir("out/mod")) - 1)
PY
check "the differential documents were written" "$?" "0"

echo "1. four doors, one task specification, four identities"
for d in human event external; do
  run --entry "entries/$d.json" --ledger "out/$d.jsonl" > "out/$d.log" 2>&1
  check "$d exits 0" "$?" "0"
done
FIRES=0
until grep -q "^completed:" out/schedule.log 2>/dev/null || [ "$FIRES" -ge 8 ]; do
  run --entry entries/schedule.json --ledger out/schedule.jsonl > out/schedule.log 2>&1
  FIRES=$((FIRES + 1))
done
check "the schedule door closes, one iteration per fire" "$FIRES" "5"
py <<'PY' > out/doors.log 2>&1
import json
doors = ("human", "event", "schedule", "external")
rows = {d: [json.loads(l) for l in open(f"out/{d}.jsonl")] for d in doors}
one = lambda d, k: {r[k] for r in rows[d] if k in r}
sub = {d: [r for r in rows[d] if r["kind"] == "pass-submitted"][0] for d in doors}
assert len({sub[d]["unit_digest"] for d in doors}) == 1, "the four doors ran different specifications"
reg = {d: [r for r in rows[d] if r["kind"] == "scorecard-registered"][0] for d in doors}
assert len({reg[d]["scorecard_digest"] for d in doors}) == 1, "the four doors registered different scorecards"
assert {reg[d]["candidates"] for d in doors} == {5, 6}, "the offered revision did not reach the registry"
for k, n in (("actor", 4), ("run_id", 4), ("correlation_id", 4)):
    seen = {d: one(d, k) for d in doors}
    assert all(len(v) == 1 for v in seen.values()), (k, seen)
    assert len({next(iter(v)) for v in seen.values()}) == n, (k, seen)
depth = {d: next(iter(one(d, "delegation_depth"))) for d in doors}
assert depth == {"human": 0, "event": 1, "schedule": 1, "external": 2}, depth
closing = {d: [r["kind"] for r in rows[d] if r["kind"].startswith("pass-")][-1] for d in doors}
assert closing == {"human": "pass-completed", "event": "pass-escalated",
                   "schedule": "pass-completed", "external": "pass-completed"}, closing
its = {d: len([r for r in rows[d] if r["kind"] == "iteration-recorded"]) for d in doors}
assert its == {"human": 5, "event": 4, "schedule": 5, "external": 6}, its
print("one specification", sub["human"]["unit_digest"], "one scorecard", reg["human"]["scorecard_digest"])
PY
check "one specification and one scorecard digest at four doors" "$?" "0"
grep -q "one specification sha256:" out/doors.log && ok "four actors, four run ids, four correlation ids, four derived depths" \
  || bad "door identity did not separate"
grep -q "^escalated: disposition escalate, terminated_by budget_ceiling" out/event.log \
  && ok "the event door's smaller ceiling escalates rather than completing" || bad "the event door did not escalate"

echo "2. declared values, one differential per value"
diffrun() {  # label, entry, ledger-name
  run --entry "out/mod/$2.json" --ledger "out/$3.jsonl" > "out/$3.log" 2>&1
}
diffrun scale e-u-scale1 d-scale1
py <<'PY'
import json
rows = [json.loads(l) for l in open("out/d-scale1.jsonl") if '"iteration-recorded"' in l]
base = [json.loads(l) for l in open("out/human.jsonl") if '"iteration-recorded"' in l]
assert base[0]["metric_id"] == "micros_per_done", base[0]["metric_id"]
assert rows[0]["metric_id"] == "attempts_per_done", rows[0]["metric_id"]
assert rows[0]["distance_before"] == 0.9 and base[0]["distance_before"] == 0.4
PY
check "metrics[].scale is read: 3.0 works micros_per_done first, 1.0 works attempts_per_done first" "$?" "0"
diffrun direction e-u-dirdown d-dirdown
py <<'PY'
import json
n = lambda p: len([l for l in open(p) if '"iteration-recorded"' in l])
m = {json.loads(l)["metric_id"] for l in open("out/d-dirdown.jsonl") if '"iteration-recorded"' in l}
assert n("out/d-dirdown.jsonl") == 4 and n("out/human.jsonl") == 5, (n("out/d-dirdown.jsonl"),)
assert "template_hold_rate" not in m, "a metric already at its target was worked anyway"
PY
check "metrics[].direction is read: down puts template_hold_rate at target, so it is never worked" "$?" "0"
diffrun ceiling2 e-u-ceiling2 d-ceiling2
py <<'PY'
import json
cap = [json.loads(l) for l in open("out/d-ceiling2.jsonl")][-1]
full = [json.loads(l) for l in open("out/human.jsonl")][-1]
assert full["kind"] == "pass-completed" and full["terminated_by"] == "verdict_pass", full
assert cap["kind"] == "pass-escalated" and cap["terminated_by"] == "iteration_ceiling", cap
assert cap["targets_held"] == 1 and full["targets_held"] == 3, (cap["targets_held"],)
assert cap["escalation"]["status"] == 504 and "iteration-ceiling-reached" in cap["escalation"]["detail"]
assert cap["escalation"]["type"].endswith("deadline-exceeded"), cap["escalation"]["type"]
PY
check "loop.iteration_ceiling is read: 8 gives verdict_pass 3/3, 2 gives iteration_ceiling 1/3" "$?" "0"
diffrun ceiling1m e-ceiling-1m d-ceiling1m
py <<'PY'
import json
low = [json.loads(l) for l in open("out/d-ceiling1m.jsonl")][-1]
assert low["terminated_by"] == "budget_ceiling" and low["iterations_run"] == 4, low
assert low["escalation"]["status"] == 402 and low["cost_micros"] == 1000000, low["escalation"]
assert [json.loads(l) for l in open("out/human.jsonl")][-1]["iterations_run"] == 5
PY
check "budget.ceiling_micros is read at the exit condition: 1000000 stops at 4, 3000000 runs to 5" "$?" "0"
diffrun value e-u-ap01-target d-value
py <<'PY'
import json
rows = [json.loads(l) for l in open("out/d-value.jsonl") if '"iteration-recorded"' in l]
ids = [json.loads(l)["candidate_id"] for l in open("out/human.jsonl") if '"iteration-recorded"' in l]
assert "rev-ap-02" in ids, ids
assert "rev-ap-02" not in [r["candidate_id"] for r in rows], "the second candidate was authored anyway"
ap = [r for r in rows if r["metric_id"] == "attempts_per_done"]
assert len(ap) == 1 and ap[0]["distance_after"] == 0.0, ap
PY
check "candidates[].value_if_promoted is read: a value that reaches the target closes the metric in one" "$?" "0"

echo "3. the gate decides, and the decision is the gate's"
diffrun mp01good e-u-mp01-good d-mp01good
py <<'PY'
import json
good = [json.loads(l) for l in open("out/d-mp01good.jsonl") if '"iteration-recorded"' in l]
ship = [json.loads(l) for l in open("out/human.jsonl") if '"iteration-recorded"' in l]
assert ship[0]["candidate_id"] == good[0]["candidate_id"] == "rev-mp-01"
assert (ship[0]["gate_outcome"], ship[0]["decision"], ship[0]["checkpoint_advanced"]) == ("failed", "declined", False), ship[0]
assert (good[0]["gate_outcome"], good[0]["decision"], good[0]["checkpoint_advanced"]) == ("passed", "promoted", True), good[0]
assert ship[0]["checkpoint_id"] == ship[0]["rollback_to_checkpoint_id"], "a declined iteration moved the checkpoint"
assert len(ship) == 5 and len(good) == 4
PY
check "candidates[].gate.unit_version is read: 1.4.1-rc declines and holds, 1.4.0 promotes and advances" "$?" "0"
run --entry entries/human.json --promote-regardless --ledger out/break.jsonl > out/break.log 2>&1
check "the breakage run exits 0" "$?" "0"
py <<'PY'
import json
br = [json.loads(l) for l in open("out/break.jsonl") if '"iteration-recorded"' in l]
ok_ = [json.loads(l) for l in open("out/human.jsonl") if '"iteration-recorded"' in l]
assert br[0]["gate_outcome"] == ok_[0]["gate_outcome"] == "failed", "the gate stopped saying failed"
assert br[0]["decision"] == "promoted" and br[0]["checkpoint_advanced"], br[0]
assert ok_[0]["decision"] == "declined" and not ok_[0]["checkpoint_advanced"], ok_[0]
assert br[0]["promotion_authority"] == "operator-override(breakage)"
assert ok_[0]["promotion_authority"] == "evaluation_gate"
PY
check "the deliberate breakage: the same failed gate promotes when the rule stops reading it" "$?" "0"

echo "4. an outside revision is gated like any other, and an empty gate is never green"
py <<'PY'
import json
ext = [json.loads(l) for l in open("out/external.jsonl")]
off = [r for r in ext if r["kind"] == "revision-offered"]
assert len(off) == 1 and off[0]["candidate_id"] == "rev-xp-01" and off[0]["carries_criterion"] is False
its = [r for r in ext if r["kind"] == "iteration-recorded"]
mine = [r for r in its if r["candidate_id"] == "rev-xp-01"]
assert len(mine) == 1, mine
r = mine[0]
assert r["cases_executed"] == 0 and r["gate_outcome"] == "inconclusive", r
assert r["decision"] == "declined" and not r["checkpoint_advanced"], r
assert r["checkpoint_id"] == r["rollback_to_checkpoint_id"], "an inconclusive gate moved the checkpoint"
after = its[its.index(r) + 1]
assert after["metric_id"] == r["metric_id"] and after["candidate_id"] == "rev-th-01", after
learned = [x for x in ext if x["kind"] == "learned"][0]
assert learned["by_template"]["template:partner-sweep"] == {"offered": 1, "held": 0}, learned["by_template"]
PY
check "the offered revision is declined on 0 cases executed and the metric is worked again" "$?" "0"
py <<'PY'
import json
fail = [json.loads(l) for l in open("out/human.jsonl") if '"iteration-recorded"' in l][0]
inc = [json.loads(l) for l in open("out/external.jsonl") if '"iteration-recorded"' in l][3]
assert fail["gate_outcome"] == "failed" and inc["gate_outcome"] == "inconclusive"
for r in (fail, inc):
    assert r["decision"] == "declined" and not r["checkpoint_advanced"] and r["reason"] is not None
assert fail["reason"] == "gate_failed" and inc["reason"] == "gate_inconclusive"
PY
check "inconclusive is not a softer failed: both decline and both hold the checkpoint" "$?" "0"
diffrun nofilter e-nofilter d-nofilter
py <<'PY'
import json
r = [json.loads(l) for l in open("out/d-nofilter.jsonl") if '"rev-xp-01"' in l and '"iteration-recorded"' in l][0]
assert r["cases_executed"] == 6 and r["gate_outcome"] == "passed" and r["decision"] == "promoted", r
PY
check "gate.case_filter is read: none executes 0 cases and declines, removed executes 6 and promotes" "$?" "0"
diffrun norevision e-norevision d-norevision
py <<'PY'
import json
n = lambda p: [json.loads(l) for l in open(p) if '"iteration-recorded"' in l]
assert len(n("out/external.jsonl")) == 6 and len(n("out/d-norevision.jsonl")) == 5
assert not [r for r in n("out/d-norevision.jsonl") if r["candidate_id"] == "rev-xp-01"]
assert not [l for l in open("out/d-norevision.jsonl") if '"revision-offered"' in l]
PY
check "revision_offered is read: with it 6 iterations and rev-xp-01 authored, without it 5 and never" "$?" "0"

echo "5. the two swaps: the loop driver by declaration, the evaluation adapter by configuration"
diffrun fireinproc e-fire-inproc d-fireinproc
py <<'PY'
import json
fire = [json.loads(l) for l in open("out/schedule.jsonl")]
proc = [json.loads(l) for l in open("out/d-fireinproc.jsonl")]
parked = [r for r in fire if r["kind"] == "pass-parked"]
assert len(parked) == 4 and not [r for r in proc if r["kind"] == "pass-parked"], len(parked)
strip = lambda rows: [{k: v for k, v in r.items() if k not in ("seq", "prev", "hash")}
                      for r in rows if r["kind"] == "iteration-recorded"]
a, b = strip(fire), strip(proc)
assert len(a) == len(b) == 5, (len(a), len(b))
assert a == b, [x for x in zip(a, b) if x[0] != x[1]][:1]
assert [r for r in fire if r["kind"] == "pass-submitted"][0]["driver"] != \
       [r for r in proc if r["kind"] == "pass-submitted"][0]["driver"]
print("records identical across fire modes:", len(a))
PY
check "fire_mode is read: 5 fires with 4 parks against 1 process, and the same five records byte for byte" "$?" "0"
py <<'PY'
import os, sys
sys.path.insert(0, os.getcwd())
import harnesses
il, build = harnesses.improvement_loop()
axes = {}
for name in harnesses.DRIVERS:
    d = build(name)
    axes[name] = (d.execution_model, d.checkpoint_store, d.survives_process_loss)
assert len(set(axes.values())) == 2, axes
assert sum(1 for i in range(3) if axes["dryrun"][i] != axes["second"][i]) == 3, axes
assert {d.promotion_authority for d in (build("dryrun"), build("second"))} == {"evaluation_gate"}
PY
check "the two drivers differ on all three declared axes and neither may promote on its own" "$?" "0"
run --entry entries/human.json --gate second --ledger out/gate2.jsonl > out/gate2.log 2>&1
check "the second evaluation adapter runs the same pass" "$?" "0"
py <<'PY'
import json
def strip(path, kind):
    return [{k: v for k, v in json.loads(l).items() if k not in ("seq", "prev", "hash")}
            for l in open(path) if f'"{kind}"' in l]
a, b = strip("out/human.jsonl", "iteration-recorded"), strip("out/gate2.jsonl", "iteration-recorded")
assert len(a) == 5 and a == b, "the two evaluation adapters disagreed"
# the outcome and the learned table are compared too, not only the rows inside them:
# a claim about identical outcomes is not closed by comparing what happened per iteration.
for kind in ("pass-completed", "learned"):
    x, y = strip("out/human.jsonl", kind), strip("out/gate2.jsonl", kind)
    assert len(x) == len(y) == 1, (kind, len(x), len(y))
    assert x == y, (kind, [k for k in x[0] if x[0][k] != y[0][k]])
assert x[0]["micros"] == 1250000 and json.loads(
    [l for l in open("out/human.jsonl") if '"pass-completed"' in l][0])["cost_micros"] == 1250000
import os, sys
sys.path.insert(0, os.getcwd())
import harnesses
il, _ = harnesses.improvement_loop()
axes = {n: (a_.execution_model, a_.trajectory_source, a_.emit_evaluation_result)
        for n in il.GATE_ADAPTERS for a_ in [il.load_gate_adapter(n)]}
assert sum(1 for i in range(3) if axes["dryrun"][i] != axes["second"][i]) == 3, axes
PY
check "both evaluation adapters give the same iterations, the same closing record and the same learned table" "$?" "0"

echo "6. one boundary is one pass"
run --entry out/mod/e-second-boundary.json --ledger out/second-boundary.jsonl > out/second-boundary.log 2>&1
check "a second boundary exits 0" "$?" "0"
py <<'PY'
import json
a = [json.loads(l) for l in open("out/schedule.jsonl")]
b = [json.loads(l) for l in open("out/second-boundary.jsonl")]
la = [r for r in a if r["kind"] == "loop-opened"][0]
lb = [r for r in b if r["kind"] == "loop-opened"][0]
assert la["loop_id"] != lb["loop_id"], "two boundaries shared one loop"
assert la["boundary_ref"] != lb["boundary_ref"]
first = [r for r in b if r["kind"] == "iteration-recorded"]
assert len(first) == 1 and first[0]["iteration_index"] == 0, first
resumed = [r for r in a if r["kind"] == "iteration-recorded"]
assert [r["iteration_index"] for r in resumed] == [0, 1, 2, 3, 4], resumed
assert len([r for r in a if r["kind"] == "loop-opened"]) == 1, "a resumed fire re-opened the loop"
PY
check "boundary.ref is read: the same boundary resumes at the next index, a different one opens a loop at 0" "$?" "0"
# Two receipts whose file names collide are two passes, not one: the driver's store
# is keyed on the receipt's resolved path. If it were keyed on the basename, the
# second fire below would resume a loop against an empty receipt.
mkdir -p out/a out/b out/c
run --entry entries/schedule.json --ledger out/a/probe.jsonl > out/a/probe.log 2>&1
check "the first of two same-named receipts exits 0" "$?" "0"
run --entry entries/schedule.json --ledger out/b/probe.jsonl > out/b/probe.log 2>&1
check "the second of two same-named receipts exits 0" "$?" "0"
py <<'PY'
import json
rows = {d: [json.loads(l) for l in open(f"out/{d}/probe.jsonl")] for d in ("a", "b")}
for d, rs in rows.items():
    assert [r["kind"] for r in rs] == ["pass-submitted", "scorecard-registered", "loop-opened",
                                       "iteration-recorded", "pass-parked"], (d, [r["kind"] for r in rs])
    assert [r for r in rs if r["kind"] == "iteration-recorded"][0]["iteration_index"] == 0, d
    assert "Traceback" not in open(f"out/{d}/probe.log").read(), d
PY
check "two receipts with one basename are two passes, each opening its own loop at index 0" "$?" "0"
# And the separated case is a typed refusal rather than an unguarded store read: a
# store holding a checkpoint whose receipt holds no loop-opened record.
run --entry entries/schedule.json --ledger out/c/probe.jsonl > out/c/first.log 2>&1
: > out/c/probe.jsonl
run --entry entries/schedule.json --ledger out/c/probe.jsonl > out/c/resumed.log 2>&1
check "a resumed fire whose receipt holds no loop-opened exits 2" "$?" "2"
py <<'PY'
import json
body = open("out/c/resumed.log").read()
assert "Traceback" not in body, body[-400:]
lines = body.splitlines(True)
head = [n for n, l in enumerate(lines) if l.strip() == "application/problem+json"]
assert len(head) == 1, body[-400:]
problem = json.loads("".join(lines[head[0] + 1:]))
assert problem["type"] == "urn:agentic:problem:document-invalid" and problem["status"] == 422, problem
assert "loop-opened" in problem["detail"], problem["detail"]
rows = [json.loads(l) for l in open("out/c/probe.jsonl")]
assert [r["kind"] for r in rows] == ["refusal"] and rows[0]["at"] == "resume", rows
PY
check "the separated fire is refused 422 at resume and records it, rather than raising" "$?" "0"
BEFORE=$(wc -l < out/human.jsonl)
run --entry entries/human.json --ledger out/human.jsonl > out/replay.log 2>&1
check "re-firing a closed pass exits 0" "$?" "0"
check "re-firing a closed pass appends nothing" "$(wc -l < out/human.jsonl)" "$BEFORE"
grep -q "^REPLAY: improve-human-ceremony-75-run-review already closed as pass-completed" out/replay.log \
  && ok "the receipt is the idempotency authority: the same key returns REPLAY" || bad "no REPLAY line"

echo "7. refusals: typed, and before the work they refuse"
refuse() {  # label, document, expected type suffix, expected status
  run --entry "out/mod/$2.json" --ledger "out/r-$2.jsonl" > "out/r-$2.log" 2>&1
  check "$1 exits 2" "$?" "2"
  py "$2" "$3" "$4" <<'PY'
import json, sys
name, want_type, want_status = sys.argv[1], sys.argv[2], int(sys.argv[3])
lines = open(f"out/r-{name}.log").read().splitlines(True)
head = [i for i, l in enumerate(lines) if l.strip() == "application/problem+json"]
assert len(head) == 1, f"{name}: expected one problem body, found {len(head)}"
body = json.loads("".join(lines[head[0] + 1:]))
assert body["type"] == "urn:agentic:problem:" + want_type, body["type"]
assert body["status"] == want_status, body["status"]
assert body["title"] and body["detail"], body
PY
  check "$1 is $3 ($4)" "$?" "0"
}
refuse "a malformed envelope" e-no-key document-invalid 422
refuse "a caller declaring the decision rule" e-decision-rule document-invalid 422
refuse "a revision offered at a boundary that may not offer one" e-smuggled document-invalid 422
refuse "a partner finding that names no revision" e-partner-bare document-invalid 422
refuse "a specification naming another promotion authority" e-u-author-judgment document-invalid 422
refuse "a specification with no iteration ceiling" e-u-no-ceiling document-invalid 422
refuse "a plan floor above the ceiling" e-ceiling-tiny budget-exhausted 402
refuse "a metric with no candidate left to author" e-u-no-ap02 criterion-unresolvable 422
py <<'PY'
import json, os
# what was NOT written: a refused envelope leaves no receipt at all, and a pass
# refused at the plan leaves the submission and the refusal and nothing else.
for name in ("e-no-key", "e-decision-rule", "e-smuggled", "e-partner-bare",
             "e-u-author-judgment", "e-u-no-ceiling"):
    assert not os.path.exists(f"out/r-{name}.jsonl"), f"{name} wrote a receipt"
rows = [json.loads(l) for l in open("out/r-e-ceiling-tiny.jsonl")]
assert [r["kind"] for r in rows] == ["pass-submitted", "refusal"], [r["kind"] for r in rows]
assert rows[1]["at"] == "plan" and rows[1]["ended_pass"] is True
fail = [json.loads(l) for l in open("out/r-e-u-no-ap02.jsonl")]
kinds = [r["kind"] for r in fail]
assert kinds[-3:] == ["refusal", "learned", "pass-failed"], kinds
assert [r for r in fail if r["kind"] == "refusal"][0]["at"] == "run_iteration"
assert [r for r in fail if r["kind"] == "iteration-recorded"], "the pass failed before it ran anything"
PY
check "a refusal before any spend writes no loop, and a refusal after work names where it happened" "$?" "0"
# The plan's 402 is a first-fire gate. A fire that resumes an open loop is priced by
# nothing, and the exit condition reads the ceiling the loop was OPENED with: the
# same 500000 that is refused before a case is replayed on a first fire is neither
# refused nor enforced on a resumed one. Measured, not smoothed over; README gap G11.
run --entry entries/schedule.json --ledger out/resume-tiny.jsonl > out/resume-tiny-1.log 2>&1
check "the first fire of the resumed-ceiling pass exits 0" "$?" "0"
FIRES=0
until grep -qE "^(completed|escalated):" out/resume-tiny-2.log 2>/dev/null || [ "$FIRES" -ge 8 ]; do
  run --entry out/mod/e-sched-tiny.json --ledger out/resume-tiny.jsonl > out/resume-tiny-2.log 2>&1
  FIRES=$((FIRES + 1))
done
check "the fires declaring a ceiling below the plan floor close the pass instead of being refused" "$FIRES" "4"
py <<'PY'
import json
rows = [json.loads(l) for l in open("out/resume-tiny.jsonl")]
assert not [r for r in rows if r["kind"] == "refusal"], "a resumed fire was refused at the plan"
close = [r for r in rows if r["kind"] == "pass-completed"]
assert len(close) == 1 and close[0]["terminated_by"] == "verdict_pass", close
tiny = json.load(open("out/mod/e-sched-tiny.json"))["budget"]["ceiling_micros"]
assert tiny == 500000 and close[0]["cost_micros"] == 1250000, (tiny, close[0]["cost_micros"])
assert "spent 1250000 of 500000 micros" in open("out/resume-tiny-2.log").read()
first = [json.loads(l) for l in open("out/r-e-ceiling-tiny.jsonl")]
assert [r["kind"] for r in first] == ["pass-submitted", "refusal"], first
assert first[1]["type"].endswith("budget-exhausted") and first[1]["at"] == "plan", first[1]
PY
check "the same ceiling refuses a first fire 402 and reaches nothing on a resumed one" "$?" "0"
py <<'PY'
import os, sys
sys.path.insert(0, os.getcwd())
import harnesses
il, _ = harnesses.improvement_loop()
seen = set()
for name in ("document-invalid", "budget-exhausted", "criterion-unresolvable",
             "adapter-unavailable", "deadline-exceeded", "iteration-ceiling-reached"):
    p = il.problem(name, "probe")
    seen.add(p.type)
    assert p.type.startswith("urn:agentic:problem:")
assert "urn:agentic:problem:iteration-ceiling-reached" not in seen, "an unregistered type was minted"
assert len(seen) == 5, sorted(seen)
PY
check "no unregistered problem type is minted: six suffixes render as five registered types" "$?" "0"

echo "8. the stamps, the rollback state, and a member nothing reads"
py <<'PY'
import glob, json
need = {"run_id", "correlation_id", "actor", "delegation_depth", "entry_kind",
        "idempotency_key", "boundary_kind", "boundary_ref", "kind", "seq", "prev", "hash"}
n = 0
for path in glob.glob("out/*.jsonl") + glob.glob("out/mod/*.jsonl"):
    for line in open(path):
        row = json.loads(line)
        missing = need - set(row)
        assert not missing, (path, row["kind"], missing)
        n += 1
assert n > 100, n
print("records carrying every stamp:", n)
PY
check "every record of every run carries the seven stamps and the chain fields" "$?" "0"
py <<'PY2'
import glob, json, re
# the README's list of record kinds, set for set against the receipts themselves,
# and the number it spells read back out of the same list.
row = [l for l in open("README.md") if l.startswith("| The receipt: `out/*.jsonl`")]
assert len(row) == 1, len(row)
named = {m for m in re.findall(r"`([a-z][a-z-]+)`", row[0])}
written = set()
for path in glob.glob("out/**/*.jsonl", recursive=True):
    for line in open(path):
        written.add(json.loads(line)["kind"])
assert named == written, {"named, never written": sorted(named - written),
                          "written, never named": sorted(written - named)}
words = {11: "eleven", 10: "ten", 12: "twelve", 13: "thirteen", 9: "nine"}
assert f"the {words[len(written)]} kinds" in row[0], (len(written), row[0][-400:])
print("record kinds named and written:", len(written))
PY2
check "the README names every record kind these runs write, and no other, and counts them right" "$?" "0"
diffrun rollback e-u-rollback-open d-rollback
py <<'PY'
import json
prev = [json.loads(l) for l in open("out/human.jsonl") if '"iteration-recorded"' in l]
opened = [json.loads(l) for l in open("out/d-rollback.jsonl") if '"iteration-recorded"' in l]
assert [r["rollback_to"] for r in prev][:1] == ["previous_checkpoint"]
assert [r["rollback_to"] for r in opened][:1] == ["open_loop_checkpoint"]
assert prev[0]["rollback_to_checkpoint_id"] == opened[0]["rollback_to_checkpoint_id"]
differ = [i for i in range(1, 5) if prev[i]["rollback_to_checkpoint_id"] != opened[i]["rollback_to_checkpoint_id"]]
assert differ == [2, 3, 4], differ
o = json.loads([l for l in open("out/d-rollback.jsonl") if '"loop-opened"' in l][0])
assert {r["rollback_to_checkpoint_id"] for r in opened} == {o["open_checkpoint_id"]}, "not the opening state"
PY
check "promotion.rollback_to is read: previous_checkpoint and open_loop_checkpoint name different states" "$?" "0"
diffrun depth99 e-depth99 d-depth99
py <<'PY'
import json
strip = lambda p: [{k: v for k, v in json.loads(l).items() if k not in ("seq", "prev", "hash")}
                   for l in open(p)]
a, b = strip("out/external.jsonl"), strip("out/d-depth99.jsonl")
assert a == b, "a member nothing reads changed a record"
assert {r["delegation_depth"] for r in b} == {2}, "the declared depth reached a record"
PY
check "correlation.depth is carried and not consumed: 1 and 99 give identical records at depth 2" "$?" "0"
diffrun loopref e-u-loopref d-loopref
py <<'PY'
import dataclasses, json, os, sys
strip = lambda p: [{k: v for k, v in json.loads(l).items() if k not in ("seq", "prev", "hash")}
                   for l in open(p)]
a, b = strip("out/human.jsonl"), strip("out/d-loopref.jsonl")
assert len(a) == len(b) == 10, (len(a), len(b))
for x, y in zip(a, b):
    if x["kind"] == "pass-submitted":
        assert x["unit_digest"] != y["unit_digest"], "the two specifications were one document"
        x = {k: v for k, v in x.items() if k != "unit_digest"}
        y = {k: v for k, v in y.items() if k != "unit_digest"}
    assert x == y, (x["kind"], [k for k in x if x[k] != y.get(k)])
assert "loop_ref" not in open("run.py").read(), "the runner reads loop_ref after all"
sys.path.insert(0, os.getcwd())
import harnesses
il, build = harnesses.improvement_loop()
assert "loop_ref" not in [f.name for f in dataclasses.fields(il.LoopSpec)], "LoopSpec carries it"
assert "loop_ref" not in json.dumps(il.LOOP_SPEC_SCHEMA), "the capability's schema names it"
# on_cap is the half that IS read: the capability refuses a declaration that changes
# it, and this example's own schema refuses such a specification first.
bad = build("dryrun").open_loop(il.LoopSpec("il-probe", 8, 3000000, 250000, "continue"),
                                "sc-improve-platform")
assert isinstance(bad, il.Problem) and bad.status == 422 and "on_cap" in bad.detail, bad
unit = json.load(open("units/improve-platform-scorecard.json"))
unit["loop"]["on_cap"] = "continue"
errs = harnesses.reference().validate(unit, json.load(open("schemas/unit.schema.json")))
assert errs and any("on_cap" in e for e in errs), errs
PY
check "loop.on_cap is read and validated; loop.loop_ref reaches no code, no schema and no record" "$?" "0"
diffrun renamedunit e-u-renamed-unit d-renamedunit
py <<'PY'
import json
strip = lambda p: [{k: v for k, v in json.loads(l).items() if k not in ("seq", "prev", "hash")}
                   for l in open(p)]
a, b = strip("out/human.jsonl"), strip("out/d-renamedunit.jsonl")
assert len(a) == len(b) == 10, (len(a), len(b))
moved = [(x, y) for x, y in zip(a, b) if x != y]
assert len(moved) == 1 and moved[0][0]["kind"] == "pass-submitted", [x["kind"] for x, _ in moved]
x, y = moved[0]
assert {k for k in x if x[k] != y[k]} == {"unit_id", "template", "unit_digest"}, \
    {k for k in x if x[k] != y[k]}
assert (y["unit_id"], y["template"]) == ("totally-different-id", "template:something-else"), y
assert "template:something-else" not in json.dumps(
    [json.loads(l) for l in open("out/d-renamedunit.jsonl") if '"learned"' in l][-1]), \
    "the specification's own template reached the learned table"
PY
check "unit_id, template and note are carried and not consumed: three strings of one record move" "$?" "0"
run --verify-ledger --ledger out/human.jsonl > out/verify.log 2>&1
check "the receipt's hash chain verifies" "$?" "0"
py <<'PY'
lines = open("out/human.jsonl").read().splitlines(True)
lines[3] = lines[3].replace("micros_per_done", "micros_per_dono", 1)
open("out/tampered.jsonl", "w").writelines(lines)
PY
run --verify-ledger --ledger out/tampered.jsonl > out/tampered.log 2>&1
check "a one-word edit to the receipt is detected" "$?" "2"
grep -q "chain broken at seq 3" out/tampered.log && ok "the break is located at the record that moved" \
  || bad "the tamper was not located"

echo "9. the learned numbers, recomputed from the records"
py <<'PY'
import json
unit = json.load(open("units/improve-platform-scorecard.json"))
# What an iteration cost is the spend_micros that iteration's own record carries.
# A row count times the declared price would agree with the runner while telling
# nobody whether either read the records.
spend = lambda rs: sum(int(r["spend_micros"]) for r in rs)
tpl = {c["candidate_id"]: c["template"] for c in unit["candidates"]}
tpl["rev-xp-01"] = json.load(open("entries/external.json"))["payload"]["improve"]["revision_offered"]["template"]
for door in ("human", "event", "schedule", "external"):
    rows = [json.loads(l) for l in open(f"out/{door}.jsonl")]
    its = [r for r in rows if r["kind"] == "iteration-recorded"]
    said = [r for r in rows if r["kind"] == "learned"][-1]
    assert said["iterations"] == len(its), (door, said["iterations"], len(its))
    assert said["micros"] == spend(its), (door, said["micros"], spend(its))
    assert said["promoted"] == len([r for r in its if r["decision"] == "promoted"])
    assert said["declined"] == len(its) - said["promoted"]
    assert said["promoted"] + said["declined"] == len(its), (door, said)
    closing = [r for r in rows if r["kind"].startswith("pass-") and "cost_micros" in r]
    assert len(closing) == 1 and closing[0]["cost_micros"] == spend(its), (door, closing)
    for m in unit["scorecard"]["metrics"]:
        mine = [r for r in its if r["metric_id"] == m["metric_id"]]
        held = [r for r in mine if r["decision"] == "promoted"]
        row = said["per_metric"][m["metric_id"]]
        assert row["attempts"] == len(mine) and row["micros"] == spend(mine), (door, m["metric_id"], row)
        assert row["held_candidate"] == (held[-1]["candidate_id"] if held else None), (door, row)
        assert row["held_template"] == (tpl.get(held[-1]["candidate_id"]) if held else None), (door, row)
        if mine:
            assert row["distance_at_open"] == mine[0]["distance_before"]
            assert row["distance_now"] == mine[-1]["distance_after"]
    by = {}
    for r in its:
        b = by.setdefault(tpl[r["candidate_id"]], {"offered": 0, "held": 0})
        b["offered"] += 1
        b["held"] += 1 if r["decision"] == "promoted" else 0
    assert said["by_template"] == by, (door, said["by_template"], by)
print("learned rows recomputed for four doors")
PY
check "every learned number is recomputed from the iteration records at all four doors" "$?" "0"
py <<'PY'
import json, re
learned = [json.loads(l) for l in open("out/human.jsonl") if '"learned"' in l][-1]
line = [l for l in open("out/human.log") if "micros per target held" in l][-1]
n = [int(x) for x in re.findall(r"\d+", line)]
assert n[:3] == [learned["iterations"], learned["promoted"], learned["declined"]], (n, learned)
assert n[3] == learned["micros"] and n[5] == learned["micros"] // 3, (n, learned)
PY
check "the printed totals are the record's numbers, not a second count" "$?" "0"
diffrun renamed e-u-template-renamed d-renamed
py <<'PY'
import json
a = [json.loads(l) for l in open("out/human.jsonl") if '"learned"' in l][-1]
b = [json.loads(l) for l in open("out/d-renamed.jsonl") if '"learned"' in l][-1]
assert a["per_metric"]["micros_per_done"]["held_template"] == "template:contained-fix"
assert b["per_metric"]["micros_per_done"]["held_template"] == "template:renamed-fix"
assert set(b["by_template"]) == {"template:contained-fix", "template:renamed-fix", "template:gated-release"}
assert a["iterations"] == b["iterations"] == 5
PY
check "candidates[].template is read: renaming it renames the template the learned table says held" "$?" "0"
diffrun halfmicros e-u-half-micros d-halfmicros
py <<'PY'
import json, re
floor = lambda path: int(re.search(r"floor (\d+) micros", open(path).read()).group(1))
assert (floor("out/human.log"), floor("out/d-halfmicros.log")) == (750000, 375000), \
    (floor("out/human.log"), floor("out/d-halfmicros.log"))
rows = lambda path: [json.loads(l) for l in open(path)]
base, half = rows("out/human.jsonl"), rows("out/d-halfmicros.jsonl")
its = lambda rs: [r for r in rs if r["kind"] == "iteration-recorded"]
one = lambda rs, kind: [r for r in rs if r["kind"] == kind][-1]
assert len(its(base)) == len(its(half)) == 5, (len(its(base)), len(its(half)))
assert {r["spend_micros"] for r in its(base)} == {250000}, "the shipped price is not on the records"
assert {r["spend_micros"] for r in its(half)} == {125000}, "halving the price left the records alone"
assert (one(base, "learned")["micros"], one(half, "learned")["micros"]) == (1250000, 625000)
assert (one(base, "pass-completed")["cost_micros"],
        one(half, "pass-completed")["cost_micros"]) == (1250000, 625000)
PY
check "loop.per_iteration_micros is read: halving it halves the plan floor, every record's spend, the learned micros and the cost" "$?" "0"

echo "10. provenance cites exactly the ids the rows carry, in both directions"
py <<'PY'
import glob, json, os, re
prov = json.load(open("provenance.json"))
for field in ("area", "doors", "cites", "measured", "claimed", "litmus_sections", "visible_checks_counted"):
    assert field in prov, f"provenance is missing {field}"
assert prov["area"] == "improve" and sorted(prov["doors"]) == ["event", "external", "human", "schedule"]
cited = set(prov["cites"])
pattern = re.compile(r"\b(?:F|E|R|T|X|REF)-[A-Za-z0-9][A-Za-z0-9./_#,-]*")   # CITES-SCAN
sources = ["README.md", "run.py", "harnesses.py", "test.sh"] + sorted(
    glob.glob("units/*.json") + glob.glob("schemas/*.json") + glob.glob("entries/*.json"))
found = set()
for path in sources:
    for line in open(path):
        if "CITES-SCAN" in line:          # the scanner's own pattern is not a citation
            continue
        for m in pattern.findall(line):
            found.add(m.rstrip(".,;)"))
assert cited == found, {"cited, carried by no row": sorted(cited - found),
                        "carried by a row, never cited": sorted(found - cited)}
print(f"{len(found)} ids across {len(sources)} files, cited both ways")
PY
check "provenance.cites equals the ids the rows carry, over every file of the example" "$?" "0"
py <<'PY'
import json, os
prov = json.load(open("provenance.json"))
missing = [c for c in prov["cites"] if c.startswith("REF-")
           and not os.path.exists(os.path.join("../..", c[4:].split("#")[0]))]
assert not missing, missing
readme = open("README.md").read()
gaps = [f"| G{i} |" for i in range(1, 12)]
assert all(g in readme for g in gaps), [g for g in gaps if g not in readme]
assert "| G12 |" not in readme
PY
check "every REF- id resolves to a file on disk, and the gap table is keyed G1..G11" "$?" "0"

echo "11. every quote is grepped back out of the record it names"
py <<'PY'
import glob, json, os, re, sys
ROOT = "../.."
records = {}
for name in ("facts", "target-facts", "reference-facts"):
    for line in open(os.path.join(ROOT, "kb", f"{name}.jsonl")):
        row = json.loads(line)
        records[row["id"]] = row.get("text", "")
for path in glob.glob(os.path.join(ROOT, "kb", "research", "*.jsonl")):
    for line in open(path):
        row = json.loads(line)
        records[row["id"]] = json.dumps(row, ensure_ascii=False)
norm = lambda s: re.sub(r"\s+", " ", s).replace("—", "-").strip()
def block_of(body, anchor):
    """An anchor on a source file names a definition, so the record a quote is
    grepped out of is that class or function - not the 700-line module it sits in.
    A comma-separated anchor names more than one definition."""
    out = []
    for name in anchor.split(","):
        m = re.search(rf"^([ \t]*)(?:class|def) {re.escape(name)}\b", body, re.M) or \
            re.search(rf"^()({re.escape(name)})(?=[:= ])", body, re.M)   # a module-level constant
        if m is None:
            return None
        indent, lines = len(m.group(1)), body[m.start():].splitlines(True)
        end = len(lines)
        for i, line in enumerate(lines[1:], 1):
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                end = i
                break
        out.append("".join(lines[:end]))
    return "\n".join(out)
def source_of(cite):
    if cite.startswith("REF-"):
        rel, _, anchor = cite[4:].partition("#")
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            return None
        body = open(path).read()
        if anchor and rel.endswith(".py"):
            block = block_of(body, anchor)
            assert block is not None, f"{cite}: the anchor names no definition in {rel}"
            body = block
        return norm(body)
    return norm(records[cite]) if cite in records else None
ids = re.compile(r"`((?:F|E|R|T|X|REF)-[A-Za-z0-9][A-Za-z0-9./_#,-]*)`")
quotes = re.compile(r'"([^"]{12,})"')
checked = unresolved = 0
for n, line in enumerate(open("README.md"), 1):
    named = [i for i in ids.findall(line)]
    if not named:
        continue
    bodies = [(i, source_of(i)) for i in named]
    for quote in quotes.findall(line):
        want = norm(quote.replace("\\|", "|"))
        hits = [i for i, body in bodies if body and want in body]
        assert hits, f"README line {n}: {want[:70]!r} is in none of {named}"
        checked += 1
    unresolved += len([i for i, body in bodies if body is None])
assert unresolved == 0, "an id resolved to no record"
assert checked >= 30, checked
print("quotes grepped back into the record they name:", checked)
PY
check "every quote is verbatim in one of the records its line names, an anchor narrowed to its definition" "$?" "0"

echo "12. the printed commands, run as printed"
py <<'PY' > out/steps.txt
import re
rows = re.findall(r"^\| \d+ \| [^|]+ \| `([^`]+)` \| `([^`]+)` \|$",
                  open("README.md").read(), re.M)
assert len(rows) == 10, len(rows)
print("\n".join(f"{c}\t{last}" for c, last in rows))
PY
check "the run-steps table parses into ten commands and ten promised last lines" "$?" "0"
py <<'PY'
import re
# A label is a promise too. A step whose label says the pass closes must promise a
# completed: or escalated: line, and one that says it parks must promise a parked:
# line - the fourth column alone being right is what let a label say the opposite.
rows = re.findall(r"^\| \d+ \| ([^|]+) \| `[^`]+` \| `([^`]+)` \|$", open("README.md").read(), re.M)
assert len(rows) == 10, len(rows)
closes = re.compile(r"\b(close|closes|closing|complete|completes|finish|finishes)\b", re.I)
parks = re.compile(r"\b(park|parks|parked|parking)\b", re.I)
replays = re.compile(r"\b(re-fire|refire|replay|replays)\b", re.I)
escalates = re.compile(r"\b(escalate|escalates)\b", re.I)
bad = []
for label, last in rows:
    verb = last.split(":")[0].strip().lower()
    said_close, said_park = bool(closes.search(label)), bool(parks.search(label))
    if said_close and verb not in ("completed", "escalated"):
        bad.append((label.strip(), verb, "says it closes"))
    if said_park and verb != "parked":
        bad.append((label.strip(), verb, "says it parks"))
    if verb == "parked" and said_close:
        bad.append((label.strip(), verb, "parks but the label says it closes"))
    if escalates.search(label) and verb != "escalated":
        bad.append((label.strip(), verb, "says it escalates"))
    if verb.startswith("replay") and not replays.search(label):
        bad.append((label.strip(), verb, "prints a replay and the label does not say so"))
assert not bad, bad
print("run-step labels agreeing with their own promised last line:", len(rows))
PY
check "every run step's label says what its command actually prints" "$?" "0"
STEP=0
while IFS=$'\t' read -r cmd last; do
  STEP=$((STEP + 1))
  case "$cmd" in *test.sh*) continue;; esac      # step 1 is this file; see the gate below
  GOT=$( (cd "$ROOT" && eval "$cmd") 2>&1 | tail -1)
  if [ "$GOT" = "$last" ]; then ok "step $STEP prints its promised last line"
  else bad "step $STEP: expected '$last', got '$GOT'"; fi
done < out/steps.txt
py <<'PY'
import re, subprocess
flags = set(re.findall(r"^\s+(--[a-z-]+)", subprocess.run(
    ["python3", "run.py", "--help"], capture_output=True, text=True).stdout, re.M))
named = set(re.findall(r"(--[a-z][a-z-]+)", open("README.md").read()))
assert named <= flags, {"named in the README, absent from the runner": sorted(named - flags)}
assert {"--entry", "--ledger", "--gate", "--promote-regardless", "--verify-ledger"} <= flags, flags
PY
check "every flag the README names exists in the runner's own argument parser" "$?" "0"

echo "13. the interface, and what this example may not reach"
py <<'PY'
import os, re, sys
sys.path.insert(0, os.getcwd())
import harnesses
il, build = harnesses.improvement_loop()
five = set(il.interface_operations())
assert five == {"register_scorecard", "open_loop", "run_iteration", "evaluate_exit",
                "read_checkpoint"}, five
used = set(re.findall(r"\bdriver\.([a-z_]+)", open("run.py").read()))
assert used - {"next_fire", "name", "gate"} == five, used
assert il.no_in_place_edit_operation(), "the interface can name a target file"
assert il.candidate_carries_no_criterion(), "a candidate can carry a criterion"
assert il.ceiling_is_required(), "a loop can be declared with no ceiling"
assert harnesses.DRIVERS == ("dryrun", "second"), harnesses.DRIVERS
PY
check "the runner calls the five published operations and no sixth, and the design assertions hold" "$?" "0"
py <<'PY'
import glob, os, re
# No credential, endpoint or live adapter is reachable from this directory.
bad = []
for path in ["run.py", "harnesses.py", "test.sh"] + glob.glob("*.json") + glob.glob("*/*.json"):
    body = "".join(l for l in open(path) if "CITES-SCAN" not in l)
    body = body.replace("https://json-schema.org/draft/2020-12/schema", "")   # the dialect, not an endpoint
    for pattern in (r"https?://", r"\bAPI_KEY\b", r"\bTOKEN\b", r"adapters\.live\b", r'"live"'):   # CITES-SCAN
        if re.search(pattern, body):
            bad.append((path, pattern))
assert not bad, bad
PY
check "no endpoint, credential or live adapter is named anywhere in the example" "$?" "0"

echo "14. capabilities and standards, never products"
py <<'PY'
import glob, os, re
names = ["firecracker", "gvisor", "kata", "docker", "kubernetes", "podman", "temporal",  # CITES-SCAN
         "langfuse", "langchain", "langsmith", "litellm", "openai", "anthropic", "claude",  # CITES-SCAN
         "goose", "opa", "rego", "cedar", "jaeger", "datadog", "grafana", "prometheus",  # CITES-SCAN
         "redis", "postgres", "sqlite", "e2b", "modal", "daytona", "braintrust", "mlflow",  # CITES-SCAN
         "arize", "phoenix", "bedrock", "vertex", "azure", "aws", "gcp"]  # CITES-SCAN
pattern = re.compile(r"\b(" + "|".join(names) + r")\b", re.I)
files = sorted(set(glob.glob("*.*") + glob.glob("*/*.*") + glob.glob("out/**/*", recursive=True)))
files = [f for f in files if os.path.isfile(f) and not f.endswith(".pyc")]
hits = []
for path in files:
    for n, line in enumerate(open(path, errors="replace"), 1):
        if "CITES-SCAN" in line:
            continue
        for m in pattern.findall(line):
            hits.append((path, n, m))
assert not hits, hits[:5]
print(f"files scanned for {len(names)} product names, word-anchored: {len(files)}")
PY
check "no product name appears in any file of this example or in any artifact these runs wrote" "$?" "0"
py <<'PY'
import json, re
prov = json.load(open("provenance.json"))
floor = int(re.search(r"^FLOOR=(\d+)$", open("test.sh").read(), re.M).group(1))
assert prov["visible_checks_counted"] == floor, (prov["visible_checks_counted"], floor)
assert len(prov["measured"]) >= 12 and len(prov["claimed"]) >= 4
PY
check "provenance.visible_checks_counted is the floor this file gates on" "$?" "0"

echo
PROMISED=$(grep -oE '`passed [0-9]+, failed 0`' README.md | head -1 | tr -d '`')
if [ "$PROMISED" = "passed $((PASS + 1)), failed 0" ]; then
  ok "the README promises the count this run reached"
else
  bad "the README promises '$PROMISED', this run reached 'passed $((PASS + 1)), failed 0'"
fi
echo
[ "$FAIL" -eq 0 ] || { echo "passed $PASS, failed $FAIL"; exit 1; }
[ "$PASS" -ge "$FLOOR" ] || { echo "the visible check counted $PASS, below the floor of $FLOOR"; exit 1; }
echo "passed $PASS, failed $FAIL"
