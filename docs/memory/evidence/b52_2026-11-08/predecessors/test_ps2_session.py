#!/usr/bin/env python3
"""B49 (host): the PS2 launch kind behind PRIVYHUB_PS2=1 -- the folders, the list, the ini, the pads, the BIOS copy,
the command, pause / resume / exit, the save-state behaviours off, the rows -- and absent = today. Fakes only: temp
folders with made-up names; no real BIOS, title or folder, and PCSX2 is never started.

    python3 -m unittest discover -s tests/ps2_session -v
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(ROOT / "tools"))

import ps2_session as ps2  # noqa: E402
import players_session  # noqa: E402
import ps2_p2_frames as p2  # noqa: E402


def tree(files: dict[str, bytes | str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="b49_"))
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
    return root


def snapshot(root: Path) -> list[tuple[str, int, float]]:
    return sorted((str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime) for p in root.rglob("*"))


class Paths(unittest.TestCase):
    def test_the_flag(self):
        self.assertTrue(ps2.enabled({"PRIVYHUB_PS2": "1"}))
        for v in (None, "", "0", "true", "yes"):
            self.assertFalse(ps2.enabled({} if v is None else {"PRIVYHUB_PS2": v}))

    def test_the_paths_file_two_keys_only(self):
        proj = tree({"runtime/h3_p1_paths.txt": "BIOS_DIR=/fake/bios\nGAMES_DIR=/fake/games\nT1=ignored\nX\n"})
        self.assertEqual(ps2.read_paths(proj, {}), {"bios_dir": Path("/fake/bios"), "games_dir": Path("/fake/games")})
        named = tree({"p.txt": "GAMES_DIR=/other\n"})
        self.assertEqual(ps2.read_paths(proj, {"PRIVYHUB_PS2_PATHS": str(named / "p.txt")}),
                         {"bios_dir": None, "games_dir": Path("/other")})
        self.assertEqual(ps2.read_paths(tree({}), {}), {"bios_dir": None, "games_dir": None})

    def test_one_appimage(self):
        proj = tree({"runtime/emulators/pcsx2/pcsx2-vX.AppImage": b"x"})
        self.assertEqual(ps2.find_appimage(proj).name, "pcsx2-vX.AppImage")
        with self.assertRaises(ps2.PS2Error):
            ps2.find_appimage(tree({}))
        with self.assertRaises(ps2.PS2Error):
            ps2.find_appimage(tree({"runtime/emulators/pcsx2/a.AppImage": b"x", "runtime/emulators/pcsx2/b.AppImage": b"x"}))


class Listing(unittest.TestCase):
    def test_the_rules_and_nothing_written(self):
        g = tree({
            "alpha.chd": b"1", "alpha.iso": b"22",                        # twice: .chd preferred
            "beta.iso": b"333",
            "gamma.bin": b"4", "gamma.cue": 'FILE "gamma.bin" BINARY\n',  # .cue listed, .bin never itself
            "delta.bin": b"5",                                            # .bin without .cue: skipped
            "eps.cue": 'FILE "missing.bin" BINARY\n',                     # .cue with a missing file: skipped
            ".hidden.chd": b"6", "sub/zeta.chd": b"7", "notes.txt": b"8",
        })
        before = snapshot(g)
        got = [(t["relative"], t["suffix"]) for t in ps2.list_titles(g)]
        self.assertEqual(got, [("alpha.chd", ".chd"), ("beta.iso", ".iso"), ("gamma.cue", ".cue"), ("sub/zeta.chd", ".chd")])
        self.assertEqual(before, snapshot(g))
        self.assertEqual(ps2.list_titles(None), [])
        self.assertEqual(ps2.list_titles(g / "absent"), [])
        self.assertFalse((g / "absent").exists())

    def test_resolve_refuses_escapes(self):
        g = tree({"a.chd": b"1"})
        self.assertEqual(ps2.resolve_title(g, "ps2/a.chd"), (g / "a.chd").resolve())
        for bad in ("ps2/../x.chd", "games/ps1/a.chd", "ps2/missing.chd"):
            with self.assertRaises(ps2.PS2Error):
                ps2.resolve_title(g, bad)
        with self.assertRaises(ps2.PS2Error):
            ps2.resolve_title(None, "ps2/a.chd")


class Ini(unittest.TestCase):
    def test_merge_keeps_foreign_keys_and_sets_ours(self):
        text = "[UI]\nTheme = dark\nStartFullscreen = false\n\n[EmuCore/GS]\nRenderer = 12\nVsyncEnable = false\n"
        s = ps2.settings_for(Path("/proj"), "image.bin", "AMD Radeon Graphics (RADV TEST)", 2, False)
        out = ps2.ini_merge(text, s)
        self.assertEqual(ps2.ini_get(out, "UI", "Theme"), "dark")
        self.assertEqual(ps2.ini_get(out, "UI", "StartFullscreen"), "true")
        self.assertEqual(ps2.ini_get(out, "EmuCore/GS", "Renderer"), "14")
        self.assertEqual(ps2.ini_get(out, "EmuCore/GS", "VsyncEnable"), "true")          # B50: ours now (tears)
        self.assertEqual(ps2.ini_get(out, "EmuCore/GS", "upscale_multiplier"), "1")
        for k in ("OsdShowSpeed", "OsdShowFPS", "OsdShowVPS", "OsdShowCPU", "OsdShowGPU", "OsdShowResolution"):
            self.assertEqual(ps2.ini_get(out, "EmuCore/GS", k), "false")
        self.assertEqual(ps2.ini_get(out, "EmuCore/GS", "Adapter"), "AMD Radeon Graphics (RADV TEST)")
        self.assertEqual(ps2.ini_get(out, "AutoUpdater", "CheckAtStartup"), "false")
        self.assertEqual(ps2.ini_get(out, "EmuCore", "EnableDiscordPresence"), "false")
        self.assertEqual(ps2.ini_get(out, "EmuCore", "EnablePINE"), "true")
        self.assertEqual(ps2.ini_get(out, "Folders", "MemoryCards"), "/proj/data/games/ps2/memcards")
        self.assertEqual(ps2.ini_get(out, "Folders", "Savestates"), "/proj/data/games/ps2/sstates")
        self.assertEqual(ps2.ini_get(out, "Folders", "Bios"), "/proj/data/games/ps2/bios")
        self.assertEqual(ps2.ini_get(out, "Filenames", "BIOS"), "image.bin")
        self.assertEqual(ps2.ini_get(out, "Hotkeys", "TogglePause"), "Keyboard/Space")
        self.assertEqual(ps2.ini_merge(out, s), out)                     # idempotent

    def test_the_adapter_rules(self):
        self.assertEqual(ps2.pick_adapter("AMD X (RADV Y)", None), "AMD X (RADV Y)")
        fake = lambda cmd: "deviceName = llvmpipe (LLVM)\n deviceName = AMD Radeon Graphics (RADV FAKE)\n"
        self.assertEqual(ps2.pick_adapter("llvmpipe", fake), "AMD Radeon Graphics (RADV FAKE)")
        self.assertIsNone(ps2.pick_adapter(None, lambda cmd: "deviceName = llvmpipe\n"))
        self.assertIsNone(ps2.pick_adapter(None, lambda cmd: (_ for _ in ()).throw(OSError())))


class Pads(unittest.TestCase):
    def test_two_players_no_multitap(self):
        s = ps2.pad_sections(2, False)
        self.assertEqual(s["Pad"], {"MultitapPort1": "false", "MultitapPort2": "false"})
        self.assertEqual(s["Pad1"]["Cross"], "SDL-0/FaceSouth")
        self.assertEqual(s["Pad2"]["Cross"], "SDL-1/FaceSouth")
        self.assertEqual(s["Pad2"]["Type"], "DualShock2")
        self.assertTrue(all(s[f"Pad{n}"] == {"Type": "None"} for n in range(3, 9)))

    def test_the_ds2_layout(self):
        p1 = ps2.pad_sections(2, False)["Pad1"]
        self.assertEqual({k: p1[k] for k in ("Triangle", "Circle", "Square", "Select", "Start", "L2", "R2", "L3", "R3",
                                             "LUp", "LRight", "RDown", "Up")},
                         {"Triangle": "SDL-0/FaceNorth", "Circle": "SDL-0/FaceEast", "Square": "SDL-0/FaceWest",
                          "Select": "SDL-0/Back",
                          "Start": "SDL-0/Start", "L2": "SDL-0/+LeftTrigger", "R2": "SDL-0/+RightTrigger",
                          "L3": "SDL-0/LeftStick", "R3": "SDL-0/RightStick", "LUp": "SDL-0/-LeftY",
                          "LRight": "SDL-0/+LeftX", "RDown": "SDL-0/+RightY", "Up": "SDL-0/DPadUp"})
        self.assertEqual(len(p1), 1 + 24)

    def test_four_on_the_multitap_in_creation_order(self):
        s = ps2.pad_sections(4, True)
        self.assertEqual(s["Pad"]["MultitapPort1"], "true")
        self.assertEqual([s[f"Pad{n}"].get("Cross") for n in (1, 3, 4, 5)],
                         ["SDL-0/FaceSouth", "SDL-1/FaceSouth", "SDL-2/FaceSouth", "SDL-3/FaceSouth"])
        self.assertEqual(s["Pad2"], {"Type": "None"})

    def test_one_player_one_port(self):
        s = ps2.pad_sections(1, False)
        self.assertEqual(s["Pad1"]["Type"], "DualShock2")
        self.assertEqual(s["Pad2"], {"Type": "None"})

    def test_the_sdl_line_and_the_environment(self):
        self.assertEqual(ps2.SDL_MAPPING,
                         "03000000091200004850000001000000,PrivyHub Virtual Gamepad,a:b0,b:b1,y:b2,x:b3,"
                         "leftshoulder:b4,rightshoulder:b5,back:b6,start:b7,leftstick:b8,rightstick:b9,leftx:a0,"
                         "lefty:a1,lefttrigger:a2,rightx:a3,righty:a4,righttrigger:a5,dpup:h0.1,dpright:h0.2,"
                         "dpdown:h0.4,dpleft:h0.8,platform:Linux,")
        env = ps2.launch_env({"DISPLAY": ":9"})
        self.assertEqual(env["DISPLAY"], ":9")
        self.assertEqual(env["SDL_GAMECONTROLLERCONFIG"], ps2.SDL_MAPPING)

    def test_the_guid_matches_the_companions_pads(self):
        import native_session_io as nsi
        b = nsi.NativeControllerBridge
        guid = "0300" + "0000" + b.LINUX_VENDOR_ID.to_bytes(2, "little").hex() + "0000" + \
            b.LINUX_PRODUCT_ID.to_bytes(2, "little").hex() + "0000" + b.LINUX_VERSION_ID.to_bytes(2, "little").hex() + "0000"
        self.assertEqual(ps2.SDL_MAPPING.split(",")[0], guid)

    def test_the_plan_for_ps2(self):
        for n, (ports, tap) in {1: (1, False), 2: (2, False), 4: (4, True)}.items():
            p = players_session.plan("ps2", n, None)
            self.assertEqual((p["ports"], p["multitap"], p["multitap_available"], p["device_args"], p["ps1_mode"]),
                             (ports, tap, True, [], None))


class Bios(unittest.TestCase):
    def test_copied_once_never_overwritten_and_the_source_unchanged(self):
        src = tree({"image.bin": b"\0" * ps2.BIOS_IMAGE_BYTES, "image.nvm": b"n1", "image.mec": b"m"})
        before = snapshot(src)
        hub = Path(tempfile.mkdtemp()) / "bios"
        self.assertEqual(ps2.bios_copy_once(src, hub), 3)
        (hub / "image.nvm").write_bytes(b"written-on-the-hub")
        (src / "image.nvm").write_bytes(b"n1")                       # (the same bytes as before)
        self.assertEqual(ps2.bios_copy_once(src, hub), 0)
        self.assertEqual((hub / "image.nvm").read_bytes(), b"written-on-the-hub")
        self.assertEqual([x[:2] for x in before], [x[:2] for x in snapshot(src)])
        self.assertEqual(ps2.choose_bios(hub, None), "image.bin")
        self.assertEqual(ps2.choose_bios(hub, "image.mec"), "image.mec")
        with self.assertRaises(ps2.PS2Error):
            ps2.bios_copy_once(None, Path(tempfile.mkdtemp()) / "b")

    def test_the_command(self):
        cmd = ps2.command(Path("/proj/runtime/emulators/pcsx2/x.AppImage"), Path("/proj"), Path("/games/a.chd"))
        self.assertEqual(cmd, ["/proj/runtime/emulators/pcsx2/x.AppImage", "-datapath", "/proj/data/games/ps2/config",
                               "-nogui", "-fullscreen", "--", "/games/a.chd"])


class FakeProc:
    def __init__(self, exits_on_term=True):
        self.exits_on_term = exits_on_term
        self.signals = []
        self.returncode = None

    def wait(self, timeout=None):
        if self.exits_on_term and signal.SIGTERM in self.signals or signal.SIGKILL in self.signals:
            self.returncode = 0
            return 0
        raise subprocess.TimeoutExpired("x", timeout)


def session(statuses, proc=None):
    """A Session on fakes: `statuses` the PINE answers in turn (the last repeats), xdotool finds window 77."""
    calls, lines = [], []
    seq = list(statuses)

    def run(cmd, **kw):
        calls.append(cmd)
        return types.SimpleNamespace(stdout="77\n" if "search" in cmd else "")

    def status():
        return seq.pop(0) if len(seq) > 1 else seq[0]

    def kill(pid, sig):
        calls.append(("kill", sig))
        if proc is not None:
            proc.signals.append(sig)

    clock = [0.0]
    s = ps2.Session(4242, lines.append, run=run, status=status, kill=kill, sleep=lambda d: clock.__setitem__(0, clock[0] + d),
                    clock=lambda: clock[0])
    return s, calls, lines


class PauseResume(unittest.TestCase):
    def test_the_hotkey_confirmed_by_pine(self):
        s, calls, lines = session([ps2.PINE_RUNNING, ps2.PINE_PAUSED])
        self.assertEqual(s.pause(), "hotkey")
        self.assertIn(["xdotool", "key", "--clearmodifiers", "space"], calls)
        self.assertNotIn(("kill", signal.SIGSTOP), calls)
        s.status = lambda seq=[ps2.PINE_PAUSED, ps2.PINE_RUNNING]: seq.pop(0) if len(seq) > 1 else seq[0]
        self.assertEqual(s.resume(), "hotkey")
        self.assertEqual(lines, ["PS2 pause: hotkey", "PS2 resume: hotkey"])

    def test_pine_unreachable_is_sigstop_and_sigcont(self):
        s, calls, lines = session([None])
        self.assertEqual(s.pause(), "sigstop")
        self.assertNotIn(["xdotool", "key", "--clearmodifiers", "space"], calls)   # no unconfirmable hotkey
        self.assertEqual(s.resume(), "sigcont")
        self.assertEqual([c for c in calls if c[0] == "kill"], [("kill", signal.SIGSTOP), ("kill", signal.SIGCONT)])
        self.assertEqual(lines, ["PS2 pause: sigstop", "PS2 resume: sigcont"])

    def test_an_unconfirmed_hotkey_falls_back_to_sigstop(self):
        s, calls, _ = session([ps2.PINE_RUNNING])                      # PINE answers but never says paused
        self.assertEqual(s.pause(), "sigstop")
        self.assertIn(("kill", signal.SIGSTOP), calls)
        self.assertEqual(s.pause(), "sigstop")                         # a second pause: no second signal
        self.assertEqual(sum(1 for c in calls if c == ("kill", signal.SIGSTOP)), 1)

    def test_exit_by_sigterm_else_sigkill(self):
        proc = FakeProc(True)
        s, calls, lines = session([None], proc)
        s.pause()
        self.assertTrue(s.stop(proc).startswith("sigterm"))
        self.assertEqual(proc.signals, [signal.SIGSTOP, signal.SIGCONT, signal.SIGTERM])  # continued before the TERM
        stubborn = FakeProc(False)
        s2, _, lines2 = session([None], stubborn)
        self.assertEqual(s2.stop(stubborn), "sigkill")
        self.assertEqual(stubborn.signals, [signal.SIGTERM, signal.SIGKILL])
        self.assertEqual(lines2, ["PS2 exit: sigkill"])

    def test_pine_status_on_a_fake_socket(self):
        import socket as so
        import struct
        import threading
        d = Path(tempfile.mkdtemp())
        path = d / "pcsx2.sock"
        srv = so.socket(so.AF_UNIX, so.SOCK_STREAM)
        srv.bind(str(path))
        srv.listen(1)
        got = {}

        def serve():
            c, _ = srv.accept()
            got["req"] = c.recv(16)
            c.sendall(struct.pack("<IBI", 9, 0, 1))
            c.close()
        t = threading.Thread(target=serve, daemon=True)
        t.start()
        self.assertEqual(ps2.pine_status(path), ps2.PINE_PAUSED)
        t.join(2)
        self.assertEqual(got["req"], struct.pack("<IB", 5, 0x0F))
        srv.close()
        self.assertIsNone(ps2.pine_status(d / "none.sock"))
        self.assertEqual(ps2.pine_socket_path({"XDG_RUNTIME_DIR": "/run/user/x"}), Path("/run/user/x/pcsx2.sock"))


# --- the hooks: a fresh interpreter per flag state, so module-level imports are what the service would do --------

PLUGIN_CODE = r'''
import json, os, sys, types, importlib.util, tempfile
from pathlib import Path
sys.path.insert(0, "companion")
spec = importlib.util.spec_from_file_location("g", "companion/plugins/games.py")
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from games import emulator_manager as em
out = {"ps2_imported": "ps2_session" in sys.modules, "em_ps2": em._ps2 is not None}
p = object.__new__(G.GamesPlugin)
G.GamesPlugin.__init__.__globals__  # (no __init__: the services stay off)
if G._ps2_session is not None:
    p.SYSTEMS = {**G.GamesPlugin.SYSTEMS, "ps2": {"name": "PlayStation 2", "folder": None, "extensions": set()}}
out["systems"] = sorted(p.SYSTEMS)
proj = Path(os.environ["B49_PROJ"])
p.PROJECT_ROOT = proj
p.GAMES_ROOT = proj / "games"
p._lock = __import__("threading").RLock(); p._cached_at = 0.0; p._cached_games = []
out["scan"] = sorted((g["system"], g["relative_path"]) for g in p._scan())
m = em.EmulatorManager(Path("."), config_path=Path("companion/games/config/emulators.json"))
try:
    out["catalog"] = list(m._controller_profile_catalog({"system": "ps2"}))
except Exception as exc:
    out["catalog"] = type(exc).__name__
print(json.dumps(out))
'''


def run_plugin(flag: str | None, proj: Path) -> dict:
    env = {"PATH": "/usr/bin:/bin", "B49_PROJ": str(proj)}
    if flag is not None:
        env["PRIVYHUB_PS2"] = flag
    r = subprocess.run([sys.executable, "-c", PLUGIN_CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class Hooks(unittest.TestCase):
    def setUp(self):
        self.games = tree({"one.chd": b"1", "one.iso": b"1", "two.iso": b"2"})
        self.proj = tree({"games/ps1/p.chd": b"x"})
        (self.proj / "runtime").mkdir()
        (self.proj / "runtime" / "h3_p1_paths.txt").write_text(f"GAMES_DIR={self.games}\n")

    def test_absent_is_today(self):
        out = run_plugin(None, self.proj)
        self.assertEqual(out["ps2_imported"], False)
        self.assertEqual(out["em_ps2"], False)
        self.assertNotIn("ps2", out["systems"])
        self.assertEqual([s for s, _ in out["scan"]], ["ps1"])
        self.assertEqual(out["catalog"], "EmulatorError")                 # today's refusal for an unknown system
        self.assertFalse((self.proj / "data" / "games" / "ps2").exists())
        self.assertEqual(run_plugin("0", self.proj), out)

    def test_with_the_flag_the_list_and_the_catalog(self):
        before = snapshot(self.games)
        out = run_plugin("1", self.proj)
        self.assertTrue(out["ps2_imported"] and out["em_ps2"])
        self.assertIn("ps2", out["systems"])
        self.assertEqual(out["scan"], [["ps1", "games/ps1/p.chd"], ["ps2", "ps2/one.chd"], ["ps2", "ps2/two.iso"]])
        self.assertEqual(out["catalog"], ["ps2", "", {}])
        self.assertEqual(before, snapshot(self.games))                     # the drive's folder never written
        self.assertFalse((self.proj / "data" / "games" / "ps2").exists())  # the list touches no hub file


LAUNCH_CODE = r"""
import json, os, sys, types, subprocess
from pathlib import Path
sys.path.insert(0, "companion")
from games import emulator_manager as em
proj = Path(os.environ["B49_PROJ"])
calls = {"popen": [], "kill": []}
class FakePopen:
    def __init__(self, cmd, **kw):
        calls["popen"].append({"cmd": cmd, "env_sdl": kw.get("env", {}).get("SDL_GAMECONTROLLERCONFIG", "")[:40],
                               "new_session": kw.get("start_new_session"), "cwd": kw.get("cwd")})
        self.pid = 999999999; self.returncode = None; self.stdin = None
    def poll(self): return self.returncode
    def wait(self, timeout=None): self.returncode = 0; return 0
