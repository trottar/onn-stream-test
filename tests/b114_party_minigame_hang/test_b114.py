#!/usr/bin/env python3
"""B114 (host): the party mini game's start can no longer hang the companion — through the real HTTP server on loopback.

PP-H3's second mini game hung the companion: the start held the manager's lock across the stream switch, whose end
(the live bitrate controller's note) waited on the bitrate lock, held by a client-health report waiting on the
manager's lock. This test runs **two mini games back to back through a live (stubbed) stream** with the hub's adopted
lines that matter on (the live bitrate controller, the link recovery's stall worker and stall owner, the fast restart)
and the onn's traffic from other threads (client-health every 0.1 s, heartbeats, stall datagrams; `status`,
`native-stream-status` and `party-minigame-result` every 0.1 s; Home and RESUME during the first match). The stream
stub has its own lock and its capture follows one process (that process gone → the stream down), as the real one.
Then, after the fix: END from the onn during starting / playing / a hand-over each way / a stuck start, and a start
stuck in the watch's start and in the stream switch given up by the hub. A start that never reaches `playing` within
25 s (or a match that never ends within 40 s) makes the child write every thread's stack and leave: **the suite fails,
it does not hang.** `B114_AGAINST=<rev>` runs the same scenario on that revision's companion (the record's HEAD run).
Each flag absent → HEAD's answers byte for byte. Temp dirs removed.

    python3 -m unittest discover -s tests/b114_party_minigame_hang -v
"""
from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("art_systems", "b99_h7_live_read", "b102_h7_endscreen", "b103_h7_minigame", "b108_party_launch"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402
import test_b103 as b103  # noqa: E402
import test_b108 as b108  # noqa: E402

BASELINE = "8fa398c8"                    # queue AQ's baseline (PP-H3 committed): the companion before B114
ADOPTED = {"PRIVYHUB_ADAPTIVE_BITRATE_MODE": "live", "PRIVYHUB_LINK_RECOVERY": "1", "PRIVYHUB_RESTART_FAST": "1",
           "PRIVYHUB_RESTART_FAST_UNLOCK": "1"}
BOTH = {**b85.FLAGS, **ADOPTED, "PRIVYHUB_PARTY": "1", "PRIVYHUB_H7": "1"}
SCENARIO = (HERE / "b114_scenario.py").read_text()
WITHIN_S = 2.0
CLOCK = re.compile(r'"(since_ms|elapsed_seconds)": [0-9.]+')   # the recovery's clock reading: not the code's answer


def code_of(rev: str) -> Path | None:
    try:
        repo = os.environ.get("H7_GIT_REPO") or str(ROOT)
        data = subprocess.run(["git", "-C", repo, "archive", rev, "companion"], capture_output=True, timeout=120,
                              check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    d = Path(tempfile.mkdtemp(prefix="b114_head_"))
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        tf.extractall(d, filter="data")
    return d


def child() -> str:
    return b103.CHILD.split('out = {"steps": {}}')[0] + SCENARIO


def run(root: Path, env: dict, ids: dict, mode: str, timeout: int = 600) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="b114_fx_"))
    fx = b108.fixtures(work)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules"),
                      "PRIVYHUB_PARTY_CONFIG": str(work / "party.json"), "B108_BOARD_DIR": fx["board_dir"]})
    (root / "tools").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools" / "h7_endscreen.py", root / "tools" / "h7_endscreen.py")
    frames, spec_dir, js = b103.fixtures(work)
    try:
        r = subprocess.run([sys.executable, "-I", "-B", "-c", child(), str(root),
                            json.dumps({"id": ids[b85.PS1_TITLE], "mode": mode, "p1": b99.P1, "p2": b99.P2,
                                        "frames": str(frames), "spec_dir": str(spec_dir), "start_s": 0.6, **fx})],
                           cwd=root, env=child_env, capture_output=True, text=True, timeout=timeout)
    finally:
        # the stand-in board, if a hung run left it, is ended with the child (it exits by itself after 120 s)
        try:
            pid = int((Path(fx["board_dir"]) / "pid").read_text())
            os.kill(pid, 15)
        except (OSError, ValueError):
            pass
        shutil.rmtree(work, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-4000:]
    if os.environ.get("B114_OUT"):                       # the record keeps the child's own answer
        with open(os.environ["B114_OUT"], "a", encoding="utf-8") as fh:
            fh.write(r.stdout.strip().splitlines()[-1] + "\n")
    return json.loads(r.stdout.strip().splitlines()[-1])


