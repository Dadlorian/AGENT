#!/usr/bin/env python3
"""An independent verifier. Imports no adapter and no interface module.

Reads the two files the second store publishes - the entries a third party
would hold and the window heads it published - and recomputes every window
head from the entry hashes alone. Reports the first window whose recomputed
head does not match what was published, without ever touching the adapter's
own reader.

    python3 verify_external.py <entries.jsonl> <published-heads.jsonl>
    {"windows": N, "verified": true, "break_at_window": -1}
"""
from __future__ import annotations

import hashlib
import json
import sys


def canonical(doc) -> bytes:
    return json.dumps(doc, sort_keys=True, separators=(",", ":")).encode()


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def window_head(prior_head: str, entry_hashes: list) -> str:
    return sha256_hex(canonical({"prior_head": prior_head, "entries": entry_hashes}))


def entry_hash(prev: str, action: str, actor: str, delegation_chain, correlation: dict, kind: str, at: str) -> str:
    return sha256_hex(canonical({"prev": prev, "action": action, "actor": actor,
                                 "delegation_chain": list(delegation_chain), "correlation": correlation,
                                 "kind": kind, "at": at}))


def main() -> int:
    entries_path, heads_path = sys.argv[1], sys.argv[2]
    entries = [json.loads(l) for l in open(entries_path).read().splitlines() if l]
    windows = [json.loads(l) for l in open(heads_path).read().splitlines() if l]
    by_seq = {e["seq"]: e for e in entries}

    break_at = -1
    for wi, w in enumerate(windows):
        window_entries = [by_seq[s] for s in range(w["from_seq"], w["to_seq"] + 1) if s in by_seq]
        if len(window_entries) != w["size"]:
            break_at = wi
            break
        # recompute each entry's own hash from its fields - catches a body edited in place
        # even when the entry's claimed hash field was left untouched by the tamper.
        recomputed_entry_hashes = []
        mismatch = False
        for e in window_entries:
            h = entry_hash(e["prev"], e["action"], e["actor"], e["delegation_chain"],
                           e["correlation"], e["kind"], e["at"])
            recomputed_entry_hashes.append(h)
            if h != e["hash"]:
                mismatch = True
        recomputed = window_head(w["prior_head"], recomputed_entry_hashes)
        if mismatch or recomputed != w["head"]:
            break_at = wi
            break
    result = {"windows": len(windows), "verified": break_at == -1, "break_at_window": break_at,
             "entries_seen": len(entries), "adapter_imported": [m for m in sys.modules if "adapter" in m]}
    print(json.dumps(result))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
