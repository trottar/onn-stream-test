#!/usr/bin/env python3
"""B99 (host): H7's live read — `GET /plugins/games/h7-read` behind PRIVYHUB_H7=1, through the companion's real HTTP
server on loopback.

B90's harness: a child `python3 -I` on B82 / B83's fixture tree with its own companion/ (`from plugins import
PLUGINS`; `privyhub_service`'s handler on a ThreadingHTTPServer at 127.0.0.1:0; network beyond loopback blocked).
RetroArch is a fake on the UDP command port the hub configured — B90's, **extended with core memory** (2 MiB the test
changes; `-1` past its end; an optional delay before answering) and **a command log**. A PS1 title (made up) launched
through `POST /plugins/games/launch`. Flag absent / 0: the same calls on the baseline's companion (`git archive 6cb4663b`, HEAD when B99 began) and on
this one, compared byte for byte; an audit hook records any file opened under the rules folder. No emulator, no
network beyond loopback; made-up titles; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b99_h7_live_read -v
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402

ON = {**b85.FLAGS, "PRIVYHUB_H7": "1"}
P1, P2 = 0x0A9610, 0x0AAEA0             # made-up addresses (2 bytes each)
BASELINE = "6cb4663b"                   # queue AK's baseline (H7-P3 committed): the companion before B99

CHILD = r'''
import json, os, re, socket, subprocess, sys, threading, time, types, urllib.request, urllib.error
from pathlib import Path
root = Path(sys.argv[1]).resolve()
args = json.loads(sys.argv[2])
rules = os.environ.get("PRIVYHUB_H7_RULES", "")
opened = []
def _audit(event, a):
    if event == "open" and rules and a and str(a[0]).startswith(rules):
        opened.append(str(a[0]))
sys.addaudithook(_audit)
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
g._native_stream = Inert()
fake = {}
class FakeRetroArch:
    """B90's fake (GET_STATUS, PAUSE_TOGGLE, SAVE_FILES) + core memory, SAVE_STATE_SLOT 0, a delay, a command log."""
    def __init__(self, cmd, **kw):
        self.pid = 999999999; self.returncode = None; self.stdin = None; self.stop = False
        self.out = kw.get("stdout"); self.paused = False
        self.mem = bytearray(0x200000); self.delay = 0.0; self.log = []; self.wrong = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", int(m._network_cmd_port)))
        self.sock.settimeout(0.05)
        fake["ra"] = self
        threading.Thread(target=self.serve, daemon=True).start()
    def serve(self):
        while not self.stop:
            try:
                data, addr = self.sock.recvfrom(4096)
            except OSError:
                continue
            c = data.decode().strip()
            self.log.append(c.split()[0] if c else "")
            if self.delay:
                time.sleep(self.delay)
            w = c.split()
            if c == "GET_STATUS":
                self.sock.sendto(f"GET_STATUS {'PAUSED' if self.paused else 'PLAYING'} psx,fixture,crc32=0".encode(), addr)
            elif c == "PAUSE_TOGGLE":
                self.paused = not self.paused
            elif c == "SAVE_FILES":
                self.sock.sendto(b"SAVE_FILES OK", addr)
            elif c == "SAVE_STATE_SLOT 0":
                d = m._state_root(); d.mkdir(parents=True, exist_ok=True)
                (d / (m._active_state_stem() + ".state")).write_bytes(b"#RZIPv\x01#" + bytes(self.mem[:64]) + os.urandom(16))
                self.sock.sendto(b"SAVE_STATE_SLOT 0 OK", addr)
            elif w and w[0] in ("READ_CORE_RAM", "READ_CORE_MEMORY") and len(w) == 3:
                a, n = int(w[1], 16), int(w[2])
                body = "-1" if a + n > len(self.mem) else " ".join(f"{b:02x}" for b in self.mem[a:a + n])
                said = f"{a + 1:x}" if self.wrong else w[1]               # an answer to another address
                self.sock.sendto(f"{w[0]} {said} {body}".encode(), addr)
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
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
def read():
    t = time.monotonic(); code, body = call("GET", "/plugins/games/h7-read")
    return {"code": code, "body": json.loads(body or "{}"), "raw": body, "elapsed": round(time.monotonic() - t, 3)}
