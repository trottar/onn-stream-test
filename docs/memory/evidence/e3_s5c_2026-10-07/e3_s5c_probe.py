#!/usr/bin/env python3
"""E3-S5C probe: the audio sender's send timing three ways -- no flag, PRIVYHUB_AUDIO_SENDER_PACING=frame, =frame_spin.

E3-S5B's probe (e3_s5b_2026-10-06/e3_s5b_probe.py), extended to a third session and to the sender thread's own
counters. Three sessions, each: the E3 drop-in with PRIVYHUB_AUDIO_SEND_TRACE=<here>/trace_<tag>.txt (+ the pacing value
for the flagged ones), a unit restart, E1-PS1-STREAM's launch to PLAYING (tools/e1_suite.py's functions), the sender
thread (the companion's one SCHED_RR thread) read twice inside the trace's 60 s (voluntary / involuntary context
switches, schedstat CPU ns), wait for the trace, then E1's teardown (drop-in removed, daemon-reload, restart, environ
checked against the adopted state, APK, PS1 files). Then the gap statistics -> probe_stats.json.
"""
import glob
import importlib.util
import json
import os
import statistics
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
spec = importlib.util.spec_from_file_location("e1s", os.path.join(REPO, "tools/e1_suite.py"))
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)


def rr_thread(pid):
    for st in glob.glob(f"/proc/{pid}/task/*/stat"):
        try:
            f = open(st).read().rsplit(")", 1)[1].split()
        except OSError:
            continue
        if int(f[38]) == 2:            # policy (field 41) == SCHED_RR
            return int(st.split("/")[4])
    return None


def thread_counters(pid, tid):
    s = open(f"/proc/{pid}/task/{tid}/status").read()
    v = int(s.split("voluntary_ctxt_switches:")[1].split()[0])
    nv = int(s.split("nonvoluntary_ctxt_switches:")[1].split()[0])
    cpu_ns = int(open(f"/proc/{pid}/task/{tid}/schedstat").read().split()[0])
    return {"t": time.time(), "vol": v, "nonvol": nv, "cpu_ns": cpu_ns}


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
        pid = E.mainpid()
        tid = None
        for _ in range(20):
            tid = rr_thread(pid)
            if tid:
                break
            time.sleep(0.5)
        t_seen = time.time()
        if tid:
            # the trace runs 30-90 s after the sender starts (~ when its thread is first seen): read at +35 and +85 s
            time.sleep(max(0, 35 - (time.time() - t_seen)))
            a = thread_counters(pid, tid)
            time.sleep(50)
            b = thread_counters(pid, tid)
            dt = b["t"] - a["t"]
            rec["sender_thread"] = {"span_s": round(dt, 2),
                                    "voluntary_cs_per_s": round((b["vol"] - a["vol"]) / dt, 1),
                                    "nonvoluntary_cs_per_s": round((b["nonvol"] - a["nonvol"]) / dt, 1),
                                    "cpu_pct": round(100 * (b["cpu_ns"] - a["cpu_ns"]) / 1e9 / dt, 2)}
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
            "bunches_ge_4": sum(1 for x in bunches if x >= 4)}


def main():
    out = {}
    for tag, flags in (("noflag", []), ("frame", ["PRIVYHUB_AUDIO_SENDER_PACING=frame"]),
                       ("frame_spin", ["PRIVYHUB_AUDIO_SENDER_PACING=frame_spin"])):
        r = session(tag, flags)
        out[tag] = {"run": {k: r.get(k) for k in ("started_utc", "ended_utc", "trace_bytes", "stream")},
                    "sender_thread": r.get("sender_thread"),
                    "teardown_ok": r["teardown"].get("flags_absent") and r["teardown"].get("apk") == "CONFIRMED"}
        if r.get("trace_bytes"):
            out[tag]["stats"] = s = stats(tag)
            st = r.get("sender_thread") or {}
            if st.get("voluntary_cs_per_s") is not None:
                pkts_per_s = s["originals"] / s["span_s"]
                out[tag]["wakeups_per_packet"] = round(st["voluntary_cs_per_s"] / pkts_per_s, 2)
        if not out[tag]["teardown_ok"]:
            break
    json.dump(out, open(os.path.join(HERE, "probe_stats.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
