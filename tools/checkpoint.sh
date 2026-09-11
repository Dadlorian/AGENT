#!/usr/bin/env bash
# Serialized checkpoint for a night run (STATUS rows 75, 76): one commit at a time, checks first, push with retries.
# Usage: bash tools/checkpoint.sh "<label>" <path> [<path> ...]
set -u
cd "$(dirname "$0")/.."
label="$1"; shift
exec 9>state/checkpoint.lock
flock 9
python3 tools/validate_skills.py >/tmp/ck_validate.txt 2>&1 || { echo "CHECKPOINT REFUSED: validator red"; tail -3 /tmp/ck_validate.txt; exit 1; }
python3 tools/kb.py verify >/tmp/ck_kb.txt 2>&1 || { echo "CHECKPOINT REFUSED: kb verify red"; tail -2 /tmp/ck_kb.txt; exit 1; }
# `git add -- <paths>` fails WHOLESALE on one bad pathspec, and swallowing that error made a
# silent no-op indistinguishable from "nothing changed": on 2026-09-11 a checkpoint reported
# "nothing to commit" for a phase with 26 modified files, because one path in the list named
# docs/reference/egress-log.jsonl and the file is kb/egress-log.jsonl. Refuse loudly instead.
if ! git add -- "$@" kb/ledger.jsonl 2>/tmp/ck_add.txt; then
  echo "CHECKPOINT REFUSED: git add failed -- nothing was staged"; sed -n '1,4p' /tmp/ck_add.txt; exit 1
fi
if git diff --cached --quiet; then echo "checkpoint: nothing to commit for $label"; exit 0; fi
# Attribution comes from the environment, never hardcoded: a fixed URL here stamped every
# session's commits with one session's id, so the trail claimed work the named session never did.
trailer=""
[ -n "${CLAUDE_SESSION_URL:-}" ] && trailer="

Claude-Session: ${CLAUDE_SESSION_URL}"
git commit -q -m "$label${trailer}" || { echo "CHECKPOINT REFUSED: commit failed"; exit 1; }
for d in 2 4 8 16; do git push -u origin claude/auto-skill-creation-i8javu >/dev/null 2>&1 && { echo "checkpoint: $label committed and pushed ($(git rev-parse --short HEAD))"; exit 0; }; sleep $d; done
echo "checkpoint: $label committed, push failed after retries ($(git rev-parse --short HEAD))"; exit 0
