#!/usr/bin/env python3
"""Second adapter: compile the schema once, then check instances against the
compiled form -- a different execution model from the walk-per-document
adapters (F-b1-04, build-adapter-pair). Where dryrun.py and live.py
re-interpret the raw schema dict on every call, prepare() here turns the
schema into a tree of closures exactly once; validate() never looks at a
schema keyword again, it only calls closures that were already built.

cap-document-validation-implement names the swap candidate as a compiled
validator "in a different language runtime, reached out of process" (proposed).
This adapter is a faithful stub of that shape (author brief: real shape and
real swap procedure, stub where the component is unreachable): with
DOCVALID_SECOND_SUBPROCESS unset it runs the compiled tree in this process;
set to 1, it hands the compiled-check step to a short-lived subprocess instead,
so processes_required_for_progress genuinely changes with configuration, no
code edit. Standard library only.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

from interface import (DIALECT_2020_12, TYPES, DocumentValidationAdapter, PreparedHandle,
                       Problem, REPO_ROOT, ValidationError, _ptr_push, load_json_file, resolve_path)

HERE = os.path.dirname(os.path.abspath(__file__))


# --- the compiler: schema keywords are read exactly once, here -------------
def compile_node(schema: dict, root: dict):
    """schema -> callable(inst, path, kpath, counter) -> list[ValidationError].

    Every keyword this schema declares is inspected once, at compile time;
    what is returned closes over the precomputed parts (a compiled regex, the
    resolved $ref target, each property's own compiled function) so a later
    check never re-reads schema structure.
    """
    if "$ref" in schema:
        parts = schema["$ref"].lstrip("#/").split("/")
        node = root
        for part in parts:
            node = node[part]
        target = compile_node(node, root)
        return lambda inst, path, kpath, counter: target(inst, path, kpath + "/$ref", counter)

    if "anyOf" in schema:
        branches = [compile_node(b, root) for b in schema["anyOf"]]

        def check_any_of(inst, path, kpath, counter):
            for i, branch in enumerate(branches):
                if not branch(inst, path, f"{kpath}/anyOf/{i}", [0]):
                    return []
            return [ValidationError(path, kpath + "/anyOf", "matches none of the allowed branches")]
        return check_any_of

    if_fn = compile_node(schema["if"], root) if "if" in schema else None
    then_fn = compile_node(schema["then"], root) if "then" in schema else None
    else_fn = compile_node(schema["else"], root) if "else" in schema else None
    want_type = TYPES.get(schema.get("type")) if schema.get("type") else None
    const = schema.get("const", _MISSING)
    enum = schema.get("enum")
    pattern = re.compile(schema["pattern"]) if "pattern" in schema else None
    min_len, max_len = schema.get("minLength", 0), schema.get("maxLength", 10 ** 9)
    has_len = "minLength" in schema or "maxLength" in schema
    minimum, maximum = schema.get("minimum"), schema.get("maximum")
    min_items = schema.get("minItems")
    contains_fn = compile_node(schema["contains"], root) if "contains" in schema else None
    items_fn = compile_node(schema["items"], root) if "items" in schema else None
    required = tuple(schema.get("required", ()))
    props = {k: compile_node(v, root) for k, v in schema.get("properties", {}).items()}
    closed = schema.get("additionalProperties") is False
    type_name = schema.get("type")

    def check(inst, path, kpath, counter):
        errs: list = []
        if if_fn is not None:
            counter[0] += 1
            branch_fn = then_fn if not if_fn(inst, path, kpath + "/if", [0]) else else_fn
            if branch_fn is not None:
                errs += branch_fn(inst, path, kpath + ("/then" if branch_fn is then_fn else "/else"), counter)
        if want_type is not None:
            counter[0] += 1
            bad = not isinstance(inst, want_type) or (type_name in ("integer", "number") and isinstance(inst, bool))
            if bad:
                return errs + [ValidationError(path, kpath + "/type", f"expected {type_name}, got {type(inst).__name__}")]
        if const is not _MISSING:
            counter[0] += 1
            if inst != const:
                errs.append(ValidationError(path, kpath + "/const", f"must equal {const!r}"))
        if enum is not None:
            counter[0] += 1
            if inst not in enum:
                errs.append(ValidationError(path, kpath + "/enum", f"must be one of {enum}"))
        if isinstance(inst, str):
            if pattern is not None:
                counter[0] += 1
                if not pattern.search(inst):
                    errs.append(ValidationError(path, kpath + "/pattern", f"does not match {pattern.pattern}"))
            if has_len:
                counter[0] += 1
                if not min_len <= len(inst) <= max_len:
                    errs.append(ValidationError(path, kpath + "/length", f"length {len(inst)} outside declared bounds"))
        if isinstance(inst, int) and not isinstance(inst, bool):
            if minimum is not None:
                counter[0] += 1
                if inst < minimum:
                    errs.append(ValidationError(path, kpath + "/minimum", f"violates minimum {minimum}"))
            if maximum is not None:
                counter[0] += 1
                if inst > maximum:
                    errs.append(ValidationError(path, kpath + "/maximum", f"violates maximum {maximum}"))
        if isinstance(inst, list):
            if min_items is not None:
                counter[0] += 1
                if len(inst) < min_items:
                    errs.append(ValidationError(path, kpath + "/minItems", f"fewer than minItems {min_items}"))
            if contains_fn is not None:
                counter[0] += 1
                if not any(not contains_fn(i, path, kpath + "/contains", [0]) for i in inst):
                    errs.append(ValidationError(path, kpath + "/contains", "no item matches the required 'contains' shape"))
            if items_fn is not None:
                counter[0] += 1
                for i, item in enumerate(inst):
                    errs += items_fn(item, _ptr_push(path, i), kpath + "/items", counter)
        if isinstance(inst, dict):
            if required:
                counter[0] += 1
                for req in required:
                    if req not in inst:
                        errs.append(ValidationError(_ptr_push(path, req), kpath + "/required",
                                                    f"missing required property '{req}'"))
            if closed:
                counter[0] += 1
                for k in inst:
                    if k not in props:
                        errs.append(ValidationError(_ptr_push(path, k), kpath + "/additionalProperties",
                                                    f"property '{k}' is not allowed"))
            for k, v in inst.items():
                if k in props:
                    errs += props[k](v, _ptr_push(path, k), kpath + f"/properties/{k}", counter)
        return errs

    return check


class _Missing:
    def __repr__(self):
        return "<no const declared>"


_MISSING = _Missing()


class CompiledSchemaAdapter(DocumentValidationAdapter):
    entity = "compiled-schema checker (compile once, check many)"
    execution_model = "schema compiled ahead of use"
    processes_required_for_progress = 0
    declared_marker = "compiled-tree-check"

    def __init__(self):
        super().__init__()
        self._subprocess = bool(os.environ.get("DOCVALID_SECOND_SUBPROCESS"))
        if self._subprocess:
            self.processes_required_for_progress = 1
            self.declared_marker = "compiled-subprocess-check"

    def _read_schema(self, schema_uri: str) -> dict:
        path = resolve_path(schema_uri, REPO_ROOT)
        return load_json_file(path, schema_uri)

    def _compile(self, schema_doc: dict) -> object:
        self.prepares += 1     # the one place schema structure is ever read
        return compile_node(schema_doc, schema_doc)

    def _check(self, handle: PreparedHandle, instance) -> tuple[list, int]:
        if self._subprocess:
            return self._check_out_of_process(handle, instance)
        counter = [0]
        errs = handle.compiled(instance, "", "#", counter)
        return errs, counter[0]

    def _check_out_of_process(self, handle: PreparedHandle, instance) -> tuple[list, int]:
        """A genuine separate process: recompiles in a child, since the compiled
        closures cannot cross a process boundary. Honest about the tradeoff
        (declared_gaps): a subprocess pays a compile cost this stub's in-process
        path does not, which is the axis a native out-of-process validator
        would also pay."""
        worker = os.path.join(HERE, "_second_worker.py")
        payload = json.dumps({"schema": handle.schema_doc, "instance": instance}).encode()
        try:
            proc = subprocess.run([sys.executable, worker], input=payload, capture_output=True,
                                  timeout=10, check=True)
        except (OSError, subprocess.SubprocessError) as exc:
            raise Problem("schema-unavailable", f"the out-of-process checker could not run: {exc}",
                          retry_after_s=5) from exc
        result = json.loads(proc.stdout.decode())
        errs = [ValidationError(**e) for e in result["errors"]]
        return errs, result["keywords_checked"]


Adapter = CompiledSchemaAdapter
