#!/usr/bin/env bash
# The visible check for examples/run. Everything here is measured, not claimed.
# It prints `passed N, failed 0` with N counting checks that actually ran; a run
# that counts nothing is a defect, not a pass. So the gate at the bottom has two
# halves: no failure, and a floor under the number of checks that ran. A gutted
# copy of this file counts zero and is refused there rather than exiting 0
# (`F-a7-03` "A deterministic gate can be structurally green and mean nothing").
# FLOOR moves with provenance.json's visible_checks_counted.
#
# The deciding check for this example is held out and is not in this directory.
set -u
FLOOR=45
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
py()   { python3 - "$@"; }

rm -rf out && mkdir -p out

echo "1. four doors, one unit, one contained cell each"
for d in human event schedule external; do
  # the schedule document declares payload.fleet_size 50; this step compares the
  # four doors unit for unit, so the CLI override narrows that one door to 1.
  width=""; [ "$d" = "schedule" ] && width="--fleet 1"
  python3 run.py --entry "entries/$d.json" $width --ledger "out/$d.jsonl" > "out/$d.log" 2>&1
  check "$d exits 0" "$?" "0"
  grep -q "^completed:" "out/$d.log" && ok "$d reached completed" || bad "$d did not complete"
done
py <<'PY' > out/doors.log 2>&1
import json
doors = ("human", "event", "schedule", "external")
rows = {d: [json.loads(l) for l in open(f"out/{d}.jsonl")] for d in doors}
# per door: the stable prefix holds across every attempt of the unit
prefix = {d: {r["stable_prefix_digest"] for r in v if r["kind"] == "contract-sealed"} for d, v in rows.items()}
assert all(len(x) == 1 for x in prefix.values()), f"the stable prefix moved between attempts: {prefix}"
# across doors: the five declared contract entries are the same bytes. Only the
# intent summary the door carried, and the folded outcome, differ.
declared = {}
for d, v in rows.items():
    corr = next(iter({r["correlation_id"] for r in v}))
    manifest = json.load(open(f"out/units/{corr}/contract-manifest-1.json"))
    declared[d] = tuple(sorted((e["path"], e["digest"]) for e in manifest["entries"]
                               if e["path"] not in ("intent.json", "folded-outcome.json")))
assert len(set(declared.values())) == 1, f"the declared contract differs by door: {declared}"
assert len({next(iter(prefix[d])) for d in doors}) == 4, "the door intent never reached the contract"
cand = {d: [r["candidate_digest"] for r in v if r["kind"] == "attempt-recorded"][-1] for d, v in rows.items()}
assert len(set(cand.values())) == 1, f"four doors produced different subjects: {cand}"
actors = {d: {r["actor"] for r in v} for d, v in rows.items()}
assert all(len(a) == 1 for a in actors.values()) and len({next(iter(a)) for a in actors.values()}) == 4, actors
corr = {d: {r["correlation_id"] for r in v} for d, v in rows.items()}
assert all(len(c) == 1 for c in corr.values()) and len({next(iter(c)) for c in corr.values()}) == 4, corr
print("declared contract", declared["human"][0][1], "candidate", next(iter(set(cand.values()))))
PY
check "four doors, one declared contract and one candidate" "$?" "0"
grep -q "declared contract sha256:" out/doors.log && ok "four actors, four correlation ids, one subject" \
  || bad "door identity did not separate"

echo "2. the contract is hashed and ledgered before the cell starts"
py <<'PY' > out/contract.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl")]
seal = [r for r in rows if r["kind"] == "contract-sealed"]
admit = [r for r in rows if r["kind"] == "cell-admitted"]
assert seal and admit, "no contract or no cell"
assert seal[0]["seq"] < admit[0]["seq"], "a cell was admitted before any contract digest was ledgered"
for s, a in zip(seal, admit):
    assert s["seq"] < a["seq"] and s["contract_digest"] == a["contract_digest"], (s, a)
