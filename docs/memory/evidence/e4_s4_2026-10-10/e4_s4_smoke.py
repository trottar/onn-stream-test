#!/usr/bin/env python3
"""E4-S4 smoke (before the pre-registration; not data). With the flag: a PS1 stream, six forced refreshes (expected:
all deferred, the status shows 6 pending), the stream stopped, the six drain and complete, the guide serves. Without
the flag: a PS1 stream, six forced refreshes run at once (today). -> smoke.jsonl. Uses tools/e1_suite.py's helpers;
the flag lives in the drop-in e3_flag.conf for the smoke's first half only and is removed (daemon-reload + restart)
on every exit path."""
import importlib.util
import json
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
spec = importlib.util.spec_from_file_location("e1_suite", REPO / "tools/e1_suite.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
FLAG = "PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1"
OUT = HERE / "smoke.jsonl"


def w(row):
    row["at_utc"] = m.utc()
    with open(OUT, "a") as fh:
        fh.write(json.dumps(row, default=str) + "\n")
    print(json.dumps(row, default=str)[:400], flush=True)


def stream_on():
    code, _ = m.http("POST", f"/plugins/games/launch?id={m.TEKKEN['id']}", 90)
    for _ in range(20):
        if m.games_status().get("active"):
            break
        time.sleep(1)
    return {"launch_http": code, "stream": m.open_stream(), "recovery": (m.games_status().get("recovery") or {}).get("state")}


def stream_off(before):
    out = {}
    if "NativeStreamActivity" in m.top_activity():
        out["report"] = m.back_and_report(before)
    out["stopped"] = m.stop_game()
    out["banner"] = m.banner_clear()
    return out


def refreshes():
    rows = []
    for ch in m.EPG_CHANNELS:
        t0 = time.time()
        code, d = m.http("POST", f"/plugins/epg/refresh?channel_id={urllib.parse.quote(ch)}", 150)
        rows.append({"channel": ch, "http": code, "s": round(time.time() - t0, 2), "ok": d.get("ok"),
                     "refresh_deferred": d.get("refresh_deferred"), "stream_state": d.get("stream_state"),
                     "pending": d.get("deferred_pending"), "programmes": d.get("programme_count")})
    return rows


def main():
    import os
    before = set(os.listdir(m.SESSDIR))
    st = m.preflight()
    w({"step": "preflight", "ok": st["ok"]})
    if not st["ok"]:
        return 1
    w({"step": "guide_before", **m.guide_read()})
    try:
        # ---- A: with the flag
        m.DROPIN.write_text(f"[Service]\nEnvironment={FLAG}\n")
        m.sh(["systemctl", "--user", "daemon-reload"], 60)
        r = m.restart_unit()
        w({"step": "A_restart", "environ": r["environ"], "flag_in_environ": FLAG in r["environ"]})
        w({"step": "A_stream", **stream_on()})
        rows = refreshes()
        w({"step": "A_refreshes", "rows": rows, "all_deferred": all(x["refresh_deferred"] for x in rows)})
        w({"step": "A_status_while_playing", "deferred": (m.http("GET", "/plugins/epg/status", 10)[1] or {}).get("deferred"),
           "epg_children": len(m.comm_pids({"node", "npm"}))})
        w({"step": "A_stop", **stream_off(before)})
        w({"step": "A_drain", **m.wait_deferred_drain()})
    finally:
        m.DROPIN.unlink(missing_ok=True)
        m.sh(["systemctl", "--user", "daemon-reload"], 60)
        r = m.restart_unit()
        w({"step": "A_flag_removed", "dropin_absent": not m.DROPIN.exists(), "environ": r["environ"],
           "environ_adopted": r["environ"] == m.ADOPTED})
    # ---- B: without the flag (today)
    before = set(os.listdir(m.SESSDIR))
    w({"step": "B_stream", **stream_on()})
    rows = refreshes()
    w({"step": "B_refreshes", "rows": rows, "none_deferred": not any(x["refresh_deferred"] for x in rows),
       "all_ok": all(x["ok"] for x in rows)})
    w({"step": "B_status", "has_deferred_key": "deferred" in (m.http("GET", "/plugins/epg/status", 10)[1] or {})})
    w({"step": "B_stop", **stream_off(before)})
    w({"step": "guide_after", **m.guide_read()})
    w({"step": "final", "preflight": m.preflight(), "apk": "CONFIRMED" if m.apk_hash() == m.EXPECT_APK else "MISMATCH",
       "ps1_files_identical": m.ps1_files_identical(), "retroarch": len(m.retroarch_pids()), "encoder": len(m.encoder_pids())})
    return 0


if __name__ == "__main__":
    sys.exit(main())
