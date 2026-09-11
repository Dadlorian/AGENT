#!/usr/bin/env python3
"""Flag unoptimized token patterns in agent-facing text BEFORE a workload is fired.

Run wf_8d4230e8-999 spent 1,110,376,052 tokens against an 11M estimate and was stopped by the
owner mid-run. Nothing warned anyone. This is that warning, and it is cheap: it reads prompts and
briefs, never a model.

THE COST MODEL IT CHECKS AGAINST
--------------------------------
    cost  ~=  agents x turns x prefix

`cache_read` is re-billed on EVERY assistant turn at the full prefix size. Measured on that run:
cache_read 97.8% of spend, cache_creation 2.1%, output 0.07%. The governing ratio is
cache_read/cache_creation = how many times the average token was billed again: 46.0 overall,
opus 54.3, sonnet 39.0, haiku 13.9. That ordering tracks TURN-HEAVINESS, not model price --
haiku searched and wrote one file; opus ran write/render/validate/fix/revalidate per facet.

So a token admitted at turn T of ~46 is billed roughly (46 - T) more times. A line in a prompt
telling an agent to read a 16k-token file is not a 16k decision.

WHAT IT CANNOT SEE
------------------
Only text. It cannot count an agent's actual turns or measure a real prefix, because no artifact
in this repo records either -- cost.json has totals per model and nothing per agent. Every
projection below is `size x multiplier x agents` arithmetic shown in full, not a measurement.
Treat a finding as a question to answer, never as a verdict.

  python3 tools/token_review.py                 scan the agent-facing corpus
  python3 tools/token_review.py <file> [...]    scan specific files
  python3 tools/token_review.py --patterns      print the pattern list and the mechanisms
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = [ROOT / "state" / "briefs", ROOT / "state" / "loop-workflow.js",
          ROOT / "state" / "author-brief.md", ROOT / "state" / "author-prompt-round.md"]

MULTIPLIER = 46.0        # cache_read / cache_creation, measured on wf_8d4230e8-999
TOK = 4                  # bytes per token, rough

# Large shared artifacts. A prompt that says "read <this>" without a slice admits the whole file
# into every agent's prefix, where it is re-billed on every turn.
BIG = ["state/lessons.jsonl", "kb/research.jsonl", "PASS.md", "TARGET.md", "bridge.md",
       "CLAUDE.md", "docs/reference/knowledge-pool.md", "STATUS.md", "README.md"]

# Work a script already does deterministically. Paying a model to execute it buys nothing and
# costs a full-prefix turn each time.
PROCEDURAL = [
    (r"git\s+(?:add|commit|push)", "git operations -- tools/checkpoint.sh does this, with a "
                                   "flock and a refusal on red"),
    (r"validate_skills\.py", "validation -- a script call between phases, not an agent turn"),
    (r"render_skill\.py", "rendering -- deterministic from skill.json"),
    (r"kb\.py\s+(?:verify|ledger-verify|merge-research)", "kb maintenance -- a script call"),
    (r"skill_graph\.py|examples_index\.py|acceptance_check\.py", "index regeneration -- derived output"),
    (r"ceremony[- ]number|highest\s+ceremony|max\(ls", "ceremony numbering -- tools/ceremony_next.py "
                                                       "reads it off disk"),
    (r"retry\s+\d+\s+times\s+with", "retry/backoff spelled out in prose -- the script owns this"),
]

SELF_REPORT = (r"Return JSON:\s*ok\b|\bok:\s*\{?\s*type:\s*'boolean'|schema:\s*SUMMARY",
               "agent self-reports pass/fail -- a gate's exit code is evidence, a summary is not "
               "(bridge.md section 3)")

FORKABLE = (r"subagent_type\s*[:=]\s*['\"]general-purpose|one\s+agent\s+per|launch\s+\d+\s+agents?",
            "fan-out without naming fork -- forks inherit the captain's context and skip "
            "rediscovery; fresh agents each rebuild it")

MECHANISMS = """Mechanisms available in this harness, and what each actually saves:

  fork (Agent subagent_type "fork")
      Inherits the parent's full context. Saves REDISCOVERY -- the tool calls and orientation
      turns that rebuild what the captain already knows. Does NOT save carriage: a fork pays the
      whole inherited prefix on every one of its own turns, so three forks off a large captain
      cost three times that prefix. Fork after the recon, from a deliberately small captain.
      Constraint: a fork always runs the parent's model and effort; a model override is ignored.

  workflow resume (Workflow scriptPath + resumeFromRunId)
      Replay, not rewind. The longest unchanged prefix of agent() calls returns cached results
      instantly; only the first edited or new call and everything after it runs live. It moves a
      workflow FORWARD without re-running finished stages. It does not restore any context.

  /rewind (owner-invoked slash command, NOT callable by the model)
      "Restore the code and/or conversation to a previous point." The genuine rewind: the
      transcript returns to an earlier state. For token economy choose CONVERSATION ONLY, so the
      working tree survives. Explore, fail, learn, rewind, continue in a small context -- the dead
      ends are paid for once instead of carried at x46 forever. Precondition: every finding must
      already be on disk, because a conversation-only rewind discards whatever lived only in the
      transcript. The model's job is to write findings down continuously and to SAY when context
      has filled with dead ends, since the owner cannot see that from outside.

  subagent firebreak (Agent / fork, then keep only the return)
      The prospective twin of /rewind, and model-invocable. The subagent burns its own context on
      the iteration and returns a short answer, so the flailing never enters the parent at all.
      Verify the artifact it produced, never its report (bridge.md section 3).

  continue an existing agent (SendMessage to its id)
      Keeps one agent's prefix warm across successive questions instead of paying a cold start
      per question. The read-once-then-ask-repeatedly shape.

  per-agent tiering (Workflow agent opts.model / opts.effort)
      The only place model AND effort are settable per call. The plain Agent tool takes a model
      override but inherits session effort; fork takes neither.

  background (run_in_background)
      Parallelism, not a token saving. Included so it is not mistaken for one."""


def tokens_of(rel: str) -> int:
    p = ROOT / rel
    return (os.path.getsize(p) // TOK) if p.is_file() else 0


def scan(path: Path) -> list:
    try:
        text = path.read_text()
    except Exception:
        return []
    rel = str(path.relative_to(ROOT))
    out = []
    for artifact in BIG:
        name = re.escape(os.path.basename(artifact))
        # The window is 220 chars, not 60: prompts list several files after one "Read", and the
        # largest offender in this repo sits 78 characters past it. A 60-char window missed the
        # single biggest item on the first run of this tool.
        # `[^\n]`, not `[^.\n]`: the intervening text contains dots (paths, `${args.brief}`),
        # and excluding them silently dropped the single largest offender in this repo.
        for m in re.finditer(rf"read[^\n]{{0,220}}?{name}|{name}[^\n]{{0,30}}\bwhole\b", text, re.I):
            line = text[:m.start()].count("\n") + 1
            sliced = re.search(r"grep|sed -n|head|tail|slice|the entries about|lines?\s+\d",
                               text[max(0, m.start() - 200):m.end() + 200], re.I)
            if sliced:
                continue
            t = tokens_of(artifact)
            out.append({"at": f"{rel}:{line}", "kind": "whole-file read", "detail": artifact,
                        "tokens": t,
                        "why": f"~{t:,} tokens admitted to every agent's prefix; at the measured "
                               f"x{MULTIPLIER:.0f} re-billing that projects to ~{int(t*MULTIPLIER):,} "
                               f"per agent. Slice it with grep or sed -n instead."})
    for pattern, why in PROCEDURAL:
        for m in re.finditer(pattern, text, re.I):
            line = text[:m.start()].count("\n") + 1
            out.append({"at": f"{rel}:{line}", "kind": "procedure in a prompt",
                        "detail": m.group(0)[:44], "tokens": 0, "why": why})
    for pattern, why in (SELF_REPORT, FORKABLE):
        for m in re.finditer(pattern, text):
            line = text[:m.start()].count("\n") + 1
            kind = "self-report" if pattern is SELF_REPORT[0] else "fan-out shape"
            out.append({"at": f"{rel}:{line}", "kind": kind, "detail": m.group(0)[:44],
                        "tokens": 0, "why": why})
    return out


def main() -> int:
    if "--patterns" in sys.argv:
        print(MECHANISMS)
        print("\nPatterns flagged: whole-file read of a large shared artifact; procedure in a "
              "prompt;\nagent self-report where a gate could decide; fan-out that does not name "
              "fork.")
        return 0
    args = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    files = []
    for src in (args or CORPUS):
        src = src if src.is_absolute() else ROOT / src
        files += sorted(src.rglob("*.md")) + sorted(src.rglob("*.js")) if src.is_dir() else [src]
    files = [f for f in files if f.is_file()]

    findings = []
    for f in files:
        findings += scan(f)
    by_kind = {}
    for f in findings:
        by_kind.setdefault(f["kind"], []).append(f)

    for kind in sorted(by_kind, key=lambda k: -len(by_kind[k])):
        rows = by_kind[kind]
        print(f"\n{kind.upper()}  ({len(rows)})")
        seen = set()
        for r in sorted(rows, key=lambda r: r["at"]):
            key = (r["at"].split(":")[0], r["detail"])
            if key in seen:
                continue
            seen.add(key)
            print(f"  {r['at']:46} {r['detail']}")
            print(f"      {r['why']}")

    worst = sorted({(f["detail"], f["tokens"]) for f in findings if f["tokens"]},
                   key=lambda x: -x[1])
    if worst:
        print("\nLargest artifacts admitted whole, by projected per-agent cost at "
              f"x{MULTIPLIER:.0f}:")
        for name, t in worst[:5]:
            print(f"  {name:38} ~{t:>7,} tok  ->  ~{int(t*MULTIPLIER):>10,} per agent")
    print(f"\n{len(findings)} finding(s) across {len(files)} file(s). "
          f"Projections are size x {MULTIPLIER:.0f} x agents arithmetic, not measurements - "
          f"no artifact records per-agent turns or prefix.")
    print("Nothing here blocks. It exists so a workload is not fired without seeing this first.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
