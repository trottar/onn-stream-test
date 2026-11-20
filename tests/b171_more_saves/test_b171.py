#!/usr/bin/env python3
"""B171 (host): several saves per ending; learn says which save to add — the add-a-game tool on made-up near-alike and
far-apart end screens (`near_capture.py`), a made-up hub on loopback (the library's one made-up title, its game file),
the user's made-up slots (the slot index as the hub keeps it). Nothing of the hub's read.

- **register asks for two saves per ending:** one per ending → FAIL, `end_P1_2`, `end_P2_2` missing; a role past the
  cap (`end_P1_5`) refused; an ending of a player the title has not → "another kind".
- **near-alike, two per ending of the same look** (the same characters in every match) → learn FAIL on its own bars
  and **one plain line naming the save to add**; each named save collected from a match with other characters → learn
  again on **the same bars** → PASS, no line; only the added save captured each time.
- **far-apart screens pass on two saves per ending.**
- **the cap:** two endings whose screens look the same → asked up to `_4` each, then "cannot be told apart this way",
  no role named, FAIL.
- **rehearse, T88's shape** (a made-up title already added; its kept folder: begin, one save per ending, a mid-fight
  extra): FAIL naming `end_P1_2`, the mid-fight extra "not an end screen", below two saves `end_P1_2`, `end_P2_2`;
  each named save collected (the slot saved over between: the tool's kept copy used) → PASS; the real rules folder's
  every sha256 before = after; a kept extra the real rules end on is one more source.
- no title, id or path in anything written or printed; learn twice → the same bytes. Temp dirs removed.

    python3 -m unittest discover -s tests/b171_more_saves -v
"""
from __future__ import annotations

import contextlib
import hashlib
import http.server
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))
import near_capture as nc  # noqa: E402

GAME = "madeupnear1"
WORDS = "Near Alike Made Up"
REL = "games/ps1/Near Alike Made Up (USA).cue"
REG = ("register", "T80", "--players", 2, "--system", "ps1", "--result", "winner", "--find", WORDS, "--setup", "none")


class NearHub:
    """The routes register and rehearse call: `games` (one made-up title), `details` (its made-up game file)."""

    def __init__(self):
        class H(http.server.BaseHTTPRequestHandler):
            def _answer(self):
                action = urlparse(self.path).path.rsplit("/", 1)[-1]
                body = {"ok": True}
                if action == "games":
                    body = {"nodes": [{"id": GAME, "node_type": "game", "name": WORDS}]}
                elif action == "details":
                    body = {"relative_path": REL, "title": WORDS}
                raw = json.dumps(body).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = _answer

            def log_message(self, *a):
                pass

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"

    def close(self):
        self.srv.shutdown()
        self.srv.server_close()


