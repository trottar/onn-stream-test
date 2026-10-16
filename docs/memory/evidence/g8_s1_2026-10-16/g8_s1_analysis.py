#!/usr/bin/env python3
"""G8-S1 (partial): the completed cells read from the driver's files only -- cells.jsonl, runs/<cell>/ (the suite's
summary.json, status_poll.jsonl, decisions.jsonl, recovery.jsonl, gaps.jsonl), wan_poll_run<n>.jsonl and
impairment_run<n>.jsonl -- against g8_s1_preregistration.txt as hashed. Read-only.
-> g8_s1_table.md, g8_s1_cells_read.json, validity.json.

Field sources (named in the record):
- resyncs_window: summary key.heartbeat.stream_resyncs (the driver's `resyncs`; the heartbeat over the 600-s window);
  resyncs_session: summary teardown.report_fields["video.sequence_resyncs"] (the client's end-of-session report: the
  whole session, warm-up included).
- loss pre/post-FEC per min and FEC groups: the last wan poll's measures.packet_loss_per_min.{pre_fec,post_fec} and
  measures.fec_groups.{recovered_packets,unrecoverable_groups} (G5-S1's per-session object, the session so far);
  loss_per_min (heartbeat) beside them.
- rules suggestions: decisions.jsonl rows with source == "wan_rules", by rule id."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLB3 = HERE.parent / "cl_b3_2026-10-16/cl_b3_verdict.json"
INTENT = {"none": "clean", "loss-1": "lossy", "loss-5": "lossy", "burst-50x20": "lossy", "delay-50": "-",
          "delay-150": "latency-limited", "jitter-30": "-", "reorder-5": "-", "cap-6000": "capacity-limited",
          "cap-4500": "capacity-limited", "delay-50+loss-1": "lossy"}


def jl(p):
    try:
        return [json.loads(l) for l in open(p) if l.strip()]
    except OSError:
        return []


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def read(row):
    cdir = HERE / "runs" / row["cell"]
    rd = HERE / row["run_dir"] if row.get("run_dir") else None
    s = json.loads((rd / "summary.json").read_text()) if rd and (rd / "summary.json").exists() else {}
    rf = k(s, "teardown", "report_fields") or {}
    polls = [p for p in jl(cdir / f"wan_poll_run{row['attempt']}.jsonl") if isinstance(p.get("wan"), dict)]
    last = polls[-1]["wan"] if polls else {}
    m = last.get("measures") or {}
    rungs = Counter(int(r["bitrate_kbps"]) for r in jl(rd / "status_poll.jsonl") if isinstance(r.get("bitrate_kbps"), (int, float))) if rd else Counter()
    dec = jl(rd / "decisions.jsonl") if rd else []
    rules = Counter(r.get("rule") for r in dec if r.get("source") == "wan_rules")
    acted = [r for r in dec if r.get("acted")]
    sh = row.get("shim") or {}
    out = {
        "n": row["n"], "cell": row["cell"], "profile": row["profile"], "arm": row["arm"], "validity": row["validity"],
        "attempt": row["attempt"], "playing": k(s, "launch", "stream"),
        "retroarch_fps": row.get("retroarch_fps"), "capture_fps": row.get("capture_fps"), "dupdrop_per_min": row.get("dupdrop_per_min"),
        "gate_retroarch": (row.get("retroarch_fps") or 0) >= 59.9,
        "gate_capture": row.get("capture_fps") is not None and abs(row["capture_fps"] - 60) <= 0.1,
        "gate_dupdrop": row.get("dupdrop_per_min") is not None and row["dupdrop_per_min"] <= 0.2,
        "gate_flags_absent": bool(row.get("flags_absent_after")) and bool(row.get("final_flags_absent")),
        "host_cpu": row.get("host_cpu"), "companion_cpu": row.get("companion_cpu"), "shim_cpu_pct_core": row.get("shim_cpu_pct_core"),
        "loss_per_min_heartbeat": row.get("loss_per_min"),
        "loss_pre_fec_per_min": k(m, "packet_loss_per_min", "value", "pre_fec"),
        "loss_post_fec_per_min": k(m, "packet_loss_per_min", "value", "post_fec"),
        "fec_recovered_packets": k(m, "fec_groups", "value", "recovered_packets"),
        "fec_unrecoverable_groups": k(m, "fec_groups", "value", "unrecoverable_groups"),
        "wan_reports": last.get("reports"), "wan_poll_at": polls[-1]["at_utc"] if polls else None,
        "rendered_fps": row.get("rendered_fps"), "stale_per_min": row.get("stale_per_min"), "spikes20_per_min": row.get("spikes20_per_min"),
        "resyncs_window": row.get("resyncs"), "resyncs_session": rf.get("video.sequence_resyncs"),
        "client_pauses": row.get("client_pauses"),
        "rung_min": min(rungs) if rungs else None, "rung_max": max(rungs) if rungs else None,
        "rung_polls": {str(r): n for r, n in sorted(rungs.items())}, "ladder_acted": len(acted),
        "rules_suggestions": sum(rules.values()), "rules_by_id": dict(rules),
        "wan_class": last.get("class"), "wan_windows": last.get("window_primary_counts"),
        "wan_polls": len(polls), "wan_redacted": sum(p.get("redacted_matches") or 0 for p in jl(cdir / f"wan_poll_run{row['attempt']}.jsonl")),
        "shim_in": sh.get("packets_in"), "shim_out": sh.get("packets_out"), "shim_dropped_loss": sh.get("dropped_loss"),
        "shim_dropped_burst": sh.get("dropped_burst"), "shim_dropped_queue": sh.get("dropped_queue"),
        "shim_delayed": sh.get("delayed"), "shim_reordered": sh.get("reordered"), "shim_queue_max": sh.get("queue_max"),
        "shim_loss_frac": sh.get("loss_frac"), "profile_applied": row.get("profile_applied"),
        "flags_under_load": row.get("flags_under_load"),
        "recovery_rows": len(jl(rd / "recovery.jsonl")) if rd else None, "gaps_rows": len(jl(rd / "gaps.jsonl")) if rd else None,
        "recovery_key": k(s, "key", "recovery"),
        "intent": INTENT.get(row["profile"]),
    }
    return out


def main():
    rows = jl(HERE / "cells.jsonl")
    res = [read(r) for r in rows if r.get("validity") != "busy"]
    (HERE / "g8_s1_cells_read.json").write_text(json.dumps(res, indent=1) + "\n")
    (HERE / "validity.json").write_text(json.dumps({r["cell"]: r["validity"] for r in rows}, indent=1) + "\n")
    g = lambda b: "met" if b else "NOT MET"
    md = ["# G8-S1 — the completed cells (partial)", "",
          "| cell | validity | PLAYING (attempt, s) | RetroArch | capture | dup+drop /min | gates | host CPU % | companion % core | shim % core |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        p = r["playing"] or {}
        gates = "all met" if all((r["gate_retroarch"], r["gate_capture"], r["gate_dupdrop"], r["gate_flags_absent"])) else \
            ", ".join(f"{n} {g(v)}" for n, v in (("RA", r["gate_retroarch"]), ("capture", r["gate_capture"]),
                                                   ("dup+drop", r["gate_dupdrop"]), ("flags", r["gate_flags_absent"])))
        md.append(f"| {r['cell']} | {r['validity']} | {p.get('attempt')}, {p.get('s_to_playing')} | {r['retroarch_fps']} | "
                  f"{r['capture_fps']} | {r['dupdrop_per_min']} | {gates} | {r['host_cpu']} | {r['companion_cpu']} | {r['shim_cpu_pct_core']} |")
    md += ["", "| cell | loss/min heartbeat | pre-FEC /min | post-FEC /min | FEC recovered pkts | unrecoverable groups | rendered | stale /min | spikes≥20 ms /min | resyncs window | resyncs session | client pauses |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['cell']} | {r['loss_per_min_heartbeat']} | {r['loss_pre_fec_per_min']} | {r['loss_post_fec_per_min']} | "
                  f"{r['fec_recovered_packets']} | {r['fec_unrecoverable_groups']} | {r['rendered_fps']} | {r['stale_per_min']} | "
                  f"{r['spikes20_per_min']} | {r['resyncs_window']} | {r['resyncs_session']} | {r['client_pauses']} |")
    md += ["", "| cell | rung min-max (polls) | ladder acted | rules suggestions (by rule) | wan class | wan windows (primary) | shim in / out | dropped loss / burst / queue | delayed | reordered | queue max | applied |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['cell']} | {r['rung_min']}-{r['rung_max']} {r['rung_polls']} | {r['ladder_acted']} | {r['rules_suggestions']} {r['rules_by_id'] or ''} | "
                  f"{r['wan_class']} | {r['wan_windows']} | {r['shim_in']} / {r['shim_out']} | {r['shim_dropped_loss']} / {r['shim_dropped_burst']} / "
                  f"{r['shim_dropped_queue']} | {r['shim_delayed']} | {r['shim_reordered']} | {r['shim_queue_max']} | {r['profile_applied']} |")
    try:
        cl = {x["label"]: x for x in json.loads(CLB3.read_text())["runs"]}
    except (OSError, ValueError, KeyError):
        cl = {}
    if cl:
        md += ["", "Comparison (i): CL-B3 (no shim) beside the `none` cells.", "",
               "| run | host CPU % | companion % core | RetroArch / encoder % core | rendered | loss/min | resyncs | rung |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
        for lab in ("R1", "W"):
            x = cl.get(lab)
            if x:
                p = x["procs_cpu_pct_of_core"]
                md.append(f"| CL-B3 {lab} | {x['host_cpu']} | {p.get('companion')} | {p.get('retroarch')} / {p.get('encoder')} | "
                          f"{x['rendered_fps']} | {x['loss_per_min']} | {x['resyncs']} | {x['rung_kbps_range']} |")
        for r in res:
            if r["profile"] == "none":
                md.append(f"| G8-S1 {r['cell']} | {r['host_cpu']} | {r['companion_cpu']} | (cells.jsonl keeps the companion only) | "
                          f"{r['rendered_fps']} | {r['loss_per_min_heartbeat']} | {r['resyncs_window']} | {r['rung_min']}-{r['rung_max']} |")
    md += ["", "Comparison (iii): class vs intent.", "", "| cell | intent | class | windows |", "| --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['cell']} | {r['intent']} | {r['wan_class']} | {r['wan_windows']} |")
    (HERE / "g8_s1_table.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