em.subprocess.Popen = FakePopen
out = {"em_ps2": em._ps2 is not None}
if em._ps2 is not None:
    P = em._ps2
    class FakeSession(P.Session):
        def __init__(self, pid, log):
            clock = [0.0]
            def run(cmd, **kw):
                if "search" in cmd:
                    return types.SimpleNamespace(stdout="77\n")
                if cmd[:3] == ["pactl", "list", "sink-inputs"]:
                    calls.setdefault("pactl", 0)
                    calls["pactl"] += 1
                    return types.SimpleNamespace(stdout=f'application.process.id = "{pid}"\n')
                return types.SimpleNamespace(stdout="")
            super().__init__(pid, log, run=run, status=lambda: None, kill=lambda pid, sig: calls["kill"].append(int(sig)),
                             sleep=lambda d: clock.__setitem__(0, clock[0] + d), clock=lambda: clock[0],
                             pine_path=proj / "no-pine.sock")
    P.Session = FakeSession
    P.default_runner = lambda cmd: "deviceName = AMD Fake (RADV FAKE)\n"
m = em.EmulatorManager(proj, config_path=Path("companion/games/config/emulators.json").resolve())
game = {"id": "game_ps2_x", "system": "ps2", "title": "made-up", "relative_path": "ps2/one.chd"}
try:
    r = m.launch(game, players_chosen=int(os.environ["B49_PICK"]) if os.environ.get("B49_PICK") else None)
    out["launch"] = {k: r.get(k) for k in ("active", "launch_kind", "ps2_mode", "ps2_multitap")}
    out["kind"] = m._launch_kind
    out["pause"] = m.pause().get("ps2_pause"); out["paused"] = m._paused
    out["resume"] = m.resume().get("ps2_resume")
    try:
        m.save_state(1)
    except em.EmulatorError as exc:
        out["save_state"] = str(exc)
    out["stop"] = m.stop().get("ps2_exit"); out["kind_after"] = m._launch_kind
