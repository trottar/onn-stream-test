#!/usr/bin/env python3
"""G8-S1: the cells read from the driver's files only -- cells.jsonl, runs/<cell>/ (the suite's summary.json and
summary_failed_attempt<n>.json, status_poll.jsonl, decisions.jsonl, recovery.jsonl, gaps.jsonl, suite.log),
wan_poll_run<n>.jsonl and impairment_run<n>.jsonl -- against g8_s1_preregistration.txt as hashed. Read-only.

The partial pass (2026-10-16, 5 cells) wrote g8_s1_table.md and g8_s1_cells_read.json; those stay as that record's
reading. The final pass (2026-10-17, all 22 cells; extended here) writes g8_s1_table_final.md,
g8_s1_cells_read_final.json and validity.json (replaced).

Field sources (named in the record):
- resyncs_window: summary key.heartbeat.stream_resyncs (the driver's `resyncs`; the heartbeat over the 600-s window);
  resyncs_session: summary teardown.report_fields["video.sequence_resyncs"] (the client's end-of-session report: the
  whole session, warm-up included).
- loss pre/post-FEC per min and FEC groups: the last wan poll's measures.packet_loss_per_min.{pre_fec,post_fec} and
  measures.fec_groups.{recovered_packets,unrecoverable_groups} (G5-S1's per-session object, the session so far);
  loss_per_min (heartbeat) beside them.
- rules suggestions: decisions.jsonl rows with event "wan_suggestion" and source "wan_rules", by rule id and
  suggestion, with their ladder_result; the driver's own count (cells.jsonl rules_suggestions) counts every line that
  contains "wan_rules", so it also counts refused / transition rows naming wan_rules -- both are given.
- the ladder's rung path: decisions.jsonl rows with event "transition" and acted true (from_kbps -> to_kbps, reason,
  class), with whether the transition fell inside the 600-s window.
- the shim: impairment_run<n>.jsonl lines are per-second deltas; t_s restarts at each stream start, so a run with
  several stream starts (the cap cells) has several segments. The shim's cost is sum(cpu_s) / sum(segment durations).
  (The driver's shim_cpu_pct_core divides by the longest t_s, which is right for one segment only.)
- the code version of a run: its summary started_utc against the edit times of session B's companion files
  (G8_S1_RESUME_2026-10-17.md section 5; file mtimes re-read at the final record)."""
import json
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLB3 = HERE.parent / "cl_b3_2026-10-16/cl_b3_verdict.json"
INTENT = {"none": "clean", "loss-1": "lossy", "loss-5": "lossy", "burst-50x20": "lossy", "delay-50": "-",
          "delay-150": "latency-limited", "jitter-30": "-", "reorder-5": "-", "cap-6000": "capacity-limited",
          "cap-4500": "capacity-limited", "delay-50+loss-1": "lossy"}
CAP_KBPS = {"cap-6000": 6000, "cap-4500": 4500}
# session B's last companion edit of each task (UTC): G5-S3 (wan_adaptation, adaptive_bitrate_live, plugins/games,
# diagnostics/c3_linux_actuator_probe, remote_ladder new) and G5-S4 (adaptive_bitrate_live, remote_ladder; remote_cap new)
EDIT_G5S3_FIRST, EDIT_G5S3_LAST = "2026-10-17T00:22:39Z", "2026-10-17T00:23:10Z"
EDIT_G5S4_FIRST, EDIT_G5S4_LAST = "2026-10-17T00:38:38Z", "2026-10-17T00:39:00Z"


def jl(p):
    try:
        return [json.loads(l) for l in open(p) if l.strip()]
    except OSError:
        return []


def jf(p):
    try:
        return json.loads(Path(p).read_text())
    except (OSError, ValueError):
        return {}


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def version(started):
    if not started:
        return None
    t = started[:19] + "Z"
    if t < EDIT_G5S3_FIRST:
        return "pre-registered"
    if t < EDIT_G5S4_FIRST:
        return "G5-S3 edits" if t > EDIT_G5S3_LAST else "during G5-S3 edits"
    return "G5-S3 + G5-S4 edits" if t > EDIT_G5S4_LAST else "during G5-S4 edits"


