# MVP-SCALE — Open Standards & Open-Source Stack Alignment v3

**Date:** 2026-09-11
**Scope:** Keep the MVP-SCALE seven-layer reference model. Define the contract each layer exposes, the standard at each boundary, the permissive open-source adapters behind each contract, the ledger that feeds self-improvement, and the self-improvement loop itself.
**License filter:** Apache-2.0, MIT, BSD-2/3, PostgreSQL License only. MPL, (A/L)GPL, BUSL, SSPL, ELv2, source-available excluded. Open-core allowed only where the open core alone fills the port; flagged.
**Verification legend:** ✅ license read from the repository LICENSE file this session · ⚠️ asserted from project docs/knowledge, re-read before adoption · ⛔ excluded by license.

---

# 0. Rules

1. A layer is never a product.
2. Only contracts cross layer boundaries.
3. An industry standard is used at every boundary where one exists.
4. Products sit behind provider interfaces and are replaceable.
5. Shared services are consumed through service contracts, not embedded in layers.
6. Cross-cutting concerns apply across layers without owning layer function.
7. Runtime infrastructure lives in Layer 4. Layer 3 sees only a sandbox handle.
8. Workflow state, agent state, and runtime state have different owners.
9. Every layer writes to the ledger. Only Layer 7 reads it to change the platform, and only through a promotion gate.

Disciplines: **ports-and-adapters** (rules 1–7) and **event sourcing** (rule 9 — an append-only record of expectation and outcome, queried deterministically).

---

# 1. Layer contracts

| # | Layer | Owns | Contract in → out | Standard at boundary |
|---|---|---|---|---|
| 1 | Invocation / Entry Points | protocol adaptation, auth context, tenant identity, normalization | external protocol → `WorkRequest` | AG-UI, ACP, A2A, CloudEvents, HTTP/gRPC |
| 2 | Orchestration & Control Plane | intake, policy, budgets, planning, durable workflow, dispatch | `WorkRequest` → `AgentTask` | — |
| 3 | Core Agent | harness loop, model/tool selection, context, workspace identity, sandbox handle | `AgentTask` → `ExecutionRequest`; `ExecutionResult` → `WorkProduct` | MCP, AGENTS.md, Agent Skills |
| 4 | Execution & Runtime | isolation, CPU/RAM, filesystem, processes, snapshot/recovery, memory store | `ExecutionRequest` → `ExecutionResult` | OCI, CRI/RuntimeClass, CNI, WASI |
| 5 | Assurance & Completion | deterministic gates, security gates, eval gates, admission, provenance, return | `WorkProduct` → `Completion` | in-toto, SLSA, SPDX/CycloneDX |
| 6 | Observe | telemetry, evaluation data, lineage, **ledger** | all layers → `LedgerEvent` | OpenTelemetry, OpenLineage |
| 7 | Self-Improvement | analyze, experiment, evaluate blind, promote, rollback | `LedgerEvent` → `PromotionCandidate` → versioned artifact | OpenFeature, OCI artifacts |
| S | Shared Platform Services | source, artifacts, knowledge, metadata, registry | service contracts | Git, S3 API, OCI Distribution |

State ownership (from rule 8):

| State | Owner |
|---|---|
| Workflow state — progression, retries, timers, budgets, approvals | Layer 2 |
| Agent state — objective, compact context, decisions, workspace identity | Layer 3 |
| Runtime state — VM/process, memory image, snapshot, overlay | Layer 4 |
| Durable artifacts | Shared services |
| Ledger, telemetry, lineage | Layer 6 |

---

# 2. Standards status

