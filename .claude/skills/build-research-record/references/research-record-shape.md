# research-record: full shape, field rules, worked example

Proposed reference material for `build-research-record`. The skill body is enough to write and cite a
record by hand; open this file only when you are building or checking the record store itself — writing a
lens file from scratch, writing a validator over `kb/research.jsonl`, adding a field to the schema, or
reviewing a record whose fields are all present but whose values look wrong.

The authoritative copy of this schema is `schemas/research.schema.json` in this repository. If the two
disagree, the file in `schemas/` wins and this page is stale.

## Full schema (JSON Schema 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/Dadlorian/AGENT/schemas/research.schema.json",
  "title": "Research record",
  "type": "object",
  "required": ["id", "type", "lens", "topic", "query", "url", "title", "snippet", "status", "agent", "date"],
  "additionalProperties": false,
  "properties": {
    "id": {"type": "string", "pattern": "^X-[a-z0-9]+(-[a-z0-9]+)*-[0-9]{3}$"},
    "type": {"const": "research"},
    "lens": {"type": "string"},
    "topic": {"type": "string"},
    "informs": {"type": "array", "items": {"type": "string", "pattern": "^[FERT]-"}},
    "query": {"type": "string"},
    "url": {"type": "string", "format": "uri"},
    "title": {"type": "string"},
    "snippet": {"type": "string"},
    "read": {"type": ["string", "null"]},
    "status": {"enum": ["search-only", "fetched"]},
    "claim": {"type": "string"},
    "agent": {"type": "string"},
    "date": {"type": "string", "format": "date"}
  }
}
```

## Field rules

| Field | Rule | Failure it prevents |
|---|---|---|
| `id` | `X-<lens>-<nnn>`, three digits, unique across `kb/research.jsonl`. The lens segment matches the `lens` field. | Two lenses silently overwriting each other's numbering after a merge. |
| `lens` | The research angle or agent that produced the record; it is also the basename of the file the record lives in, `kb/research/<lens>.jsonl`. | A record that cannot be traced to the pass that collected it. |
| `topic` | The item or gap the record informs, in words. Machine-readable links go in `informs`. | A record kept because it was interesting rather than because something needed it. |
| `informs` | Optional list of `F-`, `E-`, `R-` or `T-` ids the record bears on. | A record that supports a claim nobody can locate. |
| `query` | The exact query string that was run, not a description of it. | A search that cannot be re-run by the next reader. |
| `url` | The result's own URL, copied. Never assembled from a remembered pattern. | An invented URL, which is the single worst defect this store can carry. |
| `title` | The result's title, copied. | A title rewritten to fit the claim. |
| `snippet` | Verbatim text from the search result. Copied, never retyped. | A paraphrase that no later tool can re-check against the source. |
| `read` | Verbatim excerpt from the page body when it was actually fetched; `null` otherwise. | A search snippet being presented as if the page had been read. |
| `status` | `search-only` when only the title and snippet were seen; `fetched` when the page content was read into `read`. | Claimed evidence wearing the authority of measured evidence. |
| `claim` | Optional: one sentence saying what this record supports. It is a pointer to the argument, never the argument. | A decision smuggled into the evidence store. |
| `agent` | Who or what produced the record. | An unattributable record. |
| `date` | ISO date of the search. A `fetched` record is cited as of this date. | A stale read presented as current. |

## Worked example

One record, as a single line of `kb/research/<lens>.jsonl` (pretty-printed here for reading):

```json
{
  "id": "X-build-research-record-002",
  "type": "research",
  "lens": "build-research-record",
  "topic": "Evidence-based documentation and source attribution best practices",
  "informs": ["F-b1-02"],
  "query": "evidence-based documentation best practices source attribution",
  "url": "https://thecrctoolkit.com/blog/post-source-documentation",
  "title": "Source Documentation Best Practices: The Foundation of Research Data",
  "snippet": "Ethical research and writing means giving proper attribution and credit to the work of others, as the ideas, words, and publications of others are considered intellectual property in the academic community. Citing sources without reading them is considered fraudulent because you are lying about the work you have done.",
  "read": null,
  "status": "search-only",
  "claim": "Source documentation requires verifying sources were actually read and properly crediting intellectual property to avoid fraudulent citation.",
  "agent": "research lens: build-research-record",
  "date": "2026-09-03"
}
```

A skill then cites it as `sources: ["X-build-research-record-002"]` with a quote copied character for
character out of `snippet`, for example `"Citing sources without reading them is considered fraudulent"`.

## Merging and citing

1. Records are written into `kb/research/<lens>.jsonl`, one JSON object per line.
2. `python3 tools/kb.py merge-research` collects every lens file into `kb/research.jsonl`.
3. `tools/validate_skills.py` loads `kb/research.jsonl` alongside facts, entities, edges and target facts,
   so an `X-` id only resolves after the merge has been run.
4. The quote check compares the skill's quote against the record's serialized text. A quote containing a
   double quote character will not match, because the serialization escapes it; pick a different span of
   the same snippet rather than editing the record.

## Lens naming

A lens is one angle of enquiry, not one skill. The three lenses on disk when this was written —
`entry-composition`, `cross-structure` and `end-to-end` — are worked examples of the convention: name the
question the pass was asking, so a later reader can tell what was and was not being looked for.
