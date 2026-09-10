"""The visible route test, in the source snapshot's own test tree.

It is in the contract, so the unit may run it as often as it likes. It does not
decide: one deciding check asserts these bytes are unchanged after the attempt.
"""


def visible_checks(apply_coupon):
    results = []
    results.append(("v-known-tier", apply_coupon({"total": 100.0}, {"tier": "gold"}) == 90.0))
    try:
        apply_coupon({"total": 100.0}, {})
        results.append(("v-missing-tier-does-not-raise", True))
    except Exception:
        results.append(("v-missing-tier-does-not-raise", False))
    return results
