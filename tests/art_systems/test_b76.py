#!/usr/bin/env python3
"""B76 (host): artwork and details for N64 / PS2 / GameCube through the hub's fetcher, behind PRIVYHUB_ART_SYSTEMS=1.

Fixtures only: made-up titles in clrmamepro text placed in an offline provider cache; a fetcher that fails the test if
it is ever called. Nothing is fetched; the temp dirs are removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b76.py' -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401

from games import metadata_importer as mi  # noqa: E402

ON = {"PRIVYHUB_ART_SYSTEMS": "1"}

def block(name: str, crc: str, **keys) -> str:
    """One clrmamepro game block, each key on its own line as RetroArch's .dat files have them."""
    lines = ["game (", f'\tname "{name}"']
    for k, v in keys.items():
        lines.append(f'\t{k} "{v}"' if not isinstance(v, int) else f"\t{k} {v}")
    lines += [f'\trom ( name "{name}.bin" crc {crc} )', ")", ""]
    return "\n".join(lines)


CATALOGS = {
    "n64": block("Alpha Racer (USA)", "AAAA0001", region="USA")
    + block("Alpha Racer (Europe)", "AAAA0002", region="Europe")
    + block("Bravo Kart (USA) (Rev 1)", "AAAA0003", region="USA")
    + block("Bravo Kart (USA)", "AAAA0004", region="USA"),
    "ps2": block("Charlie Quest (USA) (Disc 1)", "BBBB0001", region="USA", serial="SLUS-90001")
    + block("Charlie Quest (USA) (Disc 2)", "BBBB0002", region="USA", serial="SLUS-90002")
    + block("Delta Force Ops (USA)", "BBBB0003", region="USA", serial="SLUS-90003"),
    "gamecube": block("Echo Brawl (USA) (En,Ja) (Rev 2)", "CCCC0001", region="USA", serial="GXXE01")
    + block("Echo Brawl (USA) (En,Ja)", "CCCC0002", region="USA", serial="GXXE01")
    + block("Foxtrot Sun (Europe) (En,Fr,De)", "CCCC0003", region="Europe", serial="GYYP01"),
}


def fragment(comment: str, crc: str, key: str, value) -> str:
    v = value if isinstance(value, int) else f'"{value}"'
    return f'game (\n\tcomment "{comment}"\n\t{key} {v}\n\trom ( crc {crc} )\n)\n'


FRAGMENTS = {
    ("n64", "developer"): fragment("Alpha Racer (USA)", "AAAA0001", "developer", "Made Up Dev"),
    ("n64", "genre"): fragment("Alpha Racer (USA)", "AAAA0001", "genre", "Racing"),
    ("n64", "releaseyear"): fragment("Alpha Racer (USA)", "AAAA0001", "releaseyear", 1998),
    ("n64", "maxusers"): fragment("Alpha Racer (USA)", "AAAA0001", "users", 4),
    ("ps2", "maxusers"): fragment("Delta Force Ops (USA)", "BBBB0003", "users", 2),
    ("gamecube", "genre"): fragment("Foxtrot Sun", "CCCC0003", "genre", "Platform"),
}
# the user's file names as the in-place scanner turns them into titles (the stem; the suffix never reaches the title)
FILES = {
    "n64": ["Alpha Racer (USA).v64", "Bravo Kart (USA) (Rev 1).z64", "Nobody Here (USA).n64"],
    "ps2": ["Charlie Quest (USA) (Disc 2).chd", "Delta Force Ops (USA).iso", "Charlie Quest (Japan).chd"],
    "gamecube": ["Echo Brawl (USA) (En,Ja) (Rev 2).rvz", "Foxtrot Sun (Europe) (En,Fr,De).rvz"],
}


def project() -> Path:
    root = Path(tempfile.mkdtemp(prefix="b76_"))
    cache = root / "data/games/metadata/provider_cache/libretro"
    for system_id, text in CATALOGS.items():
        (cache / system_id).mkdir(parents=True, exist_ok=True)
        (cache / system_id / "catalog.dat").write_text(text, encoding="utf-8")
    for (system_id, folder), text in FRAGMENTS.items():
        (cache / system_id / f"{folder}.dat").write_text(text, encoding="utf-8")
    return root


def games() -> list[dict]:
    out = []
    for system_id, names in FILES.items():
        for i, name in enumerate(names):
            out.append({"id": f"game_{system_id}_{i:016d}", "title": Path(name).stem, "system": system_id,
                        "relative_path": f"{system_id}/{name}"})
    return out


def no_network(*_a, **_k):
    raise AssertionError("a fetch was attempted")


