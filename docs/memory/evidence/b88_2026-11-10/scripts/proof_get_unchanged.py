#!/usr/bin/env python3
"""B88: the GET ps2-patches (B80's, kept) answers byte for byte as HEAD's, through the companion's HTTP server, on B83's
tree; then details reads it back the same. usage: proof_get_unchanged.py <HEAD copy> <B88 copy>"""
import functools, json, os, subprocess, sys
from pathlib import Path
head, b88 = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(b88 / "tests/client_contract")); sys.path.insert(0, str(b88 / "tests/art_systems"))
import test_contract as t, test_b83 as b83  # noqa: E402
outs = []
for code in (head, b88):
    orig = b83.b82.make_tree
    b83.b82.make_tree = functools.partial(orig, code)
    try:
        root, ids = b83.tree()
    finally:
        b83.b82.make_tree = orig
    gid = ids[("ps2", "Delta Force Ops (USA)")]
    calls = [{"path": "/plugins/games/ps2-patches", "method": "GET", "params": [], "query": f"id={gid}&ws=1&ni=0&fps60=1"},
             {"path": "/plugins/games/details", "method": "GET", "params": [], "query": f"id={gid}"}]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")}; env.update(t.FLAGS)
    r = subprocess.run([sys.executable, "-I", "-B", "-c", t.SERVER_CHILD, str(root), json.dumps(calls),
                        json.dumps({"default": gid, "ps2": gid})], cwd=root, env=env, capture_output=True, text=True)
    res = json.loads(r.stdout.strip().splitlines()[-1])
    outs.append([(x["status"], x["body"].replace(str(root), "<root>")) for x in res])
print("GET ps2-patches:", "SAME" if outs[0][0] == outs[1][0] else "DIFF", outs[0][0][0], "/", outs[1][0][0])
print("details after it (ps2_patches):", "SAME" if json.loads(outs[0][1][1]).get("ps2_patches") == json.loads(outs[1][1][1]).get("ps2_patches") else "DIFF",
      json.loads(outs[1][1][1]).get("ps2_patches"))
