#!/usr/bin/env python3
"""Coverage: the guarantee that no artifact escapes attestation.

interface.py and call.py answer "can one caller get one signed statement over
one artifact it hands us." concern-provenance-q3 asks the question they leave
open (docs/litmus/answers/d.jsonl, score 0): does every artifact PRODUCED over
a period have a record, can that be shown by counting rather than assumed, and
can a component produce one through a path that emits nothing at all. The
finding there was concrete: orphan_subjects was a hard-coded 0, not a count,
and grep -c 'attest' examples/end-to-end/run.py was 0 -- the platform's own
dispatch path emitted no records for what it produced.

The mechanism (closure for concern-provenance-q3, citing X-maturity-a-005 and
X-maturity-a-006): wire emission into the one execution boundary every
artifact-producing action must pass through, so a component that calls no
attestation API of its own still yields a record -- emission is a property of
the *path*, not of the producer's cooperation. Below, produce_artifact() is
that boundary; component_a and component_b (under the CALLER CODE marker) are
producers that mention no adapter, no signer, no store, and still end up
attested. Store.register() is the second half: it is the only write path into
the manifest reconcile() trusts, and it refuses (Problem, document-invalid) to
record any digest the adapter cannot resolve to a real attestation, modelling
"no credential to publish through any other route." reconcile() then counts
artifacts recorded against attestations the adapter can resolve for the same
window and names any gap as a defect, rather than asserting zero
(X-maturity-a-005: coverage moving from opt-in to default, always-on).
admission_check() is the second, independent enforcement X-maturity-a-006
describes: an attestation alone is only a linkage claim, so a consumer at
admission time refuses anything it cannot resolve, regardless of what the
store's manifest claims.

Standard: reuses interface.py's in-toto Statement / DSSE envelope / verify
machinery already cited there (in-toto Attestation Framework + SLSA
provenance). No standard mandates the coverage guarantee itself -- it is
pipeline and admission-policy design, per this item's closure.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import AttestRequest, PREDICATE_BUILD, Problem, digest_of  # noqa: E402
from adapters.dryrun import LocalSignedRecordAdapter                      # noqa: E402

CLOCK = os.environ.get("PROVENANCE_CLOCK", "2026-09-03T00:00:00Z")
WINDOW = "2026-09-03"


def _predicate(component: str, digest: str) -> dict:
    return {"builder": {"id": "harness/provenance/coverage", "actor": "user:corey",
                        "delegation_chain": [{"actor": "user:corey", "obtained_via": "direct"}]},
            "code_version": {"scripts_sha256": {"coverage.py": "n/a"}, "git_commit": "unset",
                             "interface_version": "0.1"},
            "materials": [{"name": component, "digest": digest}],
            "invocation": {"workflow_ref": "harness/provenance/coverage",
                           "correlation": {"run_id": "cov-run", "correlation_id": "cov-corr"},
                           "decision_refs": ["budget:ceiling_micros", "policy:allow"]},
            "started_at": CLOCK, "ended_at": CLOCK}


class Store:
    """The one artifact store this window's coverage is measured against.

    register() is called only from produce_artifact(): it refuses to add a
    manifest entry for any digest the adapter cannot resolve to a real
    attestation. inject_bypass() is the deliberate breakage -- it writes an
    artifact and a manifest line the way a component would if it wrote its
    own output and skipped the boundary, so the escape path the litmus
    question asks about actually exists here to be caught or missed.
    """

    def __init__(self, root: str, adapter):
        self.root = root
        self.adapter = adapter
        self.artifacts_dir = os.path.join(root, "artifacts")
        self.manifest_path = os.path.join(root, "manifest.jsonl")
        os.makedirs(self.artifacts_dir, exist_ok=True)
        open(self.manifest_path, "w").close()   # a run starts from an empty manifest

    def _append(self, record: dict) -> None:
        with open(self.manifest_path, "a") as f:
            f.write(json.dumps(record) + "\n")

    def register(self, artifact_id: str, digest: str, component: str, statement_id: str) -> None:
        if not self.adapter.resolve(digest):
            raise Problem("document-invalid",
                          f"no attestation resolves for {digest}; refusing to register {artifact_id}",
                          coverage_violation="unattested-registration")
        self._append({"artifact_id": artifact_id, "digest": digest, "component": component,
                      "statement_id": statement_id, "window": WINDOW})

    def entries(self) -> list:
        with open(self.manifest_path) as f:
            return [json.loads(line) for line in f if line.strip()]

    def inject_bypass(self, artifact_id: str, payload: bytes) -> str:
        digest = digest_of(payload)
        with open(os.path.join(self.artifacts_dir, artifact_id), "wb") as f:
            f.write(payload)
        # Deliberately skips register(): the escape path, not the boundary.
        self._append({"artifact_id": artifact_id, "digest": digest, "component": "bypass",
                      "statement_id": None, "window": WINDOW})
        return digest


def produce_artifact(store: Store, component: str, payload: bytes) -> dict:
    """THE execution boundary. Every artifact a component below the CALLER
    CODE marker returns comes in here to become a recorded artifact; nothing
    below this function names an adapter, a signer or a store."""
    digest = digest_of(payload)
    artifact_id = component + "-" + digest[7:19]
    ask = AttestRequest.from_dict({
        "subjects": [{"name": component, "digest": digest}],
        "predicate_type": PREDICATE_BUILD, "predicate": _predicate(component, digest),
        "actor": "user:corey",
        "correlation": {"run_id": "cov-run", "correlation_id": "cov-corr"},
        "idempotency_key": "idem-" + digest[7:31]})
    receipt = store.adapter.attest(ask)
    store.adapter.publish(receipt)
    with open(os.path.join(store.artifacts_dir, artifact_id), "wb") as f:
        f.write(payload)
    store.register(artifact_id, digest, component, receipt.statement_id)
    return {"artifact_id": artifact_id, "digest": digest, "statement_id": receipt.statement_id}


# --------------------------------------------------------------------------
# >>> CALLER CODE: two producing components. Neither imports interface.py,
# neither knows an adapter exists, and both still end up with a record
# because the harness routes their output through produce_artifact().
def component_a(source: bytes) -> bytes:
    return b"summary: " + source[:8] + b"\n"


def component_b(source: bytes) -> bytes:
    return b"digest-report: " + source[::-1] + b"\n"
# --------------------------------------------------------------------------


def reconcile(store: Store) -> dict:
    """Count artifacts recorded in the store against attestations the adapter
    can resolve for the same window; name any gap instead of asserting zero."""
    entries = store.entries()
    unattested = [e["artifact_id"] for e in entries
                  if not (e.get("statement_id") and store.adapter.resolve(e["digest"]))]
    attested = len(entries) - len(unattested)
    return {"window": WINDOW, "artifacts_produced": len(entries), "attestations_valid": attested,
            "unattested": unattested, "reconciled": attested == len(entries) and not unattested}


def admission_check(store: Store, digest: str) -> bool:
    """The second, independent enforcement: refuses anything the adapter
    cannot itself resolve, regardless of what the manifest claims."""
    return bool(store.adapter.resolve(digest))


def main() -> int:
    root = "out/coverage"
    if "--root" in sys.argv:
        root = sys.argv[sys.argv.index("--root") + 1]
    breakage = "--break" in sys.argv

    adapter = LocalSignedRecordAdapter(path=os.path.join(root, "attestations.jsonl"))
    store = Store(root, adapter)

    r1 = produce_artifact(store, "component_a", component_a(b"hello world"))
    r2 = produce_artifact(store, "component_b", component_b(b"hello world"))
    print(f"produced via boundary: {r1['artifact_id']}, {r2['artifact_id']} "
          f"(component_a/component_b call no attestation API of their own)")

    if breakage:
        digest = store.inject_bypass("bypass-artifact", b"snuck in with no attestation\n")
        print(f"deliberate breakage: an artifact was written to the store bypassing "
              f"produce_artifact (digest {digest}); this is the escape path the guarantee claims "
              f"cannot happen unnoticed")

    report = reconcile(store)
    print("reconcile: " + json.dumps(report))

    admitted = {e["artifact_id"]: admission_check(store, e["digest"]) for e in store.entries()}
    print("admission_check: " + json.dumps(admitted))

    ok = report["reconciled"] and all(admitted.values())
    print("COVERAGE OK: two counts reconcile, nothing admitted without a resolvable attestation"
          if ok else
          "COVERAGE VIOLATION: an artifact exists in the store with no attestation the adapter "
          "can resolve, and admission_check refuses it")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
