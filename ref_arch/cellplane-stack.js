// Reference Stack — open source building blocks per Reference Model layer.
// Structure: layers[] → challenges[] → picks[] / alts[] / excluded[] (tool names). Tool metadata lives in `tools`.
// tier: 'core' = start-here minimum for mid-market; 'watch' = emerging, hold or licence-flagged, research before committing; 'excluded' = fails the licence or commercial filter; absent = standard pick.
// exclude: 'licence' | 'pricing' | 'both' — why an excluded tool is out. Pricing = a permissive-looking project whose usable edition is gated behind commercial terms.
// verified: true = licence read from the repo LICENSE file in the research session; false = re-verify before adoption.
// build: true on a challenge = no permissive OSS covers the port; it must be built.
// Source: MVP-SCALE Open Standards & Open-Source Stack Alignment v3 (uploads/mvp-scale-open-stack-alignment-v3.md), 2026-09-11.

export const meta = { version: '0.3', updated: '2026-09-11',
  filter: 'Permissive licences only (Apache-2.0, MIT, BSD, PostgreSQL). Copyleft, BUSL, SSPL, ELv2 and source-available are out, and so is anything whose usable edition sits behind commercial pricing.',
  criteria: ['Permissive licence only (Apache, MIT, BSD, PostgreSQL)', 'Usable edition is the open one; no commercial gate on core function', 'Self-hostable on Cloudflare, Google Cloud or AWS', 'Production track record at mid-market to enterprise scale', 'Implements the standard at its layer boundary'] };

