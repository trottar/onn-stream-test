#!/usr/bin/env python3
"""B71 (host): "Change disc" on a multi-disc PS1 (.m3u) session over RetroArch's command port.

    python3 -m unittest discover -s tests/b71_disc_swap -v

A fake RetroArch: a UDP socket on 127.0.0.1 in a thread that answers GET_STATUS and, for each disk command, appends
RetroArch 1.22.2's own log line to the session's game log (the label included, so the tests can show it is never
copied). A real EmulatorManager on a temp project (its real `_retroarch_network_request`); temp dirs removed at exit.
"""

from __future__ import annotations

import ast
import atexit
import json
import socket
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import disc_swap as ds  # noqa: E402
from games import emulator_manager as em  # noqa: E402
from games import native_stream_heartbeat as hb  # noqa: E402

LABEL = "Fake Label Disc"          # what a core names a disc: must never reach PrivyHub's lines / rows
_OPEN: list = []                   # the managers' game-log handles, closed at exit (before the temp dirs go)
atexit.register(lambda: [h.close() for h in _OPEN])


class FakeRetroArch:
    """`mode`: "ok" (RetroArch's behaviour: NEXT at the last disc stays there), "removed" (NEXT past the end removes
    the disc), "silent_steps" (no line for NEXT / PREV), "silent_eject" (no line for the eject)."""

    def __init__(self, log_path: Path, discs: int, index: int = 0, mode: str = "ok", paused: bool = True):
        self.log_path, self.n, self.index, self.mode, self.paused = log_path, discs, index, mode, paused
        self.tray_open = False
        self.commands: list[tuple[float, str]] = []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.1)
        self.port = self.sock.getsockname()[1]
        self.stop = False
        self.t = threading.Thread(target=self.run, daemon=True)
        self.t.start()

    def line(self, text: str) -> None:
        with self.log_path.open("a", encoding="utf-8") as h:
            h.write(f"[INFO] [Disc] {text}\n")

    def set_line(self) -> None:
        if self.index >= self.n:
            self.line("Removed disk from tray.")
        else:
            self.line(f"Setting disc in tray: {self.index + 1}/{self.n} - {LABEL} {self.index + 1}")

    def run(self) -> None:
        while not self.stop:
            try:
                data, addr = self.sock.recvfrom(4096)
            except (socket.timeout, OSError):
                continue
            cmd = data.decode().strip()
            self.commands.append((time.monotonic(), cmd))
            if cmd == "GET_STATUS":
                state = "PAUSED" if self.paused else "PLAYING"
                self.sock.sendto(f"GET_STATUS {state} playstation,Fake Title,crc32=0".encode(), addr)
            elif cmd == "PAUSE_TOGGLE":
                self.paused = not self.paused
            elif cmd == "DISK_EJECT_TOGGLE":
                self.tray_open = not self.tray_open
                if self.mode != "silent_eject":
                    self.line("Ejected virtual disc tray." if self.tray_open else "Closed virtual disc tray.")
            elif cmd in ("DISK_NEXT", "DISK_PREV"):
                if cmd == "DISK_NEXT":
                    self.index = min(self.index + 1, self.n if self.mode == "removed" else self.n - 1)
                else:
                    self.index = max(self.index - 1, 0)
                if self.mode != "silent_steps":
                    self.set_line()

    def close(self) -> None:
        self.stop = True
        self.t.join(1)
        self.sock.close()

    def disk_commands(self) -> list[str]:
        return [c for _, c in self.commands if c.startswith("DISK_")]


def project():
    return Path(tempfile.mkdtemp(prefix="b71_proj_"))


def m3u(folder: Path, n: int, extra: str = "") -> Path:
    p = folder / "games/ps1/Set.m3u"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(extra + "".join(f"Set (Disc {i}).cue\n" for i in range(1, n + 1)))
    return p


def manager(discs: int = 4, index: int = 0, mode: str = "ok", paused: bool = True, launch_line: bool = True):
    proj = project()
    log_path = proj / "logs/games/x-game_ps1_0123.log"
    log_path.parent.mkdir(parents=True)
    log_path.write_text("PrivyHub game session\n")
    fake = FakeRetroArch(log_path, discs, index, mode, paused)
    if launch_line:
        fake.set_line()                                   # RetroArch's own line at the launch
    m = em.EmulatorManager(proj)
    m.process = types.SimpleNamespace(pid=1, poll=lambda: None, stdin=None)
    m._refresh_process = lambda: None
    m.active_game = {"id": "game_ps1_0123", "system": "ps1", "relative_path": "games/ps1/Set.m3u"}
    m._paused = paused
    m._network_cmd_port = fake.port
    m.log_handle = log_path.open("a", encoding="utf-8")
    _OPEN.append(m.log_handle)
    m.record_save_state_probe_event = lambda *a, **k: None
    m._disc_session = ds.session_for(m3u(proj, discs), "ps1")
    m._disc_tail = ds.LogTail(log_path) if m._disc_session else None
    return m, fake, log_path