class NoHang(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        against = os.environ.get("B114_AGAINST")
        code = code_of(against) if against else None
        if against and code is None:
            raise unittest.SkipTest("git is absent")
        root, cls.ids = b99.tree(code)
        cls.out = run(root, BOTH, cls.ids, "all")
        cls.s = cls.out["steps"]

    def test_0_two_mini_games_back_to_back_not_hung(self):
        self.assertTrue(self.s["abr_live_same"] and self.s["stall_worker"])   # the adopted lines are live in the test
        self.assertIsNone(self.out["hung"], json.dumps({k: self.out.get(k) for k in
                                                        ("hung", "mg_thread", "waiting_on_emu_lock")}))
        for tag, cls_, scores in (("m1", "end_P2", [0, 1]), ("m2", "end_P1", [1, 0])):
            r = self.s[tag]
            self.assertEqual((r["state"], r["class"], r["scores"]), ("ended", cls_, scores), (tag, r))
            self.assertTrue(self.s[tag + "_closed"], tag)
            self.assertTrue(self.s[tag + "_end_again"], tag)
            self.assertTrue(self.s[tag + "_title_gone"], tag)
            self.assertIsNone(self.s[tag + "_route_after"], tag)
            self.assertEqual(self.s[tag + "_status_kind"], "godot", tag)
            self.assertTrue(self.s[tag + "_board_picture_back"], tag)

    def test_1_every_route_within_2_s(self):
        """While a mini game is on (started and not yet finished); the calls with none on are today's code."""
        lat = self.out["lat"]
        for kind in ("status", "result", "ns_status", "home", "board_end", "end_onn", "start"):
            self.assertIn(kind, lat)
            self.assertLess(lat[kind]["max"], WITHIN_S, (kind, lat[kind], [x for x in self.out["slow"] if x[4]][:8]))
        self.assertGreater(lat["status"]["n"], 100)
        self.assertGreater(lat["result"]["n"], 100)

    def test_2_no_lock_of_the_manager_inside_a_stream_start(self):
        self.assertTrue(self.out["emu_lock_in_start"])
        self.assertEqual(set(self.out["emu_lock_in_start"]), {False}, self.out["emu_lock_in_start"])

    def test_3_home_and_resume_taken_at_once_and_acted_on_in_order(self):
        self.assertEqual(self.s["m1_home"], {"code": 200, "taken": "home"})
        self.assertIs(self.s["m1_title_paused_after_home"], True)             # Home paused the title
        self.assertEqual(self.s["m1_resume"], {"start": 200, "start_active": True, "ready": 200, "released": True})
        self.assertIs(self.s["m1_title_running_after_resume"], True)
        steps = self.s["m1_rows"]
        taken = [i for i, x in enumerate(steps) if x == "minigame_taken"]
        self.assertGreaterEqual(len(taken), 3)                                 # home, resume start, resume ready

    def test_4_end_from_the_onn_in_every_phase(self):
        self._end_cases(("starting", "playing", "handover_in", "stuck"))

    def test_4b_end_from_the_onn_during_the_hand_over_back(self):
        """B115's way back (the switch before the title's stop) makes the hand-over back a step of the mini game."""
        self._end_cases(("handover_back",))

    def _end_cases(self, phases):
        for when in phases:
            tag = "end_" + when
            self.assertEqual(self.s[tag + "_stop"], {"code": 200, "taken": "end"}, tag)
            self.assertTrue(self.s[tag + "_gone"], (tag, self.s[tag + "_rows"]))   # the title and the board gone
            self.assertTrue(self.s[tag + "_closed"], tag)
            self.assertIn("F10", self.s[tag + "_keys"], tag)                     # the board quit by its own key
            self.assertTrue(self.s[tag + "_active_after"], tag)
            self.assertIsNone(self.s[tag + "_route_after"], tag)
            if when != "handover_back":
                self.assertIn("ended from the onn", self.s[tag + "_why"] or "", tag)

    def test_5_a_stuck_start_given_up_by_the_hub(self):
        self.assertEqual(self.s["stuck_watch"]["state"], "given_up")
        self.assertIn("did not start within 3 s", self.s["stuck_watch"]["why"])
        self.assertEqual(self.s["stuck_switch"]["state"], "given_up")
        self.assertIn("switch did not finish within 2 s", self.s["stuck_switch"]["why"])
        for tag in ("stuck_watch", "stuck_switch"):
            self.assertTrue(self.s[tag + "_closed"], tag)
            self.assertTrue(self.s[tag + "_title_gone"], tag)
            self.assertTrue(self.s[tag + "_board_kind"], tag)                   # the board's session back
            self.assertTrue(self.s[tag + "_board_alive"], tag)
            self.assertIsNone(self.s[tag + "_route_after"], tag)
            self.assertTrue(self.s[tag + "_picture_back"], tag)                 # the stream on the board again


class FlagsAbsentAreToday(unittest.TestCase):
    def test_each_flag_absent(self):
        code = code_of(BASELINE)
        if code is None:
            self.skipTest("git is absent")
        for env in ({**b85.FLAGS, **ADOPTED, "PRIVYHUB_PARTY": "1"}, {**b85.FLAGS, **ADOPTED, "PRIVYHUB_H7": "1"},
                    {**b85.FLAGS, **ADOPTED}, {**b85.FLAGS, **ADOPTED, "PRIVYHUB_PARTY": "1", "PRIVYHUB_H7": "0"}):
            root, ids = b99.tree(code)
            base = run(root, env, ids, "today")
            root2, ids2 = b99.tree()
            mine = run(root2, env, ids2, "today")
            for k in ("list", "start", "result", "end", "status_idle", "home_idle", "stop_idle"):
                self.assertEqual((mine["steps"][k]["code"], CLOCK.sub("<ms>", mine["steps"][k]["raw"])),
                                 (base["steps"][k]["code"], CLOCK.sub("<ms>", base["steps"][k]["raw"])), (env, k))
            self.assertIn("Unknown Games plugin", base["steps"]["start"]["body"]["error"])


if __name__ == "__main__":
    unittest.main()
