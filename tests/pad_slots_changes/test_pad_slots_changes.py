#!/usr/bin/env python3
"""B38 (host): `updates_by_player` counts only the slots whose state changed in a tick, for a stable-slot client.

The sender sends all four players every ~8-ms tick (CTRL-L1), so the bridge's per-packet counter rose equally on all
four in HOME-1 C4. With a client's `pad_slots` key the bridge also counts changes (`changes_by_player`), and the
heartbeat row carries them as `updates_by_player`, today's per-packet counts as `packets_by_player`. No key = today.

    python3 -m unittest discover -s tests/pad_slots_changes -v

The real `NativeControllerBridge._apply_report` on a temp root, the gamepad write stubbed (no uinput); `plugins/games.py`
loaded alone with a real LinkDropRecovery (tests/pad_slots' way).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))

import native_session_io as nsio  # noqa: E402
import pad_slots  # noqa: E402
from games import link_drop_recovery as ldr  # noqa: E402

spec = importlib.util.spec_from_file_location("b38_games_plugin", ROOT / "companion" / "plugins" / "games.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)

TWO = "0:a1b2c3:sony,1:d4e5f6:sony"
HB = "sequence={}&interval_ms=2000&last_output_age_ms=16&rendered_frames=600&queued_frames=0&rx_packets=900&elapsed_ms=10000"
A = nsio.NativeControllerBridge.XUSB_A


def bridge():
    b = nsio.NativeControllerBridge(Path(tempfile.mkdtemp(prefix="b38_bridge_")))
    b._gamepads = [object() for _ in range(b.MAX_PLAYERS)]
    b._controller_backend = "linux_uinput"
    b._write_linux_report_locked = lambda *a, **k: None
    return b


def ticks(b, n, press_at=None, player=1):
    """n ticks of all four players' full state, as the sender sends them; player `player` holds A for 10 ticks."""
    for t in range(n):
        for p in range(b.MAX_PLAYERS):
            held = press_at is not None and p == player and press_at <= t < press_at + 10
            b._apply_report(p, A if held else 0, 0, 0, 0, 0, 0, 0)


def plugin(controller):
    root = Path(tempfile.mkdtemp(prefix="b38_root_"))
    rec = ldr.LinkDropRecovery(
        root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
        restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
        end_session=lambda: None, client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})

    class Emu:
        def status(self):
            return {"active": True, "paused": True, "pid": 1}

    p = object.__new__(G.GamesPlugin)
    p.PROJECT_ROOT = root
    p._emulator = Emu()
    p._recovery = rec
    p._native_stream = types.SimpleNamespace(start=lambda **kw: {"active": True},
                                             _session_io=types.SimpleNamespace(controller=controller))
    p._diagnostic_heartbeat_interval_ms = lambda: 2000
    p._adaptive_bitrate_session_ended = lambda: None
    return p, root, rec


def hb_rows(root):
    path = root / "logs" / "games" / "native_stream_heartbeat.log"
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


class Bridge(unittest.TestCase):
    def test_only_the_pressed_slot_counts_a_change(self):
        b = bridge()
        self.assertTrue(pad_slots.enable_changes(b))
        ticks(b, 300, press_at=100, player=1)
        s = b.status()
        self.assertEqual(s["changes_by_player"], [0, 2, 0, 0])      # the press and the release
        self.assertEqual(s["updates_by_player"], [300, 300, 300, 300])  # today's per-packet count, unchanged
        self.assertEqual(s["vigem_updates_by_player"], [300, 300, 300, 300])

    def test_an_axis_move_counts_and_a_held_state_does_not(self):
        b = bridge()
        pad_slots.enable_changes(b)
        for v in (0, 1000, 1000, 1000, 2000, 2000):
            b._apply_report(0, 0, v, 0, 0, 0, 0, 0)
        self.assertEqual(b.status()["changes_by_player"], [2, 0, 0, 0])   # 0 (no change), →1000, held ×2, →2000, held

    def test_not_enabled_is_today(self):
        b = bridge()
        base = nsio.NativeControllerBridge(Path(tempfile.mkdtemp(prefix="b38_bridge_")))
        self.assertIsNone(b._changes_by_player)
        ticks(b, 50, press_at=10)
        s = b.status()
        self.assertNotIn("changes_by_player", s)
        self.assertEqual(sorted(s), sorted(base.status()))           # the same keys as a bridge never fed
        self.assertEqual(s["updates_by_player"], [50, 50, 50, 50])

    def test_enable_is_idempotent_and_a_missing_bridge_is_refused(self):
        b = bridge()
        pad_slots.enable_changes(b)
        ticks(b, 20, press_at=5, player=2)
        pad_slots.enable_changes(b)                                   # a later heartbeat: no reset
        self.assertEqual(b.status()["changes_by_player"], [0, 0, 2, 0])
        self.assertFalse(pad_slots.enable_changes(None))


class Rows(unittest.TestCase):
    def test_a_stable_slot_client_gets_changes_on_the_heartbeat_row(self):
        b = bridge()
        p, root, rec = plugin(b)
        p.handle_post_request("native-stream-start", "port=48100&pad_slots=" + TWO, "127.0.0.1")
        self.assertIsNotNone(b._changes_by_player)                    # on from the start query
        ticks(b, 200, press_at=50, player=0)
        p.handle_post_request("native-stream-heartbeat", HB.format(1) + "&pad_slots=" + TWO, "127.0.0.1")
        row = hb_rows(root)[0]
        self.assertEqual(row["updates_by_player"], [2, 0, 0, 0])
        self.assertEqual(row["packets_by_player"], [200, 200, 200, 200])

    def test_no_key_is_today(self):
        b = bridge()
        p, root, rec = plugin(b)
        p.handle_post_request("native-stream-start", "port=48100", "127.0.0.1")
        ticks(b, 20, press_at=5)
        p.handle_post_request("native-stream-heartbeat", HB.format(1), "127.0.0.1")
        self.assertIsNone(b._changes_by_player)
        row = hb_rows(root)[0]
        for k in ("pad_slots", "updates_by_player", "packets_by_player", "pad_slots_bad"):
            self.assertNotIn(k, row)
        self.assertNotIn("changes_by_player", b.status())

    def test_a_fresh_process_without_the_key_imports_nothing(self):
        code = ("import sys, importlib.util; sys.path.insert(0, 'companion');"
                "import native_session_io as n;"
                "print('pad_slots' in sys.modules, n.NativeControllerBridge._changes_by_player)")
        out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "False None")


if __name__ == "__main__":
    unittest.main()
