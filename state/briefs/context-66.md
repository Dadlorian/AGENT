# Context for STATUS row 66: the litmus questionnaire (captain's context, read this and nothing else in the repo)

## Why this exists (owner, 2026-09-03)
A self-reflection on PASS.md B3 and B4: for each capability interface and each cross-cutting concern, state the idealistic future state a build could reach today, tool-agnostic where a standard allows it, and ask it from several angles, because how a standard is used matters more than whether it is used. Score each answer on a closed scale that separates absent from exists from directionally aligned, and marks alignment toward something that would not work as an error.

You are writing questions, not answers. Nothing you write may assume what has been built; you have not seen it and you must not look. Your inputs are this file and the web. Do not open .claude/, harness/, docs/ (other than docs/litmus/frame.json and your own part), kb/ceremonies/, examples/, state/ (other than this file and state/briefs/litmus.md), README.md, STATUS.md or any other file in the repo. The check tool refuses any text that names something this repo built, and you would not know those names anyway.

Window: 2026-03-03 to 2026-09-03 (the state of technology in the last six months; what could be developed right now). Everything you say about direction is about this window; cite a research record for it.

## The frame

Angles (a section needs at least 4 of the six, always including depth and usage; 4 to 8 questions):
- `presence`: Is the standard or interface present at all? The single litmus test; never sufficient on its own.
- `depth`: Are the standard's distinguishing mechanisms in use, the ones that separate real adoption from a label?
- `boundary`: Does the element sit behind a capability interface with a proven second adapter, so the core imports the interface and never the implementation?
- `guarantees`: Do the cross-cutting concerns ride on this element without the caller asking, and which ones apply here?
- `usage`: How does a caller use it across every entry (human, event, schedule, external), and how does it compose with the other elements?
- `direction`: Is the build aligned with where the standard and its ecosystem are heading inside the window, and what would be an error to build now?

Scale an answerer will score each question on (you write what aligned and misaligned look like so the score is decidable from evidence):
- -1 `misaligned`: Built toward something that would not work, or against where the standard is going. An error to correct, not a gap to fill.
- 0 `absent`: Nothing exists for this question.
- 1 `exists`: Something exists, but its use is nominal or its direction cannot be judged from the evidence.
- 2 `aligned`: Exists and is directionally aligned with the future state stated for the section.
- 3 `leading`: At or beyond the future state stated for the section, with the evidence to show it.

Settledness of a standard (say which and why, from research):
- `baseline`: The standard is the principled baseline with no credible competitor; the question is how deeply it is used.
- `contested`: Two or more candidates are live; the future state names the property to hold, not the winner.
- `emerging`: The direction is visible but no standard has settled; the future state names the direction and the exit if it changes.
- `none`: PASS.md records no standard; the future state is original design held to the B5 specification.

