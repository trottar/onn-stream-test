#!/usr/bin/env python3
"""B64 (host): the first heartbeat after a start carries the previous game's joined count with no claim -- its
`pad_slots` change row is tagged `stale: true` (and the heartbeat row `pad_slots_stale`); real joins are not. HOME-7's
sequence replayed with a fake recovery; no files outside the temp dirs (removed at exit).

    python3 -m unittest discover -s tests/b64_stale_pad_rows -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import pad_slots as pslots  # noqa: E402

MAP2 = "0:aaaaaa:sony,1:bbbbbb:sony"


class Rec:
    def __init__(self):
        self.rows = []

    def _log(self, event, **fields):
        self.rows.append({"event": event, **fields})


def beat(log, rec, seq, joined=None, claims=None, raw=MAP2):
    values = {"sequence": seq}
    log.heartbeat(rec, raw, values, claims=claims, players_joined=joined)
    return values


class Stale(unittest.TestCase):
    def test_homes_sequence(self):
        rec, log = Rec(), pslots.SlotsLog()
        log.start(rec, MAP2)                                              # the start: no join fields
        v1 = beat(log, rec, 1, joined=2)                                  # the carry-over, no claims
        v2 = beat(log, rec, 2, joined=2)                                  # the same again: no new row
        v3 = beat(log, rec, 3, joined=1, claims="0:p")                    # the first real join
        v4 = beat(log, rec, 4, joined=2, claims="0:p,1:p")
        changes = [r for r in rec.rows if r["when"] == "change"]
        self.assertEqual([(r["heartbeat_sequence"], r.get("stale")) for r in changes], [(1, True), (3, None), (4, None)])
        self.assertTrue(v1.get("pad_slots_stale"))
        self.assertTrue(v2.get("pad_slots_stale"))
        self.assertNotIn("pad_slots_stale", v3)
        self.assertNotIn("pad_slots_stale", v4)

    def test_a_restart_is_tagged_again(self):
        rec, log = Rec(), pslots.SlotsLog()
        log.start(rec, MAP2)
        beat(log, rec, 1, joined=2)
        beat(log, rec, 3, joined=2, claims="0:p,1:p")
        log.start(rec, MAP2)                                              # the next game
        beat(log, rec, 1, joined=2)
        changes = [r for r in rec.rows if r["when"] == "change"]
        self.assertEqual([r.get("stale") for r in changes], [True, None, True])

    def test_not_tagged(self):
        rec, log = Rec(), pslots.SlotsLog()
        log.start(rec, MAP2)
        beat(log, rec, 1, joined=2, claims="0:p,1:p")                     # a claimed row before session_started
        beat(log, rec, 2)                                                 # no join key (B46's client): no row field
        self.assertTrue(all("stale" not in r for r in rec.rows))
        rec2, log2 = Rec(), pslots.SlotsLog()
        log2.start(rec2, MAP2)
        v = beat(log2, rec2, 1, joined=0)
        self.assertNotIn("pad_slots_stale", v)
        self.assertTrue(all("stale" not in r for r in rec2.rows))

    def test_after_a_claim_an_unclaimed_row_is_not_stale(self):
        rec, log = Rec(), pslots.SlotsLog()
        log.start(rec, MAP2)
        beat(log, rec, 1, joined=1, claims="0:p")
        v = beat(log, rec, 2, joined=2, claims="")                       # claims gone mid-session: not a carry-over
        self.assertNotIn("pad_slots_stale", v)
        self.assertTrue(all("stale" not in r for r in rec.rows))

    def test_no_join_client_is_byte_for_byte(self):
        rec, log = Rec(), pslots.SlotsLog()
        log.start(rec, MAP2)
        v = beat(log, rec, 1, raw="0:aaaaaa:sony")
        self.assertEqual(rec.rows[-1], {"event": "pad_slots", "when": "change", "slots": [
            {"slot": 0, "pad": "aaaaaa", "class": "sony"}], "count": 1, "heartbeat_sequence": 1})
        self.assertEqual(set(v), {"sequence", "pad_slots"})


if __name__ == "__main__":
    unittest.main()
