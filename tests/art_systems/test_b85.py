#!/usr/bin/env python3
"""B85 (host): the cheat list cleaned for the TV, through the plugin as the companion constructs it.

B83's harness (a child `python3 -I` on B82's fixture tree with its own companion/; `from plugins import PLUGINS`; the
emulators faked; the network blocked and counted). Fixture `.cht` files with made-up names and codes in every shape
the hub's lists have: a player tag, a bare "P2" row, a "must be on" code, a lone joypad conditional, a heading row,
"Part n" parts, an identical repeat, a repeat with another code, a trailing code in the name. The real
`handle_post_request("cheat-catalog")` and the real `handle_post("launch")`. Temp dirs removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b85.py' -v
"""

from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _tmp_cleanup  # noqa: E402,F401
import test_b83 as b83  # noqa: E402

FLAGS = b83.FLAGS
N64_TITLE = ("n64", "Alpha Racer (USA)")
PS1_TITLE = ("ps1", "Juliet Run (USA)")
N64_ROWS = [
    ("Infinite Health P1", "80001000 0063"),          # 0  player 1
    ("P2", "80002000 0063"),                          # 1  a bare row: "Infinite Health — Player 2"
    ("Must Be On", "F1001000 2400"),                  # 2  required: hidden, applied with any pick
    ("Activator 1 (P1)", "D01F0000 0020"),            # 3  a lone conditional: hidden, never applied
    ("Weapons", ""),                                  # 4  a heading row: hidden
    ("Moon Jump (Part 1)", "81003000 0001"),          # 5  parts 5 + 6: one entry
    ("Moon Jump (Part 2)", "81003002 0001"),          # 6
    ("Max Money", "80004000 00FF"),                   # 7
    ("Max Money", "80004000 00FF"),                   # 8  identical: folded
    ("Max Money", "80005000 00FF"),                   # 9  another code: "Max Money — variant 2"
    ("Level Select [8000ABCD 0001]", "8000ABCD 0001"),  # 10 the trailing code tidied
    ("Infinite Lives 2P", "80006000 0009"),           # 11 player 2
]
PS1_ROWS = [
    ("Enable Code (M)", "C0001000 0001"),             # 0  required
    ("Infinite HP P1", "80010000 03E7"),              # 1
    ("Infinite HP P2", "80010100 03E7"),              # 2
]

EXTRA = r'''
elif mode == "catalog":
    out["catalog"] = g.handle_post_request("cheat-catalog", args["query"], "127.0.0.1")
    out["today"] = {"ok": True, "plugin": "games", **m.cheat_catalog(game(gid))}
elif mode == "post_launch":
    retroarch_fakes()
    r = g.handle_post("launch", args["query"])
    out["active"] = (r.get("active") if isinstance(r, dict) else None)
    out["enabled"] = (m._active_cheat_session or {}).get("enabled_cheat_indexes")
    out["cheat_apply"] = calls["cheat_apply"]
'''
CHILD = b83.CHILD.replace('out["popen"] = calls["popen"]', EXTRA.strip("\n") + '\nout["popen"] = calls["popen"]', 1)


def cht(rows) -> bytes:
    out = [f"cheats = {len(rows)}", ""]
    for i, (desc, code) in enumerate(rows):
        out += [f'cheat{i}_desc = "{desc}"', f'cheat{i}_code = "{code}"', f"cheat{i}_enable = false", ""]
    return "\n".join(out).encode()


def manifest(root: Path, records: list[tuple[str, str, str, bytes]]) -> None:
    """data/games/cheats.json as the cheat tool writes it, for (system, id, relative path, .cht bytes)."""
    games = {}
    for system, gid, rel_path, data in records:
        rel = f"data/games/user_content/{gid}/cheats/libretro/made-up.cht"
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_bytes(data)
        games[gid] = {"id": gid, "system": system, "relative_path": rel_path, "status": "cached", "provider": "libretro",
                      "files": [{"local_path": rel, "local_filename": "made-up.cht",
                                 "local_sha256": hashlib.sha256(data).hexdigest().upper(),
                                 "cheat_count": data.count(b"_desc")}]}
    (root / "data/games/cheats.json").write_text(json.dumps({"games": games}), encoding="utf-8")


