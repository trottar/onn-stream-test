#!/usr/bin/env python3
"""B127 (host): the mini games under each title's cheat setup — through the real HTTP server on loopback, behind
PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

B114's harness (B108's stand-in board, B101 / B103's fake RetroArch, B103's fake pictures, the stream stub with its own
lock, the onn's client thread and status / result / native-stream-status every 0.1 s) with the hub's adopted lines on;
B124's two titles (the PS1 one with B103's two-player spec, the N64 one with B122's version-3 spec). **The fake
RetroArch reads its states folder from the session config the launch wrote** (`savestate_directory` + the core's
folder: where RetroArch itself would look); RetroArch's network side of the cheat toggles is stubbed as B83's harness
does. The setups are made as the user made them — the onn's Extras launch from loopback (B85's made-up `.cht`: the PS1
pick with its required code, the N64 split cheat with its required code) — and read back through `cheat-profiles`.

Checked: `h7-start` under a setup loads the setup's own begin (`<game id>.<prefix>.state`, else the normal one) through
the setup's own `states/<core>/<stem>.state8`, the scratch removed; N64 refused unless PAUSED (nothing sent); a sidecar
whose setup is gone / not on the hub / whose indexes changed → 400 plainly, nothing launched, the board still the
session, no new setup folder; a malformed `cheat` not listed; **two back to back** — two-player under the PS1 setup,
four-player under the N64 setup with Home / RESUME — the launch's query the onn's Extras query, the session's
`profile_id` the setup's, the begin from the setup's folder, the right class / places / scores, every hand-over
planned, every route < 2 s while a mini game is on; **every file of both setups and the normal states byte-equal; no
`.state8`**. Today: each flag absent → HEAD's answers through the real routes (the cheat launch, `cheat-profiles`, the
H7 / party routes, status, stop; numbers of 4+ digits, decimals and times masked); **a sidecar without `cheat`** →
B124's four-player run on HEAD's code and mine: the same rows and answers. Temp dirs removed.

    python3 -m unittest discover -s tests/b127_party_cheat_setups -v
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b123_h7_n64_start", "b115_party_handovers", "b124_party_four_seats"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b114 as b114  # noqa: E402  (harnesses; their tests are not collected here)
import test_b115 as b115  # noqa: E402
import test_b124 as b124  # noqa: E402

HEAD = "d9e95e66"                     # queue AS's baseline (H7-C2 committed): the companion before B127
GONE = "the cheat setup this mini game names is not on the hub (or its cheats changed): nothing was launched"
MASK = re.compile(r'(?<![A-Za-z_])\d+\.\d+|\b\d{4,}\b|\d{4}-\d\d-\d\dT[0-9:.]+Z?')


def extra(work: Path, frames: Path) -> dict:
    more = b124.extra(work, frames)
    return more


class UnderSetups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.update(ids)
        cls.out = b114.run(root, b114.BOTH, ids, "cheat", extra=extra)
        cls.s = cls.out["steps"]

    def test_0_the_setups_made_as_the_user_made_them(self):
        self.assertIsNone(self.out["hung"], self.out.get("mg_thread"))
        for key, enabled in (("ps1", [0, 1]), ("n64", [2, 5, 6])):          # B85: the picks + parts + required
            self.assertEqual(self.s[f"c_make_{key}"]["code"], 200, self.s[f"c_make_{key}"])
            self.assertEqual(self.s[f"c_profiles_{key}"], 1)
            self.assertEqual(self.s[f"c_setup_{key}"], {"source_index": 0, "enabled": enabled, "same_id_as_launch": True})
        self.assertGreaterEqual(self.s["c_files_hashed"], 9)

    def test_1_h7_start_loads_the_setups_begin_from_the_setups_folder(self):
        s = self.s
        self.assertTrue(s["c_ps1_session"])
        self.assertEqual((s["c_h7_ps1_normal"].get("watch"), s["c_h7_ps1_normal"].get("begin")), ("started", "normal"))
        self.assertEqual((s["c_h7_ps1_setup"].get("watch"), s["c_h7_ps1_setup"].get("loaded"),
                          s["c_h7_ps1_setup"].get("begin")), ("started", True, "setup"))
        self.assertEqual(s["c_h7_ps1_loaded_from"], [s["c_h7_ps1_want"]])
        self.assertEqual(s["c_h7_ps1_mem"], [7, 9])                         # the setup's begin, not the normal one
        self.assertEqual(s["c_h7_ps1_scratch"], [])

    def test_2_n64_only_while_paused(self):
        s = self.s
        r = s["c_h7_n64_running"]
        self.assertEqual(r["code"], 400)
        self.assertIn("not paused", r["body"]["error"])
        self.assertEqual(s["c_h7_n64_running_sent"], [])
        self.assertEqual((s["c_h7_n64_paused"].get("loaded"), s["c_h7_n64_paused"].get("begin")), (True, "setup"))
        self.assertEqual(s["c_h7_n64_loaded_from"], [s["c_h7_n64_want"]])
        self.assertEqual(s["c_h7_n64_mem"], [3, 4])
        self.assertEqual(s["c_h7_n64_scratch"], [])

    def test_3_a_setup_not_on_the_hub_refused_plainly_nothing_launched(self):
        for tag, check in (("c_ref_no_profile", "no_profile"), ("c_ref_folder_gone", "no_profile"),
                           ("c_ref_indexes_changed", "profile_differs")):
            r = self.s[tag]
            self.assertTrue(r["listed"], tag)
            self.assertEqual((r["code"], r["error"]), (400, GONE), (tag, r))
            self.assertEqual(r["popens"], 0, tag)                             # no RetroArch started
            self.assertEqual(r["rows"], [{"step": "minigame_refused", "why": "the cheat setup is not on the hub",
                                          "check": check}], tag)
            self.assertEqual((r["board_session"], r["mg"]), ("godot", "none"), tag)
        self.assertTrue(self.s["c_dirs_after_refusals"])                      # no new setup folder
        self.assertEqual(self.s["c_malformed_listed"], [])

    def test_4_two_back_to_back_under_the_setups(self):
        s = self.s
        self.assertEqual(s["c_list"], [2, 4])
        for tag in ("ca2", "cb4"):
            self.assertEqual(s[tag + "_launch_queries"], [s[tag + "_want_query"]], tag)   # the onn's Extras query
            self.assertIn("cheat_source=0&cheat_indexes=", s[tag + "_want_query"])
            self.assertEqual(s[tag + "_launch_row"], {"pid_owned": True, "cheat": True, "profile_matches": True})
            self.assertTrue(s[tag + "_session_profile"], tag)
            self.assertTrue(s[tag + "_status_profile"], tag)
            self.assertEqual(s[tag + "_loaded_from"], [s[tag + "_want_folder"]], tag)
            self.assertTrue(s[tag + "_closed"] and s[tag + "_title_gone"], tag)
            self.assertIsNone(s[tag + "_route_after"], tag)
        self.assertEqual(s["ca2_mem"], [7, 9])
        self.assertEqual(s["cb4_mem"], [3, 4])
        self.assertEqual(s["ca2_route_during"], {"1": 0, "0": 1})
        self.assertEqual(s["cb4_route_during"], {"2": 0, "0": 1, "3": 2, "1": 3})
        a, b = s["ca2"], s["cb4"]
        self.assertEqual((a["state"], a["class"], a["scores"]), ("ended", "end_P2", [0, 1]))
        self.assertEqual((b["state"], b["class"], b["places"], b["scores"], b["seats"]),
                         ("ended", "end", [2, 1, 4, 3], [3, 4, 1, 2], [3, 1, 4, 2]))
        self.assertEqual(s["cb4_resume_ports"], {"players": 4, "ports": 4})
        self.assertTrue(s["c_applied"] and all(s["c_applied"]))

    def test_5_every_hand_over_planned_every_route_within_2_s(self):
        for tag in ("ca2", "cb4"):
            sw = [(x["window"], x["switched"], x.get("planned")) for x in self.s[tag + "_switches"]]
            self.assertEqual(sw, [("minigame", True, True), ("board", True, True)], tag)
            acts = [x for x in self.s[tag + "_rec"] if x in b115.RECOVERY_ACTS]
            self.assertEqual(acts, [], (tag, self.s[tag + "_rec"]))
            self.assertEqual(self.s[tag + "_keys_all"], [], tag)
            self.assertTrue(self.s[tag + "_board_picture_back"], tag)
        events = [e[0] for e in self.s["abr_all"]]
        self.assertNotIn("escalation_armed", events)
        self.assertNotIn("transition", events)
        lat = self.out["lat"]
        for kind in ("status", "result", "ns_status", "home", "board_end", "start"):
            self.assertLess(lat[kind]["max"], b114.WITHIN_S, (kind, lat[kind]))

    def test_6_the_users_files_byte_equal_no_scratch_nothing_running(self):
        self.assertTrue(self.s["c_files_same"], self.s["c_files_diff"])
        self.assertEqual(self.s["c_scratch_end"], [])
        self.assertEqual(self.s["c_running_after"], [False, None])


def masked(step: dict) -> tuple:
    return step["code"], MASK.sub("<n>", b114.CLOCK.sub("<ms>", step["raw"]))


class Today(unittest.TestCase):
    def test_each_flag_absent_is_heads(self):
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        for env in ({**b114.b85.FLAGS, **b114.ADOPTED}, {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_PARTY": "1"},
                    {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_H7": "1"}):
            root, ids = b114.b99.tree(code)
            base = b114.run(root, env, ids, "cheat_today")["steps"]
            root2, ids2 = b114.b99.tree()
            mine = b114.run(root2, env, ids2, "cheat_today")["steps"]
            routes = [k for k in base if isinstance(base[k], dict) and "code" in base[k]]
            self.assertEqual(len(routes), 10)
            for k in routes:
                self.assertEqual(masked(mine[k]), masked(base[k]), (sorted(env), k))
            self.assertEqual(base["launch_cheat"]["code"], 200)
            self.assertEqual(base["profiles"]["code"], 200)

    def test_a_sidecar_without_cheat_is_heads(self):
        """B124's four-player run (no `cheat` anywhere) on HEAD's companion and on mine: the same rows and answers."""
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        outs = []
        for c in (code, None):
            root, ids = b114.b99.tree(c)
            b124.IDS.clear()
            b124.IDS.update(ids)
            outs.append(b114.run(root, b114.BOTH, ids, "four", extra=b124.extra)["steps"])
        base, mine = outs
        for tag in ("a2", "b4", "c2", "d4"):
            keep = ("state", "class", "scores", "places", "seats", "recognised", "why", "closed")
            self.assertEqual({k: mine[tag].get(k) for k in keep}, {k: base[tag].get(k) for k in keep}, tag)
            # the switch-window rows land 3 s after each switch (B115), after B114's row snapshot or before it as the
            # machine's load has it: compared from the waited-for list below, not from the snapshot
            late = "minigame_switch_window"
            self.assertEqual([r for r in mine[tag + "_rows"] if r != late], [r for r in base[tag + "_rows"] if r != late],
                             tag)
            self.assertEqual([sorted(w) for w in mine[tag + "_windows"]], [sorted(w) for w in base[tag + "_windows"]], tag)
            self.assertEqual(mine[tag + "_route_during"], base[tag + "_route_during"], tag)
            self.assertEqual([(x["window"], x["switched"], x.get("planned")) for x in mine[tag + "_switches"]],
                             [(x["window"], x["switched"], x.get("planned")) for x in base[tag + "_switches"]], tag)
        self.assertEqual(mine["four_list"], base["four_list"])
        for k in ("refuse_4p_two_seats", "refuse_2p_four_seats"):
            self.assertEqual((mine[k]["code"], mine[k]["raw"]), (base[k]["code"], base[k]["raw"]), k)


if __name__ == "__main__":
    unittest.main()
