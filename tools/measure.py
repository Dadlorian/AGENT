#!/usr/bin/env python3
"""Run a skill's definition of done and record the result; the only way a row becomes "measured".

Usage: python3 tools/measure.py <skill-name> [--breakage-cmd "<shell that applies the breakage>" --restore-cmd "<shell that undoes it>"]
Runs definition_of_done.criterion, then (if given) the breakage, the criterion again, and the restore.
Writes the real outputs into the skill's definition_of_done (status measured only if the clean run passed
and the breakage run failed), re-renders, and appends a ledger record with both outputs. Never edits text by hand.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def clear_bytecode() -> None:
    """Stale .pyc files survive a git checkout and can serve broken code after a restore (seen 2026-09-03 in
    harness/state-persistence); every run starts from source."""
    import shutil
    for d in ROOT.rglob("__pycache__"):
        if ".git" not in d.parts:
            shutil.rmtree(d, ignore_errors=True)


def run(cmd: str) -> tuple[int, str]:
    clear_bytecode()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run(cmd, shell=True, cwd=ROOT, capture_output=True, text=True, env=env)
    return r.returncode, (r.stdout + r.stderr).strip()[-600:]


def tree_digest() -> dict:
    """sha256 of every file git knows or sees as untracked (ignored files excluded), so a breakage that a
    restore command failed to undo is detected whether or not the file was ever committed."""
    import hashlib
    # subprocess directly: run() truncates output for the record, which hid most of the file list (2026-09-03)
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT,
                         capture_output=True, text=True).stdout.splitlines()
    digest = {}
    for f in out:
        fp = ROOT / f
        if fp.is_file():
            digest[f] = hashlib.sha256(fp.read_bytes()).hexdigest()
    return digest


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__); return 2
    name = argv[0]
    opts = dict(zip(argv[1::2], argv[2::2]))
    p = ROOT / ".claude" / "skills" / name / "skill.json"
    sk = json.loads(p.read_text())
    d = sk["definition_of_done"]
    rc1, out1 = run(d["criterion"])
    result = {"clean_exit": rc1, "clean_output": out1}
    ok = rc1 == 0
    if "--breakage-cmd" in opts:
        before = tree_digest()
        brc, brout = run(opts["--breakage-cmd"])
        if brc != 0 or tree_digest() == before:
            # A breakage that did not apply (non-zero exit, or no file changed) would let the clean run stand in
            # for the broken one; seen 2026-09-03 on xc-compensation-implement.
            print(f"FAIL: breakage command did not apply (exit {brc}): {brout.strip().splitlines()[-1] if brout.strip() else 'no output'}")
            result.update({"breakage_applied": False}); ok = False
        rc2, out2 = run(d["criterion"])
        run(opts.get("--restore-cmd", "git checkout -- ."))
        after = tree_digest()
        not_restored = sorted(f for f in set(before) | set(after) if before.get(f) != after.get(f))
        result.update({"breakage_exit": rc2, "breakage_output": out2, "restored": not not_restored})
        if not_restored:
            # A restore that did not restore (git checkout on an untracked file does nothing) would leave the
            # breakage in the tree and let it be committed; seen on 2026-09-03 in two harnesses.
            print("FAIL: restore did not restore: " + ", ".join(not_restored[:5]))
            ok = False
        ok = ok and rc2 != 0
    d["status"] = "measured" if ok else "claimed"
    d["measured_run"] = {"by": "tools/measure.py", "commit": run("git rev-parse --short HEAD")[1], **result}
    p.write_text(json.dumps(sk, indent=2, ensure_ascii=False) + "\n")
    run(f"python3 tools/render_skill.py .claude/skills/{name}")
    # Append through the library, not a shell string: an output containing a quote broke the shell form (L-00085, L-00139).
    sys.path.insert(0, str(ROOT / "tools"))
    from kb import ledger_append
    ledger_append({"kind": "measure", "skill": name, "agent": "tools/measure.py", "result": result, "status": d["status"]})
    print(f"{name}: {d['status']} (clean exit {rc1}" + (f", breakage exit {result.get('breakage_exit')}" if "breakage_exit" in result else "") + ")")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
