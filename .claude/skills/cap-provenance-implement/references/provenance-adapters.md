# Provenance adapters: mapping, subsets and the swap runbook (long material)

Proposed. Open this only when you are building or swapping an adapter; the skill body is enough to
build either one without it.

## 1. Per-adapter mapping

| Contract call | Local signed envelope (adapter today, extended) | Keyless with a public log (second) |
|---|---|---|
| `attest` | Wrap the existing evidence record in a predicate, sign with a held key, append beside the record | Obtain a per-run signing identity, sign, publish, return the inclusion proof with the envelope |
| `verify` | Check the signature against the configured public key | Check the signature against the identity and the log entry |
| `resolve` | Index by subject digest over the local envelope file | Query the log by subject digest |
| `publish` | Copy the envelope to the configured attestation store | The publish is the log append, and is not optional for this adapter |

## 2. Declared conformance subsets

| Property | Local | Log |
|---|---|---|
| Signature over the envelope | yes | yes |
| Third-party verification without our store | yes, given the public key out of band | yes |
| Inclusion proof | **unsupported, declared** | yes |
| Signer authority expires | no, the key is held | yes |
| Emission works offline | yes | no |

A declared `unsupported` is honest. Reporting `0` for a property the adapter cannot provide is the
failure the pair exists to expose (see the skill's invariants).

## 3. Failure modes each adapter can and cannot detect

| Failure | Local | Log |
|---|---|---|
| Artifact modified after emission | detected: subject digest mismatch | detected |
| Statement modified after emission | detected: signature fails | detected |
| Statement deleted from our store | **not detected**: nothing else knows it existed | detected: the log entry remains |
| Signing key stolen and used later | not detected without key rotation | limited: the identity expired, and the log records when |
| Whole store replaced consistently | **not detected** | detected by an outside monitor of the log |

The two rows in bold are the reason the second adapter is not a different product of the same shape.

## 4. Swap runbook

1. Bring both adapters up behind the same `attest` call; select with one configuration key.
2. Run `tools/conformance/provenance_verify.py` against each, store unmounted, and keep both reports.
3. Assert the merged report shows `adapters_run == 2` and `selected_by == "configuration"`.
4. Record the local adapter's declared subset in the report rather than asserting the members it
   cannot provide.
5. Apply the definition-of-done breakage (rebuild from a modified input, do not regenerate) and keep
   the failing reports next to the passing ones. A breakage that fails neither adapter, or fails only
   one, has not tested what the pair is for.
6. Write both runs to the evidence store in the form `build-evidence-record` fixes, labelled
   `claimed` until they have actually been run.
