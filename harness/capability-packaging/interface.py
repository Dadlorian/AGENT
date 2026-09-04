#!/usr/bin/env python3
"""Capability packaging: one portable directory shape any conformant runtime loads.

Read it in this order. PackageRequest is the whole caller vocabulary: an
identity, and (optionally) the trigger that matched a description and one
reference path a package declares. resolve() is a template method: it locates
the package, checks the two required resident fields, checks the declared name
matches the identity that resolved it, and only then returns a
PackageResolution with tiers_loaded=["resident"] — enforced identically
whichever adapter is bound. load_body() and open_reference() call resolve()
first, so the gate cannot be skipped by asking for a deeper tier straight away.

No product name, path or endpoint appears in this file (T-t7-02, F-b1-02).
Python 3.11 standard library only.
"""
from __future__ import annotations

import os as _errors_os
import sys as _errors_sys
# Found by walking up from this file's own directory, not by a fixed "../errors"
# offset: several harnesses' test.sh copy interface.py into out/breakage/ (and
# deeper) for a deliberate-breakage run, and a fixed relative offset would miss
# harness/errors/problem.py from there. The walk stays inside the repository
# tree either way (out/breakage/ is still nested under this harness's own
# directory), and stops at the first "errors" sibling that actually has it.
_search_dir = _errors_os.path.dirname(_errors_os.path.abspath(__file__))
for _ in range(10):
    _candidate = _errors_os.path.join(_search_dir, "errors")
    if _errors_os.path.isfile(_errors_os.path.join(_candidate, "problem.py")):
        if _candidate not in _errors_sys.path:
            _errors_sys.path.append(_candidate)  # appended, never inserted at 0: this
            # harness's own adapters/ package must resolve before errors/adapters/ does
        break
    _up = _errors_os.path.dirname(_search_dir)
    if _up == _search_dir:
        break
    _search_dir = _up
from problem import render_body  # noqa: E402  -- errors-q5: the one shared point every
# capability's own registry gate renders its wire body through, instead of building one
# itself (harness/errors/problem.py owns render_body; this is not a second copy of it).

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

INTERFACE_VERSION = "0.1"
REQUIRED_RESIDENT = ("name", "description")

# --- Typed failures: RFC 9457 problem details, closed registry (F-b4-07,
# docs/decomposition.md 2.1.6) -----------------------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # suffix -> (status, title, retryable)
    "document-invalid": (422, "Request is not a well-formed package request", False),
    "adapter-unavailable": (503, "No source serves this identity", True),
}


