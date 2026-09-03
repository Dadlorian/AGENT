---
name: cap-capability-packaging-use
description: How to publish and use a packaged capability without knowing how packages are stored: one directory and two fields to publish, one identity to consume, one outcome to read. Load it when you are about to add a reusable unit to this platform, when a caller needs something a package provides, when an event says a package changed, when someone asks 'what is the least I have to write for this to be found', 'how do I use one from my agent', or 'what comes back when the thing is not there', and before anyone joins a path or reads a package file directly.
---

# cap-capability-packaging-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Make packaging usable in three moves: write a directory with two fields to publish one, name an identity to use one, read one outcome to know what happened. Nothing else is required of a caller. | sourced | `T-t3-01`, `X-entry-composition-035` "The simplest skill is a directory containing a SKILL.md file" |

## Entities

| Entity |
|---|
| `E-capability-capability-packaging` |
| `E-standard-agent-skills-spec` |
| `E-standard-rfc-9457-problem-details` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| publish (proposed): what a human does | a directory named after the capability, holding a package file whose frontmatter carries a name and a description | an identity that resolves; nothing else is registered, configured or declared (proposed) | proposed | - |
| use (proposed): what an agent does | one identity | the resident fields always, the body once the description matched the work in hand, a reference file only if a step said to open one (proposed) | proposed | - |
| refresh (proposed): what an event does | a notification that a package was published, changed or withdrawn, carrying the identity | the same resolution, re-run for that identity; no caller changes and nothing else is re-read (proposed) | proposed | - |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a human publishes the smallest possible package** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-packaging:example:publish",
  "title": "Two fields and a body is a publishable package",
  "description": "The author creates the directory `incident-triage/` holding one package file whose frontmatter is exactly `name: incident-triage` and a description saying when to load it. Nothing is registered by hand; the identity is the directory name.",
  "examples": [
    {
      "identity": "incident-triage",
      "resident": {
        "name": "incident-triage",
        "description": "Triage a production incident from an alert body: name the failing component, the fault family and the repro command. Load it when an alert arrives, when someone asks what broke, or before opening an incident record."
      },
      "body": "SKILL.md",
      "references": [],
      "resolved": true,
      "source": "directory",
      "tiers_loaded": [
        "resident"
      ]
    }
  ]
}
```

**Worked example 2 (proposed): an agent names an identity that is not published** (proposed; sources: -)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-packaging:example:unresolved",
  "title": "An unresolved identity comes back as a problem, not an exception",
  "description": "The agent asked for `incident-triarge`. The outcome carries resolved false and an RFC 9457 problem details body. The caller branches on type, shows detail to a person, and does not retry. `urn:agentic:problem:package-unresolved` is proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns; until that row lands an implementation returns the registered `document-invalid` with the unresolved identity in detail rather than minting a suffix at the call site.",
  "examples": [
    {
      "identity": "incident-triarge",
      "resolved": false,
      "source": "directory",
      "tiers_loaded": [],
      "problem": {
        "type": "urn:agentic:problem:package-unresolved",
        "title": "No package carries that identity",
        "status": 404,
        "detail": "no package named 'incident-triarge' under the configured source; the nearest published identity is 'incident-triage'",
        "retryable": false,
        "correlation_id": "run-2026-09-03-0011"
      }
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Three ways in, one identity. TARGET T1's three ways in are a human, an agent and an event - which is a different enumeration from T6.2's four entries - and all three name the same identity and get the same package back. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "An internal or external event must be able to enter the system." |
| cap-capability-packaging states the two required resident fields (X-entry-composition-035). What that buys a publisher: a name and a description are the entire obligation, so publishing a capability costs one directory and two lines rather than a registration step. | sourced | `X-entry-composition-035` "a directory containing a SKILL.md file" |
| Enhancing one aspect leaves the rest untouched: rewriting a body, adding a reference file, versioning a package or moving it from a directory to a registry changes nothing in a caller that named an identity, because the identity is the only thing it was ever asked to write down. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The complexity is hidden on purpose: a caller never chooses a tier, a scan order, a transport or a digest. Those exist, and cap-capability-packaging-implement is where they are decided; none of them appears in what a caller writes. | sourced | `T-t2-01` "Composability hides the complexity." |
| Failure arrives as a problem details object, the same shape cap-errors defines for the whole platform, never as a file-not-found exception or a log line. A caller branches on the type member and reads retryable; it never string-matches a message. | sourced | `F-b3-13` "RFC 9457 problem details" |
| Proposed: there is nothing to switch on. A caller does not request packaging, cannot decline it, and has no packaging configuration to get wrong; the whole consuming surface is one identity in and one outcome out. | proposed | - |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | To publish: make a directory named after the capability, put a package file in it whose frontmatter carries a name equal to the directory and a description saying when to load it, and write the working text in the body. Stop there. | cap-capability-packaging states that the two resident fields are the whole requirement; anything more you add is optional, and anything you add because it felt incomplete becomes a cost every future package pays. | sourced | `X-entry-composition-035` "YAML frontmatter that includes required metadata" |
| 2 | To use one from an agent: name the identity and read what comes back. Do not join paths, open files, decide which tier to load, or cache anything yourself. | The tiers, the source and the transport are the capability's business, and a caller that reaches around them has bound itself to today's source and will break the first time the source changes. | sourced | `T-t2-01` "Composability hides the complexity." |
| 3 | On an event that says a package was published, changed or withdrawn, re-resolve that one identity. Do not rebuild a local index and do not restart the caller. | An event is one of the three ways into the system, and it must reach this capability the same way a human or an agent does: by naming an identity. | sourced | `T-t1-03` "An internal or external event must be able to enter the system." |
| 4 | Read the outcome's resolved member, and when it is false branch on the problem's type member. Show detail to a person; never parse it, key metrics on it, or match on its wording. | cap-errors owns the failure shape for the whole platform, and title and detail are written for readers and may be reworded without notice, while the type is the part a caller was promised. | sourced | `F-b4-07` "Typed and machine-readable. Never parsed from prose" |
| 5 | When a package outgrows its body, move material down a tier into a reference file that a step in the body says to open; do not add a frontmatter field and do not split it into a second package. | cap-capability-packaging states the three tiers and what each one costs (X-cap-capability-packaging-005); what it means for a publisher is that moving material down a tier keeps an installed package cheap while it is not being used, whereas a new required field would be paid by every package rather than by this one. | sourced | `X-cap-capability-packaging-005` "reference files only when needed" |
| 6 | Compose by handing the same identity to whatever loads it - a workflow step, a loop, an agent profile - rather than by copying the package into each consumer. | One identity in many places is what lets a package be improved once; a copy per consumer is a package that will be improved in one place and stale in the others. | sourced | `T-t2-02` "enhancing particular aspects of any element without touching the rest" |
| 7 | Read the two worked examples above, then stop. Open cap-capability-packaging only if you have to judge whether something is conformant, and cap-capability-packaging-implement only if you are building a package source rather than using one. | One directory, two fields, one identity and one outcome is the whole consuming surface; loading the contract and the build guidance in order to publish a package is the kind of weight that stops a platform from being used at all. | sourced | `T-t3-02` "It cannot be daunting or overly complex, or no one will use it." |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| cap-capability-packaging already states that the description is the trigger surface (X-cap-capability-packaging-001). What it buys a publisher: the description is the only thing anyone reads before deciding to load you, so name the situations and the phrasings a caller would actually use, not the ones you would. | sourced | `X-cap-capability-packaging-001` "that Claude loads only when it's relevant to your task" |
| cap-capability-packaging states that packages are published rather than copied (X-entry-composition-056). What it buys a consumer: name the identity and let the source resolve it, so an improvement to the package reaches you without a change on your side. | sourced | `X-entry-composition-056` "a public registry of reusable" |
| Proposed: do not retry an unresolved identity. A name that is not published is deterministic - it will not resolve on the second attempt either - and the problem body carries retryable false to say so. | proposed | - |
| Proposed: if writing the description is hard, the package is doing more than one thing. Split it before you publish it, because a description that has to cover two jobs will match the wrong one. | proposed | - |

## Definition of done

| Field | Value |
|---|---|
| Criterion | The smallest package, end to end, from the repository root: create a directory holding a package file whose frontmatter carries only a name equal to the directory and a description, then run the proposed packaging tool `python3 tools/conformance_capability_packaging.py --root .claude/skills --identity <name> --resolve --report out/packaging-use.json`. It asserts required_field_missing == 0 for that identity, resolved == true, and tiers_loaded == ["resident"] before any trigger has matched. |
| Expected | exit 0 and one line reading `identity=<name> resolved=true required_field_missing=0 tiers_loaded=[resident]`. |
| Deliberate breakage | Delete the description line from that package's frontmatter, leaving the name and the body untouched. |
| Expected failure | exit non-zero with `identity=<name> resolved=false required_field_missing=1`, and the outcome carries a problem details body whose type is the packaging-nonconformant URI and whose detail names the missing field `description`. The body is still readable prose, which is the useful part: a caller that had string-matched the old message would have seen a sentence and missed the contract. |
| Status | claimed |
| Evidence | `F-part-c-04`, `X-entry-composition-035` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `cap-capability-packaging`, `cap-capability-packaging-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Should a consumer ever see which source served a package, and its digest? | Count, across recorded resolutions, how often a caller would have behaved differently had it known the source or the digest. If it never would, both belong in the platform-side record keyed by the correlation identifier rather than in what a caller reads. | Report both on the outcome and tell callers to read them only for reporting, never for branching. Removing a member later is cheaper than adding one after callers exist. | `T-t2-01` "Composability hides the complexity" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-capability-packaging 2831cb4f, 2026-09-03 |
