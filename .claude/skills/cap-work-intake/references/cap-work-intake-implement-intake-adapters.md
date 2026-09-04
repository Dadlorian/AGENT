# Work intake adapters: mapping, failure modes, and the migration runbook

Proposed material. The `cap-work-intake-implement` skill body is enough to build either producer
without this file; open it when you are writing a mapper, planning the cut-over, or working out why
an equivalence run reports two digests.

The canonical envelope and the shared mapping table live in
`.claude/skills/cap-work-intake/references/intake-envelope.md`. This file is about the two adapters.

---

## 1. The pair and the axis

| | Request-pushed event producer (today) | Agent-message producer (second) |
|---|---|---|
| Who initiates | a person, a hook, a clock, a script | another autonomous agent |
| Transport shape | one hop; the submission is held open until the acknowledgement | send and detach |
| Producer at the end of the job | present, usually watching | usually gone |
| Failure surface | a status the caller reads immediately | a typed problem the agent must parse later |
| Identity available | the authenticated caller, one hop | an attested workload credential, then an exchange, then the human origin |
| What it cannot do | serve a producer that has disconnected anything richer than an acknowledgement | be told anything synchronously; assume a human will read a refusal |

**The axis: whether the producer is present for the outcome.** It matters because it is the
assumption that decides whether the acknowledgement may carry a result. An interface both adapters
pass cannot have been shaped around either one's liveness — which is why `ack_carries_result` is a
`const false` in `IntakeAdapterConfig` rather than a default someone can flip.

A second adapter that is another request-pushed producer with a different body format would break no
assumption at all, and is the pair that proves nothing.

---

## 2. Failure modes, and which adapter can detect them

| Failure | Request-pushed producer | Agent-message producer |
|---|---|---|
| Producer format has no registered mapper | refused synchronously, caller sees it | refused; the agent must read the problem later |
| Envelope invalid after mapping | refused, offending pointer named | same, but the mapper is the only place to fix it |
| Idempotency key collides with a different job digest | 409 conflict, caller can inspect both | 409 conflict; the agent may retry blindly, so the key derivation must be stable |
| Duplicate submission, same digest | no-op with `duplicate_of` set | same |
| Producer stamps a field of its own | caught by the published schema | caught by the published schema |
| Delegation chain cannot be attested | one hop is honest here | **cannot be detected as wrong** — a short chain looks like a direct submission |
| Producer disconnects before acknowledgement | visible as a transport error | not applicable; there is nothing to disconnect from |

The row worth reading twice is the delegation chain. The second adapter is the case where a chain
that is silently too short is indistinguishable from a correct one, which is why step 6 says to mark
the chain incomplete rather than fabricate a hop.

---

## 3. Migration runbook

Three steps, each independently revertible, with the published schema fixed throughout.

### Step A — envelope built, old path authoritative

- Publish the envelope schema and the equivalence corpus.
- Wrap the producer that already runs so that it builds an envelope **and** continues down the
  existing path.
- Validate every envelope, log the result, act on nothing.
- **Revert:** stop calling the builder. Nothing downstream has changed.
- **Done when:** `invalid == 0` over a week of real submissions, and every envelope has an actor, a
  correlation identifier, a ceiling and a derived idempotency key.

### Step B — envelope authoritative for one producer

- Cut the running producer over: the envelope, not its native message, is what continues.
- Turn refusals into typed problems. Start counting `untyped_refusals`.
- **Revert:** flip back to the old path; the envelopes already written stay valid.
- **Done when:** `untyped_refusals == 0` and no producer has needed a field added to the envelope.

### Step C — second producer, selectable by configuration

- Register the agent-message mapper.
- Run the equivalence corpus against each adapter, changing only configuration.
- **Revert:** deselect the second adapter; it stays registered and stays tested.
- **Done when:** `adapters_run == 2` with `distinct_job_digests == 1` in each run.

Do not delete either adapter at the end of step C. An interface with one surviving implementation
drifts back into the shape of whatever runs.

---

## 4. What starts red, and why that is correct

Three of this capability's assertions cannot pass today, and each is recorded rather than dressed up:

| Assertion | Why it starts red | The record |
|---|---|---|
| Every entry carries an actor and a delegation chain | there is no identity field anywhere in the system | `F-a6-05` |
| Every refusal is typed | typed errors are absent | `F-a6-06` |
| `adapters_run == 2` | neither mapper nor the runner exists here | the definition of done, status claimed |

A definition of done that reported green on any of these would be reporting the absence of a test.
