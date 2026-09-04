---
name: "build-research-record"
description: "The discipline of keeping one record per search, source and quote, so a claim a skill makes can be traced back to text that was actually read. Load before citing an X- id in a skill, when a statement needs a source and none is on file, before searching for prior art for a capability or a seam, when deciding whether a page was read or only its search result seen, before writing down a URL, a title or a version string, when a reviewer asks where a sentence came from, and when a search found nothing and you have to say so anyway. Fixes the record's fields (lens, topic, query, url, title, verbatim snippet, read, status search-only versus fetched), the rule that a cited quote is a verbatim substring of the record it names, and the merge that makes an X- id resolve at all."
---

# build-research-record (folded into `build-skill-authoring`)

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Keep one record per search, source and quote - collecting and storing the information about each source at the moment it is read - so a claim a skill makes can be traced back to text that was actually read, and so a search that found nothing is written down rather than lost. PASS.md states the write-down-what-you-searched rule for the first-cut Dispatch and State design; applying it to every lens in this repository is our own convention, recorded in the invariants below. | sourced | `X-build-research-record-001`, `X-build-research-record-002`, `F-part-c-03` "keeping track of your sources that allow you to collect and store information about sources" |

## Entities

| Entity |
|---|
| `E-standard-json-schema-2020-12` |
| `E-provisioning-concern-evidence-store` |

## Contract

### Standards

| Standard | Version | Version status | URL | Sources |
|---|---|---|---|---|
| `E-standard-json-schema-2020-12` | 2020-12 | unverified | - | `F-b3-09`, `E-standard-json-schema-2020-12` |

### Shapes (JSON Schema 2020-12)

