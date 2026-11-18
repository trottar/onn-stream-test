#!/usr/bin/env python3
"""B139 (host): a party mini game's title launched with RetroArch's on-screen text off — through the real HTTP server
on loopback, behind PRIVYHUB_PARTY=1 and PRIVYHUB_H7=1.

B114's scenario: B101's fake RetroArch reads the session config it is started with (each launch's B139 keys kept, and
whether a party mini game launched it); it draws notices and "Paused." only when that config leaves them on.

Checked: **every launch a party mini game makes carries `video_font_enable = "false"` and
`menu_show_load_content_animation = "false"` once each; the users' own launch of the same game in the same companion
carries neither** — plain (`nopress`) and under a cheat setup (B127's `cheat` mode: the users' Extras launches beside
the party's); the party's watch reads unmasked (`watching` has no `label_mask`) and still reads the start; **the users'
launch's session config byte for byte HEAD's** (normalised for the temp root and the per-launch port) with the flags
absent, and with the flags set; offline (the hub's own kept pictures, read only; skipped elsewhere): T88's paused
pictures with the label's pixels removed as the settings remove them → `start`, `other` read as the screen 0 on every
kept run. Temp dirs removed.

    python3 -m unittest discover -s tests/b139_party_clean_window -v
"""
from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b127_party_cheat_setups", "b115_party_handovers",
            "b123_h7_n64_start"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
import test_b114 as b114  # noqa: E402  (harnesses; their tests are not collected here)
import test_b124 as b124  # noqa: E402
import test_b127 as b127  # noqa: E402

HEAD = "c1a66bc9"                       # queue AW's baseline: the companion before B139
SETTINGS = {"video_font_enable": ["false"], "menu_show_load_content_animation": ["false"]}


def _run(mode, code=None, env=None, extra=b124.extra):
    root, ids = b114.b99.tree(code)
    b124.IDS.clear()
    b124.IDS.update(ids)
    return b114.run(root, env or b114.BOTH, ids, mode, extra=extra)


class PartyLaunchesOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = _run("nopress")["steps"]

    def test_0_every_party_launch_carries_the_settings_the_users_does_not(self):
        launches = self.s["b139_launches"]
        party = [c for c in launches if c["party"]]
        users = [c for c in launches if not c["party"]]
        self.assertGreaterEqual(len(party), 8)
        self.assertGreaterEqual(len(users), 1)
        for c in party:
            self.assertEqual(c["keys"], SETTINGS, c)
        for c in users:
            self.assertEqual(c["keys"], {}, c)

    def test_1_the_watch_unmasked_no_label_and_the_start_read(self):
        s = self.s
        self.assertEqual(s["n1_ready"]["phase"], "ready")
        self.assertEqual(s["n1_reads_paused_label"], 0)            # the fake drew no "Paused." (the config's text off)
        self.assertEqual(s["n1_watching_label_mask"], [None])        # the watch did not mask
        self.assertEqual(s["n1"]["state"], "ended")


