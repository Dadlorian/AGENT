#!/usr/bin/env python3
"""The contract role: a manifest of content-addressed entries, hashed before
the cell starts.

Four roles cross the boundary of a unit (docs/consumption/unit-design.md,
"The four roles"): contract, source, work, output. This module builds the
first one. It is a manifest rather than a directory listing so that three
things are data instead of habit: the load tier per entry, the token count per
entry (which is what a pre-flight card reads), and the split between the
stable prefix - identical bytes on every attempt of the unit - and the one
per-attempt entry, the folded outcome of attempt n-1.

Proposed, and stated as such in the README: the stable-prefix digest is this
example's reading of two rules at once - "immutable for the life of the unit"
and "the next attempt receives that outcome list folded into its contract as
declared context". Keeping the two digests apart is what makes both checkable.

Python 3.11 standard library only.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat

HERE = os.path.dirname(os.path.abspath(__file__))


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def tokens(data: bytes) -> int:
    """Proposed: the same four-bytes-per-token estimate the model-access
    interface uses for a prompt, applied to a contract entry so the room a
    unit is given is a number before it is spent, not after."""
    return max(1, len(data) // 4)


def render(unit: dict, envelope: dict, attempt: int, folded, out_dir: str) -> dict:
    """Render one attempt's contract mount and return its manifest.

    `folded` is the outcome list of attempt n-1: a list of (check_id, outcome)
    pairs and nothing else. The criterion body, the command and the expected
    value never appear here - the unit sees its outcome, never the criterion it
    is judged against.
    """
    entries = []
    stable = []
    for row in unit["contract_entries"]:
        raw = open(os.path.join(HERE, "contract", row["path"]), "rb").read()
        entry = {"path": row["path"], "digest": digest(raw), "load_tier": row["load_tier"],
                 "tokens": tokens(raw)}
        entries.append((entry, raw))
        stable.append(entry)

    intent = json.dumps({"unit": unit["unit"], "task": unit["task"],
                         "summary": envelope["intent"]["summary"],
                         "source_ref": unit["source_ref"],
                         "attempt_ceiling": unit["ceilings"]["attempts"]},
                        sort_keys=True, indent=2).encode()
    intent_entry = {"path": "intent.json", "digest": digest(intent), "load_tier": "resident",
                    "tokens": tokens(intent)}
    entries.append((intent_entry, intent))
    stable.append(intent_entry)

    # The one per-attempt entry. Attempt 1 is cold by rule: no folded outcome,
    # so at least one attempt of every unit is independent of the last one.
    fold = json.dumps({"attempt": attempt, "cold": not folded,
                       "previous_outcomes": [{"check_id": c, "outcome": o} for c, o in (folded or [])]},
                      sort_keys=True, indent=2).encode()
    fold_entry = {"path": "folded-outcome.json", "digest": digest(fold), "load_tier": "resident",
                  "tokens": tokens(fold)}
    entries.append((fold_entry, fold))

    mount = os.path.join(out_dir, "contract")
    os.makedirs(mount, exist_ok=True)
    for entry, raw in entries:
        target = os.path.join(mount, entry["path"])
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "wb") as fh:
            fh.write(raw)
        os.chmod(target, stat.S_IRUSR)           # read-only, as the mount is

    manifest = {
        "unit": unit["unit"], "attempt": attempt, "mount": mount,
        "entries": [e for e, _ in entries],
        "resident_tokens": sum(e["tokens"] for e, _ in entries if e["load_tier"] == "resident"),
        "stable_prefix_digest": digest(json.dumps(stable, sort_keys=True).encode()),
    }
    manifest["contract_digest"] = digest(json.dumps(manifest["entries"], sort_keys=True).encode())
    with open(os.path.join(out_dir, f"contract-manifest-{attempt}.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    return manifest


def read_back(manifest: dict) -> str:
    """Recompute the contract digest from the bytes actually on the mount.

    A deciding check compares this against the digest ledgered before the cell
    started: a seed that was widened after the fact and one that was honoured
    are otherwise indistinguishable.
    """
    entries = []
    for entry in manifest["entries"]:
        raw = open(os.path.join(manifest["mount"], entry["path"]), "rb").read()
        entries.append({"path": entry["path"], "digest": digest(raw),
                        "load_tier": entry["load_tier"], "tokens": tokens(raw)})
    return digest(json.dumps(entries, sort_keys=True).encode())
