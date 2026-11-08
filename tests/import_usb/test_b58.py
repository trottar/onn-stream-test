#!/usr/bin/env python3
"""B58: import slice 1b (behind PRIVYHUB_IMPORT=1) against fixture trees built from bytes -- synthetic SNES / NES /
Genesis cartridge files (headers made here, no real content), B56's fake CHD / cue sets -- never a real game file.
Each system's accept / reject by extension and header; the duplicates per system; the plain-folder form equal to the
stick form; the journal: an interrupted apply resumed or cleaned, never a half-placed title in the list; PS2 / N64 /
GameCube folders reported, nothing planned; NEW for a cartridge title; the log; absent -> the tool refuses.

    python3 -m unittest discover -s tests/import_usb -v
"""

from __future__ import annotations

import json
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401  (this run's temp dirs removed at exit)

import import_usb as iu  # noqa: E402
import test_import_usb as b56  # noqa: E402  (as a module: its tests are not collected twice)

ON, FREE = b56.ON, b56.FREE


# --- synthetic cartridge files ------------------------------------------------------------------------------------

def snes(path: Path, seed: int, mapping: str = "lo", copier: bool = False, good: bool = True, kib: int = 64) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray([seed]) * (kib * 1024)
    off = {"lo": 0x7FDC, "hi": 0xFFDC}[mapping]
    complement = (seed * 257 + 0x1234) & 0xFFFF
    checksum = complement ^ 0xFFFF if good else complement
    data[off:off + 4] = complement.to_bytes(2, "little") + checksum.to_bytes(2, "little")
    path.write_bytes((b"\0" * 512 if copier else b"") + bytes(data))
    return path


def nes(path: Path, seed: int, good: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((b"NES\x1a" if good else b"XXXX") + bytes([2, 1, 0, 0]) + b"\0" * 8 + bytes([seed]) * 40960)
    return path


def genesis(path: Path, seed: int, good: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray([seed]) * 131072
    if good:
        data[0x100:0x110] = b"SEGA MEGA DRIVE "
    path.write_bytes(bytes(data))
    return path


class Tree(b56.Tree):
    def __init__(self):
        super().__init__()
        self.games.rmdir()                  # B56's tree makes an empty stick ps1/ folder; here only what a test puts
        self.src = self.stick / iu.IMPORT_DIR / "games"
        self.plain = self.base / "drive" / "games"

    def lib_of(self, system):
        d = self.hub / "games" / system
        d.mkdir(parents=True, exist_ok=True)
        return d

    def plan_plain(self, system, folder=None):
        return iu.make_plan(None, self.hub, free_bytes=FREE, source=folder or self.plain / system, system=system)


def decisions(plan):
    return {c["title"]: (c["system"], c["decision"], c["reason"]) for c in plan["candidates"]}


def strip(plan):
    """A plan without what depends on the form: the source paths, the form, the time."""
    out = json.loads(json.dumps(plan))
    for k in ("source_root", "source_form", "created_utc"):
        out.pop(k)
    for c in out["candidates"]:
        for f in c["files"]:
            f.pop("source")
    for r in out["rejected"]:
        r.pop("source")
    return out


class Headers(unittest.TestCase):
    def test_each_systems_accept_and_reject_by_extension_and_header(self):
        t = Tree()
        s, n, g = t.src / "snes", t.src / "nes", t.src / "genesis"
        snes(s / "Lo Ok.sfc", 1)
        snes(s / "Hi Copier.smc", 2, mapping="hi", copier=True)
        snes(s / "Bad Sum.sfc", 3, good=False)
        (s / "Bad Size.sfc").write_bytes(b"\1" * 1000)
        (s / "Packed.zip").write_bytes(b"PK\3\4" + b"\0" * 100)
        (s / "notes.txt").write_text("x")
        nes(n / "Nes Ok.nes", 4)
        nes(n / "Nes Bad.nes", 5, good=False)
        genesis(g / "Gen Md.md", 6)
        genesis(g / "Gen Gen.gen", 7)
        genesis(g / "Gen Bin.bin", 8)
        genesis(g / "Gen Bad.bin", 9, good=False)
        plan = t.plan()
        self.assertEqual(plan["systems"], ["genesis", "nes", "snes"])
        self.assertEqual(decisions(plan), {
            "Lo Ok": ("snes", "accept", None), "Hi Copier": ("snes", "accept", None),
            "Bad Sum": ("snes", "reject", "bad_header"), "Bad Size": ("snes", "reject", "bad_header"),
            "Nes Ok": ("nes", "accept", None), "Nes Bad": ("nes", "reject", "bad_header"),
            "Gen Md": ("genesis", "accept", None), "Gen Gen": ("genesis", "accept", None),
            "Gen Bin": ("genesis", "accept", None), "Gen Bad": ("genesis", "reject", "bad_header")})
        copier = {c["title"]: c.get("copier_header") for c in plan["candidates"] if c["system"] == "snes"}
        self.assertEqual((copier["Lo Ok"], copier["Hi Copier"]), (False, True))
        self.assertEqual(sorted((r["system"], r["reason"]) for r in plan["rejected"]),
                         [("snes", "unknown_type"), ("snes", "unknown_type")])
        # the targets and ids: the system's own library folder, the plugin's id rule
        c = [c for c in plan["candidates"] if c["title"] == "Hi Copier"][0]
        self.assertEqual(c["entry_target"], "games/snes/Hi Copier.smc")
        self.assertEqual(c["game_id"], b56.load_plugin(on=False).GamesPlugin._stable_id("snes",
                                                                                         "games/snes/Hi Copier.smc"))
        # labels run across systems in the source's order
        self.assertEqual([c["label"] for c in plan["candidates"]], [f"T{i}" for i in range(1, 11)])

    def test_the_extension_rule_is_the_lists(self):
        plugin_systems = b56.load_plugin(on=False).GamesPlugin.SYSTEMS
        for system, exts in iu.ROM_EXT.items():
            self.assertEqual(set(exts), plugin_systems[system]["extensions"], system)
        self.assertEqual(set(iu.SYSTEMS), set(plugin_systems))


class Duplicates(unittest.TestCase):
    def test_per_system_by_hash_title_and_inside_the_source(self):
        t = Tree()
        lib = t.lib_of("snes")
        snes(lib / "Library Name.sfc", 10)
        snes(lib / "Held Title.sfc", 11)
        snes(lib / "Other Size.sfc", 12, kib=128)
        s = t.src / "snes"
        snes(s / "Renamed Copy.sfc", 10)                         # the library's bytes under another name
        snes(s / "Held Title.smc", 13)                           # the same title in a second format
        snes(s / "Fresh One.sfc", 14)
        snes(s / "Fresh Twin.sfc", 14)                           # the same bytes twice on the stick
        nes(t.lib_of("nes") / "Kept.nes", 15)
        nes(t.src / "nes" / "Kept Again.nes", 15)
        reads = []
        orig = iu.sha256
        iu.sha256 = lambda p: (reads.append(Path(p)), orig(p))[1]
        try:
            plan = t.plan()
        finally:
            iu.sha256 = orig
        d = {c["title"]: c for c in plan["candidates"]}
        rc = d["Renamed Copy"]
        self.assertEqual((rc["decision"], rc["reason"], rc["duplicate_of"]),
                         ("duplicate", "duplicate: already in the library",
                          iu.stable_id("snes", "games/snes/Library Name.sfc")))
        self.assertEqual((d["Held Title"]["reason"], d["Held Title"]["duplicate_of"]),
                         ("duplicate: title present", iu.stable_id("snes", "games/snes/Held Title.sfc")))
        self.assertEqual(d["Fresh One"]["decision"], "accept")
        self.assertEqual((d["Fresh Twin"]["reason"], d["Fresh Twin"]["duplicate_of"]),
                         ("duplicate: same content on the stick", d["Fresh One"]["label"]))
        self.assertEqual(d["Kept Again"]["reason"], "duplicate: already in the library")
        self.assertNotIn((lib / "Other Size.sfc").resolve(), [p.resolve() for p in reads])   # size-gated
        self.assertEqual(plan["hide"], {})                       # the hidden rule is PS1's only

    def test_a_cartridge_target_with_other_bytes_is_never_overwritten(self):
        t = Tree()
        lib = t.lib_of("genesis")
        (lib / "Clash.md").write_bytes(b"\0" * 10)               # the same path with other bytes (also the same title)
        genesis(t.src / "genesis" / "Clash.md", 20)
        plan = t.plan()
        self.assertEqual(plan["candidates"][0]["decision"], "duplicate")   # the title rule comes first
        self.assertEqual((lib / "Clash.md").read_bytes(), b"\0" * 10)


class PlainFolder(unittest.TestCase):
    def build(self, root: Path, system: str):
        if system == "ps1":
            b56.chd(root / "Alpha Quest.chd", 1)
            b56.cue_set(root / "Beta Racer", "Beta Racer", 2)
            b56.chd(root / "Gamma Saga" / "Gamma Saga (Disc 1).chd", 3)
            b56.chd(root / "Gamma Saga" / "Gamma Saga (Disc 2).chd", 4)
            (root / "readme.txt").parent.mkdir(parents=True, exist_ok=True)
            (root / "readme.txt").write_text("x")
        elif system == "snes":
            snes(root / "Lo Ok.sfc", 1)
            snes(root / "Sub" / "Hi Copier.smc", 2, mapping="hi", copier=True)
            snes(root / "Bad Sum.sfc", 3, good=False)
        elif system == "nes":
            nes(root / "Nes Ok.nes", 4)
            nes(root / "Nes Bad.nes", 5, good=False)
        else:
            genesis(root / "Gen Md.md", 6)
            genesis(root / "Gen Bad.bin", 9, good=False)

    def test_the_plain_form_equals_the_stick_form_on_the_same_files(self):
        for system in ("ps1", "snes", "nes", "genesis"):
            with self.subTest(system=system):
                t = Tree()
                self.build(t.src / system, system)
                self.build(t.plain / system, system)
                stick, plain = t.plan(), t.plan_plain(system)
                self.assertEqual((stick["source_form"], plain["source_form"]), ("stick", "plain"))
                self.assertTrue(stick["candidates"])
                self.assertEqual(strip(stick), strip(plain))
                # read in place: no symlink anywhere in the plain source
                self.assertFalse(any(p.is_symlink() for p in (t.plain / system).rglob("*")))

    def test_the_plain_form_end_to_end_with_the_cli(self):
        t = Tree()
        self.build(t.plain / "snes", "snes")
        code, out, _ = t.run("inspect", "--source", str(t.plain / "snes"), "--system", "snes")
        self.assertEqual(code, 0, out)
        self.assertIn("SNES candidates: 3", out)                # inspect reads no header (plan does)
        self.assertNotIn("BIOS", out)                            # the plain form reads no BIOS
        self.assertNotIn("Lo Ok", out)                           # labels only without --names
        code, out, _ = t.run("plan", "--source", str(t.plain / "snes"), "--system", "snes")
        self.assertEqual(code, 0, out)
        code, out, _ = t.run("apply")
        self.assertEqual(code, 0, out)
        self.assertEqual((t.hub / "games/snes/Sub/Hi Copier.smc").read_bytes(),
                         (t.plain / "snes/Sub/Hi Copier.smc").read_bytes())
        self.assertEqual(t.run("verify")[0], 0)

    def test_the_forms_are_exclusive_and_the_library_is_not_a_source(self):
        t = Tree()
        self.build(t.plain / "snes", "snes")
        self.assertEqual(t.run("plan", str(t.stick), "--source", str(t.plain / "snes"), "--system", "snes")[0], 2)
        self.assertEqual(t.run("plan", "--source", str(t.plain / "snes"))[0], 2)
        self.assertEqual(t.run("plan", str(t.stick), "--system", "snes")[0], 2)
        self.assertEqual(t.run("plan")[0], 2)
        self.build(t.lib_of("snes"), "snes")
        code, _, err = t.run("plan", "--source", str(t.hub / "games" / "snes"), "--system", "snes")
        self.assertEqual(code, 2)
        self.assertIn("inside the hub's own library", err)


class Reported(unittest.TestCase):
    def test_ps2_n64_gamecube_and_an_unknown_folder_are_reported_nothing_planned(self):
        t = Tree()
        for folder, name in (("ps2", "One.iso"), ("n64", "Two.z64"), ("gamecube", "Three.rvz"),
                             ("Private Stuff", "Four.dat")):
            (t.src / folder).mkdir(parents=True, exist_ok=True)
            (t.src / folder / name).write_bytes(b"\0" * 64)
        code, out, _ = t.run("inspect", str(t.stick))
        self.assertEqual(code, iu.EXIT_NOTHING)
        self.assertIn("ps2/: 1 file(s) - PS2 games stay on the external drive and are listed from there", out)
        self.assertIn("n64/: 1 file(s) - not supported yet", out)
        self.assertIn("gamecube/: 1 file(s) - not supported yet", out)
        self.assertIn("a folder/: 1 file(s) - not a system the hub lists", out)
        self.assertNotIn("Private Stuff", out)
        plan = t.plan()
        self.assertEqual((plan["candidates"], plan["systems"]), ([], []))
        self.assertEqual(set(plan["reported"]), {"ps2", "n64", "gamecube", "Private Stuff"})
        self.assertEqual(t.run("plan", str(t.stick))[0], iu.EXIT_NOTHING)
        for system in ("ps2", "n64", "gamecube"):
            (t.plain / system).mkdir(parents=True, exist_ok=True)
            (t.plain / system / "x.iso").write_bytes(b"\0" * 64)
            code, out, _ = t.run("plan", "--source", str(t.plain / system), "--system", system)
            self.assertEqual(code, iu.EXIT_NOTHING, system)
            self.assertIn("nothing planned", out)
            self.assertEqual(t.plan_plain(system)["candidates"], [])
        self.assertFalse((t.hub / "games" / "ps2").exists())


class Journal(unittest.TestCase):
    def crash(self, hook_name, when):
        def boom(*a):
            if when(*a):
                raise KeyboardInterrupt
        setattr(iu, hook_name, boom)
        self.addCleanup(setattr, iu, hook_name, None)

    def journal(self, t):
        return iu.read_journal(t.hub)

    def test_a_crash_mid_copy_leaves_a_part_and_an_entry_then_the_next_apply_resumes(self):
        t = Tree()
        snes(t.src / "snes" / "Lo Ok.sfc", 1)
        nes(t.src / "nes" / "Nes Ok.nes", 4)
        self.assertEqual(t.run("plan", str(t.stick))[0], 0)
        self.crash("_PART_HOOK", lambda part: "snes" in str(part))
        with self.assertRaises(KeyboardInterrupt):
            t.run("apply")
        iu._PART_HOOK = None
        parts = list((t.hub / "games/snes").glob(".import-*"))
        self.assertEqual(len(parts), 1)
        self.assertEqual([e["system"] for e in self.journal(t).values()], ["snes"])
        self.assertFalse((t.hub / "games/snes/Lo Ok.sfc").exists())
        self.assertTrue((t.hub / "games/nes/Nes Ok.nes").exists())     # placed before the crash: kept
        code, out, _ = t.run("inspect", str(t.stick))
        self.assertIn("An interrupted import was found (1 title(s))", out)
        code, out, _ = t.run("apply")                            # the same plan again
        self.assertEqual(code, 0, out)
        self.assertIn("interrupted before: resumed", out)
        self.assertIn("already_placed", out)                     # the title placed before the crash: not again
        marks = iu.read_marks(t.hub / "data/import/marks.json")  # and both get the NEW mark the crash never wrote
        self.assertEqual(set(marks["new"]), {iu.stable_id("snes", "games/snes/Lo Ok.sfc"),
                                             iu.stable_id("nes", "games/nes/Nes Ok.nes")})
        self.assertEqual(list((t.hub / "games").rglob(".import-*")), [])
        self.assertFalse(iu.journal_path(t.hub).exists())
        self.assertEqual((t.hub / "games/snes/Lo Ok.sfc").read_bytes(), (t.src / "snes/Lo Ok.sfc").read_bytes())
        self.assertEqual(t.run("verify")[0], 0)

    def multi_disc_crash(self):
        t = Tree().standard()
        self.assertEqual(t.run("plan", str(t.stick))[0], 0)
        gamma = [c for c in t.plan()["candidates"] if c["title"] == "Gamma Saga"][0]
        self.crash("_FAIL_HOOK", lambda cid, n: cid == gamma["cid"] and n == 0)
        with self.assertRaises(KeyboardInterrupt):
            t.run("apply")
        iu._FAIL_HOOK = None
        return t

    def listed(self, t, on):
        p = b56.plugin(b56.load_plugin(on=on), t.hub)
        return sorted((g["system"], g["title"]) for g in p._scan())

    def test_a_half_placed_multi_disc_set_is_never_listed_and_the_next_plan_accepts_it_again(self):
        t = self.multi_disc_crash()
        disc1 = t.hub / "games/ps1/Gamma Saga/Gamma Saga (Disc 1).chd"
        self.assertTrue(disc1.exists())                          # linked before the crash
        self.assertFalse((t.hub / "games/ps1/Gamma Saga/Gamma Saga.m3u").exists())
        self.assertEqual(self.listed(t, on=True), [("ps1", "Alpha Quest"), ("ps1", "Beta Racer")])
        # without the companion's flag the list does not read the journal (today; disclosed)
        self.assertIn(("ps1", "Gamma Saga (Disc 1)"), self.listed(t, on=False))
        plan = t.plan()
        d = {c["title"]: c["decision"] for c in plan["candidates"]}
        self.assertEqual(d, {"Alpha Quest": "duplicate", "Beta Racer": "duplicate", "Gamma Saga": "accept"})
        self.assertEqual(plan["journal_pending"], 1)
        self.assertEqual(t.run("plan", str(t.stick))[0], 0)
        code, out, _ = t.run("apply")
        self.assertEqual(code, 0, out)
        self.assertIn("interrupted before: resumed", out)
        self.assertEqual(self.listed(t, on=True), [("ps1", "Alpha Quest"), ("ps1", "Beta Racer"),
                                                   ("ps1", "Gamma Saga")])
        self.assertFalse(iu.journal_path(t.hub).exists())

    def test_an_apply_of_another_plan_cleans_the_interrupted_title_only(self):
        t = self.multi_disc_crash()
        other = Tree()
        snes(other.src / "snes" / "Lo Ok.sfc", 1)
        plan = iu.make_plan(other.stick, t.hub, free_bytes=FREE)
        plan["_plan_name"] = "other.json"
        code, summary = iu.apply_plan(plan, t.hub, active=lambda: False, free_bytes=FREE)
        self.assertEqual(code, 0)
        self.assertEqual([r["result"] for r in summary["journal"]], ["cleaned"])
        self.assertFalse((t.hub / "games/ps1/Gamma Saga").exists())       # its files and its new folder gone
        self.assertTrue((t.hub / "games/ps1/Alpha Quest.chd").exists())   # the placed titles kept
        self.assertTrue((t.hub / "games/ps1/Beta Racer/Beta Racer.cue").exists())
        self.assertTrue((t.hub / "games/snes/Lo Ok.sfc").exists())
        self.assertFalse(iu.journal_path(t.hub).exists())

    def test_a_changed_final_is_left_and_reported(self):
        t = self.multi_disc_crash()
        disc1 = t.hub / "games/ps1/Gamma Saga/Gamma Saga (Disc 1).chd"
        disc1.write_bytes(b"someone else's")
        empty = Tree()
        p = iu.make_plan(empty.stick, t.hub, free_bytes=FREE)
        code, summary = iu.apply_plan(p, t.hub, active=lambda: False, free_bytes=FREE)
        self.assertEqual(code, iu.EXIT_PARTIAL)
        self.assertEqual([r["result"] for r in summary["journal"]], ["journal_conflict"])
        self.assertEqual(disc1.read_bytes(), b"someone else's")

    def test_the_journal_never_reaches_outside_the_library(self):
        t = Tree()
        outside = t.base / "keep.txt"
        outside.write_text("keep")
        (t.hub / "games/snes").mkdir(parents=True)
        marks = t.hub / "data/import/marks.json"                # a hub file outside games/, its bytes matching
        iu.write_json_atomic(marks, {"new": {}, "hide": {}})
        iu._journal_set(t.hub, "c_000000000000", {"system": "snes", "label": "T1", "targets": [
            "../keep.txt", str(outside), "data/import/marks.json"], "parts": ["games/snes/not-ours.part"],
            "preexisting": [], "dirs_new": ["games"], "list_ids": [],
            "sha256": {"../keep.txt": iu.sha256(outside), str(outside): iu.sha256(outside),
                       "data/import/marks.json": iu.sha256(marks)}})
        (t.hub / "games/snes/not-ours.part").write_text("x")
        r = iu.recover_journal(t.hub)
        self.assertEqual(r[0]["result"], "journal_conflict")
        self.assertEqual(outside.read_text(), "keep")
        self.assertTrue(marks.is_file())
        self.assertTrue((t.hub / "games/snes/not-ours.part").exists())
        self.assertTrue((t.hub / "games").is_dir())

    def test_an_apply_refused_while_playing_touches_no_journal(self):
        t = self.multi_disc_crash()
        before = iu.journal_path(t.hub).read_bytes()
        self.assertEqual(t.run("apply", active=lambda: True)[0], iu.EXIT_ACTIVE)
        self.assertEqual(iu.journal_path(t.hub).read_bytes(), before)


class NewTag(unittest.TestCase):
    def test_a_placed_cartridge_title_is_new_in_the_list(self):
        t = Tree()
        snes(t.src / "snes" / "Lo Ok.sfc", 1)
        genesis(t.src / "genesis" / "Gen Md.md", 6)
        t.run("plan", str(t.stick))
        self.assertEqual(t.run("apply")[0], 0)
        marks = iu.read_marks(t.hub / "data/import/marks.json")
        self.assertEqual(set(marks["new"]), {iu.stable_id("snes", "games/snes/Lo Ok.sfc"),
                                             iu.stable_id("genesis", "games/genesis/Gen Md.md")})
        self.assertEqual(marks["hide"], {})
        for on, want in ((True, ["Lo Ok · NEW"]), (False, ["Lo Ok"])):
            p = b56.plugin(b56.load_plugin(on=on), t.hub)
            p._annotated_games = lambda p=p: [dict(g, favorite=False, last_played_unix_ms=0, play_count=0,
                                                   continue_available=False, player_mode="", max_players=0)
                                              for g in p._scan()]
            self.assertEqual(sorted(n["name"] for n in p.games({"system": ["snes"]})["nodes"]), want)


    def test_a_re_apply_keeps_a_placed_titles_new_date(self):
        t = Tree()
        snes(t.src / "snes" / "Lo Ok.sfc", 1)
        t.run("plan", str(t.stick))
        self.assertEqual(t.run("apply")[0], 0)
        marks_path = t.hub / "data/import/marks.json"
        gid = iu.stable_id("snes", "games/snes/Lo Ok.sfc")
        earlier = int(time.time() * 1000) - 2 * 86_400_000
        iu.write_json_atomic(marks_path, {"new": {gid: earlier}, "hide": {}})
        code, out, _ = t.run("apply")                            # the same plan again: nothing copied
        self.assertEqual(code, 0, out)
        self.assertIn("already_placed", out)
        self.assertEqual(iu.read_marks(marks_path)["new"][gid], earlier)


class Absent(unittest.TestCase):
    def test_the_tool_refuses_both_forms_and_nothing_changes(self):
        t = Tree()
        snes(t.src / "snes" / "Lo Ok.sfc", 1)
        snes(t.plain / "snes" / "Lo Ok.sfc", 1)

        def listing():
            return sorted((str(p.relative_to(t.base)), p.stat().st_size, p.stat().st_mtime_ns)
                          for p in t.base.rglob("*"))
        before = listing()
        for env in ({}, {"PRIVYHUB_IMPORT": "0"}, {"PRIVYHUB_IMPORT": ""}, {"PRIVYHUB_IMPORT": "yes"}):
            for argv in (("inspect", "--source", str(t.plain / "snes"), "--system", "snes"),
                         ("plan", "--source", str(t.plain / "snes"), "--system", "snes"),
                         ("plan", str(t.stick)), ("apply",), ("verify",)):
                code, _, err = t.run(*argv, env=env)
                self.assertEqual(code, iu.EXIT_FLAG, argv)
                self.assertIn("nothing was read or written", err)
        self.assertEqual(listing(), before)


class Log(unittest.TestCase):
    def test_no_name_path_hash_or_id_in_the_log(self):
        t = Tree()
        snes(t.src / "snes" / "Lo Ok.sfc", 1)
        nes(t.src / "nes" / "Nes Ok.nes", 4)
        genesis(t.src / "genesis" / "Gen Md.md", 6)
        (t.src / "Private Stuff").mkdir()
        (t.src / "Private Stuff" / "x").write_text("x")
        t.run("plan", str(t.stick))
        self.crash_once = True

        def boom(part):
            if self.crash_once and "nes" in part.parts:
                self.crash_once = False
                raise KeyboardInterrupt
        iu._PART_HOOK = boom
        try:
            with self.assertRaises(KeyboardInterrupt):
                t.run("apply")
        finally:
            iu._PART_HOOK = None
        t.run("apply")
        t.run("verify")
        text = "".join(p.read_text() for p in (t.hub / "data/import/logs").glob("*.jsonl"))
        plan = json.loads(sorted((t.hub / "data/import/plans").glob("*.json"))[-1].read_text())
        forbidden = ["Lo Ok", "Nes Ok", "Gen Md", "Private", ".sfc", ".nes", ".md", str(t.base), iu.IMPORT_DIR]
        forbidden += [f["sha256"] for c in plan["candidates"] for f in c["files"] if f["sha256"]]
        forbidden += [c["game_id"] for c in plan["candidates"]] + [c["cid"] for c in plan["candidates"]]
        for word in forbidden:
            self.assertNotIn(word, text, word)
        for word in ('"system": "snes"', '"system": "nes"', '"journal": "resumed"', '"unknown_system_folder": 1',
                     '"source_form": "stick"'):
            self.assertIn(word, text)


class GitIgnore(unittest.TestCase):
    @unittest.skipUnless((ROOT / ".git").exists(), "a copy without .git (run in the tree)")
    def test_the_journal_the_new_libraries_and_a_stick_folder_are_ignored(self):
        import subprocess
        paths = ["data/import/journal.json", "games/snes/x.sfc", "games/nes/x.nes", "games/genesis/x.md",
                 "PrivyHub-Import/games/snes/x.sfc"]
        r = subprocess.run(["git", "check-ignore", *paths], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(sorted(r.stdout.split("\n")[:-1]), sorted(paths))


if __name__ == "__main__":
    unittest.main()
