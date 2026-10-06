#!/usr/bin/env python3
"""E3: "the guide still serves" -- the EPG read endpoint for the suite's six channels (non-forced GET, cache only)
plus the status's cache-file count. Prints one JSON line. Read-only (a non-forced read of a fresh cache spawns
nothing; a stale or missing cache would queue a background refresh, which is reported as refresh_queued)."""
import json
import sys
import urllib.parse
import urllib.request

BASE = "http://localhost:8765"
CH = ["ComedyCentral.us@East", "CNBCUK.uk@SD", "10Bold.au@Sydney", "FoxSports1.us@HD", "NBC.us@East",
      "FilmBox.nl@Netherlands"]


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read() or b"{}")


out = {"channels": {}}
for c in CH:
    d = get("/plugins/epg/guide?channel_id=" + urllib.parse.quote(c))
    out["channels"][c] = {"ok": d.get("ok"), "programme_count": d.get("programme_count"), "cached": d.get("cached"),
                          "stale": d.get("stale"), "refresh_queued": d.get("refresh_queued")}
out["channels_serving"] = sum(1 for v in out["channels"].values() if v["ok"] and (v["programme_count"] or 0) > 0)
out["programmes_total"] = sum(v["programme_count"] or 0 for v in out["channels"].values())
st = get("/plugins/epg/status")
out["guide_cache_files"] = st.get("guide_cache_files")
print(json.dumps(out))
