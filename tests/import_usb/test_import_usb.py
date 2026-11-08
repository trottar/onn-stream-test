#!/usr/bin/env python3
"""B56: `tools/import_usb.py` (PS1, behind PRIVYHUB_IMPORT=1) against fixture trees built from bytes -- a fake CHD v5
header, cue sets whose data track carries a synthetic `CD001` / `PLAYSTATION` sector 16, a two-disc set -- never real
content. inspect / plan / apply / verify end to end; the rejections; the multi-disc `.m3u`; the duplicate rules; a copy
failing midway leaving nothing half-written; the sanitized log; the list's marks; absent -> the tool refuses and the
list is today's.

    python3 -m unittest discover -s tests/import_usb -v
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import import_usb as iu  # noqa: E402

ON = {"PRIVYHUB_IMPORT": "1"}
FREE = lambda p: 10 ** 12   # noqa: E731
NAMES = ["Alpha Quest", "Beta Racer", "Gamma Saga", "Delta Iso", "Epsilon Old"]


def chd(path: Path, seed: int, version: int = 5) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"MComprHD" + (124).to_bytes(4, "big") + version.to_bytes(4, "big") + bytes([seed]) * 4000)
    return path


def bin_track(path: Path, seed: int, sysid: str = "PLAYSTATION", sectors: int = 20, cd001: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray([seed]) * (sectors * iu.SECTOR)
    off = 16 * iu.SECTOR + 24
    if cd001:
        data[off:off + 6] = b"\x01CD001"
        data[off + 8:off + 40] = sysid.ljust(32).encode()
    path.write_bytes(bytes(data))
    return path


def cue(path: Path, bins: list[str], mode: str = "MODE2/2352") -> Path:
    lines = []
    for i, b in enumerate(bins, 1):
        lines += [f'FILE "{b}" BINARY', f"  TRACK {i:02d} {mode if i == 1 else 'AUDIO'}", "    INDEX 01 00:00:00"]
    path.write_text("\n".join(lines) + "\n")
    return path


def cue_set(folder: Path, title: str, seed: int, **kw) -> Path:
    bin_track(folder / f"{title} (Track 1).bin", seed, **kw)
    bin_track(folder / f"{title} (Track 2).bin", seed + 100, cd001=False)
    return cue(folder / f"{title}.cue", [f"{title} (Track 1).bin", f"{title} (Track 2).bin"])


class Tree:
    """A fixture stick and a fixture hub (library, data) in one temp dir."""

    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix="b56_"))
        self.stick = self.base / "stick"
        self.games = self.stick / iu.IMPORT_DIR / "games" / "ps1"
        self.bios = self.stick / iu.IMPORT_DIR / "bios" / "ps1"
        self.hub = self.base / "hub"
        self.lib = self.hub / "games" / "ps1"
        self.games.mkdir(parents=True)
        self.lib.mkdir(parents=True)

    def run(self, *argv, env=ON, active=lambda: False):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = iu.main(list(argv), project_root=self.hub, environ=env, active=active, free_bytes=FREE)
        return code, out.getvalue(), err.getvalue()

    def plan(self):
        return iu.make_plan(self.stick, self.hub, free_bytes=FREE)

    def standard(self):
        chd(self.games / "Alpha Quest.chd", 1)
        cue_set(self.games / "Beta Racer", "Beta Racer", 2)
        chd(self.games / "Gamma Saga" / "Gamma Saga (Disc 1).chd", 3)
        chd(self.games / "Gamma Saga" / "Gamma Saga (Disc 2).chd", 4)
        return self


def by_label(plan):
    return {c["title"]: c for c in plan["candidates"]}


class Flag(unittest.TestCase):
    def test_absent_refuses_and_writes_nothing(self):
        t = Tree().standard()
        before = sorted(str(p) for p in t.base.rglob("*"))
        for env in ({}, {"PRIVYHUB_IMPORT": "0"}, {"PRIVYHUB_IMPORT": ""}, {"PRIVYHUB_IMPORT": "yes"}):
            for argv in (("inspect", str(t.stick)), ("plan", str(t.stick)), ("apply",), ("verify",)):
                code, _, err = t.run(*argv, env=env)
                self.assertEqual(code, iu.EXIT_FLAG)
                self.assertIn("nothing was read or written", err)
        self.assertEqual(sorted(str(p) for p in t.base.rglob("*")), before)


class Inspect(unittest.TestCase):
    def test_types_candidates_and_rejections(self):
        t = Tree().standard()
        (t.games / "Lonely.bin").write_bytes(b"\0" * iu.SECTOR)
        (t.games / "Notes.txt").write_text("x")
        (t.games / "Old.pbp").write_bytes(b"\0PBP")
        (t.games / "._Alpha Quest.chd").write_bytes(b"x")         # a hidden helper file: ignored
        (t.games / "Link.chd").symlink_to(t.base)
        cue(t.games / "Missing.cue", ["Missing (Track 1).bin"])
        bin_track(t.games / "case" / "case (track 1).bin", 9)
        cue(t.games / "case" / "Case.cue", ["Case (Track 1).bin"])
        cue(t.games / "Outside.cue", ["../escape.bin"])
        chd(t.games / "Gap" / "Gap (Disc 1).chd", 5)
        chd(t.games / "Gap" / "Gap (Disc 3).chd", 6)
        st = iu.scan_stick(iu.find_root(t.stick))
        kinds = {c["title"]: (c["kind"], c["error"]) for c in st["candidates"]}
        self.assertEqual(kinds["Alpha Quest"], ("chd", None))
        self.assertEqual(kinds["Beta Racer"], ("cue_set", None))
        self.assertEqual(kinds["Gamma Saga"], ("m3u_set", None))
        self.assertEqual(kinds["Missing"], ("cue_set", "cue_missing_file"))
        self.assertEqual(kinds["Case"], ("cue_set", "cue_case_mismatch"))
        self.assertEqual(kinds["Outside"], ("cue_set", "cue_outside"))
        self.assertEqual(kinds["Gap"], ("m3u_set", "multidisc_gap"))
        rej = sorted((Path(r["source"]).name, r["reason"]) for r in st["rejected"])
        self.assertIn(("Lonely.bin", "bin_without_cue"), rej)
        self.assertIn(("Notes.txt", "unknown_type"), rej)
        self.assertIn(("Old.pbp", "pbp_not_supported"), rej)
        self.assertIn(("Link.chd", "symlink"), rej)
        self.assertEqual(st["ignored_hidden"], 1)
        code, out, _ = t.run("inspect", str(t.stick))
        self.assertEqual(code, 0)
        self.assertNotIn("Alpha", out)                              # labels only without --names
        self.assertIn("T1", out)

    def test_a_bin_named_by_two_cues_is_ambiguous(self):
        t = Tree()
        bin_track(t.games / "Shared (Track 1).bin", 1)
        cue(t.games / "One.cue", ["Shared (Track 1).bin"])
        cue(t.games / "Two.cue", ["Shared (Track 1).bin"])
        st = iu.scan_stick(iu.find_root(t.stick))
        self.assertEqual({c["error"] for c in st["candidates"]}, {"bin_claimed_twice"})

    def test_the_bios_report(self):
        t = Tree()
        t.bios.mkdir(parents=True)
        (t.bios / "SCPH5501.BIN").write_bytes(b"\0" * iu.BIOS_SIZE)
        (t.bios / "scph1001.bin").write_bytes(b"\0" * iu.BIOS_SIZE)
        (t.bios / "scph5502.bin").write_bytes(b"\0" * 1000)        # wrong size: not a real set
        st = iu.scan_stick(iu.find_root(t.stick))
        self.assertEqual([(b["region"], b["real"]) for b in st["bios"]], [(None, False), ("US", True), ("EU", False)])
        code, out, _ = t.run("inspect", str(t.stick))
        self.assertIn("BIOS on the stick: US; 2 other file(s) not used", out)
        self.assertIn("none (the core uses its built-in OpenBIOS)", out)


class Plan(unittest.TestCase):
    def test_headers_and_the_disc_ids(self):
        t = Tree()
        chd(t.games / "Old Chd.chd", 1, version=3)
        cue_set(t.games / "Other", "Other", 2, sysid="SEGA SEGASATURN")
        cue_set(t.games / "No Pvd", "No Pvd", 3, cd001=False)
        (t.games / "Short").mkdir()
        (t.games / "Short" / "Short (Track 1).bin").write_bytes(b"\0" * 1000)
        cue(t.games / "Short" / "Short.cue", ["Short (Track 1).bin"])
        p = by_label(t.plan())
        self.assertEqual(p["Old Chd"]["reason"], "bad_header")
        self.assertEqual(p["Other"]["reason"], "not_ps1_disc")
        self.assertEqual(p["No Pvd"]["reason"], "not_ps1_disc")
        self.assertEqual(p["Short"]["reason"], "bad_header")

    def test_the_plan_destinations_ids_m3u_and_space(self):
        t = Tree().standard()
        plan = t.plan()
        p = by_label(plan)
        self.assertEqual([c["decision"] for c in plan["candidates"]], ["accept"] * 3)
        self.assertEqual(p["Alpha Quest"]["entry_target"], "games/ps1/Alpha Quest.chd")
        g = p["Gamma Saga"]
        self.assertEqual(g["make_m3u"], {"target_rel": "games/ps1/Gamma Saga/Gamma Saga.m3u",
                                         "lines": ["Gamma Saga (Disc 1).chd", "Gamma Saga (Disc 2).chd"]})
        self.assertEqual([f["role"] for f in p["Beta Racer"]["files"]], ["track", "track", "entry"])   # entry last
        # the ids are the plugin's
        spec = importlib.util.spec_from_file_location("b56_plugin_ids", ROOT / "companion" / "plugins" / "games.py")
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        for c in plan["candidates"]:
            self.assertEqual(c["game_id"], G.GamesPlugin._stable_id("ps1", c["entry_target"]))
        self.assertEqual(iu.clean_name(Path("x/ALPHA_QUEST.chd")), G.GamesPlugin._clean_name(Path("x/ALPHA_QUEST.chd")))
        self.assertTrue(plan["space"]["ok"])
        tight = iu.make_plan(t.stick, t.hub, free_bytes=lambda p: 10)
        self.assertFalse(tight["space"]["ok"])
        code, out, _ = t.run("plan", str(t.stick))
        self.assertEqual(code, 0)
        self.assertTrue(list((t.hub / "data/import/plans").glob("*.json")))

    def test_duplicates_by_hash_size_gated_and_inside_the_stick(self):
        t = Tree().standard()
        chd(t.lib / "Renamed Alpha.chd", 1)                         # Alpha's bytes under another name
        chd(t.games / "Omega.chd", 11)
        chd(t.games / "Omega Copy.chd", 11)                         # the same new bytes twice on the stick
        reads = []
        orig = iu.sha256
        iu.sha256 = lambda p: (reads.append(Path(p)), orig(p))[1]
        try:
            p = by_label(t.plan())
        finally:
            iu.sha256 = orig
        self.assertEqual((p["Alpha Quest"]["decision"], p["Alpha Quest"]["reason"]),
                         ("duplicate", "duplicate: already in the library"))
        self.assertEqual(p["Alpha Quest"]["duplicate_of"], iu.stable_id("ps1", "games/ps1/Renamed Alpha.chd"))
        # the first by path is kept ("Omega Copy.chd" sorts first), the other is the stick duplicate
        self.assertEqual({p["Omega"]["reason"], p["Omega Copy"]["reason"]},
                         {None, "duplicate: same content on the stick"})
        big = bin_track(t.lib / "Unrelated (Track 1).bin", 7, sectors=99)   # no candidate has its size
        reads.clear()
        iu.sha256 = lambda p: (reads.append(Path(p)), orig(p))[1]
        try:
            t.plan()
        finally:
            iu.sha256 = orig
        self.assertNotIn(big, reads)                                # size-gated: never hashed

    def test_the_iso_and_title_rules_and_hide(self):
        t = Tree()
        (t.games / "Delta Iso.iso").write_bytes(b"\0" * 4096)
        chd(t.games / "Delta Iso.chd", 4)
        (t.games / "Lone Iso.iso").write_bytes(b"\1" * 4096)
        (t.lib / "Epsilon Old.iso").write_bytes(b"\2" * 4096)        # a library .iso, the .chd arriving now
        chd(t.games / "Epsilon Old.chd", 5)
        (t.lib / "Zeta.iso").write_bytes(b"\3" * 4096)               # a library .iso beside its library .chd
        chd(t.lib / "Zeta.chd", 6)
        cue_set(t.lib / "Eta", "Eta", 7)                             # the title is in the library already
        chd(t.games / "Eta.chd", 8)
        plan = t.plan()
        p = {(c["title"], c["kind"]): c for c in plan["candidates"]}
        self.assertEqual(p[("Delta Iso", "iso")]["reason"], "duplicate: chd present")
        self.assertEqual(p[("Delta Iso", "chd")]["decision"], "accept")
        self.assertEqual(p[("Lone Iso", "iso")]["reason"], "iso_not_launchable")
        self.assertEqual(p[("Epsilon Old", "chd")]["decision"], "accept")
        self.assertEqual(p[("Eta", "chd")]["reason"], "duplicate: title present")
        self.assertEqual(set(plan["hide"]), {iu.stable_id("ps1", "games/ps1/Epsilon Old.iso"),
                                             iu.stable_id("ps1", "games/ps1/Zeta.iso")})

    def test_a_target_with_other_bytes_is_rejected_never_renamed(self):
        t = Tree()
        cue_set(t.games / "Iota", "Iota", 2)
        (t.lib / "Iota").mkdir()
        bin_track(t.lib / "Iota" / "Iota (Track 1).bin", 3)          # an unlisted file at a target path, other bytes
        p = by_label(t.plan())
        self.assertEqual((p["Iota"]["decision"], p["Iota"]["reason"]), ("reject", "target_exists_different"))


class Apply(unittest.TestCase):
    def test_end_to_end_with_the_list(self):
        t = Tree().standard()
        t.bios.mkdir(parents=True)
        (t.bios / "scph5501.bin").write_bytes(b"\7" * iu.BIOS_SIZE)
        os.chmod(t.stick, 0o555)
        for p in t.stick.rglob("*"):
            os.chmod(p, 0o555 if p.is_dir() else 0o444)
        self.addCleanup(lambda: [os.chmod(p, 0o755) for p in [t.stick, *t.stick.rglob("*")] if p.is_dir()])
        stick_before = {str(p): p.stat().st_mtime_ns for p in t.stick.rglob("*")}
        self.assertEqual(t.run("plan", str(t.stick))[0], 0)
        code, out, _ = t.run("apply")
        self.assertEqual(code, 0, out)
        for rel in ("Alpha Quest.chd", "Beta Racer/Beta Racer.cue", "Beta Racer/Beta Racer (Track 2).bin",
                    "Gamma Saga/Gamma Saga (Disc 2).chd", "Gamma Saga/Gamma Saga.m3u"):
            self.assertTrue((t.lib / rel).is_file(), rel)
        self.assertEqual((t.lib / "Gamma Saga/Gamma Saga.m3u").read_text(),
                         "Gamma Saga (Disc 1).chd\nGamma Saga (Disc 2).chd\n")
        self.assertEqual(list(t.lib.rglob(".import-*")), [])
        self.assertTrue((t.hub / iu.BIOS_REL / "scph5501.bin").is_file())
        self.assertEqual({str(p): p.stat().st_mtime_ns for p in t.stick.rglob("*")}, stick_before)
        marks = json.loads((t.hub / "data/import/marks.json").read_text())
        self.assertEqual(len(marks["new"]), 3)
        self.assertEqual(t.run("verify")[0], 0)
        # a second plan: everything already there (idempotent)
        t.run("plan", str(t.stick))
        plan2 = json.loads(sorted((t.hub / "data/import/plans").glob("*.json"))[-1].read_text())
        self.assertEqual(plan2["totals"]["accept"], 0)
        # the scanner lists the set once, by its .m3u
        G = load_plugin(on=True)
        games = plugin(G, t.hub)._scan()
        self.assertEqual(sorted(g["title"] for g in games), ["Alpha Quest", "Beta Racer", "Gamma Saga"])

    def test_a_copy_failing_midway_leaves_nothing_half_written(self):
        t = Tree().standard()
        t.run("plan", str(t.stick))
        calls = []

        def boom(cid, n):
            calls.append((cid, n))
            if n == 1:                                              # after the second file of a candidate
                raise OSError("pulled")
        iu._FAIL_HOOK = boom
        try:
            code, out, _ = t.run("apply")
        finally:
            iu._FAIL_HOOK = None
        self.assertIn(code, (iu.EXIT_SOURCE, iu.EXIT_PARTIAL))
        self.assertTrue((t.lib / "Alpha Quest.chd").is_file())       # one file: placed before any failure
        self.assertFalse((t.lib / "Beta Racer").exists())            # rolled back, its new dir gone
        self.assertFalse((t.lib / "Gamma Saga").exists())
        self.assertEqual(list(t.lib.rglob(".import-*")), [])

    def test_a_verify_mismatch_rolls_back(self):
        t = Tree()
        cue_set(t.games / "Kappa", "Kappa", 1)
        t.run("plan", str(t.stick))
        orig = iu._copier

        def flipping(src):
            w = orig(src)

            def write(fh):
                got = w(fh)
                if src.suffix == ".cue":                             # the entry's copy comes out one byte off
                    fh.seek(0)
                    fh.write(b"#")
                    return "f" * 64
                return got
            return write
        iu._copier = flipping
        try:
            code, out, _ = t.run("apply")
        finally:
            iu._copier = orig
        self.assertEqual(code, iu.EXIT_VERIFY)
        self.assertIn("verify_failed", out)
        self.assertFalse((t.lib / "Kappa").exists())                 # the tracks placed before it rolled back too
        self.assertEqual(list(t.lib.rglob("*")), [])

    def test_a_stale_part_is_not_ours_and_is_left(self):
        t = Tree()
        chd(t.games / "Rho.chd", 1)
        t.run("plan", str(t.stick))
        plan = json.loads(sorted((t.hub / "data/import/plans").glob("*.json"))[-1].read_text())
        stale = t.lib / f".import-{plan['candidates'][0]['cid']}-0.part"
        stale.write_bytes(b"someone else's")
        code, out, _ = t.run("apply")
        self.assertEqual(code, iu.EXIT_PARTIAL)
        self.assertEqual(stale.read_bytes(), b"someone else's")      # never removed: not this run's file
        self.assertFalse((t.lib / "Rho.chd").exists())

    def test_a_source_changed_after_the_plan_is_not_copied(self):
        t = Tree()
        chd(t.games / "Lambda.chd", 1)
        t.run("plan", str(t.stick))
        chd(t.games / "Lambda.chd", 2)
        code, out, _ = t.run("apply")
        self.assertEqual(code, iu.EXIT_PARTIAL)
        self.assertIn("source_changed", out)
        self.assertFalse((t.lib / "Lambda.chd").exists())

    def test_an_existing_final_is_never_overwritten(self):
        t = Tree()
        chd(t.games / "Mu.chd", 1)
        t.run("plan", str(t.stick))
        chd(t.lib / "Mu.chd", 9)                                     # appears between the plan and the apply
        code, out, _ = t.run("apply")
        self.assertEqual(code, iu.EXIT_PARTIAL)
        self.assertIn("target_exists", out)
        self.assertEqual((t.lib / "Mu.chd").read_bytes()[16:17], bytes([9]))

    def test_a_game_active_refuses(self):
        t = Tree().standard()
        t.run("plan", str(t.stick))
        code, _, err = t.run("apply", active=lambda: True)
        self.assertEqual(code, iu.EXIT_ACTIVE)
        self.assertEqual(list(t.lib.iterdir()), [])

    def test_the_bios_never_overwrites(self):
        t = Tree()
        t.bios.mkdir(parents=True)
        (t.bios / "scph5500.bin").write_bytes(b"\5" * iu.BIOS_SIZE)
        (t.hub / iu.BIOS_REL).mkdir(parents=True)
        (t.hub / iu.BIOS_REL / "scph5500.bin").write_bytes(b"\6" * iu.BIOS_SIZE)
        plan = t.plan()
        self.assertEqual(plan["bios"]["stick"][0]["decision"], "duplicate")
        self.assertEqual(plan["bios"]["core_has_real"], ["JP"])


class Log(unittest.TestCase):
    def test_the_log_has_no_name_title_folder_or_hash(self):
        t = Tree().standard()
        t.bios.mkdir(parents=True)
        (t.bios / "scph5501.bin").write_bytes(b"\7" * iu.BIOS_SIZE)
        t.run("plan", str(t.stick))
        t.run("apply")
        t.run("verify")
        text = "".join(p.read_text() for p in (t.hub / "data/import/logs").glob("*.jsonl"))
        plan = json.loads(sorted((t.hub / "data/import/plans").glob("*.json"))[-1].read_text())
        forbidden = NAMES + ["Track", "Disc", ".chd", ".cue", ".bin", ".m3u", "scph", str(t.base), iu.IMPORT_DIR]
        forbidden += [f["sha256"] for c in plan["candidates"] for f in c["files"] if f["sha256"]]
        forbidden += [c["game_id"] for c in plan["candidates"]]
        for word in forbidden:
            self.assertNotIn(word, text, word)
        self.assertIn('"label": "T1"', text)
        self.assertIn("US:accept", text)


def load_plugin(on: bool):
    old = os.environ.get("PRIVYHUB_IMPORT")
    if on:
        os.environ["PRIVYHUB_IMPORT"] = "1"
    else:
        os.environ.pop("PRIVYHUB_IMPORT", None)
    try:
        spec = importlib.util.spec_from_file_location(f"b56_plugin_{on}", ROOT / "companion" / "plugins" / "games.py")
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        return G
    finally:
        if old is None:
            os.environ.pop("PRIVYHUB_IMPORT", None)
        else:
            os.environ["PRIVYHUB_IMPORT"] = old


def plugin(G, hub: Path):
    p = object.__new__(G.GamesPlugin)
    p.PROJECT_ROOT = hub
    p.GAMES_ROOT = hub / "games"
    p._emulator = type("Idle", (), {"status": lambda self: {"active": False}})()
    p._lock = threading.Lock()
    p._cached_games = []
    p._cached_at = 0.0
    return p


class List(unittest.TestCase):
    def setUp(self):
        self.t = Tree()
        chd(self.t.lib / "Nu.chd", 1)
        (self.t.lib / "Nu.iso").write_bytes(b"\0" * 4096)
        chd(self.t.lib / "Xi.chd", 2)
        nu, iso = iu.stable_id("ps1", "games/ps1/Nu.chd"), iu.stable_id("ps1", "games/ps1/Nu.iso")
        import time
        now = int(time.time() * 1000)
        iu.write_json_atomic(self.t.hub / "data/import/marks.json",
                             {"new": {nu: now - 86_400_000, iu.stable_id("ps1", "games/ps1/Xi.chd"):
                                      now - 8 * 86_400_000}, "hide": {iso: "chd present"}})

    def names(self, G):
        p = plugin(G, self.t.hub)
        p._annotated_games = lambda: [dict(g, favorite=False, last_played_unix_ms=0, play_count=0,
                                           continue_available=False, player_mode="", max_players=0)
                                      for g in p._scan()]
        games = p.games({"system": ["ps1"]})
        systems = p.systems()
        ps1 = [n["name"] for n in systems["nodes"] if n["id"] == "games_system_ps1"][0]
        return sorted(n["name"] for n in games["nodes"]), ps1

    def test_new_for_seven_days_the_hidden_iso_and_openbios(self):
        names, ps1 = self.names(load_plugin(on=True))
        self.assertEqual(names, ["Nu · NEW", "Xi"])                  # Xi's import is 8 days old; Nu's .iso hidden
        self.assertEqual(ps1, "PlayStation (OpenBIOS) (2)")
        (self.t.hub / iu.BIOS_REL).mkdir(parents=True)
        (self.t.hub / iu.BIOS_REL / "scph5500.bin").write_bytes(b"\0" * 1000)   # a wrong size is not a BIOS
        self.assertEqual(self.names(load_plugin(on=True))[1], "PlayStation (OpenBIOS) (2)")
        (self.t.hub / iu.BIOS_REL / "scph5501.bin").write_bytes(b"\0" * iu.BIOS_SIZE)
        self.assertEqual(self.names(load_plugin(on=True))[1], "PlayStation (2)")

    def test_absent_is_todays_list(self):
        names, ps1 = self.names(load_plugin(on=False))
        self.assertEqual(names, ["Nu", "Nu", "Xi"])                   # the .iso listed, no tag
        self.assertEqual(ps1, "PlayStation (3)")


class GitIgnore(unittest.TestCase):
    @unittest.skipUnless((ROOT / ".git").exists(), "a copy without .git (run in the tree)")
    def test_the_library_the_bios_and_the_import_data_are_ignored(self):
        import subprocess
        paths = ["games/ps1/x.chd", "data/games/retroarch/system/x.bin", "data/import/plans/x.json",
                 "data/import/logs/x.jsonl", "data/import/marks.json"]
        r = subprocess.run(["git", "check-ignore", *paths], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(sorted(r.stdout.split()), sorted(paths))


if __name__ == "__main__":
    unittest.main()
