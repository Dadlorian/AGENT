#!/usr/bin/env python3
"""Grade a problem body against cap-errors: registered type, RFC 9457 members, retry decision readable without prose, correlation present."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
reg = (ROOT / ".claude/skills/cap-errors/references/problem-registry.md").read_text()
suffixes = set(re.findall(r"^\| `([a-z][a-z0-9-]+)` \|", reg, re.M)) | set(re.findall(r"urn:agentic:problem:([a-z][a-z0-9-]+)", reg))
p = json.loads(Path(sys.argv[1]).read_text())
checks = {
    "type is a URI": isinstance(p.get("type"), str) and p["type"].startswith(("urn:", "http")),
    "type suffix is in the closed registry": isinstance(p.get("type"), str) and p["type"].rsplit(":", 1)[-1] in suffixes,
    "title present": bool(p.get("title")),
    "status is an int": isinstance(p.get("status"), int),
    "detail present": bool(p.get("detail")),
    "retryable is a boolean member": isinstance(p.get("retryable"), bool),
    "correlation or run id present": any(k in p for k in ("correlation_id", "run_id", "correlation")),
    "no stack trace or log line": not re.search(r"Traceback|\bat [A-Za-z_.]+\(|\.py:\d+", json.dumps(p)),
    "policy rule or decision named": any(k in json.dumps(p).lower() for k in ("rule", "policy", "decision")),
}
for k, v in checks.items():
    print(("ok  " if v else "FAIL"), k)
print(f"{sum(checks.values())} of {len(checks)}")
sys.exit(0 if all(checks.values()) else 1)
