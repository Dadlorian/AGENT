---
name: cap-provenance-use
description: How to use the Provenance capability as a caller: send what you were going to send, get back a result that carries a subject digest and a reference to a signed statement about it, and hand that statement to any verifier you trust. Load it when you need to show someone outside this platform where an output came from, when an auditor or a downstream system asks for evidence about a result, when you are deciding what to keep after a run so the result stays defensible later, when a result and its statement disagree, or when you are tempted to prove an output by pointing at our own log.
---

# cap-provenance-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| cap-provenance states the contract this rests on (F-b4-05); this facet reduces it to what a caller does, which is nothing: the statement arrives with the result, and the only real action is handing it to a verifier of your own choosing. | sourced | `F-b4-05`, `T-t3-01` "verifiable with a tool we did not write" |

## Entities

| Entity |
|---|
| `E-capability-provenance` |
| `E-concern-provenance` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| receive (proposed) | nothing extra; you send the envelope you were already sending, through whichever entry you already use | your result, plus two fields on it: the subject digest of each output and a reference to the signed statement over that digest | proposed | `F-b4-05` |
| fetch (proposed) | a statement reference, or a subject digest you already hold | the signed envelope itself, which you may keep, forward, or archive; keeping it is what makes the result defensible after our store is gone | proposed | `F-b4-05` |
| verify it yourself (proposed) | the envelope and your own trust policy: whose signatures you accept and what values you expect | accepted or rejected, decided by a verifier you chose and we did not write; you never have to ask us whether our own output is genuine | proposed | `F-b4-05`, `X-cap-provenance-005` |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a result that carries its own evidence** (proposed; sources: `F-b4-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:provenance:example:result",
  "title": "What comes back",
  "description": "Send entries/human.json as usual. The result carries a subject digest per output and a statement reference; you hand the fetched envelope to your own verifier and never touch our store. Proposed: the digest half is what the reference runner emits today, the statement half is not emitted anywhere yet.",
  "examples": [
    {
      "run_id": "run-human-0001",
      "state": "completed",
      "outputs": [
        {
          "step_id": "fix#2",
          "subject_digest": "sha256:0c7ac1524c7ab5870f1018b8f3547b8b4c6324ebedc61530354010f890d6b716",
          "attestation_ref": "urn:agentic:attestation:run-human-0001:fix#2"
        }
      ],
      "your_next_step": "fetch the envelope, run your own verifier over it, keep it"
    }
  ]
}
```

**Worked example 2 (proposed): the failure shape, when a statement does not check out** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:provenance:example:unverifiable",
  "title": "An envelope that does not verify",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Ask for a statement whose subject digest no longer matches the artifact you hold, or whose signer your policy does not accept. The answer is RFC 9457 problem details with media type application/problem+json, the shape cap-errors owns. The type below is proposed and needs a row added to that registry before anything may raise it.",
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
| All three of TARGET T1's ways in reach this the same way. A human must be able to enter the system, an agent must be able to enter the system, and an internal or external event must be able to enter the system; each gets the same subject digests and the same statement references back, and nothing about the evidence depends on which of the three it was. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "2. An agent must be able to enter the system." |
| Proposed: the caller's obligation is zero fields. There is no attest call to make, no key to hold, no flag to set and no way to ask for provenance or to decline it; cap-provenance fixes the contract and cap-provenance-implement wires attest into the emitter and the run seal. | proposed | `F-b1-08`, `F-b4-05` |
| Enhancing one aspect leaves the rest untouched: moving from a held signing key to an expiring identity, changing where envelopes are stored, or adding a new predicate changes nothing in a caller that keeps the envelope it was handed, because the envelope is the only thing it was ever given. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The surface is kept to one returned reference because a contract that is daunting or overly complex will not be used, and a caller who finds evidence expensive to collect will simply not collect it and will have nothing when asked. | sourced | `T-t3-02`, `T-t3-01` "It cannot be daunting or overly complex, or no one will use it." |
| Proposed: an answer from us about our own output is not evidence. The composable move is that the envelope leaves with you, so the check is done by your verifier against your policy; a verification endpoint of ours is a convenience for debugging and is never the thing an auditor is shown. | proposed | `F-b4-05` |
| Proposed: statements compose the way results do. A workflow, a loop or an agent that calls other steps on your behalf produces a statement per output and one over the sealed run, so a caller who kept the run's envelope can still reach every part of it without having watched the run happen. | proposed | `T-t2-03` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: you never see which adapter signed, which key or identity was used, or where the envelope was stored. If a caller could tell the local case from the published one it would start branching on the difference, and the swap would stop being free. | proposed | - |
| Proposed: holding a statement reference does not entitle you to the artifact it is about. The statement names a digest; who may read the bytes stays a matter for identity and policy. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Send what you were already sending. Do not add a provenance field, a signing option or a request to attest; there is nothing to opt into. | Proposed usage of the placement cap-provenance fixes. The platform applies this concern rather than offering it, so a caller-side switch would be a hole rather than a feature. | proposed | `F-b1-08` |
| 2 | Read the subject digest and the statement reference off the result, and store both next to whatever you do with the output. | Proposed. The digest is what ties your copy of an output to the statement about it; a result kept without its digest cannot be matched to any evidence later, and the match is the whole question an auditor asks. | proposed | `F-b4-05` |
| 3 | Fetch the envelope and keep it yourself, rather than keeping a pointer into our store. | The concern's contract is verification with a tool we did not write, and evidence you can only reach through us is evidence that ends when your access does. Keeping the bytes is the difference between citing a record and holding one. | sourced | `F-b4-05` "verifiable with a tool we did not write" |
| 4 | Verify with your own tool and your own policy: name the signers you accept and the values you expect, then check the envelope. | cap-provenance states what an outside verifier does (X-cap-provenance-005), checking cryptographic signatures and matching expected values such as builder ID and source repository; for a caller the consequence is that this is the only check that answers the question you actually have, which is whether to trust us. | sourced | `X-cap-provenance-005` "checking cryptographic signatures and matching expected values such as builder ID and source repository" |
| 5 | Handle exactly one failure, the 422 in worked example 2, and handle it by refusing the artifact rather than by retrying. Everything else that comes back is the ordinary answer or an ordinary typed failure. | Proposed. The failure shape, the media type and the closed registry belong to cap-errors, so a caller that already reads type and retryable needs no new branch here beyond recognising one more registered type; a statement that does not check out will not check out on a second attempt. | proposed | `F-b4-07` |
| 6 | If the statement points at a public append-only log, keep the inclusion proof with the envelope and check the log yourself from time to time rather than only at the moment you receive it. | cap-provenance states this consequence for the capability (X-cross-structure-053); for a caller it means a log is tamper-evident but not tamper-proof, so a proof you never re-check is a guarantee nobody is exercising on your behalf. | sourced | `X-cross-structure-053` "tamper-evident but not tamper-proof" |
| 7 | Proposed: if you want to see the starting state, use examples/end-to-end. Its results already carry a subject digest per output, and it emits no statement at all, which is what the definition of done below measures. | Proposed, and it is the shortest route from this page to something running: the reference runner needs no services, and the gap it shows is the honest one rather than a rehearsed success. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: keep the envelope, not a screenshot of a green check. The envelope is the thing another party can re-check; a record that our verifier said yes is a claim about us again, which is the specific thing this capability exists to stop being the answer. | proposed | `F-b4-05` |
| Ask which level of guarantee the statement carries rather than treating every statement as equal: the build track has four levels representing increasing grades of security, and a statement produced by an unhardened path is still a real statement about a weaker process. | sourced | `X-build-definition-of-done-007` "representing increasing grades of security" |
| Proposed: pin the verifier you use and record its version alongside the envelope. A check that passed under one verifier and a later one that does not is a fact worth keeping, and without the version you cannot tell a relaxed check from a changed artifact. | proposed | `F-part-c-10` |
| Proposed: treat a missing statement as a defect to report, not as a case to handle. Provenance is applied by the platform, so an output arriving with a digest and no statement means the emitter was bypassed, and a caller that quietly tolerates it is the reason nobody notices. | proposed | `F-b1-08` |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `cd examples/end-to-end && bash test.sh` to produce the corpus, then the caller-side provenance assertion over what it appended: `python3 -c "import json,re;r=[json.loads(l) for l in open('out/ledger.jsonl')];s=[x for x in r if 'output_digest' in x or x.get('kind')=='agent-called'];nod=[x for x in s if not re.fullmatch(r'sha256:[0-9a-f]{64}', x.get('output_digest',''))];att=[x for x in r if x.get('kind')=='attestation-recorded'];orph=[x for x in s if x.get('output_digest') not in {a.get('subject_digest') for a in att}];print(f'records={len(r)} subjects={len(s)} subjects_without_digest={len(nod)} attestations_found={len(att)} orphan_subjects={len(orph)}');raise SystemExit(1 if nod or orph else 0)"`. It asserts what a caller is promised: every produced output carries a subject digest, and every subject digest has a statement over it that the caller could take away. |
| Expected | test.sh exits 0 and prints `passed 29, failed 0`; the assertion prints `records=56 subjects=32 subjects_without_digest=0 attestations_found=0 orphan_subjects=32` and exits 1. That is the correct starting state, not a pass: the digest half is delivered today and the statement half is not delivered anywhere, so this check starts red by construction and turns green only when cap-provenance-implement's first signing adapter exists. |
| Deliberate breakage | In `examples/end-to-end/run.py`, delete the `output_digest=` argument from the `record("agent-called", ...)` call, which is what emitting an output with nothing identifying it looks like from the caller's side. Change nothing else. |
| Expected failure | test.sh still exits 0 and still prints `passed 29, failed 0` - the existing suite asserts nothing about provenance, which is the useful half of this breakage - while the assertion prints `records=56 subjects=32 subjects_without_digest=32 attestations_found=0 orphan_subjects=32` and exits 1, the first counter having moved from 0 to 32. Measured in session cap-provenance 2831cb4f on 2026-09-03: both runs were performed, the broken run against a copy of examples/end-to-end in this session's scratchpad, and the repository tree was left unmodified (run.py sha256 e54d31b921b707bc672c3ec6f680a7c0a77fdc9b70202ff56699e4f01d55f7e9). |
| Status | measured |
| Evidence | `F-b4-05` "Every artifact is attributable to the code version, inputs and actor that produced it" |

## Composes with

Builds on: `cap-provenance`, `cap-provenance-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The reference runner lists provenance as delivered by a hash chain plus per-output digest, verified with `python3 run.py --verify-ledger`, which is our own reader over our own file. | Measured on 2026-09-03: the corpus carries 32 subject digests and zero statements, so nothing an outside verifier could read is produced. agentic-stack already cites the chain property that command checks (F-a5-03), each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable; that is integrity for us, and the concern's contract is verification with a tool we did not write. | Recorded as a disagreement with examples/end-to-end rather than resolved here. The change proposed: keep `--verify-ledger` as the integrity check it is, rename what the README calls provenance to integrity, and add a provenance row that stays red until the first signing adapter emits an envelope. | `F-b4-05`, `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| Which problem type does an unverifiable statement raise, given that the first-cut registry in docs/decomposition.md section 2.1.6 has no provenance row? | Whether any existing registered type fits: the closest are document-invalid, which is about schema validation, and identity-untrusted, which is about a delegation chain. Neither is about a subject digest that no longer matches. | Proposed: add one row, attestation-unverifiable at 422 and not retryable, as worked example 2 shows. cap-errors owns the registry, so the row lands there and this skill cites it; until it does, the type in that example is proposed and unregistered. | `F-b4-07` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-provenance 2831cb4f, 2026-09-03 |
