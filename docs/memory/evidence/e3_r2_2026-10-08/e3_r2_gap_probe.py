#!/usr/bin/env python3
"""E3-R2 §1 -- the 10-min gap-log probe. A PS1 stream (E1-PS1-STREAM's launch) PLAYING for 600 s, nobody at the
controller, on the adopted state plus PRIVYHUB_RECOVERY_GAP_LOG=1 alone (the E3 drop-in for this probe only; the v2
trigger ABSENT, so today's rule is live): the silence-gap log (logs/games/native_stream_ctrl_gaps.log), the recovery
state at 4 Hz, the 1-s sampler, the heartbeats. Then E1's teardown, the drop-in removed, the adopted state checked.
-> gap_probe/ (sampler files, ages.jsonl, gaps.jsonl, heartbeats.jsonl, recovery.jsonl, run.json), gap_stats.json"""
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("e1s", os.path.join(REPO, "tools/e1_suite.py"))
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
OUT = os.path.join(HERE, "gap_probe")
SECS = 600
FLAG = "PRIVYHUB_RECOVERY_GAP_LOG=1"
GAPLOG = os.path.join(REPO, "logs/games/native_stream_ctrl_gaps.log")
RECLOG = os.path.join(REPO, "logs/games/native_stream_recovery.log")


def lines_in(path, key, t0, t1):
    out = []
    for f in (path + ".1", path):
        if not os.path.exists(f):
            continue
        for l in open(f, errors="replace"):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if t0 <= (r.get(key) or "") <= t1:
                out.append(r)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    rec = {"started_utc": E.utc(), "preflight": E.preflight(), "flag": FLAG}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    before = set(os.listdir(E.SESSDIR))
    samp = None
    w = {"dropin": [FLAG]}
    try:
        E.DROPIN.write_text(f"[Service]\nEnvironment={FLAG}\n")
        E.sh(["systemctl", "--user", "daemon-reload"], 60)
        rec["restart"] = r = E.restart_unit()
        if not (r["mainpid_serves_8765"] and r["environ"] == sorted(E.ADOPTED + [FLAG]) and r["manager"] == []):
            raise RuntimeError(f"unit not as expected after restart: {r}")
        samp = subprocess.Popen([sys.executable, os.path.join(REPO, "tools/e1_sampler.py"), "run", OUT, "--telemetry"],
                                stdout=open(os.path.join(OUT, "sampler.log"), "w"), stderr=subprocess.STDOUT)
        E.http("POST", f"/plugins/games/launch?id={E.TEKKEN['id']}", 90)
        for _ in range(20):
            if E.games_status().get("active"):
                break
            time.sleep(1)
        rec["stream"] = E.open_stream()
        if not rec["stream"]["ok"]:
            raise RuntimeError("stream did not reach PLAYING")
        time.sleep(30)                                   # settle
        rec["window"] = {"from": E.utc()}
        t_end = time.time() + SECS
        with open(os.path.join(OUT, "ages.jsonl"), "w") as fh:
            while time.time() < t_end:
                t0 = time.time()
                r = (E.games_status().get("recovery") or {})
                fh.write(json.dumps({"at_utc": E.utc(), "ctrl_age_ms": r.get("last_client_seen_ms"),
                                     "state": r.get("state")}) + "\n")
                time.sleep(max(0, 0.25 - (time.time() - t0)))
        rec["window"]["to"] = E.utc()
    finally:
        td = {}
        if "NativeStreamActivity" in E.top_activity():
            td["report"] = E.back_and_report(before)
            td["report_fields"] = E.report_fields(td["report"])
        td["stopped"] = E.stop_game()
        td["banner"] = E.banner_clear()
        E.teardown_flags(w, td)
        td["apk"] = "CONFIRMED" if E.apk_hash() == E.EXPECT_APK else "MISMATCH"
        td["ps1_files_identical"] = E.ps1_files_identical()
        td["retroarch_left"], td["encoder_left"] = len(E.retroarch_pids()), len(E.encoder_pids())
        if samp:
            open(os.path.join(OUT, "sampler.stop"), "w").close()
            try:
                samp.wait(timeout=30)
            except subprocess.TimeoutExpired:
                samp.kill()
        rec["teardown"] = td
        rec["ended_utc"] = E.utc()
        json.dump(rec, open(os.path.join(OUT, "run.json"), "w"), indent=1, default=str)
    t0, t1 = rec["window"]["from"], rec["window"]["to"]
    gaps = lines_in(GAPLOG, "start_utc", rec["started_utc"], rec["ended_utc"])
    recov = lines_in(RECLOG, "at_utc", rec["started_utc"], rec["ended_utc"])
    hb = [r for r in lines_in(os.path.join(REPO, "logs/games/native_stream_heartbeat.log"), "received_at_utc", t0, t1)]
    for name, rows in (("gaps.jsonl", gaps), ("recovery.jsonl", recov), ("heartbeats.jsonl",
                       [{k: r.get(k) for k in ("received_at_utc", "sequence", "last_output_age_ms")} for r in hb])):
        with open(os.path.join(OUT, name), "w") as fh:
            fh.writelines(json.dumps(r) + "\n" for r in rows)
    win = [g for g in gaps if t0 <= g["start_utc"] <= t1]
    gm = [g["gap_ms"] for g in win]
    bs = [g["burst_500ms"] for g in win]
    ages = [json.loads(l) for l in open(os.path.join(OUT, "ages.jsonl"))]
    a = [x["ctrl_age_ms"] for x in ages if isinstance(x.get("ctrl_age_ms"), (int, float))]
    oa = [r["last_output_age_ms"] for r in hb if isinstance(r.get("last_output_age_ms"), (int, float))]
    st = {"window": [t0, t1], "flag": FLAG, "states_seen": sorted({x.get("state") for x in ages}),
          "gaps_over_250ms": {"count": len(gm), "max_ms": max(gm, default=None),
                              "median_ms": statistics.median(gm) if gm else None,
                              "over_500": sum(1 for g in gm if g > 500), "over_1000": sum(1 for g in gm if g > 1000),
                              "over_5000": sum(1 for g in gm if g > 5000)},
          "catch_up_burst_500ms": {"median": statistics.median(bs) if bs else None, "max": max(bs, default=None),
                                   "min": min(bs, default=None), "truncated": sum(1 for g in win if g["burst_truncated"])},
          "gaps_whole_probe_incl_launch_teardown": len(gaps),
          "recovery_events_in_window": [r for r in recov if t0 <= r["at_utc"] <= t1],
          "ctrl_age_poll_max_ms": max(a, default=None),
          "client_output_age_ms_max": max(oa, default=None), "heartbeats": len(oa),
          "would_today_have_paused": [g for g in win if g["gap_ms"] > 1000],
          "teardown_ok": rec["teardown"].get("flags_absent") and rec["teardown"].get("apk") == "CONFIRMED"}
    json.dump(st, open(os.path.join(HERE, "gap_stats.json"), "w"), indent=1)
    print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
