# Capability-packaging harness — one portable directory, three tiers

| Step | Command |
|---|---|
| 1. Run the gate | `bash harness/capability-packaging/test.sh` |
| 2. Make one call | `ADAPTER=dryrun python3 harness/capability-packaging/call.py` |
| 3. Swap the adapter | `ADAPTER=second python3 harness/capability-packaging/call.py` |
| 4. Prove the interface held | `python3 harness/capability-packaging/conformance.py --adapter dryrun --adapter second` |

## Files

| File | What it is |
|---|---|
| `interface.py` | The capability interface: `PackageRequest`, `PackageResolution`, `Problem`, and `CapabilityPackagingAdapter` with `list_resident`, `resolve`, `load_body`, `open_reference`, `check_package`. `resolve` is concrete, so no adapter can decline the two-required-field check |
| `adapters/dryrun.py` | Three fixture packages, in process, no filesystem, no network. One well-formed, one missing `description`, one whose declared name has drifted from its identity. Failure path on `DRYRUN_FAIL=1` |
| `adapters/live.py` | Today's component: reads this repository's `.claude/skills/` tree at `SKILLS_ROOT`, parsing `SKILL.md` frontmatter with a two-line hand-rolled parser (stdlib only). Product names live here |
| `adapters/second.py` | The second loader: a content-addressed registry, network fetch, digest-verified. Mirrors the dry-run fixtures' three identities so the swap proof runs the same cases. Reachable over `REGISTRY_URL`, or in process when unset |
| `call.py` | The minimal call. 27 lines below the `>>> CALLER CODE` marker; everything above it is the platform stamping the envelope |
| `conformance.py` | The 12 cases every directory-shaped adapter passes (9 for `live`, whose real tree has no broken fixture), plus the product-name scan over code |
| `test.sh` | The gate: 27 checks in dry run (30 with `--live`), the swap proof, and one deliberate breakage |
| `provenance.json` | Owner skill, co-skills, blueprint entry, kb ids, what is measured and what is claimed |

## The minimal call

| Line of the caller's code | What it does |
|---|---|
| `adapter = ADAPTERS[os.environ.get("ADAPTER", "dryrun")]()` | Binds one of three adapters by configuration, not by code |
| `ask = envelope(identity, trigger, reference_path)` | One entry envelope; the platform stamps correlation id, ceiling, idempotency key and actor into it without being asked |
| `found = next(e for e in adapter.list_resident() ...)` | Discover one package by name; the entry carries only `identity`, `name`, `description` |
| `resolution = adapter.load_body(identity, trigger)` | Resident tier, then body tier, on activation |
| `opened = adapter.open_reference(identity, reference_path)` | Reference tier, read only when named; merged into `resolution` |
| `adapter.resolve(BROKEN_IDENTITY)` inside `try/except Problem` | Refuses a package missing a required field with a typed problem |
| `ADAPTERS["second"]().resolve(identity)` | The same package, resolved by digest from the second (registry) loader |
| `table(...)`, `print(...)` | Identity, source, tiers loaded, digest, the refusal, the second loader's view |

| Environment knob | Default | Effect |
|---|---|---|
| `ADAPTER` | `dryrun` | `dryrun`, `live` or `second` |
| `IDENTITY` | `quickstart-parser` | Any identity the bound source knows |
| `TRIGGER` | one line about a starter template | The description-match text that authorizes reading the body |
| `REFERENCE_PATH` | `references/schema.md` | The one reference file read on demand |
| `BROKEN_IDENTITY` | `broken-legacy-importer` | An identity used to demonstrate the missing-field refusal |
| `ENTRY_KIND`, `ACTOR` | `human`, `user:corey` | Which of the four entries is acting, and as whom |

## Env vars for live mode

