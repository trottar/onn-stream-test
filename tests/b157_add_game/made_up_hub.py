"""B162: a made-up hub on loopback for the add-a-game tool's unit tests — the routes solo, close and rehearse call:
`party-minigame-only` (set / clear, kept in its own memory), `party-minigames` (the listed titles, filtered while set,
as the companion does), `details` (a made-up game file), `status` / `native-stream-status` (nothing running).
Everything made up; nothing read from the hub."""
from __future__ import annotations

import json
import threading
import http.server
from urllib.parse import parse_qs, urlparse


class MadeUpHub:
    def __init__(self, listed: list[dict], relative_path: str = "games/ps1/Made Up (USA).cue", take_only: bool = True):
        self.listed = listed                    # [{"id", "players", "title", "game"}]
        self.relative_path = relative_path
        self.take_only = take_only              # False: the route answers as on a hub without it (an old companion)
        self.only: dict | None = None
        self.calls: list[str] = []
        hub = self

        class H(http.server.BaseHTTPRequestHandler):
            def _answer(self, method):
                u = urlparse(self.path)
                action = u.path.rsplit("/", 1)[-1]
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                hub.calls.append(f"{method} {action}" + (" clear" if "clear" in q else " set" if "game" in q else ""))
                code, body = 200, {"ok": True}
                if action == "party-minigame-only" and method == "POST" and hub.take_only:
                    if q.get("clear") == "1":
                        hub.only = None
                        body = {"ok": True, "only": False}
                    else:
                        e = next((x for x in hub.listed if x["game"] == q.get("game")), None)
                        if e is None:
                            code, body = 400, {"ok": False, "error": "not a listed mini game: nothing set"}
                        else:
                            hub.only = {"game": e["game"], "players": e["players"]}
                            body = {"ok": True, "only": True, "players": e["players"]}
                elif action == "party-minigame-only":
                    code, body = 400, {"ok": False, "error": "Unknown Games plugin action: party-minigame-only"}
                elif action == "party-minigames":
                    lst = [x for x in hub.listed if hub.only is None or x["players"] != hub.only["players"]
                           or x["game"] == hub.only["game"]]
                    body = {"ok": True, "minigames": [{k: x[k] for k in ("id", "players", "title")} for x in lst]}
                elif action == "details":
                    body = {"relative_path": hub.relative_path}
                raw = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                self._answer("GET")

            def do_POST(self):
                self._answer("POST")

            def log_message(self, *a):
                pass

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def close(self) -> None:
        self.srv.shutdown()
        self.srv.server_close()
