#!/usr/bin/env python3
"""Extract the reference stack from ref_arch/cellplane-stack.js into docs/reference/reference-stack.json.

The stack is the tool-selection layer the reference model does not carry: per layer, the ports
(`challenges`) that layer has, and per port the primary picks, the alternates that swap in for
them, and the tools excluded on licence or pricing. It joins to the model by layer key.

Read-only against the source; rerun after cellplane-stack.js changes.

  python3 tools/extract_reference_stack.py           rewrite docs/reference/reference-stack.json
  python3 tools/extract_reference_stack.py --check   verify the checked-in JSON matches the source

Why a parser and not a regex: the source is an ES module with single-quoted strings that contain
escaped apostrophes (`the customer\\'s OIDC provider`). tools/extract_reference_model.py's
split_args() closes a string on the first quote character and would cut those in half.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "ref_arch" / "cellplane-stack.js"
OUT = ROOT / "docs" / "reference" / "reference-stack.json"
MODEL = ROOT / "docs" / "reference" / "reference-model.json"
TIERS = (None, "core", "watch", "excluded")
# The two owner artifacts disagree on exactly one layer key: docs/reference/reference-model.json
# calls the ninth area `concerns`, ref_arch/cellplane-stack.js calls it `cross`. Same title, same
# position, so the join is unambiguous -- declared here and echoed into the output rather than
# normalised away silently, because a mapping nobody can see is a mapping nobody can dispute.
KEY_ALIAS = {"cross": "concerns"}
EXCLUDE_REASONS = (None, "licence", "pricing", "both")
# T(tier, license, kind, maturity, note, verified, exclude) -- from the source's own helper
T_FIELDS = ("tier", "license", "kind", "maturity", "note", "verified", "exclude")


class P:
    """Minimal reader for the JS literal subset this file uses: objects, arrays, single-quoted
    strings with backslash escapes, booleans, null, integers, bare identifier keys, and T(...)."""

    def __init__(self, s: str, i: int = 0):
        self.s, self.i = s, i

    def ws(self):
        while self.i < len(self.s):
            if self.s[self.i] in " \t\r\n,":
                self.i += 1
            elif self.s.startswith("//", self.i):
                self.i = self.s.find("\n", self.i) + 1 or len(self.s)
            else:
                return

    def value(self):
        self.ws()
        c = self.s[self.i]
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c in "'\"":
            return self.string()
        m = re.match(r"(true|false|null|undefined|-?\d+)", self.s[self.i:])
        if m:
            self.i += m.end()
            tok = m.group(1)
            return {"true": True, "false": False, "null": None,
                    "undefined": None}.get(tok, None) if not tok.lstrip("-").isdigit() else int(tok)
        m = re.match(r"T\s*\(", self.s[self.i:])
        if m:
            self.i += m.end()
            args = []
            while True:
                self.ws()
                if self.s[self.i] == ")":
                    self.i += 1
                    break
                args.append(self.value())
            out = dict(zip(T_FIELDS, args + [None] * (len(T_FIELDS) - len(args))))
            out["verified"] = bool(out.get("verified"))
            return out
        raise ValueError(f"unparsed at {self.i}: {self.s[self.i:self.i+60]!r}")

    def string(self):
        q, self.i = self.s[self.i], self.i + 1
        out = ""
        while True:
            c = self.s[self.i]
            if c == "\\":
                out += self.s[self.i + 1]
                self.i += 2
                continue
            if c == q:
                self.i += 1
                return out
            out += c
            self.i += 1

    def arr(self):
        self.i += 1
        out = []
        while True:
            self.ws()
            if self.s[self.i] == "]":
                self.i += 1
                return out
            out.append(self.value())

    def obj(self):
        self.i += 1
        out = {}
        while True:
            self.ws()
            if self.s[self.i] == "}":
                self.i += 1
                return out
            quoted = self.s[self.i] in "'\""
            if quoted:
                key = self.string()          # string() advances i past the closing quote
            else:
                key = re.match(r"[A-Za-z_$][\w$]*", self.s[self.i:]).group(0)
                self.i += len(key)           # only a bare key still needs advancing
            self.ws()
            assert self.s[self.i] == ":", f"expected : at {self.i}"
            self.i += 1
            out[key] = self.value()


def export(name: str, text: str):
    m = re.search(rf"export const {name}\s*=\s*", text)
    if not m:
        raise ValueError(f"no export named {name}")
    return P(text, m.end()).value()


def build() -> dict:
    text = SRC.read_text()
    src_line = re.search(r"// Source: (.+)", text)
    return {
        "generated_from": str(SRC.relative_to(ROOT)),
        "note": "Derived. Do not hand-edit: rerun tools/extract_reference_stack.py. Joins to "
                "docs/reference/reference-model.json by layer key.",
        "source_claimed": src_line.group(1).strip() if src_line else None,
        "key_aliases": KEY_ALIAS,
        "meta": export("meta", text),
        "standards": export("standards", text),
        "tools": export("tools", text),
        "layers": export("layers", text),
    }


def checks(d: dict) -> list:
    out, errs = [], []
    tools, layers, standards = d["tools"], d["layers"], d["standards"]
    tool_names = set(tools)
    std_names = {s["name"] for s in standards}

    model_keys = set()
    if MODEL.is_file():
        model_keys = {a["key"] for a in json.loads(MODEL.read_text())["areas"]}
    bad = [l["key"] for l in layers
           if model_keys and KEY_ALIAS.get(l["key"], l["key"]) not in model_keys]
    out.append(("every layer key resolves to an area in the reference model", not bad, bad))
    used = sorted({l["key"] for l in layers if l["key"] in KEY_ALIAS})
    out.append((f"declared key aliases in use: {used or 'none'}", True, []))

    missing = sorted({t for l in layers for c in l["challenges"]
                      for k in ("picks", "alts", "excluded") for t in (c.get(k) or [])
                      if t not in tool_names})
    out.append(("every tool a port names exists in tools", not missing, missing))

    missing_std = sorted({s for l in layers for c in l["challenges"]
                          for s in (c.get("standards") or []) if s not in std_names})
    out.append(("every standard a port names exists in standards", not missing_std, missing_std))

    missing_st = sorted({t for s in standards for t in (s.get("tools") or [])
                         if t not in tool_names})
    out.append(("every tool a standard names exists in tools", not missing_st, missing_st))

    bad_tier = sorted({n for n, t in tools.items() if t.get("tier") not in TIERS})
    out.append(("every tier is core, watch, excluded or absent", not bad_tier, bad_tier))

    bad_ex = sorted({n for n, t in tools.items() if t.get("exclude") not in EXCLUDE_REASONS})
    out.append(("every exclude reason is licence, pricing or both", not bad_ex, bad_ex))

    unreasoned = sorted({n for n, t in tools.items()
                         if t.get("tier") == "excluded" and not t.get("exclude")})
    out.append(("every excluded tool says why", not unreasoned, unreasoned))

    empty = [c["title"] for l in layers for c in l["challenges"]
             if not (c.get("title") or "").strip() or not (c.get("problem") or "").strip()]
    out.append(("no port with an empty title or problem", not empty, empty))

    nolic = sorted({n for n, t in tools.items() if not (t.get("license") or "").strip()})
    out.append(("every tool names a licence", not nolic, nolic))

    orphan = sorted(tool_names - {t for l in layers for c in l["challenges"]
                                  for k in ("picks", "alts", "excluded")
                                  for t in (c.get(k) or [])}
                    - {t for s in standards for t in (s.get("tools") or [])})
    out.append(("every tool is used by a port or a standard", not orphan, orphan))
    return out


def main() -> int:
    d = build()
    results = checks(d)
    for label, ok, detail in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {label}" + ("" if ok else f": {detail[:6]}"))
    held = sum(1 for _, ok, _ in results if ok)
    ports = sum(len(l["challenges"]) for l in d["layers"])
    build_ports = sum(1 for l in d["layers"] for c in l["challenges"] if c.get("build"))
    print(f"{held} of {len(results)} checks hold; {len(d['layers'])} layers, {ports} ports, "
          f"{len(d['tools'])} tools, {len(d['standards'])} standards, "
          f"{build_ports} ports no permissive OSS fills")
    if held != len(results):
        return 1
    text = json.dumps(d, indent=2, ensure_ascii=False) + "\n"
    if "--check" in sys.argv:
        if not OUT.is_file():
            print(f"error: {OUT.relative_to(ROOT)} does not exist; run without --check")
            return 1
        if OUT.read_text() != text:
            print(f"error: {OUT.relative_to(ROOT)} differs from what the source renders")
            return 1
        print(f"{OUT.relative_to(ROOT)} matches its source")
        return 0
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
