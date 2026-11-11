"""B90: a game launch answered to a client that has gone.

The onn waits 60 s for the launch's answer (its control read timeout). When the launch returns after the client has
closed its connection, or after that wait, or the answer cannot be written, nobody will ever see the game: the hub stops
it (the plugin's own Stop path) and writes one `launch_orphaned` row. PRIVYHUB_CHEAT_STAGED=0: today's answer path.
"""

from __future__ import annotations

import os
import select
import socket

CLIENT_WAIT_SECONDS = 60.0     # the onn's CONTROL_READ_TIMEOUT_MS


def enabled() -> bool:
    return str(os.environ.get("PRIVYHUB_CHEAT_STAGED", "")).strip() != "0"


def client_gone(conn: socket.socket) -> bool:
    """True when the peer has closed its side: the socket reads as ready and a peek returns nothing (or fails)."""
    try:
        ready, _w, _x = select.select([conn], [], [], 0)
        if not ready:
            return False
        return conn.recv(1, socket.MSG_PEEK) == b""
    except (OSError, ValueError):
        return True


def reason(conn: socket.socket, elapsed_s: float) -> str | None:
    """Why the launch's answer would reach nobody, or None to answer as today."""
    if client_gone(conn):
        return "client_closed"
    if elapsed_s >= CLIENT_WAIT_SECONDS:
        return "client_wait_passed"
    return None
