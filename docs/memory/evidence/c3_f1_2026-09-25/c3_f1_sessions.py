#!/usr/bin/env python3
"""C3-F1 step 4: four short attract-mode sessions, one per ladder level
(7000, 6000, 5500, 5000), each exercising recovery's restart at that level.
Pre-registration: c3_f1_preregistration.txt (written before this ran).

Uses tools/d7_regression.py's launcher/session helpers. Loopback routes only:
c3-validated-bitrate-transition (to the level and back to 7000) and
c3-recovery-restart (the callable link-drop recovery uses). Writes
sessions.json beside this file, plus per-session report copies. No address
is written: the journal is reduced to counts and matched lines' fixed text.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "tools"))
import d7_regression as d  # noqa: E402

LEVELS = (7000, 6000, 5500, 5000)
RECOVERY_LOG = REPO / "logs/games/native_stream_recovery.log"
ALPHA = REPO / "logs/games/native_video_alpha.log"   # the manager's log: the cycle labels land here


def telemetry():
    return d.http("GET", "/diagnostics/stream-telemetry")[1]


def settle(n=2, timeout=30):
    """Two distinct, fresh telemetry snapshots (session_elapsed_ms advanced)."""
    seen = []
    t0 = time.time()
    while time.time() - t0 < timeout:
        t = telemetry()
        e = t.get("session_elapsed_ms")
        if t.get("fresh") and e is not None and (not seen or e != seen[-1][0]):
            seen.append((e, (t.get("receiver") or {}).get("recent_mbps")))
            if len(seen) > n:
                return seen
        time.sleep(0.5)
    return seen


def recovery_events(since_utc):
    out = []
    if RECOVERY_LOG.exists():
        for line in RECOVERY_LOG.read_text(errors="replace").splitlines()[-400:]:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("at_utc", "") >= since_utc:
                out.append({"event": r.get("event"), "at_utc": r.get("at_utc"), "method": r.get("method")})
    return out


def main():
    results = []
    # the companion restarted through its unit before the first session
    boot = d.row_boot()
    results.append({"boot": boot})
    print("boot", boot["verdict"], flush=True)
    for level in LEVELS:
        s = {"level": level}
        since_utc = d.now()
        since_local = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        before_reports = set(os.listdir(d.SESSDIR))
        alpha_mark = ALPHA.stat().st_size if ALPHA.exists() else 0
        s["launch"] = d.row_launch()
        ns = d.stream_status()
        s["any_override_at_playing"] = (ns.get("encoder_overrides") or {}).get("any_override")
        s["settle_initial"] = settle()
        if level != 7000:
            code, tr = d.http("POST", f"/plugins/games/c3-validated-bitrate-transition?target={level}", timeout=60)
            s["transition_to_level"] = {"http": code, "ok": tr.get("ok"), "from": tr.get("from_bitrate_kbps"),
                                        "to": tr.get("target_bitrate_kbps")}
            s["settle_after_transition"] = settle()
        s["bitrate_before_restart"] = d.stream_status().get("bitrate_kbps")
        t_restart_utc = d.now()
        t_restart_epoch = time.time()
        code, rr = d.http("POST", "/plugins/games/c3-recovery-restart", timeout=60)
        s["restart"] = {"http": code, "ok": rr.get("ok"), "schema": rr.get("schema"), "mode": rr.get("mode"),
                        "from": rr.get("from_bitrate_kbps"), "target": rr.get("target_bitrate_kbps"),
                        "video": rr.get("video"), "error": rr.get("error"), "at_utc": t_restart_utc}
        s["bitrate_after_restart"] = d.stream_status().get("bitrate_kbps")
        s["settle_after_restart"] = settle(n=3)
        s["recent_mbps_after_restart"] = s["settle_after_restart"][-1][1] if s["settle_after_restart"] else None
        time.sleep(8)
        if level != 7000:
            code, tr = d.http("POST", "/plugins/games/c3-validated-bitrate-transition?target=7000", timeout=60)
            s["return_to_7000"] = {"http": code, "ok": tr.get("ok")}
            settle()
        br = d.back_and_report(before_reports)
        s["report"] = br["report"]
        time.sleep(3)
        d.http("POST", "/plugins/games/stop", timeout=60)
        for _ in range(20):
            if d.games_status().get("active") is False:
                break
            time.sleep(1)
        s["game_active_after"] = d.games_status().get("active")
        s["bitrate_at_end"] = d.stream_status().get("bitrate_kbps")
        s["recovery_events"] = recovery_events(since_utc)
        lines = d.journal_since(since_local)
        with open(ALPHA, "rb") as fh:
            fh.seek(alpha_mark)
            alpha = fh.read().decode("utf-8", "replace").splitlines()
        s["alpha_log"] = [l[:200] for l in alpha if "C3-F1" in l or "C3.L1 Linux actuator" in l
                          or "C3.L3a Linux validated-ladder" in l]
        s["journal"] = {
            "native_stream_start_posts": sum(1 for l in lines if '"POST /plugins/games/native-stream-start' in l),
            "recovery_restart_posts": sum(1 for l in lines if '"POST /plugins/games/c3-recovery-restart' in l),
        }
        s["restart_epoch"] = t_restart_epoch
        if br["report"]:
            shutil.copy2(d.SESSDIR / br["report"], HERE / f"report_{level}.json")
        # heartbeats of the session, for mapping host time to the client clock
        hb = d.heartbeats_between(since_utc, d.now())
        with open(HERE / f"heartbeat_{level}.jsonl", "w") as fh:
            for r in hb:
                fh.write(json.dumps(r) + "\n")
        results.append(s)
        print(level, "restart http", s["restart"]["http"], "ok", s["restart"]["ok"], "bitrate",
              s["bitrate_before_restart"], "->", s["bitrate_after_restart"], "report", s["report"], flush=True)
        d.adb("shell", "input", "keyevent", "KEYCODE_WAKEUP")
        time.sleep(20)
    (HERE / "sessions.json").write_text(json.dumps(results, indent=2, default=str))
    print("done")


if __name__ == "__main__":
    main()
