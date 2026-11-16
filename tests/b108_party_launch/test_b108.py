#!/usr/bin/env python3
"""B108 (host): the board game as a launch behind PRIVYHUB_PARTY=1, through the companion's real HTTP server on loopback.

B103's harness (a child `python3 -I` on B82 / B83's fixture tree; the companion's handler on a ThreadingHTTPServer at
127.0.0.1:0; network beyond loopback blocked; B101's fake RetroArch for the emulator side; a stub stream that records
its starts). The board is **a stand-in**: a small executable script named as the config's `godot` — it records its
command line and environment, says its pid, and exits 0 when the fake F10 reaches it (or ignores it, when its project
folder holds IGNORE_F10). The key sender and the window / sound lookups are a fake `run` handed to the session (the
`xdotool` / `pactl` calls recorded); the pads' listing is a fake /proc file. QUIT_WAIT_S is 1 s in the test (8 s on the
hub). Flag absent / 0: the library and the routes on `git archive f302f8a8`'s companion and on this one, byte for
byte. Temp dirs removed at exit. No Godot, no emulator, no window.

    python3 -m unittest discover -s tests/b108_party_launch -v
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
sys.path.insert(0, str(ROOT / "tests" / "b99_h7_live_read"))
sys.path.insert(0, str(ROOT / "tests" / "b102_h7_endscreen"))
sys.path.insert(0, str(ROOT / "tests" / "b103_h7_minigame"))
sys.path.insert(0, str(ROOT / "companion"))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402  (modules: their tests are not collected twice)
import test_b103 as b103  # noqa: E402

BASELINE = "f302f8a8"                    # queue AO's baseline (PP-H1 committed): the companion before B108
ON = {**b85.FLAGS, "PRIVYHUB_PARTY": "1"}

BOARD = r'''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
here = Path(os.environ["B108_BOARD_DIR"])
project = Path(sys.argv[sys.argv.index("--path") + 1])
(here / "cmd.json").write_text(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(),
    "sdl_mapping": "PrivyHub Virtual Gamepad" in os.environ.get("SDL_GAMECONTROLLERCONFIG", "")}))
(here / "pid").write_text(str(os.getpid()))
keys = here / "keys"
end = time.time() + 120
while time.time() < end:
    if keys.exists() and "F10" in keys.read_text().split() and not (project / "IGNORE_F10").exists():
        (here / "pid").unlink()
        sys.exit(0)
    time.sleep(0.05)
'''

SCENARIO = r'''
try:
    import party_session as party           # this companion's (absent from HEAD's: the "today" run never needs it)
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
starts = []
def stream_start(**kw):
    starts.append({"pid": kw.get("managed_process_id"), "client_ip": kw.get("client_ip")})
    stream.active = True
    return {"active": True}
stream.start = stream_start
def stream_stop(*a, **k):
    stream.active = False
    return {"active": False}
stream.stop = stream_stop
def keys():
    p = board_dir / "keys"
    return p.read_text().split() if p.exists() else []
def rows():
    p = root / "logs/games/party.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.is_file() else []
def keyed(n0):
    return [c[-1] for c in cmds[n0:] if c[:2] == ["xdotool", "windowactivate"]]
out = {"steps": {}}
S = out["steps"]
cfg_path = Path(os.environ["PRIVYHUB_PARTY_CONFIG"])
good = {"godot": args["board"], "project": args["project"], "pictures": args["pictures"]}
def config(d):
    if d is None:
        cfg_path.unlink(missing_ok=True)
    else:
        cfg_path.write_text(json.dumps(d))
S["sources"] = call("GET", "/sources")
S["systems"] = call("GET", "/plugins/games/systems")
S["party_games"] = call("GET", "/plugins/games/games?system=party")
pid_ = [n for n in S["party_games"]["body"].get("nodes", []) if n.get("node_type") == "game"]
gid = pid_[0]["id"] if pid_ else None
S["party_id"] = gid
S["details"] = call("GET", f"/plugins/games/details?id={gid}")
S["details_ps1"] = call("GET", f"/plugins/games/details?id={args['id']}")
S["ps1_games"] = call("GET", "/plugins/games/games?system=ps1")
if args["mode"] == "today":
    S["status"] = call("GET", "/plugins/games/status")
    S["launch_ps1"] = call("POST", f"/plugins/games/launch?id={args['id']}")["code"]
    S["stop"] = call("POST", "/plugins/games/stop")["code"]
else:
    # the plain refusals
    config(None); S["no_config"] = call("POST", f"/plugins/games/launch?id={gid}")
    config({k: v for k, v in good.items() if k != "pictures"}); S["missing_field"] = call("POST", f"/plugins/games/launch?id={gid}")
    config({**good, "pictures": args["pictures"] + "_gone"}); S["missing_folder"] = call("POST", f"/plugins/games/launch?id={gid}")
    config({**good, "renderer": "forward_plus"}); S["bad_renderer"] = call("POST", f"/plugins/games/launch?id={gid}")
    config(good); S["with_mod"] = call("POST", f"/plugins/games/launch?id={gid}&mod_index=0")
    S["nothing_started"] = not (board_dir / "cmd.json").exists()
    # the launch
    config({**good, "renderer": "mobile"})
    n0 = len(cmds)
    S["launch"] = call("POST", f"/plugins/games/launch?id={gid}")
    S["cmd"] = json.loads((board_dir / "cmd.json").read_text()) if (board_dir / "cmd.json").exists() else None
    S["launch_keys"] = keyed(n0)
    S["status_running"] = call("GET", "/plugins/games/status")["body"]
    S["second_launch"] = call("POST", f"/plugins/games/launch?id={gid}")
    S["still_running_after_second"] = (board_dir / "pid").exists()
    # the stream as for a game
    S["stream_start"] = call("POST", "/plugins/games/native-stream-start?port=48100")
    S["starts"] = list(starts)
    S["ready"] = call("POST", "/plugins/games/native-stream-ready")
    S["keys_after_ready"] = keys()
    # Home: the stream closed by the client → pause → Esc once; a second Home: nothing
    S["home"] = call("POST", "/plugins/games/native-stream-stop")
    S["keys_after_home"] = keys()
    S["home_again"] = call("POST", "/plugins/games/native-stream-stop")
    S["keys_after_home_again"] = keys()
    # RESUME: the stream again, then ready → Esc once
    S["resume_start"] = call("POST", "/plugins/games/native-stream-start?port=48100")
    S["resume_ready"] = call("POST", "/plugins/games/native-stream-ready")
    S["keys_after_resume"] = keys()
    # SAVE / LOAD refused, nothing sent
    n0 = len(cmds)
    S["save"] = call("POST", "/plugins/games/save-state?slot=1")
    S["load"] = call("POST", "/plugins/games/load-state?slot=1")
    S["save_load_cmds"] = cmds[n0:]
    # END: F10, exit 0 awaited
    t = time.monotonic()
    S["end"] = call("POST", "/plugins/games/stop")
    S["end_s"] = round(time.monotonic() - t, 2)
    S["keys_after_end"] = keys()
    S["status_after_end"] = call("GET", "/plugins/games/status")["body"].get("active")
    S["board_gone"] = not (board_dir / "pid").exists()
    # END with a board that ignores F10: SIGTERM after QUIT_WAIT_S
    (board_dir / "keys").unlink(missing_ok=True)
    (Path(args["project"]) / "IGNORE_F10").write_text("1")
    S["launch_ignoring"] = call("POST", f"/plugins/games/launch?id={gid}")["code"]
    t = time.monotonic()
    S["end_ignoring"] = call("POST", "/plugins/games/stop")
    S["end_ignoring_s"] = round(time.monotonic() - t, 2)
    (Path(args["project"]) / "IGNORE_F10").unlink()
    (board_dir / "pid").unlink(missing_ok=True)
    # an emulator launch while the board runs, and the reverse
    (board_dir / "keys").unlink(missing_ok=True)
    S["board_then"] = call("POST", f"/plugins/games/launch?id={gid}")["code"]
    S["ps1_over_board"] = call("POST", f"/plugins/games/launch?id={args['id']}")["code"]
    S["keys_ps1_over_board"] = keys()
    S["status_ps1"] = call("GET", "/plugins/games/status")["body"].get("game", {}).get("system")
    (board_dir / "keys").unlink(missing_ok=True)
    S["board_over_ps1"] = call("POST", f"/plugins/games/launch?id={gid}")["code"]
    S["status_board"] = call("GET", "/plugins/games/status")["body"].get("launch_kind")
    S["ra_commands"] = fake["ra"].log if "ra" in fake else None
    # launch_orphaned: the plugin's own path
    (board_dir / "keys").unlink(missing_ok=True)
    pidnow = m.process.pid if m.process is not None else None
    S["orphaned"] = g.launch_orphaned("client_closed", 1.0, pidnow)
    S["keys_orphaned"] = keys()
    out["rows"] = rows()
    out["cmds_kinds"] = sorted({" ".join(c[:2]) for c in cmds})
httpd.shutdown()
print(json.dumps(out))
'''


def child() -> str:
    head = b103.CHILD.split('out = {"steps": {}}')[0]
    head = head.replace("import hashlib, json,", "import hashlib, json,")
    return head + "import types\n" + SCENARIO


def fixtures(work: Path) -> dict:
    board_dir = work / "board"
    board_dir.mkdir()
    board = work / "board_standin"
    board.write_text(BOARD)
    board.chmod(0o755)
    project = work / "project"
    project.mkdir()
    (project / "project.godot").write_text("; a stand-in\n")
    pictures = work / "pictures"
    pictures.mkdir()
    (pictures / "one.txt").write_text("x")
    devices = work / "devices"
    blocks = [("P3", 7), ("P1", 4), ("P4", 9), ("P2", 5)]          # the system's listing, not in creation order
    devices.write_text("\n\n".join(f'N: Name="PrivyHub Virtual Gamepad {p}"\nH: Handlers=js{e} event{e}' for p, e in blocks)
                       + "\n\nN: Name=\"Some Keyboard\"\nH: Handlers=sysrq kbd event1\n")
    return {"board_dir": str(board_dir), "board": str(board), "project": str(project), "pictures": str(pictures),
            "devices": str(devices)}


def run(root: Path, env: dict, gid: str, mode: str) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="b108_fx_"))
    fx = fixtures(work)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules"),
                      "PRIVYHUB_PARTY_CONFIG": str(work / "party.json"), "B108_BOARD_DIR": fx["board_dir"]})
    (root / "tools").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools" / "h7_endscreen.py", root / "tools" / "h7_endscreen.py")
    frames, spec_dir, _js = b103.fixtures(work)
    try:
        r = subprocess.run([sys.executable, "-I", "-B", "-c", child(), str(root),
                            json.dumps({"id": gid, "mode": mode, "p1": b99.P1, "p2": b99.P2, "frames": str(frames),
                                        "spec_dir": str(spec_dir), **fx})],
                           cwd=root, env=child_env, capture_output=True, text=True, timeout=900)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-3000:]
    # each run has its own fixture tree: its folder named the same way in every run (the library names it)
    text = r.stdout.strip().splitlines()[-1]
    for form in {str(root), str(root.resolve())}:
        text = text.replace(form, "<root>")
    return json.loads(text)


def steps(rows, name):
    return [r for r in rows if r.get("step") == name]


class Board(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b99.tree()
        cls.ps1 = ids[b85.PS1_TITLE]
        cls.out = run(root, ON, cls.ps1, "on")
        cls.s = cls.out["steps"]

    def err(self, r):
        return r["code"], r["body"].get("error")

    def test_listed_as_its_own_system_with_one_game(self):
        systems = json.dumps(self.s["systems"]["body"])
        self.assertIn("games_system_party", systems)
        games = [n for n in self.s["party_games"]["body"]["nodes"] if n.get("node_type") == "game"]
        self.assertEqual(len(games), 1)
        self.assertTrue(self.s["party_id"].startswith("game_party_"))
        self.assertEqual(self.s["details"]["code"], 200)

    def test_the_plain_refusals(self):
        for k, want in (("no_config", "The board game is not set up on this hub (no config file)"),
                        ("missing_field", "The board game's config is incomplete: pictures"),
                        ("missing_folder", "The board game's pictures was not found"),
                        ("bad_renderer", "The board game's renderer must be gl_compatibility or mobile"),
                        ("with_mod", "Cheats and mods are not offered for the board game.")):
            code, error = self.err(self.s[k])
            self.assertGreaterEqual(code, 400, k)
            self.assertIn(want, error, k)
        self.assertTrue(self.s["nothing_started"])

    def test_the_launch(self):
        b = self.s["launch"]["body"]
        self.assertEqual(self.s["launch"]["code"], 200, b)
        self.assertEqual((b["active"], b["paused"], b["launch_kind"]), (True, True, "godot"))
        argv = self.s["cmd"]["argv"]
        self.assertEqual(argv[:8], ["--path", self.s["cmd"]["cwd"], "--rendering-method", "mobile",
                                    "--rendering-driver", "vulkan", "--fullscreen", "--"])
        self.assertTrue(argv[8].startswith("--content=") and argv[8].endswith("pictures"))
        self.assertTrue(self.s["cmd"]["sdl_mapping"])
        self.assertEqual(self.s["launch_keys"], [])                          # no key at launch (the lobby)
        st = self.s["status_running"]
        self.assertEqual((st["launch_kind"], st["party"]["window"], st["party"]["renderer"]), ("godot", True, "mobile"))
        rows = self.out["rows"]
        w = steps(rows, "window")[0]
        self.assertEqual((w["found"], w["class"]), (True, "PrivyParty"))
        self.assertTrue(steps(rows, "audio")[0]["sink_input"])
        self.assertNotIn("b108_fx_", json.dumps(rows))                      # no path of the config's in a row

    def test_the_pads_in_creation_order(self):
        pads = steps(self.out["rows"], "pads")[0]["in_event_order"]
        self.assertEqual([p["player"] for p in pads], [1, 2, 3, 4])

    def test_the_stream_as_for_a_game(self):
        self.assertEqual(self.s["stream_start"]["code"], 200, self.s["stream_start"]["body"])
        self.assertTrue(self.s["stream_start"]["body"].get("party_mode"))
        self.assertEqual(len(self.s["starts"]), 1)
        self.assertIsNotNone(self.s["starts"][0]["pid"])
        self.assertEqual(self.s["ready"]["code"], 200, self.s["ready"]["body"])
        self.assertTrue(self.s["ready"]["body"]["released"])
        self.assertEqual(self.s["keys_after_ready"], [])                     # the first release: no key

    def test_home_pauses_once_and_resume_resumes(self):
        self.assertEqual(self.s["home"]["code"], 200, self.s["home"]["body"])
        self.assertEqual(self.s["keys_after_home"], ["Escape"])
        self.assertEqual(self.s["keys_after_home_again"], ["Escape"])        # already paused: nothing sent
        self.assertEqual(self.s["resume_ready"]["code"], 200, self.s["resume_ready"]["body"])
        self.assertEqual(self.s["keys_after_resume"], ["Escape", "Escape"])
        steps_ = [(r["step"], r.get("key")) for r in self.out["rows"] if r["step"] in ("pause", "resume")]
        self.assertIn(("pause", "Escape"), steps_)
        self.assertIn(("resume", "Escape"), steps_)

    def test_save_and_load_refused_nothing_sent(self):
        for k in ("save", "load"):
            code, error = self.err(self.s[k])
            self.assertGreaterEqual(code, 400)
            self.assertIn("Saving and loading are not offered for the board game; nothing was sent.", error)
        self.assertEqual(self.s["save_load_cmds"], [])

    def test_end_quits_by_f10(self):
        b = self.s["end"]["body"]
        self.assertEqual(self.s["end"]["code"], 200, b)
        self.assertEqual((b["party_exit"], b["graceful"]), ("quit 0", True))
        self.assertEqual(self.s["keys_after_end"][-1], "F10")
        self.assertTrue(self.s["board_gone"])
        self.assertFalse(self.s["status_after_end"])
        self.assertLess(self.s["end_s"], 1.0)
        self.assertIn({"step": "exited", "code": 0}, [{k: r[k] for k in ("step", "code")} for r in steps(self.out["rows"], "exited")])

    def test_end_with_a_board_that_ignores_f10(self):
        self.assertEqual(self.s["launch_ignoring"], 200)
        b = self.s["end_ignoring"]["body"]
        self.assertEqual(self.s["end_ignoring"]["code"], 200, b)
        self.assertTrue(b["party_exit"].startswith("sigterm"), b)
        self.assertFalse(b["graceful"])
        self.assertGreaterEqual(self.s["end_ignoring_s"], 1.0)
        st = steps(self.out["rows"], "sigterm")
        self.assertEqual(len(st), 1)
        self.assertIn("no exit", st[0]["why"])

    def test_a_second_launch_while_it_runs(self):
        code, error = self.err(self.s["second_launch"])
        self.assertGreaterEqual(code, 400)
        self.assertIn("already running", error)

    def test_an_emulator_over_the_board_and_the_reverse(self):
        self.assertEqual((self.s["board_then"], self.s["ps1_over_board"]), (200, 200))
        self.assertEqual(self.s["keys_ps1_over_board"][-1], "F10")           # the board quit first
        self.assertEqual(self.s["status_ps1"], "ps1")
        self.assertEqual(self.s["board_over_ps1"], 200)                      # the emulator stopped first
        self.assertEqual(self.s["status_board"], "godot")

    def test_launch_orphaned_quits_the_board(self):
        self.assertTrue(self.s["orphaned"]["stopped"])
        self.assertEqual(self.s["keys_orphaned"][-1], "F10")

    def test_only_these_commands(self):
        self.assertEqual(self.out["cmds_kinds"], ["pactl list", "xdotool getwindowpid", "xdotool search",
                                                  "xdotool windowactivate"])


class PadsFollowTheOnnsSlots(unittest.TestCase):
    """The onn picks each pad's player byte (its own join, the lowest open slot); the hub drives P<byte+1> whatever
    order the pads joined in — the bridge's own mapping, with recording pads."""

    def test_a_shuffled_join(self):
        import native_session_io as nsio
        b = nsio.NativeControllerBridge(Path(tempfile.mkdtemp(prefix="b108_bridge_")))
        b._gamepads = [f"P{i + 1}" for i in range(b.MAX_PLAYERS)]
        b._controller_backend = "linux_uinput"
        got = []
        b._write_linux_report_locked = lambda index, report, *a, **k: got.append((b._gamepads[index], report["buttons"]))
        for player in (2, 0, 3, 1):                                         # the pads joined in this order
            b._apply_report(player, 1 << player, 0, 0, 0, 0, 0, 0)
        self.assertEqual(sorted(got), [("P1", 1), ("P2", 2), ("P3", 4), ("P4", 8)])
        self.assertEqual([nsio.NativeControllerBridge.LINUX_GAMEPAD_NAME.format(player=i + 1) for i in range(4)],
                         [f"PrivyHub Virtual Gamepad P{i}" for i in (1, 2, 3, 4)])