# today's reader refuses a whole file holding a heading row (addendum 1): the knob-0 comparisons use this one
N64_ROWS_NO_HEADING = [r if r[1] else ("Weapons", "80007000 0001") for r in N64_ROWS]


def tree(n64_rows=N64_ROWS):
    root, ids = b83.tree()
    rel_of = {g[2]: g[3] for g in b83.b82.scan(root, FLAGS)["games"]}    # the manifest's identity check
    manifest(root, [("n64", ids[N64_TITLE], rel_of[ids[N64_TITLE]], cht(n64_rows)),
                    ("ps1", ids[PS1_TITLE], rel_of[ids[PS1_TITLE]], cht(PS1_ROWS))])
    return root, ids


def run(root, env, mode, args):
    old = b83.CHILD
    b83.CHILD = CHILD
    try:
        r, attempts, _ = b83.run(root, env, mode, args)
    finally:
        b83.CHILD = old
    return b83.out_of(r), attempts


class Catalog(unittest.TestCase):
    def test_the_n64_list_cleaned(self):
        root, ids = tree()
        gid = ids[N64_TITLE]
        out, attempts = run(root, FLAGS, "catalog", {"id": gid, "query": f"id={gid}"})
        self.assertEqual(attempts, 0)
        src = out["catalog"]["sources"][0]
        shown = [(e["index"], e["description"], e["group"]) for e in src["entries"]]
        self.assertEqual(shown, [
            (0, "Infinite Health Player 1", "player1"),
            (1, "Infinite Health — Player 2", "player2"),
            (5, "Moon Jump", "general"),
            (7, "Max Money", "general"),
            (9, "Max Money — variant 2", "general"),
            (10, "Level Select", "general"),
            (11, "Infinite Lives Player 2", "player2"),
        ])
        self.assertEqual((src["raw_count"], src["shown_count"], src["folded_parts"]), (12, 7, 1))
        self.assertEqual(src["hidden"], {"header": 1, "trigger": 1, "enabler": 1, "duplicate": 1})
        by = {e["index"]: e for e in src["entries"]}
        self.assertEqual(by[5]["parts"], [5, 6])                  # a split cheat: one entry, both parts
        self.assertEqual(by[9]["variant_of"], 7)
        self.assertEqual(by[0]["requires"], [2])                   # the "must be on" code goes with any pick
        self.assertNotIn(2, by)                                    # …and is not shown
        self.assertNotIn(3, by)                                    # the lone conditional: neither
        self.assertTrue(out["catalog"]["clean"])

    def test_raw_and_the_knob_zero_are_todays_list(self):
        root, ids = tree(N64_ROWS_NO_HEADING)
        gid = ids[N64_TITLE]
        raw, _ = run(root, FLAGS, "catalog", {"id": gid, "query": f"id={gid}&raw=1"})
        self.assertEqual(json.dumps(raw["catalog"], sort_keys=True), json.dumps(raw["today"], sort_keys=True))
        off, _ = run(root, {**FLAGS, "PRIVYHUB_CHEAT_CLEAN": "0"}, "catalog", {"id": gid, "query": f"id={gid}"})
        self.assertEqual(json.dumps(off["catalog"], sort_keys=True), json.dumps(off["today"], sort_keys=True))
        self.assertEqual(len(off["catalog"]["sources"][0]["entries"]), 12)
        self.assertEqual(json.dumps(off["catalog"], sort_keys=True), json.dumps(raw["catalog"], sort_keys=True))

    def test_a_heading_row_is_read_with_the_knob_and_refused_without(self):
        root, ids = tree()                                      # the file holds a heading row (a name, no code)
        gid = ids[N64_TITLE]
        raw, _ = run(root, FLAGS, "catalog", {"id": gid, "query": f"id={gid}&raw=1"})
        self.assertEqual(len(raw["catalog"]["sources"][0]["entries"]), 12)
        r, _a, _s = b83.run(root, {**FLAGS, "PRIVYHUB_CHEAT_CLEAN": "0"}, "ids")   # (the companion starts)
        old = b83.CHILD
        b83.CHILD = CHILD
        try:
            r, _a, _s = b83.run(root, {**FLAGS, "PRIVYHUB_CHEAT_CLEAN": "0"}, "catalog", {"id": gid, "query": f"id={gid}"})
        finally:
            b83.CHILD = old
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("missing a cheat description or payload", r.stderr)        # today's refusal, unchanged

    def test_gamecube_tidied_nothing_hidden_and_the_users_file_as_it_is(self):
        root, ids = tree()
        gc = ids[("gamecube", "Foxtrot Sun (Europe) (En,Fr,De)")]
        out, _ = run(root, FLAGS, "catalog", {"id": gc, "query": f"id={gc}"})
        src = out["catalog"]["sources"][0]
        self.assertEqual(src["raw_count"], src["shown_count"])
        self.assertEqual(sorted(e["description"] for e in src["entries"]),
                         sorted(e["description"] for e in out["today"]["sources"][0]["entries"]))
        ps1 = ids[PS1_TITLE]
        folder = root / "data/games/retroarch/cheats/ps1/Juliet Run (USA)"
        folder.mkdir(parents=True)
        (folder / "mine P1.cht").write_bytes(cht([("My Own P1 (M)", "D0000000 0000")]))
        out, _ = run(root, FLAGS, "catalog", {"id": ps1, "query": f"id={ps1}"})
        user = [s for s in out["catalog"]["sources"] if s["provider"] == "user"][0]
        self.assertEqual([(e["description"], e["group"]) for e in user["entries"]], [("My Own P1 (M)", "yours")])