| Standard | Governance | Version / date | Stability | Placement | Diagram correction |
|---|---|---|---|---|---|
| **A2A** | Linux Foundation (from Google, Jun 2025) | v1.0 Mar 12 2026; v1.0.1 May 2026 | Stable | L1 Agent-to-Agent; L3 delegation | none |
| **ACP** (Agent Client Protocol) | Zed Industries; repo `agentclientprotocol/agent-client-protocol` ✅ Apache-2.0 | JSON-RPC 2.0; registry Jan 2026 | Early; remote transport on roadmap | L1 editor/IDE entry only | **Scope is editor ↔ coding agent, not generic client ↔ agent** |
| ACP (Agent Communication Protocol, IBM) | — | merged into A2A Aug 29 2025 | Deprecated | — | do not build on it |
| **AG-UI** | CopilotKit ✅ MIT | 16 event types; TS + Python SDKs | Active | L1 Human UI | **Move off Scheduled; belongs on Human** |
| **CloudEvents** | CNCF graduated ✅ Apache-2.0 | v1.0 | Stable | L1 Scheduled / Internal Event / External Event | **Add — the diagram has no standard here** |
| **MCP** | Linux Foundation / AAIF (from Anthropic, Dec 2025) | spec 2025-11-25 | De-facto standard | L3 Tool Interface | none |
| **AGENTS.md** | AAIF (from OpenAI) | v1.1 proposal; no schema | Convention, 60k+ repos | L3 Workspace | none |
| **Agent Skills** | `agentskills/agentskills` ✅ Apache-2.0 | folder + SKILL.md | Early | L3 Workspace | add beside AGENTS.md |
| **OpenTelemetry GenAI semconv** | OTel, repo `semantic-conventions-genai` | split out at v1.42.0 (Jun 2026) | **Development — no `gen_ai.*` attribute is Stable** | L6 | pin versions; map raw keys behind a view |
| **OpenFeature** | CNCF ✅ Apache-2.0 (flagd) | spec + flagd | Stable | L7 Promote | add — fills the promote/rollback port |
| **OCI Distribution / ORAS** | OCI / CNCF ✅ Apache-2.0 | — | Stable | S Registry | add — versioned prompts/configs as artifacts |

Internal contracts (`WorkRequest`, `AgentTask`, `ExecutionRequest`, `ExecutionResult`, `WorkProduct`, `Completion`, `LedgerEvent`, `PromotionCandidate`) are MVP-SCALE's own; not industry standards.

---

# 3. The ledger

The ledger is the append-only record that lets a query — not a model — answer *did this meet expectations, where was the pain, where did budget go.*

## 3.1 Write points

These are the blue-icon boxes on the reference diagram plus Registry.

| Layer | Write point | Event | Fields |
|---|---|---|---|
| 2 | Intake | `expectation` | work_request_id, tenant, objective_hash, acceptance_criteria[], budget{tokens, usd, steps, seconds}, policy_context, requested_profile |
| 2 | Policy | `policy_decision` | rule_id, allow/deny, constraints applied |
| 2 | Planning | `plan` | pattern (single/fan-out/crew), decomposition[], allocation per sub-task |
| 3 | Model Interface | `model_call` | attempt_id, model, provider, tokens_in/out, latency_ms, cost_usd, reasoning_effort, cache_hit |
| 3 | Tool Interface | `tool_call` | tool, server, latency_ms, ok/error, bytes |
| 4 | Runtime | `exec` | sandbox_id, profile, cmd_hash, exit_code, wall_ms, cpu_ms, resident_mb |
| 5 | Validation | `gate` | gate_id, kind (lint/test/scan/eval/policy), pass/fail, score, evidence_ref |
| 5 | Complete / Return | `outcome` | status, admitted, attempts, retries, human_interventions, actual{tokens, usd, steps, seconds}, artifact_refs[] |
| S | Registry | `promotion` | artifact_ref, version, from_version, flag_id, cohort, rollback_of |

Every event carries: `trace_id`, `work_request_id`, `workflow_id`, `agent_id`, `attempt_id`, `tenant_id`, `config_version` (which promoted prompt/routing/tool set was live).

## 3.2 Deterministic queries

| Question | Query shape |
|---|---|
| Met expectations? | every `gate` for the request passed AND `outcome.actual` ≤ `expectation.budget` on every dimension |
| Where is the pain? | failed `gate` count grouped by gate_id, task class, config_version |
| Where did budget go? | sum of `model_call.cost_usd` + `exec.wall_ms` grouped by plan phase |
| Are we getting more efficient? | `outcome.actual.steps` per admitted result, by task class, by config_version over time |
| Did a promotion regress? | same metric, cohort with flag on vs off, same window |
| Which tool/model mattered? | admitted rate grouped by model or tool present in the attempt |

## 3.3 Store