class TheBoardsToggle(unittest.TestCase):
    """The board's pause is a toggle: the session sends Esc only to change the state (the plugin also pauses only an
    unpaused game, so this is the second guard), and never before the board's first release."""

    def test_one_key_per_change(self):
        import types
        import party_session as party
        sent = []

        def run(cmd, timeout=3.0):
            if cmd[:2] == ["xdotool", "windowactivate"]:
                sent.append(cmd[-1])
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        sess = party.Session(4242, lambda row: None, run=run)
        sess.window_id = "7"
        self.assertEqual((sess.pause(), sent), ("held", []))               # the lobby, before the first release
        self.assertEqual((sess.resume(), sent), ("released", []))
        self.assertEqual((sess.pause(), sess.pause(), sent), ("key", "already", ["Escape"]))
        self.assertEqual((sess.resume(), sess.resume(), sent), ("key", "released", ["Escape", "Escape"]))


class FlagAbsentIsToday(unittest.TestCase):
    def test_absent_and_zero_answer_as_heads_code(self):
        old = b99.BASELINE
        b99.BASELINE = BASELINE
        try:
            code = b99.head_code()
        finally:
            b99.BASELINE = old
        if code is None:
            self.skipTest("git is absent")
        root, ids = b99.tree(code)
        gid = ids[b85.PS1_TITLE]
        base = run(root, b85.FLAGS, gid, "today")
        keys = ("sources", "systems", "party_games", "details", "details_ps1", "ps1_games")
        import re
        masked = lambda raw: re.sub(r"-?\d+(\.\d+)?", "#", raw)          # status: its counters run (keys / words exact)
        for env in (b85.FLAGS, {**b85.FLAGS, "PRIVYHUB_PARTY": "0"}):
            root2, _ = b99.tree()
            mine = run(root2, env, gid, "today")
            for k in keys:
                self.assertEqual((mine["steps"][k]["code"], mine["steps"][k]["raw"]),
                                 (base["steps"][k]["code"], base["steps"][k]["raw"]), k)
            self.assertEqual((mine["steps"]["status"]["code"], masked(mine["steps"]["status"]["raw"])),
                             (base["steps"]["status"]["code"], masked(base["steps"]["status"]["raw"])))
            for k in ("launch_ps1", "stop", "party_id"):
                self.assertEqual(mine["steps"][k], base["steps"][k], k)
        self.assertIsNone(base["steps"]["party_id"])
        self.assertNotIn("party", base["steps"]["systems"]["raw"])


if __name__ == "__main__":
    unittest.main()
