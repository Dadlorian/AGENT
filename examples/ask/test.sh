#!/usr/bin/env bash
# The visible check for examples/ask. Everything here is measured, not claimed.
# It prints `passed N, failed 0` with N counting checks that actually ran, so
# the gate at the bottom has two halves: no failure, and a floor under the
# number of checks that ran. A gutted copy of this file counts zero and is
# refused there rather than exiting 0 (`F-a7-03` "A deterministic gate can be
# structurally green and mean nothing"). FLOOR moves with provenance.json's
# visible_checks_counted.
#
# Every extension point in README section 6 is proved here by a differential
# run: the same door twice, one declared value changed, the two records
# asserted different in the named way. A green run at the default value proves
# the default path and nothing else.
#
# The deciding check for this example is held out and is not in this directory.
set -u
FLOOR=63
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }
py()   { python3 - "$@"; }

rm -rf out && mkdir -p out

echo "1. four doors, one job, one envelope shape"
for d in human event schedule external; do
  python3 run.py --entry "entries/$d.json" --ledger "out/$d.jsonl" --json > "out/$d.json" 2> "out/$d.log"
  check "$d exits 0" "$?" "0"
done
py <<'PY' > out/doors.log 2>&1
import json
doors = ("human", "event", "schedule", "external")
rows = {d: json.load(open(f"out/{d}.json"))[0] for d in doors}
assert all(r["round_trip"] == "exact" for r in rows.values()), \
    {d: r["round_trip"] for d, r in rows.items()}
assert all(r["kind"] == "entry-admitted" for r in rows.values())
print("round_trip exact at", len(rows), "doors")
jobs = {r["job_digest"] for r in rows.values()}
manifests = {r["plan"]["manifest_digest"] for r in rows.values()}
entries = {r["entry_id"] for r in rows.values()}
corr = {r["correlation_id"] for r in rows.values()}
actors = {r["identity"]["executing_identity"] for r in rows.values()}
keys = {r["idempotency_key"] for r in rows.values()}
assert len(jobs) == 1 and len(manifests) == 1, (jobs, manifests)
assert len(entries) == len(corr) == len(actors) == len(keys) == 4, (entries, corr, actors, keys)
print(f"one job {len(jobs)} manifest {len(manifests)} entries {len(entries)} "
      f"correlations {len(corr)} executing {len(actors)} keys {len(keys)}")
declared = json.load(open("admission.json"))["lifecycle"]
states = {r["state"] for r in rows.values()}
assert states == {declared["initial"]}, (states, declared["initial"])
assert all(r["units_started"] == 0 for r in rows.values()), "intake started work"
assert all(set(r["receipt"]) <= {"entry_id", "correlation_id", "job_digest", "accepted",
                                 "duplicate_of"} for r in rows.values()), "a result rode back"
print("state submitted, units started 0, no result member on any acknowledgement")
PY
check "four doors, one job, four submissions" "$?" "0"
grep -q "round_trip exact at 4 doors" out/doors.log && ok "each door reproduces its entry document exactly" \
  || bad "a door did not reproduce its document"
grep -q "one job 1 manifest 1 entries 4 correlations 4 executing 4 keys 4" out/doors.log \
  && ok "one job digest and one resolved manifest, four of everything a door owns" \
  || bad "the doors did not normalise onto one job"
grep -q "state submitted, units started 0" out/doors.log \
  && ok "submitted, nothing executed, no result in the acknowledgement" || bad "intake returned a result"
py <<'PY'
import json, os, sys
sys.path.insert(0, ".")
import harnesses
ref = harnesses.reference()
schema = json.load(open(os.path.join("..", "end-to-end", "schemas", "entry.schema.json")))
bad = {d: ref.validate(json.load(open(f"entries/{d}.json")), schema)
       for d in ("human", "event", "schedule", "external")}
assert not any(bad.values()), bad
print("four entry documents, 0 errors, one published schema")
PY
check "the four entry documents validate against the published schema" "$?" "0"
py <<'PY'
import json
rows = [json.loads(l) for d in ("human", "event", "schedule", "external")
        for l in open(f"out/{d}.jsonl")]
need = ("run_id", "correlation_id", "attested_subject", "idempotency_key", "entry_id", "door")
missing = [(r.get("door"), n) for r in rows for n in need if not r.get(n)]
assert not missing, missing
blank = [r for r in rows if not r["identity"]["executing_identity"]
         or not r["identity"]["triggering_identity"]]
assert not blank, "an action recorded with an identity field blank"
print(len(rows), "records, every one correlated and named")
PY
check "every record names the run, the correlation and both identities" "$?" "0"

