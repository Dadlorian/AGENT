# intake — bounded interrogation to a dispatchable package

A questioning service asks; an agent relays in ordinary language and maps replies back to stable
question ids; the service decides what to ask next and **when to stop**. Output is a requirements
package another model turns into assignments. Intake and dispatch stay separate.

| File | Role | Edit? |
|---|---|---|
| `SPEC.md` | the protocol: layers, question space, termination proof, answer record, state, dispatch seam, tool surface, errors | ✅ the source of truth |
| `termination.py` | runnable evidence for §4 — the bound, the phase transition, the deliberate breakage | ✅ |
| `vectors.jsonl` | 18 conformance vectors, one per L1 rule | ✅ add when a rule is added |
| `check_vectors.py` | reference checker for the L1 rules; grades the vectors | ✅ |

## Run the gates

```
python3 intake/check_vectors.py        # 18 passed, 0 failed
python3 intake/termination.py --prove  # bound = 52 advancing rounds, holds on every seed
```

Both breakages must fail, or the gates check nothing:

```
python3 intake/check_vectors.py --break-order   # exit 1, isolates V03
python3 intake/termination.py --break-i1        # exit 1, 0/25 terminate at p >= 0.55
python3 intake/termination.py --sweep           # the phase transition at p = 0.5
```

## The one idea

**The protocol is provable; the content is not.** 14 of the 20 rules are decidable from stored
state, and every one of them governs the *trace* — which question, at which revision, answered by
whom, applied exactly once. Every undecidable rule governs *meaning*. A package is therefore
evidence of how it was collected, never evidence that it is right, and §1 of the spec makes that
split load-bearing rather than apologetic.

The second idea follows: the loop terminates because the question space is **pinned finite at session
start**, and an unknown answer yields a *requirement*, never a new question. Without that, intake is a
branching process that halts only while the user knows more than half the answers.
