#!/usr/bin/env python3
"""Reference runner: one entry envelope in, one result table out.

Read it in this order: main() is the whole run; plan() is the pure function that
prices the work before anything executes; Run.walk() executes the same tree while
the platform applies correlation, identity, budget, idempotency, provenance and
typed errors that the caller never asked for and cannot decline; the two Adapter
classes are one interface with two implementations.
Python 3.11 standard library only.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# --- Minimal JSON Schema 2020-12 validator ----------------------------------
# Supports exactly the keywords these schemas use; unknown keywords are ignored.
TYPES = {"object": dict, "array": list, "string": str, "integer": int,
         "number": (int, float), "boolean": bool}

def validate(inst, schema, root=None, path="$"):
    """Return a list of human-readable errors. Empty list means valid."""
    root = root if root is not None else schema
    if "$ref" in schema:
        node = root
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        return validate(inst, node, root, path)
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            if not validate(inst, branch, root, path):
                return []
        return [f"{path}: matches none of the allowed step shapes"]
    errs = []
    t = schema.get("type")
    if t:
        want = TYPES[t]
        bad = not isinstance(inst, want) or (t in ("integer", "number") and isinstance(inst, bool))
        if bad:
            return [f"{path}: expected {t}, got {type(inst).__name__}"]
    if "const" in schema and inst != schema["const"]:
        errs.append(f"{path}: must equal {schema['const']!r}")
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: must be one of {schema['enum']}")
    if isinstance(inst, str):
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            errs.append(f"{path}: does not match {schema['pattern']}")
        if not schema.get("minLength", 0) <= len(inst) <= schema.get("maxLength", 10 ** 9):
            errs.append(f"{path}: length {len(inst)} outside declared bounds")
    if isinstance(inst, int) and not isinstance(inst, bool):
        for key, ok in (("minimum", inst >= schema.get("minimum", inst)), ("maximum", inst <= schema.get("maximum", inst))):
            if not ok:
                errs.append(f"{path}: violates {key} {schema[key]}")
    if isinstance(inst, list):
        if len(inst) < schema.get("minItems", 0):
            errs.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "items" in schema:
            for i, item in enumerate(inst):
                errs += validate(item, schema["items"], root, f"{path}[{i}]")
    if isinstance(inst, dict):
        for req in schema.get("required", []):
            if req not in inst:
                errs.append(f"{path}: missing required property '{req}'")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for k in inst:
                if k not in props:
                    errs.append(f"{path}: property '{k}' is not allowed")
        for k, v in inst.items():
            if k in props:
                errs += validate(v, props[k], root, f"{path}.{k}")
    return errs

# --- Typed errors: RFC 9457 problem details ---------------------------------
PROBLEM_BASE = "urn:agentic:problem:"
REGISTRY = {  # type suffix -> (status, title, retryable)
    "document-invalid": (422, "Envelope failed schema validation", False),
    "budget-exhausted": (402, "A step would cross the budget ceiling", False),
    "idempotency-conflict": (409, "Same idempotency key, different envelope", False),
    "adapter-unavailable": (503, "A capability adapter is unreachable", True),
}

class Problem(Exception):
    """A failure the caller can branch on without parsing prose."""
    def __init__(self, suffix, detail, **ext):
        status, title, retryable = REGISTRY[suffix]
        self.body = {"type": PROBLEM_BASE + suffix, "title": title, "status": status,
                     "detail": detail, "retryable": retryable, **ext}
        super().__init__(detail)

# --- Ledger: append-only, hash-chained --------------------------------------
def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))

class Ledger:
    """Every step lands here before the run is allowed to call it done."""
    def __init__(self, path):
        self.path = path
        self.records = [json.loads(l) for l in open(path)] if os.path.exists(path) else []

    def head(self):
        return self.records[-1]["hash"] if self.records else "sha256:" + "0" * 64

    def append(self, **fields):
        rec = {"seq": len(self.records), "prev": self.head(), **fields}
        rec["hash"] = "sha256:" + hashlib.sha256((rec["prev"] + canonical(rec)).encode()).hexdigest()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a") as fh:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
        self.records.append(rec)
        return rec

    def verify(self):
        prev = "sha256:" + "0" * 64
        for i, rec in enumerate(self.records):
            body = {k: v for k, v in rec.items() if k != "hash"}
            want = "sha256:" + hashlib.sha256((prev + canonical(body)).encode()).hexdigest()
            if rec["prev"] != prev or rec["hash"] != want or rec["seq"] != i:
                return f"chain broken at seq {i}"
            prev = rec["hash"]
        return None

    def completed(self, key):
        return next((r for r in self.records
                     if r["kind"] == "run-completed" and r.get("idempotency_key") == key), None)

# --- Criteria: the graded never sees these ----------------------------------
# Rule 6. The criterion body lives here, keyed by the opaque handle a workflow
# carries. Nothing in this dict is ever placed in an adapter prompt.
CRITERIA = {"criterion://fix-acceptable/v1": {"must_contain": ["patch:", "regression verified"]}}

def judge(text, criterion_ref):
    """Pure function (result, criterion) -> verdict."""
    criterion = CRITERIA.get(criterion_ref)
    if criterion is None:
        return "fail", "criterion does not resolve"
    missing = [tok for tok in criterion["must_contain"] if tok not in text]
    return ("pass", "all required evidence present") if not missing else ("fail", f"missing {missing}")

# --- Dispatch: one interface, two adapters ----------------------------------
COST_MICROS = {"free": 0, "low": 15000, "medium": 60000, "high": 200000}

class DryRunAdapter:
    """Deterministic stub. No network, no spend, same bytes every run."""
    name = "dry-run"

    def complete(self, profile, task, step_input, correlation):
        text = self._text(profile, task, step_input)
        jitter = int(hashlib.sha256((profile["name"] + task).encode()).hexdigest()[:4], 16) % 5
        return {"text": text,
                "cost_micros": COST_MICROS[profile["cost_class"]] + jitter * 100,
                "tokens_in": 120 + jitter, "tokens_out": 60 + jitter}

    def _text(self, profile, task, step_input):
        if profile["name"] == "code-fixer":
            attempt = int(step_input.get("attempt", 1))
            base = "patch: 2 hunks in pricing/coupon.py; test_output: 1 failed -> 0 failed"
            return base + (" regression verified" if attempt >= 2 else " (test not re-run)")
        head = "; ".join(f"{k}={str(v)[:40]}" for k, v in list(step_input.items())[:3])
        return f"[{profile['name']}] {task[:70]} :: {head}"

class OpenAICompatibleAdapter:
    """POST /v1/chat/completions against the model gateway (LiteLLM today,
    per PASS.md B3 'Model access'). The interface is the standard; the product
    behind $GATEWAY_URL is replaceable without touching anything above.
    model = the profile's model_class, so the caller names a class, not a vendor."""
    name = "openai-compatible"

    def complete(self, profile, task, step_input, correlation):
        url = os.environ.get("GATEWAY_URL", "").rstrip("/") + "/v1/chat/completions"
        body = json.dumps({
            "model": profile["model_class"],
            "messages": [{"role": "system", "content": f"You are {profile['name']}. "
                                                       f"Good at: {'; '.join(profile['good_at'])}."},
                         {"role": "user", "content": f"{task}\n\ninput: {json.dumps(step_input)}"}],
        }).encode()
        req = urllib.request.Request(url, data=body, headers={
            "content-type": "application/json",
            "authorization": "Bearer " + os.environ.get("GATEWAY_KEY", ""),
            "x-correlation-id": correlation["correlation_id"],   # A7 finding 1: explicit, not traceparent
            "x-run-id": correlation["run_id"],
        })
        try:
            with urllib.request.urlopen(req, timeout=int(os.environ.get("GATEWAY_TIMEOUT_S", "120"))) as r:
                data = json.load(r)
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}") from exc
        usage = data.get("usage", {})
        return {"text": data["choices"][0]["message"]["content"],
                "cost_micros": int(float(data.get("cost", 0)) * 1_000_000) or COST_MICROS[profile["cost_class"]],
                "tokens_in": usage.get("prompt_tokens", 0), "tokens_out": usage.get("completion_tokens", 0)}

