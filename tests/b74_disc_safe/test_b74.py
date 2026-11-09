#!/usr/bin/env python3
"""B74 (host): the disc change made safe -- a set's launch starts on disc 1 (or the disc asked for) by RetroArch's own
disk index record, the settled swap sequence unchanged, `launched_disc` on the rows.

    python3 -m unittest discover -s tests/b74_disc_safe -v

A fake RetroArch boot reads the record as RetroArch 1.22 + Beetle do (index > 0 and the path equal to the `.m3u` entry
-> that disc, else disc 1) and writes the launch's own `Setting disc in tray: k/n - <label>` line; B71's fake command
port (a real UDP socket) answers the swap. Temp dirs removed at exit.
"""

from __future__ import annotations

import ast
import atexit
import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "tests/b71_disc_swap"))
import _tmp_cleanup  # noqa: E402,F401

import disc_swap as ds  # noqa: E402
from games import emulator_manager as em  # noqa: E402
import test_b71 as b71  # noqa: E402  (its FakeRetroArch and LABEL)

_OPEN: list = []
atexit.register(lambda: [h.close() for h in _OPEN])
CORE = "mednafen_psx_hw_libretro.so"


def project() -> Path:
    return Path(tempfile.mkdtemp(prefix="b74_proj_")).resolve()


def setup(n: int = 4, record_index: int | None = None, record_dir: str = "Beetle PSX HW", extra: dict | None = None,
          cue: bool = False):
    proj = project()
    content = proj / "games/ps1" / ("Set (Disc 1).cue" if cue else "Set.m3u")
    content.parent.mkdir(parents=True)
    if cue:
        content.write_text("FILE x\n")
    else:
        content.write_text("#EXTM3U\n" + "".join(f"Set (Disc {i}).cue\n" for i in range(1, n + 1)))
    saves = proj / "data/games/retroarch/saves"
    saves.mkdir(parents=True)
    cfg = proj / "data/games/retroarch/config/privyhub-session.cfg"
    cfg.parent.mkdir(parents=True)
    cfg.write_text(f'video_driver = "gl"\nsavefile_directory = "{saves}"\nnetwork_cmd_enable = "true"\n')
    rec = saves / record_dir / "Set.ldci"
    if record_index is not None:
        rec.parent.mkdir(parents=True, exist_ok=True)
        data = {"version": "1.0", "image_index": record_index,
                "image_path": str(content.parent / f"Set (Disc {record_index + 1}).cue")}
        data.update(extra or {})
        rec.write_text(json.dumps(data, indent=2) + "\n")
    m = em.EmulatorManager(proj)
    return m, proj, content, cfg, saves, rec


def fake_boot(content: Path, saves: Path, log_path: Path) -> int:
    """RetroArch's start: the record (core folder first, then the savefile dir) -> the disc; its own launch line."""
    entries = ds.m3u_entries(content)
    disc = 1
    for rec in (saves / "Beetle PSX HW" / "Set.ldci", saves / "Set.ldci"):
        if rec.is_file():
            try:
                d = json.loads(rec.read_text())
            except ValueError:
                break
            i = d.get("image_index")
            if isinstance(i, int) and 0 < i < len(entries) and d.get("image_path") == str(content.parent / entries[i]):
                disc = i + 1
            break
    with log_path.open("a") as h:
        h.write(f"[INFO] [Disc] Setting disc in tray: {disc}/{len(entries)} - {b71.LABEL} {disc}\n")
    return disc


def launch_like(m, content: Path, cfg: Path, saves: Path, start_disc, system: str = "ps1"):
    """launch()'s B74 part around a fake boot: the record before, the session after (as launch() writes them)."""
    game = {"id": "game_ps1_0123", "system": system}
    disc_start = m._disc_start_prepare(game, content, Path("/cores") / CORE, cfg, start_disc)
    log_path = m.project_root / "logs/games/x.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("PrivyHub game session\n" + (
        f"PS1 start disc: {disc_start[0]} of {disc_start[1]} (record {disc_start[2]})\n" if disc_start else ""))
    booted = fake_boot(content, saves, log_path) if content.suffix == ".m3u" else None
    m._disc_session = ds.session_for(content, system)
    m._disc_tail = ds.LogTail(log_path) if m._disc_session is not None else None
    if m._disc_session is not None:
        m._disc_session["launched_disc"] = None
        m._disc_session["_launch_line_open"] = True
        if disc_start is not None:
            m._disc_session.update(disc=disc_start[0], start_disc=disc_start[0])
    m._disc_refresh()
    return disc_start, booted, log_path


