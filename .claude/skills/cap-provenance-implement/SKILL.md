---
name: cap-provenance-implement
description: How to build the Provenance capability on this stack: what the append-only evidence records and the hash-chained store already give you and what they do not, a first adapter that wraps an existing record in a signed envelope with a held key, a second with a different execution model that signs with an ephemeral identity and publishes to a public append-only log, the migration between them, where the attest call is wired so no output can skip it, and a definition of done with the breakage that makes it fail. Load it when writing the code that emits or checks a statement, when picking where envelopes are stored, when adding signing to a pipeline that today only rehashes its own file, or when a conformance run reports an output with no statement over its digest.
---

# cap-provenance-implement

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Turn the contract in cap-provenance into something that runs here: one attest call, two signing adapters behind it whose execution models differ, and every artifact and agent action reaching a statement an outside verifier can check. | sourced | `F-b3-12`, `F-b4-05`, `E-capability-provenance` "in-toto · SLSA · DSSE" |

## Entities

| Entity |
|---|
| `E-capability-provenance` |
| `E-concern-provenance` |
| `E-adapter-jsonl-evidence-records` |
| `E-adapter-jsonl-hash-chain` |
| `E-swap-candidate-sigstore` |
| `E-swap-candidate-any-attestation-store` |

## Contract

### Shapes (JSON Schema 2020-12)

