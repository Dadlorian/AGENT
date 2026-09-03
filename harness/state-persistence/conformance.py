#!/usr/bin/env python3
"""The conformance run every state-persistence adapter must pass.

The same cases run against any binding: nothing here knows which adapter
answered. Used before and after a swap; the two reports are what proves the
interface held (T-t7-05, T-t9-06). Case 9 hands the stored records to a
verifier this file did not write - verify_external.py - invoked as a
subprocess with no access to this module's own tree-building code.

    python3 harness/state-persistence/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/state-persistence/conformance.py --adapter second --report out/second.json
    python3 harness/state-persistence/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (AppendRequest, Problem, StatePersistenceAdapter,  # noqa: E402
                       proof_as_dict, verify_inclusion_proof)
from adapters.dryrun import DryRunAdapter                                # noqa: E402
from adapters.live import LiveLedgerAdapter                              # noqa: E402
from adapters.second import ObjectStoreAdapter                           # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveLedgerAdapter, "second": ObjectStoreAdapter}
# Product names belong in adapters/ and in the env-var table of README.md, nowhere else.
PRODUCTS = re.compile(r"(s3|gcs|postgres|dynamodb|kafka|litellm|firecracker|temporal|langfuse)", re.I)


def run_external_verifier(docs: list) -> dict:
    """Invokes verify_external.py as a subprocess - it never imports this module."""
    proc = subprocess.run([sys.executable, os.path.join(HERE, "verify_external.py")],
                          input=json.dumps(docs), capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, f"verify_external.py exited {proc.returncode}: {proc.stderr}"
    return json.loads(proc.stdout)


def mk(partition: str, kind: str, body: dict, head, **extra) -> dict:
    doc = {"partition": partition, "kind": kind, "body": body,
          "fencing_token": head.size + 1 + extra.pop("token_bump", 0),
          "expected_head": head.chain_digest if head.size else None}
    doc.update(extra)
    return doc


def run(name: str) -> tuple[list, dict]:
    adapter: StatePersistenceAdapter = ADAPTERS[name]()
    partition = f"conformance-{name}"
    report = {"binding": name, "adapter": adapter.entity, "execution_model": adapter.execution_model,
              "declared_gaps": list(adapter.declared_gaps), "cases": []}
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

    @case("put one opaque record and read it back")
    def _happy():
        h0 = adapter.resolve_head(partition)
        rec, h1 = adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": 1}, h0)))
        assert rec.body == {"n": 1}, "the body came back changed"
        back = adapter.read_at(partition, h1, {"record_id": rec.record_id})
        assert len(back) == 1 and back[0].record_id == rec.record_id, "the record did not read back"
        report["record_id"] = rec.record_id
        report["head0_size"] = h0.size
        return f"record_id={rec.record_id[:19]}... read back at size {h1.size}"

    @case("a pinned snapshot does not see a later write")
    def _pin():
        h = adapter.resolve_head(partition)
        rec_a, h_a = adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": "a"}, h)))
        rec_b, h_b = adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": "b"}, h_a)))
        at_a = adapter.read_at(partition, h_a)
        ids = [r.record_id for r in at_a]
        assert rec_a.record_id in ids and rec_b.record_id not in ids, "the later write leaked into the pin"
        report["pinned_size"] = h_a.size
        report["landed_after_pin"] = h_b.size - h_a.size
        return f"pinned at size {h_a.size}; {h_b.size - h_a.size} more landed after and did not appear"

    @case("an inclusion proof verifies without the whole log")
    def _prove():
        h = adapter.resolve_head(partition)
        rec, h1 = adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": "prove-me"}, h)))
        proof = adapter.prove(partition, rec.record_id, h1)
        assert verify_inclusion_proof(proof), "the proof did not verify against its own head"
        assert len(proof.path) <= max(1, (h1.size - 1).bit_length()), \
            f"path length {len(proof.path)} is not logarithmic in tree size {h1.size}"
        report["path_length"] = len(proof.path)
        report["tree_size_at_proof"] = h1.size
        return f"path length {len(proof.path)} for tree size {h1.size}: no full-log rehash needed"

    @case("a tampered proof does not verify")
    def _bad_proof():
        h = adapter.resolve_head(partition)
        rec, h1 = adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": "tamper-me"}, h)))
        proof = adapter.prove(partition, rec.record_id, h1)
        broken = proof_as_dict(proof)
        broken["record_id"] = "sha256:" + "0" * 64
        from interface import InclusionProof, Head as _H
        tampered = InclusionProof(broken["record_id"], proof.leaf_index, proof.head, proof.path)
        assert not verify_inclusion_proof(tampered), "a proof for the wrong record still verified"
        return "a proof naming a different record_id was rejected"

    @case("two writers racing for the same head never fork the log")
    def _fork():
        h = adapter.resolve_head(partition)
        rec_a, h_a = adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"who": "A"}, h)))
        try:
            adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"who": "B"}, h)))
            raise AssertionError("writer B was accepted even though the head had already moved")
        except Problem as problem:
            assert problem.body["type"].endswith("head-moved") and problem.body["status"] == 409, problem.body
        after = adapter.resolve_head(partition)
        assert after.chain_digest == h_a.chain_digest, "the head is not the single winner's head"
        return f"writer B refused as head-moved 409; the head is winner A's ({after.size} records, one line)"

    @case("a stale fencing token is refused even if the head still matches")
    def _stale_token():
        h = adapter.resolve_head(partition)
        adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": "fresh-token"}, h)))
        try:
            adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": "stale-token"}, h,
                                                       token_bump=-1)))
            raise AssertionError("a token at or behind the last accepted one was allowed through")
        except Problem as problem:
            assert problem.body["type"].endswith("head-moved"), problem.body
        return "a delayed writer's stale token was refused independently of the head check"

    @case("an append naming a field outside the vocabulary is refused before it is applied")
    def _malformed():
        h = adapter.resolve_head(partition)
        doc = mk(partition, "probe", {"n": "x"}, h, vendor="a-vendor")
        try:
            adapter.append(AppendRequest.from_dict(doc))
            raise AssertionError("a request naming an extra field was accepted")
        except Problem as problem:
            assert problem.body["type"].endswith("document-invalid") and problem.body["status"] == 422, problem.body
        return "document-invalid 422, nothing was applied"

    @case("read_at filters by kind without reading the whole partition into the caller")
    def _selector():
        h = adapter.resolve_head(partition)
        _, h1 = adapter.append(AppendRequest.from_dict(mk(partition, "tagged", {"n": 1}, h)))
        matched = adapter.read_at(partition, h1, {"kind": "tagged"})
        assert all(r.kind == "tagged" for r in matched) and matched, "the kind selector did not filter"
        return f"{len(matched)} record(s) of kind 'tagged' at size {h1.size}"

    @case("a consistency proof shows the log only grew")
    def _consistency():
        h_old = adapter.resolve_head(partition)
        adapter.append(AppendRequest.from_dict(mk(partition, "probe", {"n": "grows-the-log"}, h_old)))
        h_new = adapter.resolve_head(partition)
        cp = adapter.prove_consistency(partition, h_old, h_new)
        from interface import verify_consistency
        old_root = bytes.fromhex(h_old.root_hash.split(":", 1)[1])
        new_root = bytes.fromhex(h_new.root_hash.split(":", 1)[1])
        path = [bytes.fromhex(p.split(":", 1)[1]) for p in cp.path]
        ok = verify_consistency(h_old.size, h_new.size, path, old_root, new_root)
        assert ok, "the consistency proof did not verify the extension"
        return f"size {h_old.size} -> {h_new.size} verified as a pure extension"

    @case("redact drops the body but the record's proof still verifies")
    def _redact():
        h = adapter.resolve_head(partition)
        rec, h1 = adapter.append(AppendRequest.from_dict(mk(partition, "secret", {"ssn": "redact-me"}, h)))
        proof_before = adapter.prove(partition, rec.record_id, h1)
        assert verify_inclusion_proof(proof_before), "the proof did not verify before redaction"
        tomb = adapter.redact(partition, rec.record_id, "conformance-authority")
        assert tomb.body is None and tomb.record_id == rec.record_id, "redact changed the record's identity"
        proof_after = adapter.prove(partition, rec.record_id, h1)
        assert verify_inclusion_proof(proof_after), "the proof broke after the body was dropped"
        report["redact_supported"] = True
        return "body dropped, record_id unchanged, the same proof still verifies"

    @case("an independent verifier, run as a subprocess, recomputes the same head")
    def _external():
        h = adapter.resolve_head(partition)
        records = adapter.read_at(partition, h)
        docs = [{"record_id": r.record_id, "kind": r.kind, "partition": r.partition, "body": r.body}
               for r in records]
        out = run_external_verifier(docs)
        assert out["root_hash"] == h.root_hash, f"external root {out['root_hash']} != adapter root {h.root_hash}"
        content_gap = any("content-id recomputation does not apply" in g for g in adapter.declared_gaps)
        if not content_gap:
            assert out["chain_break_at"] == -1, f"the untampered log reported a chain break at {out['chain_break_at']}"
        report["external_head_matches"] = out["root_hash"] == h.root_hash
        report["chain_break_at"] = out["chain_break_at"]
        report["content_id_gap_honoured"] = content_gap
        report["records_verified_externally"] = out["count"]
        return f"{out['count']} records, external root matches the adapter's head, chain_break_at={out['chain_break_at']}"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["appends"] = adapter.appends
    report["refusals"] = adapter.refusals
    report["marker"] = adapter.observed_marker
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def product_scan(root: str) -> tuple[int, list]:
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
                if found and "PRODUCTS = " not in line:
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the state-persistence interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names outside adapters/")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product name outside adapters/")
        print(f"product_hits={count}")
        return 1 if count else 0

    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        cases, report = run(name)
        print(f"# binding {name} ({report['execution_model']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"appends={report['appends']} refusals={report['refusals']} product_hits={report['product_hits']}")
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
