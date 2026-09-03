#!/usr/bin/env python3
"""The conformance run every packaging adapter must pass.

The same twelve cases run against any binding: nothing here knows which
adapter answered. dryrun and second publish the same three identities, so both
run all twelve; live reads this host's real .claude/skills/ tree, which has no
broken package to test refusal against, so three cases report skip there
rather than fail. Used before and after a swap; the two reports are what
proves the interface held (T-t7-05, T-t9-06).

    python3 harness/capability-packaging/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/capability-packaging/conformance.py --adapter second --report out/second.json
    python3 harness/capability-packaging/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import REQUIRED_RESIDENT, Problem, resolution_as_dict         # noqa: E402
from adapters.dryrun import DryRunAdapter                                    # noqa: E402
from adapters.live import LiveSkillFilesAdapter                              # noqa: E402
from adapters.second import RegistryAdapter                                  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveSkillFilesAdapter, "second": RegistryAdapter}
# Per-binding fixtures: dryrun and second publish the same three identities
# (one good, one missing a required field, one whose name has drifted from its
# identity), so the swap proof compares them directly. The live binding reads
# this host's real .claude/skills/ tree, which by construction carries no
# broken package, so its "missing"/"drifted" identities are None and the two
# cases that need them are skipped rather than failed for that binding alone.
_SHARED = {"good": "quickstart-parser", "trigger": "a request names a starter template",
          "reference": "references/schema.md", "missing": "broken-legacy-importer",
          "drifted": "drifted-directory", "absent": "no-such-package"}
FIXTURES = {"dryrun": _SHARED, "second": _SHARED,
           "live": {"good": "cap-capability-packaging", "trigger": "packaging a capability",
                    "reference": "references/packaging-shapes.md", "missing": None, "drifted": None,
                    "absent": "no-such-package-conformance-probe"}}
# Product names may live in adapters/ and in README.md's env table. Nowhere else.
PRODUCTS = re.compile(r"(litellm|openrouter|gemini|sglang|vllm|openai|anthropic|cursor|goose|langfuse)", re.I)


class Skip(Exception):
    """Raised when a case needs a fixture this binding's identity space has none of."""