def _tool(*argv):
    import party_add_game as pag
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(a) for a in argv])
    return rc, buf.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        import party_add_game as pag
        self.pag = pag
        self.tmp = Path(tempfile.mkdtemp(prefix="b171_"))
        self.hub = NearHub()
        self.env = {"PRIVYHUB_ADD_GAME_HOME": str(self.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(self.tmp / "ev"),
                    "PRIVYHUB_ADD_GAME_PROJECT": str(self.tmp / "proj"), "PRIVYHUB_H7_RULES": str(self.tmp / "rules"),
                    "PRIVYHUB_ADD_GAME_DROPINS": str(self.tmp / "dropins"), "PRIVYHUB_ADD_GAME_SYSTEMCTL": "true",
                    "PRIVYHUB_ADD_GAME_HUB": self.hub.url, "PRIVYHUB_ADD_GAME_KEPT_ROOT": str(self.tmp / "kept"),
                    "PARTY_ADD_GAME_CAPTURE": "near_capture:capture"}
        self.old = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)
        self.bars = json.dumps(pag.BARS, sort_keys=True)
        (self.tmp / "dropins").mkdir()                       # eighteen made-up lines, never the hub's own
        for i in range(18):
            (self.tmp / "dropins" / f"line{i:02d}.conf").write_text(f"[Service]\nEnvironment=PRIVYHUB_LINE{i:02d}=1\n")
        (self.tmp / "rules").mkdir()
        (self.tmp / "proj/data/games/retroarch/states/Beetle PSX HW").mkdir(parents=True)
        nc.CALLS.clear()
        self.n = 0

    def tearDown(self):
        self.assertEqual(json.dumps(self.pag.BARS, sort_keys=True), self.bars)     # no bar changed, ever
        self.hub.close()
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def save(self, slot: int, kind: str, look: int = 0, far: bool = False) -> None:
        """The user's SAVE to slot `slot` (the slot index as the hub keeps it); every save other bytes."""
        self.n += 1
        ra = self.tmp / "proj/data/games/retroarch"
        f = ra / "states/Beetle PSX HW" / f"Near Alike Made Up (USA).state{slot}"
        f.write_text(nc.state(kind, look, far, self.n))
        ix = ra / "privyhub_state_slots.json"
        idx = json.loads(ix.read_text()) if ix.is_file() else {"schema": 1, "games": {}}
        ent = idx["games"].setdefault(f"ps1::{REL.casefold()}", {"slots": {}})
        ent["slots"][str(slot)] = {"state_file": str(f.relative_to(self.tmp / "proj"))}
        ix.write_text(json.dumps(idx))

    def collect(self, saves: list) -> tuple[int, str]:
        """A round: [(role, kind, look, far)], to slots 1, 2, 3 in turn, then register --collect each."""
        args = []
        for slot, (role, kind, look, far) in enumerate(saves, 1):
            self.save(slot, kind, look, far)
            args += ["--collect", f"{role}={slot}"]
        return _tool(*REG, *args)

    def verdict(self, stage: str, code: str = "T80") -> tuple[dict, dict, str]:
        v = json.loads((self.tmp / f"ev/{code}/{stage}.json").read_text())
        return v, {c["cell"]: c for c in v["cells"]}, (self.tmp / f"ev/{code}/{stage}.md").read_text()

    def written(self) -> str:
        return "\n".join(p.read_text() for p in sorted((self.tmp / "ev").rglob("*")) if p.is_file())

    def names_absent(self, text: str) -> None:
        for n in (GAME, WORDS, "Near Alike", str(self.tmp)):
            self.assertNotIn(n.casefold(), text.casefold())

    def two_per_ending(self, look1=1, look2=1, far=False) -> None:
        rc, text = self.collect([("begin", "start", 0, False), ("other", "other", 0, False),
                                 ("end_P1", "end_P1", look1, far)])
        rc, text = self.collect([("end_P2", "end_P2", look1, far), ("end_P1_2", "end_P1", look2, far),
                                 ("end_P2_2", "end_P2", look2, far)])
        self.assertEqual(rc, 0, text)

    def follow_asks(self, kinds: dict, looks, most: int = 6) -> tuple[list, int, str]:
        """learn; while its line names a save: that save from the next look, collected; learn again (the same bars)."""
        asked, looks = [], iter(looks)
        rc, out = _tool("learn", "T80")
        while rc != 0 and len(asked) < most:
            v, _c, page = self.verdict("learn")
            role = (v.get("recorded") or {}).get("one more save")
            if not role:
                break
            asked.append(role)
            ending = self.pag._role_class(role)
            nc.CALLS.clear()
            rc2, text = self.collect([(role, kinds[ending], next(looks), False)])
            self.assertEqual(rc2, 0, text)
            rc, out = _tool("learn", "T80")
            self.assertEqual([k for k, _l in nc.CALLS], [kinds[ending]], "only the added save captured")
        return asked, rc, out


class Register(Base):
    def test_one_save_per_ending_asks_for_the_second(self):
        self.collect([("begin", "start", 0, False), ("other", "other", 0, False), ("end_P1", "end_P1", 1, False)])
        rc, text = self.collect([("end_P2", "end_P2", 1, False)])
        v, c, _page = self.verdict("register")
        self.assertEqual(rc, 1, text)
        self.assertEqual(c["missing"]["read"], ["end_P1_2", "end_P2_2"])
        self.assertEqual(_tool("learn", "T80")[0], 2)                      # learn refused without register's PASS

    def test_past_the_cap_refused_and_another_kind(self):
        self.two_per_ending(1, 2)
        self.save(1, "end_P1", 3)
        self.assertEqual(_tool(*REG, "--collect", "end_P1_5=1")[0], 2)    # the most is end_P1_4
        rc, text = _tool(*REG, "--collect", "end_P3_2=1")
        v, c, _page = self.verdict("register")
        self.assertEqual(rc, 1, text)
        self.assertEqual(c["no ending of another kind"]["read"], ["end_P3_2"])