except em.EmulatorError as exc:
    out["error"] = type(exc).__name__
out["calls"] = calls
print(json.dumps(out))
"""


def run_launch(flag, proj, pick=None):
    env = {"PATH": "/usr/bin:/bin", "B49_PROJ": str(proj)}
    if flag is not None:
        env["PRIVYHUB_PS2"] = flag
    if pick is not None:
        env["B49_PICK"] = str(pick)
    r = subprocess.run([sys.executable, "-c", LAUNCH_CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class Launch(unittest.TestCase):
    def setUp(self):
        self.games = tree({"one.chd": b"1"})
        self.bios = tree({"image.bin": b"\0" * ps2.BIOS_IMAGE_BYTES, "image.nvm": b"n"})
        self.proj = tree({"runtime/emulators/pcsx2/pcsx2-fake.AppImage": b"x"})
        (self.proj / "runtime" / "h3_p1_paths.txt").write_text(f"BIOS_DIR={self.bios}\nGAMES_DIR={self.games}\n")
        self.ini = self.proj / "data/games/ps2/config/PCSX2/inis/PCSX2.ini"

    def test_absent_is_todays_refusal_and_nothing_written(self):
        out = run_launch(None, self.proj)
        self.assertEqual((out["em_ps2"], out.get("error"), out["calls"]["popen"]), (False, "EmulatorError", []))
        self.assertFalse((self.proj / "data" / "games" / "ps2").exists())

    def test_the_launch_the_ini_the_log_and_the_lifecycle(self):
        before_g, before_b = snapshot(self.games), snapshot(self.bios)
        out = run_launch("1", self.proj, pick=4)
        self.assertEqual(out["launch"], {"active": True, "launch_kind": "pcsx2", "ps2_mode": True, "ps2_multitap": True})
        cmd = out["calls"]["popen"][0]["cmd"]
        self.assertEqual(cmd[1:5], ["-datapath", str((self.proj / "data/games/ps2/config").resolve()), "-nogui",
                                    "-fullscreen"])
        self.assertEqual(cmd[5:], ["--", str((self.games / "one.chd").resolve())])
        self.assertTrue(out["calls"]["popen"][0]["new_session"])
        self.assertEqual(out["calls"]["popen"][0]["env_sdl"], ps2.SDL_MAPPING[:40])
        text = self.ini.read_text()
        self.assertEqual(ps2.ini_get(text, "Pad", "MultitapPort1"), "true")
        self.assertEqual(ps2.ini_get(text, "Pad5", "Cross"), "SDL-3/FaceSouth")
        self.assertEqual(ps2.ini_get(text, "EmuCore/GS", "Adapter"), "AMD Fake (RADV FAKE)")
        self.assertEqual(ps2.ini_get(text, "Filenames", "BIOS"), "image.bin")
        self.assertEqual(sorted(p.name for p in (self.proj / "data/games/ps2/bios").iterdir()), ["image.bin", "image.nvm"])
        self.assertEqual((out["pause"], out["paused"], out["resume"]), ("sigstop", True, "sigcont"))
        # B51 (disclosed): no refusal any more; with no PINE answer it is a real failure, in PS1's error shape
        self.assertEqual(out["save_state"], "PCSX2 did not acknowledge the save state")
        self.assertTrue(out["stop"].startswith("sigterm"))
        self.assertIsNone(out["kind_after"])
        self.assertEqual(out["calls"]["kill"], [int(signal.SIGSTOP), int(signal.SIGCONT), int(signal.SIGTERM)])
        log = next((self.proj / "logs/games").glob("*-ps2.log")).read_text()
        self.assertIn("PS2 launch: pcsx2 players=4 multitap=true adapter=named", log)
        for line in ("PS2 pause: sigstop", "PS2 resume: sigcont", "PS2 exit: sigterm", "PS2 audio: sink-input 0.0s",
                     "PS2 memcards: Mcd001.ps2=created Mcd002.ps2=created"):
            self.assertIn(line, log)
        self.assertNotIn("one.chd", log); self.assertNotIn("made-up", log); self.assertNotIn("game_ps2_x", log)
        self.assertEqual(before_g, snapshot(self.games)); self.assertEqual(before_b, snapshot(self.bios))

    def test_no_pick_is_two_ports_no_multitap(self):
        run_launch("1", self.proj)
        text = self.ini.read_text()
        self.assertEqual(ps2.ini_get(text, "Pad", "MultitapPort1"), "false")
        self.assertEqual(ps2.ini_get(text, "Pad2", "Cross"), "SDL-1/FaceSouth")
        self.assertEqual(ps2.ini_get(text, "Pad3", "Type"), "None")

    def test_unconfigured_folders_refuse(self):
        (self.proj / "runtime" / "h3_p1_paths.txt").unlink()
        out = run_launch("1", self.proj)
        self.assertEqual((out.get("error"), out["calls"]["popen"]), ("EmulatorError", []))


ROWS_CODE = r"""
import json, os, sys, types, importlib.util, tempfile
from pathlib import Path
sys.path.insert(0, "companion")
spec = importlib.util.spec_from_file_location("g", "companion/plugins/games.py")
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from games import link_drop_recovery as ldr
root = Path(tempfile.mkdtemp())
rec = ldr.LinkDropRecovery(root, pause_game=lambda: None, resume_game=lambda: None, save_recovery_state=lambda: {},
    restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True, end_session=lambda: None,
    client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})