echo "2. what the boundary sets, and the producer cannot"
py <<'PY'
import json
producers = {k: v for k, v in json.load(open("producers.json")).items() if not k.startswith("_")}
forbidden = ("idempotency_key", "correlation_id", "run_id", "budget", "ceiling_micros")
found = [(d, f) for d, p in producers.items() for f in forbidden if f in json.dumps(p["body"])]
assert not found, found
print("no producer body carries a key, a correlation or a ceiling")
PY
check "no producer supplies a key, a correlation id or a ceiling" "$?" "0"
py <<'PY'
import json, sys
sys.path.insert(0, ".")
import doors
declaration = json.load(open("admission.json"))
producers = doors.load_producers()
derived = {d: doors.derive_key(declaration, p["format"], p["body"],
                               p["transport"]["attested_subject"]) for d, p in producers.items()}
declared = {d: json.load(open(f"entries/{d}.json"))["idempotency_key"] for d in derived}
assert derived == declared, (derived, declared)
print("derived == declared at", len(derived), "doors")
PY
check "the key the boundary derives is the key the document declares" "$?" "0"
py <<'PY'
import json
envelopes = {d: json.load(open(f"entries/{d}.json")) for d in ("human", "event", "schedule", "external")}
text = json.dumps(envelopes)
assert "user:root" not in text, "a producer's claim about its own identity reached an envelope"
assert envelopes["event"]["actor"]["subject"] == "service:alerting"
assert envelopes["external"]["actor"]["subject"] == "agent:partner-sre-bot"
print("claimed_submitter and submittedBy dropped; the attested subject stands")
PY
check "an identity a producer claimed for itself never reaches the envelope" "$?" "0"
py <<'PY'
import json
rows = {d: json.load(open(f"out/{d}.json"))[0] for d in ("human", "event", "schedule", "external")}
dropped = {d: r["dropped"] for d, r in rows.items()}
assert dropped["human"] == ["cwd", "tty"], dropped["human"]
assert "claimed_submitter" in dropped["event"] and "datacontenttype" in dropped["event"], dropped["event"]
assert "recurrence" in dropped["schedule"] and "received_at" in dropped["schedule"], dropped["schedule"]
assert "priority" in dropped["external"] and "submittedBy" in dropped["external"], dropped["external"]
print("dropped:", json.dumps(dropped))
PY
check "every producer-specific attribute is named as dropped, not carried" "$?" "0"
py <<'PY'
import json, re
# The other direction of the same claim: the README says every dropped member is
# named there, and a table written by hand is true only in the direction its
# author checked. The dropped lists are computed by doors.dropped_by, so the
# table is held to them rather than the other way round.
rows = {d: json.load(open(f"out/{d}.json"))[0] for d in ("human", "event", "schedule", "external")}
readme = open("README.md").read()
missing = sorted({m for r in rows.values() for m in r["dropped"]
                  if not re.search(rf"`{re.escape(m)}`", readme)})
assert not missing, missing
print(sum(len(r["dropped"]) for r in rows.values()), "dropped members, every one of them named in README")
PY
check "every member of every dropped list is named in the README, not only the other way round" "$?" "0"
py <<'PY'
import json
d = json.load(open("admission.json"))
d.pop("parent_correlation_fields")        # no producer's own correlation is adopted as a parent
json.dump(d, open("out/noparent.json", "w"), indent=2)
PY
python3 run.py --door external --admission out/noparent.json --ledger out/noparent.jsonl --json \
  > out/noparent.json.out 2>&1
check "the external door with no parent field declared exits 0" "$?" "0"
py <<'PY'
import json
named = json.load(open("out/external.json"))[0]
bare = json.load(open("out/noparent.json.out"))[0]
context = json.load(open("producers.json"))["external"]["body"]["contextId"]
envelope = json.load(open("entries/external.json"))["correlation"]
assert named["parent_correlation_id"] == context, named["parent_correlation_id"]
assert envelope["parent_correlation_id"] == context and envelope["depth"] == 1, envelope
assert named["correlation_id"] != context, "the partner's context was adopted as our correlation"
assert named["correlation_depth"] == 1, named["correlation_depth"]
assert bare["parent_correlation_id"] is None, bare["parent_correlation_id"]
assert bare["correlation_depth"] == 0, bare["correlation_depth"]
assert bare["correlation_id"] == named["correlation_id"], "the parent moved this run's correlation"
print("DIFFERENTIAL parent_correlation_fields: contextId named -> parent set, depth 1; "
      "no row -> no parent, depth 0")
PY
check "DIFFERENTIAL parent_correlation_fields: depth follows from having a parent, not from which door" "$?" "0"
py <<'PY'
import json
declared = json.load(open("admission.json"))["budget"]
seen = {json.dumps(json.load(open(f"entries/{d}.json"))["budget"], sort_keys=True)
        for d in ("human", "event", "schedule", "external")}
