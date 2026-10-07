#!/usr/bin/env python3
"""E3-S4 smoke (not data): does the lighter core load, run the fixture's demo loop and reach PLAYING on the stream?

One session with PRIVYHUB_SNES_CORE=snes9x in the E3 drop-in, the counter override in RetroArch's per-core dir for
"Snes9x" (tools/e1_suite.py's SNES_CORENAMES rule), E1-SNES-STREAM's launch (Super Mario World) to PLAYING, 180 s with
tools/e1_sampler.py (--telemetry --title) running, the RetroArch process's loaded core read from /proc/<pid>/maps, then
E1's teardown (BACK + report, stop, override removed, banner, drop-in removed + daemon-reload + restart, the environ
checked against the adopted state, APK, PS1 files). -> smoke/ (sampler files), smoke.json."""
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("e1s", os.path.join(REPO, "tools/e1_suite.py"))
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
KV = "PRIVYHUB_SNES_CORE=snes9x"
OVR = E.RA_CFG / E.SNES_CORENAMES["snes9x"] / E.SMW["override"].name


def loaded_cores():
    out = {}
    for p in E.retroarch_pids():
        try:
            maps = open(f"/proc/{p}/maps").read()
        except OSError:
            continue
        out[p] = sorted({os.path.basename(l.split()[-1]) for l in maps.splitlines() if l.endswith("_libretro.so")})
    return list(out.values())


def main():
    sd = Path(HERE) / "smoke"
    sd.mkdir(exist_ok=True)
    rec = {"started_utc": E.utc(), "preflight": E.preflight(), "override_dir_existed": OVR.parent.exists()}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    if OVR.exists():
        raise SystemExit("a file already sits at the override's path")
    before = set(os.listdir(E.SESSDIR))
    samp = None
    try:
        OVR.parent.mkdir(parents=True, exist_ok=True)
        OVR.write_text(E.COUNTER)
        E.DROPIN.write_text(f"[Service]\nEnvironment={KV}\n")
        E.sh(["systemctl", "--user", "daemon-reload"], 60)
        rec["restart"] = E.restart_unit()
        samp = subprocess.Popen([sys.executable, os.path.join(REPO, "tools/e1_sampler.py"), "run", str(sd), "--telemetry",
                                 "--title"], stdout=open(sd / "sampler.log", "w"), stderr=subprocess.STDOUT)
        code, _ = E.http("POST", f"/plugins/games/launch?id={E.SMW['id']}", 90)
        rec["launch_http"] = code
        for _ in range(20):
            if E.games_status().get("active"):
                break
            time.sleep(1)
        rec["stream"] = E.open_stream()
        rec["loaded_cores_at_playing"] = loaded_cores()
        t0 = E.utc()
        time.sleep(180)
        rec["window"] = {"from": t0, "to": E.utc()}
        rec["loaded_cores_at_end"] = loaded_cores()
        st = E.stream_status()
        rec["status_end"] = {k: st.get(k) for k in ("width", "height", "bitrate_kbps", "profile_id")}
        rec["recovery_end"] = (E.games_status().get("recovery") or {}).get("state")
    finally:
        td = {}
        if "NativeStreamActivity" in E.top_activity():
            td["report"] = E.back_and_report(before)
            td["report_fields"] = E.report_fields(td["report"])
        td["stopped"] = E.stop_game()
        td["retroarch_left"], td["encoder_left"] = len(E.retroarch_pids()), len(E.encoder_pids())
        OVR.unlink(missing_ok=True)
        td["override_removed"] = not OVR.exists()
        td["banner"] = E.banner_clear()
        E.teardown_flags({"dropin": [KV]}, td)
        td["apk"] = "CONFIRMED" if E.apk_hash() == E.EXPECT_APK else "MISMATCH"
        td["ps1_files_identical"] = E.ps1_files_identical()
        td["game_active"] = E.games_status().get("active")
        if samp:
            (sd / "sampler.stop").touch()
            try:
                samp.wait(timeout=30)
            except subprocess.TimeoutExpired:
                samp.kill()
        rec["teardown"] = td
        rec["ended_utc"] = E.utc()
    if rec.get("window"):
        h = E.S.summarize(str(sd), rec["window"]["from"], rec["window"]["to"])
        rec["retroarch_title"] = h.get("retroarch")
        hh = h.get("host") or {}
        rec["retroarch_cpu_mean"] = (hh.get("procs.retroarch.cpu_pct") or {}).get("mean")
        rec["host_cpu_mean"] = (hh.get("cpu.mean_pct") or {}).get("mean")
        rec["heartbeat"] = E.heartbeat_figures(rec["window"]["from"], rec["window"]["to"])
    ok = (rec.get("stream", {}).get("ok") and any("snes9x_libretro.so" in c for c in rec.get("loaded_cores_at_end", []))
          and (rec.get("retroarch_title") or {}).get("frames_per_s", 0) >= 59.0
          and rec["teardown"].get("flags_absent"))
    rec["smoke_ok"] = bool(ok)
    json.dump(rec, open(os.path.join(HERE, "smoke.json"), "w"), indent=1, default=str)
    print(json.dumps({k: rec.get(k) for k in ("smoke_ok", "stream", "loaded_cores_at_end", "retroarch_title",
                                              "retroarch_cpu_mean", "host_cpu_mean", "heartbeat")}, indent=1, default=str))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
