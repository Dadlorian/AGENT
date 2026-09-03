#!/usr/bin/env python3
"""Out-of-process half of adapters/second.py's compiled checker.

Reads {"schema", "instance"} as JSON on stdin, compiles the schema in this
child process, checks the instance, and writes {"errors", "keywords_checked"}
as JSON on stdout. A separate process is spawned per call because the compiled
closures in second.py cannot be pickled across a process boundary -- exactly
the cost a real out-of-process compiled validator would also pay on a cold
schema. Standard library only; no import of the parent module's package state.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from interface import TYPES, ValidationError, _ptr_push          # noqa: E402
from adapters.second import compile_node                          # noqa: E402


def main() -> int:
    payload = json.loads(sys.stdin.buffer.read())
    schema, instance = payload["schema"], payload["instance"]
    compiled = compile_node(schema, schema)
    counter = [0]
    errs = compiled(instance, "", "#", counter)
    sys.stdout.write(json.dumps({"errors": [e.as_dict() for e in errs], "keywords_checked": counter[0]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
