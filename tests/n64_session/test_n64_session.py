#!/usr/bin/env python3
"""B59 (host): N64 through RetroArch behind PRIVYHUB_N64=1 -- the in-place list, the plugin's system, the launch (the
command, four ports, the core options, the input file, the log, the ports echo), the core's presence check, the frame
metric, the keeper's label -- and absent = today. Fakes only: temp folders with made-up names, a fake RetroArch tree
and core files of a few bytes; RetroArch is never started and nothing is fetched.

    python3 -m unittest discover -s tests/n64_session -v
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401  (this run's temp dirs removed at exit)
sys.path.insert(0, str(ROOT / "tools"))

import inplace_library  # noqa: E402
import n64_session as n64  # noqa: E402
import players_session  # noqa: E402
import n64_frames  # noqa: E402
import n64_core_check  # noqa: E402

RA_EXE = "runtime/emulators/retroarch-nightly-20260907-linux/RetroArch-Linux-x86_64/RetroArch-Linux-x86_64.AppImage"
CORES = "runtime/emulators/retroarch/cores-linux"


def tree(files: dict[str, bytes | str]) -> Path:
    root = Path(tempfile.mkdtemp(prefix="b59_"))
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
    return root


def snapshot(root: Path) -> list[tuple[str, int, float]]:
    return sorted((str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime) for p in root.rglob("*"))


# --- the list --------------------------------------------------------------------------------------------------

class Listing(unittest.TestCase):
    def test_one_per_stem_z64_first_and_nothing_written(self):
        d = tree({"one.v64": b"1", "one.z64": b"1", "one.n64": b"1", "two.n64": b"2", "two.v64": b"2",
                  "three.V64": b"3", ".hidden.z64": b"h", "notes.txt": b"t", "four.zip": b"z",
                  "sub/five.n64": b"5", ".dot/six.z64": b"6"})
        before = snapshot(d)
        got = [(t["relative"], t["suffix"]) for t in n64.list_titles(d)]
        self.assertEqual(got, [("one.z64", ".z64"), ("sub/five.n64", ".n64"), ("three.V64", ".v64"),
                               ("two.v64", ".v64")])
        self.assertEqual(before, snapshot(d))

    def test_no_folder_is_an_empty_list(self):
        self.assertEqual(n64.list_titles(None), [])
        absent = Path(tempfile.mkdtemp()) / "absent"
        self.assertEqual(n64.list_titles(absent), [])
        self.assertFalse(absent.exists())                                       # never made (no mkdir on the drive)

    def test_the_paths_file_key_only(self):
        proj = tree({"runtime/h3_p1_paths.txt": "GAMES_DIR=/x/ps2\nN64_DIR=/y/n64\nT1=secret\n"})
        self.assertEqual(n64.read_dir(proj, {}), Path("/y/n64"))
        self.assertIsNone(inplace_library.read_dir(proj, "GAMECUBE_DIR", {}))
        other = tree({"p.txt": "N64_DIR=/z\n"})
        self.assertEqual(n64.read_dir(proj, {"PRIVYHUB_PS2_PATHS": str(other / "p.txt")}), Path("/z"))
        self.assertIsNone(n64.read_dir(tree({}), {}))

    def test_resolve_refuses_escapes_prefixes_and_missing(self):
        d = tree({"one.z64": b"1"})
        outside = tree({"x.z64": b"x"})
        self.assertEqual(n64.resolve_title(d, "n64/one.z64"), (d / "one.z64").resolve())
        for bad in ("n64/../" + os.path.relpath(outside / "x.z64", d), "ps2/one.z64", "n64/none.z64", "one.z64"):
            with self.assertRaises(n64.N64Error):
                n64.resolve_title(d, bad)
        with self.assertRaises(n64.N64Error):
            n64.resolve_title(None, "n64/one.z64")


# --- the pieces ------------------------------------------------------------------------------------------------

class Pieces(unittest.TestCase):
    def test_four_ports_always_no_multitap(self):
        p = n64.plan()
        self.assertEqual(p["device_args"], ["--device=1:1", "--device=2:1", "--device=3:1", "--device=4:1"])
        self.assertEqual((p["ports"], p["multitap"], p["multitap_available"], p["source"]), (4, False, False, "n64"))

    def test_the_ports_echo_reads_the_plan(self):
        class Emu:
            _players_session = n64.plan()
            active_game = {"system": "n64"}
        got = players_session.ports_set(Emu(), None)["ports_set"]
        self.assertEqual(got, {"players_chosen": 4, "ports": 4, "multitap": False, "multitap_available": False,
                               "source": "n64", "players": 4})

    def test_the_options_merge(self):
        text = '# keep\nmupen64plus-cpucore = "pure_interpreter"\nother-core-key = "x"\nmupen64plus-cpucore = "dup"\n'
        out = n64.merge_options(text, n64.OPTIONS)
        self.assertIn("# keep\n", out)
        self.assertIn('other-core-key = "x"\n', out)
        self.assertEqual(out.count("mupen64plus-cpucore"), 1)
        for k, v in n64.OPTIONS.items():
            self.assertIn(f'{k} = "{v}"\n', out)
        self.assertEqual(n64.merge_options(out, n64.OPTIONS), out)               # idempotent

    def test_the_option_values(self):
        self.assertEqual(n64.OPTIONS["mupen64plus-rdp-plugin"], "gliden64")
        self.assertEqual(n64.OPTIONS["mupen64plus-EnableNativeResFactor"], "1")
        self.assertEqual(n64.OPTIONS["mupen64plus-alt-map"], "False")              # the C-buttons on the right stick
        self.assertEqual([n64.OPTIONS[f"mupen64plus-pak{i}"] for i in range(1, 5)], ["memory"] * 4)

    def test_options_only_for_mupen64plus_next(self):
        cfg = Path(tempfile.mkdtemp())
        self.assertEqual(n64.write_options(cfg, "parallel_n64_libretro.so"), {"library": None, "keys": 0,
                                                                              "written": False})
        self.assertEqual(list(cfg.iterdir()), [])

    def test_core_names(self):
        self.assertEqual(n64.core_file({}), "mupen64plus_next_libretro.so")
        self.assertEqual(n64.core_file({"PRIVYHUB_N64_CORE": "parallel_n64"}), "parallel_n64_libretro.so")
        for bad in ("../x", "Mupen", "a b"):
            with self.assertRaises(n64.N64Error):
                n64.core_file({"PRIVYHUB_N64_CORE": bad})

    def test_the_profile_is_injected_into_a_copy(self):
        rt = {"config": {"systems": {"snes": {"core": "x"}}}, "core_status": {"snes": {}}}
        out = n64.runtime_with_profile(rt)
        self.assertIn("n64", out["config"]["systems"])
        self.assertEqual(out["config"]["systems"]["n64"]["controls"], {"analog_dpad": "none"})
        self.assertNotIn("n64", rt["config"]["systems"])
        self.assertNotIn("n64", out["core_status"])


# --- the presence check ----------------------------------------------------------------------------------------

def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


class Presence(unittest.TestCase):
    def setUp(self):
        self._connect = socket.socket.connect

        def refuse(*a, **k):
            raise AssertionError("the presence check opened a connection")
        socket.socket.connect = refuse

    def tearDown(self):
        socket.socket.connect = self._connect

    def test_fetch_needed_then_bundled(self):
        proj = tree({f"{CORES}/bsnes_libretro.so": b"x"})
        self.assertEqual(n64.presence(proj, {})["state"], "fetch needed")
        self.assertEqual(quiet(n64_core_check.main, ["--root", str(proj)]), 3)
        (proj / CORES / "mupen64plus_next_libretro.so").write_bytes(b"\0" + b"\0".join(k.encode() for k in n64.OPTIONS))
        self.assertEqual(n64.presence(proj, {})["state"], "bundled")
        self.assertEqual(quiet(n64_core_check.main, ["--root", str(proj), "--keys"]), 0)

    def test_keys_found_and_missing(self):
        some = list(n64.OPTIONS)[:3]
        core = tree({"c.so": b"\x7fELF" + b"\0".join(k.encode() for k in some)}) / "c.so"
        got = n64.keys_in_core(core)
        self.assertEqual(got["found"], some)
        self.assertEqual(len(got["missing"]), len(n64.OPTIONS) - 3)
        proj = tree({f"{CORES}/mupen64plus_next_libretro.so": core.read_bytes()})
        self.assertEqual(quiet(n64_core_check.main, ["--root", str(proj), "--keys"]), 4)


# --- the plugin and the catalog, a fresh interpreter per flag state -------------------------------------------

PLUGIN_CODE = r'''
import json, os, sys, threading, importlib.util
from pathlib import Path
sys.path.insert(0, "companion")
spec = importlib.util.spec_from_file_location("g", "companion/plugins/games.py")
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from games import emulator_manager as em
out = {"n64_imported": "n64_session" in sys.modules, "inplace_imported": "inplace_library" in sys.modules,
       "em_n64": em._n64 is not None}
p = object.__new__(G.GamesPlugin)
if G._n64_session is not None:
    p.SYSTEMS = {**G.GamesPlugin.SYSTEMS, "n64": {"name": "Nintendo 64", "folder": None, "extensions": set()}}
out["systems"] = sorted(p.SYSTEMS)
proj = Path(os.environ["B59_PROJ"])
p.PROJECT_ROOT = proj; p.GAMES_ROOT = proj / "games"
p._lock = threading.RLock(); p._cached_at = 0.0; p._cached_games = []
out["scan"] = sorted((g["system"], g["relative_path"], g["format"]) for g in p._scan())
out["ids"] = sorted(g["id"].split("_")[1] for g in p._scan())
m = em.EmulatorManager(Path("."), config_path=Path("companion/games/config/emulators.json"))
try:
    out["catalog"] = list(m._controller_profile_catalog({"system": "n64"}))
except Exception as exc:
    out["catalog"] = type(exc).__name__
print(json.dumps(out))
'''


def run_plugin(flag, proj):
    env = {"PATH": "/usr/bin:/bin", "B59_PROJ": str(proj)}
    if flag is not None:
        env["PRIVYHUB_N64"] = flag
    r = subprocess.run([sys.executable, "-c", PLUGIN_CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class Plugin(unittest.TestCase):
    def setUp(self):
        self.drive = tree({"one.z64": b"1", "one.v64": b"1", "two.v64": b"2"})
        self.proj = tree({"games/snes/s.sfc": b"x"})
        (self.proj / "runtime").mkdir()
        (self.proj / "runtime/h3_p1_paths.txt").write_text(f"N64_DIR={self.drive}\n")

    def test_absent_is_today(self):
        out = run_plugin(None, self.proj)
        self.assertEqual((out["n64_imported"], out["inplace_imported"], out["em_n64"]), (False, False, False))
        self.assertNotIn("n64", out["systems"])
        self.assertEqual([s for s, _, _ in out["scan"]], ["snes"])
        self.assertEqual(out["catalog"], "EmulatorError")
        self.assertEqual(run_plugin("0", self.proj), out)
        self.assertEqual(run_plugin("yes", self.proj), out)

    def test_with_the_flag_listed_in_place(self):
        before = snapshot(self.drive)
        out = run_plugin("1", self.proj)
        self.assertTrue(out["n64_imported"] and out["em_n64"])
        self.assertIn("n64", out["systems"])
        self.assertEqual(out["scan"], [["n64", "n64/one.z64", "z64"], ["n64", "n64/two.v64", "v64"],
                                       ["snes", "games/snes/s.sfc", "sfc"]])
        self.assertEqual(out["ids"], ["n64", "n64", "snes"])
        self.assertEqual(out["catalog"], ["n64", "", {}])
        self.assertEqual(before, snapshot(self.drive))
        self.assertFalse((self.proj / "games" / "n64").exists())


# --- the launch: a fake RetroArch tree, a fake Popen, a fresh interpreter -------------------------------------

LAUNCH_CODE = r"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, "companion")
from games import emulator_manager as em
import players_session as ps
proj = Path(os.environ["B59_PROJ"])
calls = []
class FakePopen:
    def __init__(self, cmd, **kw):
        calls.append(list(cmd)); self.pid = 999999999; self.returncode = None; self.stdin = None
    def poll(self): return self.returncode
    def wait(self, timeout=None): self.returncode = 0; return 0
em.subprocess.Popen = FakePopen
em.time.sleep = lambda s: None
em.EmulatorManager._wait_for_retroarch_command_ready = lambda self, *a, **k: {"fake": True}
m = em.EmulatorManager(proj, config_path=Path("companion/games/config/emulators.json").resolve())
game = json.loads(os.environ["B59_GAME"])
joined = os.environ.get("B59_JOINED")
kw = {"players_chosen": ps.ports_for_joined(int(joined))} if joined else {}
out = {"em_n64": em._n64 is not None}
try:
    r = m.launch(game, **kw)
    out["n64_session"] = r.get("n64_session")
    out["n64_core"] = getattr(m, "_n64_core", None)      # B61
    out["ports_set"] = ps.ports_set(m, None)["ports_set"]
except em.EmulatorError as exc:
    out["error"] = str(exc)
out["calls"] = calls
cfg = proj / "data/games/retroarch/config"
for name in ("privyhub-input.cfg", "privyhub-session.cfg"):
    p = cfg / name
    out[name] = p.read_text() if p.is_file() else None
opt = Path(os.environ["XDG_CONFIG_HOME"]) / "retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt"
out["opt"] = opt.read_text() if opt.is_file() else None
rmp = Path(os.environ["XDG_CONFIG_HOME"]) / "retroarch/config/remaps/Mupen64Plus-Next/Mupen64Plus-Next.rmp"
out["rmp"] = rmp.read_text() if rmp.is_file() else None                       # B62
try:
    out["label"] = m.controller_profile(game)["label"]                        # B62
except em.EmulatorError as exc:
    out["label"] = "EmulatorError"
logs = sorted((proj / "logs/games").glob("*.log")) if (proj / "logs/games").is_dir() else []
out["log"] = logs[-1].read_text() if logs else ""
print(json.dumps(out))
"""


