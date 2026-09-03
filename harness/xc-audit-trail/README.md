# xc-audit-trail harness

## Files

| file | what it is |
|---|---|
| `interface.py` | `TrailAdapter` ABC: `append`, `project`, `fetch_by_correlation`, `attribute`, `scan`; typed `Problem` failures |
| `adapters/dryrun.py` | in-memory hash-chained trail, seeded fixture, no disk, no network |
| `adapters/live.py` | projection over `kb/ledger.jsonl` via `tools/kb.py`, read-only |
| `adapters/second.py` | window-sealed log with a published head an outsider can check |
| `verify_external.py` | standalone verifier over the second store's published files; imports no adapter |
| `scan.py` | runs the integrity scan as its own process, given an identity and a `--scheduled` flag |
| `call.py` | the minimal call a caller writes |
| `conformance.py` | the cases every adapter must pass; `--product-scan`, `--caller-lines`, `--break wiring-fault` |
| `test.sh` | the gate: conformance, swap proof, breakage, `--live` |

## The minimal call

```
ADAPTER=dryrun python3 call.py
```
projects a run's records into a trail, fetches everything under one correlation id, and attributes one entry to its actor and delegation chain. `ADAPTER=second` and (with the env var below) `ADAPTER=live` run the same fourteen lines of caller code unchanged.

## Env vars for live

| var | meaning |
|---|---|
| `AUDIT_TRAIL_LEDGER_PATH` | path to the chained append-only file to project (e.g. `kb/ledger.jsonl`); unset refuses as `adapter-unavailable` rather than guessing a path |
| `TRAIL_CLOCK` | fixes the clock the dry-run/second fixtures and the live adapter's "now" use, for deterministic ages |
| `SECOND_STORE_DIR` | where the second adapter publishes its window heads and entries; defaults to `out/second` |
| `SECOND_UNREACHABLE=1` | makes the second store refuse a seal, rather than deferring it |
| `TRAIL_DRYRUN_FAIL=1` | makes the dry-run store's reads refuse as `adapter-unavailable` |

## What each test proves

| test | proves |
|---|---|
| conformance vs dryrun | project, fetch-by-correlation, attribute, an independent scheduled scan, and a tampered entry caught by the trail's own recompute |
| product scan | no product name outside `adapters/` |
| caller-lines | the minimal call is under 40 lines and names no adapter's storage |
| the dry-run failure path | an unreachable store is a typed `adapter-unavailable`, not a stack trace |
| swap proof | conformance passes on `second` too (one extra case: its own external verifier), the same four files' hash is unchanged before and after, and `execution_model`, `adapter`, and `external_checkable` differ across the pair |
| second store's own case | `verify_external.py`, importing no adapter, recomputes every window head from the entry hashes and confirms it, independent of the second store's own reader |
| the "found by both stores" case | tampering one entry mid-trail is caught by the trail's own chain recompute on **both** adapters, and, on the second store only, by the wholly separate published-head file `verify_external.py` reads |
| breakage (`--break wiring-fault`) | deleting the scan's schedule and calling it inline from the writer's own identity: `independent` and `scheduled` both go false, `scan.py` exits non-zero **naming the writer's identity**, while `chain_breaks` stays 0 and `entries_checked` stays 24 - the wiring broke, not the record |
| `--live` | the same conformance and the same caller code, run against this repository's own ledger |

## What would pin, and how the boundary avoids it

The blueprint tool entry is `kb/ledger.jsonl` via `tools/kb.py` - the chained append-only file this repository already writes and checks with its own reader (`tools/kb.py ledger-verify`). A caller that imported that reader directly would pin to one file format and to nobody but us being able to check it. `TrailAdapter` hides the file: callers get `AuditEntry` objects with an `actor`, a `delegation_chain`, a `correlation` pair and a `kind`, never a byte offset or a JSONL line. The second adapter is chosen on exactly the axis the pin would matter on - who can check the record without holding our credentials - by publishing sealed window heads to a second location that `verify_external.py` checks with no import of anything under `adapters/`.

## Honest gaps

- The definition of done in `xc-audit-trail-implement` names `entries_checked >= 100`, a `retention-floor-days 180`, and a scheduled scan tool that does not exist on this stack; this harness runs a 24-entry deterministic fixture spanning a synthetic 200-day window instead, and everything about a real 180-day retention floor, a real cron schedule, and a real credential boundary on the second store stays **claimed**, not measured, exactly as that skill's own `definition_of_done.expected_failure` says.
- `kb/ledger.jsonl` predates this harness: its records carry `agent`, not `actor`, and no correlation triple, so `live.py`'s `coverage_start` marks the earliest record it could attribute rather than claiming the whole file was always an audit trail.
- The live adapter is read-only; it does not append to the repository's own ledger, and `adapter.tamper()` (used by the "found by both stores" case) is only implemented on `dryrun` and `second`.
