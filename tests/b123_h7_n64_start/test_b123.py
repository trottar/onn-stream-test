#!/usr/bin/env python3
"""B123 (host): `h7-start`'s load for an N64 title, and the watch ending on a row of places — through the real HTTP
server on loopback, behind PRIVYHUB_H7=1.

B103's harness (a child `python3 -I` on B82 / B83's fixture tree, B101's fake RetroArch, B103's fake pictures), with
the fixture's **N64 title launched** (B59's N64 session: `_n64_core` = the Mupen64Plus-Next core): the kept
`<game id>.state` through scratch slot 8 in the core's own folder (`Mupen64Plus-Next/<stem>.state8`), RetroArch's own
load line, the scratch removed, the users' slots there byte-equal, no `.state8` left; **a core answering PLAYING →
refused plainly, no load sent**; the watch with a **real version-3 spec** (B122, learnt here from B122's synthetic
pictures) reading synthetic results pictures → `ended` with `places`. Each flag absent → today: `h7-start` and
`h7-result` answered as HEAD's code answers. Temp dirs removed.

    python3 -m unittest discover -s tests/b123_h7_n64_start -v
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("art_systems", "b99_h7_live_read", "b102_h7_endscreen", "b103_h7_minigame", "b122_h7_places"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import _tmp_cleanup  # noqa: E402,F401
import test_b85 as b85  # noqa: E402
import test_b99 as b99  # noqa: E402
import test_b103 as b103  # noqa: E402
import test_b122 as b122  # noqa: E402

BASELINE = "cb16e0c8"
N64_NOT_PAUSED = "the N64 game is not paused: its state is loaded only into a paused core; nothing was sent"

SCENARIO = r'''
import shutil
out = {"steps": {}}
S = out["steps"]
gid = args["n64"]
def folder():                                            # the fake's slot folder: the N64 core's own
    return m._state_root() / "Mupen64Plus-Next"
if args["mode"] == "today":
    S["start"] = start(); S["result"] = call("GET", "/plugins/games/h7-result")
    print(json.dumps(out)); raise SystemExit(0)
rules_ = Path(rules); rules_.mkdir(parents=True, exist_ok=True)
v3 = Path(args["v3"])
js_ = json.loads(v3.read_text()); npz = v3.with_name(js_["arrays"])
shutil.copyfile(npz, rules_ / f"{gid}.endscreen.npz")
js_["arrays"] = f"{gid}.endscreen.npz"
(rules_ / f"{gid}.endscreen.json").write_text(json.dumps(js_))
(rules_ / f"{gid}.state").write_text(json.dumps({"P1": 5, "P2": 7}))
S["launch"] = call("POST", f"/plugins/games/launch?id={gid}")["code"]
S["n64_session"] = bool(m._n64_core)
sf = folder(); sf.mkdir(parents=True, exist_ok=True)
stem = m._active_state_stem()
for i, x in enumerate((".state", ".state1", ".state2", ".state3")):
    (sf / (stem + x)).write_bytes(os.urandom(64) + bytes([i]))
def slots():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sf.iterdir()) if not p.name.endswith(".state8")}
before = slots()
mini = g._h7_minigame_runner(); mini.picture = pic; mini.read_every = 0.2; mini.recognise_s = 1.6
ra = fake["ra"]
S["paused_before"] = ra.paused
pic.set(["s4start"] * 4 + ["s4other"] * 3 + ["s4r2143"] * 20)
n0 = len(ra.log)
S["load"] = start()
S["ra_log"] = ra.log[n0:]
S["mem"] = [int.from_bytes(ra.mem[P1:P1 + 2], "little"), int.from_bytes(ra.mem[P2:P2 + 2], "little")]
S["scratch"] = sorted(p.name for p in sf.iterdir() if p.name.endswith(".state8"))
end = time.monotonic() + 20; b = {}
while time.monotonic() < end:
    b = result()
    if b.get("state") == "ended":
        break
    time.sleep(0.05)
S["ended"] = {k: b.get(k) for k in ("state", "class", "places", "recognised", "seen_start")}
S["slots_equal"] = slots() == before
S["slots_n"] = len(before)
call("POST", "/plugins/games/h7-stop")
ra.paused = False                                         # the core running: no load is ever sent into it
n1 = len(ra.log)
S["load_playing"] = start()
S["ra_log_playing"] = ra.log[n1:]
S["scratch_after"] = sorted(p.name for p in sf.iterdir() if p.name.endswith(".state8"))
S["rows"] = [json.loads(l).get("step") for l in (root / "logs/games/h7_results.jsonl").read_text().splitlines()]
print(json.dumps(out))
'''


def frames_with_places(work: Path) -> Path:
    """B103's fixture frames plus B122's synthetic four-player pictures (tokens s4start, s4other, s4r2143)."""
    frames, _spec_dir, _js = b103.fixtures(work)
    import numpy as np
    rng = np.random.default_rng(123)
    for i in range(6):
        b122.start(i, rng).save(frames / f"s4start_{i}.png")
        b122.other(i, rng).save(frames / f"s4other_{i}.png")
        b122.results(i, "2143", 40, rng).save(frames / f"s4r2143_{i}.png")
    return frames


def v3_spec(work: Path) -> Path:
    plan = []
    for k, row in enumerate(b122.TRAIN):
        plan += [("start", 10, None, 0), ("other", 10, None, 0), (f"end_r{row}", 14, row, 20 * (k + 1))]
    runs, labels = b122.write_run(work, plan)
    spec, arrays, _rep = b122.E.learn(runs, labels, name="four")
    return b122.E.save_spec(spec, arrays, work / "four.endscreen.json")


def run(root: Path, env: dict, ids: dict, mode: str) -> dict:
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env.update({"XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "PRIVYHUB_H7_RULES": str(root / "h7rules")})
    (root / "tools").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / "tools" / "h7_endscreen.py", root / "tools" / "h7_endscreen.py")
    work = Path(tempfile.mkdtemp(prefix="b123_fx_"))
    try:
        frames = frames_with_places(work)
        spec = v3_spec(work) if mode != "today" else work / "none"
        child = b103.CHILD.split('out = {"steps": {}}')[0] + SCENARIO
        r = subprocess.run([sys.executable, "-I", "-B", "-c", child, str(root),
                            json.dumps({"n64": ids[b85.N64_TITLE], "mode": mode, "p1": b99.P1, "p2": b99.P2,
                                        "frames": str(frames), "v3": str(spec)})],
                           cwd=root, env=child_env, capture_output=True, text=True, timeout=600)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    assert r.returncode == 0, r.stderr[-4000:]
    text = r.stdout.strip().splitlines()[-1]
    for form in {str(root), str(root.resolve())}:
        text = text.replace(form, "<root>")
    return json.loads(text)


def code_of(rev: str) -> Path | None:
    try:
        data = subprocess.run(["git", "-C", os.environ.get("H7_GIT_REPO") or str(ROOT), "archive", rev, "companion"],
                              capture_output=True, timeout=120, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    d = Path(tempfile.mkdtemp(prefix="b123_head_"))
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        tf.extractall(d, filter="data")
    return d


class N64Start(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, cls.ids = b99.tree()
        cls.s = run(root, {**b85.FLAGS, "PRIVYHUB_H7": "1"}, cls.ids, "n64")["steps"]

    def test_an_n64_session(self):
        self.assertEqual(self.s["launch"], 200)
        self.assertTrue(self.s["n64_session"])
        self.assertIs(self.s["paused_before"], True)                       # launched paused (the start's own)

    def test_the_begin_state_loads_into_the_paused_core(self):
        self.assertEqual(self.s["load"]["code"], 200, self.s["load"]["body"])
        self.assertTrue(self.s["load"]["body"]["loaded"])
        self.assertIsNotNone(self.s["load"]["body"]["load_line_ms"])       # RetroArch's own load line
        log = self.s["ra_log"]
        self.assertIn("LOAD_STATE_SLOT", log)
        self.assertLess(log.index("GET_STATUS"), log.index("LOAD_STATE_SLOT"))   # asked PAUSED first
        self.assertEqual(self.s["mem"], [5, 7])                            # the kept state is what loaded
        self.assertEqual(self.s["scratch"], [])                            # the scratch slot 8 removed

    def test_the_users_slots_untouched(self):
        self.assertEqual(self.s["slots_n"], 4)
        self.assertTrue(self.s["slots_equal"])
        self.assertEqual(self.s["scratch_after"], [])

    def test_a_running_core_is_refused_and_nothing_sent(self):
        self.assertEqual((self.s["load_playing"]["code"], self.s["load_playing"]["body"].get("error")),
                         (400, N64_NOT_PAUSED))
        self.assertNotIn("LOAD_STATE_SLOT", self.s["ra_log_playing"])
        self.assertIn("refused", self.s["rows"])

    def test_the_watch_ends_on_the_row_of_places(self):
        e = self.s["ended"]
        self.assertEqual((e["state"], e["class"], e["places"], e["recognised"]), ("ended", "end", [2, 1, 4, 3], True), e)


class FlagAbsentIsToday(unittest.TestCase):
    def test_h7_absent(self):
        code = code_of(BASELINE)
        if code is None:
            self.skipTest("git is absent")
        for env in (b85.FLAGS, {**b85.FLAGS, "PRIVYHUB_H7": "0"}, {**b85.FLAGS, "PRIVYHUB_PARTY": "1"}):
            root, ids = b99.tree(code)
            base = run(root, env, ids, "today")["steps"]
            root2, ids2 = b99.tree()
            mine = run(root2, env, ids2, "today")["steps"]
            for k in ("start", "result"):
                self.assertEqual((mine[k]["code"], mine[k]["raw"]), (base[k]["code"], base[k]["raw"]), (env, k))
            self.assertIn("Unknown Games plugin", base["start"]["body"]["error"])


if __name__ == "__main__":
    unittest.main()
