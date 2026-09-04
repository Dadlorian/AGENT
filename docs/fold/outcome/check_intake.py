#!/usr/bin/env python3
"""Grade an entry envelope against the platform's own entry schema (examples/end-to-end/schemas/entry.schema.json) and cap-work-intake's rule that the producer's fields do not leak to the top level."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
schema = json.loads((ROOT / "examples/end-to-end/schemas/entry.schema.json").read_text())
e = json.loads(Path(sys.argv[1]).read_text())
req = schema.get("required", [])
props = set(schema.get("properties", {}).keys())
checks = {f"required field {r}": r in e for r in req}
checks["no field outside the schema at top level"] = set(e.keys()) <= props if props else True
checks["kind names the door"] = str(e.get("kind", "")).lower() in {"event", "external", "human", "schedule"} or str(e.get("entry", {}).get("kind", "")).lower() in {"event", "external", "human", "schedule"}
checks["producer payload kept under payload, not spread"] = "invoice_id" not in e and "amount_cents" not in e
checks["idempotency key present"] = any("idempot" in k.lower() for k in json.dumps(e).replace("{", " ").replace('"', " ").split())
checks["correlation present"] = "correlation" in json.dumps(e).lower()
for k, v in checks.items():
    print(("ok  " if v else "FAIL"), k)
print(f"{sum(checks.values())} of {len(checks)}")
sys.exit(0 if all(checks.values()) else 1)