| Variable | Required | Meaning |
|---|---|---|
| `SKILLS_ROOT` | yes | Root directory to scan for packages (this repo's `.claude/skills`, or any conformant directory) |

## Env vars for the second (registry) adapter

| Variable | Required | Meaning |
|---|---|---|
| `REGISTRY_URL` | no | Base URL of a registry serving `GET {REGISTRY_URL}/{identity}` -> JSON record. Unset means the in-process simulation runs, over the same three identities the dry-run adapter serves |
| `REGISTRY_TIMEOUT_S` | no | Per-request timeout in seconds, default 30 |

## What each test proves

| # | Check | What it proves |
|---|---|---|
| 1 | Conformance, dry-run adapter, 12/12 | Discovery, the two-field gate, all three tiers, both refusals and `check_package` hold with no filesystem or network |
| 1b | Caller code is 27 lines, under 40, and names no adapter storage | One call is one call; the stamps are the platform's work, not the caller's |
| 1b | The minimal call discovers, loads 3 tiers, refuses the broken fixture, shows the second loader's digest | The exact scenario in plan.json's `minimal_call`, run end to end |
| 1c | `IDENTITY=no-such-package` / `broken-legacy-importer` / `REFERENCE_PATH=…nope.md` each exit 2, typed `document-invalid` (422) | Every refusal in the caller's own envelope is typed, not an exception leak |
| 1d | `DRYRUN_FAIL=1` exits 2 with `adapter-unavailable` (503) | The failure path is exercised, not only the happy one |
| 2 | Conformance before (dryrun) and after (second), 12/12 each | The interface held across a swap of the loader |
| 2 | `sha256` of `interface.py`, `call.py`, `conformance.py` identical across both runs | The swap was configuration, not a code edit |
| 2 | 2 execution-model axes differ (`source`, `digest_at_resolve`) | The second adapter breaks a different assumption: where the bytes come from, and whether identity carries a digest |
| 3 | `product_hits=0` over the code | No product name outside `adapters/` |
| 4 | Widening the required-field list to three makes the run FAIL and report `conformance FAILED` | The green run in step 1 can fail; the interface enforces exactly what the spec requires, never more |
| 5 | `--live`: 9/9 (3 skipped) against `SKILLS_ROOT` | Skipped with a message when `SKILLS_ROOT` is unset. The 3 skips are the missing-field and drifted-name cases, which a checked-in tree has no broken fixture to exercise |

## The two adapters behind one interface

| Axis | `adapters/live.py` / `adapters/dryrun.py` (today) | `adapters/second.py` (second) |
|---|---|---|
| Where the bytes come from | local directory read | network fetch (or an in-process simulation of one) |
| What identity is | a path (the directory name) | a namespace-scoped name with a content digest |
| `source` on the resolution | `directory` | `registry` |
| `digest` on the resolution | always `null` | `sha256:...`, computed over the resident, body and reference content |
| Swap procedure | `ADAPTER=dryrun` or `live` | `ADAPTER=second`; no code edit, same fixtures, compare the two reports |

## Failures a caller can get

| `type` | Status | Raised when |
|---|---|---|
| `urn:agentic:problem:document-invalid` | 422 | An identity nothing publishes, a package missing `name` or `description`, or a reference path the package does not declare. Carries the proposed `package-unresolved` suffix in `detail` (pending registration, docs/decomposition.md 2.1.6) rather than minting an unregistered type |
| `urn:agentic:problem:adapter-unavailable` | 503 | The bound source cannot be reached (`SKILLS_ROOT` unset or not a directory; the registry unreachable; `DRYRUN_FAIL=1`) |

## What would pin this to a component, and how the boundary avoids it

| Would pin (blueprint) | How this harness avoids it |
|---|---|
| A request field naming a filesystem path, a registry host, or a byte offset | `PackageRequest.from_dict` accepts only `identity`, `trigger`, `reference_path`; every adapter primitive is confined to `_scan_all` / `_locate` / `_read_body` / `_list_references` / `_read_reference` / `_digest`, never called from `call.py` |
| A third required resident field | `resolve()` checks exactly `REQUIRED_RESIDENT = ("name", "description")` in the interface, not per adapter. The deliberate breakage widens it and every binding that was green turns FAIL |
| Conflating the specification's own conformance with this repository's link convention (does the declared name match the directory) | `resolve()` never checks the name-matches-identity rule; only `check_package` (the proposed operation) reports `name_mismatch`, so a drifted package is still spec-conformant and still resolves (cap-capability-packaging step 5) |
| A caller learning which loader answered, then branching on it | The resolution carries `identity`, `resolved`, `source`, `digest`, `tiers_loaded` and `resident`/`body`/`reference`, and nothing about a path or a host; the `_no_leak` conformance case asserts the binding's own marker never reaches the payload |
| Loading the whole package to answer a discovery query | `list_resident()` reads only the resident tier; `load_body` and `open_reference` are additive tiers, each contingent on a trigger or a named reference path, never on being asked "give me everything" |

## What is measured here and what is not

| Claim | Status |
|---|---|
| Dry-run conformance, the swap proof and the breakage | Measured by `test.sh`: 27 checks, 0 failures |
| Live conformance and the same caller code against `SKILLS_ROOT=.claude/skills` | Measured by `test.sh --live`: 30 checks, 0 failures, 3 cases skipped (no broken fixture exists in a checked-in tree) |
| The second adapter's networked form, over a real `REGISTRY_URL` | Claimed. The dry run exercises its content-addressed state machine in process; no registry on this host has been reached |
| The standard, "Agent Skills spec" | Version unverified: no published version string exists to cite (F-b3-07, X-cap-capability-packaging-002); the specification's identity and URL are cited in place of a number |
| `check_package`, the `package-source-binding` and `packaging-conformance-report` shapes | Proposed operations from `cap-capability-packaging` / `cap-capability-packaging-implement`, not sourced from the specification itself |
