#!/usr/bin/env python3
"""E3-S7 probe: the grabber child's share of the CONC loss, CPU vs network. Three spawn-only arms against a live PS1
stream (E1-PS1-STREAM's launch), one session each, the 1-s sampler (--e2 --telemetry) on (eno1 rx/tx per second, the
busiest core, the epg category = the grabber tree), E3-S6's probe hook (PRIVYHUB_MEM_PROBE=1: op=prepare once, then
op=spawn = the grabber child for the prepared candidate, no parse, no cache write):
  A -- the child as today;
  B -- the child at SCHED_IDLE / nice 19 / idle I/O (E3-S1's flag PRIVYHUB_EPG_GRAB_PRIORITY=idle): CPU removed;
  C -- the child in its own user + network namespace (this task's probe hook PRIVYHUB_EPG_GRAB_NONET=1: `unshare -rn`,
       no route, loopback down): its start-up as today, its fetch fails at the first DNS lookup, nothing leaves the host.
Per session: drop-in, restart, launch, PLAYING, 60 s settle, 60 s quiet, prepare x1, spawn x20 at 15-s spacing, 15 s,
E1's teardown (drop-in removed, the adopted environ checked). Channel CNBCUK.uk@SD (E3-S6's). -> probe_<arm>/ (sampler),
probe_triggers_<arm>.jsonl, probe_run_<arm>.json; then the alignment (e2_analysis.py's loss series, offsets 0..10 s)
-> probe_aligned.json. Reading rule (the task's, before the probe): the arm whose 0-2 s loss falls to <= 25 % of A's
names the cause -- B -> CPU; C -> network; both -> both (the change is then the network one); neither -> report, and
the change is the network one by default."""
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
V = load("e3a2v", "docs/memory/evidence/e3_a2_2026-10-07/e3_a2_validity.py")
CH = "CNBCUK.uk@SD"
ARMS = {"A": ["PRIVYHUB_MEM_PROBE=1"], "B": ["PRIVYHUB_MEM_PROBE=1", "PRIVYHUB_EPG_GRAB_PRIORITY=idle"],
        "C": ["PRIVYHUB_MEM_PROBE=1", "PRIVYHUB_EPG_GRAB_NONET=1"]}
# E3-A2's standing validity rule: a session whose recovery state leaves PLAYING inside its trigger window is invalid and
# is replaced (at most twice); the replacement of arm X is X_r1, X_r2 with X's flags. `--arms A,B_r1` runs only those.
for _x in ("B", "C"):
    for _n in (1, 2):
        ARMS[f"{_x}_r{_n}"] = ARMS[_x]


def session(arm):
    kvs = ARMS[arm]
    rec = {"arm": arm, "flags": kvs, "started_utc": E.utc(), "preflight": E.preflight(), "channel": CH}
    if not rec["preflight"]["ok"]:
        raise SystemExit(f"preflight not clean: {rec['preflight']}")
    before = set(os.listdir(E.SESSDIR))
    sd = os.path.join(HERE, f"probe_{arm}")
    os.makedirs(sd, exist_ok=True)
    samp = None
    trig = open(os.path.join(HERE, f"probe_triggers_{arm}.jsonl"), "w")
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
        samp = subprocess.Popen([sys.executable, os.path.join(REPO, "tools/e1_sampler.py"), "run", sd, "--e2", "--telemetry"],
                                stdout=open(os.path.join(sd, "sampler.log"), "w"), stderr=subprocess.STDOUT)
        time.sleep(60)
        rec["quiet_from"] = E.utc()
        time.sleep(60)
        for op, n in (("prepare", 1), ("spawn", 20)):
            for i in range(n):
                t0 = time.time()
                code, d = E.http("GET", f"/plugins/epg/memprobe?op={op}&channel_id={CH.replace('@', '%40')}", 150)
                trig.write(json.dumps({"op": op, "i": i, "start_utc": E.utc(t0), "end_utc": E.utc(), "http": code,
                                       **{k: d.get(k) for k in ("wall_s", "thread_cpu_s", "ok", "programmes", "candidates")}}) + "\n")
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
        E.teardown_flags({"dropin": kvs}, td)
        td["apk"] = "CONFIRMED" if E.apk_hash() == E.EXPECT_APK else "MISMATCH"
        td["ps1_files_identical"] = E.ps1_files_identical()
        td["retroarch_left"], td["encoder_left"] = len(E.retroarch_pids()), len(E.encoder_pids())
        rec["teardown"] = td
        rec["ended_utc"] = E.utc()
        json.dump(rec, open(os.path.join(HERE, f"probe_run_{arm}.json"), "w"), indent=1, default=str)
    return rec


