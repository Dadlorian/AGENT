# Agentic Platform — Current State and Target Architecture

**Two parts, deliberately separate.**

**Part A** is an inventory. What runs today, by name and version, verified against the running host on 2026-09-03. No interpretation.

**Part B** is a target architecture for a greenfield build. No code carries over. Our current components appear only as *today's adapter* for a capability — never as the architecture itself.

**The rule that separates them:** Part A names products. Part B names capabilities and the standard that governs each. If Part B cannot swap an implementation without touching the core, the boundary is drawn wrong.

---

# PART A — Current state

## A1. Containerised services

Verified with `docker ps`. All bound to loopback except where noted.

| Service | Image | Port | Purpose |
|---|---|---|---|
| `gateway-litellm-1` | `ghcr.io/berriai/litellm-database:v1.97.0` | `127.0.0.1:4000` | Model gateway — one OpenAI-compatible API over every provider |
| `gateway-cli-bridge-1` | `agentic-stack/cli-bridge:0.2.0` | `127.0.0.1:8081` | Exposes coding CLIs as chat-completions endpoints |
| `gateway-db-1` | `postgres:16` | internal | Gateway config, virtual keys, spend ledger |
| `observe-langfuse-web-1` | `langfuse/langfuse:4` | `:3000` | Trace UI and ingestion API |
| `observe-langfuse-worker-1` | `langfuse/langfuse-worker:4` | `127.0.0.1:3030` | Async trace processing |
| `observe-clickhouse-1` | `clickhouse/clickhouse-server:25.12` | `127.0.0.1:8123`, `:9000` | Trace storage |
| `observe-postgres-1` | `postgres:17` | `127.0.0.1:5432` | Langfuse metadata |
| `observe-redis-1` | `redis:7` | `127.0.0.1:6379` | Queue and cache |
| `observe-minio-1` | `cgr.dev/chainguard/minio` | `127.0.0.1:9090/9091` | Blob storage for trace payloads |

## A2. Host services

| Unit | Type | Bind | Purpose |
|---|---|---|---|
| `approve.service` | systemd, enabled, running | `100.125.65.101:8088` (Tailscale) | Approve / reject / return a parked workflow from a phone |
| `firecracker-cell@.service` | systemd template, static | — | One microVM per agent, startable without sudo via polkit |
| `firecracker-cell-long@.service` | systemd template, static | — | Long-lived variant, larger runtime ceiling |

## A3. Sandbox internals

| Element | Value |
|---|---|
| Isolation | Firecracker microVM — hardware virtualisation, not a container |
| Agent runtime | goose `v1.46.0` |
| Control protocol | Agent Client Protocol (ACP), JSON-RPC over stdio |
| Guest network | **None.** Egress is a flag, default off |
| Guest credential | **Dummy key.** No real secret inside the VM |
| Jail | `0700`, owned by a per-VM uid with no passwd entry — verified live |
| Model egress | vsock → host broker, which holds the real key and picks the endpoint |
| Field filtering | Model and destination overrides dropped by name at the broker |
| Cancellation | `session/cancel` mid-tool-call ends the turn in ~8s against a 45s operation, zero trailing frames |

## A4. Model routing — 25 groups

Callers request a class, never a vendor. Prefix carries the contract.

| Prefix | Contract | Count | Members |
|---|---|---|---|
| `f-` | Free, local GPU | 6 | `f-grunt`, `f-3090-q14`, `f-3090-q30`, `f-5090-q30`, `f-runpod-dsv4`, `f-smoke` |
| `i-` | Interactive, metered | 9 | `i-default`, `i-fast`, `i-escalate`, `i-google-gemini`, `i-google-gemini-flash-lite`, `i-openai-gpt`, `i-claude-haiku`, `i-claude-sonnet`, `i-claude-opus`, `i-claude-fable` |
| `b-` | Asynchronous batch | 5 | `b-google-gemini` (default), `b-openai-gpt`, `b-deep`, `b-claude-sonnet`, `b-claude-opus` |
| `cli-` | Coding CLI as a model | 4 | `claude-code-cli`, `cli-cursor-api`, `cli-cursor-auto`, `cli-cursor-only` |

Local inference: SGLang serving Qwen3-Coder-30B on an RTX 3090 Ti, plus additional cards.

