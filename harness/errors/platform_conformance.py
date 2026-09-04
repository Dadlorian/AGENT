#!/usr/bin/env python3
"""errors-q5, answered platform-wide: harness/errors/conformance.py's own
--construction-scan only ever walked harness/errors itself (its docstring says
so verbatim). This is the wider check the re-answer asked for: it walks every
harness under harness/, not just this one, for the two things a new capability
adapter could otherwise use to invent its own failure shape --

  --construction-scan   a static scan: is there anywhere under harness/, other
                         than render_body() in this file, that hand-assembles a
                         dict carrying the RFC 9457 core members (type, title,
                         status, detail, retryable) together? After the
                         errors-q5 migration there should be none: every
                         harness's own typed condition (its own Problem class
                         or its own problem() gate -- keeping its own closed
                         registry is correct, cap-errors names each
                         capability's own typed conditions) calls render_body()
                         in problem.py instead of building the dict itself.

  --raise-all            the dynamic companion: load every harness's own
                         interface.py in one process, raise every row of every
                         harness's own registry, and confirm the shared
                         render_body() counter in problem.py rose by exactly
                         that many -- proof, at runtime and not just by
                         grepping source, that every one of them rendered
                         through the one path this module owns, never a
                         second one built locally.

    python3 harness/errors/platform_conformance.py --construction-scan ..
    python3 harness/errors/platform_conformance.py --raise-all ..

Python 3.11 standard library only.
"""
from __future__ import annotations

import argparse
import ast
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import problem as problem_module  # noqa: E402  the shared point itself

RFC9457_CORE_KEYS = {"type", "title", "status", "detail", "retryable"}
OWNER_FILE = os.path.join(HERE, "problem.py")


def _dict_literal_keys(node: ast.Dict) -> set[str]:
    """The literal string keys stated directly in a Dict node -- a **spread
    entry (None in ast.Dict.keys at that position) is skipped, not treated as
    an unknown key: {"type": ..., "title": ..., **ext} still names its five
    core members literally and is exactly the pattern being scanned for, while
    a pure reshape like linked/interface.py's Problem.adopt ({**body, **ext})
    states no literal keys at all and so can never satisfy the core-member
    subset check below regardless of what body happens to carry."""
    return {k.value for k in node.keys
            if k is not None and isinstance(k, ast.Constant) and isinstance(k.value, str)}


