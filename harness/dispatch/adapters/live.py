#!/usr/bin/env python3
"""Today's dispatch path, reached only through the environment variables in the
README's env table. This file and that table are the only places a product is
named.

What PASS.md records today: agent execution runs as one **Firecracker** microVM
per agent, started through the **systemd** template unit `firecracker-cell@.service`
(and its long-lived variant), driven over the **Agent Client Protocol** on a
vsock channel, with model egress leaving over vsock to the host broker
(**LiteLLM**) that holds the real key. There are three such execution paths and
no contract between them (F-b5-03), which is what this harness exists to put one
in front of.

The mapping this shim claims, and which has never been executed here:

  dispatch    write the document, the ceilings and the context declaration to
              the unit over ACP `session/prompt`; the ACP stop reason maps onto
              the seam's first five stop reasons and the platform's five endings
              are decided by this shim, not by the guest.
  cancel      ACP `session/cancel` on the same channel inside cancel_grace_s;
              outside it, the shim reports cancel_timeout and stops the unit.
  resume      a new unit with previous_dispatch_id, started at the first step
              whose checkpoint reference is null. The shim, not the guest, owns
              the deadline timer, the budget reservation and the step record.
  replay      answered by the shim from its own step records; the guest is never
              started, so nothing is re-executed.
  read_step   the shim's step records; the guest keeps no journal.

Nothing below the reachability probe has been run. With the env vars unset the
harness skips live mode and says so; with them set and nothing listening, the
probe answers `urn:agentic:problem:adapter-unavailable` (503, retryable) rather
than failing open, which is the only live behaviour this harness measures.

Python 3.11 standard library only; urllib and subprocess only, both guarded.
"""
from __future__ import annotations

import os
import socket
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import core  # noqa: E402
from adapters.base import SeamDispatcher, run_steps  # noqa: E402
from interface import Problem  # noqa: E402


class Adapter(SeamDispatcher):
    dispatcher_marker = "contained-unit-over-acp/unverified"
    unit_lifetime = "session_held"
    cancellation_reach = "mid_call"
    keeps_own_journal = False
    executor_reached_over = "vsock control channel to a per-agent microVM"
    binding_role = "today"
    cost_read_mode = "scan-and-fold"

    # The env vars, and nothing else, say where the executor is.
    UNIT = "DISPATCH_UNIT"            # systemd template instance, e.g. firecracker-cell@7.service
    CHANNEL = "DISPATCH_ACP_SOCKET"   # the ACP control channel (vsock or unix socket path)
    GATEWAY = "GATEWAY_URL"           # the host broker that holds the real model key
    TIMEOUT = "DISPATCH_TIMEOUT_S"

    def configured(self) -> bool:
        return bool(os.environ.get(self.CHANNEL) or os.environ.get(self.UNIT))

    def probe(self) -> None:
        """The one live behaviour that has been exercised: report unreachable as
        a typed problem instead of failing open."""
        channel = os.environ.get(self.CHANNEL, "")
        timeout = float(os.environ.get(self.TIMEOUT, "5"))
        if not self.configured():
            raise Problem("adapter-unavailable",
                          f"neither {self.CHANNEL} nor {self.UNIT} is set; live mode has no "
                          f"executor to reach", retry_after=None)
        if channel and not os.path.exists(channel):
            raise Problem("adapter-unavailable",
                          f"control channel {channel} does not exist on this host")
        try:
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(channel)
            sock.close()
        except Exception as exc:
            raise Problem("adapter-unavailable",
                          f"control channel {channel} did not accept a connection: "
                          f"{type(exc).__name__}: {exc}") from exc

    def unit_work(self):
        """Per-step work: the model call leaves over the broker named by
        GATEWAY_URL, which holds the key; the unit never sees a real secret.
        The worked example's gateway client is reused rather than re-written."""
        if not os.environ.get(self.GATEWAY):
            raise Problem("adapter-unavailable",
                          f"{self.GATEWAY} is unset, so a contained unit has no broker to "
                          f"reach for model egress")
        return core.example.OpenAICompatibleAdapter().complete

    def execute_unit(self, req_body: dict, plan: dict, prior: dict) -> dict:
        self.probe()                       # never reached on this host
        dispatch_id = req_body["dispatch_id"]

        def probe_cancel() -> bool:
            record = self.cancel_record(dispatch_id)
            return bool(record) and not record.get("already_terminal")

        return run_steps(req_body, plan, self.log, self.unit_work(), probe_cancel, prior)


def urlopen(url: str, timeout: float):
    """Kept so the broker's own health route can be read without importing a
    client library that is not installed here."""
    return urllib.request.urlopen(url, timeout=timeout)
