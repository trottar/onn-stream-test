#!/usr/bin/env python3
"""B110 (host): the party mini game behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1, through the real HTTP server on loopback.

B108's stand-in board (a real process: its command line, its pid, F10 → exit 0) and B103's harness (a child `python3 -I`
on B82 / B83's fixture tree; B101's fake RetroArch for the mini game's title — a second process beside the board;
B103's fake picture source with synthetic tallies and a spec learnt in the test); a stub stream recording each start's
pid and each stop; a real controller bridge with recording pads (the route). Shortened limits in the test (the hub's:
8 s recognised, 900 s play, 120 s / 60 s caller). Each flag absent → HEAD's answers byte for byte. Temp dirs removed.

    python3 -m unittest discover -s tests/b110_party_minigame -v
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("art_systems", "b99_h7_live_read", "b102_h7_endscreen", "b103_h7_minigame", "b108_party_launch"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402  (modules: their tests are not collected twice)
import test_b103 as b103  # noqa: E402
import test_b108 as b108  # noqa: E402

BASELINE = "0a3d78e2"                    # queue AP's baseline (PP-H2 committed): the companion before B110
BOTH = {**b85.FLAGS, "PRIVYHUB_PARTY": "1", "PRIVYHUB_H7": "1"}

SCENARIO = r'''
import types, hashlib
try:
    import party_session as party
    party.QUIT_WAIT_S = 1.0
except ImportError:
    party = None
board_dir = Path(args["board_dir"])
cmds = []
def fake_run(cmd, timeout=3.0):
    cmds.append(list(cmd))
    pid = (board_dir / "pid").read_text() if (board_dir / "pid").exists() else ""
    out, rc = "", 0
    if cmd[:4] == ["xdotool", "search", "--onlyvisible", "--class"]:
        out = "4242\n" if pid else ""
    elif cmd[:2] == ["xdotool", "getwindowpid"]:
        out = pid + "\n"
    elif cmd[:2] == ["xdotool", "windowactivate"]:
        with (board_dir / "keys").open("a") as fh:
            fh.write(cmd[-1] + "\n")
    elif cmd[:2] == ["pactl", "list"]:
        out = f'application.process.id = "{pid}"\n' if pid else ""
    else:
        rc = 1
    return types.SimpleNamespace(returncode=rc, stdout=out, stderr="")
m._party_session_kwargs = {"run": fake_run, "devices": Path(args["devices"])}
events = []
def stream_start(**kw):
    events.append(["start", kw.get("managed_process_id")])
    stream.active = True
    return {"active": True}
def stream_stop(*a, **k):
    events.append(["stop", None])
    stream.active = False
    return {"active": False}
stream.start = stream_start
stream.stop = stream_stop
import native_session_io as nsio
bridge = nsio.NativeControllerBridge(Path(args["board_dir"]) / "bridge")
bridge._gamepads = ["P1", "P2", "P3", "P4"]
bridge._controller_backend = "linux_uinput"
pad_writes = []
bridge._write_linux_report_locked = lambda index, report, *a, **k: pad_writes.append([bridge._gamepads[index], report["buttons"]])
stream._session_io = types.SimpleNamespace(controller=bridge)
def keys():
    p = board_dir / "keys"
    return p.read_text().split() if p.exists() else []
def rows():
    p = root / "logs/games/party.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.is_file() else []
def wait_for(pred, bound=30):
    end = time.monotonic() + bound; b = {}
    while time.monotonic() < end:
        b = call("GET", "/plugins/games/party-minigame-result")["body"]
        if pred(b):
            return b
        time.sleep(0.05)
    return dict(b, timeout=True)
out = {"steps": {}}
S = out["steps"]
cfg = Path(os.environ["PRIVYHUB_PARTY_CONFIG"])
cfg.write_text(json.dumps({"godot": args["board"], "project": args["project"], "pictures": args["pictures"]}))
S["launch_ps1"] = None
board_nodes = call("GET", "/plugins/games/games?system=party")["body"].get("nodes", [])
board_id = next((n["id"] for n in board_nodes if n.get("node_type") == "game"), None)
title = args["id"]
S["list_before_launch"] = call("GET", "/plugins/games/party-minigames")
if args["mode"] == "today":
    S["start"] = call("POST", "/plugins/games/party-minigame-start?id=x&seats=1,2")
    S["result"] = call("GET", "/plugins/games/party-minigame-result")
    S["end"] = call("POST", "/plugins/games/party-minigame-end")
    S["systems"] = call("GET", "/plugins/games/systems")
else:
    rules_ = Path(rules); rules_.mkdir(parents=True, exist_ok=True)
    def put_spec(gid):
        for name in os.listdir(args["spec_dir"]):
            shutil.copyfile(Path(args["spec_dir"], name), rules_ / name.replace("GAME", gid))
        js_ = json.loads((rules_ / f"{gid}.endscreen.json").read_text())
        js_["arrays"] = f"{gid}.endscreen.npz"
        (rules_ / f"{gid}.endscreen.json").write_text(json.dumps(js_))
    put_spec(title)
    (rules_ / f"{title}.state").write_text(json.dumps({"P1": 0, "P2": 0}))
    S["list_no_sidecar"] = call("GET", "/plugins/games/party-minigames")["body"]
    (rules_ / f"{title}.party.json").write_text(json.dumps({"players": 2, "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}}))
    # a second title with no state: never listed
    other = args["other_id"]
    put_spec(other)
    (rules_ / f"{other}.party.json").write_text(json.dumps({"players": 2, "scores": {"end_P1": [1, 0], "end_P2": [0, 1]}}))
    S["list"] = call("GET", "/plugins/games/party-minigames")["body"]
    token = S["list"]["minigames"][0]["id"] if S["list"].get("minigames") else None
    S["start_no_board"] = call("POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
    # the board as the session, its stream up (as the onn would have it)
    S["board_launch"] = call("POST", f"/plugins/games/launch?id={board_id}")["code"]
    call("POST", "/plugins/games/native-stream-start?port=48100")
    call("POST", "/plugins/games/native-stream-ready")
    board_pid = int((board_dir / "pid").read_text())
    mini = g._h7_minigame_runner(); mini.picture = pic; mini.read_every = 0.2; mini.recognise_s = 1.6
    layer = g._party_minigame_runner(); layer.tick = 0.05
    stem_ = None
    def slots():
        f = m._state_root() / "Beetle PSX HW"
        if not f.is_dir():
            return {}
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(f.iterdir()) if not p.name.endswith(".state8")}
    def scratch():
        f = m._state_root() / "Beetle PSX HW"
        return sorted(p.name for p in f.iterdir() if p.name.endswith(".state8")) if f.is_dir() else []
    S["bad_seats"] = call("POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,1")
    S["bad_id"] = call("POST", "/plugins/games/party-minigame-start?id=mg_nothing&seats=1,2")
    def run_one(tag, seats, script, until=("ended", "given_up"), bound=30, during=None):
        pic.set(script)
        k0, e0, w0, r0 = len(keys()), len(events), len(pad_writes), len(rows())
        S[tag + "_start"] = call("POST", f"/plugins/games/party-minigame-start?id={token}&seats={seats}")
        S[tag + "_playing"] = wait_for(lambda b: b.get("state") in ("playing",) + tuple(until), bound)
        S[tag + "_title_paused_at_playing"] = fake["ra"].paused if "ra" in fake else None
        if during is not None:
            during(tag)
        S[tag] = wait_for(lambda b: b.get("state") in until, bound)
        S[tag + "_end"] = call("POST", "/plugins/games/party-minigame-end")
        S[tag + "_end_again"] = call("POST", "/plugins/games/party-minigame-end")
        S[tag + "_keys_during"] = keys()[k0:]
        S[tag + "_events"] = events[e0:]
        S[tag + "_route_after"] = bridge._party_route
        S[tag + "_rows"] = [r["step"] for r in rows()[r0:]]
        S[tag + "_status"] = call("GET", "/plugins/games/status")["body"]
        S[tag + "_ra_log"] = list(fake["ra"].log) if "ra" in fake else None
        S[tag + "_scratch"] = scratch()
    def probe_pads(tag):
        # the onn's players 1-4 press A (bit 0x1000) while the mini game plays: only the seats reach pads, as ports
        w0 = len(pad_writes)
        for p_ in range(4):
            bridge._apply_report(p_, 0x1000 | (1 << p_), 0, 0, 0, 0, 0, 0)
        S[tag + "_pads"] = pad_writes[w0:]
        S[tag + "_route_during"] = {str(k): v for k, v in (bridge._party_route or {}).items()}
    # made-up user slots for the title (Continue's slot 0 and slots 1-3), hashed before and after
    stem_ = Path(g._find_game_by_id(title)["relative_path"]).stem
    sf = m._state_root() / "Beetle PSX HW"; sf.mkdir(parents=True, exist_ok=True)
    for i, x in enumerate((".state", ".state1", ".state2", ".state3")):
        (sf / (stem_ + x)).write_bytes(os.urandom(64) + bytes([i]))
    slots_before = slots()
    END1 = ["start"] * 3 + ["other"] * 6 + ["end_P1"] * 40
    run_one("m24", "2,4", END1, during=probe_pads)
    run_one("m42", "4,2", END1)
    run_one("unrec", "1,2", ["unknown"] * 200)
    layer.play_limit_s = 2.0
    run_one("limit", "1,2", ["start"] * 3 + ["other"] * 400)
    layer.play_limit_s = 900.0
    # Home during a mini game: the stream closed by the onn → the title paused, the board no key; RESUME → the title
    def home(tag):
        k0 = len(keys()); n0 = len(fake["ra"].log)
        S[tag + "_home"] = call("POST", "/plugins/games/native-stream-stop")
        S[tag + "_resume_start"] = call("POST", "/plugins/games/native-stream-start?port=48100")
        S[tag + "_resume_ready"] = call("POST", "/plugins/games/native-stream-ready")
        S[tag + "_home_ra"] = fake["ra"].log[n0:]
        S[tag + "_home_keys"] = keys()[k0:]
    run_one("home", "1,2", ["start"] * 3 + ["other"] * 30 + ["end_P2"] * 40, during=home)
    S["slots_equal"] = slots() == slots_before
    S["slots_count"] = len(slots_before)
    # END during a mini game: the title stopped, then F10 to the board
    pic.set(["start"] * 3 + ["other"] * 400)
    k0 = len(keys())
    S["end_start"] = call("POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
    S["end_playing"] = wait_for(lambda b: b.get("state") == "playing")
    S["end_stop"] = call("POST", "/plugins/games/stop")
    S["end_keys"] = keys()[k0:]
    S["end_result"] = call("GET", "/plugins/games/party-minigame-result")["body"]
    S["end_status_active"] = call("GET", "/plugins/games/status")["body"].get("active")
    S["end_board_gone"] = not (board_dir / "pid").exists()
    # the board dying mid-game
    (board_dir / "keys").unlink(missing_ok=True)
    call("POST", f"/plugins/games/launch?id={board_id}")
    call("POST", "/plugins/games/native-stream-start?port=48100"); call("POST", "/plugins/games/native-stream-ready")
    pic.set(["start"] * 3 + ["other"] * 400)
    call("POST", f"/plugins/games/party-minigame-start?id={token}&seats=1,2")
    wait_for(lambda b: b.get("state") == "playing")
    os.kill(int((board_dir / "pid").read_text()), 15)
    S["died"] = wait_for(lambda b: b.get("closed"), 20)
    S["died_rows"] = [r for r in rows() if r["step"] in ("minigame_given_up", "minigame_end")][-2:]
    S["scratch_left"] = scratch()
    S["slots_equal_final"] = slots() == slots_before
    out["board_pid"] = board_pid
httpd.shutdown()
print(json.dumps(out))
'''


def child() -> str:
    head = b103.CHILD.split('out = {"steps": {}}')[0]
    return head + SCENARIO


def run(root: Path, env: dict, ids: dict, mode: str) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="b110_fx_"))
    fx = b108.fixtures(work)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules"),
                      "PRIVYHUB_PARTY_CONFIG": str(work / "party.json"), "B108_BOARD_DIR": fx["board_dir"]})
    (root / "tools").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools" / "h7_endscreen.py", root / "tools" / "h7_endscreen.py")
    frames, spec_dir, js = b103.fixtures(work)
    js["arrays"] = "GAME.endscreen.npz"
    try:
        r = subprocess.run([sys.executable, "-I", "-B", "-c", child(), str(root),
                            json.dumps({"id": ids[b85.PS1_TITLE], "other_id": ids[b85.N64_TITLE], "mode": mode,
                                        "p1": b99.P1, "p2": b99.P2, "frames": str(frames),
                                        "spec_dir": str(spec_dir), **fx})],
                           cwd=root, env=child_env, capture_output=True, text=True, timeout=900)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-4000:]
    text = r.stdout.strip().splitlines()[-1]
    for form in {str(root), str(root.resolve())}:
        text = text.replace(form, "<root>")
    return json.loads(text)


class Minigame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, cls.ids = b99.tree()
        cls.out = run(root, BOTH, cls.ids, "on")
        cls.s = cls.out["steps"]

    def test_the_list(self):
        self.assertEqual(self.s["list_no_sidecar"]["minigames"], [])
        mgs = self.s["list"]["minigames"]
        self.assertEqual(len(mgs), 1)                                        # the title without a state: not listed
        self.assertEqual(mgs[0]["players"], 2)
        self.assertTrue(re.fullmatch(r"mg_[0-9a-f]{12}", mgs[0]["id"]))
        self.assertNotIn(self.ids[b85.PS1_TITLE], json.dumps(self.s["list"]))  # opaque

    def test_refusals(self):
        self.assertGreaterEqual(self.s["start_no_board"]["code"], 400)
        self.assertIn("board game is not the running session", self.s["start_no_board"]["body"]["error"])
        self.assertIn("different seats", self.s["bad_seats"]["body"]["error"])
        self.assertIn("no such mini game", self.s["bad_id"]["body"]["error"])

    def test_ended_with_scores_in_the_order_of_the_seats(self):
        for tag, seats in (("m24", [2, 4]), ("m42", [4, 2])):
            self.assertEqual(self.s[tag + "_start"]["body"]["state"], "starting")
            p = self.s[tag + "_playing"]
            self.assertEqual(p["state"], "playing", p)
            self.assertIs(self.s[tag + "_title_paused_at_playing"], False, tag)   # the pause released for the players
            r = self.s[tag]
            self.assertEqual((r["state"], r["class"], r["scores"], r["seats"], r["recognised"]),
                             ("ended", "end_P1", [1, 0], seats, True), r)
            self.assertTrue(self.s[tag + "_end"]["body"]["ended"])
            self.assertTrue(self.s[tag + "_end_again"]["body"].get("again"))

    def test_the_pads_routed_for_the_mini_game_and_cleared(self):
        self.assertEqual(self.s["m24_route_during"], {"1": 0, "3": 1})      # seat 2 → port 1, seat 4 → port 2
        pressed = [w for w in self.s["m24_pads"] if w[1]]
        self.assertEqual(pressed, [["P1", 0x1000 | 2], ["P2", 0x1000 | 8]])  # players 1 and 3 dropped
        for tag in ("m24", "m42", "unrec", "limit", "home"):
            self.assertIsNone(self.s[tag + "_route_after"], tag)

    def test_the_stream_switched_both_ways_with_no_session_end(self):
        board = self.out["board_pid"]
        for tag in ("m24", "m42", "unrec", "limit"):
            ev = self.s[tag + "_events"]
            self.assertEqual([e[0] for e in ev], ["start", "start"], (tag, ev))  # no stop between
            self.assertNotEqual(ev[0][1], board)
            self.assertEqual(ev[1][1], board, tag)                          # the board's window again

    def test_no_key_to_the_board_during_a_mini_game(self):
        for tag in ("m24", "m42", "unrec", "limit", "home"):
            self.assertEqual(self.s[tag + "_keys_during"], [], tag)

    def test_not_recognised_and_the_time_limit_give_up(self):
        u = self.s["unrec"]
        self.assertEqual((u["state"], u["scores"]), ("given_up", None))
        self.assertIn("not recognised", u["why"])
        lim = self.s["limit"]
        self.assertEqual(lim["state"], "given_up")
        self.assertIn("no end within", lim["why"])
        for tag in ("unrec", "limit"):
            self.assertEqual(self.s[tag + "_status"]["launch_kind"], "godot", tag)   # the board's session back

    def test_home_pauses_the_title_only(self):
        self.assertEqual(self.s["home_home"]["code"], 200, self.s["home_home"]["body"])
        self.assertIn("PAUSE_TOGGLE", self.s["home_home_ra"])
        self.assertEqual(self.s["home_home_keys"], [])
        self.assertEqual(self.s["home_resume_ready"]["code"], 200, self.s["home_resume_ready"]["body"])
        self.assertEqual((self.s["home"]["state"], self.s["home"]["scores"]), ("ended", [0, 1]))

    def test_end_during_a_mini_game(self):
        self.assertEqual(self.s["end_stop"]["code"], 200, self.s["end_stop"]["body"])
        self.assertEqual(self.s["end_keys"], ["F10"])
        self.assertTrue(self.s["end_board_gone"])
        self.assertFalse(self.s["end_status_active"])
        self.assertEqual(self.s["end_result"]["state"], "given_up")
        self.assertIn("ended from the onn", self.s["end_result"]["why"])

    def test_the_board_dying_mid_game(self):
        self.assertTrue(self.s["died"].get("closed"), self.s["died"])
        self.assertEqual(self.s["died"]["why"], "the board stopped")
        self.assertEqual([r["step"] for r in self.s["died_rows"]], ["minigame_given_up", "minigame_end"])

    def test_nothing_of_the_users_touched(self):
        self.assertEqual(self.s["slots_count"], 4)
        self.assertTrue(self.s["slots_equal"])
        self.assertTrue(self.s["slots_equal_final"])
        self.assertEqual(self.s["scratch_left"], [])
        for tag in ("m24", "m42", "unrec", "limit", "home"):
            self.assertEqual(self.s[tag + "_scratch"], [], tag)

    def test_one_row_per_step(self):
        steps = self.s["m24_rows"]
        for want in ("minigame_start", "minigame_launch", "minigame_route", "minigame_stream", "minigame_watch",
                     "minigame_playing", "minigame_ended", "minigame_restore", "minigame_end"):
            self.assertIn(want, steps)


class FlagsAbsentAreToday(unittest.TestCase):
    def test_each_flag_absent(self):
        old = b99.BASELINE
        b99.BASELINE = BASELINE
        try:
            code = b99.head_code()
        finally:
            b99.BASELINE = old
        if code is None:
            self.skipTest("git is absent")
        for env in ({**b85.FLAGS, "PRIVYHUB_PARTY": "1"}, {**b85.FLAGS, "PRIVYHUB_H7": "1"}, b85.FLAGS,
                    {**b85.FLAGS, "PRIVYHUB_PARTY": "1", "PRIVYHUB_H7": "0"}):
            root, ids = b99.tree(code)
            base = run(root, env, ids, "today")
            root2, ids2 = b99.tree()
            mine = run(root2, env, ids2, "today")
            for k in ("list_before_launch", "start", "result", "end", "systems"):
                self.assertEqual((mine["steps"][k]["code"], mine["steps"][k]["raw"]),
                                 (base["steps"][k]["code"], base["steps"][k]["raw"]), (env, k))
            self.assertIn("Unknown Games plugin", base["steps"]["start"]["body"]["error"])


if __name__ == "__main__":
    unittest.main()