class Detection(unittest.TestCase):
    def test_m3u_count(self):
        d = project()
        self.assertEqual(ds.m3u_discs(m3u(d, 2, extra="#EXTM3U\n\n# a comment\n")), 2)
        self.assertEqual(ds.session_for(m3u(d, 4), "ps1"), {"discs": 4, "disc": 1})

    def test_not_a_multi_disc_session(self):
        d = project()
        one = m3u(d, 1)
        self.assertIsNone(ds.session_for(one, "ps1"))                       # one disc
        cue = d / "games/ps1/Single.cue"
        cue.write_text("FILE x\n")
        self.assertIsNone(ds.session_for(cue, "ps1"))                       # a .cue
        self.assertIsNone(ds.session_for(m3u(d, 2), "n64"))                 # another system
        self.assertIsNone(ds.session_for(d / "missing.m3u", "ps1"))         # unreadable
        self.assertIsNone(ds.session_for(m3u(d, 2), "ps1", environ={"PRIVYHUB_DISC_SWAP": "0"}))   # the knob
        self.assertIsNotNone(ds.session_for(m3u(d, 2), "ps1", environ={"PRIVYHUB_DISC_SWAP": "1"}))

    def test_starting_disc_from_the_launch_line(self):
        m, fake, _ = manager(discs=4, index=1)          # RetroArch restored disc 2 at the launch
        try:
            self.assertEqual(m.status()["disc"], 2)
            self.assertEqual(m.status()["discs"], 4)
        finally:
            fake.close()
        m, fake, _ = manager(discs=2, launch_line=False)
        try:
            self.assertEqual(m.status()["disc"], 1)     # no line: disc 1
        finally:
            fake.close()

    def test_last_index_reads_only_the_numbers(self):
        text = "[INFO] [Disc] Setting disc in tray: 1/4 - A\n[INFO] [Disc] Setting disc in tray: 3/4\nother 2/4\n"
        self.assertEqual(ds.last_index(text, 4), 3)
        self.assertIsNone(ds.last_index(text, 2))       # another count: not this set


