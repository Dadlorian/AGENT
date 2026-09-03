# Using the improvement loop

Long material for `compose-improvement-loop`. The skill body is enough to seed, gate and promote a
candidate; this file carries the worked `seed_candidate` request for each of TARGET T1's three ways
in, and the worked rejection. Everything here is **proposed**: the finding id and file paths are
this repository's own, from `kb/ceremonies/ceremony-09-improve.json`.

## 1. The same request from a human, an agent and an event

`cap-consumption` owns the entry envelope and the caller doctrine; these are this composition's
payloads inside it, one per way in TARGET T1 names.

### A human closes a ceremony and seeds a candidate

```json
{
  "kind": "human",
  "actor": {
    "subject": "user:corey",
    "delegation_chain": [ { "actor": "user:corey", "obtained_via": "direct" } ]
  },
  "intent": { "capability": "compose-improvement-loop", "operation": "seed_candidate",
              "why": "a ceremony finding is worth an automated gate before a hand edit" },
  "payload": {
    "ceremony": 9,
    "target": { "kind": "skill", "name": "xc-typed-errors-implement",
                "ref": ".claude/skills/xc-typed-errors-implement/skill.json" },
    "seed": { "kind": "finding", "ref": "C9-001" },
    "rationale": "the adapter row's minted entity id needs recording as an open question, the way three wave-4c siblings already record the same gap"
  }
}
```

### An agent seeds a candidate against a recurring lesson

```json
{
  "kind": "external",
  "actor": {
    "subject": "agent:compose-improvement-loop",
    "delegation_chain": [
      { "actor": "user:corey", "obtained_via": "direct" },
      { "actor": "agent:compose-improvement-loop", "obtained_via": "rfc8693_token_exchange" }
    ]
  },
  "intent": { "capability": "compose-improvement-loop", "operation": "seed_candidate",
              "why": "lessons_for_next_section named a defect recurring across five closed ceremonies" },
  "payload": {
    "ceremony": 10,
    "target": { "kind": "discipline", "name": "build-ceremony",
                "ref": ".claude/skills/build-ceremony/skill.json" },
    "seed": { "kind": "finding", "ref": "lessons-row-10-numbering" },
    "rationale": "a session-supplied ceremony number drifted from the repository-global counter in at least five closed ceremonies; the discipline's own step 3 should refuse a taken number rather than only describe the correction"
  }
}
```

### An event seeds a candidate from a regressed evaluation case

```json
{
  "kind": "event",
  "actor": {
    "subject": "service:nightly-regression-scan",
    "delegation_chain": [ { "actor": "service:nightly-regression-scan", "obtained_via": "workload_attestation" } ]
  },
  "intent": { "capability": "compose-improvement-loop", "operation": "seed_candidate",
              "why": "a scheduled cap-evaluation replay moved a case from pass to fail against the current baseline" },
  "payload": {
    "ceremony": null,
    "target": { "kind": "skill", "name": "agent:release-reviewer",
                "ref": "config/agents/release-reviewer.json" },
    "seed": { "kind": "transition", "ref": "cs-release-review#case-12" },
    "rationale": "case-12's tool-use dimension regressed against baseline bl-2026-08-27 with no ceremony open at the time"
  }
}
```

## 2. The worked rejection: gate_revision's case set or baseline does not resolve

`cap-evaluation` already states this failure shape for its own `evaluate` call (F-b3-13, F-b4-07);
this is the instance a candidate's `gate_revision` step actually receives when the target names a
`case_set_id` or `baseline_id` nothing resolves. `criterion-unresolvable` is the registered row that
fits.

```json
{
  "type": "urn:agentic:problem:criterion-unresolvable",
  "title": "The candidate's case set or baseline does not resolve",
  "status": 422,
  "detail": "candidate cand-2026-09-03-014 names baseline_id bl-2026-09-02, which no version of the registered baseline store resolves",
  "retryable": false,
  "correlation_id": "run-2026-09-03-0091"
}
```
