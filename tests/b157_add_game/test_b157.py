#!/usr/bin/env python3
"""B157 (host): the add-a-game tool (`tools/party_add_game.py`) — through the real HTTP server on loopback.

B114's harness, its `b157` mode: a made-up two-player PS1 title (T90, `winner`) and a made-up four-player N64 title
(T97, `places`), their "saves" made-up states in the users' own slots (the slot index as the hub keeps it), the
pictures made-up (`fake_capture.py`); register -> learn -> bench -> close against the companion and B103's fake
RetroArch (the fake shows the screen a loaded state names). Shown: **the whole path PASS** for both; **each gate
failing with its cell named** — a missing state (register), an ending that reads as another's class (learn), a start
not PAUSED, a file changed, a reload (bench); **refused** without the stage before and after its inputs changed; **run
twice -> the same bytes, nothing rewritten**; no run-time name (title, id, path) in anything written or printed.
`SoloReads`: solo's lines (B162: on a made-up hub that takes the one-title setting), then its read of made-up logs
(B162: with a launch log for its title) — PASS, and each bar failing (a switch over 1.6 s, the sound
not back, the band outside a practice, the board's lines out of order, a winner the user did not name). `Described`:
**T88 and T89 from the hub's rules folder as it is, read only (`--check`): register and learn PASS, nothing written**
(skipped where there is no such folder). Temp dirs removed.

    python3 -m unittest discover -s tests/b157_add_game -v
"""
from __future__ import annotations

import io
import contextlib
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for sub in ("b114_party_minigame_hang", "b124_party_four_seats", "b123_h7_n64_start"):
    sys.path.insert(0, str(ROOT / "tests" / sub))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools"))
import test_b114 as b114  # noqa: E402
import test_b124 as b124  # noqa: E402
import fake_capture as fc  # noqa: E402
import made_up_hub  # noqa: E402  (B162: solo's one-title setting needs a hub that takes it)

BARS: dict = {}                                     # the mutation runs leave this empty; a test may set a bar


def extra(work, frames):
    import numpy as np
    rng = np.random.default_rng(157)
    for tok in ("s4start", "s4other") + tuple(f"s4r{r}" for r in fc.ROWS):
        for i in range(6):
            fc.picture(tok, i, rng).save(frames / f"{tok}_{i}.png")
    return {"n64_id": b124.IDS[b114.b85.N64_TITLE], "tools": str(ROOT / "tools"), "fake_dir": str(HERE), "bars": BARS}


