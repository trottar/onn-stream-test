#!/usr/bin/env python3
"""B111 (host): the board's hub mini game (`minigames/hub_minigame.gd` in the board game's repo) and its check
(`checks/hub_minigame_check.gd`), run by Godot headless in a scratch copy of the board's repo — once with the check's
own stand-in hub, once against this test's fake hub (a loopback HTTP server answering the four party routes per
scenario, recording every call). The board's repo is read only here (its HEAD archived, the two new files copied from
its working tree); Godot's own folders point into the scratch folder; everything removed after.

Godot and the board's repo are named by the environment (PRIVYPARTY_GODOT, PRIVYPARTY_REPO); absent → skipped.

    python3 -m unittest discover -s tests/b111_party_board -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
import _tmp_cleanup  # noqa: E402,F401

NEW = ("minigames/hub_minigame.gd", "checks/hub_minigame_check.gd")
GODOT = os.environ.get("PRIVYPARTY_GODOT", "")
REPO = os.environ.get("PRIVYPARTY_REPO", "")


class FakeHub:
    """The four party routes, answered per scenario (the path's /s/<scenario> prefix), every call recorded."""

    def __init__(self):
        self.calls: list[str] = []
        self.polls: dict[str, int] = {}
        hub = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _answer(self):
                path = self.path
                hub.calls.append(path)
                parts = path.split("/")
                scenario = parts[2] if len(parts) > 2 else ""
                action = path.split("/plugins/games/", 1)[-1].split("?", 1)[0]
                code, body = 200, {"ok": True}
                if action == "party-minigames":
                    body["minigames"] = [{"id": "mg_one", "players": 4 if scenario == "four" else 2}]
                elif action == "party-minigame-start":
                    if scenario == "refused":
                        code, body = 400, {"ok": False, "error": "a mini game is already on"}
                    else:
                        body["state"] = "starting"
                elif action == "party-minigame-result":
                    n = hub.polls[scenario] = hub.polls.get(scenario, 0) + 1
                    if scenario == "silent":                          # B116: the hub not answering
                        code, body = 500, {"ok": False, "error": "the hub is busy"}
                    elif n <= (3 if scenario in ("slow", "teardown") else 1):
                        body.update(state="playing", recognised=True)
                    elif scenario == "giveup":
                        body.update(state="given_up", why="no end within 900 s", scores=None)
                    else:
                        body.update({"state": "ended", "class": "end_P1",
                                     "scores": [0, 1] if scenario in ("win2", "slow") else [1, 0]})
                elif action == "party-minigame-end":
                    body["ended"] = True
                else:
                    code, body = 404, {"ok": False, "error": "Unknown Games plugin action"}
                data = json.dumps(body).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = do_POST = _answer

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def run_check(extra_env: dict) -> subprocess.CompletedProcess:
    scratch = Path(tempfile.mkdtemp(prefix="b111_"))
    try:
        repo = scratch / "repo"
        repo.mkdir()
        tar = subprocess.run(["git", "-C", REPO, "archive", "HEAD"], capture_output=True, check=True, timeout=120).stdout
        subprocess.run(["tar", "-x", "-C", str(repo)], input=tar, check=True, timeout=120)
        for rel in NEW:
            shutil.copyfile(Path(REPO) / rel, repo / rel)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PRIVYPARTY_HUB", "PRIVYPARTY_CHECK"))}
        env.update({"XDG_DATA_HOME": str(scratch / "data"), "XDG_CONFIG_HOME": str(scratch / "config"),
                    "XDG_CACHE_HOME": str(scratch / "cache"), "TMPDIR": str(scratch / "tmp"), **extra_env})
        for k in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "TMPDIR"):
            Path(env[k]).mkdir(parents=True, exist_ok=True)
        subprocess.run([GODOT, "--headless", "--path", str(repo), "--import"], env=env, capture_output=True,
                       timeout=300, check=False)
        return subprocess.run([GODOT, "--headless", "--path", str(repo), "--script", "res://checks/hub_minigame_check.gd"],
                              env=env, capture_output=True, text=True, timeout=300, check=False)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


@unittest.skipUnless(GODOT and REPO and Path(GODOT).is_file() and (Path(REPO) / NEW[0]).is_file(),
                     "Godot or the board's repo (with the two new files) not given")
class BoardCheck(unittest.TestCase):
    def test_with_the_checks_own_stand_in_hub(self):
        r = run_check({})
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-1000:])
        self.assertIn("HUB MINIGAME CHECK: PASS (34 assertions)", r.stdout)   # B116: 20 + 14 on the frame rate

    def test_against_this_tests_fake_hub(self):
        hub = FakeHub()
        try:
            r = run_check({"PRIVYPARTY_CHECK_HUB": hub.url})
        finally:
            hub.close()
        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr[-1000:])
        # its five "asked" ones, "listens" and (B116) the five frame-rate ones it reads at its own hub are ours here
        self.assertIn("HUB MINIGAME CHECK: PASS (23 assertions)", r.stdout)
        starts = [c for c in hub.calls if "party-minigame-start" in c]
        self.assertIn("/s/win1/plugins/games/party-minigame-start?id=mg_one&seats=1,2", starts)
        self.assertEqual(sum(1 for c in hub.calls if c.endswith("party-minigame-end")), 8)   # every started one
        self.assertIn("PrivyParty: hub mini game: a draw: the hub stopped answering", r.stdout)   # B116's silent hub
        self.assertFalse(any(c.startswith("/s/refused/") and c.endswith("party-minigame-end") for c in hub.calls))
        self.assertIn("PrivyParty: hub mini game: a draw: the hub gave it up (no end within 900 s)", r.stdout)
        self.assertIn("PrivyParty: hub mini game: a draw: no hub (no hub)", r.stdout)


if __name__ == "__main__":
    unittest.main()
