#!/usr/bin/env python3
"""B72 (host / tools): the small readings after HOME-9+GC.

(b) diag_read's `fps (min)` clamped at 0, a counter-reset second and a hold-resume second excluded from the min;
(c) B66's hold-resume split on a dolphin session starting at the hold's own desync_pause;
(d) gc_frames.py's 20-fps class, a segment classed by its own median, the VIs beside a render segment;
(e) the Dolphin launch's environment keeps SDL off the virtual pads (only the evdev four);
(f) a stall during the last load's picture check is not re-saved into slot 9 (the check awaited);
(g) the SAVE / LOAD reply bodies as `state_reply` rows (fixed keys, no path / title / state file).

    python3 -m unittest discover -s tests/b72_small_readings -v

Fakes only (B36's diag fixture, B69's fake Dolphin); temp dirs removed at exit.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import types
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests" / "diag_read"))
sys.path.insert(0, str(ROOT / "tests" / "gamecube_session"))

import diag_fixture as fx  # noqa: E402
import diag_read as dr  # noqa: E402
import gc_frames as gf  # noqa: E402
import gamecube_session as gc  # noqa: E402
import rewind_cores  # noqa: E402
import test_gamecube_session as tg  # noqa: E402  (B69's rig and fakes; its own tests are not collected here)
from games import emulator_manager as em  # noqa: E402

NY = ZoneInfo("America/New_York")
ORIG = fx.logs


# --- (b) / (c): diag_read ------------------------------------------------------------------------------------------

def analysis(extra_rows=(), hb_edit=None):
    """B36's fixture evening (session 1: 0-300 s, an R hitch at 100), with rows added in time order and an optional
    edit of the heartbeat rows."""
    def logs():
        out = ORIG()
        rows = out["native_stream_recovery.log"].splitlines() + [fx.rec(s, e, **kw) for s, e, kw in extra_rows]
        rows.sort(key=lambda l: json.loads(l)["at_utc"])
        out["native_stream_recovery.log"] = "\n".join(rows) + "\n"
        if hb_edit is not None:
            hb = [json.loads(l) for l in out["native_stream_heartbeat.log"].splitlines()]
            out["native_stream_heartbeat.log"] = "\n".join(json.dumps(hb_edit(r)) for r in hb) + "\n"
        return out
    fx.logs = logs
    try:
        kd = fx.write_keeper_dir(Path(tempfile.mkdtemp(prefix="b72_read_")) / fx.DAY)
    finally:
        fx.logs = ORIG
    lg = dr.Logs()
    lg.add_keeper_dir(kd)
    return dr.Analysis(lg, datetime(2026, 10, 30, 9, 0), datetime(2026, 10, 30, 11, 0), NY)


def first_row(an):
    return an.session_row(an.sessions[0])


def counter_reset_at(second: int):
    """The client's counters restart at `second` of session 1 (a Home hold's new activity): a negative delta there."""
    def edit(r):
        t = dr.ts(r["received_at_utc"])
        s = (t - fx.T).total_seconds()
        if 0 <= s < 300 and s >= second:
            r = dict(r)
            r["rendered_frames"] = max(0, r["rendered_frames"] - 5000)
        return r
    return edit


class FpsMin(unittest.TestCase):
    def test_today_without_a_reset(self):
        self.assertEqual(first_row(analysis())["rendered_fps_min"], 40.0)    # the fixture's R second: today's

    def test_a_counter_reset_second_is_not_the_min(self):
        an = analysis(hb_edit=counter_reset_at(200))
        raw = an.row[dr.sec(fx.at(200))]["fps"]
        self.assertLess(raw, 0)                                               # the hold's gap, as C36's -1659.0
        r = first_row(an)
        self.assertEqual(r["rendered_fps_min"], 40.0)                         # the real lowest second
        self.assertGreaterEqual(r["rendered_fps_min"], 0)

    def test_a_hold_resume_second_is_not_the_min(self):
        an = analysis([(99.6, "resumed", {"via": "stall_end", "from_state": "PAUSED_RECOVERING"})])
        self.assertGreater(first_row(an)["rendered_fps_min"], 40.0)          # the R second (100) is a hold's

    def test_never_negative(self):
        an = analysis(hb_edit=lambda r: {**r, "rendered_frames": -r["elapsed_ms"]})
        for s in an.sessions:
            v = an.session_row(s)["rendered_fps_min"]
            self.assertTrue(v is None or v >= 0, v)


C35 = [(-1, "gc_session", {"gc_mode": True, "gc_states": "hotkey"}),
       (94, "client_stall", {"age_ms": 519}), (94.0, "desync_pause", {"trigger": "client_stall"}),
       (101, "input_release", {"via": "stall_end", "method": "state", "why": "long"}),
       (102.2, "resumed", {"via": "stall_end", "from_state": "PAUSED_RECOVERING"})]


class DolphinSplit(unittest.TestCase):
    def test_c35_shaped_hold_is_split(self):
        an = analysis(C35)
        self.assertEqual(an.sessions[0]["core"], "dolphin")
        r = first_row(an)
        self.assertEqual((r["hitch_s"], r["hold_resume_s"], r["hitch_s_bar"]), (4, 1, 3))   # the R at 100 apart

    def test_the_same_rows_on_another_core_are_today(self):
        an = analysis(C35[1:])                                                # no gc_session row: the fixture's PS1
        self.assertNotEqual(an.sessions[0]["core"], "dolphin")
        r = first_row(an)
        self.assertEqual((r["hitch_s"], r["hold_resume_s"], r["hitch_s_bar"]), (4, 0, 4))   # B66's window only

    def test_dolphin_without_a_desync_pause_is_today(self):
        an = analysis([C35[0], C35[4]])
        r = first_row(an)
        self.assertEqual(r["hold_resume_s"], 0)


# --- (d): gc_frames ------------------------------------------------------------------------------------------------

def presents(per_second: list[int]) -> list[float]:
    """Render intervals giving `n` presents in each second."""
    out = []
    for n in per_second:
        out += [1000.0 / n] * n if n else [1000.0]
    return out


class Frames(unittest.TestCase):
    def test_twenty_is_a_class(self):
        r = gf.render(presents([60] * 12 + [19, 21, 20, 19, 21, 20, 21, 19, 20, 21, 20, 19] + [60] * 12))
        rates = [s["rate"] for s in r["segments"]]
        self.assertEqual(rates, [60, 20, 60])
        mid = r["segments"][1]
        self.assertEqual((mid["hitch_bar_lt"], mid["hitch_seconds"]), (round(20 * gf.HITCH_SHARE, 2), 0))
        self.assertEqual(r["hitch_seconds_total"], 0)

    def test_a_hitch_second_stays_in_its_run(self):
        # a 30-fps run with one 23-present second: still one 30 segment and that second a hitch (the cut is 30 / 60)
        r = gf.render(presents([30] * 12 + [23] + [30] * 12))
        self.assertEqual([(s["rate"], s["hitch_seconds"]) for s in r["segments"]], [(30, 1)])

    def test_a_segment_by_its_own_median(self):
        self.assertEqual(gf.own_rate([24, 26, 21, 21, 22], 30), 20)          # seconds near 25 / median 22 -> 20
        self.assertEqual(gf.own_rate([], 30), 30)

    def test_vis_beside_a_render_segment(self):
        vb = [16.68] * (60 * 30)
        r = gf.render(presents([60] * 10 + [20] * 10 + [60] * 10), vblank_ms=vb)
        for s in r["segments"]:
            self.assertAlmostEqual(s["vi_per_s"], 60.0, delta=0.5)
            self.assertEqual(s["vi_p99_ms"], 16.68)
        self.assertNotIn("vi_per_s", gf.render(presents([60] * 10))["segments"][0])   # no --vblank: today's keys

    def test_sixty_only_is_today(self):
        r = gf.render(presents([60] * 20))
        self.assertEqual([(s["rate"], s["hitch_seconds"]) for s in r["segments"]], [(60, 0)])


# --- (e): SDL off the virtual pads -----------------------------------------------------------------------------------

class SdlPads(unittest.TestCase):
    def test_the_hints(self):
        env = gc.launch_env({"PATH": "/usr/bin"})
        for hint in gc.SDL_HINTS:
            self.assertEqual(env[hint], "0x1209/0x5048")
        self.assertEqual(env["PATH"], "/usr/bin")

    def test_an_existing_value_kept(self):
        env = gc.launch_env({"SDL_JOYSTICK_BLACKLIST_DEVICES": "0x0001/0x0002"})
        self.assertEqual(env["SDL_JOYSTICK_BLACKLIST_DEVICES"], "0x0001/0x0002,0x1209/0x5048")
        env = gc.launch_env({"SDL_JOYSTICK_BLACKLIST_DEVICES": "0x1209/0x5048"})
        self.assertEqual(env["SDL_JOYSTICK_BLACKLIST_DEVICES"], "0x1209/0x5048")   # not twice

    def test_the_knob_is_today(self):
        base = {"PATH": "/usr/bin", "PRIVYHUB_GC_SDL_PADS": "1"}
        self.assertEqual(gc.launch_env(base), base)

    def test_the_ids_are_the_virtual_pads(self):
        import native_session_io as nsi
        cls = next(v for v in vars(nsi).values() if isinstance(v, type) and hasattr(v, "LINUX_VENDOR_ID"))
        self.assertEqual(gc.PAD_USB_ID, f"0x{cls.LINUX_VENDOR_ID:04x}/0x{cls.LINUX_PRODUCT_ID:04x}")

    def test_the_launch_passes_it(self):
        src = (ROOT / "companion/games/emulator_manager.py").read_text()
        i = src.index("def _launch_dolphin(")
        self.assertIn("env=_gc.launch_env(os.environ)", src[i:i + 6000])
        self.assertNotIn("env=dict(os.environ)", src[i:i + 6000])
        self.assertIn('Device = evdev/0/PrivyHub Virtual Gamepad P1', gc.gcpad_ini())      # the ini unchanged


class SdlLaunch(tg.Rig):
    def test_a_launch_builds_the_env(self):
        seen = []
        real = gc.launch_env
        with mock.patch.object(gc, "launch_env", side_effect=lambda e=None: (seen.append(True), real(e))[1]):
            self.launch()
        self.assertEqual(seen, [True])


# --- (f): one save per stall, none during a check --------------------------------------------------------------------

class CheckWindow(tg.Rig):
    def cores(self, **kw):
        m, r = self.launch(**kw)
        rec = tg.Rec()
        c = rewind_cores.Cores("state", m, rec, clock=self.fake.clock, wall=lambda: 1000.0 + self.fake.t,
                               threaded=False)
        spawned = []
        c._spawn = spawned.append
        return m, rec, c, spawned

    def first_hold(self):
        m, rec, c, spawned = self.cores()
        c.save(10.0, 10.4, "stall")
        m.pause()
        c.release(tg.rw(), rec, {"via": "client_ready_stall"}, {"onset": 10.0, "paused_at": 11.0})
        self.assertEqual(self.fake.loaded, [9])
        self.assertFalse(c.gc_check_idle.is_set())                           # the check is pending
        m.resume()
        return m, rec, c, spawned

    def test_a_stall_during_the_check_is_not_re_saved(self):
        m, rec, c, spawned = self.first_hold()
        keys_before = list(self.fake.keys)
        saves_before = len(rec.of("state_saved"))
        t = threading.Thread(target=lambda: c.save(12.0, 12.2, "stall"))   # the second stall, 0.23 s after
        t.start()
        time.sleep(0.2)
        self.assertTrue(t.is_alive())                                         # awaiting the check's result
        spawned[0]()                                                          # the check runs and ends
        t.join(5)
        self.assertFalse(t.is_alive())
        self.assertEqual(self.fake.keys, keys_before)                         # no Shift+F9
        self.assertEqual(len(rec.of("state_saved")), saves_before)
        skip = rec.of("state_save_skipped")[-1]
        self.assertEqual((skip["reason"], skip["core"], skip["slot"], skip["kind"]),
                         (rewind_cores.GC_CHECK_SKIP, "dolphin", 9, "stall"))
        events = [r["event"] for r in rec.rows]
        self.assertLess(events.index("gc_states"), events.index("state_save_skipped"))   # the verdict first
        # that stall's release: no scratch state -> a resume in place, no second load
        m.pause()
        c.release(tg.rw(), rec, {"via": "client_ready_stall"}, {"onset": 12.0, "paused_at": 13.0})
        self.assertEqual(rec.of("rewind_skipped")[-1]["reason"], "no scratch state for this pause")
        self.assertEqual(self.fake.loaded, [9])

    def test_after_the_check_a_stall_saves_as_today(self):
        m, rec, c, spawned = self.first_hold()
        spawned[0]()
        self.assertTrue(c.gc_check_idle.is_set())
        c.save(20.0, 20.4, "stall")
        self.assertEqual(self.fake.keys[-1], "Shift_L+F9")
        self.assertEqual(rec.of("state_saved")[-1]["slot"], 9)

    def test_a_check_that_raises_still_ends(self):
        m, rec, c, spawned = self.first_hold()
        with mock.patch.object(c, "_verify_gc_check", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                spawned[0]()
        self.assertTrue(c.gc_check_idle.is_set())


# --- (g): state_reply rows -------------------------------------------------------------------------------------------

def plugin(save=None, load=None):
    import importlib.util
    spec = importlib.util.spec_from_file_location("g72", str(ROOT / "companion/plugins/games.py"))
    G = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(G)
    rows = []
    p = object.__new__(G.GamesPlugin)
    p._recovery = types.SimpleNamespace(_log=lambda e, **k: rows.append({"event": e, **k}))
    p._emulator = types.SimpleNamespace(save_state=save, load_state=load, record_save_state_probe_event=lambda *a, **k: None,
                                        disc_after_load=lambda payload: payload, _n64_continue_event=None)
    return p, rows


SAVE_REPLY = {"ok": True, "kind": "game_session", "action": "save_state", "slot": 1, "accepted": True, "confirmed": True,
              "replaced_existing": False, "overwrite_requires_confirmation": False,
              "control": "retroarch_nightly_save_state_slot", "retroarch_response": "SAVE_STATE_SLOT 1",
              "slot_detail": {"label": "Slot 1", "state_file": "data/games/retroarch/states/Made Up Title.state1"},
              "state_file": "data/games/retroarch/states/Made Up Title.state1", "paused": True,
              "game": {"id": "game_ps1_x", "title": "Made Up Title"}}


class StateReply(unittest.TestCase):
    def test_a_save_reply_row(self):
        p, rows = plugin(save=lambda slot, replace=False: dict(SAVE_REPLY))
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PRIVYHUB_STATE_REPLY_ROWS", None)
            p.handle_post("save-state", "slot=1")
        r = [r for r in rows if r["event"] == "state_reply"]
        self.assertEqual(len(r), 1)
        r = r[0]
        self.assertEqual((r["action"], r["slot"], r["ok"], r["accepted"], r["confirmed"], r["control"], r["paused"]),
                         ("save-state", 1, True, True, True, "retroarch_nightly_save_state_slot", True))
        text = json.dumps(r)
        for leak in ("Made Up Title", "state_file", "slot_detail", "data/games", "game_ps1_x", "retroarch_response"):
            self.assertNotIn(leak, text)

    def test_a_load_failure_row(self):
        def load(slot):
            raise em.EmulatorError("RetroArch exited during startup (code 1). See logs/games/x-game_ps1_y.log")
        p, rows = plugin(load=load)
        with self.assertRaises(RuntimeError):
            p.handle_post("load-state", "slot=2")
        r = [r for r in rows if r["event"] == "state_reply"][0]
        self.assertEqual((r["action"], r["slot"], r["ok"]), ("load-state", 2, False))
        self.assertIn("<path>", r["error"])
        self.assertNotIn("logs/games", r["error"])

    def test_the_knob_is_today(self):
        p, rows = plugin(save=lambda slot, replace=False: dict(SAVE_REPLY))
        with mock.patch.dict(os.environ, {"PRIVYHUB_STATE_REPLY_ROWS": "0"}):
            p.handle_post("save-state", "slot=1")
        self.assertEqual([r for r in rows if r["event"] == "state_reply"], [])

    def test_a_gamecube_load_reply(self):
        p, rows = plugin(load=lambda slot: {"action": "load_state", "slot": slot, "accepted": True, "confirmed": True,
                                            "verification": "picture", "paused": True, "control": "dolphin_hotkey_load_state",
                                            "hotkey": "F1"})
        p.handle_post("load-state", "slot=1")
        r = [r for r in rows if r["event"] == "state_reply"][0]
        self.assertEqual((r["verification"], r["hotkey"], r["control"]), ("picture", "F1", "dolphin_hotkey_load_state"))


if __name__ == "__main__":
    unittest.main()
