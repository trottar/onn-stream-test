#!/usr/bin/env python3
"""B90 (host): the cheat launch without walking the list, and no game left running when the onn has hung up.

Every case goes through **the companion's real HTTP server on loopback** (tests/client_contract's form): a child
`python3 -I` on B85's / B87's fixture tree (its own companion/), the companion's own `privyhub_service` handler on a
`ThreadingHTTPServer` at 127.0.0.1:0, and the onn's call `POST /plugins/games/launch?id=…&cheat_source=0&cheat_indexes=…`
sent by an HTTP client in the child. RetroArch is B87's fake on loopback (a thread on the UDP command port the hub
configured, writing RetroArch's own log lines into the hub's game log), **extended to apply at load**: it reads the
session config, loads the cheat file only under RetroArch's own name and folder, and with `apply_cheats_after_load` on
marks the file's enabled cheats on and logs `Applying cheat changes.`; pulses before its core "runs" are lost.
No emulator, no network beyond loopback; made-up titles, names and codes; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b90_cheat_staged -v
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
sys.path.insert(0, str(ROOT / "tests" / "b87_cheat_ready"))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b87 as b87  # noqa: E402

FLAGS = {**b85.FLAGS, "PRIVYHUB_SNES_CORE": "snes9x"}         # the hub's own SNES core
OFF = {**FLAGS, "PRIVYHUB_CHEAT_STAGED": "0"}
SNES_TITLE = ("snes", "Golf Hotel (USA)")


def rows(n: int) -> list[tuple[str, str]]:
    """B85's twelve shapes (a "must be on" code, parts, a heading, a conditional…) then made-up plain cheats."""
    return list(b85.N64_ROWS) + [(f"Made Up Cheat {i}", f"8030{(2 * i) & 0xFFFF:04X} 0001") for i in range(12, n)]


