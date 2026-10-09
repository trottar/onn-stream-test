#!/usr/bin/env python3
"""E3-A3B -- the verification bar as pre-registered (e3_a3b_preregistration.txt §2): a run is judged on
controller-trigger events only; client_output_silence pauses are counted and reported, not voiding. Read-only over the
repo's logs (the recovery log and its archive, the gap log). Written for this task (pieces follow E3-R2's / E3-A3's
analyses; no other task's script is run). -> validity.json, gaps/<run>.jsonl, e3_a3b_table.md/.json, e3_a3b_verdict.json"""
import glob
import json
import os
import statistics
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
EV = os.path.join(REPO, "docs/memory/evidence")
LOGS = os.path.join(REPO, "logs/games")
NS_PER_PACKET, US_PER_LINE = 51.5, 42.4
REF = {"E1-PS1-STREAM": {"cpu": (9.7, 13.7), "comp": (22.3, 26.3), "label": "E2 PS1-STREAM",
                         "dir": f"{EV}/e2_s1_2026-10-05/runs/E1-PS1-STREAM/run1"},
       "E1-CONC": {"cpu": (20.2, 24.2), "comp": (24.5, 28.5), "label": "E3-S6A CONC",
                   "dir": f"{EV}/e3_s6a_2026-10-07/runs/E1-CONC/run1"}}
tt = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def k(s, *p):
    for x in p:
        s = (s or {}).get(x) if isinstance(s, dict) else None
    return s


def jsonlines(paths):
    seen, out = set(), []
    for f in paths:
        try:
            lines = open(f, errors="replace").read().splitlines()
        except OSError:
            continue
        for l in lines:
            if l not in seen:
                seen.add(l)
                try:
                    out.append(json.loads(l))
                except ValueError:
                    pass
    return out


