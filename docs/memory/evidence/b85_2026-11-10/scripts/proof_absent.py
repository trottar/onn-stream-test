#!/usr/bin/env python3
"""B85's absent proof: the same fixture tree (test_b85's) built once with HEAD's code and once with B85's; the plugin as
the companion constructs it, in a child per run (network blocked). Compared byte for byte (json, sorted keys):
the `cheat-catalog` reply with PRIVYHUB_CHEAT_CLEAN=0 and with raw=1 vs HEAD's; the launch's staged indexes with the
knob 0 and with cheat_raw=1 vs HEAD's; the heading-row file: HEAD's refusal = B85's with the knob 0.
usage: proof_absent.py <HEAD copy> <B85 copy>"""
import functools, json, sys
from pathlib import Path
head, b85 = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(b85 / "tests/art_systems"))
import test_b85 as t   # noqa: E402
orig = t.b83.b82.make_tree
def tree(code, rows):
    t.b83.b82.make_tree = functools.partial(orig, code)
    try:
        return t.tree(rows)
    finally:
        t.b83.b82.make_tree = orig
def child(root, env, mode, args):
    old = t.b83.CHILD; t.b83.CHILD = t.CHILD
    try:
        r, attempts, _ = t.b83.run(root, env, mode, args)
    finally:
        t.b83.CHILD = old
    return r, attempts
F = t.FLAGS; OFF = {**F, "PRIVYHUB_CHEAT_CLEAN": "0"}
def norm(root, r):
    if r.returncode:
        return "REFUSED: " + r.stderr.strip().splitlines()[-1].split(":", 1)[-1].strip()
    out = json.loads(r.stdout.strip().splitlines()[-1])
    out.pop("popen", None); out.pop("reconcile_alive", None)
    return json.dumps(out, sort_keys=True).replace(str(root), "<root>")
cases = [
    ("cheat-catalog, knob 0", t.N64_ROWS_NO_HEADING, F, OFF, "catalog", lambda g: {"id": g, "query": f"id={g}"}),
    ("cheat-catalog, raw=1 (knob on)", t.N64_ROWS_NO_HEADING, F, F, "catalog", lambda g: {"id": g, "query": f"id={g}&raw=1"}),
    ("launch 5,0, knob 0", t.N64_ROWS_NO_HEADING, F, OFF, "post_launch",
     lambda g: {"id": g, "query": f"id={g}&cheat_source=0&cheat_indexes=5,0"}),
    ("launch 5,0, cheat_raw=1 (knob on)", t.N64_ROWS_NO_HEADING, F, F, "post_launch",
     lambda g: {"id": g, "query": f"id={g}&cheat_source=0&cheat_indexes=5,0&cheat_raw=1"}),
    ("cheat-catalog of a file with a heading row, knob 0", t.N64_ROWS, F, OFF, "catalog", lambda g: {"id": g, "query": f"id={g}"}),
]
diffs = 0
for label, rows, env_head, env_b85, mode, args in cases:
    texts = []
    for code, env in ((head, env_head), (b85, env_b85)):
        root, ids = tree(code, rows)
        gid = ids[t.N64_TITLE]
        r, attempts = child(root, env, mode, args(gid))
        texts.append((norm(root, r), attempts))
    same = texts[0][0] == texts[1][0]
    diffs += not same
    print(f"{'SAME' if same else 'DIFF'}  {label}: {len(texts[0][0])} bytes; network attempts HEAD {texts[0][1]} / B85 {texts[1][1]}"
          + ("" if texts[0][0].startswith("{") else f" ({texts[0][0][:60]})"))
print("DIFFS", diffs)