class Record(unittest.TestCase):
    def test_left_on_disc_4_starts_on_disc_1(self):
        m, proj, content, cfg, saves, rec = setup(record_index=3)
        before = fake_boot(content, saves, proj / "probe.log")                # today: RetroArch restores disc 4
        self.assertEqual(before, 4)
        disc_start, booted, log = launch_like(m, content, cfg, saves, 1)
        self.assertEqual(disc_start, (1, 4, "set"))
        self.assertEqual(booted, 1)
        d = json.loads(rec.read_text())
        self.assertEqual((d["image_index"], d["image_path"], d["version"]), (0, str(content.parent / "Set (Disc 1).cue"), "1.0"))
        self.assertEqual((m._disc_session["launched_disc"], m._disc_session["disc"], m._disc_session["start_disc"]), (1, 1, 1))
        self.assertIn("PS1 start disc: 1 of 4 (record set)", log.read_text())

    def test_disc_1_already_kept_byte_for_byte(self):
        m, proj, content, cfg, saves, rec = setup(record_index=0)
        os.utime(rec, (1_000_000_000, 1_000_000_000))
        raw = rec.read_bytes()
        disc_start, booted, _ = launch_like(m, content, cfg, saves, 1)
        self.assertEqual(disc_start[2], "kept")
        self.assertEqual(rec.read_bytes(), raw)
        self.assertEqual(rec.stat().st_mtime, 1_000_000_000)
        self.assertEqual(booted, 1)

    def test_no_record_and_disc_1_writes_nothing(self):
        m, proj, content, cfg, saves, rec = setup()
        disc_start, booted, _ = launch_like(m, content, cfg, saves, "1")
        self.assertEqual(disc_start[2], "none")
        self.assertEqual(list(saves.rglob("*")), [])
        self.assertEqual(booted, 1)

    def test_chosen_disc_3_created_in_the_cores_folder(self):
        m, proj, content, cfg, saves, rec = setup()
        disc_start, booted, _ = launch_like(m, content, cfg, saves, "3")
        self.assertEqual(disc_start, (3, 4, "set"))
        self.assertTrue(rec.is_file())
        self.assertEqual(json.loads(rec.read_text())["image_index"], 2)
        self.assertEqual(booted, 3)
        self.assertEqual((m._disc_session["launched_disc"], m._disc_session["disc"]), (3, 3))

    def test_core_folder_map(self):
        for core, folder in (("mednafen_psx_libretro.so", "Beetle PSX"), ("other_libretro.so", None)):
            m, proj, content, cfg, saves, rec = setup()
            self.assertEqual(ds.ldci_set(saves, core, content, 2), "set")
            where = (saves / folder / "Set.ldci") if folder else (saves / "Set.ldci")
            self.assertTrue(where.is_file(), core)

    def test_malformed_record_rewritten_other_keys_kept(self):
        m, proj, content, cfg, saves, rec = setup(record_index=2, extra={"other": 7})
        self.assertEqual(ds.ldci_set(saves, CORE, content, 1), "set")
        self.assertEqual(json.loads(rec.read_text())["other"], 7)
        rec.write_text("{ not json")
        self.assertEqual(ds.ldci_set(saves, CORE, content, 1), "set")
        self.assertEqual(json.loads(rec.read_text())["image_index"], 0)
        self.assertEqual(sorted(p.name for p in rec.parent.iterdir()), ["Set.ldci"])        # no temp file left

    def test_a_record_in_the_savefile_dir_itself(self):
        m, proj, content, cfg, saves, rec = setup(record_index=3, record_dir=".")
        self.assertEqual(ds.ldci_set(saves, CORE, content, 1), "set")
        self.assertEqual(json.loads((saves / "Set.ldci").read_text())["image_index"], 0)
        self.assertFalse((saves / "Beetle PSX HW").exists())

    def test_isolated_session_uses_its_own_savefile_dir(self):
        m, proj, content, cfg, saves, rec = setup(record_index=3)
        iso = proj / "data/games/retroarch/cheat_session/saves"
        (iso / "Beetle PSX HW").mkdir(parents=True)
        (iso / "Beetle PSX HW/Set.ldci").write_text(rec.read_text())
        cfg.write_text(f'savefile_directory = "{saves}"\nsavefile_directory = "{iso}"\n')   # the last assignment wins
        launch_like(m, content, cfg, saves, 1)
        self.assertEqual(json.loads((iso / "Beetle PSX HW/Set.ldci").read_text())["image_index"], 0)
        self.assertEqual(json.loads(rec.read_text())["image_index"], 3)                  # the other dir untouched

    def test_start_disc_parse(self):
        for value, want in ((None, 1), ("", 1), ("x", 1), ("0", 1), ("5", 1), ("-2", 1), (" 2 ", 2), (4, 4)):
            self.assertEqual(ds.parse_start_disc(value, 4), want, value)

    def test_the_relaunch_and_the_knob_write_nothing(self):
        m, proj, content, cfg, saves, rec = setup(record_index=3)
        raw = rec.read_bytes()
        disc_start, booted, _ = launch_like(m, content, cfg, saves, None)          # B54's relaunch: RetroArch's restore
        self.assertIsNone(disc_start)
        self.assertEqual(booted, 4)
        self.assertNotIn("start_disc", m._disc_session)
        self.assertEqual(m._disc_session["launched_disc"], 4)
        with mock.patch.dict("os.environ", {"PRIVYHUB_DISC_SWAP": "0"}):
            m2, proj2, content2, cfg2, saves2, rec2 = setup(record_index=3)
            raw2 = rec2.read_bytes()
            disc_start, booted, _ = launch_like(m2, content2, cfg2, saves2, 1)
            self.assertIsNone(disc_start)
            self.assertIsNone(m2._disc_session)
            self.assertEqual(rec2.read_bytes(), raw2)
        self.assertEqual(rec.read_bytes(), raw)

    def test_one_disc_game_untouched(self):
        m, proj, content, cfg, saves, rec = setup(cue=True)
        disc_start, booted, log = launch_like(m, content, cfg, saves, 1)
        self.assertIsNone(disc_start)
        self.assertIsNone(m._disc_session)
        self.assertEqual(log.read_text(), "PrivyHub game session\n")
        self.assertEqual(list(saves.rglob("*")), [])
        m1, proj1, c1, cfg1, s1, r1 = setup(n=1)                                     # a one-disc .m3u
        self.assertIsNone(launch_like(m1, c1, cfg1, s1, 1)[0])

    def test_no_path_returned_and_nothing_deleted(self):
        src = (ROOT / "companion/disc_swap.py").read_text()
        b74 = src[src.index("# --- B74"):]
        for word in ("unlink", "rmtree", "os.remove", ".rmdir"):
            self.assertNotIn(word, b74)
        tree = ast.parse(src)
        fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "ldci_set")
        returns = {ast.unparse(r.value) for r in ast.walk(fn) if isinstance(r, ast.Return)}
        self.assertEqual(returns, {"'none'", "'error'", "result"})
        assigned = {ast.unparse(a.value) for a in ast.walk(fn) if isinstance(a, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "result" for t in a.targets)}
        self.assertEqual(assigned, {"'kept'", "'set'"})


