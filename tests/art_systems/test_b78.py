#!/usr/bin/env python3
"""B78 (host): N64 cheats from RetroArch's cheat database, wired as PS1's, inside PRIVYHUB_N64=1
(PRIVYHUB_N64_CHEATS=0 = today).

Fixtures only: a made-up cheat index (root + an N64 tree) behind fake fetchers, a made-up title and .cht; nothing is
fetched, RetroArch is never started; temp dirs removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b78.py' -v
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

import n64_session  # noqa: E402
from games import cheat_importer as ci  # noqa: E402
from games import emulator_manager as em  # noqa: E402

N64_ON = {"PRIVYHUB_N64": "1"}
CHT = (b'cheats = 2\n\ncheat0_desc = "Made Up Lives"\ncheat0_code = "8000AAAA 0003"\ncheat0_enable = false\n\n'
       b'cheat1_desc = "Made Up Speed"\ncheat1_code = "8100BBBB FFFF"\ncheat1_enable = false\n')
GAME = {"id": "game_n64_0000000000000001", "title": "Alpha Racer (USA)", "system": "n64",
        "system_name": "Nintendo 64", "relative_path": "n64/Alpha Racer (USA).z64"}
META = {"match": {"status": "matched", "canonical_title": "Alpha Racer (USA)", "method": "title_exact_tagged",
                  "confidence": 0.995, "metadata": {"region": "USA"}}}


def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def fake_json(url: str):
    if "/contents/cht" in url:
        return [{"type": "dir", "name": "Nintendo - Nintendo 64", "sha": "tree64"},
                {"type": "dir", "name": "Sony - PlayStation", "sha": "treeps1"}]
    if "/git/trees/tree64" in url:
        return {"truncated": False, "tree": [
            {"type": "blob", "path": "Alpha Racer (USA).cht", "sha": blob_sha(CHT), "size": len(CHT)},
            {"type": "blob", "path": "Somebody Else (USA).cht", "sha": "0" * 40, "size": 1}]}
    raise AssertionError("unexpected index request")


def fake_bytes(url: str) -> bytes:
    assert url.endswith("Alpha%20Racer%20%28USA%29.cht"), url
    return CHT


def project() -> Path:
    root = Path(tempfile.mkdtemp(prefix="b78_"))
    (root / "data/games").mkdir(parents=True)
    (root / "data/games/metadata.json").write_text(json.dumps({"games": {GAME["id"]: META}}), encoding="utf-8")
    return root


def run_tool(root: Path, env: dict) -> dict:
    with mock.patch.dict(os.environ, env, clear=False), \
            mock.patch.object(ci, "scan_privyhub_games", lambda _r: [dict(GAME)]), \
            mock.patch.object(ci, "_download_json", fake_json), \
            mock.patch.object(ci.LibretroCheatProvider, "_download_bytes", staticmethod(fake_bytes)):
        for k in ("PRIVYHUB_N64", "PRIVYHUB_N64_CHEATS"):
            if k not in env:
                os.environ.pop(k, None)
        return ci.run_cheat_update(root, offline=False)


class Map(unittest.TestCase):
    def test_n64_only_with_the_flag(self):
        self.assertEqual(ci.cheat_system_specs(N64_ON)["n64"]["database_name"], "Nintendo - Nintendo 64")
        for env in ({}, {"PRIVYHUB_N64": "0"}, {"PRIVYHUB_N64": "1", "PRIVYHUB_N64_CHEATS": "0"}):
            self.assertEqual(ci.cheat_system_specs(env), ci.SYSTEM_SPECS)

    def test_cli_choices_from_the_map(self):
        text = (ROOT / "tools/update_game_cheats.py").read_text()
        self.assertIn("choices=sorted(cheat_system_specs())", text)


class Tool(unittest.TestCase):
    def test_the_title_matched_stored_and_in_the_manifest(self):
        root = project()
        report = run_tool(root, N64_ON)
        self.assertEqual(report["counts"]["games_with_cheats"], 1, report["counts"])
        manifest = json.loads((root / "data/games/cheats.json").read_text())["games"][GAME["id"]]
        self.assertEqual(manifest["status"], "cached")
        self.assertEqual(manifest["system"], "n64")
        f = manifest["files"][0]
        stored = root / f["local_path"]
        self.assertTrue(stored.is_file())
        self.assertIn(f"data/games/user_content/{GAME['id']}/cheats/libretro/", f["local_path"])
        self.assertEqual(f["cheat_count"], 2)

    def test_knob_zero_is_todays_refusal(self):
        # today's tool with an N64 title that has a matched record (after B76's fetch): it stops on the system it
        # does not know. Kept as today with the knob 0 (disclosed in KNOWN_ISSUES); absent PRIVYHUB_N64 the scanner
        # lists no N64 title at all.
        root = project()
        with self.assertRaises(ci.CheatError) as cm:
            run_tool(root, {"PRIVYHUB_N64": "1", "PRIVYHUB_N64_CHEATS": "0"})
        self.assertIn("Unsupported game system: n64", str(cm.exception))
        self.assertFalse((root / "data/games/user_content").exists())
        self.assertFalse((root / "data/games/cheats.json").exists())


class Manager(unittest.TestCase):
    def setUp(self):
        self.old = em._n64
        em._n64 = n64_session          # as PRIVYHUB_N64=1 sets it at import
        self.addCleanup(lambda: setattr(em, "_n64", self.old))
        self.root = project()
        run_tool(self.root, N64_ON)
        self.m = em.EmulatorManager(self.root, config_path=ROOT / "companion/games/config/emulators.json")

    def test_library_name(self):
        self.assertEqual(self.m._cheat_core_library_name("n64"), "Mupen64Plus-Next")
        self.assertEqual(self.m._cheat_core_library_name("ps1"), "Beetle PSX HW")
        with mock.patch.dict(os.environ, {"PRIVYHUB_N64_CHEATS": "0"}):
            self.assertIsNone(self.m._cheat_core_library_name("n64"))
        em._n64 = None
        self.assertIsNone(self.m._cheat_core_library_name("n64"))

    def test_the_onns_list_shape(self):
        cat = self.m.cheat_catalog(GAME)
        self.assertEqual(cat["status"], "cached")
        entries = cat["sources"][0]["entries"]
        self.assertEqual([e["description"] for e in entries], ["Made Up Lives", "Made Up Speed"])
        self.assertEqual([e["index"] for e in entries], [0, 1])

    def test_staged_for_the_n64_core(self):
        content = Path("/nowhere/Alpha Racer (USA).z64")
        root, session = self.m._prepare_cheat_runtime(GAME, content, 0, [0])
        staged = root / "Mupen64Plus-Next" / "Alpha Racer (USA).cht"
        self.assertTrue(staged.is_file())
        self.assertEqual(staged.read_bytes(), (self.root / json.loads(
            (self.root / "data/games/cheats.json").read_text())["games"][GAME["id"]]["files"][0]["local_path"]
        ).read_bytes())
        self.assertEqual(session["enabled_cheat_indexes"], [0])
        self.assertEqual(session["session_kind"], "cheat")

    def test_without_the_flag_the_launch_prep_refuses(self):
        em._n64 = None
        with self.assertRaises(em.EmulatorError) as cm:
            self.m._prepare_cheat_runtime(GAME, Path("/nowhere/x.z64"), 0, [0])
        self.assertIn("No validated RetroArch cheat library name", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