def setmem(p1, p2):
    ra = fake["ra"]
    ra.mem[args["p1"]:args["p1"] + 2] = int(p1).to_bytes(2, "little")
    ra.mem[args["p2"]:args["p2"] + 2] = int(p2).to_bytes(2, "little")
def rule(path, p2=None):
    Path(rules).mkdir(parents=True, exist_ok=True)
    Path(rules, args["id"] + ".json").write_text(json.dumps({"players": [
        {"name": "P1", "address": hex(args["p1"]), "bytes": 2, "endian": "little"},
        {"name": "P2", "address": hex(p2 if p2 is not None else args["p2"]), "bytes": 2, "endian": "little"}],
        "winner": "max", "memory": "ram", "none_when": "equal"}))
out = {"steps": {}}
S = out["steps"]
S["before_launch"] = read()
S["launch"] = call("POST", f"/plugins/games/launch?id={args['id']}")[0]
time.sleep(0.3)
if args["mode"] == "today":
    S["after_launch"] = read()
    time.sleep(0.3)
    S["again"] = read()
    code, body = call("GET", "/plugins/games/systems")
    S["systems"] = [code, body.replace(str(root), "<the tree>")]                 # each run's own temp tree
else:
    S["launch_commands"] = list(fake["ra"].log); S["paused_after_launch"] = fake["ra"].paused
    S["no_rule"] = read(); time.sleep(0.3)
    rule(rules)
    setmem(140, 70); S["read_after_launch"] = read(); time.sleep(0.3)   # the hub launches paused (the stream resumes)
    fake["ra"].paused = False                                             # as the stream's start would
    S["p1_ahead"] = read(); time.sleep(0.3)
    setmem(100, 130); S["p2_ahead"] = read(); time.sleep(0.3)
    setmem(90, 90); S["equal"] = read(); time.sleep(0.3)
    ra = fake["ra"]; ra.paused = True; setmem(120, 60); S["paused"] = read(); ra.paused = False; time.sleep(0.3)
    n0 = len(ra.log); S["floor_first"] = read(); S["floor_second"] = read(); S["floor_commands"] = ra.log[n0:]
    time.sleep(0.3)
    n0 = len(ra.log)
    for _ in range(5):
        S.setdefault("five_reads", []).append(read()["code"]); time.sleep(0.3)
    S["read_commands"] = sorted(set(ra.log[n0:]))
    S["read_command_count"] = len(ra.log) - n0
    rule(rules, p2=0x1FFFFF); S["beyond_memory"] = read(); time.sleep(0.3)
    rule(rules); ra.wrong = True; S["wrong_answer"] = read(); ra.wrong = False; time.sleep(0.3)
    rule(rules)
    ra.delay = 1.0; S["slow"] = read(); time.sleep(1.5); ra.delay = 0.0; time.sleep(0.3)
    setmem(77, 33)
    race = {"reads": [], "status": [], "save": None}
    stop = time.monotonic() + 3.0
    def reads():
        while time.monotonic() < stop:
            r = read(); race["reads"].append({"code": r["code"], "values": r["body"].get("values"), "error": r["body"].get("error")})
            time.sleep(0.27)
    def polls():
        while time.monotonic() < stop:
            race["status"].append(call("GET", "/plugins/games/status")[0]); time.sleep(0.05)
    def save():
        time.sleep(0.5); code, body = call("POST", "/plugins/games/save-state?slot=1")
        race["save"] = {"code": code, "error": json.loads(body or "{}").get("error")}
    th = [threading.Thread(target=f) for f in (reads, polls, save)]
    [t.start() for t in th]; [t.join() for t in th]
    S["race"] = race
    m._launch_kind = "pcsx2"; time.sleep(0.3); S["ps2_kind"] = read(); m._launch_kind = None
