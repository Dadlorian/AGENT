---
name: build-evidence-record
description: The discipline of recording claimed versus measured evidence, so a reader can tell what was observed from what was believed. Load whenever you are about to record a definition-of-done outcome or an entry in the evidence store, label a check as passing, upgrade a claim to a measurement, cite evidence inside a skill, or reconcile a measurement that contradicts what the design says: it fixes what an evidence record contains (what was run, the code version and tree hash under test, whether the tree was dirty, the output, the status label), how records are appended and chained so an edit is detectable, and what a contradicting measurement obliges you to do.
---

# build-evidence-record

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| Record what was actually run, against which code version, and what came back, so a claim is never laundered into a measurement by rewording. agentic-stack fixes the claimed-versus-measured distinction for the whole repository (F-part-c-08); this discipline carries the record that makes a label checkable. | sourced | `F-part-c-08`, `F-a5-04` "Distinguish **claimed** from **measured** throughout" |

## Entities

| Entity |
|---|
| `E-provisioning-concern-evidence-store` |
| `E-provisioning-concern-task-store` |
| `E-provisioning-concern-deployment-phases` |
| `E-finding-a7-1` |
| `E-finding-a7-2` |
| `E-finding-a7-3` |
| `E-concern-provenance` |
| `E-constraint-c-constraint-202` |

## Contract

### Shapes (JSON Schema 2020-12)