| Port | Primary | Alternate | Note |
|---|---|---|---|
| Ledger store | ClickHouse ⚠️ Apache-2.0 | PostgreSQL ⚠️ | ClickHouse is also OpenLIT's backend (Layer 6 table) — one store for traces and ledger |
| Transport | OpenTelemetry Collector ⚠️ Apache-2.0 | — | events emitted as OTel spans/events, exported to the store |
| Schema | **must build** | — | no OSS project models expectation vs outcome per attempt; the `gen_ai.*` conventions cover model/tool spans only |

---

# 4. Self-improvement loop

Reads the ledger (Section 3). Changes reach production only through Promote.

```text
ledger ──> Analyze ──> Experiment (isolated) ──> Evaluate Blind ──> Promote (flag/canary) ──> ledger
                                                                          │
                                                                    regression ──> Rollback
```

## 4.1 Levers the loop may change

| Lever | Layer | Registry artifact |
|---|---|---|
| prompts / system instructions | 3 | prompt version |
| model routing per task class | 3 | routing table |
| reasoning effort / context budget | 3 | agent config |
| tool set / MCP server list | 3 | tool manifest |
| skills loaded | 3 | skill bundle |
| gate set and thresholds (test strategy) | 5 | gate policy |
| runtime profile (CPU/RAM/isolation) | 4 | profile table |
| retry / timeout thresholds | 2 | workflow config |
| budget allocation per phase, crew size | 2 | planning policy |

## 4.2 Options per stage

| Stage | Option | Repo | License | Fit |
|---|---|---|---|---|
| Analyze | SQL over ledger store | — | — | **primary**; deterministic; must build the queries in 3.2 |
| Analyze | MLflow tracing + evaluation tables | github.com/mlflow/mlflow | Apache-2.0 ⚠️ | experiment lineage next to analysis |
| Analyze | OpenLIT evaluations | github.com/openlit/openlit | Apache-2.0 ✅ | same store as ledger |
| Analyze | failure clustering | — | — | must build; embed failed `gate` evidence, cluster, rank by cost |
| Experiment | MLflow experiments + prompt registry | github.com/mlflow/mlflow | Apache-2.0 ⚠️ | **primary** record of every candidate |
| Experiment | Optuna | github.com/optuna/optuna | MIT ✅ | search over numeric/categorical levers (routing, effort, thresholds, crew size) |
| Experiment | DSPy | github.com/stanfordnlp/dspy | MIT ⚠️ | prompt/program optimization |
| Experiment | TextGrad | github.com/zou-group/textgrad | MIT ⚠️ | textual-gradient prompt optimization |
| Experiment | Opik Agent Optimizer | github.com/comet-ml/opik | Apache-2.0 ✅ | six optimizers (few-shot, evolutionary, Bayesian) closest to turnkey |
| Experiment | Promptfoo | github.com/promptfoo/promptfoo | MIT ⚠️ | prompt regression matrix |
| Evaluate Blind | Inspect AI | github.com/UKGovernmentBEIS/inspect_ai | MIT ✅ | **primary**; hidden datasets, sandboxed, multi-turn |
| Evaluate Blind | Promptfoo holdout | github.com/promptfoo/promptfoo | MIT ⚠️ | CI-native `--error` fail |
| Evaluate Blind | Ragas | github.com/explodinggradients/ragas | Apache-2.0 ⚠️ | RAG-specific metrics |
| Evaluate Blind | DeepEval | github.com/confident-ai/deepeval | MIT ⚠️ | pytest-style |
| Promote | OpenFeature + flagd | github.com/open-feature/flagd | Apache-2.0 ✅ | **primary**; percentage / tenant cohort rollout, OTel-integrated |
| Promote | ORAS + Harbor | github.com/oras-project/oras | Apache-2.0 ✅ | versioned artifact for every lever in 4.1 |
| Promote | cosign + in-toto | github.com/sigstore/cosign | Apache-2.0 ⚠️ | signed provenance on promoted artifact |
| Promote | OPA promotion gate | github.com/open-policy-agent/opa | Apache-2.0 ⚠️ | gain-vs-cost-vs-risk threshold as policy |
| Rollback | flagd flip + ledger regression query | — | — | 3.2 "did a promotion regress" drives it; must build the trigger |

## 4.3 Objective

Multi-dimensional, evaluated from the ledger, never from a judge alone:

```text
admitted rate ↑   steps per admitted result ↓   cost per admitted result ↓
latency ↓         retries ↓                     human interventions ↓
policy/security violations = 0
```

## 4.4 Must build

