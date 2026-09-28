#!/usr/bin/env python3
"""C4-D1: adaptive FEC decided on the evidence already on disk. Read-only.

Population (pre-registered, handoffs/C4-D1_ADAPTIVE_FEC_EVIDENCE_TASK.md):
every decoder session on the adopted build -- from D-BASE-P6a's validation
session V1 (native_decoder_20260922_062613_928, cap 90,000 by profile) on;
the reports carry no cap field, so the build is taken by date, and every
session after V1 ran with the profile's cap (no PRIVYHUB_ENC_MAX_FRAME_SIZE /
BUFSIZE override is recorded after P6a) -- of >= 5 minutes. Split into
HOLDS (ssrc_changes == 0) and TRANSITION sessions. Excluded, with the reason
printed: the two deliberate link-drop runs (R3b N150, E30: induced outages).
Session 2 of the C3.L3a rerun (rejected by the old cap) is read from its
journal-rebuilt copy in evidence.

What 8+1 is (companion/native_fec_relay.py, RtpH264Receiver.kt): one XOR
parity per group of <= 8 data packets of ONE frame (a frame's last group is
partial). The client builds a group on its parity and recovers exactly one
missing data packet; a group with >= 2 missing is pruned at 40 ms and
counted `fec_unrecoverable_groups`; a group whose parity is lost is never
seen. `lost_packets` and `forward_gap_events` are counted AFTER recovery
(a recovered packet fills its hole), so each post-FEC forward gap is a run
of consecutive data packets FEC did not restore; `lost_packets_in_resyncs`
is restart loss, not FEC's business, and is excluded.

1. Alternatives, UPPER BOUNDS ignoring interleaving (per post-FEC gap of b
   consecutive packets): k+2 (two parities per 8-group; any two missing):
   at most min(b, 4) of the gap (only a gap's two edge groups can hold <= 2
   of it); 4+1 (two 4-groups per 8): at most min(b, 2). A window with G gap
   events and L lost is bounded by min(L, 4G) and min(L, 2G) whatever the
   split. Summed over 2 s heartbeat windows. Gap sizes are exact in windows
   holding one gap event. Also a POINT estimate from those exact sizes:
   k+2 recovers gaps of b <= 2, 4+1 gaps of b = 1 (and a b = 2 gap on the
   one of its seven offsets that straddles the 4|4 boundary) -- stated beside
   the bounds, not used by the rule.
2. Capacity pressure, per client minute: loss (post-FEC, non-resync) against
   the columns that exist per minute on this build (see SUBSTITUTIONS);
   Spearman, and the bucket table loss 0 / 1-5 / 6-20 / > 20. Pre-registered
   reading: ABSENT if the loss buckets show no monotone rise in queue depth
   or output gap and |rho| < 0.3 on every column; PRESENT if either rises
   across all buckets.
3. Warm split: minutes with onn cpu-thermal >= 67.5 C (t2_sample.py rows)
   against < 67.5, 1 and 2 repeated; multi-packet gaps in warm minutes.
4. Latency: group completion delay = group size x mean packet interval
   (host frame-size series), beside the 8+1 figure; and within a frame burst.

Decision rule (pre-registered): DEFER WITH EVIDENCE if the extra recoverable
loss under k+2 or 4+1 is < 2 packets/min at the corpus median AND pressure is
absent; BUILD (static k+2 first) if a fixed alternative recovers >= 5/min
more at the median with no pressure signal; BUILD ADAPTIVE only if pressure
is present and loss rises with it. The rule's input is the computation the
task specifies -- the UPPER BOUND; every branch is printed as written.

SUBSTITUTIONS (stated, not hidden): `queue_depth`, `output_gap_ms`,
`recent_fps`, `interarrival_jitter_ms`, `send_call_avg_us`/`max_us` are
fields of the latest-only /diagnostics/stream-telemetry snapshot; no per-
minute series of them was logged on the adopted build. Per minute exist:
rendered fps (heartbeat `rendered_frames`) for recent_fps; the client's
frames queued-but-not-rendered per minute (`queued_frames - rendered_frames`
delta) for queue depth; the largest `last_output_age_ms` seen at the 2 s
heartbeats for output gap; the host's offered load per second (packets,
bytes, largest frame, frames >= 40 packets) for the sender side; and where a
t2 sampler ran, the Opal's tx retries / failed per minute for the air.
Jitter and send-call timing: NOT AVAILABLE per minute.

Usage: c4_d1_analyze.py <repo root> > c4_d1_analysis.txt
"""
from __future__ import annotations

