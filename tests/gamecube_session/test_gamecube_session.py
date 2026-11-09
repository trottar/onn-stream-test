#!/usr/bin/env python3
"""B69 (host): the GameCube launch kind (Dolphin) behind PRIVYHUB_GAMECUBE=1 -- the in-place list, the config written
whole, GCPadNew.ini for the four virtual pads, the pause by the F10 hotkey confirmed by the CPU thread's clock (SIGSTOP
on a silent one), SAVE / LOAD through the state hotkeys (the file check, B52's picture check), the hold / stall /
give-up through the reserved slots, four ports with no relaunch, the exit and its helper wait, the rows and logs, the
keeper / diag_read label, the per-segment metric -- and absent = today. Fakes only (fake_dolphin.py): no Dolphin, no
display, no title; the real folder never used.

    python3 -m unittest discover -s tests/gamecube_session -v
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "companion"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _tmp_cleanup  # noqa: E402,F401  (this run's temp dirs removed at exit)
sys.path.insert(0, str(ROOT / "tools"))

import gamecube_session as gc  # noqa: E402
import players_session  # noqa: E402
import relaunch_ports  # noqa: E402
import rewind_cores  # noqa: E402
from games import emulator_manager as em  # noqa: E402
from fake_dolphin import FAKE_ID, FakeDolphin  # noqa: E402

MIB = 1 << 20


def tree(files: dict[str, bytes | str | int]) -> Path:
    """A temp tree; an int value is a sparse file of that size."""
    root = Path(tempfile.mkdtemp(prefix="b69_"))
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, int):
            with open(p, "wb") as fh:
                fh.truncate(data)
        else:
            p.write_bytes(data if isinstance(data, bytes) else data.encode())
    return root


def snapshot(root: Path) -> list[tuple[str, int, float]]:
    return sorted((str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime) for p in root.rglob("*"))


def ini(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    cur = None
    for line in text.splitlines():
        if line.startswith("[") and line.endswith("]"):
            cur = out.setdefault(line[1:-1], {})
        elif cur is not None and " = " in line:
            k, _, v = line.partition(" = ")
            cur[k] = v
    return out


# --- the list ------------------------------------------------------------------------------------------------------

class Listing(unittest.TestCase):
    def test_the_rules_and_nothing_written(self):
        d = tree({"one.iso": MIB, "one.rvz": MIB, "one.gcm": MIB, "two.ciso": MIB, "two.iso": MIB,
                  "three.GCM": 2 * MIB, ".hidden.rvz": MIB, "sub/four.rvz": MIB, ".dot/five.rvz": MIB,
                  "notes.txt": "t", "region/small.bin": 2048, "stub.rvz": 4096, "six.zip": MIB})
        before = snapshot(d)
        got = [(t["relative"], t["suffix"]) for t in gc.list_titles(d)]
        self.assertEqual(got, [("one.rvz", ".rvz"), ("sub/four.rvz", ".rvz"), ("three.GCM", ".gcm"),
                               ("two.iso", ".iso")])
        self.assertEqual(before, snapshot(d))                                   # read-only

    def test_no_folder_is_an_empty_list_and_never_made(self):
        self.assertEqual(gc.list_titles(None), [])
        absent = Path(tempfile.mkdtemp()) / "absent"
        self.assertEqual(gc.list_titles(absent), [])
        self.assertFalse(absent.exists())

    def test_the_paths_file_key_only(self):
        proj = tree({"runtime/h3_p1_paths.txt": "GAMES_DIR=/x/ps2\nN64_DIR=/y\nGAMECUBE_DIR=/z/gc\nT1=secret\n"})
        self.assertEqual(gc.read_dir(proj, {}), Path("/z/gc"))
        self.assertIsNone(gc.read_dir(tree({}), {}))

    def test_resolve_refuses_escapes_prefixes_and_missing(self):
        d = tree({"one.rvz": MIB})
        outside = tree({"x.rvz": MIB})
        self.assertEqual(gc.resolve_title(d, "gamecube/one.rvz"), (d / "one.rvz").resolve())
        for bad in ("gamecube/../" + os.path.relpath(outside / "x.rvz", d), "n64/one.rvz", "gamecube/none.rvz",
                    "one.rvz"):
            with self.assertRaises(gc.GCError):
                gc.resolve_title(d, bad)
        with self.assertRaises(gc.GCError):
            gc.resolve_title(None, "gamecube/one.rvz")

    def test_the_plugin_entries(self):
        d = tree({"one.rvz": MIB})
        e = gc.titles_for_plugin(d, lambda s, r: f"id:{s}:{r}", lambda p: p.stem)
        self.assertEqual(e, [{"id": "id:gamecube:gamecube/one.rvz", "title": "one", "system": "gamecube",
                              "system_name": "GameCube", "relative_path": "gamecube/one.rvz", "format": "rvz",
                              "size_bytes": MIB}])

    def test_one_appimage(self):
        proj = tree({"runtime/emulators/dolphin/dolphin-x.AppImage": "x"})
        self.assertEqual(gc.find_appimage(proj).name, "dolphin-x.AppImage")
        (proj / "runtime/emulators/dolphin/other.AppImage").write_text("y")
        with self.assertRaises(gc.GCError):
            gc.find_appimage(proj)


# --- the config ----------------------------------------------------------------------------------------------------

class Config(unittest.TestCase):
    def test_the_command(self):
        u = Path(tempfile.mkdtemp())
        self.assertEqual(gc.command(Path("/r/d.AppImage"), u, Path("/g/t.rvz")),
                         ["/r/d.AppImage", "-b", "-u", str(u.resolve()), "-e", "/g/t.rvz"])

    def test_five_files_written_whole(self):
        u = Path(tempfile.mkdtemp())
        (u / "Config").mkdir()
        (u / "Config" / "Dolphin.ini").write_text("[Core]\nCPUThread = False\nStale = yes\n[Old]\nX = 1\n")
        (u / "Config" / "Hotkeys.ini").write_text("[Hotkeys]\nGeneral/Stop = Escape\n")
        self.assertEqual(sorted(gc.write_config(u)), ["Dolphin.ini", "GCPadNew.ini", "GFX.ini", "Hotkeys.ini",
                                                      "Logger.ini"])
        d = ini((u / "Config" / "Dolphin.ini").read_text())
        self.assertNotIn("Old", d)
        self.assertNotIn("Stale", d["Core"])                                     # nothing carried over
        self.assertEqual({k: d["Core"][k] for k in ("CPUThread", "SkipIPL", "GFXBackend", "SlotA")},
                         {"CPUThread": "True", "SkipIPL": "True", "GFXBackend": "Vulkan", "SlotA": "8"})
        self.assertEqual([d["Core"][f"SIDevice{i}"] for i in range(4)], ["6"] * 4)
        self.assertEqual((d["Display"]["RenderToMain"], d["Display"]["Fullscreen"]), ("True", "True"))
        self.assertEqual((d["Interface"]["ConfirmStop"], d["Interface"]["UsePanicHandlers"],
                          d["Interface"]["OnScreenDisplayMessages"]), ("False", "False", "False"))
        self.assertEqual((d["Analytics"]["PermissionAsked"], d["Analytics"]["Enabled"]), ("True", "False"))
        self.assertEqual((d["DSP"]["Backend"], d["Input"]["BackgroundInput"]), ("Cubeb", "True"))
        self.assertIn("UpdateTrack = \n", (u / "Config" / "Dolphin.ini").read_text())
        g = ini((u / "Config" / "GFX.ini").read_text())
        self.assertEqual(g, {"Hardware": {"Adapter": "0"},
                             "Settings": {"InternalResolution": "1", "ShaderCompilationMode": "2",
                                          "WaitForShadersBeforeStarting": "True", "ShowFPS": "False",
                                          "LogRenderTimeToFile": "True"}})
        lg = ini((u / "Config" / "Logger.ini").read_text())
        self.assertEqual(lg["Options"]["Verbosity"], "4")
        self.assertEqual(sorted(k for k, v in lg["Logs"].items() if v == "True"), sorted(gc.LOG_ON))
        self.assertIn("CI", gc.LOG_ON)
        self.assertEqual(list((u / "Config").glob("*.tmp")), [])

    def test_the_hotkeys_and_nothing_else(self):
        h = ini(gc.hotkeys_ini())["Hotkeys"]
        want = {"Device": "XInput2/0/Virtual core pointer", "General/Toggle Pause": "`F10`"}
        for n in (1, 2, 3, 8, 9):
            want[f"Load State/Load State Slot {n}"] = f"`F{n}`"
            want[f"Save State/Save State Slot {n}"] = f"@(Shift+`F{n}`)"
        self.assertEqual(h, want)                       # no Stop on Escape, no fullscreen toggle, no other slot

    def test_gcpadnew_for_four_pads(self):
        p = ini(gc.gcpad_ini())
        self.assertEqual(sorted(p), ["GCPad1", "GCPad2", "GCPad3", "GCPad4"])
        for n in range(1, 5):
            sec = p[f"GCPad{n}"]
            self.assertEqual(sec["Device"], f"evdev/0/PrivyHub Virtual Gamepad P{n}")
            self.assertEqual({k: sec[k] for k in ("Buttons/A", "Buttons/B", "Buttons/X", "Buttons/Y", "Buttons/Z",
                                                  "Buttons/Start")},
                             {"Buttons/A": "`SOUTH`", "Buttons/B": "`WEST`", "Buttons/X": "`EAST`",
                              "Buttons/Y": "`NORTH`", "Buttons/Z": "`TR`", "Buttons/Start": "`START`"})
            self.assertEqual((sec["Main Stick/Up"], sec["Main Stick/Right"], sec["C-Stick/Up"],
                              sec["C-Stick/Left"]), ("`Axis 1-`", "`Axis 0+`", "`Axis 4-`", "`Axis 3-`"))
            self.assertEqual((sec["Triggers/L-Analog"], sec["Triggers/R-Analog"], sec["Triggers/L"],
                              sec["Triggers/R"]), ("`Axis 2-+`", "`Axis 5-+`", "`Axis 2-+`", "`Axis 5-+`"))
            self.assertEqual((sec["D-Pad/Up"], sec["D-Pad/Down"], sec["D-Pad/Left"], sec["D-Pad/Right"]),
                             ("`Axis 7-`", "`Axis 7+`", "`Axis 6-`", "`Axis 6+`"))

    def test_the_layout_matches_the_companions_pad(self):
        import native_session_io as nsi
        c = nsi.NativeControllerBridge
        self.assertEqual(c.LINUX_GAMEPAD_NAME.format(player=3), gc.PAD_DEVICE.format(n=3).split("/", 2)[2])
        # the onn's cross / square / circle / triangle reach SOUTH / WEST / EAST / NORTH (the XUSB mapping)
        src = (ROOT / "companion/native_session_io.py").read_text()
        for xusb, code in (("XUSB_A", "BTN_SOUTH"), ("XUSB_X", "BTN_WEST"), ("XUSB_B", "BTN_EAST"),
                           ("XUSB_Y", "BTN_NORTH"), ("XUSB_RIGHT_SHOULDER", "BTN_TR")):
            self.assertIn(f"(self.{xusb}, ecodes.{code})", src)

    def test_the_pads_read_from_dolphins_log(self):
        d = Path(tempfile.mkdtemp())
        log = d / "x-dolphin.log"
        log.write_text("17:01:00:001 InputCommon/ControllerInterface/ControllerInterface.cpp:300 N[CI]: Added device: "
                       "evdev/0/PrivyHub Virtual Gamepad P1\n"
                       "17:01:00:002 x.cpp:1 N[CI]: Added device: evdev/0/PrivyHub Virtual Gamepad P2\n"
                       "17:01:00:003 x.cpp:1 N[CI]: Added device: evdev/1/PrivyHub Virtual Gamepad P3\n"
                       "17:01:00:004 x.cpp:1 N[CI]: Removed device: evdev/0/PrivyHub Virtual Gamepad P2\n")
        seen = gc.pads_seen(log)
        self.assertEqual(seen, {"P1": "evdev/0", "P3": "evdev/1"})
        self.assertEqual(gc.pads_line(seen), "P1=evdev/0 P3=evdev/1 MISMATCH (the ini names evdev/0)")
        self.assertEqual(gc.pads_line({}), "none yet")
        self.assertEqual(gc.pads_line({"P1": "evdev/0"}), "P1=evdev/0")


# --- pause / resume ------------------------------------------------------------------------------------------------

class PauseResume(unittest.TestCase):
    def fake(self, **kw):
        f = FakeDolphin(Path(tempfile.mkdtemp(prefix="b69_")), **kw)
        return f, f.session(gc)

    def test_the_hotkey_confirmed_by_the_clock(self):
        f, s = self.fake()
        self.assertEqual(s.pause(), "hotkey")
        self.assertEqual((f.keys, f.signals, f.paused), (["F10"], [], True))
        self.assertIn(["xdotool", "windowactivate", "--sync", "77"], f.cmds)
        self.assertIn(["xdotool", "windowfocus", "--sync", "77"], f.cmds)
        self.assertEqual(s.resume(), "hotkey")
        self.assertEqual((f.keys, f.paused), (["F10", "F10"], False))
        self.assertIn("GC pause: hotkey", f.lines)
        self.assertIn("GC resume: hotkey", f.lines)

    def test_a_silent_clock_is_sigstop_with_no_key(self):
        f, s = self.fake(clock_ok=False)
        self.assertEqual(s.pause(), "sigstop")
        self.assertEqual((f.keys, f.signals), ([], [int(signal.SIGSTOP)]))
        self.assertEqual(s.resume(), "sigcont")
        self.assertEqual((f.keys, f.signals), ([], [int(signal.SIGSTOP), int(signal.SIGCONT)]))

    def test_an_unconfirmed_key_falls_back_to_sigstop_once(self):
        f, s = self.fake(hotkeys=False)
        self.assertEqual(s.pause(), "sigstop")
        self.assertEqual((f.keys, f.signals), (["F10"], [int(signal.SIGSTOP)]))
        self.assertEqual(s.resume(), "sigcont")
        self.assertEqual(f.keys, ["F10"])                                     # no second key

    def test_a_late_key_after_sigstop_is_undone_on_resume(self):
        f, s = self.fake()
        f.paused = True                                                       # the key landed after the SIGSTOP
        f.kill(f.pid, signal.SIGSTOP)
        s.paused_by = "sigstop"
        self.assertEqual(s.resume(), "sigcont+hotkey")
        self.assertFalse(f.paused or f.stopped)

    def test_a_missed_resume_key_is_sent_once_more(self):
        f, s = self.fake()
        s.pause()
        f.ignore_keys = 1
        self.assertEqual(s.resume(), "hotkey")
        self.assertEqual(f.keys, ["F10", "F10", "F10"])
        self.assertFalse(f.paused)

    def test_a_resume_that_never_comes_is_an_error(self):
        f, s = self.fake()
        s.pause()
        f.hotkeys = False
        with self.assertRaises(gc.GCError):
            s.resume()

    def test_no_window_is_sigstop(self):
        f, s = self.fake(window=False)
        self.assertEqual(s.pause(), "sigstop")
        self.assertEqual(f.keys, [])

    def test_a_sigstop_pause_is_made_hotkey_for_a_state_key(self):
        f, s = self.fake(clock_ok=True, hotkeys=False)
        s.pause()                                                             # sigstop (the key was not read)
        f.hotkeys = True
        s.ensure_hotkey_pause()
        self.assertEqual((s.paused_by, f.paused, f.stopped), ("hotkey", True, False))
        self.assertEqual(f.signals, [int(signal.SIGSTOP), int(signal.SIGCONT)])

    def test_the_boot_wait_needs_the_clock_to_grow(self):
        f, s = self.fake()
        self.assertIsNotNone(s.wait_boot())
        f2, s2 = self.fake(clock_ok=False)
        self.assertIsNone(s2.wait_boot(bound=2.0))
        f3, s3 = self.fake()
        f3.paused = True                                                      # the pre-compile: no emulation yet
        self.assertIsNone(s3.wait_boot(bound=2.0))


# --- the manager: launch, SAVE / LOAD, stop ------------------------------------------------------------------------

class FakeProc:
    def __init__(self, pid):
        self.pid = pid
        self.returncode = None
        self.stdin = None

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.returncode = 0
        return 0


class Rig(unittest.TestCase):
    """The manager with `_gc` set as PRIVYHUB_GAMECUBE=1 sets it, a fake Popen and the fake Dolphin."""

    def setUp(self):
        self.old_gc, self.old_popen, self.old_session = em._gc, em.subprocess.Popen, gc.Session
        self.old_wait = gc.wait_helpers
        em._gc = gc
        self.games = tree({"one.rvz": MIB})
        self.proj = tree({"runtime/emulators/dolphin/dolphin-fake.AppImage": "x"})
        (self.proj / "runtime" / "h3_p1_paths.txt").write_text(f"GAMECUBE_DIR={self.games}\n")
        self.user = (self.proj / "data/games/gamecube/user").resolve()
        self.popen: list[dict] = []
        self.helper_calls: list[int] = []

    def tearDown(self):
        em._gc, em.subprocess.Popen, gc.Session, gc.wait_helpers = (self.old_gc, self.old_popen, self.old_session,
                                                                   self.old_wait)

    def launch(self, players_chosen=None, **fake_kw):
        f = FakeDolphin(self.proj, user_dir=self.user, **fake_kw)
        self.fake = f
        rig = self

        def popen(cmd, **kw):
            rig.popen.append({"cmd": cmd, **{k: kw.get(k) for k in ("cwd", "start_new_session")}})
            return FakeProc(f.pid)

        class S(rig.old_session):
            def __init__(self, pid, log, **kw):
                super().__init__(pid, log, run=f.run, kill=f.kill, sleep=f.sleep, clock=f.clock, proc_root=f.proc,
                                 grab=f.grab, **kw)

        em.subprocess.Popen = popen
        gc.Session = S
        gc.wait_helpers = lambda sid, *a, **k: (rig.helper_calls.append(sid), "gone 1.0s")[1]
        m = em.EmulatorManager(self.proj, config_path=ROOT / "companion/games/config/emulators.json")
        self.addCleanup(lambda: m._close_quietly(m.log_handle))
        game = {"id": "game_gc_fake", "system": "gamecube", "title": "made-up", "relative_path": "gamecube/one.rvz"}
        r = m.launch(game, players_chosen=players_chosen)
        return m, r

    def log_text(self):
        return next((self.proj / "logs/games").glob("*-gamecube.log")).read_text()


class Launch(Rig):
    def test_the_launch_the_config_the_ports_and_the_log(self):
        before = snapshot(self.games)
        m, r = self.launch()
        self.assertEqual((r["launch_kind"], r["gc_mode"], m._launch_kind), ("dolphin", True, "dolphin"))
        cmd = self.popen[0]["cmd"]
        self.assertEqual(cmd[1:], ["-b", "-u", str(self.user), "-e", str((self.games / "one.rvz").resolve())])
        self.assertTrue(self.popen[0]["start_new_session"])
        self.assertEqual(self.popen[0]["cwd"], str(self.user))
        self.assertEqual(sorted(p.name for p in (self.user / "Config").glob("*.ini")),
                         ["Dolphin.ini", "GCPadNew.ini", "GFX.ini", "Hotkeys.ini", "Logger.ini"])
        self.assertEqual(r["players_session"], gc.plan())
        ports = players_session.ports_set(m, None)["ports_set"]
        self.assertEqual((ports["ports"], ports["players"], ports["multitap"], ports["multitap_available"],
                          ports["source"]), (4, 4, False, False, "gamecube"))
        self.assertNotIn("capable", ports)
        log = self.log_text()
        for line in ("GC launch: dolphin ports=4 backend=vulkan adapter=0 config=whole", "GC window: ",
                     "GC boot: cpu thread ", "GC audio: sink-input ", "GC pads: none yet", "GC dolphin-log: "):
            self.assertIn(line, log)
        self.assertNotIn("one.rvz", log); self.assertNotIn("made-up", log); self.assertNotIn("game_gc_fake", log)
        self.assertNotIn(str(self.games), log)
        self.assertEqual(before, snapshot(self.games))                          # the drive's folder never written
        link = self.user / "Logs" / "dolphin.log"
        self.assertTrue(link.is_symlink())
        self.assertRegex(os.readlink(link), r"/data/games/gamecube/logs/\d{8}T\d{6}Z-dolphin\.log$")

    def test_four_ports_whatever_the_join_no_relaunch(self):
        for chosen in (None, 1, 2, 4):
            m, r = self.launch(players_chosen=chosen)
            self.assertEqual(m._players_session["ports"], 4)
            self.assertEqual(m._last_device_args, [])
            m.stop()

    def test_the_relaunch_is_refused(self):
        m, r = self.launch()
        plugin = types.SimpleNamespace(_emulator=m, _native_stream=None, _recovery_start_args={"client_ip": "x"})
        for players in (2, 4):
            with self.assertRaises(relaunch_ports.RelaunchRefused) as cm:
                relaunch_ports.run(plugin, players)
            self.assertIn("GameCube has four ports", str(cm.exception))
        with self.assertRaises(em.EmulatorError):
            m.save_relaunch_state()

    def test_unconfigured_folder_refuses_with_no_popen(self):
        (self.proj / "runtime" / "h3_p1_paths.txt").unlink()
        with self.assertRaises(em.EmulatorError):
            self.launch()
        self.assertEqual(self.popen, [])

    def test_no_window_ends_the_launch(self):
        with self.assertRaises(em.EmulatorError):
            self.launch(window=False)
        self.assertIn(int(signal.SIGTERM), self.fake.signals)

    def test_the_exit_and_the_next_launchs_helper_wait(self):
        m, r = self.launch()
        out = m.stop()
        self.assertTrue(out["gc_exit"].startswith("sigterm"))
        self.assertIsNone(m._launch_kind)
        self.assertIn(int(signal.SIGTERM), self.fake.signals)
        self.assertEqual(m._gc_helper_sid, self.fake.pid)
        self.assertIn("GC exit: sigterm", self.log_text())
        game = {"id": "game_gc_fake", "system": "gamecube", "title": "made-up", "relative_path": "gamecube/one.rvz"}
        m.launch(game)
        self.assertEqual(self.helper_calls, [self.fake.pid])
        self.assertIsNone(m._gc_helper_sid)
        self.assertTrue(any("GC helper: gone 1.0s" in p.read_text()
                            for p in (self.proj / "logs/games").glob("*-gamecube.log")))


class SaveLoad(Rig):
    def paused(self, **kw):
        m, r = self.launch(**kw)
        p = m.pause()
        self.assertEqual((p["gc_pause"], m._paused), ("hotkey", True))
        return m

    def test_save_by_shift_f1_the_file_check_and_the_ps1_shaped_reply(self):
        m = self.paused()
        r = m.save_state(1)
        self.assertEqual(self.fake.keys[-1], "Shift_L+F1")
        for k, v in (("action", "save_state"), ("slot", 1), ("accepted", True), ("confirmed", True),
                     ("replaced_existing", False), ("control", "dolphin_hotkey_save_state"), ("hotkey", "Shift+F1")):
            self.assertEqual(r[k], v)
        self.assertTrue(r["state_file"].endswith(f"StateSaves/{FAKE_ID}.s01"))
        self.assertTrue(m._save_state_slot_detail(1)["exists"])
        self.assertTrue(m._paused and self.fake.paused)                         # saved paused, left paused
        self.assertRegex(self.log_text(), r"GC save: slot 1 hotkey; file stable 0\.\ds")
        self.assertTrue(m.save_state(1)["replaced_existing"])

    def test_a_file_that_never_comes_is_the_error(self):
        m = self.paused(writes_state=False)
        with self.assertRaises(em.EmulatorError) as cm:
            m.save_state(2)
        self.assertEqual(str(cm.exception), "PrivyHub could not verify the saved GameCube state")
        self.assertIn("GC save: slot 2 hotkey; file not stable in 1.0s", self.log_text())

    def test_a_file_still_growing_at_the_bound_is_not_confirmed(self):
        m = self.paused(save_delay=0.9)                       # appears at 0.9 s: cannot stand 0.25 s by 1.0 s
        with self.assertRaises(em.EmulatorError):
            m.save_state(3)

    def test_load_by_f1_with_the_picture_check(self):
        m = self.paused()
        m.save_state(1)
        r = m.load_state(1)
        self.assertIn("F1", self.fake.keys)
        self.assertEqual(self.fake.loaded, [1])
        for k, v in (("action", "load_state"), ("confirmed", True), ("verification", "picture"), ("paused", True),
                     ("control", "dolphin_hotkey_load_state"), ("hotkey", "F1")):
            self.assertEqual(r[k], v)
        self.assertTrue(m._paused and self.fake.paused)                         # paused again after the check
        self.assertIn("GC load: slot 1 hotkey; picture ok", self.log_text())

    def test_a_static_picture_is_the_error_with_the_game_paused(self):
        m = self.paused(picture="static")
        m.save_state(1)
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(1)
        self.assertEqual(str(cm.exception), "The game did not resume from the save")
        self.assertTrue(m._paused and self.fake.paused)
        self.assertIn("GC load: slot 1 hotkey; picture static", self.log_text())

    def test_load_refused_running_or_empty(self):
        m, r = self.launch()
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(1)
        self.assertEqual(str(cm.exception), "Load State requires the game to be paused")
        m.pause()
        with self.assertRaises(em.EmulatorError) as cm:
            m.load_state(2)
        self.assertEqual(str(cm.exception), "No save state exists in Slot 2")


# --- the hold, the stall, the give-up --------------------------------------------------------------------------------

class Rec:
    def __init__(self):
        self.rows = []

    def _log(self, event, **f):
        self.rows.append({"event": event, **f})

    def of(self, event):
        return [r for r in self.rows if r["event"] == event]


def rw():
    return types.SimpleNamespace(fps=60.0, _row=lambda recovery, event, fields, **extra: (
        recovery._log(event, **{**fields, **extra}), {**fields, **extra})[1])


class Recovery(Rig):
    def cores(self, **kw):
        m, r = self.launch(**kw)
        rec = Rec()
        c = rewind_cores.Cores("state", m, rec, clock=self.fake.clock, wall=lambda: 1000.0 + self.fake.t,
                               threaded=False)
        spawned = []
        c._spawn = spawned.append
        return m, rec, c, spawned

    def hold(self, kind="silence", onset=10.0, **kw):
        m, rec, c, spawned = self.cores(**kw)
        c.save(onset, onset + 0.4, kind)                          # the quiet mark: the game running
        self.assertFalse(self.fake.paused)
        m.pause()                                                 # the hold owns a pause
        pending = {"onset": onset, "paused_at": onset + 1.0}
        row = c.release(rw(), rec, {"via": "client_ready_stall" if kind == "stall" else "input_release"}, pending)
        return m, rec, c, spawned, row

    def test_the_slot9_save_is_shift_f9_into_the_running_game(self):
        m, rec, c, _ = self.cores()
        c.save(10.0, 10.4, "silence")
        self.assertEqual(self.fake.keys[-1], "Shift_L+F9")
        row = rec.of("state_saved")[-1]
        self.assertEqual((row["slot"], row["core"], row["gc_states"], row["ack"]), (9, "dolphin", "hotkey",
                                                                                     "hotkey sent"))
        self.assertIn("GC state save: slot 9 hotkey sent (silence)", self.log_text())

    def test_the_hold_s_return_loads_slot_9_then_the_picture_after_the_resume(self):
        m, rec, c, spawned, row = self.hold()
        self.assertEqual(self.fake.loaded, [9])
        self.assertEqual((row["slot"], row["core"], row["gc_states"], row["verification"]),
                         (9, "dolphin", "hotkey", "picture_after_resume"))
        self.assertLessEqual(row["load_ms"], gc.RELEASE_SHARE_S * 1000.0)
        self.assertTrue(self.fake.paused)                          # the resume is the recovery's
        m.resume()
        spawned[0]()
        self.assertEqual(rec.of("gc_states")[-1]["verdict"], "ok")
        self.assertEqual(rec.of("rewind_failed"), [])
        self.assertIsNone(c.last_save)

    def test_the_stall_resume_loads_the_stall_save(self):
        m, rec, c, spawned, row = self.hold(kind="stall", onset=20.0)
        self.assertEqual(rec.of("input_release")[-1]["via"], "client_ready_stall")
        self.assertEqual(self.fake.loaded, [9])

    def test_a_static_picture_is_the_ps1_shaped_rewind_failed_row(self):
        m, rec, c, spawned, row = self.hold(picture="static")
        m.resume()
        spawned[0]()
        self.assertEqual(rec.of("rewind_failed")[-1]["reason"],
                         "the game did not resume from the save (picture static)")

    def test_no_file_resumes_without_a_load(self):
        m, rec, c, spawned, row = self.hold(writes_state=False)
        self.assertEqual(self.fake.loaded, [])
        self.assertEqual(rec.of("rewind_skipped")[-1]["reason"], "the GameCube state file is not stable")
        self.assertEqual(spawned, [])

    def test_the_rewind_is_off_outside_the_state_mode(self):
        import hold_rewind
        m, r = self.launch()
        rec = Rec()
        rw_obj = object.__new__(hold_rewind.Rewinder)
        rw_obj._lock = threading.Lock()
        rw_obj.cap, rw_obj.b9, rw_obj.emulator, rw_obj.fps = 30, None, m, 60.0
        rw_obj.counter_before = lambda pending: 50
        rw_obj._row = rw()._row
        rec._state_since = 7
        rw_obj._pending = {"key": 7, "onset": 10.0, "paused_at": 11.0}
        rw_obj.rewind(rec, "input_release")
        row = rec.of("rewind_skipped")[-1]
        self.assertEqual((row["reason"], row["gc_mode"]), ("gamecube: no rewind in Dolphin", True))

    def test_the_give_up_save_the_prompts_resume_and_the_copy(self):
        m, r = self.launch()
        m.pause()
        saved = m.save_recovery_state()
        self.assertEqual(self.fake.keys[-1], "Shift_L+F8")
        self.assertEqual(saved["gc_states"], "hotkey")
        self.assertTrue(saved["state_file"].endswith(".s08"))
        self.assertTrue(m.recovery_state_detail()["exists"])
        m.resume()
        out = m.load_recovery_state_running()
        self.assertEqual((out["verification"], out["gc_states"]), ("picture", "hotkey"))
        self.assertEqual(self.fake.loaded, [8])
        self.assertFalse(self.fake.paused)                                       # left running
        cp = m.copy_recovery_state_to_slot(2)
        self.assertTrue(cp["state_file"].endswith(f"{FAKE_ID}.s02"))
        self.assertTrue(m._save_state_slot_detail(2)["exists"])
        with self.assertRaises(em.EmulatorError):
            m.load_recovery_state_running(source=Path("x.s07"))

    def test_the_give_up_row_carries_gc_states(self):
        from games import link_drop_recovery as ldr
        rec = ldr.LinkDropRecovery(Path(tempfile.mkdtemp(prefix="b69_")), pause_game=lambda: None,
                                   resume_game=lambda: None,
                                   save_recovery_state=lambda: {"state_file": "x.s08", "gc_states": "hotkey"},
                                   restart_encoder=lambda: {}, full_start_encoder=lambda: {}, stream_active=lambda: True,
                                   end_session=lambda: None, client_packet_age_ms=lambda: 10.0,
                                   recovery_save_detail=lambda: {})
        rec._give_up_and_save()
        row = [json.loads(x) for x in rec.log_path().read_text().splitlines() if '"gave_up_saved"' in x][0]
        self.assertEqual(row["gc_states"], "hotkey")
        self.assertNotIn("ps2_states", row)


# --- Dolphin's log per launch, the exit's helper ------------------------------------------------------------------

class LogsAndHelper(unittest.TestCase):
    def test_the_link_the_fallback_and_the_counters(self):
        proj = Path(tempfile.mkdtemp(prefix="b69_"))
        user = proj / "data/games/gamecube/user"
        target = gc.log_for_launch(proj, 1_800_000_000.0)
        self.assertEqual(target.name, "20270115T080000Z-dolphin.log")
        (user / "Logs").mkdir(parents=True)
        (user / "Logs" / "dolphin.log").write_text("from a missed exit\n")
        kept = gc.link_log(user, target)
        self.assertRegex(kept, r"^\d{8}T\d{6}Z-dolphin\.log$")
        self.assertEqual((target.parent / kept).read_text(), "from a missed exit\n")
        with open(user / "Logs" / "dolphin.log", "a") as fh:                    # Dolphin writes through the link
            fh.write("line one\n")
        self.assertEqual(target.read_text(), "line one\n")
        (user / "Logs" / "dolphin.log").unlink()
        (user / "Logs" / "dolphin.log").write_text("line two\n")                # Dolphin replaced the link
        (user / "Logs" / "vblank_times.txt").write_text("16.6\n")
        (user / "Logs" / "render_times.txt").write_text("16.6\n")
        out = gc.collect_after_exit(user, target)
        self.assertEqual((out["appended"], sorted(out["moved"])), (True, ["render_times.txt", "vblank_times.txt"]))
        self.assertEqual(target.read_text(), "line one\nline two\n")
        self.assertTrue((target.parent / "20270115T080000Z-vblank_times.txt").is_file())

    def test_the_30_day_prune(self):
        d = Path(tempfile.mkdtemp(prefix="b69_"))
        now = 1_800_000_000.0
        for name in (gc.stamp_of(now - 31 * 86400) + "-dolphin.log", gc.stamp_of(now - 31 * 86400) + "-vblank_times.txt",
                     gc.stamp_of(now - 29 * 86400) + "-dolphin.log", "other.txt"):
            (d / name).write_text("x")
        removed = gc.prune_logs(d, now)
        self.assertEqual(len(removed), 2)
        self.assertEqual(sorted(p.name for p in d.iterdir()), sorted([gc.stamp_of(now - 29 * 86400) + "-dolphin.log",
                                                                      "other.txt"]))

    def proc(self, entries):
        root = Path(tempfile.mkdtemp(prefix="b69_"))
        for pid, (sid, argv0) in entries.items():
            (root / str(pid)).mkdir()
            (root / str(pid) / "stat").write_text(f"{pid} (x y) S 1 {sid} {sid} 0 -1 0\n")
            (root / str(pid) / "cmdline").write_bytes(argv0.encode() + b"\0--appimage-mount\0")
        return root

    def test_the_helper_count_and_the_wait(self):
        root = self.proc({501: (500, "/r/dolphin.AppImage"), 502: (500, "/usr/bin/other"), 601: (600, "/r/x.AppImage")})
        self.assertEqual(gc.session_members(500, root), [501])
        clock = [0.0]
        kills = []

        def sleep(d):
            clock[0] += d
            if clock[0] >= 2.0 and (root / "501").exists():
                for f in (root / "501").iterdir():
                    f.unlink()
                (root / "501").rmdir()
        got = gc.wait_helpers(500, proc_root=root, kill=lambda p, s: kills.append(p), sleep=sleep,
                              clock=lambda: clock[0])
        self.assertEqual((got, kills), ("gone 2.0s", []))
        self.assertEqual(gc.wait_helpers(500, proc_root=root, kill=lambda p, s: kills.append(p)), "none")

    def test_the_sigkill_bound(self):
        root = self.proc({701: (700, "/r/dolphin.AppImage")})
        clock = [0.0]
        kills = []
        got = gc.wait_helpers(700, proc_root=root, kill=lambda p, s: kills.append((p, s)),
                              sleep=lambda d: clock.__setitem__(0, clock[0] + d), clock=lambda: clock[0])
        self.assertEqual((got, kills), ("killed 1 after 10s", [(701, signal.SIGKILL)]))


# --- the hooks: the flag absent / 0 / 1 (fresh interpreters) -----------------------------------------------------------

PLUGIN_CODE = r"""
import json, os, sys, importlib.util
from pathlib import Path
sys.path.insert(0, "companion")
spec = importlib.util.spec_from_file_location("g", "companion/plugins/games.py")
G = importlib.util.module_from_spec(spec); spec.loader.exec_module(G)
from games import emulator_manager as em
proj = Path(os.environ["B69_PROJ"])
out = {"gc_imported": "gamecube_session" in sys.modules, "em_gc": em._gc is not None}
p = object.__new__(G.GamesPlugin)                 # (no __init__: the services stay off; its SYSTEMS lines as written)
if G._gc_session is not None:
    p.SYSTEMS = {**G.GamesPlugin.SYSTEMS, G._gc_session.SYSTEM_ID: {"name": G._gc_session.SYSTEM_NAME,
                                                                    "folder": None, "extensions": set()}}