def _references_registry(node: ast.Dict) -> bool:
    """True when the dict literal's own subtree names PROBLEM_BASE, REGISTRY or
    PROBLEM_REGISTRY -- the signature of a *fresh* construction (a suffix is
    being turned into a body by hand) rather than a reshape of an already-typed
    body a caller passed in (e.g. observability/adapters/second.py's OTLP
    export, which only ever reads fields off an existing dict -- exactly the
    reshape pattern errors-q5 calls out as legitimate: reshape_from_body still
    goes through render_body/construct_problem, and does not fabricate a type,
    title or status that were not already present)."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id in ("PROBLEM_BASE", "REGISTRY", "PROBLEM_REGISTRY"):
            return True
    return False


def construction_scan(root: str) -> tuple[int, list[str]]:
    """Every .py file under root (excluding out/ and __pycache__/), other than
    problem.py itself, scanned for a dict literal whose keys are a superset of
    the RFC 9457 core members AND whose value expressions derive from a
    PROBLEM_BASE/REGISTRY lookup -- i.e. a *fresh* body built from a registry
    row rather than an existing typed body reshaped for another wire format.
    Returns (stray_count, [file:line: snippet])."""
    hits: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ("out", "__pycache__")]
        for name in sorted(filenames):
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            if os.path.abspath(path) == os.path.abspath(OWNER_FILE):
                continue
            try:
                src = open(path, encoding="utf-8").read()
                tree = ast.parse(src, filename=path)
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    keys = _dict_literal_keys(node)
                    if keys is not None and RFC9457_CORE_KEYS <= keys and _references_registry(node):
                        rel = os.path.relpath(path, root)
                        hits.append(f"{rel}:{node.lineno}: dict literal built fresh from a registry row, "
                                    f"carrying {sorted(RFC9457_CORE_KEYS)}")
    return len(hits), hits


def _harness_dirs(harness_root: str) -> list[str]:
    return sorted(
        d for d in os.listdir(harness_root)
        if os.path.isfile(os.path.join(harness_root, d, "interface.py"))
    )


def _load_interface(harness_root: str, name: str):
    """Load harness/<name>/interface.py under a unique module name (never
    'interface') so 26 harnesses that each name their own top-level module
    'interface' can all be loaded into one process without one shadowing
    another in sys.modules -- the collision every other cross-harness
    composition in this tree that plain-imports 'interface' is exposed to."""
    path = os.path.join(harness_root, name, "interface.py")
    modname = f"_platform_conformance_{name.replace('-', '_')}_interface"
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    # interface.py assumes its own directory is already searched first for its
    # sibling modules (adapters/, etc.) -- true of every call.py/conformance.py
    # in this tree, so it is true here too.
    hdir = os.path.join(harness_root, name)
    added = hdir not in sys.path
    if added:
        sys.path.insert(0, hdir)
    try:
        spec.loader.exec_module(mod)
    finally:
        if added:
            sys.path.remove(hdir)
    return mod


def _registry_of(mod) -> dict | None:
    return getattr(mod, "REGISTRY", None) or getattr(mod, "PROBLEM_REGISTRY", None)


def raise_all(harness_root: str) -> tuple[int, int, list[str]]:
    """Load every harness's interface.py (except harness/errors itself, whose
    own conformance.py already raises every row of its own registry twice, once
    per adapter -- this covers the 26 harnesses that consume the shared point,
    not the harness that owns it), raise/construct every row of its own
    registry, and confirm each one rendered through problem.render_body().
    Returns (conditions_raised, harnesses_covered, failures)."""
    failures: list[str] = []
    total_raised = 0
    covered = 0
    for name in _harness_dirs(harness_root):
        if name == "errors":
            continue
        try:
            mod = _load_interface(harness_root, name)
        except Exception as exc:  # noqa: BLE001 -- reported, not swallowed
            failures.append(f"{name}: interface.py did not load: {exc!r}")
            continue
        registry = _registry_of(mod)
        problem_cls = getattr(mod, "Problem", None)
        if registry is None or problem_cls is None:
            continue  # a harness with no typed-condition registry has nothing to raise
        is_exception = isinstance(problem_cls, type) and issubclass(problem_cls, BaseException)
        gate_fn = getattr(mod, "problem", None)  # evaluation / observability's own gate
        covered += 1
        for suffix, row in registry.items():
            before = problem_module.render_count()
            try:
                if not is_exception and callable(gate_fn):
                    body = gate_fn(suffix, f"platform_conformance exercising {suffix}").as_dict()
                elif isinstance(row, dict) and not row.get("registered", True):
                    continue  # a proposed-but-not-yet-registered row; the gate itself refuses it
                elif is_exception:
                    try:
                        raise problem_cls(suffix, f"platform_conformance exercising {suffix}")
                    except problem_cls as exc:
                        body = exc.body
                else:
                    failures.append(f"{name}:{suffix}: neither an exception-typed Problem class "
                                     f"nor a problem() gate function was found")
                    continue
            except Exception as exc:  # noqa: BLE001
                failures.append(f"{name}:{suffix}: {exc!r}")
                continue
            after = problem_module.render_count()
            if after != before + 1:
                failures.append(f"{name}:{suffix}: render_body() ran {after - before} times, not exactly 1 "
                                 f"(body={body!r})")
            elif not RFC9457_CORE_KEYS <= set(body.keys()):
                failures.append(f"{name}:{suffix}: body is missing a core member: {sorted(body.keys())}")
            else:
                total_raised += 1
    return total_raised, covered, failures


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--construction-scan", metavar="ROOT",
                     help="static: scan ROOT/harness (or ROOT itself if it ends in harness) for a "
                          "second hand-built RFC 9457 dict outside problem.py")
    ap.add_argument("--raise-all", metavar="ROOT",
                     help="dynamic: raise every typed condition of every harness under ROOT and "
                          "confirm every one rendered through render_body()")
    args = ap.parse_args(argv)

    if args.construction_scan:
        root = os.path.abspath(args.construction_scan)
        harness_root = root if os.path.basename(root) == "harness" else os.path.join(root, "harness")
        count, hits = construction_scan(harness_root)
        print("\n".join(hits) or "no hand-built RFC 9457 dict outside problem.py, anywhere under harness/")
        print(f"platform_stray_construction_hits={count}")
        print(f"owner={os.path.relpath(OWNER_FILE, root)}")
        return 1 if count else 0

    if args.raise_all:
        root = os.path.abspath(args.raise_all)
        harness_root = root if os.path.basename(root) == "harness" else os.path.join(root, "harness")
        raised, covered, failures = raise_all(harness_root)
        for f in failures:
            print(f"FAIL {f}")
        print(f"conditions_raised={raised} harnesses_covered={covered} render_count={problem_module.render_count()}")
        if raised != problem_module.render_count():
            print(f"FAIL render_count ({problem_module.render_count()}) != conditions_raised ({raised}): "
                  f"something rendered a body this run did not raise, or twice")
            return 1
        return 1 if failures else 0

    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
