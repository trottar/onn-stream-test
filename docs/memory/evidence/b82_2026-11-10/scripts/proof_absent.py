#!/usr/bin/env python3
"""B82's absent proof: the same fixture tree (tests/art_systems/test_b82.py's make_tree) built once with HEAD's code
and once with B82's; each tool / the scan run in a child with no PRIVYHUB_ value; outputs compared byte for byte after
the tree's own path is replaced by <root>. Network blocked in every child (the test's runner).

usage: proof_absent.py <HEAD copy> <B82 copy>   (each holds companion/ tools/ tests/)"""
import json, re, sys
from pathlib import Path
head, b82 = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(b82 / "tests/art_systems"))
import test_b82 as t   # noqa: E402  (its helpers; _tmp_cleanup removes the trees at exit)

CASES = [
    ("scan", None, ()),
    ("tool", "update_game_metadata.py", ("--dry-run", "--json")),
    ("tool", "update_game_metadata.py", ("--dry-run",)),
    ("tool", "update_game_metadata.py", ("--dry-run", "--json", "--offline")),
    ("tool", "update_game_cheats.py", ("--no-download", "--offline", "--json")),
    ("tool", "update_game_cheats.py", ("--no-download", "--offline")),
]
VOLATILE = re.compile(r'"generated_unix_ms": \d+')
fails = 0
for mode, name, args in CASES:
    outs = []
    for code in (head, b82):
        root = t.make_tree(code)
        if mode == "scan":
            r, n = t.run(root, {}, "scan", str(root))
            text = json.dumps(json.loads(r.stdout.strip().splitlines()[-1])["games"])
        else:
            r, n = t.tool(root, {}, name, *args)
            text = r.stdout
        outs.append((VOLATILE.sub('"generated_unix_ms": <t>', text.replace(str(root), "<root>")), r.returncode, n))
    same = outs[0][0] == outs[1][0] and outs[0][1] == outs[1][1]
    fails += not same
    label = mode if mode == "scan" else f"{name} {' '.join(args)}"
    print(f"{'SAME' if same else 'DIFF'}  {label}: rc {outs[0][1]} / {outs[1][1]}, {len(outs[0][0])} bytes,"
          f" network attempts HEAD {outs[0][2]} / B82 {outs[1][2]}")
print("DIFFS", fails)
