#!/usr/bin/env python3
"""Resume: the decision point re-entered before the next side-effecting call.

concern-policy-q3 (X-maturity-c-003, X-maturity-c-004). An allow names the
single action it admits and the instant it was taken, and is spent the
moment that action fires or is abandoned - never treated as valid for as
long as the run lasts. Work that stops short of its side effect - paused,
queued, or interrupted by a restart - carries no residual authorization
forward. Before its next side-effecting call it re-enters the decision
point, decided against the rule set and the version the binding is serving
NOW, not the one pinned when the work was first admitted. A rule changed in
the interval therefore governs the resumed work with no special-casing,
because there was never a cached decision to invalidate.

PausedWork is the durable checkpoint that crosses the interruption: plain,
JSON-serialisable data written by one process (or one moment) and read back
by another. It carries the pre-pause decision only as a record of what
happened, never as a credential resume() will honour.

    python3 harness/policy/resume.py                                  the property holds: exit 0
    POLICY_TRUST_STALE_DECISION=1 python3 harness/policy/resume.py    deliberate breakage: exit 1

The breakage names the anti-pattern the closure marks as being abandoned:
session-scoped "decide once, valid for the run" authorization. With the flag
set, resume() reuses the pre-pause decision instead of re-entering the
decision point - exactly the property this check exists to catch, and it
fails the same assertions that pass without the flag.
"""
from __future__ import annotations

import copy
import dataclasses
import json
import os
import sys
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from interface import (Decision, DecisionRequest, Problem, decision_as_dict,   # noqa: E402
                       digest_of, load_bundle)
from adapters.dryrun import DryRunPolicyAdapter                                # noqa: E402

CHECKPOINT = os.path.join(HERE, "out", "resume-checkpoint.json")
REASONS = {"paused", "queued", "restarted"}


