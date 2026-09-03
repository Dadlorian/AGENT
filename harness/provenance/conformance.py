#!/usr/bin/env python3
"""The conformance run every provenance adapter must pass.

The same thirteen cases run against any binding: nothing here knows which
adapter answered. Used before and after a swap; the two reports are what proves
the interface held (T-t7-05, T-t9-06). The report shape is the
ProvenanceConformanceReport cap-provenance-implement fixes.

The verification case does not verify in this process. It writes the bundle and
the trust policy to a file, then runs this same script in --verify-bundle mode
as a separate process with the store path pointed at somewhere that does not
exist, and that child imports no adapter and opens no store. A run with our
store reachable would not have tested the property (F-b4-05).

    python3 harness/provenance/conformance.py --adapter dryrun --report out/a.json
    python3 harness/provenance/conformance.py --adapter second --report out/b.json
    python3 harness/provenance/conformance.py --adapter dryrun --break rebuilt-artifact
    python3 harness/provenance/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import base64
import copy
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import (AttestRequest, PREDICATE_AGENT_ACTION, PREDICATE_BUILD,  # noqa: E402
                       Problem, TrustPolicy, canonical, digest_of, mac, pae, verify)

BREAKAGES = ("rebuilt-artifact", "dropped-signature")
# Product names belong in adapters/ and in the env-var table of README.md.
PRODUCTS = re.compile(r"(sigstore|rekor|fulcio|cosign|archivista|slsa-verifier|litellm|temporal|"
                      r"langfuse|firecracker|kb/ledger)", re.I)
STORAGE = re.compile(r"""["'][^"']*(\.jsonl|\.ndjson|\.db|\.sqlite3?|\.journal)["']""")
MARKER, GUARD, BOUND = ">>> CALLER CODE", "if __name__", 40


def adapters():
    """Imported here, not at module scope: the child verifier must import none."""
    from adapters.dryrun import LocalSignedRecordAdapter
    from adapters.live import LiveEvidenceStoreAdapter
    from adapters.second import KeylessTransparencyLogAdapter
    return {"dryrun": LocalSignedRecordAdapter, "live": LiveEvidenceStoreAdapter,
            "second": KeylessTransparencyLogAdapter}


CLOCK = os.environ.get("PROVENANCE_CLOCK", "2026-09-03T00:00:00Z")


def build(source: bytes) -> bytes:
    return b"report: " + __import__("hashlib").sha256(source).hexdigest().encode() + b"\n"


def ask(artifact: bytes, source: bytes, name="report", actor="user:corey", **over) -> dict:
    doc = {"subjects": [{"name": name, "digest": digest_of(artifact)}],
           "predicate_type": PREDICATE_BUILD,
           "predicate": {"builder": {"id": "harness/provenance", "actor": actor},
                         "code_version": {"scripts_sha256": {"conformance.py": digest_of(b"fixed")[7:]},
                                          "git_commit": "unset"},
                         "materials": [{"name": "source", "digest": digest_of(source)}],
                         "invocation": {"correlation": {"run_id": "run-conformance",
                                                        "correlation_id": "corr-conformance"}},
                         "started_at": CLOCK, "ended_at": CLOCK},
           "actor": actor,
           "correlation": {"run_id": "run-conformance", "correlation_id": "corr-conformance"},
           "idempotency_key": "idem-conformance"}
    doc.update(over)
    return doc


def trust(adapter, keyid, expect: dict, proof: bool, types=(PREDICATE_BUILD,)) -> TrustPolicy:
    material = adapter.verifying_material(keyid)
    accepted = ({material["keyid"]: material["material"]} if material.get("issuer") is None
                else {material["issuer"]: "accepted by issuer"})
    return TrustPolicy(accepted, expect, tuple(types), proof, CLOCK)


def refused(adapter, doc: dict, want: str) -> dict:
    before = adapter.attestations
    try:
        adapter.attest(AttestRequest.from_dict(doc))
    except Problem as problem:
        body = dict(problem.body)
        body["_emitted"] = adapter.attestations - before
        return body
    raise AssertionError(f"expected {want}, got an envelope")


# --- the verifier, run as a separate process with the store unreachable -----
def verify_bundle(path: str) -> int:
    doc = json.load(open(path))
    store = doc["store_path"]
    result = verify(doc["envelope"], TrustPolicy.from_dict(doc["policy"]),
                    doc.get("inclusion_proof"), doc.get("verification_material"))
    print(json.dumps({"accepted": result.accepted, "reason": result.reason, "checks": result.checks,
                      "subject_mismatches": result.subject_mismatches,
                      "signer": result.signer, "inclusion_proof_verified": result.inclusion_proof_verified,
                      "store_mounted": os.path.exists(store),
                      "adapters_imported": [m for m in sys.modules if m.startswith("adapters")]}))
    return 0 if result.accepted else 1


def externally_verify(bundle: dict, policy: TrustPolicy, proof, material, out_dir: str) -> tuple:
    """Write the bundle out, then run this script again with no store to read."""
    os.makedirs(out_dir, exist_ok=True)
    store = os.path.join(tempfile.gettempdir(), "provenance-store-that-does-not-exist")
    path = os.path.join(out_dir, "bundle.json")
    with open(path, "w") as fh:
        json.dump({"envelope": bundle, "policy": policy.to_dict(), "inclusion_proof": proof,
                   "verification_material": material, "store_path": store}, fh, indent=1, sort_keys=True)
    proc = subprocess.run([sys.executable, os.path.join(HERE, "conformance.py"), "--verify-bundle", path],
                          capture_output=True, text=True, cwd=tempfile.gettempdir())
    try:
        return proc.returncode, json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return proc.returncode, {"accepted": False, "reason": proc.stderr.strip()[-200:], "checks": []}


VERIFIER = ("harness/provenance/conformance.py --verify-bundle, run as a separate process with no store "
            "(written in this repository; a verifier we did not write is not available here)")


def run(name: str, breakage: str = "") -> tuple:
    adapter = adapters()[name]()
    out_dir = os.path.join(HERE, "out", f"{name}{'-' + breakage if breakage else ''}")
    report = {"binding": name, "adapter": adapter.adapter_kind, "selected_by": "configuration",
              "adapters_run": 1, "attestations_emitted": 0, "attestations_verified": 0,
              "subject_mismatches": 0, "orphan_subjects": 0,
              "external_verifier": VERIFIER, "external_verifier_exit": -1, "store_mounted": True,
              "log_inclusion_proofs": 0 if adapter.supports_inclusion_proof else "unsupported",
              "breakage": breakage or None, "cases": []}
    report.update(adapter.binding())
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            return fn
        return wrap

    source = b"one input line"
    artifact = build(source)
    receipt = adapter.attest(AttestRequest.from_dict(ask(artifact, source)))
    where = adapter.publish(receipt)
    bundle = adapter.fetch(where.uri)

    @case("attest returns a signed envelope carrying an in-toto Statement")
    def _shape():
        env = receipt.envelope.to_dict()
        assert env["payloadType"] == "application/vnd.in-toto+json", env["payloadType"]
        assert env["signatures"] and env["signatures"][0]["sig"], "no signature"
        doc = receipt.envelope.statement()
        assert doc["_type"] == "https://in-toto.io/Statement/v1", doc["_type"]
        assert doc["subject"][0]["digest"]["sha256"] == digest_of(artifact)[7:], "subject digest is not the artifact"
        assert doc["predicateType"] == PREDICATE_BUILD, doc["predicateType"]
        return f"{len(env['signatures'])} signature, subject {doc['subject'][0]['name']}, {doc['predicateType']}"

    @case("the statement binds code version, inputs and actor, or there is no statement")
    def _bindings():
        doc = receipt.envelope.statement()["predicate"]
        assert doc["builder"]["actor"] and doc["code_version"] and doc["materials"], doc
        thin = ask(artifact, source)
        thin["predicate"] = {"builder": {"id": "harness/provenance"}, "materials": []}
        body = refused(adapter, thin, "document-invalid")
        assert body["status"] == 422 and body["_emitted"] == 0, body
        assert body["absent"] == ["actor", "code_version", "inputs"], body["absent"]
        return f"bound; a predicate missing {body['absent']} is 422 with nothing emitted"

    @case("the envelope verifies in another process with our store unreachable")
    def _external():
        held, expect = bundle["envelope"], {"report": digest_of(artifact)}
        if breakage == "rebuilt-artifact":         # the artifact was rebuilt, the statement was not
            expect = {"report": digest_of(build(b"one input line, modified"))}
        if breakage == "dropped-signature":
            held = copy.deepcopy(held)
            held["signatures"] = []
        code, out = externally_verify(held, trust(adapter, receipt.signer["keyid"], expect,
                                                  bool(where.inclusion_proof)),
                                      where.inclusion_proof, bundle["verification_material"], out_dir)
        report["external_verifier_exit"] = code
        report["store_mounted"] = out.get("store_mounted", True)
        report["attestations_verified"] = int(bool(out.get("accepted")))
        report["subject_mismatches"] = out.get("subject_mismatches", 0)
        report["log_inclusion_proofs"] = (int(bool(out.get("inclusion_proof_verified")))
                                          if adapter.supports_inclusion_proof else "unsupported")
        assert not out.get("adapters_imported"), f"the verifier imported {out['adapters_imported']}"
        assert out.get("store_mounted") is False, "the verifier could reach our store"
        assert code == 0 and out.get("accepted"), f"exit {code}: {out.get('reason')}"
        return f"exit 0, store_mounted=false, {len(out['checks'])} checks, no adapter imported"

    @case("editing one byte of the artifact fails verification")
    def _one_byte():
        edited = artifact[:-1] + bytes([artifact[-1] ^ 1])
        result = adapter.verify(bundle["envelope"], trust(adapter, receipt.signer["keyid"],
                                                          {"report": digest_of(edited)},
                                                          bool(where.inclusion_proof)),
                                where.inclusion_proof, bundle["verification_material"])
        assert not result.accepted and result.subject_mismatches == 1, result
        assert result.problem()["status"] == 422, result.problem()
        return f"rejected: {result.reason[:60]}... as 422"

    @case("editing the statement fails the signature")
    def _edited_payload():
        forged = copy.deepcopy(bundle["envelope"])
        doc = json.loads(base64.b64decode(forged["payload"]))
        doc["predicate"]["builder"]["actor"] = "user:someone-else"
        forged["payload"] = base64.b64encode(canonical(doc)).decode()
        result = adapter.verify(forged, trust(adapter, receipt.signer["keyid"], {"report": digest_of(artifact)},
                                              False), None, bundle["verification_material"])
        assert not result.accepted and "signature" in result.reason, result
        return "the actor cannot be changed without the signature failing"

    @case("a signature over the raw JSON instead of the encoding is not accepted")
    def _pae():
        material = adapter.verifying_material(receipt.signer["keyid"])
        key = material["material"]
        if key is None:
            return "the binding publishes no material to sign with; case not applicable"
        forged = copy.deepcopy(bundle["envelope"])
        payload = base64.b64decode(forged["payload"])
        forged["signatures"] = [{"keyid": receipt.signer["keyid"], "sig": mac(bytes.fromhex(key), payload)}]
        result = adapter.verify(forged, trust(adapter, receipt.signer["keyid"], {"report": digest_of(artifact)},
                                              False), None, bundle["verification_material"])
        assert not result.accepted, "a signature over the raw JSON was accepted"
        assert mac(bytes.fromhex(key), pae("application/vnd.in-toto+json", payload)) != forged["signatures"][0]["sig"]
        return "format confusion refused: the encoding is signed, not the document"

    @case("a signer the policy does not accept is rejected")
    def _unknown_signer():
        policy = TrustPolicy({"some-other-keyid": "00" * 32}, {"report": digest_of(artifact)}, (), False, CLOCK)
        result = adapter.verify(bundle["envelope"], policy, where.inclusion_proof,
                                bundle["verification_material"])
        assert not result.accepted and "accepted signer" in result.reason, result
        return "no accepted signer matches the keyid"

    @case("resolve finds the envelope by subject digest, and an unattested digest finds nothing")
    def _resolve():
        found = adapter.resolve(digest_of(artifact))
        assert len(found) == 1, f"resolve returned {len(found)}"
        orphan = build(b"an output nothing attested")
        assert adapter.resolve(digest_of(orphan)) == [], "an unattested digest resolved to something"
        report["orphan_subjects"] = 0
        return "1 envelope for the attested digest, 0 for an unattested one"

    @case("publish gives a location a third party fetches, byte for byte")
    def _publish():
        again = adapter.fetch(where.uri)
        assert canonical(again["envelope"]) == canonical(receipt.envelope.to_dict()), "the fetch differs"
        assert where.store and ":" in where.uri, where
        return f"{where.uri} -> the same envelope, from {where.store}"

    @case("the artifact never travels in the envelope, and a request carrying it is refused")
    def _no_payload():
        assert artifact.decode() not in json.dumps(bundle["envelope"]), "the artifact bytes are in the envelope"
        body = refused(adapter, ask(artifact, source, artifact_bytes=artifact.decode()), "document-invalid")
        assert body["status"] == 422 and body["_emitted"] == 0 and body["rejected_fields"] == ["artifact_bytes"]
        return "only the digest is carried; a request with the bytes is 422 with nothing emitted"

    @case("one envelope format carries an agent action as well as a build")
    def _agent_action():
        action = {"actor": "agent:planner", "tool": "i-fast",
                  "argument_digest": digest_of(b"the argument"), "result_digest": digest_of(artifact),
                  "code_version": {"git_commit": "unset"}, "started_at": CLOCK, "ended_at": CLOCK}
        got = adapter.attest(AttestRequest.from_dict(
            ask(artifact, source, name="turn", predicate_type=PREDICATE_AGENT_ACTION, predicate=action)))
        result = adapter.verify(got.envelope,
                                trust(adapter, got.signer["keyid"], {"turn": digest_of(artifact)},
                                      False, (PREDICATE_AGENT_ACTION,)),
                                None, adapter.verifying_material(got.signer["keyid"]))
        assert result.accepted, result.reason
        return "the same verifier accepts both predicates in the same envelope"

    @case("the declared subset is honest: a proof is verified or declared unsupported")
    def _subset():
        if adapter.supports_inclusion_proof:
            assert where.inclusion_proof and adapter.verify(
                bundle["envelope"],
                trust(adapter, receipt.signer["keyid"], {"report": digest_of(artifact)}, True),
                where.inclusion_proof, bundle["verification_material"]).inclusion_proof_verified
            return f"inclusion proof over a log of {where.inclusion_proof['tree_size']} entries verified"
        assert where.inclusion_proof is None, "a binding that declares no proofs returned one"
        assert any("inclusion proof" in gap for gap in adapter.declared_gaps), "the gap is not declared"
        return "log inclusion proofs declared unsupported, not reported as zero"

    @case("the store's own integrity check is not what verification rests on")
    def _store():
        integrity = adapter.store_integrity()
        assert integrity["verified"], integrity
        assert integrity["entries"] >= 1 and integrity["head"], integrity
        report["store_integrity_kind"] = integrity["kind"]
        return f"{integrity['kind']} head {integrity['head'][:12]} over {integrity['entries']} entries, verified"

    report["attestations_emitted"] = adapter.attestations
    report["refusals"] = adapter.refusals
    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def product_scan(root: str) -> tuple:
    """Product names may live in adapters/ and in README.md's env table. Nowhere else."""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("adapters", "out", "__pycache__")]
        for name in sorted(filenames):
            if not name.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, name)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = PRODUCTS.search(line)
                if found and "PRODUCTS = " not in line and not line.strip().startswith('r"'):
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def caller_lines() -> tuple:
    """The same rule harness/caller_lines.py applies to the other harnesses."""
    lines = open(os.path.join(HERE, "call.py")).read().splitlines()
    marks = [i for i, line in enumerate(lines) if MARKER in line]
    assert len(marks) == 1, f"expected one {MARKER} marker, found {len(marks)}"
    body = lines[marks[0] + 1:]
    end = next((i for i, line in enumerate(body) if line.startswith(GUARD)), len(body))
    counted = [line for line in body[:end] if line.strip() and not line.strip().startswith("#")]
    storage = [f"call.py:{n}: {line.strip()}" for n, line in enumerate(lines, 1) if STORAGE.search(line)]
    return len(counted), storage


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the provenance interface.")
    ap.add_argument("--adapter", action="append", choices=("dryrun", "live", "second"), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--break", dest="breakage", choices=BREAKAGES, default="",
                    help="the deliberate breakage: the run must fail")
    ap.add_argument("--verify-bundle", metavar="PATH", help="child mode: verify one bundle, read no store")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names outside adapters/")
    ap.add_argument("--caller-lines", action="store_true", help="count the caller region of call.py")
    args = ap.parse_args(argv)

    if args.verify_bundle:
        return verify_bundle(args.verify_bundle)
    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product name outside adapters/")
        print(f"product_hits={count}")
        return 1 if count else 0
    if args.caller_lines:
        lines, storage = caller_lines()
        print("\n".join(storage) or "call.py names no adapter storage")
        print(f"caller_lines={lines} bound={BOUND} storage_named={len(storage)}")
        return 1 if lines >= BOUND or storage else 0

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        try:
            cases, report = run(name, args.breakage)
        except Problem as problem:      # a binding that cannot be reached at all
            print(f"# binding {name} could not be reached")
            print(json.dumps(problem.body, indent=1))
            return 1
        print(f"# binding {name} ({report['adapter']}, {report['signer_authority']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  entity={report['entity']}")
        print(f"  cases={report['cases_run']} passed={report['cases_passed']} "
              f"emitted={report['attestations_emitted']} verified={report['attestations_verified']} "
              f"subject_mismatches={report['subject_mismatches']} orphan_subjects={report['orphan_subjects']} "
              f"store_mounted={report['store_mounted']} verifier_exit={report['external_verifier_exit']} "
              f"log_inclusion_proofs={report['log_inclusion_proofs']} product_hits={report['product_hits']}")
        reports.append(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} binding(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
