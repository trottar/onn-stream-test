#!/usr/bin/env python3
"""B101 (host): H7's timed contest — `POST /plugins/games/h7-contest?seconds=N` and `GET /plugins/games/h7-contest`
behind PRIVYHUB_H7=1, through the companion's real HTTP server on loopback.

B99's harness (a child `python3 -I` on B82 / B83's fixture tree with its own companion/; `privyhub_service`'s handler
on a ThreadingHTTPServer at 127.0.0.1:0; network beyond loopback blocked; a made-up PS1 title launched through
`POST /plugins/games/launch`). The fake RetroArch is B99's, extended: `LOAD_STATE_SLOT n` reads
`<core folder>/<stem>.state<n>` (a made-up file holding the values to set), writes RetroArch's own load line into the
game log and answers; on demand it refuses (RetroArch's failure line, memory untouched); after a load its memory
follows a script in time; every command is logged. The stream is a stub whose `active` each case sets. Made-up slot
files 1-3 and the slot-0 copy are hashed before and after. Flag absent / 0: both routes on the baseline's companion
(`git archive 33d8d2cf`) and on this one, byte for byte. No emulator; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b101_h7_contest -v
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
sys.path.insert(0, str(ROOT / "tests" / "b99_h7_live_read"))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402  (a module: its tests are not collected twice)

ON = {**b85.FLAGS, "PRIVYHUB_H7": "1"}
BASELINE = "33d8d2cf"                   # queue AL's baseline (H7-L1 committed): the companion before B101

CHILD = r'''
import hashlib, json, os, re, socket, subprocess, sys, threading, time, types, urllib.request, urllib.error
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
        self.script = []; self.t_load = None
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
            if self.t_load is not None:
                now = time.monotonic() - self.t_load
                while self.script and self.script[0][0] <= now:
                    _, a, b = self.script.pop(0); self.put(a, b)
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
                    pass                                             # answers, but no load line at all
                elif self.refuse or not p.is_file():
                    self.logline(f'[ERROR] [State] Failed to load state from "{p}".')
                else:
                    vals = json.loads(p.read_text())
                    self.put(vals["P1"], vals["P2"])
                    self.logline(f'[INFO] [State] Loading state "{p}", {p.stat().st_size} bytes.')
                    self.t_load = time.monotonic(); self.script = list(fake.get("script", []))
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
def start(n=5):
    return call("POST", f"/plugins/games/h7-contest?seconds={n}")
def wait_done(bound=60):
    end = time.monotonic() + bound
    while time.monotonic() < end:
        st = call("GET", "/plugins/games/h7-contest")["body"].get("contest") or {}
        if st.get("state") in ("done", "error", "ended"):
            return st
        time.sleep(0.2)
    return {"timeout": True}
out = {"steps": {}}
S = out["steps"]
S["get_before"] = call("GET", "/plugins/games/h7-contest")
S["post_before_launch"] = start(10)
S["launch"] = call("POST", f"/plugins/games/launch?id={args['id']}")["code"]
time.sleep(0.3)
if args["mode"] == "today":
    S["get_after"] = call("GET", "/plugins/games/h7-contest")
    S["post_after"] = start(10)
    S["post_bad"] = call("POST", "/plugins/games/h7-contest?seconds=999")
else:
    ra = fake["ra"]; ra.paused = False
    stem = m._active_state_stem(); f = folder(); f.mkdir(parents=True, exist_ok=True)
    slots = [f / (stem + x) for x in (".state", ".state1", ".state2", ".state3")]
    for i, p in enumerate(slots):
        p.write_bytes(os.urandom(64) + bytes([i]))
    digest = lambda: [hashlib.sha256(p.read_bytes()).hexdigest() for p in slots]
    before = digest()
    Path(rules).mkdir(parents=True, exist_ok=True)
    S["no_rule"] = start()
    Path(rules, args["id"] + ".json").write_text(json.dumps({"players": [
        {"name": "P1", "address": hex(P1), "bytes": 2}, {"name": "P2", "address": hex(P2), "bytes": 2}],
        "winner": "max", "memory": "ram", "none_when": "equal"}))
    S["no_state"] = start()
    Path(rules, args["id"] + ".state").write_text(json.dumps({"P1": 0, "P2": 0}))
    stream.active = False; S["no_stream"] = start(); stream.active = True
    S["bad_seconds"] = start(3)
    ra.put(50, 60)
    # 1: end to end — 0 / 0 for 1 s, the bars fill, P1 ahead at the clock
    fake["script"] = [(1.0, 140, 140), (3.0, 140, 100), (5.0, 120, 100)]
    n0 = len(ra.log)
    S["c1_start"] = start(5); time.sleep(0.2); S["c1_second"] = start(5)
    S["c1_running"] = call("GET", "/plugins/games/h7-contest")["body"]
    S["c1"] = wait_done(); S["c1_commands"] = ra.log[n0:]
    # 2: a new round inside the time — every value back to full — then P2 ahead
    fake["script"] = [(0.5, 140, 140), (2.0, 140, 90), (3.0, 140, 140), (4.5, 100, 140)]
    S["c2_start"] = start(5); S["c2"] = wait_done()
    # 3: equal at the clock
    fake["script"] = [(0.5, 140, 140), (2.0, 120, 130), (3.5, 110, 110)]
    S["c3_start"] = start(5); S["c3"] = wait_done()
    # 4: a load the fake refuses
    ra.put(77, 33); ra.refuse = True
    S["c4"] = start(5); S["c4_mem"] = [int.from_bytes(ra.mem[P1:P1 + 2], "little"), int.from_bytes(ra.mem[P2:P2 + 2], "little")]
    S["c4_get"] = call("GET", "/plugins/games/h7-contest")["body"]
    ra.refuse = False
    ra.silent = True; t = time.monotonic(); S["c4b"] = start(5); S["c4b_elapsed"] = round(time.monotonic() - t, 2)
    S["c4b_mem"] = [int.from_bytes(ra.mem[P1:P1 + 2], "little"), int.from_bytes(ra.mem[P2:P2 + 2], "little")]
    ra.silent = False
    S["c4_scratch_left"] = sorted(p.name for p in f.iterdir() if p.name.endswith(".state8"))
    # 5: never armed (the values never leave the state's)
    fake["script"] = []
    t = time.monotonic(); S["c5_start"] = start(5); S["c5"] = wait_done(); S["c5_elapsed"] = round(time.monotonic() - t, 1)
    # 6: N64 and PS2 sessions
    old_sys = m.active_game.get("system"); m.active_game["system"] = "n64"; S["n64"] = start(); m.active_game["system"] = old_sys
    m._launch_kind = "pcsx2"; S["ps2"] = start(); m._launch_kind = None
    # 7: the user's END during a contest
    fake["script"] = [(0.5, 140, 140), (2.0, 120, 140)]
    S["c7_start"] = start(30); time.sleep(2.0)
    S["c7_stop"] = call("POST", "/plugins/games/stop")["code"]
    S["c7"] = wait_done(); S["c7_lock_free"] = m.lock.acquire(timeout=1.0)
    if S["c7_lock_free"]: m.lock.release()
    S["scratch_left"] = sorted(p.name for p in f.iterdir() if p.name.endswith(".state8"))
    S["slots_equal"] = digest() == before
    log = root / "logs/games/h7_contests.jsonl"
    out["rows"] = [json.loads(l) for l in log.read_text().splitlines()] if log.is_file() else None
httpd.shutdown()
print(json.dumps(out))
'''


def run(root: Path, env: dict, gid: str, mode: str) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules")})
    r = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, str(root),
                        json.dumps({"id": gid, "mode": mode, "p1": b99.P1, "p2": b99.P2})],
                       cwd=root, env=child_env, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


class TimedContest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b99.tree()
        cls.gid = ids[b85.PS1_TITLE]
        cls.out = run(root, ON, cls.gid, "on")
        cls.s = cls.out["steps"]

    def err(self, r):
        return r["code"], r["body"].get("error")

    def test_before_any_contest_and_no_game(self):
        self.assertEqual(self.s["get_before"]["body"], {"ok": True, "contest": None})
        self.assertEqual(self.err(self.s["post_before_launch"]), (400, "no game is running"))

    def test_the_plain_refusals(self):
        self.assertEqual(self.err(self.s["no_rule"]), (400, "no rule for this game"))
        self.assertEqual(self.err(self.s["no_state"]), (400, "no state for this game's contest"))
        self.assertEqual(self.err(self.s["no_stream"]), (400, "the stream is not up"))
        self.assertEqual(self.err(self.s["bad_seconds"]), (400, "seconds must be a whole number from 5 to 300"))
        self.assertEqual(self.err(self.s["c1_second"]), (400, "a contest is already running"))

    def test_a_contest_end_to_end(self):
        st = self.s["c1_start"]["body"]
        self.assertEqual((st["contest"], st["seconds"], st["state_values"]), ("started", 5, {"P1": 0, "P2": 0}))
        self.assertIn(self.s["c1_running"]["contest"]["state"], ("arming", "running"))
        c = self.s["c1"]
        self.assertEqual(c["state"], "done", c)
        self.assertEqual((c["winner"], c["reason"], c["values"]), ("P1", None, {"P1": 120, "P2": 100}))
        self.assertEqual((c["seconds"], c["ended"], c["resets_seen"]), (5, "running", 0))
        self.assertTrue(0.75 <= c["armed_after_s"] <= 1.75, c["armed_after_s"])     # the bars filled at 1.0 s
        self.assertEqual(c["samples"][0][1:], [140, 140])                         # armed at the filled values
        self.assertGreaterEqual(len(c["samples"]), 5)
        self.assertTrue(all(c["samples"][i][0] < c["samples"][i + 1][0] for i in range(len(c["samples"]) - 1)))
        self.assertTrue(4.8 <= c["samples"][-1][0] <= 5.6, c["samples"][-1])

    def test_only_status_reads_and_one_load(self):
        cmds = self.s["c1_commands"]
        self.assertEqual(set(cmds), {"GET_STATUS", "READ_CORE_RAM", "LOAD_STATE_SLOT"})
        self.assertEqual(cmds.count("LOAD_STATE_SLOT"), 1)

    def test_a_new_round_is_seen_not_used(self):
        c = self.s["c2"]
        self.assertEqual((c["state"], c["resets_seen"], c["winner"]), ("done", 1, "P2"))

    def test_equal_at_the_clock(self):
        c = self.s["c3"]
        self.assertEqual((c["winner"], c["reason"], c["values"]), (None, "no winner yet", {"P1": 110, "P2": 110}))

    def test_a_refused_load_leaves_the_game_as_it_was(self):
        self.assertEqual(self.err(self.s["c4"]), (503, "the contest's state did not load; the game is as it was"))
        self.assertEqual(self.s["c4_mem"], [77, 33])
        self.assertEqual(self.s["c4_scratch_left"], [])
        self.assertEqual(self.s["c4_get"]["contest"]["state"], "done")                # the last outcome kept

    def test_a_load_without_retroarchs_line_is_not_a_load(self):
        self.assertEqual(self.err(self.s["c4b"]), (503, "the contest's state did not load; the game is as it was"))
        self.assertEqual(self.s["c4b_mem"], [77, 33])
        self.assertLess(self.s["c4b_elapsed"], 1.5 + 1.0)                            # the line's bound, not longer

    def test_never_armed(self):
        c = self.s["c5"]
        self.assertEqual(c["state"], "error")
        self.assertEqual(c["error"], "the fight did not start within 20 s; the game left running")
        self.assertLess(self.s["c5_elapsed"], 20 + 3)

    def test_n64_and_ps2(self):
        self.assertEqual(self.err(self.s["n64"]),
                         (400, "not supported yet — a state cannot be loaded into a running N64 game"))
        self.assertEqual(self.err(self.s["ps2"]), (400, "not supported yet"))

    def test_end_during_a_contest(self):
        c = self.s["c7"]
        self.assertEqual(self.s["c7_stop"], 200)
        self.assertEqual((c["state"], c["why"]), ("ended", "the game stopped"))
        self.assertNotIn("winner", c)
        self.assertTrue(self.s["c7_lock_free"])
        self.assertEqual(self.s["scratch_left"], [])

    def test_the_users_slots_untouched(self):
        self.assertTrue(self.s["slots_equal"])

    def test_one_row_per_step(self):
        steps = [r["step"] for r in self.out["rows"]]
        for want in ("refused", "loaded", "armed", "done", "error", "not_armed", "ended"):
            self.assertIn(want, steps)
        loaded = next(r for r in self.out["rows"] if r["step"] == "loaded")
        self.assertEqual(loaded["game"], self.gid)
        self.assertIsNotNone(loaded["load_line_ms"])


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
        for env in (b85.FLAGS, {**b85.FLAGS, "PRIVYHUB_H7": "0"}):
            root2, _ = b99.tree()
            mine = run(root2, env, gid, "today")
            for k in ("get_before", "post_before_launch", "get_after", "post_after", "post_bad"):
                self.assertEqual((mine["steps"][k]["code"], mine["steps"][k]["raw"]),
                                 (base["steps"][k]["code"], base["steps"][k]["raw"]), k)
            self.assertEqual(mine["steps"]["launch"], base["steps"]["launch"])
        self.assertEqual(base["steps"]["get_after"]["body"]["error"], "Unknown Games plugin action: h7-contest")
        self.assertEqual(base["steps"]["post_after"]["body"]["error"], "Unknown Games plugin POST action: h7-contest")


if __name__ == "__main__":
    unittest.main()