assert seen == {json.dumps(declared, sort_keys=True)}, seen
print("one stamped ceiling at four doors")
PY
check "the ceiling on every envelope is the one the declaration stamps" "$?" "0"

echo "3. replay, conflict, and the schedule's occurrence"
python3 run.py --door event --again --ledger out/replay.jsonl --json > out/replay.json 2>&1
py <<'PY'
import json
first, second = json.load(open("out/replay.json"))
assert first["claim"] == "fresh" and second["claim"] == "duplicate", (first["claim"], second["claim"])
assert second["replay"] is True and second["receipt"] == first["receipt"], second["receipt"]
assert second["entries_recorded"] == 1, second["entries_recorded"]
assert second["correlation_id"] == first["correlation_id"], "the replay lost the original correlation"
print("replay: duplicate, stored receipt returned, 1 entry recorded")
PY
check "a replay returns the stored receipt and records nothing new" "$?" "0"
python3 run.py --door event --again-window 999 --ledger out/conflict.jsonl > out/conflict.log 2>&1
check "the same key under a different job exits 2" "$?" "2"
py <<'PY'
import json
rows = [json.loads(l) for l in open("out/conflict.jsonl")]
refusal = [r for r in rows if r["kind"] == "entry-refused"][0]
assert refusal["problem"]["type"] == "urn:agentic:problem:idempotency-conflict", refusal["problem"]
assert refusal["problem"]["status"] == 409 and refusal["entries_recorded"] == 1
print("409 idempotency-conflict, 1 entry recorded, second job never admitted")
PY
check "it is refused as a typed 409 and nothing is admitted" "$?" "0"
python3 run.py --door schedule --again-received-at 2026-09-04T06:00:00Z \
  --ledger out/backfill.jsonl --json > out/backfill.json 2>&1
py <<'PY'
import json
first, second = json.load(open("out/backfill.json"))
assert first["idempotency_key"] == second["idempotency_key"], "the wall clock reached the key"
assert second["claim"] == "duplicate" and second["entries_recorded"] == 1
print("same occurrence, later wall clock:", second["claim"])
PY
check "a catch-up delivery of the same occurrence is a duplicate" "$?" "0"
py <<'PY'
import json
d = json.load(open("admission.json"))
d["key_fields"]["schedule-occurrence"] = ["schedule", "occurrence", "received_at"]
json.dump(d, open("out/wallclock.json", "w"), indent=2)
PY
python3 run.py --door schedule --again-received-at 2026-09-04T06:00:00Z \
  --admission out/wallclock.json --ledger out/wallclock.jsonl --json > out/wallclock.json.out 2>&1
py <<'PY'
import json
base = json.load(open("out/backfill.json"))
wall = json.load(open("out/wallclock.json.out"))
assert base[0]["idempotency_key"] == base[1]["idempotency_key"], "declared derivation moved"
assert wall[0]["idempotency_key"] != wall[1]["idempotency_key"], "the declaration was not read"
assert [r["claim"] for r in base] == ["fresh", "duplicate"], [r["claim"] for r in base]
assert [r["claim"] for r in wall] == ["fresh", "fresh"], [r["claim"] for r in wall]
assert wall[1]["entries_recorded"] == 2 and base[1]["entries_recorded"] == 1
print("key_fields read at derivation: 1 key and 1 entry, against 2 and 2")
PY
check "DIFFERENTIAL key_fields: naming the wall clock splits one occurrence into two entries" "$?" "0"
python3 run.py --door schedule --occurrence 2026-09-05T02:00:00Z --ledger out/next.jsonl --json \
  > out/next.json 2>&1
py <<'PY'
import json
today = json.load(open("out/backfill.json"))[0]["idempotency_key"]
tomorrow = json.load(open("out/next.json"))[0]["idempotency_key"]
assert today != tomorrow, "two occurrences of one schedule derived one key"
print("occurrence in the key:", today, "vs", tomorrow)
PY
check "the next occurrence of the same schedule derives a different key" "$?" "0"

echo "4. redelivery under contention"
RACE_DELAY_S=0.02 python3 run.py --door event --redeliveries 8 \
  --ledger out/fold.jsonl > out/fold.log 2>&1
RACE_DELAY_S=0.02 python3 run.py --door event --redeliveries 8 --idempotency second \
  --ledger out/lease.jsonl > out/lease.log 2>&1
grep -q "8 concurrent, 8 claims answered fresh" out/fold.log \
  && ok "without a lease, 8 concurrent redeliveries all claim the key" \
  || bad "the fold binding did not show the race ($(grep redeliveries out/fold.log))"
grep -q "8 concurrent, 1 claims answered fresh" out/lease.log \
  && ok "DIFFERENTIAL idempotency binding: with a lease, exactly 1 of the 8 claims it" \
  || bad "the lease binding did not arbitrate ($(grep redeliveries out/lease.log))"