def segments(lines):
    segs, cur = [], []
    for r in lines:
        if cur and (r.get("t_s") or 0) < (cur[-1].get("t_s") or 0):
            segs.append(cur)
            cur = []
        cur.append(r)
    if cur:
        segs.append(cur)
    out = []
    for sg in segs:
        s = lambda key, rows=sg: sum(r.get(key) or 0 for r in rows)
        dur = max(r.get("t_s") or 0 for r in sg)
        steady = [r for r in sg if (r.get("t_s") or 0) > 2.5]
        sd = len(steady)
        out.append({"lines": len(sg), "duration_s": round(dur, 1), "packets_in": s("packets_in"), "packets_out": s("packets_out"),
                    "bytes_in": s("bytes_in"), "bytes_out": s("bytes_out"), "dropped_queue": s("dropped_queue"),
                    "dropped_loss": s("dropped_loss"), "dropped_burst": s("dropped_burst"), "delayed": s("delayed"),
                    "reordered": s("reordered"), "queue_max": max(r.get("queue_max") or 0 for r in sg), "cpu_s": round(s("cpu_s"), 3),
                    "steady_in_kbps": round(sum(r["bytes_in"] for r in steady) * 8 / sd / 1000, 1) if sd else None,
                    "steady_out_kbps": round(sum(r["bytes_out"] for r in steady) * 8 / sd / 1000, 1) if sd else None,
                    "steady_out_kbps_max": round(max(r["bytes_out"] for r in steady) * 8 / 1000, 1) if sd else None,
                    "steady_drop_frac": round(sum(r["dropped_queue"] + (r.get("dropped_loss") or 0) for r in steady) /
                                              max(1, sum(r["packets_in"] for r in steady)), 4) if sd else None})
    return out