class Learn(Base):
    def test_near_alike_asks_then_passes_on_the_same_bars(self):
        self.two_per_ending(1, 1)                                          # the same characters in every match
        rc, out = _tool("learn", "T80")
        v, c, page = self.verdict("learn")
        self.assertEqual(rc, 1, out)
        bad = [k for k, x in c.items() if not x["met"]]
        self.assertTrue({"every class separable", "margin_needed"} & set(bad), bad)
        self.assertEqual(v["recorded"], {"one more save": "end_P1_3"})
        line = ("One more save: end_P1_3 — the screen after a match player 1 won, from a match not saved yet (other "
                "characters or another stage than its saves kept); save it to a free slot, then register T80 … "
                "--collect end_P1_3=<slot> and learn T80 again.")
        self.assertIn(line, page)
        self.assertIn(line, out)
        asked, rc, out = self.follow_asks({"end_P1": "end_P1", "end_P2": "end_P2"}, looks=[2, 3, 4, 5])
        v, c, page = self.verdict("learn")
        self.assertEqual(rc, 0, out + page)
        self.assertEqual(asked, ASKED_NEAR)
        self.assertNotIn("One more save", page + out)
        self.assertNotIn("recorded", v)
        self.assertTrue(c["margin_needed"]["met"])
        self.assertEqual(c["margin_needed"]["bar"], ">= 0.0796 (T89's kept spec (the lower of T88 0.0921 / T89 0.0796))")
        self.assertTrue((self.tmp / f"rules/{GAME}.endscreen.json").is_file())    # only a pass reaches the rules
        self.names_absent(self.written() + out)
        before = {p.name: p.read_bytes() for p in (self.tmp / "ev/T80").iterdir()}
        rc2, _ = _tool("learn", "T80")                                      # twice: the same verdict, the same bytes
        self.assertEqual(rc2, 0)
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.tmp / "ev/T80").iterdir()})

    def test_far_apart_pass_on_two(self):
        self.two_per_ending(1, 1, far=True)
        rc, out = _tool("learn", "T80")
        v, c, page = self.verdict("learn")
        self.assertEqual(rc, 0, out + page)
        self.assertNotIn("One more save", page)

    def test_the_cap(self):
        """Two endings whose screens are the same (who won not shown): asked to the cap, then said plainly."""
        self.collect([("begin", "start", 0, False), ("other", "other", 0, False), ("end_P1", "same", 1, False)])
        self.collect([("end_P2", "same", 1, False), ("end_P1_2", "same", 2, False), ("end_P2_2", "same", 2, False)])
        asked, rc, out = self.follow_asks({"end_P1": "same", "end_P2": "same"}, looks=[3, 3, 4, 4, 5, 5], most=6)
        v, c, page = self.verdict("learn")
        self.assertEqual(rc, 1)
        self.assertEqual(asked, ["end_P1_3", "end_P2_3", "end_P1_4", "end_P2_4"])
        self.assertEqual(v["recorded"], {"cannot be told apart": ["end_P1", "end_P2"]})
        self.assertIn("The end screens cannot be told apart this way: end_P1, end_P2 have 4 saves each from different "
                      "matches and learn still does not meet its bars. Instead: another mode whose end screen shows who "
                      "won by player, or save each ending on another screen that shows it, and start the title's saves "
                      "again.", page)
        self.assertNotIn("One more save", page)
        self.assertFalse((self.tmp / f"rules/{GAME}.endscreen.json").exists())

    def test_no_line_when_the_pictures_fail(self):
        self.two_per_ending(1, 1)
        os.environ["PARTY_ADD_GAME_CAPTURE"] = "near_capture:fails"
        rc, out = _tool("learn", "T80")
        v, c, page = self.verdict("learn")
        self.assertEqual(rc, 1)
        self.assertIn("pictures made", c)
        self.assertNotIn("One more save", page + out)


