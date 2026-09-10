#!/usr/bin/env python3
"""ask - I have intent; how do I hand it over, and what do I get back at once?

    python3 examples/ask/run.py --entry examples/ask/entries/human.json
    python3 examples/ask/run.py --all-doors
    python3 examples/ask/run.py --describe

One admission pipeline, four producers, one canonical envelope, one receipt.
Nothing here executes the work: intake admits, and the acknowledgement carries
no result, because the producer may be gone before anything runs.

Read it in this order. `Admission.submit()` is the pipeline, and its steps are
in the order the guarantees require: map and derive at the boundary, check the
document against the published dialect, resolve the acting identity and its
chain, take the admission decision, price the plan against the stamped ceiling,
claim the key, and only then record the entry and complete the claim. Every
refusal above the claim leaves nothing recorded and no key held.

Everything the pipeline decides on is read from the admission declaration
(admission.json) at the point of the decision, never transcribed here; test.sh
runs the same door twice with one declared value changed and asserts the two
records differ.

Python 3.11 standard library only. No network. No product name outside the
adapters table in README.md.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import doors                                                        # noqa: E402
import harnesses                                                    # noqa: E402

DOOR_ORDER = ("human", "event", "schedule", "external")
CLOCK = "2026-09-04T09:30:00Z"          # one fixed clock, so two runs are byte-identical


# --- what a refusal looks like to a caller ---------------------------------
def problem_body(exc) -> dict:
    """Every capability in this repository keeps its own typed condition class;
    the wire body is rendered in one place, harness/errors/problem.py. This is
    the caller's side of that: whichever capability refused, a caller reads one
    shape and branches on `type`, never on prose."""
    if hasattr(exc, "body"):
        return exc.body
    return exc.problem.body()


class Refused(Exception):
    """A typed refusal, carried with the step that raised it."""

    def __init__(self, step: str, body: dict) -> None:
        self.step, self.body = step, body
        super().__init__(body.get("detail", ""))


# --- the pipeline -----------------------------------------------------------
class Admission:
    """The four doors, and the five capabilities behind them."""

    def __init__(self, declaration: dict, bindings: dict, ledger_path: str) -> None:
        self.d = declaration
        self.bindings = bindings
        os.environ.setdefault("IDENTITY_CLOCK", CLOCK)
        os.environ.setdefault("POLICY_CLOCK", CLOCK)

        self.intake_i, harness_second = harnesses.work_intake(
            "second" if bindings["intake"] == "detached" else None)
        self.validation_i, validation_a = harnesses.document_validation(bindings["validation"])
        self.identity_i, identity_a = harnesses.identity(bindings["identity"])
        self.policy_i, policy_a = harnesses.policy(bindings["policy"])
        self.idem_i, idem_a = harnesses.idempotency(bindings["idempotency"])
        self.errors_i, self.problem_m = harnesses.errors()
        self.reference = harnesses.reference()

        adapter_class = (doors.detached_binding(self.intake_i, harness_second, self.d)
                         if bindings["intake"] == "detached"
                         else doors.binding(self.intake_i, self.d))
        self.intake = adapter_class()
        self.validation = validation_a()
        self.identity = identity_a()
        self.policy = policy_a(self.action_vocabulary(self.policy_i.load_bundle()))
        self.idem = idem_a(os.path.join(os.path.dirname(ledger_path) or ".", "claims"))
        self.policy_version = self.policy.active_version
        self.ledger = self.reference.Ledger(ledger_path)
        self.lock = threading.Lock()

    def action_vocabulary(self, bundle: dict) -> dict:
        """The declared action vocabulary, composed into the rule set the decision
        is pinned to, as one deny in front of it.

        `policy.action` is what this decision point submits; `policy.actions_permitted`
        is the closed set it is allowed to be. A vocabulary nothing evaluates is a
        vocabulary in prose, so the declaration is turned into a rule rather than
        trusted: an action outside the set matches every `ne` condition at once and
        is denied at admission.entry, before the rule set's own entry rule is
        reached. The composed bundle is what `activate()` digests, so the version
        every decision is pinned to covers this rule as well (F-b4-04: refusal is
        deterministic and happens before execution).
        """
        composed = dict(bundle)
        composed["rules"] = [{
            "rule_id": "deny-entry-action-outside-vocabulary",
            "decision_point": self.d["policy"]["decision_point"],
            "effect": "deny",
            "detail": "the request names an action outside the closed vocabulary this decision point "
                      "declares; refused before anything was spent and before any entry was recorded",
            "when": [{"path": "action", "op": "ne", "value": name}
                     for name in self.d["policy"]["actions_permitted"]],
        }] + list(bundle["rules"])
        return composed

    # --- step 2: the published dialect, checked at the boundary -------------
    def cross_check(self, envelope: dict, correlation_id: str) -> dict:
        """The document-validation capability's own structured output for this
        envelope: the dialect actually in effect, and one located violation per
        failure - an instance location and a keyword location, not a sentence.

        The work-intake interface refuses an invalid envelope before any binding
        of ours is reached, with the reference example's validator; this is the
        second implementation, and what the platform's typed failure object is
        rendered from. Running both on the same document is the point: two
        validators over one dialect either agree or the dialect is not what is
        being enforced (docs/maturity/closures.md, document-validation).
        """
        request = self.validation_i.ValidationRequest.from_dict(
            {"schema_uri": self.d["schema_ref"], "dialect": self.d["dialect"], "instance": envelope})
        outcome = self.validation.validate(request)
        return {"dialect": outcome.dialect, "schema_uri": outcome.schema_uri,
                "valid": outcome.valid, "errors": len(outcome.errors),
                "causes": [e.as_dict() for e in outcome.errors[:3]]}

    def validate(self, envelope: dict, correlation_id: str) -> dict:
        try:
            report = self.cross_check(envelope, correlation_id)
        except Exception as exc:                      # an unsupported dialect, or no schema to read
            if hasattr(exc, "body"):
                raise Refused("validate", problem_body(exc)) from exc
            raise
        if not report["valid"]:                       # unreachable from a mapper that maps: the
            raise Refused("validate", problem_body(self.intake_i.Problem(   # interface refused first
                "document-invalid", report["causes"][0]["message"],
                instance=report["causes"][0]["instance_location"], errors=report["errors"])))
        return {"dialect": report["dialect"], "schema_uri": report["schema_uri"],
                "errors": 0, "validators_agree": True}

    # --- step 3: the acting identity, and the chain that produced it --------
    def resolve_identity(self, envelope, correlation_id: str) -> dict:
        chain = envelope.actor["delegation_chain"]
        bound = self.d["identity"]["max_delegation_depth"]
        if len(chain) > bound:
            raise Refused("identity", self.errors_i.construct(
                "policy-denied",
                f"the delegation chain at this door is {len(chain)} hops, past the declared bound of "
                f"{bound}; no credential was issued and nothing was admitted",
                correlation_id, rule_id="delegation-depth-bound").body())
        scopes, lifetimes = self.d["identity"]["scopes"], self.d["identity"]["hop_lifetime_s"]
        audience = self.d["audience"]
        rungs = min(len(scopes), len(lifetimes))
        if len(chain) > rungs:
            # Clamping the last rung and reusing it is the silent failure this
            # refusal exists to stop: a hop past the ladder would be issued the
            # scope of the hop before it, and "narrows rather than replaces the
            # chain" would be true of the declaration and false of the credential.
            raise Refused("identity", self.errors_i.construct(
                "policy-denied",
                f"the delegation chain at this door is {len(chain)} hops and the declared scope ladder "
                f"has {rungs} rungs; a hop past the ladder would hold the rung before it, so no "
                f"credential was issued and nothing was admitted",
                correlation_id, rule_id="scope-ladder-shorter-than-chain").body())

        def level(index: int) -> tuple[list, int]:
            """One rung per hop, read from the declaration and never clamped."""
            return list(scopes[index:]), lifetimes[index]

        try:
            root = chain[-1]
            scope, lifetime = level(0)
            held = self.identity.verify(self.presented(root["actor"], scope, audience, lifetime))
            credentials = [held]
            # Per hop, not per chain: what this hop was issued is what the next
            # hop's scope and lifetime are compared against, so per-invocation
            # narrowing is observable in the record rather than asserted about it.
            issued = [{"actor": root["actor"], "scope": scope, "lifetime_s": lifetime,
                       "seconds_left": held.remaining_s()}]
            for index, hop in enumerate(reversed(chain[:-1]), start=1):
                scope, lifetime = level(index)
                acting = self.identity.attest(self.identity_i.AttestRequest.from_dict(
                    {"unit": hop["actor"], "audience": audience, "scope": scope,
                     "lifetime_s": lifetime,
                     "platform_facts": {"door": envelope.kind, "attested_via": hop["obtained_via"]},
                     "presented": self.presented(hop["actor"], scope, audience, lifetime),
                     "vouched_by": credentials[-1] if index > 1 else None}))
                held = self.identity.delegate(self.identity_i.DelegationRequest.from_dict(
                    {"subject": held, "actor": acting, "scope": scope, "audience": audience,
                     "lifetime_s": lifetime}))
                credentials.append(held)
                issued.append({"actor": hop["actor"], "scope": scope, "lifetime_s": lifetime,
                               "seconds_left": held.remaining_s()})
        except Exception as exc:                        # a typed identity refusal, never a stack trace
            if hasattr(exc, "body"):
                raise Refused("identity", problem_body(exc)) from exc
            raise
        return {"executing_identity": chain[0]["actor"], "triggering_identity": chain[-1]["actor"],
                "delegation_depth": len(chain), "audience": held.audience,
                "scope": list(held.scope), "seconds_left": held.remaining_s(),
                "ladder_rungs": rungs,
                "issued_hops": [hop["actor"] for hop in issued], "issued": issued}

    def presented(self, subject: str, scope, audience: str, lifetime_s: int) -> str:
        """The test seam standing in for what an outside issuer handed the door.
        It is the adapter's, not this example's: no credential is minted here."""
        return self.identity.fixture_presented(subject, scope, audience, lifetime_s, "direct")

    # --- step 4: the admission decision, before anything is spent ----------
    def decide(self, envelope, correlation_id: str, resource_tenant: str | None) -> dict:
        request = self.policy_i.DecisionRequest.from_dict({
            "decision_point": self.d["policy"]["decision_point"],
            "subject": {"id": envelope.actor_subject, "tenant": self.d["tenant"],
                        "delegation_chain": envelope.actor["delegation_chain"], "mandates": []},
            "action": self.d["policy"]["action"],
            "resource": {"tenant": resource_tenant or self.d["tenant"],
                         "workflow_ref": envelope.intent["workflow_ref"],
                         "summary": envelope.intent["summary"]},
            "context": {"run_id": envelope.correlation["run_id"],
                        "root_dispatch_id": "disp-" + doors._short(envelope.idempotency_key)},
            "policy_version": self.policy_version})
        try:
            decision, _ = self.policy.admit(request, lambda meter: "admitted; nothing dispatched")
        except Exception as exc:
            if hasattr(exc, "body"):
                raise Refused("policy", problem_body(exc)) from exc
            raise
        return {"effect": decision.effect, "rule_id": decision.rule_id,
                "decision_point": decision.decision_point,
                "policy_version": decision.policy_version[:21]}

    # --- step 5: the priced plan, against the ceiling the platform stamped --
    def price(self, envelope, correlation_id: str) -> dict:
        manifest = self.intake_i.resolve_manifest(envelope)
        if manifest.total_micros > envelope.ceiling_micros:
            raise Refused("budget", self.errors_i.construct(
                "budget-exhausted",
                f"the shortest finishing path of {manifest.workflow_ref} prices at "
                f"{manifest.total_micros} micros, past the ceiling of {envelope.ceiling_micros} the "
                f"platform stamped; refused before a claim was taken and before anything was recorded",
                correlation_id, stop_reason="ceiling_below_plan_floor").body())
        return {"workflow_ref": manifest.workflow_ref, "steps": len(manifest.steps),
                "estimate_micros": manifest.total_micros, "ceiling_micros": manifest.ceiling_micros,
                "headroom_micros": manifest.ceiling_micros - manifest.total_micros,
                "manifest_digest": manifest.digest()}

    # --- steps 6 and 7: one claim over the key, then the durable entry -----
    def claim_and_record(self, envelope, correlation_id: str) -> tuple[str, dict, bool]:
        request = self.idem_i.ClaimRequest.for_payload(
            envelope.idempotency_key, envelope.job(), self.d["idempotency"]["scope"],
            correlation_id, envelope.actor_subject, envelope.kind,
            self.d["idempotency"]["retention_s"])
        try:
            outcome = self.idem.claim(request)
        except Exception as exc:
            if hasattr(exc, "body"):
                raise Refused("idempotency", problem_body(exc)) from exc
            raise
        if outcome.outcome != "fresh":
            stored = json.loads(outcome.result_ref) if outcome.result_ref else {}
            return outcome.outcome, stored, outcome.in_flight
        try:
            ack = self.intake.admit(envelope)                 # the durable entry
        except Exception as exc:
            if not hasattr(exc, "body"):
                raise
            # The claim was taken and the entry was not written. Release it, or
            # the key is wedged until the retention window elapses and the
            # producer's retry is answered from an outcome that never existed.
            self.idem.expire(request.idempotency_key, request.scope,
                             now=time.time() + request.retention_s + 1)
            raise Refused("record", dict(problem_body(exc), claim_released=True)) from exc
        receipt = ack.dict()
        self.idem.complete(request.idempotency_key, request.scope, json.dumps(receipt, sort_keys=True))
        return "fresh", receipt, False

    # --- the whole of it ----------------------------------------------------
    def submit(self, door: str, native: dict, expected: dict | None = None,
               resource_tenant: str | None = None) -> dict:
        fmt = native["format"]
        record: dict = {"door": door, "producer_format": fmt, "at": CLOCK,
                        # stamped before anything is parsed, so even the earliest
                        # refusal names who was at the door
                        "attested_subject": native["transport"]["attested_subject"]}
        message = self.intake.render_message(native, None)
        try:
            envelope = self.intake.accept(message)
        except Exception as exc:
            if not hasattr(exc, "body"):
                raise
            body = dict(exc.body)
            if body["type"].endswith("document-invalid"):
                # The interface refused with the reference validator. The located
                # violations the caller is handed come from the document-validation
                # capability, run on the same document: a caller gets a pointer,
                # not a sentence, and the two validators are compared where it
                # matters, on a document one of them has already rejected.
                report = self.cross_check(self.intake.normalise(message).dict(), "")
                body["causes"] = report["causes"]
                body["errors"] = report["errors"]
                record["validation"] = {"dialect": report["dialect"], "errors": report["errors"],
                                        "schema_uri": report["schema_uri"],
                                        "validators_agree": not report["valid"]}
            return self.refuse(record, Refused("accept", body))
        correlation_id = envelope.correlation["correlation_id"]
        record.update(entry_kind=envelope.kind, entry_id=envelope.entry_id,
                      run_id=envelope.correlation["run_id"], correlation_id=correlation_id,
                      parent_correlation_id=envelope.correlation.get("parent_correlation_id"),
                      correlation_depth=envelope.correlation["depth"],
                      actor=envelope.actor_subject, idempotency_key=envelope.idempotency_key,
                      job_digest=self.intake.job_digest(envelope),
                      occurred_at=envelope.occurred_at)
        if expected is not None:
            record["round_trip"] = ("exact" if self.reference.canonical(envelope.dict())
                                    == self.reference.canonical(expected) else "differs")
        try:
            record["validation"] = self.validate(envelope.dict(), correlation_id)
            record["identity"] = self.resolve_identity(envelope, correlation_id)
            record["policy"] = self.decide(envelope, correlation_id, resource_tenant)
            record["plan"] = self.price(envelope, correlation_id)
            claim, receipt, in_flight = self.claim_and_record(envelope, correlation_id)
        except Refused as refusal:
            return self.refuse(record, refusal)
        record.update(kind="entry-admitted", bindings=self.binding_axes(), claim=claim, in_flight=in_flight,
                      state=self.d["lifecycle"]["initial"], receipt=receipt,
                      replay=claim != "fresh",
                      cancellable="cancelled" in self.d["lifecycle"]["states"],
                      ack_delivery=self.intake.ack_delivery,
                      producer_present_at_ack=getattr(self.intake, "producer_present_at_ack", False),
                      dropped=self.intake.dropped.get(fmt, []) if hasattr(self.intake, "dropped") else [],
                      units_started=self.intake.work_started,
                      entries_recorded=self.intake.records)
        with self.lock:
            self.ledger.append(**record)
        return record

    def refuse(self, record: dict, refusal: Refused) -> dict:
        """A refusal is audited like an admission: the same correlation, the same
        two identities, and the typed body. What it does not get is an entry."""
        record.update(kind="entry-refused", bindings=self.binding_axes(),
                      refused_at=refusal.step, problem=refusal.body,
                      state="rejected-before-admission",
                      entries_recorded=self.intake.records, units_started=self.intake.work_started)
        with self.lock:
            self.ledger.append(**record)
        return record

    def binding_axes(self) -> dict:
        """What each binding declares about how it works, read back off the
        adapters rather than restated here. Two runs that differ only in a
        binding differ in these numbers and nowhere else."""
        return {
            "intake": {"name": self.bindings["intake"], "ack_delivery": self.intake.ack_delivery,
                       "execution_model": self.intake.execution_model},
            "validation": {"name": self.bindings["validation"],
                           "execution_model": self.validation.execution_model,
                           "schema_reads": self.validation.schema_reads},
            "identity": {"name": self.bindings["identity"],
                         "authority_calls": self.identity.authority_calls,
                         "verifications": self.identity.verifications},
            "policy": {"name": self.bindings["policy"], "entity": self.policy.entity},
            "idempotency": {"name": self.bindings["idempotency"],
                            "supports_in_flight": self.idem.supports_in_flight,
                            "unit_of_conditionality": self.idem.unit_of_conditionality},
        }

    # --- what an outside caller reads before writing any code --------------
    def describe(self) -> dict:
        """The capability description: fetchable, and enough to submit against
        without a client library this repository wrote."""
        return {
            "description_version": self.d["declaration_version"],
            "envelope": {"schema_ref": self.d["schema_ref"], "dialect": self.d["dialect"],
                         "set_by_the_boundary": ["correlation", "idempotency_key", "budget",
                                                 "actor", "entry_id", "kind"]},
            "doors": [{"door": reg["door"], "producer_format": fmt,
                       "identity_members_the_key_is_derived_from": self.d["key_fields"][fmt],
                       "attested_via": reg["acting_via"],
                       "authorised_by": reg["authorised_by"]}
                      for fmt, reg in self.d["producers"].items()],
            "task_lifecycle": {"states": self.d["lifecycle"]["states"],
                               "initial": self.d["lifecycle"]["initial"],
                               "cancellable": "cancelled" in self.d["lifecycle"]["states"],
                               "input_required_served": "input-required" in self.d["lifecycle"]["states"]},
            "idempotency": {"retention_s": self.d["idempotency"]["retention_s"],
                            "scope": self.d["idempotency"]["scope"],
                            "key_supplied_by": "the boundary, from the producer's own message identity"},
            "problem_types": sorted(
                "urn:agentic:problem:" + suffix for suffix in
                ("adapter-unavailable", "budget-exhausted", "dialect-unsupported",
                 "document-invalid", "idempotency-conflict", "policy-denied")),
            "acknowledgement": {"carries_result": False, "delivery": self.intake.ack_delivery},
        }


# --- presentation -----------------------------------------------------------
def table(rows, header) -> None:
    widths = [max(len(str(r[i])) for r in [header] + rows) for i in range(len(header))]
    print("  ".join(str(h).ljust(w) for h, w in zip(header, widths)))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print("  ".join(str(c).ljust(w) for c, w in zip(row, widths)))


def show(records: list) -> int:
    admitted = [r for r in records if r["kind"] == "entry-admitted"]
    refused = [r for r in records if r["kind"] == "entry-refused"]
    if admitted:
        table([(r["door"], r["state"], r["claim"], r["entry_id"], r["correlation_id"],
                r["job_digest"][7:19], r["identity"]["executing_identity"],
                r["identity"]["triggering_identity"], r["identity"]["delegation_depth"],
                r["plan"]["estimate_micros"], r["plan"]["ceiling_micros"])
               for r in admitted],
              ("door", "state", "claim", "entry_id", "correlation", "job", "executing",
               "triggering", "hops", "estimate", "ceiling"))
        print(f"\none job: {len({r['job_digest'] for r in admitted})} job digest   "
              f"{len({r['plan']['manifest_digest'] for r in admitted})} resolved manifest   "
              f"{len({r['entry_id'] for r in admitted})} submissions   "
              f"{admitted[-1]['entries_recorded']} entries recorded   "
              f"{admitted[-1]['units_started']} units of work started")
        last = admitted[-1]
        print(f"acknowledgement: {json.dumps(last['receipt'])}")
        print(f"delivery: {last['ack_delivery']}   producer present: "
              f"{last['producer_present_at_ack']}   cancellable: {last['cancellable']}   "
              f"dropped by the mapper: {last['dropped'] or 'nothing left over'}")
    for r in refused:
        print(f"\nREFUSED at {r['refused_at']} (application/problem+json):")
        print(json.dumps(r["problem"], indent=2))
        print(f"entries recorded: {r['entries_recorded']}   units started: {r['units_started']}")
    return 2 if refused else 0


# --- the command line -------------------------------------------------------
def parse(argv=None):
    p = argparse.ArgumentParser(description="hand intent over at one of four doors")
    p.add_argument("--entry", help="the entry document a door is expected to produce")
    p.add_argument("--door", choices=DOOR_ORDER, help="submit at one door")
    p.add_argument("--all-doors", action="store_true", help="submit the same job at all four")
    p.add_argument("--admission", default=os.path.join(HERE, "admission.json"))
    p.add_argument("--producers", default=os.path.join(HERE, "producers.json"))
    p.add_argument("--ledger", default=os.path.join(HERE, "out", "ledger.jsonl"))
    p.add_argument("--intake", choices=("derived", "detached"))
    p.add_argument("--validation", choices=("dryrun", "second"))
    p.add_argument("--identity", choices=("dryrun", "second"))
    p.add_argument("--policy", choices=("dryrun", "second"))
    p.add_argument("--idempotency", choices=("dryrun", "second"))
    p.add_argument("--again", action="store_true", help="submit the identical message a second time")
    p.add_argument("--again-window", type=int, metavar="H",
                   help="submit a second time under the same message identity, different job")
    p.add_argument("--again-received-at", metavar="TS",
                   help="submit the same occurrence a second time, received at another wall clock")
    p.add_argument("--redeliveries", type=int, default=0, help="concurrent redeliveries of one message")
    p.add_argument("--occurrence", help="the schedule door's nominal occurrence")
    p.add_argument("--resource-tenant", help="a resource in another tenant, to see the deny")
    p.add_argument("--format", help="submit this door's message under another producer format")
    p.add_argument("--describe", action="store_true", help="print the capability description")
    p.add_argument("--verify-ledger", action="store_true")
    p.add_argument("--json", action="store_true", help="the records, machine-readable")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse(argv)
    declaration = json.load(open(args.admission))
    bindings = dict(declaration["bindings"])
    for name in ("intake", "validation", "identity", "policy", "idempotency"):
        if getattr(args, name):
            bindings[name] = getattr(args, name)

    if args.verify_ledger:
        ledger = harnesses.reference().Ledger(args.ledger)
        broken = ledger.verify()
        print(broken or f"chain verifies: {len(ledger.records)} records, head {ledger.head()[:19]}")
        return 2 if broken else 0

    admission = Admission(declaration, bindings, args.ledger)
    if args.describe:
        print(json.dumps(admission.describe(), indent=2))
        return 0

    natives = doors.load_producers(args.producers)
    if args.entry:
        expected = json.load(open(args.entry))
        selected = [(expected["kind"], expected)]
    elif args.all_doors or not args.door:
        selected = [(d, None) for d in DOOR_ORDER]
    else:
        selected = [(args.door, None)]

    records = []
    for door, expected in selected:
        native = json.loads(json.dumps(natives[door]))
        if args.occurrence:
            native["body"] = doors.mutate(native["format"], native["body"], occurrence=args.occurrence)
        if args.format:
            native["format"] = args.format
        if not args.redeliveries:
            records.append(admission.submit(door, native, expected, args.resource_tenant))
        if args.again or args.again_window is not None or args.again_received_at:
            second = json.loads(json.dumps(native))
            second["body"] = doors.mutate(second["format"], second["body"],
                                          window_hours=args.again_window,
                                          received_at=args.again_received_at)
            records.append(admission.submit(door, second, None, args.resource_tenant))
        if args.redeliveries:
            racers = []
            barrier = threading.Barrier(args.redeliveries)
            lock = threading.Lock()

            def deliver():
                barrier.wait()
                out = admission.submit(door, native, None, args.resource_tenant)
                with lock:
                    racers.append(out)
            threads = [threading.Thread(target=deliver) for _ in range(args.redeliveries)]
            [t.start() for t in threads]
            [t.join() for t in threads]
            records.extend(racers)
            fresh = sum(1 for r in racers if r.get("claim") == "fresh")
            print(f"redeliveries: {len(racers)} concurrent, {fresh} claims answered fresh, "
                  f"{admission.intake.records} entries recorded, "
                  f"in_flight_seen={any(r.get('in_flight') for r in racers)}, "
                  f"lease={admission.idem.supports_in_flight}, "
                  f"conditionality={admission.idem.unit_of_conditionality}")
    if args.json:
        print(json.dumps(records, indent=2, sort_keys=True))
        return 2 if any(r["kind"] == "entry-refused" for r in records) else 0
    return show(records)


if __name__ == "__main__":
    sys.exit(main())
