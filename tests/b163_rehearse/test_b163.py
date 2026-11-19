#!/usr/bin/env python3
"""B163 (host): `rehearse <code>` — learn's whole real path on a title already in the rules folder, into a scratch
rules folder; the real one only read.

Everything made up: a title already added (its rules — spec, begin, sidecar — learnt from made-up pictures, B157's
`fake_capture`), its kept folder (begin, end_p1, end_p2, end_p1_b; no `other`, as T88's), a made-up hub on loopback answering its game
file, a made-up user's slot 2 holding a mid-match state. **Without `other` the learner cannot run: rehearse FAIL, the
missing role and the learner's own words named.** `register --rules-players` → `learn` → **`rehearse --collect
other=2` PASS** (the slot read only, copied into the scratch only): the roles on the page,
learn's cells inside, every kept ending read by the scratch rules as by the real ones, **the real rules folder's every
sha256 before = after**, the scratch removed, nothing named. A kept extra ending that shows the other player's screen →
its cell not met. A learn bar raised past the made-up spec → rehearse FAIL with `learn: …` named. Refused before
learn's PASS and for a title not already in the rules folder. **The real picture source is not run here** (the title
started headless is A's to run). Temp dirs removed.

    python3 -m unittest discover -s tests/b163_rehearse -v
"""
from __future__ import annotations

import contextlib
import hashlib
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
sys.path.insert(0, str(ROOT / "tests" / "b157_add_game"))
sys.path.insert(0, str(ROOT / "tools"))
import fake_capture as fc  # noqa: E402
import made_up_hub  # noqa: E402

GAME = "madeupgame3"
CODES = {"start": 100, "other": 101, "end_P1": 102, "end_P2": 103}


def state(token: str, extra: int = 0) -> str:
    return json.dumps({"P1": CODES[token], "P2": extra})


def _tool(*argv):
    import party_add_game as pag
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(a) for a in argv])
    return rc, buf.getvalue()


