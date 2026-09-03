# Identity: long material

Open this only when you need the full request and response schemas, a worked chain, or the
mapping from each recorded standard to the operations it governs. The skill body is enough to
judge an implementation without it.

Every schema here is **proposed** (our design): PASS.md records the capability, the two governing
standards and the absent adapter, not the call shapes. Ids resolve with
`python3 tools/kb.py show <id>`.

## 1. Standards to operations

| Recorded standard (`F-b3-14`) | Operations it governs | What it does not cover |
|---|---|---|
| Token exchange (`E-standard-oauth-2-0-token-exchange`) | `delegate`, and the `verify` of an exchanged token | Naming a unit the platform started; it authenticates a client that already holds a credential |
| Workload identity (`E-standard-workload-identity`) | `attest`, and the `verify` of an attested credential | Expressing on-behalf-of: an attested document names one workload, not a chain (`X-cross-structure-034`) |

Both are recorded as version `unverified`: search-only research records name RFC 8693 and describe
workload identity documents, and no specification was fetched from this environment
(`X-cap-identity-001`, `X-cap-identity-005`).

## 2. attest

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:attest:request:0.1",
  "title": "AttestRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["unit_ref", "platform_facts"],
  "properties": {
    "unit_ref": { "type": "string", "minLength": 1,
                  "description": "The unit of work asking to be named." },
    "platform_facts": {
      "type": "object",
      "description": "Observed, not asserted by the unit: where it runs, under which account, in which image.",
      "additionalProperties": { "type": "string" }
    },
    "delegated_by": {
      "type": "string",
      "description": "Set only when the platform cannot observe the unit in place. The subject of the already-attested party that vouches for it (X-cross-structure-035)."
    }
  }
}
```

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:attest:response:0.1",
  "title": "AttestResponse",
  "type": "object",
  "additionalProperties": false,
  "required": ["subject", "not_after", "obtained_via"],
  "properties": {
    "subject":      { "type": "string" },
    "not_after":    { "type": "string", "format": "date-time",
                      "description": "Short-lived by construction. There is no renew that outlives the unit." },
    "obtained_via": { "const": "workload_attestation" },
    "credential_ref": { "type": "string",
                        "description": "A handle. The credential itself never enters a document, a ledger record or a problem body." }
  }
}
```

## 3. delegate

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:identity:delegate:request:0.1",
  "title": "DelegateRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["subject_token", "actor_token", "audience"],
  "properties": {
    "subject_token": { "type": "string", "description": "The principal the work is done for." },
    "actor_token":   { "type": "string",
                       "description": "The agent that will act. Required: without it the result is impersonation, not delegation (X-cross-structure-036)." },
    "audience":      { "type": "string", "description": "The party the issued token is for." },
    "scope":         { "type": "array", "items": { "type": "string" } }
  }
}
```

The response is a scoped token plus the `ActorIdentity` in the skill body, its
`delegation_chain` extended by one hop with `obtained_via` `token_exchange`.

## 4. A worked chain

A person asks for work; an intake service takes it; an agent does it. Three hops, current actor
first and least recent last, which is the ordering `examples/end-to-end/entries/external.json`
carries (its `subject` equals `delegation_chain[0].actor`):

```json
{
  "subject": "agent:fix-writer",
  "delegation_chain": [
    { "actor": "agent:fix-writer", "obtained_via": "token_exchange" },
    { "actor": "service:intake",   "obtained_via": "token_exchange" },
    { "actor": "user:corey",       "obtained_via": "direct" }
  ]
}
```

As nested `act` claims the same chain nests rather than lists: the outermost `act` is the current
actor and the least recent actor is the most deeply nested (`X-entry-composition-048`), which is
the same order the array above is written in.

```json
{
  "sub": "user:corey",
  "act": { "sub": "agent:fix-writer",
           "act": { "sub": "service:intake" } }
}
```

Authorisation reads `sub` and the outermost `act` only; everything nested inside it is
informational (`X-cross-structure-038`). The array form above is the platform's storage and audit
form: a reader walks it from the actor that is acting now back to the principal it started with.
docs/decomposition.md section 2.1 describes the same field as oldest hop first, which is the open
question recorded in the skill body.

## 5. What the chain does not carry

`act` records who acted at each hop and not what that hop was permitted to spend or do
(`X-end-to-end-032`). Budget ceilings, policy decisions and tenancy scope travel in their own
members of the entry envelope and the dispatch request, and an implementation that starts reading
constraints out of the chain has merged two concerns that fail differently.
