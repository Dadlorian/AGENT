---
name: cap-capability-packaging
description: The capability-packaging contract: one portable directory shape any conformant runtime can discover, two required resident fields, three load tiers, and the criteria that decide whether a candidate loader or registry may serve. Load it before you add a skill, workflow, loop or agent as a reusable unit, when deciding what belongs in frontmatter versus the body versus reference files, when someone asks 'how would another runtime find this', 'why does this only load sometimes', 'what does a conformant package have to contain', or 'can we serve these from a registry instead', and whenever a composable unit is about to be copied between repositories rather than published.
---

# cap-capability-packaging

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Fix one contract for packaging a capability as a portable directory that a runtime we did not write can discover and load, so the core imports the packaging interface and the directory layout stays an adapter. | sourced | `F-b3-07`, `F-b3-01` "The right two columns prove it is swappable." |

## Entities

| Entity |
|---|
| `E-capability-capability-packaging` |
| `E-standard-agent-skills-spec` |
| `E-adapter-skill-files` |
| `E-swap-candidate-any-spec-conformant-registry` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-agent-skills-spec` | no published version string; recorded as unversioned | unverified | https://agentskills.io/specification | `F-b3-07`, `X-end-to-end-024`, `X-end-to-end-025` |

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| list_resident | the package roots a runtime is configured to search | one entry per package carrying its identity and the two required resident fields, name and description, and nothing else | sourced | `X-entry-composition-035` "required metadata: name and description" |
| resolve | a package identity | the package root that identity names, located the same way whether it sits in a directory the runtime scans or in a registry entry carrying the same identity | sourced | `X-end-to-end-024` "load from a well-known directory" |
| load_body | a package identity plus the trigger that matched its description | the package body, read on activation rather than at startup | sourced | `X-cap-capability-packaging-005` "the full SKILL.md body on activation" |
| open_reference | a package identity and one reference path the package declares | that reference file's content, read at the moment it is needed and not before | sourced | `X-cap-capability-packaging-005` "reference files only when needed" |
| check_package (call name is ours; the two required fields it checks are the standard's) | a package root | a conformance outcome: whether the package file exists, whether its frontmatter carries the two required fields, and whether the identity it declares matches the directory that holds it (proposed) | sourced | `X-entry-composition-035` "required metadata: name and description" |

### Shapes (JSON Schema 2020-12)

**capability-package (the required members are the standard's two resident fields plus a body; the optional directories are this platform's own tiering, in references/packaging-shapes.md)** (sourced; sources: `X-entry-composition-035`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-packaging:package:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "identity",
    "resident",
    "body"
  ],
  "properties": {
    "identity": {
      "type": "string",
      "minLength": 1
    },
    "resident": {
      "type": "object",
      "additionalProperties": false,
      "required": [
        "name",
        "description"
      ],
      "properties": {
        "name": {
          "type": "string",
          "minLength": 1
        },
        "description": {
          "type": "string",
          "minLength": 1
        }
      }
    },
    "body": {
      "type": "string",
      "minLength": 1
    },
    "references": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "scripts": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "assets": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

**package-resolution-outcome (tiers_loaded reflects the standard's three load tiers; source distinguishes this platform's two adapters; the failure members are in references/packaging-shapes.md)** (sourced; sources: `X-cap-capability-packaging-005`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-packaging:resolution:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "identity",
    "resolved",
    "source",
    "tiers_loaded"
  ],
  "properties": {
    "identity": {
      "type": "string"
    },
    "resolved": {
      "type": "boolean"
    },
    "source": {
      "enum": [
        "directory",
        "registry"
      ]
    },
    "digest": {
      "type": [
        "string",
        "null"
      ]
    },
    "tiers_loaded": {
      "type": "array",
      "items": {
        "enum": [
          "resident",
          "body",
          "reference"
        ]
      },
      "uniqueItems": true
    }
  }
}
```