py <<'PY'
import json
fold = [json.loads(l) for l in open("out/fold.jsonl")][-1]["bindings"]["idempotency"]
lease = [json.loads(l) for l in open("out/lease.jsonl")][-1]["bindings"]["idempotency"]
assert fold["supports_in_flight"] is False and lease["supports_in_flight"] is True
assert fold["unit_of_conditionality"] != lease["unit_of_conditionality"], fold
print(fold["unit_of_conditionality"], "|", lease["unit_of_conditionality"])
PY
check "the two bindings declare different units of conditionality" "$?" "0"

echo "5. one document, one dialect, two validators"
python3 run.py --door schedule --occurrence "tuesday night" --ledger out/bad.jsonl > out/bad.log 2>&1
check "an envelope that fails the schema exits 2" "$?" "2"
py <<'PY'
import json
row = [json.loads(l) for l in open("out/bad.jsonl")][0]
problem = row["problem"]
assert problem["type"] == "urn:agentic:problem:document-invalid" and problem["status"] == 422
cause = problem["causes"][0]
assert cause["instance_location"] == "/occurred_at", cause
assert cause["keyword_location"].startswith("#/properties/occurred_at"), cause
assert row["validation"]["validators_agree"] is True, row["validation"]
assert row["entries_recorded"] == 0 and row["state"] == "rejected-before-admission"
print("422 at", cause["instance_location"], "keyword", cause["keyword_location"])
PY
check "the refusal locates the violation and both validators rejected it" "$?" "0"
[ -s out/bad.jsonl ] && ok "the refusal is audited" || bad "a refusal left no record"
py <<'PY'
import json
schema = json.load(open("../end-to-end/schemas/entry.schema.json"))
schema["$schema"] = "https://json-schema.org/draft-07/schema#"
json.dump(schema, open("out/other-dialect.schema.json", "w"), indent=2)
d = json.load(open("admission.json"))
d["schema_ref"] = "examples/ask/out/other-dialect.schema.json"
json.dump(d, open("out/dialect.json", "w"), indent=2)
PY
python3 run.py --door human --admission out/dialect.json --ledger out/dialect.jsonl > out/dialect.log 2>&1
check "a schema declaring another dialect exits 2" "$?" "2"
py <<'PY'
import json
row = [json.loads(l) for l in open("out/dialect.jsonl")][0]
assert row["problem"]["type"].endswith("dialect-unsupported"), row["problem"]["type"]
assert row["refused_at"] == "validate" and row["entries_recorded"] == 0
assert row["problem"]["declared_dialect"] == "https://json-schema.org/draft-07/schema#"
print("DIFFERENTIAL schema_ref/dialect:", row["problem"]["status"], row["problem"]["type"])
PY
check "DIFFERENTIAL dialect: a valid envelope is refused before any instance is checked" "$?" "0"
python3 run.py --door external --validation second --ledger out/v2.jsonl --json > out/v2.json 2>&1
py <<'PY'
import json
one = json.load(open("out/external.json"))[0]
two = json.load(open("out/v2.json"))[0]
assert one["bindings"]["validation"]["execution_model"] != two["bindings"]["validation"]["execution_model"]
assert one["bindings"]["validation"]["schema_reads"] != two["bindings"]["validation"]["schema_reads"]
assert one["validation"]["dialect"] == two["validation"]["dialect"]
assert one["job_digest"] == two["job_digest"] and one["entry_id"] == two["entry_id"]
print("DIFFERENTIAL validation binding:", one["bindings"]["validation"], two["bindings"]["validation"])
PY
check "DIFFERENTIAL validation binding: two execution models, one outcome" "$?" "0"

echo "6. the identity behind the door"
py <<'PY'
import json
rows = {d: json.load(open(f"out/{d}.json"))[0]["identity"]
        for d in ("human", "event", "schedule", "external")}
