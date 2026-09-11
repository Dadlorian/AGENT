#!/usr/bin/env python3
"""Every module a ref_arch page imports must exist beside it.

  python3 tools/ref_arch_imports.py              check every page
  python3 tools/ref_arch_imports.py --selftest   plant a missing import, prove this fails

WHY
---
On 2026-09-11 ref_arch/Reference Stack.dc.html could not render at all: its component does
`import('./cellplane-stack.js')` and that module was not beside it -- it sat in an untracked
ref_arch/new/ directory with fifteen other files. Nothing in the repo noticed, because nothing
reads these pages' imports. A page that renders nothing is not visibly different from a page
nobody opened.

It checks both forms the pages use: `<script src="./x.js">` and dynamic `import('./x.js')`.
Remote URLs are ignored -- this asks whether a local file is missing, not whether a host is up.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "ref_arch"
PATTERNS = (r"""import\(\s*['"](\./[^'"]+)['"]\s*\)""", r"""src=["'](\./[^"']+)["']""")


def imports_of(text: str) -> set:
    return {m for p in PATTERNS for m in re.findall(p, text)}


def check(pages) -> list:
    findings = []
    for page in pages:
        for ref in sorted(imports_of(page.read_text())):
            target = (page.parent / ref).resolve()
            findings.append({"page": page.name, "ref": ref, "ok": target.is_file()})
    return findings


def pages() -> list:
    return sorted(p for p in REF.glob("*.dc.html"))


def report(findings: list) -> int:
    missing = [f for f in findings if not f["ok"]]
    for f in missing:
        print(f"  BLOCK  {f['page']:34} imports {f['ref']} -- not beside it")
    print(f"{len(findings) - len(missing)} of {len(findings)} local imports resolve "
          f"across {len({f['page'] for f in findings})} page(s)")
    if missing:
        print(f"{len(missing)} need a person.")
    return 1 if missing else 0


def selftest() -> int:
    import shutil, tempfile
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        real = pages()[0]
        shutil.copy(real, d / real.name)
        for js in REF.glob("*.js"):
            shutil.copy(js, d / js.name)
        clean = [f for f in check([d / real.name]) if not f["ok"]]
        (d / real.name).write_text((d / real.name).read_text()
                                   + "\n<script>import('./definitely-not-here.js')</script>")
        dirty = [f for f in check([d / real.name]) if not f["ok"]]
    print("self-test - plant an import of a module that is not there")
    print(f"  before planting: {len(clean)} missing")
    print(f"  after planting:  {len(dirty)} missing "
          f"{[f['ref'] for f in dirty]}")
    ok = not clean and any(f["ref"].endswith("definitely-not-here.js") for f in dirty)
    print("PASS - a missing local import fails, and a page whose imports resolve does not" if ok
          else "FAIL - the planted missing import was not caught")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    p = pages()
    if not p:
        print("no ref_arch pages; nothing to check")
        return 0
    return report(check(p))


if __name__ == "__main__":
    sys.exit(main())