Each group carries a scoped LiteLLM virtual key with a hard budget cap, verified to terminate spend rather than merely record it.

Batch runs through Gemini's native `:batchGenerateContent` via LiteLLM passthrough — not the OpenAI-shaped `/v1/batches` route, which branches only on `openai`/`azure`/`vertex_ai` and refuses Gemini. No GCS bucket, no Vertex project, no service account. Context caching stacks on top at batch pricing.

## A5. Provisioning and data

| Concern | Implementation |
|---|---|
| Configuration management | Ansible — 9 roles: `gateway`, `observe`, `hitl`, `batch`, `fleet`, `policy`, `git_events`, `approve`, `cells` |
| Deployment phases | 8, each with automated verification, all currently green |
| Task store | JSONL, hash-chained — each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable |
| Evidence store | Append-only JSONL. Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty. ~2,445 records across 308 runs |
| Policy | Rego / Open Policy Agent |
| Private network | Tailscale |

## A6. Defined but not running

Stated because an inventory that omits this is not an inventory.

| Element | Status |
|---|---|
| **Temporal** | Data directory present; server not listening on `7233`/`8233`. Durable workflow orchestration and human-in-the-loop signals are designed around it and it is currently down |
| MCP endpoint | Live and authenticated, **zero tools registered** |
| Policy in the gate path | Conformance checks exist; not wired into the enforcement path |
| Identity | No identity field anywhere in the system |
| Typed errors | Absent |

## A7. Three measured findings

Each invalidates a design that looks correct on paper.

**1. W3C trace context does not survive the agent boundary.** We inject `TRACEPARENT`; goose ignores it and mints its own root trace. A depth-3 task tree produces three unrelated root traces. Correlation must ride on an explicit resource attribute set at dispatch.

**2. A deterministic gate can be structurally green and mean nothing.** Our 9-stage pipeline recently ran with every behavioural stage skipped — static analysis, tests, type checking, security scanning, coverage — because the generated work contained nothing those tools apply to. Only diff, syntax and format ran. Those establish well-formedness, not correctness.

**3. Configuration written in the documented place was silently discarded.** A `LiteLLM_Config` row in Postgres overlays and replaces `router_settings` on every gateway load. Values written to YAML validated, reviewed correctly, and had no runtime effect.

---

# PART B — Target architecture

Greenfield. No code carries over. Everything in Part A is available as substrate, and nothing in Part A is the architecture.

## B1. Design rules

These are the rules that produce flexibility. Everything downstream is a consequence.

1. **Every external dependency sits behind a capability interface.** The core imports interfaces, never implementations.
2. **Each interface names the standard that governs it.** Where a standard exists, adopt it whole rather than modelling our own shape.
3. **Swappability is a tested property, not an intention.** Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing.
4. **A caller needs no client library we wrote.** If integration requires our SDK, a boundary is bespoke where a standard existed.
5. **Cost is knowable before commitment.** Planning is a pure function and completes before execution begins.
6. **The grader is never visible to the graded.** An agent sees its outcome, never the criterion it is judged against.
7. **Cross-cutting guarantees are not optional.** Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller.

## B2. The core — small, and ours

Five components. Zero outward dependencies. Each earns its place by what breaks without it.

| Component | Is | Remove it and… |
|---|---|---|
| **Document** | data — declared intent, definition of done, steps | nothing is declarable |
| **Planner** | pure function `document → plan + cost` | nothing is pricable before it is spent |
| **Graph** | typed nodes, typed edges (existence / interface / implementation) | nothing composes |
| **Judge** | pure function `(result, criterion) → verdict` | "done" becomes an opinion |
| **Ledger** | append-only across runs; the deduplication authority | nothing survives the run |

This is the entire owned surface. Everything else is an adapter.

## B3. Capability interfaces

**The middle column is the contract. The right two columns prove it is swappable.**