out["systems"] = sorted(p.SYSTEMS)
p.PROJECT_ROOT = proj; p.GAMES_ROOT = proj / "games"
p._lock = __import__("threading").RLock(); p._cached_at = 0.0; p._cached_games = []
out["scan"] = sorted([g["system"], g["relative_path"]] for g in p._scan())
m = em.EmulatorManager(proj, config_path=Path("companion/games/config/emulators.json").resolve())
try:
    out["catalog"] = list(m._controller_profile_catalog({"system": "gamecube"}))
except Exception as exc:
    out["catalog"] = type(exc).__name__
if em._gc is None:                                # absent: today's launch refusal, nothing made
    try:
        m.launch({"id": "g", "system": "gamecube", "title": "t", "relative_path": "gamecube/one.rvz"})
        out["launch"] = "launched"
    except em.EmulatorError:
        out["launch"] = "EmulatorError"
out["data_gc"] = (proj / "data/games/gamecube").exists()
print(json.dumps(out))
"""


def run_plugin(flag, proj):
    env = {"PATH": "/usr/bin:/bin", "B69_PROJ": str(proj)}
    if flag is not None:
        env["PRIVYHUB_GAMECUBE"] = flag
    r = subprocess.run([sys.executable, "-c", PLUGIN_CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class Hooks(unittest.TestCase):
    def setUp(self):
        self.games = tree({"one.rvz": MIB, "two.iso": MIB, "region/x.bin": 100})
        self.proj = tree({"games/ps1/p.chd": b"x", "runtime/emulators/dolphin/d.AppImage": "x"})
        (self.proj / "runtime" / "h3_p1_paths.txt").write_text(f"GAMECUBE_DIR={self.games}\n")

    def test_absent_is_today(self):
        before = snapshot(self.games)
        out = run_plugin(None, self.proj)
        self.assertEqual((out["gc_imported"], out["em_gc"]), (False, False))
        self.assertNotIn("gamecube", out["systems"])
        self.assertEqual(out["scan"], [["ps1", "games/ps1/p.chd"]])
        self.assertEqual(out["catalog"], "EmulatorError")                     # today's refusal: no profile
        self.assertEqual(out["launch"], "EmulatorError")
        self.assertFalse(out["data_gc"])
        self.assertEqual(run_plugin("0", self.proj), out)
        self.assertEqual(before, snapshot(self.games))

    def test_with_the_flag_the_list_and_the_catalog(self):
        before = snapshot(self.games)
        out = run_plugin("1", self.proj)
        self.assertTrue(out["gc_imported"] and out["em_gc"])
        self.assertIn("gamecube", out["systems"])
        self.assertEqual(out["scan"], [["gamecube", "gamecube/one.rvz"], ["gamecube", "gamecube/two.iso"],
                                       ["ps1", "games/ps1/p.chd"]])
        self.assertEqual(out["catalog"], ["gamecube", "", {}])
        self.assertFalse(out["data_gc"])                                        # the list touches no hub file
        self.assertEqual(before, snapshot(self.games))                          # the drive's folder never written


# --- the rows: gc_mode on the start and every heartbeat, the gc_session row ----------------------------------------

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
class Sess:
    def note_pads(self): return "P1=evdev/0"
class Emu:
    active_game = {"id": "g", "system": "gamecube", "title": "t"}
    _launch_kind = os.environ.get("B69_KIND") or None
    _players_session = None
    _gc = Sess()
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
print(json.dumps({"start_gc_mode": r.get("gc_mode"), "gc_rows": [x for x in rows if x["event"] == "gc_session"],
                  "hb_gc_mode": hb[-1].get("gc_mode"), "hb_keys": sorted(hb[-1])}))
"""