hops = {d: r["delegation_depth"] for d, r in rows.items()}
assert hops == {"human": 1, "event": 2, "schedule": 2, "external": 3}, hops
assert all(r["triggering_identity"] == "user:corey" for r in rows.values()), rows
assert rows["external"]["executing_identity"] == "agent:partner-sre-bot"
assert all(r["issued_hops"][0] == r["triggering_identity"] for r in rows.values())
print("hops", json.dumps(hops), "triggering identity present at every door")
PY
check "each door names an executing and a triggering identity, and its chain" "$?" "0"
py <<'PY'
import json
d = json.load(open("admission.json"))
d["identity"]["max_delegation_depth"] = 2
json.dump(d, open("out/depth2.json", "w"), indent=2)
PY
python3 run.py --door external --admission out/depth2.json --ledger out/depth2.jsonl > out/depth2.log 2>&1
check "a chain past the declared bound exits 2" "$?" "2"
py <<'PY'
import json
tight = [json.loads(l) for l in open("out/depth2.jsonl")][0]
loose = json.load(open("out/external.json"))[0]
assert tight["problem"]["rule_id"] == "delegation-depth-bound", tight["problem"]
assert tight["problem"]["status"] == 403 and tight["entries_recorded"] == 0
assert loose["kind"] == "entry-admitted" and loose["identity"]["delegation_depth"] == 3
print("DIFFERENTIAL max_delegation_depth: 4 admits 3 hops, 2 refuses them")
PY
check "DIFFERENTIAL max_delegation_depth: the same door admitted at 4, refused at 2" "$?" "0"
python3 run.py --door external --identity second --ledger out/i2.jsonl --json > out/i2.json 2>&1
py <<'PY'
import json
one = json.load(open("out/external.json"))[0]
two = json.load(open("out/i2.json"))[0]
assert one["bindings"]["identity"]["authority_calls"] == 3, one["bindings"]["identity"]
assert two["bindings"]["identity"]["authority_calls"] == 0, two["bindings"]["identity"]
assert one["identity"]["issued_hops"] == two["identity"]["issued_hops"]
assert one["identity"]["scope"] == two["identity"]["scope"]
print("DIFFERENTIAL identity binding: authority calls 3 against 0, same chain issued")
PY
check "DIFFERENTIAL identity binding: one issuer calls an authority, the other never does" "$?" "0"
py <<'PY'
import json
# Within one chain, hop against consecutive hop - not one door against another,
# which compares two chains and can be green while nothing narrows at all
# (X-litmus-c-020: per-invocation narrowing, not collapsed at the first hop).
declared = json.load(open("admission.json"))["identity"]
audience = json.load(open("admission.json"))["audience"]
rows = {d: json.load(open(f"out/{d}.json"))[0]["identity"]
        for d in ("human", "event", "schedule", "external")}
for door, row in rows.items():
    issued = row["issued"]
    assert len(issued) == row["delegation_depth"], (door, len(issued))
    assert [h["actor"] for h in issued] == row["issued_hops"], door
    assert set(issued[0]["scope"]) == set(declared["scopes"]), (door, issued[0]["scope"])
    for near, far in zip(issued, issued[1:]):
        assert set(far["scope"]) < set(near["scope"]), (door, near["scope"], far["scope"])
        assert far["lifetime_s"] < near["lifetime_s"], (door, near, far)
        assert far["seconds_left"] < near["seconds_left"], (door, near, far)
    assert set(row["scope"]) == set(issued[-1]["scope"]), (door, row["scope"])
    assert row["audience"] == audience, (door, row["audience"])
ext = rows["external"]["issued"]
print("per-hop scope", " -> ".join(str(len(h["scope"])) for h in ext),
      "seconds", " -> ".join(str(h["seconds_left"]) for h in ext),
      "over", rows["external"]["delegation_depth"], "hops of one chain")
PY
check "scope narrows and lifetime shortens between consecutive hops of one chain" "$?" "0"
py <<'PY'
import json
d = json.load(open("admission.json"))
d["identity"]["scopes"] = d["identity"]["scopes"][-2:]      # two rungs, three hops
json.dump(d, open("out/short-ladder.json", "w"), indent=2)
PY
python3 run.py --door external --admission out/short-ladder.json --ledger out/short-ladder.jsonl \
  > out/short-ladder.log 2>&1
check "a chain longer than the declared scope ladder exits 2" "$?" "2"
py <<'PY'
import json
short = [json.loads(l) for l in open("out/short-ladder.jsonl")][0]
full = json.load(open("out/external.json"))[0]
assert short["problem"]["rule_id"] == "scope-ladder-shorter-than-chain", short["problem"]
assert short["problem"]["status"] == 403 and short["entries_recorded"] == 0
assert short["refused_at"] == "identity" and "identity" not in short
assert full["identity"]["ladder_rungs"] == 4 and full["identity"]["delegation_depth"] == 3
assert len({tuple(h["scope"]) for h in full["identity"]["issued"]}) == 3, "two hops share a rung"
print("DIFFERENTIAL scope ladder: 4 rungs issue 3 distinct hops, 2 rungs refuse the chain")
PY
check "DIFFERENTIAL identity.scopes: a hop past the ladder is refused, never handed the rung before it" "$?" "0"