class Rehearse(Base):
    """T88's shape: a made-up title already added (its rules learnt from three looks per ending — three sittings, the
    kept saves' among them);
    its kept folder: begin, one save per ending, a mid-fight extra."""

    def setUp(self):
        super().setUp()
        pag = self.pag
        es = pag._endscreen()
        pics = self.tmp / "made" / "pictures"
        kept = {}
        plan = [("begin", "start", 0), ("other", "other", 0)] + \
               [(f"end_P{k}" + ("" if s == 1 else f"_{s}"), f"end_P{k}", look) for k in (1, 2)
                for s, look in ((1, 1), (2, 11), (3, 12))]          # the kept saves among them, as T88's V1 sitting
        for role, kind, look in plan:
            sf = self.tmp / "made" / f"{role}.state"
            sf.parent.mkdir(parents=True, exist_ok=True)
            sf.write_text(nc.state(kind, look))
            (pics / role).mkdir(parents=True)
            rows = nc.capture(sf, {}, pics / role, 12.0, pag.CAPTURE_EVERY)
            (pics / role / "index.csv").write_text("seconds,file\n" + "".join(f"{t:.2f},{n}\n" for t, n in rows))
            kept[role] = role
        labels = pag._labels(pics, kept, es)
        (pics / "labels.json").write_text(json.dumps(labels))
        spec, arrays, _rep = es.learn(pics, pics / "labels.json", "first", name=GAME)
        self.assertGreaterEqual(spec["margin_needed"], pag.BARS["margin_needed_min"][0])   # the real rules are good
        es.save_spec(spec, arrays, self.tmp / "rules" / f"{GAME}.endscreen.json")
        (self.tmp / "rules" / f"{GAME}.state").write_text(nc.state("start"))
        (self.tmp / "rules" / f"{GAME}.party.json").write_text(json.dumps({"players": 2, "result": "winner"}, indent=1,
                                                                          sort_keys=True) + "\n")
        shutil.rmtree(self.tmp / "made")
        k = self.tmp / "kept" / "t85"
        k.mkdir(parents=True)
        (k / "begin.state").write_text(nc.state("start"))
        (k / "end_p1.state").write_text(nc.state("end_P1", 1))
        (k / "end_p2.state").write_text(nc.state("end_P2", 1, n=1))
        (k / "end_p1_b.state").write_text(nc.state("mid", 0))                 # mid-fight: not an end screen
        self.kept_sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in k.iterdir()}
        args = ("T85", "--players", 2, "--system", "ps1", "--result", "winner", "--rules-players", 2)
        self.assertEqual(_tool("register", *args)[0], 0)
        self.assertEqual(_tool("learn", "T85")[0], 0)

    def rules_shas(self):
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((self.tmp / "rules").iterdir())}

    def test_t88_shape_asks_then_passes(self):
        before = self.rules_shas()
        self.save(2, "other")
        rc, out = _tool("rehearse", "T85", "--collect", "other=2")
        v, c, page = self.verdict("rehearse", "T85")
        self.assertEqual(rc, 1, out)
        self.assertEqual(v["recorded"]["one more save"], "end_P1_2")
        self.assertEqual(v["recorded"]["below two saves per ending"], ["end_P1_2", "end_P2_2"])
        self.assertEqual(v["recorded"]["endings read, not a role"], ["end_p1_b"])
        self.assertIn("end_p1_b (not an end screen to the real rules)", page)
        self.assertIn("then rehearse T85 --collect end_P1_2=<slot>.", page)
        self.assertIn("then rehearse T85 --collect end_P1_2=<slot>.", out)
        self.assertTrue(c["the real rules folder: every file's sha256 before = after"]["met"])
        asked = ["end_P1_2"]
        looks = iter([2, 3, 4, 5])
        for _ in range(4):
            role = v["recorded"].get("one more save")
            if rc == 0 or not role:
                break
            self.save(2, self.pag._role_class(role), next(looks))        # slot 2 saved over: other is the tool's copy
            rc, out = _tool("rehearse", "T85", "--collect", f"{role}=2")
            v, c, page = self.verdict("rehearse", "T85")
            if v["recorded"].get("one more save"):
                asked.append(v["recorded"]["one more save"])
        self.assertEqual(rc, 0, out + page)
        self.assertEqual(asked, ASKED_REHEARSE)
        self.assertEqual(v["recorded"]["roles"]["other"], "a save collected before")
        self.assertEqual(before, self.rules_shas())
        self.assertTrue(c["the scratch removed"]["met"])
        self.assertEqual(self.kept_sha, {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in (self.tmp / "kept/t85").iterdir()})
        self.names_absent(self.written() + out)

    def test_a_kept_extra_that_is_an_end_screen_is_a_source(self):
        (self.tmp / "kept/t85/end_p2_b.state").write_text(nc.state("end_P2", 5))
        self.save(2, "other")
        rc, out = _tool("rehearse", "T85", "--collect", "other=2")
        v, c, page = self.verdict("rehearse", "T85")
        self.assertEqual(v["recorded"]["roles"]["end_P2_2"], "end_p2_b.state")
        self.assertEqual(v["recorded"]["endings read, not a role"], ["end_p1_b"])
        self.assertEqual(v["recorded"]["below two saves per ending"], ["end_P1_2"])
        self.assertTrue(c["end_P2_2: the scratch rules read it as the real rules"]["read"][1][0] == "end_P2")


ASKED_NEAR = ["end_P1_3", "end_P2_3"]   # as the first run gave them (the learner decides; the bars never change)
ASKED_REHEARSE = ["end_P1_2", "end_P2_2"]


if __name__ == "__main__":
    unittest.main()
