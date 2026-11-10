#!/usr/bin/env python3
"""ART-1R ADDITION 1, read-only: did the hidden reconcile inside ART-1's tool runs (2026-11-10 ~00:32-00:45Z) make
a request or write a record? Counts only; no name or path printed beyond the hub's own fixed folder names."""
import json, os, sys, datetime
from pathlib import Path
root = Path(sys.argv[1])
def ts(s): return datetime.datetime.fromisoformat(s).timestamp()
W = (ts("2026-11-10T00:30:00+00:00"), ts("2026-11-10T00:50:00+00:00"))   # the tool runs' window, padded
L = (ts("2026-11-10T00:30:00+00:00"), ts(sys.argv[2]))                     # to now (wider)
def u(t): return datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
print("window", u(W[0]), "-", u(W[1]), "; wide", u(L[0]), "-", u(L[1]))
st = root / "logs/games/game_metadata_startup_reconcile.json"
d = json.loads(st.read_text())
print("reconcile status: result", d.get("result"), "| generated", u(d["generated_unix_ms"]/1000), "| file mtime", u(st.stat().st_mtime))
print("  reasons", len(d.get("reasons", [])), "| discovered_count", d.get("discovered_count"), "| metadata_count_before", d.get("metadata_count_before"),
      "| incomplete_count_before", d.get("incomplete_count_before"), "| metadata_update_invoked", d.get("metadata_update_invoked"),
      "| catalog_cache_invalidated", d.get("catalog_cache_invalidated"), "| metadata_update_counts", "present" if "metadata_update_counts" in d else "absent")
def count(base, per_system=True):
    out = {}
    if not base.exists(): return None
    for dp, _, fs in os.walk(base):
        for f in fs:
            p = Path(dp) / f
            try: m = p.stat().st_mtime
            except OSError: continue
            key = p.relative_to(base).parts[0] if per_system and len(p.relative_to(base).parts) > 1 else "(top)"
            o = out.setdefault(key, [0, 0, 0]); o[0] += 1
            if W[0] <= m <= W[1]: o[1] += 1
            if L[0] <= m <= L[1]: o[2] += 1
    return out
for label, rel in (("provider cache (libretro)", "data/games/metadata/provider_cache/libretro"),
                   ("box art", "media/games/box_art")):
    c = count(root / rel)
    print(label + ":", "absent" if c is None else "; ".join(f"{k} files {v[0]} in-window {v[1]} since-00:30Z {v[2]}" for k, v in sorted(c.items())))
for rel in ("data/games/metadata.json", "data/games/library_state.json", "data/games/metadata/provider_cache/libretro"):
    p = root / rel
    print(rel.split("/")[-1], "mtime", u(p.stat().st_mtime), "in-window", W[0] <= p.stat().st_mtime <= W[1])
# metadata records: any record whose own time stamp falls in the window
md = json.loads((root / "data/games/metadata.json").read_text())
games = md.get("games", {}) if isinstance(md, dict) else {}
TS_KEYS = ("updated_unix_ms", "matched_unix_ms", "checked_unix_ms", "generated_unix_ms", "last_attempt_unix_ms", "fetched_unix_ms")
inw = {}; tot = {}; keys_seen = set()
for gid, rec in (games.items() if isinstance(games, dict) else []):
    sysid = str(rec.get("system", "?")) if isinstance(rec, dict) else "?"
    tot[sysid] = tot.get(sysid, 0) + 1
    if not isinstance(rec, dict): continue
    for k, v in rec.items():
        if isinstance(v, (int, float)) and k.endswith("_ms"): keys_seen.add(k)
    if any(isinstance(rec.get(k), (int, float)) and L[0] <= rec[k]/1000 <= L[1] for k in keys_seen):
        inw[sysid] = inw.get(sysid, 0) + 1
print("metadata records per system:", dict(sorted(tot.items())), "| top-level generated", u(md.get("generated_unix_ms", 0)/1000) if isinstance(md, dict) and md.get("generated_unix_ms") else "n/a")
print("record time keys seen:", sorted(keys_seen))
print("records stamped since 00:30Z:", inw or "none")
# the reports the update writes
for rel in ("logs/games",):
    n = sum(1 for p in (root / rel).glob("game_metadata*") if W[0] <= p.stat().st_mtime <= W[1])
    names = sorted(p.name for p in (root / rel).glob("game_metadata*") if W[0] <= p.stat().st_mtime <= W[1])
    print("logs/games game_metadata* files written in window:", n, names)
