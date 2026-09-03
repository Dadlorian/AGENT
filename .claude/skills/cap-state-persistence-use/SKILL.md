---
name: cap-state-persistence-use
description: How to use the State persistence capability as a caller: send what you were going to send, get back a result that carries the head your work was recorded at, read anything back at that head and get the same answer forever, and ask for a proof about a single record that you can keep and check somewhere else. Load it when you need a result to still be defensible next quarter, when two reads of the same thing disagreed, when you are about to cache platform state in your own database, when a retry might duplicate what a previous attempt already wrote, or when someone asks you to show that a record has not been altered. Also load it before writing code that reads the store's file, table or bucket directly.
---

# cap-state-persistence-use

Rendered from `skill.json` by `tools/render_skill.py`. Do not edit by hand. Source IDs resolve with `python3 tools/kb.py show <id>`.

## Purpose

| Statement | Origin | Evidence |
|---|---|---|
| cap-state-persistence fixes the contract this rests on (F-b5-05); this facet reduces it to what a caller does, which is almost nothing: keep the head you are handed, read back at it, and ask for a proof when you will have to defend an answer. | sourced | `F-b5-05`, `T-t3-01` "the query surface a planner needs" |

## Entities

| Entity |
|---|
| `E-capability-state-persistence` |
| `E-seam-state` |

## Contract

### Operations

| Operation | Input | Output | Origin | Evidence |
|---|---|---|---|---|
| get a head (proposed) | nothing extra; you send the envelope you were already sending, through whichever entry you already use | your result, plus one opaque value on it: the head your work was recorded at. That value is the whole caller-side surface of this capability | proposed | `F-b5-05` |
| read back at a head (proposed) | a head you were handed and what you want to know | the answer as of that head, and the same answer at that head forever, whatever anyone has written since; you never have to reason about whether a concurrent writer changed your answer mid-question | proposed | `F-b5-05`, `F-b1-06` |
| ask for a proof (proposed) | the record id of something you will have to defend, and the head you hold | a small proof you can keep, forward and check with a verifier of your own; you never need the log, our reader, or our permission to check it later | proposed | `X-cross-structure-052` |

### Shapes (JSON Schema 2020-12)

