#!/usr/bin/env python3
"""Queue BK B195: every file under files_digest's roots whose mtime falls between T91's bench (19:05Z) and its close
(19:11Z), 2026-11-21 (one minute either side), read only — its root, its kind (from its suffix) and its hashed name
(files_digest's own: the 16-hex hash of its path from the root's parent). No name printed. Also: whether it is T91's
own (its stem compared in process) and whether the user's slots 0-3 changed in that window. usage: t91_files.py <repo>"""
import datetime as dt, hashlib, json, re, sys
from pathlib import Path
P = Path(sys.argv[1]).resolve(); H = Path.home() / "privyhub_h7"
roots = {"states": P / "data/games/retroarch/states", "setups' states": P / "data/games/retroarch/cheat_profiles",
         "rules": H / "rules", "this title's kept folder": H / "add_game/T91/kept"}
kept = [p for p in sorted(H.iterdir()) if p.is_dir() and p.name not in ("rules", "add_game")]
def kind(n):
    m = re.search(r"\.state(\d*)(\.png)?$", n)
    if m:
        s = int(m.group(1) or 0); pic = " picture" if m.group(2) else ""
        return (f"a user's slot {s}{pic}" if 1 <= s <= 3 else f"slot 0{pic} (every SAVE rewrites it)" if s == 0
                else f"the hub's slot 9{pic} (its hold scratch)" if s == 9 else f"slot {s}{pic}")
    return "an in-game save" if n.endswith(".srm") else "another file"
stem = Path(json.load(open(H / "add_game/T91/binding.json"))["relative_path"]).stem
lo = dt.datetime(2026, 11, 21, 19, 4, tzinfo=dt.timezone.utc).timestamp(); hi = lo + 8 * 60
print("window: 2026-11-21 19:04:00Z - 19:12:00Z (bench 19:05Z, close 19:11Z, a minute either side)")
total = 0
for name, root in list(roots.items()) + [("a kept H7 folder", p) for p in kept]:
    if not root.is_dir():
        print(f"{name}: absent"); continue
    files = [p for p in root.rglob("*") if p.is_file()]
    hits = [p for p in files if lo <= p.stat().st_mtime <= hi]
    print(f"{name}: {len(files)} files, {len(hits)} changed in the window")
    for p in sorted(hits):
        total += 1
        h = hashlib.sha256(str(p.relative_to(root.parent)).encode()).hexdigest()[:16]
        print(f"  {h}  {kind(p.name)}  at {dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc):%H:%M:%S}Z"
              f"  T91's own: {p.name.startswith(stem + '.')}  left out by files_digest today: {p.name.endswith('.state8')}")
users = [p for p in roots["states"].rglob("*") if p.is_file() and p.name.startswith(stem + ".")
         and re.search(r"\.state[0-3]?(\.png)?$", p.name)]
print(f"T91's slots 0-3 and their pictures: {len(users)} files, changed in the window: "
      f"{sum(lo <= p.stat().st_mtime <= hi for p in users)}")
print(f"changed in the window, every root: {total}")
