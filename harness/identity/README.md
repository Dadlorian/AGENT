# Identity harness — an actor, and the chain that produced the right to act

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/identity/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/identity/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/identity/call.py` |
| 4. Prove the interface held | `python3 harness/identity/conformance.py --adapter dryrun --adapter second` |
| 5. See the breakage fail | `IDENTITY_BREAK=forward-token python3 harness/identity/conformance.py --adapter dryrun` |
| 6. Ask the host | `bash harness/identity/test.sh --live` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 456 | The capability interface: `Credential`, `Hop`, `AttestRequest`, `DelegationRequest`, `Problem`, and `IdentityAdapter` with verify, attest, delegate. All three are concrete template methods, so no adapter can decline scope narrowing, lifetime shortening, acyclicity, the single audience or the expiry check. No product name |
| `trust.json` | 29 | Data: the scope vocabulary, what counts as a root, the trust material each binding holds, and the vectors that test the two pure functions. No code branches on it |
| `adapters/dryrun.py` | 118 | The first adapter: an exchange-issuing provider in process. A client presents a credential it already holds; every verification is a call back to the authority. Declares `attest_from_platform_facts` unsupported |
| `adapters/live.py` | 173 | Today's component: none. PASS.md B3 records the adapter for Identity as absent, so every operation returns a typed refusal naming the absence until `IDENTITY_ISSUER_URL` or `WORKLOAD_API_SOCKET` is set; with them set it POSTs the RFC 8693 token-exchange grant. Product names may live here |
| `adapters/second.py` | 126 | The second adapter: attested workload identity. Issues only against platform facts it observed or a vouching attested party, and verifies locally against a trust bundle with no authority call. Declares `attest_from_presented_credential` unsupported |
| `call.py` | 137 | The minimal call. 20 lines below the `>>> CALLER CODE` marker; everything above it is the platform stamping the envelope and presenting what arrived at the door |
| `conformance.py` | 399 | The 16 cases every adapter passes, the 50-action delegation-chain corpus, and the product-name scan over code |
| `test.sh` | 174 | The gate: 46 checks in dry run, the swap proof, the pair run, and one deliberate breakage |
| `provenance.json` | — | Owner skill, co-skills, kb and research ids, what is measured and what is claimed |
| `plan-entry.json` | — | This harness's row, in the shape of the entries in `harness/plan.json`, for the orchestrator to merge |

## The minimal call

| Line of the caller's code | What it does | What the platform did without being asked |
|---|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters | Nothing downstream branches on which answered |
| `ask = envelope(adapter)` | One entry envelope | Stamped the correlation id, the run id, the budget ceiling, the idempotency key and the actor; presented what arrived at the door |
| `principal = adapter.verify(...)` | Turns what arrived into an actor | Refused an expired credential, a chain with a cycle, and a chain rooted in a name the caller supplied for itself |
| `intake = adapter.attest(unit(ask, "intake_unit"))` | One unit of work gets an identity | Issued short-lived, with no long-lived secret planted anywhere |
| `first = adapter.delegate(hop(ask, "first_hop", principal, intake))` | Hop 1: the service acts for the person | Checked that the scope narrows and the expiry does not extend, before anything was minted |
| `worker = adapter.attest(unit(ask, "worker_unit", vouched_by=intake))` | The agent gets an identity | Took the vouching path for a unit the platform cannot observe in place |
| `token = adapter.delegate(hop(ask, "second_hop", first, worker))` | Hop 2: the agent acts, for one downstream call | Prepended the acting party, kept the chain acyclic, and wrote one hop record per hop |
| `adapter.delegate(hop(ask, "widening_hop", token, worker))` | The hop that asks for more | Refused it: 403 `policy-denied`, `rule_id` `scope-must-narrow`, nothing issued |

| What comes back | Value in dry run, identical on both adapters |
|---|---|
| chain on the issued credential | `agent:worker-7` ← `service:intake` ← `user:corey`, current actor first |
| how each hop was obtained | `token_exchange`, `token_exchange`, `direct` (the root) |
| scope | `read:incident call:model write:ledger` → `read:incident call:model` → `call:model` |
| seconds left | 3600 → 1800 → 1200 → 900 → 300 |
| the refused hop | `urn:agentic:problem:policy-denied` 403, `scope-must-narrow`, `enforcement_point` `platform-pre-issue` |
| what differs across the swap | authority calls: 3 on the first adapter, 0 on the second |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `second` or `live` |
| `PRINCIPAL` | `user:corey` | Who the work is done for |
| `ENTRY_KIND` | `human` | Which of the four entries is acting |
| `CEILING_MICROS` | `200000` | The ceiling the platform stamps on the envelope |
| `WIDEN_SCOPE` | `deploy:prod` | The scope the last hop tries to add, to see the refusal |
| `IDENTITY_CLOCK` | `2026-09-03T09:12:00Z` | The fixed clock that keeps a dry run byte-stable |
| `MIN_ACTIONS` | `50` | Actions in the delegation-chain corpus |
| `DRYRUN_FAIL` | unset | `1` makes the issuing authority unreachable, to exercise the failure path |
| `IDENTITY_BREAK` | unset | `forward-token` injects the deliberate breakage |

## Env vars for live mode

There is nothing to reach today: PASS.md B3 records the adapter for Identity as
*absent* and PASS.md A6 records "No identity field anywhere in the system".
`adapters/live.py` says exactly that, with a typed refusal, until one of these is
set. Nothing in this table has ever been exercised from this environment.

| Variable | Required | Meaning |
|---|---|---|
| `IDENTITY_ISSUER_URL` | for the exchange form | Token endpoint of an OIDC provider serving the RFC 8693 token-exchange grant (SPIFFE/SPIRE or any OIDC provider are the swap candidates PASS.md B3 names) |
| `IDENTITY_ISSUER_TOKEN` | with the above | The platform's own actor credential, sent as `Authorization: Bearer` |
| `IDENTITY_INTROSPECT_URL` | for verify | Where a presented credential is checked |
| `IDENTITY_PRESENTED_CREDENTIAL` | for a live run | The credential the operator presents; this adapter mints no fixtures |
| `WORKLOAD_API_SOCKET` | for the attestation form | A SPIFFE Workload API socket. `adapters/second.py` probes it and returns a typed refusal rather than inventing an SVID fetch protocol it has never spoken |
| `IDENTITY_TIMEOUT_S` | no | Per-request timeout, default 30 |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | The minimal call exits 0 with three hops and a rooted chain | A unit of work obtains an identity, exchanges it for one downstream call, and the chain travels with the call |
| 1 | The caller writes 20 lines, under 40, and names no adapter storage | The stamps, the narrowing, the acyclicity and the hop records are the platform's work. Counted by `harness/caller_lines.py`, the one method the harnesses share, called as a module because this harness is not yet in that file's own list |
| 1b | `DRYRUN_FAIL=1` exits 2 with `adapter-unavailable` | The failure path is exercised, not only the happy one |
| 1b | `ADAPTER=live` exits 2 naming the absence | The live adapter says nothing runs rather than implying something answered |
| 2 | Conformance, 16/16, corpus of 50 actions | Attestation, delegation, verification, the four refusals, the leak scan and P13's four counters all hold with no network |
| 3 | Conformance before (`dryrun`) and after (`second`), 16/16 each | The interface held across a swap of the root of trust |
| 3 | `sha256` of `interface.py`, `call.py`, `conformance.py`, `trust.json` identical across both runs | The swap was configuration, not a code edit |
| 3 | 6 axes differ, 10 contract facts identical | The second adapter breaks different assumptions; what the caller sees does not move |
| 3 | Authority calls 3 vs 0 for the same caller code | The swap really happened; the caller cannot tell |
| 3b | One run over both bindings: `adapters_run == 2`, `selected_by == configuration`, both `unsupported` non-empty | The definition of done's merged-report shape, and two honestly declared conformance subsets |
| 4 | `product_hits=0` over the code | No product name outside `adapters/` |
| 5 | `IDENTITY_BREAK=forward-token` makes the first adapter exit 1 with `short_chains == 1` and `executing_unit_mismatch == 1`, and leaves the second at 0 | The green corpus run can fail, and the breakage singles out one binding: a document that names the unit it attested cannot be forwarded unchanged |
| 5 | The suite passes again once the hop is restored | The breakage was the defect, not the run |
| 6 | `--live` | Skipped with the reason. Nothing live has been measured here, because there is nothing live |

## What the conformance run measures

| Case | What is asserted |
|---|---|
| verify | An actor is what `verify` returned; a caller-built actor object is 422 and nothing is issued |
| attest | The credential names the unit, is short-lived, and its root hop is not self-asserted |
| declared subset | Each binding issues for one attestation form and declares the other in `unsupported`, rather than answering it with something weaker |
| vouched issuance | The path for a unit the platform cannot observe in place is either served or declared |
| chain | Three hops, current actor first, root last, middle hop `token_exchange` |
| narrowing | No hop widens scope and no hop outlives the credential it came from |
| widening / lifetime / cycle | Three typed 403 refusals with `rule_id`, each with nothing issued |
| expiry / unrooted | Two typed 401 refusals, not retryable |
| leak scan | No credential material, no trust material, no product name and no extra field in what the caller can read |
| authorisation | `authorise` reads the current actor and the top-level scope; the root's wider scope is not consulted |
| pure functions | 5 scope vectors and 4 chain vectors, with no adapter touched |
| hop records | One record per hop, the shape `xc-identity-delegation-implement` names, `enforcement_point` read off the answer |
| corpus (P13) | 50 actions: `missing_subject`, `short_chains`, `cyclic`, `executing_unit_mismatch` all zero |

## The two adapters behind one interface

| Axis | `adapters/dryrun.py` and `adapters/live.py` (the exchange form) | `adapters/second.py` (attested workload identity) |
|---|---|---|
| How a root credential comes to exist | the client presents one it already holds | the platform observes where the unit runs and issues |
| Where a presented credential is checked | a call to the authority, every time | locally, against distributed trust material |
| Authority calls in one conformance run | 153 | 0 |
| What is behind a handle | a bearer token with nested act claims | a signed document carrying the chain in its claims |
| The form it declares it cannot serve | `attest_from_platform_facts` | `attest_from_presented_credential` |
| Whether a hop can forward an incoming credential | yes, which is why the breakage lands here | no: a document names the unit it attested |
| Swap procedure | `ADAPTER=second`; no code edit, same fixtures, compare the two reports |

The X.509 form of an identity document names one workload and cannot express an
on-behalf-of chain at all; `cap-identity-implement` records the document-with-claims
form as the open question on that limit. This second adapter is that form, so it
serves `delegate` and declares its subset elsewhere. An X.509 binding would declare
`delegate` instead, and the report's `unsupported` list is where that would show.

## Failures a caller can get

| `type` | Status | Retryable | Raised when |
|---|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | no | A field is missing, a subject or audience is malformed, a scope token is outside the vocabulary, or an actor was built by the caller instead of returned by verify |
| `urn:agentic:problem:identity-untrusted` | 401 | no | A credential expired, nothing verifies it, or the chain is cyclic or rooted in a self-asserted name |
| `urn:agentic:problem:policy-denied` | 403 | no | A hop widens scope, extends the lifetime, repeats an actor, or acts outside the scope it holds. Carries `rule_id` |
| `urn:agentic:problem:adapter-unavailable` | 503 | varies | The issuing authority is unreachable (retryable), or the binding declares it does not serve this form (not retryable, naming the operation) |

Every type is a row of the closed registry in `docs/decomposition.md` 2.1.6.
Nothing new was invented: a declared conformance subset is `adapter-unavailable`
with `retryable` false, which that section allows explicitly.

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| The chain being one provider's token, so the issuer cannot change without changing what a hop is (blueprint state type: identity and delegation chain) | A hop is `{actor, obtained_via}` and a credential is a handle. Both adapters produce the identical three-hop chain; only `authority_calls` and the marker move |
| The identity root changing from an attested workload credential to a plain provider (blueprint impact row) | That is the swap this harness executes. `trust.json` says what counts as a root; the conformance run asserts the same 16 cases on both roots |
| A caller learning which binding answered and branching on it | The credential carries seven fields and no issuer. The enforcement point is read off the answer into the report and the hop records, never into anything a caller can route on |
| Prior hops leaking into an authorisation decision | `authorise` reads the current actor and the top-level scope only; the case proves that a wider scope at the root does not authorise the action |
| A credential or trust material reaching a log, a document or a failure body | Material never leaves the adapter: the leak-scan case asserts it is absent from every caller-visible view |
| An adapter that cannot express a chain answering with a one-hop credential anyway | `unsupported` is declared per binding and the pair run asserts both lists are non-empty; the corpus counts a chain shorter than the hops that occurred |
| A chain reconstructed from logs after the fact | Hops are recorded as they are made, one appended record per hop, with the unit the platform asked for beside the actor that came back |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the corpus, the swap proof and the breakage | Measured by `test.sh`: 46 checks, 0 failures |
| Live mode | Absent, not merely unmeasured: no identity component runs on this host |
| The token-exchange request shape in `adapters/live.py` | Claimed. The grant type and the `subject_token`/`actor_token` pair are sourced; the response field names and whether act claims can be read back are unverified |
| The SVID fetch protocol behind `WORKLOAD_API_SOCKET` | Not implemented. The adapter probes and refuses rather than inventing a wire protocol |
| The standards' versions | Unverified. Every record on file for RFC 8693 and for workload identity is a search result, not a fetched specification |
| Chain order, current actor first | This repo's convention, matching the entry envelope and `cap-identity`'s shape. Whether the standard's act-claim nesting fixes that order is an open question recorded in `cap-identity` |