**Worked example 2 (proposed): an agent names an identity that is not published [caller's view, folded from cap-capability-packaging-use]** (proposed; sources: -)

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
| The capability is the contract and the layout is the adapter: what the core imports is 'a capability is packaged as a portable directory a conformant runtime discovers and loads', governed by the Agent Skills spec, and the two right-hand columns exist to prove that layout can be replaced. | sourced | `F-b3-07`, `F-b3-01` "The right two columns prove it is swappable." |
| A package carries exactly two required fields resident: a name and a description. Anything else a runtime needs is optional, and a package that requires more than those two to be listed has stopped being the minimum unit. | sourced | `X-entry-composition-035` "The simplest skill is a directory containing a SKILL.md file that starts with YAML frontmatter that includes required metadata: name and description." |
| Loading is tiered, not all-or-nothing: name and description at startup, the body when the description matches a trigger, reference files only at the moment they are used. A package that has to be read whole to be considered has broken the tiering. | sourced | `X-cap-capability-packaging-005` "Agents load skills in three tiers: name + description at startup (~100 tokens per skill), the full SKILL.md body on activation (recommended under 5,000 tokens), and reference files only when needed." |
| The unit is a portable folder, not a runtime extension: a package adds capability to an agent that has never seen it, and requires no change to the agent that loads it. | sourced | `X-cross-structure-062` "portable folders that any AI agent can discover and use" |
| build-skill-authoring already states the swap class for this row (F-b3-07). The consequence stated here is this skill's own and proposed - a separation of checks: the packaging check asserts only what the specification requires, and this repository's link and manifest conventions are a second check layered on top, so a package that passes the first is loadable by a runtime that has never heard of the second. | sourced | `F-b3-07` "spec-conformant registry" |
| cap-document-validation already states the contract for checking a declared shape (F-b3-09). The consequence stated here is this skill's own and proposed: frontmatter conformance is decided by that capability against a published schema, never by a parser written inside the loader, because a loader that decides its own conformance cannot be swapped without renegotiating what conformance means. | sourced | `F-b3-09` "Document validation" |
| Proposed: one packaging shape covers every composable unit this platform ships - a skill, a workflow, a bounded loop, an agent profile - rather than one shape per kind, because a second shape doubles what a runtime must implement to load anything at all. Research query: does the Agent Skills spec, or any adjacent proposal on file, extend its one shape to a workflow or an agent profile, or is that generalisation ours alone? | proposed | - |
| cap-errors owns the failure shape for the whole platform (F-b3-13, adopted directly rather than redesigned). The consequence here is that this interface adds no failure vocabulary of its own: a package that cannot be found, cannot be read, or fails frontmatter conformance comes back as a problem details object on the resolution outcome, never as a runtime exception or a bare string. | sourced | `F-b3-13` "— adopt the RFC directly" |
| All three of TARGET T1's ways in - a human, an agent, an internal or external event - reach this capability the same way, and enhancing one aspect of it leaves the rest untouched: rewriting a body, adding a reference file, versioning a package or moving it from a directory to a registry changes nothing in a caller that named an identity, because the identity is the only thing it was ever asked to write down. cap-document-validation states the same record (T-t2-02) for its own boundary; this row is that rule's consequence here. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03`, `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: the loader's context accounting, its trigger-matching strategy and its scan order. A package that behaves correctly only under one matching strategy has bound itself to one runtime. Research query: does the Agent Skills spec name a matching or scan-order algorithm as part of the contract, which would mean this exclusion is confirming a documented boundary rather than inventing one? | proposed | - |
| The distribution transport and the on-disk path below the package root. A caller names an identity; whether it arrived over a filesystem or a network is the adapter's business. | sourced | `X-cap-capability-packaging-004` "uses namespace/name identity with reverse-DNS and supports both git and OCI distribution" |
| The criterion a packaged capability's output will be judged against is never a field of the package manifest, of a trigger declaration or of anything the loader hands the package at discovery time. agentic-stack and cap-document-validation both state design rule 6 (F-b1-07); the consequence here is that a package declares what it is good at and what loads it, never how its results will be scored. | sourced | `F-b1-07` "An agent sees its outcome, never the criterion it is judged against." |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | State the boundary as a capability plus its standard before any layout is named: 'a capability is packaged as a portable directory a conformant runtime discovers and loads, per the Agent Skills spec, version unverified'. Read the row the way the table's template row is read. | The contract has to survive the layout, so that when packaging needs change the adapter changes and the core does not. | sourced | `F-b3-07`, `F-b3-18` "Read the Isolation row as the template for the whole table." |
| 2 | Require exactly two fields in a package's frontmatter, a name and a description, and reject any proposal to make a third one required. | Two fields is the whole entry cost of publishing a capability; every field added to the required list is paid by every package that will ever exist, including the ones written by people who do not work here. | sourced | `X-entry-composition-035` "required metadata: name and description" |
| 3 | Assign every piece of a package to one of the three tiers as you write it: identity and trigger resident, the working instructions in the body, everything long in reference files that are opened on use. | The tiering is what keeps a large collection of packages affordable to have installed: a package that is not being used should cost its name and its description and nothing more. | sourced | `X-cap-capability-packaging-005`, `X-entry-composition-036` "reference files load only when needed" |
| 4 | Validate frontmatter through the document-validation capability against a published schema, and let that capability report every violation; do not hand-roll a frontmatter parser inside the loader. | cap-document-validation owns checking a declared shape (F-b3-09), and reusing it is what keeps the packaging check identical across every adapter that serves this interface. | sourced | `F-b3-09` "any 2020-12 validator" |
| 5 | Record the standard's version as unverified and write no version string that was not read: the format is published as an open standard but not as an explicitly versioned artifact, so name the specification and its URL instead. | build-skill-authoring requires a standard's version to be cited rather than guessed (F-part-c-10); where no version exists to cite, the honest record is the specification's identity plus unverified. | sourced | `X-end-to-end-025`, `X-cap-capability-packaging-002` "Anthropic does not currently publish the skill format as an explicitly versioned artifact." |
| 6 | Choose the second adapter on a different distribution model, not a second directory: an entry format with namespace-scoped identity, served from a registry over a network, with distribution as an addressable artifact. | build-adapter-pair owns this discipline (F-b1-04). The consequence here is specific: two filesystem layouts would leave the interface free to keep assuming a local path, and only a fetched package forces identity, integrity and versioning to become contractual rather than incidental. | sourced | `X-cap-capability-packaging-004`, `F-b1-04` "uses namespace/name identity with reverse-DNS and supports both git and OCI distribution" |
| 7 | Package every composable unit this platform ships in the same shape, and publish packages to a registry rather than copying directories between repositories. | Proposed on the first half: one shape for skills, workflows, loops and agent profiles keeps a runtime's loader singular. The second half is what makes reuse survive the second repository, the way a public registry of reusable modules does for composable build logic. | sourced | `X-entry-composition-056` "a public registry of reusable Dagger modules" |
| 8 | To publish: make a directory named after the capability, put a package file in it whose frontmatter carries a name equal to the directory and a description saying when to load it, and write the working text in the body. Stop there. | This skill states that the two resident fields are the whole requirement; anything more you add is optional, and anything you add because it felt incomplete becomes a cost every future package pays. | sourced | `X-entry-composition-035` "YAML frontmatter that includes required metadata" |
| 9 | Proposed: open references/packaging-shapes.md when you are implementing the package shape, assigning content to tiers, or reviewing someone who did. The body of this skill is enough to judge and to call the capability without it. Open references/usage.md instead when you are calling this capability rather than serving it: it carries the caller's minimal inputs and outputs, the two worked calls and the worked rejection in full. The body of this skill is enough to call it without either file. | Proposed: the full shape and the tier assignment table are longer than the body's budget allows, and a reader deciding whether to package something does not need them. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| agentic-stack already states the green-gate finding (F-a7-03). What it adds here, as this skill's own consequence and proposed: a package whose frontmatter parses is well-formed, not useful - conformance says nothing about whether the description ever matches a real trigger, so a conformance pass must never be reported as evidence that the package works. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |
| Write the description as the trigger surface it is: it is the only text resident before the package is loaded, so it must name the situations that should load it, including the phrasings that do not use the obvious keyword. | sourced | `X-cap-capability-packaging-001` "that Claude loads only when it's relevant to your task" |
| Treat portability as the measurable payoff rather than an aspiration: compatible implementations exist across many independent agent products, so a package that only our runtime can load has given up the property the standard was adopted for. | sourced | `X-cap-capability-packaging-003` "at least 25 other agent products had shipped compatible implementations" |
| Proposed: hold the resident tier to a counted ceiling rather than an impression; build-simplicity-budget owns the counting method, and the resident tier is the clearest place in this platform where a count and not a judgement decides whether a surface is still simple. Research query: does build-simplicity-budget's own skill.json state a specific count for the resident tier that this row should cite directly instead of restating the counting principle? | proposed | - |
| Proposed, following the reference example in docs/reference/composable-plan.md: judge the extension mechanism by whether teaching the platform something new is adding a file. A capability definition, a profile, a driver, an instrument and a view are each a file whose presence widens the legal values of a field a caller already writes, so new capability arrives as a new legal value rather than as a new field or new call syntax; a package kind that obliges a caller to learn a key is an extension point that leaked into the call. | proposed | `REF-5-1-01`, `REF-5-1-07`, `REF-12-12` "a capability definition \| legal step verbs" |

## Adapters

| Adapter | Role | Maps to | Cannot | Swap procedure | Status | Evidence |
|---|---|---|---|---|---|---|
| `E-adapter-skill-files` | today | list_resident, resolve, load_body and open_reference served by reading package directories from a root on the local filesystem. PASS.md records this adapter only as skill files; describing it as a filesystem directory layout is the manifest's entry and is proposed here. | Proposed: cannot be reached by a runtime on another machine without copying the tree, carries no identity beyond its path, and produces no digest, so two copies that have drifted apart are indistinguishable to a caller. | Point the resolver at the other source by configuration, resolve the same identities through both, and require identical resident fields, identical bodies and identical reference sets. No core file is edited, because the core imports the interface. | claimed | `F-b3-07` "skill files" |
| `E-swap-candidate-any-spec-conformant-registry` | second | the same four operations served by a registry entry format with namespace-scoped identity, fetched over a network and distributed as an addressable artifact; the row names the candidate class rather than a product. | Proposed: cannot hand back a local path, cannot be edited in place by the caller, and cannot serve a package whose identity is only a directory name - which is the point, since anything it cannot implement was a filesystem assumption leaking into the contract. | One conformance run resolves the same identity set through both adapters and diffs the resolved packages. Proposed: the execution-model axes that must differ are where the bytes come from (local directory read versus network fetch) and what identity is (a path versus a namespace-scoped name with a content digest). | claimed | `F-b3-07`, `X-cap-capability-packaging-004` "spec-conformant registry" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | bash harness/capability-packaging/test.sh |
| Expected | Two checks, both run from the repository root, deliberately separable. (1) Spec conformance, proposed tool built with the first adapter: `python3 tools/conformance_capability_packaging.py --root .claude/skills --report out/packaging-conformance.json`, asserting packages_checked > 0, frontmatter_missing == 0, required_field_missing == 0 over exactly the fields name and description, and name_mismatch == 0 where the declared name must equal the directory name. (2) Repository link check, which exists today: `python3 tools/validate_skills.py`, asserting 0 errors, plus the proposed counters links_checked > 0, dangling == 0 and asymmetric == 0 reported alongside its existing 'builds on unknown skill' and 'does not list ... under used_by' errors. (1) exit 0 with a report line reading `packages_checked=<N greater than 0> frontmatter_missing=0 required_field_missing=0 name_mismatch=0`. (2) exit 0 with `<N> skills checked, 0 errors` and `links_checked=<N greater than 0> dangling=0 asymmetric=0`. Until that proposed tool exists, `bash harness/capability-packaging/test.sh` (owned by cap-capability-packaging-implement) is the running gate: every check line reads ok and the script exits 0. |
| Deliberate breakage | Rename one package directory and update that package's own frontmatter name to match its new directory, leaving every link in other packages that names the old directory unchanged. |
| Expected failure | Check (1) stays green and still reports `name_mismatch=0`, because the renamed package is still spec-conformant on its own. Check (2) exits 1 with `dangling` non-zero and errors naming the old directory under 'builds on unknown skill'. The two checks failing independently is the point: the packaging contract is the specification's, and the link rule is ours. |
| Status | claimed |
| Evidence | `F-part-c-04`, `X-entry-composition-035` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`, `build-adapter-pair`, `build-definition-of-done`, `build-skill-authoring`, `cap-document-validation`, `cap-errors`

Used by: `cap-capability-packaging-implement`, `cap-capability-registry`, `compose-agent`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| What is the resident cost of one installed package, and what ceiling should it carry? | Two records on file give different figures for the same tier, roughly 100 tokens per package in one and 30 to 50 in the other; measure the resident tier of this repository's own packages under one tokenizer and set the ceiling from the measurement. | Bound the resident tier by counted fields rather than by a token number - two required fields and one sentence of description - until a measurement replaces the estimate. | `X-cap-capability-packaging-005`, `X-entry-composition-036` "only the name and description load at startup (~30-50 tokens per skill)" |
| Does the specification publish a version string this skill can cite? | A fetch of the specification recording a version and a date; the record on file says the format is not published as an explicitly versioned artifact, and documentation fetches were blocked in this environment. | version_status unverified everywhere, with the specification's identity and URL cited in place of a number. | `X-end-to-end-025`, `X-end-to-end-024` "The authoritative specification is hosted externally at https://agentskills.io/specification." |
| Is a package identified by name or by content, once a registry serves it? | Resolve the same identity twice through a registry across a republish and compare; a registry that orders versions by parsing them as semantic versions makes name-plus-version the identity, while a content digest makes the bytes the identity. | Carry both: a namespace-scoped name for callers to write down and a content digest for the resolution outcome to report, so a drifted copy is detectable without changing how anything is called. | `X-end-to-end-023`, `X-cap-capability-packaging-004` "the registry attempts to parse versions as semantic versions for proper ordering" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-capability-packaging 2831cb4f, 2026-09-03 |
