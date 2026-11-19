#!/usr/bin/env python3
"""B153 (host): the planned switch's length — through the real HTTP server on loopback.

PP-H4: the planned switches came in two lengths, 1.66-1.98 s and 3.48-3.61 s. The long kind's whole extra was the old
sound's stop: the stop event ends the audio reader's draining, ffmpeg notices SIGTERM only at its next 0.5-s wake, a
full pipe then blocks its last write, and `_kill_process`'s 2-s wait runs out before SIGKILL. B153: a party's planned
switch kills the old capture and the old encoder at once and starts the new sound before the encoder's 0.75-s check;
every other start is today's.

B114's harness, its `b153` mode (B143's set-up: the real routes, the real `PartyMinigames._switch_stream`, the real
`NativeStreamManager._start_linux_locked` on G8-S2's stubbed manager, the real `NativeAudioStreamer`, Opus, to a socket
on loopback) **with the capture the real ffmpeg** — lavfi silence at the real rate standing in for the pulse monitor,
the same s16le pipe (no audio device, no pulse, no title; B114's made-up title). A fresh board (the onn's own start), a
users' restart of its stream (the start route again, another process armed), then a held start, **ten practices in a
row left by Select (twenty planned switches, both ways)**, a real go and its end (two more).

Shown: every planned switch ≤ BOUND_S and its sound's gap ≤ GAP_MS; the capture and the encoder killed at once at
every planned switch, never at the users' starts; the sequence continued (B143). **HEAD's code, the same scenario: the
long kind** — a capture's SIGTERM stop ≥ 1.9 s and its switch ≥ 1.9 s. **A users' start on G8-S2's recorders** (the
flags' arm for another process set): its calls, argv and payload the same as HEAD's. Temp dirs removed.

    python3 -m unittest discover -s tests/b153_party_switch_length -v
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b114_party_minigame_hang"))
sys.path.insert(0, str(ROOT / "tests" / "b124_party_four_seats"))
sys.path.insert(0, str(ROOT / "tests" / "b143_party_audio_switch"))
sys.path.insert(0, str(ROOT / "tests" / "start_rung"))
import test_b114 as b114  # noqa: E402  (its harness; its tests are not collected here)
import test_b124 as b124  # noqa: E402

BASELINE = "d7a99b62"            # queue BA's baseline: the companion before B153
STUB_S = 0.6                     # the harness's stream stub's own start, before the real one (B114's start_s)
OWN_S = 0.9                      # the real start's own bound (the 0.75-s check + the rest; no window search, no VAAPI)
BOUND_S = STUB_S + OWN_S         # a planned switch's row
GAP_MS = 300.0                   # the harness's bound on the sound's gap at a planned switch
LONG_MS = 1900.0                 # a capture's stop this long: the 2-s wait ran out (the long kind)


def extra(work, frames):
    return {**b124.extra(work, frames), "start_rung": str(ROOT / "tests" / "start_rung")}


def run_mode(code_rev: str | None) -> dict:
    code = b114.code_of(code_rev) if code_rev else None
    if code_rev and code is None:
        raise unittest.SkipTest("git is absent")
    root, ids = b114.b99.tree(code)
    try:
        b124.IDS.clear()
        b124.IDS.update(ids)
        return b114.run(root, b114.BOTH, ids, "b153", extra=extra)["steps"]
    finally:
        shutil.rmtree(root, ignore_errors=True)
        if code is not None:
            shutil.rmtree(code, ignore_errors=True)


def analyse(s: dict) -> dict:
    """Per planned start (from the held start on): its row's seconds, the stops inside it (kind, ms), the sound's gap
    (the last datagram before the new stream's first) and whether the sequence went on."""
    starts = s["b153_starts"]
    s0 = s["b153_starts_from"]
    dg = sorted(s["b153_dg"], key=lambda d: d[0])
    times = [d[0] for d in dg]
    kills = s["b153_kills"]
    rows = [r for r in s["b153_switch_rows"] if r.get("switched")]
    out = []
    for k, st in enumerate(starts[s0:], start=s0):
        t_stop, t_up = st["t_stop"], st["t_up"]
        inside = [x for x in kills if t_stop - 0.01 <= x["t"] <= t_up]
        # the switch's own gap: the longest silence between two datagrams from the stop to 0.5 s after the start
        js = [j for j in range(1, len(dg)) if t_stop <= times[j] <= t_up + 0.5]
        j = max(js, key=lambda j: times[j] - times[j - 1]) if js else None
        gap = None if j is None else round((times[j] - times[j - 1]) * 1000.0, 1)
        cont = None if j is None else dg[j][1] == (max(d[1] for d in dg[max(0, j - 8):j]) + 1) & 0xFFFF
        out.append({"k": k, "board": st["board"], "stops": [[x["kind"], x["ms"]] for x in inside], "gap_ms": gap,
                    "continued": cont, "up_s": round(t_up - t_stop, 3)})
    return {"starts": out, "rows": rows}


class TwentyInARow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = run_mode(None)
        cls.a = analyse(cls.s)
        if os.environ.get("B153_OUT"):
            Path(os.environ["B153_OUT"]).write_text(json.dumps({"mine": cls.a, "users": {
                k: cls.s.get(k) for k in ("b153_users_kills_board", "b153_users_kills_restart", "b153_users_restart")},
                "b153": cls.s.get("b153"), "errors": cls.s.get("b143_errors"),
                "thread_exc": cls.s.get("b143_thread_exc")}, indent=1))

    def test_0_the_scenario_played(self):
        s = self.s
        self.assertIsNone(s.get("b143_errors"), s.get("b143_errors"))
        self.assertIsNone(s.get("b143_thread_exc"), s.get("b143_thread_exc"))
        self.assertEqual(s["b153"]["state"], "ended", s["b153"])
        self.assertEqual(s["b153"].get("practices"), 10, s["b153"])
        self.assertEqual(s["b153_users_restart"], 200)
        windows = [r["window"] for r in self.a["rows"]]
        self.assertEqual(windows, ["minigame", "board"] * 11, windows)     # 20 practices' switches + the go + the end

    def test_1_every_planned_switch_under_the_bound(self):
        rows = self.a["rows"]
        self.assertEqual(len(rows), 22)
        for r in rows:
            self.assertTrue(r["planned"], r)
            self.assertLessEqual(r["seconds"], BOUND_S, rows)
        for x in self.a["starts"]:
            self.assertLessEqual(x["up_s"], OWN_S, x)

    def test_2_the_sound_back_quickly_and_continued(self):
        planned = self.a["starts"]
        self.assertEqual(len(planned), 22, planned)
        for x in planned:
            self.assertIsNotNone(x["gap_ms"], x)
            self.assertLessEqual(x["gap_ms"], GAP_MS, planned)
            self.assertTrue(x["continued"], x)                          # B143: the sequence goes on

    def test_3_killed_at_once_only_at_planned_switches(self):
        for x in self.a["starts"]:
            kinds = [k for k, _ms in x["stops"]]
            self.assertIn("capture_kill", kinds, x)
            self.assertIn("encoder_kill", kinds, x)
            self.assertNotIn("capture_term", kinds, x)
            self.assertNotIn("encoder_term", kinds, x)
            self.assertTrue(all(ms < 300 for _k, ms in x["stops"]), x)
        for key in ("b153_users_kills_board", "b153_users_kills_restart"):   # the users' starts: today's SIGTERM
            kinds = {k["kind"] for k in self.s[key]}          # the board's first start: nothing running to stop
            self.assertTrue(kinds <= {"capture_term", "encoder_term"}, (key, self.s[key]))
        self.assertEqual({k["kind"] for k in self.s["b153_users_kills_restart"]}, {"capture_term", "encoder_term"})


class HeadShowsTheLongKind(unittest.TestCase):
    """HEAD's companion, the same twenty-two switches: the capture stopped by SIGTERM, and at least one stop runs the
    2-s wait out (the long kind; ~1 in 3 on the hub and here)."""

    @classmethod
    def setUpClass(cls):
        cls.s = run_mode(BASELINE)
        cls.a = analyse(cls.s)
        if os.environ.get("B153_OUT_HEAD"):
            Path(os.environ["B153_OUT_HEAD"]).write_text(json.dumps({"head": cls.a}, indent=1))

    def test_head_long_kind(self):
        rows = self.a["rows"]
        self.assertEqual(len(rows), 22, rows)
        stops = [ms for x in self.a["starts"] for k, ms in x["stops"] if k == "capture_term"]
        self.assertEqual(len(stops), 22, self.a["starts"])
        self.assertFalse(any(k == "capture_kill" for x in self.a["starts"] for k, _ in x["stops"]))
        long_ = [ms for ms in stops if ms >= LONG_MS]
        self.assertGreaterEqual(len(long_), 1, stops)
        self.assertGreaterEqual(max(r["seconds"] for r in rows), LONG_MS / 1000.0, rows)


class UsersStartOnRecorders(unittest.TestCase):
    """G8-S2's stubbed manager: `_start_linux_locked` for a users' start (an arm for another process set on mine) —
    every stub call, the encoder's argv and the payload the same on HEAD's module and mine."""

    def one(self, companion: Path, arm: bool) -> dict:
        import importlib
        import stub_manager as stubm
        for name in ("native_stream", "native_session_io", "native_host_telemetry"):
            sys.modules.pop(name, None)
        sys.path.insert(0, str(companion))
        try:
            mod = importlib.import_module("native_stream")
            calls: list = []
            if arm and hasattr(mod.NativeStreamManager, "party_switch_next"):
                mod.NativeStreamManager._party_switch_pid = 424242      # armed for another process
            r = stubm.run_start(mod, "127.0.0.1", calls)
            shutil.rmtree(r["manager"].project_root, ignore_errors=True)
            return {"calls": r["calls"], "argv": r["argv"], "payload": r["payload"]}
        finally:
            sys.path.remove(str(companion))
            for name in ("native_stream", "native_session_io", "native_host_telemetry"):
                sys.modules.pop(name, None)

    def test_users_start_the_same(self):
        head = b114.code_of(BASELINE)
        if head is None:
            self.skipTest("git is absent")
        try:
            theirs = self.one(head / "companion", arm=False)
            mine = self.one(ROOT / "companion", arm=True)
        finally:
            shutil.rmtree(head, ignore_errors=True)
        self.assertTrue(theirs["calls"])
        self.assertEqual(json.dumps(mine, sort_keys=True, default=str), json.dumps(theirs, sort_keys=True, default=str))


if __name__ == "__main__":
    unittest.main()
