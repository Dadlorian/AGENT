# Identity adapters: mapping, subsets and the swap runbook

Open this when you need the per-adapter operation mapping, what each adapter cannot do, or the
step-by-step swap. The skill body is enough to build either adapter without it.

Everything here is **proposed** unless a kb id is given; ids resolve with
`python3 tools/kb.py show <id>`. PASS.md records the capability, its two standards and an absent
adapter (`F-b3-14`, `F-a6-05`), not these mappings.

## 1. Operation mapping

| Operation (cap-identity) | Adapter A — exchange-issuing provider | Adapter B — attested workload identity |
|---|---|---|
| `attest` | Client credentials the unit already holds, or federation from a platform token | Native: the agent observes node, account and image and issues a short-lived SVID (`X-cap-identity-007`) |
| `delegate` | Native: the token-exchange grant, `actor_token` required, `act` extended by one hop (`X-cap-identity-002`, `X-cross-structure-036`) | Declared **unsupported**: an SVID names one workload, not an on-behalf-of chain (`X-cross-structure-034`) |
| `verify` | Introspect or validate the token against the issuer's keys | Validate the presented SVID against the trust bundle, locally (`X-cap-identity-008`) |
| Issuance for a unit the platform cannot observe | A secret must be planted before the unit can ask for anything | Delegated issuance by an already-attested party (`X-cross-structure-035`) |

## 2. The axis the pair differs on

Adapter A puts a request to a central authority on every hop and hands out bearer tokens: whoever
holds the token is the actor. Adapter B attests once from platform facts and then verifies
peer-to-peer with no authority call per action, binding identity to the transport rather than to a
bearer string (`X-cap-identity-006`).

That difference is the point of the pair. If the interface can only be served by something that
answers a synchronous issuance call per hop, the interface has been shaped around adapter A.

## 3. Failure modes each adapter can and cannot detect

| Failure | A detects | B detects |
|---|---|---|
| Stolen credential replayed by another unit | No (bearer) | Yes, if bound to the transport |
| Chain truncated at a hop | Yes: the exchange did not happen, so the `act` claim did not grow | No: it never had a chain to truncate |
| Issuer unreachable | Every hop fails | Verification continues from the distributed trust material until credentials expire |
| Unit running somewhere it should not be | No: it authenticates the credential, not the location | Yes: attestation is against observed platform facts |

## 4. Swap runbook

1. Make the actor object required on the entry envelope and the dispatch request. Run the P13
   corpus assertion; expect `missing_subject` to fall to zero and `short_chains` to stay high.
2. Stand adapter A behind `attest`, `delegate` and `verify`. Wire verification at entry and the
   exchange at each dispatch hop. Re-run; expect `short_chains == 0`.
3. Stand adapter B behind the same three calls with `delegate` in its `unsupported` list.
4. Select the adapter by configuration only — no code edit, no redeploy of anything but the
   configuration — and record `selected_by` in the report at runtime rather than reading it back
   from the file that set it (`F-a7-04`, stated by agentic-stack).
5. Run the identical corpus assertion under each. Require `adapters_run == 2` in the merged report,
   and require adapter B's `unsupported` list to be present rather than empty.
6. Apply the breakage in the skill's definition of done to adapter A only, and check that adapter
   B's run still passes. A suite that fails both, or neither, has not tested the swap.

## 5. What does not change when the adapter changes

The `ActorIdentity` shape in cap-identity, the requiredness of the field, the two enforcement
points, the `identity-untrusted` problem type, and the P13 assertions. If a swap needs any of
those to change, the boundary was drawn in the wrong place (`F-meta-04`, stated by agentic-stack).
