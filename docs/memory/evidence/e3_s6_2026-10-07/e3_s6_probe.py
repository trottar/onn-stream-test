#!/usr/bin/env python3
"""E3-S6 probe: which half of a grab the live stream feels -- the guide-metadata parse alone, or the grabber child
alone -- against a PS1 stream (E1-PS1-STREAM's launch, tools/e1_suite.py's functions), the 1-s sampler (--e2) on.

The companion runs with PRIVYHUB_MEM_PROBE=1 (drop-in, probe only), which serves /plugins/epg/memprobe?op=parse|
prepare|spawn. Sequence after PLAYING + 60 s settle + 60 s quiet: parse x20, prepare (one channel), spawn x20, parse x20,
each trigger 15 s after the previous one started. Then E1's teardown. Then the alignment (e2_analysis.py's loss series
and the busiest core, offsets 0..10 s) and the reading rule -> probe_triggers.jsonl, probe_aligned.json.
Reading rule (the task's, written before): an op reproduces the peak if its mean lost packets/s at offsets 0-2 s is
>= 3x the stream's baseline loss/s (the same window, seconds outside 0..10 s after any trigger)."""
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, rel))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


E = load("e1s", "tools/e1_suite.py")
A = load("e2a", "docs/memory/evidence/e2_s1_2026-10-05/e2_analysis.py")
CH = "CNBCUK.uk@SD"
KV = "PRIVYHUB_MEM_PROBE=1"


def pss_kb(pid):
    try:
        for line in open(f"/proc/{pid}/smaps_rollup"):
            if line.startswith("Pss:"):
                return int(line.split()[1])
    except OSError:
        return None


def run():
    rec = {"started_utc": E.utc(), "preflight": E.preflight(), "channel": CH}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    before = set(os.listdir(E.SESSDIR))
    sd = os.path.join(HERE, "probe_sampler")
    os.makedirs(sd, exist_ok=True)
    samp = None
    trig = open(os.path.join(HERE, "probe_triggers.jsonl"), "w")
    try:
        E.DROPIN.write_text(f"[Service]\nEnvironment={KV}\n")
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
        samp = subprocess.Popen([sys.executable, os.path.join(REPO, "tools/e1_sampler.py"), "run", sd, "--e2", "--telemetry"],
                                stdout=open(os.path.join(sd, "sampler.log"), "w"), stderr=subprocess.STDOUT)
        time.sleep(60)
        rec["quiet_from"] = E.utc()
        time.sleep(60)
        pid = E.mainpid()
        plan = [("parse", 20), ("prepare", 1), ("spawn", 20), ("parse", 20)]
        for op, n in plan:
            for i in range(n):
                t0 = time.time()
                code, d = E.http("GET", f"/plugins/epg/memprobe?op={op}&channel_id={CH.replace('@', '%40')}", 150)
                row = {"op": op, "i": i, "start_utc": E.utc(t0), "end_utc": E.utc(), "http": code,
                       "pss_kb_after": pss_kb(pid), **{k: d.get(k) for k in ("wall_s", "thread_cpu_s", "items", "ok",
                                                                             "programmes", "candidates")}}
                trig.write(json.dumps(row) + "\n")
                trig.flush()
                time.sleep(max(0, 15 - (time.time() - t0)))
        rec["triggers_to"] = E.utc()
        time.sleep(15)
    finally:
        trig.close()
        if samp:
            open(os.path.join(sd, "sampler.stop"), "w").close()
            try:
                samp.wait(timeout=30)
            except subprocess.TimeoutExpired:
                samp.kill()
        td = {}
        if "NativeStreamActivity" in E.top_activity():
            td["report"] = E.back_and_report(before)
            td["report_fields"] = E.report_fields(td["report"])
        td["stopped"] = E.stop_game()
        td["banner"] = E.banner_clear()
        E.teardown_flags({"dropin": [KV]}, td)
        td["apk"] = "CONFIRMED" if E.apk_hash() == E.EXPECT_APK else "MISMATCH"
        td["ps1_files_identical"] = E.ps1_files_identical()
        td["retroarch_left"], td["encoder_left"] = len(E.retroarch_pids()), len(E.encoder_pids())
        rec["teardown"] = td
        rec["ended_utc"] = E.utc()
        json.dump(rec, open(os.path.join(HERE, "probe_run.json"), "w"), indent=1, default=str)
    return rec


def analyse():
    rec = json.load(open(os.path.join(HERE, "probe_run.json")))
    trig = [json.loads(l) for l in open(os.path.join(HERE, "probe_triggers.jsonl"))]
    t0, t1 = A.t(rec["quiet_from"]), A.t(rec["triggers_to"]) + 10
    L = A.hb_loss_series(t0, t1)
    busy = {}
    for r in A.jl(os.path.join(HERE, "probe_sampler", "samples.jsonl")):
        busy[int(A.t(r["at_utc"]))] = (r.get("cpu") or {}).get("max_pct")
    starts = [int(A.t(x["start_utc"])) for x in trig]
    near = set(s + o for s in starts for o in range(0, 11))
    base = [v for sec, v in L.items() if sec not in near]
    bb = [v for sec, v in busy.items() if t0 <= sec <= t1 and sec not in near and v is not None]
    out = {"baseline_loss_per_s": round(statistics.mean(base), 3) if base else None, "baseline_seconds": len(base),
           "baseline_busiest_core": round(statistics.mean(bb), 1) if bb else None, "ops": {}}
    for op in ("parse", "spawn"):
        ss = [int(A.t(x["start_utc"])) for x in trig if x["op"] == op]
        al = {"loss": [], "busiest": []}
        for o in range(11):
            lv = [L.get(s + o) for s in ss if L.get(s + o) is not None]
            bv = [busy.get(s + o) for s in ss if busy.get(s + o) is not None]
            al["loss"].append(round(statistics.mean(lv), 3) if lv else None)
            al["busiest"].append(round(statistics.mean(bv), 1) if bv else None)
        m02 = [x for x in al["loss"][:3] if x is not None]
        m = statistics.mean(m02) if m02 else None
        rows = [x for x in trig if x["op"] == op]
        out["ops"][op] = {"n": len(ss), "aligned": al, "loss_0_2_mean": round(m, 3) if m is not None else None,
                          "ratio_to_baseline": round(m / out["baseline_loss_per_s"], 2) if m is not None and out["baseline_loss_per_s"] else None,
                          "reproduces": bool(m is not None and out["baseline_loss_per_s"] is not None and m >= 3 * out["baseline_loss_per_s"]),
                          "wall_s_median": statistics.median([x["wall_s"] for x in rows if x.get("wall_s") is not None]),
                          "thread_cpu_s_median": statistics.median([x["thread_cpu_s"] for x in rows if x.get("thread_cpu_s") is not None]),
                          "pss_mb_after_min_max": [round(min(x["pss_kb_after"] for x in rows) / 1024, 1),
                                                   round(max(x["pss_kb_after"] for x in rows) / 1024, 1)]}
    p, s = out["ops"]["parse"]["reproduces"], out["ops"]["spawn"]["reproduces"]
    out["names"] = "both" if p and s else "parse" if p else "spawn" if s else "neither"
    json.dump(out, open(os.path.join(HERE, "probe_aligned.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if "--analyse-only" not in sys.argv:
        run()
    analyse()