class Mapping(unittest.TestCase):
    def test_knob_on_adds_the_three_names(self):
        specs = mi.system_specs(ON)
        self.assertEqual(set(specs), {"nes", "snes", "genesis", "ps1", "n64", "ps2", "gamecube"})
        self.assertEqual(specs["n64"]["database_name"], "Nintendo - Nintendo 64")
        self.assertEqual(specs["ps2"]["database_name"], "Sony - PlayStation 2")
        self.assertEqual(specs["gamecube"]["database_name"], "Nintendo - GameCube")
        self.assertEqual(specs["n64"]["catalog_path"], "metadat/no-intro/Nintendo - Nintendo 64.dat")
        self.assertEqual(specs["ps2"]["catalog_path"], "metadat/redump/Sony - PlayStation 2.dat")
        self.assertEqual(specs["gamecube"]["catalog_path"], "metadat/redump/Nintendo - GameCube.dat")
        for s in ("n64", "ps2", "gamecube"):
            self.assertEqual(specs[s]["checksum_mode"], "title_fallback")

    def test_absent_or_other_values_are_todays_four(self):
        for env in ({}, {"PRIVYHUB_ART_SYSTEMS": "0"}, {"PRIVYHUB_ART_SYSTEMS": "true"}, {"PRIVYHUB_ART_SYSTEMS": ""}):
            self.assertEqual(mi.system_specs(env), mi.SYSTEM_SPECS)
            self.assertEqual(list(mi.system_specs(env)), ["nes", "snes", "genesis", "ps1"])
        self.assertEqual(set(mi.SYSTEM_SPECS), {"nes", "snes", "genesis", "ps1"})   # the module's table untouched

    def test_provider_default_reads_the_environment(self):
        root = project()
        with mock.patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("PRIVYHUB_ART_SYSTEMS", None)
            self.assertEqual(set(mi.LibretroProvider(root, offline=True).system_specs), set(mi.SYSTEM_SPECS))
            os.environ["PRIVYHUB_ART_SYSTEMS"] = "1"
            self.assertIn("gamecube", mi.LibretroProvider(root, offline=True).system_specs)


class Absent(unittest.TestCase):
    def test_three_systems_unavailable_without_any_fetch(self):
        root = project()
        p = mi.LibretroProvider(root, offline=False, specs=mi.system_specs({}))
        with mock.patch.object(mi, "_download_limited", no_network):
            for g in games():
                r = p.match_game(g)
                self.assertEqual(r["status"], "provider_unavailable")
                self.assertTrue(r["preserve_prior"])
                self.assertEqual(p.fetch_artwork(g, {"status": "matched", "canonical_title": "x"})["status"],
                                 "invalid_match")

    def test_prior_records_kept_by_a_run_without_the_knob(self):
        root = project()
        prior = {g["id"]: {"id": g["id"], "match": {"status": "matched", "canonical_title": "kept"},
                           "artwork": {"status": "downloaded"}} for g in games()}
        (root / "data/games").mkdir(parents=True, exist_ok=True)
        (root / "data/games/metadata.json").write_text(json.dumps({"games": prior}), encoding="utf-8")
        with mock.patch.object(mi, "scan_privyhub_games", lambda _r: games()), \
                mock.patch.object(mi, "_download_limited", no_network), \
                mock.patch.dict("os.environ", {"PRIVYHUB_ART_SYSTEMS": "0"}):
            report = mi.run_metadata_update(root, offline=False, download_artwork=True)
        self.assertEqual(report["counts"]["prior_preserved"], len(games()))
        written = json.loads((root / "data/games/metadata.json").read_text())["games"]
        self.assertEqual(written, prior)


