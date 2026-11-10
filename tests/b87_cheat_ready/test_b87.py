#!/usr/bin/env python3
"""B87 (host): an N64 (and PS1) cheat launch waits for RetroArch's own evidence before any cheat command.

The launch through the plugin as the companion constructs it (`from plugins import PLUGINS`; `handle_post("launch")`;
B85's / B83's harness: a child `python3 -I` on a fixture tree with its own companion/). RetroArch is a fake **on
loopback**: a thread bound to the UDP command port the hub configured, answering GET_STATUS / PAUSE_TOGGLE and writing
RetroArch's own log lines into the hub's game log — `Load game-specific cheatfile` when it finds the file under
RetroArch's name rule (one more dot-suffix stripped), `Cheat #n: <name>: on|off` for index pulses only once its "core
runs" (pulses before that are lost, as measured headless), toggles flipping the state. No emulator, no network beyond
loopback; made-up names; temp dirs removed at exit.

    python3 -m unittest discover -s tests/b87_cheat_ready -v
"""

from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parent / "art_systems"
sys.path.insert(0, str(ART))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402

FLAGS = b85.FLAGS
OFF = {**FLAGS, "PRIVYHUB_CHEAT_READY": "0"}
DOTTED = "Made Up v1.1 (USA).v64"                  # a title whose name holds a dot (RetroArch: "Made Up v1.cht")
ROWS = [(f"Made Up Cheat {i}", f"8010{i:04X} 0001") for i in range(6)]

FAKE = r'''
elif mode == "ra_launch":
    import socket as _s, re as _re
    events = {"toggles": 0, "pulses": 0, "lost": 0, "loaded": False}
    cfg = {}
    _real_socket = _s.socket
    _real_connect = None
    class FakeRetroArch:
        def __init__(self, cmd, **kw):
            self.pid = 999999999; self.returncode = None; self.stdin = None
            self.out = kw.get("stdout"); self.content = Path(cmd[-1]); self.t0 = time.monotonic()
            self.paused = False; self.cursor = 0; self.on = {}; self.stop = False
            text = (root / "data/games/retroarch/config/privyhub-session.cfg").read_text()
            db = Path(_re.search(r'cheat_database_path = "([^"]+)"', text).group(1))
            stem = self.content.stem
            ra_name = Path(stem).stem if "." in stem else stem          # RetroArch's own rule (measured headless)
            self.file = db / "Mupen64Plus-Next" / f"{ra_name}.cht"
            if not self.file.is_file():
                self.file = db / "Beetle PSX HW" / f"{ra_name}.cht"
            self.names = {}
            if self.file.is_file():
                for line in self.file.read_text().splitlines():
                    mm = _re.match(r'cheat(\d+)_desc = "(.*)"', line)
                    if mm:
                        self.names[int(mm.group(1))] = mm.group(2)
            self.sock = _real_socket(_s.AF_INET, _s.SOCK_DGRAM)
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
                elif c == "CHEAT_INDEX_PLUS":
                    events["pulses"] += 1
                    if not (running and events["loaded"]):
                        events["lost"] += 1                    # before the core runs: lost, not late
                        continue
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
    em.EmulatorManager._wait_for_retroarch_command_ready = em.EmulatorManager._wait_for_retroarch_command_ready
    t_start = time.monotonic()
    try:
        g.handle_post("launch", args["query"])
        out["error"] = None
    except Exception as exc:
        out["error"] = str(exc)
    out["elapsed"] = round(time.monotonic() - t_start, 2)
    s = m._active_cheat_session or {}
    out["session"] = {k: s.get(k) for k in ("enabled_cheat_indexes", "activation_verified", "activation_verification_lines",
                                            "activation_error")}
    out["events"] = events
    out["running"] = m.process is not None and m.process.poll() is None
    out["staging_left"] = sorted(str(p.relative_to(root)) for p in (root / "data/games/retroarch").rglob("*.cht")
                                 if "cheat_runtime" in str(p))
'''
CHILD = b85.CHILD.replace('out["popen"] = calls["popen"]', FAKE.strip("\n") + '\nout["popen"] = calls["popen"]', 1)


