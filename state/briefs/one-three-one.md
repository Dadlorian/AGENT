# Brief: 3-1-3-1, and the token model underneath it

Three engineers each produce a 1-3-1; a judge stitches. Nine solutions, three recommendations,
one plan. TARGET.md T5.2 defines the unit: *"define the problem, identify the three best possible
solutions that align to the goal, and follow the recommendation."* T5.3 handles a tie: drop the
two lowest, find two more, repeat.

This brief also carries the cost model, because the first time this repo ran a large fan-out it
spent 1,110,376,052 tokens against an 11M estimate and the owner stopped it mid-run.

## The cost model — learn this before designing any fan-out

```
cost  ≈  agents × turns × prefix
```

`cache_read` is re-billed on EVERY assistant turn at the full prefix size. Measured on run
`wf_8d4230e8-999` (docs/night/cost.json):

| | |
|---|---|
| total | 1,110,376,052 tokens over 129 agents |
| cache_read | 1,085,944,829 — **97.8%** |
| cache_creation | 23,632,106 — 2.1% |
| output | 775,167 — 0.07% |
| unique context per agent | 183,194 tokens — an ordinary working set |
| **cache_read ÷ cache_creation** | **×46.0** — times the average token was re-billed |

Per model: opus ×54.3, sonnet ×39.0, haiku ×13.9. That ordering is not about model price; it
tracks **turn-heaviness**. Haiku searched and wrote one file. Opus ran
write → render → validate → fix → revalidate, per facet, per item. Every iteration re-charged the
whole prefix.

**The run did not cost 1.11B because agents read too much once. It cost that because they
re-read it 46 times each.**

### What fork does and does not do

`subagent_type: "fork"` inherits the parent's context, so forks skip rediscovery — the tool calls
and orientation turns that rebuild what the captain already knows. That is real, and it is a
saving on `cache_creation` plus some turns.

**It is not a lever on the 97.8%.** A fork pays the full inherited prefix on every one of its own
turns. Forking three children off a large captain multiplies that prefix by three. So:

> Fork *after* the recon, and only from a captain whose context you have deliberately kept small.
> Forking off a long session is a cost multiplier, not a saving.

`state/briefs/captain.md` has said "keep it small" since 2026-09-03 — one day before the 1.11B
run. The rule was written; nothing checked it. That is why it did not hold.

### The rule that generalises

> **Spawn an agent to DISCOVER a category. Never to APPLY one.**

Every application the night run paid a model for — ceremony numbering, committing, validating,
rendering, aggregating — was a category someone had already discovered and written down. The
improve prompt specifies `git push` "retry 4 times with 2s,4s,8s,16s backoff"; `tools/checkpoint.sh`
already implements that exact backoff, with a `flock` and a refusal on red.

The inverse held too: research, the step every citation rests on, ran at `model: 'haiku',
effort: 'medium'` with a retry branch for when it came back thin.

## Running a 3-1-3-1

1. **Recon once, in the captain.** Gather the evidence yourself. Read the artifacts, compute the
   numbers, verify the claims. This is the prefix every engineer inherits — keep it to what all
   three need.
2. **Fork three engineers, one angle each.** Give each a genuinely different lens; three agents
   asked the same question return one answer three times. Angles that worked here: context
   economics, orchestration shape, work decomposition. Tell each one explicitly: *do not re-read
   what is already in your context; that duplication is the defect under review.*
3. **Bind them to evidence.** Never invent a number, path or quote; name the source of every
   figure; say "not derivable from the artifacts" rather than estimating; mark unsupported claims
   proposed.
4. **Verify before you synthesise.** A subagent's report is not evidence — check the artifact.
   In this run all three engineers independently overturned the captain's own stated premise
   about fork, and two load-bearing claims needed checking on disk before they could be repeated.
5. **Judge: stitch, do not pick.** The convergence across angles is the signal. Where they
   disagree, the disagreement is the finding.

## Measurable target

`cache_read ÷ cache_creation` **below 20**, from 46.0. Computable from a run's cost record alone,
needs no transcripts, and falls only if turns or prefix actually fall.

**Instrument first.** No artifact records per-agent turn count or context composition — only what
it cost. Every optimisation beyond "move procedure into the script" is unverifiable until a run
records those two numbers.

## What this review cost

Three forks, 1,114,311 tokens — 0.1% of the 1,110,376,052 it analysed.
