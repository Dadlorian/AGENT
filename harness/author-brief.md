# Harness author brief

Work in /home/user/AGENT. Read OWNER.md first, then this file, harness/plan.json (your harness's row), TARGET.md T6, T7, T9.6, the skill.json of your owner_skill and co_skills (contract, adapters, definition_of_done), the blueprint tool entry and impact rows for your component (grep docs/architecture/blueprint.json), and examples/end-to-end/run.py as prior art for style. Do not commit or push. Never invent a URL, version, endpoint, or fact: cite kb ids (python3 tools/kb.py show <id>) in provenance.json; anything else is marked proposed.

Deliver under harness/<name>/:
- interface.py: the capability interface only: dataclasses or TypedDicts for the request, result, and problem shapes, and an abstract adapter class with the operations the owner skill's contract names. No product names.
- adapters/dryrun.py: a deterministic in-process adapter that runs here with no network; implements the whole interface; exercises the failure path too.
- adapters/live.py: the adapter for today's component from PASS.md Part A, reached only through environment variables named in README (endpoint, key, socket path); product names allowed here and nowhere else; must import nothing unavailable here (use urllib/subprocess; guard imports).
- adapters/second.py: the second adapter from plan.json's second_adapter, with a different execution model; it may be a faithful stub if the component is not reachable, but its shape and swap procedure must be real.
- call.py: the minimal call a caller writes (under 40 lines of caller code): build the envelope from cap-consumption's shape, choose the adapter by ADAPTER=dryrun|live|second, run the minimal_call from plan.json, print the result table. Cross-cutting stamps (correlation id, budget ceiling, idempotency key, actor) are applied by call.py without the caller asking.
- conformance.py: the conformance run every adapter must pass: the same cases against any adapter; used for the swap proof.
- test.sh: dry-run: conformance against dryrun, then a swap proof (conformance before with dryrun, swap to second, conformance after; both must pass), then one deliberate breakage that fails; exit 0 only if all hold. --live: the same against live, skipped with a clear message when env vars are unset. Must pass here in dry-run.
- README.md: tables only: files; the minimal call; env vars for live; what each test proves; what would pin (from the blueprint) and how the adapter boundary avoids it.
- provenance.json: {"owner_skill","co_skills","blueprint_tool_entry","kb_ids":[...],"research_ids":[...],"standard","measured":{"dryrun":"...","swap":"...","breakage":"..."},"claimed":["live mode until run on the host"]}.
Then: bash harness/<name>/test.sh (record the output), python3 tools/kb.py ledger '{"kind":"harness","harness":"<name>","agent":"...","result":"<test.sh last line>","status":"measured"}'.
Keep it simple (T3): a newcomer follows one call in ten minutes. Reply in under 80 words: files, test.sh result, swap proof result, what is claimed.