**Worked example 1 (proposed): a result that tells you where it was recorded** (proposed; sources: `F-b5-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:example:result",
  "title": "What comes back",
  "description": "Send entries/human.json as usual. The result carries the head your run closed at, and a record id per step. Proposed: the reference runner emits a chain head today and no record id or proof, which is exactly what the definition of done below measures.",
  "examples": [
    {
      "run_id": "run-human-0001",
      "state": "completed",
      "recorded_at_head": {
        "partition": "run-human-0001",
        "size": 14,
        "chain_digest": "sha256:d096193c95c1957c983632e11f317e52c2c4b5877d90a04f8020c4a9154f1bf2",
        "root_hash": "sha256:<tree root at that size>",
        "sealed_at": "2026-09-03T09:12:14Z"
      },
      "your_next_step": "keep recorded_at_head; every later question you ask about this run is asked at it"
    }
  ]
}
```

**Worked example 2 (proposed): reading back, and keeping a proof** (proposed; sources: `X-cross-structure-052`, `F-b5-05`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:example:read-and-prove",
  "title": "Two calls, one of which you keep",
  "description": "Proposed. Ask what a step cost, at the head you kept, and get the same number a year from now. Then ask for a proof of the one record you will have to defend, and store the proof next to your own copy of the answer. The proof is a few hundred bytes and does not grow with the store.",
  "examples": [
    {
      "read_at": {
        "at_head": "sha256:d096193c95c1957c983632e11f317e52c2c4b5877d90a04f8020c4a9154f1bf2",
        "ask": "cost_micros for step fix#2",
        "answer": 61200,
        "stable": "same head, same answer, forever"
      },
      "prove": {
        "record_id": "sha256:0c7ac1524c7ab5870f1018b8f3547b8b4c6324ebedc61530354010f890d6b716",
        "returns": {
          "leaf_index": 9,
          "path": [
            "sha256:...",
            "sha256:...",
            "sha256:..."
          ]
        },
        "your_next_step": "keep the proof and the head; check them later with any verifier, ours unreachable"
      }
    }
  ]
}
```

**The failure shape (proposed): what a refused write or an unverifiable record looks like** (proposed; sources: `F-b4-07`)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic:state:example:problem",
  "title": "Problem details from this capability",
  "$ref": "urn:agentic:problem:0.1",
  "description": "Proposed. Failures arrive as RFC 9457 problem details with media type application/problem+json, the shape cap-errors owns; nothing here returns a bare status or a message to be parsed. Both types below are proposed and need rows in that registry before anything may raise them. The distinction that matters to a caller is retryable: a lost race is retried after re-reading the head, a broken chain never is. Both are proposed and pending registration in docs/decomposition.md section 2.1.6, the closed registry cap-errors owns: until the rows land an implementation returns `idempotency-conflict` for `urn:agentic:problem:head-moved` and `document-invalid` for `urn:agentic:problem:record-unverifiable`, accepting that `idempotency-conflict` is not retryable while a lost race is, which is itself the argument for the head-moved row.",
  "examples": [
    {
      "type": "urn:agentic:problem:head-moved",
      "title": "Another writer advanced the head first",
      "status": 409,
      "detail": "expected head sha256:d09619... but the current head is sha256:50873a...",
      "retryable": true
    },
    {
      "type": "urn:agentic:problem:record-unverifiable",
      "title": "The proof does not check out against the head you supplied",
      "status": 422,
      "detail": "inclusion proof for sha256:0c7ac1... does not reconstruct root sha256:...",
      "retryable": false
    }
  ]
}
```

### Invariants

| Invariant | Origin | Evidence |
|---|---|---|
| All three of TARGET T1's ways in reach this the same way. A human must be able to enter the system, an agent must be able to enter the system, and an internal or external event must be able to enter the system; each gets back a head of the same shape over a store of the same kind, and nothing you can do with that head depends on which of the three you were. | sourced | `T-t1-01`, `T-t1-02`, `T-t1-03` "3. An internal or external event must be able to enter the system." |
| That sameness is the guarantee, not a coincidence of the current build: state, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used. A caller therefore never asks whether its entry kind gets durability, and never carries a code path for the case where it does not. | sourced | `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure" |
| Composability allows enhancing particular aspects of any element without touching the rest, and here that is concrete: the store can move from a local file to content-addressed objects, gain proofs, gain a lease and change its retention classes, and a caller holding a head and a proof changes nothing, because a head and a proof are the only things it was ever given. | sourced | `T-t2-02` "Composability allows enhancing particular aspects of any element without touching the rest." |
| The surface stays at one opaque value because it cannot be daunting or overly complex, or no one will use it. A caller asked to choose a consistency level, name a partition or manage a snapshot would eventually stop reading back at a head at all, and would then be arguing about which of two answers was real. | sourced | `T-t3-02`, `T-t3-01` "It cannot be daunting or overly complex, or no one will use it." |
| Proposed: a head is a promise about answers, not a grant of access. Reading at a head you are not entitled to read returns a typed failure rather than a different answer, and a head whose bodies have passed their retention window returns tombstones rather than silently different data; identity, policy and retention decide what you may see, and none of them may change what the head means. | proposed | `F-b5-05`, `F-b1-08` |
| Proposed: proofs compose the way results do. A workflow, a loop or an agent that ran steps on your behalf leaves one record per step under one sealed head, so a caller who kept the run's head can still get a proof about any individual step later without having watched the run happen or having stored anything but that head. | proposed | `T-t2-03`, `X-cross-structure-052` |

### Deliberately not exposed

| Item | Origin | Evidence |
|---|---|---|
| Proposed: you never learn which adapter stored your record, whether it is a line in a file or an object under a content address, or where that lives. cap-state-persistence keeps the medium out of the contract; the consequence for a caller is that there is no path, table name or bucket to write down, and therefore no code of yours to change when the store is swapped. | proposed | `F-b3-17` |
| Proposed: there is no call that hands you the whole log, and asking for one is the request this interface is designed to refuse. Whatever you were going to do by scanning everything is either a read at a head or a proof about one record, and both stay the same size as the store grows. | proposed | `F-b5-05` |

## Instructions

| Step | Action | Why | Origin | Evidence |
|---|---|---|---|---|
| 1 | Send what you were already sending. There is no durability option, no consistency level and no store to name; nothing about persistence is something you opt into. | Proposed usage of the placement cap-state-persistence fixes. The platform applies this rather than offering it, so a caller-side switch would be a hole rather than a feature, and a caller that could turn it off would eventually be the reason a run cannot be reconstructed. | proposed | `F-b1-08` |
| 2 | Read the head off the result and keep it next to whatever you do with the answer. One opaque value, stored once. | Proposed. The head is the only thing that makes a later question answerable in the same terms as the original one; a result kept without its head can be re-read only at whatever the store looks like at the time you ask, which is a different question wearing the same words. | proposed | `F-b5-05` |
| 3 | Ask every follow-up question at that head, not at now. If you genuinely want the current state, resolve a fresh head first and say so. | agentic-stack states design rule 5 (F-b1-06), that planning is a pure function and completes before execution begins; the consequence for a caller is that a read is deterministic at a head, which is what lets a plan be a function of what it read. Mixing a pinned read with an unpinned one inside the same piece of work produces two answers that were both true and cannot both be acted on. | sourced | `F-b5-05`, `F-b1-06` "Planning is a pure function and completes before execution begins" |
| 4 | For anything you may have to defend later, ask for a proof and keep the proof itself, not a link to it. | cap-state-persistence sets the criterion (X-cross-structure-052) that a valid log can be cryptographically verified by any third-party; the consequence for a caller is that a proof you hold survives losing access to us, and a pointer into our store does not. The proof also stays small as the store grows, so keeping it is not a storage decision. | sourced | `X-cross-structure-052` "a valid log can be cryptographically verified by any third-party" |
| 5 | Handle exactly two failures, both in the failure shape above: a moved head, which you retry after re-reading the head, and a record that will not verify, which you never retry and instead report. | Proposed. The media type, the registry and the retryable field belong to cap-errors, so a caller that already branches on type and retryable needs no new logic here beyond recognising two more registered types; retrying an unverifiable record produces the same answer and hides the one event worth escalating. | proposed | `F-b4-07` |
| 6 | Do not mirror platform state into a store of your own and read from that. Keep the head, keep proofs, and ask again. | Proposed. A mirror is a fold you now maintain by hand: it drifts on the first record you did not know to copy, and it cannot be proved, which means the copy you would show someone is the one thing nobody can check. Reading again at a head you already hold costs one call and answers the same question. | proposed | `F-b2-06` |
| 7 | Proposed: to see the starting state for yourself, run examples/end-to-end. Its ledger is append-only and hash-chained and its chain verifies, and it emits no record ids, no proofs and no sealed heads, which is the honest gap this capability closes. | Proposed, and it is the shortest route from this page to something running: the reference runner needs no services and no network, and what it shows is the real distance between a chain that our reader checks and a proof you could keep. | proposed | - |

## Best practices

| Practice | Origin | Evidence |
|---|---|---|
| Proposed: store the head with the decision it justified, not in a log line. Six months later the question is not what the store said, it is what you acted on and whether that was what the store said; only the pair answers it. | proposed | `F-b5-05` |
| Proposed: treat a moved head as ordinary rather than exceptional. It means someone else got there first, which is the store working; the fix is to re-read the head and decide again, not to retry the same write harder or to widen a lock you do not hold. | proposed | `X-cross-structure-048` |
| Do not treat the store's own report as the check. A store is tamper-evident and not tamper-proof, so what you keep is a proof that lets you notice an edit, and the noticing only happens if something of yours re-checks it rather than reading a green line from us. | sourced | `X-cross-structure-053` "tamper-evident but not tamper-proof" |
| Ask for the answer rather than the events when the platform can fold for you: instead of storing the current state of your entities, you persist every state change as an immutable event, so a caller pulling raw records to sum them is rebuilding a fold the store already computes, and will get a different total the first time a record kind changes. | sourced | `X-cross-structure-047` "Instead of storing the current state of your entities, you persist every state change as an immutable event" |

## Definition of done

| Field | Value |
|---|---|
| Criterion | `cd examples/end-to-end && bash test.sh` to produce the corpus, then the caller-side state assertion over the store it appended to: `python3 -c "import json,hashlib,sys;from run import canonical;r=[json.loads(l) for l in open('out/ledger.jsonl')];prev='sha256:'+'0'*64;brk=-1 for i,rec in enumerate(r):     body={k:v for k,v in rec.items() if k!='hash'}     want='sha256:'+hashlib.sha256((prev+canonical(body)).encode()).hexdigest()     if rec['prev']!=prev or rec['hash']!=want: brk=i; break     prev=rec['hash'] runs=len({x['run_id'] for x in r});cid=sum(1 for x in r if 'record_id' in x);prf=sum(1 for x in r if 'inclusion_proof' in x);seal=sum(1 for x in r if x.get('kind')=='head-sealed');print(f'records={len(r)} runs={runs} chain_break_at={brk} content_addressed={cid} inclusion_proofs={prf} sealed_heads={seal} consistency_proofs_expected={runs-1}');sys.exit(0 if brk==-1 and prf==len(r) and seal==runs else 1)"`. It asserts what a caller is promised: the chain is unbroken, every record has an identity that does not depend on its position, every record can be proved on its own, and every run closes with a sealed head that carries continuity to the next. |
| Expected | test.sh exits 0 and prints `passed 29, failed 0`; the assertion prints `records=56 runs=4 chain_break_at=-1 content_addressed=0 inclusion_proofs=0 sealed_heads=0 consistency_proofs_expected=3` and exits 1. That is the correct starting state, not a pass: the chain half is delivered today and the proof half is delivered nowhere, so this check starts red by construction and turns green only when cap-state-persistence-implement's identity, tree and sealed-head stages land. |
| Deliberate breakage | Row P16's breakage, on the store that exists: copy examples/end-to-end elsewhere and edit one record body in place with `sed '5s/"cost_micros": [0-9]*/"cost_micros": 1/' out/ledger.jsonl > out/broken.jsonl`, then re-run the identical assertion against `out/broken.jsonl`. Change nothing else. |
| Expected failure | The assertion prints `records=56 runs=4 chain_break_at=4 content_addressed=0 inclusion_proofs=0 sealed_heads=0 consistency_proofs_expected=3` and exits 1: the break index moves from -1 to 4, naming the edited record, while the three zero counters do not move. The half of the promise that is delivered fails loudly and the half that is not stays silently absent, which is why the criterion asserts on both. Measured in session cap-state-persistence 2831cb4f on 2026-09-03: both runs were performed, the broken run against a copy of examples/end-to-end in this session's scratchpad directory, and the repository tree was left unmodified (out/ledger.jsonl sha256 87f6d76d540a9c69746a1904e2a6aac47e74efadc770e3d526331083b3c78dd6). |
| Status | measured |
| Evidence | `F-b5-05`, `F-a5-03` "The chain is the valuable idea and should survive; the file is not" |

## Composes with

Builds on: `cap-state-persistence`, `cap-state-persistence-implement`

Used by: -

## Open questions

| Question | Deciding evidence | Default until then | Evidence |
|---|---|---|---|
| The reference runner presents its hash-chained ledger as the durable record and verifies it with `python3 run.py --verify-ledger`, which is our own reader rehashing our own file. | Measured on 2026-09-03: the corpus holds 56 records across 4 runs, the chain verifies, and there are zero content-addressed record ids, zero inclusion proofs and zero sealed heads, so nothing a caller could keep and check elsewhere is produced. That is integrity for us; the capability's criterion is a proof a third party can check. | Recorded as a disagreement with examples/end-to-end rather than resolved here. The change proposed is the first two stages cap-state-persistence-implement already sequences, applied to the reference runner: keep `--verify-ledger` as the chain check it is, add a `record_id` over canonical bytes and a `head-sealed` record per run, and put a caller-visible head on the result, so the example shows the shape this skill describes rather than only its first half. | `F-a5-03`, `F-b5-05` "Today a JSONL file with a hash chain" |
| Which problem types does this capability raise, given that the first-cut registry in docs/decomposition.md section 2.1.6 has no state rows? | Whether any registered type already fits: the closest are document-invalid, which is about schema validation, and budget-exhausted, which is about spend. Neither is about an append that lost a race or a proof that will not reconstruct a root. | Proposed: add two rows, head-moved at 409 and retryable, and record-unverifiable at 422 and not retryable, as the failure shape above shows. cap-errors owns the registry, so the rows land there and this skill cites them; until they do, both types are proposed and unregistered. | `F-b4-07` |

## Provenance

| Field | Value |
|---|---|
| PASS.md sha256 | cfe8ca287e66ec24c6a317e394937b1dbdce2f2e0ddfe6ee49ac34846ef03b96 |
| kb facts head | 9cf193b3b5fc00700bd36c572e0a2bff3c7a7b9512b94d22fbb6e6d78a24c04e |
| kb entities head | 747fc34d69f35eba6092afb9af0ff7bd4df64f577da79e1e58cfba21e4859604 |
| kb edges head | a14cd00838048f03ae4c25794163429bce87c24794c70f6949dc42ce444c1dc6 |
| Author | session cap-state-persistence 2831cb4f, 2026-09-03 |