import glob
import json
import math
import os
import statistics
import sys
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
EV = os.path.join(ROOT, "docs/memory/evidence")
FIRST = "native_decoder_20260922_062613_928.json"          # P6a V1
EXCLUDE = {
    "native_decoder_20260922_152630_102.json": "R3b N150: deliberate link drop",
    "native_decoder_20260923_031009_782.json": "R3b E30: deliberate link drop",
}
EXTRA = [os.path.join(EV, "c3_l3a_r2_2026-09-24/native_decoder_20260924_171642_rebuilt.json")]
WARM_C = 67.5
MIN_S = 300


def ts(s: str) -> float:
    return datetime.strptime(s[:23], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()


def spearman(x, y):
    n = len(x)
    if n < 3:
        return float("nan")

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    rx, ry = ranks(x), ranks(y)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def med(v):
    return statistics.median(v) if v else float("nan")


# ---------------------------------------------------------------- sources
def load_jsonl(paths, key):
    out = {}
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                k = key(r)
                if k is not None:
                    out[k] = r
    return out


hb_paths = sorted(set(
    glob.glob(os.path.join(ROOT, "logs/games/native_stream_heartbeat.log"))
    + glob.glob(os.path.join(ROOT, "logs/games/stream_log_archive/native_stream_heartbeat.log.*"))
    + glob.glob(os.path.join(EV, "**/heartbeat_*.jsonl"), recursive=True)
    + glob.glob(os.path.join(EV, "**/heartbeat_lines.jsonl"), recursive=True)))
HB = load_jsonl(hb_paths, lambda r: (r.get("received_at_utc"), r.get("sequence"))
                if "lost_packets" in r and r.get("received_at_utc") else None)
hb_rows = sorted(HB.values(), key=lambda r: r["received_at_utc"])
hb_t = [ts(r["received_at_utc"]) for r in hb_rows]

fr_paths = sorted(set(
    glob.glob(os.path.join(ROOT, "logs/games/native_frame_sizes.jsonl"))
    + glob.glob(os.path.join(ROOT, "logs/games/stream_log_archive/native_frame_sizes.jsonl.*"))
    + glob.glob(os.path.join(EV, "**/frames_*.jsonl"), recursive=True)))
FR = load_jsonl(fr_paths, lambda r: r.get("t") if r.get("schema") == "privyhub_native_frame_sizes_v1" else None)
fr_keys = sorted(FR)

t2_paths = sorted(glob.glob(os.path.join(EV, "**/t2_samples.jsonl"), recursive=True))
T2 = load_jsonl(t2_paths, lambda r: r.get("at_utc"))
t2_rows = sorted(T2.values(), key=lambda r: r["at_utc"])
t2_t = [ts(r["at_utc"]) for r in t2_rows]

print("C4-D1 analysis -- read-only; sources")
print(f"  heartbeat rows (deduplicated): {len(hb_rows)} from {len(hb_paths)} files")
print(f"  host frame-size seconds:       {len(fr_keys)} from {len(fr_paths)} files")
print(f"  t2 samples (host+onn+Opal):    {len(t2_rows)} from {len(t2_paths)} files")
print()

# ---------------------------------------------------------------- population
reports = sorted(glob.glob(os.path.join(ROOT, "logs/games/decoder_sessions/native_decoder_2026092[234]_*.json")))
sessions, skipped = [], []
for p in reports + EXTRA:
    name = os.path.basename(p)
    if p not in EXTRA and name < FIRST:
        continue
    r = json.load(open(p, encoding="utf-8"))
    rep = r["report"]
    dur = rep["duration_ms"] / 1000.0
    if name in EXCLUDE:
        skipped.append((name, EXCLUDE[name]))
        continue
    if dur < MIN_S:
        skipped.append((name, f"{dur:.0f} s < 5 min"))
        continue
    v = rep["video"]
    end = ts(r["received_at_utc"])
    sessions.append(dict(name=name.replace("native_decoder_", "").replace(".json", ""), dur=dur,
                         end=end, start=end - dur, v=v, dec=rep.get("decoder", {}),
                         kind="hold" if v["ssrc_changes"] == 0 else "transition"))

print("=== POPULATION ===")
print(f"adopted build from {FIRST} (P6a V1); >= 5 min; holds = no SSRC change")
print(f"{'session':<22} {'kind':<10} {'min':>6} {'ssrc':>4} {'lost':>5} {'inres':>5} {'gapev':>5} "
      f"{'maxgap':>6} {'fecrec':>6} {'unrec':>5} {'parity%':>7} {'hold_ms':>7}")
for s in sessions:
    v = s["v"]
    s["L"] = v["lost_packets"] - v["lost_packets_in_resyncs"]
    par = 100.0 * v["fec_parity_packets"] / max(1, v["packets"])
    print(f"{s['name']:<22} {s['kind']:<10} {s['dur'] / 60:6.1f} {v['ssrc_changes']:4} {v['lost_packets']:5} "
          f"{v['lost_packets_in_resyncs']:5} {v['forward_gap_events']:5} {v['max_forward_gap_packets']:6} "
          f"{v['fec_recovered_packets']:6} {v['fec_unrecoverable_groups']:5} {par:7.1f} {v.get('fec_max_hold_ms', 0):7}")
print(f"sessions: {len(sessions)} (holds {sum(s['kind'] == 'hold' for s in sessions)}, "
      f"transition {sum(s['kind'] == 'transition' for s in sessions)})")
for name, why in skipped:
    print(f"  skipped {name}: {why}")
print()

# ---------------------------------------------------------------- windows
F = ("lost_packets", "lost_packets_in_resyncs", "forward_gap_events", "fec_recovered_packets",
     "fec_unrecoverable_groups", "rendered_frames", "queued_frames", "stream_resyncs")


def session_rows(s):
    i, j = bisect_left(hb_t, s["start"] - 10), bisect_right(hb_t, s["end"] + 5)
    rows = [r for r in hb_rows[i:j]]
    # one client session: the longest run of rising elapsed_ms ending nearest the report
    runs, cur = [], []
    for r in rows:
        if cur and r["elapsed_ms"] <= cur[-1]["elapsed_ms"]:
            runs.append(cur)
            cur = []
        cur.append(r)
    if cur:
        runs.append(cur)
    return max(runs, key=len) if runs else []


def frames_between(t0, t1):
    i, j = bisect_left(fr_keys, math.floor(t0)), bisect_right(fr_keys, math.floor(t1))
    return [FR[k] for k in fr_keys[i:j]]


def t2_between(t0, t1):
    i, j = bisect_left(t2_t, t0), bisect_right(t2_t, t1)
    return t2_rows[i:j]


minutes = []          # per-client-minute rows over all sessions
single_gap_sizes = []  # exact b from windows with exactly one gap event
single_gap_warm = []
for s in sessions:
    rows = session_rows(s)
    s["hb_n"] = len(rows)
    s["hb_cover_s"] = (rows[-1]["elapsed_ms"] - rows[0]["elapsed_ms"]) / 1000.0 if len(rows) > 1 else 0.0
    ub_k2 = ub_41 = pt_k2 = pt_41 = L_series = 0
    per_min = {}
    for a, b in zip(rows, rows[1:]):
        d = {k: (b.get(k, 0) or 0) - (a.get(k, 0) or 0) for k in F}
        dL = d["lost_packets"] - d["lost_packets_in_resyncs"]
        dG = d["forward_gap_events"]
        if min(d.values()) < 0:
            continue
        if d["stream_resyncs"] > 0:
            # a restart window: its gaps belong to the resync, not to FEC
            dL = max(0, dL)
        L_series += dL
        ub_k2 += min(dL, 4 * dG)
        ub_41 += min(dL, 2 * dG)
        m = b["elapsed_ms"] // 60000
        pm = per_min.setdefault(m, dict(L=0, G=0, R=0, U=0, rend=0, q=0, dt=0.0, age=0,
                                        t0=ts(a["received_at_utc"]), t1=0.0, ub_k2=0, ub_41=0,
                                        multi=0, resync=0))
        pm["L"] += dL
        pm["G"] += dG
        pm["R"] += d["fec_recovered_packets"]
        pm["U"] += d["fec_unrecoverable_groups"]
        pm["rend"] += d["rendered_frames"]
        pm["q"] += d["queued_frames"] - d["rendered_frames"]
        pm["dt"] += (b["elapsed_ms"] - a["elapsed_ms"]) / 1000.0
        pm["age"] = max(pm["age"], b.get("last_output_age_ms", 0) or 0)
        pm["t1"] = ts(b["received_at_utc"])
        pm["ub_k2"] += min(dL, 4 * dG)
        pm["ub_41"] += min(dL, 2 * dG)
        pm["resync"] += d["stream_resyncs"]
        if dG == 1 and d["stream_resyncs"] == 0:
            single_gap_sizes.append((s["name"], dL, pm))
            pt_k2 += dL if dL <= 2 else 0
            pt_41 += 1 if dL == 1 else (2.0 / 7.0 if dL == 2 else 0)   # b=2: straddles 4|4 at 1 of 7 offsets
        if dG >= 1 and dL > dG:
            pm["multi"] += 1
    s.update(ub_k2=ub_k2, ub_41=ub_41, pt_k2=pt_k2, pt_41=pt_41, L_series=L_series,
             single_L=sum(b for n, b, _ in single_gap_sizes if n == s["name"]))
    for m, pm in sorted(per_min.items()):
        if pm["dt"] < 50:          # partial first/last minute
            continue
        fr = frames_between(pm["t0"], pm["t1"])
        t2 = t2_between(pm["t0"], pm["t1"])
        onn = [x["onn"].get("cpu_thermal_c") for x in t2 if x.get("onn", {}).get("cpu_thermal_c") is not None]
        opal = [x["opal"] for x in t2 if x.get("opal", {}).get("onn_row_found")]
        row = dict(session=s["name"], kind=s["kind"], minute=m, dt=pm["dt"],
                   L=pm["L"] * 60.0 / pm["dt"], G=pm["G"], R=pm["R"] * 60.0 / pm["dt"], U=pm["U"],
                   ub_k2=pm["ub_k2"], ub_41=pm["ub_41"], multi=pm["multi"], resync=pm["resync"],
                   fps=pm["rend"] / pm["dt"], backlog=pm["q"], age=pm["age"],
                   pps=(sum(x["packets"] for x in fr) / len(fr)) if fr else None,
                   Bps=(sum(x.get("payload_bytes", 0) for x in fr) / len(fr)) if fr and "payload_bytes" in fr[0] else None,
                   maxpk=max((x["max_packets"] for x in fr), default=None),
                   ge40=sum(x.get("frames_ge_40", 0) for x in fr) if fr else None,
                   onn_c=(sum(onn) / len(onn)) if onn else None,
                   retries=(opal[-1]["tx_retries"] - opal[0]["tx_retries"]) if len(opal) > 1 else None,
                   failed=(opal[-1]["tx_failed"] - opal[0]["tx_failed"]) if len(opal) > 1 else None)
        pm["onn_c"] = row["onn_c"]
        minutes.append(row)

# ---------------------------------------------------------------- 1. recoverability
print("=== 1. WHAT 8+1 RECOVERS, AND BOUNDS ON THE ALTERNATIVES ===")
print("per session, per minute of the report's duration; L = post-FEC lost excluding resync loss")
print("ub = upper bound summed over 2 s heartbeat windows (min(L,4G) k+2, min(L,2G) 4+1)")
print(f"{'session':<22} {'kind':<10} {'hb':>4} {'cov%':>5} {'rec/min':>7} {'unrec/min':>9} {'L/min':>6} "
      f"{'k+2 ub/min':>10} {'4+1 ub/min':>10} {'L k+2 ub':>8} {'L 4+1 ub':>8}")
for s in sessions:
    mins = s["dur"] / 60.0
    v = s["v"]
    cov = 100.0 * s["hb_cover_s"] / s["dur"]
    # the series misses the head/tail; scale the bound to the report by L / L_series when covered
    scale = (s["L"] / s["L_series"]) if s["L_series"] else 1.0
    s["ub_k2_min"] = s["ub_k2"] * max(1.0, scale) / mins if s["hb_n"] > 1 else min(s["L"], 4 * v["forward_gap_events"]) / mins
    s["ub_41_min"] = s["ub_41"] * max(1.0, scale) / mins if s["hb_n"] > 1 else min(s["L"], 2 * v["forward_gap_events"]) / mins
    s["L_min"] = s["L"] / mins
    print(f"{s['name']:<22} {s['kind']:<10} {s['hb_n']:4} {cov:5.0f} {v['fec_recovered_packets'] / mins:7.2f} "
          f"{v['fec_unrecoverable_groups'] / mins:9.2f} {s['L_min']:6.2f} {s['ub_k2_min']:10.2f} {s['ub_41_min']:10.2f} "
          f"{max(0, s['L_min'] - s['ub_k2_min']):8.2f} {max(0, s['L_min'] - s['ub_41_min']):8.2f}")
print("(no heartbeat series: session-level bound min(L, 4G) / min(L, 2G) from the report)")
print()
for label, sel in (("ALL", sessions), ("HOLDS", [s for s in sessions if s["kind"] == "hold"]),
                   ("TRANSITION", [s for s in sessions if s["kind"] == "transition"])):
    if not sel:
        continue
    print(f"{label:<10} n={len(sel):2}  median L/min {med([s['L_min'] for s in sel]):.2f}  "
          f"recovered/min {med([s['v']['fec_recovered_packets'] / (s['dur'] / 60) for s in sel]):.2f}  "
          f"unrec groups/min {med([s['v']['fec_unrecoverable_groups'] / (s['dur'] / 60) for s in sel]):.2f}  "
          f"k+2 extra ub/min {med([s['ub_k2_min'] for s in sel]):.2f}  "
          f"4+1 extra ub/min {med([s['ub_41_min'] for s in sel]):.2f}  "
          f"-> L/min k+2 >= {med([max(0, s['L_min'] - s['ub_k2_min']) for s in sel]):.2f}, "
          f"4+1 >= {med([max(0, s['L_min'] - s['ub_41_min']) for s in sel]):.2f}")
print()
sizes = [b for _, b, _ in single_gap_sizes]
print(f"post-FEC gap sizes, exact (windows holding exactly one gap event, no resync): n = {len(sizes)}")
hist = {}
for b in sizes:
    key = b if b <= 8 else (">8-16" if b <= 16 else ">16")
    hist[key] = hist.get(key, 0) + 1
for k in [1, 2, 3, 4, 5, 6, 7, 8, ">8-16", ">16"]:
    if k in hist:
        print(f"  b = {str(k):>6}: {hist[k]:5}  ({100.0 * hist[k] / len(sizes):5.1f} %)")
print(f"  packets in them: {sum(sizes)}; in b <= 2 gaps: {sum(b for b in sizes if b <= 2)} "
      f"({100.0 * sum(b for b in sizes if b <= 2) / max(1, sum(sizes)):.1f} %)")
tot_min = sum(s["dur"] for s in sessions) / 60.0
print(f"point estimate over the single-gap windows (not the rule's input): k+2 would restore "
      f"{sum(s['pt_k2'] for s in sessions)} packets, 4+1 ~{sum(s['pt_41'] for s in sessions):.0f}, "
      f"over {tot_min:.0f} session-minutes")
frac_k2 = sum(s['pt_k2'] for s in sessions) / max(1, sum(sizes))
frac_41 = sum(s['pt_41'] for s in sessions) / max(1, sum(sizes))
for s in sessions:
    f2 = s['pt_k2'] / s['single_L'] if s['single_L'] >= 20 else frac_k2
    f4 = s['pt_41'] / s['single_L'] if s['single_L'] >= 20 else frac_41
    s['pt_k2_min'] = s['L_min'] * f2
    s['pt_41_min'] = s['L_min'] * f4
print(f"point estimate scaled to each session's L (own single-gap fraction when >= 20 packets, else the "
      f"population's {100 * frac_k2:.1f} % / {100 * frac_41:.1f} %):")
for label, sel in (("ALL", sessions), ("HOLDS", [s for s in sessions if s["kind"] == "hold"]),
                   ("TRANSITION", [s for s in sessions if s["kind"] == "transition"])):
    print(f"  {label:<10} median extra recoverable /min: k+2 {med([s['pt_k2_min'] for s in sel]):.2f}, "
          f"4+1 {med([s['pt_41_min'] for s in sel]):.2f}; post-FEC L/min would be k+2 "
          f"{med([s['L_min'] - s['pt_k2_min'] for s in sel]):.2f}, 4+1 {med([s['L_min'] - s['pt_41_min'] for s in sel]):.2f} "
          f"(actual {med([s['L_min'] for s in sel]):.2f})")
print()
# overheads
pk = sum(s["v"]["packets"] for s in sessions)
par = sum(s["v"]["fec_parity_packets"] for s in sessions)
frames = sum(s["v"]["frames"] for s in sessions)
print("overhead, parity packets per data packet, whole population:")
print(f"  8+1 actual (partial last groups included): {100.0 * par / pk:.1f} %  (nominal 12.5 %)")
print(f"  k+2 (two parities per 8-group):            {200.0 * par / pk:.1f} %  (nominal 25 %)")
print(f"  4+1 bounds: >= {100.0 * pk / 4 / pk:.1f} % (nominal) and <= {100.0 * (pk / 4 + frames) / pk:.1f} % "
      f"(one partial group per frame); 8+1 groups/frame here {par / max(1, frames):.2f}")
print()

# ---------------------------------------------------------------- 2. pressure
print("=== 2. IS ANY OF IT CAPACITY PRESSURE? (per client minute, full minutes only) ===")
cols = [("fps", "rendered fps (for recent_fps)"),
        ("backlog", "frames queued-not-rendered / min (for queue depth)"),
        ("age", "max last_output_age_ms at the 2 s beats (for output gap)"),
        ("pps", "host packets / s (offered load)"),
        ("Bps", "host payload bytes / s"),
        ("maxpk", "largest frame, packets"),
        ("ge40", "frames >= 40 packets / min"),
        ("retries", "Opal tx_retries / min (t2 minutes only)"),
        ("failed", "Opal tx_failed / min (t2 minutes only; tracks tx_retries)")]


def pressure(sel, label):
    print(f"-- {label}: {len(sel)} minutes, {sum(1 for m in sel if m['L'] > 0)} with loss")
    print(f"   {'column':<55} {'n':>5} {'rho':>6}   bucket medians: loss 0 | 1-5 | 6-20 | >20   monotone rise")
    verdict_rho = True
    verdict_mono_q = verdict_mono_g = False
    for c, desc in cols:
        pairs = [(m["L"], m[c]) for m in sel if m[c] is not None]
        if len(pairs) < 10:
            print(f"   {desc:<55} {len(pairs):5}   n/a")
            continue
        rho = spearman([p[0] for p in pairs], [p[1] for p in pairs])
        buckets = [[y for x, y in pairs if x == 0], [y for x, y in pairs if 0 < x <= 5],
                   [y for x, y in pairs if 5 < x <= 20], [y for x, y in pairs if x > 20]]
        meds = [med(b) for b in buckets]
        present = [x for x in meds if not math.isnan(x)]
        mono = len(present) >= 3 and all(a < b for a, b in zip(present, present[1:]))
        if abs(rho) >= 0.3:
            verdict_rho = False
        if c == "backlog" and mono:
            verdict_mono_q = True
        if c == "age" and mono:
            verdict_mono_g = True
        cells = " | ".join(f"{x:8.1f}" if not math.isnan(x) else "       -" for x in meds)
        ns = "/".join(str(len(b)) for b in buckets)
        print(f"   {desc:<55} {len(pairs):5} {rho:+6.2f}   {cells}   {'YES' if mono else 'no'}  (n {ns})")
    absent = verdict_rho and not verdict_mono_q and not verdict_mono_g
    present_ = verdict_mono_q or verdict_mono_g
    print(f"   reading: |rho| < 0.3 on every column: {verdict_rho}; queue-depth substitute rises: {verdict_mono_q}; "
          f"output-gap substitute rises: {verdict_mono_g}  ->  "
          f"{'ABSENT' if absent else ('PRESENT' if present_ else 'NEITHER (a |rho| >= 0.3 without a monotone rise)')}")
    return absent, present_


holds_m = [m for m in minutes if m["kind"] == "hold"]
all_m = [m for m in minutes if m["resync"] == 0]
res_all = pressure(all_m, "all sessions, minutes without a restart")
res_hold = pressure(holds_m, "holds only")
print()

# ---------------------------------------------------------------- 3. warm
print("=== 3. THE WARM STATE (onn cpu-thermal >= 67.5 C, minutes with t2 samples) ===")
therm = [m for m in all_m if m["onn_c"] is not None]
warm = [m for m in therm if m["onn_c"] >= WARM_C]
cool = [m for m in therm if m["onn_c"] < WARM_C]
for lab, sel in (("warm", warm), ("cool", cool)):
    if not sel:
        print(f"{lab}: 0 minutes")
        continue
    Ls = [m["L"] for m in sel]
    print(f"{lab}: {len(sel)} minutes from {len(set(m['session'] for m in sel))} sessions; loss/min median "
          f"{med(Ls):.1f}, mean {statistics.mean(Ls):.2f}; recovered/min median {med([m['R'] for m in sel]):.1f}; "
          f"minutes with a multi-packet window {sum(1 for m in sel if m['multi'])}; "
          f"k+2 ub/min {statistics.mean([m['ub_k2'] * 60 / m['dt'] for m in sel]):.2f}, "
          f"4+1 ub/min {statistics.mean([m['ub_41'] * 60 / m['dt'] for m in sel]):.2f}")
if warm:
    pressure(warm, "warm minutes")
ws = [b for _, b, pm in single_gap_sizes if pm.get("onn_c") is not None and pm["onn_c"] >= WARM_C]
cs = [b for _, b, pm in single_gap_sizes if pm.get("onn_c") is not None and pm["onn_c"] < WARM_C]
for lab, v in (("warm", ws), ("cool", cs)):
    if v:
        print(f"exact single-gap sizes, {lab}: n = {len(v)}, b = 1: {sum(1 for b in v if b == 1)}, b = 2: "
              f"{sum(1 for b in v if b == 2)}, b >= 3: {sum(1 for b in v if b >= 3)}, max {max(v)}")
print()

# ---------------------------------------------------------------- 4. latency
print("=== 4. COST IN LATENCY -- group completion delay ===")
secs = [FR[k] for k in fr_keys if FR[k].get("packets")]
pps = [x["packets"] for x in secs]
fps_h = [x["frames"] for x in secs]
if secs:
    mean_pps = statistics.mean(pps)
    interval_ms = 1000.0 / mean_pps
    mean_pkt_per_frame = sum(pps) / max(1, sum(fps_h))
    print(f"host seconds with packets: {len(secs)}; mean packets/s {mean_pps:.0f} -> mean interval {interval_ms:.3f} ms; "
          f"mean packets/frame {mean_pkt_per_frame:.1f}")
    for g, lab in ((8, "8+1 (now)"), (8, "k+2 = 8+2"), (4, "4+1"), (16, "16+2 (for scale)")):
        print(f"  {lab:<18} group {g:2} x {interval_ms:.3f} ms = {g * interval_ms:6.2f} ms (the task's formula)")
    print("  groups never span frames and each frame leaves as one burst (pacing off), so inside a")
    print("  frame the parity follows its 8th packet by the burst's own spacing; the client's")
    print(f"  measured hold for a gap: max {max(s['v'].get('fec_max_hold_ms', 0) for s in sessions)} ms "
          f"(fec_max_hold_ms, population max; timeout 12 ms)")
print()
print("=== DECISION INPUTS ===")
ub2 = med([s["ub_k2_min"] for s in sessions])
ub4 = med([s["ub_41_min"] for s in sessions])
pt2 = med([s["pt_k2_min"] for s in sessions])
pt4 = med([s["pt_41_min"] for s in sessions])
print(f"corpus median extra recoverable, UPPER BOUND (the pre-registered computation): k+2 {ub2:.2f} /min, 4+1 {ub4:.2f} /min")
print(f"corpus median extra recoverable, point estimate (b <= 2 gaps; not the rule's input): k+2 {pt2:.2f} /min, 4+1 {pt4:.2f} /min")
absent, present = res_all
print(f"capacity pressure on the corpus, by the rule's definitions: ABSENT {absent}, PRESENT {present}")
print("rule branches, as written:")
print(f"  DEFER WITH EVIDENCE: extra < 2 under k+2 or 4+1 ({ub2 < 2 or ub4 < 2}) AND pressure absent ({absent})"
      f" -> {(ub2 < 2 or ub4 < 2) and absent}")
print(f"  BUILD (static k+2 first): a fixed alternative >= 5 more ({ub2 >= 5 or ub4 >= 5}) with no pressure signal"
      f" (not PRESENT: {not present}) -> {(ub2 >= 5 or ub4 >= 5) and not present}")
print(f"  BUILD ADAPTIVE: pressure present ({present}) and loss rises with it -> {present}")