@dataclass(frozen=True)
class PausedWork:
    """What crosses the interruption. Plain data - no method here can turn it
    back into permission to run; only resume() decides that, and only by
    asking again."""
    request: dict
    decision: dict
    reason: str
    stopped_at: str

    def write(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            json.dump(dataclasses.asdict(self), fh, indent=1, sort_keys=True)

    @classmethod
    def read(cls, path: str) -> "PausedWork":
        with open(path) as fh:
            return cls(**json.load(fh))


def pause(adapter, request: DecisionRequest, reason: str = "paused") -> PausedWork:
    """Decide once, then stop short of the side effect: the unit is queued,
    not run. A deny here is exactly a deny at admit() - it was never going to
    run - so nothing is paused; the Problem propagates."""
    if reason not in REASONS:
        raise ValueError(f"reason must be one of {sorted(REASONS)}")
    decision = adapter.decide(request)
    if decision.effect == "deny":
        raise Problem("policy-denied", decision.problem["detail"], rule_id=decision.rule_id,
                      decision_point=decision.decision_point, policy_version=decision.policy_version,
                      input_digest=decision.input_digest, spend_delta_micros=0)
    return PausedWork(request.as_dict(), decision_as_dict(decision), reason, decision.decided_at)


def resume(adapter, paused: PausedWork, work):
    """The decision point re-entered before the next side-effecting call.

    The prior decision (paused.decision) travels only as a record; nothing
    below reads it as authority except under the deliberate breakage. What is
    decided is a fresh DecisionRequest, re-pinned to the version the adapter
    is serving now - the state of the world at resume time - which is what
    makes a rule changed in the interval take effect on work admitted before
    the interval began.
    """
    stale_request = DecisionRequest.from_dict(paused.request)
    if os.environ.get("POLICY_TRUST_STALE_DECISION") == "1":
        # Deliberate breakage: treat a decision taken once as valid for as
        # long as the run lasts. No decision point is re-entered.
        decision = Decision(**paused.decision)
    else:
        fresh_request = dataclasses.replace(stale_request, policy_version=adapter.active_version)
        decision = adapter.decide(fresh_request)
    if decision.effect == "deny":
        body = dict(decision.problem) if decision.problem else {"detail": "denied on resume"}
        body["spend_delta_micros"] = adapter.meter.spend(stale_request.context["root_dispatch_id"])
        raise Problem("policy-denied", body["detail"], rule_id=decision.rule_id,
                      decision_point=decision.decision_point, policy_version=decision.policy_version,
                      input_digest=decision.input_digest, spend_delta_micros=body["spend_delta_micros"])
    return decision, work(adapter.meter)


# --------------------------------------------------------------------------
# The runnable check for concern-policy-q3.
# --------------------------------------------------------------------------
def scenario() -> dict:
    """Admit under bundle v1 (one process), change the policy, force a
    pause/queue/restart cycle (a second, independent process picks the
    checkpoint up from disk), resume. Returns everything the check asserts
    on."""
    bundle_v1 = load_bundle()
    dispatch = "disp-resume-001"
    request = DecisionRequest.from_dict({
        "decision_point": "dispatch.tool_call",
        "subject": {"id": "user:corey", "tenant": "tenant-acme"},
        "action": "invoke",
        "resource": {"tenant": "tenant-acme", "tool": "tool:report-export", "scope": "internal"},
        "context": {"run_id": "run-resume-001", "root_dispatch_id": dispatch},
        "policy_version": digest_of(bundle_v1),
    })

    # -- before the interruption: one process, one adapter, one decision --
    adapter_before = DryRunPolicyAdapter(bundle=bundle_v1)
    paused = pause(adapter_before, request, reason="queued")

    # a durable checkpoint: written here, read back below as if by another process
    paused.write(CHECKPOINT)

    # -- the governing policy rule changes while the work sits paused/queued --
    bundle_v2 = copy.deepcopy(bundle_v1)
    bundle_v2["rules"].insert(0, {
        "rule_id": "deny-tool-call-after-policy-change",
        "decision_point": "dispatch.tool_call",
        "effect": "deny",
        "detail": "a rule added after this unit was admitted now denies its action",
        "when": [],
    })

    # -- restart: a second, independent adapter instance (nothing carried
    # over but the checkpoint on disk) serving the changed policy --
    adapter_after = DryRunPolicyAdapter(bundle=bundle_v2)
    reloaded = PausedWork.read(CHECKPOINT)

    ran: list = []

    def work(meter):
        ran.append(meter.charge(dispatch, 1200))
        return "ran"

    denied = None
    decision_post = None
    try:
        decision_post, _ = resume(adapter_after, reloaded, work)
    except Problem as problem:
        denied = problem.body

    return {
        "dispatch": dispatch,
        "decision_pre_pause": paused.decision,
        "decision_post_resume": decision_as_dict(decision_post) if decision_post else None,
        "denied": denied,
        "ran": ran,
        "adapter_before_journal": len(adapter_before.journal),
        "adapter_after_journal": len(adapter_after.journal),
    }


def main() -> int:
    result = scenario()
    ok = True
    lines: list[str] = []

    def check(label: str, cond: bool) -> None:
        nonlocal ok
        if not cond:
            ok = False
        lines.append(f"  {'ok' if cond else 'FAIL':4} {label}")

    check("the pre-pause decision allowed the work under the rule set in force at admission",
          result["decision_pre_pause"]["effect"] == "allow")
    check("a durable checkpoint crossed the interruption (paused, queued, restarted) as plain data, not a credential",
          os.path.exists(CHECKPOINT))
    check("exactly one decision was recorded by the process that admitted the work, before the interruption",
          result["adapter_before_journal"] == 1)
    check("the resumed work's next side-effecting call was decided again, against the rules serving now, not reused",
          result["denied"] is not None and result["denied"]["type"].endswith("policy-denied"))
    check("the rule changed during the interval governs the resumed work, never the rule in force at admission",
          (result["denied"] or {}).get("rule_id") == "deny-tool-call-after-policy-change")
    check("the resumed work's side effect never ran: refused before execution, not after spend",
          result["ran"] == [] and (result["denied"] or {}).get("spend_delta_micros") == 0)
    check("the pre-pause and post-resume decisions were pinned to different policy versions",
          result["denied"] is not None and
          result["decision_pre_pause"]["policy_version"] != result["denied"]["policy_version"])
    check("the decision log carries two distinct records - pre-pause and post-resume - for the same run",
          result["adapter_before_journal"] == 1 and result["adapter_after_journal"] == 1)

    breakage = os.environ.get("POLICY_TRUST_STALE_DECISION") == "1"
    print(f"concern-policy-q3: work resumed after pause/queue/restart is decided again "
          f"({'breakage POLICY_TRUST_STALE_DECISION=1' if breakage else 'property'})")
    for line in lines:
        print(line)
    print(f"decision_pre_pause={result['decision_pre_pause']['effect']}:{result['decision_pre_pause']['rule_id']} "
          f"post_resume={'denied:' + result['denied']['rule_id'] if result['denied'] else 'allow (not re-decided)'} "
          f"work_ran={result['ran'] != []}")
    print("RESUME_CHECK " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
