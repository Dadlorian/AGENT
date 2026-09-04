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
git add -- "$@" kb/ledger.jsonl 2>/dev/null
if git diff --cached --quiet; then echo "checkpoint: nothing to commit for $label"; exit 0; fi
git commit -q -m "$label

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01XDYnrM4HZbMdASzsqN4j96" || { echo "CHECKPOINT REFUSED: commit failed"; exit 1; }
for d in 2 4 8 16; do git push -u origin claude/auto-skill-creation-i8javu >/dev/null 2>&1 && { echo "checkpoint: $label committed and pushed ($(git rev-parse --short HEAD))"; exit 0; }; sleep $d; done
echo "checkpoint: $label committed, push failed after retries ($(git rev-parse --short HEAD))"; exit 0
