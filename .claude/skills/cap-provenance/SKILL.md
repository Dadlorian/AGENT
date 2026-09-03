---
name: "cap-provenance"
description: "The ideal state of the Provenance capability: a signed statement binding an artifact to the code version, inputs and actor that produced it, in a format a verifier we did not write can check standing alone. Load it when deciding what makes an output accountable after the fact, when choosing an attestation format or a predicate, when judging whether a store's own integrity check counts as verification, or when a review asks how an outsider would confirm that this output came from that input. Also load it when someone proposes proving an output by rehashing our own log, when an agent action rather than a build artifact is the thing to be vouched for, when signing keys or a transparency log come up, and when a record is described as tamper-proof."
---

# cap-provenance

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix the contract for producing a signed statement about an artifact or an agent action, so that accountability is a property an outside party can check rather than a claim our own store makes about itself. | sourced | `F-b4-05`, `F-b3-12`, `E-capability-provenance`, `E-concern-provenance` "Every artifact is attributable to the code version, inputs and actor that produced it" |

## Entities

| Entity |
|---|
| `E-capability-provenance` |
| `E-concern-provenance` |
| `E-standard-in-toto` |
| `E-standard-slsa` |
| `E-standard-dsse` |
| `E-adapter-jsonl-evidence-records` |
| `E-swap-candidate-sigstore` |
| `E-swap-candidate-any-attestation-store` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-in-toto` | Attestation Framework v1.0.2; Statement v1 | unverified | https://github.com/in-toto/attestation | `F-b3-12`, `X-cross-structure-050`, `X-end-to-end-052`, `X-cap-provenance-001`, `X-gap-c-001` |
| `E-standard-dsse` | unverified | unverified | - | `F-b3-12`, `X-cap-provenance-003`, `X-cross-structure-050` |
| `E-standard-slsa` | v1.1 or v1.0, unverified | unverified | https://slsa.dev/spec/v1.1/ | `F-b3-12`, `X-end-to-end-051`, `X-cap-provenance-002` |

- `E-standard-in-toto` version note: X-gap-c-001 (search-only, not fetched): "in-toto Attestation Framework defines a standard format for attestations which bind subjects to arbitrary authenticated metadata about the artifact". Statement v1 per X-cap-provenance-001. Row owned by cap-provenance.
- `E-standard-dsse` version note: unverified (no version string appears in any record on file; the envelope format is named, not versioned)
- `E-standard-slsa` version note: v1.1 per one search-only record, against v1.0 in the manifest entry for this skill; neither was fetched, so the version stays unverified and the open question below records the disagreement

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| attest (operation set the recorded standards fix a document format for, not a set of calls) | one or more subject digests, a predicate type, the predicate body, and the actor on whose behalf the statement is made | a signed envelope carrying an in-toto Statement over those subjects, returned to the caller and handed to the store | sourced | `F-b4-05`, `X-cross-structure-050` "can be broken down to three layers" |
| verify | an envelope and a trust policy naming the accepted signers and expected values | accepted or rejected with the reason; the platform's own implementation of this call is a convenience, and the contract is that an outside verifier reaches the same answer from the envelope alone | sourced | `F-b4-05`, `X-cap-provenance-005` "checking cryptographic signatures and matching expected values such as builder ID and source repository" |
| resolve (proposed) | a subject digest | every envelope whose statement names that digest as a subject, so a reader holding only an output can find what vouches for it | proposed | `F-b4-05` |
| publish (proposed) | an envelope and the store it belongs in | a location a third party can fetch the envelope from without holding our credentials; where that location is an append-only log, the fetch also carries an inclusion proof | proposed | `X-cap-provenance-006`, `X-cross-structure-052` |

### Shapes (JSON Schema 2020-12)

**Attestation (summary shape of the envelope-statement-predicate stack the recorded standards define; the full schemas and the predicate field tables are in references/attestation-shapes.md)** (sourced; sources: `X-cross-structure-050`, `X-cap-provenance-003`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:provenance:attestation:0.1",
  "title": "Attestation",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "payloadType",
    "payload",
    "signatures"
  ],
  "properties": {
    "payloadType": {
      "const": "application/vnd.in-toto+json"
    },
    "payload": {
      "type": "string",
      "description": "Base64 of the in-toto Statement. Decoded, it carries _type https://in-toto.io/Statement/v1, subject[] of {name, digest}, predicateType and predicate."
    },
    "signatures": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": [
          "sig"
        ],
        "properties": {
          "keyid": {
            "type": "string"
          },
          "sig": {
            "type": "string",
            "description": "Over the Pre-Authentication Encoding of payloadType and payload, never over the raw JSON."
          }
        }
      }
    }
  }
}
```