class Swap(unittest.TestCase):
    def swap(self, start_index, target, discs=4, **kw):
        m, fake, log_path = manager(discs=discs, index=start_index, **kw)
        try:
            reply = m.disc_swap(target)
            return m, fake, log_path, reply, None
        except em.EmulatorError as exc:
            return m, fake, log_path, None, exc
        finally:
            fake.close()

    def test_one_to_two(self):
        m, fake, log_path, reply, err = self.swap(0, 2, discs=2)
        self.assertIsNone(err)
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE", "DISK_NEXT", "DISK_EJECT_TOGGLE"])
        self.assertFalse(fake.tray_open)
        self.assertEqual(fake.index, 1)
        self.assertEqual((reply["from_disc"], reply["disc"], reply["discs"], reply["changed"], reply["steps"]),
                         (1, 2, 2, True, 1))
        self.assertTrue(fake.paused)                                       # left paused as it was
        self.assertNotIn("PAUSE_TOGGLE", [c for _, c in fake.commands])
        m.log_handle.flush()
        text = log_path.read_text()
        self.assertIn("PS1 disc swap: 1 -> 2\n", text)
        ours = [l for l in text.splitlines() if l.startswith("PS1 disc")]
        self.assertTrue(all(LABEL not in l and "Fake Title" not in l and "/" not in l for l in ours))

    def test_spacing_between_commands(self):
        m, fake, _, reply, err = self.swap(0, 3)
        self.assertIsNone(err)
        times = [t for t, c in fake.commands if c.startswith("DISK_")]
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE", "DISK_NEXT", "DISK_NEXT", "DISK_EJECT_TOGGLE"])
        self.assertTrue(all(b - a >= ds.GAP_S - 0.02 for a, b in zip(times, times[1:])), times)

    def test_down_and_up(self):
        m, fake, _, reply, err = self.swap(3, 1)
        self.assertIsNone(err)
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE"] + ["DISK_PREV"] * 3 + ["DISK_EJECT_TOGGLE"])
        self.assertEqual((fake.index, reply["disc"], reply["steps"]), (0, 1, 3))
        m, fake, _, reply, err = self.swap(1, 4)
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE"] + ["DISK_NEXT"] * 2 + ["DISK_EJECT_TOGGLE"])
        self.assertEqual(m._disc_session["disc"], 4)

    def test_unknown_start_found_by_its_first_step(self):
        m, fake, _ = manager(discs=4, index=3)
        try:
            m._disc_session["disc"] = None            # after a LOAD
            m._disc_tail.read()                       # the launch line already read
            reply = m.disc_swap(3)
        finally:
            fake.close()
        # NEXT from disc 4 stays at 4 (RetroArch's own rule), then PREV to 3
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE", "DISK_NEXT", "DISK_PREV", "DISK_EJECT_TOGGLE"])
        self.assertEqual((reply["from_disc"], reply["disc"]), (None, 3))

    def test_removed_past_the_end_then_prev(self):
        m, fake, _ = manager(discs=2, index=1, mode="removed")
        try:
            m._disc_session["disc"] = None
            m._disc_tail.read()
            reply = m.disc_swap(2)
        finally:
            fake.close()
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE", "DISK_NEXT", "DISK_PREV", "DISK_EJECT_TOGGLE"])
        self.assertEqual((reply["disc"], fake.index, fake.tray_open), (2, 1, False))

    def test_same_disc_no_command(self):
        m, fake, _, reply, err = self.swap(1, 2)
        self.assertIsNone(err)
        self.assertEqual(fake.disk_commands(), [])
        self.assertEqual((reply["changed"], reply["steps"], reply["disc"]), (False, 0, 2))

    def test_refusals(self):
        for kw, target, words in (({"paused": False}, 2, "Pause the game"), ({}, 5, "disc must be 1 to 4"),
                                  ({}, "x", "disc must be 1 to 4"), ({}, 0, "disc must be 1 to 4")):
            m, fake, _, reply, err = self.swap(0, target, **kw)
            self.assertIsNotNone(err, (kw, target))
            self.assertIn(words, str(err))
            self.assertEqual(fake.disk_commands(), [])
        m, fake, _ = manager(discs=2)
        fake.close()
        m._disc_session = None
        with self.assertRaises(em.EmulatorError) as cm:
            m.disc_swap(2)
        self.assertIn("one disc", str(cm.exception))
        m._disc_session = {"discs": 2, "disc": 1}
        m._launch_kind = "dolphin"
        with self.assertRaises(em.EmulatorError):
            m.disc_swap(2)

    def test_no_step_line_closes_the_tray_again(self):
        with mock.patch.object(ds, "LINE_BOUND_S", 0.3):
            m, fake, _, reply, err = self.swap(0, 2, mode="silent_steps")
        self.assertIsNotNone(err)
        self.assertIn("could not change the disc", str(err))
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE", "DISK_NEXT", "DISK_EJECT_TOGGLE"])
        self.assertFalse(fake.tray_open)                                    # closed again
        self.assertEqual(m._disc_event["ok"], False)
        self.assertEqual(m._disc_event["reason"], "no disc line from RetroArch")

    def test_no_eject_line(self):
        with mock.patch.object(ds, "LINE_BOUND_S", 0.3):
            m, fake, _, reply, err = self.swap(0, 2, mode="silent_eject")
        self.assertIsNotNone(err)
        self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE"])     # nothing stepped blind
        self.assertEqual(m._disc_event["reason"], "the tray did not open")

    def test_reply_has_the_ps1_shape(self):
        m, fake, _, reply, err = self.swap(0, 2)
        for key in ("ok", "kind", "active", "paused", "game", "save_state_slots", "action", "accepted", "confirmed",
                    "control"):
            self.assertIn(key, reply)
        self.assertEqual((reply["action"], reply["control"], reply["accepted"], reply["confirmed"]),
                         ("disc_swap", "retroarch_network_disk_control", True, True))
        ev = m._disc_event
        self.assertEqual((ev["from_disc"], ev["disc"], ev["discs"], ev["ok"], ev["steps"]), (1, 2, 4, True, 1))
        self.assertNotIn(LABEL, json.dumps(ev))