CHILD = r'''
import json, os, re, socket, subprocess, sys, threading, time, types, urllib.request, urllib.error
from pathlib import Path
root = Path(sys.argv[1]).resolve()
args = json.loads(sys.argv[2])
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
events = {"toggles": 0, "pulses": 0, "lost": 0, "loaded": False, "applied_at_load": 0, "folder": None, "save_files": 0}
class FakeRetroArch:
    def __init__(self, cmd, **kw):
        self.pid = 999999999; self.returncode = None; self.stdin = None
        self.out = kw.get("stdout"); self.content = Path(cmd[-1]); self.t0 = time.monotonic()
        self.paused = False; self.cursor = 0; self.on = {}; self.stop = False
        text = (root / "data/games/retroarch/config/privyhub-session.cfg").read_text()
        events["config_apply_lines"] = len(re.findall(r'(?m)^apply_cheats_after_load = "true"$', text))
        self.apply = events["config_apply_lines"] == 1 and not args.get("ignore_apply")
        db = Path(re.search(r'cheat_database_path = "([^"]+)"', text).group(1))
        stem = self.content.stem
        ra_name = Path(stem).stem if "." in stem else stem          # RetroArch's own rule (B87, measured)
        self.names, self.enabled, self.file = {}, {}, None
        for folder in ("Mupen64Plus-Next", "Beetle PSX HW", "Snes9x"):   # the cores' library names (B90, measured)
            if (db / folder / f"{ra_name}.cht").is_file():
                self.file = db / folder / f"{ra_name}.cht"; events["folder"] = folder
        if self.file is not None:
            body = self.file.read_text()
            events["staged_file"] = body
            for line in body.splitlines():
                mm = re.match(r'cheat(\d+)_desc = "(.*)"', line)
                if mm: self.names[int(mm.group(1))] = mm.group(2)
                mm = re.match(r'cheat(\d+)_enable = (\w+)', line)
                if mm: self.enabled[int(mm.group(1))] = mm.group(2) == "true"
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", int(m._network_cmd_port)))
        self.sock.settimeout(0.05)
        threading.Thread(target=self.serve, daemon=True).start()
    def log(self, line):
        self.out.write(line + "\n"); self.out.flush()
    def serve(self):
        load_at = args.get("load_at")
        while not self.stop:
            now = time.monotonic() - self.t0
            if load_at is not None and not events["loaded"] and now >= load_at and self.names:
                events["loaded"] = True
                self.log('[INFO] [Cheats] Load game-specific cheatfile: "<fixture>".')
                if self.apply:
                    self.on = {i: True for i, e in self.enabled.items() if e}
                    events["applied_at_load"] = len(self.on)
                    self.log("[INFO] [Cheats] Applying cheat changes.")
            try:
                data, addr = self.sock.recvfrom(4096)
            except OSError:
                continue
            c = data.decode().strip()
            running = now >= args.get("run_at", 0.0)
            if c == "GET_STATUS":
                self.sock.sendto(f"GET_STATUS {'PAUSED' if self.paused else 'PLAYING'} n64,fixture,crc32=0".encode(), addr)
            elif c == "PAUSE_TOGGLE":
                self.paused = not self.paused
            elif c == "SAVE_FILES":
                events["save_files"] += 1
                self.sock.sendto(b"SAVE_FILES OK", addr)
            elif c == "CHEAT_INDEX_PLUS":
                events["pulses"] += 1
                if not (running and events["loaded"]):
                    events["lost"] += 1
                    continue
                if not args.get("stuck_cursor"):
                    self.cursor = (self.cursor + 1) % len(self.names)
                st = "on" if self.on.get(self.cursor) else "off"
                self.log(f"[INFO] [Cheats] Cheat #{self.cursor}: {self.names[self.cursor]}: {st}")
            elif c == "CHEAT_TOGGLE":
                events["toggles"] += 1
                self.on[self.cursor] = not self.on.get(self.cursor)
                self.log("[INFO] [Cheats] Applying cheat changes.")
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
out = {}
def call(method, path, timeout=120):
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")
path = f"/plugins/games/launch?id={args['id']}&cheat_source=0&cheat_indexes={args['picks']}"
t = time.monotonic()
if args.get("hang_up_after") is None:
    status, body = call("POST", path)
    out["status"], out["error"] = status, body.get("error")
    s = body.get("cheat_session") or {}
else:                                   # the onn gives up: its socket closed before the launch answers
    c = socket.create_connection(("127.0.0.1", port))
    c.sendall(f"POST {path} HTTP/1.1\r\nHost: hub\r\nContent-Length: 0\r\n\r\n".encode())
    time.sleep(args["hang_up_after"])
    c.close()
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline and m.process is None:
        time.sleep(0.05)
    with m.lock:                         # the launch's own lock: held until the launch returns
        pass
    log = root / "logs/games/native_stream_recovery.log"
    settle = time.monotonic() + args.get("settle", 8.0)
    while time.monotonic() < settle and not (log.is_file() and '"launch_orphaned"' in log.read_text()):
        time.sleep(0.05)
    time.sleep(0.3)
    s = m._active_cheat_session or {}
out["elapsed"] = round(time.monotonic() - t, 2)
out["session"] = {k: s.get(k) for k in ("enabled_cheat_indexes", "activation_verified", "activation_mode",
                                        "activation_pulses", "staged", "activation_verification_lines")}
out["events"] = events
st, body = call("GET", "/plugins/games/status")
out["status_read"] = {"code": st, "active": body.get("active")}
log = root / "logs/games/native_stream_recovery.log"
out["orphan_rows"] = [json.loads(l) for l in log.read_text().splitlines()
                      if '"launch_orphaned"' in l] if log.is_file() else []
httpd.shutdown()
print(json.dumps(out))
'''