def read(row):
    cdir = HERE / "runs" / row["cell"]
    rd = HERE / row["run_dir"] if row.get("run_dir") else None
    s = jf(rd / "summary.json") if rd else {}
    rf = k(s, "teardown", "report_fields") or {}
    polls_all = jl(cdir / f"wan_poll_run{row['attempt']}.jsonl")
    polls = [p for p in polls_all if isinstance(p.get("wan"), dict)]
    last = polls[-1]["wan"] if polls else {}
    m = last.get("measures") or {}
    rungs = Counter(int(r["bitrate_kbps"]) for r in jl(rd / "status_poll.jsonl") if isinstance(r.get("bitrate_kbps"), (int, float))) if rd else Counter()
    dec = jl(rd / "decisions.jsonl") if rd else []
    sugg = [r for r in dec if r.get("event") == "wan_suggestion" and r.get("source") == "wan_rules"]
    rules = Counter(r.get("rule") for r in sugg)
    rules_detail = Counter(f"{r.get('rule')} {r.get('suggestion')} -> {r.get('ladder_result')}" for r in sugg)
    acted = [r for r in dec if r.get("acted")]
    win = s.get("window") or {}
    path = [{"at_utc": r.get("at_utc"), "from_kbps": r.get("from_kbps"), "to_kbps": r.get("to_kbps"), "reason": r.get("reason"),
             "class": r.get("class"), "session_elapsed_s": round((r.get("session_elapsed_ms") or 0) / 1000, 1),
             "in_window": bool(win) and win.get("from", "") <= (r.get("at_utc") or "") <= win.get("to", "")}
            for r in dec if r.get("event") == "transition" and r.get("acted")]
    gaps = jl(rd / "gaps.jsonl") if rd else []
    sh = row.get("shim") or {}
    segs = segments(jl(cdir / f"impairment_run{row['attempt']}.jsonl"))
    seg_dur = sum(x["duration_s"] for x in segs)
    failed = sorted(rd.glob("summary_failed_attempt*.json")) if rd else []
    attempts = []
    for f in failed + ([rd / "summary.json"] if rd and (rd / "summary.json").exists() else []):
        a = jf(f)
        arf = k(a, "teardown", "report_fields") or {}
        attempts.append({"file": f.name, "started_utc": a.get("started_utc"), "ended_utc": a.get("ended_utc"),
                         "status": a.get("status"), "launch": k(a, "launch", "stream"), "error": a.get("error"),
                         "code_version": version(a.get("started_utc")),
                         "client_report": {x: arf.get(x) for x in ("duration_ms", "rendered_frames", "lost_packets", "max_output_gap_ms",
                                                                    "video.sequence_resyncs", "video.recent_fps", "stale_output_drops",
                                                                    "audio.underruns")} if arf else None,
                         "flags_absent": k(a, "teardown", "flags_absent"),
                         "environ_at_restart": k(a, "restart", "environ")})
    remote_flags = sorted({e for a in attempts for e in (a["environ_at_restart"] or []) if e.startswith("PRIVYHUB_REMOTE")})
    valid_run = attempts[-1] if attempts else {}
    out = {
        "n": row["n"], "cell": row["cell"], "profile": row["profile"], "arm": row["arm"], "validity": row["validity"],
        "attempt": row["attempt"], "start_utc": row.get("start_utc"), "playing": k(s, "launch", "stream"),
        "suite_attempts": len(attempts), "suite_attempts_failed": len(failed), "attempts": attempts,
        "code_version_of_counted_run": valid_run.get("code_version"), "remote_flags_in_environ": remote_flags,
        "window": win or None,
        "retroarch_fps": row.get("retroarch_fps"), "capture_fps": row.get("capture_fps"), "dupdrop_per_min": row.get("dupdrop_per_min"),
        "gate_retroarch": (row.get("retroarch_fps") or 0) >= 59.9,
        "gate_capture": row.get("capture_fps") is not None and abs(row["capture_fps"] - 60) <= 0.1,
        "gate_dupdrop": row.get("dupdrop_per_min") is not None and row["dupdrop_per_min"] <= 0.2,
        "gate_flags_absent": bool(row.get("flags_absent_after")) and bool(row.get("final_flags_absent")),
        "host_cpu": row.get("host_cpu"), "companion_cpu": row.get("companion_cpu"),
        "shim_cpu_pct_core_driver": row.get("shim_cpu_pct_core"),
        "shim_cpu_pct_core": round(100 * sum(x["cpu_s"] for x in segs) / seg_dur, 3) if seg_dur else None,
        "shim_segments": len(segs), "shim_seconds": round(seg_dur, 1), "shim_segment_detail": segs,
        "loss_per_min_heartbeat": row.get("loss_per_min"),
        "loss_pre_fec_per_min": k(m, "packet_loss_per_min", "value", "pre_fec"),
        "loss_post_fec_per_min": k(m, "packet_loss_per_min", "value", "post_fec"),
        "fec_recovered_packets": k(m, "fec_groups", "value", "recovered_packets"),
        "fec_unrecoverable_groups": k(m, "fec_groups", "value", "unrecoverable_groups"),
        "goodput_kbps": k(m, "delivered_goodput_kbps", "value"), "rtt_ms": k(m, "rtt_ms", "value"), "jitter_ms": k(m, "jitter_ms", "value"),
        "rtt_source": k(m, "rtt_ms", "source"),
        "wan_reports": last.get("reports"), "wan_poll_at": polls[-1]["at_utc"] if polls else None,
        "rendered_fps": row.get("rendered_fps"), "stale_per_min": row.get("stale_per_min"), "spikes20_per_min": row.get("spikes20_per_min"),
        "resyncs_window": row.get("resyncs"), "resyncs_session": rf.get("video.sequence_resyncs"),
        "client_pauses": row.get("client_pauses"),
        "rung_min": min(rungs) if rungs else None, "rung_max": max(rungs) if rungs else None,
        "rung_polls": {str(r): n for r, n in sorted(rungs.items())}, "ladder_acted": len(acted), "rung_path": path,
        "rules_suggestions": sum(rules.values()), "rules_by_id": dict(rules), "rules_detail": dict(rules_detail),
        "rules_lines_driver": row.get("rules_suggestions"),
        "wan_class": last.get("class"), "wan_windows": last.get("window_primary_counts"), "wan_window_counts": last.get("window_counts"),
        "wan_polls": len(polls), "wan_redacted": sum(p.get("redacted_matches") or 0 for p in polls_all),
        "shim_in": sh.get("packets_in"), "shim_out": sh.get("packets_out"), "shim_dropped_loss": sh.get("dropped_loss"),
        "shim_dropped_burst": sh.get("dropped_burst"), "shim_dropped_queue": sh.get("dropped_queue"),
        "shim_delayed": sh.get("delayed"), "shim_reordered": sh.get("reordered"), "shim_queue_max": sh.get("queue_max"),
        "shim_loss_frac": sh.get("loss_frac"), "profile_applied": row.get("profile_applied"),
        "shim_seconds_input_over_cap": sh.get("seconds_input_over_cap"), "shim_out_kbps_max": sh.get("out_kbps_max"),
        "flags_under_load": row.get("flags_under_load"), "flags_absent_after": row.get("flags_absent_after"),
        "recovery_rows": len(jl(rd / "recovery.jsonl")) if rd else None, "gaps_rows": len(gaps),
        "gaps_ms": [round(g.get("gap_ms") or 0) for g in gaps],
        "recovery_key": k(s, "key", "recovery"),
        "intent": INTENT.get(row["profile"]),
    }
    return out


def fmt_path(p):
    return "; ".join(f"{x['from_kbps']}→{x['to_kbps']} {x['reason']} ({x['class']}, {x['at_utc'][11:19]}Z, "
                     f"{'in window' if x['in_window'] else 'before the window'})" for x in p) or "none"


