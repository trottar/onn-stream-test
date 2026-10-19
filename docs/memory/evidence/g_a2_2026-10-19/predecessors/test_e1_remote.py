#!/usr/bin/env python3
"""G4-P1: the suite's `--remote` row.

    python3 -m unittest tools/test_e1_remote.py -v

The argument parsing; the endpoint's class and hash from /proc/net/tcp
text (the addresses are built from integers here and must never appear in
any output); the preflight refusing with the flags absent; a whole run
against a fake suite (no stream, no companion, no sleep) whose log and
summary must carry the hash and never the address; and the suite's
dispatch, guarded by `--remote`.

G4-P2: the counter override (written, removed, refused over an existing file,
never touching the real RetroArch tree -- the fake suite's path is a temp
directory), the sampler's `--e2`, and gate 3's keys from fixtures (`title.txt`,
`encoder.jsonl`), with `segcap` equal to E4-S5D's.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import ipaddress
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import e1_remote as R  # noqa: E402
import e1_sampler  # noqa: E402
from e1_suite import COUNTER  # noqa: E402  (a constant; nothing runs)

OVERLAY_IP = R.OVERLAY_NETWORKS[0][0x2A17]
LAN_IP = ipaddress.ip_network((0xC0A86400, 24))[23]
LOOP_IP = ipaddress.ip_address(0x7F000001)
MAPPED_OVERLAY = ipaddress.IPv6Address(b"\x00" * 10 + b"\xff\xff" + R.OVERLAY_NETWORKS[0][0x2A18].packed)


def hex4(ip, port):
    return ip.packed[::-1].hex().upper() + f":{port:04X}"


def hex6(ip6, port):
    p = ip6.packed
    return "".join(p[i:i + 4][::-1].hex().upper() for i in range(0, 16, 4)) + f":{port:04X}"


HEADER = "  sl  local_address rem_address   st tx_queue rx_queue tr tm->when retrnsmt   uid  timeout inode\n"


def tcp_text(rows):
    return HEADER + "".join(f"   {i}: {l} {r} 01 00000000:00000000 00:00000000 00000000  1000 0 0\n"
                            for i, (l, r) in enumerate(rows))


def everything_text(obj) -> str:
    return json.dumps(obj, default=str)


ADDRESS_STRINGS = [str(OVERLAY_IP), str(LAN_IP), str(R.OVERLAY_NETWORKS[0][0x2A18]),
                   hex4(OVERLAY_IP, 0).split(":")[0], hex4(LAN_IP, 0).split(":")[0]]


class Args(unittest.TestCase):
    def test_defaults(self):
        a = R.parse_args(["run", "--remote", "--out", "/tmp/x"])
        self.assertEqual((a["runs"], a["window"], a["gap"], a["wait"], a["adb"]), (3, 600, 300, 900, False))
        self.assertEqual(a["out"], Path("/tmp/x"))

    def test_values_and_adb(self):
        a = R.parse_args(["run", "--remote", "--out", "/o", "--runs", "1", "--window", "120", "--adb"])
        self.assertEqual((a["runs"], a["window"], a["adb"]), (1, 120, True))

    def test_refusals(self):
        for argv in (["run", "--remote"], ["run", "--remote", "--out", "/o", "--window", "10"],
                     ["run", "--remote", "--out"], ["run", "--remote", "--out", "/o", "--runs", "0"]):
            with self.assertRaises(ValueError):
                R.parse_args(argv)


class Endpoint(unittest.TestCase):
    def test_classes_and_hashes_only(self):
        local = (LOOP_IP, 8765)
        v4 = tcp_text([
            (hex4(ipaddress.ip_address(0), 8765), hex4(OVERLAY_IP, 51000)),
            (hex4(ipaddress.ip_address(0), 8765), hex4(LAN_IP, 51001)),
            (hex4(*local), hex4(LOOP_IP, 40000)),
            (hex4(ipaddress.ip_address(0), 22), hex4(LAN_IP, 51002)),     # another port: ignored
        ])
        v6 = tcp_text([(hex6(ipaddress.IPv6Address(0), 8765), hex6(MAPPED_OVERLAY, 51003))])
        peers = R.control_peers([v4, v6])
        self.assertEqual(sorted(peers), ["lan", "local", "overlay"])
        self.assertEqual(len(peers["overlay"]), 2)
        self.assertIn(hashlib.sha256(str(OVERLAY_IP).encode()).hexdigest()[:12], peers["overlay"])
        text = everything_text(peers)
        for a in ADDRESS_STRINGS:
            self.assertNotIn(a, text)

    def test_classify(self):
        self.assertEqual(R.classify(OVERLAY_IP), "overlay")
        self.assertEqual(R.classify(LAN_IP), "lan")
        self.assertEqual(R.classify(LOOP_IP), "local")


class Preflight(unittest.TestCase):
    def test_flags_absent_refuses_with_a_clear_line(self):
        pf = R.preflight_remote(lambda kv: False, lambda: "List of devices attached\n")
        self.assertFalse(pf["ok"])
        self.assertTrue(pf["refusal"].startswith("refusing: --remote needs the companion running with "))
        for kv in R.REQUIRED_FLAGS:
            self.assertIn(kv, pf["refusal"])
        self.assertFalse(pf["adb_device"])

    def test_one_flag_absent(self):
        pf = R.preflight_remote(lambda kv: kv == R.REQUIRED_FLAGS[0], lambda: "")
        self.assertFalse(pf["ok"])
        self.assertIn(R.REQUIRED_FLAGS[1], pf["refusal"])
        self.assertNotIn("not read back: " + R.REQUIRED_FLAGS[0], pf["refusal"])

    def test_both_flags(self):
        pf = R.preflight_remote(lambda kv: kv in R.REQUIRED_FLAGS, lambda: "List\nserial-fixture\tdevice\n")
        self.assertTrue(pf["ok"])
        self.assertTrue(pf["adb_device"])

    def test_main_refuses_without_flags(self):
        d = Path(tempfile.mkdtemp())
        pre = d / "prereg.txt"
        pre.write_text("fixture pre-registration\n")
        pre.with_suffix(".sha256").write_text(hashlib.sha256(pre.read_bytes()).hexdigest() + "  prereg.txt\n")
        E = SimpleNamespace(mainpid=lambda: 1, environ_has=lambda pid, kv: False, adb=lambda *a: "")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = R.main_remote(["run", "--remote", "--out", str(d / "o"), "--prereg", str(pre)], E)
        self.assertEqual(rc, 2)
        self.assertIn("refusing: --remote needs", out.getvalue())
        self.assertFalse((d / "o").exists())


class FakeSuite:
    """The e1_suite functions run_remote_once calls; no companion, no stream."""

    def __init__(self, tmp: Path):
        self.REPO = tmp
        self.lines: list[str] = []
        self.log = lambda *a: self.lines.append(" ".join(map(str, a)))
        self.stopped = False
        self.S = SimpleNamespace(summarize=lambda rd, t0, t1: {"host": {}, "retroarch": {"fps": 60.0}})
        # G4-P2: the home row's override constants, at a temp path (never the real RetroArch tree)
        self.TEKKEN = {"id": "game_ps1_fixture", "override": tmp / "ra" / "Beetle PSX HW" / "Tekken 3 (USA).cfg"}
        self.COUNTER = COUNTER

    def utc(self): return "2026-10-16T00:00:00.000Z"
    def mainpid(self): return 1
    def environ_has(self, pid, kv): return kv in R.REQUIRED_FLAGS
    def adb(self, *a): return "List of devices attached\n"
    def games_status(self): return {"active": not self.stopped}
    def stream_status(self): return {"active": True, "bitrate_kbps": 7000, "width": 1280, "height": 720}
    def stop_game(self): self.stopped = True; return True
    def http(self, method, path, timeout=30):
        return 200, {"overlay": {"connected": True, "path": "direct", "endpoint": "present", "endpoint_hash": "abcd1234"}}
    def heartbeat_figures(self, t0, t1): return {"rows": 0}
    def telemetry_figures(self, p, t0, t1): return {"reports": 0}
    def poll_figures(self, p, t0, t1): return {"reads": 0}

    class Poller(threading.Thread):
        def __init__(self, path, stop):
            super().__init__(daemon=True)
            self.stop = stop

        def run(self):
            self.stop.wait(1)


class WholeRun(unittest.TestCase):
    def test_hash_logged_never_the_address(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "tools").mkdir()
        E = FakeSuite(tmp)
        peers = R.control_peers([tcp_text([(hex4(ipaddress.ip_address(0), 8765), hex4(OVERLAY_IP, 51000))])])
        with mock.patch.object(R.time, "sleep", lambda s: None), \
                mock.patch.object(R, "read_control_peers", lambda: peers), \
                mock.patch.object(R.subprocess, "Popen", lambda *a, **k: SimpleNamespace(wait=lambda timeout=None: 0)):
            rec = R.run_remote_once(E, 1, tmp / "out", window=60, gap=0, wait=60, use_adb=False)
        self.assertEqual(rec["status"], "OK", rec.get("error"))
        self.assertEqual(rec["endpoint"]["class"], "overlay")
        self.assertEqual(rec["endpoint"]["hash"], hashlib.sha256(str(OVERLAY_IP).encode()).hexdigest()[:12])
        self.assertEqual(rec["teardown"]["client"], "not harvested (no adb device or --adb not given)")
        written = (tmp / "out" / "E1-PS1-STREAM-REMOTE" / "run1" / "summary.json").read_text()
        for a in ADDRESS_STRINGS:
            self.assertNotIn(a, written)
            self.assertNotIn(a, "\n".join(E.lines))
        self.assertTrue(any(rec["endpoint"]["hash"] in l for l in E.lines))

    def test_not_over_the_overlay_fails(self):
        tmp = Path(tempfile.mkdtemp())
        E = FakeSuite(tmp)
        peers = R.control_peers([tcp_text([(hex4(ipaddress.ip_address(0), 8765), hex4(LAN_IP, 51000))])])
        with mock.patch.object(R.time, "sleep", lambda s: None), \
                mock.patch.object(R, "read_control_peers", lambda: peers), \
                mock.patch.object(R.subprocess, "Popen", lambda *a, **k: SimpleNamespace(wait=lambda timeout=None: 0)):
            rec = R.run_remote_once(E, 1, tmp / "out", window=60, gap=0, wait=60, use_adb=False)
        self.assertEqual(rec["status"], "FAILED")
        self.assertIn("not reached over the overlay", rec["error"])
        self.assertTrue(E.stopped)


def run_with_popen(E, tmp, peers_ip=None, popen=None):
    peers = R.control_peers([tcp_text([(hex4(ipaddress.ip_address(0), 8765), hex4(peers_ip or OVERLAY_IP, 51000))])])
    popen = popen or (lambda *a, **k: SimpleNamespace(wait=lambda timeout=None: 0))
    with mock.patch.object(R.time, "sleep", lambda s: None), \
            mock.patch.object(R, "read_control_peers", lambda: peers), \
            mock.patch.object(R.subprocess, "Popen", popen):
        return R.run_remote_once(E, 1, tmp / "out", window=60, gap=0, wait=60, use_adb=False)


class Gate3(unittest.TestCase):
    """G4-P2: one test per new field."""

    def test_counter_override_written_then_removed(self):
        tmp = Path(tempfile.mkdtemp())
        E = FakeSuite(tmp)
        seen = {}

        def popen(argv, **k):
            seen["argv"] = argv
            seen["override_during_run"] = E.TEKKEN["override"].read_text()
            return SimpleNamespace(wait=lambda timeout=None: 0)
        rec = run_with_popen(E, tmp, popen=popen)
        self.assertEqual(rec["status"], "OK", rec.get("error"))
        self.assertEqual(rec["counter_override"], "set")
        self.assertEqual(seen["override_during_run"], COUNTER)
        self.assertTrue(any("gate 3 reads RetroArch's counter" in l for l in E.lines))   # the per-game note
        self.assertTrue(rec["teardown"]["counter_override_removed"])
        self.assertFalse(E.TEKKEN["override"].exists())

    def test_counter_extra_as_the_home_row(self):
        tmp = Path(tempfile.mkdtemp())
        E = FakeSuite(tmp)
        seen = {}

        def popen(argv, **k):
            seen["text"] = E.TEKKEN["override"].read_text()
            return SimpleNamespace(wait=lambda timeout=None: 0)
        with mock.patch.dict(R.os.environ, {"E1_COUNTER_EXTRA": 'a = "1"\\nb = "2"'}):
            run_with_popen(E, tmp, popen=popen)
        self.assertEqual(seen["text"], COUNTER + 'a = "1"\nb = "2"')

    def test_refuses_over_an_existing_file_and_leaves_it(self):
        tmp = Path(tempfile.mkdtemp())
        E = FakeSuite(tmp)
        E.TEKKEN["override"].parent.mkdir(parents=True)
        E.TEKKEN["override"].write_text("someone else's override\n")
        rec = run_with_popen(E, tmp)
        self.assertEqual(rec["status"], "FAILED")
        self.assertIn("refusing to overwrite", rec["error"])
        self.assertEqual(E.TEKKEN["override"].read_text(), "someone else's override\n")
        self.assertNotIn("counter_override_removed", rec["teardown"])

    def test_sampler_started_with_e2(self):
        tmp = Path(tempfile.mkdtemp())
        E = FakeSuite(tmp)
        seen = {}

        def popen(argv, **k):
            seen["argv"] = argv
            return SimpleNamespace(wait=lambda timeout=None: 0)
        run_with_popen(E, tmp, popen=popen)
        self.assertEqual(seen["argv"][2:], ["run", str(tmp / "out" / "E1-PS1-STREAM-REMOTE" / "run1"),
                                            "--telemetry", "--title", "--e2"])

    def test_summary_keys_present(self):
        tmp = Path(tempfile.mkdtemp())
        E = FakeSuite(tmp)
        E.S = SimpleNamespace(summarize=lambda rd, t0, t1: {"host": {}, "retroarch": {"titles": 0}})
        rec = run_with_popen(E, tmp)
        self.assertEqual(rec["key"]["retroarch"], {"titles": 0})          # the home row's key, as the home row
        g = rec["key"]["gate3"]
        self.assertEqual((g["retroarch_fps"], g["capture_fps"], g["dupdrop_per_min"]), (None, None, None))

    def fixtures(self, rd: Path):
        rd.mkdir(parents=True, exist_ok=True)
        t = 1792195200.0                                   # 2026-10-17T00:00:00Z, built from an integer
        lines = ["# xprop -spy"]
        for i in range(61):
            lines.append(f"{t + i:.3f} RetroArch Beetle PSX HW || FPS: 59.94 || Frames: {1000 + 60 * i}")
        (rd / "title.txt").write_text("\n".join(lines) + "\n")
        utc = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        rows = []
        frame, dup, drop = 5000, 3, 1
        for i in range(61):
            if i == 30:
                frame, dup, drop = 0, 0, 0                  # a counter reset (an encoder restart): its pair skipped
            frame += 60
            if i == 20:
                dup += 1
            rows.append({"at_utc": utc(t + i + (5 if i >= 45 else 0)), "records": 2, "frame": frame, "fps": 60.0,
                         "dup": dup, "drop": drop, "speed": 1.0})        # a > 3-s hole before row 45: skipped
        (rd / "encoder.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        return utc(t), utc(t + 70)

    def test_gate3_from_fixtures_and_segcap_is_e4_s5ds(self):
        rd = Path(tempfile.mkdtemp()) / "run1"
        t0, t1 = self.fixtures(rd)
        host = {"retroarch": e1_sampler.ra_fps(str(rd / "title.txt"), R._ep(t0), R._ep(t1))}
        g = R.gate3_figures(rd, host, t0, t1)
        self.assertEqual(g["retroarch_fps"], 60.0)
        self.assertEqual(g["capture_fps"], 60.0)
        spec = __import__("importlib.util").util.spec_from_file_location(
            "e4_s5d", TOOLS.parent / "docs/memory/evidence/e4_s5d_2026-10-15/e4_s5d_analysis.py")
        s5d = __import__("importlib.util").util.module_from_spec(spec)
        spec.loader.exec_module(s5d)
        self.assertEqual(R.segcap(rd, t0, t1), s5d.segcap(str(rd), {"window": {"from": t0, "to": t1}}))
        self.assertEqual((g["capture_fps"], g["dupdrop_per_min"]), R.segcap(rd, t0, t1))
        self.assertGreater(g["dupdrop_per_min"], 0)

    def test_dry_dispatch_with_no_companion_refuses_as_today(self):
        d = Path(tempfile.mkdtemp())
        pre = d / "prereg.txt"
        pre.write_text("fixture pre-registration\n")
        pre.with_suffix(".sha256").write_text(hashlib.sha256(pre.read_bytes()).hexdigest() + "  prereg.txt\n")
        E = SimpleNamespace(mainpid=lambda: None, environ_has=lambda pid, kv: False, adb=lambda *a: "",
                            TEKKEN={"override": d / "never" / "Tekken 3 (USA).cfg"}, COUNTER=COUNTER)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = R.main_remote(["run", "--remote", "--out", str(d / "o"), "--prereg", str(pre)], E)
        self.assertEqual(rc, 2)
        self.assertIn("refusing: --remote needs", out.getvalue())
        self.assertFalse((d / "o").exists())
        self.assertFalse((d / "never").exists())                         # no override before the preflight


class SuiteDispatch(unittest.TestCase):
    def test_guarded_import(self):
        src = (TOOLS / "e1_suite.py").read_text()
        tree = ast.parse(src)
        self.assertFalse([n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
                          and (getattr(n, "module", "") or "").startswith("e1_remote")])
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
        first = main.body[0]
        self.assertIsInstance(first, ast.If)
        self.assertEqual(ast.get_source_segment(src, first.test), '"--remote" in argv')

    def test_dispatch_refuses_without_prereg(self):
        import e1_suite
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = e1_suite.main(["run", "--remote", "--out", tempfile.mkdtemp()])
        self.assertEqual(rc, 2)
        self.assertIn("--prereg", out.getvalue())


if __name__ == "__main__":
    unittest.main()