const T = (tier, license, kind, maturity, note, verified, exclude) => ({ tier, license, kind, maturity, note, verified: !!verified, exclude: exclude || null });
export const tools = {
  // Layer 1
  'agentgateway': T('core', 'Apache-2.0', 'Agentic gateway', 'Linux Foundation', 'One gateway for LLM, MCP and A2A traffic. Also fills the layer 3 model-gateway port, which is why LiteLLM no longer defines it.', true),
  'Envoy AI Gateway': T(null, 'Apache-2.0', 'AI gateway', 'CNCF', 'Envoy Gateway with AI routing. Alternate ingress.', true),
  'Higress': T(null, 'Apache-2.0', 'AI gateway', 'Alibaba → CNCF', 'MCP-aware gateway; a closed Enterprise edition exists separately.', true),
  'Keycloak': T('core', 'Apache-2.0', 'Identity provider', 'CNCF', 'Self-hosted OIDC / SAML IdP. Use the customer\'s OIDC provider instead when one exists.'),
  'Zitadel': T(null, 'Apache-2.0', 'Identity provider', 'Zitadel', 'Cloud-native IdP alternate.'),
  'A2A SDK': T('core', 'Apache-2.0', 'Protocol SDK', 'Linux Foundation · v1.0.1 May 2026', 'Agent2Agent v1.0 (March 2026): signed Agent Cards, JSON-RPC 2.0. Python, .NET, Go.'),
  'AG-UI SDKs': T(null, 'MIT', 'Protocol SDK', 'CopilotKit', 'UI ↔ agent events, 16 event types. Belongs on the Human entry, not Scheduled.', true),
  'Agent Client Protocol': T('watch', 'Apache-2.0', 'Protocol SDK', 'Zed Industries · early', 'Editor ↔ coding-agent contract only, not a generic client protocol. Remote transport still on the roadmap. Not IBM\'s deprecated ACP.', true),
  'CloudEvents SDKs': T('core', 'Apache-2.0', 'Event envelope', 'CNCF graduated · v1.0', 'Standard envelope for scheduled, internal and external events. The diagram had no standard here before.', true),
  // Layer 2
  'Temporal': T('core', 'MIT', 'Durable workflow engine', 'Temporal Technologies', 'Deterministic replay, schedules, task queues. Wrap nondeterministic LLM calls in activities.'),
  'Hatchet': T(null, 'MIT', 'Durable workflow engine', 'Hatchet', 'Postgres-backed, self-host-first.'),
  'Kestra': T(null, 'Apache-2.0', 'Workflow orchestrator', 'Kestra', 'Declarative YAML orchestration.'),
  'Windmill': T('excluded', 'AGPL-3.0', 'Workflow platform', 'Windmill Labs', 'Platform core is AGPLv3.', true, 'licence'),
  'Open Policy Agent': T('core', 'Apache-2.0', 'Policy engine', 'CNCF graduated', 'Rego for ABAC, budgets, admission and the layer 7 promotion gate. Styra support winding down; OPA stays CNCF.'),
  'Cedar': T(null, 'Apache-2.0', 'Policy language', 'AWS', 'Formally analysable authorization language.'),
  'OpenFGA': T(null, 'Apache-2.0', 'ReBAC engine', 'CNCF', 'Zanzibar-style permissions when the tenant / resource graph grows. SpiceDB is the alternate.'),
  'Infisical': T('core', 'MIT', 'Secrets manager', 'Infisical · open-core', 'Everything outside ee/ is MIT. The permissive answer now that Vault is BUSL.', true),
  'OpenBao': T('excluded', 'MPL-2.0', 'Secrets manager', 'Linux Foundation', 'MPL. Vault itself is BUSL. Keep behind a secret-store interface in case either is accepted later.', false, 'licence'),
  'PostgreSQL': T('core', 'PostgreSQL', 'Relational store', 'PGDG', 'Canonical state, metadata and catalog store.'),
  'Valkey': T(null, 'BSD-3-Clause', 'Cache / leases', 'Linux Foundation', 'Redis fork under a permissive licence. Redis relicensed to AGPL / SSPL.'),
  'NATS': T(null, 'Apache-2.0', 'Event bus', 'CNCF', 'Lightweight bus with a CloudEvents envelope; JetStream for persistence. Add when needed.'),
  'Apache Kafka': T(null, 'Apache-2.0', 'Event bus', 'Apache', 'When scale demands it.'),
  'Redpanda': T('excluded', 'BSL', 'Event bus', 'Redpanda', 'Business Source License.', false, 'licence'),
  // Layer 3
  'goose': T('core', 'Apache-2.0', 'Agent harness', 'Agentic AI Foundation (LF)', 'General workhorse profile. Rust, provider-neutral, MCP-native. Moved to aaif-goose April 2026.', true),
  'Pydantic AI': T('core', 'MIT', 'Agent harness', 'Pydantic Services', 'Typed-service profile. Native Temporal, MCP, AG-UI and A2A.', true),
  'workerd': T('watch', 'Apache-2.0', 'JS / Wasm runtime', 'Cloudflare', 'API-only "captain" profile. Hold: benchmark density against paused goose / Pydantic workers before adopting a JS / Wasm boundary.', true),
  'OpenHands': T(null, 'MIT', 'Coding harness', 'All Hands AI · open-core', 'Core is MIT; /enterprise is Polyform Free Trial.', true),
  'Codex CLI': T(null, 'Apache-2.0', 'Coding harness', 'OpenAI', 'Rust CLI is Apache-2.0; desktop app is proprietary. AGENTS.md and an ACP adapter.', true),
  'Gemini CLI': T(null, 'Apache-2.0', 'Coding harness', 'Google', 'Reference ACP implementation.', true),
  'Aider': T(null, 'Apache-2.0', 'Coding harness', 'Aider AI', 'Git-native.', true),
  'Google ADK': T(null, 'Apache-2.0', 'Agent framework', 'Google', 'Native A2A: to_a2a() and RemoteA2aAgent.', true),
  'OpenAI Agents SDK': T(null, 'MIT', 'Agent framework', 'OpenAI · v0.19.4 Aug 2026', 'Lightweight; tracing is not OTel-native.', true),
  'Strands Agents': T(null, 'Apache-2.0', 'Agent framework', 'AWS', 'MCP and A2A.', true),
  'smolagents': T(null, 'Apache-2.0', 'Agent framework', 'Hugging Face', 'Minimal.', true),
  'LangGraph': T('watch', 'MIT (core)', 'Agent framework', 'LangChain', 'Core is MIT; the langgraph-api server is Elastic License 2.0 and needs a commercial key for production self-hosting. Core only.', true),
  'Bifrost': T(null, 'Apache-2.0', 'Model gateway', 'Maxim', 'Rust core; alternate model gateway.', true),
  'Portkey Gateway': T(null, 'MIT', 'Model gateway', 'Portkey', 'Alternate model gateway; hosted version adds governance.', true),
  'LiteLLM': T('watch', 'MIT', 'Model gateway', 'BerriAI · open-core', 'Adapter only; no longer defines the port. enterprise/ is proprietary and its gate checks leak into MIT files, so the boundary is not runtime-clean.', true),
  'MCP SDKs': T('core', 'MIT', 'Protocol SDK', 'Linux Foundation · spec 2025-11-25', 'Official SDKs in Python, TypeScript, Go, Rust, Java, C#, Kotlin.'),
  'Agent Skills': T(null, 'Apache-2.0', 'Workspace convention', 'Agentic AI Foundation', 'Folder + SKILL.md convention beside AGENTS.md.', true),
  'vLLM': T(null, 'Apache-2.0', 'Local inference', 'PyTorch Foundation', 'Throughput on a GPU fleet.', true),
  'SGLang': T(null, 'Apache-2.0', 'Local inference', 'LMSYS', 'Structured output.'),
  'Ollama': T(null, 'MIT', 'Local inference', 'Ollama', 'Developer laptops and single node; llama.cpp underneath.'),
  // Layer 4
  'Firecracker': T('core', 'Apache-2.0', 'MicroVM', 'AWS', 'Primary VMM. ≤125 ms to init. Direct adapter is node 1; Kata does not expose Firecracker checkpoint / restore (kata #13754).'),
  'Cloud Hypervisor': T(null, 'Apache-2.0 / BSD-3', 'MicroVM', 'Linux Foundation', 'Alternate VMM.'),
  'E2B Runtime': T('watch', 'Apache-2.0', 'Sandbox runtime', 'E2B', 'Study for the direct Firecracker adapter (node controller + vsock executor). Pyro (MIT) likewise.'),
  'Kata Containers': T(null, 'Apache-2.0', 'Sandboxed containers', 'OpenInfra / CNCF', 'K3s + containerd + Kata is the standards adapter for scale-out (OCI / CRI / CNI). Not node 1.'),
  'gVisor': T(null, 'Apache-2.0', 'Sandboxed containers', 'Google', 'Alternate isolation profile.'),
  'KEDA': T(null, 'Apache-2.0', 'Autoscaling', 'CNCF graduated', 'Queue-driven autoscaling; with the K3s adapter only.', true),
  'Wasmtime': T('core', 'Apache-2.0', 'WASM runtime', 'Bytecode Alliance', 'WASI runtime for the WASM profile.'),
  'WasmEdge': T(null, 'Apache-2.0', 'WASM runtime', 'CNCF', 'Alternate WASM runtime.'),
  'microsandbox': T(null, 'Apache-2.0', 'Sandbox platform', 'microsandbox', 'Self-host reference on libkrun.'),
  'Daytona': T('excluded', 'AGPL-3.0', 'Sandbox platform', 'Daytona', 'AGPL.', false, 'licence'),
  'CRIU': T('excluded', 'GPL-2.0 / LGPL', 'Checkpoint / restore', 'CRIU', 'No permissive equivalent exists. Use layer 2 replay plus layer 4 VM snapshots instead.', false, 'licence'),
  'Mem0': T('core', 'Apache-2.0', 'Agent memory', 'Mem0 Inc', 'Extract-and-retrieve memory; bring your own store.', true),
  'Letta': T(null, 'Apache-2.0', 'Agent memory', 'Letta Inc', 'Tiered self-editing memory.', true),
  'Graphiti': T(null, 'Apache-2.0', 'Temporal memory', 'Zep', 'Only option with as-of validity windows. Needs Neo4j or FalkorDB.', true),
  'Cognee': T(null, 'Apache-2.0', 'Graph memory', 'Topoteretes', 'Graph + vector, embedded defaults.', true),
  // Layer 5
  'Trivy': T('core', 'Apache-2.0', 'Scanner', 'Aqua Security', 'Vulnerabilities, SBOM, misconfig, secrets in one binary.', true),
  'Syft + Grype': T(null, 'Apache-2.0', 'SBOM + scanner', 'Anchore', 'Split SBOM generation and scan.', true),
  'Gitleaks': T('core', 'MIT', 'Secret scanner', 'Gitleaks', 'CLI is MIT; gitleaks-action carries a separate licence.', true),
  'Semgrep': T('excluded', 'LGPL-2.1', 'SAST', 'Semgrep Inc', 'LGPL engine. Evaluate OpenGrep, the permissive fork.', false, 'licence'),
  'TruffleHog': T('excluded', 'AGPL-3.0', 'Secret scanner', 'Truffle Security', 'AGPL, pending LICENSE check.', false, 'licence'),
  'in-toto': T('core', 'Apache-2.0', 'Attestation', 'CNCF', 'Supply-chain attestation (in-toto, SLSA).'),
  'cosign': T('core', 'Apache-2.0', 'Signing', 'OpenSSF Sigstore', 'Keyless signing of admitted and promoted artifacts.'),
  'Inspect AI': T('core', 'MIT', 'Evaluation framework', 'UK AI Safety Institute', 'Eval gate in layer 5 and blind holdout in layer 7. Hidden datasets, sandboxed, multi-turn.', true),
  'Promptfoo': T(null, 'MIT', 'LLM evaluation', 'Promptfoo', 'Regression matrix and red-team; --error fails CI.'),
  'Ragas': T(null, 'Apache-2.0', 'RAG evaluation', 'Exploding Gradients', 'RAG-specific metrics.'),
  'DeepEval': T(null, 'MIT', 'LLM evaluation', 'Confident AI', 'Pytest-style.'),
  'NeMo Guardrails': T('core', 'Apache-2.0', 'Guardrails', 'NVIDIA', 'Programmable rails.'),
  'LLM Guard': T(null, 'MIT', 'Guardrails', 'Protect AI', 'Input / output scanners.'),
  // Layer 6
  'OTel Collector': T('core', 'Apache-2.0', 'Telemetry pipeline', 'CNCF', 'Redact, enrich and route before egress. GenAI semconv still Development-status; pin versions and map raw keys behind a view.'),
  'OpenLIT': T('core', 'Apache-2.0', 'GenAI observability', 'OpenLIT', 'OTel-native SDK and trace / eval UI on ClickHouse. No licence key, no usage limit. One store for traces and the ledger.', true),
  'OpenLLMetry': T(null, 'Apache-2.0', 'GenAI instrumentation', 'Traceloop', 'Alternate OTel instrumentation.'),
  'Opik': T(null, 'Apache-2.0', 'Trace / eval UI', 'Comet', 'Fully permissive, no ee/ split; bundles Agent Optimizer.', true),
  'Langfuse': T('watch', 'MIT', 'Trace / eval UI', 'ClickHouse Inc · open-core', 'Optional adapter. ee/ directories (RBAC, audit logs, SCIM, masking, retention) are proprietary.', true),
  'Arize Phoenix': T('excluded', 'Elastic 2.0', 'Trace store', 'Arize', 'ELv2 is source-available, not OSI.', true, 'licence'),
  'ClickHouse': T('core', 'Apache-2.0', 'Columnar store', 'ClickHouse Inc', 'Ledger and trace store. Schema and the six deterministic queries are the build.'),
  'Prometheus': T('core', 'Apache-2.0', 'Metrics', 'CNCF graduated', 'Metrics.'),
  'Perses': T(null, 'Apache-2.0', 'Dashboards', 'CNCF', 'Dashboards as code. Grafana is AGPL.'),
  'Jaeger': T(null, 'Apache-2.0', 'Trace backend', 'CNCF graduated', 'If a separate trace backend is wanted.'),
  'Loki / Tempo': T('excluded', 'AGPL-3.0', 'Logs / traces', 'Grafana Labs', 'AGPL, as is Grafana.', false, 'licence'),
  'OpenLineage': T(null, 'Apache-2.0', 'Lineage', 'LF AI & Data', 'Lineage spec and client; Marquez is the reference server.'),
  // Layer 7
  'MLflow': T('core', 'Apache-2.0', 'Experiments / registry', 'LF AI & Data', 'Record of every candidate; prompt registry; tracing and evaluation tables.'),
  'Optuna': T(null, 'MIT', 'Hyperparameter search', 'Preferred Networks', 'Search over numeric and categorical levers: routing, effort, thresholds, crew size.', true),
  'DSPy': T(null, 'MIT', 'Prompt optimization', 'Stanford NLP', 'Prompt / program optimization.'),
  'TextGrad': T(null, 'MIT', 'Prompt optimization', 'Zou Group (Stanford)', 'Textual gradients.'),
  'Opik Agent Optimizer': T(null, 'Apache-2.0', 'Closed-loop optimizer', 'Comet', 'Six optimizers; closest to turnkey.', true),
  'OpenFeature + flagd': T('core', 'Apache-2.0', 'Feature flags', 'CNCF', 'Percentage and tenant-cohort rollout, OTel-integrated. Fills the promote / rollback port.', true),
  // Shared
  'Gitea': T('core', 'MIT', 'Git hosting', 'Gitea', 'Self-hosted Git with Actions-compatible CI.'),
  'Forgejo': T('excluded', 'GPL-3.0+', 'Git hosting', 'Codeberg', 'Relicensed to GPLv3+.', false, 'licence'),
  'SeaweedFS': T('core', 'Apache-2.0', 'S3 storage', 'SeaweedFS', 'Permissive S3-compatible object store for self-host. Use R2 / S3 directly when on a cloud.'),
  'MinIO': T('excluded', 'AGPL-3.0', 'S3 storage', 'MinIO Inc', 'AGPL, and the community edition was wound down in 2025 in favour of the commercial AIStor product, whose pricing is enterprise-scale. Fails on both licence and pricing. Garage (AGPL) and Ceph (LGPL) are also out.', false, 'both'),
  'pgvector': T('core', 'PostgreSQL', 'Vector extension', 'pgvector', 'Vectors in Postgres; one engine for knowledge and state.'),
  'Qdrant': T(null, 'Apache-2.0', 'Vector database', 'Qdrant', 'Scale-out vector store. Milvus and LanceDB are further options.'),
  'ORAS + Harbor': T('core', 'Apache-2.0', 'OCI artifact registry', 'CNCF', 'Every promoted lever (prompts, configs, playbooks, images) as a versioned OCI artifact.', true),
  'Zot': T(null, 'Apache-2.0', 'OCI registry', 'Linux Foundation', 'Lighter registry alternate.'),
  // Cross-cutting
  'SPIRE': T(null, 'Apache-2.0', 'Workload identity', 'CNCF graduated', 'SPIFFE mTLS identity; multi-node and BYOC.'),
  'OpenCost': T(null, 'Apache-2.0', 'Cost allocation', 'CNCF', 'Kubernetes adapter only; the ledger is the platform\'s cost source of truth.'),
  'Presidio': T('core', 'MIT', 'PII detection', 'Microsoft', 'PII redaction inside the Collector pipeline.'),
  'Pulumi': T(null, 'Apache-2.0', 'Provisioning', 'Pulumi', 'Permissive IaC; cloud-init for nodes.'),
  'OpenTofu': T('excluded', 'MPL-2.0', 'Provisioning', 'Linux Foundation', 'MPL. Terraform is BUSL; Ansible is GPL.', false, 'licence'),
  'Sealed Secrets': T(null, 'Apache-2.0', 'Secrets bootstrap', 'Bitnami', 'Kubernetes-only bootstrap with the K3s adapter.')
};

