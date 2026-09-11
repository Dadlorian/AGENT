#!/usr/bin/env python3
"""Every declared knob must change something, or say it does not. The lesson, executed.

  python3 tools/inert_check.py              check every area under examples/reference/
  python3 tools/inert_check.py <area>       check one example area
  python3 tools/inert_check.py --selftest   plant an inert knob, prove this tool sees it

WHY THIS EXISTS
---------------
state/lessons.jsonl has carried the rule since 2026-09-04, ceremony 75:

  "Inert declarations, widened: ... each must appear on the deciding side of a branch, with a
   check that removes or changes it and asserts a different record or a typed refusal ... A
   declaration whose deletion changes nothing is decoration however precisely it is documented."

It recurred anyway on 2026-09-11 in a brand-new area: `Unit.profile` was declared, documented and
cited, and could not reach the step that selects a bundle -- so setting it changed nothing. Caught
by an isolated reviewer, not by any of this repo's gates, because the rule was prose a reviewer had
to remember. Prose does not run. This does.

WHAT IT CHECKS
--------------
For every field of every input dataclass an area's `interface.py` declares, the area's `cards.json`
must carry a `knobs` entry, and that entry must be one of two honest things:

  varied   two values are given; the tool builds two otherwise-identical calls, runs both through
           every runnable adapter, and requires the observable result to DIFFER. A knob that
           changes nothing fails here.
  carried  the field is declared to be carried and not consumed, with a `why`. The tool then
           requires it to change NOTHING -- so a field quietly wired up later stops matching its
           own declaration and is flagged too.

A field absent from `knobs` is an error. That is the part that cannot be gamed by omission, which
is how the original defect survived eighteen author-written assertions.

VERDICTS ARE TYPED
------------------
  inert       declared as varied, changed nothing                        BLOCKS
  undeclared  a field with no knobs entry                                BLOCKS
  live        declared as varied, and the observable differs             ok
  carried     declared as carried-and-not-consumed, and nothing differs  ok
  woke        declared carried, but it DOES change something             BLOCKS -- the declaration is now false
"""
from __future__ import annotations

import dataclasses
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCKING = ("inert", "undeclared", "woke")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def observe(area: Path, adapter: str, unit_kw: dict, unpack_kw: dict) -> tuple:
    """One full call through the contract, reduced to what a caller can actually see."""
    sys.path.insert(0, str(area))
    try:
        iface = load_module(area / "interface.py", "interface")
        sandbox = iface.load(adapter)
        bundle = sandbox.unpack("registry.example/agent-base:2026-09", **unpack_kw)
        unit = iface.Unit(**unit_kw)
        handle = sandbox.run(bundle, unit)
        running = sandbox.inspect(handle)
        final = sandbox.stop(handle)
        return (handle, bundle.image, bundle.digest, getattr(bundle, "profile", None),
                running.status, running.trace, running.warm, final.status, final.trace)
    finally:
        sys.path.remove(str(area))
        for m in ("interface", "adapters.dryrun", "adapters.second", "adapters.live", "adapters"):
            sys.modules.pop(m, None)


def declared_fields(area: Path) -> dict:
    sys.path.insert(0, str(area))
    try:
        iface = load_module(area / "interface.py", "interface")
        out = {}
        for cls_name in ("Unit",):
            cls = getattr(iface, cls_name, None)
            if cls and dataclasses.is_dataclass(cls):
                for f in dataclasses.fields(cls):
                    out[f"{cls_name}.{f.name}"] = f
        return out
    finally:
        sys.path.remove(str(area))
        sys.modules.pop("interface", None)


def check(area: Path, knobs_override=None) -> list:
    cards = json.loads((area / "cards.json").read_text())
    knobs = knobs_override if knobs_override is not None else (cards.get("knobs") or [])
    by_field = {k.get("field"): k for k in knobs}
    fields = declared_fields(area)
    adapters = cards.get("runnable_adapters") or ["dryrun", "second"]
    findings = []

    for name in sorted(fields):
        knob = by_field.get(name)
        if not knob:
            findings.append({"field": name, "verdict": "undeclared",
                             "what": "no `knobs` entry in cards.json; a declaration nothing "
                                     "vouches for is how an inert field survives review"})
            continue
        attr = name.split(".", 1)[1]
        base = {"unit_id": "k1", "intent": "inert-check"}
        differs = []
        for adapter in adapters:
            a_unit, b_unit = dict(base), dict(base)
            a_up, b_up = {}, {}
            a_unit[attr], b_unit[attr] = knob.get("a", "A"), knob.get("b", "B")
            if knob.get("reaches_unpack"):
                a_up[attr], b_up[attr] = a_unit[attr], b_unit[attr]
            differs.append(observe(area, adapter, a_unit, a_up)
                           != observe(area, adapter, b_unit, b_up))
        moved = any(differs)
        if knob.get("carried"):
            findings.append({"field": name, "verdict": "woke" if moved else "carried",
                             "what": knob.get("why", ""), "adapters": adapters})
        else:
            findings.append({"field": name, "verdict": "live" if moved else "inert",
                             "what": knob.get("why", "declared as varied"), "adapters": adapters})

    for f in by_field:
        if f not in fields:
            findings.append({"field": f, "verdict": "undeclared",
                             "what": "knobs names a field the interface does not declare"})
    return findings


def report(area: Path, findings: list) -> int:
    for f in sorted(findings, key=lambda f: (f["verdict"] not in BLOCKING, f["field"])):
        mark = "BLOCK" if f["verdict"] in BLOCKING else "ok"
        print(f"  {mark:5} {f['field']:20} {f['verdict']:11} {f['what'][:64]}")
    blocking = [f for f in findings if f["verdict"] in BLOCKING]
    dist = {}
    for f in findings:
        dist[f["verdict"]] = dist.get(f["verdict"], 0) + 1
    print(f"\n{area.name}: {len(findings)} declared field(s) - "
          + "  ".join(f"{v} {k}" for k, v in sorted(dist.items(), key=lambda x: -x[1])))
    print(f"{len(blocking)} need a person.")
    return 1 if blocking else 0


def selftest() -> int:
    """Plant an inert knob and prove the tool sees it. A criterion nothing can fail is not one."""
    area = ROOT / "examples/reference/3-core-agent"
    real = json.loads((area / "cards.json").read_text()).get("knobs") or []
    clean = [f for f in check(area, real) if f["verdict"] in BLOCKING]
    planted = [dict(k) for k in real]
    for k in planted:
        if k["field"].endswith(".profile"):
            k.pop("reaches_unpack", None)      # exactly the h-10 defect: profile cannot reach unpack
    dirty = [f for f in check(area, planted) if f["verdict"] in BLOCKING]
    print("self-test - re-plant the h-10 defect: profile no longer reaches bundle selection")
    print(f"  before planting: {len(clean)} blocking finding(s)")
    print(f"  after planting:  {len(dirty)} blocking finding(s) "
          + ", ".join(f"{f['field']} {f['verdict']}" for f in dirty))
    ok = not clean and any(f["verdict"] == "inert" for f in dirty)
    print("PASS - the check fails on an inert declaration and is green without one" if ok
          else "FAIL - the check did not catch the planted inert declaration")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    if not args:
        areas = sorted(p.parent for p in (ROOT / "examples/reference").glob("*/cards.json"))
        if not areas:
            print("no example area declares knobs yet; nothing to check")
            return 0
        worst = 0
        for a in areas:
            worst = max(worst, report(a, check(a)))
        return worst
    area = Path(args[0])
    if not area.is_absolute():
        area = ROOT / area
    return report(area, check(area))


if __name__ == "__main__":
    sys.exit(main())
