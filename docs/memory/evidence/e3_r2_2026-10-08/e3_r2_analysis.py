#!/usr/bin/env python3
"""E3-R2 -- the run bar as pre-registered (e3_r2_preregistration.txt §2), plus clause (i) from replay.json. Read-only
over the repo's logs. E3-A2's validity rule (its definition, re-implemented here so no other task's script runs: a run
whose recovery state leaves PLAYING inside its window is invalid; its replacement in runs_retry<n>/ takes its place).
-> validity.json, gaps/<run>.jsonl, e3_r2_table.md/.json (tools/e3_table.py), e3_r2_verdict.json"""
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
REF = {"E1-PS1-STREAM_flag": {"label": "E2 PS1-STREAM", "cpu": 11.69, "fps": 59.81, "comp": 24.3,
                              "dir": f"{EV}/e2_s1_2026-10-05/runs/E1-PS1-STREAM/run1"},
       "E1-CONC_flag": {"label": "E3-S6A CONC", "cpu": 22.2, "fps": 57.64, "comp": 26.5,
                        "dir": f"{EV}/e3_s6a_2026-10-07/runs/E1-CONC/run1"}}


def tt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


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
            if l in seen:
                continue
            seen.add(l)
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def recovery_lines():
    return jsonlines(sorted(glob.glob(os.path.join(LOGS, "stream_log_archive/native_stream_recovery.log*")))
                     + [os.path.join(LOGS, "native_stream_recovery.log.1"), os.path.join(LOGS, "native_stream_recovery.log")])


def gap_lines():
    return jsonlines([os.path.join(LOGS, "native_stream_ctrl_gaps.log.1"), os.path.join(LOGS, "native_stream_ctrl_gaps.log")])