# --- Planner: pure. Runs to completion before anything executes -------------
def plan(workflow, agents, envelope, loop_iterations="max"):
    """envelope + workflow -> (step list, cost in micros). No side effects.
    loop_iterations="max" prices the worst case; 1 prices the shortest path that can still finish."""
    steps = []

    def walk(node, iteration=None):
        op, sid = node["op"], node["id"] + (f"#{iteration}" if iteration else "")
        if op == "sequence":
            for child in node["steps"]:
                walk(child, iteration)
        elif op == "parallel":
            for branch in node["branches"]:
                walk(branch, iteration)
        elif op == "loop":
            for i in range(1, (node["max_iterations"] if loop_iterations == "max" else 1) + 1):
                walk(node["body"], i)
        elif op == "agent":
            profile = agents[node["agent"]]
            steps.append({"id": sid, "op": op, "agent": node["agent"],
                          "model_class": profile["model_class"],
                          "estimate_micros": COST_MICROS[profile["cost_class"]]})
        else:  # judge and approval are platform work, not metered calls
            steps.append({"id": sid, "op": op, "agent": "-", "model_class": "-", "estimate_micros": 0})

    walk(workflow["root"])
    return steps, sum(s["estimate_micros"] for s in steps)

# --- Executor: the cross-cutting concerns live here, not in the workflow ----
class Run:
    def __init__(self, envelope, workflow, agents, adapter, ledger, approval):
        self.env, self.wf, self.agents = envelope, workflow, agents
        self.adapter, self.ledger, self.approval = adapter, ledger, approval
        self.remaining = envelope["budget"]["ceiling_micros"]
        self.results, self.rows, self.stopped = {}, [], False
        self.clock = datetime.strptime(envelope["occurred_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    def record(self, kind, **fields):
        self.clock += timedelta(seconds=1)
        c = self.env["correlation"]
        return self.ledger.append(
            ts=self.clock.isoformat().replace("+00:00", "Z"), kind=kind,
            run_id=c["run_id"], correlation_id=c["correlation_id"],
            actor=self.env["actor"]["subject"],
            delegation_depth=len(self.env["actor"]["delegation_chain"]),
            entry_kind=self.env["kind"], idempotency_key=self.env["idempotency_key"],
            budget_remaining_micros=self.remaining, **fields)

    def spend(self, step_id, estimate):
        if self.remaining < estimate:
            raise Problem("budget-exhausted",
                          f"step {step_id} estimated {estimate} micros, {self.remaining} left",
                          step_id=step_id, correlation=self.env["correlation"])

    def call_agent(self, node, iteration):
        sid = node["id"] + (f"#{iteration}" if iteration else "")
        profile = self.agents[node["agent"]]
        self.spend(sid, COST_MICROS[profile["cost_class"]])
        step_input = {"attempt": iteration or 1}
        for ref in node["input_from"]:
            step_input[ref] = (json.dumps(self.env["payload"])[:200] if ref == "entry.payload"
                               else self.results.get(ref, {}).get("text", "not produced")[:200])
        if "fix-judge" in node["input_from"]:  # rule 6: the verdict travels, the criterion does not
            step_input["previous_verdict"] = self.results.get("fix-judge", {}).get("verdict", "none")
            step_input.pop("fix-judge", None)
        out = self.adapter.complete(profile, node["task"], step_input, self.env["correlation"])
        self.remaining -= out["cost_micros"]
        self.results[node["id"]] = out
        self.record("agent-called", step_id=sid, op="agent", agent=node["agent"],
                    model_class=profile["model_class"], cost_micros=out["cost_micros"],
                    output_digest="sha256:" + hashlib.sha256(out["text"].encode()).hexdigest(),
                    detail=out["text"][:90])
        self.rows.append((sid, "agent", profile["model_class"], out["cost_micros"], self.remaining, "ok"))

    def run_judge(self, node, iteration):
        sid = node["id"] + (f"#{iteration}" if iteration else "")
        verdict, reason = judge(self.results.get(node["of"], {}).get("text", ""), node["criterion_ref"])
        self.results[node["id"]] = {"text": verdict, "verdict": verdict}
        self.record("judged", step_id=sid, op="judge", criterion_ref=node["criterion_ref"],
                    verdict=verdict, cost_micros=0, detail=reason)
        self.rows.append((sid, "judge", "-", 0, self.remaining, verdict))
        return verdict

    def run_approval(self, node):
        self.record("approval-parked", step_id=node["id"], op="approval", cost_micros=0, detail=node["asks"])
        decision = self.approval
        self.record("approval-returned", step_id=node["id"], op="approval", cost_micros=0,
                    decision=decision, detail=f"human returned '{decision}' on the same correlation id")
        self.rows.append((node["id"], "approval", "-", 0, self.remaining, decision))
        if decision == "reject" and node.get("on_reject", "stop") == "stop":
            self.stopped = True

    def walk(self, node, iteration=None):
        if self.stopped:
            return
        op = node["op"]
        if op == "sequence":
            for child in node["steps"]:
                self.walk(child, iteration)
        elif op == "parallel":  # one process here; the fan-out is the contract, not the threading
            for branch in node["branches"]:
                self.walk(branch, iteration)
        elif op == "loop":
            for i in range(1, node["max_iterations"] + 1):
                self.walk(node["body"], i)
                if self.results.get(node["exit_when"]["judge_step"], {}).get("verdict") == node["exit_when"]["verdict"]:
                    break
        elif op == "agent":
            self.call_agent(node, iteration)
        elif op == "judge":
            self.run_judge(node, iteration)
        elif op == "approval":
            self.run_approval(node)

# --- Wiring -----------------------------------------------------------------
def load(rel):
    with open(os.path.join(HERE, rel)) as fh:
        return json.load(fh)

def table(rows, header):
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    line = "  ".join("-" * w for w in widths)
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)) + "\n" + line)
    for r in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(r, widths)))

