#!/usr/bin/env python3
"""Summarize the A1-live / A3-live captures of 2026-09-20.
Inputs (produced by the commands in GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md):
  logs/games/a1_sample.h264          10 s production-command VAAPI encode
  <trace>                            ffmpeg -bsf:v trace_headers stderr of that file
  logs/games/a3_grab_framemd5.txt    30 s x11grab -> framemd5 of the same window
Usage: a1_a3_live_summarize.py <a1_trace_headers_log> > a1_a3_live_summary.json
"""
import sys, json, re, subprocess, collections
trace = sys.argv[1]
out = {}
# --- A1: frame types via ffprobe, SPS/SEI fields via trace_headers ---
pt = subprocess.run(["ffprobe","-v","error","-select_streams","v","-show_entries","frame=pict_type","-of","csv=p=0","logs/games/a1_sample.h264"],capture_output=True,text=True).stdout
types = collections.Counter(l.strip().strip(",") for l in pt.splitlines() if l.strip())
seq = "".join(l.strip().strip(",") for l in pt.splitlines() if l.strip())
fields = collections.Counter()
for line in open(trace, errors="replace"):
    m = re.match(r"^\[[^\]]*\]\s+\d+\s+(\S+)\s+[01]+\s+=\s+(-?\d+)\s*$", line)
    if m:
        fields[(m.group(1), int(m.group(2)))] += 1
want = ["nal_unit_type","bitstream_restriction_flag","max_num_reorder_frames","max_dec_frame_buffering",
        "max_num_ref_frames","pic_order_cnt_type","vui_parameters_present_flag","timing_info_present_flag",
        "num_units_in_tick","time_scale","fixed_frame_rate_flag","nal_hrd_parameters_present_flag",
        "low_delay_hrd_flag","pic_struct_present_flag","dpb_output_delay","initial_cpb_removal_delay[0]",
        "last_payload_type_byte","profile_idc","level_idc","entropy_coding_mode_flag","frame_mbs_only_flag"]
out["a1"] = {
    "pict_type_counts": dict(types),
    "pict_type_sequence_first_45": seq[:45],
    "b_frames": types.get("B", 0),
    "trace_fields": {k: {str(v): n for (kk, v), n in sorted(fields.items()) if kk == k} for k in want},
}
# --- A3: framemd5 duplicates and PTS cadence ---
rows=[l.split(',') for l in open('logs/games/a3_grab_framemd5.txt') if l[0]!='#']
pts=[int(r[1]) for r in rows]; md=[r[-1].strip() for r in rows]
d=[b-a for a,b in zip(pts,pts[1:])]
dup_pos=[i+1 for i,(a,b) in enumerate(zip(md,md[1:])) if a==b]
sec=collections.defaultdict(list)
for p,h in zip(pts,md): sec[(p-pts[0])//60].append(h)
per=[[s,len(v),len(set(v))] for s,v in sorted(sec.items())]
runs=[];cur=0
for a,b in zip(md,md[1:]):
    if a==b: cur+=1
    elif cur: runs.append(cur); cur=0
if cur: runs.append(cur)
first27 = [p for p in dup_pos if p < 27*60]
out["a3"] = {
    "frames": len(rows), "tb": "1/60", "dups_total": len(dup_pos),
    "pts_delta_hist": dict(collections.Counter(d)),
    "dup_positions": dup_pos, "dup_run_length_hist": dict(collections.Counter(runs)),
    "per_second_grabbed_unique": per,
    "first_27s": {"frames": 27*60, "dups": len(first27), "dup_positions": first27,
                  "unique_share": round(1 - len(first27)/(27*60), 5)},
}
json.dump(out, sys.stdout, indent=1)
