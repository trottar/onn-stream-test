#!/usr/bin/env python3
"""B82: GamesPlugin's systems as the companion constructs it (`from plugins import PLUGINS`), HEAD's code vs B82's,
for all 8 combinations of the three flags, on test_b82's fixture tree; plus, for B82, `listed_systems()` equal to the
constructed instance's and the scan's systems. Network blocked in each child. Prints one line per combination.

usage: proof_init_systems.py <HEAD copy> <B82 copy>"""
import itertools, json, sys
from pathlib import Path
head, b82 = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
sys.path.insert(0, str(b82 / "tests/art_systems"))
import test_b82 as t   # noqa: E402
CHILD = t.RUNNER.split("mode, root =")[0] + r'''
root = sys.argv[1]
sys.path.insert(0, os.path.join(root, "companion"))
from plugins import PLUGINS
g = PLUGINS["games"]
g._metadata_reconcile_thread.join(120)
out = {"instance_attr": "SYSTEMS" in vars(g),
       "systems": {k: {**v, "extensions": sorted(v["extensions"])} for k, v in g.SYSTEMS.items()}}
cls = type(g)
if hasattr(cls, "listed_systems"):
    out["builder_equal"] = cls.listed_systems() == g.SYSTEMS
    from games.metadata_importer import scan_privyhub_games
    out["scan_systems_within"] = sorted({x["system"] for x in scan_privyhub_games(cls.PROJECT_ROOT)} - set(g.SYSTEMS))
print(json.dumps(out, sort_keys=True))
'''
import os, subprocess
fails = 0
for combo in itertools.product((0, 1), repeat=3):
    env = {k: "1" for k, on in zip(("PRIVYHUB_PS2", "PRIVYHUB_N64", "PRIVYHUB_GAMECUBE"), combo) if on}
    res = []
    for code in (head, b82):
        root = t.make_tree(code)
        child_env = {k: v for k, v in os.environ.items() if not k.startswith("PRIVYHUB_")} | env
        child_env["B82_NET_LOG"] = str(root / "net.log")
        r = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD, str(root)], env=child_env, cwd=root,
                           capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr[-1500:]
        res.append(json.loads(r.stdout.strip().splitlines()[-1]))
    same = res[0]["systems"] == res[1]["systems"] and res[0]["instance_attr"] == res[1]["instance_attr"]
    ok = same and res[1]["builder_equal"] and res[1]["scan_systems_within"] == []
    fails += not ok
    print(f"{'OK  ' if ok else 'FAIL'} flags {sorted(env) or 'none'}: systems {sorted(res[1]['systems'])}; "
          f"HEAD = B82 {same}; instance attribute {res[1]['instance_attr']}; builder = instance "
          f"{res[1]['builder_equal']}; scan's systems within the list {res[1]['scan_systems_within'] == []}")
print("FAILS", fails)