assert len({s["stable_prefix_digest"] for s in seal}) == 1, "the stable prefix moved between attempts"
assert len({s["contract_digest"] for s in seal}) == len(seal), "the folded outcome did not change the digest"
assert all(s["resident_tokens"] > 0 for s in seal), "no resident token count on the manifest"
fold = json.load(open("out/units/corr-run-human-0001/contract/folded-outcome.json"))
assert set(fold) == {"attempt", "cold", "previous_outcomes"}, set(fold)
assert all(set(p) == {"check_id", "outcome"} for p in fold["previous_outcomes"]), fold
assert json.load(open("out/units/corr-run-human-0001/contract-manifest-1.json"))["entries"], "empty manifest"
print("attempt 1 cold:", json.load(open("out/units/corr-run-human-0001/contract-manifest-1.json")))
PY
check "digest ledgered before admission, prefix stable, fold per attempt" "$?" "0"

echo "3. the visible checks do not decide, and the criterion never reaches the mount"
py <<'PY' > out/split.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl")]
first_visible = [r for r in rows if r["kind"] == "visible-checks"][0]
first_report = [r for r in rows if r["kind"] == "check-report"][0]
assert all(o["outcome"] == "pass" for o in first_visible["outcomes"]), first_visible
assert first_visible["decides"] is False, "a visible check claimed to decide"
assert first_report["outcome"] == "failed", "the deciding set agreed with the visible set on attempt 1"
print("visible green while the held-out set is red:", first_report["outcome"])
PY
check "attempt 1 is green on the visible set and red on the deciding set" "$?" "0"
if grep -rql "diamond" out/units/*/contract/ 2>/dev/null; then
  bad "the held-out fixture reached a contract mount"
else ok "the held-out fixture appears in no contract mount"; fi
if grep -rql "_d_unknown_tier" out/units/ out/human.log 2>/dev/null; then
  bad "a criterion body name reached the mount or the caller"
else ok "no criterion body name in the mount or the run output"; fi

echo "4. deciding checks can fail (deliberate breakage)"
python3 run.py --entry entries/human.json --widen-contract --attempts 1 --ledger out/widen.jsonl > out/widen.log 2>&1
check "a widened contract does not complete" "$?" "3"
py <<'PY' > out/widen2.log 2>&1
import json
rows = [json.loads(l) for l in open("out/widen.jsonl")]
rep = [r for r in rows if r["kind"] == "check-report"][-1]
assert rep["outcome"] == "failed", rep
PY
check "the widened seed is caught by a deciding check, not by a log line" "$?" "0"
grep -q "d-05            well_formedness  fail" out/widen.log \
  && ok "the contract-digest check is the one that failed" || bad "the wrong check failed"

echo "5. escalation is evidence-gated, once, and never a silent stop"
python3 run.py --entry entries/human.json --stuck --ledger out/stuck.jsonl > out/stuck.log 2>&1
check "an attempter that never learns does not complete" "$?" "3"
py <<'PY' > out/stuck2.log 2>&1
import json
rows = [json.loads(l) for l in open("out/stuck.jsonl")]
esc = [r for r in rows if r["kind"] == "escalated"]
att = [r for r in rows if r["kind"] == "attempt-recorded"]
park = [r for r in rows if r["kind"] == "approval-parked"]
assert len(esc) == 1, f"expected exactly one class step, got {len(esc)}"
assert esc[0]["failure_signature"] == "d-03", esc[0]
assert att[0]["model_class"] == att[1]["model_class"], "the class stepped before the evidence repeated"
assert att[2]["model_class"] != att[0]["model_class"], "the class never stepped"
assert att[0]["cold"] is True and att[1]["cold"] is False, "no cold attempt, or no folded attempt"
assert park and park[0]["state"] == "input-required", "the ceiling fired and nothing parked"
print("stepped", att[0]["model_class"], "->", att[2]["model_class"])
PY
check "one class step, gated on the same check failing twice, then parked" "$?" "0"
grep -q "^input-required:" out/stuck.log && ok "parked rather than stopped silently" || bad "stopped silently"
py <<'PY' > out/permit.log 2>&1
import json, subprocess
doc = json.load(open("units/fix-checkout-coupon-500s.json"))
def run(permitted, ledger):
    doc["escalation"]["class_steps_permitted"] = permitted
    json.dump(doc, open(f"out/unit-permit-{permitted}.json", "w"))
    subprocess.run(["python3", "run.py", "--entry", "entries/human.json", "--stuck",
                    "--unit", f"out/unit-permit-{permitted}.json", "--ledger", ledger],
                   capture_output=True, text=True)
    rows = [json.loads(l) for l in open(ledger)]
    return ([r for r in rows if r["kind"] == "escalated"],
            [r["model_class"] for r in rows if r["kind"] == "attempt-recorded"])
esc0, classes0 = run(0, "out/permit0.jsonl")
assert esc0 == [], f"a unit permitting no class step took {len(esc0)}"
assert len(set(classes0)) == 1, f"the class moved with no step permitted: {classes0}"
esc1, classes1 = run(1, "out/permit1.jsonl")
assert len(esc1) == 1 and len(set(classes1)) == 2, (esc1, classes1)
assert esc1[0]["trigger"] == doc["escalation"]["trigger"], "the trigger text was not read from the document"
assert esc1[0]["ladder"] == ["f-", "b-", "i-", "cli-"], esc1[0]["ladder"]
PY
check "class_steps_permitted 0 takes no class step, 1 takes exactly one" "$?" "0"
py <<'PY' > out/ladder.log 2>&1
import sys; sys.path.insert(0, ".")
import harnesses, run
gi, _ = harnesses.gateway("dryrun")
rungs = run.ladder(gi)
prices = [gi.ROUTING_TABLE[p]["unit_micros_per_1k"] for p in rungs]
assert prices == sorted(prices) and len(rungs) == len(gi.ROUTING_TABLE), (rungs, prices)
doc = {"escalation_class": "cli-"}
assert run.step_class(rungs, doc, "i-fast") == "cli-"
assert run.step_class(rungs, doc, "cli-") == "cli-", "it stepped past the top of the ladder"
assert run.step_class(rungs, doc, "z-made-up") == "z-made-up", "a class off the table raised"
print("ladder", rungs, prices)
PY
check "the ladder is the routing table ordered by price, read not transcribed" "$?" "0"

echo "6. a run in which nothing behavioural ran is inconclusive, not passed"
python3 run.py --entry entries/human.json --criteria wellformedness-only --attempts 1 \
  --ledger out/wf.jsonl > out/wf.log 2>&1
py <<'PY' > out/wf2.log 2>&1
import json
rep = [json.loads(l) for l in open("out/wf.jsonl") if json.loads(l)["kind"] == "check-report"][-1]
assert rep["behavioural_run"] == 0 and rep["checks_run"] > 0, rep
assert rep["outcome"] == "inconclusive", rep
PY
check "behavioural_run 0 reports inconclusive" "$?" "0"

echo "7. ceilings terminate the unit, not the platform"
python3 run.py --entry entries/human.json --budget-micros 1000 --ledger out/low.jsonl > out/low.log 2>&1
check "a ceiling below the plan floor exits 2" "$?" "2"
grep -q "budget-exhausted" out/low.log && ok "typed as budget-exhausted (402)" || bad "not typed"
grep -q "cell-admitted" out/low.jsonl && bad "a cell was admitted anyway" || ok "no cell admitted"
python3 run.py --entry entries/human.json --ceiling-seconds 0.02 --attempts 1 --ledger out/dl.jsonl > out/dl.log 2>&1
check "a wall-clock ceiling shorter than the turn does not complete" "$?" "3"
grep -q '"terminated_by": "budget-ceiling"' out/dl.jsonl \
  && ok "the boundary ended the turn, not the unit's goodwill" || bad "the ceiling was not enforced outside"
grep -q "^failed:" out/dl.log && ok "reported failed, with the stop reason named" || bad "no stop reason"

echo "8. containment is asserted from outside the unit, on every cell"
py <<'PY' > out/contain.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl") if json.loads(l)["kind"] == "cell-terminated"]
assert rows, "no cell was terminated"
assert all(r["observed_from"] == "host" for r in rows), "a unit reported on its own containment"
assert all(r["jail_mode"] == "0700" for r in rows), {r["jail_mode"] for r in rows}
assert all(r["owner_in_host_passwd"] is False for r in rows), "the unit's owner exists on the host"
assert all(r["secrets_seen_inside"] == 0 for r in rows), "a real secret was seen inside a unit"
assert all(r["egress_made"] == r["egress_blocked"] > 0 for r in rows), "egress was attempted and allowed"
print(len(rows), "cells, all asserted from the host")
PY
check "jail mode, owner, secrets and egress read by the host" "$?" "0"
py <<'PY' > out/decl.log 2>&1
import sys; sys.path.insert(0, ".")
import harnesses
ci, cls, _ = harnesses.containment("dryrun")
for doc, why in (({"profile": "small", "vcpus": 4}, "a machine-shaped field"),
                 ({"profile": "small", "egress": "allowlist", "egress_allowlist": []}, "an empty allowlist"),
                 ({"profile": "small", "credentials": "inline"}, "an inline credential")):
    try:
        ci.IsolationDeclaration.from_dict(doc)
        raise AssertionError(f"{why} was accepted")
    except ci.Problem as exc:
        assert exc.body["status"] == 422, exc.body
print("three declarations refused, all 422")
PY
check "a declaration that describes a machine is refused (422)" "$?" "0"

echo "9. the swap: a second isolation class, one call shape"
ADAPTER=second python3 run.py --entry entries/human.json --ledger out/second.jsonl > out/second.log 2>&1
check "the second containment technology exits 0" "$?" "0"
py <<'PY' > out/swap.log 2>&1
import json
one = [json.loads(l) for l in open("out/human.jsonl")]
two = [json.loads(l) for l in open("out/second.jsonl")]
mark = lambda rows: {r["containment_marker"] for r in rows if r["kind"] == "cell-terminated"}
cand = lambda rows: [r["candidate_digest"] for r in rows if r["kind"] == "attempt-recorded"]
assert mark(one) != mark(two), f"the same technology answered twice: {mark(one)}"
assert cand(one) == cand(two), "the swap moved the result, not just the technology"
kinds = {r["measure_cell"] for r in two if r["kind"] == "check-report"}
assert any("fresh-admission" in k for k in kinds), kinds
print("markers", mark(one), mark(two))
PY
check "the marker moved, the candidate digests did not" "$?" "0"
grep -q "isolation-operation-unsupported" out/second.log \
  && ok "an unserved lifecycle operation answers with a typed refusal" || bad "it degraded silently"

echo "10. what the unit reaches for, it reaches through the host"
py <<'PY' > out/caps.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl") if json.loads(l)["kind"] == "capability-call"]
tools = [r for r in rows if r["capability"] == "tool-access"][0]
skills = [r for r in rows if r["capability"] == "capability-packaging"][0]
model = [r for r in rows if r["capability"] == "model-access"][0]
assert tools["published"] > tools["declared_surface"], tools
assert len(tools["refused"]) == 2, tools
assert skills["tiers_loaded"] == ["resident", "body", "reference"], skills
assert model["model_class"].startswith(("f-", "i-", "b-", "cli-")), model
assert model["tokens_in"] > 0 and model["cost_micros"] > 0 and model["cost_status"], model
print(tools, skills, model)
PY
check "tool surface narrower than the catalogue, tiers loaded in order, class priced" "$?" "0"
grep -qE "vendor|openai|anthropic|litellm|firecracker|goose" out/human.log \
  && bad "a product or vendor name reached the caller" || ok "no product name in what the caller sees"
py <<'PY' > out/refuse.log 2>&1
import json
rows = [json.loads(l) for l in open("out/human.jsonl") if json.loads(l)["kind"] == "capability-call"]
tools = [r for r in rows if r["capability"] == "tool-access"][0]
assert sorted(tools["refused"]) == ["declared-surface", "read-only-verdict"], tools["refused"]
PY
check "both tool refusals are the declared rules, taken before dispatch" "$?" "0"

echo "11. fifty of them at once, declared by the door's own document"
python3 run.py --entry entries/schedule.json --ledger out/fleet.jsonl > out/fleet.log 2>&1
check "a fleet of fifty exits 0" "$?" "0"
grep -q "FLEET  50 units, 50 completed" out/fleet.log && ok "fifty units, fifty completed" || bad "not fifty"
py <<'PY' > out/fanout.log 2>&1
import json
assert json.load(open("entries/schedule.json"))["payload"]["fleet_size"] == 50
assert json.load(open("entries/human.json"))["payload"]["fleet_size"] == 1
PY
check "the fan-out width is declared in the envelope, not on the command line" "$?" "0"
python3 run.py --entry entries/schedule.json --fleet 4 --ledger out/fleet4.jsonl > out/fleet4.log 2>&1
grep -q "FLEET  4 units" out/fleet4.log && ok "--fleet overrides the declared width" \
  || bad "the override did not apply"
py <<'PY' > out/fleet2.log 2>&1
import json
rows = [json.loads(l) for l in open("out/fleet.jsonl")]
admits = [r for r in rows if r["kind"] == "cell-admitted"]
term = [r for r in rows if r["kind"] == "cell-terminated"]
assert len({r["correlation_id"] for r in rows}) == 50, "fifty units did not carry fifty correlation ids"
measure = [r for r in rows if r["kind"] == "check-report"]
assert len({r["unit_id"] for r in admits}) == len(admits) == 100, len(admits)
assert len({r["unit_id"] for r in measure}) == len(measure) == 100, len(measure)
assert len({r["unit_id"] for r in admits} | {r["unit_id"] for r in measure}) == 200, "cells were reused"
assert all(r["checks_ran"] == "host-side" for r in measure), "the check-report did not say where it ran"
assert all(r.get("correlation_id") and r.get("run_id") for r in rows), "a record with no correlation"
assert all(r["secrets_seen_inside"] == 0 and r["jail_mode"] == "0700" for r in term), "a fleet cell leaked"
print(len(rows), "records,", len(admits), "cells")
PY
check "50 units, 100 attempt cells, 100 measure cells, 200 distinct cell ids" "$?" "0"
python3 run.py --entry entries/schedule.json --fleet 8 --share-run-id --attempts 1 \
  --ledger out/share.jsonl > out/share.log 2>&1
grep -q "rejected" out/share.log && ok "units that reuse one run id are refused at admission" \
  || bad "the run-level admission budget did not fire"
grep -q "urn:agentic:problem:budget-exhaust" out/share.log && ok "that refusal is typed, not a crash" \
  || bad "the refusal was not typed"

echo "12. the ledger"
python3 run.py --verify-ledger --ledger out/human.jsonl > out/verify.log 2>&1
check "the chain verifies" "$?" "0"
sed '5s/"cost_micros": [0-9]*/"cost_micros": 1/' out/human.jsonl > out/tampered.jsonl
python3 run.py --verify-ledger --ledger out/tampered.jsonl > out/tamper.log 2>&1
check "a one-character edit is detected" "$?" "2"

echo "13. a malformed envelope"
py <<'PY'
import json
e = json.load(open("entries/human.json"))
del e["budget"]; e["kind"] = "telepathy"
json.dump(e, open("out/malformed.json", "w"))
PY
python3 run.py --entry out/malformed.json --ledger out/bad.jsonl > out/bad.log 2>&1
check "a malformed envelope exits 2" "$?" "2"
grep -q "document-invalid" out/bad.log && ok "typed as document-invalid (422)" || bad "not typed"
grep -q "missing required property 'budget'" out/bad.log && ok "names the missing field" || bad "field not named"
[ -f out/bad.jsonl ] && bad "an invalid envelope wrote to a ledger" || ok "nothing written for an invalid envelope"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge "$FLOOR" ] || { echo "the visible check counted $PASS, below the floor of $FLOOR"; exit 1; }
