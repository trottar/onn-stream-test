#!/usr/bin/env python3
"""B103 (host): H7's mini game — `POST /plugins/games/h7-start[?load=0]` and `GET /plugins/games/h7-result` behind
PRIVYHUB_H7=1, through the companion's real HTTP server on loopback.

B101's harness (a child `python3 -I` on B82 / B83's fixture tree with its own companion/ and tools/h7_endscreen.py;
`privyhub_service`'s handler on a ThreadingHTTPServer at 127.0.0.1:0; network beyond loopback blocked; a made-up PS1
title launched through `POST /plugins/games/launch`; B101's fake RetroArch with its command log and its load). The
picture source is a fake the test scripts: synthetic frames drawn as in B102's tests (a still panel, a moving banner, a
varying portrait, a seven-segment tally: start 0-0, end_P1 1-0, end_P2 0-1, unknown 1-1; other = moving shapes), and
a spec learnt from B102's synthetic runs in the test and put in the test's rules folder. Made-up slot files 1-3 and the
slot-0 copy hashed before and after. Flag absent / 0: the routes on the baseline's companion (`git archive 8b43a266`)
and on this one, byte for byte. No emulator; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b103_h7_minigame -v
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
sys.path.insert(0, str(ROOT / "tools"))
import _tmp_cleanup  # noqa: E402,F401
import numpy as np  # noqa: E402
import h7_endscreen as E  # noqa: E402
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402  (modules: their tests are not collected twice)
import test_b102 as b102  # noqa: E402

ON = {**b85.FLAGS, "PRIVYHUB_H7": "1"}
BASELINE = "8b43a266"                   # queue AM's baseline (H7-V1 committed): the companion before B103
TALLY = {"start": "00", "end_P1": "10", "end_P2": "01", "unknown": "11"}

CHILD = r'''
import hashlib, json, os, re, shutil, socket, subprocess, sys, threading, time, types, urllib.request, urllib.error
from pathlib import Path
root = Path(sys.argv[1]).resolve()
args = json.loads(sys.argv[2])
rules = os.environ.get("PRIVYHUB_H7_RULES", "")
_connect = socket.socket.connect
def _guard(self, addr, *a, **k):
    if isinstance(addr, tuple) and addr[0] not in ("127.0.0.1", "localhost", "::1"):
        raise OSError("network beyond loopback blocked by the test")
    return _connect(self, addr, *a, **k)
socket.socket.connect = _guard
_real_run = subprocess.run
def _run(cmd, *a, **k):
    return types.SimpleNamespace(returncode=1, stdout=b"" if not k.get("text") else "", stderr="")
subprocess.run = _run
sys.path.insert(0, str(root / "companion"))
import privyhub_service as svc
from plugins import PLUGINS
from games import emulator_manager as em
g = PLUGINS["games"]
g._metadata_reconcile_thread.join(120)
m = g._emulator
class Inert:
    def __getattr__(self, name): return Inert()
    def __call__(self, *a, **k): return {}
    def __bool__(self): return False
class Stream(Inert):
    active = True
    def status(self): return {"active": self.active}
stream = Stream()
g._native_stream = stream
P1, P2 = args["p1"], args["p2"]
fake = {}
def folder():
    return m._state_root() / "Beetle PSX HW"
class FakeRetroArch:
    def __init__(self, cmd, **kw):
        self.pid = 999999999; self.returncode = None; self.stdin = None; self.stop = False
        self.out = kw.get("stdout"); self.paused = False
        self.mem = bytearray(0x200000); self.log = []; self.refuse = False; self.silent = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", int(m._network_cmd_port)))
        self.sock.settimeout(0.02)
        fake["ra"] = self
        threading.Thread(target=self.serve, daemon=True).start()
    def put(self, a, b):
        self.mem[P1:P1 + 2] = int(a).to_bytes(2, "little"); self.mem[P2:P2 + 2] = int(b).to_bytes(2, "little")
    def logline(self, line):
        self.out.write(line + "\n"); self.out.flush()
    def serve(self):
        while not self.stop:
            try:
                data, addr = self.sock.recvfrom(4096)
            except OSError:
                continue
            c = data.decode().strip(); w = c.split()
            self.log.append(w[0] if w else "")
            if c == "GET_STATUS":
                self.sock.sendto(f"GET_STATUS {'PAUSED' if self.paused else 'PLAYING'} psx,fixture,crc32=0".encode(), addr)
            elif c == "PAUSE_TOGGLE":
                self.paused = not self.paused
            elif c == "SAVE_FILES":
                self.sock.sendto(b"SAVE_FILES OK", addr)
            elif w and w[0] == "LOAD_STATE_SLOT" and len(w) == 2:
                p = folder() / (m._active_state_stem() + f".state{w[1]}")
                if self.silent:
                    pass
                elif self.refuse or not p.is_file():
                    self.logline(f'[ERROR] [State] Failed to load state from "{p}".')
                else:
                    vals = json.loads(p.read_text())
                    self.put(vals["P1"], vals["P2"])
                    self.logline(f'[INFO] [State] Loading state "{p}", {p.stat().st_size} bytes.')
                self.sock.sendto(c.encode(), addr)
            elif w and w[0] in ("READ_CORE_RAM", "READ_CORE_MEMORY") and len(w) == 3:
                a, n = int(w[1], 16), int(w[2])
                body = "-1" if a + n > len(self.mem) else " ".join(f"{b:02x}" for b in self.mem[a:a + n])
                self.sock.sendto(f"{w[0]} {w[1]} {body}".encode(), addr)
    def poll(self): return self.returncode
    def wait(self, timeout=None):
        self.returncode = 0; self.stop = True; return 0
    def terminate(self): self.returncode = -15; self.stop = True
    def kill(self): self.returncode = -9; self.stop = True
em.subprocess.Popen = FakeRetroArch
from PIL import Image
frames = Path(args["frames"])
class FakePicture:
    """Scripted pictures: each grab takes the next token ('fail' raises); the last token repeats."""
    def __init__(self):
        self.script = []; self.grabs = 0; self.lock = threading.Lock(); self.n = {}
    def set(self, tokens):
        with self.lock:
            self.script = list(tokens)
    def grab(self):
        with self.lock:
            tok = self.script.pop(0) if len(self.script) > 1 else (self.script[0] if self.script else "other")
            self.grabs += 1
            i = self.n[tok] = (self.n.get(tok, -1) + 1) % 6
        if tok == "fail":
            raise RuntimeError("the picture was not read: a scripted failure")
        with Image.open(frames / f"{tok}_{i}.png") as im:
            return im.convert("L")
pic = FakePicture()
from http.server import ThreadingHTTPServer
httpd = ThreadingHTTPServer(("127.0.0.1", 0), svc.PrivyHubRequestHandler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
port = httpd.server_address[1]
def call(method, path, timeout=60):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            code, raw = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read().decode()
    return {"code": code, "raw": raw, "body": json.loads(raw or "{}")}
def result():
    return call("GET", "/plugins/games/h7-result")["body"]
def start(q=""):
    return call("POST", "/plugins/games/h7-start" + q)
def timeline(bound=30, until=("ended",), stop_at_reads=None):
    """GET every 30 ms: the distinct (reads, state, class, seen_start) seen, until a state in `until` or the bound."""
    seen = []; end = time.monotonic() + bound
    while time.monotonic() < end:
        b = result()
        key = [b.get("reads"), b.get("state"), b.get("class"), b.get("seen_start")]
        if not seen or seen[-1] != key:
            seen.append(key)
        if b.get("state") in until or (stop_at_reads is not None and (b.get("reads") or 0) >= stop_at_reads):
            return seen, b
        time.sleep(0.03)
    return seen, {"timeout": True}
out = {"steps": {}}
S = out["steps"]
S["get_before_launch"] = call("GET", "/plugins/games/h7-result")
S["start_before_launch"] = start()
S["launch"] = call("POST", f"/plugins/games/launch?id={args['id']}")["code"]
time.sleep(0.3)
if args["mode"] == "today":
    S["get_after"] = call("GET", "/plugins/games/h7-result")
    S["start_after"] = start()
    S["start_after_load0"] = start("?load=0")
else:
    mini = g._h7_minigame_runner()
    mini.picture = pic
    mini.read_every = 0.2
    ra = fake["ra"]; ra.paused = False
    stem = m._active_state_stem(); f = folder(); f.mkdir(parents=True, exist_ok=True)
    slots = [f / (stem + x) for x in (".state", ".state1", ".state2", ".state3")]
    for i, p in enumerate(slots):
        p.write_bytes(os.urandom(64) + bytes([i]))
    digest = lambda: [hashlib.sha256(p.read_bytes()).hexdigest() for p in slots]
    before = digest()
    Path(rules).mkdir(parents=True, exist_ok=True)
    S["get_no_spec"] = result()
    S["start_no_spec"] = start()
    Path(rules, args["id"] + ".endscreen.json").write_text("{not json")
    S["get_bad_spec"] = result()
    S["start_bad_spec"] = start()
    for name in os.listdir(args["spec_dir"]):
        shutil.copyfile(Path(args["spec_dir"], name), Path(rules, name.replace("GAME", args["id"])))
    S["get_idle"] = result()
    S["start_no_state"] = start()
    S["start_bad_load_word"] = start("?load=2")
    Path(rules, args["id"] + ".state").write_text(json.dumps({"P1": 0, "P2": 0}))
    stream.active = False; S["start_no_stream"] = start(); stream.active = True
    old_sys = m.active_game.get("system"); m.active_game["system"] = "n64"; S["start_n64"] = start(); m.active_game["system"] = old_sys
    m._launch_kind = "pcsx2"; S["start_ps2"] = start(); m._launch_kind = None
    ra.put(77, 33)
    # a load the fake refuses; a load with no line
    ra.refuse = True; S["load_refused"] = start(); ra.refuse = False
    S["load_refused_mem"] = [int.from_bytes(ra.mem[P1:P1 + 2], "little"), int.from_bytes(ra.mem[P2:P2 + 2], "little")]
    ra.silent = True; t = time.monotonic(); S["load_silent"] = start(); S["load_silent_s"] = round(time.monotonic() - t, 2); ra.silent = False
    S["load_silent_mem"] = [int.from_bytes(ra.mem[P1:P1 + 2], "little"), int.from_bytes(ra.mem[P2:P2 + 2], "little")]
    S["scratch_after_refusals"] = sorted(p.name for p in f.iterdir() if p.name.endswith(".state8"))
    S["get_after_refusals"] = result()
    # W1: the load, then start, an other stretch, two end reads broken by an other, three end reads → ended end_P1
    pic.set(["start"] * 2 + ["other"] * 5 + ["end_P1"] * 2 + ["other"] + ["end_P1"] * 3 + ["end_P2"] * 20)
    n0 = len(ra.log); g0 = pic.grabs
    S["w1_start"] = start()
    S["w1_second"] = start()
    S["w1_timeline"], S["w1"] = timeline()
    time.sleep(1.0)
    S["w1_after"] = result(); S["w1_grabs"] = pic.grabs - g0
    S["w1_commands"] = ra.log[n0:]
    S["w1_mem"] = [int.from_bytes(ra.mem[P1:P1 + 2], "little"), int.from_bytes(ra.mem[P2:P2 + 2], "little")]
    # W2: no load; an end shown before any start is not counted
    pic.set(["end_P2"] * 5 + ["other"] * 3 + ["start"] * 3 + ["end_P2"] * 3 + ["end_P1"] * 20)
    n0 = len(ra.log)
    S["w2_start"] = start("?load=0")
    S["w2_timeline"], S["w2"] = timeline()
    S["w2_commands"] = ra.log[n0:]
    # W3: an unknown screen (1-1): reported, never an end; a second start refused meanwhile; then end_P1
    pic.set(["start"] * 3 + ["unknown"] * 8 + ["end_P1"] * 3 + ["end_P2"] * 20)
    S["w3_start"] = start("?load=0")
    S["w3_mid_timeline"], S["w3_mid"] = timeline(until=(), stop_at_reads=9)
    S["w3_second"] = start("?load=0")
    S["w3_timeline"], S["w3"] = timeline()
    # W4: a failed picture is a row and the watch goes on
    pic.set(["start"] * 3 + ["fail"] * 2 + ["end_P2"] * 3 + ["other"] * 20)
    S["w4_start"] = start("?load=0")
    S["w4_timeline"], S["w4"] = timeline()
    # W5: a PS2 game, the watcher alone (load=0): any system
    m._launch_kind = "pcsx2"
    pic.set(["start"] * 3 + ["end_P2"] * 3 + ["other"] * 20)
    n0 = len(ra.log)
    S["w5_start"] = start("?load=0")
    S["w5_timeline"], S["w5"] = timeline()
    S["w5_commands"] = ra.log[n0:]
    m._launch_kind = None
    # W6: an other stretch never ends it; then the user's END
    pic.set(["start"] * 3 + ["other"] * 40)
    S["w6_start"] = start()
    S["w6_timeline"], S["w6"] = timeline(until=(), stop_at_reads=25)
    S["w6_stop"] = call("POST", "/plugins/games/stop")["code"]
    time.sleep(1.0)
    S["w6_after"] = result()
    S["w6_lock_free"] = m.lock.acquire(timeout=1.0)
    if S["w6_lock_free"]: m.lock.release()
    S["scratch_left"] = sorted(p.name for p in f.iterdir() if p.name.endswith(".state8"))
    S["slots_equal"] = digest() == before
    log = root / "logs/games/h7_results.jsonl"
    out["rows"] = [json.loads(l) for l in log.read_text().splitlines()] if log.is_file() else None
    out["contest_rows"] = (root / "logs/games/h7_contests.jsonl").is_file()
httpd.shutdown()
print(json.dumps(out))
'''


def fixtures(root: Path) -> tuple[Path, Path]:
    """The frame library (six of each token) and a spec learnt from B102's synthetic runs (named GAME.*)."""
    rng = np.random.default_rng(103)
    frames = root / "frames"
    frames.mkdir()
    for tok, tally in TALLY.items():
        for i in range(6):
            b102.screen(50 + i, tally, rng).save(frames / f"{tok}_{i}.png")
    for i in range(6):
        b102.other(900 + i, rng).save(frames / f"other_{i}.png")
    learn = Path(tempfile.mkdtemp(prefix="b103_learn_"))
    runs, labels = b102.write_runs(learn)
    spec, arrays, _ = E.learn(runs, labels, name="GAME")
    spec_dir = root / "spec"
    spec_dir.mkdir()
    E.save_spec(spec, arrays, spec_dir / "GAME.endscreen.json")
    js = json.loads((spec_dir / "GAME.endscreen.json").read_text())
    shutil.rmtree(learn, ignore_errors=True)
    return frames, spec_dir, js


