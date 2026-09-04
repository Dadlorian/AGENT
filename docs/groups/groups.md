# Domain groups

Draft (proposed) from PASS.md B3, B4 and B5. Groups follow what one unit of work meets, in the order it meets it.

| Group | Asks | Capabilities | Standards that must interoperate | Example |
|---|---|---|---|---|
| Entry | How does work arrive, and is it well-formed? | work-intake, document-validation, scheduling, human-interaction | CloudEvents, A2A, JSON Schema 2020-12, RFC 5545 | `examples/entry` |
| Cell | How does one unit of work execute, contained, with a model and tools, and return one result? | isolation, agent-runtime, tool-access, capability-packaging, model-access | OCI Runtime Spec, Agent Client Protocol, Model Context Protocol, Agent Skills, OpenAI-compatible completions | `examples/cell` |
| Continuity | How does work survive a crash, a retry and time? | durable-execution, state-persistence, idempotency | none (B5 design), idempotency-key convention | `examples/continuity` |
| Assurance | What does the platform apply that a caller cannot decline, and what does a refusal look like? | identity, policy, errors, budget, identity, policy, errors, idempotency | OAuth 2.0 Token Exchange, workload identity, Rego / OPA, RFC 9457 | `examples/assurance` |
| Evidence | What survives the run that a stranger can verify, and how is done decided? | telemetry, provenance, evaluation, telemetry, provenance | OTLP, GenAI semantic conventions, in-toto, SLSA, DSSE | `examples/evidence` |
| Composition | How are units wired into workflows, loops, panels and an improving system? |  | none (operators are this platform's closed set) | `examples/composition` |

## Information flow

One envelope enters at the door and its correlation id, actor chain, budget and idempotency key ride every hop; the contract hash and the cell's containment report join at execution; checkpoints and leases join in continuity; each guarantee stamps a decision; telemetry, the problem object and the attestation carry the same ids out. The standards that make this one flow: CloudEvents and A2A for the envelope, W3C trace context carried as explicit attributes for correlation, RFC 9457 for every failure, DSSE and in-toto for what survives.

