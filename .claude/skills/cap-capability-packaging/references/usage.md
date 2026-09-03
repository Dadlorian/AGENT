# cap-capability-packaging: the caller's view

Proposed. Folded in from the former `cap-capability-packaging-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-capability-packaging` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 0 row(s) of that kind were dropped in the fold.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- Make packaging usable in three moves: write a directory with two fields to publish one, name an identity to use one, read one outcome to know what happened. Nothing else is required of a caller.  
  _sourced_ - `T-t3-01`, `X-entry-composition-035` "The simplest skill is a directory containing a SKILL.md file"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| publish (proposed): what a human does | a directory named after the capability, holding a package file whose frontmatter carries a name and a description | an identity that resolves; nothing else is registered, configured or declared (proposed) | proposed | - |
| use (proposed): what an agent does | one identity | the resident fields always, the body once the description matched the work in hand, a reference file only if a step said to open one (proposed) | proposed | - |
| refresh (proposed): what an event does | a notification that a package was published, changed or withdrawn, carrying the identity | the same resolution, re-run for that identity; no caller changes and nothing else is re-read (proposed) | proposed | - |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-capability-packaging` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a human publishes the smallest possible package

_proposed_ - sources: -.

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

### Worked example 2 (proposed): an agent names an identity that is not published

_proposed_ - sources: -.  Also carried in the body of `cap-capability-packaging` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-capability-packaging` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **To use one from an agent: name the identity and read what comes back. Do not join paths, open files, decide which tier to load, or cache anything yourself.**  
  _why:_ The tiers, the source and the transport are the capability's business, and a caller that reaches around them has bound itself to today's source and will break the first time the source changes.  
  _sourced_ - `T-t2-01` "Composability hides the complexity."
- **On an event that says a package was published, changed or withdrawn, re-resolve that one identity. Do not rebuild a local index and do not restart the caller.**  
  _why:_ An event is one of the three ways into the system, and it must reach this capability the same way a human or an agent does: by naming an identity.  
  _sourced_ - `T-t1-03` "An internal or external event must be able to enter the system."
- **Read the outcome's resolved member, and when it is false branch on the problem's type member. Show detail to a person; never parse it, key metrics on it, or match on its wording.**  
  _why:_ cap-errors owns the failure shape for the whole platform, and title and detail are written for readers and may be reworded without notice, while the type is the part a caller was promised.  
  _sourced_ - `F-b4-07` "Typed and machine-readable. Never parsed from prose"
- **When a package outgrows its body, move material down a tier into a reference file that a step in the body says to open; do not add a frontmatter field and do not split it into a second package.**  
  _why:_ cap-capability-packaging states the three tiers and what each one costs (X-cap-capability-packaging-005); what it means for a publisher is that moving material down a tier keeps an installed package cheap while it is not being used, whereas a new required field would be paid by every package rather than by this one.  
  _sourced_ - `X-cap-capability-packaging-005` "reference files only when needed"
- **Compose by handing the same identity to whatever loads it - a workflow step, a loop, an agent profile - rather than by copying the package into each consumer.**  
  _why:_ One identity in many places is what lets a package be improved once; a copy per consumer is a package that will be improved in one place and stale in the others.  
  _sourced_ - `T-t2-02` "enhancing particular aspects of any element without touching the rest"
- **Read the two worked examples above, then stop. Open cap-capability-packaging only if you have to judge whether something is conformant, and cap-capability-packaging-implement only if you are building a package source rather than using one.**  
  _why:_ One directory, two fields, one identity and one outcome is the whole consuming surface; loading the contract and the build guidance in order to publish a package is the kind of weight that stops a platform from being used at all.  
  _sourced_ - `T-t3-02` "It cannot be daunting or overly complex, or no one will use it."

## Other caller invariants

- cap-capability-packaging states the two required resident fields (X-entry-composition-035). What that buys a publisher: a name and a description are the entire obligation, so publishing a capability costs one directory and two lines rather than a registration step.  
  _sourced_ - `X-entry-composition-035` "a directory containing a SKILL.md file"
- The complexity is hidden on purpose: a caller never chooses a tier, a scan order, a transport or a digest. Those exist, and cap-capability-packaging-implement is where they are decided; none of them appears in what a caller writes.  
  _sourced_ - `T-t2-01` "Composability hides the complexity."
- Failure arrives as a problem details object, the same shape cap-errors defines for the whole platform, never as a file-not-found exception or a log line. A caller branches on the type member and reads retryable; it never string-matches a message.  
  _sourced_ - `F-b3-13` "RFC 9457 problem details"
- Proposed: there is nothing to switch on. A caller does not request packaging, cannot decline it, and has no packaging configuration to get wrong; the whole consuming surface is one identity in and one outcome out.  
  _proposed_ - -

## Caller practices

- cap-capability-packaging already states that the description is the trigger surface (X-cap-capability-packaging-001). What it buys a publisher: the description is the only thing anyone reads before deciding to load you, so name the situations and the phrasings a caller would actually use, not the ones you would.  
  _sourced_ - `X-cap-capability-packaging-001` "that Claude loads only when it's relevant to your task"
- cap-capability-packaging states that packages are published rather than copied (X-entry-composition-056). What it buys a consumer: name the identity and let the source resolve it, so an improvement to the package reaches you without a change on your side.  
  _sourced_ - `X-entry-composition-056` "a public registry of reusable"
- Proposed: do not retry an unresolved identity. A name that is not published is deterministic - it will not resolve on the second attempt either - and the problem body carries retryable false to say so.  
  _proposed_ - -
- Proposed: if writing the description is hard, the package is doing more than one thing. Split it before you publish it, because a description that has to cover two jobs will match the wrong one.  
  _proposed_ - -

## Open questions carried over

- **Should a consumer ever see which source served a package, and its digest?**  
  _deciding evidence:_ Count, across recorded resolutions, how often a caller would have behaved differently had it known the source or the digest. If it never would, both belong in the platform-side record keyed by the correlation identifier rather than in what a caller reads.  
  _default until then:_ Report both on the outcome and tell callers to read them only for reporting, never for branching. Removing a member later is cheaper than adding one after callers exist.  
  `T-t2-01` "Composability hides the complexity"

