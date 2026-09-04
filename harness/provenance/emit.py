#!/usr/bin/env python3
"""The one execution boundary a producing path calls to get a record.

concern-provenance-q3 (row 76, B1) asks whether every artifact a component
produces gets a record, whether that can be *shown* by counting rather than
assumed, and whether a component can produce one through a path that emits
nothing at all. The first build of coverage.py answered that only against two
functions defined inside coverage.py itself -- a demonstration, not a fact
about the platform. This module is the fix: it is the *same* function real
producing paths call, not a stand-in for it.

`attest_and_record()` is imported and called directly from the single choke
point each real platform already has for what it produces:

  - examples/end-to-end/run.py:  Run.call_agent(), the one method every agent
    completion passes through regardless of which agent or model answered.
  - harness/linked/linked.py:    Linked._run(), the one method every submit()
    call passes through to produce its Result.
  - harness/provenance/coverage.py: component_a/component_b, kept as the
    zero-cooperation demonstration this module was factored out of.

None of those callers name an adapter, a signer or a store; all three end up
with a record because the call is wired into the boundary, not because the
caller asked (X-maturity-a-005: coverage moving from opt-in to default).

Two things this module has to be careful about because it is imported from
*inside* other harnesses' own processes (run.py and linked.py import it, not
just this harness's own scripts):

1. Every harness in this repo names its capability module `interface.py` and
   relies on process isolation to avoid collisions between them (each is its
   own `python3` invocation). Importing this module from inside linked.py's
   process breaks that isolation: `sys.modules['interface']` is already
   bound to harness/linked's own interface.py by the time this file loads.
   A bare `from interface import ...` here would silently pick up whichever
   `interface` module got there first (harness/linked's, not
   harness/provenance's) and fail on a missing name, or worse, succeed
   against the wrong contract. `_load_private()` below loads
   harness/provenance/interface.py under a private module name via
   importlib so this file never touches the bare `interface` name at all.
2. For the same reason this module does not import adapters/dryrun.py: that
   file's own top-level code is `from interface import (...)`, a bare import
   that would hit the same collision. What this module needs from that
   adapter -- sign, chain, append, resolve -- is reimplemented directly here
   against the privately-loaded interface module instead.

The store this writes is not wiped on construction, unlike the dry-run
adapter harness/provenance's own gate uses (whose wipe is deliberate: a
single gate run asserts on deterministic bytes). A period is made of more
than one process -- run.py is invoked once per entry, call.py once per
adapter binding -- and none of those invocations may erase what an earlier
one in the same period wrote.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_private(name: str, filename: str):
    """Load a module from this directory under a name that cannot collide
    with a same-named module another harness already put in sys.modules."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_iface = _load_private("_harness_provenance_interface", "interface.py")
AttestRequest = _iface.AttestRequest
PREDICATE_BUILD = _iface.PREDICATE_BUILD
Problem = _iface.Problem
digest_of = _iface.digest_of
canonical = _iface.canonical
statement = _iface.statement
pae = _iface.pae
mac = _iface.mac
bindings = _iface.bindings
PAYLOAD_TYPE = _iface.PAYLOAD_TYPE
Envelope = _iface.Envelope
Receipt = _iface.Receipt
Location = _iface.Location

CLOCK = os.environ.get("PROVENANCE_CLOCK", "2026-09-03T00:00:00Z")
_HELD_KEY = hashlib.sha256(b"harness/provenance dry-run held key").digest()   # same key dryrun.py signs with
_ADAPTERS: dict[str, "_Store"] = {}      # one store per root, reused within a process


class _Store:
    """The same shape as adapters/dryrun.py's LocalSignedRecordAdapter --
    possession-signed, hash-chained, append-only -- reimplemented against the
    privately-loaded interface module (see module docstring) instead of
    importing that file, and never wiped on construction: a store that
    already holds attestations from an earlier run in this period keeps them."""

    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        if not os.path.exists(path):
            open(path, "w").close()          # a period starts from an empty store exactly once
        records = self._records()
        self.head = records[-1]["hash"] if records else "genesis"

    def _records(self) -> list:
        with open(self.path) as fh:
            return [json.loads(line) for line in fh if line.strip()]

    def attest(self, request) -> "Receipt":
        bound = bindings(request.predicate)
        doc = statement(request.subjects, request.predicate_type, request.predicate)
        payload = canonical(doc)
        keyid = "local-held-key-v1"
        envelope = Envelope(PAYLOAD_TYPE, __import__("base64").b64encode(payload).decode(),
                            [{"keyid": keyid, "sig": mac(_HELD_KEY, pae(PAYLOAD_TYPE, payload))}])
        statement_id = "urn:agentic:attestation:" + hashlib.sha256(payload).hexdigest()[:24]
        record = {"id": statement_id, "prev": self.head, "envelope": envelope.to_dict(),
                  "subjects": [s.digest for s in request.subjects],
                  "actor": bound["actor"], "code_version": bound["code_version"],
                  "correlation": request.correlation}
        record["hash"] = hashlib.sha256(canonical(record)).hexdigest()
        with open(self.path, "a") as fh:
            fh.write(json.dumps(record, sort_keys=True) + "\n")
        self.head = record["hash"]
        return Receipt(envelope, statement_id, {"keyid": keyid, "authority": "possession", "expires": None})

    def resolve(self, subject_digest: str) -> list:
        return [r["envelope"] for r in self._records() if subject_digest in r["subjects"]]


