#!/usr/bin/env python3
"""Dry-run adapter: today's substrate - one shared keyspace, a principal
column filtered at read, recall and spend time.

PASS.md A6 records no identity field anywhere in the system (F-a6-05); no
fact names a tenant. This is what a principal column is added to, not an
incumbent that already enforces one - modelled beside the per-VM uid jail
(F-a3-06) and the per-group scoped budget key (F-a4-07), neither of which
carries a tenant concept, sitting over the single hash-chained log every
run's records fold into (F-b3-17). "Shared database with shared schema" in
the research on file (X-xc-tenancy-001).

The filter is one `!=` comparison per operation, below. There is no
environment knob that disables it - a caller cannot decline this guarantee
any more than any other (F-b1-08) - so the deliberate breakage this
harness's test.sh runs works the only honest way: on a copy, it edits this
file's read path to drop the comparison, and runs the untouched original
beside it. That is the point of the pair: the second adapter's isolation has
no filter to drop, so the same edit made there would have nothing to remove.

Deterministic, in process, no network. Standard library only.
"""
from __future__ import annotations

from interface import Problem, TenancyAdapter

DEFAULT_CEILING_MICROS = 500_000


class DryRunTenancyAdapter(TenancyAdapter):
    entity = "dry-run in-process shared keyspace"
    report_adapter = "shared-keyspace-principal-column"
    locus_of_the_tenant_boundary = "a principal column filtered at read time within one shared keyspace"
    failure_mode_of_a_wrong_or_missing_principal = "returns another principal's rows if the filter is dropped"
    provisioning_cost_of_a_new_principal = "a new principal needs only a new value in an existing column"

    def __init__(self):
        super().__init__()
        self._store: dict[str, dict] = {}          # key -> {"principal": ..., "value": ...}  (one shared dict)
        self._budgets: dict[str, int] = {}          # principal -> remaining micros (one shared dict)

    def _write(self, principal, key, value, context):
        self._store[key] = {"principal": principal, "value": value}
        return {"key": key, "principal": principal}

    def _read(self, principal, key, context):
        rec = self._store.get(key)
        if rec is None:
            raise Problem("document-invalid", f"no such key {key!r}", key=key)
        if rec["principal"] != principal:            # the filter: the line the breakage removes
            raise Problem("cross-tenant-denied",
                          f"key {key!r} belongs to a different principal than the requesting actor",
                          key=key, rule_id="tenancy-scope")
        return rec["value"]

    def _recall(self, principal, context):
        return sorted(key for key, rec in self._store.items() if rec["principal"] == principal)

    def _spend(self, principal, target_principal, amount_micros, context):
        if target_principal != principal:             # the filter: the line the breakage removes
            raise Problem("cross-tenant-denied",
                          f"a spend by {principal!r} named a different target principal {target_principal!r}",
                          rule_id="tenancy-scope")
        balance = self._budgets.setdefault(target_principal, DEFAULT_CEILING_MICROS)
        if amount_micros > balance:
            raise Problem("budget-exceeded",
                          f"{target_principal!r}'s own ceiling ({balance} micros) was exceeded by a spend of "
                          f"{amount_micros}; only that principal's unit is terminated",
                          principal=target_principal, remaining_micros=balance)
        self._budgets[target_principal] = balance - amount_micros
        return self._budgets[target_principal]


# The one name every adapter module exports: the entry point of this module.
Adapter = DryRunTenancyAdapter