class Emu:
    active_game = {"id": "g", "system": "ps2", "title": "t"}
    _launch_kind = os.environ.get("B49_KIND") or None
    _players_session = None
    def status(self): return {"active": True, "paused": True, "pid": 1}
    def ps1_multitap(self, g): return {"enabled": False}
p = object.__new__(G.GamesPlugin)
p.PROJECT_ROOT = root; p._emulator = Emu(); p._recovery = rec
p._native_stream = types.SimpleNamespace(start=lambda **kw: {"active": True}, _session_io=types.SimpleNamespace(controller=None))
p._diagnostic_heartbeat_interval_ms = lambda: 2000
p._adaptive_bitrate_session_ended = lambda: None
r = p.handle_post_request("native-stream-start", "port=48100", "127.0.0.1")
p.handle_post_request("native-stream-heartbeat", "sequence=1&interval_ms=2000&last_output_age_ms=16&rendered_frames=6&queued_frames=0&rx_packets=9&elapsed_ms=100", "127.0.0.1")
rows = [json.loads(x) for x in rec.log_path().read_text().splitlines()] if rec.log_path().exists() else []
hb = [json.loads(x) for x in (root / "logs/games/native_stream_heartbeat.log").read_text().splitlines()]
print(json.dumps({"start_ps2_mode": r.get("ps2_mode"), "ps2_rows": [x for x in rows if x["event"] == "ps2_session"],
                  "hb_ps2_mode": hb[-1].get("ps2_mode"), "hb_keys": sorted(hb[-1])}))
