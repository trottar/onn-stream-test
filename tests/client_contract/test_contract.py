#!/usr/bin/env python3
"""B88 (host): the client ↔ hub contract — every call the onn makes, through the hub's real HTTP server.

`calls.json` lists every hub call in the client's source (path, method, parameter names). Two checks:
- **the source check** (`scan.py`): every hub path literal in the client's `.kt` sources is in the list with its method,
  and every literal the list names is still in the source;
- **the server check:** a child `python3 -I` on a fixture tree (B82's builder: its own companion/, a fixture library)
  imports the companion's own `privyhub_service` (the plugin registry as the companion builds it), serves its
  `PrivyHubRequestHandler` on a `ThreadingHTTPServer` at 127.0.0.1:0, and sends every call with the client's method and
  parameters. Nothing starts: every process the hub would launch is a fake `Popen`, the stream manager's calls answer
  empty, network beyond loopback is blocked. Asserted: no 404, no 405, no "Unknown … action".

    python3 -m unittest discover -s tests/client_contract -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tests" / "art_systems"))
import _tmp_cleanup  # noqa: E402,F401  (art_systems' helper: this run's temp dirs removed at exit)
import scan  # noqa: E402
import test_b82 as b82  # noqa: E402

CALLS = json.loads((HERE / "calls.json").read_text())
# the hub's adopted switches that add routes: the three systems and the movie player's retry log (B35, adopted;
# without it /diagnostics/vod-client is not served at all)
FLAGS = {**b82.FLAGS, "PRIVYHUB_VOD_LOG": "1"}

SERVER_CHILD = r'''
import json, os, socket, subprocess, sys, threading, time, types, urllib.request, urllib.error
from pathlib import Path
root = Path(sys.argv[1]).resolve()
calls = json.loads(sys.argv[2])
ids = json.loads(sys.argv[3])
_connect = socket.socket.connect
def _guard(self, addr, *a, **k):
    if isinstance(addr, tuple) and addr[0] not in ("127.0.0.1", "localhost", "::1"):
        raise OSError("network beyond loopback blocked by the test")
    return _connect(self, addr, *a, **k)
socket.socket.connect = _guard
class FakeProc:
    pid = 999999999; returncode = None; stdin = None; stdout = None; stderr = None
    def __init__(self, *a, **k): pass
    def poll(self): return self.returncode
    def wait(self, timeout=None): self.returncode = 0; return 0
    def terminate(self): self.returncode = -15
    def kill(self): self.returncode = -9
    def communicate(self, *a, **k): self.returncode = 0; return (b"", b"")
_RealPopen = subprocess.Popen
subprocess.Popen = FakeProc
def _run(cmd, *a, **k):
    if isinstance(cmd, (list, tuple)) and cmd and str(cmd[0]) == "7z":     # the bundles' reader (local, read-only)
        p = _RealPopen(list(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(timeout=k.get("timeout") or 30)
        return types.SimpleNamespace(returncode=p.returncode, stdout=out, stderr=err)
    return types.SimpleNamespace(returncode=1, stdout=b"" if not k.get("text") else "", stderr="")
subprocess.run = _run
sys.path.insert(0, str(root / "companion"))
import privyhub_service as svc
from plugins import PLUGINS
g = PLUGINS["games"]
g._metadata_reconcile_thread.join(60)
class Inert:
    """The stream manager without a stream: every call answers an empty dict."""
    def __getattr__(self, name): return Inert()
    def __call__(self, *a, **k): return {}
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __bool__(self): return False
g._native_stream = Inert()
from http.server import ThreadingHTTPServer
httpd = ThreadingHTTPServer(("127.0.0.1", 0), svc.PrivyHubRequestHandler)
threading.Thread(target=httpd.serve_forever, daemon=True).start()
port = httpd.server_address[1]
values = {"id": ids.get("default"), "q": "made", "view": "search", "mode": "single", "profile": "default",
          "enabled": "0", "cheat_source": "0", "cheat_indexes": "0", "ws": "1", "ni": "0", "fps60": "0", "slot": "1",
          "replace": "0", "disc": "1", "players": "2", "name": "Contract", "profile_id": "contract",
          "mapping": "{}", "sequence": "1", "interval_ms": "1000", "last_output_age_ms": "0", "reason": "test",
          "age_ms": "0"}
results = []
for c in calls:
    params = {p: values[p] for p in c["params"] if p in values}
    if c["path"].endswith("/ps2-patches"):
        params["id"] = ids["ps2"]
    query = "&".join(f"{k}={urllib.request.quote(str(v))}" for k, v in params.items() if v is not None)
    url = f"http://127.0.0.1:{port}{c['path']}" + (f"?{query}" if query else "")
    body = b"{}" if c["method"] == "POST" else None
    req = urllib.request.Request(url, data=body, method=c["method"],
                                 headers={"Content-Type": "application/json"} if body else {})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            status, text = r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode(errors="replace")
    except Exception as e:
        status, text = -1, type(e).__name__ + ": " + str(e)
    if c.get("query") is not None:
        url = f"http://127.0.0.1:{port}{c['path']}?{c['query']}"
        req = urllib.request.Request(url, data=body, method=c["method"],
                                     headers={"Content-Type": "application/json"} if body else {})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                status, text = r.status, r.read().decode(errors="replace")
        except urllib.error.HTTPError as e:
            status, text = e.code, e.read().decode(errors="replace")
    results.append({"path": c["path"], "method": c["method"], "status": status,
                    "body": text[:4000] if c.get("query") is not None else None,
                    "unknown": ("Unknown" in text and "action" in text) or "Unknown plugin" in text,
                    "error": (json.loads(text).get("error") if text.startswith("{") else None) if status != 200 else None})
httpd.shutdown()
print(json.dumps(results))
'''


def serve_all(code_root: Path = ROOT, flags: dict | None = None) -> list[dict]:
    """Every call in calls.json against the companion's own HTTP server built from `code_root`'s companion/."""
    root = b82.make_tree(code_root)
    games = b82.scan(root, FLAGS)["games"]
    ids = {"default": next(g[2] for g in games if g[0] == "snes"), "ps2": next(g[2] for g in games if g[0] == "ps2")}
    env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    env.update(FLAGS if flags is None else flags)
    r = subprocess.run([sys.executable, "-I", "-B", "-c", SERVER_CHILD, str(root), json.dumps(CALLS["calls"]),
                        json.dumps(ids)], cwd=root, env=env, capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


class SourceCheck(unittest.TestCase):
    def test_every_hub_call_in_the_source_is_in_the_list_and_back(self):
        rows = scan.scan(ROOT / "PrivyHub/app/src/main/java")
        listed = {(c["path"], c["method"]) for c in CALLS["calls"]}
        listed_paths = {c["path"] for c in CALLS["calls"]}
        missing = []
        for r in rows:
            if "$" in r["path"]:
                key = next((t for t in CALLS["templates"] if t.startswith(r["path"])), None)
                if key is None:
                    missing.append(r)
            elif r["method"] == "?":
                if r["path"] not in listed_paths:
                    missing.append(r)
            elif (r["path"], r["method"]) not in listed:
                missing.append(r)
        self.assertEqual(missing, [], "calls in the client's source that calls.json lacks")
        scanned = {r["path"] for r in rows}
        stale = [c for c in CALLS["calls"] if c["source"] == "literal" and c["path"] not in scanned]
        self.assertEqual(stale, [], "calls.json names a literal the source no longer has")

    def test_the_check_sees_a_new_call(self):
        tmp = Path(__import__("tempfile").mkdtemp(prefix="b88_scan_"))
        (tmp / "X.kt").write_text('val u = "http://$host:$CONTROL_PORT/plugins/games/made-up-action?id=1"\n'
                                  'fun f() { httpPost(u) }\n')
        rows = scan.scan(tmp)
        self.assertEqual([(r["path"]) for r in rows], ["/plugins/games/made-up-action"])
        self.assertNotIn("/plugins/games/made-up-action", {c["path"] for c in CALLS["calls"]})


def ps2_round_trip(code_root: Path = ROOT) -> list[dict]:
    """B83's tree (a fake PCSX2 AppImage holding a real patches.zip; PCSX2's log of an earlier launch): the onn's
    Save (POST ps2-patches, ws=1) then the details the onn reads (GET details), through the HTTP server."""
    import functools
    import test_b83 as b83
    orig = b83.b82.make_tree
    b83.b82.make_tree = functools.partial(orig, code_root)
    try:
        root, ids = b83.tree()
    finally:
        b83.b82.make_tree = orig
    gid = ids[("ps2", "Delta Force Ops (USA)")]
    calls = [{"path": "/plugins/games/ps2-patches", "method": "POST", "params": [], "query": f"id={gid}&ws=1&ni=0&fps60=0"},
             {"path": "/plugins/games/details", "method": "GET", "params": [], "query": f"id={gid}"}]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}
    env.update(FLAGS)
    r = subprocess.run([sys.executable, "-I", "-B", "-c", SERVER_CHILD, str(root), json.dumps(calls),
                        json.dumps({"default": gid, "ps2": gid})], cwd=root, env=env, capture_output=True, text=True,
                       timeout=900)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


class Ps2PatchesRoundTrip(unittest.TestCase):
    def test_the_onns_save_answers_and_details_reads_it_back(self):
        save, details = ps2_round_trip()
        self.assertEqual(save["status"], 200, save)
        self.assertEqual(json.loads(save["body"])["ps2_patches"], {"available": ["ws", "60"], "on": ["ws"]})
        self.assertEqual(details["status"], 200, details)
        self.assertEqual(json.loads(details["body"])["ps2_patches"], {"available": ["ws", "60"], "on": ["ws"]})


class Server(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = serve_all()

    def test_every_call_is_served(self):
        bad = [r for r in self.results if r["status"] in (404, 405) or r["unknown"] or r["status"] == -1]
        self.assertEqual(bad, [], json.dumps(bad, indent=1))
        self.assertEqual(len(self.results), len(CALLS["calls"]))

    def test_ps2_patches_saved_on_post_and_read_back_by_details(self):
        r = next(x for x in self.results if x["path"].endswith("/ps2-patches"))
        self.assertNotIn(r["status"], (404, 405))
        self.assertFalse(r["unknown"])


if __name__ == "__main__":
    unittest.main()
