# Typed errors: enforcement table, audit blind spots, research ledger

Long material for `xc-typed-errors`. The skill body is enough to place and judge the guarantee;
open this when wiring a specific boundary, when deciding what the audit cannot see, or when
checking what a cited research record actually establishes.

Every statement below is either sourced to the knowledge-base id given in brackets, or marked
**proposed**. Quotes are verbatim substrings of the record named.

## 1. Where the guarantee attaches (proposed)

One row per boundary that can fail. `type_or_count` runs at each; the untyped counter is kept per
row, labelled with the boundary and the adapter beneath it, so a non-zero value names an owner.

| Boundary | Failure it raises | Registered type it returns | Counter owner |
|---|---|---|---|
| Entry envelope validation | The envelope does not match its declared shape | `urn:agentic:problem:document-invalid` | the driving adapter that accepted the entry |
| Policy gate | A deterministic pre-execution refusal | `urn:agentic:problem:policy-denied`, carrying `rule_id` | the policy adapter |
| Budget meter | A metered call would cross the ceiling | `urn:agentic:problem:budget-exhausted` | the dispatch seam |
| Identity check | The delegation chain does not verify | `urn:agentic:problem:identity-untrusted` | the identity adapter |
| Idempotency lease | Same key, different request body | `urn:agentic:problem:idempotency-conflict` | the state seam |
| Capability adapter | Anything the adapter did not type | `urn:agentic:problem:adapter-unavailable`, untyped payload in `detail` | that adapter |

Every suffix in this table has a row in the closed registry in `docs/decomposition.md` section
2.1.6, which `cap-errors` owns. Nothing here adds a type.

## 2. What the string-match audit cannot see (proposed)

Row X6's check is `grep -rn -E 'match.*(error|failed|timeout)' src/ --include='*.py'` outside
`src/problem/`. It is a floor, not a ceiling. Known blind spots, each of which is why the
per-boundary untyped counter exists alongside it:

1. **A compiled or vendored dependency.** A library that classifies failures by substring inside
   its own code is invisible to a grep over `src/`. The counter sees it, because the adapter
   wrapping that library either produces a registered type or is counted.
2. **A prompt.** An agent instructed in natural language to "retry if the message mentions rate
   limits" is string matching in a place no linter reads.
3. **Another language.** The pattern is scoped to one file extension; a second runtime in the tree
   needs its own pattern added in the same change that adds the runtime.
4. **A success-shaped failure.** "The worst failures in AI systems don't look like failures—they
   arrive with a 200 status code" [X-xc-typed-errors-004]. Nothing in a grep for error words finds
   a completion that carries no usable output. Instruction 7 in the skill body covers this case.
5. **A widened exclusion list.** A second path added beside `src/problem/` silently removes a
   region of the tree from the check, which is why `parser_path` is a required member of the report
   rather than a build-script argument.

## 3. Research ledger

What each cited record establishes, and what it does not.

| Record | Establishes | Does not establish |
|---|---|---|
| `X-xc-typed-errors-001` | The standard's media type and its five base members | Any version claim beyond what the record itself says; the specification was not fetched |
| `X-xc-typed-errors-002` | That extension members are explicitly allowed: "RFC 9457 explicitly allows Extension Members." | Which extension members this platform declares; that belongs to the registry row |
| `X-xc-typed-errors-003` | That categories drive different handling: "Only transient errors should be retried; others require different handling." | That its category names are this platform's type suffixes; they are not |
| `X-xc-typed-errors-004` | That failures arrive success-shaped | Any measured rate; the record is search-only |
| `X-xc-typed-errors-005` | That both an attempt count and a retry budget are needed | Any numeric value for either bound |
| `X-xc-typed-errors-006` | The contract this guarantee enforces: "every failure can be programmatically identified without string parsing" | Where the check runs; that is this skill's contribution |
| `X-xc-typed-errors-007` | Only that some registry exists | The registry's contents. Its eight-name list matches no other record on file and its URL is not a fetched specification, so the ten-row registry in `docs/decomposition.md` section 2.1.6 is normative. See open question 1 in the skill body |
| `X-entry-composition-042` | That the several ways in are driving adapters into one core | Which adapters this platform runs |
| `X-entry-composition-046` | Why one shape is adopted rather than several invented | The version, which stays unverified |

## 4. The four worked failures

The `FailureAtEveryEntry` examples in the skill body are the audit's fixtures, one per way in
plus the schedule entry. They exist so the assertion "one refusal condition returns one identical
type under every entry" has concrete inputs rather than a prose rule. Read them there; they are
not duplicated here, because a second copy is a second thing to keep in step.
