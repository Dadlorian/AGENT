# Skill: API reference

Use when documenting any HTTP surface in this project. Produces a drillable reference, not a guide. Guides (Control Plane API Guide, Router API Guide) tell the story and link into this reference; the reference is where every call is fully specified.

## Source of truth
- Terms come from `cellplane-glossary.js`. A schema `description` is the glossary definition of its term; never paraphrase it. New entities are added to the glossary first, with their governing standard, then to the spec.
- One OpenAPI 3.1 file per service: `cellplane.openapi.json`. Nothing about an endpoint is written anywhere else.
- Each operation MUST have: `operationId`, `tags` (one, the resource), `summary` (≤ 60 chars, verb first), `description` (what changes, what it costs, what it is idempotent over), `security`, `x-roles` (roles that may call it), `parameters` with `description` and `example`, `requestBody` schema with `example`, every `responses` entry it can return, and `x-errors` (list of problem-type URNs with when).
- Every schema lives in `components.schemas` with a one-line `description` per property. No inline anonymous objects in responses.
- Errors are RFC 9457 and reference `components.schemas.Problem`; problem types are enumerated in `x-problem-types` with `status`, `title`, `retryable`, `next`.
- Examples are complete and consistent: the same ids (`org_7f`, `prj_a1`, `spec_8f1`, `wf_9c`, `t-0217`) across all operations so a reader can follow one object through the API.
- Vendor extensions: `x-cli` (the `cp` command for this operation), `x-node` (the SDK call), `x-roles`, `x-errors`, `x-scope` (`org | ws | task`), `x-mock` (canned response for Try it). CLI and Node snippets are generated from these, never hand-written in the page.

## Page structure (Stripe pattern)
- Three columns ≥ 1180px: left nav by resource (sticky), middle prose + parameters + schemas, right code column (sticky, follows the operation in view). ≤ 1180: code moves inline under each operation. ≤ 860: nav becomes a top chip row.
- Order: Introduction (base URL, auth, scope, idempotency, errors, versioning, rate limits) → one section per resource → Problem types → Schemas.
- Each resource section: one paragraph on the object, the object schema rendered as an attribute list (name · type · description · example), then one block per operation.
- Each operation block: `METHOD /path` in mono with method colour; summary; roles pill(s); scope pill; parameters (path, query, header) as attribute lists; request body attributes; response attributes per status; errors as a list of problem-type links; right column shows request (tabs: CLI · Node · HTTP) and response example. A Try it button sends the example to the mock and shows the mock response inline.
- Anchors: `#res-{tag}` and `#op-{operationId}`. Left nav highlights the operation in view.
- Search box filters operations by path, summary, operationId.

## Code
- Inline: every path, verb, id, URN, header, field or value in prose is `<code>`.
- Block: every listing is `<pre><code>` with an explicit language (`data-lang`: http · shell · js · json · yaml · rego) and is rendered through `cellplane-code.js` → header bar with language label + Copy, line numbers on multi-line blocks, palette colouring (method/keyword `--accent`, key `--park`, string `--run`, number `--wait`, comment `--faint`, url `--text`).
- No pseudo-notation inside code (`→`, `∈`, `…` as syntax). Results go in a `# returns` / `// returns` comment line; alternatives go in a comment line above the key, never padded to the right of it.
- Same identifiers in every listing (`org_7f`, `prj_a1`, `spec_8f1`, `wf_9c`, `t-0217`).

## Style
- Follows `Style Guide.dc.html` and `cellplane-tokens.css`. Method colours: GET `--run`, POST `--park`, PUT `--wait`, DELETE `--stuck`, PATCH `--muted`. Pills mono uppercase outlined. Code blocks surface bg with hairline, accent top rule only on the request, never on the response.
- Attribute lists, not tables, for parameters and schema properties (name in mono, type in muted mono, description in prose). Tables only for enumerations.
- No prose the spec does not carry. If it needs explaining, it goes in the spec `description`.

## Acceptance criteria
- Every operation in the spec renders; every `x-errors` URN resolves to a Problem types entry; every `$ref` resolves.
- Try it works for every operation with an `x-mock`.
- Same ids across every example (checked by grep).
- No horizontal overflow at 924px; no default scrollbars.