class Matching(unittest.TestCase):
    def setUp(self):
        self.root = project()
        self.p = mi.LibretroProvider(self.root, offline=True, specs=mi.system_specs(ON))
        self.by_title = {g["title"]: g for g in games()}

    def match(self, title):
        with mock.patch.object(mi, "_download_limited", no_network):
            return self.p.match_game(self.by_title[title])

    def test_v64_stem_with_usa(self):
        r = self.match("Alpha Racer (USA)")
        self.assertEqual((r["status"], r["canonical_title"]), ("matched", "Alpha Racer (USA)"))

    def test_rev_tag(self):
        r = self.match("Bravo Kart (USA) (Rev 1)")
        self.assertEqual((r["status"], r["canonical_title"]), ("matched", "Bravo Kart (USA) (Rev 1)"))

    def test_chd_disc_tag(self):
        r = self.match("Charlie Quest (USA) (Disc 2)")
        self.assertEqual((r["status"], r["canonical_title"]), ("matched", "Charlie Quest (USA) (Disc 2)"))

    def test_iso_plain(self):
        self.assertEqual(self.match("Delta Force Ops (USA)")["status"], "matched")

    def test_rvz_language_and_rev_tags(self):
        r = self.match("Echo Brawl (USA) (En,Ja) (Rev 2)")
        self.assertEqual((r["status"], r["canonical_title"]), ("matched", "Echo Brawl (USA) (En,Ja) (Rev 2)"))
        self.assertEqual(self.match("Foxtrot Sun (Europe) (En,Fr,De)")["status"], "matched")

    def test_absent_title_and_wrong_region_miss(self):
        self.assertEqual(self.match("Nobody Here (USA)")["status"], "no_match")
        self.assertNotEqual(self.match("Charlie Quest (Japan)")["status"], "matched")

    def test_details_as_ps1(self):
        md = self.match("Alpha Racer (USA)")["metadata"]
        self.assertEqual((md["developer"], md["genre"], md["release_year"], md["max_players"]),
                         ("Made Up Dev", "Racing", 1998, 4))
        self.assertEqual(md["player_mode_suggested"], "multi")
        self.assertEqual(self.match("Delta Force Ops (USA)")["metadata"]["max_players"], 2)

    def test_artwork_url_uses_the_thumbnail_set(self):
        for system_id, name in (("n64", "Nintendo - Nintendo 64"), ("ps2", "Sony - PlayStation 2"),
                                ("gamecube", "Nintendo - GameCube")):
            url = self.p._artwork_url(system_id, "Some: Title")
            self.assertIn("/" + urllib.parse.quote(name, safe="") + "/Named_Boxarts/", url)
            self.assertTrue(url.endswith(urllib.parse.quote("Some_ Title.png", safe="")))

    def test_art_lands_by_game_id_in_the_shared_cache(self):
        g = self.by_title["Alpha Racer (USA)"]
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 16
        seen = []
        match = self.match("Alpha Racer (USA)")      # the match from the cached list (offline)
        p = mi.LibretroProvider(self.root, offline=False, specs=mi.system_specs(ON))
        with mock.patch.object(mi, "_download_limited", lambda url, **k: (seen.append(url), (png, "image/png"))[1]):
            r = p.fetch_artwork(g, match)
        self.assertEqual(r["status"], "downloaded")
        self.assertEqual(r["relative_path"], f"media/games/box_art/{g['id']}.png")
        self.assertEqual(len(seen), 1)
        self.assertIn("Nintendo%20-%20Nintendo%2064", seen[0])


class DryRun(unittest.TestCase):
    def run_dry(self, env, root=None):
        root = root or project()
        with mock.patch.object(mi, "_download_limited", no_network), \
                mock.patch.object(mi.LibretroProvider, "fetch_artwork", no_network):
            return root, mi.run_metadata_dry_run(root, offline=True, environ=env, games=games())

    def test_counts_and_labels(self):
        root, r = self.run_dry(ON)
        self.assertEqual(r["systems"]["n64"], {"total": 3, "matched": 2, "ambiguous": 0, "no_match": 1,
                                               "provider_unavailable": 0})
        self.assertEqual(r["systems"]["ps2"]["matched"], 2)
        self.assertEqual(r["systems"]["ps2"]["total"], 3)
        self.assertEqual(r["systems"]["gamecube"]["matched"], 2)
        self.assertEqual(r["misses"]["n64"], ["n64-miss-1"])
        self.assertEqual(r["misses"]["ps2"], ["ps2-miss-1"])
        self.assertNotIn("gamecube", r["misses"])

    def test_no_title_id_or_path_in_the_output(self):
        _root, r = self.run_dry(ON)
        text = json.dumps(r)
        for g in games():
            self.assertNotIn(g["title"].split(" (")[0], text)
            self.assertNotIn(g["id"], text)
        self.assertNotIn("/", text.replace("n64-", "").replace("ps2-", ""))

    def test_nothing_written_but_nothing_and_no_art(self):
        root = project()
        before = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
        self.run_dry(ON, root)
        after = sorted(str(p.relative_to(root)) for p in root.rglob("*"))
        self.assertEqual(before, after)
        self.assertFalse((root / "data/games/metadata.json").exists())
        self.assertFalse((root / "media").exists())

    def test_absent_knob_lists_them_as_not_offered(self):
        _root, r = self.run_dry({})
        self.assertEqual(r["systems"], {})
        self.assertEqual(r["not_offered"], {"n64": 3, "ps2": 3, "gamecube": 2})

    def test_unavailable_list_counts_without_fetching(self):
        root = Path(tempfile.mkdtemp(prefix="b76_empty_"))
        _root, r = self.run_dry(ON, root)
        self.assertEqual(r["systems"]["n64"]["provider_unavailable"], 3)
        self.assertEqual(r["misses"]["n64"], ["n64-miss-1", "n64-miss-2", "n64-miss-3"])


class Cli(unittest.TestCase):
    def test_choices_follow_the_knob_and_dry_run_flag_exists(self):
        import importlib
        import os
        sys.path.insert(0, str(ROOT / "tools"))
        import update_game_metadata as cli
        with mock.patch.dict("os.environ", {}):
            os.environ.pop("PRIVYHUB_ART_SYSTEMS", None)
            importlib.reload(cli)
            self.assertEqual(sorted(mi.system_specs()), ["genesis", "nes", "ps1", "snes"])
        text = (ROOT / "tools/update_game_metadata.py").read_text()
        self.assertIn("--dry-run", text)
        self.assertIn("choices=sorted(system_specs())", text)


if __name__ == "__main__":
    unittest.main()