def _store_for(root: str) -> _Store:
    path = os.path.join(root, "attestations.jsonl")
    key = os.path.abspath(path)
    if key not in _ADAPTERS:
        _ADAPTERS[key] = _Store(path)
    return _ADAPTERS[key]


def _predicate(component: str, digest: str, actor: str) -> dict:
    return {"builder": {"id": component, "actor": actor,
                        "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "code_version": {"scripts_sha256": {}, "git_commit": os.environ.get("GIT_COMMIT", "unset"),
                             "interface_version": "0.1"},
            "materials": [{"name": component, "digest": digest}],
            "invocation": {"workflow_ref": component,
                           "correlation": {"run_id": "n/a", "correlation_id": "n/a"},
                           "decision_refs": []},
            "started_at": CLOCK, "ended_at": CLOCK}


def reset(root: str) -> None:
    """Start a new period: wipe the accumulated store. Never called implicitly
    by construction -- only a caller that means to start a fresh window calls
    this (the gate does, once, before the runs it measures)."""
    key = os.path.abspath(os.path.join(root, "attestations.jsonl"))
    _ADAPTERS.pop(key, None)
    os.makedirs(root, exist_ok=True)
    open(os.path.join(root, "attestations.jsonl"), "w").close()
    open(os.path.join(root, "manifest.jsonl"), "w").close()
    artifacts_dir = os.path.join(root, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    for name in os.listdir(artifacts_dir):
        os.remove(os.path.join(artifacts_dir, name))


def attest_and_record(root: str, component: str, payload: bytes, actor: str = "user:corey") -> dict:
    """THE boundary. Attest `payload`, write it to the artifact store and
    append the one manifest line register_or_refuse would also accept -- so
    a caller of this function alone already satisfies the guarantee; nothing
    below this call names an adapter, a signer or a store."""
    store = _store_for(root)
    digest = digest_of(payload)
    ask = AttestRequest.from_dict({
        "subjects": [{"name": component, "digest": digest}],
        "predicate_type": PREDICATE_BUILD, "predicate": _predicate(component, digest, actor),
        "actor": actor})
    receipt = store.attest(ask)
    artifacts_dir = os.path.join(root, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)
    artifact_id = component + "-" + digest[7:19]
    with open(os.path.join(artifacts_dir, artifact_id), "wb") as f:
        f.write(payload)
    register_or_refuse(root, artifact_id, digest, component, receipt.statement_id)
    return {"artifact_id": artifact_id, "digest": digest, "statement_id": receipt.statement_id}


def register_or_refuse(root: str, artifact_id: str, digest: str, component: str, statement_id) -> None:
    """The only write path into manifest.jsonl. Refuses -- raises, appends
    nothing -- for any digest the store cannot itself resolve to a real
    attestation, which is what a component trying to register an artifact it
    never had attested would have to get past. There is no other function in
    this module that appends to manifest.jsonl."""
    store = _store_for(root)
    if not statement_id or not store.resolve(digest):
        raise Problem("document-invalid",
                      f"no attestation resolves for {digest}; refusing to register {artifact_id} "
                      f"({component}) -- there is no credential to publish through any other route",
                      coverage_violation="unattested-registration")
    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "manifest.jsonl"), "a") as f:
        f.write(json.dumps({"artifact_id": artifact_id, "digest": digest, "component": component,
                            "statement_id": statement_id}) + "\n")


def manifest_entries(root: str) -> list:
    path = os.path.join(root, "manifest.jsonl")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def produced_artifacts(root: str) -> list:
    """Ground truth: what is actually on disk in the artifact store, not what
    a manifest self-reports. This is the enumeration concern-provenance-q3
    asks for -- 'can it be shown', not 'is it claimed'."""
    artifacts_dir = os.path.join(root, "artifacts")
    if not os.path.isdir(artifacts_dir):
        return []
    return sorted(os.listdir(artifacts_dir))


def reconcile(root: str) -> dict:
    """Count artifacts actually present in the store (a directory listing,
    not a self-reported log) against manifest entries the store can still
    resolve to a valid attestation. Name any gap; never assert zero."""
    store = _store_for(root)
    produced = produced_artifacts(root)
    by_id = {e["artifact_id"]: e for e in manifest_entries(root)}
    unattested = []
    for artifact_id in produced:
        entry = by_id.get(artifact_id)
        if entry is None or not entry.get("statement_id") or not store.resolve(entry["digest"]):
            unattested.append(artifact_id)
    return {"artifacts_produced": len(produced), "attestations_valid": len(produced) - len(unattested),
            "unattested": unattested, "reconciled": not unattested}


def admission_check(root: str, digest: str) -> bool:
    """The second, independent enforcement: refuses anything the store
    cannot itself resolve, regardless of what the manifest claims."""
    return bool(_store_for(root).resolve(digest))
