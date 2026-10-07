#!/usr/bin/env python3
"""E3-S5B probe: the audio sender's send timing, without and with PRIVYHUB_AUDIO_SENDER_PACING=frame.

Two sessions, each: a drop-in with PRIVYHUB_AUDIO_SEND_TRACE=<here>/trace_<tag>.txt (+ the pacing flag for the
flagged one), a unit restart, E1-PS1-STREAM's launch to PLAYING (tools/e1_suite.py's functions), wait for the trace
(the sender writes 60 s of sendto times starting 30 s after it starts), then E1's teardown (drop-in removed,
daemon-reload, restart, environ checked, APK, PS1 files). Then the gap statistics -> probe_stats.json.
"""
import importlib.util
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("e1s", os.path.join(REPO, "tools/e1_suite.py"))
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def session(tag, flags):
    trace = os.path.join(HERE, f"trace_{tag}.txt")
    if os.path.exists(trace):
        os.unlink(trace)
    kvs = [f"PRIVYHUB_AUDIO_SEND_TRACE={trace}"] + flags
    rec = {"tag": tag, "flags": flags, "started_utc": E.utc(), "preflight": E.preflight()}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    before = set(os.listdir(E.SESSDIR))
    try:
        E.DROPIN.write_text("[Service]\n" + "".join(f"Environment={kv}\n" for kv in kvs))
        E.sh(["systemctl", "--user", "daemon-reload"], 60)
        rec["restart"] = E.restart_unit()
        E.http("POST", f"/plugins/games/launch?id={E.TEKKEN['id']}", 90)
        for _ in range(20):
            if E.games_status().get("active"):
                break
            time.sleep(1)
        rec["stream"] = E.open_stream()
        if not rec["stream"]["ok"]:
            raise RuntimeError("stream did not reach PLAYING")
        t0 = time.time()
        while time.time() - t0 < 150 and not (os.path.exists(trace) and os.path.getsize(trace) > 0):
            time.sleep(2)
        time.sleep(3)
        rec["trace_bytes"] = os.path.getsize(trace) if os.path.exists(trace) else 0
    finally:
        td = {}
        if "NativeStreamActivity" in E.top_activity():
            td["report"] = E.back_and_report(before)
            td["report_fields"] = E.report_fields(td["report"])
        td["stopped"] = E.stop_game()
        td["banner"] = E.banner_clear()
        E.teardown_flags({"dropin": kvs}, td)
        td["apk"] = "CONFIRMED" if E.apk_hash() == E.EXPECT_APK else "MISMATCH"
        td["ps1_files_identical"] = E.ps1_files_identical()
        td["retroarch_left"], td["encoder_left"] = len(E.retroarch_pids()), len(E.encoder_pids())
        rec["teardown"] = td
        rec["ended_utc"] = E.utc()
    json.dump(rec, open(os.path.join(HERE, f"probe_{tag}_run.json"), "w"), indent=1, default=str)
    return rec


def stats(tag):
    rows = [l.split() for l in open(os.path.join(HERE, f"trace_{tag}.txt"))]
    t = [int(a) for a, k in rows]
    orig = [int(a) for a, k in rows if k == "o"]
    g = [(b - a) / 1e6 for a, b in zip(orig, orig[1:])]           # ms between consecutive originals (ticks)
    gs = sorted(g)
    # bunches: runs of datagrams (originals and duplicates) each < 0.2 ms after the previous
    bunches, run = [], 1
    for a, b in zip(t, t[1:]):
        if b - a < 200_000:
            run += 1
        else:
            bunches.append(run)
            run = 1
    bunches.append(run)
    span_s = (t[-1] - t[0]) / 1e9
    return {"datagrams": len(t), "originals": len(orig), "span_s": round(span_s, 2),
            "tick_gap_ms": {"median": round(statistics.median(g), 4), "p99": round(gs[int(0.99 * (len(gs) - 1))], 4),
                            "p999": round(gs[int(0.999 * (len(gs) - 1))], 4), "max": round(max(g), 3),
                            "min": round(min(g), 4), "sd": round(statistics.pstdev(g), 4)},
            "tick_gaps_gt_10ms": sum(1 for x in g if x > 10), "tick_gaps_gt_20ms": sum(1 for x in g if x > 20),
            "tick_gaps_lt_1ms": sum(1 for x in g if x < 1),
            "bunch_sizes": {str(k): bunches.count(k) for k in sorted(set(bunches))},
            "bunches_ge_4": sum(1 for x in bunches if x >= 4),
            "bunches_ge_4_per_min": round(sum(1 for x in bunches if x >= 4) / (span_s / 60), 2)}


def main():
    out = {}
    for tag, flags in (("noflag", []), ("flag", ["PRIVYHUB_AUDIO_SENDER_PACING=frame"])):
        r = session(tag, flags)
        out[tag] = {"run": {k: r.get(k) for k in ("started_utc", "ended_utc", "trace_bytes", "stream")},
                    "teardown_ok": r["teardown"].get("flags_absent") and r["teardown"].get("apk") == "CONFIRMED"}
        if r.get("trace_bytes"):
            out[tag]["stats"] = stats(tag)
    json.dump(out, open(os.path.join(HERE, "probe_stats.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
