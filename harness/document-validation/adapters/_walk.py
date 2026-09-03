#!/usr/bin/env python3
"""Shared walk-per-document check: re-interprets the schema tree on every call.

Used by dryrun.py and live.py -- both today's execution model (F-b3-09: "in
place"). Supports the JSON Schema 2020-12 keywords examples/end-to-end/run.py's
in-place checker already supports ($ref, anyOf, if/then/else, type, const, enum,
pattern, min/maxLength, minimum, maximum, minItems, contains, items, required,
properties, additionalProperties), and nothing this platform's own schemas do
not use. Unlike run.py's checker, every violation carries a JSON Pointer
instance_location and a keyword_location (X-cap-document-validation-005)
instead of one human-readable string.

adapters/second.py is deliberately NOT built on this module: it compiles the
schema once in prepare() and checks instances against the compiled form, which
is the different execution model build-adapter-pair requires of a second
adapter (F-b1-04).
"""
from __future__ import annotations

import re

from interface import TYPES, ValidationError, _ptr_push


def walk(inst, schema, root, path, kpath, keywords_seen) -> list:
    """Return every ValidationError found in inst against schema, one pass."""
    if "$ref" in schema:
        keywords_seen[0] += 1
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return walk(inst, node, root, path, kpath + "/$ref", keywords_seen)
    if "anyOf" in schema:
        keywords_seen[0] += 1
        for i, branch in enumerate(schema["anyOf"]):
            if not walk(inst, branch, root, path, f"{kpath}/anyOf/{i}", [0]):
                return []
        return [ValidationError(path, kpath + "/anyOf", "matches none of the allowed branches")]
    errs: list = []
    if "if" in schema:
        keywords_seen[0] += 1
        branch = "then" if not walk(inst, schema["if"], root, path, kpath + "/if", [0]) else "else"
        if branch in schema:
            errs += walk(inst, schema[branch], root, path, f"{kpath}/{branch}", keywords_seen)
    t = schema.get("type")
    if t:
        keywords_seen[0] += 1
        want = TYPES[t]
        bad = not isinstance(inst, want) or (t in ("integer", "number") and isinstance(inst, bool))
        if bad:
            return errs + [ValidationError(path, kpath + "/type", f"expected {t}, got {type(inst).__name__}")]
    if "const" in schema:
        keywords_seen[0] += 1
        if inst != schema["const"]:
            errs.append(ValidationError(path, kpath + "/const", f"must equal {schema['const']!r}"))
    if "enum" in schema:
        keywords_seen[0] += 1
        if inst not in schema["enum"]:
            errs.append(ValidationError(path, kpath + "/enum", f"must be one of {schema['enum']}"))
    if isinstance(inst, str):
        if "pattern" in schema:
            keywords_seen[0] += 1
            if not re.search(schema["pattern"], inst):
                errs.append(ValidationError(path, kpath + "/pattern", f"does not match {schema['pattern']}"))
        if "minLength" in schema or "maxLength" in schema:
            keywords_seen[0] += 1
            if not schema.get("minLength", 0) <= len(inst) <= schema.get("maxLength", 10 ** 9):
                errs.append(ValidationError(path, kpath + "/length", f"length {len(inst)} outside declared bounds"))
    if isinstance(inst, int) and not isinstance(inst, bool):
        for key in ("minimum", "maximum"):
            if key in schema:
                keywords_seen[0] += 1
                ok = inst >= schema[key] if key == "minimum" else inst <= schema[key]
                if not ok:
                    errs.append(ValidationError(path, f"{kpath}/{key}", f"violates {key} {schema[key]}"))
    if isinstance(inst, list):
        if "minItems" in schema:
            keywords_seen[0] += 1
            if len(inst) < schema["minItems"]:
                errs.append(ValidationError(path, kpath + "/minItems", f"fewer than minItems {schema['minItems']}"))
        if "contains" in schema:
            keywords_seen[0] += 1
            if not any(not walk(i, schema["contains"], root, path, kpath + "/contains", [0]) for i in inst):
                errs.append(ValidationError(path, kpath + "/contains", "no item matches the required 'contains' shape"))
        if "items" in schema:
            keywords_seen[0] += 1
            for i, item in enumerate(inst):
                errs += walk(item, schema["items"], root, _ptr_push(path, i), kpath + "/items", keywords_seen)
    if isinstance(inst, dict):
        if "required" in schema:
            keywords_seen[0] += 1
            for req in schema["required"]:
                if req not in inst:
                    errs.append(ValidationError(_ptr_push(path, req), kpath + "/required",
                                                f"missing required property '{req}'"))
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            keywords_seen[0] += 1
            for k in inst:
                if k not in props:
                    errs.append(ValidationError(_ptr_push(path, k), kpath + "/additionalProperties",
                                                f"property '{k}' is not allowed"))
        for k, v in inst.items():
            if k in props:
                errs += walk(v, props[k], root, _ptr_push(path, k), kpath + f"/properties/{k}", keywords_seen)
    return errs


def check(schema_doc: dict, instance) -> tuple[list, int]:
    keywords_seen = [0]
    errs = walk(instance, schema_doc, schema_doc, "", "#", keywords_seen)
    return errs, keywords_seen[0]
