# Provenance chain: full shapes, worked instances and sweep report

Proposed throughout. The skill body is enough to judge whether a chain is closed and to wire the
binding; this file exists for the author who has to code against the fields. Every id here resolves
with `python3 tools/kb.py show <id>`.

## 1. `attestation-recorded`, in full

The record kind is named in `docs/decomposition.md` section 2.2.1 alongside `head-sealed`. The summary
shape in the skill body carries the required fields; the full shape adds the optional ones a sweep may
read but never asserts on.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:provenance-chain:attestation-recorded:1",
  "title": "AttestationRecorded",
  "type": "object",
  "additionalProperties": false,
  "required": ["subject_digest", "statement_ref", "envelope_digest", "actor",
               "code_version", "run_id", "recorded_at"],
  "properties": {
    "subject_digest":  { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                         "description": "The join key. Digest over canonical bytes, never a name or a path." },
    "subject_name":    { "type": "string",
                         "description": "Human label only. Never used to match a statement to an artifact." },
    "statement_ref":   { "type": "string",
                         "description": "Fetchable by a party who does not hold our credentials." },
    "envelope_digest": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "predicate_type":  { "type": "string", "format": "uri",
                         "description": "Which predicate the statement carries. cap-provenance owns the two." },
    "actor":           { "type": "string",
                         "description": "Producer identity: user:, agent:, service: or schedule:." },
    "delegation_chain_ref": { "type": "string",
                         "description": "Reference to the identity chain that authorised the producer." },
    "code_version":    { "type": "string" },
    "inputs_digest":   { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$",
                         "description": "Digest over the canonicalised input set, so inputs are attributable too." },
    "run_id":          { "type": "string" },
    "root_dispatch_id":{ "type": "string" },
    "sealed_head":     { "type": "string",
                         "description": "seam-state owns the sealing; this field only names the head." },
    "recorded_at":     { "type": "string", "format": "date-time" }
  }
}
```

Why these and not more: the record is read by a sweep that must run without read access to any payload,
so nothing here is the artifact, the prompt, the criterion or the output text.

## 2. Worked instances, one per way in

TARGET T1 names three ways in (`T-t1-01`, `T-t1-02`, `T-t1-03`). The same record shape covers all three
and nothing downstream branches on which door was used, which is the claim these three instances exist
to make checkable.

### 2.1 A human enters

```json
{
  "subject_digest": "sha256:1f0a4c2d9b7e5613a8c04f2e6d13b8a75c9e02f4a61d8b3c7e50f9a2d64b81c3",
  "subject_name": "out/report.md",
  "statement_ref": "attest://run-human-0001/stmt-01",
  "envelope_digest": "sha256:9c31b7d0e5a24f68c1de73f0a2b95c48d6e70a13f5c92b84d0e17a36c48b9f52",
  "predicate_type": "urn:agentic:provenance:predicate:agent-action:0.1",
  "actor": "user:corey",
  "code_version": "git:8f3c1a2",
  "inputs_digest": "sha256:0d47b2e8c1a90f36d5b8e207a4c13f96b70e5d2a8f416c09b3d72e15a06c8f43",
  "run_id": "run-human-0001",
  "root_dispatch_id": "disp-human-0001",
  "sealed_head": "head:4b7e91c0",
  "recorded_at": "2026-09-03T10:14:02Z"
}
```

### 2.2 An agent enters

```json
{
  "subject_digest": "sha256:2b8e01c7d4a9f36502be7c1d8a0f45e93c26b7d1058fa9e3b47c02d16e8a5f70",
  "subject_name": "out/patch.diff",
  "statement_ref": "attest://run-agent-0042/stmt-07",
  "envelope_digest": "sha256:5d92c48b0e17a3f6c81de07b34a95f2c6e8017d4b93a0c5f2e64d18b70a9c3f5",
  "predicate_type": "urn:agentic:provenance:predicate:agent-action:0.1",
  "actor": "agent:planner-01",
  "delegation_chain_ref": "chain://run-agent-0042/2",
  "code_version": "git:8f3c1a2",
  "inputs_digest": "sha256:6c015a7e39b2d84f0e7c31a95d068b47f2e91c30a5847bd6e0f39c12a70b4d85",
  "run_id": "run-agent-0042",
  "root_dispatch_id": "disp-human-0001",
  "sealed_head": "head:4b7e91c0",
  "recorded_at": "2026-09-03T10:16:41Z"
}
```

Note `root_dispatch_id`: the agent was delegated to by the human run above, and the two records share a
root. The chain guarantee does not care; the audit trail does.

### 2.3 An event enters

```json
{
  "subject_digest": "sha256:3c7d19a0b6e24f85d1c0378ae59b2f46071da8c3f9e50b27a4c86d10f35b7e92",
  "subject_name": "out/build-manifest.json",
  "statement_ref": "attest://run-event-0007/stmt-02",
  "envelope_digest": "sha256:7a05c3e91d48b60f2c7ea15d039b48c7f20e6a91d53c087b4f62a19c05d38e7b",
  "predicate_type": "urn:agentic:provenance:predicate:agent-action:0.1",
  "actor": "service:git-webhook",
  "code_version": "git:8f3c1a2",
  "inputs_digest": "sha256:b41e0d75a3c9268f0e1d5b3c78a04f92d6e83b17c05a2f94d31e60b8a7c25f03",
  "run_id": "run-event-0007",
  "root_dispatch_id": "disp-event-0007",
  "sealed_head": "head:4b7e91c0",
  "recorded_at": "2026-09-03T10:19:08Z"
}
```

A scheduled entry is the same record with `actor` reading `schedule:nightly-rollup`; TARGET T6.2's four
entries and TARGET T1's three ways in are different enumerations, and this file cites T1.

## 3. The refusal, in full

The type is the registered `adapter-unavailable` row of the closed registry in `docs/decomposition.md`
section 2.1.6. cap-errors owns the object; this guarantee only supplies one registered row of it.

```json
{
  "type": "urn:agentic:problem:adapter-unavailable",
  "title": "No attestation could be produced for the output",
  "status": 503,
  "detail": "result res-0007 references sha256:3c7d19a0b6e2... and no statement could be signed over it; the release was refused rather than emitted unattested",
  "instance": "urn:agentic:run:run-event-0007",
  "dispatch_id": "0f5f0f26-1c1e-4c2f-9d0a-1b9a3c5e7d21",
  "retryable": true,
  "retry_after_s": 30,
  "correlation": { "run_id": "run-event-0007", "correlation_id": "corr-event-0007" }
}
```

`retryable` is true because an unreachable signer is a condition that clears. It is a field, not an
inference from the status code.

## 4. Sweep report

The fields the definition of done asserts on. Written once per run of the sweep.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:xc:provenance-chain:sweep-report:1",
  "title": "ProvenanceChainSweepReport",
  "type": "object",
  "additionalProperties": false,
  "required": ["at_head", "results_read", "artifacts_checked",
               "attestations_matched", "orphans", "entry_kinds_seen"],
  "properties": {
    "at_head":              { "type": "string", "description": "The pinned head every read was taken at." },
    "results_read":         { "type": "integer", "minimum": 0 },
    "artifacts_checked":    { "type": "integer", "minimum": 0,
                              "description": "Asserted, so an empty corpus cannot report the same green as a clean one." },
    "attestations_matched": { "type": "integer", "minimum": 0 },
    "orphans":              { "type": "integer", "minimum": 0 },
    "orphan_digests":       { "type": "array", "items": { "type": "string" },
                              "description": "Named in the failure output, so the breakage is locatable." },
    "digest_mismatches":    { "type": "integer", "minimum": 0,
                              "description": "A record exists but its subject_digest differs from the artifact." },
    "external_resolutions": { "type": "integer", "minimum": 0,
                              "description": "Resolutions served from the published statement with our store unreachable." },
    "entry_kinds_seen":     { "type": "array", "items": { "enum": ["user", "agent", "service", "schedule"] },
                              "description": "All three of TARGET T1's ways in must appear, or the wiring was only proved on one door." }
  }
}
```

## 5. Reading order

`cap-provenance` for what a statement is and what an outside check means; this skill for the closure
over the set of outputs; `seam-state` for the sealed head, the inclusion proof and the consistency
proof; `xc-provenance-chain-implement` for the two adapters, the migration and the run.
