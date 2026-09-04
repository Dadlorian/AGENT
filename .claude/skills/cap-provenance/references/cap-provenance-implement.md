---
name: "cap-provenance-implement"
description: "How to build the Provenance capability on this stack: what the append-only evidence records and the hash-chained store already give you and what they do not, a first adapter that wraps an existing record in a signed envelope with a held key, a second with a different execution model that signs with an ephemeral identity and publishes to a public append-only log, the migration between them, where the attest call is wired so no output can skip it, and a definition of done with the breakage that makes it fail. Load it when writing the code that emits or checks a statement, when picking where envelopes are stored, when adding signing to a pipeline that today only rehashes its own file, or when a conformance run reports an output with no statement over its digest."
---

# cap-provenance-implement (folded into `cap-provenance`)

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

**ProvenanceConformanceReport (the counters the definition of done below asserts on, per adapter)** (sourced; sources: `T-t9-06`)

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
| Proposed: the statement is emitted at the moment the artifact is produced, from the values in hand, never reconstructed later from a log. A statement assembled after the fact attests to what the log says happened, which is the claim it was supposed to be independent of. Research query: does F-b4-05's attributability contract, read in full, fix that a statement must be emitted at production time rather than reconstructed later from the log, or is the emit-not-reconstruct rule this facet's own reading of what attributability requires? | proposed | `F-b4-05` |
| cap-provenance and build-evidence-record already fix that an artifact must be verifiable with a tool we did not write (F-b4-05). The build consequence: the verification half of the definition of done runs with our evidence store unreachable and shells out to a verifier nobody here wrote. A run with the store mounted is recorded as unsupported rather than as a pass, so store_mounted is a const in the report shape above rather than a field an implementation can set. | sourced | `F-b4-05` "verifiable with a tool we did not write" |
| build-definition-of-done already names the structurally-green trap (F-a7-03): a gate can pass while asserting nothing. The build consequence here: the local adapter declares log inclusion proofs unsupported instead of reporting zero of them. A documented conformance subset is honest; an adapter that reports a property it cannot provide is exactly the failure the pair exists to expose. | sourced | `F-a7-03` "A deterministic gate can be structurally green and mean nothing" |
| agentic-stack and build-evidence-record already fix the chain our own reader recomputes (F-a5-03): JSONL, hash-chained, where each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable. The build consequence: that is integrity for us and evidence for nobody else, so the signed envelope is added on top of it and the chain is not removed. | sourced | `F-a5-03`, `F-b5-05` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| cap-provenance states design rule 7 as the reason for this placement, and agentic-stack fixes that cross-cutting guarantees are applied by the platform, not requested by the caller (F-b1-08). The build consequence: attest is wired into the platform's result emitter and its run-seal path, not into each caller, and there is no flag that skips it - a new step kind inherits attestation by construction because it reaches emission through the same path. | sourced | `F-b1-08` "applied by the platform, not requested by the caller" |
| Proposed: a failure to attest, sign or publish is returned as problem details from the registry cap-errors owns, and this capability mints no failure object of its own; a new registry row is required before any new type is raised. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Start from what is already true: subject digests exist and nothing signs them. Do not re-derive the contract; cap-provenance states the recorded row (F-b3-12) and the concern's contract (F-b4-05), and this facet only builds against them. | Proposed sequencing. The reference runner already stamps a digest on every produced output, so the first change is signing rather than a new record kind; treating this as a green-field capability would add a second identity for artifacts that already have one. Research query: is there a fetched (not search-only) record naming this platform's evidence store as unsigned subject digests specifically (as opposed to the general provenance row F-b3-12), which would source the starting-point claim directly rather than via this facet's own paraphrase of it? | proposed | `F-b3-12`, `F-b4-05` |
| 2 | Build the first adapter by wrapping, not replacing: put the existing evidence record in a predicate, put the predicate in a statement over the output's digest, sign the envelope with a key this deployment holds, and append the envelope beside the record. | Proposed. The recorded adapter today is JSONL evidence records, each naming the script SHA-256, git commit, tree hash under test, and whether the tree was dirty, which is most of a build-shaped predicate already; wrapping keeps every existing reader working while adding the one thing the concern asks for. | sourced | `F-a5-04`, `F-b3-12` "Append-only JSONL. Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |
| 3 | Build the second adapter as keyless signing with a public append-only log, the way cap-provenance's own swap candidate names it: an ephemeral signing identity obtained per run, verified through the Rekor transparency log rather than a held key, the envelope published to a log, and an inclusion proof returned with it. | Proposed second adapter, per the manifest and the recorded swap-candidate column. It breaks a different assumption than the first: the local adapter's trust comes from possession of a file our code rehashes and it works offline, while the log adapter's comes from an identity that expires and a log any third party can verify, and it cannot produce a statement at all without reaching the network. That is the axis the pair has to differ on. | sourced | `X-cap-provenance-004`, `F-b3-12` "verified through the Rekor transparency log" |
| 4 | Wire attest at two places only: the emitter that returns a result to a caller, and the run-seal path that closes a run. agentic-stack fixes that cross-cutting guarantees are not optional (F-b1-08); the build consequence is that callers get no flag that skips either. | Proposed wiring, following cap-provenance's placement rule. Two enforcement points cover every output and every run boundary; a third would be a caller deciding for itself, which is the property a cross-cutting guarantee does not have. | sourced | `F-b1-08` "Cross-cutting guarantees are not optional" |
| 5 | Sign the sealed head as well as the individual outputs, and use the same envelope format for both so one verifier covers a run and its parts. | Proposed, and it is what docs/decomposition.md section 2.2.3 already specifies for the state seam: a chain gives no way for a third party to verify one record without the whole log, so the sealed head carries the run and the per-output statements carry the parts. Research query: does F-b5-05's chain description, read in full rather than as a table row, fix that the sealed head and the individual outputs must share one envelope format, or is that unification this facet's own design choice? | proposed | `F-b5-05`, `F-a5-03` |
| 6 | cap-provenance and build-evidence-record already fix that an artifact must be verifiable with a tool we did not write (F-b4-05). The build consequence: make the conformance run adapter-parameterised and store-unmounted from the start: one command, one report shape, `--adapter` selecting which implementation signs, and the external verifier invoked as a subprocess with no access to our store. | Proposed. A suite written against one adapter and adapted later encodes that adapter's assumptions in its asserts, and a suite that can reach our store will eventually be satisfied by it, which is precisely the outcome the concern's contract forbids. | sourced | `F-b4-05` "verifiable with a tool we did not write" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Verify the runtime effect of the signing configuration rather than the file that declares it. agentic-stack and build-definition-of-done state the configuration finding (F-a7-04): what a file declares was silently discarded at runtime before. The consequence here is that the only proof a deployment signs with the identity it meant to is an envelope read back and checked, not a settings file reviewed. | sourced | `F-a7-04` "was silently discarded" |
| Watch the log instead of trusting it once. build-definition-of-done already cites this record for gates (X-cross-structure-053): transparency logs are tamper-evident but not tamper-proof, so it becomes important to have a tool to monitor the transparency log for any evidence of tampering. Publishing without monitoring buys the ability to detect tampering and never exercises it. | sourced | `X-cross-structure-053` "Transparency logs are tamper-evident but not tamper-proof, so it becomes important to have a tool to monitor the transparency log for any evidence of tampering" |
| Proposed: pin and record the external verifier's name and version in every report. A green run that does not say what checked it is a claim about our own code again, and an upgrade that silently relaxes a check is invisible without the version. Research query: does F-part-c-10's preference for an existing standard over an original design extend to pinning that standard's implementation version in every conformance report, or does it only cover choosing the standard, leaving the pin-and-record practice this facet's own? | proposed | `F-part-c-10` |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-evidence-records` | today | cap-provenance already records this role (F-b3-12, F-a5-04): what is there today is JSONL evidence records with a hash chain, append-only local records naming the script, commit and tree under test, integrity our own reader recomputes, no signature anywhere. What this facet adds is the first adapter that discharges anything, and the one the second is paired against: the local signed envelope described in this skill, the same record in a predicate, in a statement, in an envelope signed by a held key. | Cannot produce a signature at all in its recorded form, and even once signing is added it cannot offer an inclusion proof or a signer whose authority expires, so a third party must trust that the file it was handed is the file that was written. It declares log inclusion proofs unsupported rather than reporting zero. | Add the wrapper in front of the existing append: nothing that reads the records changes, and the envelope is written beside the record rather than in place of it, so the migration is revertible by not reading the new file. | claimed | `F-b3-12`, `F-a5-04`, `E-adapter-jsonl-evidence-records` "JSONL evidence records" |
| `E-swap-candidate-sigstore` | second | Keyless signing with a public append-only log: a signing identity obtained per run and discarded, the envelope published to a log that is append-only and once entries are added they cannot be modified, and an inclusion proof returned to the caller alongside the envelope. | Cannot sign while offline or while the identity provider is unreachable, cannot host a subject whose name must not be public, and adds a network dependency to the emission path that the local adapter does not have. Its execution model is the inverse of the local one: authority comes from an expiring identity and a public log rather than from possession of a file. | cap-provenance already records the two roles and the axis they differ on (F-b3-12, F-b1-04); what this facet adds is the procedure. Select the adapter by configuration only, run the identical store-unmounted verification suite against each, and require the merged report to show adapters_run == 2, selected_by == configuration, and the local adapter's declared subset recorded rather than asserted. | claimed | `F-b3-12`, `F-b1-04`, `X-cross-structure-052` "Sigstore · any attestation store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/provenance/test.sh && python3 harness/provenance/conformance.py --adapter dryrun --adapter second |
| Expected | Measured by tools/measure.py at 372cdc1: exit 0; last lines:   cases=13 passed=13 emitted=2 verified=1 subject_mismatches=0 orphan_subjects=0 store_mounted=False verifier_exit=0 log_inclusion_proofs=1 product_hits=0 \| conformance PASSED: 26/26 cases, 2 binding(s) |
| Deliberate breakage | Append a product-name comment (`# breakage: sigstore`) to the end of harness/provenance/call.py, outside adapters/. Restored with `git checkout -- harness/provenance/call.py`. |
| Expected failure | Measured by tools/measure.py at 372cdc1: exit 1; last lines:   ok   the run names what broke it \| passed 21, failed 6 |
| Status | measured |
| Evidence | `F-b4-05`, `F-b3-12` "verifiable with a tool we did not write" |

## Composes with

Builds on: `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `cap-provenance`

Used by: -

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
