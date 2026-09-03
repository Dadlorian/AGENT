#!/usr/bin/env python3
"""The conformance run every tool-access adapter must pass.

The same seventeen cases run against any binding: nothing here knows which adapter
answered, and nothing here hard-codes a tool's arguments. Every call's arguments
are built from the input schema the server published at bind time, so a server
that requires a field this platform never heard of is still called correctly.
The two reports are what proves the interface held across a swap (T-t7-05,
T-t9-06).

Two kinds of assertion, and the difference is the point of this capability:

  cases        the shape of the contract. They can all pass over a server that
               publishes nothing, because there is nothing to get wrong.
  counts       tools_listed, schemas_checked, schemas_invalid, undeclared_refused.
               These are what has teeth over an endpoint recorded live and
               authenticated with zero tools registered (F-a6-03). A case that
               needed a tool and found none is reported as NOT EXERCISED, never
               as passing - the shape A7's green-gate finding takes here
               (F-a7-03).

    python3 harness/tool-access/conformance.py --adapter dryrun --report out/before.json
    python3 harness/tool-access/conformance.py --adapter second --report out/after.json
    python3 harness/tool-access/conformance.py --product-scan .
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from interface import (Binding, CallContext, Problem,  # noqa: E402
                       ToolDescriptor, result_as_dict)

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = ("dryrun", "live", "second")
# Product and transport names belong in adapters/ and in the env-var table of
# README.md, nowhere else.
PRODUCTS = re.compile(r"(mcp|modelcontextprotocol|anthropic|openai|claude|litellm|langfuse|temporal|"
                      r"firecracker|goose|github|slack)", re.I)


def load(name: str, cfg: dict):
    import importlib
    return importlib.import_module(f"adapters.{name}").Adapter(cfg)


def config() -> dict:
    with open(os.path.join(HERE, "binding.json")) as fh:
        return json.load(fh)


def ctx(step: str, run: str = "run-conformance", ceiling: int = 32, verdict: str = "allow",
        revision: str | None = None, cfg: dict | None = None) -> CallContext:
    cfg = cfg or config()
    return CallContext(correlation_id="cor-" + step, run_id=run, actor="agent:conformance",
                       idempotency_key="idem-" + step, protocol_revision=revision or cfg["revision"],
                       ceiling_calls=ceiling, policy_verdict=verdict)


# --- arguments built from the schema the server published -------------------
def synth(schema: dict) -> dict:
    """A valid argument object for this tool, read off its own input schema."""
    args = {}
    for name in schema.get("required", []):
        sub = schema["properties"][name]
        kind = sub["type"]
        if "enum" in sub:
            args[name] = sub["enum"][0]
        elif kind == "string":
            args[name] = ("arg-" + name).ljust(sub.get("minLength", 1), "x")
        elif kind in ("integer", "number"):
            args[name] = sub.get("minimum", 1)
        elif kind == "boolean":
            args[name] = True
        elif kind == "array":
            args[name] = []
        else:
            args[name] = {}
    return args


def broken(schema: dict) -> tuple[dict, str]:
    """Arguments the published schema must reject, and why."""
    args = synth(schema)
    required = schema.get("required", [])
    for name in required:                                  # a wrong type on a required field
        if schema["properties"][name]["type"] == "string":
            args[name] = 17
            return args, f"{name} sent as an integer where the schema declares a string"
    if required:                                           # or the required field missing
        args.pop(required[0])
        return args, f"required argument {required[0]} omitted"
    args["not-a-declared-argument"] = 1
    return args, "an argument the schema does not declare"


def run(name: str, cfg: dict) -> tuple[list, dict]:
    adapter = load(name, cfg)
    surface = list(cfg["declared_surface"])
    report = {"binding": name, "adapter": adapter.entity, "cases": [], **adapter.axes()}
    cases: list[tuple[str, str]] = []

    def case(label, needs_tool=False, needs_resource=False):
        def wrap(fn):
            absent = ("no tool" if needs_tool and not catalogue else
                      "no resource" if needs_resource and not (binding and binding.resources) else "")
            if absent:
                # Not a pass. A case that found nothing to exercise is the
                # green-gate finding in this capability's own shape (F-a7-03).
                cases.append(("NOT-EXERCISED", f"{label}: the server published {absent} to exercise"))
                return fn
            try:
                cases.append(("ok", f"{label}: {fn()}"))
            except AssertionError as exc:
                cases.append(("FAIL", f"{label}: {exc}"))
            except Problem as exc:
                cases.append(("FAIL", f"{label}: unexpected {exc.body['type']} - {exc.body['detail']}"))
            return fn
        return wrap

    def refused(fn, want: str) -> dict:
        before = adapter.dispatches
        try:
            fn()
        except Problem as problem:
            body = dict(problem.body)
            body["_dispatched"] = adapter.dispatches - before
            assert body["type"].endswith(want), f"expected {want}, got {body['type']}"
            return body
        raise AssertionError(f"expected {want}, nothing was refused")

    def role(kind: str) -> ToolDescriptor:
        want = adapter.conformance_roles[kind]
        tool = next((t for t in catalogue if t.name == want), None)
        assert tool is not None, f"the {kind} role names {want!r}, absent from the catalogue"
        return tool

    # --- bind: the one operation that must work over an empty server too ----
    binding: Binding | None = None
    catalogue: list = []
    try:
        binding = adapter.bind_server(cfg["server_ref"], surface, ctx("bind", cfg=cfg))
        catalogue = adapter.list_tools(binding)
        cases.append(("ok", f"a binding opens and the marker is read back from the server: "
                            f"{binding.server_marker!r}, {len(catalogue)} tools discovered"))
    except Problem as exc:
        cases.append(("FAIL", f"a binding opens: {exc.body['type']} - {exc.body['detail']}"))

    if binding is not None:
        @case("the catalogue is data with a schema on every entry", needs_tool=True)
        def _catalogue():
            for tool in catalogue:
                assert tool.name and tool.effect in ("read_only", "mutating", "unknown"), tool.name
                assert isinstance(tool.input_schema, dict) and tool.input_schema.get("type") == "object", \
                    f"{tool.name} publishes no usable input schema"
            assert binding.schemas_checked == len(catalogue), "a schema was not checked at bind"
            assert binding.schemas_invalid == 0, f"{binding.schemas_invalid} published schemas are invalid"
            return (f"{len(catalogue)} tools, {binding.schemas_checked} schemas checked against the "
                    f"meta-schema, {binding.schemas_invalid} invalid")

        @case("a declared name the server does not publish is refused before any call")
        def _unresolved():
            probe = adapter.bind_server(cfg["server_ref"], surface + ["never.published"],
                                        ctx("probe", cfg=cfg))
            assert "never.published" in probe.unresolved, \
                "a declared name absent from the catalogue was not recorded at bind"
            body = refused(lambda: adapter.begin_call(probe, "never.published", {},
                                                      ctx("unres", run="run-unres", cfg=cfg)),
                           "tool-unknown")
            assert body["status"] == 404 and body["_dispatched"] == 0, body
            report["unresolved_at_bind"] = list(probe.unresolved)
            return f"unresolved at bind {list(probe.unresolved)} -> {body['type']} 404, dispatched=0"

        @case("a descriptor with no input schema never enters a catalogue")
        def _meta_schema():
            vectors = [({"name": "t", "effect": "read_only"}, "publishes no input schema"),
                       ({"name": "t", "effect": "read_only", "input_schema": {"type": "array"}},
                        "must declare type object"),
                       ({"name": "", "effect": "read_only", "input_schema": {"type": "object"}},
                        "non-empty name"),
                       ({"name": "t", "effect": "sideways", "input_schema": {"type": "object"}},
                        "declares effect")]
            for doc, want in vectors:
                try:
                    ToolDescriptor.from_dict(doc)
                except Problem as exc:
                    assert want in exc.body["detail"], f"{doc} refused for the wrong reason"
                else:
                    raise AssertionError(f"{doc} entered a catalogue")
            return f"{len(vectors)} vectors refused, from a table, with no server reachable"

        @case("one call, with arguments built from the schema the server published", needs_tool=True)
        def _happy():
            tool = role("read_only")
            args = synth(tool.input_schema)
            adapter.check_arguments(tool, args)
            result = adapter.call_tool(binding, tool.name, args, ctx("happy", run="run-happy", cfg=cfg))
            assert result.ok, f"ok false: {result.problem}"
            assert result.content, "a successful result carried no content"
            assert result.correlation_id == "cor-happy", "the correlation id was not stamped on the way back"
            report["happy_tool"] = tool.name
            report["happy_args"] = sorted(args)
            return f"{tool.name}({sorted(args)}) -> ok, correlation stamped both ways"

        @case("arguments the published schema rejects never leave the platform", needs_tool=True)
        def _bad_args():
            tool = role("read_only")
            args, why = broken(tool.input_schema)
            body = refused(lambda: adapter.call_tool(binding, tool.name, args,
                                                     ctx("badargs", run="run-bad", cfg=cfg)),
                           "arguments-invalid")
            assert body["status"] == 422 and body["_dispatched"] == 0, body
            return f"{why} -> {body['type']} 422, dispatched=0"

        @case("a tool outside the declared surface is refused before dispatch", needs_tool=True)
        def _undeclared():
            extra = next((t for t in catalogue if t.name not in surface), None)
            assert extra is not None, "the server publishes nothing outside the declared surface"
            body = refused(lambda: adapter.call_tool(binding, extra.name, synth(extra.input_schema),
                                                     ctx("undeclared", run="run-und", cfg=cfg)),
                           "policy-denied")
            assert body["status"] == 403 and body["_dispatched"] == 0, body
            assert body["rule_id"] == "declared-surface", body
            assert body["enforcement_point"] == "platform-pre-dispatch", body
            report["undeclared_tool"] = extra.name
            return f"{extra.name} -> {body['type']} 403 at {body['enforcement_point']}, dispatched=0"

        @case("a tool that fails inside a successful envelope comes back typed", needs_tool=True)
        def _in_band():
            tool = role("in_band_failure")
            result = adapter.call_tool(binding, tool.name, synth(tool.input_schema),
                                       ctx("inband", run="run-inband", cfg=cfg))
            assert result.ok is False, "the tool's own failure was reported as success"
            assert result.problem and result.problem["type"].endswith("tool-failed"), result.problem
            assert result.problem["channel"] == "tool-result", "the failure channel was not recorded"
            assert result.content == [], "a failed call carried content as well as a problem"
            return f"{tool.name} -> ok=false, {result.problem['type']} 502 from the tool-result channel"

        @case("a read is not a tool call", needs_resource=True)
        def _resource():
            calls, reads = adapter.tool_calls, adapter.resource_reads
            got = adapter.read_resource(binding, binding.resources[0], ctx("read", cfg=cfg))
            assert got.content, "a read returned nothing"
            assert adapter.tool_calls == calls, "a read was counted as a tool call"
            assert adapter.resource_reads == reads + 1, "a read was not counted at all"
            return f"{got.uri} read; tool_calls unchanged at {calls}, resource_reads {reads} -> {reads + 1}"

        @case("a call is cancelled while it is still in flight", needs_tool=True)
        def _cancel():
            tool = role("slow")
            handle = adapter.begin_call(binding, tool.name, synth(tool.input_schema),
                                        ctx("cancel", run="run-cancel", cfg=cfg))
            in_flight = handle.state == "in_flight"
            ack = adapter.cancel(handle)
            assert ack.outcome in ("stopped", "recorded"), ack.outcome
            assert ack.outcome == adapter.cancellation, \
                f"the binding declares cancellation {adapter.cancellation!r} and the ack said {ack.outcome!r}"
            assert ack.detail, "a cancel must say what happened"
            body = refused(lambda: adapter.claim(handle), "call-cancelled")
            assert body["status"] == 409, body
            report["cancel_outcome"] = ack.outcome
            report["cancel_in_flight"] = in_flight
            return f"in_flight={in_flight} -> {ack.outcome}, effect_owed={ack.effect_owed}, claim 409"

        @case("the same key with the same arguments is not a second call", needs_tool=True)
        def _idempotent():
            tool = role("mutating")
            args = synth(tool.input_schema)
            key = ctx("replay", run="run-replay", cfg=cfg)
            first = adapter.begin_call(binding, tool.name, args, key)
            before = adapter.dispatches
            again = adapter.begin_call(binding, tool.name, args, key)
            assert again.call_id == first.call_id, "a replay produced a different call"
            assert adapter.dispatches == before, "a replay reached the server"
            other = dict(args)
            other[sorted(args)[0]] = "different-" + str(other[sorted(args)[0]])
            body = refused(lambda: adapter.begin_call(binding, tool.name, other, key),
                           "idempotency-conflict")
            assert body["status"] == 409 and body["_dispatched"] == 0, body
            return "same arguments replayed for free, different arguments is 409"

        @case("a call over the ceiling is refused before dispatch", needs_tool=True)
        def _ceiling():
            tool = role("read_only")
            args = synth(tool.input_schema)
            adapter.call_tool(binding, tool.name, args, ctx("cap1", run="run-cap", ceiling=1, cfg=cfg))
            body = refused(lambda: adapter.call_tool(binding, tool.name, args,
                                                     ctx("cap2", run="run-cap", ceiling=1, cfg=cfg)),
                           "budget-exhausted")
            assert body["status"] == 402 and body["_dispatched"] == 0, body
            assert body["enforcement_point"] == "platform-pre-dispatch", body
            return f"the second call of a 1-call run -> {body['type']} 402, dispatched=0"

        @case("a policy verdict narrows the surface, it does not widen it", needs_tool=True)
        def _policy():
            mutating = role("mutating")
            body = refused(lambda: adapter.call_tool(binding, mutating.name, synth(mutating.input_schema),
                                                     ctx("ro1", run="run-ro", verdict="allow-read-only",
                                                         cfg=cfg)),
                           "policy-denied")
            assert body["rule_id"] == "read-only-verdict" and body["_dispatched"] == 0, body
            readonly = role("read_only")
            still = adapter.call_tool(binding, readonly.name, synth(readonly.input_schema),
                                      ctx("ro2", run="run-ro", verdict="allow-read-only", cfg=cfg))
            assert still.ok, "a read-only tool was refused under a read-only verdict"
            return f"{mutating.name} refused 403, {readonly.name} still served"

        @case("the protocol revision is declared per call and refused per call")
        def _revision():
            body = refused(lambda: adapter.begin_call(binding, surface[0], {},
                                                      ctx("rev", run="run-rev", revision="1999-01-01",
                                                          cfg=cfg)),
                           "protocol-unsupported")
            assert body["status"] == 400 and body["_dispatched"] == 0, body
            assert body["declared_revision"] == "1999-01-01", body
            if catalogue:                       # the binding is untouched by that refusal
                tool = role("read_only")
                assert adapter.call_tool(binding, tool.name, synth(tool.input_schema),
                                         ctx("revok", run="run-rev", cfg=cfg)).ok, "the binding was lost"
            return f"{body['type']} 400 on that call; served revisions {body['served_revisions']}"

        @case("health counts registered tools rather than answering green")
        def _health():
            health = adapter.health(binding)
            assert health.status in ("serving", "empty", "unreachable"), health.status
            assert health.status != "green", "the vocabulary contains no green"
            assert health.tools_listed == len(catalogue), "health disagrees with the catalogue"
            assert (health.status == "serving") == (health.tools_listed > 0), \
                "a server with no tools reported as serving"
            assert health.schemas_checked == health.tools_listed, "health did not count the schemas"
            report["health_status"] = health.status
            report["health_detail"] = health.detail
            return (f"status={health.status} tools_listed={health.tools_listed} "
                    f"schemas_checked={health.schemas_checked} schemas_invalid={health.schemas_invalid}")

        @case("the catalogue is read at every bind, not compiled in")
        def _reread():
            again = adapter.bind_server(cfg["server_ref"], surface, ctx("rebind", cfg=cfg))
            same = again.catalogue_digest == binding.catalogue_digest
            assert same == (adapter.catalogue_stability == "frozen"), \
                (f"the binding declares catalogue_stability {adapter.catalogue_stability!r} and a second "
                 f"bind {'matched' if same else 'differed'}")
            assert list(again.declared_surface) == surface, "the declared surface did not survive a re-bind"
            report["catalogue_digest_first"] = binding.catalogue_digest[:23]
            report["catalogue_digest_second"] = again.catalogue_digest[:23]
            report["tools_listed_second_bind"] = len(again.catalogue)
            return (f"{len(catalogue)} tools then {len(again.catalogue)}; digests "
                    f"{'match' if same else 'differ'}, as {adapter.catalogue_stability} declares")

        @case("nothing names a server, a product or a transport on the way out", needs_tool=True)
        def _no_leak():
            tool = role("read_only")
            result = adapter.call_tool(binding, tool.name, synth(tool.input_schema),
                                       ctx("leak", run="run-leak", cfg=cfg))
            doc = json.dumps(result_as_dict(result))
            found = PRODUCTS.search(doc)
            assert not found, f"a product name reached the caller: {found.group(0) if found else ''}"
            assert set(json.loads(doc)) <= {"tool", "ok", "content", "correlation_id", "problem"}, \
                "the result grew a field"
            assert adapter.observed_marker not in doc, "the server marker reached the caller"
            return "the result carries a tool name, ok, content and a correlation id, and nothing else"

    # --- the counts, which is what has teeth over an empty server -----------
    counts: list[tuple[str, str]] = []

    def count(label, ok, detail):
        counts.append(("ok" if ok else "FAIL", f"{label}: {detail}"))

    listed = len(catalogue)
    checked = binding.schemas_checked if binding else 0
    invalid = binding.schemas_invalid if binding else 0
    count("tools_listed > 0", listed > 0, f"tools_listed={listed}")
    count("schemas_checked == tools_listed", checked == listed, f"schemas_checked={checked}")
    count("schemas_invalid == 0", invalid == 0, f"schemas_invalid={invalid}")
    count("undeclared_refused >= 1", adapter.undeclared_refused >= 1,
          f"undeclared_refused={adapter.undeclared_refused}")
    count("the server marker was read back", bool(adapter.observed_marker),
          f"server_marker={adapter.observed_marker or 'none'}")
    unresolved = list(binding.unresolved) if binding else surface
    count("the declared surface resolved at bind", not unresolved,
          f"surface_unresolved={unresolved}")

    report["cases"] = [{"status": s, "case": c} for s, c in cases] + \
                      [{"status": s, "count": c} for s, c in counts]
    report["cases_run"] = len(cases)
    report["cases_passed"] = sum(1 for s, _ in cases if s == "ok")
    report["cases_not_exercised"] = sum(1 for s, _ in cases if s == "NOT-EXERCISED")
    report["conformance_failures"] = sum(1 for s, _ in cases if s == "FAIL")
    report["count_failures"] = sum(1 for s, _ in counts if s == "FAIL")
    report.update({"tools_listed": listed, "schemas_checked": checked, "schemas_invalid": invalid,
                   "undeclared_refused": adapter.undeclared_refused, "tool_calls": adapter.tool_calls,
                   "resource_reads": adapter.resource_reads, "refusals": adapter.refusals,
                   "server_marker_observed": adapter.observed_marker,
                   "server_marker_declared": adapter.server_marker,
                   "surface_unresolved": unresolved,
                   "catalogue_digest": binding.catalogue_digest if binding else "",
                   "declared_surface": surface,
                   "product_hits": product_scan(HERE)[0]})
    return cases + counts, report


def product_scan(root: str) -> tuple[int, list]:
    """Product and transport names may live in adapters/ and in README's env
    table. Nowhere else. Code is what is scanned (.py and .sh)."""
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("adapters", "out", "__pycache__")]
        for fname in sorted(filenames):
            if not fname.endswith((".py", ".sh")):
                continue
            path = os.path.join(dirpath, fname)
            for i, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
                found = PRODUCTS.search(line)
                if found and "PRODUCTS = " not in line and not line.lstrip().startswith("r\""):
                    hits.append(f"{os.path.relpath(path, root)}:{i}: {found.group(0)}")
    return len(hits), hits


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Conformance run for the tool-access interface.")
    ap.add_argument("--adapter", action="append", choices=ADAPTERS, default=[])
    ap.add_argument("--report", help="write the report JSON here")
    ap.add_argument("--product-scan", metavar="DIR", help="scan a tree for product names outside adapters/")
    args = ap.parse_args(argv)

    if args.product_scan:
        found, hits = product_scan(os.path.abspath(args.product_scan))
        print("\n".join(hits) or "no product name outside adapters/")
        print(f"product_hits={found}")
        return 1 if found else 0

    cfg = config()
    reports, failures = [], 0
    for name in args.adapter or ["dryrun"]:
        rows, report = run(name, cfg)
        print(f"# binding {name} ({report['catalogue_authority']}, {report['call_locality']})")
        for status, text in rows:
            print(f"  {status:14} {text}")
        failures += report["conformance_failures"] + report["count_failures"] + report["product_hits"]
        marker = "match" if report["server_marker_observed"] == report["server_marker_declared"] \
            else "read:" + (report["server_marker_observed"] or "none")
        print(f"  adapter={report['adapter']} server_marker={marker} "
              f"conformance_failures={report['conformance_failures']} "
              f"tools_listed={report['tools_listed']} schemas_checked={report['schemas_checked']} "
              f"schemas_invalid={report['schemas_invalid']} "
              f"undeclared_refused={report['undeclared_refused']} "
              f"cases_not_exercised={report['cases_not_exercised']} "
              f"product_hits={report['product_hits']}")
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
