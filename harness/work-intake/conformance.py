#!/usr/bin/env python3
"""The conformance run every work-intake binding must pass.

The same thirteen cases run against any binding: nothing here knows which one
answered. Equivalence is the only property intake has, so the swap test and the
normalisation test are the same run - the report carries the job digest and the
resolved manifest digest, and the two reports before and after a swap must
agree on both (T-t7-05, T-t9-06).

    python3 harness/work-intake/conformance.py --adapter dryrun --report out/before.json
    python3 harness/work-intake/conformance.py --adapter second --report out/after.json
    python3 harness/work-intake/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import producers                                                        # noqa: E402
from interface import (ENTRY_SCHEMA, Envelope, Problem, ProducerMessage,  # noqa: E402
                       resolve_manifest, validate)
from adapters.dryrun import Adapter as DryRunAdapter                    # noqa: E402
from adapters.live import Adapter as LiveAdapter                        # noqa: E402
from adapters.second import Adapter as SecondAdapter                    # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
BINDINGS = {"dryrun": DryRunAdapter, "live": LiveAdapter, "second": SecondAdapter}
# The two rows of the published adapter-config enum. A binding reports which of
# the two execution models it is, never its own name.
CONFIGURED_AS = {"dryrun": "request-pushed-event", "live": "request-pushed-event",
                 "second": "agent-message"}
# Product names belong in adapters/ and in the env-var table of README.md, nowhere else.
PRODUCTS = re.compile(r"(ansible|git_events|github|gitlab|gitea|jenkins|litellm|langfuse|"
                      r"temporal|firecracker|goose|kafka|rabbitmq)", re.I)
ACK_FIELDS = {"entry_id", "correlation_id", "job_digest", "accepted", "duplicate_of"}


def refused(adapter, call, report: dict) -> dict:
    """Run something that must be refused; return the problem body. A refusal
    that is not a registered problem is counted, not swallowed."""
    before = adapter.records
    try:
        call()
    except Problem as problem:
        if not Problem.registered(problem.body["type"]):
            report["untyped_refusals"] += 1
        body = dict(problem.body)
        body["_records_written"] = adapter.records - before
        return body
    except Exception as exc:                       # anything not a problem object is untyped
        report["untyped_refusals"] += 1
        raise AssertionError(f"refusal arrived as {type(exc).__name__}, not problem details: {exc}")
    raise AssertionError("expected a refusal, got an acknowledgement")


def run(name: str) -> tuple[list, dict]:
    adapter = BINDINGS[name]()
    report = {"binding": name, "adapter": CONFIGURED_AS[name], "selected_by": adapter.selected_by,
              "entity": adapter.entity, "declared_gaps": list(adapter.declared_gaps),
              "producers_run": 0, "distinct_job_digests": 0, "distinct_entry_ids": 0,
              "invalid": 0, "untyped_refusals": 0, "adapters_run": 1,
              "job_digest": "", "manifest_digest": "", "rejected_at_intake": [],
              "schema_id": ENTRY_SCHEMA["$id"], "cases": []}
    report.update(adapter.axes())
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            except Exception as exc:      # a case may never end the run: it reports and fails
                cases.append(("FAIL", f"{label}: unexpected {type(exc).__name__}: {exc}"))
            return fn
        return wrap

    def submit(door, subject=None):
        message = adapter.render_message(door, subject or producers.SUBJECT)
        envelope = adapter.accept(message)
        return message, envelope, adapter.admit(envelope)

    # --- the one document, through all four doors ---------------------------
    # A producer refused here is not a crash: it is counted and the cases below
    # report it, which is what lets one binding fail while the other passes.
    admitted: list[tuple[dict, ProducerMessage, Envelope, object]] = []
    for door in producers.DOORS:
        try:
            admitted.append((door,) + submit(door))
        except Problem as problem:
            report["rejected_at_intake"].append({"kind": door["kind"], "type": problem.body["type"],
                                                 "detail": problem.body["detail"]})
            if problem.body["type"].endswith("document-invalid"):
                report["invalid"] += 1
    report["producers_run"] = len(admitted) + len(report["rejected_at_intake"])

    @case("one document through the four producers")
    def _four():
        assert not report["rejected_at_intake"], \
            f"{len(report['rejected_at_intake'])} producers were refused: {report['rejected_at_intake'][0]}"
        assert len(admitted) == 4, f"{len(admitted)} producers ran"
        digests = {ack.job_digest for _, _, _, ack in admitted}
        entries = {e.entry_id for _, _, e, _ in admitted}
        report["distinct_job_digests"], report["distinct_entry_ids"] = len(digests), len(entries)
        report["job_digest"] = sorted(digests)[0]
        assert len(digests) == 1, f"{len(digests)} job digests; a producer left a fingerprint on the job"
        assert len(entries) == 4, f"{len(entries)} entry ids; submissions were collapsed"
        assert {e.kind for _, _, e, _ in admitted} == {"human", "event", "schedule", "external"}
        return f"job_digest={report['job_digest'][7:19]} one job, {len(entries)} submissions"

    @case("one resolved manifest, and it cannot see a door field")
    def _manifest():
        assert admitted, "nothing was admitted, so no manifest could be resolved"
        manifests = {resolve_manifest(e).digest() for _, _, e, _ in admitted}
        report["manifest_digest"] = sorted(manifests)[0]
        assert len(manifests) == 1, f"{len(manifests)} manifests across four doors"
        first = admitted[0][2]
        moved = Envelope(**{**first.dict(), "kind": "external", "entry_id": "another-submission-0001",
                            "occurred_at": "2030-01-01T00:00:00Z",
                            "actor": {"subject": "agent:someone-else",
                                      "delegation_chain": [{"actor": "agent:someone-else",
                                                            "obtained_via": "workload_attestation"}]},
                            "correlation": {"run_id": "run-x", "correlation_id": "corr-x"},
                            "idempotency_key": "another-key-000001"})
        assert resolve_manifest(moved).digest() == report["manifest_digest"], \
            "the manifest changed when only door fields changed"
        steps = len(resolve_manifest(first).steps)
        return f"manifest_digest={report['manifest_digest'][7:19]} {steps} steps, blind to all six door fields"

    @case("every envelope validates against the published schema")
    def _valid():
        report["invalid"] += sum(1 for _, _, e, _ in admitted if validate(e.dict(), ENTRY_SCHEMA))
        assert report["invalid"] == 0, \
            f"{report['invalid']} of {report['producers_run']} envelopes failed {ENTRY_SCHEMA['$id']}"
        return f"{len(admitted)} envelopes, 0 invalid, against {ENTRY_SCHEMA['$id']}"

    @case("the shipped entry fixtures validate against the same schema")
    def _fixtures():
        bad = {k: validate(v, ENTRY_SCHEMA) for k, v in producers.FIXTURES.items()}
        failed = {k: v for k, v in bad.items() if v}
        assert not failed, f"fixtures failed validation: {failed}"
        return f"{len(bad)} fixtures from examples/end-to-end/entries, 0 invalid"

    @case("a producer-specific attribute never reaches the envelope")
    def _dropped():
        for _, message, envelope, _ in admitted:
            assert "priority" in json.dumps(message.body), "the fixture message stopped carrying one"
            assert "priority" not in json.dumps(envelope.dict()), f"{envelope.kind} carried it through"
        return "priority sent by every producer, mapped nowhere, dropped everywhere"

    @case("no transport handle reaches the envelope")
    def _no_handle():
        for _, message, envelope, _ in admitted:
            text = json.dumps(envelope.dict())
            leaked = [v for v in message.transport.values() if isinstance(v, str) and v in text]
            assert not leaked, f"{envelope.kind} carried transport members {leaked}"
        return "handles and content types observed by the adapter, carried by none"

    @case("a malformed task is refused, typed, and nothing is admitted")
    def _malformed():
        door = producers.DOORS[0]
        body = refused(adapter, lambda: submit(door, producers.malformed(producers.SUBJECT)), report)
        assert body["status"] == 422 and body["type"].endswith("document-invalid"), body
        assert body["_records_written"] == 0, "a refused submission wrote an entry"
        assert set(body) >= {"type", "title", "status", "detail"}, "not problem details"
        report["refusal_type"] = body["type"]
        return f"{body['type']} 422, records written {body['_records_written']}"

    @case("a message the mapper cannot map is refused, typed, never a stack trace")
    def _unmappable():
        fmt = adapter.registered_mappers[0]
        body = refused(adapter, lambda: adapter.accept(ProducerMessage(fmt, {"nothing": True}, {})), report)
        assert body["status"] == 422 and body["type"].endswith("document-invalid"), body
        assert "could not map" in body["detail"], body["detail"]
        return f"{body['type']} 422 from the {fmt} mapper"

    @case("an unregistered producer format is refused, never guessed at")
    def _unmapped():
        message = ProducerMessage("some-format-nobody-registered", {"job": {}}, {})
        body = refused(adapter, lambda: adapter.accept(message), report)
        assert body["status"] == 403 and body["rule_id"] == "refuse-unmapped-producer", body
        assert adapter.refuse_unmapped is True, "refuse_unmapped is not a const"
        return f"{body['type']} 403 rule_id={body['rule_id']}"

    @case("a replay under the same key is free")
    def _replay():
        assert admitted, "nothing was admitted, so nothing could be replayed"
        door, _, envelope, ack = admitted[0]
        before = adapter.records
        _, again, ack2 = submit(door)
        assert ack2.duplicate_of == envelope.entry_id, f"duplicate_of {ack2.duplicate_of}"
        assert ack2.job_digest == ack.job_digest, "the replay digested differently"
        assert adapter.records == before, f"the replay wrote {adapter.records - before} entries"
        report["replay_noops"] = 1
        return f"duplicate_of={ack2.duplicate_of}, 0 new entries"

    @case("the same key with a different job is a conflict")
    def _conflict():
        door = producers.DOORS[1]
        body = refused(adapter, lambda: submit(door, producers.other_job(producers.SUBJECT)), report)
        assert body["status"] == 409 and body["type"].endswith("idempotency-conflict"), body
        assert body["_records_written"] == 0, "a conflicting submission wrote an entry"
        return f"{body['type']} 409, records written 0"

    @case("the acknowledgement carries no result")
    def _ack():
        for _, _, _, ack in admitted:
            assert set(ack.dict()) <= ACK_FIELDS, f"the acknowledgement grew {set(ack.dict()) - ACK_FIELDS}"
            assert ack.accepted is True, "acceptance is a const, not a flag"
        assert adapter.ack_carries_result is False, "ack_carries_result is not a const false"
        return "entry id, correlation id, job digest, accepted; nothing about the outcome"

    @case("identity and budget attach per door, checked by value")
    def _identity_budget():
        want = producers.SUBJECT["budget"]
        for door, _, envelope, _ in admitted:
            assert envelope.actor_subject == door["actor_subject"], \
                f"{envelope.kind} acts as {envelope.actor_subject}, not {door['actor_subject']}"
            assert envelope.identity_hops >= len(door["chain"]), \
                f"{envelope.kind} lost delegation hops"
            assert envelope.budget == want, f"{envelope.kind} carries {envelope.budget}"
            assert envelope.budget["on_exceed"] == "terminate_unit", "on_exceed is not a const"
        hops = sorted({e.identity_hops for _, _, e, _ in admitted})
        return f"four actors, hops {hops}, one ceiling {want['ceiling_micros']} micros per door"

    @case("intake admits; it does not execute and it does not plan")
    def _admits_only():
        assert adapter.work_started == 0, f"{adapter.work_started} units of work started at intake"
        assert not hasattr(adapter, "resolve_manifest"), "an adapter that plans cannot be swapped for a mapper"
        assert adapter.records == len(admitted), \
            f"{adapter.records} entries written for {len(admitted)} admitted submissions"
        return "4 entries recorded, 0 work started, planning is a pure function outside the adapter"

    @case("the marker is read from the binding that answered")
    def _marker():
        assert admitted, "nothing was admitted, so no binding answered"
        assert adapter.observed_marker == adapter.declared_marker, \
            f"observed {adapter.observed_marker!r}, binding declares {adapter.declared_marker!r}"
        for _, _, envelope, ack in admitted:
            assert adapter.declared_marker not in json.dumps([envelope.dict(), ack.dict()]), \
                "the binding's marker reached a producer"
        return f"{adapter.observed_marker} matches the binding, and reaches no producer"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["records"] = adapter.records
    report["refusals"] = adapter.refusals
    report["work_started"] = adapter.work_started
    report["product_hits"] = product_scan(HERE)[0]
    report["verdict"] = "pass" if (report["cases_passed"] == report["cases_run"]
                                   and report["producers_run"] == 4
                                   and report["invalid"] == 0) else "fail"
    return cases, report


def product_scan(root: str) -> tuple[int, list]:
    """Product names may live in adapters/ and in README.md's env table. Nowhere
    else. Code is what is scanned (.py and .sh)."""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("adapters", "out", "__pycache__")]
        for name in sorted(filenames):
            if not name.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, name)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = PRODUCTS.search(line)
                if found and "PRODUCTS = " not in line and not line.lstrip().startswith("r\""):
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the work-intake interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(BINDINGS), default=[])
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
        print(f"# binding {name} configured as {report['adapter']} ({report['execution_model']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        failures += report["invalid"] + report["untyped_refusals"]
        print(f"  producers_run={report['producers_run']} distinct_job_digests={report['distinct_job_digests']} "
              f"distinct_entry_ids={report['distinct_entry_ids']} invalid={report['invalid']} "
              f"untyped_refusals={report['untyped_refusals']} records={report['records']} "
              f"work_started={report['work_started']} marker={report['endpoint_marker']} "
              f"product_hits={report['product_hits']} verdict={report['verdict']}")
        reports.append(report)
    if len(reports) > 1:
        for r in reports:
            r["adapters_run"] = len({x["adapter"] for x in reports})
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