class Rehearse(unittest.TestCase):
    def setUp(self):
        import party_add_game as pag
        self.pag = pag
        self.tmp = Path(tempfile.mkdtemp(prefix="b163_"))
        self.hub = made_up_hub.MadeUpHub([], relative_path="games/ps1/Made Up Three (USA).cue")
        self.env = {"PRIVYHUB_ADD_GAME_HOME": str(self.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(self.tmp / "ev"),
                    "PRIVYHUB_ADD_GAME_PROJECT": str(self.tmp / "proj"), "PRIVYHUB_H7_RULES": str(self.tmp / "rules"),
                    "PRIVYHUB_ADD_GAME_DROPINS": str(self.tmp / "dropins"), "PRIVYHUB_ADD_GAME_SYSTEMCTL": "true",
                    "PRIVYHUB_ADD_GAME_HUB": self.hub.url, "PRIVYHUB_ADD_GAME_KEPT_ROOT": str(self.tmp / "kept"),
                    "PARTY_ADD_GAME_CAPTURE": "fake_capture:capture"}
        self.old = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)
        self.bars = dict(pag.BARS)
        (self.tmp / "dropins").mkdir()
        (self.tmp / "proj").mkdir()
        rules = self.tmp / "rules"
        rules.mkdir()
        # the title as it was added: its spec learnt from made-up pictures of shorter runs (12 s, not the tool's 20 s),
        # so a spec the scratch learns is never the same file — a learn written into this folder would change its
        # sha256 — its begin, its sidecar as learn writes it (the same bytes: only the spec can tell)
        es = pag._endscreen()
        pics = self.tmp / "made" / "pictures"
        kept = {}
        for role, tok in (("begin", "start"), ("other", "other"), ("end_P1", "end_P1"), ("end_P2", "end_P2")):
            sf = self.tmp / "made" / f"{role}.state"
            sf.parent.mkdir(parents=True, exist_ok=True)
            sf.write_text(state(tok))
            (pics / role).mkdir(parents=True)
            rows = fc.capture(sf, {}, pics / role, 12.0, pag.CAPTURE_EVERY)
            (pics / role / "index.csv").write_text("seconds,file\n" + "".join(f"{t:.2f},{n}\n" for t, n in rows))
            kept[role] = role
        labels = pag._labels(pics, kept, es)
        (pics / "labels.json").write_text(json.dumps(labels))
        spec, arrays, _rep = es.learn(pics, pics / "labels.json", "first", name=GAME)
        es.save_spec(spec, arrays, rules / f"{GAME}.endscreen.json")
        (rules / f"{GAME}.state").write_text(state("start"))
        (rules / f"{GAME}.party.json").write_text(json.dumps({"players": 2, "result": "winner"}, indent=1,
                                                             sort_keys=True) + "\n")
        shutil.rmtree(self.tmp / "made")
        k = self.tmp / "kept" / "t95"
        k.mkdir(parents=True)
        (k / "begin.state").write_text(state("start"))
        (k / "end_p1.state").write_text(state("end_P1"))
        (k / "end_p2.state").write_text(state("end_P2"))
        (k / "end_p1_b.state").write_text(state("end_P1", 7))
        (k / "SHA256SUMS").write_text("made-up\n")
        # the user's own slot 2 (a mid-match save), as the hub's slot index keeps it — read only by rehearse
        ra = self.tmp / "proj/data/games/retroarch"
        (ra / "states/Beetle PSX HW").mkdir(parents=True)
        (ra / "states/Beetle PSX HW/Made Up Three (USA).state2").write_text(state("other"))
        (ra / "privyhub_state_slots.json").write_text(json.dumps({"schema": 1, "games": {
            "ps1::games/ps1/made up three (usa).cue": {"slots": {"2": {
                "state_file": "data/games/retroarch/states/Beetle PSX HW/Made Up Three (USA).state2"}}}}}))
        self.slot2 = hashlib.sha256((ra / "states/Beetle PSX HW/Made Up Three (USA).state2").read_bytes()).hexdigest()

    def tearDown(self):
        self.pag.BARS.clear()
        self.pag.BARS.update(self.bars)
        self.hub.close()
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def rules_shas(self):
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((self.tmp / "rules").iterdir())}

    def added(self):
        args = ("T95", "--players", 2, "--system", "ps1", "--result", "winner", "--rules-players", 2)
        rc, text = _tool("register", *args)
        self.assertEqual(rc, 0, text)
        rc, text = _tool("learn", "T95")
        self.assertEqual(rc, 0, text)

    def verdict(self):
        v = json.loads((self.tmp / "ev/T95/rehearse.json").read_text())
        return v, {c["cell"]: c for c in v["cells"]}

    def test_0_refused_before_learn_and_for_a_new_title(self):
        rc, text = _tool("rehearse", "T95")
        self.assertEqual(rc, 2, text)                                     # no register
        _tool("register", "T95", "--players", 2, "--system", "ps1", "--result", "winner", "--rules-players", 2)
        rc, text = _tool("rehearse", "T95")
        self.assertEqual(rc, 2, text)                                     # no learn
        self.assertIn("learn has no PASS", text)
        b = json.loads((self.tmp / "home/T95/binding.json").read_text())
        b["described"] = False
        (self.tmp / "home/T95/binding.json").write_text(json.dumps(b))
        rc, text = _tool("rehearse", "T95")
        self.assertEqual(rc, 2, text)
        self.assertIn("already in the rules folder", text)

    def test_1_pass(self):
        self.added()
        before = self.rules_shas()
        rc, text = _tool("rehearse", "T95", "--collect", "other=2")
        v, c = self.verdict()
        self.assertEqual(rc, 0, text + (self.tmp / "ev/T95/rehearse.md").read_text())
        self.assertEqual(before, self.rules_shas())
        self.assertTrue(c["the real rules folder: every file's sha256 before = after"]["met"])
        self.assertEqual(c["the real rules folder: every file's sha256 before = after"]["read"], [3 + 1, 3 + 1, 0])
        self.assertTrue(c["the scratch removed"]["met"])
        self.assertEqual([p.name for p in (self.tmp / "home/T95").iterdir() if p.name.startswith("rehearse_")], [])
        self.assertTrue(any(k.startswith("learn: ") for k in c))
        self.assertEqual(c["learn's verdict in the scratch"]["read"], "PASS")
        for e in ("end_P1", "end_P2", "end_p1_b"):
            self.assertTrue(c[f"{e}: the scratch rules read it as the real rules"]["met"], e)
        self.assertEqual(c["end_p1_b: the scratch rules read it as the real rules"]["read"][1][0], "end_P1")
        self.assertEqual(v["recorded"]["roles"], {"begin": "begin.state", "end_P1": "end_p1.state",
                                                  "end_P2": "end_p2.state", "other": "slot 2"})
        self.assertEqual(v["recorded"]["missing"], [])
        self.assertEqual(self.slot2, hashlib.sha256((self.tmp / "proj/data/games/retroarch/states/Beetle PSX HW/"
                                                     "Made Up Three (USA).state2").read_bytes()).hexdigest())
        self.assertEqual(v["recorded"]["endings read, not a role"], ["end_p1_b"])
        page = (self.tmp / "ev/T95/rehearse.md").read_text()
        self.assertIn("Missing: none", page)
        self.assertIn("slot 2 -> other", page)
        self.assertIn("Endings read, not a role: end_p1_b", page)
        for n in (GAME, str(self.tmp), "Made Up Three"):
            self.assertNotIn(n, page + json.dumps(v) + text)
        rc2, _ = _tool("rehearse", "T95", "--collect", "other=2")         # twice: the same verdict, the same bytes
        self.assertEqual(rc2, 0)
        self.assertEqual(json.loads((self.tmp / "ev/T95/rehearse.json").read_text()), v)

    def test_2_an_extra_ending_that_is_another_players(self):
        (self.tmp / "kept/t95/end_p2_b.state").write_text(state("end_P1", 9))     # saved as P2 won, shows P1's screen
        self.added()
        rc, _ = _tool("rehearse", "T95", "--collect", "other=2")
        v, c = self.verdict()
        self.assertEqual(rc, 1)
        bad = [k for k, x in c.items() if not x["met"]]
        self.assertEqual(bad, ["end_p2_b: the scratch rules read it as the real rules"])
        self.assertEqual(c["end_p2_b: the scratch rules read it as the real rules"]["read"][1][0], "end_P1")

    def test_3_a_learn_bar_not_met_in_the_scratch(self):
        self.added()
        self.pag.BARS["margin_needed_min"] = (9.9, "test: past the made-up spec")
        before = self.rules_shas()
        rc, _ = _tool("rehearse", "T95", "--collect", "other=2")
        v, c = self.verdict()
        self.assertEqual(rc, 1)
        self.assertFalse(c["learn: margin_needed"]["met"])
        self.assertEqual(before, self.rules_shas())
        self.assertTrue(c["the scratch removed"]["met"])


    def test_4_no_other_kept_the_learner_cannot_run(self):
        """T88's kept folder as it is: no mid-match state. Said plainly: FAIL, other missing, the learner's words."""
        self.added()
        before = self.rules_shas()
        rc, text = _tool("rehearse", "T95")
        v, c = self.verdict()
        self.assertEqual(rc, 1, text)
        self.assertEqual(v["recorded"]["missing"], ["other"])
        self.assertIn("no other frames", c["learn ran in the scratch"]["read"])
        self.assertEqual(before, self.rules_shas())
        self.assertTrue(c["the scratch removed"]["met"])
        self.assertIn("Missing: other", (self.tmp / "ev/T95/rehearse.md").read_text())

    def test_5_collect_only_a_missing_role(self):
        self.added()
        rc, _ = _tool("rehearse", "T95", "--collect", "end_P1=2")       # the kept folder has end_P1
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