def refused(fn, want_status: int, **kw) -> dict:
    try:
        fn(**kw)
    except Problem as problem:
        assert problem.body["status"] == want_status, problem.body
        return problem.body
    raise AssertionError("expected a refusal, got a result")


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    fx = FIXTURES.get(name, _SHARED)
    GOOD, TRIGGER, REF = fx["good"], fx["trigger"], fx["reference"]
    MISSING, DRIFTED, ABSENT = fx["missing"], fx["drifted"], fx["absent"]
    report = {"binding": name, "adapter": adapter.entity, "source": adapter.source,
              "declared_gaps": list(adapter.declared_gaps), "cases": []}
    cases: list[tuple[str, str]] = []

    def case(label):
        def wrap(fn):
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except Skip as exc:
                cases.append(("skip", f"{label}: {exc}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            return fn
        return wrap

    @case("discover one package by name")
    def _discover():
        entries = adapter.list_resident()
        found = [e for e in entries if e["identity"] == GOOD]
        assert found, f"{GOOD!r} was not listed among {[e['identity'] for e in entries]}"
        assert set(found[0]) == {"identity", "name", "description"}, found[0]
        report["resident_listed"] = len(entries)
        return f"{len(entries)} well-formed packages listed, {GOOD!r} among them"

    @case("a package missing a required field is invisible at discovery, not a crash")
    def _hidden():
        if MISSING is None:
            raise Skip("this binding's identity space has no broken fixture to hide")
        identities = {e["identity"] for e in adapter.list_resident()}
        assert MISSING not in identities, identities
        assert DRIFTED in identities, "a spec-conformant package must still be discoverable"
        return "the missing-field fixture did not reach the caller; the drifted one, spec-conformant, did"

    @case("resolve reads the two required resident fields")
    def _resolve():
        res = adapter.resolve(GOOD)
        assert res.resolved and res.tiers_loaded == ["resident"], res.tiers_loaded
        assert set(res.resident) == set(REQUIRED_RESIDENT), res.resident
        report["source"] = res.source
        report["digest_at_resolve"] = res.digest
        return f"tiers={res.tiers_loaded} source={res.source} digest={res.digest}"

    @case("load_body reaches the body tier only on activation")
    def _body():
        res = adapter.load_body(GOOD, TRIGGER)
        assert res.tiers_loaded == ["resident", "body"], res.tiers_loaded
        assert isinstance(res.body, str) and res.body, "body is empty"
        return f"tiers={res.tiers_loaded} body_len={len(res.body)}"

    @case("open_reference reaches the reference tier only when named")
    def _reference():
        res = adapter.open_reference(GOOD, REF)
        assert res.tiers_loaded == ["resident", "reference"], res.tiers_loaded
        assert isinstance(res.reference, str) and res.reference, "reference is empty"
        return f"tiers={res.tiers_loaded} reference_len={len(res.reference)}"

    @case("a reference path the package does not declare is refused")
    def _undeclared():
        body = refused(adapter.open_reference, 422, identity=GOOD, reference_path="references/__no-such-ref.md")
        assert body["type"].endswith("document-invalid"), body["type"]
        return f"{body['type']} 422"

    @case("an identity nothing publishes is a typed failure, not an exception leak")
    def _absent():
        before = adapter.resolutions
        body = refused(adapter.resolve, 422, identity=ABSENT)
        assert adapter.resolutions == before, "a miss was counted as a resolution"
        return f"{body['type']} 422, resolutions unchanged"

    @case("a package missing a required resident field is refused")
    def _missing_field():
        if MISSING is None:
            raise Skip("this binding's identity space has no broken fixture to refuse")
        body = refused(adapter.resolve, 422, identity=MISSING)
        assert body.get("missing") == ["description"], body
        return f"{body['type']} 422, missing={body['missing']}"

    @case("a declared name that does not match its identity still resolves; the spec's check "
          "and this repository's link check are kept separate")
    def _drifted():
        if DRIFTED is None:
            raise Skip("this binding's identity space has no drifted fixture to resolve")
        res = adapter.resolve(DRIFTED)
        assert res.resolved and res.resident["name"] != DRIFTED, res.resident
        return f"resolved={res.resolved} declared_name={res.resident['name']!r} != identity={DRIFTED!r}"

    @case("check_package reports a conformance outcome, never an exception, for a package "
          "that exists and one that does not")
    def _check():
        good = adapter.check_package(GOOD)
        gone = adapter.check_package(ABSENT)
        assert good == {"identity": GOOD, "package_exists": True, "required_field_missing": [],
                        "name_mismatch": False}, good
        assert gone == {"identity": ABSENT, "package_exists": False,
                        "required_field_missing": list(REQUIRED_RESIDENT), "name_mismatch": False}, gone
        return "an existing package and an absent one both reported without raising"

    @case("nothing names a path, a host or which binding answered on the way out")
    def _no_leak():
        # This checks the resolution payload, not the package's own prose (which may
        # legitimately name a real standard or its publisher). Product names in *code*
        # are the product_scan() check below, over .py/.sh files only.
        res = adapter.load_body(GOOD, TRIGGER)
        doc = json.dumps(resolution_as_dict(res))
        assert adapter.declared_marker not in doc, "the binding's own marker reached the caller"
        assert "/" not in res.identity and "\\" not in res.identity, \
            "identity looks like a path, not a name a caller could have written"
        assert set(json.loads(doc)) <= {"identity", "resolved", "source", "digest", "tiers_loaded",
                                        "resident", "body", "reference"}, "resolution grew a field"
        return "resolution carries identity, tiers and resident content, and nothing about where it lives"

    @case("the source marker is read from the response")
    def _marker():
        adapter.resolve(GOOD)
        assert adapter.observed_marker == adapter.declared_marker, \
            f"observed {adapter.observed_marker!r}, binding declares {adapter.declared_marker!r}"
        report["source_marker"] = adapter.observed_marker
        return f"{adapter.observed_marker} matches the binding"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_skipped"] = sum(1 for s, _ in cases if s == "skip")
    report["cases_run"] = sum(1 for s, _ in cases if s != "skip")
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["resolutions"] = adapter.resolutions
    report["refusals"] = adapter.refusals
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
    ap = argparse.ArgumentParser(description="Conformance run for the capability-packaging interface.")
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
        print(f"# binding {name} (source={report['source']})")
        for status, text in cases:
            print(f"  {status:4} {text}")
        failures += report["cases_run"] - report["cases_passed"] + report["product_hits"]
        print(f"  adapter={report['adapter']} cases={report['cases_run']} passed={report['cases_passed']} "
              f"skipped={report['cases_skipped']} resolutions={report['resolutions']} "
              f"refusals={report['refusals']} source_marker={report.get('source_marker', 'none')} "
              f"product_hits={report['product_hits']}")
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