export const standards = [
  { n: '1', name: 'ACP', sub: 'Editor ↔ coding agent · Zed, early', tools: ['Agent Client Protocol', 'Gemini CLI', 'Codex CLI'] },
  { n: '2', name: 'AG-UI', sub: 'Human UI ↔ agent events · CopilotKit', tools: ['AG-UI SDKs', 'Pydantic AI'] },
  { n: '3', name: 'A2A', sub: 'Agent ↔ agent · LF, v1.0 Mar 2026', tools: ['A2A SDK', 'agentgateway', 'Pydantic AI', 'Google ADK'] },
  { n: '4', name: 'MCP', sub: 'Agent ↔ tools · LF, spec 2025-11-25', tools: ['MCP SDKs', 'agentgateway', 'goose'] },
  { n: '5', name: 'AGENTS.md', sub: 'Workspace instructions · AAIF, 60k+ repos', tools: ['goose', 'Codex CLI', 'Agent Skills'] },
  { n: '6', name: 'CloudEvents', sub: 'Scheduled / internal / external events · CNCF v1.0', tools: ['CloudEvents SDKs', 'NATS'] },
  { n: '7', name: 'OCI / CRI / WASI', sub: 'Runtime boundary · sandboxes and artifacts', tools: ['Kata Containers', 'Wasmtime', 'ORAS + Harbor'] },
  { n: '8', name: 'in-toto / SLSA', sub: 'Provenance and SBOM · SPDX, CycloneDX', tools: ['in-toto', 'cosign', 'Trivy'] },
  { n: '9', name: 'OTel GenAI', sub: 'Span semantics · Development status, pin versions', tools: ['OTel Collector', 'OpenLIT'] },
  { n: '10', name: 'OpenFeature', sub: 'Promote / rollback flags · CNCF', tools: ['OpenFeature + flagd'] }
];

