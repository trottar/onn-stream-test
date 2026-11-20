#!/usr/bin/env python3
"""B167 (host): the add-a-game tool's picture source starts, and says why when it cannot.

`tools/party_add_game_capture.py` with a made-up RetroArch (`fake_ra.py`, standing in for the AppImage), made-up cores,
a made-up user RetroArch config and a made-up hub on loopback: **each reason** — busy (nothing started), display (none
given; and RetroArch's own video-driver line), content not found, core missing, config, exited, not playing, state
refused — fixed words, no name or path; RetroArch's log copied to `log_to` whatever the end. **It starts as the hub
does:** the display from the user manager when the caller has none (the fake sees it); the hub's own core (bsnes for
SNES, Beetle PSX HW for PS1); the core's and the title's own core options copied, `game_specific_options` on; frames
made. **learn says the reason as a cell** ("pictures made"), the log's place named, nothing named. **learn's labels
anchored on the screen that stays** (an ending saved a moment early). **rehearse takes the rules folder's begin** for a
title already added. Temp dirs removed.

    python3 -m unittest discover -s tests/b167_pictures_start -v
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import stat
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "tests" / "b157_add_game"))
sys.path.insert(0, str(ROOT / "tools"))
import made_up_hub  # noqa: E402

ENV_KEYS = ("PRIVYHUB_ADD_GAME_RA_APP", "PRIVYHUB_ADD_GAME_RA_CORES", "PRIVYHUB_ADD_GAME_RA_CONFIG",
            "PRIVYHUB_ADD_GAME_HUB", "PRIVYHUB_ADD_GAME_SYSTEMCTL", "FAKE_RA_MODE", "DISPLAY", "XAUTHORITY",
            "PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_ADD_GAME_PROJECT", "PRIVYHUB_H7_RULES",
            "PRIVYHUB_ADD_GAME_DROPINS", "PRIVYHUB_ADD_GAME_KEPT_ROOT", "PARTY_ADD_GAME_CAPTURE", "PRIVYHUB_ADD_GAME_LOGS",
            "PRIVYHUB_ADD_GAME_RA_BASE")
NAME = "Made Up Seven (USA)"


class Base(unittest.TestCase):
    def setUp(self):
        import party_add_game_capture as cap
        self.cap = cap
        self.old = {k: os.environ.get(k) for k in ENV_KEYS}
        self.bound = cap.START_BOUND_S
        cap.START_BOUND_S = 2.0
        self.tmp = Path(tempfile.mkdtemp(prefix="b167_"))
        app = self.tmp / "app" / "RetroArch.AppImage"
        app.parent.mkdir()
        shutil.copyfile(HERE / "fake_ra.py", app)
        app.chmod(app.stat().st_mode | stat.S_IEXEC)
        cores = self.tmp / "cores"
        cores.mkdir()
        for c in ("bsnes_libretro.so", "mednafen_psx_hw_libretro.so", "mupen64plus_next_libretro.so"):
            (cores / c).write_bytes(b"made-up core")
        conf = self.tmp / "userconf"
        for lib in ("bsnes", "Beetle PSX HW"):
            (conf / lib).mkdir(parents=True)
            (conf / lib / f"{lib}.opt").write_text('made_up_scale = "4x"\n')
            (conf / lib / f"{NAME}.opt").write_text('made_up_title = "on"\n')
            (conf / lib / "Another (USA).opt").write_text('another = "x"\n')
        base = self.tmp / "retroarch.cfg"                     # a made-up persistent config (the hub's is not read)
        base.write_text('config_save_on_exit = "false"\nvideo_driver = "gl"\n')
        self.game = self.tmp / "games" / f"{NAME}.cue"
        self.game.parent.mkdir()
        self.game.write_text("made-up game file")
        self.state = self.tmp / "kept.state"
        self.state.write_text("made-up state")
        self.hub = made_up_hub.MadeUpHub([])
        self.ctl = self.tmp / "systemctl"
        self.ctl.write_text("#!/bin/sh\nexit 0\n")
        self.ctl.chmod(0o755)
        for k in ("DISPLAY", "XAUTHORITY", "FAKE_RA_MODE"):
            os.environ.pop(k, None)
        os.environ.update({"PRIVYHUB_ADD_GAME_RA_APP": str(app), "PRIVYHUB_ADD_GAME_RA_CORES": str(cores),
                           "PRIVYHUB_ADD_GAME_RA_CONFIG": str(conf), "PRIVYHUB_ADD_GAME_HUB": self.hub.url,
                           "PRIVYHUB_ADD_GAME_SYSTEMCTL": str(self.ctl), "DISPLAY": ":97",
                           "PRIVYHUB_ADD_GAME_RA_BASE": str(base)})

    def tearDown(self):
        self.cap.START_BOUND_S = self.bound
        self.hub.close()
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_capture(self, mode="ok", system="ps1", content=None):
        if mode:
            os.environ["FAKE_RA_MODE"] = mode
        out = self.tmp / "out"
        shutil.rmtree(out, ignore_errors=True)
        out.mkdir()
        log = self.tmp / "logs" / "begin.retroarch.log"
        log.unlink(missing_ok=True)
        b = {"content": str(content or self.game), "system": system}
        try:
            rows = self.cap.capture(self.state, b, out, 1.0, 0.5, log_to=log)
            return rows, None, log
        except self.cap.CaptureError as exc:
            return None, exc, log


class Reasons(Base):
    def assertReason(self, exc, reason):
        self.assertIsNotNone(exc, reason)
        self.assertEqual(exc.reason, reason)
        self.assertEqual(exc.words, self.cap.WORDS[reason])
        self.assertNotIn(NAME, str(exc))
        self.assertNotIn(str(self.tmp), str(exc))

    def test_busy_nothing_started(self):
        import http.server, threading
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                body = json.dumps({"active": True}).encode()
                self.send_response(200); self.send_header("Content-Length", str(len(body))); self.end_headers()
                self.wfile.write(body)
            def log_message(self, *a):
                pass
        srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        os.environ["PRIVYHUB_ADD_GAME_HUB"] = f"http://127.0.0.1:{srv.server_address[1]}"
        try:
            _rows, exc, log = self.run_capture("ok")
        finally:
            srv.shutdown(); srv.server_close()
        self.assertReason(exc, "busy")
        self.assertFalse(log.exists())                       # RetroArch never started: no log

    def test_no_display_given(self):
        os.environ.pop("DISPLAY")
        _rows, exc, log = self.run_capture("ok")
        self.assertReason(exc, "display")
        self.assertFalse(log.exists())

    def test_display_from_the_user_manager(self):
        os.environ.pop("DISPLAY")
        self.ctl.write_text("#!/bin/sh\necho 'HOME=/x'\necho 'DISPLAY=:77'\necho 'XAUTHORITY=/made/up'\n")
        rows, exc, log = self.run_capture("ok")
        self.assertIsNone(exc, exc)
        self.assertIn("FAKE display :77", log.read_text())

    def test_each_log_reason(self):
        for mode, reason in (("display", "display"), ("content", "content not found"), ("core", "core missing"),
                             ("config", "config"), ("other", "exited"), ("silent", "not playing"),
                             ("state", "state refused")):
            _rows, exc, log = self.run_capture(mode)
            self.assertReason(exc, reason)
            self.assertTrue(log.is_file(), mode)            # RetroArch's own log kept, whatever the end

    def test_content_not_found_and_core_missing_before_start(self):
        _rows, exc, log = self.run_capture("ok", content=self.tmp / "games" / "gone.cue")
        self.assertReason(exc, "content not found")
        (self.tmp / "cores" / "mednafen_psx_hw_libretro.so").unlink()
        _rows, exc, log = self.run_capture("ok")
        self.assertReason(exc, "core missing")

    def test_base_config_unreadable(self):
        os.environ["PRIVYHUB_ADD_GAME_RA_BASE"] = str(self.tmp / "no_such.cfg")
        _rows, exc, log = self.run_capture("ok")
        self.assertReason(exc, "config")


class StartsAsTheHub(Base):
    def test_frames_core_and_options(self):
        rows, exc, log = self.run_capture("ok", system="snes")
        self.assertIsNone(exc, exc)
        self.assertGreaterEqual(len(rows), 2)
        text = log.read_text()
        self.assertIn("FAKE core bsnes_libretro.so", text)  # the hub's SNES core, not B95's snes9x
        self.assertIn('FAKE opts ["Made Up Seven (USA).opt", "bsnes.opt"]', text)   # the core's and the title's own
        self.assertIn("FAKE game_specific_options true", text)
        self.assertIn("FAKE display :97", text)
        rows, exc, log = self.run_capture("ok", system="ps1")
        self.assertIn("FAKE core mednafen_psx_hw_libretro.so", log.read_text())
        self.assertEqual(self.cap.hub_core("n64"), "mupen64plus_next_libretro.so")


def _tool(*argv):
    import party_add_game as pag
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(a) for a in argv])
    return rc, buf.getvalue()


def failing_capture(state, binding, out_dir, seconds, every, log_to=None):
    """A picture source that cannot start (as the hub's without a display)."""
    import party_add_game_capture as cap
    if log_to is not None:
        Path(log_to).parent.mkdir(parents=True, exist_ok=True)
        Path(log_to).write_text("[ERROR] [Video] Cannot open video driver. Exiting...\n")
    raise cap.CaptureError("display")


class LearnSaysWhy(unittest.TestCase):
    def setUp(self):
        import party_add_game as pag
        self.pag = pag
        self.tmp = Path(tempfile.mkdtemp(prefix="b167_learn_"))
        self.old = {k: os.environ.get(k) for k in ENV_KEYS}
        os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(self.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(self.tmp / "ev"),
                           "PRIVYHUB_ADD_GAME_PROJECT": str(self.tmp / "proj"), "PRIVYHUB_H7_RULES": str(self.tmp / "rules"),
                           "PARTY_ADD_GAME_CAPTURE": "test_b167:failing_capture"})
        sys.path.insert(0, str(HERE))
        b = {"code": "T94", "game": "madeupgame7", "players": 2, "system": "ps1", "result": "winner", "cheat": None,
             "relative_path": "games/ps1/x.cue", "title": NAME, "content": "", "found_lines": "x"}
        kept = self.tmp / "home/T94/kept"
        kept.mkdir(parents=True)
        for r in ("begin", "other", "end_P1", "end_P2"):
            (kept / f"{r}.state").write_text(r)
        b["register_inputs"] = pag.register_inputs(b, pag.kept_states("T94"))
        (self.tmp / "home/T94/binding.json").write_text(json.dumps(b))
        (self.tmp / "ev/T94").mkdir(parents=True)
        (self.tmp / "ev/T94/register.json").write_text(json.dumps({"verdict": "PASS", "inputs": b["register_inputs"]}))

    def tearDown(self):
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_the_cell_names_the_reason(self):
        rc, text = _tool("learn", "T94")
        self.assertEqual(rc, 1, text)
        v = json.loads((self.tmp / "ev/T94/learn.json").read_text())
        c = {x["cell"]: x for x in v["cells"]}
        self.assertFalse(c["pictures made"]["met"])
        self.assertIn("display: RetroArch could not open a window", c["pictures made"]["read"])
        self.assertIn("logs/begin.retroarch.log in the title's add_game folder", c["pictures made"]["read"])
        self.assertNotIn("ProofError", json.dumps(v))
        self.assertTrue((self.tmp / "home/T94/logs/begin.retroarch.log").is_file())   # beside the tool's folder
        for n in (NAME, "madeupgame7", str(self.tmp)):
            self.assertNotIn(n, json.dumps(v) + (self.tmp / "ev/T94/learn.md").read_text() + text)


class LabelsTheScreenThatStays(unittest.TestCase):
    def test_an_ending_saved_a_moment_early(self):
        import numpy as np
        import party_add_game as pag
        sys.path.insert(0, str(ROOT / "tests" / "b102_h7_endscreen"))
        import test_b102 as b102
        tmp = Path(tempfile.mkdtemp(prefix="b167_labels_"))
        try:
            rng = np.random.default_rng(167)
            run = tmp / "end_P1"
            run.mkdir()
            rows = ["seconds,file"]
            for k in range(20):                               # 2 frames of another screen, then the end screen stays
                im = b102.other(900 + k, rng) if k < 2 else b102.screen(50, "10", rng)
                im.save(run / f"f{k:04d}.png")
                rows.append(f"{k * 0.5:.2f},f{k:04d}.png")
            (run / "index.csv").write_text("\n".join(rows) + "\n")
            lab = pag._labels(tmp, {"end_P1": "x"}, None)
            spans = [(s["from"], s["to"], s["label"]) for s in lab["runs"]["end_P1"]]
            self.assertEqual(spans, [(0.0, 0.5, "ignore"), (1.0, 9.5, "end_P1")])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