def tree(n_rows: int = 2092):
    """B87's tree (B85's titles, a dotted N64 title), the N64 title's list made `n_rows` long, a SNES list, the
    snes9x core file the hub runs."""
    root, ids, _dotted = b87.tree()
    rel_of = {g[2]: g[3] for g in b85.b83.b82.scan(root, FLAGS)["games"]}
    ids[SNES_TITLE] = next(g[2] for g in b85.b83.b82.scan(root, FLAGS)["games"] if (g[0], g[1]) == SNES_TITLE)
    b85.manifest(root, [("n64", ids[b85.N64_TITLE], rel_of[ids[b85.N64_TITLE]], b85.cht(rows(n_rows))),
                        ("ps1", ids[b85.PS1_TITLE], rel_of[ids[b85.PS1_TITLE]], b85.cht(b85.PS1_ROWS)),
                        ("snes", ids[SNES_TITLE], rel_of[ids[SNES_TITLE]],
                         b85.cht([("Made Up Lives", "7E0100:09"), ("Made Up Time", "7E0102:63")]))])
    (root / b85.b83.CORES / "snes9x_libretro.so").write_bytes(b"\x7fELF")
    return root, ids


def launch(root: Path, env: dict, gid: str, picks: str, **fake) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg)})
    r = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, str(root), json.dumps({"id": gid, "picks": picks, **fake})],
                       cwd=root, env=child_env, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def todays_walk(desired: list[int], length: int) -> int:
    """Today's answered pulses on the fake: the ready probe's one, then per pick the forward walk to it and a full lap
    back to it."""
    cursor, answered = 1, 1
    for p in desired:
        answered += ((p - cursor - 1) % length) + 1 + length
        cursor = p
    return answered


class Staged(unittest.TestCase):
    def check_staged(self, picks: str, n_rows: int = 2092):
        root, ids = tree(n_rows)
        out = launch(root, FLAGS, ids[b85.N64_TITLE], picks, load_at=0.05, run_at=0.6)
        self.assertEqual(out["status"], 200, out)
        s = out["session"]
        self.assertTrue(s["activation_verified"])
        self.assertEqual(s["activation_mode"], "staged")
        desired = s["enabled_cheat_indexes"]
        k = len(desired)
        self.assertEqual(s["staged"]["source_indexes"], desired)
        ev = out["events"]
        self.assertEqual(ev["toggles"], 0)                                   # no toggle, no walk
        self.assertEqual(ev["applied_at_load"], k)
        self.assertEqual(ev["config_apply_lines"], 1)
        self.assertLessEqual(ev["pulses"] - ev["lost"], 1 + 2 * k + 4)        # the count, not time alone
        self.assertLessEqual(s["activation_pulses"], 2 * k + 4)
        self.assertTrue(out["status_read"]["active"])
        self.assertEqual(out["orphan_rows"], [])
        return out, desired

    def test_a_2092_entry_list_one_pick(self):
        out, desired = self.check_staged("2000")
        self.assertEqual(desired, [2, 2000])                                   # the pick + B85's "must be on" code
        self.assertLess(out["elapsed"], 15.0)

    def test_a_2092_entry_list_three_picks_with_parts_and_the_last_entry(self):
        out, desired = self.check_staged("0,5,2091")
        self.assertEqual(desired, [0, 2, 5, 6, 2091])
        self.assertLess(out["elapsed"], 15.0)

    def test_the_staged_files_contents(self):
        out, desired = self.check_staged("5,1500", n_rows=1600)
        body = out["events"]["staged_file"]
        src = rows(1600)
        want = [f"cheats = {len(desired)}", ""]
        for j, i in enumerate(desired):
            want += [f'cheat{j}_desc = "{src[i][0]}"', f'cheat{j}_code = "{src[i][1]}"', f"cheat{j}_enable = true", ""]
        self.assertEqual(body, "\n".join(want) + "\n")
        self.assertEqual(out["session"]["staged"]["descriptions"], [src[i][0] for i in desired])


    def test_a_retroarch_that_does_not_apply_at_load_fails_closed(self):
        root, ids = tree(100)
        out = launch(root, FLAGS, ids[b85.N64_TITLE], "50", load_at=0.05, run_at=0.0, ignore_apply=True)
        self.assertEqual(out["status"], 503, out)
        self.assertIn("did not apply the staged cheats at load", out["error"])
        self.assertFalse(out["status_read"]["active"])                        # stopped, never left running
        self.assertEqual(out["events"]["toggles"], 0)


    def test_a_cheat_never_reported_stops_within_the_pulse_bound(self):
        root, ids = tree(100)
        out = launch(root, FLAGS, ids[b85.N64_TITLE], "50", load_at=0.05, run_at=0.0, stuck_cursor=True)
        self.assertEqual(out["status"], 503, out)
        self.assertIn("did not report every staged cheat", out["error"])
        k = 2                                                                  # the pick + its "must be on" code
        self.assertLessEqual(out["events"]["pulses"] - out["events"]["lost"], 1 + 2 * k + 4)   # bounded, not timed out
        self.assertFalse(out["status_read"]["active"])


