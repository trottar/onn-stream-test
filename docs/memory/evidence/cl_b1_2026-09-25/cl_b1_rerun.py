#!/usr/bin/env python3
"""CL-B1 step 3, RE-RUN with the rebuilt arm APK (slow_event_capacity fixed): arm session
only, then the adopted APK reinstalled; the target-form session is not repeated.
Original:  one session on the arm APK (report as a body), then the
adopted APK reinstalled and its hash confirmed, then one session on it
(report in the request target). Attract mode, 7000 throughout, no
controller in any mode, BACK after >= 3 min. Writes sessions.json here.
Addresses never written: journal reduced to counts and fixed text.
"""
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "tools"))
import d7_regression as d  # noqa: E402

ARM_APK = REPO / "runtime/cl_b1/arm2_app-debug.apk"
ARM_SHA = "71d8c3d7e9cf287fc79ec16cfe8e514842d005278e3c7f25a90b3ac1393bcd4c"
ADOPTED_APK = REPO / "runtime/c4_m1/adopted_app-debug.apk"
ADOPTED_SHA = "f31b1c180c5d0849230860d2f5b7ab1b4a8637f7be56a7dcf1f71aba77668ae7"
HOLD_S = 190


def device_sha():
    p = d.adb("shell", "pm", "path", d.PKG).strip().replace("package:", "")
    return d.adb("shell", "sha256sum", p).split()[0] if p else None


def install(apk, want):
    for attempt in (1, 2):
        d.adb("shell", "am", "force-stop", d.PKG)
        out = d.sh(["adb", "install", "-r", str(apk)], 120).strip().splitlines()
        got = device_sha()
        if got == want:
            return {"ok": True, "attempt": attempt, "result": out[-1] if out else "", "device_sha": got}
    return {"ok": False, "result": out[-1] if out else "", "device_sha": got}


def session(label):
    s = {"label": label}
    since = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    before = set(os.listdir(d.SESSDIR))
    s["launch"] = d.row_launch()
    ns = d.stream_status()
    s["any_override_at_playing"] = (ns.get("encoder_overrides") or {}).get("any_override")
    s["bitrate"] = ns.get("bitrate_kbps")
    time.sleep(HOLD_S)
    br = d.back_and_report(before)
    s["report"] = br["report"]
    time.sleep(3)
    d.http("POST", "/plugins/games/stop", timeout=60)
    for _ in range(20):
        if d.games_status().get("active") is False:
            break
        time.sleep(1)
    lines = d.journal_since(since)
    s["journal"] = {
        "received_as_body": [l.split("]: ", 1)[-1] for l in lines if "decoder-session-log received as body" in l],
        "stored": sum(1 for l in lines if "Native decoder session log:" in l),
        "warnings": sum(1 for l in lines if "WARNING decoder-session-log" in l),
        "target_form_posts": sum(1 for l in lines if '"POST /plugins/games/decoder-session-log?report=' in l),
        "body_form_posts": sum(1 for l in lines if '"POST /plugins/games/decoder-session-log HTTP' in l),
        "tracebacks": sum(1 for l in lines if "Traceback" in l),
    }
    if br["report"]:
        shutil.copy2(d.SESSDIR / br["report"], HERE / f"report_{label}.json")
    s["game_active_after"] = d.games_status().get("active")
    return s


def main():
    out = {}
    out["install_arm"] = install(ARM_APK, ARM_SHA)
    if not out["install_arm"]["ok"]:
        out["reinstall_adopted"] = install(ADOPTED_APK, ADOPTED_SHA)
        (HERE / "sessions.json").write_text(json.dumps(out, indent=2))
        print("arm install failed; adopted reinstalled", out["reinstall_adopted"]["ok"])
        return
    out["arm_session"] = session("arm2_body")
    print("arm", json.dumps(out["arm_session"]["journal"]), flush=True)
    out["reinstall_adopted"] = install(ADOPTED_APK, ADOPTED_SHA)
    print("adopted reinstall", out["reinstall_adopted"], flush=True)
    d.adb("shell", "am", "force-stop", d.PKG)
    d.open_launcher()
    out["banner_after"] = d.screen_has("NOW PLAYING")
    out["device_sha_end"] = device_sha()
    (HERE / "sessions.json").write_text(json.dumps(out, indent=2, default=str))
    print("done")


if __name__ == "__main__":
    main()
