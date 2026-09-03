#!/usr/bin/env python3
"""Live adapter for the tenancy component on this host today: there is none.

PASS.md A6 records "No identity field anywhere in the system" (F-a6-05), and
no fact anywhere in PASS.md names a tenant or a principal - tenancy as such
is absent from the substrate, exactly as xc-tenancy-implement's purpose
states. The nearest measured analogues are the per-VM uid jail, `0700` and
owned by a per-VM uid with no passwd entry, verified live (F-a3-06), and the
per-group scoped LiteLLM virtual key carrying a hard budget cap, verified to
terminate spend rather than merely record it (F-a4-07). Neither carries a
principal concept: the jail scopes a VM, the key scopes a routing class.

So this binding's write, read and recall operations say so, with a typed
refusal, rather than imply a tenancy-scoped store answered. Its spend
operation is the one place a real measured component exists to reach: the
per-group virtual key's budget. It queries that key's own remaining budget
and refuses the spend, scoped to that key alone, when the spend would exceed
it - the same shape F-a4-07 records as verified, reused here as evidence
that a per-principal ceiling terminating only that principal's spend already
runs for an unrelated reason (routing class, not tenant).

Reached only through the environment variables in README.md:

  TENANCY_STORE_URL     where a tenancy-scoped write/read/recall store would
                         be reached; unset today, because none exists
  TENANCY_BUDGET_URL    the key-info endpoint of the virtual-key budget
                         component (LiteLLM today, F-a4-07)
  TENANCY_BUDGET_TOKEN  the admin credential for that endpoint

The request and response shapes below (`GET {url}/key/info?key=...` ->
`{"info": {"spend": ..., "max_budget": ...}}`) are proposed, not fetched from
a live document: no request in this file has ever reached an endpoint from
this environment, so they stay claimed until run on the host.

Standard library only; the import is guarded so this module never breaks a
dry run on a host with no network stack.
"""
from __future__ import annotations

import json
import os
import urllib.parse

from interface import Problem, TenancyAdapter

try:                                   # guarded: absence is a typed failure, never an import crash
    import urllib.error
    import urllib.request
    URLLIB = urllib.request
except Exception:                      # pragma: no cover
    URLLIB = None

ABSENT_STORE = ("PASS.md A6 records no identity field anywhere in the system, and no fact names a "
                "tenant: nothing on this host writes, reads or recalls by principal. Point "
                "TENANCY_STORE_URL at a tenancy-scoped store and run this again")


class LiveTenancyAdapter(TenancyAdapter):
    entity = "the tenancy component on this host (absent today; the per-group virtual-key budget cap answers spend)"
    report_adapter = "absent-store-with-live-budget-key"
    locus_of_the_tenant_boundary = "unmeasured for write/read/recall; a per-group virtual key for spend"
    failure_mode_of_a_wrong_or_missing_principal = "adapter-unavailable for write/read/recall; a 403 refusal for spend"
    provisioning_cost_of_a_new_principal = "unmeasured: no provisioning path for a tenancy-scoped store exists here"

    def _write(self, principal, key, value, context):
        raise Problem("adapter-unavailable", ABSENT_STORE, what_is_missing="tenancy-scoped store")

    def _read(self, principal, key, context):
        raise Problem("adapter-unavailable", ABSENT_STORE, what_is_missing="tenancy-scoped store")

    def _recall(self, principal, context):
        raise Problem("adapter-unavailable", ABSENT_STORE, what_is_missing="tenancy-scoped store")

    def _spend(self, principal, target_principal, amount_micros, context):
        if target_principal != principal:
            raise Problem("cross-tenant-denied",
                          f"a spend by {principal!r} named a different target principal {target_principal!r}",
                          rule_id="tenancy-scope")
        if URLLIB is None:
            raise Problem("adapter-unavailable", "urllib is unavailable in this environment", retry_after_s=30)
        url = self._env("TENANCY_BUDGET_URL")
        token = self._env("TENANCY_BUDGET_TOKEN")
        headers = {"authorization": "Bearer " + token,
                   "x-correlation-id": os.environ.get("CORRELATION_ID", "corr-harness-xc-tenancy"),
                   "x-run-id": context.get("run_id", "run-harness-xc-tenancy")}
        query = urllib.parse.urlencode({"key": target_principal})
        try:
            with URLLIB.urlopen(URLLIB.Request(f"{url}/key/info?{query}", headers=headers),
                                timeout=int(os.environ.get("TENANCY_TIMEOUT_S", "30"))) as response:
                doc = json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read()[:400].decode("utf-8", "replace")
            raise Problem("adapter-unavailable", f"HTTP {exc.code}: {detail}", retry_after_s=30) from exc
        except Exception as exc:
            raise Problem("adapter-unavailable", f"{type(exc).__name__}: {exc}", retry_after_s=30) from exc
        info = doc.get("info") or {}
        spend, max_budget = info.get("spend"), info.get("max_budget")
        if max_budget is None:
            raise Problem("adapter-unavailable",
                          f"the budget key {target_principal!r} carries no max_budget; nothing was charged")
        remaining_micros = int((max_budget - (spend or 0)) * 1_000_000)
        if amount_micros > remaining_micros:
            raise Problem("budget-exceeded",
                          f"{target_principal!r}'s own ceiling ({remaining_micros} micros) was exceeded by a "
                          f"spend of {amount_micros}; only that principal's unit is terminated",
                          principal=target_principal, remaining_micros=remaining_micros)
        return remaining_micros - amount_micros

    def _env(self, name: str) -> str:
        value = os.environ.get(name)
        if not value:
            raise Problem("adapter-unavailable", f"{name} is not set; {ABSENT_STORE}")
        return value


# The one name every adapter module exports: the entry point of this module.
Adapter = LiveTenancyAdapter
