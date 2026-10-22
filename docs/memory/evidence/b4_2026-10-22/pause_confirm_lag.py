#!/usr/bin/env python3
"""B4: how far EmulatorManager.pause()'s confirmation trails the pause, from the companion's own NCI log (read-only).
Per PAUSE_TOGGLE: the next GET_STATUS replies (ms after the toggle was sent). Prints times and states only.
    python3 -I pause_confirm_lag.py logs/games/retroarch_control_probe.txt"""
import json, statistics, sys
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
out = {"toggles": 0, "pause": [], "resume": []}
for i, r in enumerate(rows):
    if r.get("event") == "command_sent" and r.get("command") == "PAUSE_TOGGLE":
        rep = [q for q in rows[i + 1:i + 8] if q.get("command") == "GET_STATUS" and q.get("event") == "command_response"]
        if len(rep) < 2:
            continue
        a, b = rep[0], rep[1]
        first = a["response"].split()[1]
        kind = "pause" if first == "PLAYING" else "resume"
        out["toggles"] += 1
        out[kind].append({"first_ms": round((a["time_unix"] - r["time_unix"]) * 1000, 1), "first": first,
                          "second_ms": round((b["time_unix"] - r["time_unix"]) * 1000, 1), "second": b["response"].split()[1],
                          "lag_ms": round((b["time_unix"] - a["time_unix"]) * 1000, 1)})
for k in ("pause", "resume"):
    lags = [x["lag_ms"] for x in out[k]]
    out[k + "_summary"] = {"n": len(lags), "first_reply_old_state": sum(1 for x in out[k] if x["first"] != x["second"]),
                           "lag_ms_min": min(lags), "lag_ms_median": statistics.median(lags), "lag_ms_max": max(lags),
                           "lag_frames_min": round(min(lags) * 0.06, 2), "lag_frames_max": round(max(lags) * 0.06, 2)}
print(json.dumps(out, indent=1))