def main():
    rec, gaps = recovery_lines(), gap_lines()
    runs = {}
    for sp in sorted(glob.glob(os.path.join(HERE, "runs*", "*", "run*", "summary.json"))):
        s = json.load(open(sp))
        if s.get("kind") != "stream" or not s.get("window"):
            continue
        rel = os.path.relpath(os.path.dirname(sp), HERE)
        t0, t1 = s["window"]["from"], s["window"]["to"]
        ev = [r for r in rec if t0 <= (r.get("at_utc") or "") <= t1]
        bad = [{"at_utc": r.get("at_utc"), "event": r.get("event"), "state": r.get("state"), "trigger": r.get("trigger"),
                "via": r.get("via")} for r in ev if r.get("event") == "desync_pause" or str(r.get("event", "")).startswith("gave_up")
               or str(r.get("state", "")).startswith("PAUSED")]
        runs[rel] = {"summary": s, "window": [t0, t1], "valid": not bad, "events": bad, "all_events": ev}
    json.dump({r: {"window": v["window"], "valid": v["valid"], "events": v["events"]} for r, v in runs.items()},
              open(os.path.join(HERE, "validity.json"), "w"), indent=1)

    # (ii) over every window run, replaced or not
    ii = {"gave_up_saved": [], "controller_pauses": [], "client_pauses": []}
    for rel, v in runs.items():
        evs = sorted(v["all_events"], key=lambda r: r["at_utc"])
        for i, r in enumerate(evs):
            if str(r.get("event", "")).startswith("gave_up"):
                ii["gave_up_saved"].append([rel, r["at_utc"]])
            if r.get("event") == "desync_pause":
                nxt = next((x for x in evs[i + 1:] if x.get("event") in ("resumed", "gave_up_saved", "session_ended")), None)
                item = {"run": rel, "at_utc": r["at_utc"], "trigger": r.get("trigger"), "age_ms": r.get("age_ms"),
                        "next": None if not nxt else {"event": nxt.get("event"), "at_utc": nxt["at_utc"], "via": nxt.get("via"),
                                                      "after_s": round(tt(nxt["at_utc"]) - tt(r["at_utc"]), 2)}}
                if r.get("trigger") == "controller_silence":
                    item["exited_by_part3_within_10s"] = bool(nxt and nxt.get("event") == "resumed"
                                                              and nxt.get("via") == "controller_return"
                                                              and tt(nxt["at_utc"]) - tt(r["at_utc"]) <= 10.0)
                    ii["controller_pauses"].append(item)
                else:
                    ii["client_pauses"].append(item)
    ii["holds"] = not ii["gave_up_saved"] and all(x["exited_by_part3_within_10s"] for x in ii["controller_pauses"])

    def judged_for(row):
        """the first two valid runs: runs/<row>/run1, run2, then the replacements in runs_retry1/, runs_retry2/"""
        order = [f"runs/{row}/run1", f"runs/{row}/run2"] + sorted(x for x in runs if x.startswith(f"runs_retry1/{row}/")) \
            + sorted(x for x in runs if x.startswith(f"runs_retry2/{row}/"))
        ok = [c for c in order if c in runs and runs[c]["valid"]][:2]
        return ok + [None] * (2 - len(ok))
    judged = {row: judged_for(row) for row in REF}
    os.makedirs(os.path.join(HERE, "gaps"), exist_ok=True)
    per = {}
    for row, rels in judged.items():
        ref = REF[row]
        for n, rel in enumerate(rels, 1):
            if not rel:
                per[f"{row} r{n}"] = {"judged": None}
                continue
            s, rd = runs[rel]["summary"], os.path.join(HERE, rel)
            t0, t1 = runs[rel]["window"]
            g = [x for x in gaps if t0 <= x["start_utc"] <= t1]
            with open(os.path.join(HERE, "gaps", rel.replace("/", "_") + ".jsonl"), "w") as fh:
                fh.writelines(json.dumps(x) + "\n" for x in g)
            sam = [json.loads(l) for l in open(os.path.join(rd, "samples.jsonl"))]
            rx = [k(r, "net", "eno1", "rx_pps") for r in sam if t0 <= r["at_utc"] <= t1]
            rx = [x for x in rx if isinstance(x, (int, float))]
            rxm = statistics.median(rx) if rx else None
            win_s = tt(t1) - tt(t0)
            cost = (NS_PER_PACKET * 1e-9 * (rxm or 0) + len(g) * US_PER_LINE * 1e-6 / win_s) * 100
            logged = sorted(tt(x["logged_utc"]) for x in gaps if x.get("logged_utc"))
            own = [x for x in g if any(0 <= tt(x["start_utc"]) - L <= 0.05 for L in logged)]
            gm = [x["gap_ms"] for x in g]
            x = {"judged": rel, "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
                 "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
                 "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
                 "underruns": k(s, "key", "heartbeat", "audio_underruns"), "resyncs": k(s, "key", "heartbeat", "stream_resyncs"),
                 "companion_cpu": k(s, "host", "host", "procs.companion.cpu_pct", "mean"),
                 "gaps": {"count": len(g), "max_ms": max(gm, default=None), "over_500": sum(1 for v in gm if v > 500),
                          "over_1000": sum(1 for v in gm if v > 1000), "over_5000": sum(1 for v in gm if v > 5000),
                          "burst_max": max((v["burst_500ms"] for v in g), default=None)},
                 "rx_pps_median": rxm, "gap_log_cost_core_points": round(cost, 5), "gaps_after_own_write": len(own)}
            x["iii"] = (x["host_cpu"] is not None and abs(x["host_cpu"] - ref["cpu"]) <= 2
                        and x["rendered_fps"] is not None and abs(x["rendered_fps"] - ref["fps"]) <= 0.5)
            x["iv"] = x["companion_cpu"] is not None and abs(x["companion_cpu"] - ref["comp"]) <= 2
            x["v"] = cost <= 0.5 and not own
            per[f"{row} r{n}"] = x
    rp = json.load(open(os.path.join(HERE, "replay.json")))["bar"]
    i_ = {c: rp[c] for c in ("r1", "r2", "r3", "r4")}
    cols = [(f"{lab} (flag)", os.path.join(HERE, v["judged"])) for lab, v in per.items() if v.get("judged")]
    cols += [(v["label"], v["dir"]) for v in REF.values()]
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_r2_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    broke = any(not v.get("judged") for v in per.values())
    out = {"i_replay": i_, "i": rp["replay_bar_holds"], "ii": ii, "rows": per,
           "iii": all(v.get("iii") for v in per.values()), "iv": all(v.get("iv") for v in per.values()),
           "v": all(v.get("v") for v in per.values())}
    ok = out["i"] and ii["holds"] and out["iii"] and out["iv"] and out["v"]
    out["verdict"] = "REJECTED (broke the row: no valid run after two replacements)" if broke else \
        ("ACCEPTED" if ok else "REJECTED")
    json.dump(out, open(os.path.join(HERE, "e3_r2_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