- Ledger schema and queries (3.1–3.2)
- Failure clustering and candidate generation policy
- Promotion threshold policy (what gain justifies what risk)
- Rollback trigger
- The loop orchestration itself — no single permissive OSS product does trace → cluster → candidate → blind eval → promote

---

# 5. Adapters per layer

## Layer 1 — Invocation / Entry Points

| Port | Project | Repo | License | Backing | Role |
|---|---|---|---|---|---|
| Agentic gateway (LLM + MCP + A2A) | agentgateway | github.com/agentgateway/agentgateway | Apache-2.0 ✅ | Linux Foundation | **primary**; also fills L3 model gateway |
| Ingress / AI gateway | Envoy AI Gateway | github.com/envoyproxy/ai-gateway | Apache-2.0 ✅ | CNCF | alternate |
| Ingress / AI gateway | Higress | github.com/alibaba/higress | Apache-2.0 ✅ | Alibaba → CNCF | alternate |
| Human identity | Keycloak | github.com/keycloak/keycloak | Apache-2.0 ⚠️ | CNCF | **primary** if self-hosted IAM needed; else customer OIDC |
| Human identity | Zitadel | github.com/zitadel/zitadel | Apache-2.0 ⚠️ | Zitadel | alternate |
| A2A adapter | A2A SDKs | github.com/a2aproject/A2A | Apache-2.0 ⚠️ | Linux Foundation | Python/.NET/Go |
| AG-UI adapter | AG-UI SDKs | github.com/ag-ui-protocol/ag-ui | MIT ✅ | CopilotKit | TS/Python |
| ACP adapter | Agent Client Protocol | github.com/agentclientprotocol/agent-client-protocol | Apache-2.0 ✅ | Zed | editor entry |
| Event adapter | CloudEvents SDKs | github.com/cloudevents/spec | Apache-2.0 ✅ | CNCF | scheduled/internal/external |
| `WorkRequest` normalizer | — | — | — | — | **must build** |

## Layer 2 — Orchestration & Control Plane

| Port | Project | Repo | License | Backing | Role |
|---|---|---|---|---|---|
| Durable workflow | Temporal | github.com/temporalio/temporal | MIT ⚠️ | Temporal Technologies | **primary**; nondeterministic calls wrapped in activities |
| Durable workflow | Hatchet | github.com/hatchet-dev/hatchet | MIT ⚠️ | Hatchet | alternate; Postgres-backed |
| Durable workflow | Kestra | github.com/kestra-io/kestra | Apache-2.0 ⚠️ | Kestra | alternate; declarative |
| Durable workflow | Windmill | — | AGPL-3.0 ⛔ | — | excluded |
| Policy decision | OPA | github.com/open-policy-agent/opa | Apache-2.0 ⚠️ | CNCF | **primary** |
| Policy decision | Cedar | github.com/cedar-policy/cedar | Apache-2.0 ⚠️ | AWS | alternate; analyzable |
| Policy — ReBAC | OpenFGA | github.com/openfga/openfga | Apache-2.0 ⚠️ | CNCF | when tenant/resource graph grows |
| Policy — ReBAC | SpiceDB | github.com/authzed/spicedb | Apache-2.0 ⚠️ | AuthZed | alternate |
| Secrets | Infisical | github.com/Infisical/infisical | MIT ✅ open-core (`ee/` proprietary) | Infisical | **primary** under filter |
| Secrets | OpenBao / Vault | — | MPL-2.0 / BUSL ⛔ | — | excluded; keep behind secret-store interface if accepted later |
| Relational state | PostgreSQL | github.com/postgres/postgres | PostgreSQL ⚠️ | PGDG | **primary** |
| Cache / leases | Valkey | github.com/valkey-io/valkey | BSD-3 ⚠️ | Linux Foundation | when needed |
| Event bus | NATS | github.com/nats-io/nats-server | Apache-2.0 ⚠️ | CNCF | when needed; CloudEvents envelope |
| Event bus | Redpanda | — | BSL ⛔ | — | excluded; Kafka ⚠️ Apache-2.0 if scale demands |
| Budget-aware planning, placement, crew strategy | — | — | — | — | **must build — this is the differentiation** |

## Layer 3 — Core Agent

