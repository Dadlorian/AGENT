# Blueprint shape, section by section (proposed)

Long material for `build-solution-architecture`. The skill body is enough to produce and revise a
blueprint without this file; open it when you need the column list for one section or the exact
error strings the checker prints. Every column list below is proposed: it is the shape
`docs/architecture/blueprint.json` carries, not a rule anyone published.

## Per-section columns

| Section | Columns beyond `sources` and `quote` |
|---|---|
| `standards_at_play` | `standard`, `version` (a value or `unverified`), `version_status`, `governs`, `capabilities[]`, `what_it_fixes`, `what_it_leaves_open` |
| `state_types` | `state`, `owner_capability`, `home_today` (from the inventory, or `gap`), `home_ideal`, `standard`, `written_by`, `read_by[]`, `lifetime`, `crosses_boundaries[]`, `pinning_risk`, optional `status` and `gap_ref` |
| `entry_matrix` | `entry`, `entry_kind`, `entry_enumeration` (which enumeration the label cites), `state`, `minimal_caller_action`, `platform_applies` |
| `tool_entries` | `component`, `capability`, `standard`, `adapter_boundary` (exposes / hides), `must_stay_loose`, `would_pin`, `second_adapter`, `harness_minimal_call` |
| `impact_map` | `if_changes`, `affected_adapters[]`, `affected_tests[]`, `affected_skills[]`, `unaffected_core` |
| `myopia_check` | `gap`, `why_it_matters`, `proposed_owner`, optional `promoted_to` pointing at the row it became |
| `gaps` | `gap_ref`, `where`, `claim`, `why_needed`, `research_query`, `status`, optional `closure` |
| `open_questions` | `question`, `deciding_evidence` |
| `usability` | `scope` (caller or builder), `entry`, `common_task`, the counted reads, `proposed_budget`, `met`, `measured_against`, `note` |
| `provenance` | `kb_source_sha256`, `kb_heads` |

## Gap triage classes

Three classes, and each has a different owner (proposed shape; the classes come from the owner's
decisions, T-t8-01 and T-t8-02):

| Class | What it is | Who closes it |
|---|---|---|
| `A-version` | a standard is named and no version is recorded | research: a real search result, or none found |
| `C-standard-exists` | no standard is recorded for a shape we would otherwise invent | research: cite the standard, or record none found |
| `B-host-fact` | the thing is absent on the host today | the owner: design work, not a search |

## Checker error strings

`python3 tools/blueprint_check.py [path]` prints one `error:` line per problem and then a counts
line, and exits 1 when any error was printed:

- `<section>[<i>]: unknown source <id>`
- `<section>[<i>]: quote is not a substring of any cited record: '<first 50 chars>'`
- `<section>[<i>]: no sources, not a gap, not marked proposed`
- `<section>[<i>]: status gap but not listed in gaps[]`
- `provenance head <name> does not match kb/meta.json`
- counts line: `N entries, S sourced, G gaps, L listed gaps, E errors`

`gaps`, `open_questions` and `myopia_check` are exempt from the third error only: a finding or a
question may be recorded before anything sources it. Everything else must cite, be a gap, or say
proposed.
