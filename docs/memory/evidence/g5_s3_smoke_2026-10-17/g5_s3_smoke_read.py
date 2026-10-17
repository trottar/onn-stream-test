#!/usr/bin/env python3
"""G5-S3 / G5-S4 LAN smoke: the run read against preregistration.txt as hashed. Read-only.

Inputs: runs/E1-PS1-STREAM_flag/run1/ (the suite's summary.json, decisions.jsonl, status_poll.jsonl, encoder.jsonl
for E4-S5D's segment-aware capture), and the live ladder log logs/games/adaptive_bitrate_shadow.jsonl from the run's
start (run_started_at.txt) to its end (run_ended_at.txt) -- copied, sliced, to ladder_log_run.jsonl.
Outputs: reading.json, reading.md, validity.json. References: CL-B3 R1 / W (cl_b3_verdict.json) and the G8-S1 `none`
cells (g8_s1_cells_read_final.json)."""
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RD = HERE / "runs" / "E1-PS1-STREAM_flag" / "run1"
EV = HERE.parent
spec = importlib.util.spec_from_file_location("s5d", EV / "e4_s5d_2026-10-15/e4_s5d_analysis.py")
S5D = importlib.util.module_from_spec(spec)
sys.argv = [sys.argv[0]]
spec.loader.exec_module(S5D)


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()]