| Port | Project | Repo | License | Backing | Role |
|---|---|---|---|---|---|
| Harness — general workhorse | Goose | github.com/aaif-goose/goose | Apache-2.0 ✅ | AAIF (from Block, moved Apr 2026) | **primary profile** |
| Harness — typed service | Pydantic AI | github.com/pydantic/pydantic-ai | MIT ✅ | Pydantic | **primary profile**; native Temporal, MCP, AG-UI, A2A |
| Harness — API-only / captain | workerd | github.com/cloudflare/workerd | Apache-2.0 ✅ | Cloudflare | **hold**; benchmark density vs paused Goose/Pydantic before adopting a JS/Wasm boundary |
| Harness — coding | OpenHands | github.com/OpenHands/OpenHands | MIT ✅ open-core (`/enterprise` Polyform) | All Hands | alternate |
| Harness — coding | Codex CLI | github.com/openai/codex | Apache-2.0 ✅ | OpenAI | alternate; AGENTS.md, ACP adapter |
| Harness — coding | Gemini CLI | github.com/google-gemini/gemini-cli | Apache-2.0 ✅ | Google | alternate; ACP reference impl |
| Harness — coding | Aider | github.com/Aider-AI/aider | Apache-2.0 ✅ | Aider AI | alternate; git-native |
| Harness — research | SWE-agent / mini-swe-agent | github.com/SWE-agent/SWE-agent | MIT ✅ | Princeton/Stanford | eval baseline |
| Framework | OpenAI Agents SDK | github.com/openai/openai-agents-python | MIT ✅ | OpenAI | v0.19.4 Aug 2026 |
| Framework | Google ADK | github.com/google/adk-python | Apache-2.0 ✅ | Google | native A2A |
| Framework | Strands Agents | github.com/strands-agents/sdk-python | Apache-2.0 ✅ | AWS | MCP, A2A |
| Framework | smolagents | github.com/huggingface/smolagents | Apache-2.0 ✅ | Hugging Face | minimal |
| Framework | AG2 | github.com/ag2ai/ag2 | Apache-2.0 ✅ | ag2ai | AutoGen successor |
| Framework | Semantic Kernel | github.com/microsoft/semantic-kernel | MIT ✅ | Microsoft | being succeeded by Agent Framework |
| Framework | CrewAI | github.com/crewAIInc/crewAI | MIT ✅ | crewAI | multi-agent |
| Framework | LangGraph | github.com/langchain-ai/langgraph | MIT ✅ core; `langgraph-api` ELv2 | LangChain | core only; server excluded |
| Model gateway | agentgateway | see Layer 1 | Apache-2.0 ✅ | Linux Foundation | **primary** |
| Model gateway | Bifrost | github.com/maximhq/bifrost | Apache-2.0 ✅ | Maxim | alternate |
| Model gateway | Portkey Gateway | github.com/Portkey-AI/gateway | MIT ✅ | Portkey | alternate |
| Model gateway | LiteLLM | github.com/BerriAI/litellm | MIT ✅ open-core (`enterprise/`; gate checks leak into MIT files) | BerriAI | adapter only; no longer defines the port |
| Tool protocol | MCP SDKs | github.com/modelcontextprotocol | MIT ⚠️ | Linux Foundation | Python/TS/Go/Rust/Java/C#/Kotlin |
| Workspace context | AGENTS.md + Agent Skills | github.com/agentskills/agentskills | Apache-2.0 ✅ | AAIF | conventions |
| Local inference | vLLM | github.com/vllm-project/vllm | Apache-2.0 ✅ | PyTorch Foundation | **primary** throughput |
| Local inference | SGLang | github.com/sgl-project/sglang | Apache-2.0 ⚠️ | LMSYS | alternate; structured output |
| Local inference | llama.cpp / Ollama | github.com/ggml-org/llama.cpp | MIT ⚠️ | ggml / Ollama | CPU / dev laptops |

## Layer 4 — Execution & Runtime

Two adapters behind one `ExecutionRequest` contract. Kata issue #13754 (open) confirms Kata does not expose Firecracker running-VM checkpoint/restore, so the direct adapter is not optional if snapshot density matters.