class LaunchWiring(unittest.TestCase):
    def test_launch_sets_the_record_before_retroarch_starts(self):
        src = (ROOT / "companion/games/emulator_manager.py").read_text()
        tree = ast.parse(src)
        launch = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "launch")
        body = ast.unparse(launch)
        self.assertIn("start_disc", [a.arg for a in launch.args.kwonlyargs])
        i_prep = body.index("self._disc_start_prepare(game, content_path, core_path, session_config, start_disc)")
        self.assertLess(i_prep, body.index("subprocess.Popen"))
        self.assertLess(body.index("PS1 start disc:"), body.index("subprocess.Popen"))
        after = body[body.index("subprocess.Popen"):]
        self.assertIn("self._disc_session['_launch_line_open'] = True", after)
        self.assertIn("self._disc_session.update(disc=disc_start[0], start_disc=disc_start[0])", after)

    def test_relaunch_ports_passes_no_start_disc(self):
        src = (ROOT / "companion/relaunch_ports.py").read_text()
        self.assertNotIn("start_disc", src)
        self.assertIn("emulator.launch(game, players_chosen=ports)", src)


class Sequence(unittest.TestCase):
    def manager(self, launch_line=True, index=0):
        m, fake, log = b71.manager(discs=4, index=index, launch_line=launch_line)
        m._disc_session.update(launched_disc=None, _launch_line_open=True, start_disc=index + 1)
        return m, fake, log

    def test_the_settled_sequence_unchanged(self):
        m, fake, log = self.manager()
        try:
            reply = m.disc_swap(3)
            self.assertEqual(fake.disk_commands(), ["DISK_EJECT_TOGGLE", "DISK_NEXT", "DISK_NEXT", "DISK_EJECT_TOGGLE"])
            self.assertNotIn("PAUSE_TOGGLE", [c for _, c in fake.commands])
            self.assertTrue(fake.paused)
            self.assertEqual((reply["from_disc"], reply["disc"], reply["steps"]), (1, 3, 2))
            ev = m._disc_event
            self.assertEqual(set(ev) - {"event"}, {"ok", "from_disc", "disc", "discs", "changed", "steps", "ms",
                                                  "launched_disc"})
            self.assertEqual(ev["launched_disc"], 1)
            gaps = [b - a for (a, x), (b, y) in zip(fake.commands, fake.commands[1:])
                    if x.startswith("DISK_") and y.startswith("DISK_")]
            self.assertTrue(all(g >= ds.GAP_S * 0.9 for g in gaps), gaps)
            text = log.read_text()
            self.assertIn("PS1 disc swap: 1 -> 3", text)
            self.assertNotIn(b71.LABEL, json.dumps(ev))
        finally:
            fake.close()

    def test_launched_disc_never_taken_from_a_swaps_line(self):
        m, fake, log = self.manager(launch_line=False)
        try:
            m.disc_swap(2)
            m._disc_refresh()
            self.assertIsNone(m._disc_session["launched_disc"])
            self.assertIsNone(m._disc_event["launched_disc"])
        finally:
            fake.close()

    def test_launched_disc_is_the_first_line_of_a_read(self):
        m, fake, log = self.manager(index=1)                                  # the launch line 2/4
        try:
            fake.index = 2
            fake.set_line()                                                   # a later 3/4 in the same read
            m._disc_refresh()
            self.assertEqual((m._disc_session["launched_disc"], m._disc_session["disc"]), (2, 3))
        finally:
            fake.close()

    def test_a_line_after_the_first_swap_is_never_the_launchs(self):
        m, fake, log = self.manager(launch_line=False)
        try:
            m.disc_swap(2)
            fake.index = 3
            fake.set_line()                                                   # any later line: not the launch's
            m._disc_refresh()
            self.assertIsNone(m._disc_session["launched_disc"])
            self.assertEqual(m._disc_session["disc"], 4)
        finally:
            fake.close()

    def test_failure_row_has_launched_disc(self):
        m, fake, log = b71.manager(discs=4, mode="silent_steps")
        m._disc_session.update(launched_disc=None, _launch_line_open=True)
        try:
            with self.assertRaises(em.EmulatorError):
                m.disc_swap(2)
            self.assertEqual((m._disc_event["ok"], m._disc_event["launched_disc"]), (False, 1))
        finally:
            fake.close()