def main():
    s = json.loads((RD / "summary.json").read_text())
    rf = k(s, "teardown", "report_fields") or {}
    mins = (rf.get("duration_ms") or 0) / 60000
    hh = lambda key: k(s, "host", "host", key, "mean")
    cap, dd = S5D.segcap(RD, s)
    dec = jl(RD / "decisions.jsonl")
    polls = [r for r in jl(RD / "status_poll.jsonl") if isinstance(r.get("bitrate_kbps"), (int, float))]
    rungs = Counter(int(r["bitrate_kbps"]) for r in polls)
    t0, t1 = (HERE / "run_started_at.txt").read_text().strip(), (HERE / "run_ended_at.txt").read_text().strip()
    live_all = [json.loads(l) for l in open(ROOT / "logs/games/adaptive_bitrate_shadow.jsonl") if l.strip()]
    live = [r for r in live_all if t0 <= r.get("at_utc", "") <= t1]
    (HERE / "ladder_log_run.jsonl").write_text("".join(json.dumps(r) + "\n" for r in live))
    # the flagged process: from its controller_start (the first after t0) to the next controller_start (teardown's)
    starts = [i for i, r in enumerate(live) if r.get("event") == "controller_start"]
    flagged = live[starts[0]:starts[1]] if len(starts) > 1 else live[starts[0]:] if starts else []
    is4000 = lambda r: 4000 in (r.get("to_kbps"), r.get("target_kbps"), r.get("level_kbps"), r.get("stream_kbps"))
    capcfg = [r for r in flagged if r.get("event") == "remote_cap_config"]
    out = {
        "status": s.get("status"), "window": s.get("window"), "playing": k(s, "launch", "stream"),
        "environ_at_restart": k(s, "restart", "environ"), "environ_under_load": k(s, "profile_at_playing", "environ")
        if isinstance(k(s, "profile_at_playing"), dict) else None,
        "gates": {"retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "capture_fps": cap, "dupdrop_per_min": dd,
                  "flags_absent_after": k(s, "teardown", "flags_absent")},
        "host_cpu": hh("cpu.mean_pct"), "companion_cpu": hh("procs.companion.cpu_pct"),
        "retroarch_cpu": hh("procs.retroarch.cpu_pct"), "encoder_cpu": hh("procs.encoder.cpu_pct"),
        "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"), "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
        "resyncs_window": k(s, "key", "heartbeat", "stream_resyncs"), "resyncs_session": rf.get("video.sequence_resyncs"),
        "stale_per_min": round(rf["decoder.stale_output_drops"] / mins, 3) if mins and "decoder.stale_output_drops" in rf else None,
        "spikes20_per_min": round(rf["decoder.spike_20_ms"] / mins, 2) if mins and "decoder.spike_20_ms" in rf else None,
        "client_pauses": len(k(s, "key", "recovery", "client_pauses") or []), "recovery_key": k(s, "key", "recovery"),
        "decisions_rows": len(dec), "decisions_path_class": dict(Counter(str(r.get("path_class")) for r in dec)),
        "decisions_events": dict(Counter(r.get("event") for r in dec)),
        "acted": [{x: r.get(x) for x in ("at_utc", "event", "from_kbps", "to_kbps", "reason")} for r in dec if r.get("acted")],
        "rows_4000_window": sum(1 for r in dec if is4000(r)), "rows_remote_cap_window": sum(1 for r in dec if "remote_cap" in (r.get("reason"), r.get("trigger"), r.get("source"))),
        "rung_polls": {str(r): n for r, n in sorted(rungs.items())},
        "live_rows": len(live), "live_events": dict(Counter(r.get("event") for r in live)),
        "flagged_rows": len(flagged), "flagged_path_class": dict(Counter(str(r.get("path_class")) for r in flagged)),
        "flagged_rows_4000": sum(1 for r in flagged if is4000(r)),
        "flagged_rows_remote_cap_decision": sum(1 for r in flagged if r.get("event") != "remote_cap_config" and
                                                "remote_cap" in (r.get("reason"), r.get("trigger"), r.get("source"))),
        "remote_cap_config_rows": capcfg,
        "unflagged_rows": [{x: r.get(x) for x in ("at_utc", "event", "path_class")} for r in live if r not in flagged],
    }
    cl = {x["label"]: x for x in json.loads((EV / "cl_b3_2026-10-16/cl_b3_verdict.json").read_text())["runs"]}
    g8 = [r for r in json.loads((EV / "g8_s1_2026-10-16/g8_s1_cells_read_final.json").read_text()) if r["profile"] == "none"]
    out["reference"] = {
        **{f"CL-B3 {l}": {"host_cpu": cl[l]["host_cpu"], "companion_cpu": cl[l]["procs_cpu_pct_of_core"]["companion"],
                          "rung": cl[l]["rung_kbps_range"], "ladder_acted": cl[l].get("ladder_acted"),
                          "rendered_fps": cl[l]["rendered_fps"], "loss_per_min": cl[l]["loss_per_min"], "resyncs": cl[l]["resyncs"],
                          "dropin": cl[l].get("dropin")} for l in ("R1", "W")},
        **{f"G8-S1 {r['cell']}": {"host_cpu": r["host_cpu"], "companion_cpu": r["companion_cpu"], "rung": [r["rung_min"], r["rung_max"]],
                                   "ladder_acted": r["ladder_acted"], "rendered_fps": r["rendered_fps"],
                                   "loss_per_min": r["loss_per_min_heartbeat"], "resyncs": r["resyncs_window"]} for r in g8}}
    g = out["gates"]
    out["gate_results"] = {"retroarch": (g["retroarch_fps"] or 0) >= 59.9, "capture": g["capture_fps"] is not None and abs(g["capture_fps"] - 60) <= 0.1,
                           "dupdrop": g["dupdrop_per_min"] is not None and g["dupdrop_per_min"] <= 0.2, "flags_absent": g["flags_absent_after"] is True}
    out["expected"] = {
        "1_path_class_lan": set(out["decisions_path_class"]) == {"lan"} and set(out["flagged_path_class"]) == {"lan"},
        "2_no_4000_no_remote_cap_row_config_once": out["rows_4000_window"] == 0 and out["flagged_rows_4000"] == 0
        and out["rows_remote_cap_window"] == 0 and out["flagged_rows_remote_cap_decision"] == 0 and "4000" not in out["rung_polls"]
        and len(capcfg) == 1,
        "3_rung_path_adopted": out["rung_polls"] == {"7000": sum(rungs.values())} and not out["acted"],
    }
    (HERE / "reading.json").write_text(json.dumps(out, indent=1) + "\n")
    (HERE / "validity.json").write_text(json.dumps({"E1-PS1-STREAM_flag/run1": "valid" if out["status"] == "OK" and (out["playing"] or {}).get("ok") else "invalid"}, indent=1) + "\n")
    md = ["| run | host CPU % | companion % core | rung | ladder acted | rendered | loss/min | resyncs (window) |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for lab, x in out["reference"].items():
        md.append(f"| {lab} | {x['host_cpu']} | {x['companion_cpu']} | {x['rung']} | {x['ladder_acted']} | {x['rendered_fps']} | {x['loss_per_min']} | {x['resyncs']} |")
    md.append(f"| G5-S3 smoke (3 flags) | {out['host_cpu']} | {out['companion_cpu']} | {out['rung_polls']} | {len(out['acted'])} | "
              f"{out['rendered_fps']} | {out['loss_per_min']} | {out['resyncs_window']} |")
    (HERE / "reading.md").write_text("\n".join(md) + "\n")
    print(json.dumps({x: out[x] for x in ("status", "gates", "gate_results", "expected", "decisions_path_class", "flagged_path_class",
                                          "rung_polls", "acted", "remote_cap_config_rows", "unflagged_rows", "live_events",
                                          "host_cpu", "companion_cpu", "loss_per_min", "rendered_fps", "resyncs_window",
                                          "resyncs_session", "stale_per_min", "spikes20_per_min", "client_pauses")}, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