echo "7. the admission decision, before anything is spent"
py <<'PY'
import json
row = json.load(open("out/human.json"))[0]["policy"]
assert row["effect"] == "allow" and row["rule_id"] == "allow-entry-in-tenant", row
assert row["decision_point"] == "admission.entry" and row["policy_version"].startswith("sha256:")
print("allow", row["rule_id"], "at", row["decision_point"], "pinned to", row["policy_version"])
PY
check "an allow names the rule that fired and the version it was pinned to" "$?" "0"
python3 run.py --door human --resource-tenant tenant-other --ledger out/tenant.jsonl > out/tenant.log 2>&1
check "a resource in another tenant exits 2" "$?" "2"
py <<'PY'
import json
row = [json.loads(l) for l in open("out/tenant.jsonl")][0]
assert row["problem"]["rule_id"] == "deny-cross-tenant-resource", row["problem"]
assert row["problem"]["spend_delta_micros"] == 0 and row["entries_recorded"] == 0
assert row["refused_at"] == "policy"
print("DIFFERENTIAL tenant: 403 before any spend, nothing admitted")
PY
check "DIFFERENTIAL tenant: the deny is typed, spends nothing and admits nothing" "$?" "0"
py <<'PY'
import json
d = json.load(open("admission.json"))
d["policy"]["action"] = "delete-everything"     # an action nobody registered
json.dump(d, open("out/action.json", "w"), indent=2)
d["policy"]["actions_permitted"] = ["submit", "delete-everything"]   # now somebody did
json.dump(d, open("out/vocabulary.json", "w"), indent=2)
PY
python3 run.py --door human --admission out/action.json --ledger out/action.jsonl > out/action.log 2>&1
check "an action outside the declared vocabulary exits 2" "$?" "2"
python3 run.py --door human --admission out/vocabulary.json --ledger out/vocabulary.jsonl --json \
  > out/vocabulary.json.out 2>&1
check "the same action inside a widened vocabulary exits 0" "$?" "0"
py <<'PY'
import json
outside = [json.loads(l) for l in open("out/action.jsonl")][0]
widened = json.load(open("out/vocabulary.json.out"))[0]
inside = json.load(open("out/human.json"))[0]
assert outside["problem"]["rule_id"] == "deny-entry-action-outside-vocabulary", outside["problem"]
assert outside["problem"]["status"] == 403 and outside["problem"]["spend_delta_micros"] == 0
assert outside["refused_at"] == "policy" and outside["entries_recorded"] == 0
assert inside["policy"]["effect"] == "allow" and inside["policy"]["rule_id"] == "allow-entry-in-tenant"
# Both halves are read at the decision: the same action denies under the declared
# vocabulary and allows under a widened one, and because the vocabulary is composed
# into the rule set the decision is pinned to, widening it moves the pin as well.
assert widened["policy"]["effect"] == "allow" and widened["policy"]["rule_id"] == "allow-entry-in-tenant"
assert outside["problem"]["policy_version"].startswith(inside["policy"]["policy_version"]), "the pin moved"
assert widened["policy"]["policy_version"] != inside["policy"]["policy_version"], "the pin did not move"
print("DIFFERENTIAL policy.action: submit allows, an unregistered action denies 403 before any spend, "
      "and the same action allows once the vocabulary names it")
PY
check "DIFFERENTIAL policy.action: the declared vocabulary decides, and an action nobody registered is refused" "$?" "0"
python3 run.py --door human --policy second --ledger out/p2.jsonl --json > out/p2.json 2>&1
py <<'PY'
import json
one = json.load(open("out/human.json"))[0]
two = json.load(open("out/p2.json"))[0]
assert one["bindings"]["policy"]["entity"] != two["bindings"]["policy"]["entity"]
assert (one["policy"]["effect"], one["policy"]["rule_id"]) == \
       (two["policy"]["effect"], two["policy"]["rule_id"]), (one["policy"], two["policy"])
assert one["policy"]["policy_version"] == two["policy"]["policy_version"]
print("DIFFERENTIAL policy binding: two engines, one effect and one rule id")
PY
check "DIFFERENTIAL policy binding: two engines answer the same question alike" "$?" "0"

echo "8. the ceiling the platform stamped"
py <<'PY'
import json
d = json.load(open("admission.json"))
d["budget"]["ceiling_micros"] = 1000
json.dump(d, open("out/poor.json", "w"), indent=2)
PY
python3 run.py --door human --admission out/poor.json --ledger out/poor.jsonl > out/poor.log 2>&1
check "a ceiling below the plan floor exits 2" "$?" "2"
py <<'PY'
import json
poor = [json.loads(l) for l in open("out/poor.jsonl")][0]
rich = json.load(open("out/human.json"))[0]
assert poor["problem"]["type"].endswith("budget-exhausted") and poor["problem"]["status"] == 402
assert poor["problem"]["stop_reason"] == "ceiling_below_plan_floor"
assert poor["refused_at"] == "budget" and poor["entries_recorded"] == 0
assert rich["plan"]["headroom_micros"] > 0 and rich["kind"] == "entry-admitted"
print("DIFFERENTIAL ceiling: 1500000 admits, 1000 refuses at 402 before the claim")
PY
check "DIFFERENTIAL ceiling: refused before a claim was taken and before anything was recorded" "$?" "0"

