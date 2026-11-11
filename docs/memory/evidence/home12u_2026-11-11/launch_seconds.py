#!/usr/bin/env python3
"""HOME-12U: the 60-second rule's read. Real launches WITHOUT cheats (the journal's launch 200 lines with no
cheat_source), request-to-answer seconds estimated as the journal's 200 time minus the game log's opening time (the log
opens just after the request arrives: a lower bound by well under a second). Per system: counts and seconds only."""
import re, sys, os, time, datetime, json
from pathlib import Path
lines = Path(sys.argv[1]).read_text().splitlines(); logdir = Path(sys.argv[2])
logs = []
for f in os.listdir(logdir):
    m = re.match(r"(\d{8}-\d{6})-(.*)\.log$", f)
    if not m: continue
    ts = time.mktime(time.strptime(m.group(1), "%Y%m%d-%H%M%S"))
    logs.append((ts, m.group(2)))
logs.sort()
def system_of(gid):
    for s in ("ps1", "snes", "n64", "ps2", "gamecube", "gc"):
        if gid.startswith(f"game_{s}_"): return "gamecube" if s == "gc" else s
    return "other"
out = {}; unmatched = {}
for l in lines:
    m = re.match(r"(\S+) .*\"POST /plugins/games/launch\?(\S+) HTTP/1\.1\" (\d+)", l)
    if not m or m.group(3) != "200": continue
    q = m.group(2)
    if "cheat_source=" in q: continue
    gid = re.search(r"(?:^|&)id=([^&]+)", q).group(1); sysn = system_of(gid)
    t = datetime.datetime.fromisoformat(m.group(1)).timestamp()
    cands = [ts for ts, name in logs if t - 300 <= ts <= t + 1 and (name == gid or name == sysn or (sysn == "gamecube" and name == "gamecube"))]
    if not cands:
        unmatched[sysn] = unmatched.get(sysn, 0) + 1; continue
    secs = t - max(cands)
    r = out.setdefault(sysn, {"launches": 0, "max_s": 0.0, "ge_45": 0, "ge_60": 0, "secs": []})
    r["launches"] += 1; r["max_s"] = max(r["max_s"], secs); r["ge_45"] += secs >= 45; r["ge_60"] += secs >= 60; r["secs"].append(secs)
for s, r in out.items():
    v = sorted(r.pop("secs")); r["median_s"] = round(v[len(v)//2], 1); r["max_s"] = round(r["max_s"], 1)
print(json.dumps({"per_system": out, "launch_200_without_cheats_unmatched_to_a_log": unmatched}, indent=1, sort_keys=True))