log = root / "logs/games/h7_reads.jsonl"
out["rows"] = [json.loads(l) for l in log.read_text().splitlines()] if log.is_file() else None
out["opened_under_rules"] = sorted(set(opened))
httpd.shutdown()
print(json.dumps(out))
'''


def tree(code_root: Path | None = None):
    """B85's tree (B83's: made-up titles, the emulators' fake files); with code_root, its companion/ replaced."""
    root, ids = b85.tree()
    if code_root is not None:
        shutil.rmtree(root / "companion")
        shutil.copytree(code_root / "companion", root / "companion", ignore=shutil.ignore_patterns("__pycache__"))
    return root, ids


def head_code() -> Path | None:
    """The baseline's companion/ (git archive of BASELINE, HEAD when B99 began), for the flag-absent comparison."""
    try:
        repo = os.environ.get("H7_GIT_REPO") or str(ROOT)       # a test work copy is not a git repo: its runner says where
        data = subprocess.run(["git", "-C", repo, "archive", BASELINE, "companion"], capture_output=True,
                              timeout=120, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    d = Path(tempfile.mkdtemp(prefix="b99_head_"))
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        tf.extractall(d, filter="data")
    return d


def run(root: Path, env: dict, gid: str, mode: str) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules")})
    r = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, str(root),
                        json.dumps({"id": gid, "mode": mode, "p1": P1, "p2": P2})],
                       cwd=root, env=child_env, capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


class LiveRead(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = tree()
        cls.gid = ids[b85.PS1_TITLE]
        cls.out = run(root, ON, cls.gid, "on")
        cls.s = cls.out["steps"]

    def test_no_game_then_the_launch(self):
        self.assertEqual((self.s["before_launch"]["code"], self.s["before_launch"]["body"]),
                         (200, {"ok": True, "running": False}))
        self.assertEqual(self.s["launch"], 200)

    def test_the_launch_leaves_the_game_paused_and_the_read_says_so(self):
        self.assertEqual(self.s["launch_commands"], ["GET_STATUS", "GET_STATUS", "PAUSE_TOGGLE", "GET_STATUS"])
        self.assertTrue(self.s["paused_after_launch"])
        r = self.s["read_after_launch"]["body"]
        self.assertEqual((r["paused"], r["values"], r["winner"]), (True, {"P1": 140, "P2": 70}, "P1"))

    def test_no_rule(self):
        r = self.s["no_rule"]
        self.assertEqual((r["code"], r["body"]["error"]), (400, "no rule for this game"))

    def test_the_values_the_winner_and_the_new_leader(self):
        a, b = self.s["p1_ahead"]["body"], self.s["p2_ahead"]["body"]
        self.assertEqual((a["game"], a["running"], a["paused"]), (self.gid, True, False))
        self.assertEqual((a["values"], a["winner"], a["reason"]), ({"P1": 140, "P2": 70}, "P1", None))
        self.assertEqual((b["values"], b["winner"]), ({"P1": 100, "P2": 130}, "P2"))
        self.assertLess(a["read_ms"], 600)

    def test_equal_is_no_winner_yet(self):
        e = self.s["equal"]["body"]
        self.assertEqual((e["values"], e["winner"], e["reason"]), ({"P1": 90, "P2": 90}, None, "no winner yet"))

    def test_paused(self):
        p = self.s["paused"]["body"]
        self.assertEqual((p["paused"], p["values"], p["winner"]), (True, {"P1": 120, "P2": 60}, "P1"))

    def test_the_reads_change_nothing(self):
        self.assertEqual(self.s["read_commands"], ["GET_STATUS", "READ_CORE_RAM"])     # no pause, save, load, write
        self.assertEqual(self.s["read_command_count"], 5 * 3)                         # status + 2 fields, each read

    def test_the_floor(self):
        first, second = self.s["floor_first"]["body"], self.s["floor_second"]["body"]
        self.assertNotIn("cached", first)
        self.assertTrue(second["cached"])
        self.assertLess(second["age_ms"], 250)
        self.assertEqual(second["values"], first["values"])
        self.assertEqual(self.s["floor_commands"], ["GET_STATUS", "READ_CORE_RAM", "READ_CORE_RAM"])   # one read sent

    def test_memory_the_core_does_not_have(self):
        r = self.s["beyond_memory"]
        self.assertEqual(r["code"], 502)
        self.assertEqual(r["body"]["error"], "the game's memory has no address 0x1fffff")

    def test_an_answer_to_another_address_is_never_read_as_memory(self):
        r = self.s["wrong_answer"]
        self.assertEqual((r["code"], r["body"]["error"]), (502, "an unexpected answer from RetroArch; not read"))

    def test_a_slow_core_is_a_plain_error_within_the_bound(self):
        r = self.s["slow"]
        self.assertEqual((r["code"], r["body"]["error"]), (502, "the game's memory did not answer in time; not read"))
        self.assertLess(r["elapsed"], 0.6 + 0.3)

    def test_reads_racing_a_save_and_status_polls(self):
        race = self.s["race"]
        self.assertTrue(race["reads"])
        for r in race["reads"]:
            if r["code"] == 200:
                self.assertEqual(r["values"], {"P1": 77, "P2": 33})                   # its own answer, never another's
            else:
                self.assertEqual(r["code"], 502)
                self.assertIn(r["error"], ("the game is busy (a save or a load); not read",
                                           "the game's memory did not answer in time; not read"))
        self.assertTrue(all(c == 200 for c in race["status"]))
        self.assertEqual(race["save"]["code"], 200, race["save"])

    def test_ps2_and_gamecube_are_not_supported_yet(self):
        r = self.s["ps2_kind"]
        self.assertEqual((r["code"], r["body"]["error"]), (400, "reading a PS2 game's memory is not supported yet"))

    def test_one_log_row_per_read_sent(self):
        rows = self.out["rows"]
        self.assertTrue(rows)
        ok = [r for r in rows if "error" not in r]
        self.assertEqual(ok[0]["game"], self.gid)
        self.assertEqual((ok[0]["values"], ok[0]["winner"]), ({"P1": 140, "P2": 70}, "P1"))
        self.assertTrue({"time_unix", "read_ms", "paused", "reason"} <= set(ok[0]))
        self.assertTrue(any(r.get("error", "").startswith("the game's memory has no address") for r in rows))
        cached_not_logged = len([1 for k in ("p1_ahead", "p2_ahead", "equal", "paused", "floor_first")])
        self.assertGreaterEqual(len(ok), cached_not_logged + 5)
        self.assertTrue(self.out["opened_under_rules"])                                # the flag on: the rule read


class FlagAbsentIsToday(unittest.TestCase):
    def test_absent_and_zero_answer_as_heads_code_byte_for_byte(self):
        code = head_code()
        if code is None:
            self.skipTest("git is absent")
        root, ids = tree(code)
        gid = ids[b85.PS1_TITLE]
        head = run(root, b85.FLAGS, gid, "today")
        for env in (b85.FLAGS, {**b85.FLAGS, "PRIVYHUB_H7": "0"}):
            root2, ids2 = tree()
            self.assertEqual(ids2[b85.PS1_TITLE], gid)
            mine = run(root2, env, gid, "today")
            for k in ("before_launch", "after_launch", "again"):
                self.assertEqual((mine["steps"][k]["code"], mine["steps"][k]["raw"]),
                                 (head["steps"][k]["code"], head["steps"][k]["raw"]), k)
            self.assertEqual(mine["steps"]["systems"], head["steps"]["systems"])
            self.assertEqual(mine["steps"]["launch"], head["steps"]["launch"])
            self.assertIsNone(mine["rows"])                                              # no h7_reads row
            self.assertEqual(mine["opened_under_rules"], [])                             # no rules folder looked at
        self.assertEqual(head["steps"]["after_launch"]["code"], 400)
        self.assertEqual(head["steps"]["after_launch"]["body"]["error"], "Unknown Games plugin action: h7-read")


if __name__ == "__main__":
    unittest.main()