class WholePath(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root, ids = b114.b99.tree()
        try:
            b124.IDS.clear()
            b124.IDS.update(ids)
            cls.s = b114.run(root, b114.BOTH, ids, "b157", timeout=1500, extra=extra)["steps"]
        finally:
            shutil.rmtree(root, ignore_errors=True)

    def test_0_two_player_whole_path(self):
        s = self.s
        self.assertIsNone(s.get("b157_error"), s.get("b157_error"))
        self.assertEqual(s["t90_learn_first"]["rc"], 2, s["t90_learn_first"])          # refused before register
        self.assertEqual(s["t90_reg"]["rc"], 0, s["t90_reg_v"])
        self.assertEqual(s["t90_learn"]["rc"], 0, s["t90_learn_v"])
        self.assertEqual(s["t90_bench"]["rc"], 0, s["t90_bench_v"])
        self.assertEqual(s["t90_close"]["rc"], 0, s["t90_close_v"])
        self.assertEqual(s["t90_bench_v"]["cells"]["end_P1: winner"], 1)
        self.assertEqual(s["t90_bench_v"]["cells"]["end_P2: winner"], 2)

    def test_1_four_player_whole_path(self):
        s = self.s
        self.assertEqual(s["t97_reg"]["rc"], 0, s["t97_reg_v"])
        self.assertEqual(s["t97_learn"]["rc"], 0, s["t97_learn_v"])
        self.assertEqual(s["t97_bench"]["rc"], 0, s["t97_bench_v"])
        self.assertEqual(s["t97_close"]["rc"], 0, s["t97_close"])

    def test_2_a_missing_state(self):
        self.assertEqual(self.s["t90_reg_missing"]["rc"], 1)
        self.assertIn("kept states present", self.s["t90_reg_missing_v"]["bad"])
        self.assertEqual(self.s["t90_reg_missing_v"]["cells"]["missing"], ["end_P2"])

    def test_3_an_ending_read_as_another(self):
        self.assertEqual(self.s["t91_reg"]["rc"], 0)
        self.assertEqual(self.s["t91_learn"]["rc"], 1)
        bad = self.s["t91_learn_v"]["bad"]
        self.assertTrue("every class separable" in bad or "end_P2: ended as itself" in bad, bad)

    def test_4_the_bench_gates(self):
        s = self.s
        for tag, cell in (("notpaused", "PAUSED at every read to the go"), ("filechanged", "every file after = before"),
                          ("reload", "no reload before the go")):
            self.assertEqual(s[f"t90_bench_{tag}"]["rc"], 1, (tag, s[f"t90_bench_{tag}_v"]))
            self.assertIn(cell, s[f"t90_bench_{tag}_v"]["bad"], tag)

    def test_5_refused_after_the_inputs_changed(self):
        self.assertEqual(self.s["t90_bench_changed"]["rc"], 2)
        self.assertIn("REFUSED", self.s["t90_bench_changed"]["out"])

    def test_6_run_twice_nothing_rewritten(self):
        self.assertEqual(self.s["t90_learn_again"]["rc"], 0)
        self.assertEqual(self.s["t90_twice_same"], [True, True, True])

    def test_7_no_run_time_name_written_or_printed(self):
        text = self.s["texts"].casefold()
        for n in self.s["names"]:
            self.assertNotIn(str(n).casefold(), text)
        self.assertTrue(all(p.startswith("evidence/") for p in self.s["written"]))


def _tool(*argv) -> tuple[int, str]:
    import party_add_game as pag
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = pag.main([str(a) for a in argv])
    return rc, buf.getvalue()


class SoloReads(unittest.TestCase):
    """solo's read on made-up logs (the hub's rows, the onn's heartbeats, the encoder's lines, the board's log)."""

    def setUp(self):
        import party_add_game as pag
        self.pag = pag
        self.tmp = Path(tempfile.mkdtemp(prefix="b157_solo_"))
        self.env = {"PRIVYHUB_ADD_GAME_HOME": str(self.tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(self.tmp / "ev"),
                    "PRIVYHUB_ADD_GAME_PROJECT": str(self.tmp / "proj"), "PRIVYHUB_H7_RULES": str(self.tmp / "rules"),
                    "PRIVYHUB_ADD_GAME_DROPINS": str(self.tmp / "dropins"), "PRIVYHUB_ADD_GAME_SYSTEMCTL": "true",
                    "PRIVYHUB_ADD_GAME_HUB": "http://127.0.0.1:9", "PRIVYHUB_ADD_GAME_KEPT_ROOT": str(self.tmp / "kept")}
        self.hub = made_up_hub.MadeUpHub([{"id": "mg_1", "players": 2, "title": "", "game": "madeupgame1"},
                                          {"id": "mg_2", "players": 2, "title": "", "game": "madeupgame2"}])
        self.env["PRIVYHUB_ADD_GAME_HUB"] = self.hub.url
        (self.tmp / "dropins").mkdir()                       # never the hub's own: eighteen made-up lines
        for i in range(18):
            (self.tmp / "dropins" / f"line{i:02d}.conf").write_text(f"[Service]\nEnvironment=PRIVYHUB_LINE{i:02d}=1\n")
        self.old = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)
        (self.tmp / "proj/logs/games").mkdir(parents=True)
        (self.tmp / "rules").mkdir()
        b = {"code": "T93", "game": "madeupgame1", "players": 2, "system": "n64", "result": "winner",
             "register_inputs": "r", "title": "", "relative_path": "", "content": ""}
        (self.tmp / "home/T93").mkdir(parents=True)
        (self.tmp / "home/T93/binding.json").write_text(json.dumps(b))
        ev = self.tmp / "ev/T93"
        ev.mkdir(parents=True)
        (ev / "bench.json").write_text(json.dumps({"verdict": "PASS", "inputs": pag.bench_inputs("T93", b)}))

    def tearDown(self):
        self.hub.close()
        for k, v in self.old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def logs(self, seconds=(1.2, 1.3, 1.25, 1.3), gap=600, depth=3, band_in_real=False, board_order=True, winner=1):
        g = self.tmp / "proj/logs/games"
        rows, hb, enc = [], [], []
        t = 1_800_000_000.0
        rows.append({"step": "minigame_launch", "keys_written": True, "time_unix": t})
        kinds = ["practice", "board", "real", "board"]
        for i, (sec, kind) in enumerate(zip(seconds, kinds)):
            t += 20
            rows.append({"step": "minigame_stream", "planned": True, "switched": True, "seconds": sec, "time_unix": t,
                         "window": "board" if kind == "board" else "minigame"})
            if kind == "practice":
                rows.append({"step": "minigame_playing", "practice": True, "time_unix": t})
            enc.append("encoder argv: ffmpeg -vf x" + ((",drawtext=" + self.pag.BAND) if kind == "practice" or
                                                      (band_in_real and kind == "real") else ""))
            for k in range(1, 6):
                import datetime as dt
                ts = dt.datetime.fromtimestamp(t + k * 0.9, dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                hb.append({"received_at_utc": ts, "audio_queue_depth": depth, "audio_underruns": k,
                           "audio_max_arrival_gap_ms": gap})
        sc = [1, 0] if winner == 1 else [0, 1]
        rows.append({"step": "minigame_ended", "class": "end_P1", "scores": sc, "winner": winner, "time_unix": t + 5})
        (g / "party.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        (g / "native_stream_heartbeat.log").write_text("\n".join(json.dumps(r) for r in hb) + "\n")
        (g / "native_video_alpha.log").write_text("\n".join(enc) + "\n")
        lines = ["cards 1, chose 0", "practice", "load screen again", "start", "scores [1, 0] for seats 1,2"]
        if not board_order:
            lines = [lines[0], lines[3], lines[1], lines[2], lines[4]]
        (g / "20990101-000000-party.log").write_text("".join(f"PrivyParty: hub mini game: {x}\n" for x in lines))
        import time as _t                                   # B162: the title's own launch, as the manager logs it
        (g / (_t.strftime("%Y%m%d-%H%M%S") + "-madeupgame1.log")).write_text("made-up launch\n")

    def read(self, **kw):
        (self.tmp / "home/T93/solo_mark.json").write_text(json.dumps(
            {"party": 0, "heartbeat": 0, "video": 0, "video_bytes": 0, "board_log": None, "board_lines": 0}))
        self.logs(**kw)
        return _tool("solo", "T93", "--read", "--winner", 1)

    def test_lines_then_waiting(self):
        rc, text = _tool("solo", "T93")
        self.assertEqual(rc, 3)
        self.assertEqual(len(list((self.tmp / "dropins").glob("*.conf"))), 20)      # the two flags, made-up folder
        self.assertTrue(all(ln.startswith(("YOU, now:", "solo T93: WAITING")) for ln in text.strip().splitlines()))

    def test_pass(self):
        rc, text = self.read()
        self.assertEqual(rc, 0, text + (self.tmp / "ev/T93/solo.md").read_text())

    def test_described_title_goes_to_solo(self):
        """A title already in the rules folder (T88's way): register and learn written from the folder as it is,
        bench refused (its bench was its own task's), solo's lines after learn's PASS."""
        sys.path.insert(0, str(ROOT / "tests" / "b103_h7_minigame"))
        import test_b103 as b103
        work = self.tmp / "fx"
        work.mkdir()
        _frames, spec_dir, js = b103.fixtures(work)
        rules = self.tmp / "rules"
        shutil.copyfile(spec_dir / js["arrays"], rules / "madeupgame2.endscreen.npz")
        js["arrays"] = "madeupgame2.endscreen.npz"
        (rules / "madeupgame2.endscreen.json").write_text(json.dumps(js))
        (rules / "madeupgame2.state").write_text("made-up begin")
        (rules / "madeupgame2.party.json").write_text(json.dumps({"players": 2, "scores": {"end_P1": [1, 0],
                                                                                            "end_P2": [0, 1]}}))
        args = ("T96", "--players", 2, "--system", "ps1", "--result", "winner", "--rules-players", 2)
        self.assertEqual(_tool("register", *args)[0], 0)
        self.assertEqual(_tool("learn", "T96")[0], 0, _tool("learn", "T96")[1])
        self.assertEqual(_tool("bench", "T96")[0], 2)
        rc, text = _tool("solo", "T96")
        self.assertEqual(rc, 3, text)
        self.assertTrue((self.tmp / "ev/T96/learn.json").is_file())
        self.assertNotIn("madeupgame2", (self.tmp / "ev/T96/learn.json").read_text() + text)

    def test_no_restart_in_the_users_session(self):
        """A made-up hub on loopback answering that a client's stream is up: solo refuses before any flag is written."""
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
            rc, text = _tool("solo", "T93")
        finally:
            srv.shutdown()
        self.assertEqual(rc, 2, text)
        self.assertIn("stream is up", text)
        self.assertEqual(len(list((self.tmp / "dropins").glob("*.conf"))), 18)

    def test_each_bar(self):
        for kw, cell in (({"seconds": (1.2, 1.8, 1.25, 1.3)}, "every planned switch's seconds"),
                         ({"gap": 1500}, "audio_max_arrival_gap_ms at each switch"),
                         ({"depth": 0}, "S: sound within 4 s of each switch, underruns rising <= 20 a row"),
                         ({"band_in_real": True}, "the band in the practices' encoder lines only"),
                         ({"board_order": False}, "the board's lines in order"),
                         ({"winner": 2}, "the hub's result = the winner the user named")):
            rc, _ = self.read(**kw)
            v = json.loads((self.tmp / "ev/T93/solo.json").read_text())
            self.assertEqual(rc, 1, kw)
            self.assertIn(cell, [c["cell"] for c in v["cells"] if not c["met"]], kw)


class BarsAndGuard(unittest.TestCase):
    """Every bar is the number its source gives (a loosened bar is caught); the guard refuses a run-time name."""

    def test_bars_from_their_sources(self):
        import party_add_game as pag
        sys.path.insert(0, str(ROOT / "companion"))
        import h7_minigame as h7m
        B = {k: v[0] for k, v in pag.BARS.items()}
        self.assertEqual(B["start_within_s"], h7m.RECOGNISE_S)
        self.assertEqual((B["switch_s_max"], B["arrival_gap_ms_max"]), (1.6, 1200))          # B153's bounds
        self.assertEqual((B["sound_within_s"], B["underrun_rise_max"]), (4.0, 20))             # B150's S
        self.assertEqual((B["ended_within_s"], B["ended_after_load_s"], B["prepare_s_max"]), (2.0, 8.0, 6.0))
        self.assertEqual((B["wrong_class_max"], B["other_as_screen_max"], B["places_wrong_max"]), (0, 0, 0))
        self.assertEqual((B["unknown_share_max"], B["paused_reads_min"]), (0.105, 5))
        self.assertEqual((B["flag_lines_task"], B["flag_lines_found"]), (20, 18))
        self.assertEqual(B["margin_needed_min"], 0.0796)
        rules = Path.home() / "privyhub_h7" / "rules"                 # read only, where the hub keeps them
        specs = [json.loads(p.read_text()) for p in rules.glob("*.endscreen.json")] if rules.is_dir() else []
        if len(specs) == 2:
            m = [x.get("margin_needed") or (x.get("places") or {}).get("margin_needed") for x in specs]
            self.assertEqual(B["margin_needed_min"], min(float(v) for v in m))

    def test_ps1_four_player_setting(self):
        import party_add_game as pag
        tmp = Path(tempfile.mkdtemp(prefix="b157_ps1_"))
        old = os.environ.get("PRIVYHUB_ADD_GAME_PROJECT")
        os.environ["PRIVYHUB_ADD_GAME_PROJECT"] = str(tmp)
        try:
            f = tmp / "data/games/retroarch/controller_overrides.json"
            f.parent.mkdir(parents=True)
            f.write_text(json.dumps({"version": 1, "games": {"game_ps1_made_up_a": {"ps1_multitap": "port1"},
                                                             "game_ps1_made_up_b": {"controller_profile": "x"}}}))
            self.assertTrue(pag.ps1_four_on("game_ps1_made_up_a"))
            self.assertFalse(pag.ps1_four_on("game_ps1_made_up_b"))
            self.assertFalse(pag.ps1_four_on("game_ps1_made_up_c"))
        finally:
            if old is None:
                os.environ.pop("PRIVYHUB_ADD_GAME_PROJECT", None)
            else:
                os.environ["PRIVYHUB_ADD_GAME_PROJECT"] = old
            shutil.rmtree(tmp, ignore_errors=True)

    def test_guard_refuses_a_name(self):
        import party_add_game as pag
        g = pag.Guard()
        g.add("Made Up Name (USA)", "game_ps1_0123456789abcdef")
        with self.assertRaises(pag.Refused):
            g.check("a line with made up name (usa) in it")
        with self.assertRaises(pag.Refused):
            g.check('{"x": "game_ps1_0123456789abcdef"}')
        self.assertEqual(g.check("register T90: PASS"), "register T90: PASS")


class Described(unittest.TestCase):
    """T88 and T89 from the hub's own rules folder, read only: register and learn --check PASS, nothing written."""

    def test_t88_t89_check(self):
        rules = Path.home() / "privyhub_h7" / "rules"
        if not rules.is_dir() or len(list(rules.glob("*.party.json"))) != 2:
            self.skipTest("no kept rules folder here")
        before = {p.name: (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()) for p in rules.iterdir()}
        tmp = Path(tempfile.mkdtemp(prefix="b157_check_"))
        old = {k: os.environ.get(k) for k in ("PRIVYHUB_ADD_GAME_HOME", "PRIVYHUB_ADD_GAME_EVIDENCE", "PRIVYHUB_H7_RULES")}
        os.environ.update({"PRIVYHUB_ADD_GAME_HOME": str(tmp / "home"), "PRIVYHUB_ADD_GAME_EVIDENCE": str(tmp / "ev"),
                           "PRIVYHUB_H7_RULES": str(rules)})
        try:
            for args in (("T88", "--players", 2, "--system", "ps1", "--result", "winner", "--rules-players", 2),
                         ("T89", "--players", 4, "--system", "n64", "--result", "places", "--rules-players", 4)):
                for stage in ("register", "learn"):
                    rc, text = _tool(stage, *args, "--check")
                    self.assertEqual(rc, 0, text)
                    self.assertIn("PASS", text)
            self.assertFalse((tmp / "home").exists() or (tmp / "ev").exists())
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
            shutil.rmtree(tmp, ignore_errors=True)
        after = {p.name: (p.stat().st_mtime_ns, hashlib.sha256(p.read_bytes()).hexdigest()) for p in rules.iterdir()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
