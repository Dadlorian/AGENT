# Counting method — worked declaration for one element

Proposed reference. The skill body is enough to run the discipline; open this only when you are
setting a budget on a new element and want the worked numbers and the exact expressions.

## The element

`entry-envelope`, the one envelope all four entries use (`examples/end-to-end/schemas/entry.schema.json`),
together with the agent profile that a caller must fill to register an agent
(`examples/end-to-end/schemas/agent-profile.schema.json`).

## The declaration (conforms to contract.shapes simplicity-budget-declaration)

```json
{
  "element": "entry-envelope",
  "source_of_truth": [
    "examples/end-to-end/schemas/entry.schema.json",
    "examples/end-to-end/schemas/agent-profile.schema.json"
  ],
  "ceilings": {
    "first_run_concepts": 10,
    "resident_metadata": 9,
    "minimum_implementation": 9
  },
  "counted": {
    "first_run_concepts": 10,
    "resident_metadata": 9,
    "minimum_implementation": 9
  },
  "counted_on": "2026-09-03",
  "escape_hatch": "payload is an open object: any work-specific structure passes through without a new required envelope field"
}
```

Each ceiling is set at the count measured on 2026-09-03 (a ratchet), because no research record on file
supports a lower number for this element. A lower ceiling is allowed only with a cited record.

## The three counting expressions

| Count | Expression over the source of truth | Value on 2026-09-03 |
|---|---|---|
| `first_run_concepts` | `len(entry.required)` — what a caller must author for one successful run | 10 |
| `resident_metadata` | `len([f for f in entry.required if f != "payload"])` — what rides with every unit whatever the work is | 9 |
| `minimum_implementation` | `len(agent_profile["$defs"]["profile"]["required"])` — fields to declare one conforming agent | 9 |

## Why these three and not others

- `first_run_concepts` is the adoption cost: the number paid before anything works at all.
- `resident_metadata` is the per-call cost: paid on every unit, not once.
- `minimum_implementation` is the integration cost: what a third party must fill to conform.

A fourth count is added only when it changes a decision; each count that never rejects anything is
noise in the check.

## Applying it to a different element

1. Replace `source_of_truth` with that element's machine-readable definition.
2. Re-derive the three expressions against that file's shape (a registry counts entries; an interface
   counts operations; a schema counts `required`).
3. Set the ceilings at the first measured counts, then wire the criterion and the breakage from the
   skill's definition of done, substituting the new paths.
