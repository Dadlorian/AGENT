#!/usr/bin/env python3
"""Check that every cap- and seam- skill's adapters[] forms a real pair.

Usage: python3 tools/check_adapter_pairs.py --skills .claude/skills

For every skill directory whose name starts with "cap-" or "seam-" and whose skill.json
carries a non-empty adapters list, asserts: exactly one adapter has role "today"; at least
one adapter has role "second"; every adapter carries a non-empty differs_in_execution_model
(a list of {axis, today_value, second_value} entries, each naming a real axis) somewhere on
the pair; and at least one axis entry has today_value != second_value between a "today" and
a "second" adapter.

Prints "pairs_checked=N, single_adapter=N, empty_axis=N, same_model_pairs=N" and, on
failure, names the offending skills. Exits 0 only when pairs_checked > 0 and every count
is 0.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def check_skill(skill_json: dict) -> dict:
    adapters = skill_json.get("adapters") or []
    todays = [a for a in adapters if a.get("role") == "today"]
    seconds = [a for a in adapters if a.get("role") == "second"]
    single_adapter = len(todays) != 1 or len(seconds) < 1

    def axes_of(a: dict) -> list:
        return a.get("differs_in_execution_model") or []

    empty_axis = any(
        not axes_of(a) or not all(str(ax.get("axis") or "").strip() for ax in axes_of(a))
        for a in adapters
    )

    same_model_pairs = True
    if not empty_axis:
        for t in todays:
            t_vals = {ax["axis"]: ax.get("today_value") for ax in axes_of(t)}
            for s in seconds:
                s_vals = {ax["axis"]: ax.get("second_value") for ax in axes_of(s)}
                shared = set(t_vals) & set(s_vals)
                if shared and any(t_vals[ax] != s_vals[ax] for ax in shared):
                    same_model_pairs = False

    return {
        "single_adapter": single_adapter,
        "empty_axis": empty_axis,
        "same_model_pairs": same_model_pairs,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", required=True)
    args = ap.parse_args(argv)
    root = Path(args.skills)

    pairs_checked = 0
    single_adapter = empty_axis = same_model_pairs = 0
    offenders: dict[str, list[str]] = {"single_adapter": [], "empty_axis": [], "same_model_pairs": []}

    for d in sorted(root.iterdir()):
        if not d.is_dir() or not (d.name.startswith("cap-") or d.name.startswith("seam-")):
            continue
        sj = d / "skill.json"
        if not sj.is_file():
            continue
        sk = json.loads(sj.read_text())
        if not sk.get("adapters"):
            continue
        pairs_checked += 1
        result = check_skill(sk)
        for k, bad in result.items():
            if bad:
                offenders[k].append(d.name)
        single_adapter += int(result["single_adapter"])
        empty_axis += int(result["empty_axis"])
        same_model_pairs += int(result["same_model_pairs"])

    print(
        f"pairs_checked={pairs_checked}, single_adapter={single_adapter}, "
        f"empty_axis={empty_axis}, same_model_pairs={same_model_pairs}"
    )
    for k, names in offenders.items():
        if names:
            print(f"{k}: {names}")

    ok = pairs_checked > 0 and single_adapter == 0 and empty_axis == 0 and same_model_pairs == 0
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