echo "9. producers, and the execution model behind a door"
python3 run.py --door human --format smtp-mail --ledger out/unmapped.jsonl > out/unmapped.log 2>&1
check "an unregistered producer format exits 2" "$?" "2"
py <<'PY'
import json
row = [json.loads(l) for l in open("out/unmapped.jsonl")][0]
assert row["problem"]["rule_id"] == "refuse-unmapped-producer", row["problem"]
assert row["problem"]["status"] == 403 and row["entries_recorded"] == 0
assert set(row["problem"]["registered"]) == set(json.load(open("admission.json"))["producers"])
assert row["attested_subject"] == "user:corey", "the refusal did not name who was at the door"
print("DIFFERENTIAL producers: the registered four admit, a fifth is refused")
PY
check "DIFFERENTIAL producers: registration is what admits, and the refusal names the door" "$?" "0"
python3 run.py --all-doors --intake detached --ledger out/detached.jsonl --json > out/detached.json 2>&1
py <<'PY'
import json
attached = {d: json.load(open(f"out/{d}.json"))[0] for d in ("human", "event", "schedule", "external")}
detached = {r["door"]: r for r in json.load(open("out/detached.json"))}
for door, row in detached.items():
    assert row["ack_delivery"] == "recorded-for-later-collection", row["ack_delivery"]
    assert row["producer_present_at_ack"] is False
    assert attached[door]["ack_delivery"] == "in-request"
    assert attached[door]["producer_present_at_ack"] is True
    assert row["job_digest"] == attached[door]["job_digest"], door
    assert row["identity"]["delegation_depth"] == attached[door]["identity"]["delegation_depth"] + 1
# The extra hop is issued the next rung down rather than a repeat of the last one,
# so the deepest rung of the declared ladder is reached by a run rather than only
# written in the declaration.
deepest = json.load(open("admission.json"))["identity"]
outer = detached["external"]["identity"]["issued"]
assert len(outer) == 4 and [h["lifetime_s"] for h in outer] == deepest["hop_lifetime_s"], outer
assert [len(h["scope"]) for h in outer] == [4, 3, 2, 1], outer
print("DIFFERENTIAL intake binding: the acknowledgement moves, the job does not")
PY
check "DIFFERENTIAL intake binding: same job, a different way to be told it arrived" "$?" "0"

echo "10. what an outside caller reads before writing any code"
python3 run.py --describe > out/describe.json 2>&1
check "the capability description is printed" "$?" "0"
py <<'PY'
import json
d = json.load(open("out/describe.json"))
declaration = json.load(open("admission.json"))
assert len(d["doors"]) == 4 and {x["door"] for x in d["doors"]} == {"human", "event", "schedule", "external"}
assert d["envelope"]["schema_ref"] == declaration["schema_ref"]
assert d["task_lifecycle"]["states"] == declaration["lifecycle"]["states"]
assert d["task_lifecycle"]["cancellable"] is True
assert d["acknowledgement"]["carries_result"] is False
assert d["idempotency"]["retention_s"] == declaration["idempotency"]["retention_s"]
print("described:", len(d["doors"]), "doors,", len(d["task_lifecycle"]["states"]), "lifecycle states")
PY
check "it names the four doors, the schema, the lifecycle and the retention window" "$?" "0"
py <<'PY'
import json
d = json.load(open("admission.json"))
d["lifecycle"]["states"] = [s for s in d["lifecycle"]["states"] if s != "cancelled"]
json.dump(d, open("out/nocancel.json", "w"), indent=2)
PY
python3 run.py --describe --admission out/nocancel.json > out/nocancel-describe.json 2>&1
python3 run.py --door human --admission out/nocancel.json --ledger out/nocancel.jsonl --json \
  > out/nocancel.out 2>&1
py <<'PY'
import json
full = json.load(open("out/describe.json"))["task_lifecycle"]
trimmed = json.load(open("out/nocancel-describe.json"))["task_lifecycle"]
assert full["cancellable"] is True and trimmed["cancellable"] is False, (full, trimmed)
assert json.load(open("out/human.json"))[0]["cancellable"] is True
assert json.load(open("out/nocancel.out"))[0]["cancellable"] is False
print("DIFFERENTIAL lifecycle: cancellable true against false, in the description and on the receipt")
PY
check "DIFFERENTIAL lifecycle: the declared states decide what is advertised and what is served" "$?" "0"

