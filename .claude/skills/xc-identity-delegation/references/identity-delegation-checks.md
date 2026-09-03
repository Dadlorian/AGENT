# Identity delegation: full shapes, the acyclicity walk, and worked records

Proposed throughout. The skill body is enough to place the guarantee and to judge an implementation;
this file exists for the author who has to write the checker or the entry adapters. Every id cited
here resolves with `python3 tools/kb.py show <id>`.

## 1. The full chain-validity report

`ChainValidity` in the skill body is the per-action verdict. This is the report the definition of
done asserts on, one object per run of the checker.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:identity:delegation-report:0.1",
  "title": "IdentityDelegationReport",
  "description": "Proposed. Written once per enforcement point and once across enforcement points, so a green run names what it actually checked rather than only its exit code (F-a7-03).",
  "type": "object",
  "additionalProperties": false,
  "required": ["enforcement_point", "actions_checked", "delegated_actions_checked",
               "null_actor", "cyclic", "unrooted", "bound_at_entry"],
  "properties": {
    "enforcement_point": { "type": "string", "description": "Entity id of the enforcement point under test, read from the refusal that came back rather than from the binding that selected it (F-a7-04)." },
    "actions_checked": { "type": "integer", "minimum": 0 },
    "delegated_actions_checked": { "type": "integer", "minimum": 0, "description": "Actions whose chain has more than one hop. Zero means the run asserted nothing about delegation." },
    "null_actor": { "type": "integer", "minimum": 0 },
    "cyclic": { "type": "integer", "minimum": 0 },
    "unrooted": { "type": "integer", "minimum": 0 },
    "bound_at_entry": { "type": "integer", "minimum": 0, "description": "Actions whose actor equals the actor bound on their entry envelope. Anything less than actions_checked means some stage stamped an actor later." },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["action_id", "verdict"],
        "properties": {
          "action_id": { "type": "string" },
          "verdict": { "$ref": "urn:agentic:xc:identity:chain-validity:0.1" }
        }
      }
    },
    "enforcement_points_run": { "type": "integer", "minimum": 0 }
  }
}
```

## 2. The acyclicity and rooting walk

The chain is current actor first, least recent last (cap-identity's ordering decision, 2026-09-03).
The whole check is three passes over one array and holds no state between actions:

1. `actor_present`: `action.actor.subject` is a non-empty string matching the subject grammar
   `^(user|service|agent|schedule):[a-z0-9][a-z0-9._@-]*$`, and `delegation_chain` has at least one hop.
2. `acyclic`: walk the chain keeping a set of seen actor names. The first hop whose `actor` is already
   in the set sets `acyclic` to false and populates `repeated_actor` with that name. Names are compared
   whole, never by prefix: `service:intake` and `service:intake-v2` are different actors.
3. `rooted`: the last hop's `obtained_via` is `workload_attestation` or `direct`. A last hop of
   `token_exchange` is unrooted by construction, because an exchange presupposes a credential that
   some earlier hop must have held, and that hop is not in the chain.

A fourth pass, `bound_at_entry`, joins each action to its entry envelope on the run id and compares
the two actor objects for equality. It is the assertion that catches an actor stamped by a later
stage rather than by the driving adapter, which is the failure the placement exists to prevent.

## 3. The four worked bindings

Three appear in the skill body (`ActorBindingByWayIn`). The fourth, a schedule entry, is here; it is
the case where no caller exists at all and the root is the attested identity of the adapter that fired.

```json
{
  "kind": "schedule",
  "entry_id": "schedule-nightly-fault-sweep",
  "actor": {
    "subject": "schedule:nightly-fault-sweep",
    "delegation_chain": [
      { "actor": "schedule:nightly-fault-sweep", "obtained_via": "workload_attestation" },
      { "actor": "user:corey", "obtained_via": "token_exchange" }
    ]
  }
}
```

Read against the walk above: `actor_present` true; `acyclic` true, two distinct names; `rooted` -
the last hop is `token_exchange`, so under section 2 this chain is **unrooted** and the runnable
reference would fail the assertion. That is a real disagreement between the runnable reference and
row X2 rather than a typo here, and it is the reason the skill's second open question exists. The
binding this guarantee prescribes reverses the two hops so the human principal is the root:

```json
{
  "subject": "schedule:nightly-fault-sweep",
  "delegation_chain": [
    { "actor": "schedule:nightly-fault-sweep", "obtained_via": "workload_attestation" },
    { "actor": "user:corey", "obtained_via": "direct" }
  ]
}
```

The scheduler acts for the person who armed the schedule; that person was authenticated when they
armed it, not exchanged for at fire time, so `direct` is the honest value and the chain is rooted.

## 4. The worked refusal in full

```json
{
  "type": "urn:agentic:problem:identity-untrusted",
  "title": "Identity untrusted",
  "status": 401,
  "detail": "delegation chain for entry external-partner-agent-task repeats actor service:intake at hop 1 and hop 3",
  "instance": "urn:agentic:entry:external-partner-agent-task",
  "retryable": false,
  "correlation": { "run_id": "run-external-0001", "correlation_id": "corr-external-0001", "depth": 1 }
}
```

`identity-untrusted` is a registered row of the closed problem-type registry in
docs/decomposition.md section 2.1.6 (401, not retryable, raised when the delegation chain does not
verify). Nothing here invents a type. `detail` names the failing condition and the repeated actor and
carries no credential, no token and no certificate: what crosses a boundary is a non-secret reference
to an actor.