| Capability | Standard | Adapter today | Swap candidates |
|---|---|---|---|
| **Isolation** | OCI Runtime Spec | Firecracker microVM | gVisor · Kata Containers · Cloud Hypervisor · hosted sandbox services |
| **Model access** | OpenAI-compatible completions | LiteLLM | OpenRouter · direct provider SDKs · vLLM/SGLang native |
| **Durable execution** | — *(no standard; see B5)* | Temporal | Restate · DBOS · Inngest · a queue plus a state machine |
| **Agent runtime** | Agent Client Protocol | goose | Claude Code · Cursor · any ACP-speaking agent |
| **Tool access** | Model Context Protocol | MCP endpoint | any MCP server |
| **Capability packaging** | Agent Skills spec | skill files | any spec-conformant registry |
| **Work intake** | A2A messaging · CloudEvents | CLI, git event, HTTP, schedule | any conformant producer |
| **Document validation** | JSON Schema 2020-12 | in place | any 2020-12 validator |
| **Telemetry** | OTLP · GenAI semantic conventions | Langfuse + OpenTelemetry | Phoenix · Braintrust · any OTLP collector |
| **Policy** | Rego / OPA | OPA | Cedar · any policy engine with a decision API |
| **Provenance** | in-toto · SLSA · DSSE | JSONL evidence records | Sigstore · any attestation store |
| **Errors** | RFC 9457 problem details | *absent* | — adopt the RFC directly |
| **Identity** | OAuth 2.0 Token Exchange · workload identity | *absent* | SPIFFE/SPIRE · any OIDC provider |
| **Scheduling** | RFC 5545 recurrence rules | Temporal schedules | cron · any RFC 5545 parser |
| **Idempotency** | idempotency-key convention | key on the wire, no lease | any keyed lease store |
| **State persistence** | — *(no standard; see B5)* | JSONL + hash chain | object store · relational · event log |

**Read the Isolation row as the template for the whole table.** Firecracker is excellent and stays. But the architecture says *"a unit of work runs isolated, per the OCI Runtime Spec"* — and satisfies that with Firecracker today. When a workload needs faster cold start, or needs to run somewhere we do not own hardware, the adapter changes and the core does not.

## B4. Cross-cutting concerns — applied, not requested

These are the difference between a working system and a production one. The platform applies each; a caller cannot decline them.

| Concern | Contract |
|---|---|
| **Budget** | Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform |
| **Identity** | Every action names an actor, including delegated agent actors. Delegation chains are explicit |
| **Policy** | Refusal is deterministic and happens before execution, not after spend |
| **Provenance** | Every artifact is attributable to the code version, inputs and actor that produced it, verifiable with a tool we did not write |
| **Telemetry** | Correlation rides on explicit attributes, not trace parentage — see A7 finding 1 |
| **Errors** | Typed and machine-readable. Never parsed from prose |
| **Idempotency** | Every externally-triggered action is safe to replay |

## B5. What we must design ourselves

Two boundaries have no standard to adopt. **They are the only places original design effort is warranted, and they carry the weight of the platform.**

**Dispatch** — one unit of agent work executes and returns one result.

Today there are three implementations and no contract between them. This is the seam that decides whether agent execution is pluggable at all. It must specify: the request shape, the result shape, cancellation semantics, timeout and budget enforcement, partial-result handling, and what a failure returns.

**State** — the graph and the ledger persist.

Today a JSONL file with a hash chain. The chain is the valuable idea and should survive; the file is not. This must specify: the write model, concurrency and single-writer guarantees, the integrity mechanism, retention, and the query surface a planner needs.

Everything else in B3 is a decision someone else already published. These two are ours.

---

# PART C — The ask

Produce a **decomposition strategy** for Part B.

1. **An ordered build sequence** across the five core components and sixteen capabilities. Separate real dependencies from apparent ones.
2. **A first-cut design for Dispatch and State** (B5). If you searched for prior art and found none, say what you searched.
3. **Per piece: a machine-checkable definition of done, plus the deliberate breakage that proves the check can fail.** A criterion nothing can fail is not a criterion.
4. **A second adapter for at least three capabilities**, chosen to prove the interface is not shaped around its current implementation. Design rule 3.
5. **What you could not decide, and what evidence would decide it.** A required output, not an apology.

Constraints:

- Distinguish **claimed** from **measured** throughout.
- In Part B output, **name capabilities and standards, never products.** Products belong in the adapter column only.
- Prefer an existing standard to an original design. Cite the standard and its version.
- Part A is substrate, not scope. Do not propose replacing what runs.