class Launch(unittest.TestCase):
    def test_a_cleaned_selection_stages_the_real_indexes_n64(self):
        root, ids = tree()
        gid = ids[N64_TITLE]
        out, attempts = run(root, FLAGS, "post_launch", {"id": gid, "query": f"id={gid}&cheat_source=0&cheat_indexes=5,0"})
        self.assertEqual(out["enabled"], [0, 2, 5, 6])            # both parts of the split cheat + the required code
        self.assertEqual((out["cheat_apply"], attempts), (1, 0))

    def test_a_cleaned_selection_stages_the_real_indexes_ps1(self):
        root, ids = tree()
        gid = ids[PS1_TITLE]
        out, _ = run(root, FLAGS, "post_launch", {"id": gid, "query": f"id={gid}&cheat_source=0&cheat_indexes=2"})
        self.assertEqual(out["enabled"], [0, 2])

    def test_the_knob_zero_and_cheat_raw_launch_as_sent(self):
        root, ids = tree(N64_ROWS_NO_HEADING)
        gid = ids[N64_TITLE]
        off, _ = run(root, {**FLAGS, "PRIVYHUB_CHEAT_CLEAN": "0"}, "post_launch",
                     {"id": gid, "query": f"id={gid}&cheat_source=0&cheat_indexes=5,0"})
        raw, _ = run(root, FLAGS, "post_launch", {"id": gid, "query": f"id={gid}&cheat_source=0&cheat_indexes=5,0&cheat_raw=1"})
        self.assertEqual(sorted(off["enabled"]), [0, 5])
        self.assertEqual(off["enabled"], raw["enabled"])

    def test_a_saved_profiles_real_indexes_are_unchanged(self):
        root, ids = tree()
        gid = ids[N64_TITLE]
        out, _ = run(root, FLAGS, "post_launch", {"id": gid, "query": f"id={gid}&cheat_source=0&cheat_indexes=0,2,5,6"})
        self.assertEqual(out["enabled"], [0, 2, 5, 6])


if __name__ == "__main__":
    unittest.main()
