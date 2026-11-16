#!/usr/bin/env python3
"""B112 (host): the bench way to run a game with no client, behind PRIVYHUB_H7=1, through the real HTTP server on
loopback (B103 / B110's harness: the fake RetroArch, the fake picture source, the stub stream — down unless a case
puts it up; B108's stand-in board for the party case). A caller that is not loopback is made by giving the plugin
another address for that one call (the handler's address as a session would give it). Flag absent → HEAD's answers
byte for byte. Temp dirs removed.

    python3 -m unittest discover -s tests/b112_no_client_bench -v
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("art_systems", "b99_h7_live_read", "b102_h7_endscreen", "b103_h7_minigame", "b108_party_launch",
            "b110_party_minigame"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402
import test_b110 as b110  # noqa: E402  (a module: its tests are not collected twice)

BASELINE = "0a3d78e2"
H7 = {**b85.FLAGS, "PRIVYHUB_H7": "1"}
BOTH = {**H7, "PRIVYHUB_PARTY": "1"}

SCENARIO = r'''
import types
try:
    import party_session as party
    party.QUIT_WAIT_S = 1.0
except ImportError:
    party = None
board_dir = Path(args["board_dir"])
def fake_run(cmd, timeout=3.0):
    pid = (board_dir / "pid").read_text() if (board_dir / "pid").exists() else ""
    out = ""
    if cmd[:4] == ["xdotool", "search", "--onlyvisible", "--class"]:
        out = "4242\n" if pid else ""
    elif cmd[:2] == ["xdotool", "getwindowpid"]:
        out = pid + "\n"
    elif cmd[:2] == ["pactl", "list"]:
        out = f'application.process.id = "{pid}"\n' if pid else ""
    return types.SimpleNamespace(returncode=0, stdout=out, stderr="")
m._party_session_kwargs = {"run": fake_run, "devices": Path(args["devices"])}
starts = []
stream.active = False
def stream_start(**kw):
    starts.append(kw.get("managed_process_id")); stream.active = True; return {"active": True}
stream.start = stream_start
def as_other(path):
    """One call through the real server with the plugin given a non-loopback address (as a session's would be)."""
    real = g.handle_post_request
    g.handle_post_request = lambda action, raw_query, client_ip: real(action, raw_query, "a-client")
    try:
        return call("POST", path)
    finally:
        g.handle_post_request = real
def wait(path, pred, bound=20):
    end = time.monotonic() + bound; b = {}
    while time.monotonic() < end:
        b = call("GET", path)["body"]
        if pred(b):
            return b
        time.sleep(0.05)
    return dict(b, timeout=True)
out = {"steps": {}}
S = out["steps"]
title = args["id"]
S["release_no_game"] = call("POST", "/plugins/games/bench-release")
S["launch"] = call("POST", f"/plugins/games/launch?id={title}")["code"]
if args["mode"] == "today":
    S["release"] = call("POST", "/plugins/games/bench-release")
    S["h7_bench"] = call("POST", "/plugins/games/h7-start?bench=1")
    S["party_bench"] = call("POST", "/plugins/games/party-minigame-start?id=x&seats=1,2&bench=1")
else:
    rules_ = Path(rules); rules_.mkdir(parents=True, exist_ok=True)
    for name in os.listdir(args["spec_dir"]):
        shutil.copyfile(Path(args["spec_dir"], name), rules_ / name.replace("GAME", title))
    js_ = json.loads((rules_ / f"{title}.endscreen.json").read_text()); js_["arrays"] = f"{title}.endscreen.npz"
    (rules_ / f"{title}.endscreen.json").write_text(json.dumps(js_))
    (rules_ / f"{title}.state").write_text(json.dumps({"P1": 0, "P2": 0}))
    (rules_ / f"{title}.party.json").write_text(json.dumps({"players": 2, "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}}))
    mini = g._h7_minigame_runner(); mini.picture = pic; mini.read_every = 0.2; mini.recognise_s = 1.6
    S["paused_after_launch"] = call("GET", "/plugins/games/status")["body"].get("paused")
    S["ready_without_stream"] = call("POST", "/plugins/games/native-stream-ready")
    S["release_other"] = as_other("/plugins/games/bench-release")
    S["release"] = call("POST", "/plugins/games/bench-release")
    S["ra_paused_after"] = fake["ra"].paused
    S["h7_no_bench"] = call("POST", "/plugins/games/h7-start")
    S["h7_bench_other"] = as_other("/plugins/games/h7-start?bench=1")
    pic.set(["start"] * 3 + ["other"] * 4 + ["end_P1"] * 30)
    S["h7_bench"] = call("POST", "/plugins/games/h7-start?bench=1")
    S["h7_result"] = wait("/plugins/games/h7-result", lambda b: b.get("state") == "ended")
    call("POST", "/plugins/games/h7-stop")
    stream.active = True
    S["release_stream_up"] = call("POST", "/plugins/games/bench-release")
    S["h7_bench_stream_up"] = call("POST", "/plugins/games/h7-start?bench=1")
    stream.active = False
    S["starts_so_far"] = list(starts)
    if True:                                       # the party case (both flags in "on")
        cfg = Path(os.environ["PRIVYHUB_PARTY_CONFIG"])
        cfg.write_text(json.dumps({"godot": args["board"], "project": args["project"], "pictures": args["pictures"]}))
        nodes = call("GET", "/plugins/games/games?system=party")["body"].get("nodes", [])
        board_id = next(n["id"] for n in nodes if n.get("node_type") == "game")
        S["board_launch"] = call("POST", f"/plugins/games/launch?id={board_id}")["code"]
        S["board_release"] = call("POST", "/plugins/games/bench-release")
        token = call("GET", "/plugins/games/party-minigames")["body"]["minigames"][0]["id"]
        layer = g._party_minigame_runner(); layer.tick = 0.05
        S["party_bench_other"] = as_other(f"/plugins/games/party-minigame-start?id={token}&seats=1,2&bench=1")
        pic.set(["start"] * 3 + ["other"] * 4 + ["end_P2"] * 30)
        S["party_bench"] = call("POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2&bench=1")
        S["party_result"] = wait("/plugins/games/party-minigame-result", lambda b: b.get("state") in ("ended", "given_up"))
        S["party_end"] = call("POST", "/plugins/games/party-minigame-end")
        S["party_starts"] = list(starts)
        S["status_after"] = call("GET", "/plugins/games/status")["body"].get("launch_kind")
        call("POST", "/plugins/games/stop")
httpd.shutdown()
print(json.dumps(out))
'''


def run(env: dict, mode: str, code=None) -> dict:
    root, ids = b99.tree(code) if code is not None else b99.tree()
    old = b110.SCENARIO
    b110.SCENARIO = SCENARIO
    try:
        return b110.run(root, env, ids, mode)
    finally:
        b110.SCENARIO = old


class Bench(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = run(BOTH, "on")["steps"]

    def err(self, r):
        return r["code"], r["body"].get("error")

    def test_a_launch_with_no_client_released(self):
        self.assertTrue(self.s["paused_after_launch"])
        self.assertGreaterEqual(self.s["ready_without_stream"]["code"], 400)          # today's: needs the stream
        self.assertEqual(self.s["release"]["code"], 200, self.s["release"]["body"])
        self.assertTrue(self.s["release"]["body"]["released"])
        self.assertFalse(self.s["ra_paused_after"])

    def test_the_watcher_with_no_stream(self):
        self.assertEqual(self.err(self.s["h7_no_bench"]), (400, "the stream is not up"))
        self.assertEqual(self.s["h7_bench"]["code"], 200, self.s["h7_bench"]["body"])
        r = self.s["h7_result"]
        self.assertEqual((r["state"], r["class"], r["recognised"]), ("ended", "end_P1", True), r)
        self.assertEqual(self.s["starts_so_far"], [])                                   # no stream started

    def test_refused_for_a_caller_that_is_not_loopback(self):
        for k in ("release_other", "h7_bench_other", "party_bench_other"):
            self.assertEqual(self.err(self.s[k]), (400, "the bench is for loopback callers only"), k)

    def test_refused_while_a_clients_stream_is_up(self):
        for k in ("release_stream_up", "h7_bench_stream_up"):
            self.assertEqual(self.err(self.s[k]), (400, "a client's stream is up: not on the bench"), k)

    def test_the_party_mini_game_with_no_stream(self):
        self.assertEqual(self.s["board_launch"], 200)
        self.assertEqual(self.s["board_release"]["code"], 200, self.s["board_release"]["body"])
        self.assertEqual(self.s["party_bench"]["code"], 200, self.s["party_bench"]["body"])
        r = self.s["party_result"]
        self.assertEqual((r["state"], r["scores"]), ("ended", [0, 1]), r)
        self.assertTrue(self.s["party_end"]["body"]["ended"])
        self.assertEqual(self.s["party_starts"], [])                                    # no stream, no switch
        self.assertEqual(self.s["status_after"], "godot")

    def test_no_game_refused(self):
        self.assertEqual(self.err(self.s["release_no_game"]), (400, "no game is running"))


class FlagAbsentIsToday(unittest.TestCase):
    def test_absent(self):
        old = b99.BASELINE
        b99.BASELINE = BASELINE
        try:
            code = b99.head_code()
        finally:
            b99.BASELINE = old
        if code is None:
            self.skipTest("git is absent")
        for env in (b85.FLAGS, {**b85.FLAGS, "PRIVYHUB_PARTY": "1"}, {**b85.FLAGS, "PRIVYHUB_H7": "0"}):
            base = run(env, "today", code=code)
            mine = run(env, "today")
            for k in ("release_no_game", "release", "h7_bench", "party_bench"):
                self.assertEqual((mine["steps"][k]["code"], mine["steps"][k]["raw"]),
                                 (base["steps"][k]["code"], base["steps"][k]["raw"]), (env, k))
            self.assertIn("Unknown Games plugin POST action: bench-release", base["steps"]["release"]["raw"])


if __name__ == "__main__":
    unittest.main()
