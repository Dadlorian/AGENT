# cap-evaluation — full shapes and worked calls

Long material for `cap-evaluation`. Everything here is **proposed** unless a kb id is named
next to it. The skill body is enough to write a caller without this file; open it when you
need the full schemas, a worked call per way in, or the exact rejection body.

`cap-consumption` owns the entry envelope and the caller doctrine (four entries of TARGET T6.2,
one result or one problem object, configuration rather than arguments). This file shows only
what is specific to evaluation: the payload inside the envelope, and the answer that comes back.

---

## 1. The three ways in (TARGET T1)

TARGET T1 lists three ways in: a human, an agent, and an internal or external event. All three
send the same `evaluate` payload and read the same `EvaluationReport`. Nothing downstream
branches on which one arrived.

### 1.1 A human (`user:`)

A person gating a prompt change before it ships.

```json
{
  "kind": "human",
  "actor": {
    "subject": "user:corey",
    "delegation_chain": [{ "actor": "user:corey", "obtained_via": "direct" }]
  },
  "intent": { "capability": "evaluation", "operation": "evaluate",
              "why": "gate the release-reviewer prompt change" },
  "correlation": { "correlation_id": "01JB8W3Q0Z9K2M4N6P8R" },
  "budget": { "ceiling_usd": 4.00 },
  "idempotency_key": "eval-release-reviewer-1.4.0-cs-release-review-bl-2026-08-27",
  "payload": {
    "unit_under_test": { "ref": "agent:release-reviewer", "version": "1.4.0" },
    "case_set_id": "cs-release-review",
    "baseline_id": "bl-2026-08-27",
    "mode": "replay"
  }
}
```

Answer:

```json
{
  "report_id": "rep-01JB8W41",
  "unit_under_test": { "ref": "agent:release-reviewer", "version": "1.4.0" },
  "case_set": { "case_set_id": "cs-release-review", "digest": "sha256:9c1f…" },
  "baseline_id": "bl-2026-08-27",
  "outcome": "passed",
  "cases_executed": 6,
  "transitions": [],
  "correlation_id": "01JB8W3Q0Z9K2M4N6P8R"
}
```

Branch on `outcome`. Nothing else.

### 1.2 An agent (`agent:`)

A self-improvement loop checking its own candidate rewrite before proposing it. The chain has
two hops because the loop acts for the person who started it.

```json
{
  "kind": "external",
  "actor": {
    "subject": "agent:improvement-loop",
    "delegation_chain": [
      { "actor": "user:corey", "obtained_via": "direct" },
      { "actor": "agent:improvement-loop", "obtained_via": "rfc8693_token_exchange" }
    ]
  },
  "intent": { "capability": "evaluation", "operation": "evaluate",
              "why": "check the candidate rewrite before proposing it" },
  "correlation": { "correlation_id": "01JB8WA7C3D5F7H9K1M3" },
  "budget": { "ceiling_usd": 4.00 },
  "idempotency_key": "eval-cap-evaluation-implement-0.2.0-candidate-cs-release-review",
  "payload": {
    "unit_under_test": { "ref": "skill:cap-evaluation-implement", "version": "0.2.0-candidate" },
    "case_set_id": "cs-release-review",
    "baseline_id": "bl-2026-08-27",
    "mode": "replay"
  }
}
```

Answer — a regression, which is the interesting case:

```json
{
  "report_id": "rep-01JB8WB2",
  "unit_under_test": { "ref": "skill:cap-evaluation-implement", "version": "0.2.0-candidate" },
  "case_set": { "case_set_id": "cs-release-review", "digest": "sha256:9c1f…" },
  "baseline_id": "bl-2026-08-27",
  "outcome": "failed",
  "cases_executed": 6,
  "transitions": [
    { "case_id": "c-12-tool-order", "was": "pass", "now": "fail",
      "dimension_scores": { "trajectory": 0.4, "tool_use": 0.0,
                            "task_completion": 1.0, "multi_turn": 0.9 } }
  ],
  "correlation_id": "01JB8WA7C3D5F7H9K1M3"
}
```

`task_completion` still scores 1.0. The final answer was right and the run still failed, which
is the whole point of scoring the trajectory rather than the result.

### 1.3 An event (`service:`)

