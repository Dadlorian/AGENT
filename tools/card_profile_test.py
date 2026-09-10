#!/usr/bin/env python3
"""Prove the card-profile gate actually rejects things, rather than only ever passing.

A gate that has only been observed passing is a habit, not evidence (build-evidence: a
criterion, a deliberate breakage that makes it fail, and the recorded output of both runs).

This plants one known defect at a time into a real profile, runs the real checker against it,
and asserts the checker rejects it AND names the right field. Then it restores and asserts a
clean pass. Nothing here stubs the checker - it shells out to the same command CI would run.

  python3 tools/card_profile_test.py
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "validate_card_profiles.py"
SOURCE = ROOT / "docs" / "reference" / "cards" / "3-3.json"


def run_checker(path: Path):
    p = subprocess.run([sys.executable, str(CHECKER), str(path)],
                       capture_output=True, text=True, cwd=ROOT)
    return p.returncode, p.stdout + p.stderr


def research_record(rid: str) -> dict:
    for line in (ROOT / "kb" / "research.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r["id"] == rid:
                return r
    return {}


# Each defect: a mutation, and a phrase the checker's complaint must contain.
def defects(base: dict):
    # find a research record with distinct snippet and claim text, for the self-citation probe
    probe = None
    for line in (ROOT / "kb" / "research.jsonl").read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("claim") and r.get("snippet") and len(r["claim"]) > 60:
            frag = r["claim"][20:70]
            if frag not in (r.get("snippet") or "") and frag not in (r.get("read") or ""):
                probe = (r["id"], frag)
                break

    def quote_from_claim(d):
        rid, frag = probe
        d["definition"] = {"text": "x", "origin": "sourced",
                           "evidence": [{"id": rid, "quote": frag}]}
        return d

    def altered_quote(d):
        ev = d["definition"]["evidence"][0]
        ev["quote"] = ev["quote"][:-8] + " ZZZNOTREAL"
        return d

    def sourced_no_sources(d):
        d["definition"] = {"text": "x", "origin": "sourced", "evidence": []}
        return d

    def unquoted_citation(d):
        """The defect this shape exists to prevent: an id riding along with no quote."""
        d["definition"]["evidence"].append({"id": "F-b3-02", "quote": ""})
        return d

    def retired_shape(d):
        first = d["definition"]["evidence"][0]
        d["definition"] = {"text": "x", "origin": "sourced",
                           "sources": [first["id"]], "quote": first["quote"]}
        return d

    def proposed_not_saying_so(d):
        d["landscape"] = {"text": "This is a bare assertion with no marker.", "origin": "proposed"}
        return d

    def unknown_id(d):
        d["definition"]["evidence"][0]["id"] = "X-does-not-exist-999"
        return d

    def empty_gaps(d):
        d["gaps"] = []
        return d

    def bogus_standard(d):
        if d.get("standards"):
            d["standards"][0]["id"] = "no-such-standard-here"
        else:
            d["standards"] = [{"id": "no-such-standard-here", "role": "x",
                               "evidence": {"text": "y", "origin": "proposed"}}]
        return d

    cases = [
        ("quote lifted from a record's own claim field", quote_from_claim, "not verbatim in the SOURCE text"),
        ("quote altered by a few characters", altered_quote, "not verbatim in the SOURCE text"),
        ("origin=sourced with no evidence", sourced_no_sources, "no evidence"),
        ("a cited id riding along with no quote", unquoted_citation, "no quote"),
        ("the retired sources/quote shape", retired_shape, "retired sources/quote shape"),
        ("origin=proposed that never says proposed", proposed_not_saying_so, "never says so"),
        ("citation to an id that does not exist", unknown_id, "unknown id"),
        ("empty gaps list", empty_gaps, "gaps is empty"),
        ("standard with no directory on disk", bogus_standard, "no standards/"),
    ]
    return [c for c in cases if probe or c[1] is not quote_from_claim]


def main() -> int:
    if not SOURCE.is_file():
        sys.exit(f"missing {SOURCE.relative_to(ROOT)}; write a profile first")
    base = json.loads(SOURCE.read_text())

    print("control run - the unmodified profile must PASS")
    with tempfile.TemporaryDirectory() as td:
        clean = Path(td) / SOURCE.name
        clean.write_text(json.dumps(base, indent=2))
        code, out = run_checker(clean)
        ok_control = code == 0
        print(f"  {'PASS' if ok_control else 'FAIL'}  exit={code}  {out.strip().splitlines()[-1] if out.strip() else ''}")

    print("\nplanted defects - each must be REJECTED, naming the right problem")
    results = []
    for label, mutate, expect in defects(base):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / SOURCE.name
            p.write_text(json.dumps(mutate(json.loads(json.dumps(base))), indent=2))
            code, out = run_checker(p)
        caught = code != 0 and expect in out
        results.append(caught)
        detail = "" if caught else f"   <- expected {expect!r}, got exit={code}"
        print(f"  {'PASS' if caught else 'FAIL'}  {label}{detail}")

    total = len(results) + 1
    passed = sum(results) + (1 if ok_control else 0)
    print(f"\n{passed}/{total} checks hold "
          f"({len(results)} defects planted, {sum(results)} caught, control {'green' if ok_control else 'RED'})")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
