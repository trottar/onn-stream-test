#!/usr/bin/env python3
"""E3-A3 -- the verification bar as pre-registered (e3_a3_preregistration.txt §2). Adapted from E3-R2's
e3_r2_analysis.py (copied here, not run there). Read-only over the repo's logs. E3-A2's validity rule, re-implemented,
with the pre-registered exception: a controller_silence pause that resumed via controller_return within 10 s is
reported and the run still counts. -> validity.json, gaps/<run>.jsonl, e3_a3_table.md/.json, e3_a3_verdict.json"""
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
REF = {"E1-PS1-STREAM": {"label": "E3-R2 PS1 r1 (same code)", "cpu": (9.69, 13.69), "comp": (23.0, 27.2),
                         "dir": f"{EV}/e3_r2_2026-10-08/runs/E1-PS1-STREAM_flag/run1"},
       "E1-CONC": {"label": "E3-R2 CONC r2 (same code)", "cpu": (18.9, 25.4), "comp": (24.0, 29.1),
                   "dir": f"{EV}/e3_r2_2026-10-08/runs/E1-CONC_flag/run2"}}
COLS_EXTRA = [("E2 PS1-STREAM", f"{EV}/e2_s1_2026-10-05/runs/E1-PS1-STREAM/run1"),
              ("E3-S6A CONC", f"{EV}/e3_s6a_2026-10-07/runs/E1-CONC/run1")]


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
        evs = sorted(ev, key=lambda r: r["at_utc"])
        excused = set()
        for i, r in enumerate(evs):
            if r.get("event") == "desync_pause" and r.get("trigger") == "controller_silence":
                nxt = next((x for x in evs[i + 1:] if x.get("event") in ("resumed", "gave_up_saved", "session_ended")), None)
                if nxt and nxt.get("event") == "resumed" and nxt.get("via") == "controller_return" \
                        and tt(nxt["at_utc"]) - tt(r["at_utc"]) <= 10.0:
                    excused.add(r["at_utc"])
        bad_counting = [b for b in bad if b["event"] == "desync_pause" and b["at_utc"] not in excused
                        or str(b["event"] or "").startswith("gave_up")]
        runs[rel] = {"summary": s, "window": [t0, t1], "valid": not bad_counting, "events": bad,
                     "excused_controller_pauses": sorted(excused), "all_events": ev}
    json.dump({r: {"window": v["window"], "valid": v["valid"], "events": v["events"],
                   "excused_controller_pauses": v["excused_controller_pauses"]} for r, v in runs.items()},
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
        order = [f"runs/{row}/run1"] + sorted(x for x in runs if x.startswith(f"runs_retry1/{row}/")) \
            + sorted(x for x in runs if x.startswith(f"runs_retry2/{row}/"))
        ok = [c for c in order if c in runs and runs[c]["valid"]][:1]
        return ok + [None] * (1 - len(ok))
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
            x["iii"] = x["host_cpu"] is not None and ref["cpu"][0] <= x["host_cpu"] <= ref["cpu"][1]
            x["iv"] = x["companion_cpu"] is not None and ref["comp"][0] <= x["companion_cpu"] <= ref["comp"][1]
            x["gaps_over_1s"] = [[y["start_utc"], y["gap_ms"]] for y in g if y["gap_ms"] > 1000]
            x["v"] = cost <= 0.5
            per[f"{row} r{n}"] = x
    cols = [(f"{lab} (flag)", os.path.join(HERE, v["judged"])) for lab, v in per.items() if v.get("judged")]
    cols += [(v["label"], v["dir"]) for v in REF.values()] + COLS_EXTRA
    subprocess.run([sys.executable, os.path.join(REPO, "tools/e3_table.py"), os.path.join(HERE, "e3_a3_table.md")]
                   + [f"{a}={b}" for a, b in cols], check=True, stdout=subprocess.DEVNULL)
    broke = any(not v.get("judged") for v in per.values())
    out = {"i": ii, "ii": not broke and all(v.get("judged") for v in per.values()), "rows": per,
           "iii": all(v.get("iii") for v in per.values()), "iv": all(v.get("iv") for v in per.values()),
           "v": all(v.get("v") for v in per.values())}
    if not out["ii"]:
        # (iii)-(v) are judged on valid runs only; with none, they are not evaluable (reported per window below)
        for c in ("iii", "iv", "v"):
            out[c] = "not evaluable (no valid run)"
    ok = ii["holds"] and out["ii"] is True and out["iii"] is True and out["iv"] is True and out["v"] is True
    failed = [c for c, h in (("i", ii["holds"]), ("ii", out["ii"])) if h is not True] + \
        [c for c in ("iii", "iv", "v") if out[c] is False]
    out["verdict"] = "ADOPTION STANDS" if ok else \
        ("ADOPTION REVERTED (ii: broke the row -- no valid run after two replacements)" if not out["ii"] else
         f"ADOPTION REVERTED ({', '.join(failed)})")
    # reported, every window (valid or not): the numbers the bar would have read
    allw = {}
    for rel, v in sorted(runs.items()):
        s2, (t0, t1) = v["summary"], v["window"]
        g2 = [y for y in gaps if t0 <= y["start_utc"] <= t1]
        sam = [json.loads(l) for l in open(os.path.join(HERE, rel, "samples.jsonl"))]
        rx = [k(r, "net", "eno1", "rx_pps") for r in sam if t0 <= r["at_utc"] <= t1]
        rx = [x for x in rx if isinstance(x, (int, float))]
        rxm = statistics.median(rx) if rx else 0
        allw[rel] = {"valid": v["valid"],
                     "client_pauses": sum(1 for e in v["all_events"] if e.get("event") == "desync_pause" and str(e.get("trigger", "")).startswith("client_")),
                     "controller_pauses": sum(1 for e in v["all_events"] if e.get("event") == "desync_pause" and e.get("trigger") == "controller_silence"),
                     "gave_up_saved": sum(1 for e in v["all_events"] if str(e.get("event", "")).startswith("gave_up")),
                     "host_cpu": k(s2, "host", "host", "cpu.mean_pct", "mean"),
                     "companion_cpu": k(s2, "host", "host", "procs.companion.cpu_pct", "mean"),
                     "rendered_fps": k(s2, "key", "heartbeat", "rendered_fps"),
                     "loss_per_min": k(s2, "key", "heartbeat", "video_loss_per_min"),
                     "resyncs": k(s2, "key", "heartbeat", "stream_resyncs"), "underruns": k(s2, "key", "heartbeat", "audio_underruns"),
                     "gaps": len(g2), "gaps_over_1s": sum(1 for y in g2 if y["gap_ms"] > 1000),
                     "gap_max_ms": max((y["gap_ms"] for y in g2), default=None),
                     "gap_log_cost_core_points": round((NS_PER_PACKET * 1e-9 * rxm + len(g2) * US_PER_LINE * 1e-6 / (tt(t1) - tt(t0))) * 100, 5)}
    out["all_windows_reported"] = allw
    json.dump(out, open(os.path.join(HERE, "e3_a3_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    sys.exit(main())
