#!/usr/bin/env python3
"""done - how I know a unit is finished, and what happens next.

One envelope from one of the four doors names a closure declaration. This
runner reads each finished unit's check report, seals what the unit leaves
behind, attests it at the one wired boundary, appends the record through the
state seam at a pinned head, puts each promotable subject through an admission
gate that verifies the attestation before anything is promoted, notifies the
door that asked, and closes with one ledger line carrying the cost.

Read it in this order: main() is the whole run; Close.identity_chain() rebuilds
the delegation chain the envelope declares and adds one hop for the executing
unit; Close.close_unit() is the per-unit path (seal, attest, append);
Close.gate() is the admission decision that stands between an artifact and its
promotion; and Close.record() is the single write path - every record is
appended through the state seam first, and the ledger file is written from what
the store returned.

Nothing here re-runs a unit: the units arrive finished, with their check reports
and their costs declared by the run that spent them (README section 6, gap G1).
Dependency-free Python 3.11, no network.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
sys.path.insert(0, HERE)
import harnesses  # noqa: E402

CLOCK = os.environ.get("DONE_CLOCK", "2026-09-03T12:00:00Z")
# Where the object-store binding puts its objects: inside this example's own
# out/, never in the harness's scratch directory, so `rm -rf out` is a clean
# slate and two runs of the same door cannot accumulate into one partition.
os.environ.setdefault("OBJSTORE_DIR", os.path.join(OUT, "objectstore"))

# What an outside issuer handed the door: a fixture standing in for a credential
# this platform did not mint. The caller region never builds one, and no scope
# here is read out of the envelope's payload.
ROOT_SCOPE = ("read:incident", "call:model", "write:ledger")
ROOT_LIFETIME_S = 3600
HOP_LIFETIME_DIVISOR = 2                        # each hop holds half of what the one above it held


def hop_lifetime(index: int) -> int:
    """How long the hop at `index` is issued for, computed from the root's
    lifetime and the declared divisor. Nothing here is a written-down list, so
    the ladder is as long as the chain the caller declared - a chain the entry
    schema does not bound - rather than as long as a tuple in this file."""
    return max(1, ROOT_LIFETIME_S // (HOP_LIFETIME_DIVISOR ** (index + 1)))


# The closure names the predicate its full statement carries; the URI that name
# resolves to belongs to the provenance interface and is never written here.
PREDICATE_BY_NAME = {"agent-action": "PREDICATE_AGENT_ACTION", "build": "PREDICATE_BUILD"}

LADDER_TASK = "task success"
LADDER_CANDIDATE = "candidate completion"

# Which subject kind crosses which declared materiality threshold. The mapping
# is data; which of these the run acts on is read off the declaration.
THRESHOLD_OF = {"work_product": "produced-artifact", "refusal_record": "refusal-worth-auditing",
                "failure_report": "failure-worth-auditing", "candidate_held": "candidate-held"}

SURFACES = {"shell-line": "one line on the caller's own terminal, on the same correlation id",
            "callback": "a callback to the system that raised the event",
            "digest": "one digest to the principal the schedule acts for",
            "task-status": "a task-status update on the task the partner submitted"}


def sha256_of(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def code_version() -> dict:
    """What produced it: exact script digests, not a branch name."""
    scripts = {name: hashlib.sha256(open(os.path.join(HERE, name), "rb").read()).hexdigest()
               for name in ("run.py", "harnesses.py")}
    return {"scripts_sha256": scripts, "git_commit": os.environ.get("GIT_COMMIT", "unset"),
            "interface_version": "0.1"}


def narrow_ladder(root_scope, required, hops: int) -> list:
    """The scope each hop is issued with: what the promotion declares it needs,
    plus the scopes not yet dropped, spread so that the last hop holds exactly
    the required scope and no hop ever holds more than the one before it.
    Computed from the two declarations, so no ladder is written down here."""
    droppable = [s for s in root_scope if s not in required]
    out = []
    for i in range(hops):
        dropped = -(-(i + 1) * len(droppable) // hops)        # ceiling division
        keep = [s for s in root_scope if s in required or s in droppable[dropped:]]
        # what the promotion declares it needs and the root never held is asked
        # for all the same: that is how a hop that would widen gets refused
        # rather than quietly issued narrower than the action requires.
        out.append(tuple(keep + [s for s in required if s not in root_scope]))
    return out


class Refusal(Exception):
    """One refusal shape reaching the caller: an RFC 9457 problem body."""

    def __init__(self, body: dict) -> None:
        self.body = body
        super().__init__(body.get("detail", ""))


class Close:
    def __init__(self, args) -> None:
        self.args = args
        self.errors_iface, self.problem_mod = harnesses.errors()
        self.reference = harnesses.reference()
        self.prov_iface, prov_adapter = harnesses.provenance(args.prov_adapter)
        self.state_iface, state_adapter = harnesses.state(args.state_adapter)
        self.id_iface, id_adapter = harnesses.identity(args.identity_adapter)
        self.emit = harnesses.emit()
        self.envelope = json.load(open(args.entry))
        # nothing is derived from an envelope that has not been checked yet: the
        # members below are read back in validate(), which runs first.
        self.door = self.envelope.get("kind", "unvalidated")
        self.corr = self.envelope.get("correlation") or {"run_id": "unset", "correlation_id": "unset"}
        self.key = self.envelope.get("idempotency_key", "")
        self.closure_path = ""
        self.prov_root = args.prov_root
        os.makedirs(OUT, exist_ok=True)
        # one binding takes a store path, the other holds its log in process: the
        # difference is the binding's, so it is asked for rather than assumed.
        # The path is derived from --prov-root, so one flag names one period:
        # the envelopes, the artifacts and the manifest of a run move together
        # and two runs with different roots cannot share and truncate one store.
        self._prov_adapter = prov_adapter
        self._prov_kwargs = ({"path": os.path.join(self.prov_root, f"envelopes-{self.door}.jsonl")}
                             if args.prov_adapter == "dryrun" else {})
        self._prov = None
        self.state = state_adapter()
        self.ident = id_adapter()
        self.ledger = self.reference.Ledger(args.ledger)
        self.problems = (self.id_iface.Problem, self.state_iface.Problem, self.prov_iface.Problem)
        self.cost_micros = 0
        self.head = None
        self.head_at_first = None
        self.records_pre_redaction = []
        self.publisher = None
        self.root_subject = None
        self.chain_actors = []
        self.hop_trace = []
        self.locations = {}                # subject digest -> where it was published
        self.rows = []                     # one row per closed unit
        self.promoted = []

    @property
    def prov(self):
        """The attestation binding, built at first use and never at construction.
        A run that is refused before it attests anything - a replay, an envelope
        that does not validate - opens no store, so it cannot truncate the one
        the run that did the work left behind."""
        if self._prov is None:
            self._prov = self._prov_adapter(**self._prov_kwargs)
        return self._prov

    # --- refusals -----------------------------------------------------------
    def refuse(self, suffix: str, detail: str, **ext) -> Refusal:
        """Every refusal that ends this run is built at the one construction
        point the errors capability owns, against its closed registry."""
        return Refusal(self.errors_iface.construct(
            suffix, detail, correlation_id=self.corr["correlation_id"], **ext).body())

    @property
    def partition(self) -> str:
        return self.closure["retention"]["partition"] + "-" + self.corr["correlation_id"]

    # --- 1. the envelope ----------------------------------------------------
    def validate(self) -> None:
        schema = json.load(open(os.path.join(harnesses.ROOT, "examples", "end-to-end",
                                             "schemas", "entry.schema.json")))
        errs = self.reference.validate(self.envelope, schema)
        if errs:
            raise self.refuse("document-invalid",
                              f"the envelope at {self.args.entry} does not validate against the entry "
                              f"schema this platform publishes; nothing was closed", causes=errs[:4])
        self.closure_path = os.path.join(HERE, self.envelope["intent"]["workflow_ref"])
        self.closure = json.load(open(self.closure_path))

    # --- 2. the chain the envelope declares, plus one hop for the executor ---
    def identity_chain(self) -> None:
        declared = self.envelope["actor"]["delegation_chain"]
        root = declared[-1]
        self.root_subject = root["actor"]
        required = tuple(self.closure["promotion"]["requires_scope"])
        audience = self.closure["promotion"]["audience"]
        # obtained_via is read here, where the root is admitted: a chain rooted in
        # a hop nothing attested or authenticated is refused before anything runs.
        cred = self.ident.verify(self.ident.fixture_presented(
            root["actor"], ROOT_SCOPE, "svc:done", ROOT_LIFETIME_S, root["obtained_via"]))
        self.chain_actors = [root["actor"]]
        self.hop_trace = [{"hop": 0, "actor": cred.actor,
                           "declared_obtained_via": root["obtained_via"],
                           "obtained_via": cred.chain[0].obtained_via,
                           "scope": sorted(cred.scope), "remaining_s": cred.remaining_s(),
                           "chain_length": len(cred.chain)}]
        # every declared hop is carried, not just its actor: the way each one says
        # it obtained the right to act is what its presented credential asserts.
        above = list(reversed(declared[:-1]))
        # the last hop is this platform's own and nothing in the envelope declares
        # it, so its declared value is null rather than a value invented for it.
        executor = {"actor": f"agent:closer-{self.door}", "obtained_via": None}
        ladder = narrow_ladder(ROOT_SCOPE, required, len(above) + 1)
        for i, hop in enumerate(above + [executor]):
            actor, declared_via = hop["actor"], hop["obtained_via"]
            scope, lifetime = ladder[i], hop_lifetime(i)
            held = self.ident.attest(self.id_iface.AttestRequest.from_dict({
                "unit": actor, "audience": audience, "scope": scope, "lifetime_s": lifetime,
                "platform_facts": {"cell": f"cell-{i:02d}", "closure": self.closure["closure_id"]},
                "presented": self.ident.fixture_presented(actor, scope, "svc:done", lifetime,
                                                          declared_via or "direct")}))
            cred = self.ident.delegate(self.id_iface.DelegationRequest.from_dict({
                "subject": cred, "actor": held, "scope": scope, "audience": audience,
                "lifetime_s": lifetime}))
            self.chain_actors.insert(0, actor)
            # what the binding answered with, hop by hop: the scope it issued and
            # the seconds left on it, read off the credential rather than off the
            # ladder that asked for it - beside what the envelope declared, which
            # for a hop this platform issues itself is the binding's to name
            # (README gap G14).
            self.hop_trace.append({"hop": i + 1, "actor": cred.actor,
                                   "declared_obtained_via": declared_via,
                                   "obtained_via": cred.chain[0].obtained_via,
                                   "scope": sorted(cred.scope),
                                   "remaining_s": cred.remaining_s(),
                                   "chain_length": len(cred.chain)})
        self.ident.authorise(cred, required[0])       # the action needs this, or nothing proceeds
        self.publisher = cred

    # --- 3. the single write path -------------------------------------------
    def record(self, kind: str, body: dict, cost_micros: int = 0) -> dict:
        """Append through the state seam at the head this run last resolved, then
        write the ledger line from what the store returned. The store arbitrates
        the writer; the file is the receipt projection of the appended stream."""
        if self.head is None:
            self.head = self.state.resolve_head(self.partition)
        rec, self.head = self.state.append(self.state_iface.AppendRequest.from_dict({
            "partition": self.partition, "kind": kind, "body": body,
            "fencing_token": self.head.size + 1,
            "expected_head": self.head.chain_digest if self.head.size else None}))
        if self.head_at_first is None:
            self.head_at_first = self.head
        self.cost_micros += cost_micros
        line = {"kind": kind, "run_id": self.corr["run_id"],
                "correlation_id": self.corr["correlation_id"],
                "actor": self.publisher.actor if self.publisher else self.envelope["actor"]["subject"],
                "triggering_identity": self.root_subject or self.envelope["actor"]["subject"],
                "delegation_depth": len(self.chain_actors), "entry_kind": self.door,
                "idempotency_key": self.key, "cost_micros": cost_micros,
                "state_record_id": rec.record_id, "state_head_size": self.head.size,
                "state_root_hash": self.head.root_hash,
                "body_digest": sha256_of(canonical(body))}
        # the notification body is the only thing the receipt does not carry: it
        # holds the reporter's own words, and retention keeps it in one place.
        line.update({k: v for k, v in body.items() if k != "notification_body"})
        return self.ledger.append(**line)

    # --- 4. one finished unit ------------------------------------------------
    def close_unit(self, unit: dict) -> dict:
        report = unit["check_report"]
        failed = [c["check_id"] for c in report["deciding"] if c["outcome"] != "pass"]
        if unit.get("refusal"):
            rung, state, disposition = "none", "rejected", "reject"
        elif report["behavioural_run"] == 0:
            # a report whose behavioural_run is 0 is inconclusive, never passed
            rung, state, disposition = LADDER_CANDIDATE, "input-required", "escalate"
        elif failed:
            rung, state, disposition = LADDER_CANDIDATE, "failed", "escalate"
        else:
            rung, state, disposition = LADDER_TASK, "completed", "accept"
        produced = unit["produced"]
        payload = produced["text"].encode()
        digest = sha256_of(payload)
        self.record("unit-closed", {
            "unit_id": unit["unit_id"], "task_state": state, "disposition": disposition,
            "ladder_rung": rung, "attempts": unit["attempts"], "model_class": unit["model_class"],
            "stop_reason": unit["stop_reason"], "behavioural_run": report["behavioural_run"],
            "deciding_failed": failed, "refused_by": (unit.get("refusal") or {}).get("rule_id", ""),
        }, cost_micros=unit["cost_micros"])

        # The wired boundary: every subject gets a record here whatever the
        # materiality declaration says, and nothing below this call names a
        # signer, a key or a store.
        light = self.emit.attest_and_record(self.prov_root, produced["name"], payload,
                                            actor=self.publisher.actor)
        thresholds = self.closure["attestation"]["materiality"]       # read at the decision
        full = "every-unit" in thresholds or THRESHOLD_OF[produced["subject_kind"]] in thresholds
        if self.args.brk == "unattested" and produced["subject_kind"] == "work_product":
            full = False                    # the breakage: the promotable subject is never attested
        statement_id, predicate_type = light["statement_id"], self.prov_iface.PREDICATE_BUILD
        if full:
            predicate_type = (self.prov_iface.PREDICATE_BUILD
                              if self.args.brk == "build-predicate"
                              and produced["subject_kind"] == "work_product"
                              else self.full_predicate_type())
            receipt = self.prov.attest(self.prov_iface.AttestRequest.from_dict({
                "subjects": [{"name": produced["name"], "digest": digest}],
                "predicate_type": predicate_type,
                "predicate": self.predicate(unit, digest, rung, disposition),
                "actor": self.publisher.actor,
                "correlation": {"run_id": self.corr["run_id"],
                                "correlation_id": self.corr["correlation_id"]},
                "idempotency_key": self.key}))
            statement_id = receipt.statement_id
            self.locations[digest] = self.prov.publish(receipt)
        # the seal and the statement are recorded together, after both exist: a
        # capability that refuses in between leaves neither, so no receipt ever
        # ends with more subjects sealed than attested (README section 4).
        self.record("subject-sealed", {
            "unit_id": unit["unit_id"], "subject_kind": produced["subject_kind"],
            "subject_name": produced["name"], "subject_digest": digest})
        self.record("attested", {
            "unit_id": unit["unit_id"], "subject_digest": digest, "statement_id": statement_id,
            "fidelity": "full" if full else "metadata-light", "predicate_type": predicate_type,
            "artifact_id": light["artifact_id"]})
        if digest in self.locations:
            where = self.locations[digest]
            self.record("published", {
                "unit_id": unit["unit_id"], "uri": where.uri, "store": where.store,
                "inclusion_proof": bool(where.inclusion_proof),
                "inclusion_proof_supported": bool(self.prov.supports_inclusion_proof)})
        row = {"unit_id": unit["unit_id"], "state": state, "rung": rung, "disposition": disposition,
               "subject_kind": produced["subject_kind"], "subject_name": produced["name"],
               "digest": digest, "fidelity": "full" if full else "metadata-light",
               "artifact_id": light["artifact_id"], "cost_micros": unit["cost_micros"],
               "promotable": rung == LADDER_TASK}
        self.rows.append(row)
        return row

    def full_predicate_type(self) -> str:
        """The predicate a full statement carries, resolved from the name the
        closure declares to the URI the provenance interface publishes. Read
        twice: where the statement is made, and where the gate says which type
        it will accept - so the two can never drift apart."""
        declared = self.closure["attestation"]["full_predicate"]
        if declared not in PREDICATE_BY_NAME:
            raise self.refuse("document-invalid",
                              f"the closure declares full_predicate {declared!r}, which is not a "
                              f"predicate type this platform publishes; nothing was attested",
                              causes=[f"predicates published: {sorted(PREDICATE_BY_NAME)}"])
        return getattr(self.prov_iface, PREDICATE_BY_NAME[declared])

    def predicate(self, unit: dict, digest: str, rung: str, disposition: str) -> dict:
        """The run-output predicate: what would let someone reproduce or dispute
        this artifact - the acting identity and the principal it acts for, the
        exact code version, every input by digest, and the decisions that let it
        through."""
        return {
            "actor": self.publisher.actor,
            "acting_for": self.root_subject,
            "delegation_chain": [{"actor": h.actor, "obtained_via": h.obtained_via}
                                 for h in self.publisher.chain],
            "code_version": code_version(),
            "materials": [
                {"name": "entry-envelope", "digest": sha256_of(canonical(self.envelope))},
                {"name": "closure-declaration", "digest": sha256_of(canonical(self.closure))},
                {"name": "check-report", "digest": sha256_of(canonical(unit["check_report"]))},
                {"name": self.closure["source_ref"]["name"],
                 "digest": self.closure["source_ref"]["digest"]}],
            "invocation": {
                "workflow_ref": self.envelope["intent"]["workflow_ref"],
                "correlation": {"run_id": self.corr["run_id"],
                                "correlation_id": self.corr["correlation_id"]},
                "decision_refs": [f"gate:{rule}" for rule in self.closure["promotion"]["gate_rules"]]
                + [f"identity:{self.publisher.handle}"]},
            "unit": {"unit_id": unit["unit_id"], "attempts": unit["attempts"],
                     "model_class": unit["model_class"], "stop_reason": unit["stop_reason"],
                     "cost_micros": unit["cost_micros"], "ladder_rung": rung,
                     "disposition": disposition, "subject_digest": digest},
            "started_at": CLOCK, "ended_at": CLOCK}

    # --- 5. the admission gate ----------------------------------------------
    def gate(self, row: dict) -> dict:
        """Verification happens here, before consumption, on the shared path: an
        artifact whose statement is missing, whose bytes moved, or whose predicate
        is the build one rather than the run-output one is refused with a typed
        problem naming the rule that decided."""
        rules = self.closure["promotion"]["gate_rules"]              # read at the decision
        on_disk = open(os.path.join(self.prov_root, "artifacts", row["artifact_id"]), "rb").read()
        digest = sha256_of(on_disk)                     # recomputed from the bytes, never trusted
        found = self.prov.resolve(row["digest"])        # the statement that claims to describe them
        if not found:
            if "attested-subject-required" in rules:
                return {"admitted": False, "rule_id": "attested-subject-required", "checks": [],
                        "detail": f"no run-output statement resolves for {row['digest']}"}
            return {"admitted": True, "rule_id": "", "checks": [],
                    "detail": "no statement resolves and no declared rule requires one"}
        where = self.locations.get(row["digest"])
        proof = where.inclusion_proof if where is not None else None
        material = self.prov.verifying_material(found[0]["signatures"][0]["keyid"])
        accepted = ({material["keyid"]: material["material"]} if material.get("issuer") is None
                    else {material["issuer"]: "accepted by issuer"})
        # each of the other three rules is read here, at the point it would
        # decide: an undeclared rule contributes no expectation to the policy,
        # and a failure it alone would have caught does not refuse.
        trust = self.prov_iface.TrustPolicy(
            accepted,
            {row["subject_name"]: digest} if "subject-digest-must-match" in rules else {},
            (self.full_predicate_type(),) if "run-output-predicate-required" in rules else (),
            bool(proof), CLOCK)
        result = self.prov_iface.verify(found[0], trust, proof, material)
        if result.accepted:
            return {"admitted": True, "rule_id": "", "detail": "accepted", "checks": result.checks,
                    "predicate_type": result.predicate_type}
        rule = ("subject-digest-must-match" if result.subject_mismatches
                else "run-output-predicate-required" if "predicateType" in result.reason
                else "statement-must-verify")
        if rule == "statement-must-verify" and rule not in rules:
            # the only one of the four that cannot be expressed as an expectation
            # the policy carries: the envelope either checks out or it does not,
            # so an undeclared rule is honoured by not refusing on it here. The
            # other two are undeclared by putting no expectation in the policy
            # above, so this line can never stand in for them.
            return {"admitted": True, "rule_id": "", "checks": result.checks,
                    "detail": f"admitted, {rule} not declared: {result.reason}"}
        return {"admitted": False, "rule_id": rule, "detail": result.reason, "checks": result.checks}

    # --- 6. the run ----------------------------------------------------------
    def run(self) -> int:
        """One refusal ends the closure, and the refusal is itself recorded: a
        unit that was refused leaves a record like one that produced an
        artifact, on the same path, without the caller asking."""
        try:
            return self.closure_run()
        except Refusal as refusal:
            self.record_rejection(refusal.body)
            raise
        except self.problems as problem:
            # a capability refused after the entry was admitted. It reaches the
            # caller as its own problem object, and it leaves the same record a
            # refusal this runner raised would have left.
            self.record_rejection(problem.body)
            raise

    def record_rejection(self, body: dict) -> None:
        if self.publisher is None:
            return
        try:
            self.record("run-rejected", {
                "units_closed": len(self.rows), "promoted": len(self.promoted),
                "total_cost_micros": self.cost_micros, "rule_id": body.get("rule_id", ""),
                "problem_type": body["type"], "ledger_head": self.ledger.head()})
        except self.problems:
            return          # the store is what refused; there is nowhere to write the refusal

    def closure_run(self) -> int:
        self.validate()
        done = self.ledger.completed(self.key)
        if done is not None:
            print(f"REPLAY: {self.key} was closed at seq {done['seq']}; "
                  f"no record appended, no artifact promoted")
            return 0
        self.identity_chain()
        self.record("entry-admitted", {
            "entry_id": self.envelope["entry_id"],
            "intent_digest": sha256_of(self.envelope["intent"]["summary"].encode()),
            "closure_id": self.closure["closure_id"],
            "units_declared": len(self.closure["closes"]),
            "ceiling_micros": self.envelope["budget"]["ceiling_micros"]})
        self.record("identity-resolved", {
            "chain": self.chain_actors, "acting_for": self.root_subject,
            "executing_identity": self.publisher.actor, "scope": list(self.publisher.scope),
            "audience": self.publisher.audience, "hops": len(self.publisher.chain),
            "hop_trace": self.hop_trace, "authority_calls": self.ident.authority_calls})
        for unit in self.closure["closes"]:
            row = self.close_unit(unit)
            if self.args.brk == "mutate-subject" and row["subject_kind"] == "work_product":
                path = os.path.join(self.prov_root, "artifacts", row["artifact_id"])
                data = open(path, "rb").read()
                open(path, "wb").write(data[:-1] + bytes([data[-1] ^ 1]))
            if self.args.brk == "resign" and row["subject_kind"] == "work_product":
                self.tamper_signature(row["digest"])
        promotion = self.envelope["payload"]["promotion"]            # read at the decision
        for row in [r for r in self.rows if r["promotable"]]:
            verdict = self.gate(row)
            self.record("promotion-decided", {
                "unit_id": row["unit_id"], "subject_digest": row["digest"],
                "admitted": verdict["admitted"], "rule_id": verdict["rule_id"],
                "gate_rules": self.closure["promotion"]["gate_rules"],
                "verification_checks": len(verdict["checks"]), "detail": verdict["detail"]})
            if not verdict["admitted"]:
                raise self.refuse("policy-denied",
                                  f"{row['unit_id']} was not promoted: {verdict['detail']}",
                                  rule_id=verdict["rule_id"])
            subjects = [row["digest"]]
            if promotion["kind"] == "pull_request":
                # a pull request carries a second subject a branch does not: the
                # review request, sealed and recorded like any other artifact.
                review = (f"closes {row['unit_id']} on {promotion['target']}\n"
                          f"subject {row['digest']}\n").encode()
                extra = self.emit.attest_and_record(self.prov_root,
                                                   "review-request-" + row["unit_id"], review,
                                                   actor=self.publisher.actor)
                self.record("attested", {
                    "unit_id": row["unit_id"], "subject_digest": sha256_of(review),
                    "statement_id": extra["statement_id"], "fidelity": "metadata-light",
                    "predicate_type": self.prov_iface.PREDICATE_BUILD,
                    "artifact_id": extra["artifact_id"]})
                subjects.append(sha256_of(review))
            self.record("promoted", {
                "unit_id": row["unit_id"], "promotion_kind": promotion["kind"],
                "target": promotion["target"], "subjects": subjects,
                "subject_count": len(subjects),
                "ladder": "task success measured; promotion success staged, not measured"})
            self.promoted.append(row["unit_id"])
        self.notify(promotion)
        self.retention()
        self.record("run-completed", {
            "units_closed": len(self.rows), "promoted": len(self.promoted),
            "total_cost_micros": self.cost_micros, "ledger_head": self.ledger.head()})
        self.report()
        return 0

    def tamper_signature(self, digest: str) -> None:
        """The breakage `statement-must-verify` is the only rule that catches:
        the stored statement keeps its subject digest and its predicate type,
        and its signature no longer covers the pre-authentication encoding."""
        path = getattr(self.prov, "path", "")
        if not path:
            raise self.refuse("document-invalid",
                              "--break resign needs the file-backed attestation binding; this binding "
                              "holds its store in process and nothing was tampered with")
        records = [json.loads(line) for line in open(path) if line.strip()]
        for record in records:
            if digest in record["subjects"]:
                sig = record["envelope"]["signatures"][0]["sig"]
                record["envelope"]["signatures"][0]["sig"] = ("0" if sig[0] != "0" else "1") + sig[1:]
        open(path, "w").write("".join(json.dumps(r, sort_keys=True) + "\n" for r in records))

    def notify(self, promotion: dict) -> None:
        notify = self.envelope["payload"]["notify"]                  # read at the decision
        if notify["surface"] not in SURFACES:
            raise self.refuse("document-invalid",
                              f"notify.surface {notify['surface']!r} is not a surface this platform "
                              f"serves; nothing was notified",
                              causes=[f"surfaces served: {sorted(SURFACES)}"])
        self.record("notified", {
            "surface": notify["surface"], "rendered_as": SURFACES[notify["surface"]],
            "recipient": notify["recipient"], "promotion_kind": promotion["kind"],
            "receipt": {"correlation_id": self.corr["correlation_id"],
                        "cost_micros": self.cost_micros,
                        "subjects": [r["digest"] for r in self.rows],
                        "ledger_head": self.ledger.head()},
            "notification_body": {"text": self.envelope["intent"]["summary"],
                                  "closed": [r["unit_id"] for r in self.rows],
                                  "promoted": list(self.promoted)}})

    def retention(self) -> None:
        """Retention is declared per stream. A redaction is a recorded, provable
        event: the tombstone keeps the record's place and every proof over it,
        and takes the words with it. A stream declared not redactable refuses,
        and the refusal is recorded too."""
        retention = self.closure["retention"]                        # read at the decision
        self.records_pre_redaction = [self.state_iface.record_as_dict(r)
                                      for r in self.state.read_at(self.partition, self.head)]
        for kind in retention["redact_kinds"]:
            target = next((r for r in self.state.read_at(self.partition, self.head)
                           if r.kind == kind), None)
            if target is None:
                continue
            if not retention["redactable"]:
                self.record("redaction-refused", {
                    "record_id": target.record_id, "record_kind": kind,
                    "rule_id": "stream-not-redactable",
                    "detail": f"the stream {retention['partition']} declares redactable false; the "
                              f"record stands and its body is still retained"})
                continue
            tomb = self.state.redact(self.partition, target.record_id, self.publisher.actor)
            self.record("redaction-recorded", {
                "record_id": tomb.record_id, "record_kind": kind, "reason": retention["reason"],
                "authority": self.publisher.actor, "body_present": tomb.body is not None})

    # --- 7. what the caller sees ---------------------------------------------
    def report(self) -> None:
        records = self.state.read_at(self.partition, self.head)
        proof = self.state.prove(self.partition, records[0].record_id, self.head)
        consistency = self.state.prove_consistency(self.partition, self.head_at_first, self.head)
        if self.args.records_out:
            json.dump([self.state_iface.record_as_dict(r) for r in records],
                      open(self.args.records_out, "w"), indent=1)
            json.dump(self.records_pre_redaction,
                      open(self.args.records_out.replace(".json", "-pre.json"), "w"), indent=1)
        if self.args.bundle_out and self.promoted:
            self.write_bundle(next(r for r in self.rows if r["unit_id"] == self.promoted[0]))
        table([(r["unit_id"], r["state"], r["rung"], r["disposition"], r["subject_kind"],
                r["fidelity"], r["cost_micros"]) for r in self.rows],
              ("unit", "task state", "ladder rung", "disposition", "subject", "attestation", "micros"))
        print(f"\nchain      {' <- '.join(self.chain_actors)}  ({len(self.publisher.chain)} hops, "
              f"scope {' '.join(self.publisher.scope)})")
        print(f"records    {len(records)} appended, head size {self.head.size}, root "
              f"{self.head.root_hash[7:19]}, inclusion proof "
              f"{'verifies' if self.state_iface.verify_inclusion_proof(proof) else 'FAILS'}, "
              f"consistency path {len(consistency.path)}")
        print(f"notified   {self.envelope['payload']['notify']['surface']} -> "
              f"{self.envelope['payload']['notify']['recipient']}")
        print(f"closed: {len(self.rows)} units, {len(self.promoted)} promoted as "
              f"{self.envelope['payload']['promotion']['kind']}, {self.cost_micros} micros of "
              f"{self.envelope['budget']['ceiling_micros']}, ledger head {self.ledger.head()[7:19]}")

    def write_bundle(self, row: dict) -> None:
        """Everything a party holding no store needs: the envelope, the verifying
        material and the trust policy. Nothing here names an adapter."""
        envelope = self.prov.resolve(row["digest"])[0]
        material = self.prov.verifying_material(envelope["signatures"][0]["keyid"])
        accepted = ({material["keyid"]: material["material"]} if material.get("issuer") is None
                    else {material["issuer"]: "accepted by issuer"})
        where = self.locations.get(row["digest"])
        json.dump({"envelope": envelope, "material": material,
                   "proof": where.inclusion_proof if where else None,
                   "policy": {"accepted_signers": accepted,
                              "expected_subjects": {row["subject_name"]: row["digest"]},
                              "expected_predicate_types": [self.full_predicate_type()],
                              "require_inclusion_proof": bool(where and where.inclusion_proof),
                              "now": CLOCK}},
                  open(self.args.bundle_out, "w"), indent=1)


def refused(body: dict, media_type: str) -> int:
    """One refusal shape reaching the caller, and one line under it saying what
    stopped: a caller branches on the type, a reader reads the line. The media
    type is the one the errors capability publishes, not a literal typed here."""
    print(f"PROBLEM ({media_type}):")
    print(json.dumps(body, indent=2))
    rule = body.get("rule_id")
    print(f"refused: {body['type'].rsplit(':', 1)[-1]}"
          f"{' / ' + rule if rule else ''}; nothing was promoted")
    return 2


def table(rows, header) -> None:
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def verify_ledger(path: str) -> int:
    ledger = harnesses.reference().Ledger(path)
    broken = ledger.verify()
    if broken:
        print(f"PROBLEM: {broken}")
        return 2
    print(f"chain verifies: {len(ledger.records)} records, head {ledger.head()[7:19]}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Close finished units: attest, append, promote, notify.")
    ap.add_argument("--entry", help="the entry document at one of the four doors")
    ap.add_argument("--ledger", default=os.path.join(OUT, "done.jsonl"),
                    help="the receipt file this run projects the appended stream into")
    ap.add_argument("--records-out", help="write the appended state records here, as JSON")
    ap.add_argument("--prov-root", default=os.path.join(OUT, "provenance"),
                    help="the artifact store, attestation manifest and envelope store this period "
                         "accumulates in: one flag names one period")
    ap.add_argument("--bundle-out", help="write the promoted subject's envelope, verifying material "
                                         "and trust policy here, for a verifier with no store")
    ap.add_argument("--verify-ledger", help="verify the hash chain of a receipt file and exit")
    ap.add_argument("--break", dest="brk", default="none",
                    choices=("none", "unattested", "mutate-subject", "build-predicate", "resign"),
                    help="deliberate breakage: what the admission gate has to catch")
    ap.add_argument("--prov-adapter", default=os.environ.get("PROV_ADAPTER", "dryrun"),
                    help="provenance binding: dryrun or second")
    ap.add_argument("--state-adapter", default=os.environ.get("STATE_ADAPTER", "second"),
                    help="state binding: second (object store) or dryrun (in memory)")
    ap.add_argument("--identity-adapter", default=os.environ.get("IDENTITY_ADAPTER", "dryrun"),
                    help="identity binding: dryrun or second")
    args = ap.parse_args(argv)
    if args.verify_ledger:
        return verify_ledger(args.verify_ledger)
    if not args.entry:
        ap.error("--entry is required unless --verify-ledger is given")
    if not os.path.isfile(args.entry):
        errors_iface, problem_mod = harnesses.errors()
        return refused(errors_iface.construct(
            "document-invalid", f"there is no entry document at {args.entry}").body(),
            problem_mod.MEDIA_TYPE)
    close = Close(args)
    try:
        return close.run()
    except Refusal as refusal:
        return refused(refusal.body, close.problem_mod.MEDIA_TYPE)
    except close.problems as problem:      # a capability refused; one shape, one handler
        return refused(problem.body, close.problem_mod.MEDIA_TYPE)


if __name__ == "__main__":
    sys.exit(main())
