# cap-provenance: the caller's view

Proposed. Folded in from the former `cap-provenance-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-provenance` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-provenance states the contract this rests on (F-b4-05); this facet reduces it to what a caller does, which is nothing: the statement arrives with the result, and the only real action is handing it to a verifier of your own choosing.  
  _sourced_ - `F-b4-05`, `T-t3-01` "verifiable with a tool we did not write"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| receive (proposed) | nothing extra; you send the envelope you were already sending, through whichever entry you already use | your result, plus two fields on it: the subject digest of each output and a reference to the signed statement over that digest | proposed | `F-b4-05` |
| fetch (proposed) | a statement reference, or a subject digest you already hold | the signed envelope itself, which you may keep, forward, or archive; keeping it is what makes the result defensible after our store is gone | proposed | `F-b4-05` |
| verify it yourself (proposed) | the envelope and your own trust policy: whose signatures you accept and what values you expect | accepted or rejected, decided by a verifier you chose and we did not write; you never have to ask us whether our own output is genuine | proposed | `F-b4-05`, `X-cap-provenance-005` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-provenance` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a result that carries its own evidence

_proposed_ - sources: `F-b4-05`.

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

### Worked example 2 (proposed): the failure shape, when a statement does not check out

_proposed_ - sources: `F-b4-07`.  Also carried in the body of `cap-provenance` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-provenance` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Read the subject digest and the statement reference off the result, and store both next to whatever you do with the output.**  
  _why:_ Proposed. The digest is what ties your copy of an output to the statement about it; a result kept without its digest cannot be matched to any evidence later, and the match is the whole question an auditor asks.  
  _proposed_ - `F-b4-05`
- **Fetch the envelope and keep it yourself, rather than keeping a pointer into our store.**  
  _why:_ The concern's contract is verification with a tool we did not write, and evidence you can only reach through us is evidence that ends when your access does. Keeping the bytes is the difference between citing a record and holding one.  
  _sourced_ - `F-b4-05` "verifiable with a tool we did not write"
- **Verify with your own tool and your own policy: name the signers you accept and the values you expect, then check the envelope.**  
  _why:_ cap-provenance states what an outside verifier does (X-cap-provenance-005), checking cryptographic signatures and matching expected values such as builder ID and source repository; for a caller the consequence is that this is the only check that answers the question you actually have, which is whether to trust us.  
  _sourced_ - `X-cap-provenance-005` "checking cryptographic signatures and matching expected values such as builder ID and source repository"
- **Handle exactly one failure, the 422 in worked example 2, and handle it by refusing the artifact rather than by retrying. Everything else that comes back is the ordinary answer or an ordinary typed failure.**  
  _why:_ Proposed. The failure shape, the media type and the closed registry belong to cap-errors, so a caller that already reads type and retryable needs no new branch here beyond recognising one more registered type; a statement that does not check out will not check out on a second attempt.  
  _proposed_ - `F-b4-07`
- **If the statement points at a public append-only log, keep the inclusion proof with the envelope and check the log yourself from time to time rather than only at the moment you receive it.**  
  _why:_ cap-provenance states this consequence for the capability (X-cross-structure-053); for a caller it means a log is tamper-evident but not tamper-proof, so a proof you never re-check is a guarantee nobody is exercising on your behalf.  
  _sourced_ - `X-cross-structure-053` "tamper-evident but not tamper-proof"
- **Proposed: if you want to see the starting state, use examples/end-to-end. Its results already carry a subject digest per output, and it emits no statement at all, which is what the definition of done below measures.**  
  _why:_ Proposed, and it is the shortest route from this page to something running: the reference runner needs no services, and the gap it shows is the honest one rather than a rehearsed success.  
  _proposed_ - -

## Other caller invariants

- Proposed: the caller's obligation is zero fields. There is no attest call to make, no key to hold, no flag to set and no way to ask for provenance or to decline it; cap-provenance fixes the contract and cap-provenance-implement wires attest into the emitter and the run seal.  
  _proposed_ - `F-b1-08`, `F-b4-05`
- Proposed: an answer from us about our own output is not evidence. The composable move is that the envelope leaves with you, so the check is done by your verifier against your policy; a verification endpoint of ours is a convenience for debugging and is never the thing an auditor is shown.  
  _proposed_ - `F-b4-05`
- Proposed: statements compose the way results do. A workflow, a loop or an agent that calls other steps on your behalf produces a statement per output and one over the sealed run, so a caller who kept the run's envelope can still reach every part of it without having watched the run happen.  
  _proposed_ - `T-t2-03`

## Caller practices

- Proposed: keep the envelope, not a screenshot of a green check. The envelope is the thing another party can re-check; a record that our verifier said yes is a claim about us again, which is the specific thing this capability exists to stop being the answer.  
  _proposed_ - `F-b4-05`
- Ask which level of guarantee the statement carries rather than treating every statement as equal: the build track has four levels representing increasing grades of security, and a statement produced by an unhardened path is still a real statement about a weaker process.  
  _sourced_ - `X-build-definition-of-done-007` "representing increasing grades of security"
- Proposed: pin the verifier you use and record its version alongside the envelope. A check that passed under one verifier and a later one that does not is a fact worth keeping, and without the version you cannot tell a relaxed check from a changed artifact.  
  _proposed_ - `F-part-c-10`
- Proposed: treat a missing statement as a defect to report, not as a case to handle. Provenance is applied by the platform, so an output arriving with a digest and no statement means the emitter was bypassed, and a caller that quietly tolerates it is the reason nobody notices.  
  _proposed_ - `F-b1-08`

## Open questions carried over

- **The reference runner lists provenance as delivered by a hash chain plus per-output digest, verified with `python3 run.py --verify-ledger`, which is our own reader over our own file.**  
  _deciding evidence:_ Measured on 2026-09-03: the corpus carries 32 subject digests and zero statements, so nothing an outside verifier could read is produced. agentic-stack already cites the chain property that command checks (F-a5-03), each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable; that is integrity for us, and the concern's contract is verification with a tool we did not write.  
  _default until then:_ Recorded as a disagreement with examples/end-to-end rather than resolved here. The change proposed: keep `--verify-ledger` as the integrity check it is, rename what the README calls provenance to integrity, and add a provenance row that stays red until the first signing adapter emits an envelope.  
  `F-b4-05`, `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable"
- **Which problem type does an unverifiable statement raise, given that the first-cut registry in docs/decomposition.md section 2.1.6 has no provenance row?**  
  _deciding evidence:_ Whether any existing registered type fits: the closest are document-invalid, which is about schema validation, and identity-untrusted, which is about a delegation chain. Neither is about a subject digest that no longer matches.  
  _default until then:_ Proposed: add one row, attestation-unverifiable at 422 and not retryable, as worked example 2 shows. cap-errors owns the registry, so the row lands there and this skill cites it; until it does, the type in that example is proposed and unregistered.  
  `F-b4-07`