| Port | Project | Repo | License | Backing | Role |
|---|---|---|---|---|---|
| microVM | Firecracker | github.com/firecracker-microvm/firecracker | Apache-2.0 ⚠️ | AWS | **primary VMM**; ≤125 ms to init per SPECIFICATION.md |
| microVM | Cloud Hypervisor | github.com/cloud-hypervisor/cloud-hypervisor | Apache-2.0/BSD-3 ⚠️ | Linux Foundation | alternate VMM |
| Direct adapter — snapshot-optimized | node controller + vsock executor | — | — | — | **must build**; study E2B Runtime ⚠️ Apache-2.0 and Pyro ⚠️ MIT |
| Standards adapter — scale-out | K3s + containerd + Kata | github.com/kata-containers/kata-containers | Apache-2.0 ⚠️ | OpenInfra / CNCF | OCI/CRI/CNI portability; **scale-out, not node 1** |
| Container isolation | gVisor | github.com/google/gvisor | Apache-2.0 ⚠️ | Google | alternate profile |
| WASM profile | Wasmtime | github.com/bytecodealliance/wasmtime | Apache-2.0 ⚠️ | Bytecode Alliance | **primary** WASI |
| WASM profile | WasmEdge | github.com/WasmEdge/WasmEdge | Apache-2.0 ⚠️ | CNCF | alternate |
| Sandbox platform | microsandbox | github.com/microsandbox/microsandbox | Apache-2.0 ⚠️ | microsandbox | self-host reference |
| Sandbox platform | Daytona | — | AGPL-3.0 ⛔ | — | excluded |
| Checkpoint/restore | CRIU | — | GPL/LGPL ⛔ | — | excluded; **no permissive equivalent** — use Layer 2 replay + Layer 4 snapshots instead |
| Autoscaling (scale-out) | KEDA | github.com/kedacore/keda | Apache-2.0 ✅ | CNCF | with K3s adapter only |
| Agent memory | Mem0 | github.com/mem0ai/mem0 | Apache-2.0 ✅ | Mem0 | **primary**; BYO store |
| Agent memory | Letta | github.com/letta-ai/letta | Apache-2.0 ✅ | Letta | alternate; tiered self-editing |
| Agent memory — temporal graph | Graphiti | github.com/getzep/graphiti | Apache-2.0 ✅ | Zep | only option with as-of validity |
| Agent memory — graph | Cognee | github.com/topoteretes/cognee | Apache-2.0 ✅ | Topoteretes | alternate |

## Layer 5 — Assurance & Completion

Sequence: deterministic → security/supply-chain → eval → policy admission → attest + register → return.

| Port | Project | Repo | License | Backing | Role |
|---|---|---|---|---|---|
| Vuln / SBOM / misconfig / secrets | Trivy | github.com/aquasecurity/trivy | Apache-2.0 ✅ | Aqua | **primary** |
| SBOM + vuln | Syft + Grype | github.com/anchore/syft | Apache-2.0 ✅ | Anchore | alternate |
| Secret scan | Gitleaks CLI | github.com/gitleaks/gitleaks | MIT ✅ | Gitleaks | **primary**; `gitleaks-action` separate license |
| Secret scan | TruffleHog | — | AGPL-3.0 ⚠️⛔ | — | excluded pending LICENSE check |
| SAST | Semgrep engine | — | LGPL-2.1 ⛔ | — | excluded; evaluate OpenGrep ⚠️ |
| Provenance | in-toto | github.com/in-toto/in-toto | Apache-2.0 ⚠️ | CNCF | **primary** |
| Signing | cosign | github.com/sigstore/cosign | Apache-2.0 ⚠️ | OpenSSF | **primary** |
| Eval gate | Inspect AI | github.com/UKGovernmentBEIS/inspect_ai | MIT ✅ | UK AISI | **primary** |
| Eval gate | Promptfoo | github.com/promptfoo/promptfoo | MIT ⚠️ | Promptfoo | alternate; red-team |
| Guardrails | NeMo Guardrails | github.com/NVIDIA/NeMo-Guardrails | Apache-2.0 ⚠️ | NVIDIA | **primary** |
| Guardrails | LLM Guard | github.com/protectai/llm-guard | MIT ⚠️ | Protect AI | alternate |
| Admission policy | OPA | see Layer 2 | Apache-2.0 ⚠️ | CNCF | final gate |
| Admission score, acceptance contracts | — | — | — | — | **must build — differentiation** |

## Layer 6 — Observe