def fail(problem):
    print("PROBLEM (application/problem+json):\n" + json.dumps(problem.body, indent=2))
    return 2

def main(argv=None):
    ap = argparse.ArgumentParser(description="Run one entry envelope through the platform.")
    ap.add_argument("--entry", help="path to an entry envelope")
    ap.add_argument("--ledger", default=os.path.join(OUT, "ledger.jsonl"))
    ap.add_argument("--budget-micros", type=int, help="override the envelope ceiling (used to trip enforcement)")
    ap.add_argument("--approval", default="approve", choices=["approve", "edit", "reject"])
    ap.add_argument("--live", action="store_true", help="dispatch through the gateway instead of the stub")
    ap.add_argument("--verify-ledger", action="store_true")
    args = ap.parse_args(argv)
    ledger = Ledger(args.ledger)
    if args.verify_ledger:
        broken = ledger.verify()
        print(f"ledger {args.ledger}: {len(ledger.records)} records, " + (broken or "chain verifies"))
        return 2 if broken else 0
    if not args.entry:
        ap.error("--entry is required unless --verify-ledger is given")

    envelope = json.load(open(args.entry))
    errs = validate(envelope, load("schemas/entry.schema.json"))
    if errs:
        return fail(Problem("document-invalid", "; ".join(errs[:4]), instance=args.entry))
    if args.budget_micros is not None:
        envelope["budget"]["ceiling_micros"] = args.budget_micros
    digest = "sha256:" + hashlib.sha256(canonical(envelope).encode()).hexdigest()

    prior = ledger.completed(envelope["idempotency_key"])
    if prior:
        if prior["envelope_digest"] != digest:
            return fail(Problem("idempotency-conflict", f"key {envelope['idempotency_key']} was completed "
                                                        f"at seq {prior['seq']} with a different body"))
        print(f"REPLAY: idempotency key already completed at seq {prior['seq']}; nothing re-run, nothing appended.")
        table([(prior["run_id"], prior["entry_kind"], prior["cost_micros"], prior["detail"])],
              ("run_id", "entry", "spent_micros", "outcome"))
        return 0

    workflow = load(envelope["intent"]["workflow_ref"])
    agents = {a["name"]: a for a in load("agents.json")["agents"]}
    steps, estimate = plan(workflow, agents, envelope)          # pure, before anything runs
    floor = plan(workflow, agents, envelope, loop_iterations=1)[1]
    ceiling = envelope["budget"]["ceiling_micros"]
    print(f"PLAN  {workflow['name']}: {len(steps)} steps, worst case {estimate} micros, "
          f"shortest finishing path {floor}, ceiling {ceiling}")
    table([(s["id"], s["op"], s["agent"], s["model_class"], s["estimate_micros"]) for s in steps],
          ("step", "op", "agent", "model_class", "est_micros"))

    run = Run(envelope, workflow, agents, OpenAICompatibleAdapter() if args.live else DryRunAdapter(),
              ledger, args.approval)
    try:
        if floor > ceiling:
            raise Problem("budget-exhausted", f"shortest finishing path costs {floor}, ceiling is {ceiling}; "
                                              f"refused before execution", correlation=envelope["correlation"])
        run.record("run-started", step_id="-", op="-", cost_micros=0, envelope_digest=digest,
                   adapter=run.adapter.name, plan_estimate_micros=estimate, detail=envelope["intent"]["summary"])
        run.walk(workflow["root"])
    except Problem as p:
        run.record("run-refused", step_id=p.body.get("step_id", "-"), op="-", cost_micros=0,
                   envelope_digest=digest, problem_type=p.body["type"], detail=p.body["detail"])
        return fail(p)

    spent = ceiling - run.remaining
    outcome = "stopped-on-reject" if run.stopped else "completed"
    run.record("run-completed", step_id="-", op="-", cost_micros=spent, envelope_digest=digest,
               adapter=run.adapter.name, detail=outcome)
    print(f"\nRESULT  entry={envelope['kind']}  actor={envelope['actor']['subject']}  "
          f"correlation={envelope['correlation']['correlation_id']}")
    table(run.rows, ("step", "op", "model_class", "cost_micros", "budget_left", "outcome"))
    print(f"\n{outcome}: {len(run.rows)} steps, spent {spent} of {ceiling} micros, "
          f"estimate was {estimate}. Ledger head {ledger.head()[:19]}...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
