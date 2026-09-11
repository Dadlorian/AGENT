# 3-core-agent — Core Agent

Built for STATUS row 79, which is condition R7 of `python3 tools/ready_to_build.py`.

**This area is an instrument, not a deliverable.** It exists to test one claim that
`examples/reference/README.md` makes and nobody had checked: *"Write the example from the
profile."* It was built from exactly one card profile, `docs/reference/cards/3-3.json`, and every
question that profile could not answer is written down in
[`docs/reference/profile-sufficiency.md`](../../../docs/reference/profile-sufficiency.md). That
file is the finding. Read it first if you are deciding whether to build the other eight areas.

## What it covers, and what it does not

Nothing is demonstrated by implication. `cards.json` is the machine-readable version of this
table and `check_cards.py` proves it against `docs/reference/reference-model.json`.

| Address | Card | Here |
|---|---|---|
| 3.3 | Runtime / Sandbox | **demonstrated** — contract, three adapters, conformance, gate |
| 3.1 | Harness | gap — profile exists, unused |
| 3.2 | Model Interface | gap — profile exists, unused |
| 3.4 | Workspace | gap — profile exists, unused |
| 3.5 | Tool Interface | gap — profile exists, unused |

One card of five is deliberate. The experiment asks whether *a* profile is a sufficient spec; four
more of the same would have multiplied the cost of the answer without changing it. If the finding
holds up, the remaining four are ordinary work.

## Run it

```
ADAPTER=dryrun python3 call.py     the cold path
ADAPTER=second python3 call.py     the same caller, a different execution model
python3 conformance.py dryrun      does this adapter honour the contract
bash test.sh                       the visible gate: passed 19, failed 0
```

`call.py` is 37 lines and names no VMM, no runtime binary, no network mode and no resource limit.
That is not minimalism for its own sake: the caller does not configure the boundary, because this
platform decides it for them — REF-3-02 lists isolation among the things smart-defaulted so a
caller need not *"decide routing, isolation, retries, model tier, budget ceiling, deadline,
telemetry, provenance, the ledger"*. `test.sh` asserts the absence.

## The contract

`interface.py` takes its shape from the lifecycle the standard describes rather than an invented
one — *"At a high-level an OCI implementation would download an OCI Image then unpack that image
into an OCI Runtime filesystem bundle. At this point the OCI Runtime Bundle would be run by an OCI
Runtime."* (`X-refmodel-3-3-environment-011`). Hence `unpack` → `run` → `inspect` → `stop`.

`inspect` returns a status, and the trace of every status the handle has held. Without the
trace, half the status domain is decoration — a sandbox that was created first and one that went
straight to `running` read identically — and the two execution models become indistinguishable.
The status itself is there because the standard makes one mandatory — *"status (string, REQUIRED)
is the runtime state of the container."* (`X-maturity-c-010`). Its four legal values are
`creating`, `created`, `running`, `stopped`, and they are marked **proposed** rather than sourced:
they are verbatim in that same record and carry no verification stamp, because
`stamp_verification.py` stamps the quotes *card profiles* cite and no card cites the enumeration.
Finding 2 in the sufficiency note.

The whole card exists because the target architecture requires it and names the standard it is
checked against: *"a unit of work runs isolated, per the OCI Runtime Spec"* (`F-b3-18`).

## The adapters

| Adapter | Execution model | State |
|---|---|---|
| `dryrun` | cold: a bundle is unpacked per run and discarded with it | runs, deterministic, no infrastructure |
| `second` | warm pool: a template prepared once, claimed per unit | runs, deterministic, no infrastructure |
| `live` | Firecracker microVM (`F-a3-01`) | **claimed, never measured** — every method raises |

The pair is the point. `dryrun` and `second` are not two implementations of one idea; they are
different execution models behind identical signatures, so `call.py` does not change by a
character. The difference is not a label: a unit put through the cold adapter passes through
`creating`, and a unit claimed from a ready pool never does, because nothing was created for it.
`Inspection.trace` carries that, and the gate asserts both halves. The warm-pool model is not
invented here — *"The SandboxTemplate describes the pod the warm pool keeps ready"*
(`X-refmodel-3-3-environment-006`), a live project that already ships the split, and one that
3-3.json records as absent from this repo's own `cap-isolation`.

`live` refuses rather than returning a plausible `stopped`, because no harness in this repo has
run a live adapter against a real host from a session (STATUS row 37). A stub would make a claimed
path indistinguishable from a measured one. The refusal is this area's design choice — **proposed**,
not something the card states.

## What the gate actually checks

`test.sh` is the visible check, the one its author can see and tune. It asserts the caller stays
minimal and names no mechanism; that both runnable adapters conform, that every state in a lifecycle is one the standard
defines and arrives in order;
that all three adapters are callable identically; that the swap changes behaviour rather than a
label; that `live` refuses; and that every claim in `cards.json` is sourced-with-evidence or says
`proposed`, verified by `tools/prose_gate.py --corpus`.

It carries a deliberate breakage two ways. `adapters/_broken_on_purpose.py` is kept in the tree
and returns `ready` — a status no OCI runtime defines — and `test.sh` asserts conformance rejects
it *and names the offending value*, so the check cannot quietly stop checking. Separately, the gate
was run red before it was trusted green: with `dryrun` patched to end its lifecycle at `ready`,
`passed 17, failed 2`; restored, `passed 19, failed 0`. Both runs are in `provenance.json`.

**The hidden check is not written by this area's author** and is not in this directory —
`docs/night/hidden/3-core-agent.sh`, `hidden passed 10, failed 0`. A gate the author can tune is
not the same evidence as one they cannot, and this one earned its keep on the first run: it
reported `9, failed 1` against an earlier cut of this interface, because `unpack` took no
`profile` and the caller's one configurable word could therefore never select a bundle.
`Unit.profile` existed and was structurally dead. None of the eighteen checks in `test.sh` saw
it. The interface was changed, not the assertion.

## What this area does not prove

- **Nothing here is isolated.** Both runnable adapters are dry-run; `Inspection.isolation` is a
  string an adapter asserts about itself, never a measurement. The one adapter that would contain
  anything is the one that refuses to run.
- **Four of five cards in this area are gaps**, listed above with their addresses.
- **The example's own citations are outside the anti-fabrication chain.** `cards.json` quotes are
  checked verbatim against their records by `prose_gate.py`, but they are not *stamped* against a
  fetched page the way a card profile's are, because `stamp_verification.py` only collects quotes
  from `docs/reference/cards/`. Finding 2.