export const layers = [
  { key: 'entry', num: '1', title: 'Invocation / Entry Points', sub: 'External protocol → WorkRequest', challenges: [
    { title: 'Agentic gateway and normaliser', problem: 'LLM, MCP and A2A traffic through one gateway; the WorkRequest normaliser behind it is platform-specific.', picks: ['agentgateway'], alts: ['Envoy AI Gateway', 'Higress'], excluded: [], standards: ['A2A', 'MCP'], build: true },
    { title: 'Human entry', problem: 'UI, CLI and API callers with verified identity and AG-UI events.', picks: ['Keycloak', 'AG-UI SDKs'], alts: ['Zitadel', 'Agent Client Protocol'], excluded: [], standards: ['AG-UI', 'ACP'] },
    { title: 'Scheduled and event entry', problem: 'Scheduled, internal and external events in a standard envelope.', picks: ['CloudEvents SDKs'], alts: ['NATS'], excluded: [], standards: ['CloudEvents'] },
    { title: 'Agent-to-agent entry', problem: 'Other agents delegate over A2A; keep protocol churn behind the adapter.', picks: ['A2A SDK'], alts: [], excluded: [], standards: ['A2A'], hard: true }
  ] },
  { key: 'intake', num: '2', title: 'Orchestration & Control Plane', sub: 'WorkRequest → AgentTask', challenges: [
    { title: 'Durable workflow', problem: 'Owns workflow state: progression, retries, timers, budgets, approvals.', picks: ['Temporal'], alts: ['Hatchet', 'Kestra'], excluded: ['Windmill'], standards: [] },
    { title: 'Policy and secrets', problem: 'Budgets, guardrails, authZ evaluated before dispatch; secrets never handled by hand.', picks: ['Open Policy Agent', 'Infisical'], alts: ['Cedar', 'OpenFGA'], excluded: ['OpenBao'], standards: [] },
    { title: 'Intake, planning, placement', problem: 'Write the expectation event, then budget-aware planning, placement and crew strategy. The differentiation; no OSS.', picks: ['PostgreSQL'], alts: [], excluded: [], standards: [], build: true },
    { title: 'State and events', problem: 'Relational state, cache / leases and an event bus when needed.', picks: ['PostgreSQL'], alts: ['Valkey', 'NATS', 'Apache Kafka'], excluded: ['Redpanda'], standards: [] }
  ] },
  { key: 'agent', num: '3', title: 'Core Agent', sub: 'AgentTask → ExecutionRequest · sees only a sandbox handle', challenges: [
    { title: 'Harness profiles', problem: 'General workhorse, typed service and API-only captain profiles behind one contract.', picks: ['goose', 'Pydantic AI'], alts: ['workerd', 'OpenHands', 'Codex CLI', 'Gemini CLI', 'Aider'], excluded: [], standards: ['MCP', 'AGENTS.md'] },
    { title: 'Frameworks', problem: 'Building blocks for custom agents that speak the standards natively.', picks: ['Google ADK'], alts: ['OpenAI Agents SDK', 'Strands Agents', 'smolagents', 'LangGraph'], excluded: [], standards: ['A2A'] },
    { title: 'Model gateway', problem: 'One interface across providers with routing and per-task spend.', picks: ['agentgateway'], alts: ['Bifrost', 'Portkey Gateway', 'LiteLLM'], excluded: [], standards: [] },
    { title: 'Tools and workspace', problem: 'Capabilities through MCP; instructions and skills as conventions.', picks: ['MCP SDKs', 'Agent Skills'], alts: [], excluded: [], standards: ['MCP', 'AGENTS.md'] },
    { title: 'Local inference', problem: 'Self-hosted models for cost, privacy or latency.', picks: ['vLLM'], alts: ['SGLang', 'Ollama'], excluded: [], standards: [] }
  ] },
  { key: 'execute', num: '4', title: 'Execution & Runtime', sub: 'ExecutionRequest → ExecutionResult · two adapters, one contract', challenges: [
    { title: 'Direct microVM adapter', problem: 'Node controller + vsock executor over Firecracker: create, exec, snapshot, restore. Node 1 and snapshot density.', picks: ['Firecracker'], alts: ['Cloud Hypervisor', 'E2B Runtime', 'microsandbox'], excluded: ['Daytona'], standards: [], build: true },
    { title: 'Standards adapter', problem: 'K3s + containerd + Kata for OCI / CRI / CNI portability and autoscaling at scale-out.', picks: ['Kata Containers'], alts: ['gVisor', 'KEDA'], excluded: [], standards: ['OCI / CRI / WASI'] },
    { title: 'WASM profile', problem: 'Lightweight isolation for short tool runs.', picks: ['Wasmtime'], alts: ['WasmEdge'], excluded: [], standards: ['OCI / CRI / WASI'] },
    { title: 'Snapshot and recovery', problem: 'No permissive checkpoint / restore. Layer 2 replay plus layer 4 VM snapshots instead.', picks: ['Firecracker', 'Temporal'], alts: [], excluded: ['CRIU'], standards: [] },
    { title: 'Agent memory', problem: 'Runtime-owned memory store without leaking across tenants.', picks: ['Mem0'], alts: ['Letta', 'Graphiti', 'Cognee'], excluded: [], standards: [] }
  ] },
  { key: 'assure', num: '5', title: 'Assurance & Completion', sub: 'WorkProduct → Completion · deterministic → security → eval → admit → attest', challenges: [
    { title: 'Security gates', problem: 'Vulnerabilities, SBOM, misconfig and secrets on everything the agent produced.', picks: ['Trivy', 'Gitleaks'], alts: ['Syft + Grype'], excluded: ['Semgrep', 'TruffleHog'], standards: ['in-toto / SLSA'] },
    { title: 'Eval gate and guardrails', problem: 'Score against acceptance criteria; programmable rails at runtime.', picks: ['Inspect AI', 'NeMo Guardrails'], alts: ['Promptfoo', 'LLM Guard'], excluded: [], standards: [] },
    { title: 'Admission', problem: 'Final policy gate plus the admission score and acceptance contracts. Differentiation; no OSS.', picks: ['Open Policy Agent'], alts: [], excluded: [], standards: [], build: true },
    { title: 'Attest and register', problem: 'Every admitted artifact signed and traceable to inputs, model and sandbox.', picks: ['in-toto', 'cosign'], alts: [], excluded: [], standards: ['in-toto / SLSA'] }
  ] },
  { key: 'observe', num: '6', title: 'Observe', sub: 'All layers → LedgerEvent', challenges: [
    { title: 'Telemetry pipeline', problem: 'One trace from entry to completion; redact and route before egress.', picks: ['OTel Collector', 'OpenLIT'], alts: ['OpenLLMetry'], excluded: [], standards: ['OTel GenAI'] },
    { title: 'Expectation-vs-outcome ledger', problem: 'Append-only record every layer writes; six deterministic queries answer met-expectations, pain, budget. Schema is the build.', picks: ['ClickHouse'], alts: ['PostgreSQL'], excluded: [], standards: [], build: true },
    { title: 'Trace and eval UI', problem: 'Traces, evals and cost per trace on the same store as the ledger.', picks: ['OpenLIT'], alts: ['Opik', 'Langfuse'], excluded: ['Arize Phoenix'], standards: [] },
    { title: 'Metrics, dashboards, lineage', problem: 'Platform health and lineage backends.', picks: ['Prometheus'], alts: ['Perses', 'Jaeger', 'OpenLineage'], excluded: ['Loki / Tempo'], standards: [] }
  ] },
  { key: 'improve', num: '7', title: 'Self-Improvement', sub: 'LedgerEvent → PromotionCandidate → versioned artifact', challenges: [
    { title: 'Analyze and experiment', problem: 'SQL over the ledger, failure clustering, then candidates recorded as experiments.', picks: ['MLflow'], alts: ['Optuna', 'DSPy', 'TextGrad', 'Opik Agent Optimizer'], excluded: [], standards: [], build: true },
    { title: 'Evaluate blind', problem: 'Hidden holdout sets nobody can optimise against.', picks: ['Inspect AI'], alts: ['Promptfoo', 'Ragas', 'DeepEval'], excluded: [], standards: [] },
    { title: 'Promote and rollback', problem: 'Flag or canary rollout of a signed artifact; regression query flips it back. Threshold policy is the build.', picks: ['OpenFeature + flagd', 'ORAS + Harbor'], alts: ['cosign', 'Open Policy Agent'], excluded: [], standards: ['OpenFeature'], build: true }
  ] },
  { key: 'shared', num: '8', title: 'Shared Platform Services', sub: 'Consumed through service contracts · Git, S3 API, OCI Distribution', challenges: [
    { title: 'Source', problem: 'Git and worktrees agents and humans share.', picks: ['Gitea'], alts: [], excluded: ['Forgejo'], standards: ['AGENTS.md'] },
    { title: 'Artifacts', problem: 'S3 API. Self-host or use R2 / S3 directly.', picks: ['SeaweedFS'], alts: [], excluded: ['MinIO'], standards: [] },
    { title: 'Knowledge', problem: 'Embeddings and knowledge bases, partitioned per tenant.', picks: ['pgvector'], alts: ['Qdrant'], excluded: [], standards: [] },
    { title: 'Metadata', problem: 'Workflows, lineage, evaluations, catalog.', picks: ['PostgreSQL'], alts: [], excluded: [], standards: [] },
    { title: 'Registry', problem: 'Prompts, configs, playbooks and images as versioned OCI artifacts.', picks: ['ORAS + Harbor'], alts: ['Zot'], excluded: [], standards: ['OCI / CRI / WASI'] }
  ] },
  { key: 'cross', num: 'X', title: 'Cross-Cutting Concerns', sub: 'Apply across layers without owning layer function', challenges: [
    { title: 'Identity', problem: 'Workload mTLS and human identity.', picks: ['SPIRE', 'Keycloak'], alts: [], excluded: [], standards: [] },
    { title: 'Privacy and cost', problem: 'PII redaction in the pipeline; the ledger is the cost source of truth.', picks: ['Presidio'], alts: ['OpenCost'], excluded: [], standards: [] },
    { title: 'Provisioning', problem: 'Reproducible nodes and clusters across clouds.', picks: ['Pulumi'], alts: ['Sealed Secrets'], excluded: ['OpenTofu'], standards: [] }
  ] }
];