"""


def run_rows(flag, kind):
    env = {"PATH": "/usr/bin:/bin"}
    if flag:
        env["PRIVYHUB_PS2"] = flag
    if kind:
        env["B49_KIND"] = kind
    r = subprocess.run([sys.executable, "-c", ROWS_CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class Rows(unittest.TestCase):
    def test_a_ps2_session_says_so_on_the_start_and_every_heartbeat(self):
        out = run_rows("1", "pcsx2")
        self.assertTrue(out["start_ps2_mode"])
        self.assertEqual(len(out["ps2_rows"]), 1)
        # B51 (disclosed): SAVE / LOAD through PINE; the four automatic behaviours still off
        self.assertEqual((out["ps2_rows"][0]["savestates"], out["ps2_rows"][0]["off"]),
                         ("pine", list(ps2.OFF_BEHAVIOURS)))
        self.assertNotIn("save_states", out["ps2_rows"][0])
        self.assertTrue(out["hb_ps2_mode"])

    def test_a_retroarch_session_and_the_flag_absent_are_today(self):
        for flag, kind in (("1", None), (None, None), (None, "pcsx2")):
            out = run_rows(flag, kind)
            self.assertIsNone(out["start_ps2_mode"])
            self.assertEqual(out["ps2_rows"], [])
            self.assertNotIn("ps2_mode", out["hb_keys"])


class SaveStatesOff(unittest.TestCase):
    def test_the_hold_rewind_skips_with_a_row(self):
        import hold_rewind
        rows = []
        rw = object.__new__(hold_rewind.Rewinder)
        rw._lock = __import__("threading").Lock()
        rw.cap = 30
        rw.b9 = None
        rw.emulator = types.SimpleNamespace(_launch_kind="pcsx2", _network_cmd_port=None)
        rw.counter_before = lambda pending: 50
        rw._row = lambda recovery, event, fields, **extra: rows.append((event, {**fields, **extra})) or rows[-1]
        recovery = types.SimpleNamespace(_state_since=7)
        rw._pending = {"key": 7, "onset": 1.0, "paused_at": 2.0}
        rw.rewind(recovery, "input_release")
        self.assertEqual(rows[0][0], "rewind_skipped")
        self.assertEqual((rows[0][1]["reason"], rows[0][1]["ps2_mode"]), ("ps2_mode: no save states", True))

    def test_the_slot9_save_is_not_sent(self):
        import rewind_cores
        c = object.__new__(rewind_cores.Cores)
        c.emulator = types.SimpleNamespace(_launch_kind="pcsx2", _paused=False, _network_cmd_port=55355)
        c.nci_factory = lambda port: (_ for _ in ()).throw(AssertionError("no command may be sent"))
        c.save(0.0, 0.4)
        self.assertEqual(c.saves_skipped_ps2, 1)

    def test_the_recovery_save_and_the_slots(self):
        from games import emulator_manager as em
        m = object.__new__(em.EmulatorManager)
        m._launch_kind = "pcsx2"
        self.assertEqual(m.save_recovery_state(), {"skipped": "ps2_mode", "ps2_mode": True, "state_file": None})
        # B51 (disclosed): the SAVE / LOAD buttons go through PINE now (test_b51); the recovery paths stay refused
        for call in (m.load_recovery_state, m.load_recovery_state_running, lambda: m.copy_recovery_state_to_slot(1)):
            with self.assertRaises(em.EmulatorError):
                call()

    def test_the_give_up_row(self):
        from games import link_drop_recovery as ldr
        root = Path(tempfile.mkdtemp())
        rec = ldr.LinkDropRecovery(root, pause_game=lambda: None, resume_game=lambda: None,
                                   save_recovery_state=lambda: {"skipped": "ps2_mode", "ps2_mode": True, "state_file": None},
                                   restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
                                   end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
                                   recovery_save_detail=lambda: {})
        rec._give_up_and_save()
        rows = [json.loads(x) for x in rec.log_path().read_text().splitlines()]
        row = [r for r in rows if r["event"] == "gave_up_saved"][0]
        self.assertEqual((row["ps2_mode"], row["save_skipped"], row["state_file"]), (True, True, None))
        rec2 = ldr.LinkDropRecovery(Path(tempfile.mkdtemp()), pause_game=lambda: None, resume_game=lambda: None,
                                    save_recovery_state=lambda: {"state_file": "x"}, restart_encoder=lambda: {},
                                    full_start_encoder=lambda: {}, stream_active=lambda: True, end_session=lambda: None,
                                    client_packet_age_ms=lambda: 10.0, recovery_save_detail=lambda: {})
        rec2._give_up_and_save()
        row2 = [json.loads(x) for x in rec2.log_path().read_text().splitlines() if '"gave_up_saved"' in x][0]
        self.assertNotIn("ps2_mode", row2)                                  # RetroArch: today's row


class P2Metric(unittest.TestCase):
    @staticmethod
    def log(seconds):
        """seconds: list of per-second frame lists (checksum, y); 60 frames each at 1/60 s."""
        lines, n = [], 0
        for s, frames in enumerate(seconds):
            for i, (ck, y) in enumerate(frames):
                t = s + i / 60.0
                lines.append(f"[x] n:{n} pts:{n} pts_time:{t:.6f} duration:1 fmt:yuv420p s:64x48 checksum:{ck} "
                             f"plane_checksum:[{ck}] mean:[{y} 128 128] stdev:[1]")
                n += 1
        return "\n".join(lines)

    def test_black_seconds_excluded_single_repeats_corrected_a_drop_kept(self):
        play = lambda s: [(f"{s:02X}{i:06X}", 90) for i in range(60)]
        beat = lambda s: [(f"{s:02X}{(i if i != 30 else 29):06X}", 90) for i in range(60)]   # one single repeat
        black = [("00000000", 16)] * 60
        drop = lambda s: [(f"{s:02X}{(i // 2) * 2:06X}", 90) for i in range(60)]           # 30 unique: a real drop
        seconds = [play(0), beat(1), black, black, play(4), play(5), play(6)]
        r = p2.analyze(p2.parse(self.log(seconds)))
        self.assertEqual(r["excluded_static_or_black_seconds"], 2)
        self.assertEqual(r["raw_min_fps"], 0)                              # the second black second repeats all
        self.assertEqual(r["corrected_min_fps"], 60)                       # the beat's repeat counted
        self.assertEqual(r["single_repeats"], 1)
        self.assertTrue(r["pass"])
        r2 = p2.analyze(p2.parse(self.log([play(0), drop(1), play(2), play(3)])))
        self.assertEqual(r2["corrected_min_fps"], 31)                      # a real drop: only one repeat forgiven
        self.assertFalse(r2["pass"])

    def test_packed_rgb_refuses(self):
        with self.assertRaises(ValueError):
            p2.parse("pts_time:0 fmt:bgr0 checksum:AA mean:[64]")


if __name__ == "__main__":
    unittest.main()
