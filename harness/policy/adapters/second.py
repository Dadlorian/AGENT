#!/usr/bin/env python3
"""Second adapter: a typed entity model, evaluated in the calling process.

Where the first binding queries an engine with an open JSON document, this one
compiles the bundle into a typed entity model and evaluates it as a function
call, with no process to reach. The recorded swap candidate for this capability
is Cedar, alongside any policy engine with a decision API (F-b3-11). Search-only
research describes it as more strict and structured with emphasis on safety by
default, deny by default (X-cap-policy-004). Product names are allowed in this
file.

The point of the pair is the inverted failure mode. An open document query can
read anything the caller happened to send; a typed entity model can only decide
over attributes it declares. So this binding compiles the rules first, and any
decision point whose rules read a path outside the entity model is declared as a
conformance subset and refused - never answered allow. Here that is
dispatch.data_query, whose rule reads a free-form resource.query.

Reachability: this is a faithful stub of that execution model, not a Cedar
binding. It marshals entities, refuses what its model cannot express, and is
recompiled when a bundle is activated - the shape and the swap procedure are
real; the engine is not linked in. Standard library only, no network at all.
"""
from __future__ import annotations

from interface import DecisionRequest, PolicyAdapter, Problem

FIELD_OPS = {"eq_field", "ne_field"}
KINDS = {"string": str, "set": list, "integer": int, "boolean": bool}


class TypedEntityPolicyAdapter(PolicyAdapter):
    entity = "in-process typed entity evaluation"
    decision_model = "typed entity set, marshalled before evaluation"
    activation_model = "entity model and rules recompiled into the process on activation"
    processes_required = "none; the pinned rule set is evaluated in the calling process with no network hop"
    declared_marker = "in-process-decision"
    report_adapter = "in-process-typed-entity"

    # --- activation: compile, and declare what cannot be expressed ----------
    def _activated(self, bundle: dict, version: str) -> None:
        self.recompiles = getattr(self, "recompiles", 0) + 1
        self.programs = getattr(self, "programs", {})
        model = bundle.get("entity_model", {})
        attributes = {path: kind for name, attrs in model.items() if name != "_note"
                      for path, kind in attrs.items()}
        compiled, unexpressible = [], set()
        for rule in bundle["rules"]:
            paths = [c["path"] for c in rule["when"]]
            paths += [c["value"] for c in rule["when"] if c["op"] in FIELD_OPS]
            if all(p in attributes for p in paths):
                compiled.append(rule)
            elif rule["decision_point"] == "*":
                unexpressible.update(self.points)
            else:
                unexpressible.add(rule["decision_point"])
        # One compiled program per version, so replaying an older pinned bundle
        # never changes what the active one decides.
        self.programs[version] = {"attributes": attributes, "rules": compiled,
                                  "default": bundle["default"], "subset": tuple(sorted(unexpressible))}
        self.conformance_subset = self.programs[version]["subset"]

    # --- evaluation: entities in, determination out -------------------------
    def _entities(self, request: DecisionRequest, attributes: dict) -> dict:
        doc = request.as_dict()
        entities = {}
        for path, kind in attributes.items():
            cursor = doc
            for part in path.split("."):
                cursor = cursor.get(part) if isinstance(cursor, dict) else None
            if cursor is not None and not isinstance(cursor, KINDS[kind]):
                raise Problem("adapter-unavailable",
                              f"entity attribute {path} is declared {kind} and arrived as "
                              f"{type(cursor).__name__}; this binding cannot express a decision over it",
                              decision_point=request.decision_point, retry_after_s=0)
            entities[path] = cursor
        return entities

    @staticmethod
    def _holds(condition: dict, entities: dict) -> bool:
        got, op, value = entities.get(condition["path"]), condition["op"], condition.get("value")
        if op == "eq":
            return got == value
        if op == "ne":
            return got != value
        if op == "exists":
            return got is not None
        if op == "empty":
            return not got
        if op == "nonempty":
            return bool(got)
        if op == "eq_field":
            return got == entities.get(value)
        if op == "ne_field":
            return got != entities.get(value)
        raise Problem("adapter-unavailable", f"operator {op!r} is outside this binding's model", retry_after_s=0)

    def _evaluate(self, request: DecisionRequest, bundle: dict) -> tuple[str, str, str]:
        program = self.programs[request.policy_version]   # the pinned version's own compiled program
        entities = self._entities(request, program["attributes"])
        for rule in program["rules"]:
            if rule["decision_point"] not in ("*", request.decision_point):
                continue
            if all(self._holds(condition, entities) for condition in rule["when"]):
                self.observed_marker = self.declared_marker
                return rule["effect"], rule["rule_id"], rule["detail"]
        self.observed_marker = self.declared_marker
        return program["default"]["effect"], program["default"]["rule_id"], program["default"]["detail"]


# The one name every adapter module exports: the entry point of this module.
Adapter = TypedEntityPolicyAdapter
