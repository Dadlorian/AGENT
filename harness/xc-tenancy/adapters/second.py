#!/usr/bin/env python3
"""Second adapter: database per tenant - one store instance per principal,
selected before any append or read, so isolation is structural rather than a
filter over one shared store.

"Database per Tenant" in the research on file (X-xc-tenancy-001), realised on
the same swap candidate cap-state-persistence's own B3 row already names for
a different reason - object store (F-b3-17) - reused here to answer a
narrower question: not which store cap-state-persistence should use, but
whether the tenant boundary is a filter over shared partitions or a
partition of its own.

There is no flag here to disable, because there is no filter: a read or
recall for principal A only ever touches self._stores[A]. It cannot reach
another principal's records to leak them even if asked to - the closest it
comes is a lightweight routing index (populated at write time, never at
read time, and carrying only which principal owns a key - never the value)
so that a cross-tenant request is refused with a named reason instead of a
bare "not found" that would be indistinguishable from a key that never
existed anywhere. That index is metadata a tenant-router needs regardless;
it is not a second read of another tenant's store.

Cannot answer a cross-tenant query at all, even an authorised platform-level
audit, without a second read that unions every store; cannot share one
budget ledger across tenants, because the ledger is now per tenant as well.

Deterministic, in process, no network. Standard library only.
"""
from __future__ import annotations

from interface import Problem, TenancyAdapter

DEFAULT_CEILING_MICROS = 500_000


class DatabasePerTenantAdapter(TenancyAdapter):
    entity = "in-process database-per-tenant"
    report_adapter = "database-per-tenant"
    locus_of_the_tenant_boundary = "a wholly separate store instance selected by principal before any read or write"
    failure_mode_of_a_wrong_or_missing_principal = "fails to resolve a store at all, returning nothing"
    provisioning_cost_of_a_new_principal = "a new principal needs a new store instance before its first write can succeed"

    def __init__(self):
        super().__init__()
        self._stores: dict[str, dict] = {}          # principal -> {key: value}, one instance per principal
        self._budgets: dict[str, dict] = {}          # principal -> {"remaining": micros}, one ledger per principal
        self._index: dict[str, str] = {}             # key -> owning principal; routing metadata, never a value

    def _store_for(self, principal: str, create: bool) -> dict | None:
        if create:
            return self._stores.setdefault(principal, {})
        return self._stores.get(principal)

    def _write(self, principal, key, value, context):
        store = self._store_for(principal, create=True)   # provisions the instance on first write
        store[key] = value
        self._index[key] = principal
        return {"key": key, "principal": principal}

    def _read(self, principal, key, context):
        store = self._store_for(principal, create=False)
        if store is not None and key in store:
            return store[key]
        owner = self._index.get(key)
        if owner is not None and owner != principal:
            # No store resolves for this pairing: refused by construction, not by a check that could be dropped.
            raise Problem("cross-tenant-denied",
                          f"key {key!r} resolves to a different principal's store; no store instance for "
                          f"{principal!r} was ever consulted about it",
                          key=key, rule_id="tenancy-scope")
        raise Problem("document-invalid", f"no such key {key!r}", key=key)

    def _recall(self, principal, context):
        store = self._store_for(principal, create=False) or {}
        return sorted(store.keys())                  # structurally cannot see another principal's keys

    def _spend(self, principal, target_principal, amount_micros, context):
        if target_principal != principal:
            # There is no route to another tenant's ledger from here to even attempt the charge.
            raise Problem("cross-tenant-denied",
                          f"a spend by {principal!r} named a different target principal {target_principal!r}; "
                          f"no ledger for it is reachable from this principal's store",
                          rule_id="tenancy-scope")
        ledger = self._budgets.setdefault(principal, {"remaining": DEFAULT_CEILING_MICROS})
        if amount_micros > ledger["remaining"]:
            raise Problem("budget-exceeded",
                          f"{principal!r}'s own ceiling ({ledger['remaining']} micros) was exceeded by a spend "
                          f"of {amount_micros}; only that principal's unit is terminated",
                          principal=principal, remaining_micros=ledger["remaining"])
        ledger["remaining"] -= amount_micros
        return ledger["remaining"]


# The one name every adapter module exports: the entry point of this module.
Adapter = DatabasePerTenantAdapter