def main():
    rows = jl(HERE / "cells.jsonl")
    res = [read(r) for r in rows if r.get("validity") != "busy"]
    (HERE / "g8_s1_cells_read_final.json").write_text(json.dumps(res, indent=1) + "\n")
    (HERE / "validity.json").write_text(json.dumps({r["cell"]: r["validity"] for r in rows}, indent=1) + "\n")
    played = [r for r in res if r["validity"] == "valid"]
    g = lambda b: "met" if b else "NOT MET"
    md = [f"# G8-S1 — all cells ({len(res)}; valid {len(played)})", "",
          "## Table 1: host side", "",
          "| cell | validity | suite attempts (failed) | PLAYING (attempt, s) | code version (counted run) | RetroArch | capture | dup+drop /min | gates | host CPU % | companion % core |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        p = r["playing"] or {}
        if r["validity"] != "valid":
            gates = "not read (no window)"
        else:
            gates = "all met" if all((r["gate_retroarch"], r["gate_capture"], r["gate_dupdrop"], r["gate_flags_absent"])) else \
                ", ".join(f"{n} {g(v)}" for n, v in (("RA", r["gate_retroarch"]), ("capture", r["gate_capture"]),
                                                       ("dup+drop", r["gate_dupdrop"]), ("flags", r["gate_flags_absent"])))
        md.append(f"| {r['cell']} | {r['validity']} | {r['suite_attempts']} ({r['suite_attempts_failed']}) | {p.get('attempt')}, {p.get('s_to_playing')} | "
                  f"{r['code_version_of_counted_run']} | {r['retroarch_fps']} | {r['capture_fps']} | {r['dupdrop_per_min']} | {gates} | "
                  f"{r['host_cpu']} | {r['companion_cpu']} |")
    md += ["", "## Table 2: the link", "",
           "| cell | loss/min heartbeat | pre-FEC /min | post-FEC /min | FEC recovered pkts | unrecoverable groups | rendered | stale /min | spikes≥20 ms /min | resyncs window | resyncs session | client pauses |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['cell']} | {r['loss_per_min_heartbeat']} | {r['loss_pre_fec_per_min']} | {r['loss_post_fec_per_min']} | "
                  f"{r['fec_recovered_packets']} | {r['fec_unrecoverable_groups']} | {r['rendered_fps']} | {r['stale_per_min']} | "
                  f"{r['spikes20_per_min']} | {r['resyncs_window']} | {r['resyncs_session']} | {r['client_pauses']} |")
    md += ["", "## Table 3: the ladder, the rules, the classifier, the shim", "",
           "| cell | rung min-max (polls) | rung path (decisions.jsonl) | rules suggestions by rule (driver's line count) | wan class | wan windows (primary) | shim in / out | dropped loss / burst / queue | delayed | reordered | queue max | applied |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['cell']} | {r['rung_min']}-{r['rung_max']} {r['rung_polls']} | {fmt_path(r['rung_path'])} | "
                  f"{r['rules_suggestions']} {r['rules_by_id'] or ''} ({r['rules_lines_driver']}) | "
                  f"{r['wan_class']} | {r['wan_windows']} | {r['shim_in']} / {r['shim_out']} | {r['shim_dropped_loss']} / {r['shim_dropped_burst']} / "
                  f"{r['shim_dropped_queue']} | {r['shim_delayed']} | {r['shim_reordered']} | {r['shim_queue_max']} | {r['profile_applied']} |")
    md += ["", "## Table 4: session loss and recovery events", "",
           "| cell | recovery.jsonl rows | key.recovery pauses (controller / client / other) | gaps.jsonl rows | gap ms (max) |", "| --- | --- | --- | --- | --- |"]
    for r in res:
        kr = r["recovery_key"] or {}
        pz = " / ".join(str(len(kr.get(x) or [])) for x in ("controller_pauses", "client_pauses", "other_pauses")) if kr else "-"
        md.append(f"| {r['cell']} | {r['recovery_rows']} | {pz} | {r['gaps_rows']} | {max(r['gaps_ms']) if r['gaps_ms'] else '-'} |")
    md += ["", "## Table 5: the shim's cost (sum cpu_s / sum segment seconds)", "",
           "| cell | segments | shim seconds | shim % of a core | driver's figure |", "| --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['cell']} | {r['shim_segments']} | {r['shim_seconds']} | {r['shim_cpu_pct_core']} | {r['shim_cpu_pct_core_driver']} |")
    try:
        cl = {x["label"]: x for x in json.loads(CLB3.read_text())["runs"]}
    except (OSError, ValueError, KeyError):
        cl = {}
    if cl:
        md += ["", "## Comparison (i): CL-B3 (no shim) beside the `none` cells", "",
               "| run | host CPU % | companion % core | rendered | loss/min | resyncs | rung |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for lab in ("R1", "W"):
            x = cl.get(lab)
            if x:
                md.append(f"| CL-B3 {lab} | {x['host_cpu']} | {x['procs_cpu_pct_of_core'].get('companion')} | "
                          f"{x['rendered_fps']} | {x['loss_per_min']} | {x['resyncs']} | {x['rung_kbps_range']} |")
        for r in res:
            if r["profile"] == "none":
                md.append(f"| G8-S1 {r['cell']} | {r['host_cpu']} | {r['companion_cpu']} | "
                          f"{r['rendered_fps']} | {r['loss_per_min_heartbeat']} | {r['resyncs_window']} | {r['rung_min']}-{r['rung_max']} |")
    md += ["", "## Comparison (ii): off vs on per profile", "",
           "| profile | arm | rules suggestions: rule suggestion -> ladder result | rung path | rendered | stale /min | loss/min heartbeat | post-FEC /min (wan) |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        md.append(f"| {r['profile']} | {r['arm']} | {r['rules_detail'] or ('0' if r['validity'] == 'valid' else 'no window')} | {fmt_path(r['rung_path'])} | "
                  f"{r['rendered_fps']} | {r['stale_per_min']} | {r['loss_per_min_heartbeat']} | {r['loss_post_fec_per_min']} |")
    md += ["", "## Comparison (iii): class vs intent", "",
           "| cell | intent | class | windows (primary) | window counts (any class) | reports | goodput kbps | rtt ms p50/p95 | jitter ms p50/p95 |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        rt, ji = r["rtt_ms"] or {}, r["jitter_ms"] or {}
        md.append(f"| {r['cell']} | {r['intent']} | {r['wan_class']} | {r['wan_windows']} | {r['wan_window_counts']} | {r['wan_reports']} | "
                  f"{r['goodput_kbps']} | {rt.get('p50')}/{rt.get('p95')} | {ji.get('p50')}/{ji.get('p95')} |")
    md += ["", "## The cap cells: the suite's attempts and the client's reports", "",
           "| cell | attempt file | started | code version | launch | client: duration ms / rendered frames / lost packets / max output gap ms / resyncs / audio underruns | flags absent after |",
           "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        if r["profile"] in CAP_KBPS:
            for a in r["attempts"]:
                c = a["client_report"] or {}
                md.append(f"| {r['cell']} | {a['file']} | {(a['started_utc'] or '')[11:19]}Z | {a['code_version']} | {a['launch']} | "
                          f"{c.get('duration_ms')} / {c.get('rendered_frames')} / {c.get('lost_packets')} / {c.get('max_output_gap_ms')} / "
                          f"{c.get('video.sequence_resyncs')} / {c.get('audio.underruns')} | {a['flags_absent']} |")
    md += ["", "## The cap cells: the shim per stream start (segment)", "",
           "| cell | cap kbps | segment | seconds | in / out packets | dropped_queue | queue max | steady in kbps | steady out kbps (max) | steady drop fraction |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in res:
        if r["profile"] in CAP_KBPS:
            for i, x in enumerate(r["shim_segment_detail"], 1):
                md.append(f"| {r['cell']} | {CAP_KBPS[r['profile']]} | {i} | {x['duration_s']} | {x['packets_in']} / {x['packets_out']} | "
                          f"{x['dropped_queue']} | {x['queue_max']} | {x['steady_in_kbps']} | {x['steady_out_kbps']} ({x['steady_out_kbps_max']}) | "
                          f"{x['steady_drop_frac']} |")
    md += ["", "## Reference: a valid cell's shim input (the stream at 7000 with FEC and audio)", "",
           "| cell | segments | steady in kbps | steady out kbps |", "| --- | --- | --- | --- |"]
    for r in res:
        if r["profile"] in ("none", "reorder-5", "delay-50") and r["shim_segment_detail"]:
            x = r["shim_segment_detail"][-1]
            md.append(f"| {r['cell']} | {r['shim_segments']} | {x['steady_in_kbps']} | {x['steady_out_kbps']} |")
    md += ["", f"PRIVYHUB_REMOTE* flags in any restart environ: {sorted({f for r in res for f in r['remote_flags_in_environ']}) or 'none'}"]
    (HERE / "g8_s1_table_final.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