**evidence-record (proposed shape; summary - the full schema with per-field constraints and the dirty-tree rule is in references/evidence-record-shape.md)** (proposed; sources: `F-a5-04`, `F-part-c-08`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "evidence-record",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "id",
    "recorded_at",
    "claim",
    "ran",
    "code_version",
    "output",
    "status",
    "prev",
    "hash"
  ],
  "properties": {
    "id": {
      "type": "string"
    },
    "recorded_at": {
      "type": "string",
      "format": "date-time"
    },
    "claim": {
      "type": "string",
      "minLength": 1
    },
    "ran": {
      "type": "object",
      "required": [
        "command",
        "script_sha256"
      ]
    },
    "code_version": {
      "type": "object",
      "required": [
        "commit",
        "tree_hash",
        "tree_dirty"
      ]
    },
    "output": {
      "type": "object",
      "required": [
        "exit_status",
        "text"
      ]
    },
    "status": {
      "enum": [
        "claimed",
        "measured"
      ]
    },
    "supersedes": {
      "type": [
        "string",
        "null"
      ]
    },
    "prev": {
      "type": "string"
    },
    "hash": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$"
    }
  }
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| Every record names what was run and the code version it ran against: the hash of the script and the commit. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit" |
| Every record names the tree that was actually under test and whether that tree was dirty, because a dirty tree is not the commit. | sourced | `F-a5-04` "tree hash under test, and whether the tree was dirty" |
| Every record carries exactly one status label, claimed or measured, per the claimed-versus-measured rule agentic-stack states for the whole repository (F-part-c-08). An absent label is a defect, not a default. | sourced | `F-part-c-08`, `E-constraint-c-constraint-202` "Distinguish **claimed** from **measured** throughout" |
| Proposed: a result produced from a dirty tree may never carry the label measured, because nobody else can reproduce the tree it ran against. Research query: unresearched beyond the dirty flag the evidence store already records (F-a5-04); no prior-art search has been run for the reproducibility rationale specifically. | proposed | `F-a5-04` "whether the tree was dirty" |
| The store is append-only. A record is never edited or deleted; a correction is a new record naming the id of the one it supersedes. | sourced | `F-a5-04` "Append-only JSONL" |
| records are chained the way the hash-chained task store agentic-stack cites is (F-a5-03), so that each run's closing digest is the next run's opening digest and a manual edit between runs is detectable. | sourced | `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| Proposed: the record holds the output as observed, with its exit status, not a summary of it. A summary cannot be re-read against a later run. Research query: unresearched; our own convention, no prior-art search has been run for a raw-output-over-summary requirement in evidence record keeping. | proposed | - |
| Proposed: measured is a property of an attached run, not of confidence. A record with no run attached is claimed by construction, however certain its author is. Research query: unresearched; our own convention, no prior-art search has been run for a run-attachment (versus author confidence) definition of a measured label. | proposed | - |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| This discipline does not produce a signed attestation for a third party. It records what happened for a reader of this repo; attributing an artifact to the code, inputs and actor that produced it, verifiable with a tool we did not write, is the provenance concern's job and is deliberately kept separate. | sourced | `F-b4-05`, `E-concern-provenance` "verifiable with a tool we did not write" |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Write the claim down before you run anything, in the words you intend to publish, and give it a record id. Research query: unresearched; our own convention, no prior-art search has been run for a write-the-claim-before-the-run requirement in evidence or audit-trail record keeping. | Proposed: our convention. A claim written after the output is read is shaped by the output, and the record can no longer show what was believed beforehand. | proposed | - |
| 2 | Capture run identity before the run and record it as data, not as a description: the exact command, the SHA-256 of the script it invoked, the commit, the hash of the tree actually under test, and whether that tree was dirty. | These are the fields the evidence store already records. A description cannot be re-run, the script hash pins the thing that produced the output after the script changes, and the dirty flag separates a reproducible result from an unreproducible one. | sourced | `F-a5-04` "Each record names the script SHA-256, git commit, tree hash under test, and whether the tree was dirty" |
| 3 | Capture the output as observed, with its exit status, into the record. Truncate at the end if you must; do not paraphrase, reorder, or clean it up. Research query: unresearched; our own convention, no prior-art search has been run for a no-paraphrase raw-output-capture rule in evidence record keeping. | Proposed: our convention. The record's only job is to let a later reader see what you saw, including the parts that did not fit the claim. | proposed | - |
| 4 | Label the record claimed or measured. Use measured only when this record carries a run: a command, a code version, a clean tree, an exit status and the output. Everything else, including a confident inference, is claimed. | The point of the two labels, which agentic-stack fixes for the whole repository (F-part-c-08), is that a reader can separate what was observed from what was believed; this record is where that separation is written down field by field. | sourced | `F-part-c-08` "Distinguish **claimed** from **measured** throughout" |
| 5 | Refuse the label measured when the tree was dirty. Append the record as claimed and say in the claim text that the tree was dirty; re-run on a clean tree if the measurement matters. Research query: unresearched beyond the dirty flag the evidence store already records (F-a5-04); no prior-art search has been run for a reproducibility-gated label specifically. | Proposed: our convention, following the dirty flag the evidence store records. A result nobody can reproduce is a report of an event, not a measurement of the code. | proposed | `F-a5-04` "whether the tree was dirty" |
| 6 | Correct a record only by appending another, since the evidence store is append-only JSONL: to upgrade a claim to measured, append a record that attaches a run; when a measurement contradicts a claim, append the measurement. Either way name the old record's id in supersedes, and never rewrite, reword or delete the record being corrected. | Proposed: our convention on an append-only store. An in-place relabel leaves no trace of when a belief became an observation, and each recorded finding invalidates a design that looks correct on paper, so the superseded claim is what shows the next reader which paper-correct designs have already failed. | sourced | `F-a5-04`, `F-a7-01` "Append-only JSONL" |
| 7 | Append every record, chain it to its predecessor, and carry the closing digest of a run into the opening digest of the next. | A chain of the kind agentic-stack cites from the task store (F-a5-03) makes a manual edit between runs detectable, which is what stops a record being quietly improved after the fact. | sourced | `F-a5-03` "each run's closing digest is the next run's opening digest, so a manual edit between runs is detectable" |
| 8 | Verify the chain and the source hash with `python3 tools/kb.py verify` before citing any record, stop if it fails, and cite as one or more kb ids plus a quote copied character for character out of one cited record via `python3 tools/kb.py show <id>`. Research query: unresearched beyond the task store's own chain-verification property (F-a5-03); no prior-art search has been run for cite-then-verify as a citation discipline specifically. | Proposed: our convention. An unverified record is a claim about a record, and a restatement from memory is how a claim acquires the authority of a measurement it never had. | proposed | `F-a5-03` "a manual edit between runs is detectable" |
| 9 | Scope the measured label to what the run observed, and no wider: name the property that was checked, not the property you hope it stands for. | agentic-stack records the well-formedness finding A7.2 (F-a7-03): a pipeline can run green with every behavioural stage skipped, and those establish well-formedness, not correctness. The consequence for a label is that measured covers only what the run observed. | sourced | `F-a7-03` "Those establish well-formedness, not correctness" |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Record what the receiving side reported, not what was sent: injected context was ignored downstream and a depth-3 task tree produced three unrelated root traces, so a record of the injection would have been evidence of nothing. | sourced | `F-a7-02`, `E-finding-a7-1` "A depth-3 task tree produces three unrelated root traces." |
| Measure the runtime effect, not the file you wrote: agentic-stack records the runtime-effect finding A7.3 (F-a7-04), where configuration written in the documented place validated, reviewed correctly, and had no runtime effect at all. | sourced | `F-a7-04`, `E-finding-a7-3` "Values written to YAML validated, reviewed correctly, and had no runtime effect" |
| Treat an automated verification that reports all currently green as a claim about the check until a record attaches the run that produced it. | sourced | `F-a5-02` "each with automated verification, all currently green" |
| Say where and when a measurement was taken, the way the inventory does when it says it was verified against the running host on 2026-09-03; a measurement with no place and no date cannot be re-taken. | sourced | `F-meta-02` "verified against the running host on 2026-09-03" |
| prefer few records that each name their code version to many that do not. A store of ~2,445 records across 308 runs is worth only the fraction of records whose run identity is complete. | sourced | `F-a5-04` "~2,445 records across 308 runs" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | python3 tools/kb.py verify && python3 -c "import json;rs=[json.loads(l) for l in open('kb/facts.jsonl')];assert rs and all(r.get('status') for r in rs);print('labels ok',len(rs))" |
| Expected | Measured by tools/measure.py at 710e7b4: exit 0; last lines: kb verified: chains intact, source hash matches, every fact matches its lines, rebuild is identical \| labels ok 109 |
| Deliberate breakage | Two, applied one at a time to kb/facts.jsonl and then restored: (a) mismatched hash — change one character of record F-a5-04's text ('Append-only' to 'Append-Only') so the record no longer hashes to its stored digest; (b) missing status — delete the status field from record F-a5-04. |
| Expected failure | Measured by tools/measure.py at 710e7b4: exit 1; last lines: FAIL: chain broken at facts F-a5-04 \| kb verification FAILED |
| Status | measured |
| Evidence | `F-part-c-04` "A criterion nothing can fail is not a criterion" |

## Composes with

Builds on: `agentic-stack`

Used by: `build-entry-conformance`, `cap-agent-runtime-implement`, `cap-capability-packaging-implement`, `cap-capability-registry-implement`, `cap-document-validation-implement`, `cap-durable-execution-implement`, `cap-errors-implement`, `cap-evaluation`, `cap-evaluation-implement`, `cap-human-interaction-implement`, `cap-idempotency-implement`, `cap-identity-implement`, `cap-isolation-implement`, `cap-mandate-broker-implement`, `cap-memory-implement`, `cap-model-access-implement`, `cap-policy-implement`, `cap-provenance`, `cap-provenance-implement`, `cap-scheduling-implement`, `cap-state-persistence-implement`, `cap-telemetry-implement`, `cap-tool-access-implement`, `cap-work-intake-implement`, `compose-agent-implement`, `compose-approval-implement`, `compose-improvement-loop`, `compose-improvement-loop-implement`, `compose-loop`, `compose-loop-implement`, `compose-operators-implement`, `core-document-implement`, `core-graph-implement`, `core-judge-implement`, `core-ledger-implement`, `core-planner-implement`, `seam-dispatch`, `seam-dispatch-implement`, `seam-state`, `seam-state-implement`, `xc-audit-trail`, `xc-audit-trail-implement`, `xc-budget-implement`, `xc-compensation-implement`, `xc-correlation`, `xc-correlation-implement`, `xc-enforcement-chain-implement`, `xc-idempotency-lease-implement`, `xc-identity-delegation-implement`, `xc-policy-gate-implement`, `xc-provenance-chain`, `xc-provenance-chain-implement`, `xc-tenancy-implement`, `xc-typed-errors-implement`

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| Are the records in the evidence store chained, or only appended? The source states append-only for the evidence store and hash-chaining only for the task store, so the chain invariant here is ours rather than a description of what runs. | Reading the evidence store on the running host and checking whether each record carries a predecessor digest; this agent has no access to that host, so nothing here can be measured. | The chain requirement is recorded as proposed, and an evidence record is treated as unverified until a chain verification passes. | `F-a5-04`, `F-a5-03` "Append-only JSONL" |
| What counts as the tree hash when the run touches files outside the repository, for example a configuration read from the host? | A run recorded twice with the same commit and tree hash but different host state, showing whether the outputs diverge; the divergence would decide whether host state must be a required field. | Proposed: such a run is labelled claimed, and the record names the outside input it depended on. | `F-a7-04` "had no runtime effect" |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96 |