class UnderSetups(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        b124.IDS.clear()
        b124.IDS.update(ids)
        cls.s = b114.run(root, b114.BOTH, ids, "cheat", extra=b127.extra)["steps"]

    def test_party_launches_under_a_setup_carry_them_the_users_extras_launches_do_not(self):
        cfg = self.s["c_b139_cfg"]
        party = [c for c in cfg if c["party"]]
        users = [c for c in cfg if not c["party"]]
        self.assertGreaterEqual(len(party), 2)
        self.assertGreaterEqual(len(users), 2)                       # the onn's Extras launches of both titles
        for c in party:
            self.assertEqual(c["keys"], SETTINGS, c)
        for c in users:
            self.assertEqual(c["keys"], {}, c)


class Today(unittest.TestCase):
    def test_the_users_launch_config_is_heads_flags_absent_and_set(self):
        code = b114.code_of(HEAD)
        if code is None:
            self.skipTest("git is absent")
        texts = {}
        for name, env in (("absent", {**b114.b85.FLAGS, **b114.ADOPTED}),
                          ("party_only", {**b114.b85.FLAGS, **b114.ADOPTED, "PRIVYHUB_PARTY": "1"}),
                          ("both", b114.BOTH)):
            root, ids = b114.b99.tree(code)
            base = b114.run(root, env, ids, "today")["steps"]["b139_users_cfg"]["text"]
            root2, ids2 = b114.b99.tree()
            mine = b114.run(root2, env, ids2, "today")["steps"]["b139_users_cfg"]["text"]
            self.assertEqual(mine, base, name)
            self.assertNotIn("B139", mine)
            texts[name] = mine
        # the flags set, inside a party companion that has run mini games: the users' launch is the same text
        s = _run("nopress")["steps"]
        self.assertEqual(s["b139_users_cfg"]["text"], texts["both"])


def _remove_label(img):
    """The window as the settings leave it: the label's bright pixels in the right bar's top replaced by the bar's tone."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert("RGB")).copy()
    h, w, _ = a.shape
    x0 = w - 301
    below = np.median(a[200:, x0:].reshape(-1, 3), axis=0).astype(np.uint8)
    reg = a[:140, x0:]
    reg[reg.max(axis=2) > int(below.max()) + 16] = below
    return Image.fromarray(a)


class OfflineT88(unittest.TestCase):
    """The hub's own kept pictures (read only). Elsewhere: skipped."""

    def test_t88_paused_pictures_with_the_text_off_read_start_and_no_other_as_the_screen(self):
        rules = Path.home() / "privyhub_h7" / "rules"
        frames = ROOT / "runtime" / "h7_frames"
        if not rules.is_dir() or not frames.is_dir():
            self.skipTest("the hub's rules folder and kept pictures are not here")
        sys.path.insert(0, str(ROOT / "tools"))
        import h7_endscreen as es
        from PIL import Image
        side = [p for p in rules.glob("*.party.json") if json.loads(p.read_text())["players"] == 2]
        if not side:
            self.skipTest("no two-player party title")
        gid = side[0].name.split(".")[0]
        spec, arr = es.load_spec(rules / f"{gid}.endscreen.json")
        d2 = frames / f"{gid}_20261117T234139Z"                 # H7-D2 pass P
        if not d2.is_dir():
            self.skipTest("H7-D2's pictures are not here")
        rows = {int(r["file"][1:7]): r for r in csv.DictReader(open(d2 / "index.csv"))}
        starts, margins = 0, []
        for k in range(13, 67):                                  # paused, 2 to 210 frames
            r = es.Reader(spec, arr).read(_remove_label(Image.open(d2 / rows[k]["file"])))
            starts += r["class"] == "start"
            margins.append(r["margin"] or 0.0)
        self.assertEqual(starts, 54)
        self.assertGreater(min(margins), 0.05)
        boot = [es.Reader(spec, arr).read(_remove_label(Image.open(d2 / rows[k]["file"])))["screen"] for k in range(1, 13)]
        self.assertEqual(sum(boot), 0)                           # the boot frame never read as the screen
        as_screen, runs = 0, 0
        for d in sorted(frames.iterdir()):                       # every kept T88 run: its `other` pictures
            if not d.name.startswith(gid + "_") or not (d / "index.csv").is_file() or d == d2:
                continue
            runs += 1
            for row in csv.DictReader(open(d / "index.csv")):
                if row.get("class") == "other":
                    as_screen += es.Reader(spec, arr).read(_remove_label(Image.open(d / row["file"])))["screen"]
        self.assertGreaterEqual(runs, 1)
        self.assertEqual(as_screen, 0)
        print(f"\nB139 offline: T88 paused 54/54 start (least margin {min(margins):.4f}); boot 0/12 as the screen; "
              f"{runs} kept runs, `other` read as the screen 0", file=sys.stderr)


if __name__ == "__main__":
    unittest.main()
