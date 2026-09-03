# Containment harness

One contained unit, one agent turn, cancelled mid-turn. The stop reason and the
containment report come back through the capability interface; the containment
technology sits behind an adapter and is chosen by configuration.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/containment/test.sh` |
| 2. Watch one call | `ADAPTER=dryrun python3 harness/containment/call.py` |
| 3. Swap the technology | `ADAPTER=second python3 harness/containment/call.py` |
| 4. Prove the interface held | `python3 harness/containment/conformance.py --adapter dryrun --adapter second` |
| 5. Run against the host | `bash harness/containment/test.sh --live` |

## Files

| File | Lines | What it is |
|---|---|---|
| `interface.py` | 237 | The capability interface: the declaration, the containment report, the turn shapes, the closed problem registry, one abstract adapter class. No product name appears in it |
| `adapters/hostside.py` | 82 | The host side of the boundary: the per-unit directory the host creates and stats, and the broker that holds the real credential and decides every egress attempt |
| `adapters/dryrun.py` | 187 | Deterministic in-process adapter. Grants a machine, holds a process open, cancels mid-turn. Runs here with no network and no privileges |
| `adapters/live.py` | 272 | Today's component: Firecracker microVM cells started through systemd, goose driven over the Agent Client Protocol on stdio or a unix socket. Reached only through the env vars below |
| `adapters/second.py` | 191 | The second containment technology: capability grants instead of a machine, single-shot runtime, no cancellation. Faithful stub here; `SECOND_SHIM_CMD` execs a real shim |
| `binding.json` | 20 | Configuration. Which adapter, the default declaration, the turn's timings, the tuning both breakages edit |
| `call.py` | 183 | The minimal call. 17 lines of caller code below the `>>> CALLER CODE` marker, counted by `harness/caller_lines.py`; everything above it is the platform |
| `conformance.py` | 221 | The same cases against any adapter, plus the cross-adapter assertions only a swap can make |
| `test.sh` | 157 | The gate: 25 checks, dry run by default, `--live` for the host |
| `out/` | written | Conformance reports, per-unit jails, run logs |

## The minimal call

| # | Line a caller writes | What the platform did without being asked |
|---|---|---|
| 1 | `ad, name = adapter(cfg)` | Selected the containment technology from configuration; nothing downstream branches on it |
| 2 | `decl = IsolationDeclaration.from_dict(...)` | Refused any field that describes a machine rather than a resource declaration |
| 3 | `env = envelope(cfg, "human", ...)` | Stamped the correlation id, the run id, the actor and delegation chain, the budget ceiling and the idempotency key |
| 4 | `unit = ad.admit(decl, context(env))` | Resolved the profile or refused it; created the unit's own directory at mode 0700 under an identity with no host passwd entry |
| 5 | `session = ad.open_session(unit, offered)` | Negotiated streaming, permission callbacks and cancellation; every one defaults to absent |
| 6 | `Dispatch(...).start()` | Armed a monotonic ceiling timer outside the unit |
| 7 | `turn.cancel()` | Sent the cancel as acceptance, not a kill; the caller keeps taking frames |
| 8 | `result, unit_result = turn.finish()` | Enforced the grace window and the ceiling through the boundary's own destroy path, and destroyed the unit on every path |
| 9 | `report = ad.inspect_containment(unit)` | Read the jail mode, the owning identity, the egress counters and the marker from the host, never from the unit |

| Result field | dryrun | second |
|---|---|---|
| stop reason | `cancelled` | `cancel_timeout (by boundary)` |
| negotiated capabilities | streaming, callbacks, cancellation | none |
| containment marker read from the unit | `contained-by:simulated-machine-unit` | `contained-by:capability-granted-unit` |
| jail mode / owner in host passwd | `0700` / `False` | `0700` / `False` |
| egress attempts made / blocked | `3` / `3` | `3` / `3` |
| secrets seen inside the unit | `0` | `0` |
| output digest | equal across adapters | equal across adapters |

## Environment variables for live mode

| Variable | Required | What it names |
|---|---|---|
| `CELL_START_CMD` | yes | Command that starts one unit, e.g. `systemctl --user start firecracker-cell@{unit}.service`. `{unit}` is substituted; the profile's template arrives as `$CELL_TEMPLATE` |
| `CELL_STOP_CMD` | yes | Command that destroys the unit, e.g. `systemctl --user stop firecracker-cell@{unit}.service` |
| `CELL_JAIL_ROOT` | yes | Host directory holding per-unit jails; the containment report is stat'ed from here |
| `BROKER_EGRESS_COUNTERS` | yes | JSON file the host broker writes, keyed by unit id, with `made` and `blocked` counts |
| `ACP_STDIO_CMD` | one of two | Command speaking Agent Client Protocol JSON-RPC over stdio into the unit |
| `ACP_SOCKET` | one of two | Unix socket speaking the same protocol; `{unit}` is substituted |
| `CELL_CANCEL_FLOOR_S` | no | This adapter's observed cancel floor. Default 10; a shorter grace is refused |
| `CELL_TIMEOUT_S` | no | Ceiling on any host command. Default 120 |
| `SECOND_SHIM_CMD` | no | Runtime-spec shim for the second adapter. Unset, it runs as a faithful stub |
| `ADAPTER` | no | `dryrun`, `second` or `live`. Overrides `binding.json` |
| `BINDING` | no | Configuration file to read instead of `binding.json` |

## What each test proves

| # | Check | What it proves | Would pass if the property were absent? |
|---|---|---|---|
| 1 | Conformance against the dry-run adapter | Every operation the contract names is implemented and every case is answered | No |
| 2 | Conformance before, swap, conformance after | The interface held across two containment technologies, from one declaration, with no code edited between runs | No |
| 2 | Marker read back from the running unit | A different technology actually contained the unit, rather than the same one running twice with a new name in the binding | No |
| 2 | Execution models differ on at least one axis | The second adapter breaks a different assumption instead of being a different product of the same shape | No |
| 3 | The minimal call under each adapter | A caller writes the same lines either way and branches on neither | No |
| 3 | `cancel_timeout (by boundary)` under `second` | Cancellation is enforced by containment, not by the runtime's goodwill | No |
| 4 | Breakage A: `0.0.0.0/0` in the default declaration | The egress assertion can fail. Jail mode, digest, marker and identity still pass, so the run is green on everything except the property removed | No |
| 5 | Breakage B: cancel poll interval above the grace window | A runtime that claimed cancellation and missed it is told apart from one that never claimed it | No |
| 6 | Refusals are RFC 9457 problem details | An unknown profile, a machine-shaped field, an empty allowlist and an inline credential are refused before anything runs | No |
| 6 | Live mode with no env refuses | An unreachable technology answers `isolation-unavailable` rather than degrading to weaker containment | No |

## What would pin this interface, and how the boundary avoids it

Source: the blueprint's `firecracker-cell@.service` and `goose v1.46.0 over ACP` tool entries.

| Would pin it | How this harness avoids it | Where to look |
|---|---|---|
| A field only hardware virtualisation could honour: boot arguments, a block-device layout, a guest kernel | The declaration carries a profile name, an egress policy and a credential mode, and `from_dict` refuses every other field | `interface.py` `IsolationDeclaration`, conformance check "a machine-shaped field is refused" |
| Selecting the long-lived unit by naming a systemd template | Two unit shapes are two profiles behind one declaration; the template is resolved inside the adapter and never appears above it | `adapters/live.py` `PROFILES`, `adapters/second.py` `PROFILES` |
| An interface that requires a live session, a stream or a callback | Every interactive capability is negotiated at session open and defaults to false; the single-shot adapter negotiates none and the caller writes no branch for it | `interface.py` `SessionCapabilities`, `adapters/second.py` `open_session` |
| Trusting the unit's own account of its containment | Every field of the report is produced by the host: the directory is stat'ed, the broker counts and decides each egress attempt, the marker is read back from the unit | `adapters/hostside.py`, conformance check "containment asserted from outside the unit" |
| Assuming an injected trace context survives the unit boundary | The correlation id is set explicitly at admission and travels as an attribute, never as trace parentage | `call.py` `context()`, `adapters/live.py` `CELL_CORRELATION_ID` |
| A ceiling the unit enforces for itself | The ceiling timer and the cancel grace window both live outside the unit and end it through the boundary's destroy path | `call.py` `Dispatch`, conformance check "a ceiling shorter than the turn ends the unit through the boundary" |

## Swap procedure

| Step | Action |
|---|---|
| 1 | Run `python3 conformance.py --adapter <today> --report out/before.json` |
| 2 | Point `binding.json` (or `ADAPTER`) at the other adapter. No code edit |
| 3 | Run `python3 conformance.py --adapter <second> --report out/after.json` |
| 4 | Run both together and read `cross_adapter`: the marker must differ, the digest and exit status must not, and `differs_in_execution_model` must be non-empty |
