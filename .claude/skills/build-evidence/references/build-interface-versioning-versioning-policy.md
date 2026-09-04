# Interface versioning: long material

Proposed reference for `build-interface-versioning`. The skill body is enough to apply the
discipline; open this only for the per-member deprecation entry shape, the pattern comparison,
or the worked telemetry split. Every id resolves with `python3 tools/kb.py show <id>`.

## 1. The per-member deprecation entry (proposed shape)

Summarised in the skill as `interface_version_policy.deprecated`. Full shape:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "deprecated_member",
  "type": "object",
  "additionalProperties": false,
  "required": ["member", "deprecated_on", "remove_no_sooner_than", "replacement"],
  "properties": {
    "member": {
      "type": "string",
      "minLength": 1,
      "description": "Dotted path to the field, operation or error being deprecated, in the interface's own vocabulary."
    },
    "deprecated_on": {
      "type": "string",
      "format": "date",
      "description": "The date the member was marked. Not the date someone wants it gone."
    },
    "remove_no_sooner_than": {
      "type": "string",
      "format": "date",
      "description": "deprecated_on plus the interface's deprecation_window_months. Computed, never chosen."
    },
    "replacement": {
      "type": ["string", "null"],
      "description": "The member a caller should move to, or null when the capability itself is going away."
    },
    "observed_callers": {
      "type": "integer",
      "minimum": 0,
      "description": "Calls seen declaring a version in which this member is still live, over the last window. Zero is evidence for removal; it is not permission to remove early."
    }
  }
}
```

Two rules that the shape cannot express and the checker asserts instead:

1. `remove_no_sooner_than == deprecated_on + deprecation_window_months`. A hand-edited earlier
   date is the failure this file exists to make visible.
2. A member in `frozen_core_fields` may never appear in `deprecated`. Freezing and deprecating
   the same field is a contradiction, not a sequence.

## 2. The five patterns on file, and what each one is good for

Each row is a research record for this skill; all are `search-only` (no page was fetched), so
they are cited as patterns and never as verified versions. `build-research-record` owns that
distinction.

| Pattern | Record | What it contributes here |
|---|---|---|
| Per-request version declaration with a bounded deprecation window | `X-cross-structure-061` | The shape this discipline copies: the declaration is per call, and deprecated features survive a stated minimum. |
| Frozen attributes that must never change | `X-cross-structure-012` | The frozen core field set: some surface is declared unchangeable rather than versioned. |
| Major/minor numbering | `X-build-interface-versioning-001` | The vocabulary for classifying a change, once the classification has been made by consumer impact. |
| Deprecation policy with a minimum overlap period | `X-build-interface-versioning-002` | The twelve-month floor the default window is set from. |
| Side-by-side major versions under distinct namespaces | `X-build-interface-versioning-003` | How to make a breaking change without breaking existing callers. |
| Header and media-type negotiation | `X-build-interface-versioning-004` | Keeping the version out of the identity of the addressed thing. |
| Version agreed once at the initialize handshake | `X-build-interface-versioning-005` | The shape the per-request pattern moved away from; useful as the contrast, not as the target. |
| Stated policy versus practice | `X-build-interface-versioning-006` | Why the check reads a call and not a document. |

## 3. Worked example: the telemetry split (proposed)

The telemetry row (`F-b3-10`, entity `E-capability-telemetry`) names a transport and a separate
attribute mapping. They change at different rates, so the discipline versions them apart:

- **Transport contract.** Pinned. It sits in the frozen half: the wire format and the resource
  attribute carrying correlation are declared never-changing, which is what makes a run
  reassemblable after the mapping has moved. This is the direct application of the frozen-attribute
  rule in `X-cross-structure-012`, and the reason the correlation attribute
  (`F-a7-02`, stated by `agentic-stack`) belongs in that set.
- **Attribute mapping.** Versioned on its own cadence, declared per call, and recorded per run:
  every emitted batch carries the mapping version it was produced against, so a later reader can
  tell which names to expect rather than inferring them from the run date.
- **What the split buys.** A mapping revision does not touch the transport, and a transport change
  does not invalidate stored runs. That is `T-t2-02` applied to one interface: enhance one aspect
  without touching the rest.
- **What it costs.** Two version numbers on one interface, so the policy must say which one a
  caller declares. Proposed answer: the caller declares the interface version; the mapping version
  is emitted as data, never negotiated, because a consumer of stored telemetry reads it after the
  fact and cannot negotiate anything.

## 4. Applying 1-3-1 when a change resists classification

`T-t5-02` is the operating protocol. The recurring case here is a change that is additive on the
wire and significant to one consumer (`X-build-interface-versioning-006`).

- **Problem.** A field is being added; the author believes it is safe; one consumer derives
  behaviour from the absence of that field.
- **Option A.** Ship it as additive under the current version. Cheapest; breaks the consumer that
  reads absence as meaning.
- **Option B.** Ship it under a new interface version served side by side
  (`X-build-interface-versioning-003`), deprecating nothing.
- **Option C.** Ship it as additive but make the new field's absence and its presence both
  explicit values, so no consumer has to infer from absence.
- **Recommendation.** C where the field admits an explicit "not applicable" value, because it
  costs no version and removes the ambiguity that made A unsafe; B otherwise. Record the choice
  with the change, per `F-part-c-06`.
