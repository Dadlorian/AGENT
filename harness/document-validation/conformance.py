#!/usr/bin/env python3
"""The conformance run every document-validation adapter must pass.

The same cases run against any binding: nothing here knows which adapter
answered. Used before and after a swap; the two reports are what proves the
interface held (build-adapter-pair, T-t9-06).

    python3 harness/document-validation/conformance.py --adapter dryrun --report out/dryrun.json
    python3 harness/document-validation/conformance.py --adapter second --report out/second.json
    python3 harness/document-validation/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import DIALECT_2020_12, DocumentValidationAdapter, Problem, ValidationRequest  # noqa: E402
from adapters.dryrun import DryRunAdapter                                                      # noqa: E402
from adapters.live import LiveSchemaStoreAdapter                                               # noqa: E402
from adapters.second import CompiledSchemaAdapter                                              # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = {"dryrun": DryRunAdapter, "live": LiveSchemaStoreAdapter, "second": CompiledSchemaAdapter}
# Product/library names belong in adapters/ and README.md's env table, nowhere else.
PRODUCTS = re.compile(r"(ajv|jsonschema_rs|jsonschema\b|fastjsonschema|python-jsonschema|hyperjump)", re.I)

ENTRY_SCHEMA = "examples/end-to-end/schemas/entry.schema.json"
SAMPLE_SCHEMA = "harness/document-validation/schemas/sample.schema.json"
ANYOF_SCHEMA = "harness/document-validation/schemas/anyof.schema.json"
BAD_DIALECT_SCHEMA = "harness/document-validation/schemas/bad-dialect.schema.json"
NO_DIALECT_SCHEMA = "harness/document-validation/schemas/no-dialect.schema.json"

MALFORMED_ENVELOPE = {"envelope_version": "0.1", "kind": "human"}   # missing 5 required fields
VALID_KIND = {"kind": "priced", "amount": 5, "tags": ["required-tag", "x"]}
INVALID_KIND = {"kind": "priced", "tags": ["x"]}                    # missing amount, no required-tag


def req(schema_uri, instance, dialect=DIALECT_2020_12) -> dict:
    return {"schema_uri": schema_uri, "dialect": dialect, "instance": instance}


def run(name: str) -> tuple[list, dict]:
    adapter = ADAPTERS[name]()
    report = {"binding": name, "adapter": adapter.entity, "execution_model": adapter.execution_model,
              "processes_required_for_progress": adapter.processes_required_for_progress,
              "declared_gaps": list(adapter.declared_gaps), "cases": [], "outcomes": {}}
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

    def record(fixture: str, outcome) -> None:
        errs = sorted((e.as_dict() for e in outcome.errors),
                     key=lambda d: (d["instance_location"], d["keyword_location"], d["message"]))
        report["outcomes"][fixture] = {"valid": outcome.valid, "dialect": outcome.dialect, "errors": errs}

    @case("a valid instance validates true")
    def _valid():
        outcome = adapter.validate(ValidationRequest.from_dict(req(SAMPLE_SCHEMA, VALID_KIND)))
        record("sample-valid", outcome)
        assert outcome.valid, outcome.errors
        assert outcome.dialect == DIALECT_2020_12, outcome.dialect
        return f"valid=True dialect={outcome.dialect}"

    @case("a malformed instance carries the failing pointer")
    def _malformed():
        outcome = adapter.validate(ValidationRequest.from_dict(req(ENTRY_SCHEMA, MALFORMED_ENVELOPE)))
        record("entry-malformed", outcome)
        assert not outcome.valid
        first = outcome.errors[0]
        assert first.instance_location.startswith("/"), first.instance_location
        assert first.keyword_location, "no keyword_location on the violation"
        return f"valid=False first_pointer={first.instance_location}"

    @case("every violation is reported in one pass, not only the first")
    def _one_pass():
        outcome = adapter.validate(ValidationRequest.from_dict(req(ENTRY_SCHEMA, MALFORMED_ENVELOPE)))
        assert len(outcome.errors) >= 2, f"only {len(outcome.errors)} violation(s) reported"
        return f"{len(outcome.errors)} violations in one pass"

    @case("if/then, contains and array items compose into one refusal")
    def _compose():
        outcome = adapter.validate(ValidationRequest.from_dict(req(SAMPLE_SCHEMA, INVALID_KIND)))
        record("sample-invalid", outcome)
        assert not outcome.valid
        locs = {e.instance_location for e in outcome.errors}
        assert "/amount" in locs and "/tags" in locs, locs
        return f"{len(outcome.errors)} violations at {sorted(locs)}"

    @case("anyOf: any matching branch is enough")
    def _anyof_pass():
        outcome = adapter.validate(ValidationRequest.from_dict(req(ANYOF_SCHEMA, "ok-yes")))
        record("anyof-valid", outcome)
        assert outcome.valid, outcome.errors
        return "matched one of two branches"

    @case("anyOf: matching no branch is refused")
    def _anyof_fail():
        outcome = adapter.validate(ValidationRequest.from_dict(req(ANYOF_SCHEMA, "nope")))
        record("anyof-invalid", outcome)
        assert not outcome.valid and outcome.errors[0].keyword_location.endswith("/anyOf")
        return outcome.errors[0].keyword_location

    @case("a schema declaring a dialect other than 2020-12 is refused")
    def _bad_dialect():
        try:
            adapter.validate(ValidationRequest.from_dict(req(BAD_DIALECT_SCHEMA, {})))
        except Problem as problem:
            assert problem.body["type"].endswith("dialect-unsupported") and problem.body["status"] == 422
            assert problem.body["declared_dialect"] != DIALECT_2020_12
            return f"{problem.body['type']} 422, declared={problem.body['declared_dialect']}"
        raise AssertionError("a draft-07 schema was accepted")

    @case("a schema declaring no dialect is refused, never assumed")
    def _no_dialect():
        try:
            adapter.validate(ValidationRequest.from_dict(req(NO_DIALECT_SCHEMA, {})))
        except Problem as problem:
            assert problem.body["type"].endswith("dialect-unsupported") and problem.body["declared_dialect"] is None
            return f"{problem.body['type']} 422, declared=None"
        raise AssertionError("a schema with no $schema was silently defaulted")

    @case("check_schema judges the schema itself, not an instance")
    def _check_schema():
        good = adapter.check_schema(SAMPLE_SCHEMA)
        bad = adapter.check_schema(BAD_DIALECT_SCHEMA)
        assert good.valid and not bad.valid
        return f"sample={good.valid} bad-dialect={bad.valid}"

    @case("a malformed request is refused before any schema is read")
    def _bad_request():
        reads_before, prepares_before = adapter.schema_reads, adapter.prepares
        try:
            ValidationRequest.from_dict({"schema_uri": SAMPLE_SCHEMA, "instance": {}, "vendor": "x"})
        except Problem as problem:
            assert problem.body["status"] == 400 and problem.body["type"].endswith("request-invalid")
            assert adapter.schema_reads == reads_before and adapter.prepares == prepares_before
            return f"{problem.body['type']} 400, nothing read"
        raise AssertionError("an out-of-vocabulary field and a missing dialect were accepted")

    @case("prepare is read once and reused across instances")
    def _prepare_once():
        adapter.validate(ValidationRequest.from_dict(req(SAMPLE_SCHEMA, VALID_KIND)))   # may warm the cache
        warm = adapter.prepares
        adapter.validate(ValidationRequest.from_dict(req(SAMPLE_SCHEMA, VALID_KIND)))   # must hit the cache
        after = adapter.prepares
        assert after == warm, f"prepares went {warm} -> {after} on a second call to an already-prepared schema"
        return f"prepares held at {after} across a second validate() of the same schema"

    @case("dialect_in_effect is read from the adapter, never assumed from the file")
    def _dialect_in_effect():
        handle = adapter.prepare(SAMPLE_SCHEMA)
        effective = adapter.dialect_in_effect(handle)
        assert effective == DIALECT_2020_12, effective
        report["dialect_in_effect"] = effective
        return effective

    @case("keywords_checked is reported and positive")
    def _keywords_checked():
        outcome = adapter.validate(ValidationRequest.from_dict(req(SAMPLE_SCHEMA, VALID_KIND)))
        assert outcome.keywords_checked > 0, outcome.keywords_checked
        return f"keywords_checked={outcome.keywords_checked}"

    @case("nothing names a validator library on the way out")
    def _no_leak():
        outcome = adapter.validate(ValidationRequest.from_dict(req(SAMPLE_SCHEMA, VALID_KIND)))
        doc = json.dumps(outcome.as_dict())
        assert not PRODUCTS.search(doc), f"a library name reached the caller: {PRODUCTS.search(doc).group(0)}"
        assert set(json.loads(doc)) == {"valid", "dialect", "schema_uri", "keywords_checked", "errors"}, \
            "the outcome grew or shed a field"
        return "outcome carries valid, dialect, schema_uri, keywords_checked, errors and nothing else"

    report["cases"] = [{"status": s, "case": c} for s, c in cases]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["prepares"] = adapter.prepares
    report["schema_reads"] = adapter.schema_reads
    report["refusals"] = adapter.refusals
    report["product_hits"] = product_scan(HERE)[0]
    return cases, report


def product_scan(root: str) -> tuple[int, list]:
    """Library names may live in adapters/ and README.md's env table. Nowhere else."""
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
    ap = argparse.ArgumentParser(description="Conformance run for the document-validation interface.")
    ap.add_argument("--adapter", action="append", choices=sorted(ADAPTERS), default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for library names outside adapters/")
    args = ap.parse_args(argv)

    if args.product_scan:
        count, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no validator library name outside adapters/")
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
              f"prepares={report['prepares']} schema_reads={report['schema_reads']} "
              f"dialect_in_effect={report.get('dialect_in_effect', 'none')} product_hits={report['product_hits']}")
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
