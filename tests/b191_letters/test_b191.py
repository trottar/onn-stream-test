#!/usr/bin/env python3
"""B191 / B192 (host): the `letters` kind — a word spelled by the player who lost, read in each player's corner — and its
synthetic training, never synthetic proof. Every picture made-up (`letters_capture.py`); no title, nothing read from the
hub's own folders, the hub never reached (port 9), no systemctl (`true`).

- `Learner`: a made-up title whose every match has its own background — B102's whole-screen `winner` spec fails on it;
  `learn_letters` reads it, every held-out synthetic picture read, each real end read as its role; a letter no save
  shows never read.
- `Tool`: register --result letters --word (options refused as they should be; four players refused, said why) ->
  label (the line, the readings, the last look) -> learn PASS on the real saves (left-out included), the sidecar and the
  version-5 spec in the rules folder; label refusals (readings differ, a corner not fitting the word, the role not
  agreeing); a save a reader learnt without it cannot read fails learn's left-out cell though synthetic training reads
  every held-out picture.
- `Reads`: neither spelled -> other, never ended; both -> unknown; a corner not read beside a spelled one -> unknown +
  end_unread; background shapes in a player's colour never read as letters; a moving screen never ended; the begin
  with B137's corner black -> start.
- `Hub`: the listing — `letters` with a version-5 spec is B158's winner entry; any other shape not listed.
Temp dirs removed.

    python3 -m unittest discover -s tests/b191_letters -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "companion"), str(HERE)]

import numpy as np                                          # noqa: E402
from PIL import Image                                       # noqa: E402

import letters_capture as lc                                # noqa: E402

ENV_KEYS = ("PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_H7_RULES", "PRIVYHUB_ADD_GAME_LOGS",
            "PARTY_ADD_GAME_CAPTURE", "PRIVYHUB_ADD_GAME_HUB", "PRIVYHUB_ADD_GAME_DROPINS", "PRIVYHUB_ADD_GAME_ASK",
            "PRIVYHUB_ADD_GAME_PROJECT", "PRIVYHUB_ADD_GAME_SYSTEMCTL")
B, O = {"kind": "begin"}, {"kind": "other"}


def end(p1: str, p2: str, bg: int, **more) -> dict:
    return {"kind": "end", "l": [p1, p2], "bg": bg, **more}


# T91's shape: the loser's corner WOW, the winner's --- or W--; two saves of each ending, each its own background
TITLE = {"begin": B, "other": O,
         "end_P1": end("---", "WOW", 1), "end_P1_2": end("---", "WOW", 6),
         "end_P2": end("WOW", "W--", 3), "end_P2_2": end("WOW", "W--", 8)}
# one save's player-1 letters in another colour (a highlight no other save shows): no reader learnt without it reads it
ODD = dict(TITLE, end_P2_2=end("WOW", "W--", 8, colour=[[60, 200, 70], None]))
READ = {r: f"{st['l'][0]}/{st['l'][1]}" for r, st in TITLE.items() if r.startswith("end_")}


class Made(unittest.TestCase):
    N = [0]

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b191_"))
        cls.old = {k: os.environ.get(k) for k in ENV_KEYS}
        os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(cls.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(cls.tmp / "ev"),
                           "PRIVYHUB_H7_RULES": str(cls.tmp / "rules"), "PRIVYHUB_ADD_GAME_LOGS": str(cls.tmp / "logs"),
                           "PARTY_ADD_GAME_CAPTURE": "letters_capture:capture",
                           "PRIVYHUB_ADD_GAME_HUB": "http://127.0.0.1:9",
                           "PRIVYHUB_ADD_GAME_DROPINS": str(cls.tmp / "dropins"),
                           "PRIVYHUB_ADD_GAME_ASK": str(cls.tmp / "project" / "logs" / "add_game_ask"),
                           "PRIVYHUB_ADD_GAME_PROJECT": str(cls.tmp / "project"),
                           "PRIVYHUB_ADD_GAME_SYSTEMCTL": "true"})
        (cls.tmp / "rules").mkdir()
        (cls.tmp / "project").mkdir()
        import party_add_game as pag
        import h7_endscreen as es
        cls.pag, cls.es = pag, es

    @classmethod
    def tearDownClass(cls):
        for k, v in cls.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        """The made-up noise follows a state counter; every test starts it at 0, so a test reads the same pictures
        whatever ran before (disclosed: at some counters the odd-colour title's second save's left-out also fails)."""
        self.N[0] = 0

    def put(self, code: str, saves: dict, word: str = "WOW") -> None:
        """The kept states and the binding as register leaves them (register's PASS written for them)."""
        pag = self.pag
        kf = pag.kept_folder(code)
        kf.mkdir(parents=True, exist_ok=True)
        for role, st in saves.items():
            self.N[0] += 1
            (kf / f"{role}.state").write_text(json.dumps({**st, "n": self.N[0]}))
        b = {"code": code, "game": "madeup" + code.lower(), "players": 2, "system": "ps1", "result": "letters",
             "word": word, "cheat": None, "relative_path": "", "title": "", "content": ""}
        b["register_inputs"] = pag.register_inputs(b, pag.kept_states(code))
        pag.binding_path(code).write_text(json.dumps(b))
        pag.verdict_path(code, "register").parent.mkdir(parents=True, exist_ok=True)
        pag.verdict_path(code, "register").write_text(json.dumps({"verdict": "PASS", "inputs": b["register_inputs"]}))

    def tool(self, *argv) -> tuple[int, str]:
        buf, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            rc = self.pag.main([str(a) for a in argv])
        return rc, buf.getvalue() + err.getvalue()

    def verdict(self, code: str, stage: str) -> dict:
        v = self.pag.load_verdict(code, stage) or {}
        return {"verdict": v.get("verdict"), "bad": [c["cell"] for c in v.get("cells", []) if not c["met"]],
                "cells": {c["cell"]: c["read"] for c in v.get("cells", [])}, "recorded": v.get("recorded") or {}}

    def label_all(self, code: str, reads: dict) -> tuple[int, str]:
        rc, out = self.tool("label", code, *[f"{r}={t},{t}" for r, t in sorted(reads.items())])
        if rc == 1 and "Look at label/letters.png" in out:
            rc, out = self.tool("label", code, "look=all")
        return rc, out

    def pics(self, code: str) -> Path:
        return self.pag.home(code) / "pictures"


def _paths(folder: Path, role: str) -> list[str]:
    import csv
    rows = list(csv.DictReader((folder / role / "index.csv").open()))
    return [str(folder / role / r["file"]) for r in rows]


class Learner(Made):
    def test_1_whole_screen_fails_letters_passes(self):
        """B102's whole-screen learner on a title whose every match has its own background: not usable, or every
        held-out frame not read as its ending. The letters kind reads it from the same saves."""
        self.put("T61", TITLE)
        pag, es = self.pag, self.es
        kept = pag.kept_states("T61")
        pics = pag._pictures("T61", pag.load_binding("T61"), kept)
        labels = pag._labels(pics, kept, es)
        (pics / "labels.json").write_text(json.dumps(labels))
        spec, arrays, _rep = es.learn(pics, pics / "labels.json", "first", name="x")
        if spec.get("usable"):
            sc = es.score(pics, pics / "labels.json", spec, arrays, "second")
            held = {c: row for c, row in (sc.get("confusion") or {}).items() if c.startswith("end_")}
            right = sum(row.get(c, 0) for c, row in held.items())
            total = sum(sum(row.values()) for row in held.values())
            self.assertLess(right / max(total, 1), 1 - pag.BARS["unknown_share_max"][0])
        starts, others, ends = pag._letters_inputs_of(pics, kept)
        sides = {r: TITLE[r]["l"] for r in ends}
        spec, arrays, rep = es.learn_letters(starts, others, ends, sides, "WOW", 2)
        self.assertTrue(spec["usable"], json.dumps(rep, default=str)[:600])
        self.assertTrue(rep["synthetic"]["every_held_out_read"])
        self.assertEqual(rep["synthetic"]["held_out"], 4 * es.SYN_HELD)
        for role in ends:
            with Image.open(ends[role][0]) as im:
                r = es.Reader(spec, arrays).read(im.convert("RGB"))
            self.assertEqual(r["class"], pag._role_class(role))
            self.assertEqual(r["letters"], TITLE[role]["l"])
        # the same saves always give the same synthetic set
        _s2, _a2, rep2 = es.learn_letters(starts, others, ends, sides, "WOW", 2)
        self.assertEqual(rep2["synthetic"]["seed"], rep["synthetic"]["seed"])
        self.assertEqual(rep2["synthetic"]["rounds"], rep["synthetic"]["rounds"])

    def test_2_a_letter_no_save_shows_is_never_read(self):
        """X (a letter of no save) drawn in a corner: no template, never read as the nearest letter."""
        self.put("T62", TITLE)
        pag, es = self.pag, self.es
        kept = pag.kept_states("T62")
        pics = pag._pictures("T62", pag.load_binding("T62"), kept)
        starts, others, ends = pag._letters_inputs_of(pics, kept)
        spec, arrays, _rep = es.learn_letters(starts, others, ends, {r: TITLE[r]["l"] for r in ends}, "WOW", 2)
        im = lc.picture(end("WXW", "WOW", 11))
        r = es.Reader(spec, arrays).read(im)
        self.assertIsNone(r["letters"][0])
        self.assertEqual(r["class"], es.UNKNOWN)
        self.assertTrue(r.get("end_unread"))


class Tool(Made):
    def test_1_register_options(self):
        rc, out = self.tool("register", "T63", "--players", 2, "--system", "ps1", "--result", "letters",
                            "--rules-players", 2)
        self.assertEqual(rc, 2)
        self.assertIn("--result letters needs --word", out)
        rc, out = self.tool("register", "T63", "--players", 2, "--system", "ps1", "--result", "winner", "--word", "WOW",
                            "--rules-players", 2)
        self.assertEqual(rc, 2)
        self.assertIn("--word is for --result letters", out)

    def test_2_register_four_players_refused_and_said_why(self):
        pag = self.pag
        a = {"players": 4, "system": "ps1", "result": "letters", "word": "wow", "check": True, "collect": [],
             "find": "x"}
        orig = pag._find_title
        pag._find_title = lambda system, words: {"game": "madeupt64", "relative_path": "", "title": "", "content": ""}
        try:
            cells, b, _i = pag._register("T64", a)
        finally:
            pag._find_title = orig
        rows = {r["cell"]: r for r in cells.rows}
        self.assertEqual(b["word"], "WOW")
        self.assertFalse(rows["a letters title has two players"]["met"])
        self.assertIn("winner-only would name a winner the game never showed", rows["why not"]["read"])

    def test_3_label_learn_pass(self):
        self.put("T65", TITLE)
        rc, out = self.tool("learn", "T65")
        self.assertEqual(rc, 2)                                 # label first
        rc, out = self.tool("label", "T65")
        self.assertEqual(rc, 1)
        self.assertIn("Read each player's letters in its corner", out)
        self.assertEqual(sorted(p.name for p in (self.pag.home("T65") / "label").iterdir()),
                         sorted(f"{r}.{i}.png" for r in READ for i in (1, 2)))
        rc, out = self.label_all("T65", READ)
        lv = self.verdict("T65", "label")
        self.assertEqual(rc, 0, out + json.dumps(lv["bad"]))
        self.assertEqual(lv["recorded"]["sheet"], {"-": 10, "O": 4, "W": 10})
        self.assertEqual(lv["cells"]["end_P2: read back by a reader learnt without it"], ["WOW/W--", "WOW/W--"])
        rc, out = self.tool("learn", "T65")
        v = self.verdict("T65", "learn")
        self.assertEqual(rc, 0, out + json.dumps(v["bad"]))
        self.assertEqual(v["cells"]["left out: end_P1_2"][0], "end_P1")
        self.assertEqual(v["cells"]["left out: end_P2"][2], ["WOW/W--", "WOW/W--"])
        self.assertEqual(v["recorded"]["synthetic"]["held_out"], 32)
        rules = Path(os.environ["PRIVYHUB_H7_RULES"])
        self.assertEqual(json.loads((rules / "madeupt65.party.json").read_text()), {"players": 2, "result": "letters"})
        spec, _arrays = self.es.load_spec(rules / "madeupt65.endscreen.json")
        self.assertEqual(spec["version"], 5)
        self.assertEqual(spec["letters"]["word"], "WOW")

    def test_4_label_refusals(self):
        self.put("T66", TITLE)
        bad = dict(READ, end_P1="---/WOW", end_P2="WOX/W--", end_P2_2="---/WOW")
        rc, out = self.tool("label", "T66", "end_P1=---/WOW,---/WO-", *[f"{r}={t},{t}" for r, t in sorted(bad.items())
                                                                      if r != "end_P1"])
        lv = self.verdict("T66", "label")
        self.assertEqual(rc, 1)
        self.assertIn("end_P1: the two readings the same", lv["bad"])
        self.assertIn("end_P2: each corner fits the word", lv["bad"])
        self.assertIn("end_P2_2: the role agreeing", lv["bad"])
        self.assertIn("Read again: end_P1 (its two readings differ); end_P2 (a corner does not fit the word); "
                      "end_P2_2 (its letters do not say P2 won)", out)
        self.assertNotIn("the letters at one place in every save", lv["cells"])     # nothing learnt from them

    def test_5_left_out_reads_the_real_save(self):
        """end_P2_2's player-1 letters in a colour no other save shows: synthetic training reads every held-out picture
        (it pastes that save's own pixels), but a reader learnt without the save cannot read the real save — learn
        FAILs on its left-out cell. A synthetic picture never counts toward a pass."""
        self.put("T67", ODD)
        pag = self.pag
        rec = {"saves": {r: {"sha": pag.kept_states("T67")[r], "readings": [READ[r], READ[r]], "by": "session"}
                         for r in READ}}
        pag.label_path("T67").write_text(json.dumps(rec))     # the label stage's PASS for these readings
        b = pag.load_binding("T67")
        pag.verdict_path("T67", "label").write_text(json.dumps({"verdict": "PASS", "inputs": pag.label_inputs("T67", b)}))
        rc, out = self.tool("learn", "T67")
        v = self.verdict("T67", "learn")
        self.assertEqual(rc, 1, out)
        self.assertIn("left out: end_P2_2", v["bad"], json.dumps(v["cells"], default=str)[:800])
        self.assertTrue(all(c.startswith("left out: ") for c in v["bad"]), v["bad"])   # (at some noise seeds a second
        #                                     save's left-out cannot be trained either: that colour is in one save only)
        self.assertEqual(v["cells"]["every held-out synthetic picture read (training's own bar; never counts toward a "
                                    "pass)"]["read wrong or not read"], 0)
        self.assertIn("end_P2_2: a reader learnt without it does not read it", out)
        self.assertFalse((Path(os.environ["PRIVYHUB_H7_RULES"]) / "madeupt67.party.json").exists())


class Reads(Made):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.N[0] = 1000
        self_ = cls("test_1_neither_spelled_never_ends")
        self_.put("T68", TITLE)
        pag, es = cls.pag, cls.es
        kept = pag.kept_states("T68")
        pics = pag._pictures("T68", pag.load_binding("T68"), kept)
        starts, others, ends = pag._letters_inputs_of(pics, kept)
        cls.spec, cls.arrays, _r = es.learn_letters(starts, others, ends, {r: TITLE[r]["l"] for r in ends}, "WOW", 2)
        cls.starts = starts

    def run_of(self, pictures, start_loaded=True):
        es = self.es
        rd, ended = es.Reader(self.spec, self.arrays), es.Ended(self.spec)
        if start_loaded:
            ended.start_loaded()
        reads = [rd.read(im) for im in pictures]
        done = None
        for r in reads:
            done = ended.feed(r["class"], None) or done
        return reads, done

    def test_1_neither_spelled_never_ends(self):
        reads, done = self.run_of([lc.picture(end("W--", "WO-", 12))] * 6)
        self.assertEqual({r["class"] for r in reads}, {"other"})
        self.assertEqual(reads[0]["letters"], ["W--", "WO-"])
        self.assertIsNone(done)

    def test_2_both_spelled_no_result(self):
        reads, done = self.run_of([lc.picture(end("WOW", "WOW", 13))] * 6)
        self.assertEqual({r["class"] for r in reads}, {"unknown"})
        self.assertIsNone(done)

    def test_3_a_corner_not_read_beside_a_spelled_one(self):
        st = end("WOW", "W--", 14, blobs=[[2, 470, 84, 120, 28]])     # P2's corner covered in its own colour
        reads, done = self.run_of([lc.picture(st)] * 4)
        self.assertEqual(reads[0]["letters"], ["WOW", None])
        self.assertEqual({r["class"] for r in reads}, {"unknown"})
        self.assertTrue(all(r.get("end_unread") for r in reads))
        self.assertIsNone(done)

    def test_4_background_shapes_never_letters(self):
        """Three bars in player 1's colour where its letters sit, a little larger than its not-yet marks: not marks."""
        st = end("_", "WOW", 15, blobs=[[1, 72, 95, 21, 12], [1, 98, 95, 21, 12], [1, 124, 95, 21, 12]])
        reads, done = self.run_of([lc.picture(st)] * 4)
        self.assertIsNone(reads[0]["letters"][0])
        self.assertNotIn("end_P1", {r["class"] for r in reads})
        self.assertIsNone(done)

    def test_5_a_moving_screen_never_ends(self):
        base = lc.picture(end("---", "WOW", 16))
        moved = []
        for i in range(8):
            a = np.asarray(base).copy()
            sc = np.roll(np.asarray(lc.background(17 + i, None), dtype=np.uint8), 0, axis=1)
            keep = np.zeros(a.shape[:2], bool)
            for b in self.spec["letters"]["places"].values():
                keep[b[1]:b[3], b[0]:b[2]] = True
            a[~keep] = sc[~keep]                              # the scene changes every read; the corners stay
            moved.append(Image.fromarray(a))
        reads, done = self.run_of(moved)
        self.assertIn("end_P1", {r["class"] for r in reads})  # it reads the letters ...
        self.assertIsNone(done)                               # ... and never ends on a moving screen
        _reads, done = self.run_of([base] * 3)
        self.assertEqual(done, "end_P1")                      # the same picture held: ended

    def test_6_the_begin_with_the_corner_black(self):
        with Image.open(self.starts[0]) as im:
            r1 = self.es.Reader(self.spec, self.arrays).read(im.convert("RGB"))
            black = im.convert("RGB").copy()
        w = black.size[0]
        black.paste((0, 0, 0), (w - 200, 0, w, 70))
        r2 = self.es.Reader(self.spec, self.arrays).read(black)
        self.assertEqual((r1["class"], r2["class"]), ("start", "start"))
        _reads, done = self.run_of([black] * 5, start_loaded=False)
        self.assertIsNone(done)


class Hub(unittest.TestCase):
    def test_listing(self):
        import party_minigame as pm
        cls = pm.PartyMinigames if hasattr(pm, "PartyMinigames") else None
        fn = None
        for name in dir(pm):
            obj = getattr(pm, name)
            if isinstance(obj, type) and hasattr(obj, "_letters_entry"):
                fn = obj._letters_entry
        self.assertIsNotNone(fn)
        del cls
        v5 = {"version": 5, "start_class": "start", "end_classes": ["end_P1", "end_P2"]}
        e = fn(v5, {"players": 2, "result": "letters"}, 2)
        self.assertEqual(e["winner_of"], {"end_P1": 1, "end_P2": 2})
        self.assertEqual(e["scores"], {"end_P1": [1, 0], "end_P2": [0, 1]})
        self.assertIsNone(fn(dict(v5, version=2), {"players": 2, "result": "letters"}, 2))
        self.assertIsNone(fn(v5, {"players": 2, "result": "letters", "scores": {}}, 2))
        self.assertIsNone(fn(dict(v5, end_classes=["end_P1", "end_P2", "end_P3", "end_P4"]),
                             {"players": 4, "result": "letters"}, 4))


if __name__ == "__main__":
    unittest.main()