**AgentActionPredicate (proposed; no standard predicate for agent actions exists on file, so this half of the capability is ours and is marked proposed)** (proposed; sources: `X-cross-structure-054`, `F-b4-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:provenance:predicate:agent-action:0.1",
  "title": "AgentActionPredicate",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "actor",
    "tool",
    "argument_digest",
    "result_digest",
    "started_at",
    "ended_at"
  ],
  "properties": {
    "actor": {
      "type": "object",
      "description": "The subject and delegation chain of the acting unit; the shape belongs to the identity capability."
    },
    "tool": {
      "type": "string",
      "description": "The tool or model class invoked, named as a class, never as a vendor."
    },
    "argument_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "result_digest": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "decision_refs": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "References to the policy and budget decisions that permitted the action."
    },
    "code_version": {
      "type": "string"
    },
    "started_at": {
      "type": "string",
      "format": "date-time"
    },
    "ended_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

**Worked example 2 (proposed): the failure shape, when a statement does not check out [caller's view, folded from cap-provenance-use]** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:provenance:example:unverifiable",
  "title": "An envelope that does not verify",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Ask for a statement whose subject digest no longer matches the artifact you hold, or whose signer your policy does not accept. The answer is RFC 9457 problem details with media type application/problem+json, the shape cap-errors owns. The type below is proposed and needs a row added to that registry before anything may raise it. The type is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns: until `urn:agentic:problem:attestation-unverifiable` has a row, an implementation returns the registered `document-invalid`, which is also 422 and not retryable, with the statement id and the digest that did not match in detail.",
  "examples": [
    {
      "type": "urn:agentic:problem:attestation-unverifiable",
      "title": "The statement does not check out against the artifact",
      "status": 422,
      "detail": "subject digest sha256:0c7ac15... in urn:agentic:attestation:run-human-0001:fix#2 does not match the artifact supplied",
      "retryable": false
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| The contract this capability must deliver is one sentence: every artifact is attributable to the code version, inputs and actor that produced it, and that attribution is checkable by a tool we did not write. build-evidence-record states the same record as the boundary of its own discipline (F-b4-05). | sourced | `F-b4-05`, `E-concern-provenance` "Every artifact is attributable to the code version, inputs and actor that produced it" |
| The recorded row for this capability names in-toto, SLSA and DSSE as the governing standards, JSONL evidence records as the adapter today, and a keyless-signing service or any attestation store as the swap candidates. | sourced | `F-b3-12`, `E-capability-provenance` "in-toto · SLSA · DSSE \| JSONL evidence records" |
| An attestation is three layers, and they stay distinct: the envelope that carries the signature, the statement that names the subjects, and the predicate that carries the payload. A verifier can check the signature and the subject digests without understanding our predicate at all, which is what makes an outside check possible. | sourced | `X-cross-structure-050` "can be broken down to three layers" |
| The statement header is a fixed, versioned type rather than a shape of ours: the embedded attestation in the envelope carries a _type of https://in-toto.io/Statement/v1. A statement missing it is not something a third-party verifier will read. | sourced | `X-cross-structure-050` "The embedded attestation in the dsse envelope includes a" |
| One capability carries two predicates. For an artifact the predicate is build-shaped, and the established model already binds what this concern asks for: provenance is a claim that some entity (builder) produced one or more software artifacts (Statement's subject) by executing some recipe, using some other artifacts as input (materials). | sourced | `X-cross-structure-051`, `F-b4-05` "Provenance is a claim that some entity (builder) produced one or more software artifacts (Statement's subject) by executing some recipe, using some other artifacts as input (materials)." |
| The second predicate is run-shaped and covers an agent action rather than a build, carrying actor, tool, argument digest, result digest and the decision references that permitted it, per the AgentActionPredicate shape above. Prior art exists for per-action signed receipts, taken whenever the agent makes an external call like querying an API, editing a file, or invoking a tool; no standard predicate type for it appears in any record on file, so the predicate type URI itself is this platform's own, not adopted from elsewhere. | sourced | `X-cross-structure-054` "Whenever the agent makes an external call like querying an API, editing a file, or invoking a tool" |
| Proposed: both predicates travel as in-toto Statements inside the same envelope format and through the same attest call, so one verifier and one trust policy cover an artifact and an agent action. Two envelope formats would mean the outside check works for builds and not for the thing this platform actually does. Research query: does the in-toto Attestation Framework (X-cap-provenance-001) explicitly endorse carrying a run-shaped predicate in the same Statement type as a build-shaped one, or is unifying them under one envelope this platform's own extension of the framework? | proposed | `X-cross-structure-050`, `X-cross-structure-054` |
| Verification is judged by what an outside verifier does: it checks cryptographic signatures and matches expected values such as builder ID and source repository. A check that reads our store, our chain or our reader has not met this concern's contract whatever it reports. | sourced | `X-cap-provenance-005`, `F-b4-05` "checking cryptographic signatures and matching expected values such as builder ID and source repository" |
| This capability is applied by the platform and cannot be requested or declined, because cross-cutting guarantees are not optional. agentic-stack states design rule 7 (F-b1-08); the consequence here is that there is no attest flag on any request shape, and an output with no statement over its digest is a defect rather than a caller's choice. | sourced | `F-b1-08`, `F-b4-01` "Cross-cutting guarantees are not optional" |
| All three of TARGET T1's ways in - a human, an agent, an internal or external event - reach this capability the same way, and enhancing one aspect of it leaves the rest untouched: moving from a held signing key to an expiring identity, changing where envelopes are stored, or adding a new predicate changes nothing in a caller that keeps the envelope it was handed, because the envelope is the only thing it was ever given. cap-errors states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the artifact itself never travels in a predicate, only its digest. A statement has to be publishable to a party that may not read the output it vouches for, and a predicate carrying the payload would make publication a disclosure decision every time. Research query: does F-b4-05's 'verifiable with a tool we did not write' requirement itself imply the artifact stays out of the predicate, or is that a separate design step this row is taking beyond what the fact states? | proposed | `F-b4-05` |
| Signing material is not part of this interface. A caller asks for a statement and receives an envelope; which key, which identity and which lifetime signed it is the adapter's business, which is what makes moving from a held key to an ephemeral one a configuration change rather than an interface change. | sourced | `X-cap-provenance-004` "ephemeral key signing tied to OIDC identities" |
| The criterion a result is judged against never appears in a predicate, in a subject name or in a trust policy. agentic-stack states design rule 6 (F-b1-07); the consequence here is that an attestation over a judged output records the verdict and the digests, never the rule. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Adopt the three-layer document as given and add nothing to the outer two: an envelope carrying the signature, an in-toto Statement carrying the statement type and the subject digests, and a predicate for everything of ours. | Proposed adoption of the recorded standards. Everything a foreign verifier reads lives in the outer two layers, so any field of ours placed there is a field that makes the document unreadable to the tool the concern requires. | sourced | `X-cross-structure-050` "the transport layer, the in-toto Statement: the attestation header, and the predicate: the attestation payload" |
| 2 | Bind the subject as a digest set computed over canonical bytes, and name the subject by a stable identifier rather than by a path or a URL. | Proposed. The subject digest is the only thing that ties a statement to a thing, and it is the assertion the P11 breakage attacks: a rebuilt artifact must stop matching. A path is not stable across stores and would let a statement follow the wrong bytes. Research query: does the in-toto Statement spec (informing this row via F-b3-12) name 'canonical bytes' or a specific digest algorithm as the subject-binding method, which this row could cite directly instead of asserting it? | proposed | `F-b4-05` |
| 3 | For an artifact, fill the build-shaped predicate with the builder, the recipe, the materials and the subject, and populate them from what the platform already records rather than from a re-declared description of the build. | The established provenance predicate binds exactly the code version, inputs and actor this concern asks for, so adopting its field set means the contract is met by construction rather than by argument. | sourced | `X-cross-structure-051`, `X-cap-provenance-002` "capturing builder identity, build instructions, parameters, environment variables, and dependency digests" |
| 4 | For an agent action, emit the AgentActionPredicate above under a predicate type URI this platform owns, and say in the same place that it is proposed and has no standard behind it. | Proposed. A predicate type is an extension point the framework provides, so inventing one is legitimate; presenting it as a standard is not. Marking it keeps a reader from concluding that an outside verifier will understand the payload as well as it understands the envelope. Research query: has any other platform registered a predicate type URI for agent-action receipts (beyond the AAL prior art in X-cross-structure-054) that this platform's own URI should track or interoperate with? | proposed | `X-cross-structure-054`, `X-cap-provenance-001` |
| 5 | Judge every candidate implementation by running a verifier nobody here wrote, against the envelope alone, with our store unreachable. | The concern's contract is verification by a tool we did not write, and the only way to establish that our store is not secretly required is to take it away during the check. A verifier that succeeds with the store mounted proves nothing about the case that matters. | sourced | `F-b4-05`, `X-cap-provenance-005` "attributable to the code version, inputs and actor that produced it, verifiable with a tool we did not write" |
| 6 | Publish each envelope where a third party can fetch it, and treat the choice of store as configuration: attestations can be stored in a transparency log, or in a plain attestation store, and the interface must not care which. | The recorded swap candidates are a keyless-signing service or any attestation store, so the store is exactly the axis the second adapter moves along. An interface that assumes a log cannot host the local case, and one that assumes a file cannot host the public case. | sourced | `X-cap-provenance-006`, `F-b3-12` "Attestations can be stored in a transparency log" |
| 7 | Where the store is an append-only log, monitor it rather than trusting it, and record the monitoring as part of the capability instead of as an operational extra. | build-definition-of-done already cites this record for gates (X-cross-structure-053); the consequence for this capability is that transparency logs are tamper-evident but not tamper-proof, so a log nobody watches gives a third party the ability to detect tampering that nobody is exercising. | sourced | `X-cross-structure-053`, `X-cross-structure-052` "tamper-evident but not tamper-proof" |
| 8 | Send what you were already sending. Do not add a provenance field, a signing option or a request to attest; there is nothing to opt into. | Proposed usage of the placement this skill fixes. The platform applies this concern rather than offering it, so a caller-side switch would be a hole rather than a feature. | sourced | `F-b1-08` "Cross-cutting guarantees are not optional.** Telemetry, policy, provenance and budget are applied" |
| 9 | Proposed: open references/attestation-shapes.md when you need the full statement and predicate schemas, the field-by-field mapping from the build-shaped predicate to what the platform records, or the trust-policy fields. This skill body is enough to judge an implementation without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed, progressive disclosure. The two schemas run past the length at which a contract stops being readable, and a reader deciding whether an implementation is acceptable does not need the field tables to do it. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Keep note-taking and attestation apart. build-evidence-record is the discipline for recording what was run and observed; this capability produces a signed envelope for someone else. Merging them is how an unsigned note ends up quoted as if a third party had checked it. | sourced | `F-a5-04`, `E-concern-provenance` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |
| Sign over the encoding, not the document: the signature is computed over the Pre-Authentication Encoding (PAE) of the payload type and payload bytes, not over the raw JSON, which prevents format-confusion attacks. A signature taken over serialised JSON is a signature over one of many spellings of the same object. | sourced | `X-cap-provenance-003` "The signature is computed over the Pre-Authentication Encoding (PAE) of the payload type and payload bytes, not over the raw JSON, which prevents format-confusion attacks." |
| Say which level of guarantee you are claiming rather than claiming provenance flatly: the build track has four levels representing increasing grades of security, from no provenance at all to a hardened, isolated build platform with authenticated, signed provenance. An unlevelled claim reads as the top of that range and is almost never earned. | sourced | `X-build-definition-of-done-007` "the build track has four levels (L0–L3) representing increasing grades of security, from no provenance at L0 to a hardened, isolated build platform with authenticated, signed provenance at L3" |
| Prefer signing identities that expire to keys that are held: ephemeral key signing tied to OIDC identities removes the long-lived secret that a held key makes someone responsible for, and moves the question from who has the key to who was allowed to be that identity at that moment. | sourced | `X-cap-provenance-004` "ephemeral key signing tied to OIDC identities" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-jsonl-evidence-records` | today | The recorded adapter is JSONL evidence records: append-only local records naming what was run and the tree under test, integrity carried by a hash chain that our own reader recomputes. It serves resolve, because a digest can be looked up, and it serves the note-taking half of attest. | Cannot produce a signature at all, so it cannot serve verify for anyone outside this repository: the check is a rehash performed by code we wrote, against a file only we hold. Its execution model is a local file whose trust comes from possession. | Wrap what is already written rather than replacing it: put the existing record in a predicate, put the predicate in a statement, and sign the envelope. cap-provenance-implement owns the migration, the per-adapter conformance subsets and the full procedure; this row records the roles PASS.md B3 fixes and the axis the pair differs on. | claimed | `F-b3-12`, `F-a5-04`, `E-adapter-jsonl-evidence-records` "JSONL evidence records" |
| `E-swap-candidate-sigstore` | second | Keyless signing with a public transparency log: the envelope is signed by an ephemeral key tied to an OIDC identity and verified through the Rekor transparency log, which is append-only and once entries are added they cannot be modified, and a valid log can be cryptographically verified by any third-party. | Cannot produce a statement while offline or while the identity provider is unreachable, and cannot host a subject that must not be publicly listed, where the recorded adapter needs nothing beyond a local file. The axis the pair is chosen for is where trust comes from: possession of a local file that our own code rehashes, against an ephemeral identity and a public log any third party can verify. That is a different execution model, not a different product of the same shape. | Select the adapter by configuration only, with no code edit between runs, and run the identical external-verification suite against each; the merged report must show adapters_run >= 2. agentic-stack already states design rule 3 (F-b1-04): the second adapter exists to prove the first is not load-bearing. What is new here is the axis, not the rule. | claimed | `F-b3-12`, `F-b1-04`, `X-cap-provenance-004`, `X-cross-structure-052` "Sigstore · any attestation store" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/conformance/provenance_verify.py --adapter local-signed-jsonl --adapter keyless-transparency-log --artifact out/artifact.bin --report out/prov.json |
| Expected | docs/decomposition.md section 3.2 row P11, made precise and run over the adapter pair above: that command (proposed tool, built with the first signing adapter), the adapter selected by configuration with no code edit between runs. Per adapter it produces an artifact, emits the statement, then shells out to a third-party verifier that we did not write, with our evidence store unmounted, and asserts that the external verifier exits 0, that `attestations_verified > 0`, and that every subject digest in the statement matches the artifact on disk; across adapters it asserts `adapters_run >= 2`. exit 0 with, per adapter, `external_verifier_exit == 0`, `attestations_verified > 0`, `subject_mismatches == 0` and `store_mounted == false`, followed by `adapters_run=2` |
| Deliberate breakage | Rebuild the artifact from a modified input without regenerating the attestation, and re-run the same command unchanged. |
| Expected failure | exit 1 with the external verifier exiting non-zero on subject digest mismatch, `subject_mismatches == 1` and `attestations_verified == 0`, under both adapters, because the mismatch is in the statement rather than in either signer; a run where the external verifier still exits 0 means the check was reading our own store and the store was not actually unmounted. Claimed: no statement is emitted anywhere today, neither signing adapter is written and the conformance tool does not exist, so neither run has been performed here. What is measured is the starting state, recorded in cap-provenance-use: the reference runner emits subject digests and zero attestations. |
| Status | claimed |
| Evidence | `F-b4-05`, `F-b3-12` "verifiable with a tool we did not write" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-evidence-record`, `build-skill-authoring`, `cap-errors`

Used by: `cap-capability-registry`, `cap-mandate-broker`, `cap-provenance-implement`, `xc-audit-trail`, `xc-provenance-chain`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Which version of the maturity framework governs, and which statement and envelope versions can be cited as verified? | A fetch of each specification recording the version string and the date. One search-only record on file says version 1.1 of the SLSA specification defines several SLSA levels and recommended attestation formats, while the manifest entry for this skill says v1.0; the proxy blocked documentation fetches in this session, so neither was read. | Every standard in the table above stays version_status unverified, and no skill states a level claim until a fetch has happened. Reversible by one fetch and one edit per row. | `X-end-to-end-051`, `F-part-c-10` "Version 1.1 of the SLSA specification defines several SLSA levels and recommended attestation formats" |
| Is the agent-action predicate proposed upstream as a predicate type, or kept as a platform-owned URI? | Whether any published predicate type covers actor, tool, argument digest and result digest for a runtime action; the only record on file describing per-action signed receipts is a paper, not a specification, and nothing was fetched here. | Proposed: a platform-owned predicate type URI, versioned, with the field set above and a note in every skill that cites it saying it is ours. Reversible: adopting a published type later changes the predicateType string and nothing in the envelope or the statement. | `X-cross-structure-054` "a compact, tamper-proof record summarizing the action's essential details" |
| Does every attested subject go to a public log, or only the sealed heads that cross a run boundary? | Measure the volume of subjects a representative workload produces against what a public log will accept, and count how many subjects would disclose a caller's payload by their name alone. | Proposed: seal and publish at run close and on any externally visible artifact, and keep per-step statements in the local store, so the public surface stays small while every step is still covered by a statement someone can ask for. | `X-cross-structure-052`, `X-cap-provenance-006` "The log is append-only and once entries are added they cannot be modified" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-provenance 2831cb4f, 2026-09-03 |