Tool-agnostic where possible: a future state and a question name capabilities and standards, never products. A product may appear only in standard.why and direction.text, as evidence of where the ecosystem is going. Where a standard is the principled baseline (the owner's example is OpenTelemetry), do not look for a competitor; ask how deeply and how well it is used, because how a standard is used matters more than whether it is used.

## PASS.md Part B, verbatim, with the knowledge-base id of every row (cite these ids)

### B1. Design rules
- `F-b1-01`: These are the rules that produce flexibility. Everything downstream is a consequence.
- `F-b1-02`: 1. **Every external dependency sits behind a capability interface.** The core imports interfaces, never implementations.
- `F-b1-03`: 2. **Each interface names the standard that governs it.** Where a standard exists, adopt it whole rather than modelling our own shape.
- `F-b1-04`: 3. **Swappability is a tested property, not an intention.** Every interface ships with at least two adapters, and the second exists to prove the first is not load-bearing.
- `F-b1-05`: 4. **A caller needs no client library we wrote.** If integration requires our SDK, a boundary is bespoke where a standard existed.
- `F-b1-06`: 5. **Cost is knowable before commitment.** Planning is a pure function and completes before execution begins.
- `F-b1-07`: 6. **The grader is never visible to the graded.** An agent sees its outcome, never the criterion it is judged against.
- `F-b1-08`: 7. **Cross-cutting guarantees are not optional.** Telemetry, policy, provenance and budget are applied by the platform, not requested by the caller.

### B2. The core
- `F-b2-01`: Five components. Zero outward dependencies. Each earns its place by what breaks without it.
- `F-b2-02`: | **Document** | data — declared intent, definition of done, steps | nothing is declarable |
- `F-b2-03`: | **Planner** | pure function `document → plan + cost` | nothing is pricable before it is spent |
- `F-b2-04`: | **Graph** | typed nodes, typed edges (existence / interface / implementation) | nothing composes |
- `F-b2-05`: | **Judge** | pure function `(result, criterion) → verdict` | "done" becomes an opinion |
- `F-b2-06`: | **Ledger** | append-only across runs; the deduplication authority | nothing survives the run |
- `F-b2-07`: This is the entire owned surface. Everything else is an adapter.

### B3. Capability interfaces (one section per row F-b3-02 to F-b3-17)
- `F-b3-01`: **The middle column is the contract. The right two columns prove it is swappable.**
- `F-b3-02`: | **Isolation** | OCI Runtime Spec | Firecracker microVM | gVisor · Kata Containers · Cloud Hypervisor · hosted sandbox services |
- `F-b3-03`: | **Model access** | OpenAI-compatible completions | LiteLLM | OpenRouter · direct provider SDKs · vLLM/SGLang native |
- `F-b3-04`: | **Durable execution** | — *(no standard; see B5)* | Temporal | Restate · DBOS · Inngest · a queue plus a state machine |
- `F-b3-05`: | **Agent runtime** | Agent Client Protocol | goose | Claude Code · Cursor · any ACP-speaking agent |
- `F-b3-06`: | **Tool access** | Model Context Protocol | MCP endpoint | any MCP server |
- `F-b3-07`: | **Capability packaging** | Agent Skills spec | skill files | any spec-conformant registry |
- `F-b3-08`: | **Work intake** | A2A messaging · CloudEvents | CLI, git event, HTTP, schedule | any conformant producer |
- `F-b3-09`: | **Document validation** | JSON Schema 2020-12 | in place | any 2020-12 validator |
- `F-b3-10`: | **Telemetry** | OTLP · GenAI semantic conventions | Langfuse + OpenTelemetry | Phoenix · Braintrust · any OTLP collector |
- `F-b3-11`: | **Policy** | Rego / OPA | OPA | Cedar · any policy engine with a decision API |
- `F-b3-12`: | **Provenance** | in-toto · SLSA · DSSE | JSONL evidence records | Sigstore · any attestation store |
- `F-b3-13`: | **Errors** | RFC 9457 problem details | *absent* | — adopt the RFC directly |
- `F-b3-14`: | **Identity** | OAuth 2.0 Token Exchange · workload identity | *absent* | SPIFFE/SPIRE · any OIDC provider |
- `F-b3-15`: | **Scheduling** | RFC 5545 recurrence rules | Temporal schedules | cron · any RFC 5545 parser |
- `F-b3-16`: | **Idempotency** | idempotency-key convention | key on the wire, no lease | any keyed lease store |
- `F-b3-17`: | **State persistence** | — *(no standard; see B5)* | JSONL + hash chain | object store · relational · event log |
- `F-b3-18`: **Read the Isolation row as the template for the whole table.** Firecracker is excellent and stays. But the architecture says *"a unit of work runs isolated, per the OCI Runtime Spec"* — and satisfies that with Firecracker today. When a workload needs faster cold start, or needs to run somewhere we do not own hardware, the adapter changes and the core does not.

### B4. Cross-cutting concerns, applied not requested (one section per row F-b4-02 to F-b4-08)
- `F-b4-01`: These are the difference between a working system and a production one. The platform applies each; a caller cannot decline them.
- `F-b4-02`: | **Budget** | Every unit of work carries a ceiling. Exceeding it terminates the unit, not the platform |
- `F-b4-03`: | **Identity** | Every action names an actor, including delegated agent actors. Delegation chains are explicit |
- `F-b4-04`: | **Policy** | Refusal is deterministic and happens before execution, not after spend |
- `F-b4-05`: | **Provenance** | Every artifact is attributable to the code version, inputs and actor that produced it, verifiable with a tool we did not write |
- `F-b4-06`: | **Telemetry** | Correlation rides on explicit attributes, not trace parentage — see A7 finding 1 |
- `F-b4-07`: | **Errors** | Typed and machine-readable. Never parsed from prose |
- `F-b4-08`: | **Idempotency** | Every externally-triggered action is safe to replay |

### B5. What we must design ourselves (the two rows in B3 with no standard point here)
- `F-b5-01`: Two boundaries have no standard to adopt. **They are the only places original design effort is warranted, and they carry the weight of the platform.**
- `F-b5-02`: **Dispatch** — one unit of agent work executes and returns one result.
- `F-b5-03`: Today there are three implementations and no contract between them. This is the seam that decides whether agent execution is pluggable at all. It must specify: the request shape, the result shape, cancellation semantics, timeout and budget enforcement, partial-result handling, and what a failure returns.
- `F-b5-04`: **State** — the graph and the ledger persist.
- `F-b5-05`: Today a JSONL file with a hash chain. The chain is the valuable idea and should survive; the file is not. This must specify: the write model, concurrency and single-writer guarantees, the integrity mechanism, retention, and the query surface a planner needs.
- `F-b5-06`: Everything else in B3 is a decision someone else already published. These two are ours.

A concern section (B4) asks whether the guarantee rides on every unit of work through every entry without being requested; a capability section (B3) asks about the interface, its standard and its adapters. The same word (identity, policy, provenance, telemetry, errors, idempotency) appears in both tables on purpose; write the two sections so each asks what the other does not.

## What one section is (JSON, one object per row; your part file is {"sections": [...]})

```json
{
  "id": "<fixed id from the table in state/briefs/litmus.md>",
  "kind": "capability | concern",
  "source": "F-b3-10",
  "name": "Telemetry",
  "standard": {"name": "OTLP · GenAI semantic conventions", "settledness": "baseline", "why": "...from research, products allowed here...", "cites": ["X-litmus-b-004"]},
  "future_state": {"text": "What a build inside the window should be doing with this element, in capabilities and standards. Say proposed when it is your synthesis.", "origin": "sourced | proposed", "cites": ["F-b3-10", "X-litmus-b-004"], "quote": "verbatim substring of one cited record, required when sourced"},
  "direction": {"text": "Where the standard and its ecosystem are heading inside the window; what is settling, what is being abandoned. Products allowed as evidence.", "origin": "sourced | proposed", "cites": ["X-litmus-b-005"], "quote": "..."},
  "questions": [
    {"id": "telemetry-q1", "angle": "depth", "question": "...", "evidence_expected": "what an answerer must produce: an artifact, a trace, a command output, a configuration; tool-agnostic", "aligned_looks_like": "...", "misaligned_looks_like": "...", "origin": "proposed", "cites": ["F-b3-10", "F-b4-06"]}
  ],
  "gaps": [{"claim": "what you could not source", "research_query": "the query that would"}]
}
```

Citation rules: `origin: sourced` needs a `quote` that is a verbatim substring of one cited record's text (F-, T-) or snippet (X-). Copy it; never retype. `origin: proposed` text contains the word proposed. Questions are usually proposed (they are the owner's design, derived from the row) and cite the F- row they derive from plus the X- records that name the mechanism they ask about. Every id you cite must exist: the F- ids above, or X- ids you create.

## Research records (one file: kb/research/litmus-<part>.jsonl, one JSON object per line)

Each web search you rely on becomes one record. Fields, all required unless noted: id `X-litmus-<part>-NNN` (NNN from 001, contiguous), type "research", lens `litmus-<part>`, topic (the section id), informs (list of F- ids), query, url, title, snippet (verbatim from the search result), read (null; page fetch is blocked in this environment), status "search-only", claim (one sentence, optional), agent (your model), date "2026-09-03". Never invent a url, title or version. A search that found nothing becomes a gap in the section, with the query.

Search, per section: the standard's current version and activity in the window; the mechanisms that separate deep use from nominal use; where the ecosystem is heading and what is being abandoned; whether a credible alternative exists (settledness); what production users of hundreds of agents are doing with it.

## Check your part

`python3 tools/litmus_check.py check docs/litmus/parts/<part>.json` must print `... 0 errors` before you finish. It checks the shape, the fixed ids, the angle coverage, that every cited id resolves, that every quote is verbatim, and that no text names a product outside standard.why and direction.text or anything this repo built.