**research-record (proposed shape; the field-by-field rules, a worked example and the lens naming convention are in references/build-research-record-research-record-shape.md)** (proposed; sources: `F-b3-09`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "research-record",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "id",
    "type",
    "lens",
    "topic",
    "query",
    "url",
    "title",
    "snippet",
    "status",
    "agent",
    "date"
  ],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^X-[a-z0-9]+(-[a-z0-9]+)*-[0-9]{3}$"
    },
    "type": {
      "const": "research"
    },
    "lens": {
      "type": "string"
    },
    "topic": {
      "type": "string"
    },
    "informs": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^[FERT]-"
      }
    },
    "query": {
      "type": "string"
    },
    "url": {
      "type": "string",
      "format": "uri"
    },
    "title": {
      "type": "string"
    },
    "snippet": {
      "type": "string"
    },
    "read": {
      "type": [
        "string",
        "null"
      ]
    },
    "status": {
      "enum": [
        "search-only",
        "fetched"
      ]
    },
    "claim": {
      "type": "string"
    },
    "agent": {
      "type": "string"
    },
    "date": {
      "type": "string",
      "format": "date"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Status is the claimed-versus-measured line for research, the same distinction agentic-stack states for the platform: search-only means a title and a result snippet were seen; fetched means the page body was read into the record. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| Proposed: read is non-null exactly when status is fetched. A search-only record never carries page text, and a fetched record never carries an empty read. Research query: research-record schema conventions for a nullable field whose non-null state is keyed to an enum value elsewhere in the same record. | proposed | - |
| A citation must never imply a page was read when only its search result was seen, because citing sources without reading them is considered fraudulent. | sourced | `X-build-research-record-002` "Citing sources without reading them is considered fraudulent because you are lying about the work you have done." |
| Proposed: nothing in a record is composed. The url, the title, the snippet, the date and any version string inside them are copied from what was in front of you or the record is not written. Research query: source-documentation practice on whether a field copied from a viewed page (url, title, snippet, date) may be normalized or must stay byte-for-byte as seen. | proposed | `F-part-c-10` "Cite the standard and its version." |
| Proposed: a version number counts as verified only when a record with status fetched carries it; otherwise the standard it governs stays version_status unverified. Research query: standards-tracking practice on what evidence is required before a version number is marked verified rather than unverified. | proposed | `F-part-c-10` "Prefer an existing standard to an original design." |
| The store is append-only, on the model of the evidence store, which PASS.md records as append-only JSONL. A record is never edited to fit a later claim; a correction is a new record and the old one stays where it is. | sourced | `F-a5-04` "Append-only JSONL" |
| Proposed: a record is citable only once it resolves in kb/research.jsonl. An X- id that resolves nowhere is a claim about a record, not a citation. Research query: citation-resolution practice on whether an id that does not resolve in a merged store counts as a citation at all. | proposed | - |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| This discipline does not record runs of our own code. A command, its exit status and the tree it ran against - the evidence-record fields PASS.md names (script SHA-256, git commit, tree hash) - belong to the evidence-record discipline (build-evidence-record), kept separate so a page somebody else wrote is never filed as something we measured. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Decide the fields before collecting: every record fills the required set in schemas/research.schema.json - id, type, lens, topic, query, url, title, snippet, status, agent, date - and nothing outside it. | The schema is the intellectual heart of a system that digests research: it encodes what was captured and so determines which comparisons across sources are possible later. | sourced | `X-build-research-record-004` "The database schema is the intellectual heart of systems that digest research information" |
| 2 | Write one record per result you intend to rely on, at the moment you read it, with the query string exactly as it was run and the url and title copied from the result. Research query: citation-manager practice on recording a source at the moment of reading versus batching citations after drafting. | Proposed: our convention, following the scholarly practice of a store that collects and keeps source information as you go rather than reconstructing citations at writing time. | proposed | `X-build-research-record-001` "collect and store information about sources, organize and keep track of your references" |
| 3 | Copy the snippet verbatim out of the result into the record. Do not retype it, tidy the punctuation, or trim it to the part that suits the claim. | The quote is the only thing a later tool can re-check, and citation hallucination is a measured failure of generated text, not a hypothetical one. | sourced | `X-build-research-record-005` "Citation hallucination rates range from 11% to 57% across commercially deployed models." |
| 4 | Set status honestly: search-only with read null when you saw a title and a snippet, fetched with a verbatim excerpt in read only when the page body was actually retrieved. | Citing sources without reading them is fraudulent, so the record has to make the difference visible rather than let a snippet pass for a reading. | sourced | `X-build-research-record-002`, `F-part-c-08` "Citing sources without reading them is considered fraudulent" |
| 5 | Record the searches that failed too: keep the query and the url of what you looked at even when nothing supported the claim, and say so in the skill. PASS.md asks this for the Dispatch and State design; doing it for every lens is proposed. Research query: whether the failed-search recording rule PASS.md states for the Dispatch/State design is meant to generalize to every research lens, or stays scoped to that one design. | A first-cut design has to say what was searched when prior art was not found, and a search nobody wrote down cannot be re-run or believed; the proposed extension to every lens is what keeps a proposed row honest rather than merely unsourced. | proposed | `F-part-c-03` "If you searched for prior art and found none, say what you searched." |
| 6 | Correct a record only by appending another and leaving the original in place; never edit a snippet, a url or a status after the fact. | On the model of the append-only evidence store PASS.md records. An in-place edit destroys the only thing that showed what was actually in front of the author. | sourced | `F-a5-04` "Append-only JSONL" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Citation hallucination rates range from 11% to 57% across commercially deployed models, and sentence-level attribution systems can attribute each sentence in generated text to quotes from source documents, allowing for quick fact-checking. | sourced | `X-build-research-record-005` "Citation hallucination rates range from 11% to 57% across commercially deployed models." |
| Verification has more than one axis: a widely-used framework checks provenance, source, date, location, and motivation, and asks whether the platform publishing the information is known for accuracy and reliability. | sourced | `X-build-research-record-006` "provenance, source, date, location, and motivation" |
| Recording where a resource came from is ordinary schema practice rather than overhead: it is very common to have a resource that has a source that needs to be recorded to understand how information was obtained. | sourced | `X-build-research-record-008` "very common to have a resource that has a source that needs to be recorded to understand how information was obtained" |
| Treat retrieval and verification as two steps, not one: fact-checking pipelines usually consist of evidence retrieval and verification, so finding a promising result is not yet having checked the claim against it. | sourced | `X-build-research-record-003` "The pipelines usually consist of evidence retrieval and verification." |
| Ethical research and writing means giving proper attribution and credit to the work of others, which is why the record names the source rather than absorbing its wording into ours. | sourced | `X-build-research-record-002` "Ethical research and writing means giving proper attribution and credit to the work of others" |
| agentic-stack already carries the well-formedness finding (F-a7-03) as a best practice; cite it by name instead of re-deriving it. Its analogue here is that a record which validates against the schema is well-formed, not true - schema-valid establishes well-formedness, not correctness. | sourced | `F-a7-03` "Those establish well-formedness, not correctness." |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/kb.py merge-research && python3 -c "import json,re,pathlib;S=json.load(open('schemas/research.schema.json'));R=[json.loads(l) for l in open('kb/research.jsonl') if l.strip()];ids={r['id'] for r in R};bad=sorted({r.get('id') for r in R if [k for k in S['required'] if k not in r] or not re.match(S['properties']['id']['pattern'],r.get('id','')) or r.get('status') not in S['properties']['status']['enum']});cited={i for p in pathlib.Path('.claude/skills').glob('*/skill.json') for i in re.findall(r'X-[a-z0-9-]+',p.read_text())};dangling=sorted(cited-ids);print('records',len(R),'invalid',bad,'dangling',dangling);assert not bad and not dangling" && python3 tools/validate_skills.py --only build-research-record |
| Expected | Measured by tools/measure.py at fd2fa05: exit 0; last lines: warning: build-research-record: restates F-part-c-08 under the same quote as agentic-stack, without naming it (compose by name, not by copy) \| build-research-record: 0 errors, 1 warnings |
| Deliberate breakage | Two, applied one at a time to kb/research/build-research-record.jsonl, re-merged with `python3 tools/kb.py merge-research`, and then restored: (a) invalid record - delete the `status` field from X-build-research-record-002; (b) altered snippet - change one character of X-build-research-record-002's snippet (`fraudulent` to `fraudulant`) so a quote this skill cites is no longer a verbatim substring of it. |
| Expected failure | Measured by tools/measure.py at fd2fa05: exit 1; last lines:   File "<string>", line 1, in <module> \| AssertionError |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: `build-entry-conformance`, `build-interface-versioning`, `build-litmus-questionnaire`, `build-simplicity-budget`, `cap-capability-registry`, `cap-evaluation`, `cap-human-interaction`, `cap-mandate-broker`, `cap-memory`, `compose-improvement-loop`, `compose-operators`, `xc-audit-trail`, `xc-compensation`, `xc-enforcement-chain`, `xc-tenancy`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Can any record in this lens move from search-only to fetched from this environment, so that a version string in it could be treated as verified? | One successful fetch of a recorded url with the page text placed in read; the outbound proxy blocked documentation fetches for the wave-1 authors, so nothing here has been read beyond its search result. | Every record in this lens stays status search-only, and no standard's version is recorded as verified on the strength of one. | `F-part-c-10` "Cite the standard and its version." |
| Should a fetched record be re-fetched before a later section cites it, given that a page can change under a stable url? | A second fetch of the same url on a later date, showing whether the recorded excerpt is still present verbatim; a divergence would decide whether re-fetching is required or the date field is enough. | Proposed: a record is cited as of its date, and the date is what a reader checks, the way the host inventory is cited as verified against the running host on 2026-09-03. | `F-meta-02` "verified against the running host on 2026-09-03" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 |
