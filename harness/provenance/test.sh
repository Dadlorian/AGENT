#!/usr/bin/env bash
# Gate for the provenance harness. Everything here is measured, not claimed.
#   bash harness/provenance/test.sh          dry run: conformance, the swap proof, two deliberate breakages
#   bash harness/provenance/test.sh --live   the same against the evidence store on this host, if its env vars are set
set -u
cd "$(dirname "$0")"
PASS=0; FAIL=0
ok()   { echo "  ok   $1"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL $1"; FAIL=$((FAIL+1)); }
check(){ if [ "$2" = "$3" ]; then ok "$1 ($2)"; else bad "$1 (expected $3, got $2)"; fi; }

rm -rf out && mkdir -p out

echo "1. conformance against the dry-run adapter"
python3 conformance.py --adapter dryrun --report out/before.json > out/dryrun.log 2>&1
check "13 cases exit 0" "$?" "0"
grep -q "conformance PASSED: 13/13" out/dryrun.log && ok "13/13 cases passed" || bad "not 13/13"
grep -q "store_mounted=False verifier_exit=0" out/dryrun.log \
  && ok "the envelope was verified by another process with our store unreachable" \
  || bad "the verification did not run store-unmounted"

echo "1b. the minimal call a caller writes"
python3 conformance.py --caller-lines > out/caller.log 2>&1
check "caller region is under 40 lines and names no adapter storage" "$?" "0"
grep -o "caller_lines=[0-9]*" out/caller.log | head -1 | sed 's/^/  ..   /'
ADAPTER=dryrun python3 call.py > out/call.log 2>&1
check "one attested artifact exits 0" "$?" "0"
grep -q "signature checks out over the PAE" out/call.log && ok "the caller read a verified statement" || bad "not verified"
grep -q "does not match the artifact supplied" out/call.log \
  && ok "one byte edited: the same envelope no longer verifies" || bad "the edit was not caught"
SKIP_PROVENANCE=1 python3 call.py > out/call-optout.log 2>&1
check "a caller asking to skip provenance exits 2" "$?" "2"
grep -q "document-invalid" out/call-optout.log && ok "typed as document-invalid (422)" || bad "not typed"
grep -q "nothing to opt into" out/call-optout.log && ok "there is no attest flag to set" || bad "no reason given"

echo "1c. the dry-run adapter's own failure path"
PROVENANCE_FAIL=1 python3 call.py > out/call-fail.log 2>&1
check "an unreadable signing key exits 2" "$?" "2"
grep -q "adapter-unavailable" out/call-fail.log && ok "typed as adapter-unavailable (503)" || bad "not typed"
grep -q "no statement was emitted" out/call-fail.log && ok "nothing was written" || bad "silence about the store"

echo "2. swap proof: same conformance, before and after, no code edit between them"
BEFORE_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
python3 conformance.py --adapter second --report out/after.json > out/second.log 2>&1
check "conformance after the swap exits 0" "$?" "0"
grep -q "conformance PASSED: 13/13" out/second.log && ok "13/13 cases passed on the second adapter" || bad "not 13/13"
AFTER_HASH=$(cat interface.py call.py conformance.py | sha256sum | cut -d' ' -f1)
check "nothing but the binding changed between the two runs" "$AFTER_HASH" "$BEFORE_HASH"
ADAPTER=second python3 call.py > out/call-second.log 2>&1
check "the same caller code runs on the second adapter" "$?" "0"
grep -q "inclusion proof recomputes log root" out/call-second.log \
  && ok "the second store returned an inclusion proof the caller never asked for" || bad "no inclusion proof"
python3 - <<'PY' > out/axes.log 2>&1
import json
before, after = json.load(open("out/before.json")), json.load(open("out/after.json"))
axes = [("signer_authority", "where authority comes from"),
        ("key_lifetime", "how long the signer lives"),
        ("store_kind", "what the envelope is written into"),
        ("material_source", "how a verifier gets the material"),
        ("offline_capable", "whether it can sign with no network"),
        ("log_inclusion_proofs", "whether a third party gets a proof"),
        ("store_integrity_kind", "what the store can say about itself")]
differ = [a for a, _ in axes if before[a] != after[a]]
for axis, why in axes:
    print(f"{axis:22} {str(before[axis]):24} {str(after[axis]):26} ({why})")
required = ["adapter", "attestations_emitted", "attestations_verified", "subject_mismatches",
            "external_verifier", "external_verifier_exit", "store_mounted", "adapters_run"]
for report in (before, after):
    missing = [f for f in required if f not in report]
    assert not missing, f"the report is missing {missing}"
    assert report["store_mounted"] is False, "a verification ran with our store reachable"
    assert report["external_verifier_exit"] == 0 and report["attestations_verified"] > 0, report["binding"]
    assert report["subject_mismatches"] == 0 and report["orphan_subjects"] == 0, report["binding"]
    assert report["selected_by"] == "configuration", "a code edit between runs would not be a swap"
assert before["adapter"] == "local-signed-jsonl" and after["adapter"] == "keyless-transparency-log"
assert before["log_inclusion_proofs"] == "unsupported", "the local adapter must declare, not report zero"
assert after["log_inclusion_proofs"] > 0, "the log adapter must produce a proof"
assert len(differ) >= 3, f"only {len(differ)} axes differ; the swap would test configuration, not the contract"
assert before["cases_passed"] == after["cases_passed"] == 13, "both bindings must pass the same cases"
print(f"axes_differing={len(differ)} adapters_run={before['adapters_run'] + after['adapters_run']} "
      f"cases_before={before['cases_passed']} cases_after={after['cases_passed']}")
PY
check "the two adapters differ in execution model on 3 or more axes" "$?" "0"
grep -q "axes_differing=7" out/axes.log && ok "7 axes differ (authority, key lifetime, store, material, offline, proof, integrity)" \
  || bad "$(tail -1 out/axes.log)"
grep -q "adapters_run=2" out/axes.log && ok "the merged report shows 2 adapters run, selected by configuration" \
  || bad "adapters_run is not 2"

echo "3. no product name in the interface, the caller or the conformance run"
python3 conformance.py --product-scan . > out/scan.log 2>&1
check "product scan over the shipped tree exits 0" "$?" "0"
grep -q "product_hits=0" out/scan.log && ok "0 hits outside adapters/" || bad "product names leaked"

echo "4. deliberate breakage: the artifact is rebuilt and the statement is not"
python3 conformance.py --adapter dryrun --break rebuilt-artifact --report out/break-1.json > out/break-1.log 2>&1
check "the breakage run exits non-zero" "$?" "1"
python3 - <<'PY' > out/break-check.log 2>&1
import json
one = json.load(open("out/break-1.json"))
assert one["subject_mismatches"] == 1, one["subject_mismatches"]
assert one["attestations_verified"] == 0, one["attestations_verified"]
assert one["external_verifier_exit"] != 0, "the verifier accepted a rebuilt artifact"
assert one["store_mounted"] is False, "the verifier could reach our store"
print(f"subject_mismatches={one['subject_mismatches']} attestations_verified={one['attestations_verified']} "
      f"verifier_exit={one['external_verifier_exit']}")
PY
check "the verifier rejected it on the subject digest, not on our store" "$?" "0"
cat out/break-check.log | sed 's/^/  ..   /'
echo "4b. deliberate breakage: the signature is dropped from the envelope"
python3 conformance.py --adapter second --break dropped-signature > out/break-2.log 2>&1
check "the breakage run exits non-zero on the second adapter too" "$?" "1"
grep -q "the envelope carries no signature" out/break-2.log && ok "the run names what broke it" || bad "no reason given"

echo "5. the honest-gap declaration is a checked property, not just a comment (C11-F)"
python3 conformance.py --adapter dryrun --report out/independence.json > out/independence-run.log 2>&1
check "generating the report exits 0" "$?" "0"
python3 conformance.py --check-verifier-independence out/independence.json > out/independence-check.log 2>&1
check "no independent verifier is wired in here, and the report honestly says so: exits 0" "$?" "0"
grep -q '"honest": true' out/independence-check.log && ok "declared_independent=false with the gap named in external_verifier" \
  || bad "$(cat out/independence-check.log)"
PROVENANCE_FAKE_INDEPENDENT=1 python3 conformance.py --adapter dryrun --report out/independence-broken.json \
  > out/independence-broken-run.log 2>&1
python3 conformance.py --check-verifier-independence out/independence-broken.json > out/independence-broken-check.log 2>&1
check "a report that falsely claims independence: exits 1" "$?" "1"
grep -q "NONCONFORMANT" out/independence-broken-check.log && ok "the false claim is named, not silently accepted" \
  || bad "$(cat out/independence-broken-check.log)"

if [ "${1:-}" = "--live" ]; then
  echo "5. live: the evidence records on this host"
  if [ -z "${EVIDENCE_STORE:-}" ] || [ -z "${ATTESTATION_STORE:-}" ] || [ -z "${PROVENANCE_KEY_FILE:-}" ]; then
    echo "  SKIP live mode: set EVIDENCE_STORE, ATTESTATION_STORE and PROVENANCE_KEY_FILE (see README.md)."
    echo "       Nothing live was measured."
  else
    python3 conformance.py --adapter live --report out/live.json > out/live.log 2>&1
    check "conformance against the live evidence store exits 0" "$?" "0"
    grep -q "conformance PASSED" out/live.log && ok "the live binding passed the same 13 cases" || bad "live binding failed"
    ADAPTER=live python3 call.py > out/call-live.log 2>&1
    check "the same caller code runs live" "$?" "0"
  fi
fi

echo
echo "passed $PASS, failed $FAIL"
[ "$FAIL" -eq 0 ] || exit 1