class Rows(unittest.TestCase):
    def test_status_keys_only_on_a_multi_disc_session(self):
        m, fake, _ = manager(discs=2)
        try:
            st = m.status()
            self.assertEqual((st["discs"], st["disc"]), (2, 1))
            m._disc_session = None
            st = m.status()
            self.assertNotIn("discs", st)
            self.assertNotIn("disc", st)
            m._disc_session = {"discs": 2, "disc": 1}
            m.process = None                                   # not active: no keys
            self.assertNotIn("discs", m.status())
        finally:
            fake.close()

    def test_load_makes_the_disc_unknown(self):
        m, fake, _ = manager(discs=2)
        fake.close()
        payload = m.disc_after_load({"discs": 2, "disc": 1, "action": "load_state"})
        self.assertIsNone(payload["disc"])
        self.assertIsNone(m._disc_session["disc"])
        m._disc_session = None
        self.assertEqual(m.disc_after_load({"action": "load_state"}), {"action": "load_state"})   # today

    def test_heartbeat_copies_only_when_present(self):
        d = project()
        hb.append_native_stream_heartbeat(d, {"elapsed_ms": 1, "rendered_frames": 2})
        hb.append_native_stream_heartbeat(d, {"elapsed_ms": 3, "rendered_frames": 4, "discs": 4, "disc": 2})
        rows = [json.loads(l) for l in hb.heartbeat_log_path(d).read_text().splitlines()]
        self.assertNotIn("discs", rows[0])
        self.assertNotIn("disc", rows[0])
        self.assertEqual((rows[1]["discs"], rows[1]["disc"]), (4, 2))

    def plugin(self, payload):
        import importlib.util
        spec = importlib.util.spec_from_file_location("g71", str(ROOT / "companion/plugins/games.py"))
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        rows = []
        p = object.__new__(G.GamesPlugin)
        p._recovery = types.SimpleNamespace(_log=lambda e, **k: rows.append({"event": e, **k}))
        sess = {"players_chosen": 2, "ports": 2, "multitap": False, "multitap_available": False, "source": "join"}
        p._emulator = types.SimpleNamespace(launch=lambda game, **kw: payload, _launch_kind=None, _players_session=sess,
                                            _last_device_args=[], active_game={"system": "ps1"})
        p._find_game_by_id = lambda gid: {"id": gid, "system": "ps1"}
        p._parse_cheat_launch_request = lambda q: (None, None)
        return p, rows

    def test_launch_ports_row(self):
        p, rows = self.plugin({"discs": 4, "disc": 1})
        p.handle_post("launch", "id=game_ps1_x")
        r = [r for r in rows if r["event"] == "launch_ports"][0]
        self.assertEqual((r["discs"], r["disc"]), (4, 1))
        p, rows = self.plugin({})
        p.handle_post("launch", "id=game_ps1_x")
        r = [r for r in rows if r["event"] == "launch_ports"][0]
        self.assertNotIn("discs", r)                                       # today's row
        self.assertNotIn("disc", r)

    def test_the_action_and_its_row(self):
        p, rows = self.plugin({})

        def swap(disc):
            p._emulator._disc_event = {"event": "disc_swap", "ok": True, "from_disc": 1, "disc": int(disc), "discs": 2,
                                       "changed": True, "steps": 1, "ms": 900}
            return {"action": "disc_swap", "disc": int(disc)}
        p._emulator.disc_swap = swap
        self.assertEqual(p.handle_post("disc-swap", "disc=2")["disc"], 2)
        r = [r for r in rows if r["event"] == "disc_swap"]
        self.assertEqual(len(r), 1)
        self.assertEqual((r[0]["from_disc"], r[0]["disc"], r[0]["ok"]), (1, 2, True))
        with mock.patch.dict("os.environ", {"PRIVYHUB_DISC_SWAP": "0"}):
            with self.assertRaises(ValueError) as cm:                    # the knob: today's unknown action
                p.handle_post("disc-swap", "disc=2")
            self.assertIn("Unknown Games plugin POST action", str(cm.exception))

    def test_the_heartbeat_hook_reads_the_session(self):
        src = (ROOT / "companion/plugins/games.py").read_text()
        i = src.index("# B71: and a multi-disc session's discs / disc")
        block = src[i:i + 400]
        self.assertIn('getattr(self._emulator, "_disc_session", None)', block)
        self.assertIn('values["discs"]', block)

    def test_every_session_end_clears_it(self):
        src = (ROOT / "companion/games/emulator_manager.py").read_text()
        self.assertEqual(src.count("self._network_cmd_port = None\n"), src.count("self._disc_session = None   # B71\n"))
        tree = ast.parse(src)
        launch = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "launch")
        first = ast.unparse(launch)
        self.assertLess(first.index("self._disc_session = None"), first.index("_launch_pcsx2"))


if __name__ == "__main__":
    unittest.main()