def run_rows(flag, kind):
    env = {"PATH": "/usr/bin:/bin"}
    if flag:
        env["PRIVYHUB_GAMECUBE"] = flag
    if kind:
        env["B69_KIND"] = kind
    r = subprocess.run([sys.executable, "-c", ROWS_CODE], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stderr[-2000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


class Rows(unittest.TestCase):
    def test_a_gamecube_session_says_so_on_the_start_and_every_heartbeat(self):
        out = run_rows("1", "dolphin")
        self.assertTrue(out["start_gc_mode"])
        self.assertEqual(len(out["gc_rows"]), 1)
        row = out["gc_rows"][0]
        self.assertEqual((row["gc_mode"], row["gc_states"], row["live"], row["off"], row["pads"]),
                         (True, "hotkey", list(gc.LIVE_BEHAVIOURS), ["rewind", "relaunch"], "P1=evdev/0"))
        self.assertTrue(out["hb_gc_mode"])

    def test_a_retroarch_session_and_the_flag_absent_are_today(self):
        for flag, kind in (("1", None), (None, None), (None, "dolphin")):
            out = run_rows(flag, kind)
            self.assertIsNone(out["start_gc_mode"])
            self.assertEqual(out["gc_rows"], [])
            self.assertNotIn("gc_mode", out["hb_keys"])


# --- the keeper and diag_read ------------------------------------------------------------------------------------------

class KeeperAndRead(unittest.TestCase):
    def test_the_game_log_name_and_the_keeper_copies_a_new_dolphin_log(self):
        import trip_log_keeper as tlk
        self.assertTrue(tlk.GAME_LOG.match("20261109-031500-gamecube.log"))
        self.assertTrue(tlk.DOLPHIN_LOG.match("20261109T081500Z-dolphin.log"))
        repo = Path(tempfile.mkdtemp(prefix="b69_"))
        logs = repo / "logs"
        (logs / "games").mkdir(parents=True)
        gl = repo / "data/games/gamecube/logs"
        gl.mkdir(parents=True)
        (gl / "20261109T070000Z-dolphin.log").write_text("old\n")
        out = repo / "keep"
        k = tlk.Keeper(out, cap=3600, start=0, logs_root=logs, overlay=lambda: {}, session=lambda: {},
                       journal=lambda a, b: b"", peers=lambda: None, clock=lambda: 1_800_000_000.0)
        k.begin()
        (gl / "20261109T081500Z-dolphin.log").write_text("00:01:000 Core/Boot/Boot.cpp:1 N[BOOT]: Booting from disc\n")
        k.copy()
        raw = out / "raw"
        self.assertTrue((raw / "gclogs__20261109T081500Z-dolphin.log").is_dir())
        self.assertFalse((raw / "gclogs__20261109T070000Z-dolphin.log").exists())   # present at the start: seen

    def test_diag_read_labels_and_counts_a_gamecube_session(self):
        import diag_read as dr
        name = "20261109T080000Z-dolphin.log"
        data = ("00:05:000 DolphinQt/Translation.cpp:301 E[COMMON]: No suitable translation file found\n"
                "00:06:000 Core/Boot/Boot.cpp:529 N[BOOT]: Booting from disc: x\n"
                "00:07:000 InputCommon/ControllerInterface/ControllerInterface.cpp:1 N[CI]: Added device: "
                "evdev/0/PrivyHub Virtual Gamepad P1\n"
                "59:59:000 Core/x.cpp:1 W[CORE]: a warning before the hour turns\n"
                "00:10:000 Core/x.cpp:1 E[CORE]: an error after it\n").encode()
        ev = dr.dolphin_events(name, data)
        kinds = [k for _, k in ev]
        self.assertEqual(kinds, ["boot", "pad_added", "warning", "error"])           # Translation.cpp not counted
        self.assertEqual(ev[-1][0], datetime(2026, 11, 9, 9, 0, 10))                 # carried into the next hour
        self.assertEqual(ev[0][0], datetime(2026, 11, 9, 8, 0, 6))

        class L:
            pcsx2_logs = {}
            dolphin_logs = {name: data}
        a = object.__new__(dr.Analysis)
        a.dolphin_launches = [datetime(2026, 11, 9, 8, 0, 0)]
        a.dolphin = ev
        s = {"start": datetime(2026, 11, 9, 8, 1, 0), "end": datetime(2026, 11, 9, 8, 59, 59, 500000)}
        a.sessions = [s]
        self.assertEqual(a.dolphin_counts(s), {"boot": 1, "pad_added": 1, "pad_removed": 0, "error": 0,
                                               "warning": 1})
        self.assertTrue(dr.is_game_log("20261109-030000-gamecube.log"))

    def test_diag_check_names_a_gamecube_row(self):
        import diag_check as dc
        p = Path(tempfile.mkdtemp(prefix="b69_")) / "sessions.jsonl"
        p.write_text(json.dumps({"system": "gamecube", "core": "dolphin", "end_utc": "2026-11-09T08:10:00Z",
                                 "hitch_s_per_10min": 1.0, "hitch_s_bar_per_10min": 0.5, "hold_resume_s": 2}) + "\n")
        self.assertTrue(dc.line_last_session(p).startswith("last session: gamecube (dolphin)"))


# --- the metric ------------------------------------------------------------------------------------------------------

class Metric(unittest.TestCase):
    def frames(self):
        out, t, i = [], 0.0, 0
        for sec in range(30):                      # 12 s at 60, 18 s at 30 (each frame twice), one hitch second
            rate = 60 if sec < 12 else 30
            for k in range(60):
                h = f"{i:08X}"
                if rate == 30 and k % 2:
                    h = out[-1][1]
                elif sec == 20 and k >= 20:        # a 30-fps second with only 10 distinct frames
                    h = out[-1][1]
                else:
                    i += 1
                out.append((sec + k / 60.0, h, 100.0))
        return out

    def test_two_segments_a_transition_and_a_hitch(self):
        import gc_frames
        r = gc_frames.capture(self.frames())
        segs = [(s["start_s"], s["end_s"], s["rate"]) for s in r["segments"]]
        self.assertEqual(segs, [(0, 11, 60), (13, 29, 30)])
        self.assertEqual(r["transition_or_short_seconds"], 2)
        self.assertEqual(r["segments"][0]["hitch_seconds"], 0)
        self.assertEqual(r["segments"][1]["hitch_seconds"], 1)
        self.assertEqual(r["hitch_seconds_total"], 1)

    def test_dolphins_render_times_and_vblank_beside(self):
        import gc_frames
        intervals = [1000 / 60] * 600 + [1000 / 30] * 300 + [250.0, 250.0] + [1000 / 30] * 300
        r = gc_frames.render(intervals)
        # the half-second gap inside the 30-fps part is a hitch second of that segment, not a new segment
        self.assertEqual([s["rate"] for s in r["segments"]], [60, 30])
        self.assertEqual([s["hitch_seconds"] for s in r["segments"]], [0, 1])
        self.assertEqual(r["transition_or_short_seconds"], 2)
        v = gc_frames.vblank([1000 / 59.94] * 600 + [40.0])
        self.assertEqual((v["n"], v["gt_34ms"], v["gt_100ms"]), (601, 1, 0))
        self.assertAlmostEqual(v["per_s"], 59.9, places=0)


if __name__ == "__main__":
    unittest.main()