def analyse():
    ev = list(V.events())
    out = {"arms": {}}
    for arm in ARMS:
        p = os.path.join(HERE, f"probe_run_{arm}.json")
        if not os.path.exists(p):
            continue
        rec = json.load(open(p))
        trig = [json.loads(l) for l in open(os.path.join(HERE, f"probe_triggers_{arm}.jsonl"))]
        t0, t1 = A.t(rec["quiet_from"]), A.t(rec["triggers_to"]) + 10
        L = A.hb_loss_series(t0, t1)
        S = {}
        for r in A.jl(os.path.join(HERE, f"probe_{arm}", "samples.jsonl")):
            e = (r.get("net") or {}).get("eno1") or {}
            epg = (r.get("procs") or {}).get("epg") or {}
            S[int(A.t(r["at_utc"]))] = {"busiest": (r.get("cpu") or {}).get("max_pct"), "rx": e.get("rx_kBps"),
                                        "tx": e.get("tx_kBps"), "epg_cpu": epg.get("cpu_pct"), "epg_pss": epg.get("pss_kb")}
        starts = [int(A.t(x["start_utc"])) for x in trig if x["op"] == "spawn"]
        near = set(s + o for s in starts for o in range(0, 11))
        base = [v for sec, v in L.items() if sec not in near]
        bq = lambda k: [v[k] for sec, v in S.items() if t0 <= sec <= t1 and sec not in near and v.get(k) is not None]
        al = {k: [] for k in ("loss", "busiest", "rx_kBps", "tx_kBps", "epg_cpu")}
        for o in range(11):
            for k, src in (("loss", None), ("busiest", "busiest"), ("rx_kBps", "rx"), ("tx_kBps", "tx"), ("epg_cpu", "epg_cpu")):
                vals = [L.get(s + o) for s in starts] if k == "loss" else [(S.get(s + o) or {}).get(src) for s in starts]
                vals = [v for v in vals if v is not None]
                al[k].append(round(statistics.mean(vals), 2) if vals else None)
        m02 = [x for x in al["loss"][:3] if x is not None]
        m = statistics.mean(m02) if m02 else None
        sp = [x for x in trig if x["op"] == "spawn"]
        bad = [r for r in ev if rec["quiet_from"] <= (r.get("at_utc") or "") <= rec["triggers_to"]
               and (r.get("event") == "desync_pause" or str(r.get("event", "")).startswith("gave_up"))]
        pss = [v["epg_pss"] for sec, v in S.items() if t0 <= sec <= t1 and v.get("epg_pss")]
        out["arms"][arm] = {"n": len(starts), "aligned": al, "loss_0_2_mean": round(m, 3) if m is not None else None,
                            "baseline_loss_per_s": round(statistics.mean(base), 3) if base else None,
                            "baseline_busiest": round(statistics.mean(bq("busiest")), 1) if bq("busiest") else None,
                            "baseline_rx_kBps": round(statistics.mean(bq("rx")), 1) if bq("rx") else None,
                            "baseline_tx_kBps": round(statistics.mean(bq("tx")), 1) if bq("tx") else None,
                            "spawn_ok": sum(1 for x in sp if x.get("ok")), "spawn_wall_s_median": statistics.median([x["wall_s"] for x in sp if x.get("wall_s") is not None]) if sp else None,
                            "epg_peak_pss_mb": round(max(pss) / 1024, 1) if pss else None,
                            "valid": not bad, "recovery_events": [(r.get("at_utc"), r.get("event"), r.get("trigger")) for r in bad]}
    # the validity rule: each arm is judged on its first valid session (X, then X_r1, X_r2); invalid ones are reported
    judged = {}
    for x in ("A", "B", "C"):
        judged[x] = next((n for n in (x, f"{x}_r1", f"{x}_r2") if (out["arms"].get(n) or {}).get("valid")), None)
    out["judged_sessions"] = judged
    pick = lambda x: (out["arms"].get(judged[x]) or {}).get("loss_0_2_mean") if judged[x] else None
    a = pick("A")
    res = {}
    for arm in ("B", "C"):
        x = pick(arm)
        res[arm] = (x is not None and a is not None and x <= 0.25 * a)
    out["at_most_25pct_of_A"] = res
    b, c = res["B"], res["C"]
    out["names"] = "both" if b and c else "CPU" if b else "network" if c else "neither"
    out["change"] = "network (PRIVYHUB_EPG_GRAB_NET=paced)" if out["names"] in ("network", "both", "neither") else "CPU (PRIVYHUB_EPG_GRAB_PRIORITY=idle)"
    json.dump(out, open(os.path.join(HERE, "probe_aligned.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if "--analyse-only" not in sys.argv:
        todo = sys.argv[sys.argv.index("--arms") + 1].split(",") if "--arms" in sys.argv else ["A", "B", "C"]
        for arm in todo:
            session(arm)
    analyse()