def run(root: Path, env: dict, gid: str, mode: str) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules")})
    (root / "tools").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools" / "h7_endscreen.py", root / "tools" / "h7_endscreen.py")
    work = Path(tempfile.mkdtemp(prefix="b103_fx_"))
    frames, spec_dir, js = fixtures(work)
    # the spec's arrays file is named by its JSON: GAME.endscreen.npz → <id>.endscreen.npz on the copy
    js["arrays"] = f"{gid}.endscreen.npz"
    (spec_dir / "GAME.endscreen.json").write_text(json.dumps(js))
    r = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, str(root),
                        json.dumps({"id": gid, "mode": mode, "p1": b99.P1, "p2": b99.P2, "frames": str(frames),
                                    "spec_dir": str(spec_dir)})],
                       cwd=root, env=child_env, capture_output=True, text=True, timeout=900)
    shutil.rmtree(work, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def first(timeline, state):
    return next((t for t in timeline if t[1] == state), None)


class MiniGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b99.tree()
        cls.gid = ids[b85.PS1_TITLE]
        cls.out = run(root, ON, cls.gid, "on")
        cls.s = cls.out["steps"]

    def err(self, r):
        return r["code"], r["body"].get("error")

    def test_no_game(self):
        self.assertEqual(self.s["get_before_launch"]["body"], {"ok": True, "state": "no_game"})
        self.assertEqual(self.err(self.s["start_before_launch"]), (400, "no game is running"))

    def test_no_spec(self):
        self.assertEqual((self.s["get_no_spec"]["state"], self.s["get_no_spec"]["why"]),
                         ("no_spec", "no end-screen spec for this game"))
        self.assertEqual(self.err(self.s["start_no_spec"]), (400, "no end-screen spec for this game"))
        self.assertEqual(self.s["get_bad_spec"]["state"], "no_spec")
        self.assertTrue(self.s["get_bad_spec"]["why"].startswith("the end-screen spec for this game cannot be read"))
        self.assertEqual(self.s["start_bad_spec"]["code"], 400)
        self.assertEqual(self.s["get_idle"], {"ok": True, "state": "idle", "game": self.gid})

    def test_the_loads_refusals_as_b101s(self):
        self.assertEqual(self.err(self.s["start_no_state"]), (400, "no state for this game's mini game"))
        self.assertEqual(self.err(self.s["start_bad_load_word"]), (400, "load is 0 or 1"))
        self.assertEqual(self.err(self.s["start_no_stream"]), (400, "the stream is not up"))
        self.assertEqual(self.err(self.s["start_n64"]),
                         (400, "not supported yet — a state cannot be loaded into a running N64 game"))
        self.assertEqual(self.err(self.s["start_ps2"]), (400, "not supported yet"))
        self.assertEqual(self.err(self.s["load_refused"]), (503, "the mini game's state did not load; the game is as it was"))
        self.assertEqual(self.s["load_refused_mem"], [77, 33])
        self.assertEqual(self.err(self.s["load_silent"]), (503, "the mini game's state did not load; the game is as it was"))
        self.assertLess(self.s["load_silent_s"], 1.5 + 1.0)
        self.assertEqual(self.s["load_silent_mem"], [77, 33])
        self.assertEqual(self.s["scratch_after_refusals"], [])
        self.assertEqual(self.s["get_after_refusals"]["state"], "idle")

    def test_start_watching_then_the_end_screen_after_k_reads(self):
        st = self.s["w1_start"]["body"]
        self.assertEqual((st["watch"], st["loaded"], st["game"]), ("started", True, self.gid))
        self.assertIsNotNone(st["load_line_ms"])
        self.assertEqual(self.err(self.s["w1_second"]), (400, "a mini game is already being watched"))
        w = self.s["w1"]
        self.assertEqual((w["state"], w["class"], w["seen_start"]), ("ended", "end_P1", True))
        self.assertEqual(w["reads"], 13)                                   # 2 + 5 + 2 + 1 + the third end read
        self.assertIn("ended_after_s", w)
        self.assertIn("since_s", w)
        self.assertEqual(set(w["last"]), {"distances", "margin"})
        ended_at = first(self.s["w1_timeline"], "ended")
        self.assertEqual(ended_at[0], 13)
        self.assertTrue(all(t[1] == "watching" for t in self.s["w1_timeline"] if (t[0] or 0) < 13))
        self.assertEqual(self.s["w1_after"]["reads"], 13)                  # it stopped reading
        self.assertEqual(self.s["w1_grabs"], 13)
        self.assertEqual(self.s["w1_after"]["state"], "ended")

    def test_no_command_to_the_game_beyond_the_load(self):
        self.assertEqual(self.s["w1_commands"], ["LOAD_STATE_SLOT"])
        self.assertEqual(self.s["w1_mem"], [0, 0])                         # the state's own values: the load took
        self.assertEqual(self.s["w2_commands"], [])
        self.assertEqual(self.s["w5_commands"], [])

    def test_an_end_before_any_start_is_not_counted(self):
        w = self.s["w2"]
        self.assertEqual((self.s["w2_start"]["body"]["loaded"], w["state"], w["class"]), (False, "ended", "end_P2"))
        self.assertEqual(w["reads"], 14)                                   # 5 + 3 + 3 + 3
        tl = self.s["w2_timeline"]
        self.assertTrue(all(t[3] is False for t in tl if t[0] is not None and t[0] <= 10))
        self.assertTrue(all(t[1] == "watching" for t in tl if (t[0] or 0) < 14))

    def test_an_unknown_screen_is_said_never_ended(self):
        mid = self.s["w3_mid"]
        self.assertEqual((mid["state"], mid["class"]), ("watching", "unknown"))
        self.assertEqual(self.err(self.s["w3_second"]), (400, "a mini game is already being watched"))
        self.assertTrue(all(t[1] == "watching" for t in self.s["w3_timeline"] if (t[0] or 0) < 14))
        self.assertIn("unknown", [t[2] for t in self.s["w3_mid_timeline"] + self.s["w3_timeline"]])
        self.assertEqual((self.s["w3"]["state"], self.s["w3"]["class"], self.s["w3"]["reads"]), ("ended", "end_P1", 14))

    def test_a_failed_picture_is_a_row_and_the_watch_goes_on(self):
        w = self.s["w4"]
        self.assertEqual((w["state"], w["class"], w["reads"], w["picture_failures"]), ("ended", "end_P2", 6, 2))

    def test_the_watcher_alone_on_any_system(self):
        self.assertEqual(self.s["w5_start"]["code"], 200)
        self.assertEqual((self.s["w5"]["state"], self.s["w5"]["class"]), ("ended", "end_P2"))

    def test_an_other_stretch_never_ends_it_and_end_stops_it(self):
        w = self.s["w6"]
        self.assertEqual((w["state"], w["class"]), ("watching", "other"))
        self.assertGreaterEqual(w["reads"], 25)
        self.assertNotIn("ended", [t[1] for t in self.s["w6_timeline"]])
        self.assertEqual(self.s["w6_stop"], 200)
        self.assertEqual(self.s["w6_after"], {"ok": True, "state": "no_game", "stopped": "the game stopped"})
        self.assertTrue(self.s["w6_lock_free"])
        self.assertEqual(self.s["scratch_left"], [])

    def test_the_users_slots_untouched(self):
        self.assertTrue(self.s["slots_equal"])

    def test_one_row_per_change(self):
        rows = self.out["rows"]
        steps = [r["step"] for r in rows]
        for want in ("refused", "loaded", "error", "watching", "start_seen", "unknown_screen", "ended", "stopped",
                     "picture_failed"):
            self.assertIn(want, steps)
        self.assertEqual(steps.count("ended"), 5)
        self.assertEqual(steps.count("stopped"), 1)
        self.assertEqual(steps.count("picture_failed"), 2)
        self.assertEqual(steps.count("unknown_screen"), 1)
        self.assertEqual([r["class"] for r in rows if r["step"] == "ended"],
                         ["end_P1", "end_P2", "end_P1", "end_P2", "end_P2"])
        self.assertFalse(self.out["contest_rows"])                         # nothing in B101's log


class FlagAbsentIsToday(unittest.TestCase):
    def test_absent_and_zero_answer_as_the_baselines_code(self):
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
        keys = ("get_before_launch", "start_before_launch", "get_after", "start_after", "start_after_load0")
        for env in (b85.FLAGS, {**b85.FLAGS, "PRIVYHUB_H7": "0"}):
            root2, _ = b99.tree()
            mine = run(root2, env, gid, "today")
            for k in keys:
                self.assertEqual((mine["steps"][k]["code"], mine["steps"][k]["raw"]),
                                 (base["steps"][k]["code"], base["steps"][k]["raw"]), k)
            self.assertEqual(mine["steps"]["launch"], base["steps"]["launch"])
        self.assertEqual(base["steps"]["get_after"]["body"]["error"], "Unknown Games plugin action: h7-result")
        self.assertEqual(base["steps"]["start_after"]["body"]["error"], "Unknown Games plugin POST action: h7-start")


if __name__ == "__main__":
    unittest.main()