def main():
    rec = jsonlines(sorted(glob.glob(os.path.join(LOGS, "stream_log_archive/native_stream_recovery.log*")))
                    + [os.path.join(LOGS, "native_stream_recovery.log.1"), os.path.join(LOGS, "native_stream_recovery.log")])
    gaps = jsonlines([os.path.join(LOGS, "native_stream_ctrl_gaps.log.1"), os.path.join(LOGS, "native_stream_ctrl_gaps.log")])
    os.makedirs(os.path.join(HERE, "gaps"), exist_ok=True)
    runs, val = {}, {}
    for sp in sorted(glob.glob(os.path.join(HERE, "runs*", "*", "run*", "summary.json"))):
        s = json.load(open(sp))
        rel = os.path.relpath(os.path.dirname(sp), HERE)
        reached = s.get("status") == "OK" and bool(s.get("window"))
        if not reached:
            val[rel] = {"valid": False, "reason": "never reached PLAYING / failed attempt"}
            continue
        t0, t1 = s["window"]["from"], s["window"]["to"]
        ev = sorted([r for r in rec if t0 <= (r.get("at_utc") or "") <= t1], key=lambda r: r["at_utc"])
        pauses = []
        for i, r in enumerate(ev):
            if r.get("event") != "desync_pause":
                continue
            nxt = next((x for x in ev[i + 1:] if x.get("event") in ("resumed", "gave_up_saved", "session_ended")), None)
            pauses.append({"at_utc": r["at_utc"], "trigger": r.get("trigger"), "age_ms": r.get("age_ms"),
                           "next": None if not nxt else nxt.get("event"), "via": None if not nxt else nxt.get("via"),
                           "after_s": None if not nxt else round(tt(nxt["at_utc"]) - tt(r["at_utc"]), 2)})
        gave_up = [r["at_utc"] for r in ev if str(r.get("event", "")).startswith("gave_up")]
        ctrl = [p for p in pauses if p["trigger"] == "controller_silence"]
        for p in ctrl:
            p["exited_within_10s"] = p["next"] == "resumed" and p["via"] == "controller_return" and p["after_s"] <= 10
        client = [p for p in pauses if str(p["trigger"]).startswith("client_")]
        # paused intervals (any trigger), to tell which > 1-s gaps the old rule would have paused on (state PLAYING)
        paused = []
        for p in pauses:
            end = tt(p["at_utc"]) + (p["after_s"] if p["after_s"] is not None else 1e9)
            paused.append((tt(p["at_utc"]), end))
        g = [x for x in gaps if t0 <= x["start_utc"] <= t1]
        with open(os.path.join(HERE, "gaps", rel.replace("/", "_") + ".jsonl"), "w") as fh:
            fh.writelines(json.dumps(x) + "\n" for x in g)
        over1 = [x for x in g if x["gap_ms"] > 1000]
        old_rule = [x for x in over1 if not any(a <= tt(x["start_utc"]) + 1.0 <= b for a, b in paused)]
        sam = [json.loads(l) for l in open(os.path.join(HERE, rel, "samples.jsonl"))]
        rx = [k(r, "net", "eno1", "rx_pps") for r in sam if t0 <= r["at_utc"] <= t1]
        rx = [x for x in rx if isinstance(x, (int, float))]
        rxm = statistics.median(rx) if rx else 0
        cost = (NS_PER_PACKET * 1e-9 * rxm + len(g) * US_PER_LINE * 1e-6 / (tt(t1) - tt(t0))) * 100
        row = rel.split("/")[1]
        x = {"window": [t0, t1], "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
             "companion_cpu": k(s, "host", "host", "procs.companion.cpu_pct", "mean"),
             "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"), "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
             "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "underruns": k(s, "key", "heartbeat", "audio_underruns"),
             "gave_up_saved": gave_up, "controller_pauses": ctrl, "client_pauses": client,
             "gaps": len(g), "gaps_over_1s": len(over1), "gap_max_ms": max((y["gap_ms"] for y in g), default=None),
             "old_rule_would_have_paused": len(old_rule), "old_rule_gaps": [[y["start_utc"], y["gap_ms"]] for y in old_rule],
             "rx_pps_median": rxm, "gap_log_cost_core_points": round(cost, 5)}
        ref = REF[row]
        x["i"] = not gave_up
        x["ii"] = all(p["exited_within_10s"] for p in ctrl)
        x["iii"] = (x["host_cpu"] is not None and ref["cpu"][0] <= x["host_cpu"] <= ref["cpu"][1]
                    and x["companion_cpu"] is not None and ref["comp"][0] <= x["companion_cpu"] <= ref["comp"][1])
        x["iv"] = cost <= 0.5
        runs[rel] = x
        val[rel] = {"valid": True, "window": [t0, t1], "client_pauses_reported": len(client), "controller_pauses": len(ctrl)}
    json.dump(val, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    judged = {}
    for row in REF:
        order = [f"runs/{row}/run1"] + sorted(r for r in runs if r.startswith(f"runs_retry1/{row}/")) + \
            sorted(r for r in runs if r.startswith(f"runs_retry2/{row}/"))
        judged[row] = next((r for r in order if r in runs), None)
    cols = [(f"{row} (adopted v2)", os.path.join(HERE, rel)) for row, rel in judged.items() if rel] + \
        [(v["label"], v["dir"]) for v in REF.values()] + \
        [("E3-A3 PS1 retry2 (v2, invalid then)", f"{EV}/e3_a3_2026-10-09/runs_retry2/E1-PS1-STREAM/run1"),
         ("E3-A3 CONC retry2 (v2, invalid then)", f"{EV}/e3_a3_2026-10-09/runs_retry2/E1-CONC/run1")]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_a3b_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    out = {"judged": judged, "rows": {r: runs[j] for r, j in judged.items() if j}}
    if not all(judged.values()):
        out["verdict"] = "ADOPTION REVERTED (broke the row: no run reached PLAYING after two replacements)"
    else:
        failed = [c for c in ("i", "ii", "iii", "iv") if not all(runs[j][c] for j in judged.values())]
        out["clauses"] = {c: all(runs[j][c] for j in judged.values()) for c in ("i", "ii", "iii", "iv")}
        out["verdict"] = "ADOPTION STANDS" if not failed else f"ADOPTION REVERTED ({', '.join(failed)})"
    json.dump(out, open(os.path.join(HERE, "e3_a3b_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
