# Isolation shapes (long material)

Proposed. Open this only when implementing or reviewing the full declaration schema, the profile
resolution rules, or the containment report. The body of `cap-isolation/SKILL.md` is enough to judge
whether a boundary is drawn correctly and to call the capability without reading this file.

Every schema here is JSON Schema 2020-12 and every one is **proposed**: PASS.md names the capability
and the standard that governs it (`F-b3-02`), not the calls or the field names. The two safe defaults
are sourced — egress off by default (`F-a3-04`) and no real secret inside the unit (`F-a3-05`,
`F-a3-07`) — and the one containment property recorded as verified live is the jail row (`F-a3-06`).

## 1. Isolation declaration (full)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:declaration:0.1",
  "title": "IsolationDeclaration",
  "type": "object",
  "additionalProperties": false,
  "required": ["profile", "egress"],
  "properties": {
    "profile": {
      "type": "string",
      "minLength": 1,
      "description": "A named resource envelope, resolved by the adapter. Names only. A caller that writes megabytes or vCPU counts has described a machine, and a capability-granting adapter has nothing to resolve."
    },
    "egress": {
      "enum": ["none", "allowlist"],
      "default": "none"
    },
    "egress_allowlist": {
      "type": "array",
      "items": { "type": "string", "minLength": 1 },
      "description": "Destinations, as names or address ranges. Required when egress is allowlist."
    },
    "credentials": {
      "const": "broker_only",
      "default": "broker_only",
      "description": "A const, not an enum. The unit is given a broker to reach; the broker holds the real key and picks the endpoint."
    },
    "filesystem": {
      "type": "array",
      "description": "Grants, not mounts. Each entry names a logical input or output the unit may reach; how it is materialised is the adapter's business.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["name", "mode"],
        "properties": {
          "name": { "type": "string", "minLength": 1 },
          "mode": { "enum": ["read", "write"] }
        }
      }
    },
    "max_duration_s": {
      "type": "integer",
      "minimum": 1,
      "description": "The wall-clock ceiling the boundary will destroy the unit at. Enforced outside the unit, never handed to it."
    }
  },
  "allOf": [
    { "if":   { "properties": { "egress": { "const": "allowlist" } }, "required": ["egress"] },
      "then": { "required": ["egress_allowlist"] } }
  ]
}
```

### Fields deliberately absent, and why

| Field a machine-shaped contract would have | Why it is not here |
|---|---|
| `kernel_boot_args` | Only a virtual machine can honour it. Its presence would make a component-sandbox adapter unbuildable. |
| `rootfs_image`, `block_devices` | A filesystem is a grant, not a device layout. An adapter with no filesystem grants nothing and is still conformant. |
| `network_interface`, `ip_address` | Egress is a policy over destinations. An adapter with no network stack satisfies `egress: "none"` trivially. |
| `memory_mb`, `vcpus` | Numbers describe a machine. `profile` describes an envelope the adapter resolves. |
| `hypervisor_socket`, host paths | Control-plane detail of one adapter, and a caller that can set it can reach the host. |

## 2. Profile resolution rules (proposed)

1. A profile name resolves in the adapter, never in the core. Two adapters may resolve the same name
   to very different envelopes; that is the point.
2. A profile a given adapter cannot resolve is refused at `admit` with the typed problem
   `isolation-unavailable`, retryable. It is never silently resolved to the nearest available profile:
   a silent downgrade produces a unit that ran with weaker containment than was asked for, and nothing
   in the result would say so.
3. Profile names are a closed set held in configuration. Adding one is a configuration change and a
   conformance run, not a code change.

## 3. Containment report (full)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:containment-report:0.1",
  "title": "ContainmentReport",
  "type": "object",
  "additionalProperties": false,
  "required": ["adapter", "jail_mode", "owner_in_host_passwd",
               "egress_attempts_made", "egress_attempts_blocked", "observed_from"],
  "properties": {
    "adapter": { "type": "string", "description": "Adapter entity id. Read by the conformance suite; never by a caller." },
    "jail_mode": { "type": "string", "pattern": "^0[0-7]{3}$" },
    "owner_in_host_passwd": { "type": "boolean", "description": "False is the passing value." },
    "egress_attempts_made": { "type": "integer", "minimum": 0 },
    "egress_attempts_blocked": { "type": "integer", "minimum": 0 },
    "secrets_seen_inside": { "type": "integer", "minimum": 0, "maximum": 0 },
    "observed_from": {
      "const": "host",
      "description": "The whole point of the record. A report the unit produced about itself is not a containment report."
    },
    "declared_gap_honoured": {
      "type": "boolean",
      "description": "True when the adapter behaved as its declared gap says it will, including when the declared behaviour is a refusal."
    }
  }
}
```

### Reading the counters

- `egress_attempts_made == 0` means the suite asserted nothing about egress. It is a failure of the
  suite, not a pass for the adapter.
- `egress_attempts_blocked == egress_attempts_made` is the passing condition under a declaration that
  named no destinations. Under `egress: "allowlist"`, the passing condition is that every attempt to a
  destination outside the list was blocked and every attempt inside it was not.
- `jail_mode` and `owner_in_host_passwd` correspond to the one containment property the substrate
  records as verified live (`F-a3-06`). Everything else in the report starts as a claim.

## 4. Unit result (proposed summary)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:cap:isolation:unit-result:0.1",
  "title": "UnitResult",
  "type": "object",
  "additionalProperties": false,
  "required": ["exit_status", "outputs", "usage"],
  "properties": {
    "exit_status": { "type": "integer" },
    "outputs": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["digest", "media_type"],
        "properties": {
          "digest": { "type": "string" },
          "media_type": { "type": "string" }
        }
      }
    },
    "usage": {
      "type": "object",
      "required": ["wall_ms"],
      "properties": {
        "wall_ms": { "type": "integer", "minimum": 0 },
        "peak_memory_bytes": { "type": "integer", "minimum": 0 }
      }
    },
    "containment": { "$ref": "urn:agentic:cap:isolation:containment-report:0.1" },
    "problem": { "$ref": "urn:agentic:problem:0.1" }
  }
}
```

There is no field naming what contained the unit. A caller that could read one would branch on it, and
the swap would stop being a configuration change.

## 5. The failure type this boundary owns

`isolation-unavailable`, HTTP status 503, retryable — raised when no adapter could admit the
declaration. The shape is the problem object `cap-errors` defines (`urn:agentic:problem:0.1`); this
capability adds a type, never a second error shape.
