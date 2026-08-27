"""The barrier taxonomy is only real once it has been watched to separate cases.

The distinction under test is the one the module exists for: a host refused at
the proxy's CONNECT is not the same finding as a host that answered and asked
for a credential, and code that conflates them tells an operator to fix the
wrong thing.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.net.reachability import (  # noqa: E402
    Barrier,
    Reachability,
    classify_exception,
    render_table,
)
from oodarag.util.http import HttpError, TransportError  # noqa: E402


class TestBarrierSemantics(unittest.TestCase):
    def test_egress_blocked_is_never_retryable(self) -> None:
        # An allowlist does not change between two attempts a second apart.
        # Retrying it is the failure this property exists to prevent.
        self.assertFalse(Barrier.EGRESS_BLOCKED.retryable)
        self.assertFalse(Barrier.EGRESS_BLOCKED.reachable)

    def test_transport_barriers_are_unreachable_credential_barriers_are_not(self) -> None:
        for barrier in (Barrier.EGRESS_BLOCKED, Barrier.DNS_FAILURE, Barrier.TIMEOUT):
            self.assertFalse(barrier.reachable, barrier)
        for barrier in (Barrier.AUTH_REQUIRED, Barrier.FORBIDDEN, Barrier.NOT_FOUND,
                        Barrier.RATE_LIMITED, Barrier.BAD_REQUEST):
            self.assertTrue(barrier.reachable, barrier)

    def test_only_transient_barriers_are_retryable(self) -> None:
        retryable = {b for b in Barrier if b.retryable}
        self.assertEqual(
            retryable, {Barrier.RATE_LIMITED, Barrier.SERVER_ERROR, Barrier.TIMEOUT}
        )

    def test_every_barrier_states_a_remedy(self) -> None:
        for barrier in Barrier:
            self.assertTrue(barrier.remedy.strip(), f"{barrier} has no remedy")


class TestClassification(unittest.TestCase):
    def test_proxy_tunnel_refusal_is_egress_blocked(self) -> None:
        # This is the exact shape urllib produces for a CONNECT refusal, and
        # the message is the only place the distinction survives.
        exc = TransportError("OSError: Tunnel connection failed: 403 Forbidden (https://x/)")
        barrier, detail = classify_exception(exc)
        self.assertIs(barrier, Barrier.EGRESS_BLOCKED)
        self.assertIn("Tunnel connection failed", detail)

    def test_dns_failure_is_not_reported_as_a_block(self) -> None:
        exc = TransportError("URLError: <urlopen error [Errno -2] Name or service not known>")
        barrier, _ = classify_exception(exc)
        self.assertIs(barrier, Barrier.DNS_FAILURE)

    def test_http_401_is_auth_required(self) -> None:
        barrier, _ = classify_exception(HttpError(401, "https://x/", "unauthorized"))
        self.assertIs(barrier, Barrier.AUTH_REQUIRED)

    def test_http_403_reached_the_service_so_is_not_a_block(self) -> None:
        barrier, _ = classify_exception(HttpError(403, "https://x/", "nope"))
        self.assertIs(barrier, Barrier.FORBIDDEN)
        self.assertTrue(barrier.reachable)

    def test_generic_4xx_still_proves_the_host_answered(self) -> None:
        barrier, _ = classify_exception(HttpError(400, "https://x/", "bad"))
        self.assertIs(barrier, Barrier.BAD_REQUEST)
        self.assertTrue(barrier.reachable)

    def test_5xx_is_retryable(self) -> None:
        barrier, _ = classify_exception(HttpError(503, "https://x/", "later"))
        self.assertIs(barrier, Barrier.SERVER_ERROR)
        self.assertTrue(barrier.retryable)


class TestRendering(unittest.TestCase):
    def test_table_names_the_remedy_for_each_row(self) -> None:
        rows = [
            Reachability("https://open/", Barrier.OPEN, 200),
            Reachability("https://blocked/", Barrier.EGRESS_BLOCKED, None),
        ]
        table = render_table(rows)
        self.assertIn("egress_blocked", table)
        self.assertIn("allowlist", table)

    def test_empty_probe_says_so_rather_than_rendering_nothing(self) -> None:
        self.assertIn("no hosts", render_table([]))

    def test_dict_form_carries_the_decision_inputs(self) -> None:
        payload = Reachability("https://x/", Barrier.AUTH_REQUIRED, 403).as_dict()
        self.assertTrue(payload["reachable"])
        self.assertFalse(payload["retryable"])
        self.assertIn("credential", payload["remedy"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
