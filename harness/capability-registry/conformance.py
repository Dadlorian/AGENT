#!/usr/bin/env python3
"""The conformance run every capability-registry adapter must pass.

The same cases run against any binding: nothing here knows which store
answered. Used before and after a swap; the two reports are what proves the
interface held (T-t7-05, T-t9-06). The fixture set and the counters
(records_checked, resolved_records, served_unverified, refusals,
refusals_typed) follow cap-capability-registry-implement's definition of
done: three records under one name - a good one, one whose signature is
absent, and one whose digest names a tree edited after signing.

    python3 harness/capability-registry/conformance.py --adapter dryrun --report out/a.json
    python3 harness/capability-registry/conformance.py --adapter second --report out/b.json
    python3 harness/capability-registry/conformance.py --adapter dryrun --break digest-warning
    python3 harness/capability-registry/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import (CapabilityRegistryAdapter, PublishRequest, Query, Problem,  # noqa: E402
                       Verification, digest_of)

BREAKAGES = ("digest-warning",)
# Product names belong in adapters/ and in the env-var table of README.md.
PRODUCTS = re.compile(r"(sigstore|rekor|fulcio|oci://|ghcr\.io|docker\.io|litellm|temporal|"
                      r"langfuse|firecracker)", re.I)
STORAGE = re.compile(r"""["'][^"']*(\.jsonl|\.ndjson|\.db|\.sqlite3?)["']""")
MARKER, GUARD, BOUND = ">>> CALLER CODE", "if __name__", 40
NAMESPACE, NAME = "acme", "widget"


def adapters():
    from adapters.dryrun import SignedIndexAdapter
    from adapters.live import LiveSkillFilesAdapter
    from adapters.second import ContentAddressedFetchAdapter
    return {"dryrun": SignedIndexAdapter, "live": LiveSkillFilesAdapter, "second": ContentAddressedFetchAdapter}


def publish(adapter, version: str, data: bytes, **over) -> object:
    doc = {"namespace": NAMESPACE, "name": NAME, "version": version, "kind": "capability",
          "package_bytes_hex": data.hex(), "actor": "user:conformance", **over}
    return adapter.publish(PublishRequest.from_dict(doc))


def make_fixtures(adapter) -> dict:
    """Three records under one name: good, unsigned, digest-mismatch."""
    good = publish(adapter, "1.0.0", b"widget v1", good_at=["a worked example twenty chars long"])
    unsigned = publish(adapter, "1.1.0", b"widget v1.1")
    adapter.unsign(f"{NAMESPACE}/{NAME}", "1.1.0")
    tampered_bytes = b"widget v1.2"
    mismatch = publish(adapter, "1.2.0", tampered_bytes, rollback_to="1.0.0")
    edited_bytes = tampered_bytes + b" edited after signing"
    adapter.tamper(f"{NAMESPACE}/{NAME}", "1.2.0", edited_bytes)
    return {"good": good, "unsigned": unsigned, "mismatch": mismatch,
           "current_bytes": {"good": b"widget v1", "unsigned": b"widget v1.1", "mismatch": edited_bytes}}


def run(name: str, breakage: str = "") -> tuple:
    adapter = adapters()[name]()
    report = {"binding": name, "adapter": adapter.adapter_kind, "selected_by": "configuration",
              "adapters_run": 1, "records_checked": 0, "resolved_records": 0, "served_unverified": 0,
              "refusals": 0, "refusals_typed": 0, "record_divergence": 0, "index_chain_broken": 0,
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

    fixtures = make_fixtures(adapter)
    original_verify = CapabilityRegistryAdapter.verify
    if breakage == "digest-warning":
        def broken_verify(self, record):
            key = self._verifying_material(record.namespace, record.name)
            import hmac as _hmac
            from interface import canonical, mac
            sig_ok = key is not None and _hmac.compare_digest(mac(key, canonical(record.unsigned())),
                                                               record.signature)
            return Verification(sig_ok, True) if sig_ok else Verification(False, False)  # BREAKAGE
        CapabilityRegistryAdapter.verify = broken_verify

    @case("publish returns an immutable record naming the digest of the package it names")
    def _publish_shape():
        rec = fixtures["good"]
        assert rec.digest == digest_of(b"widget v1"), rec.digest
        assert rec.signature and len(rec.signature) == 64, "no signature"
        assert rec.record_schema_version.endswith(":0.1"), rec.record_schema_version
        return f"{rec.namespace}/{rec.name}@{rec.version} digest={rec.digest[:18]}..."

    @case("a record cannot be edited in place: a second publish of the same version is refused")
    def _immutable():
        before = adapter.resolutions
        try:
            publish(adapter, "1.0.0", b"widget v1, edited")
            raise AssertionError("a second publish of an existing version was accepted")
        except Problem as exc:
            assert exc.body["type"] == "urn:agentic:problem:document-invalid", exc.body
        assert adapter.resolutions == before, "an in-place edit must not count as a resolution"
        return "1.0.0 is refused a second time; a change is a new version instead"

    @case("resolving each of the three fixtures individually: one resolves, two are refused")
    def _fixtures():
        results = {}
        for version, key in (("1.0.0", "good"), ("1.1.0", "unsigned"), ("1.2.0", "mismatch")):
            results[key] = adapter.resolve(Query(f"{NAMESPACE}/{NAME}", f"=={version}"))
        report["records_checked"] = len(results)
        report["resolved_records"] = sum(1 for r in results.values() if r.resolved)
        real_bytes = fixtures["current_bytes"]
        served_unverified = sum(1 for k, r in results.items() if r.resolved
                                and digest_of(real_bytes[k]) != r.record.digest)
        typed_refusals = [r.problem for r in results.values() if not r.resolved]
        report["served_unverified"] = served_unverified
        report["refusals"] = len(typed_refusals)
        report["refusals_typed"] = sum(1 for p in typed_refusals if p and p["type"].startswith("urn:agentic:problem:"))
        assert results["good"].resolved and results["good"].verification.digest_matched, results["good"]
        return (f"records_checked={report['records_checked']} resolved_records={report['resolved_records']} "
               f"served_unverified={served_unverified} refusals={report['refusals']}")

    @case("a range constraint walks candidates newest-first and refuses-then-continues within it")
    def _walk():
        outcome = adapter.resolve(Query(f"{NAMESPACE}/{NAME}", ">=1.0.0 <2.0.0"))
        if breakage:
            return "skipped under breakage: the walk's own outcome is covered by the fixtures case above"
        assert outcome.resolved and outcome.record.version == "1.0.0", outcome
        assert adapter.refusals >= 2, f"expected the walk to refuse the two bad candidates, got {adapter.refusals}"
        return f"resolved to {outcome.record.version} after refusing the two newer, unverified candidates"

    @case("describe returns the record's good_at and auth_schemes, never the package bytes")
    def _describe():
        doc = adapter.describe(f"{NAMESPACE}/{NAME}", "1.0.0")
        assert doc["good_at"] == ["a worked example twenty chars long"], doc
        assert "package_bytes" not in json.dumps(doc), "package bytes leaked into describe"
        return f"good_at={doc['good_at']}"

    @case("list_versions orders by semantic version, newest first")
    def _list_versions():
        versions = adapter.list_versions(f"{NAMESPACE}/{NAME}")
        assert versions[:3] == ["1.2.0", "1.1.0", "1.0.0"], versions
        return f"{versions}"

    @case("rollback is a resolution, not an edit: resolving the rollback_to version returns the earlier record")
    def _rollback():
        target = fixtures["mismatch"].rollback_to
        outcome = adapter.resolve(Query(f"{NAMESPACE}/{NAME}", f"=={target}"))
        assert outcome.resolved and outcome.record.version == "1.0.0" == target, outcome
        assert outcome.record.digest == fixtures["good"].digest, "rollback did not return the earlier record"
        return f"rollback_to={target} resolves to the same record digest 1.0.0 published"

    @case("a forged signature is refused, typed, and never served")
    def _forged_signature():
        forged = copy.deepcopy(fixtures["good"])
        forged.signature = "f" * 64
        result = adapter.verify(forged)
        assert not result.signature_verified and not result.digest_matched, result
        return "signature check fails first; the digest is never reached for a bad signature"

    @case("an unknown name is refused as record-not-found, typed")
    def _unknown():
        outcome = adapter.resolve(Query(f"{NAMESPACE}/does-not-exist", ">=1.0.0"))
        assert not outcome.resolved and outcome.problem["type"] == "urn:agentic:problem:record-not-found", outcome
        return outcome.problem["type"]

    @case("a publish is refused a semantic version, not guessed at from what a publisher sent")
    def _nonsemver():
        try:
            publish(adapter, "not-a-version", b"widget legacy")
            raise AssertionError("a non-semver version was accepted")
        except Problem as exc:
            assert exc.body["type"] == "urn:agentic:problem:document-invalid", exc.body
            assert "semantic version" in exc.body["detail"], exc.body
        return "refused before it reached the store (cap-capability-registry-implement step 2)"

    if breakage:
        CapabilityRegistryAdapter.verify = original_verify        # restore before reporting store integrity

    @case("this binding's own store integrity check, never what verification rests on")
    def _store():
        integrity = adapter.store_integrity()
        assert integrity["broken"] == 0, integrity
        report["store_kind"] = integrity["kind"]
        report["index_chain_broken"] = integrity["broken"]
        return f"{integrity['kind']}: {integrity['entries']} entries, 0 broken"

    report["resolutions"] = adapter.resolutions
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
        for fname in sorted(filenames):
            if not fname.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, fname)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = PRODUCTS.search(line)
                if found and "PRODUCTS = " not in line and not line.strip().startswith('r"'):
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def caller_lines() -> tuple:
    lines = open(os.path.join(HERE, "call.py")).read().splitlines()
    marks = [i for i, line in enumerate(lines) if MARKER in line]
    assert len(marks) == 1, f"expected one {MARKER} marker, found {len(marks)}"
    body = lines[marks[0] + 1:]
    end = next((i for i, line in enumerate(body) if line.startswith(GUARD)), len(body))
    counted = [line for line in body[:end] if line.strip() and not line.strip().startswith("#")]
    storage = [f"call.py:{n}: {line.strip()}" for n, line in enumerate(lines, 1) if STORAGE.search(line)]
    return len(counted), storage


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the capability-registry interface.")
    ap.add_argument("--adapter", action="append", choices=("dryrun", "live", "second"), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--break", dest="breakage", choices=BREAKAGES, default="",
                    help="the deliberate breakage: the run must fail")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names outside adapters/")
    ap.add_argument("--caller-lines", action="store_true", help="count the caller region of call.py")
    args = ap.parse_args(argv)

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
        except Problem as problem:
            print(f"# binding {name} could not be reached")
            print(json.dumps(problem.body, indent=1))
            return 1
        print(f"# binding {name} ({report['adapter']}, {report['resolution']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        breakage_failed = bool(args.breakage) and report["served_unverified"] > 0
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"] + int(breakage_failed)
        print(f"  entity={report['entity']}")
        print(f"  adapter={report['binding']} records_checked={report['records_checked']} "
              f"resolved_records={report['resolved_records']} served_unverified={report['served_unverified']} "
              f"refusals={report['refusals']} refusals_typed={report['refusals_typed']} "
              f"index_chain_broken={report['index_chain_broken']}")
        reports.append(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w") as fh:
            json.dump(reports if len(reports) > 1 else reports[0], fh, indent=1, sort_keys=True)
    print(f"adapters_run={len(reports)}")
    print(f"conformance {'PASSED' if not failures else 'FAILED'}: "
          f"{sum(r['cases_passed'] for r in reports)}/{sum(r['cases_run'] for r in reports)} cases, "
          f"{len(reports)} binding(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