echo "11. the receipt, and the record behind it"
python3 run.py --verify-ledger --ledger out/human.jsonl > out/verify.log 2>&1
check "the chain verifies" "$?" "0"
sed '1s/"units_started": 0/"units_started": 9/' out/human.jsonl > out/tampered.jsonl
python3 run.py --verify-ledger --ledger out/tampered.jsonl > out/tamper.log 2>&1
check "a one-character edit is detected" "$?" "2"
python3 run.py --all-doors --ledger out/again-a.jsonl > /dev/null 2>&1
python3 run.py --all-doors --ledger out/again-b.jsonl > /dev/null 2>&1
cmp -s out/again-a.jsonl out/again-b.jsonl && ok "two runs of the four doors are byte-identical" \
  || bad "the run is not deterministic"
INTAKE_FAIL=1 python3 run.py --door human --ledger out/unreachable.jsonl > out/unreachable.log 2>&1
check "an unreachable intake path exits 2" "$?" "2"
py <<'PY'
import json
row = [json.loads(l) for l in open("out/unreachable.jsonl")][0]
assert row["problem"]["type"].endswith("adapter-unavailable") and row["problem"]["status"] == 503
assert row["problem"]["retryable"] is True and row["problem"]["claim_released"] is True
assert row["refused_at"] == "record" and row["entries_recorded"] == 0
print("503, retryable, claim released, nothing recorded")
PY
check "the claim taken for an entry that was never written is released" "$?" "0"

echo "12. house rules"
py <<'PY'
import json, glob
described = set(json.load(open("out/describe.json"))["problem_types"])
produced = {json.loads(l)["problem"]["type"] for path in glob.glob("out/*.jsonl")
            for l in open(path) if json.loads(l)["kind"] == "entry-refused"}
assert produced, "no refusal was exercised at all"
assert described == produced, {"described only": sorted(described - produced),
                               "produced only": sorted(produced - described)}
print(len(produced), "problem types described, and every one of them produced by this run")
PY
check "the failure modes it lists are exactly the ones this run produced" "$?" "0"
py <<'PY'
import os, re
# Every file of this example except README.md, which is the one place a product
# may be named (its standards and adapters tables). This file is scanned too:
# each pattern brackets one of its own letters, so the literal product name is
# not in the scanner while the pattern still matches it, and a scan that cannot
# see itself is not the house rule it is labelled with. Word-anchored, so a
# three-letter engine name does not fire on "opaque" and does not need a
# trailing space to say so.
products = (r"\bopen[a]i\b", r"\banthropi[c]\b", r"\baw[s]\b", r"\bazur[e]\b", r"\bkubernete[s]\b",
            r"\bdocke[r]\b", r"\btempora[l]\b", r"\bstrip[e]\b", r"\bop[a]\b", r"\breg[o]\b",
            r"\bspir[e]\b", r"\bspiff[e]\b", r"\blitell[m]\b", r"\bgoos[e]\b", r"\bpostgre[s]\b",
            r"\bredi[s]\b", r"\bkafk[a]\b", r"\bceda[r]\b", r"\bfirecracke[r]\b", r"\bgviso[r]\b",
            r"\bjaege[r]\b", r"\bdatado[g]\b", r"\blangchai[n]\b", r"\bbedroc[k]\b",
            r"\bopentelemetr[y]\b")
files = []
for root, dirs, names in os.walk("."):
    dirs[:] = [d for d in dirs if d not in ("out", "__pycache__")]   # generated, and not ours
    files += [os.path.join(root, n) for n in names if n != "README.md"]
files.sort()
hits = [(p, w) for p in files for w in products if re.search(w, open(p).read(), re.I)]
assert not hits, hits
assert len(files) >= 12, f"the scan shrank to {len(files)} files: {files}"
print("product_hits=0 over", len(files), "files, this scanner among them")
PY
check "no product name outside README's standards and adapters tables" "$?" "0"
py <<'PY'
import json, re, glob
# provenance.json is scanned with its own cites list removed: a list that
# certifies itself can only ever agree with itself, and the direction that
# matters here is a cited id no row carries.
provenance = json.load(open("provenance.json"))
cited = set(provenance.pop("cites"))
sources = {"provenance.json": json.dumps(provenance)}
for path in ["README.md", "test.sh"] + glob.glob("*.py") + glob.glob("*.json"):
    if path != "provenance.json":
        sources[path] = open(path).read()
ids = set()
for text in sources.values():
    ids |= set(re.findall(r"\b(?:F|E|R|T|X|REF)-[a-z0-9-]+\b", text))
assert cited == ids, {"cited, never used": sorted(cited - ids), "used, never cited": sorted(ids - cited)}
print(len(cited), "records cited, and every one of them carried by a row in", len(sources), "files")
PY
check "provenance.cites is exactly the record ids the rows carry" "$?" "0"

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
[ "$PASS" -ge "$FLOOR" ] || { echo "the visible check counted $PASS, below the floor of $FLOOR"; exit 1; }