| Port | Project | Repo | License | Backing | Role |
|---|---|---|---|---|---|
| Telemetry pipeline | OpenTelemetry Collector | github.com/open-telemetry/opentelemetry-collector | Apache-2.0 ⚠️ | CNCF | **primary** |
| GenAI instrumentation | OpenLIT SDK | github.com/openlit/openlit | Apache-2.0 ✅ | OpenLIT | **primary**; OTel-native, no license key or usage limit |
| GenAI instrumentation | OpenLLMetry | github.com/traceloop/openllmetry | Apache-2.0 ⚠️ | Traceloop | alternate |
| Trace / eval UI | OpenLIT | github.com/openlit/openlit | Apache-2.0 ✅ | OpenLIT | **primary**; runs on ClickHouse |
| Trace / eval UI | Opik | github.com/comet-ml/opik | Apache-2.0 ✅ | Comet | alternate; fully permissive, bundles optimizer |
| Trace / eval UI | Langfuse | github.com/langfuse/langfuse | MIT ✅ open-core (`ee/`, `web/src/ee/`, `worker/src/ee/`) | ClickHouse Inc (acquired Jan 2026) | optional adapter |
| Trace / eval UI | Arize Phoenix | — | ELv2 ⛔ | — | excluded |
| Ledger + trace store | ClickHouse | github.com/ClickHouse/ClickHouse | Apache-2.0 ⚠️ | ClickHouse Inc | **primary** (Section 3.3) |
| Metrics | Prometheus | github.com/prometheus/prometheus | Apache-2.0 ⚠️ | CNCF | **primary** |
| Traces backend | Jaeger | github.com/jaegertracing/jaeger | Apache-2.0 ⚠️ | CNCF | if a separate trace backend is wanted |
| Logs | Loki / Tempo | — | AGPL-3.0 ⛔ | — | excluded |
| Dashboards | Perses | github.com/perses/perses | Apache-2.0 ⚠️ | CNCF | Grafana is AGPL |
| Lineage | OpenLineage + Marquez | github.com/OpenLineage/OpenLineage | Apache-2.0 ⚠️ | LF AI & Data | **primary** |

## Layer 7 — Self-Improvement

See Section 4.2.

## Shared Platform Services

| Port | Project | Repo | License | Backing | Role |
|---|---|---|---|---|---|
| Source | Git + worktrees; Gitea | github.com/go-gitea/gitea | MIT ⚠️ | Gitea | **primary** self-host; Forgejo is GPLv3+ ⛔ |
| Artifacts | S3 API; SeaweedFS | github.com/seaweedfs/seaweedfs | Apache-2.0 ⚠️ | SeaweedFS | **primary** self-host; R2/S3 external; MinIO/Garage/Ceph ⛔ |
| Knowledge | pgvector | github.com/pgvector/pgvector | PostgreSQL ⚠️ | pgvector | **primary** |
| Knowledge | Qdrant / Milvus / LanceDB | github.com/qdrant/qdrant | Apache-2.0 ⚠️ | — | scale-out |
| Metadata | PostgreSQL | see Layer 2 | PostgreSQL ⚠️ | PGDG | **primary** |
| Registry — artifacts | ORAS + Harbor | github.com/oras-project/oras | Apache-2.0 ✅ | CNCF | **primary**; prompts, configs, playbooks, images |
| Registry — artifacts | Zot | github.com/project-zot/zot | Apache-2.0 ⚠️ | Linux Foundation | alternate; lighter |

## Cross-cutting

| Concern | Project | Repo | License | Role |
|---|---|---|---|---|
| Workload identity | SPIRE | github.com/spiffe/spire | Apache-2.0 ⚠️ | multi-node / BYOC |
| Human identity | Keycloak | see Layer 1 | Apache-2.0 ⚠️ | — |
| Cost | OpenCost | github.com/opencost/opencost | Apache-2.0 ⚠️ | K8s adapter only; ledger (Section 3) is the platform's cost source of truth |
| Privacy | Presidio | github.com/microsoft/presidio | MIT ⚠️ | PII redaction in Collector pipeline |
| Provisioning | Pulumi; cloud-init | github.com/pulumi/pulumi | Apache-2.0 ⚠️ | Ansible GPL ⛔, OpenTofu MPL ⛔ |
| Secrets bootstrap (K8s only) | Sealed Secrets | github.com/bitnami-labs/sealed-secrets | Apache-2.0 ⚠️ | with the K3s adapter only |