def fake_project(drive: Path, cores=("mupen64plus_next_libretro.so", "bsnes_libretro.so", "snes9x_libretro.so")) -> Path:
    files = {RA_EXE: b"#!/bin/false\n", "games/snes/made-up.sfc": b"s",
             "data/games/retroarch/retroarch.cfg": 'config_save_on_exit = "false"\n'
                                                   'joypad_autoconfig_dir = "data/games/retroarch/autoconfig"\n',
             "data/games/retroarch/autoconfig/udev/x.cfg": 'input_device = "x"\n',
             "runtime/h3_p1_paths.txt": f"N64_DIR={drive}\n"}
    files.update({f"{CORES}/{c}": b"\x7fELF" for c in cores})
    return tree(files)


def run_launch(flag, proj, game, joined=None, xdg=None, extra=None):
    xdg = xdg or Path(tempfile.mkdtemp(prefix="b59_xdg_"))
    env = {"PATH": "/usr/bin:/bin", "B59_PROJ": str(proj), "B59_GAME": json.dumps(game), "XDG_CONFIG_HOME": str(xdg),
           "HOME": str(xdg)}
    if flag is not None:
        env["PRIVYHUB_N64"] = flag
    if joined is not None:
        env["B59_JOINED"] = str(joined)
    env.update(extra or {})
    r = subprocess.run([sys.executable, "-c", LAUNCH_CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-2500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


N64_GAME = {"id": "game_n64_0123456789abcdef", "system": "n64", "title": "made-up", "relative_path": "n64/one.z64"}
SNES_GAME = {"id": "game_snes_0123456789abcdef", "system": "snes", "title": "made-up",
             "relative_path": "games/snes/made-up.sfc"}
PORT = re.compile(r'network_cmd_port = "\d+"')


class Launch(unittest.TestCase):
    def setUp(self):
        self.drive = tree({"one.z64": b"N64"})
        self.proj = fake_project(self.drive)

    def test_absent_is_todays_refusal_nothing_written(self):
        for flag in (None, "0"):
            out = run_launch(flag, self.proj, N64_GAME)
            self.assertFalse(out["em_n64"])
            self.assertEqual(out["calls"], [])
            self.assertIn("No emulator profile configured for system: n64", out["error"])
            self.assertIsNone(out["opt"])

    def test_the_command_the_options_the_input_file_and_the_log(self):
        before = snapshot(self.drive)
        out = run_launch("1", self.proj, N64_GAME)
        cmd = out["calls"][0]
        self.assertEqual(cmd[1:3], ["--config", str((self.proj / "data/games/retroarch/config/privyhub-session.cfg")
                                                     .resolve())])
        self.assertEqual([a for a in cmd if a.startswith("--device=")],
                         ["--device=1:1", "--device=2:1", "--device=3:1", "--device=4:1"])
        self.assertEqual(cmd[-4:], ["--verbose", "-L", str((self.proj / CORES / "mupen64plus_next_libretro.so").resolve()),
                                    str((self.drive / "one.z64").resolve())])
        for k, v in n64.OPTIONS.items():
            self.assertIn(f'{k} = "{v}"\n', out["opt"])
        inp = out["privyhub-input.cfg"]
        for i in range(1, 5):
            self.assertIn(f'input_player{i}_analog_dpad_mode = "0"', inp)
        self.assertNotRegex(inp, r"_(btn|axis) =")                                 # no remap binds
        self.assertIn("N64 launch: core=mupen64plus_next ports=4\n", out["log"])
        self.assertIn(f"N64 core options: {len(n64.OPTIONS)} keys (Mupen64Plus-Next)\n", out["log"])
        self.assertEqual(out["n64_session"], {"core": "mupen64plus_next_libretro.so", "ports": 4,
                                              "options_keys": len(n64.OPTIONS),
                                              "layout": "face_c", "remap_binds": 8})       # B62's two keys
        self.assertEqual(out["n64_core"], "mupen64plus_next_libretro.so")            # B61: the session is N64
        self.assertEqual({k: out["ports_set"][k] for k in ("players", "multitap", "multitap_available")},
                         {"players": 4, "multitap": False, "multitap_available": False})
        self.assertEqual(before, snapshot(self.drive))

    def test_four_ports_for_every_join_count(self):
        for joined in (1, 2, 3, 4):
            out = run_launch("1", self.proj, N64_GAME, joined=joined)
            self.assertEqual([a for a in out["calls"][0] if a.startswith("--device=")],
                             [f"--device={p}:1" for p in range(1, 5)], joined)
            self.assertEqual(out["ports_set"]["players"], 4)

    def test_the_options_merge_keeps_a_foreign_key(self):
        xdg = Path(tempfile.mkdtemp(prefix="b59_xdg_"))
        opt = xdg / "retroarch/config/Mupen64Plus-Next/Mupen64Plus-Next.opt"
        opt.parent.mkdir(parents=True)
        opt.write_text('mupen64plus-other = "kept"\nmupen64plus-rdp-plugin = "angrylion"\n')
        out = run_launch("1", self.proj, N64_GAME, xdg=xdg)
        self.assertIn('mupen64plus-other = "kept"\n', out["opt"])
        self.assertIn('mupen64plus-rdp-plugin = "gliden64"\n', out["opt"])
        self.assertNotIn("angrylion", out["opt"])

    def test_another_core_by_name_no_options(self):
        proj = fake_project(self.drive, cores=("parallel_n64_libretro.so",))
        out = run_launch("1", proj, N64_GAME, extra={"PRIVYHUB_N64_CORE": "parallel_n64"})
        self.assertTrue(out["calls"][0][-2].endswith("/parallel_n64_libretro.so"))
        self.assertIsNone(out["opt"])
        self.assertIn("N64 core options: none (parallel_n64)\n", out["log"])

    def test_a_missing_core_or_folder_refuses(self):
        proj = fake_project(self.drive, cores=("bsnes_libretro.so",))
        out = run_launch("1", proj, N64_GAME)
        self.assertEqual(out["calls"], [])
        self.assertIn("N64 core not installed (fetch needed)", out["error"])
        out = run_launch("1", self.proj, N64_GAME, extra={"PRIVYHUB_N64_CORE": "../x"})
        self.assertEqual(out["calls"], [])
        self.assertIn("N64 launch refused: PRIVYHUB_N64_CORE is not a core name", out["error"])
        (self.proj / "runtime/h3_p1_paths.txt").write_text("")
        out = run_launch("1", self.proj, N64_GAME)
        self.assertEqual(out["calls"], [])
        self.assertIn("N64 folder is not configured", out["error"])

    def test_another_systems_launch_is_byte_for_byte_with_the_flag(self):
        runs = []
        for flag in (None, "1"):
            out = run_launch(flag, self.proj, SNES_GAME, joined=2)
            runs.append((out["calls"], PORT.sub("P", out["privyhub-input.cfg"]),
                         PORT.sub("P", out["privyhub-session.cfg"]), out["opt"], "N64" in out["log"],
                         out["n64_session"], out["ports_set"]))
        self.assertEqual(runs[0], runs[1])
        self.assertIsNone(runs[1][3])
        self.assertIsNone(run_launch("1", self.proj, SNES_GAME)["n64_core"])          # B61: not an N64 session
        self.assertFalse(runs[1][4])


# --- the metric -------------------------------------------------------------------------------------------------

def frames(per_second: list[int], fps: int = 60, y: float = 100.0) -> list[tuple[float, str, float]]:
    """`per_second[i]` distinct pictures in second i, each held for an equal run of the 60 captured frames."""
    out = []
    for s, distinct in enumerate(per_second):
        for f in range(fps):
            idx = f * distinct // fps
            out.append((s + f / fps, f"C{s}_{idx}", y))
    return out + [(len(per_second) + 0.0, "END", y)]


class Metric(unittest.TestCase):
    def test_a_thirty_fps_title_is_not_a_hitch(self):
        r = n64_frames.analyze(frames([30] * 20))
        self.assertEqual((r["internal_fps"], r["hitch_seconds"], r["median_distinct_fps"]), (30, 0, 30))

    def test_a_drop_below_five_sixths_is_a_hitch(self):
        r = n64_frames.analyze(frames([30] * 18 + [20, 26]))
        self.assertEqual(r["internal_fps"], 30)
        self.assertEqual(r["hitch_at_s"], [18])                                  # 20 < 25; 26 is not
        self.assertEqual(r["hitch_per_10min"], round(1 / (20 / 60) * 10, 2))

    def test_twenty_and_sixty_and_the_beat(self):
        self.assertEqual(n64_frames.analyze(frames([20] * 10 + [16]))["hitch_seconds"], 1)
        f = frames([60] * 10)
        f[30] = (f[30][0], f[29][1], f[30][2])                                   # one isolated repeat (the beat)
        r = n64_frames.analyze(f)
        self.assertEqual((r["internal_fps"], r["hitch_seconds"], r["min_distinct_fps"]), (60, 0, 60))

    def test_black_seconds_excluded_and_the_given_rate(self):
        f = [x if not 5 <= x[0] < 7 else (x[0], x[1], 10.0) for x in frames([30] * 10)]
        r = n64_frames.analyze(f)
        self.assertEqual((r["excluded_static_or_black_seconds"], r["kept_seconds"]), (2, 8))
        self.assertEqual(n64_frames.analyze(frames([30] * 10), internal_fps=60)["hitch_seconds"], 10)

    def test_the_cli_refuses_packed_rgb(self):
        p = Path(tempfile.mkdtemp()) / "s.txt"
        p.write_text("n:0 pts_time:0 fmt:bgr0 checksum:AA mean:[10]\n")
        with self.assertRaises(ValueError):
            quiet(n64_frames.main, [str(p)])


# --- the keeper's label -----------------------------------------------------------------------------------------

class Keeper(unittest.TestCase):
    def test_an_n64_log_reads_its_core(self):
        import diag_read
        m = diag_read.GAME_LOG.match("20261108-210000-game_n64_0123456789abcdef.log")
        self.assertIsNotNone(m)
        self.assertEqual(diag_read.CORES.get(m.group(3)), "mupen64plus-next")
        self.assertEqual(diag_read.CORES["ps1"], "beetle-psx-hw")


if __name__ == "__main__":
    unittest.main()