class TodayAndTheKnob(unittest.TestCase):
    def test_the_knob_zero_is_todays_walk_and_config(self):
        root, ids = tree(40)
        out = launch(root, OFF, ids[b85.N64_TITLE], "30", load_at=0.05, run_at=0.0)
        self.assertEqual(out["status"], 200, out)
        s = out["session"]
        self.assertTrue(s["activation_verified"])
        self.assertIsNone(s["activation_mode"])
        self.assertIsNone(s["staged"])
        ev = out["events"]
        self.assertEqual(ev["config_apply_lines"], 0)
        self.assertEqual(ev["applied_at_load"], 0)
        self.assertEqual(ev["toggles"], len(s["enabled_cheat_indexes"]))
        self.assertEqual(ev["pulses"] - ev["lost"], todays_walk(s["enabled_cheat_indexes"], 40))
        self.assertIn("cheat0_enable = false", ev["staged_file"])            # today's whole file, all off
        self.assertEqual(ev["staged_file"].count("_desc ="), 40)

    def test_snes_staged_under_the_running_cores_name(self):
        root, ids = tree(20)
        on = launch(root, FLAGS, ids[SNES_TITLE], "1", load_at=0.05, run_at=0.0)
        self.assertEqual(on["status"], 200, on)
        self.assertEqual(on["events"]["folder"], "Snes9x")
        self.assertTrue(on["session"]["activation_verified"])
        off = launch(tree(20)[0], OFF, ids[SNES_TITLE], "1", load_at=0.05, run_at=0.0)
        self.assertIsNone(off["events"]["folder"])                          # today: under bsnes, never read…
        self.assertIn("cheats not ready", off["error"])                       # …B87's plain error, the game stopped
        self.assertFalse(off["status_read"]["active"])


class HangUp(unittest.TestCase):
    def test_a_client_that_hangs_up_leaves_no_game_running(self):
        root, ids = tree(40)
        out = launch(root, FLAGS, ids[b85.N64_TITLE], "30", load_at=0.05, run_at=1.5, hang_up_after=0.3)
        self.assertFalse(out["status_read"]["active"], out)                 # the onn's next status read: no game
        self.assertEqual(len(out["orphan_rows"]), 1, out)
        row = out["orphan_rows"][0]
        self.assertEqual((row["reason"], row["stopped"]), ("client_closed", True))
        self.assertGreaterEqual(out["events"]["save_files"], 1)              # the onn's own Stop path (the save flush)

    def test_the_knob_zero_leaves_it_running_as_today(self):
        root, ids = tree(40)
        out = launch(root, OFF, ids[b85.N64_TITLE], "30", load_at=0.05, run_at=1.5, hang_up_after=0.3)
        self.assertTrue(out["status_read"]["active"], out)
        self.assertEqual(out["orphan_rows"], [])


class ContractListed(unittest.TestCase):
    def test_the_onns_launch_call_is_in_the_contract(self):
        calls = json.loads((ROOT / "tests/client_contract/calls.json").read_text())["calls"]
        launch_call = [c for c in calls if c["path"] == "/plugins/games/launch"]
        self.assertEqual([c["method"] for c in launch_call], ["POST"])
        self.assertTrue({"id", "cheat_source", "cheat_indexes"} <= set(launch_call[0]["params"]))


if __name__ == "__main__":
    unittest.main()