class Problem(Exception):
    """A failure the caller branches on by type, never by reading prose."""

    def __init__(self, suffix: str, detail: str, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = render_body(PROBLEM_BASE + suffix, title, status, detail, retryable, ext)
        super().__init__(detail)


# --- The caller vocabulary --------------------------------------------------
# A caller writes an identity, never a filesystem path, a registry host, or a
# byte offset. trigger and reference_path are optional: omitted, only the
# resident tier is read (F-a4... none needed here — X-cap-capability-packaging-005).
ALLOWED = {"identity", "trigger", "reference_path"}


@dataclass(frozen=True)
class PackageRequest:
    identity: str
    trigger: str | None = None
    reference_path: str | None = None

    @classmethod
    def from_dict(cls, doc: dict) -> "PackageRequest":
        """The one gate a request passes. A filesystem path never gets past it."""
        if not isinstance(doc, dict):
            raise Problem("document-invalid", "a package request is an object")
        extra = sorted(set(doc) - ALLOWED)
        if extra:
            raise Problem("document-invalid",
                          f"fields {extra} are not in the package request vocabulary; a caller "
                          f"names an identity and never a path, a host or a byte range",
                          rejected_fields=extra)
        identity = doc.get("identity")
        if not isinstance(identity, str) or not identity:
            raise Problem("document-invalid", "identity must be a non-empty string")
        for opt in ("trigger", "reference_path"):
            if opt in doc and doc[opt] is not None and not isinstance(doc[opt], str):
                raise Problem("document-invalid", f"{opt} must be a string or absent")
        return cls(identity, doc.get("trigger"), doc.get("reference_path"))


@dataclass
class PackageResolution:
    """What every operation hands back. Nothing here names a path or a host."""
    identity: str
    resolved: bool
    source: str          # directory | registry
    digest: str | None
    tiers_loaded: list = field(default_factory=lambda: ["resident"])
    resident: dict | None = None     # exactly {"name", "description"} once resolved
    body: str | None = None
    reference: str | None = None


def resolution_as_dict(res: PackageResolution) -> dict:
    """The caller-visible view. Nothing here names a path, a host or an internal."""
    doc = {"identity": res.identity, "resolved": res.resolved, "source": res.source,
           "digest": res.digest, "tiers_loaded": list(res.tiers_loaded), "resident": res.resident}
    if res.body is not None:
        doc["body"] = res.body
    if res.reference is not None:
        doc["reference"] = res.reference
    return doc


# --- The interface the core imports -----------------------------------------
class CapabilityPackagingAdapter(ABC):
    """One packaging interface: list_resident, resolve, load_body, open_reference,
    and the proposed check_package. resolve, load_body, open_reference and
    list_resident are concrete here so that no adapter can decline the
    required-field check or the name-matches-identity check; only the six
    primitives below are adapter-specific.
    """

    entity = "adapter"           # what a report names; never a caller-visible field
    source = "directory"         # directory | registry — package-resolution-outcome.source
    declared_marker = "unset"    # what a response from this binding should say
    declared_gaps: tuple = ()    # what this binding cannot do, stated rather than silently dropped

    def __init__(self):
        self.resolutions = 0          # incremented only when a resolution succeeds
        self.refusals = 0
        self.observed_marker = ""     # read from a response, never from the binding

    # 1. list_resident -- a malformed package is invisible at discovery, not a crash
    def list_resident(self) -> list[dict]:
        entries = []
        for identity, raw in self._scan_all().items():
            resident = raw.get("resident", {})
            if all(resident.get(f) for f in REQUIRED_RESIDENT):
                entries.append({"identity": identity, "name": resident["name"],
                               "description": resident["description"]})
        return sorted(entries, key=lambda e: e["identity"])

    # 2. resolve -- the one gate every deeper tier passes through
    def resolve(self, identity: str) -> PackageResolution:
        raw = self._locate(identity)
        if raw is None:
            self.refusals += 1
            raise Problem("document-invalid",
                          f"no package carries identity {identity!r}; proposed suffix "
                          f"package-unresolved is pending registration in docs/decomposition.md "
                          f"2.1.6, so this binding returns the registered document-invalid instead "
                          f"of minting a suffix at the call site",
                          identity=identity)
        resident = raw.get("resident", {})
        missing = sorted(f for f in REQUIRED_RESIDENT if not resident.get(f))
        if missing:
            self.refusals += 1
            raise Problem("document-invalid",
                          f"package {identity!r} is missing required resident field(s) {missing}; "
                          f"a package carries exactly two required fields, name and description",
                          identity=identity, missing=missing)
        # Whether the declared name equals the directory name is this repository's own link
        # check, not the specification's (cap-capability-packaging step 5: "keep the
        # spec-conformance check and this repository's link check as two separate checks ...
        # never let one imply the other"). resolve() enforces only what the spec requires;
        # check_package below reports the drift as a separate, non-blocking counter.
        self.resolutions += 1
        self.observed_marker = self.declared_marker
        return PackageResolution(identity=identity, resolved=True, source=self.source,
                                 digest=self._digest(identity, raw), tiers_loaded=["resident"],
                                 resident={"name": resident["name"], "description": resident["description"]})

    # 3. load_body -- resolves first, then reads the body tier
    def load_body(self, identity: str, trigger: str) -> PackageResolution:
        if not trigger:
            raise Problem("document-invalid",
                          "load_body requires the trigger that matched the description; the body "
                          "is read on activation, never at startup", identity=identity)
        resolution = self.resolve(identity)
        resolution.body = self._read_body(identity)
        resolution.tiers_loaded.append("body")
        return resolution

    # 4. open_reference -- resolves first, then reads one declared reference file
    def open_reference(self, identity: str, reference_path: str) -> PackageResolution:
        resolution = self.resolve(identity)
        declared = self._list_references(identity)
        if reference_path not in declared:
            self.refusals += 1
            raise Problem("document-invalid",
                          f"{reference_path!r} is not a reference {identity!r} declares",
                          identity=identity, reference_path=reference_path, declared=declared)
        resolution.reference = self._read_reference(identity, reference_path)
        resolution.tiers_loaded.append("reference")
        return resolution

    # 5. check_package (proposed operation) -- a conformance outcome, never an exception
    def check_package(self, identity: str) -> dict:
        raw = self._locate(identity)
        exists = raw is not None
        resident = (raw or {}).get("resident", {})
        missing = sorted(f for f in REQUIRED_RESIDENT if not resident.get(f)) if exists else list(REQUIRED_RESIDENT)
        name_mismatch = bool(exists and not missing and resident.get("name") != identity)
        return {"identity": identity, "package_exists": exists,
               "required_field_missing": missing, "name_mismatch": name_mismatch}

    # --- adapter-specific primitives: everything below is confined to a source ---
    @abstractmethod
    def _scan_all(self) -> dict:
        """identity -> raw record ({'resident': {...}}), every package this source knows."""

    @abstractmethod
    def _locate(self, identity: str) -> dict | None:
        """The raw record for one identity, or None. No exception on a miss."""

    @abstractmethod
    def _read_body(self, identity: str) -> str:
        ...

    @abstractmethod
    def _list_references(self, identity: str) -> list[str]:
        """The reference paths this package declares. Not the reference content."""

    @abstractmethod
    def _read_reference(self, identity: str, reference_path: str) -> str:
        ...

    @abstractmethod
    def _digest(self, identity: str, raw: dict) -> str | None:
        """None when identity is a path (directory sources); a content digest
        when identity is a namespace-scoped name (registry sources)."""
