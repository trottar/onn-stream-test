#!/usr/bin/env python3
"""B83 (host): the real-entry-point audit of B76-B81 -- one test (or two) per item through the entry point A or the hub
calls: the tool's CLI, the plugin as the companion constructs it (`from plugins import PLUGINS`), its own handlers, and
`EmulatorManager.launch` (the plugin's own manager) on the game the plugin's scan finds.

Fixture trees from B82's builder (each with its own companion/ copy, so the companion's root is the tree); fake
emulator files; the fake AppImages are real zip archives holding the bundle at the path the code reads, so the real
readers run 7z. No emulator runs (a fake Popen; B49's / B69's session fakes; RetroArch's command-port wait and its
cheat-toggle exchange stubbed). Every run is a child `python3 -I` with only the test's PRIVYHUB_ values; any socket
connect / urlopen is counted and fails the test, except B76's fake picture server (RetroArch's thumbnail host only).
Made-up titles, ids and codes; temp dirs removed at exit.

    python3 -m unittest discover -s tests/art_systems -p 'test_b83.py' -v
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import _tmp_cleanup  # noqa: E402,F401
import test_b82 as b82  # noqa: E402  (the fixture tree, the flags)

FLAGS, ART = b82.FLAGS, b82.ART
FAKE_DOLPHIN_DIR = ROOT / "tests" / "gamecube_session"
RA_EXE = "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORES = "runtime/emulators/retroarch/cores-linux"
SERIAL, CRC = "SLUS-99901", "1234ABCD"          # made up
GID = "GZZE01"                                  # made up
GC_MAGIC = bytes.fromhex("C2339F3D")
SWAP = {"player1": {"b": "b", "a": "a"}}         # B77's swap (the bottom and right face buttons), as the onn sends it
N64_CHT = b'cheats = 1\n\ncheat0_desc = "Made Up Lives"\ncheat0_code = "8000AAAA 0003"\ncheat0_enable = false\n'
USER_CHT = (b'cheats = 2\n\ncheat0_desc = "My Own A"\ncheat0_code = "80000004 0001"\ncheat0_enable = false\n\n'
            b'cheat1_desc = "My Own B"\ncheat1_code = "80000008 0001"\ncheat1_enable = false\n')
PNACH = "gametitle=made up\n[Made Up Infinite Ammo]\npatch=1,EE,00100000,word,00000000\n"
GC_ID3 = "[Core]\nCPUThread = False\n[ActionReplay]\n$Made Up Infinite Health\n04000000 00000000\n" \
         "$Made Up Moon Jump\n04000004 00000000\n[Gecko]\n$Made Up Speed [someone]\nC2000000 00000000\n"
GC_ID6 = "[ActionReplay]\n$Made Up Infinite Health\n04000000 00000000\n$Made Up All Items\n04000008 00000000\n"

CHILD = r'''
import json, os, sys, threading, time, types, urllib.request, socket
from pathlib import Path
root = Path(sys.argv[2]).resolve()
NET = os.environ["B83_NET_LOG"]
def _count(kind):
    with open(NET, "a") as f:
        f.write(kind + "\n")
def _blocked(*a, **k):
    _count("attempt")
    raise OSError("network blocked by the test")
socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.create_connection = _blocked
PNG = b"\x89PNG\r\n\x1a\n" + b"1" * 32
class _Resp:
    def __init__(self, data): self._d = [data, b""]; self.headers = {"Content-Type": "image/png"}
    def read(self, n=-1): return self._d.pop(0) if self._d else b""
    def __enter__(self): return self
    def __exit__(self, *a): return False
def _urlopen(request, *a, **k):
    url = getattr(request, "full_url", str(request))
    if os.environ.get("B83_PICTURES") == "1" and url.startswith("https://thumbnails.libretro.com/"):
        _count("served")
        return _Resp(PNG)
    return _blocked()
urllib.request.urlopen = _urlopen
mode = sys.argv[1]
if mode == "tool":
    import runpy
    sys.argv = [sys.argv[3]] + sys.argv[4:]
    try:
        runpy.run_path(sys.argv[0], run_name="__main__")
    except SystemExit as e:
        sys.exit(e.code)
    sys.exit(0)
sys.path.insert(0, str(root / "companion"))
if mode == "seed_n64_cheats":                        # the real cheat update, its two fetchers faked
    import hashlib
    from games import cheat_importer as ci
    cht = bytes.fromhex(os.environ["B83_CHT"])
    sha = hashlib.sha1(b"blob " + str(len(cht)).encode() + b"\0" + cht).hexdigest()
    def fake_json(url):
        if "/contents/cht" in url:
            return [{"type": "dir", "name": "Nintendo - Nintendo 64", "sha": "tree64"}]
        if "/git/trees/tree64" in url:
            return {"truncated": False, "tree": [{"type": "blob", "path": "Alpha Racer (USA).cht", "sha": sha,
                                                  "size": len(cht)}]}
        raise AssertionError(url)
    ci._download_json = fake_json
    ci.LibretroCheatProvider._download_bytes = staticmethod(lambda url: cht)
    r = ci.run_cheat_update(root, only_system="n64")
    print(json.dumps(r["counts"]))
    sys.exit(0)

# --- the companion's own construction ---------------------------------------------------------------------------
from plugins import PLUGINS
g = PLUGINS["games"]
g._metadata_reconcile_thread.join(120)
from games import emulator_manager as em
m = g._emulator
calls = {"popen": [], "cheat_apply": 0}
out = {"reconcile_alive": g._metadata_reconcile_thread.is_alive()}

class FakePopen:
    def __init__(self, cmd, **kw):
        calls["popen"].append([str(c) for c in cmd]); self.pid = 999999999; self.returncode = None; self.stdin = None
    def poll(self): return self.returncode
    def wait(self, timeout=None): self.returncode = 0; return 0

def ps2_fakes():
    em.subprocess.Popen = FakePopen
    P = em._ps2
    class FakeSession(P.Session):                       # B49's rig
        def __init__(self, pid, log, **kw):
            clock = [0.0]
            def run(cmd, **kw):
                if "search" in cmd:
                    return types.SimpleNamespace(stdout="77\n")
                if cmd[:3] == ["pactl", "list", "sink-inputs"]:
                    return types.SimpleNamespace(stdout=f'application.process.id = "{pid}"\n')
                return types.SimpleNamespace(stdout="")
            super().__init__(pid, log, run=run, status=lambda: None, kill=lambda pid, sig: None,
                             sleep=lambda d: clock.__setitem__(0, clock[0] + d), clock=lambda: clock[0],
                             pine_path=root / "no-pine.sock", **kw)
    P.Session = FakeSession
    P.default_runner = lambda cmd: "deviceName = AMD Fake (RADV FAKE)\n"

def gc_fakes():
    sys.path.append(os.environ["B83_FAKE_DOLPHIN_DIR"])
    from fake_dolphin import FakeDolphin
    G = em._gc
    f = FakeDolphin(root, user_dir=root / "data/games/gamecube/user")
    class FakeProc:
        def __init__(self, pid): self.pid = pid; self.returncode = None; self.stdin = None
        def poll(self): return self.returncode
        def wait(self, timeout=None): self.returncode = 0; return 0
    em.subprocess.Popen = lambda cmd, **kw: (calls["popen"].append([str(c) for c in cmd]), FakeProc(f.pid))[1]
    base = G.Session
    class S(base):                                      # B69's rig
        def __init__(self, pid, log, **kw):
            super().__init__(pid, log, run=f.run, kill=f.kill, sleep=f.sleep, clock=f.clock, proc_root=f.proc,
                             grab=f.grab, **kw)
    G.Session = S
    G.wait_helpers = lambda sid, *a, **k: "gone 1.0s"

def retroarch_fakes():
    em.subprocess.Popen = FakePopen
    em.time.sleep = lambda s: None
    em.EmulatorManager._wait_for_retroarch_command_ready = lambda self, *a, **k: {"fake": True}
    def apply(self):                                    # RetroArch's network side of the cheat toggles (PS1's code)
        calls["cheat_apply"] += 1
        return {"fake": True}
    em.EmulatorManager._apply_active_cheat_profile = apply

def game(game_id):
    return g._find_game_by_id(game_id)                  # the plugin's own lookup (its scan)

def launch_args(query):                                 # the plugin's own parse of the onn's launch query
    from urllib.parse import parse_qs
    src, idx = g._parse_cheat_launch_request(parse_qs(query))
    return {"cheat_source_index": src, "cheat_enabled_indexes": idx} if src is not None else {}

args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
if mode == "ids":                                       # the titles as the companion's own list holds them
    out["ids"] = [[x["system"], x["title"], x["id"]] for x in g._scan()]
gid = args.get("id", "")
if mode == "details":
    out["details"] = g.handle("details", f"id={gid}")
elif mode == "profile_launch":
    created = g.handle_post("input-profile-create", "name=Swap&mapping=" + __import__("urllib.parse").parse.quote(
        json.dumps(args["mapping"])))
    pid = created.get("profile", created).get("id")
    out["assigned"] = g.handle_post("input-profile-assign", f"id={gid}&profile_id={pid}").get("ok")
    (ps2_fakes if args["kind"] == "pcsx2" else gc_fakes)()
    r = m.launch(game(gid))
    out["launch_kind"] = r.get("launch_kind")
elif mode == "cheats":
    out["catalog"] = g.handle_post_request("cheat-catalog", f"id={gid}", "127.0.0.1")
    if args.get("launch") is not None:
        {"pcsx2": ps2_fakes, "dolphin": gc_fakes, "retroarch": retroarch_fakes}[args["kind"]]()
        r = m.launch(game(gid), **launch_args(f"id={gid}&" + args["launch"]))
        out["launch_kind"] = r.get("launch_kind")
        out["active"] = r.get("active")
        out["cheat_apply"] = calls["cheat_apply"]
elif mode == "patches":
    out["before"] = g.handle("details", f"id={gid}").get("ps2_patches")
    out["set"] = g.handle("ps2-patches", f"id={gid}&ws=1&ni=0&fps60=0").get("ps2_patches")
    out["after"] = g.handle("details", f"id={gid}").get("ps2_patches")
    ps2_fakes()
    r = m.launch(game(gid))
    out["launch_kind"] = r.get("launch_kind")
out["popen"] = calls["popen"]
print(json.dumps(out, default=str))
'''


def run(root: Path, env: dict, mode: str, args: dict | None = None, *extra: str, pictures: bool = False):
    net = root.parent / (root.name + ".b83net")
    net.write_text("")
    xdg = root / "xdg"
    xdg.mkdir(exist_ok=True)
    child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    child_env.update(env)
    child_env.update({"B83_NET_LOG": str(net), "B83_FAKE_DOLPHIN_DIR": str(FAKE_DOLPHIN_DIR),
                      "XDG_CONFIG_HOME": str(xdg), "HOME": str(xdg), "B83_CHT": N64_CHT.hex(),
                      "B83_PICTURES": "1" if pictures else "0"})
    argv = [sys.executable, "-I", "-B", "-c", CHILD, mode, str(root)]
    argv += [json.dumps(args or {})] if mode != "tool" else list(extra)
    r = subprocess.run(argv, cwd=root, env=child_env, capture_output=True, text=True, timeout=300)
    seen = net.read_text().splitlines()
    net.unlink()
    return r, seen.count("attempt"), seen.count("served")


def out_of(r) -> dict:
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def zip_bytes(files: dict[str, bytes | str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


def tree() -> tuple[Path, dict]:
    """B82's fixture tree with box art in place and the emulators' fake files; returns it and {(system, title): id}
    as the plugin's own scan (the companion's construction) lists them."""
    root = b82.with_art(b82.make_tree())
    files = {RA_EXE: b"#!/bin/false\n",
             # the persistent config as the hub's: one save / state folder each (a cheat session replaces them)
             "data/games/retroarch/retroarch.cfg": 'config_save_on_exit = "false"\n'
                                                   'joypad_autoconfig_dir = "data/games/retroarch/autoconfig"\n'
                                                   'savefile_directory = "data/games/retroarch/saves"\n'
                                                   'savestate_directory = "data/games/retroarch/states"\n',
             "data/games/retroarch/autoconfig/udev/x.cfg": 'input_device = "x"\n',
             "runtime/emulators/pcsx2/pcsx2-fake.AppImage": zip_bytes({"usr/bin/resources/patches.zip": zip_bytes(
                 {f"{SERIAL}_{CRC}.pnach": "gametitle=x\n[Widescreen 16:9]\npatch=1,EE,0,word,0\n"
                                           "[60 FPS]\npatch=1,EE,4,word,0\n"})}),
             "runtime/emulators/dolphin/dolphin-fake.AppImage": zip_bytes(
                 {f"usr/share/dolphin-emu/Sys/GameSettings/{GID[:3]}.ini": GC_ID3,
                  f"usr/share/dolphin-emu/Sys/GameSettings/{GID}.ini": GC_ID6})}
    for c in ("mupen64plus_next_libretro.so", "mednafen_psx_hw_libretro.so", "bsnes_libretro.so"):
        files[f"{CORES}/{c}"] = b"\x7fELF"
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
    bios = root / "drive/bios"                          # PCSX2's BIOS folder (the paths file's BIOS_DIR=)
    bios.mkdir(parents=True)
    with open(bios / "image.bin", "wb") as f:
        f.truncate(4 * 1024 * 1024)
    (bios / "image.nvm").write_bytes(b"n")
    paths = root / "runtime/h3_p1_paths.txt"
    paths.write_text(paths.read_text() + f"BIOS_DIR={bios}\n", encoding="utf-8")
    disc = GID.encode() + b"\0" * (0x1C - 6) + GC_MAGIC + b"\0" * 0x60     # B79's made-up disc header (.rvz)
    gc_file = root / "drive/gamecube/Foxtrot Sun (Europe) (En,Fr,De).rvz"
    with open(gc_file, "wb") as f:
        f.write(b"RVZ\x01" + b"\0" * (0x58 - 4) + disc + b"\0" * 0x100)
        f.truncate((1 << 20) + 1)
    logs = root / "data/games/ps2/logs"                 # PCSX2's own log of an earlier launch (B80's ids)
    logs.mkdir(parents=True)
    (logs / "20261110T000000Z-pcsx2.log").write_text(
        "[    1.3691] Disc changed to Delta Force Ops (USA).iso.\n[    1.3691]   Name: x\n"
        f"[    1.3691]   Serial: {SERIAL}\n[    1.3691]   Version: 1.00\n[    1.3691]   CRC: {CRC}\n", encoding="utf-8")
    r, attempts, _ = run(root, FLAGS, "ids")
    ids = {(s, title): game_id for s, title, game_id in out_of(r)["ids"]}
    assert attempts == 0
    return root, ids


def log_text(root: Path, suffix: str) -> str:
    return "\n".join(p.read_text() for p in sorted((root / "logs/games").glob(f"*-{suffix}.log")))


class B76ArtThroughTheCli(unittest.TestCase):
    def test_a_fetched_title_reaches_the_cache_and_the_details(self):
        root, ids = tree()
        cache = root / "data/games/metadata/provider_cache/libretro/n64"
        crc = next(l.split("crc ")[1].split()[0] for l in (cache / "catalog.dat").read_text().splitlines()
                   if "Alpha Racer (USA)" in l and "crc" in l)
        for folder, key, value in (("developer", "developer", '"Made Up Dev"'), ("genre", "genre", '"Racing"'),
                                   ("releaseyear", "releaseyear", "1998"), ("maxusers", "users", "4")):
            (cache / f"{folder}.dat").write_text(
                f'game (\n\tcomment "Alpha Racer (USA)"\n\t{key} {value}\n\trom ( crc {crc} )\n)\n', encoding="utf-8")
        alpha, nobody = ids[("n64", "Alpha Racer (USA)")], ids[("n64", "Nobody Here (USA)")]
        (root / "media/games/box_art" / (alpha + ".png")).unlink(missing_ok=True)   # this one is fetched
        r, attempts, served = run(root, {**FLAGS, **ART}, "tool", None, str(root / "tools/update_game_metadata.py"),
                                  "--system", "n64", "--json", pictures=True)
        report = json.loads(r.stdout) if r.returncode == 0 else self.fail(r.stderr[-2000:])
        self.assertEqual(report["counts"]["matched"], 2)
        self.assertEqual((attempts, served), (0, 1))
        self.assertTrue((root / "media/games/box_art" / (alpha + ".png")).read_bytes().startswith(b"\x89PNG"))
        record = json.loads((root / "data/games/metadata.json").read_text())["games"][alpha]
        self.assertEqual(record["match"]["status"], "matched")
        # the list the onn reads: the plugin as the companion constructs it (no art knob in the companion)
        r, attempts, _ = run(root, FLAGS, "details", {"id": alpha})
        d = out_of(r)["details"]
        self.assertEqual((d.get("release_year"), d.get("genre"), d.get("max_players"), d.get("box_art_available")),
                         (1998, "Racing", 4, True), d)
        self.assertEqual(attempts, 0)
        d = out_of(run(root, FLAGS, "details", {"id": nobody})[0])["details"]
        self.assertFalse(d.get("metadata_available"))


class B77ProfilesThroughThePlugin(unittest.TestCase):
    def test_ps2_swap_written_by_the_launch(self):
        root, ids = tree()
        gid = ids[("ps2", "Delta Force Ops (USA)")]
        r, attempts, _ = run(root, FLAGS, "profile_launch", {"id": gid, "mapping": SWAP, "kind": "pcsx2"})
        out = out_of(r)
        self.assertEqual((out["assigned"], out["launch_kind"], attempts), (True, "pcsx2", 0))
        ini = (root / "data/games/ps2/config/PCSX2/inis/PCSX2.ini").read_text()
        self.assertIn("Cross = SDL-0/FaceEast", ini)
        self.assertIn("Circle = SDL-0/FaceSouth", ini)
        self.assertIn("PS2 input profile: assigned overrides=1", log_text(root, "ps2"))

    def test_gamecube_swap_written_by_the_launch(self):
        root, ids = tree()
        gid = ids[("gamecube", "Foxtrot Sun (Europe) (En,Fr,De)")]
        r, attempts, _ = run(root, FLAGS, "profile_launch", {"id": gid, "mapping": SWAP, "kind": "dolphin"})
        out = out_of(r)
        self.assertEqual((out["assigned"], out["launch_kind"], attempts), (True, "dolphin", 0))
        pad = (root / "data/games/gamecube/user/Config/GCPadNew.ini").read_text()
        self.assertIn("[GCPad1]\nDevice = evdev/0/PrivyHub Virtual Gamepad P1\nButtons/A = `EAST`\nButtons/B = `WEST`\n"
                      "Buttons/X = `SOUTH`", pad)
        self.assertIn("GC input profile: assigned overrides=1", log_text(root, "gamecube"))


class B78N64CheatsThroughThePlugin(unittest.TestCase):
    def test_the_list_and_the_launchs_staging(self):
        root, ids = tree()
        gid = ids[("n64", "Alpha Racer (USA)")]
        (root / "data/games/metadata.json").write_text(json.dumps({"games": {gid: {"id": gid, "system": "n64", "match": {
            "status": "matched", "canonical_title": "Alpha Racer (USA)", "metadata": {"region": "USA"}}}}}))
        r, attempts, _ = run(root, {"PRIVYHUB_N64": "1"}, "seed_n64_cheats")
        self.assertEqual(r.returncode, 0, r.stderr[-2000:])
        self.assertEqual((json.loads(r.stdout.strip().splitlines()[-1])["games_with_cheats"], attempts), (1, 0))
        r, attempts, _ = run(root, FLAGS, "cheats", {"id": gid, "kind": "retroarch",
                                                     "launch": "cheat_source=0&cheat_indexes=0"})
        out = out_of(r)
        self.assertEqual([e["description"] for e in out["catalog"]["sources"][0]["entries"]], ["Made Up Lives"])
        self.assertEqual((out["active"], out["cheat_apply"], attempts), (True, 1, 0))   # RetroArch: no launch_kind
        self.assertTrue(out["popen"][0][0].endswith("RetroArch-Linux-x86_64.AppImage"), out["popen"])
        staged = list(root.rglob("Mupen64Plus-Next/Alpha Racer (USA).cht"))
        self.assertEqual(len(staged), 1, staged)
        self.assertEqual(staged[0].read_bytes(), N64_CHT)


class B79GameCubeCheatsThroughThePlugin(unittest.TestCase):
    def test_the_bundled_names_listed_and_written_by_the_launch(self):
        root, ids = tree()
        gid = ids[("gamecube", "Foxtrot Sun (Europe) (En,Fr,De)")]
        r, attempts, _ = run(root, FLAGS, "cheats", {"id": gid, "kind": "dolphin",
                                                     "launch": "cheat_source=0&cheat_indexes=0,2"})
        out = out_of(r)
        names = [e["description"] for e in out["catalog"]["sources"][0]["entries"]]
        self.assertEqual(sorted(names), sorted(["Made Up Infinite Health", "Made Up Moon Jump", "Made Up Speed",
                                                "Made Up All Items"]), names)
        self.assertNotIn(GID, json.dumps(out["catalog"]))
        self.assertEqual((out["launch_kind"], attempts), ("dolphin", 0))
        user = (root / f"data/games/gamecube/user/GameSettings/{GID}.ini").read_text()
        picked = {names[0], names[2]}
        for name in picked:
            self.assertIn(f"${name}", user)
        self.assertIn("EnableCheats = True", (root / "data/games/gamecube/user/Config/Dolphin.ini").read_text())
        self.assertIn("GC cheats: 2 enabled", log_text(root, "gamecube"))


class B80PatchesThroughThePlugin(unittest.TestCase):
    def test_the_details_entry_the_toggle_and_the_launch(self):
        root, ids = tree()
        gid = ids[("ps2", "Delta Force Ops (USA)")]
        r, attempts, _ = run(root, FLAGS, "patches", {"id": gid})
        out = out_of(r)
        self.assertEqual(out["before"], {"available": ["ws", "60"], "on": []})
        self.assertEqual(out["set"], {"available": ["ws", "60"], "on": ["ws"]})
        self.assertEqual(out["after"], {"available": ["ws", "60"], "on": ["ws"]})
        self.assertEqual((out["launch_kind"], attempts), ("pcsx2", 0))
        written = [p for p in (root / "data/games/ps2").rglob(f"*{CRC}*.ini") if "gamesettings" in str(p).lower()]
        self.assertTrue(written, "no game settings file")
        for p in written:
            self.assertIn("EnableWideScreenPatches = true", p.read_text())
        self.assertIn("PS2 patches: ws=on", log_text(root, "ps2"))
        self.assertNotIn(SERIAL, json.dumps(out))


class B81DropInsThroughThePlugin(unittest.TestCase):
    FOLDERS = ("data/games/retroarch/cheats/ps1", "data/games/retroarch/cheats/snes", "data/games/ps2/cheats")

    def test_folders_at_the_first_list_then_a_pnach_listed_and_staged(self):
        root, ids = tree()
        gid = ids[("ps2", "Delta Force Ops (USA)")]
        for f in self.FOLDERS:
            self.assertFalse((root / f).exists())
        out = out_of(run(root, FLAGS, "cheats", {"id": gid})[0])
        for f in self.FOLDERS:
            self.assertTrue((root / f).is_dir(), f)
        self.assertEqual(sorted(p.name for f in self.FOLDERS for p in (root / f).iterdir()), [])
        self.assertNotEqual(out["catalog"].get("status"), "error")
        (root / "data/games/ps2/cheats" / SERIAL).mkdir()
        (root / "data/games/ps2/cheats" / SERIAL / "mine.pnach").write_text(PNACH, encoding="utf-8")
        r, attempts, _ = run(root, FLAGS, "cheats", {"id": gid, "kind": "pcsx2",
                                                     "launch": "cheat_source=0&cheat_indexes=0"})
        out = out_of(r)
        self.assertEqual([e["description"] for s in out["catalog"]["sources"] for e in s["entries"]], ["mine.pnach"])
        self.assertEqual((out["launch_kind"], attempts), ("pcsx2", 0))
        staged = list(root.rglob(f"cheats/{SERIAL}_{CRC}.pnach"))
        self.assertEqual(len(staged), 1, staged)
        self.assertIn("[Made Up Infinite Ammo]", staged[0].read_text())
        self.assertIn("PS2 cheats: 1 files enabled", log_text(root, "ps2"))

    def test_a_ps1_cht_listed_and_staged_by_a_launch(self):
        root, ids = tree()
        gid = ids[("ps1", "Juliet Run (USA)")]
        folder = root / "data/games/retroarch/cheats/ps1/Juliet Run (USA)"
        folder.mkdir(parents=True)
        (folder / "mine.cht").write_bytes(USER_CHT)
        listed = out_of(run(root, FLAGS, "cheats", {"id": gid})[0])["catalog"]
        user = [s for s in listed["sources"] if s.get("provider") == "user"]
        self.assertEqual([(s["filename"], s["cheat_count"]) for s in user], [("mine.cht", 2)])
        r, attempts, _ = run(root, FLAGS, "cheats", {
            "id": gid, "kind": "retroarch", "launch": f"cheat_source={user[0]['source_index']}&cheat_indexes=1"})
        out = out_of(r)
        self.assertEqual((out["active"], out["cheat_apply"], attempts), (True, 1, 0))   # RetroArch: no launch_kind
        self.assertTrue(out["popen"][0][0].endswith("RetroArch-Linux-x86_64.AppImage"), out["popen"])
        staged = list(root.rglob("Beetle PSX HW/Juliet Run (USA).cht"))
        self.assertEqual(len(staged), 1, staged)
        self.assertEqual(staged[0].read_bytes(), USER_CHT)


if __name__ == "__main__":
    unittest.main()
