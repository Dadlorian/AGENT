# End-to-end consumption example

One way in, four entries, one workflow, one result. Dependency-free Python 3.11, no network by default.

## Start here

| Step | Command |
|---|---|
| 1. Run the gate | `bash examples/end-to-end/test.sh` |
| 2. Watch one entry | `python3 examples/end-to-end/run.py --entry examples/end-to-end/entries/human.json` |
| 3. Read the receipt | `cat examples/end-to-end/out/ledger.jsonl` |

## Files

| File | Lines | What it is |
|---|---|---|
| `schemas/entry.schema.json` | 84 | The one envelope all four entries use: kind, actor, intent, correlation, budget ceiling, idempotency key, payload |
| `schemas/agent-profile.schema.json` | 49 | An agent declared up front: name, good_at, not_for, model class, tools, input/output shapes, cost class, max concurrency |
| `schemas/workflow.schema.json` | 127 | Six operators, closed set: sequence, parallel, loop, approval, agent, judge |
| `agents.json` | 104 | Seven profiles across the four routing classes |
| `workflows/triage-and-fix.json` | 98 | One workflow using every operator once |
| `entries/human.json` | 22 | A person types a fault report |
| `entries/event.json` | 25 | An internal alert fires |
| `entries/schedule.json` | 26 | A recurrence rule fires |
| `entries/external.json` | 31 | Another agent submits a task |
| `run.py` | 397 | Validator, planner, dispatch adapters, judge, hash-chained ledger, result table |
| `test.sh` | 87 | The gate: 29 checks, all measured |
| `provenance.json` | 27 | Which TARGET, PASS and research ids this satisfies |
| `out/ledger.jsonl` | written | Append-only, hash-chained record of every step |

## The four entries

| Entry | Who acts | Command | What is different | What is identical |
|---|---|---|---|---|
| human | `user:corey` | `python3 run.py --entry entries/human.json` | Free text typed by a person; one-hop delegation chain | Envelope shape, workflow, cross-cutting concerns |
| event | `service:alerting` | `python3 run.py --entry entries/event.json` | Structured alert body; two-hop chain via token exchange | as above |
| schedule | `schedule:nightly-fault-sweep` | `python3 run.py --entry entries/schedule.json` | Carries a recurrence rule; acts on a user's behalf | as above |
| external | `agent:partner-sre-bot` | `python3 run.py --entry entries/external.json` | Three-hop chain, `parent_correlation_id`, `depth: 1` | as above |

## Other command lines

| Goal | Command |
|---|---|
| Verify the ledger chain | `python3 run.py --verify-ledger` |
| Trip the budget before anything runs | `python3 run.py --entry entries/human.json --budget-micros 50000` |
| Trip the budget mid-loop | `python3 run.py --entry entries/human.json --budget-micros 400000` |
| Reject at the approval step | `python3 run.py --entry entries/human.json --approval reject` |
| Dispatch for real | `GATEWAY_URL=... GATEWAY_KEY=... python3 run.py --entry entries/human.json --live` |

## What each step does

| # | Step | Operator | Profile | Class | Does |
|---|---|---|---|---|---|
| 1 | `triage` | agent | triage-router | `i-fast` | Names the failing component, fault family, repro command |
| 2 | `repro` | agent (parallel) | repro-extractor | `f-grunt` | Reduces the repro to one failing test, offline |
| 3 | `logs` | agent (parallel) | log-bulk-summarizer | `b-deep` | Counts occurrences in the retained window |
| 4 | `dedup` | agent (parallel) | dedup-checker | `f-smoke` | Matches against open incidents, cheaply |
| 5 | `fix#n` | agent (in loop) | code-fixer | `cli-` | Edits only the named files until the test passes |
| 6 | `fix-judge#n` | judge | — | — | Grades `fix#n` against a criterion the fixer never sees |
| 7 | `brief` | agent | risk-escalator | `i-escalate` | Writes the one-screen approval brief |
| 8 | `ship-approval` | approval | — | — | Parks; a human returns approve, edit or reject |
| 9 | `regression` | agent | regression-test-author | `cli-` | Writes the regression test |

## What comes back

| Surface | Content |
|---|---|
| Plan table (before anything runs) | Every step, its operator, its profile, its model class, its estimated micros; worst case, shortest finishing path, ceiling |
| Result table | Per step: cost in micros, budget left, outcome (`ok`, `pass`, `fail`, `approve`) |
| Closing line | Outcome, step count, spent versus ceiling, estimate, ledger head digest |
| `out/ledger.jsonl` | One record per step: seq, prev, hash, timestamp, run id, correlation id, actor, delegation depth, entry kind, idempotency key, step, operator, model class, cost, budget remaining, output digest |
| On failure | RFC 9457 problem details on stdout, exit code 2 |
| On replay | `REPLAY:` line, zero new records, exit code 0 |

## Failures you can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | The envelope fails schema validation |
| `urn:agentic:problem:budget-exhausted` | 402 | The plan floor exceeds the ceiling, or a step would cross what is left |
| `urn:agentic:problem:idempotency-conflict` | 409 | A completed key returns with a different body |
| `urn:agentic:problem:adapter-unavailable` | 503 | Live dispatch cannot reach the endpoint |

## Cross-cutting concerns, applied not requested

| Concern | Where it is applied | How you see it |
|---|---|---|
| Correlation | `Run.record`, on every ledger record and every live request header | `correlation_id` in every line of the ledger |
| Identity | Envelope actor and delegation chain, carried to every step | `actor` and `delegation_depth` on every record |
| Budget | Priced by `plan()`, checked before each step, decremented after | `budget_left` column; exit 2 with a 402 |
| Idempotency | Ledger lookup before the plan runs | `REPLAY:` line and unchanged record count |
| Provenance | Hash chain plus per-output digest | `python3 run.py --verify-ledger` |
| Typed errors | `Problem` class, closed registry | `application/problem+json` on stdout |
| Hidden criterion | `CRITERIA` in `run.py`; only the verdict travels back to the agent | Judge rows show `pass`/`fail`, never the rule |

## Adapters behind one dispatch interface

| Adapter | Default | Network | Notes |
|---|---|---|---|
| `DryRunAdapter` | yes | none | Deterministic stub; identical bytes every run, so the gate can assert on it |
| `OpenAICompatibleAdapter` | `--live` | POST `/v1/chat/completions` | `model` is the profile's model class, so the caller names a class, not a vendor |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `GATEWAY_URL` | yes | Base URL of the OpenAI-compatible model gateway (LiteLLM today, per PASS.md A1/B3) |
| `GATEWAY_KEY` | yes | Scoped virtual key, sent as `Authorization: Bearer` |
| `GATEWAY_TIMEOUT_S` | no | Per-request timeout in seconds, default 120 |

## Measured by `test.sh`

| Check | Expected |
|---|---|
| Four entries, dry run | exit 0, each reaches `completed` |
| Registry and workflow validate | 0 errors from the same validator |
| Ledger chain | verifies; a one-character edit is detected (exit 2) |
| Replay of a completed key | `REPLAY:`, exit 0, zero records appended |
| Ceiling below the plan floor | exit 2, `budget-exhausted`, nothing dispatched |
| Ceiling that runs dry mid-loop | exit 2, tripped at `fix#2` |
| Malformed envelope | exit 2, problem details naming the missing field, no ledger written |
| Criterion leakage | criterion text absent from all caller-visible output |
