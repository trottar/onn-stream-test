"""B14: the client's link notice, as the host sees it -- so a record can say the user was told.

Rides on `PRIVYHUB_LINK_REPORT=1` (B3's flag; the line G-A3 would adopt). **Absent = today**: nothing imports this
module. With the flag and a client without `debug.privyhub.link_notice=1` (no `link_notice` key): nothing new. Design:
`docs/memory/evidence/b14_2026-10-23/design_written_before_code.md` (hashed before this code).

The client's heartbeat carries `link_notice=<bits>` (0 = not shown; 1 the band is 2.4 GHz, 2 RSSI <= -72 dBm for 10 s,
4 tx <= 54 Mbps for 10 s). The heartbeat row records it beside the link fields; a transition writes one row in the
recovery log: `link_notice_shown` (0 -> non-zero) or `link_notice_cleared` (non-zero -> 0).
"""

from __future__ import annotations

from typing import Any

FIELD = "link_notice"
NAMES = ((1, "band_2_4_ghz"), (2, "rssi_weak"), (4, "tx_slow"))


def names(bits: int) -> list[str]:
    return [n for b, n in NAMES if bits & b]


class NoticeLog:
    def __init__(self) -> None:
        self.last = 0

    def note(self, recovery: Any, bits: int, values: dict[str, Any]) -> str | None:
        """One heartbeat's value; the row written, if any."""
        bits = int(bits) if isinstance(bits, int) and bits >= 0 else 0
        prev, self.last = self.last, bits
        if prev == 0 and bits != 0:
            recovery._log("link_notice_shown", reasons=bits, reason_names=names(bits),
                          link_frequency_mhz=values.get("link_frequency_mhz"), link_rssi_dbm=values.get("link_rssi_dbm"),
                          link_tx_mbps=values.get("link_tx_mbps"), heartbeat_sequence=values.get("sequence"))
            return "link_notice_shown"
        if prev != 0 and bits == 0:
            recovery._log("link_notice_cleared", previous_reasons=prev, heartbeat_sequence=values.get("sequence"))
            return "link_notice_cleared"
        return None
