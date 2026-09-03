"""The host side of the boundary.

Everything here is owned by the host, not by the unit, and stays the same
whichever containment technology is behind the adapter: the per-unit directory
the host creates and stats, and the broker that holds the real credential and
decides every egress attempt. A unit never reports on its own containment, so
these objects - not the unit - produce the containment report.
"""
from __future__ import annotations

import os
import stat

try:                       # absent on some platforms; the check degrades, it does not crash
    import pwd
except ImportError:        # pragma: no cover
    pwd = None

REAL_SECRET = "host-broker-real-credential-never-inside-a-unit"
DUMMY_KEY = "dummy-key-no-real-secret-in-the-unit"


class Jail:
    """The unit's own directory on the host, at mode 0700, owned by a name with
    no entry in the host account database."""

    def __init__(self, root: str, unit_id: str) -> None:
        self.path = os.path.join(root, unit_id)
        self.owner_name = f"unit-{unit_id}"
        os.makedirs(self.path, mode=0o700, exist_ok=True)
        os.chmod(self.path, 0o700)

    def mode(self) -> str:
        return "0" + oct(stat.S_IMODE(os.stat(self.path).st_mode))[2:].rjust(3, "0")

    def owner_in_host_passwd(self) -> bool:
        if pwd is None:
            return False
        try:
            pwd.getpwnam(self.owner_name)
            return True
        except KeyError:
            return False

    def write_marker(self, marker: str) -> None:
        """Written by the running unit into its own directory."""
        with open(os.path.join(self.path, "marker"), "w") as fh:
            fh.write(marker)

    def read_marker(self) -> str:
        """Read by the host from the running unit, never from the binding record."""
        try:
            with open(os.path.join(self.path, "marker")) as fh:
                return fh.read().strip()
        except OSError:
            return "absent"


class Broker:
    """Holds the real credential and decides every egress attempt. The unit is
    handed a dummy key and cannot reach anything the declaration did not name."""

    def __init__(self, allowlist) -> None:
        self.allowlist = list(allowlist)
        self.made = 0
        self.blocked = 0
        self.credentials_handed_out: list[str] = []

    def credential_for_unit(self) -> str:
        self.credentials_handed_out.append(DUMMY_KEY)
        return DUMMY_KEY

    def connect(self, destination: str) -> bool:
        """Called by the unit. Counted and decided here, on the host side."""
        self.made += 1
        allowed = any(destination == entry or entry == "0.0.0.0/0" for entry in self.allowlist)
        if not allowed:
            self.blocked += 1
        return allowed

    def secrets_seen_inside(self) -> int:
        return sum(1 for value in self.credentials_handed_out if value == REAL_SECRET)
