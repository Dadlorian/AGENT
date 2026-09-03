# Tool access — full shapes

Proposed unless a row says otherwise. Open this file when implementing or reviewing the shapes;
`SKILL.md` carries the summary shapes and is enough to judge a candidate server without it.

Ids resolve with `python3 tools/kb.py show <id>`. The capability row is `F-b3-06`; the state of the
endpoint that runs today is `F-a6-03`; the dialect below is governed by `cap-document-validation`
(`F-b3-09`) and the failure object by `cap-errors` (`F-b4-07`).

## 1. Building blocks

Three blocks, kept distinct at the boundary (search-only record `X-cap-tool-access-001`).

| Block | Called or read | What the platform does with it |
|---|---|---|
| Tool | called; may change something | validates arguments against the tool's input schema, applies policy, budget and idempotency around the call |
| Resource | read; changes nothing | fetches by URI, optionally built from a parameterised template (`X-cap-tool-access-004`) |
| Prompt | template | passed through; never parsed by the platform to decide anything |

## 2. Tool descriptor (full)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:tool-descriptor:1.0",
  "title": "ToolDescriptor",
  "type": "object",
  "additionalProperties": false,
  "required": ["name", "input_schema", "effect"],
  "properties": {
    "name":         { "type": "string", "minLength": 1, "maxLength": 128 },
    "title":        { "type": "string", "description": "For display only." },
    "description":  { "type": "string", "description": "For a person or a model. Never parsed to decide anything." },
    "input_schema": { "type": "object", "description": "A JSON Schema 2020-12 document, itself checked against the meta-schema before use." },
    "output_schema":{ "type": "object", "description": "Optional. When present, the result's structured content is validated against it." },
    "effect":       { "enum": ["read_only", "mutating", "unknown"], "description": "Declared. unknown is treated as mutating everywhere above." },
    "idempotent":   { "type": "boolean", "default": false },
    "catalogue_digest": {
      "type": "string",
      "description": "Digest of the descriptor as published, so a catalogue can be diffed between runs."
    }
  }
}
```

## 3. Resource template

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:resource-template:1.0",
  "title": "ResourceTemplate",
  "type": "object",
  "additionalProperties": false,
  "required": ["uri_template", "effect"],
  "properties": {
    "uri_template": { "type": "string", "description": "A parameterised URI pattern the client expands to a concrete URI." },
    "name":         { "type": "string" },
    "media_type":   { "type": "string" },
    "effect":       { "const": "read_only" }
  }
}
```

## 4. Call request

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:tool-access:tool-call-request:1.0",
  "title": "ToolCallRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["binding", "tool", "arguments", "correlation_id"],
  "properties": {
    "binding":        { "type": "string", "description": "Handle from bind_server. Carries no host, product or version." },
    "tool":           { "type": "string", "description": "A name from the catalogue AND from the unit's declared surface." },
    "arguments":      { "type": "object", "description": "Validated against the tool's input_schema before the call leaves the platform." },
    "correlation_id": { "type": "string", "minLength": 1 },
    "idempotency_key":{ "type": "string", "description": "Required when effect is mutating or unknown." },
    "deadline_s":     { "type": "number", "exclusiveMinimum": 0 }
  }
}
```

## 5. Call result and failure

The result shape is in `SKILL.md`. A failure is the problem object `cap-errors` defines; the types
this boundary raises are, proposed:

| Problem type | Raised when |
|---|---|
| `urn:agentic:problem:tool-not-declared` | the name is outside the unit's declared surface |
| `urn:agentic:problem:tool-not-found` | the name is declared but absent from the catalogue at bind time |
| `urn:agentic:problem:tool-arguments-invalid` | arguments fail the tool's input schema |
| `urn:agentic:problem:tool-schema-invalid` | the published input schema fails the 2020-12 meta-schema |
| `urn:agentic:problem:tool-call-failed` | the tool reported a failure, in the transport or inside its own envelope |
| `urn:agentic:problem:catalogue-empty` | the binding published zero tools |

## 6. Conformance counters

The definition of done in `SKILL.md` asserts on these; the report shape is in
`cap-tool-access-implement`.

| Counter | Assertion |
|---|---|
| `conformance_failures` | `== 0` per adapter |
| `tools_listed` | `> 0` per adapter |
| `schemas_checked` | `== tools_listed` |
| `schemas_invalid` | `== 0` |
| `undeclared_refused` | `>= 1` |
| `adapters_run` | `>= 2` |
