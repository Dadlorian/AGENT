# The shape of an adapter-parameterised conformance run

Proposed. This file is ours; it is not in PASS.md. It was lifted out of the 31 `*-implement`
skills, where the same paragraph had been written once per capability (consolidation part B,
`kb/ceremonies/implement-clusters.json`, cluster C3). Read it when you are writing the runner
that proves a pair, or reviewing one whose report you cannot compare across adapters.

The skill body is enough to choose and justify a second adapter without this file.

## One command, one report

- **One command** runs the whole suite. Selecting the adapter is a flag or an environment value
  that the runner passes to the binding, never a different command, a different suite, or an
  edited file. If the two adapters need two commands, the swap is not a configuration change and
  the pair has already failed the test build-adapter-pair states.
- **One report shape** for every adapter. The same field names, the same counters, the same
  ordering, so two runs diff cleanly. An adapter that cannot serve a case declares it in
  `unsupported` and the counter stays visible; it does not silently drop the case.
- **`selected_by`** records how the serving adapter was chosen - `configuration` is the only
  value a passing run may carry. Anything else (a code edit, an import switch, a test-only
  subclass) is the finding.
- **The adapter that actually answered** is read back off the run itself - a marker the running
  adapter emits, the value on the result, the refusal that came back - and recorded beside
  `selected_by`. Configuration that was written and had no runtime effect is a measured failure
  mode in this repository, so a report that only echoes the binding proves nothing about which
  implementation served.
- **Counters, not log lines.** Every assertion counts things actually checked (cases run,
  fixtures rejected, adapters exercised) and each named counter must be non-zero, per
  build-definition-of-done. A run with zero behavioural assertions is inconclusive, not green.

## Suggested fields

| Field | Meaning |
|---|---|
| `command` | The exact command, re-runnable by someone else |
| `adapter_declared` | Which adapter the binding record selected |
| `selected_by` | How it was selected; `configuration` for a passing run |
| `adapter_observed` | Which adapter the run observed answering |
| `cases_run`, `cases_passed`, `cases_failed` | Counted assertions, all named, none zero by accident |
| `unsupported` | Cases an adapter declares it cannot serve, with the reason |
| `differs_in_execution_model` | The axis and both values, from `references/execution-model-axes.md` |
| `status` | `claimed` until an evidence record attaches the run, then `measured` |

## Where the run is recorded

The run itself is written as an evidence record: build-evidence-record fixes what that record
contains (the command, the code version, the tree hash under test, whether the tree was dirty,
the output) and when the pair may stop being labelled `claimed`. Do not restate those fields in
a report format of your own.
