#!/usr/bin/env python3
"""The minimal call: discover the callable tools, check one call's arguments
against the tool's declared input schema, make the call, cancel a second call
mid-flight, and read a health check that counts registered tools.

    ADAPTER=dryrun|second|live python3 harness/tool-access/call.py

Two halves. Everything above the CALLER CODE marker is the platform: it stamps
the correlation id, the run id, the actor and delegation chain, the budget
ceiling, a per-call idempotency key and the protocol revision this call declares,
without the caller asking for any of them (F-b4-01). Everything below the marker
is what a caller writes: under 40 lines, naming no server, no transport and no
product.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from interface import CallContext, Problem, result_as_dict          # noqa: E402


# --- platform side: applied, not requested -----------------------------------
def config(path=None) -> dict:
    with open(path or os.environ.get("BINDING", os.path.join(HERE, "binding.json"))) as fh:
        return json.load(fh)


def adapter(cfg: dict):
    """Selecting a tool server is configuration. There is no code path that
    chooses one, and nothing downstream branches on which answered."""
    name = os.environ.get("ADAPTER", cfg.get("adapter", "dryrun"))
    return importlib.import_module(f"adapters.{name}").Adapter(cfg), name


def envelope(cfg: dict, kind: str, summary: str) -> dict:
    """cap-consumption's entry envelope. The caller supplies intent; the five
    stamped members are applied here (T-t6-02)."""
    actor = os.environ.get("ACTOR", cfg.get("actor", "user:corey"))
    run_id = "run-" + uuid.uuid4().hex[:8]
    return {"envelope_version": "0.1", "kind": kind,
            "actor": {"subject": actor,
                      "delegation_chain": [{"actor": actor, "obtained_via": "direct"}]},
            "intent": {"workflow_ref": "harness/tool-access", "summary": summary},
            "correlation": {"run_id": run_id, "correlation_id": "cor-" + uuid.uuid4().hex[:8]},
            "budget": {"ceiling_calls": int(os.environ.get("CEILING_CALLS",
                                                           cfg["budget"]["ceiling_calls"]))},
            "idempotency_key": "idem-" + uuid.uuid4().hex[:12],
            "payload": {"declared_surface": cfg["declared_surface"]}}


def stamper(env: dict, cfg: dict):
    """One context per call. The idempotency key is derived per step, so two
    different calls under one envelope are two calls and a repeat is a replay
    (F-b4-08). The protocol revision is declared per call, not agreed at bind."""
    revision = os.environ.get("REVISION", cfg["revision"])
    verdict = os.environ.get("POLICY_VERDICT", "allow")

    def stamp(step: str) -> CallContext:
        key = env["idempotency_key"] + "-" + hashlib.sha256(step.encode()).hexdigest()[:8]
        return CallContext(correlation_id=env["correlation"]["correlation_id"],
                           run_id=env["correlation"]["run_id"], actor=env["actor"]["subject"],
                           idempotency_key=key, protocol_revision=revision,
                           ceiling_calls=env["budget"]["ceiling_calls"], policy_verdict=verdict)
    return stamp


def table(rows) -> None:
    width = max(len(r[0]) for r in rows)
    for key, value in rows:
        print(f"  {key.ljust(width)}  {value}")


def show(out: dict) -> int:
    """Presentation, so the caller region below is calls and results only."""
    env, health, result, ack = out["envelope"], out["health"], out["result"], out["cancel"]
    print(f"TOOL CALL  correlation={env['correlation']['correlation_id']}  "
          f"actor={env['actor']['subject']}  revision={out['binding'].revision}")
    table([
        ("adapter selected (configuration)", out["adapter_selected"]),
        ("server marker (read back from the server)", out["binding"].server_marker),
        ("tools discovered at bind", f"{len(out['catalogue'])}: {[t.name for t in out['catalogue']]}"),
        ("declared surface for this unit", list(out["binding"].declared_surface)),
        ("arguments checked against", f"{out['tool'].name} input_schema "
                                      f"(required {out['tool'].input_schema.get('required', [])})"),
        ("call result", f"ok={result.ok} content={json.dumps(result.content)[:70]}"),
        ("cancel mid-flight", f"{ack.outcome}, effect_owed={ack.effect_owed}"),
        ("health status", f"{health.status} (tools_listed={health.tools_listed}, "
                          f"schemas_checked={health.schemas_checked}, "
                          f"schemas_invalid={health.schemas_invalid})"),
        ("health detail", health.detail),
    ])
    print("\n" + json.dumps(result_as_dict(result), indent=2)[:400])
    return 0 if health.status == "serving" else 3


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--binding", help="configuration file (default binding.json)")
    args = ap.parse_args(argv)
    try:
        out = minimal_call(config(args.binding))
    except Problem as problem:
        print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
        return 2
    return show(out)


# --------------------------------------------------------------------------
# >>> CALLER CODE : everything below this line is what a caller writes.
# Counted by harness/caller_lines.py, the one method all five harnesses use.
# --------------------------------------------------------------------------
def minimal_call(cfg):
    ad, name = adapter(cfg)                                       # ADAPTER=dryrun|second|live
    env = envelope(cfg, os.environ.get("ENTRY_KIND", "human"), "read one note, cancel one scan")
    stamp = stamper(env, cfg)
    binding = ad.bind_server(cfg["server_ref"], cfg["declared_surface"], stamp("bind"))
    catalogue = ad.list_tools(binding)                            # discovered, never compiled in
    call, cancel = cfg["call"], cfg["cancel"]
    tool = ad.find(binding, call["tool"])
    ad.check_arguments(tool, call["arguments"])                   # against the published schema
    result = ad.call_tool(binding, tool.name, call["arguments"], stamp("call"))
    scan = ad.begin_call(binding, cancel["tool"], cancel["arguments"], stamp("scan"))
    ack = ad.cancel(scan)                                         # while it is still in flight
    health = ad.health(binding)                                   # counts tools; there is no green
    return {"adapter_selected": name, "envelope": env, "binding": binding, "catalogue": catalogue,
            "tool": tool, "result": result, "cancel": ack, "health": health}


if __name__ == "__main__":
    sys.exit(main())
