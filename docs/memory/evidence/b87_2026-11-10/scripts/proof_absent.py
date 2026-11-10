#!/usr/bin/env python3
"""B87's absent proof: PRIVYHUB_CHEAT_READY=0 on B87's code = HEAD's code, on the same fixture trees (test_b87's: the
fake RetroArch on loopback). Compared byte for byte: the session's rows, the error, the staged files, the fake's
counts, for a PS1 launch, a slow N64 launch and a dotted N64 title.
usage: proof_absent.py <HEAD copy> <B87 copy>"""
import functools, json, sys
from pathlib import Path
head, b87 = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(b87 / "tests/b87_cheat_ready")); sys.path.insert(0, str(b87 / "tests/art_systems"))
import test_b87 as t  # noqa: E402
b82 = t.b85.b83.b82
orig = b82.make_tree
def run(code, env, which, index, **fake):
    b82.make_tree = functools.partial(orig, code)
    try:
        root, ids, dotted = t.tree()
    finally:
        b82.make_tree = orig
    gid = {"ps1": ids[t.b85.PS1_TITLE], "n64": ids[t.b85.N64_TITLE], "dotted": dotted}[which]
    out = t.launch(root, env, gid, index, **fake)
    out.pop("elapsed", None); out.pop("popen", None); out.pop("reconcile_alive", None)
    return json.dumps(out, sort_keys=True)
cases = [("PS1, the core runs at once", "ps1", 2, {"load_at": 0.0, "run_at": 0.0}),
         ("N64, the port up 1.5 s before the core runs", "n64", 3, {"load_at": 0.05, "run_at": 1.5}),
         ("a dotted N64 title", "dotted", 2, {"load_at": 0.05, "run_at": 0.0})]
diffs = 0
for label, which, index, fake in cases:
    a = run(head, t.FLAGS, which, index, **fake)
    b = run(b87, t.OFF, which, index, **fake)
    same = a == b
    diffs += not same
    print(f"{'SAME' if same else 'DIFF'}  {label}: HEAD vs B87 with PRIVYHUB_CHEAT_READY=0 ({len(a)} bytes)"
          + ("" if same else f"\n  HEAD {a[:300]}\n  B87  {b[:300]}"))
print("DIFFS", diffs)
