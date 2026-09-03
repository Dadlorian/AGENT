# cap-state-persistence: the caller's view

Proposed. Folded in from the former `cap-state-persistence-use` skill on 2026-09-03 (consolidation, part A), which was removed because the caller-facing material belongs to the skill that owns the contract. The body of `cap-state-persistence` is enough to call the capability; open this file for the worked calls, the caller's minimal inputs and outputs, and the worked rejection in full.

The caller doctrine that every capability repeated - all four entries of TARGET T6.2 arriving through one shape, failures read as RFC 9457 problem details rather than parsed prose, composing upward instead of adding arguments, changing configuration instead of branching on what answered, and the cross-cutting guarantees that cannot be requested or declined - is stated once in `cap-consumption` and is not repeated here. 1 row(s) of that kind were dropped in the fold: size-of-surface.

Every statement below carries the origin and the knowledge-base evidence it had in the folded skill. Ids resolve with `python3 tools/kb.py show <id>`.

## What this facet promised

- cap-state-persistence fixes the contract this rests on (F-b5-05); this facet reduces it to what a caller does, which is almost nothing: keep the head you are handed, read back at it, and ask for a proof when you will have to defend an answer.  
  _sourced_ - `F-b5-05`, `T-t3-01` "the query surface a planner needs"

## Minimal inputs and outputs

| Call | You supply | You read back | Origin | Evidence |
|---|---|---|---|---|
| get a head (proposed) | nothing extra; you send the envelope you were already sending, through whichever entry you already use | your result, plus one opaque value on it: the head your work was recorded at. That value is the whole caller-side surface of this capability | proposed | `F-b5-05` |
| read back at a head (proposed) | a head you were handed and what you want to know | the answer as of that head, and the same answer at that head forever, whatever anyone has written since; you never have to reason about whether a concurrent writer changed your answer mid-question | proposed | `F-b5-05`, `F-b1-06` |
| ask for a proof (proposed) | the record id of something you will have to defend, and the head you hold | a small proof you can keep, forward and check with a verifier of your own; you never need the log, our reader, or our permission to check it later | proposed | `X-cross-structure-052` |

## The three ways in, and what a swap leaves untouched

Both rows are carried in the body of `cap-state-persistence` as invariants, so they are not repeated here: TARGET T1's three ways in reach this capability through the same call, and enhancing one aspect of the implementation changes nothing a caller wrote.

## Worked examples

### Worked example 1 (proposed): a result that tells you where it was recorded

_proposed_ - sources: `F-b5-05`.

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

### Worked example 2 (proposed): reading back, and keeping a proof

_proposed_ - sources: `X-cross-structure-052`, `F-b5-05`.

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

### The failure shape (proposed): what a refused write or an unverifiable record looks like

_proposed_ - sources: `F-b4-07`.  Also carried in the body of `cap-state-persistence` as the failure shape.

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

## What a caller does

Step 1 below is carried in the body of `cap-state-persistence` as an instruction; the rest are the caller-side steps that were specific to this capability.

- **Read the head off the result and keep it next to whatever you do with the answer. One opaque value, stored once.**  
  _why:_ Proposed. The head is the only thing that makes a later question answerable in the same terms as the original one; a result kept without its head can be re-read only at whatever the store looks like at the time you ask, which is a different question wearing the same words.  
  _proposed_ - `F-b5-05`
- **Ask every follow-up question at that head, not at now. If you genuinely want the current state, resolve a fresh head first and say so.**  
  _why:_ agentic-stack states design rule 5 (F-b1-06), that planning is a pure function and completes before execution begins; the consequence for a caller is that a read is deterministic at a head, which is what lets a plan be a function of what it read. Mixing a pinned read with an unpinned one inside the same piece of work produces two answers that were both true and cannot both be acted on.  
  _sourced_ - `F-b5-05`, `F-b1-06` "Planning is a pure function and completes before execution begins"
- **For anything you may have to defend later, ask for a proof and keep the proof itself, not a link to it.**  
  _why:_ cap-state-persistence sets the criterion (X-cross-structure-052) that a valid log can be cryptographically verified by any third-party; the consequence for a caller is that a proof you hold survives losing access to us, and a pointer into our store does not. The proof also stays small as the store grows, so keeping it is not a storage decision.  
  _sourced_ - `X-cross-structure-052` "a valid log can be cryptographically verified by any third-party"
- **Handle exactly two failures, both in the failure shape above: a moved head, which you retry after re-reading the head, and a record that will not verify, which you never retry and instead report.**  
  _why:_ Proposed. The media type, the registry and the retryable field belong to cap-errors, so a caller that already branches on type and retryable needs no new logic here beyond recognising two more registered types; retrying an unverifiable record produces the same answer and hides the one event worth escalating.  
  _proposed_ - `F-b4-07`
