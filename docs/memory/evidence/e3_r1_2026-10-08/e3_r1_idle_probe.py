#!/usr/bin/env python3
"""E3-R1 probe, part 2 -- the two trigger ages idle. A PS1 stream (E1-PS1-STREAM's launch) PLAYING for 600 s with
nobody at the controller, on the adopted state, no flag: the controller-packet age the recovery monitor reads
(GET /plugins/games/status -> recovery.last_client_seen_ms; no new hook) polled at 4 Hz with the recovery state, the
1-s sampler (tools/e1_sampler.py: eno1 rx packets/s = the client->host direction), and afterwards the client's
heartbeats (2 s; last_output_age_ms, arrival). Then E1's teardown. -> idle_probe/ (sampler files, ages.jsonl,
heartbeats.jsonl, run.json), idle_stats.json"""
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
OUT = os.path.join(HERE, "idle_probe")
SECS = 600


def main():
    os.makedirs(OUT, exist_ok=True)
    rec = {"started_utc": E.utc(), "preflight": E.preflight()}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    before = set(os.listdir(E.SESSDIR))
    samp = None
    try:
        rec["restart"] = E.restart_unit()
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
        E.teardown_flags({}, td)
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
    # ---- stats
    t0, t1 = rec["window"]["from"], rec["window"]["to"]
    ages = [json.loads(l) for l in open(os.path.join(OUT, "ages.jsonl"))]
    a = [x["ctrl_age_ms"] for x in ages if isinstance(x.get("ctrl_age_ms"), (int, float))]
    states = sorted({x.get("state") for x in ages})
    hb = []
    for f in [os.path.join(REPO, "logs/games/native_stream_heartbeat.log")]:
        for l in open(f, errors="replace"):
            try:
                r = json.loads(l)
            except ValueError:
                continue
            if t0 <= r.get("received_at_utc", "") <= t1:
                hb.append({k: r.get(k) for k in ("received_at_utc", "sequence", "elapsed_ms", "last_output_age_ms",
                                                  "lost_packets", "rx_packets")})
    with open(os.path.join(OUT, "heartbeats.jsonl"), "w") as fh:
        for r in hb:
            fh.write(json.dumps(r) + "\n")
    oa = [r["last_output_age_ms"] for r in hb if isinstance(r.get("last_output_age_ms"), (int, float))]
    sam = [json.loads(l) for l in open(os.path.join(OUT, "samples.jsonl"))]
    sam = [r for r in sam if t0 <= r["at_utc"] <= t1]
    rx = [((r.get("net") or {}).get("eno1") or {}).get("rx_pps") for r in sam]
    rx = [x for x in rx if isinstance(x, (int, float))]
    q = lambda xs, p: sorted(xs)[min(len(xs) - 1, int(p * (len(xs) - 1)))] if xs else None
    from datetime import datetime
    tt = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
    arr = [tt(r["received_at_utc"]) for r in hb]
    gaps = [b - a2 for a2, b in zip(arr, arr[1:])]
    st = {"window": [t0, t1], "polls": len(ages), "states_seen": states,
          "ctrl_age_ms": {"median": statistics.median(a) if a else None, "p95": q(a, 0.95), "p99": q(a, 0.99),
                          "max": max(a, default=None), "over_250": sum(1 for x in a if x > 250),
                          "over_500": sum(1 for x in a if x > 500), "over_1000": sum(1 for x in a if x > 1000)},
          "client_output_age_ms": {"heartbeats": len(oa), "median": statistics.median(oa) if oa else None,
                                   "p95": q(oa, 0.95), "max": max(oa, default=None),
                                   "over_1000": sum(1 for x in oa if x > 1000)},
          "heartbeat_arrival_gap_s": {"median": round(statistics.median(gaps), 3) if gaps else None,
                                      "max": round(max(gaps), 3) if gaps else None,
                                      "over_3": sum(1 for g in gaps if g > 3)},
          "rx_pps": {"median": statistics.median(rx) if rx else None, "min": min(rx, default=None),
                     "p01": q(rx, 0.01), "seconds_below_50pct": sum(1 for x in rx if rx and x < 0.5 * statistics.median(rx)),
                     "seconds": len(rx)},
          "controller_packets_with_no_input": bool(rx) and statistics.median(rx) > 300,
          "teardown_ok": rec["teardown"].get("flags_absent") and rec["teardown"].get("apk") == "CONFIRMED"}
    if rx:
        st["controller_packet_interval_ms_est"] = round(1000 / statistics.median(rx), 2)
    json.dump(st, open(os.path.join(HERE, "idle_stats.json"), "w"), indent=1)
    print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