class Plugin(unittest.TestCase):
    def plugin(self, payload, session=None, discs_for=None):
        import importlib.util
        spec = importlib.util.spec_from_file_location("g74", str(ROOT / "companion/plugins/games.py"))
        G = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(G)
        rows, calls = [], []
        p = object.__new__(G.GamesPlugin)
        p._recovery = types.SimpleNamespace(_log=lambda e, **k: rows.append({"event": e, **k}))

        def launch(game, **kw):
            calls.append(kw)
            return payload
        proj = project()
        p._emulator = types.SimpleNamespace(launch=launch, _launch_kind=None, _players_session=None,
                                            _last_device_args=[], active_game={"system": "ps1"},
                                            _disc_session=session,
                                            _project_path=lambda rel: proj / rel)
        p._find_game_by_id = lambda gid: {"id": gid, "system": "ps1", "relative_path": discs_for or "games/x.cue"}
        p._parse_cheat_launch_request = lambda q: (None, None)
        return p, rows, calls, proj

    def test_launch_query(self):
        today = {"cheat_source_index": None, "cheat_enabled_indexes": None, "mod_index": None}
        p, rows, calls, proj = self.plugin({}, discs_for="games/ps1/Set.m3u")
        (proj / "games/ps1").mkdir(parents=True)
        (proj / "games/ps1/Set.m3u").write_text("a.cue\nb.cue\nc.cue\n")
        p.handle_post("launch", "id=g")
        p.handle_post("launch", "id=g&disc=3")
        self.assertEqual([c.get("start_disc") for c in calls], [1, "3"])
        with mock.patch.dict("os.environ", {"PRIVYHUB_DISC_SWAP": "0"}):
            p.handle_post("launch", "id=g&disc=3")
        self.assertEqual(calls[-1], today)                                    # the knob: today's call
        p, rows, calls, proj = self.plugin({})                                # a one-disc game (a .cue)
        p.handle_post("launch", "id=g&disc=3")
        self.assertEqual(calls[-1], today)                                    # today's call, byte for byte

    def test_launch_ports_row(self):
        sess = {"discs": 4, "disc": 1, "start_disc": 1, "launched_disc": 1}
        p, rows, calls, _ = self.plugin({"discs": 4, "disc": 1}, session=sess)
        p.handle_post("launch", "id=g")
        r = [r for r in rows if r["event"] == "launch_ports"][0]
        self.assertEqual((r["discs"], r["disc"], r["start_disc"], r["launched_disc"]), (4, 1, 1, 1))
        p, rows, calls, _ = self.plugin({"discs": 4, "disc": 2}, session={"discs": 4, "disc": 2, "launched_disc": 2})
        p.handle_post("launch", "id=g")
        r = [r for r in rows if r["event"] == "launch_ports"][0]
        self.assertNotIn("start_disc", r)                                      # a session without B74's launch: B71's
        p, rows, calls, _ = self.plugin({})
        p.handle_post("launch", "id=g")
        r = [r for r in rows if r["event"] == "launch_ports"][0]
        for key in ("discs", "disc", "start_disc", "launched_disc"):
            self.assertNotIn(key, r)                                           # a one-disc game: today's row

    def test_details_discs_only_on_a_set(self):
        p, rows, calls, proj = self.plugin({}, discs_for="games/ps1/Set.m3u")
        (proj / "games/ps1").mkdir(parents=True)
        (proj / "games/ps1/Set.m3u").write_text("a.cue\nb.cue\n")
        p.details = lambda q: {"id": "g", "kind": "game"}
        p._tile_session_fields = lambda gid: {"live_session": None}
        self.assertEqual(p.handle("details", "id=g")["discs"], 2)
        with mock.patch.dict("os.environ", {"PRIVYHUB_DISC_SWAP": "0"}):
            self.assertNotIn("discs", p.handle("details", "id=g"))
        (proj / "games/ps1/Set.m3u").write_text("a.cue\n")
        self.assertNotIn("discs", p.handle("details", "id=g"))
        p2, *_ = self.plugin({})
        p2.details = lambda q: {"id": "g"}
        p2._tile_session_fields = lambda gid: {}
        self.assertEqual(p2.handle("details", "id=g"), {"id": "g"})            # a one-disc game: today's payload


if __name__ == "__main__":
    unittest.main()