A merge on the default branch, arriving from a webhook. The subject is a workload, and its
right to act comes from attestation rather than from a person.

```json
{
  "kind": "event",
  "actor": {
    "subject": "service:git-webhook",
    "delegation_chain": [{ "actor": "service:git-webhook", "obtained_via": "workload_attestation" }]
  },
  "intent": { "capability": "evaluation", "operation": "evaluate",
              "why": "a merge landed on the default branch" },
  "correlation": { "correlation_id": "01JB8WC9E1G3J5L7N9Q1" },
  "budget": { "ceiling_usd": 12.00 },
  "idempotency_key": "eval-nightly-triage-9f2c1ab-cs-triage",
  "payload": {
    "unit_under_test": { "ref": "workflow:nightly-triage", "version": "9f2c1ab" },
    "case_set_id": "cs-triage",
    "baseline_id": "bl-2026-08-30",
    "mode": "live"
  }
}
```

A schedule (`schedule:`) enters the same way with `kind: "schedule"`; the payload does not change.

---

## 2. The worked rejection

A refusal is a problem object, never an `outcome` value. `passed`, `failed` and `inconclusive`
all describe a run that happened; this describes a run that could not start.

```json
{
  "type": "urn:agentic:problem:criterion-unresolvable",
  "title": "Rubric handle does not resolve",
  "status": 422,
  "detail": "case_set cs-release-review case c-12-tool-order names rubric_ref rub:tone-v3, which no version of the rubric store resolves",
  "instance": "urn:agentic:evaluation:request:01JB8W3Q0Z9K2M4N6P8R",
  "retryable": false,
  "correlation_id": "01JB8W3Q0Z9K2M4N6P8R"
}
```

`criterion-unresolvable` is the registered row in the closed registry (docs/decomposition.md
section 2.1.6) that fits: a rubric handle is the criterion reference a case carries. A missing
or never-promoted baseline returns the same type; a malformed request returns
`urn:agentic:problem:document-invalid`. No new type is proposed by this capability.

`cap-errors` owns the object, the closed registry and the rule that `retryable` is a field
rather than an inference from the status code.

---

## 3. The full shapes

### 3.1 CaseSet

The summary shape is in the skill body. The parts left out of it:

| Field | Meaning |
|---|---|
| `cases[].origin` | `recorded` or `synthetic`. The two halves of the corpus; keep both populated. |
| `cases[].recorded_run_ref` | Required when `origin` is `recorded`. Names the trajectory replay serves effects from. |
| `cases[].stub_policy.mode` | `record` on the pass that captures a run, `replay` on every pass after it. |
| `cases[].stub_policy.unrecorded_effect` | `fail` or `refuse`. There is deliberately no `execute`. |
| `cases[].rubric_ref` | Opaque handle. The rubric body is resolved inside the scorer, after the trajectory exists. |
| `digest` | Content digest over the canonical cases. Two registrations of identical cases agree. |
| `version` | Semantic version of the corpus. Distinct from the version of the unit under test. |

Registering a corpus is idempotent on the digest: the same cases return the same
`case_set_id`, so a caller re-registering on every run does not fork the corpus.

### 3.2 EvaluationReport

| Field | Meaning |
|---|---|
| `outcome` | `passed`, `failed` or `inconclusive`. The one field a caller branches on. |
| `cases_executed` | Zero forces `inconclusive`. Checked before anything else is reported. |
| `transitions[]` | Per-case movement against the baseline, with `was` in `pass`/`fail`/`absent`. |
| `transitions[].dimension_scores` | Per-dimension scores over the ordered trace, for the cases that moved. |
| `unit_under_test.version` | Pinned in the report, not only in the invocation that produced it. |
| `case_set.digest` | Pinned likewise. A report without both versions is not comparable to another report. |
| `correlation_id` | Set at entry by the caller, carried through, and present on the problem object too. |

`transitions` is deliberately not an aggregate delta. An aggregate can stay flat while one case
flips, which is the exact shape a regression hides in.

### 3.3 Promoting a baseline

`promote_baseline` takes a `report_id` and returns a new `baseline_id`. The previous baseline is
retained. A loop that rewrites the unit under test and promotes the baseline in the same pass has
no gate, so promotion is a separate call with its own actor and its own reason string.
