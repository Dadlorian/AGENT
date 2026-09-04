"""The subject: the module the fault report names.

Pinned, read-only source snapshot. A unit never writes back into its own
inputs; a candidate is written to the output role instead.
"""

TIERS = {"standard": 0.05, "gold": 0.10, "platinum": 0.15}


def apply_coupon(order, coupon):
    """POST /checkout/coupon lands here. KeyError: 'tier' when a coupon carries
    no tier, and again when it carries a tier nobody minted."""
    rate = TIERS[coupon["tier"]]
    return round(order["total"] * (1 - rate), 2)