**ProvenanceConformanceReport (proposed shape; the counters the definition of done below asserts on, per adapter)** (proposed; sources: `F-b1-04`, `F-b4-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:provenance:report:0.1",
  "title": "ProvenanceConformanceReport",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "adapter",
    "attestations_emitted",
    "attestations_verified",
    "subject_mismatches",
    "external_verifier",
    "external_verifier_exit",
    "store_mounted",
    "adapters_run"
  ],
  "properties": {
    "adapter": {
      "enum": [
        "local-signed-jsonl",
        "keyless-transparency-log"
      ]
    },
    "attestations_emitted": {
      "type": "integer",
      "minimum": 0
    },
    "attestations_verified": {
      "type": "integer",
      "minimum": 0,
      "description": "Counted by the external verifier, not by us. Must be greater than 0."
    },
    "subject_mismatches": {
      "type": "integer",
      "minimum": 0
    },
    "orphan_subjects": {
      "type": "integer",
      "minimum": 0,
      "description": "Subject digests referenced by a result with no statement over them."
    },
    "external_verifier": {
      "type": "string",
      "description": "Name and version of the verifier we did not write."
    },
    "external_verifier_exit": {
      "type": "integer"
    },
    "store_mounted": {
      "const": false,
      "description": "Recorded at runtime. A verification run with our store reachable has not tested the property."
    },
    "log_inclusion_proofs": {
      "type": "integer",
      "minimum": 0,
      "description": "Declared unsupported by the local adapter rather than reported as 0."
    },
    "adapters_run": {
      "type": "integer",
      "minimum": 1
    },
    "selected_by": {
      "const": "configuration",
      "description": "A code edit between runs would not be a swap."
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Proposed: the statement is emitted at the moment the artifact is produced, from the values in hand, never reconstructed later from a log. A statement assembled after the fact attests to what the log says happened, which is the claim it was supposed to be independent of. | proposed | `F-b4-05` |
| Proposed: both adapters implement the identical attest, verify, resolve and publish calls from cap-provenance, and the running adapter is chosen by configuration with no code edit between runs. build-adapter-pair states design rule 3 (F-b1-04); what this adds is that the selection must appear in the conformance report, because an unobservable swap is indistinguishable from running one adapter twice. | proposed | `F-b1-04` |
| Proposed: the verification half of the definition of done runs with our evidence store unreachable and shells out to a verifier nobody here wrote. A run with the store mounted is recorded as unsupported rather than as a pass, so store_mounted is a const in the report shape above rather than a field an implementation can set. | proposed | `F-b4-05` |
| Proposed: the local adapter declares log inclusion proofs unsupported instead of reporting zero of them. A documented conformance subset is honest; an adapter that reports a property it cannot provide is exactly the failure the pair exists to expose. | proposed | `F-b3-12` |
| Proposed: what the platform records today is a chain our own reader recomputes: JSONL, hash-chained, where each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable. That is integrity for us and evidence for nobody else, so the signed envelope is added on top of it and the chain is not removed. | proposed | `F-a5-03`, `F-b5-05` |
| Proposed: attest is wired into the platform's result emitter and its run-seal path, not into each caller, and there is no flag that skips it. cap-provenance states design rule 7 as the reason for that placement; what this adds is the wiring rule that a new step kind inherits attestation by construction because it reaches emission through the same path. | proposed | `F-b1-08`, `T-t2-03` |
| Proposed: a failure to attest, sign or publish is returned as problem details from the registry cap-errors owns, and this capability mints no failure object of its own; a new registry row is required before any new type is raised. | proposed | `F-b4-07` |
| Apply build-evidence-record: the conformance run and its breakage are written to the evidence store naming the code version and the tree hash under test, and stay claimed until they have actually been run here; proposed pointer, see that skill. | proposed | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start from what is already true: subject digests exist and nothing signs them. Do not re-derive the contract; cap-provenance states the recorded row (F-b3-12) and the concern's contract (F-b4-05), and this facet only builds against them. | Proposed sequencing. The reference runner already stamps a digest on every produced output, so the first change is signing rather than a new record kind; treating this as a green-field capability would add a second identity for artifacts that already have one. | proposed | `F-b3-12`, `F-b4-05` |
| 2 | Build the first adapter by wrapping, not replacing: put the existing evidence record in a predicate, put the predicate in a statement over the output's digest, sign the envelope with a key this deployment holds, and append the envelope beside the record. | Proposed. The recorded adapter today is JSONL evidence records, each naming the script SHA-256, git commit, tree hash under test, and whether the tree was dirty, which is most of a build-shaped predicate already; wrapping keeps every existing reader working while adding the one thing the concern asks for. | sourced | `F-a5-04`, `F-b3-12` "Append-only JSONL. Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |
| 3 | Build the second adapter as keyless signing with a public append-only log: an ephemeral signing identity obtained per run, the envelope published to a log, and an inclusion proof returned with it. | Proposed second adapter, per the manifest and the recorded swap-candidate column. It breaks a different assumption than the first: the local adapter's trust comes from possession of a file our code rehashes and it works offline, while the log adapter's comes from an identity that expires and a log any third party can verify, and it cannot produce a statement at all without reaching the network. That is the axis the pair has to differ on. | proposed | `F-b3-12`, `F-b1-04`, `X-cap-provenance-004` |
| 4 | Migrate in that order and keep both adapters live behind the same call: digests only, then local signed envelopes, then keyless-and-published selected by configuration. Do not delete the local adapter once the log adapter exists. | Proposed migration. Each step is independently revertible, and keeping the local adapter is what makes the pair testable later; an interface with one surviving implementation drifts back into the shape of whatever runs, which is the failure design rule 3 exists to catch. | proposed | `F-b1-04` |
| 5 | Wire attest at two places only: the emitter that returns a result to a caller, and the run-seal path that closes a run. Give callers no flag that skips either. | Proposed wiring, following cap-provenance's placement rule. Two enforcement points cover every output and every run boundary; a third would be a caller deciding for itself, which is the property a cross-cutting guarantee does not have. | proposed | `F-b1-08`, `T-t2-03` |
| 6 | Sign the sealed head as well as the individual outputs, and use the same envelope format for both so one verifier covers a run and its parts. | Proposed, and it is what docs/decomposition.md section 2.2.3 already specifies for the state seam: a chain gives no way for a third party to verify one record without the whole log, so the sealed head carries the run and the per-output statements carry the parts. | proposed | `F-b5-05`, `F-a5-03` |
| 7 | Make the conformance run adapter-parameterised and store-unmounted from the start: one command, one report shape, `--adapter` selecting which implementation signs, and the external verifier invoked as a subprocess with no access to our store. | Proposed. A suite written against one adapter and adapted later encodes that adapter's assumptions in its asserts, and a suite that can reach our store will eventually be satisfied by it, which is precisely the outcome the concern's contract forbids. | proposed | `F-b1-04`, `F-b4-05` |
| 8 | Proposed: open references/provenance-adapters.md when you need the per-adapter mapping table, the failure modes each adapter can and cannot detect, or the step-by-step swap procedure. This skill body is enough to build either adapter without it. | Proposed, progressive disclosure. The mapping table and the swap runbook are long material that a reader building the first adapter does not yet need. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: verify the runtime effect of the signing configuration rather than the file that declares it. agentic-stack states the configuration finding (F-a7-04); the consequence here is that the only proof a deployment signs with the identity it meant to is an envelope read back and checked, not a settings file reviewed. | proposed | `F-a7-04` |
| Watch the log instead of trusting it once. build-definition-of-done already cites this record for gates (X-cross-structure-053): transparency logs are tamper-evident but not tamper-proof, so it becomes important to have a tool to monitor the transparency log for any evidence of tampering. Publishing without monitoring buys the ability to detect tampering and never exercises it. | sourced | `X-cross-structure-053` "Transparency logs are tamper-evident but not tamper-proof, so it becomes important to have a tool to monitor the transparency log for any evidence of tampering" |
| Proposed: pin and record the external verifier's name and version in every report. A green run that does not say what checked it is a claim about our own code again, and an upgrade that silently relaxes a check is invisible without the version. | proposed | `F-part-c-10` |
| Proposed: give every emitted output the same statement shape whichever step kind produced it, and resist a fast path for cheap outputs. The moment one kind of output attests differently, the orphan count has to be re-proved for each kind, and the cheap path is where the habit of skipping forms. | proposed | `T-t2-03` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-evidence-records` | today | cap-provenance already records this role (F-b3-12, F-a5-04): what is there today is JSONL evidence records with a hash chain, append-only local records naming the script, commit and tree under test, integrity our own reader recomputes, no signature anywhere. What this facet adds is the first adapter that discharges anything, and the one the second is paired against: the local signed envelope described in this skill, the same record in a predicate, in a statement, in an envelope signed by a held key. | Cannot produce a signature at all in its recorded form, and even once signing is added it cannot offer an inclusion proof or a signer whose authority expires, so a third party must trust that the file it was handed is the file that was written. It declares log inclusion proofs unsupported rather than reporting zero. | Add the wrapper in front of the existing append: nothing that reads the records changes, and the envelope is written beside the record rather than in place of it, so the migration is revertible by not reading the new file. | claimed | `F-b3-12`, `F-a5-04`, `E-adapter-jsonl-evidence-records` "JSONL evidence records" |
| `E-swap-candidate-sigstore` | second | Keyless signing with a public append-only log: a signing identity obtained per run and discarded, the envelope published to a log that is append-only and once entries are added they cannot be modified, and an inclusion proof returned to the caller alongside the envelope. | Cannot sign while offline or while the identity provider is unreachable, cannot host a subject whose name must not be public, and adds a network dependency to the emission path that the local adapter does not have. Its execution model is the inverse of the local one: authority comes from an expiring identity and a public log rather than from possession of a file. | cap-provenance already records the two roles and the axis they differ on (F-b3-12, F-b1-04); what this facet adds is the procedure. Select the adapter by configuration only, run the identical store-unmounted verification suite against each, and require the merged report to show adapters_run == 2, selected_by == configuration, and the local adapter's declared subset recorded rather than asserted. | claimed | `F-b3-12`, `F-b1-04`, `X-cross-structure-052` "Sigstore · any attestation store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | docs/decomposition.md section 3.2 row P11, extended with the swap: `python3 tools/conformance/provenance_verify.py --adapter local-signed-jsonl --artifact out/artifact.bin --report out/prov-a.json` then the same command with `--adapter keyless-transparency-log --report out/prov-b.json`, the adapter chosen by configuration with no code edit between runs. Each run produces the artifact, emits the statement, then invokes a third-party verifier we did not write as a subprocess with our evidence store unmounted. Both reports must validate against the ProvenanceConformanceReport shape above and assert, per adapter, `external_verifier_exit == 0`, `attestations_verified > 0`, `subject_mismatches == 0`, `orphan_subjects == 0` and `store_mounted == false`; the log adapter must additionally assert `log_inclusion_proofs > 0`, and the local adapter must declare that member unsupported rather than assert it. |
| Expected | both runs exit 0; the merged report shows `adapters_run == 2`, `selected_by == "configuration"`, `attestations_verified > 0` for each adapter, the external verifier's name and version recorded in each, and `log_inclusion_proofs > 0` for the log adapter only. |
| Deliberate breakage | Rebuild the artifact from a modified input without regenerating the attestation, leaving both adapters and the command untouched. |
| Expected failure | Both runs exit 1 with `subject_mismatches == 1` and `attestations_verified == 0`, the external verifier exiting non-zero on subject digest mismatch, because the mismatch is in the statement and neither signer can hide it. A run where either adapter still exits 0 means the verifier was reading our store rather than the envelope, and `store_mounted` was wrong. Claimed: no statement is emitted anywhere today, neither adapter is written and the conformance tool does not exist, so neither run has been performed here; the measured starting state is recorded in cap-provenance-use, where the reference runner produces 32 subject digests and zero attestations. |
| Status | claimed |
| Evidence | `F-b4-05`, `F-b3-12` "verifiable with a tool we did not write" |

## Composes with

Builds on: `cap-provenance`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`

Used by: `cap-provenance-use`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which adapter is primary once both exist, and does a deployment with no outbound network get the local one or no provenance at all? | Measure, per adapter: emission latency added to the result path, the number of external services that must be reachable for an output to be emitted at all, and whether an outside party who holds only the envelope can verify it. The last is the concern's contract; the second is what decides whether the log adapter can sit on the emission path. | Proposed: the log adapter is primary for run seals and externally visible artifacts, the local adapter for per-step statements, both selected by configuration. A deployment with no outbound network runs the local adapter and records the reduced guarantee rather than emitting nothing. | `F-b1-04` |
| Does the envelope live beside the evidence record, in the state log as an attestation-recorded fact, or in both? | Whether the orphan check in docs/decomposition.md row X4 can be answered from the log alone, and whether any consumer needs the envelope without also needing the record next to it. | Proposed: the attestation-recorded fact in the log carries the subject digest and a reference, and the envelope bytes live in the attestation store, so the orphan check reads one place and the verifier fetches from the other. | `F-b5-05` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-provenance 2831cb4f, 2026-09-03 |
