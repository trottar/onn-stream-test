#!/usr/bin/env python3
"""C3-L3A-R2B: what a decoder report past the transport ceiling meets.

A throwaway http.server on an ephemeral localhost port -- not the companion --
with a log_message of the same shape as the companion's override
(`companion/privyhub_service.py`, PrivyHubRequestHandler.log_message, which
reads self.path). One POST whose request line exceeds 65,536 bytes.
"""

import socket
import threading
import time
import http.server
from urllib.parse import urlsplit


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if urlsplit(self.path).path.startswith("/diagnostics/"):
            return
        print("ACCESS", format % args)

    def do_POST(self):
        self.send_response(200)
        self.end_headers()


server = http.server.ThreadingHTTPServer(("localhost", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
sock = socket.create_connection(server.server_address)
sock.sendall(b"POST /plugins/games/decoder-session-log?report=" + b"x" * 66_000
             + b" HTTP/1.1\r\nHost: x\r\n\r\n")
sock.settimeout(3)
try:
    print("client received:", repr(sock.recv(200)[:60]))
except OSError as exc:
    print("client received nothing:", type(exc).__name__, exc)
time.sleep(0.5)
server.shutdown()
