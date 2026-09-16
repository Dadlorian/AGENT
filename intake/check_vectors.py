#!/usr/bin/env python3
"""Reference checker for Intake Protocol 0.1 L1 rules, run against vectors.jsonl.

Implements only the DECIDABLE (L1) rules of SPEC.md. It makes no judgement about
content: an L2 assertion is recorded, never rejected.

  python3 check_vectors.py                 run every vector
  python3 check_vectors.py --break-order   deliberate breakage: check staleness
                                           before replay, violating rule E4
"""
from __future__ import annotations
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
P = "urn:intake:problem:"
TYPES = {"text": str, "number": (int, float), "boolean": bool}


def submit(state: dict, req: dict, break_order: bool = False) -> tuple[str, dict]:
    """Return (outcome, effects). Outcome is 'committed', 'replayed', 'noop',
    'existing', or a problem type URI."""
    rev = state.get("revision", 1)
    saved, history = 0, {}

    def stale():
        return req.get("expectedRevision") is not None and req["expectedRevision"] < rev

    # E4: replay is checked FIRST, before staleness.
    def replay():
        prior = state.get("replay", {}).get(req["requestId"])
        if prior is None:
            return None
        return "replayed" if prior == req.get("payload_digest") else P + "replay-conflict"

    if break_order:
        if stale():
            return P + "stale-revision", {"saved": 0}
        r = replay()
    else:
        r = replay()
        if r:
            return r, {"saved": 0}
        if stale():
            return P + "stale-revision", {"saved": 0}
    if r:
        return r, {"saved": 0}

    if state.get("sealed") and req.get("targetDepth"):
        return P + "depth-after-seal", {"saved": 0}

    if req.get("instantiate"):
        known = state.get("questions", {})
        if all(q in known for q in req["instantiate"]):
            return "existing", {"saved": 0}

    answers = req.get("answers")
    if answers is None or (answers == [] and not req.get("targetDepth")):
        return "noop", {"saved": 0, "revision": rev}          # E1: read-only

    known = state.get("questions", {})
    seen = set()
    staged = []
    for a in answers:
        qid = a.get("questionId")
        if qid not in known:
            return P + "unknown-question", {"saved": 0}        # E3: nothing saved
        if qid in seen:
            return P + "duplicate-answer", {"saved": 0}
        seen.add(qid)
        status, val = a.get("status"), a.get("value")
        if status == "unknown":
            if val is not None:
                return P + "answer-type", {"saved": 0}
        elif status == "not_applicable":
            if not (a.get("reason") or "").strip():
                return P + "not-applicable-unsupported", {"saved": 0}
        elif status == "answered":
            declared = known[qid].get("answerType", "text")
            want = TYPES.get(declared, str)
            # bool is a subclass of int, so True would pass a "number" field silently.
            mistyped = not isinstance(val, want) or (isinstance(val, bool) and declared != "boolean")
            if mistyped:
                return P + "answer-type", {"saved": 0}
            if (a.get("mapping") or {}).get("source") == "user":
                return P + "mapping-source", {"saved": 0}      # A2
            if "utterance" in a and a["utterance"] is None:
                return P + "missing-utterance", {"saved": 0}   # A1
        else:
            return P + "answer-type", {"saved": 0}
        staged.append(a)

    # I2: corrections are budgeted, checked before commit.
    prior = state.get("answers", {})
    corrections = sum(1 for a in staged if a["questionId"] in prior)
    if corrections and state.get("corrections_used", 0) + corrections > state.get("K", 12):
        return P + "budget-exhausted", {"saved": 0}

    for a in staged:
        history[a["questionId"]] = len(prior.get(a["questionId"], [])) + 1
        saved += 1
    return "committed", {"saved": saved, "revision": rev + 1, "history": history}


def main() -> int:
    break_order = "--break-order" in sys.argv
    vectors = [json.loads(l) for l in (HERE / "vectors.jsonl").read_text().splitlines() if l.strip()]
    failed = []
    for v in vectors:
        out, eff = submit(v["state"], v["request"], break_order)
        ok = out == v["expect"]
        if ok and "expect_saved" in v:
            ok = eff.get("saved") == v["expect_saved"]
        if ok and "expect_revision" in v:
            ok = eff.get("revision") == v["expect_revision"]
        if ok and "expect_history" in v:
            ok = max(eff.get("history", {0: 0}).values()) == v["expect_history"]
        mark = "ok  " if ok else "FAIL"
        print(f"  {mark} {v['id']} [{v['rule']}] {v['why']}")
        if not ok:
            print(f"       expected {v['expect']!r}, got {out!r} {eff}")
            failed.append(v["id"])
    print(f"\n{len(vectors) - len(failed)} passed, {len(failed)} failed"
          + (f"  -> {failed}" if failed else ""))
    if break_order:
        print("\nDeliberate breakage (E4 order inverted): exit 1 IS the expected result."
              if failed else "\nBREAKAGE DID NOT FAIL -- the vectors check nothing.")
        return 1 if failed else 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
