# Capability packaging - full shapes and tier assignment

Proposed. Open this only while implementing the package shape, assigning content to tiers, or
reviewing someone who did. The body of `cap-capability-packaging` is enough to judge and to call
the capability without it.

## 1. capability-package, full shape (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-packaging:package:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["identity", "resident", "body"],
  "properties": {
    "identity": {
      "type": "string",
      "description": "Namespace-scoped name. Proposed: the directory name is the identity under the directory adapter; a registry adapter carries the same string plus a namespace.",
      "pattern": "^[a-z0-9]+(-[a-z0-9]+)*$"
    },
    "namespace": {"type": ["string", "null"], "description": "Proposed: null under the directory adapter, reverse-DNS under a registry adapter."},
    "resident": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name", "description"],
      "properties": {
        "name": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 40, "maxLength": 1024}
      }
    },
    "body": {"type": "string", "minLength": 1, "description": "Path to the package file, relative to the package root."},
    "references": {"type": "array", "items": {"type": "string"}, "default": []},
    "scripts": {"type": "array", "items": {"type": "string"}, "default": []},
    "assets": {"type": "array", "items": {"type": "string"}, "default": []},
    "digest": {"type": ["string", "null"], "description": "Proposed: content digest of the package tree. Null under an adapter that cannot produce one."}
  }
}
```

The optional `scripts/`, `references/` and `assets/` directories follow the structure the standard's
own documentation describes (`X-cross-structure-062`: "plus optional scripts/, references/, and
assets/ directories").

## 2. package-resolution-outcome, failure members (proposed)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:capability-packaging:resolution:0.1",
  "type": "object",
  "additionalProperties": false,
  "required": ["identity", "resolved", "source", "tiers_loaded"],
  "properties": {
    "identity": {"type": "string"},
    "resolved": {"type": "boolean"},
    "source": {"enum": ["directory", "registry"]},
    "digest": {"type": ["string", "null"]},
    "tiers_loaded": {"type": "array", "items": {"enum": ["resident", "body", "reference"]}, "uniqueItems": true},
    "problem": {
      "type": ["object", "null"],
      "description": "Proposed: when resolved is false, an RFC 9457 problem details object as cap-errors defines it. Never a bare string."
    }
  }
}
```

## 3. Tier assignment table (proposed)

| Content | Tier | Loaded when | Why it sits there |
|---|---|---|---|
| Package name | resident | always | It is the identity a caller writes down. |
| Description | resident | always | It is the only trigger surface; nothing below it is read until it matches. |
| Instructions, invariants, contract | body | the description matches a trigger | This is the working text; it is what activation is for. |
| Full schemas, tables, worked examples | reference | a step in the body says to open it | Long material that most activations never need. |
| Executable helpers | reference (scripts) | a step in the body runs it | Code is loaded by running it, not by reading it into context. |
| Fixtures, images, sample data | reference (assets) | a step in the body names it | Bytes that are never prompting context. |

## 4. The two checks, kept apart (proposed)

| Check | Owner | Asserts | Fails when |
|---|---|---|---|
| Spec conformance | the Agent Skills spec | package file present, required frontmatter fields present, declared name equals directory name | a package would not load in a runtime we did not write |
| Link and manifest check | this repository | every link resolves, links are symmetric, the package is in the manifest | a package would not compose correctly *here* |

A package can pass the first and fail the second. That is not a defect in either check; it is the
separation the notes for this skill require, and the definition of done's breakage is chosen to
demonstrate exactly that split.