def tree():
    """B85's tree plus a dotted N64 title with its own cached list."""
    root, ids = b85.tree()
    drive = root / "drive/n64"
    with open(drive / DOTTED, "wb") as f:
        f.truncate(64)
    r, _a, _s = b85.b83.run(root, FLAGS, "ids")
    ids = {(s, t): g for s, t, g in b85.b83.out_of(r)["ids"]}
    rel_of = {g[2]: g[3] for g in b85.b83.b82.scan(root, FLAGS)["games"]}
    dotted = ids[("n64", Path(DOTTED).stem)]
    b85.manifest(root, [("n64", ids[b85.N64_TITLE], rel_of[ids[b85.N64_TITLE]], b85.cht(ROWS)),
                        ("n64", dotted, rel_of[dotted], b85.cht(ROWS)),
                        ("ps1", ids[b85.PS1_TITLE], rel_of[ids[b85.PS1_TITLE]], b85.cht(b85.PS1_ROWS))])
    return root, ids, dotted


def launch(root, env, gid, index, **fake):
    old = b85.b83.CHILD
    b85.b83.CHILD = CHILD
    try:
        r, attempts, _ = b85.b83.run(root, env, "ra_launch",
                                     {"id": gid, "query": f"id={gid}&cheat_source=0&cheat_indexes={index}", **fake})
    finally:
        b85.b83.CHILD = old
    out = b85.b83.out_of(r)
    out["attempts"] = attempts
    return out


class N64(unittest.TestCase):
    def test_port_up_before_the_core_runs_the_hub_waits_then_toggles(self):
        root, ids, _d = tree()
        out = launch(root, FLAGS, ids[b85.N64_TITLE], 3, load_at=0.05, run_at=0.6)
        self.assertIsNone(out["error"], out)
        self.assertTrue(out["session"]["activation_verified"])
        self.assertEqual(out["session"]["enabled_cheat_indexes"], [3])
        self.assertEqual(out["events"]["toggles"], 1)
        self.assertGreater(out["events"]["lost"], 0)                 # pulses before the core ran were lost…
        self.assertTrue(out["running"])                             # …and the session formed anyway
        self.assertEqual(out["attempts"], 0)

    def test_a_cheat_file_never_loaded_is_the_plain_error_within_the_bound(self):
        root, ids, _d = tree()
        t = time.monotonic()
        out = launch(root, FLAGS, ids[b85.N64_TITLE], 3, load_at=None, run_at=0.0)
        self.assertIn("cheats not ready — the game did not finish loading", out["error"])
        self.assertLess(time.monotonic() - t, 10.0 + 8.0)            # the 10-s bound (+ the child's own start)
        self.assertEqual(out["events"]["toggles"], 0)                # no toggle was ever sent
        self.assertEqual(out["events"]["pulses"], 0)                 # nor a pulse: the file was never loaded
        self.assertFalse(out["running"])                            # stopped cleanly
        self.assertEqual(out["staging_left"], [])                    # the staging removed

    def test_a_core_that_never_runs_is_the_plain_error(self):
        root, ids, _d = tree()
        out = launch(root, FLAGS, ids[b85.N64_TITLE], 3, load_at=0.05, run_at=999.0)
        self.assertIn("cheats not ready", out["error"])
        self.assertEqual(out["events"]["toggles"], 0)
        self.assertFalse(out["running"])

    def test_a_dotted_title_is_staged_under_retroarchs_name_and_works(self):
        root, _ids, dotted = tree()
        out = launch(root, FLAGS, dotted, 2, load_at=0.05, run_at=0.0)
        self.assertIsNone(out["error"], out)
        self.assertTrue(out["session"]["activation_verified"])
        off = launch(tree()[0], OFF, dotted, 2, load_at=0.05, run_at=0.0)      # today: the file not found
        self.assertIsNotNone(off["error"])
        self.assertFalse(off["events"]["loaded"])


class TodayAndPS1(unittest.TestCase):
    def test_ps1_rows_equal_with_and_without_the_wait(self):
        root, ids, _d = tree()
        on = launch(root, FLAGS, ids[b85.PS1_TITLE], 2, load_at=0.0, run_at=0.0)
        off = launch(tree()[0], OFF, ids[b85.PS1_TITLE], 2, load_at=0.0, run_at=0.0)   # ids: the same relative paths
        self.assertIsNone(on["error"], on)
        self.assertIsNone(off["error"], off)
        self.assertEqual(json.dumps(on["session"], sort_keys=True), json.dumps(off["session"], sort_keys=True))
        self.assertEqual(on["session"]["enabled_cheat_indexes"], [0, 2])    # B85's "must be on" + the pick

    def test_the_knob_zero_is_todays_first_pulse_failure_on_a_slow_core(self):
        root, ids, _d = tree()
        out = launch(root, OFF, ids[b85.N64_TITLE], 3, load_at=0.05, run_at=1.5)
        self.assertIn("did not report cheat-index navigation state", out["error"])
        self.assertFalse(out["running"])


if __name__ == "__main__":
    unittest.main()
