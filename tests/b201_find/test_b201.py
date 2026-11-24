#!/usr/bin/env python3
"""B201 (host): `register --find <words>` takes the user's words as the user says them. A stub library (made-up names;
no title, no hub): the hub's `games` action as the companion answers it — `system` lists every title of the system
(paged by `offset` / `limit`, `total`), `q` applied only with `view=search` (so the tool's own match decides).

- `Words`: a part of the name -> one title; the name without its region -> one (even beside a longer name holding
  it); the whole name as the library lists it -> one; punctuation and case ignored; a title on the library's second
  page found.
- `Few`: two regions of one name -> refused "2 titles match", their names on stderr for the chat only, never on
  stdout, nothing written (no verdict, no binding).
- `None`: words no title holds -> refused; many matches (more than FIND_NAMED) -> refused, no names anywhere.
- `Ignored` (the queue's settle): the words passed as the library's `q` without `view=search` change nothing — the
  library answers every title (why T92's first run saw 72 for any words).
Temp dirs removed.

    python3 -m unittest discover -s tests/b201_find -v
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
sys.path[:0] = [str(ROOT / "tools")]

NAMES = ["Alpha Strike (USA)", "Alpha Strike II (USA)", "Beta Run (Europe)", "Gamma Ball (USA)", "Gamma Ball (Europe)",
         "Delta: The Run (USA) [!]", "Epsilon's Cup (Japan)"] + [f"Filler Title {i:02d} (USA)" for i in range(80)] + \
        ["Zeta Kick (USA)"]                                   # 88 titles: the last on the library's second page
ENV_KEYS = ("PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_H7_RULES", "PRIVYHUB_ADD_GAME_LOGS",
            "PRIVYHUB_ADD_GAME_HUB", "PRIVYHUB_ADD_GAME_DROPINS", "PRIVYHUB_ADD_GAME_PROJECT")


def library(method: str, action: str, query: dict | None = None, timeout: float = 30.0) -> dict:
    """The companion's `games` / `details` as it answers them (B201's settle): `q` only with `view=search`."""
    q = query or {}
    if action == "details":
        return {"code": 200, "body": {"relative_path": f"games/ps1/{q['id']}.bin", "title": ""}}
    if action != "games":
        return {"code": 404, "body": {}}
    games = [{"id": f"g{i:03d}", "title": n} for i, n in enumerate(NAMES)]
    if q.get("view") == "search":
        terms = str(q.get("q", "")).casefold().split()
        games = [g for g in games if terms and all(t in g["title"].casefold() for t in terms)]
    offset = int(q.get("offset", 0) or 0)
    limit = min(80, int(q.get("limit", 80) or 80))
    if "offset" not in q and len(games) > 80:
        return {"code": 200, "body": {"total": len(games), "nodes": [
            {"id": "page_01", "name": "Page 01", "node_type": "category"}]}}
    page = games[offset:offset + limit]
    return {"code": 200, "body": {"total": len(games), "nodes": [
        {"id": g["id"], "name": g["title"], "node_type": "game"} for g in page]}}


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="b201_"))
        cls.old = {k: os.environ.get(k) for k in ENV_KEYS}
        os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(cls.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(cls.tmp / "ev"),
                           "PRIVYHUB_H7_RULES": str(cls.tmp / "rules"), "PRIVYHUB_ADD_GAME_LOGS": str(cls.tmp / "logs"),
                           "PRIVYHUB_ADD_GAME_HUB": "http://127.0.0.1:9", "PRIVYHUB_ADD_GAME_DROPINS": str(cls.tmp / "dropins"),
                           "PRIVYHUB_ADD_GAME_PROJECT": str(cls.tmp / "project")})
        import party_add_game as pag
        cls.pag = pag
        cls.real_hub = pag.hub
        pag.hub = library

    @classmethod
    def tearDownClass(cls):
        cls.pag.hub = cls.real_hub
        for k, v in cls.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def find(self, words: str) -> str:
        self.pag.GUARD.names.clear()
        return self.pag._find_title("ps1", words)["title"]

    def refused(self, words: str) -> tuple[str, str, str]:
        self.pag.GUARD.names.clear()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            with self.assertRaises(self.pag.Refused) as cm:
                self.pag._find_title("ps1", words)
        return str(cm.exception), err.getvalue(), words

    def register(self, words: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = self.pag.main(["register", "T61", "--players", "2", "--system", "ps1", "--result", "score",
                                "--find", words, "--setup", "none"])
        return rc, out.getvalue(), err.getvalue()


class Words(Base):
    def test_1_a_part_of_the_name(self):
        self.assertEqual(self.find("beta"), "Beta Run (Europe)")
        self.assertEqual(self.find("zeta"), "Zeta Kick (USA)")             # on the library's second page

    def test_2_the_name_without_its_region(self):
        self.assertEqual(self.find("Alpha Strike"), "Alpha Strike (USA)")  # beside "Alpha Strike II (USA)"
        self.assertEqual(self.find("delta the run"), "Delta: The Run (USA) [!]")
        self.assertEqual(self.find("Epsilons Cup"), "Epsilon's Cup (Japan)")

    def test_3_the_whole_name(self):
        self.assertEqual(self.find("Alpha Strike II (USA)"), "Alpha Strike II (USA)")
        self.assertEqual(self.find("gamma ball (europe)"), "Gamma Ball (Europe)")


class Few(Base):
    def test_1_two_regions_named_for_the_chat_only(self):
        why, err, _w = self.refused("gamma")
        self.assertIn("2 titles match", why)
        self.assertNotIn("Gamma", why)
        self.assertIn("Gamma Ball (USA)", err)
        self.assertIn("Gamma Ball (Europe)", err)
        self.assertIn("never write", err)
        rc, out, err = self.register("gamma ball")
        self.assertEqual(rc, 2, out)
        self.assertIn("REFUSED — 2 titles match", out)
        self.assertNotIn("amma", out)
        self.assertFalse((self.tmp / "ev").exists() and any((self.tmp / "ev").rglob("*")))
        self.assertFalse((self.tmp / "home").exists() and any((self.tmp / "home").rglob("binding.json")))


class Nothing(Base):
    def test_1_no_title_and_too_many(self):
        why, err, _w = self.refused("omega")
        self.assertIn("no title of the system matches", why)
        why, err, _w = self.refused("filler")
        self.assertIn("80 titles match", why)
        self.assertEqual(err, "")


class Ignored(unittest.TestCase):
    def test_1_the_librarys_q_needs_its_search_view(self):
        every = library("GET", "games", {"system": "ps1", "q": "zeta", "offset": 0, "limit": 80})["body"]["total"]
        self.assertEqual(every, len(NAMES))
        self.assertEqual(library("GET", "games", {"view": "search", "q": "zeta"})["body"]["total"], 1)


if __name__ == "__main__":
    unittest.main()