- **Do not mirror platform state into a store of your own and read from that. Keep the head, keep proofs, and ask again.**  
  _why:_ Proposed. A mirror is a fold you now maintain by hand: it drifts on the first record you did not know to copy, and it cannot be proved, which means the copy you would show someone is the one thing nobody can check. Reading again at a head you already hold costs one call and answers the same question.  
  _proposed_ - `F-b2-06`
- **Proposed: to see the starting state for yourself, run examples/end-to-end. Its ledger is append-only and hash-chained and its chain verifies, and it emits no record ids, no proofs and no sealed heads, which is the honest gap this capability closes.**  
  _why:_ Proposed, and it is the shortest route from this page to something running: the reference runner needs no services and no network, and what it shows is the real distance between a chain that our reader checks and a proof you could keep.  
  _proposed_ - -

## Other caller invariants

- That sameness is the guarantee, not a coincidence of the current build: state, telemetry, and every cross-cutting concern are managed across the entire structure, whichever entry point was used. A caller therefore never asks whether its entry kind gets durability, and never carries a code path for the case where it does not.  
  _sourced_ - `T-t2-03` "State, telemetry, and every cross-cutting concern are managed across the entire structure"
- Proposed: a head is a promise about answers, not a grant of access. Reading at a head you are not entitled to read returns a typed failure rather than a different answer, and a head whose bodies have passed their retention window returns tombstones rather than silently different data; identity, policy and retention decide what you may see, and none of them may change what the head means.  
  _proposed_ - `F-b5-05`, `F-b1-08`
- Proposed: proofs compose the way results do. A workflow, a loop or an agent that ran steps on your behalf leaves one record per step under one sealed head, so a caller who kept the run's head can still get a proof about any individual step later without having watched the run happen or having stored anything but that head.  
  _proposed_ - `T-t2-03`, `X-cross-structure-052`

## Caller practices

- Proposed: store the head with the decision it justified, not in a log line. Six months later the question is not what the store said, it is what you acted on and whether that was what the store said; only the pair answers it.  
  _proposed_ - `F-b5-05`
- Proposed: treat a moved head as ordinary rather than exceptional. It means someone else got there first, which is the store working; the fix is to re-read the head and decide again, not to retry the same write harder or to widen a lock you do not hold.  
  _proposed_ - `X-cross-structure-048`
- Do not treat the store's own report as the check. A store is tamper-evident and not tamper-proof, so what you keep is a proof that lets you notice an edit, and the noticing only happens if something of yours re-checks it rather than reading a green line from us.  
  _sourced_ - `X-cross-structure-053` "tamper-evident but not tamper-proof"
- Ask for the answer rather than the events when the platform can fold for you: instead of storing the current state of your entities, you persist every state change as an immutable event, so a caller pulling raw records to sum them is rebuilding a fold the store already computes, and will get a different total the first time a record kind changes.  
  _sourced_ - `X-cross-structure-047` "Instead of storing the current state of your entities, you persist every state change as an immutable event"

## Open questions carried over

- **The reference runner presents its hash-chained ledger as the durable record and verifies it with `python3 run.py --verify-ledger`, which is our own reader rehashing our own file.**  
  _deciding evidence:_ Measured on 2026-09-03: the corpus holds 56 records across 4 runs, the chain verifies, and there are zero content-addressed record ids, zero inclusion proofs and zero sealed heads, so nothing a caller could keep and check elsewhere is produced. That is integrity for us; the capability's criterion is a proof a third party can check.  
  _default until then:_ Recorded as a disagreement with examples/end-to-end rather than resolved here. The change proposed is the first two stages cap-state-persistence-implement already sequences, applied to the reference runner: keep `--verify-ledger` as the chain check it is, add a `record_id` over canonical bytes and a `head-sealed` record per run, and put a caller-visible head on the result, so the example shows the shape this skill describes rather than only its first half.  
  `F-a5-03`, `F-b5-05` "Today a JSONL file with a hash chain"
- **Which problem types does this capability raise, given that the first-cut registry in docs/decomposition.md section 2.1.6 has no state rows?**  
  _deciding evidence:_ Whether any registered type already fits: the closest are document-invalid, which is about schema validation, and budget-exhausted, which is about spend. Neither is about an append that lost a race or a proof that will not reconstruct a root.  
  _default until then:_ Proposed: add two rows, head-moved at 409 and retryable, and record-unverifiable at 422 and not retryable, as the failure shape above shows. cap-errors owns the registry, so the rows land there and this skill cites them; until they do, both types are proposed and unregistered.  
  `F-b4-07`

