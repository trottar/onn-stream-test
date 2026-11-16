#!/usr/bin/env python3
"""B105 (host): the watcher's gaps behind PRIVYHUB_H7=1, through the companion's real HTTP server on loopback.

B103's harness reused (a child `python3 -I` on B82 / B83's fixture tree; `privyhub_service`'s handler on a
ThreadingHTTPServer at 127.0.0.1:0; network beyond loopback blocked; B101's fake RetroArch with its command log; the
fake picture source with B102's synthetic tallies — start 0-0, end_P1 1-0, end_P2 0-1, an unseen 1-1, fights; a spec
learnt in the test with B104's tool). Cases: a start over a running watch → `replaced`, the second watch ends rightly;
the load done but an unknown screen / a fight shown → `recognised` false within RECOGNISE_S (scaled down) and no
`ended`; the start shown → true; load=0 → null, then true; `h7-stop` → idle, nothing sent to the game; `keep=1` writes
the pictures and the index, absent writes none; `git check-ignore` for the keep folder's shape; an old-measure spec →
`no_spec` with the plain line; `last` carries the thresholds and the spec's version; the flag absent / 0 → HEAD's
answers byte for byte (h7-stop included). Temp dirs removed at exit.

    python3 -m unittest discover -s tests/b105_h7_watcher -v
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
sys.path.insert(0, str(ROOT / "tests" / "b99_h7_live_read"))
sys.path.insert(0, str(ROOT / "tests" / "b102_h7_endscreen"))
sys.path.insert(0, str(ROOT / "tests" / "b103_h7_minigame"))
sys.path.insert(0, str(ROOT / "tools"))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402  (modules: their tests are not collected twice)
import test_b103 as b103  # noqa: E402

ON = {**b85.FLAGS, "PRIVYHUB_H7": "1"}
BASELINE = "d61f9b56"                   # queue AN's baseline (H7-V2 committed): the companion before B105
RECOGNISE_S = 1.6                       # the test's: 8 reads at 0.2 s (the hub's: 8 s at 1 s)

SCENARIO = r'''
import csv
out = {"steps": {}}
S = out["steps"]
def stop():
    return call("POST", "/plugins/games/h7-stop")
def wait_for(pred, bound=20):
    end = time.monotonic() + bound; b = result()
    while time.monotonic() < end:
        b = result()
        if pred(b):
            return b
        time.sleep(0.03)
    return dict(b, timeout=True)
def rows():
    log = root / "logs/games/h7_results.jsonl"
    return [json.loads(l) for l in log.read_text().splitlines()] if log.is_file() else []
S["launch"] = call("POST", f"/plugins/games/launch?id={args['id']}")["code"]
time.sleep(0.3)
if args["mode"] == "today":
    S["get_after"] = call("GET", "/plugins/games/h7-result")
    S["start_after"] = start()
    S["start_keep"] = start("?keep=1")
    S["stop_after"] = stop()
else:
    mini = g._h7_minigame_runner()
    mini.picture = pic
    mini.read_every = 0.2
    mini.recognise_s = args["recognise_s"]
    ra = fake["ra"]; ra.paused = False
    stem = m._active_state_stem(); f = folder(); f.mkdir(parents=True, exist_ok=True)
    Path(rules).mkdir(parents=True, exist_ok=True)
    for name in os.listdir(args["spec_dir"]):
        shutil.copyfile(Path(args["spec_dir"], name), Path(rules, name.replace("GAME", args["id"])))
    Path(rules, args["id"] + ".state").write_text(json.dumps({"P1": 0, "P2": 0}))
    keep_root = root / "runtime" / "h7_frames"
    def folders():
        return sorted(p.name for p in keep_root.iterdir()) if keep_root.is_dir() else []
    S["stop_none"] = stop()
    S["bad_keep_word"] = start("?keep=2")
    # R1: a start over a running watch replaces it; the second watch ends rightly
    pic.set(["start"] * 3 + ["other"] * 200)
    n0 = len(ra.log); r0 = len(rows())
    S["r1_first"] = start()
    S["r1_mid"] = wait_for(lambda b: (b.get("reads") or 0) >= 5)
    pic.set(["start"] * 3 + ["end_P2"] * 3 + ["other"] * 50)
    S["r1_second"] = start()
    S["r1"] = wait_for(lambda b: b.get("state") == "ended")
    time.sleep(0.6)
    S["r1_commands"] = ra.log[n0:]
    S["r1_rows"] = rows()[r0:]
    # R2: the load done, an unseen tally (1-1) shown: recognised false, never ended
    for tag, tok in (("r2", "unknown"), ("r3", "other"), ("r3f", "fail")):
        pic.set([tok] * 400)
        r0 = len(rows())
        S[tag + "_start"] = start()
        S[tag + "_null"] = result()
        S[tag] = wait_for(lambda b: b.get("recognised") is not None)
        time.sleep(1.5)
        S[tag + "_after"] = result()
        S[tag + "_rows"] = rows()[r0:]
    # R4: the start shown → true at the first read
    pic.set(["start"] * 400)
    S["r4_start"] = start()
    S["r4"] = wait_for(lambda b: b.get("recognised") is not None)
    # R5: load=0: null through a fight past RECOGNISE_S, then true once the start is read
    pic.set(["other"] * 15 + ["start"] * 400)
    S["r5_start"] = start("?load=0")
    S["r5_past"] = wait_for(lambda b: (b.get("reads") or 0) >= 12)
    S["r5"] = wait_for(lambda b: b.get("recognised") is not None)
    # R6: stop → idle, nothing sent to the game after the call
    n0 = len(ra.log); r0 = len(rows())
    S["r6_stop"] = stop()
    S["r6_idle"] = result()
    time.sleep(1.0)
    S["r6_later"] = result()
    S["r6_commands"] = ra.log[n0:]
    S["r6_stop_again"] = stop()
    S["r6_rows"] = rows()[r0:]
    # R7: keep=1 writes the pictures and the index; absent writes none
    before = folders()
    pic.set(["start"] * 3 + ["end_P1"] * 3 + ["other"] * 50)
    S["r7_start"] = start("?keep=1")
    S["r7"] = wait_for(lambda b: b.get("state") == "ended")
    time.sleep(0.5)
    made = [x for x in folders() if x not in before]
    S["r7_folders"] = made
    if made:
        d = keep_root / made[0]
        S["r7_files"] = sorted(p.name for p in d.iterdir())
        with (d / "index.csv").open(newline="") as fh:
            S["r7_index"] = list(csv.DictReader(fh))
        S["r7_header"] = (d / "index.csv").read_text().splitlines()[0]
    before = folders()
    pic.set(["start"] * 3 + ["end_P2"] * 3 + ["other"] * 50)
    S["r7b_start"] = start()
    S["r7b"] = wait_for(lambda b: b.get("state") == "ended")
    S["r7b_new_folders"] = [x for x in folders() if x not in before]
    # R8: an old-measure spec (the ended watch stopped first: an ended watch is shown until the next start or stop)
    S["r8_stop"] = stop()
    js = Path(rules, args["id"] + ".endscreen.json")
    old = json.loads(js.read_text()); old["version"] = 1; old.pop("measure", None)
    js.write_text(json.dumps(old))
    S["r8_get"] = result()
    S["r8_start"] = start()
    S["scratch_left"] = sorted(p.name for p in f.iterdir() if p.name.endswith(".state8"))
    out["rows"] = rows()
httpd.shutdown()
print(json.dumps(out))
'''


def child() -> str:
    """B103's harness (everything before its own steps) + B105's steps."""
    head = b103.CHILD.split('out = {"steps": {}}')[0]
    return head + SCENARIO


def run(root: Path, env: dict, gid: str, mode: str) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules")})
    (root / "tools").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools" / "h7_endscreen.py", root / "tools" / "h7_endscreen.py")
    work = Path(tempfile.mkdtemp(prefix="b105_fx_"))
    frames, spec_dir, js = b103.fixtures(work)
    js["arrays"] = f"{gid}.endscreen.npz"
    (spec_dir / "GAME.endscreen.json").write_text(json.dumps(js))
    r = subprocess.run([sys.executable, "-I", "-B", "-c", child(), str(root),
                        json.dumps({"id": gid, "mode": mode, "p1": b99.P1, "p2": b99.P2, "frames": str(frames),
                                    "spec_dir": str(spec_dir), "recognise_s": RECOGNISE_S})],
                       cwd=root, env=child_env, capture_output=True, text=True, timeout=900)
    shutil.rmtree(work, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def steps(rows, name):
    return [r for r in rows if r["step"] == name]


class Watcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b99.tree()
        cls.gid = ids[b85.PS1_TITLE]
        cls.out = run(root, ON, cls.gid, "on")
        cls.s = cls.out["steps"]

    def test_words(self):
        self.assertEqual(self.s["stop_none"]["body"], {"ok": True, "watch": "none"})
        self.assertEqual((self.s["bad_keep_word"]["code"], self.s["bad_keep_word"]["body"]["error"]),
                         (400, "keep is 0 or 1"))

    def test_a_start_over_a_running_watch_replaces_it(self):
        s = self.s
        self.assertEqual((s["r1_first"]["code"], s["r1_first"]["body"]["replaced"]), (200, False))
        self.assertEqual((s["r1_mid"]["state"], s["r1_mid"]["class"]), ("watching", "other"))
        self.assertEqual((s["r1_second"]["code"], s["r1_second"]["body"]["replaced"]), (200, True))
        w = s["r1"]
        self.assertEqual((w["state"], w["class"], w["reads"], w["recognised"]), ("ended", "end_P2", 6, True))
        self.assertEqual(s["r1_commands"], ["LOAD_STATE_SLOT", "LOAD_STATE_SLOT"])          # the load again
        rows = s["r1_rows"]
        self.assertEqual(len(steps(rows, "replaced")), 1)
        rep = steps(rows, "replaced")[0]
        self.assertGreaterEqual(rep["reads"], 5)
        after = rows[rows.index(rep) + 1:]
        self.assertEqual([r["step"] for r in after if r["step"] in ("watching", "ended")], ["watching", "ended"])
        self.assertEqual(steps(after, "ended")[0]["reads"], 6)                    # only the new watch's rows after
        self.assertEqual(len(steps(rows, "watching")), 2)

    def test_last_carries_the_thresholds_and_the_version(self):
        last = self.s["r1"]["last"]
        self.assertEqual(set(last), {"class", "distances", "margin", "thresholds", "spec_version"})
        self.assertEqual(last["spec_version"], 2)
        self.assertEqual(set(last["thresholds"]), {"screen", "classes", "margin_needed"})
        self.assertIsNotNone(last["thresholds"]["screen"])

    def test_an_unknown_screen_or_a_fight_after_the_load_is_not_recognised(self):
        for tag, cls in (("r2", "unknown"), ("r3", "other")):
            s = self.s
            self.assertEqual(s[tag + "_start"]["code"], 200)
            self.assertIsNone(s[tag + "_null"].get("recognised"))
            w = s[tag]
            self.assertIs(w["recognised"], False, w)
            self.assertNotIn("timeout", w)
            self.assertEqual(w["state"], "watching")
            self.assertEqual(s[tag + "_after"]["state"], "watching")                # no ended, still not recognised
            self.assertIs(s[tag + "_after"]["recognised"], False)
            rec = steps(s[tag + "_rows"], "recognised")
            self.assertEqual(len(rec), 1)
            self.assertEqual((rec[0]["value"], rec[0]["class"]), (False, cls))
            self.assertGreaterEqual(rec[0]["after_s"], RECOGNISE_S)
            self.assertLess(rec[0]["after_s"], RECOGNISE_S + 0.6)                     # within the stated seconds
            self.assertEqual(steps(s[tag + "_rows"], "ended"), [])

    def test_pictures_that_cannot_be_read_after_the_load_are_not_recognised(self):
        w = self.s["r3f"]
        self.assertIs(w["recognised"], False, w)
        self.assertEqual((w["state"], w["reads"]), ("watching", 0))
        self.assertGreaterEqual(w["picture_failures"], 7)
        rec = steps(self.s["r3f_rows"], "recognised")
        self.assertEqual((len(rec), rec[0]["value"], rec[0]["class"]), (1, False, None))

    def test_the_start_shown_is_recognised(self):
        w = self.s["r4"]
        self.assertIs(w["recognised"], True)
        self.assertLessEqual(w["reads"], 2)

    def test_load_0_stays_null_then_true(self):
        self.assertIsNone(self.s["r5_past"]["recognised"])                          # past RECOGNISE_S: still null
        self.assertGreaterEqual(self.s["r5_past"]["reads"], 12)
        self.assertIs(self.s["r5"]["recognised"], True)

    def test_stop_ends_the_watch_and_sends_nothing(self):
        s = self.s
        self.assertEqual((s["r6_stop"]["code"], s["r6_stop"]["body"]["watch"]), (200, "stopped"))
        self.assertEqual(s["r6_idle"]["state"], "idle")
        self.assertEqual(s["r6_later"]["state"], "idle")
        self.assertEqual(s["r6_commands"], [])
        self.assertEqual(s["r6_stop_again"]["body"], {"ok": True, "watch": "none"})
        self.assertEqual([r["step"] for r in s["r6_rows"]], ["stopped_by_call"])

    def test_keep_writes_the_pictures_and_the_index(self):
        s = self.s
        self.assertEqual(len(s["r7_folders"]), 1)
        name = s["r7_folders"][0]
        self.assertTrue(name.startswith(self.gid + "_"))
        self.assertEqual(s["r7_start"]["body"]["keep"], name)
        self.assertEqual((s["r7"]["state"], s["r7"]["class"]), ("ended", "end_P1"))
        n = s["r7"]["reads"]
        self.assertEqual(s["r7_header"], "seconds,utc,file,class,screen,margin,distances,keep_ms")
        self.assertEqual(len(s["r7_index"]), n)
        self.assertEqual(sorted(s["r7_files"]), sorted(["index.csv"] + [f"f{i:06d}.jpg" for i in range(1, n + 1)]))
        self.assertEqual([r["class"] for r in s["r7_index"]][-3:], ["end_P1"] * 3)
        self.assertEqual(json.loads(s["r7_index"][0]["distances"])["screen"], float(s["r7_index"][0]["screen"]))
        self.assertEqual(s["r7"]["keep"], {"folder": name, "pictures": n})
        self.assertEqual(s["r7b_new_folders"], [])                                  # absent: none
        r = subprocess.run(["git", "-C", os.environ.get("H7_GIT_REPO") or str(ROOT), "check-ignore", "-q",
                            f"runtime/h7_frames/{name}/f000001.jpg"], capture_output=True, timeout=60)
        if r.returncode == 128:
            self.skipTest("git is absent")
        self.assertEqual(r.returncode, 0)                                           # git-ignored on the repo

    def test_an_old_measure_spec(self):
        line = "this end-screen spec was learnt with the old measure (absolute grey levels): learn it again"
        self.assertEqual((self.s["r8_get"]["state"], self.s["r8_get"]["why"]), ("no_spec", line))
        self.assertEqual((self.s["r8_start"]["code"], self.s["r8_start"]["body"]["error"]), (400, line))

    def test_no_scratch_left(self):
        self.assertEqual(self.s["scratch_left"], [])


class FlagAbsentIsToday(unittest.TestCase):
    def test_absent_and_zero_answer_as_heads_code(self):
        old = b99.BASELINE
        b99.BASELINE = BASELINE
        try:
            code = b99.head_code()
        finally:
            b99.BASELINE = old
        if code is None:
            self.skipTest("git is absent")
        root, ids = b99.tree(code)
        gid = ids[b85.PS1_TITLE]
        base = run(root, b85.FLAGS, gid, "today")
        keys = ("get_after", "start_after", "start_keep", "stop_after")
        for env in (b85.FLAGS, {**b85.FLAGS, "PRIVYHUB_H7": "0"}):
            root2, _ = b99.tree()
            mine = run(root2, env, gid, "today")
            for k in keys:
                self.assertEqual((mine["steps"][k]["code"], mine["steps"][k]["raw"]),
                                 (base["steps"][k]["code"], base["steps"][k]["raw"]), k)
            self.assertEqual(mine["steps"]["launch"], base["steps"]["launch"])
        self.assertEqual(base["steps"]["stop_after"]["body"]["error"], "Unknown Games plugin POST action: h7-stop")
        self.assertEqual(base["steps"]["get_after"]["body"]["error"], "Unknown Games plugin action: h7-result")


if __name__ == "__main__":
    unittest.main()
