#!/usr/bin/env python3
"""B137 (host): nothing a player presses reaches a held title before the go — through the real HTTP server on loopback,
behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

B114's scenario, its `nopress` mode: B108's stand-in board; B101's fake RetroArch taught `FRAMEADVANCE` and a title —
running, it reads the virtual pads every 1/60 s and **leaves its start screen when any button but neutral reaches it**;
a frame advance runs one frame; its load puts the begin back (PS1-shaped: shown at the next frame; N64-shaped: the load
runs a frame and reads the pads); notices cover its picture after each load; its own log. The watcher's picture follows
the fake (RetroArch's "Paused." drawn in its corner while paused); the virtual pads' writes recorded. **A confirm press
from each player through the bridge every 0.2 s from the start call to the go.**

Checked: T88-shaped → `ready`, the fake never resumed from the launch's answer to the go, every frame it ran then saw
neutral pads, presses sent inside the mute and nothing but neutral written there, `minigame_frame_advance` (2 frames,
the mute's ms), **no second load at the go** (no `minigame_reloaded`), `playing` on the begin, scored as today; every
paused read had the label's corner masked, none after the go; three practices with presses throughout (each way back
paused while still routed, then the same checks to the next go), then a real go scored; T89-shaped (N64, four pads, a
remembered go); never the start → given up, no route, no switch, never resumed; the board's end, the onn's Home, a
second start and the onn's END **during the mute** → the mute released, the title gone; every route < 2 s. **HEAD's
code (B133's order) with the same presses → "not recognised"; with none → ready.** The flags absent → HEAD's answers
byte for byte. Temp dirs removed.

    python3 -m unittest discover -s tests/b137_party_no_press -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b127_party_cheat_setups", "b115_party_handovers",
            "b123_h7_n64_start", "b133_party_prepare_go"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b114 as b114  # noqa: E402  (harnesses; their tests are not collected here)
import test_b124 as b124  # noqa: E402

HEAD = "498ff031"                       # queue AV's baseline: the companion before B137 (B133's order)
NOT_RECOGNISED = "the title's start screen was not recognised"


def _run(code=None, mode="nopress"):
    root, ids = b114.b99.tree(code)
    b124.IDS.clear()
    b124.IDS.update(ids)
    return b114.run(root, b114.BOTH, ids, mode, extra=b124.extra)


class NoPressBeforeTheGo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = _run()
        cls.s = cls.out["steps"]

    def _no_press_reached(self, seg, tag, advances=2):
        self.assertTrue(seg.get("paused_from"), (tag, seg))
        self.assertEqual(seg["resumes"], 0, (tag, seg))                     # never resumed before the go
        self.assertEqual(seg["frames_with_a_button"], 0, (tag, seg))        # every frame it ran saw neutral pads
        self.assertEqual(seg["left_start"], 0, (tag, seg))
        self.assertEqual(seg["loads"], 1, (tag, seg))
        self.assertEqual(seg["advances"], advances, (tag, seg))      # B140: as many as the window needed

    def test_0_t88_shaped_ready_with_presses_never_resumed(self):
        s = self.s
        self.assertIsNone(self.out["hung"])
        self.assertEqual(s["n1_ready"], {"state": "starting", "phase": "ready", "recognised": True, "why": None})
        self._no_press_reached(s["n1_segment"], "n1")
        self.assertGreaterEqual(s["n1_segment"]["frames"], 2)              # the advanced frames ran
        for w in s["n1_mute"]:
            self.assertGreaterEqual(w["presses_sent"], 1, w)                # presses were sent inside the mute ...
            self.assertEqual(w["buttons_written"], 0, w)                    # ... and none reached a pad
        self.assertFalse(s["n1_mute_after"])

    def test_1_the_go_no_second_load_playing_on_the_begin(self):
        s = self.s
        self.assertEqual(s["n1_go"], {"ok": True, "go": "taken", "phase": "ready", "practice": False})
        self.assertEqual(s["n1_playing"]["state"], "playing")
        self.assertEqual(s["n1_on_the_begin"], {"left_start_at_first_frame": False, "loads_after_go": 0})
        self.assertEqual(s["n1_rows"][:9], ["minigame_start", "minigame_launch", "minigame_watch",
                                            "minigame_frame_advance", "minigame_ready", "minigame_go",
                                            "minigame_route", "minigame_stream", "minigame_playing"])
        self.assertNotIn("minigame_reloaded", s["n1_rows"])
        fa = [r for r in s["n1_row_fields"] if r["step"] == "minigame_frame_advance"]
        self.assertEqual(len(fa), 1)
        self.assertEqual((fa[0]["frames"], fa[0]["paused"]), (2, True))
        self.assertGreater(fa[0]["mute_ms"], 300.0)                         # 2 x 0.15 s (slowed in the test) + the load
        self.assertLess(fa[0]["mute_ms"], 1500.0)
        self.assertEqual(s["n1_route_playing"], {"0": 0, "1": 1})
        self.assertEqual(s["n1"], {"state": "ended", "class": "end_P1", "scores": [1, 0], "places": None, "why": None})
        self.assertTrue(s["n1_title_gone"] and s["n1_closed"] and s["n1_board_picture_back"])

    def test_2_the_paused_window_read_as_it_is(self):
        """B139: the party's launch turns RetroArch's text off — no "Paused." on the paused window, so no mask."""
        s = self.s
        self.assertGreater(s["n1_reads_paused"], 0)
        self.assertEqual(s["n1_reads_paused_label"], 0)
        self.assertEqual(s["n1_watching_label_mask"], [None])
        self.assertEqual(s["n1_reads_running_masked"], 0)

    def test_3_three_practices_presses_throughout_the_ways_back(self):
        s = self.s
        self.assertEqual(s["n2_ready0"], {"state": "starting", "phase": "ready"})
        self._no_press_reached(s["n2_first_segment"], "n2 first")
        for n in range(3):
            self.assertEqual(s[f"n2_back{n + 1}"], {"state": "starting", "phase": "ready", "practices": n + 1})
            self._no_press_reached(s["n2_way_back_segments"][n], f"n2 way back {n + 1}")
            for w in s["n2_way_back_mute"][n]:
                self.assertEqual(w["buttons_written"], 0, (n, w))
        self.assertEqual(s["n2_pause_before_unroute"], [True, True, True])   # paused while still routed
        self.assertEqual(s["n2_go"]["go"], "taken")
        self.assertEqual(s["n2_playing"], {"state": "playing", "practice": None})
        self.assertEqual(s["n2_on_the_begin"], {"left_start_at_first_frame": False, "loads_after_go": 0})
        self.assertEqual(s["n2"], {"state": "ended", "class": "end_P2", "scores": [0, 1], "practices": 3})
        self.assertNotIn("minigame_reloaded", s["n2_steps"])
        self.assertEqual(s["n2_steps"].count("minigame_frame_advance"), 4)   # the first preparation + 3 ways back

    def test_4_t89_shaped_four_pads_a_remembered_go(self):
        s = self.s
        self.assertEqual(s["n3_go_early"]["go"], "remembered")
        self.assertEqual(s["n3_ready"]["state"], "playing")
        self._no_press_reached(s["n3_segment"], "n3", advances=0)     # B140: the N64-shaped load shows the begin
        self.assertGreaterEqual(s["n3_segment"]["frames"], 1)              # the load's own frame
        for w in s["n3_mute"]:
            self.assertEqual(w["buttons_written"], 0, w)
        self.assertEqual(s["n3_on_the_begin"], {"left_start_at_first_frame": False, "loads_after_go": 0})
        self.assertEqual(s["n3_route_playing"], {"2": 0, "0": 1, "3": 2, "1": 3})
        self.assertEqual((s["n3"]["state"], s["n3"]["places"], s["n3"]["scores"]), ("ended", [2, 1, 4, 3], [3, 4, 1, 2]))

    def test_5_never_the_start_given_up_never_resumed(self):
        s = self.s
        self.assertEqual(s["n4"]["state"], "given_up")
        self.assertIn("start screen was not recognised", s["n4"]["why"])
        self.assertEqual(s["n4_resumes"], 0)
        self.assertNotIn("minigame_route", s["n4_rows"])
        self.assertEqual(s["n4_switches"], [])
        self.assertTrue(s["n4_title_gone"])

    def test_6_ends_home_and_a_second_start_during_the_mute(self):
        s = self.s
        for tag in ("n5b", "n5h", "n5s", "n5e"):
            self.assertTrue(s[tag + "_mute_seen"], tag)
            self.assertEqual(s[tag + "_call"] if tag != "n5s" else 200, 200, tag)
            self.assertTrue(s[tag]["closed"], (tag, s[tag]))
            self.assertEqual(s[tag]["state"], "given_up", tag)
            self.assertFalse(s[tag + "_mute_after"], tag)                   # the mute never outlives the mini game
            self.assertTrue(s[tag + "_title_gone"], tag)
            self.assertIsNone(s[tag + "_route"], tag)
            self.assertEqual(s[tag + "_switches"], [], tag)
        self.assertEqual(s["n5s_call"], 400)                                # a second start refused
        self.assertEqual(s["n5h"]["why"], "the onn's Home during the preparation")
        self.assertEqual(s["n5h_kind_after"], "godot")
        self.assertEqual(s["n5e"]["why"], "ended from the onn")
        self.assertTrue(s["n5e_board_gone"])

    def test_7_routes_within_2_s_nothing_left(self):
        for kind in ("status", "result", "ns_status", "start", "go", "board_end", "home", "end_onn"):
            self.assertLess(self.out["lat"][kind]["max"], b114.WITHIN_S, kind)
        self.assertEqual(self.s["h_running_at_end"], [False])
        self.assertIsNone(self.s["h_board_at_end"])


class HeadsOrder(unittest.TestCase):
    """The mutation that shows the fault: HEAD's companion (B133: resumed behind the board until the start is read)."""

    def test_the_same_presses_on_heads_code_are_not_recognised(self):
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        s = _run(code, "nopress_head")["steps"]
        self.assertEqual(s["x1_ready"]["state"], "given_up", s.get("x1_ev"))
        self.assertIn(NOT_RECOGNISED, s["x1_ready"]["why"])
        self.assertNotIn("minigame_route", s["x1_rows"])
        # the control: no presses on HEAD's code -> ready, then played as before
        self.assertEqual(s["x0_ready"]["phase"], "ready")
        self.assertEqual(s["x0"]["state"], "ended")


class Today(unittest.TestCase):
    def test_flags_absent_and_no_mini_game_are_heads(self):
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        for env in ({**b114.b85.FLAGS, **b114.ADOPTED}, {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_PARTY": "1"},
                    {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_H7": "1"}):
            root, ids = b114.b99.tree(code)
            base = b114.run(root, env, ids, "today")["steps"]
            root2, ids2 = b114.b99.tree()
            mine = b114.run(root2, env, ids2, "today")["steps"]
            for k in ("list", "start", "result", "end", "go", "status_idle", "home_idle", "stop_idle"):
                self.assertEqual((mine[k]["code"], b114.CLOCK.sub("<ms>", mine[k]["raw"])),
                                 (base[k]["code"], b114.CLOCK.sub("<ms>", base[k]["raw"])), (sorted(env), k))
            self.assertEqual(mine["ports_today"], base["ports_today"], sorted(env))


if __name__ == "__main__":
    unittest.main()
