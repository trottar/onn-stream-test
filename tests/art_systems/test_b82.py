#!/usr/bin/env python3
"""B82 (host): the game scan sees every system the hub lists, through the real path.

Each test builds a fixture tree holding its own copy of companion/ and the two tools (so the tools' PROJECT_ROOT and the
plugin's are the tree), the hub's four game folders with fake files, fake in-place PS2 / N64 / GameCube folders named
by a fake runtime/h3_p1_paths.txt, and a fake provider: RetroArch's lists for all seven systems in the provider cache
(fresh) and a cheat index seeded through the real provider with fake fetchers. Every run is a child `python3 -I` with
only the test's PRIVYHUB_ values; a socket connect or urlopen in the child fails it and is counted. Made-up titles only;
nothing is fetched; the temp dirs are removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b82.py' -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import _tmp_cleanup  # noqa: E402,F401

FLAGS = {"PRIVYHUB_PS2": "1", "PRIVYHUB_N64": "1", "PRIVYHUB_GAMECUBE": "1"}
ART = {"PRIVYHUB_ART_SYSTEMS": "1"}
SEVEN = {"nes", "snes", "genesis", "ps1", "ps2", "n64", "gamecube"}

HUB_FILES = {"snes": ["Golf Hotel (USA).sfc", "India Pole (Europe).smc"],
             "ps1": ["Juliet Run (USA).chd", "Kilo Park (USA).iso"],
             "nes": [], "genesis": []}
INPLACE_FILES = {"ps2": ["Charlie Quest (USA) (Disc 2).chd", "Delta Force Ops (USA).iso"],
                 "n64": ["Alpha Racer (USA).v64", "Bravo Kart (USA) (Rev 1).z64", "Nobody Here (USA).n64"],
                 "gamecube": ["Echo Brawl (USA) (En,Ja) (Rev 2).rvz", "Foxtrot Sun (Europe) (En,Fr,De).rvz"]}
PATH_KEYS = {"ps2": "GAMES_DIR", "n64": "N64_DIR", "gamecube": "GAMECUBE_DIR"}
DATABASE = {"nes": "Nintendo - Nintendo Entertainment System", "snes": "Nintendo - Super Nintendo Entertainment System",
            "genesis": "Sega - Mega Drive - Genesis", "ps1": "Sony - PlayStation", "ps2": "Sony - PlayStation 2",
            "n64": "Nintendo - Nintendo 64", "gamecube": "Nintendo - GameCube"}
CATALOG_NAMES = {"nes": ["Lima Zone (USA)"], "genesis": ["Mike Drive (USA)"],
                 "snes": ["Golf Hotel (USA)", "India Pole (Europe)"], "ps1": ["Juliet Run (USA)", "Kilo Park (USA)"],
                 "ps2": ["Charlie Quest (USA) (Disc 2)", "Delta Force Ops (USA)"],
                 "n64": ["Alpha Racer (USA)", "Bravo Kart (USA) (Rev 1)"],
                 "gamecube": ["Echo Brawl (USA) (En,Ja) (Rev 2)", "Foxtrot Sun (Europe) (En,Fr,De)"]}
FRAGMENTS = ("developer", "publisher", "genre", "releaseyear", "maxusers")

# the child: the network blocked at the socket and urlopen, then one mode
RUNNER = r'''
import json, os, runpy, socket, sys, threading, urllib.request
def _blocked(*a, **k):
    with open(os.environ["B82_NET_LOG"], "a") as f:
        f.write("attempt\n")
    raise OSError("network blocked by the test")
socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.create_connection = _blocked
urllib.request.urlopen = _blocked
mode, root = sys.argv[1], os.path.abspath(sys.argv[2])
if mode == "tool":
    sys.argv = [sys.argv[3]] + sys.argv[4:]
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except SystemExit as e:
        sys.exit(e.code)
    sys.exit(0)
sys.path.insert(0, os.path.join(root, "companion"))
from pathlib import Path
if mode == "scan":
    from games import metadata_importer as mi
    games = mi.scan_privyhub_games(Path(root))
    threads = sorted(t.name for t in threading.enumerate())
    registry = hasattr(sys.modules.get("plugins"), "PLUGINS")
    # HEAD's code (the regression run) has no listing: None, so the scan's own checks fail for their own reason
    listed = mi.listed_privyhub_systems(Path(root)) if hasattr(mi, "listed_privyhub_systems") else None
    print(json.dumps({"games": [[g["system"], g["title"], g["id"], g["relative_path"]] for g in games],
                      "listed": listed, "registry_built": registry, "threads": threads}))
elif mode == "seed_cheats":
    import hashlib
    from games import cheat_importer as ci
    cht = b'cheats = 1\n\ncheat0_desc = "Made Up Lives"\ncheat0_code = "8000AAAA 0003"\ncheat0_enable = false\n'
    sha = hashlib.sha1(b"blob " + str(len(cht)).encode() + b"\0" + cht).hexdigest()
    def fake_json(url):
        if "/contents/cht" in url:
            return [{"type": "dir", "name": n, "sha": "tree_" + n[:3]} for n in
                    ("Nintendo - Nintendo 64", "Sony - PlayStation", "Nintendo - Super Nintendo Entertainment System")]
        if "/git/trees/" in url:
            return {"truncated": False, "tree": [{"type": "blob", "path": "Alpha Racer (USA).cht", "sha": sha,
                                                  "size": len(cht)}]}
        raise AssertionError(url)
    p = ci.LibretroCheatProvider(Path(root), json_fetcher=fake_json, bytes_fetcher=lambda u: cht)
    for s in sys.argv[3:]:
        p.entries_for_system(s)
    print(json.dumps(p.stats))
elif mode == "list":
    import re
    from plugins import PLUGINS          # the list the onn reads: the plugin's systems() as the companion builds it
    g = PLUGINS["games"]
    g._metadata_reconcile_thread.join(120)
    nodes = [n for n in g.systems()["nodes"] if str(n.get("id", "")).startswith("games_system_")]
    print(json.dumps({n["id"][len("games_system_"):]: int(re.search(r"\((\d+)\)$", n["name"]).group(1))
                      for n in nodes}))
elif mode == "reconcile":
    from plugins import PLUGINS          # the companion's own construction (privyhub_service imports it)
    thread = PLUGINS["games"]._metadata_reconcile_thread
    thread.join(120)
    print(json.dumps({"alive": thread.is_alive(),
                      "status": json.loads(Path(root, "logs/games/game_metadata_startup_reconcile.json").read_text())}))
'''


def block(name: str, crc: str) -> str:
    return f'game (\n\tname "{name}"\n\tregion "USA"\n\trom ( name "{name}.bin" crc {crc} )\n)\n'


def make_tree(code_root: Path = ROOT, *, gamecube_folder: bool = True, catalogs: tuple = tuple(SEVEN)) -> Path:
    root = Path(tempfile.mkdtemp(prefix="b82_"))
    shutil.copytree(code_root / "companion", root / "companion", ignore=shutil.ignore_patterns("__pycache__"))
    (root / "tools").mkdir()
    for tool in ("update_game_metadata.py", "update_game_cheats.py"):
        shutil.copy2(code_root / "tools" / tool, root / "tools" / tool)
    for system_id, names in HUB_FILES.items():
        folder = root / "games" / system_id
        folder.mkdir(parents=True)
        for i, name in enumerate(names):
            (folder / name).write_bytes(b"made up " + system_id.encode() + bytes([i]))
    lines = []
    for system_id, names in INPLACE_FILES.items():
        folder = root / "drive" / system_id
        lines.append(f"{PATH_KEYS[system_id]}={folder}")
        if system_id == "gamecube" and not gamecube_folder:
            continue
        folder.mkdir(parents=True)
        for name in names:
            with open(folder / name, "wb") as f:
                f.truncate((1 << 20) + 1 if system_id == "gamecube" else 64)   # sparse; GameCube's 1 MiB floor
    (root / "runtime").mkdir()
    (root / "runtime/h3_p1_paths.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    cache = root / "data/games/metadata/provider_cache/libretro"
    for n, system_id in enumerate(sorted(catalogs)):
        (cache / system_id).mkdir(parents=True)
        (cache / system_id / "catalog.dat").write_text(
            "".join(block(name, f"{n:02X}{i:06X}") for i, name in enumerate(CATALOG_NAMES[system_id])),
            encoding="utf-8")
        for folder in FRAGMENTS:
            (cache / system_id / f"{folder}.dat").write_text(
                f'game (\n\tcomment "x"\n\t{folder} "x"\n\trom ( crc FFFFFFFF )\n)\n', encoding="utf-8")
    return root


def run(root: Path, env: dict, *args: str, timeout: int = 180) -> tuple[subprocess.CompletedProcess, int]:
    net = root.parent / (root.name + ".net")
    net.write_text("")
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    child_env["B82_NET_LOG"] = str(net)
    r = subprocess.run([sys.executable, "-I", "-B", "-c", RUNNER, *args], cwd=root, env=child_env,
                       capture_output=True, text=True, timeout=timeout)
    attempts = len(net.read_text().splitlines())
    net.unlink()
    return r, attempts


def scan(root: Path, env: dict) -> dict:
    r, attempts = run(root, env, "scan", str(root))
    assert r.returncode == 0, r.stderr[-2000:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    out["attempts"] = attempts
    return out


def with_art(root: Path) -> Path:
    """Box art in the cache for every title the flags list: the companion's own startup reconcile has nothing to
    request."""
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 16
    (root / "media/games/box_art").mkdir(parents=True, exist_ok=True)
    for g in scan(root, FLAGS)["games"]:
        (root / "media/games/box_art" / (g[2] + ".png")).write_bytes(png)
    return root


def per_system(games: list) -> dict:
    out: dict[str, int] = {}
    for g in games:
        out[g[0]] = out.get(g[0], 0) + 1
    return out


def files_of(root: Path) -> list[str]:
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if "__pycache__" not in p.parts)


def tool(root: Path, env: dict, name: str, *args: str) -> tuple[subprocess.CompletedProcess, int]:
    return run(root, env, "tool", str(root), str(root / "tools" / name), *args)


class Scan(unittest.TestCase):
    def test_seven_systems_with_the_flags(self):
        # the regression: HEAD's __new__ scanner returned the class's four systems (ps1 / snes here) with the flags on
        root = make_tree()
        out = scan(root, FLAGS)
        self.assertEqual(per_system(out["games"]), {"snes": 2, "ps1": 2, "ps2": 2, "n64": 3, "gamecube": 2})
        self.assertEqual(set(out["listed"]), SEVEN)
        self.assertEqual({s: v["folder"] for s, v in out["listed"].items()}, {s: "available" for s in SEVEN})
        rels = {g[3] for g in out["games"]}
        self.assertIn("n64/Alpha Racer (USA).v64", rels)
        self.assertIn("gamecube/Foxtrot Sun (Europe) (En,Fr,De).rvz", rels)
        self.assertIn("ps2/Delta Force Ops (USA).iso", rels)
        self.assertEqual(out["attempts"], 0)

    def test_four_systems_without_the_flags(self):
        # absent: today's scan (passes on HEAD's code too)
        root = make_tree()
        out = scan(root, {})
        self.assertEqual(per_system(out["games"]), {"snes": 2, "ps1": 2})

    def test_the_list_without_the_flags_is_the_four(self):
        out = scan(make_tree(), {})
        self.assertEqual(set(out["listed"]), {"nes", "snes", "genesis", "ps1"})

    def test_each_flag_adds_its_own_system(self):
        root = make_tree()
        for flag, system_id in (("PRIVYHUB_PS2", "ps2"), ("PRIVYHUB_N64", "n64"), ("PRIVYHUB_GAMECUBE", "gamecube")):
            out = scan(root, {flag: "1"})
            self.assertEqual(set(per_system(out["games"])), {"snes", "ps1", system_id}, flag)

    def test_the_scan_does_not_build_the_companions_plugins(self):
        # the regression: HEAD's scan imported plugins/__init__.py, which constructed every plugin and started the
        # startup reconcile (a full metadata update) inside the tool's own process
        root = make_tree()
        before = files_of(root)
        out = scan(root, FLAGS)
        self.assertFalse(out["registry_built"])
        self.assertNotIn("PrivyHubGameMetadataReconcile", out["threads"])
        self.assertFalse((root / "data/games/metadata.json").exists())
        self.assertFalse((root / "logs").exists())
        self.assertEqual(files_of(root), before)

    def test_an_unreachable_folder_lists_no_titles_and_says_so(self):
        root = make_tree(gamecube_folder=False)
        out = scan(root, FLAGS)
        self.assertNotIn("gamecube", per_system(out["games"]))
        self.assertEqual(out["listed"]["gamecube"]["folder"], "unavailable")
        self.assertEqual(out["listed"]["n64"]["folder"], "available")
        self.assertFalse((root / "drive/gamecube").exists())       # never made


class MetadataCli(unittest.TestCase):
    def dry(self, root, env, *extra):
        r, attempts = tool(root, env, "update_game_metadata.py", "--dry-run", *extra)
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        return r.stdout, attempts

    def test_counts_for_all_seven(self):
        root = make_tree()
        before = files_of(root)
        text, attempts = self.dry(root, {**FLAGS, **ART}, "--json")    # online, as A runs it: the lists are fresh
        report = json.loads(text)
        self.assertEqual(set(report["systems"]), SEVEN)
        self.assertEqual({s: r["total"] for s, r in report["systems"].items()},
                         {"nes": 0, "genesis": 0, "snes": 2, "ps1": 2, "ps2": 2, "n64": 3, "gamecube": 2})
        self.assertEqual(report["systems"]["n64"]["matched"], 2)
        self.assertEqual(report["systems"]["gamecube"]["matched"], 2)
        self.assertEqual(report["systems"]["ps2"]["matched"], 2)
        self.assertEqual(report["listed"]["nes"], {"titles": 0, "folder": "available", "list": "not_needed"})
        self.assertEqual(report["listed"]["n64"], {"titles": 3, "folder": "available", "list": "available"})
        self.assertEqual(report["not_offered"], {})
        self.assertEqual(attempts, 0)
        self.assertEqual(files_of(root), before)                  # nothing written, no art, no metadata.json

    def test_folder_unavailable_and_list_unavailable_told_apart(self):
        root = make_tree(gamecube_folder=False, catalogs=tuple(SEVEN - {"n64"}))
        report = json.loads(self.dry(root, {**FLAGS, **ART}, "--json", "--offline")[0])
        self.assertEqual(report["listed"]["gamecube"], {"titles": 0, "folder": "unavailable", "list": "not_needed"})
        self.assertEqual(report["listed"]["n64"], {"titles": 3, "folder": "available", "list": "unavailable"})
        self.assertEqual(report["systems"]["n64"]["provider_unavailable"], 3)
        text = self.dry(root, {**FLAGS, **ART}, "--offline")[0]
        self.assertIn("gamecube: 0 matched, 0 unmatched of 0", text)
        self.assertIn("  folder unavailable (the drive or folder is not reachable)", text)
        self.assertIn("  list unavailable (RetroArch's list could not be read)", text)
        self.assertEqual(text.count("unavailable ("), 2)

    def test_without_the_art_knob_the_three_are_not_offered(self):
        root = make_tree()
        report = json.loads(self.dry(root, FLAGS, "--json")[0])
        self.assertEqual(set(report["systems"]), {"snes", "ps1"})
        self.assertEqual(report["not_offered"], {"ps2": 2, "n64": 3, "gamecube": 2})
        self.assertNotIn("listed", report)

    def test_absent_is_todays_report(self):
        root = make_tree()
        report = json.loads(self.dry(root, {}, "--json")[0])
        self.assertEqual(set(report), {"ok", "dry_run", "offline", "systems", "misses", "not_offered", "source_stats"})
        self.assertEqual(set(report["systems"]), {"snes", "ps1"})
        self.assertEqual(report["not_offered"], {})


class CheatCli(unittest.TestCase):
    def tree_with_matched_records(self):
        root = make_tree()
        out = scan(root, FLAGS)
        wanted = {("n64", "Alpha Racer (USA)"), ("ps2", "Delta Force Ops (USA)"),
                  ("gamecube", "Foxtrot Sun (Europe) (En,Fr,De)")}
        records = {g[2]: {"id": g[2], "system": g[0],
                          "match": {"status": "matched", "canonical_title": g[1], "metadata": {"region": "USA"}}}
                   for g in out["games"] if (g[0], g[1]) in wanted}
        self.assertEqual(len(records), 3)
        (root / "data/games/metadata.json").write_text(json.dumps({"games": records}), encoding="utf-8")
        r, attempts = run(root, FLAGS, "seed_cheats", str(root), "n64")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertEqual(attempts, 0)
        return root

    def test_n64_titles_through_the_tool(self):
        root = self.tree_with_matched_records()
        r, attempts = tool(root, {"PRIVYHUB_N64": "1"}, "update_game_cheats.py", "--system", "n64", "--no-download",
                           "--json")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        report = json.loads(r.stdout)
        self.assertEqual(report["counts"]["total_games"], 3)
        self.assertEqual(report["counts"]["games_with_cheats"], 1)
        self.assertEqual(report["counts"]["metadata_missing"], 2)
        self.assertEqual({g["system"] for g in report["games"]}, {"n64"})
        self.assertNotIn("not_offered", report)
        self.assertEqual(attempts, 0)
        self.assertFalse((root / "data/games/cheats.json").exists())     # --no-download writes no manifest

    def test_a_full_run_with_the_flags_skips_the_systems_without_a_list(self):
        root = self.tree_with_matched_records()
        r, attempts = tool(root, FLAGS, "update_game_cheats.py", "--no-download", "--json")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])        # HEAD + the scan alone: CheatError at ps2
        report = json.loads(r.stdout)
        self.assertEqual(report["not_offered"], {"ps2": 2, "gamecube": 2})
        self.assertEqual(report["counts"]["total_games"], 7)        # snes 2 + ps1 2 + n64 3
        self.assertEqual(report["counts"]["errors"], 0)
        self.assertEqual(attempts, 0)
        r, _ = tool(root, FLAGS, "update_game_cheats.py", "--no-download")
        self.assertIn("ps2: 2 not offered (no cheat list for this system)", r.stdout)

    def test_absent_flags_nothing_counted(self):
        root = make_tree()
        r, attempts = tool(root, {}, "update_game_cheats.py", "--no-download", "--offline", "--json")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        report = json.loads(r.stdout)
        self.assertNotIn("not_offered", report)
        self.assertEqual(report["counts"]["total_games"], 4)
        self.assertEqual(attempts, 0)


class ListAndScan(unittest.TestCase):
    def onn_list(self, root, env):
        r, attempts = run(root, env, "list", str(root))
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertEqual(attempts, 0)
        return json.loads(r.stdout.strip().splitlines()[-1])

    def test_the_dry_runs_systems_are_the_lists(self):
        for env, systems in ((FLAGS, SEVEN), ({}, {"nes", "snes", "genesis", "ps1"})):
            root = with_art(make_tree())
            shown = self.onn_list(root, env)
            self.assertEqual(set(shown), systems)
            out = scan(root, env)
            self.assertEqual({s: n for s, n in shown.items() if n}, per_system(out["games"]))
            self.assertEqual(set(out["listed"]), set(shown))
            r, _ = tool(root, {**env, **ART}, "update_game_metadata.py", "--dry-run", "--json")
            listed = json.loads(r.stdout)["listed"]
            self.assertEqual({s: v["titles"] for s, v in listed.items()}, shown)


class Reconcile(unittest.TestCase):
    def reconcile(self, root, env):
        r, attempts = run(root, env, "reconcile", str(root))
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertFalse(out["alive"])
        return out["status"], attempts

    def test_unchanged_for_the_four_and_the_three_with_the_flags(self):
        root = with_art(make_tree())                              # the art already cached: nothing to request
        first, attempts = self.reconcile(root, {})                 # no metadata yet: the four reconciled
        self.assertEqual(first["result"], "RECONCILED")
        self.assertEqual(first["discovered_count"], 4)
        self.assertEqual(attempts, 0)
        four = json.loads((root / "data/games/metadata.json").read_text())["games"]
        self.assertEqual({r["system"] for r in four.values()}, {"snes", "ps1"})
        again, attempts = self.reconcile(root, {})                 # without the flags: today's, nothing to do
        self.assertEqual(again["result"], "SKIPPED_CURRENT")
        self.assertEqual(again["discovered_count"], 4)
        with_flags, attempts = self.reconcile(root, FLAGS)
        self.assertEqual(with_flags["result"], "RECONCILED")
        self.assertEqual(with_flags["reasons"], ["library_changed"])
        self.assertEqual(with_flags["discovered_count"], 11)
        self.assertEqual(with_flags["metadata_update_counts"]["provider_unavailable"], 7)   # no art knob: no request
        self.assertEqual(attempts, 0)
        seven = json.loads((root / "data/games/metadata.json").read_text())["games"]
        self.assertEqual({r["system"] for r in seven.values()}, {"snes", "ps1", "ps2", "n64", "gamecube"})
        for game_id, record in four.items():                        # the four's records: the same match
            self.assertEqual(seven[game_id]["match"]["status"], record["match"]["status"])
        self.assertEqual({r["match"]["status"] for r in seven.values() if r["system"] in ("ps2", "n64", "gamecube")},
                         {"provider_unavailable"})


if __name__ == "__main__":
    unittest.main()