---

# 6. Must-build summary

| Item | Layer | Why no OSS |
|---|---|---|
| `WorkRequest` normalizer / anti-corruption layer | 1 | platform-specific semantics |
| Budget-aware planning, placement, crew strategy | 2 | differentiation |
| Direct Firecracker adapter (node controller + vsock executor) | 4 | Kata lacks checkpoint/restore; CRIU is GPL |
| Admission score and acceptance contracts | 5 | differentiation |
| Ledger schema, queries, regression trigger | 6 | no OSS models expectation vs outcome |
| Failure clustering, candidate policy, promotion threshold, loop orchestration | 7 | no single permissive product |

---

# 7. Deployment profiles

| Profile | Target | Execution adapter | Notes |
|---|---|---|---|
| A — single node / workstation / appliance | 12–16 cores, 16–32 GB, NVMe, KVM | direct Firecracker | no Kubernetes; control plane may be remote over outbound mTLS |
| B — small HA fleet | 3 control + N execution nodes | direct Firecracker on labeled nodes; K3s + Kata optional | HA PostgreSQL, Temporal cluster, agentgateway replicas, SPIRE, KEDA |
| C — cloud / multi-region | upstream K8s or K3s | K3s + Kata primary; direct Firecracker pool for snapshot density | autoscaler, BYOC nodes outbound-only, externalized storage |

Single node → scale-out per layer:

| Layer | Single node | Scale-out |
|---|---|---|
| 1 | agentgateway + Keycloak containers | agentgateway replicas behind L4 LB; clustered Keycloak |
| 2 | Temporal + PostgreSQL | Temporal sharding; Postgres replicas; NATS JetStream |
| 3 | one Goose/Pydantic worker + agentgateway + Ollama | worker pool; vLLM/SGLang GPU fleet |
| 4 | Firecracker warm pool | node controller fleet; K3s + Kata adapter |
| 5 | scanners + Inspect as CI jobs | parallel runners; shared attestation store |
| 6 | Collector + ClickHouse + OpenLIT | Collector gateway tier; ClickHouse cluster |
| 7 | MLflow + Inspect + flagd reading ledger | distributed eval runners; promotion pipeline to registry |

---

# 8. Build sequence

| Milestone | Deliverable | Depends on |
|---|---|---|
| 1 | Freeze contracts: `WorkRequest`, `AgentTask`, `ExecutionRequest/Result`, `WorkProduct`, `Completion`, `LedgerEvent`, `PromotionCandidate` | Section 1 |
| 2 | Ledger schema + the six queries | Section 3 |
| 3 | Direct Firecracker adapter: create / exec over vsock / read / write / snapshot / restore / release | Section 5, Layer 4 |
| 4 | Benchmark Layer 4: cold boot, restore, p50/p95 time-to-first-command, resident and dirty RAM at 1/10/25/50/100 sandboxes | Milestone 3 |
| 5 | Attach Layer 3: Goose and Pydantic AI through the execution contract; agentgateway in front of models and MCP | Milestone 3 |
| 6 | Attach Layer 2: Temporal dispatches `AgentTask`; OPA; Infisical | Milestone 5 |
| 7 | Layer 5 gates + cosign/in-toto + ORAS/Harbor | Milestone 6 |
| 8 | Layer 6 full: Collector + OpenLIT + ClickHouse; every write point in 3.1 live | Milestone 2, 7 |
| 9 | Layer 7: MLflow + Optuna + Inspect blind sets + flagd; first lever = model routing per task class | Milestone 8 |
| 10 | workerd density benchmark; K3s + Kata adapter; multi-node | Milestone 9 |

---

# Appendix — license exclusions and re-verification

Excluded under the filter: Windmill, OpenBao, Vault, Redpanda, Daytona, Arize Phoenix, Loki, Tempo, Grafana, MinIO, Garage, Ceph, Forgejo, Semgrep engine, TruffleHog, CRIU, Ansible, OpenTofu, `langgraph-api`.

Relicensed in the last three years: Redis → AGPL/SSPL (use Valkey), Vault/Terraform → BUSL, Forgejo → GPLv3+, Redpanda → BSL, Arize Phoenix → ELv2.

Read every ⚠️ LICENSE file at the pinned commit before adoption. Licenses verified ✅ this session were read at the default branch on 2026-09-11.
