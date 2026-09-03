#!/usr/bin/env python3
"""The conformance run every trail adapter must pass.

The same cases run against any binding: nothing here knows which adapter
answered. Used before and after a swap; the two reports are what proves the
interface held. The independence case shells out to scan.py as a separate
process (--verify-scan mode is scan.py itself) so the "run from a process
other than the one that appends" clause is actually tested, not asserted.

    python3 conformance.py --adapter dryrun --report out/before.json
    python3 conformance.py --adapter second --report out/after.json
    python3 conformance.py --adapter dryrun --break tampered-entry
    python3 conformance.py --product-scan .
    python3 conformance.py --caller-lines
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import Problem  # noqa: E402

BREAKAGES = ("wiring-fault",)   # the wiring fault xc-audit-trail-implement's definition of done names:
                                 # the scan's schedule declaration is gone and it runs inline, as the writer
PRODUCTS = re.compile(r"(sigstore|rekor|fulcio|temporal|langfuse|firecracker|litellm)", re.I)
MARKER, GUARD, BOUND = ">>> CALLER CODE", "if __name__", 40
FIXTURE_ENTRIES = int(os.environ.get("TRAIL_FIXTURE_ENTRIES", "24"))


def adapters():
    from adapters.dryrun import LocalChainedTrailAdapter
    from adapters.live import LiveLedgerTrailAdapter
    from adapters.second import ExternalCheckableLogAdapter
    return {"dryrun": LocalChainedTrailAdapter, "live": LiveLedgerTrailAdapter,
            "second": ExternalCheckableLogAdapter}


def run_scan_subprocess(adapter_name: str, identity: str, scheduled: bool, min_entries: int, env=None):
    args = [sys.executable, os.path.join(HERE, "scan.py"), "--adapter", adapter_name,
           "--identity", identity, "--min-entries", str(min_entries)]
    if scheduled:
        args.append("--scheduled")
    full_env = dict(os.environ)
    if env:
        full_env.update(env)
    proc = subprocess.run(args, capture_output=True, text=True, env=full_env)
    lines = (proc.stdout or "").splitlines()
    report = {}
    for line in lines:
        try:
            report = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    return proc.returncode, report, proc.stdout, proc.stderr


def run(name: str, breakage: str = "") -> tuple:
    adapter = adapters()[name]()
    out_dir = os.path.join(HERE, "out", f"{name}{'-' + breakage if breakage else ''}")
    os.makedirs(out_dir, exist_ok=True)
    report = {"binding": name, "adapter": adapter.adapter_kind, "selected_by": "configuration",
             "adapters_run": 1, "breakage": breakage or None, "cases": []}
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

    min_entries = 1 if name == "live" else FIXTURE_ENTRIES

    @case("project a run's records into a trail")
    def _project():
        trail = adapter.project()
        report["entries_checked"] = len(trail)
        assert len(trail) >= min_entries, f"only {len(trail)} entries, wanted >= {min_entries}"
        return f"{len(trail)} entries projected"

    trail = adapter.project()

    @case("fetch everything under one correlation id")
    def _fetch():
        corr_ids = {e.correlation.get("correlation_id") for e in trail}
        assert len(corr_ids) >= 1, "no correlation ids at all"
        cid = sorted(corr_ids)[0]
        found = adapter.fetch_by_correlation(cid)
        assert found and all(e.correlation.get("correlation_id") == cid for e in found), "fetch leaked other runs"
        report["correlation_ids_seen"] = len(corr_ids)
        return f"{len(found)} entries under {cid}, of {len(corr_ids)} correlation id(s) total"

    @case("attribute each action to an actor and its delegation chain")
    def _attribute():
        attributed = 0
        for e in trail:
            who = adapter.attribute(e.entry_id)
            if who["actor"] and who["delegation_chain"] and who["delegation_chain"][-1]["actor"] == who["actor"]:
                attributed += 1
        report["actors_missing"] = len(trail) - attributed
        assert attributed == len(trail), f"only {attributed}/{len(trail)} entries attribute cleanly"
        return f"{attributed}/{len(trail)} entries attribute to an actor and a chain ending at that actor"

    @case("the integrity scan, run from a process other than the one that appends")
    def _independent_scan():
        # the breakage xc-audit-trail-implement's definition of done names: the schedule declaration
        # is deleted and the scan is called inline from the writer, with everything else unchanged.
        if breakage == "wiring-fault":
            identity, scheduled = adapter.writer_identity, False
        else:
            identity, scheduled = "actor:scanner-process", True
        code, scan_report, out, err = run_scan_subprocess(name, identity, scheduled, min_entries)
        report["independent_scan"] = scan_report
        assert code == 0, f"scan.py exited {code} (identity={identity} scheduled={scheduled}): {(out + err)[-300:]}"
        assert scan_report.get("independent") is True, scan_report
        assert scan_report.get("scheduled") is True, scan_report
        assert scan_report.get("store_observed") == adapter.entity, scan_report.get("store_observed")
        entries_checked = scan_report["entries_checked"]
        oldest = scan_report["oldest_retained_entry_age_days"]
        return f"entries_checked={entries_checked} oldest_retained_entry_age_days={oldest} independent=true scheduled=true"

    @case("the same scan, run inline by the writer, is honestly not independent")
    def _writer_scan():
        rep = adapter.scan(adapter.writer_identity, False)
        assert rep.independent is False and rep.scheduled is False, rep
        return "independent=false scheduled=false when the identity is the writer's"

    if hasattr(adapter, "verify_externally"):
        @case("a party holding none of our credentials verifies the published heads")
        def _external_ok():
            ext = adapter.verify_externally()
            assert ext.get("verified") is True and ext.get("returncode") == 0, ext
            assert not ext.get("adapter_imported"), f"the verifier imported {ext['adapter_imported']}"
            return f"{ext['windows']} window(s) verified, 0 modules importing an adapter"

    if name in ("dryrun", "second"):
        @case("a break inserted into the middle is found by both stores")
        def _break():
            # in-process here: independence of the scan is what the case above proves; this one
            # proves the arithmetic - the same adapter instance's own chain recompute over the
            # tampered entries, plus (for the second store) a wholly separate file-based check.
            mid = trail[len(trail) // 2].seq
            adapter.tamper(mid, "TAMPERED-ACTION")
            scan_report = adapter.scan("actor:scanner-process", True).to_dict()
            report["tamper_seq"] = mid
            report["tamper_scan_chain_breaks"] = scan_report.get("chain_breaks")
            report["tamper_scan_first_break_at"] = scan_report.get("first_break_at")
            assert scan_report.get("chain_breaks") == 1, scan_report
            assert scan_report.get("first_break_at") == mid, scan_report
            extra = ""
            if hasattr(adapter, "verify_externally"):
                ext = adapter.verify_externally()
                report["tamper_external_verified"] = ext.get("verified")
                report["tamper_break_at_window"] = ext.get("break_at_window")
                assert ext.get("verified") is False, ext
                assert ext.get("break_at_window", -1) >= 0, ext
                extra = f"; the external verifier independently found window {ext['break_at_window']}"
            return f"tampered seq {mid}; the trail's own scan found it at seq {mid}{extra}"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["appended"] = adapter.appended
    report["refusals"] = adapter.refusals
    report["store_integrity"] = adapter.store_integrity()
    report["external_verifications"] = adapter.external_verifications()
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def product_scan(root: str) -> tuple:
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


def caller_lines() -> tuple:
    lines = open(os.path.join(HERE, "call.py")).read().splitlines()
    marks = [i for i, line in enumerate(lines) if MARKER in line]
    assert len(marks) == 1, f"expected one {MARKER} marker, found {len(marks)}"
    body = lines[marks[0] + 1:]
    end = next((i for i, line in enumerate(body) if line.startswith(GUARD)), len(body))
    counted = [line for line in body[:end] if line.strip() and not line.strip().startswith("#")]
    storage = [f"call.py:{n}: {line.strip()}" for n, line in enumerate(lines, 1)
              if re.search(r"""["'][^"']*\.jsonl["']""", line) and "kb/ledger" not in line]
    return len(counted), storage


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the audit-trail interface.")
    ap.add_argument("--adapter", action="append", choices=("dryrun", "live", "second"), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--break", dest="breakage", choices=BREAKAGES, default="",
                    help="the deliberate breakage: the run must fail")
    ap.add_argument("--product-scan", metavar="DIR")
    ap.add_argument("--caller-lines", action="store_true")
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
    for name in (args.adapter or ["dryrun"]):
        cases, report = run(name, args.breakage)
        reports.append(report)
        for status, label in cases:
            print(f"  {status:4} {label}")
            if status == "FAIL":
                failures += 1
        passed, total = report["cases_passed"], report["cases_run"]
        verdict = "PASSED" if passed == total else "FAILED"
        print(f"conformance {verdict}: {passed}/{total} on {name} ({report['adapter']})")

    if args.report:
        os.makedirs(os.path.dirname(args.report), exist_ok=True)
        json.dump(reports if len(reports) > 1 else reports[0], open(args.report, "w"), indent=1, sort_keys=True)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
