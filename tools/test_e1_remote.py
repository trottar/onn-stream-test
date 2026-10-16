#!/usr/bin/env python3
"""G4-P1: the suite's `--remote` row.

    python3 -m unittest tools/test_e1_remote.py -v

The argument parsing; the endpoint's class and hash from /proc/net/tcp
text (the addresses are built from integers here and must never appear in
any output); the preflight refusing with the flags absent; a whole run
against a fake suite (no stream, no companion, no sleep) whose log and
summary must carry the hash and never the address; and the suite's
dispatch, guarded by `--remote`.
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
from types import SimpleNamespace
from unittest import mock

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import e1_remote as R  # noqa: E402

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
