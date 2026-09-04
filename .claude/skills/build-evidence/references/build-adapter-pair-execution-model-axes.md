# Execution-model axes for scoring a second adapter

Proposed. This file is ours (derived from `docs/decomposition.md` section 4); it is not in PASS.md.
Read it when a candidate second adapter feels different but you cannot name the axis, or when
reviewing a pair whose difference field reads as a vendor name rather than a property.

Adapters are named here only by knowledge-base entity id. Resolve one with
`python3 tools/kb.py show <id>`.

## The axes

Score the adapter that runs today and the candidate on each axis. Record the axis name and both
values in the pair's `differs_in_execution_model` field. A candidate that scores identically on
every axis is rejected, however different its vendor.

| Axis | Question | Example values |
|---|---|---|
| Start and teardown cost | What does it cost to get to the first useful instruction, and to reclaim everything after? | boot of a full machine image; process spawn; instantiation of a linear-memory module |
| Processes required for progress | How many separate things must be running for one unit of work to advance? | zero beyond the caller; one co-located store; one remote server that can be unreachable |
| Call shape | Does the call return a result or a claim ticket? | synchronous result; ticket plus poll; stream of events with a terminal frame |
| Cancellation | Can the caller stop work already committed, and how promptly? | promptly mid-operation; only by abandoning the ticket; not at all, with a separate settlement call |
| Where durability lives | What makes a step survive a crash? | a transaction committed with the step's own effect; a replayed history on a separate server; an immutable object write |
| Verification cost and locality | What does it cost to prove one record, and who can do it? | rehash the whole log, holder only; a logarithmic proof any third party can check |
| Resource grant model | What is the unit the adapter is given, and what is denied by default? | a machine configuration with devices and a network stack; a capability list with no ambient authority |
| Determinism requirement | Must caller code be replay-deterministic for the adapter to work? | required; irrelevant |

An axis that is really a vendor difference (packaging, licence, hosting provider, config file format,
client library shape) does not count. If the only entry you can fill in is one of those, the pair is
a same-shape pair.

## The wrapper test

A second adapter that delegates to the first proves nothing, even when its axis values are copied in
by hand. Three checks, all cheap:

1. **Dependency direction.** Does the second adapter's build depend, transitively, on the first
   adapter's implementation package or its running service? If yes, reject.
2. **Kill the first.** Run the conformance suite against the second adapter with the first adapter's
   process, service and files made unavailable. A wrapper fails to start; a real second adapter passes.
3. **Axis divergence.** At least one axis value must differ, and the difference must be one a caller
   could observe through the interface — a latency class, a failure mode, a cancellation outcome,
   a proof shape.

## Worked pair, by entity id

`E-capability-state-persistence` is the clearest small example, because the two candidates differ on
axes a vendor swap never touches.

- Today: `E-adapter-jsonl-hash-chain`. Verification cost: rehash from the beginning, whole artifact
  present, one reader-writer locality. Durability: an append to one file.
- Second: `E-swap-candidate-object-store`. Verification cost: a proof about one record against a head,
  checkable by a party that does not hold the log. Durability: an immutable object write with no
  in-place append.

What the pair forces the interface to say: *give me a proof about this record at this head*, not
*rehash the log*. A method named `rehash_all()` is unimplementable against the second adapter and is
therefore a file-format detail, not a state-persistence concept. The property being preserved across
the swap is the chain, not the file (`F-b5-05`).

The same reading applies to `E-capability-isolation`, whose row PASS.md names as the template for the
whole table (`F-b3-18`), and to `E-capability-durable-execution`, where the "processes required for
progress" axis is the one that matters (`F-a6-02`, defined but not running).
