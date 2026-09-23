#!/usr/bin/env python3
"""D-BASE-T2 analysis: does audio loss track a host sensor, an onn signal or
the AP over back-to-back streaming, and does it reset with idle?

Inputs (this directory): t2_samples.jsonl (10 s rows over the whole run),
runs/heartbeat_<S>.jsonl and runs/report_<S>.json for Sa, Sb, Sc, Sd,
runs/index.txt (session windows, idle begin/end).

Definitions fixed here BEFORE the run's data existed:
  * a session MINUTE = 30 consecutive heartbeat deltas (2 s); its UTC
    window runs from the first to the last heartbeat row of the group.
    Audio / video loss per minute = the sum of the deltas.
  * a signal's value for a minute = the mean of the sampler rows whose
    timestamp falls in that minute's window. Counters (eno1 drops/errors,
    Opal tx_retries / tx_packets) are differenced per sampler round first.
  * OPENING of a session = mean audio loss/min over minutes 1-3; ENDING =
    mean over its last 3 minutes. LOW = opening < 15/min.
  * Spearman rho of audio loss/min against each signal over all session
    minutes (4 x 19 full minutes -- 596 deltas per 20-min hold, the partial
    20th is dropped); |rho| >= 0.6 implicates.
  * a signal RESET during the idle if, at the idle's last 2 minutes, it has
    recovered >= 75 % of its rise from S-a's opening (first 3 min) to
    S-b's ending (last 3 min); it did NOT reset if it recovered < 50 %.
    A signal with a rise under its own noise (|rise| < 2 x the SD of its
    S-a first 3 minutes, floor 0.5 unit) is FLAT.

Readings (handoffs/D-BASE-T2_TASK.md), checked in this order:
  NOT REPRODUCED  S-a and S-b openings within 20 % of each other and both LOW
  HOST            a host temperature or CPU-MHz signal |rho| >= 0.6 that
                  RESET in the idle while the other implicated signals did not
  ONN             the onn's thermal status changed, or its link speed / RSSI
                  |rho| >= 0.6
  AP              an Opal rate / MCS / signal |rho| >= 0.6 (falling with
                  loss) while every host and onn signal is |rho| < 0.6
  TIME ONLY       no signal reaches |rho| 0.6 and S-c opens >= 80 % of S-b's
                  ending (the idle did not reset the loss)
  otherwise       MIXED -- reported as measured.
Thresholds (proposals only) for an implicated signal: its minute value at
the first minute audio loss/min >= 30 (warn) and >= 100 (act).
"""
import json, os, statistics as st
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(HERE, "runs")
SESS = ["Sa", "Sb", "Sc", "Sd"]


def ts(s):
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in s[:23] else "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(s[:23].rstrip("Z"), fmt).replace(tzinfo=timezone.utc).timestamp()


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            r[o[k]] = (i + j) / 2.0
        i = j + 1
    return r


def spearman(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 10:
        return None
    rx, ry = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else None


# ---- sampler rows -> flat signals ---------------------------------------
rows = [json.loads(l) for l in open(os.path.join(HERE, "t2_samples.jsonl")) if l.strip()]
flat = []
prev = None
for r in rows:
    f = {"t": ts(r["at_utc"])}
    h, o, p = r.get("host") or {}, r.get("onn") or {}, r.get("opal") or {}
    for k, v in (h.get("temps_c") or {}).items():
        f["host." + k] = v
    if h.get("temps_c"):
        f["host.hottest_c"] = max(h["temps_c"].values())
    f["host.cpu_mhz_min"] = h.get("cpu_mhz_min")
    f["host.cpu_mhz_mean"] = h.get("cpu_mhz_mean")
    f["host.encoder_cpu_pct"] = (h.get("encoder") or {}).get("cpu_pct")
    f["host.retroarch_cpu_pct"] = (h.get("retroarch") or {}).get("cpu_pct")
    net = h.get("net_eno1") or {}
    for k in ("onn.thermal_status", "onn.cpu_thermal_c", "onn.rssi_dbm", "onn.link_mbps",
              "onn.tx_link_mbps", "onn.rx_link_mbps"):
        f[k] = o.get(k.split(".", 1)[1])
    for k in ("signal_dbm", "signal_avg_dbm", "tx_bitrate_mbps", "tx_mcs", "rx_bitrate_mbps",
              "rx_mcs", "soc_temp_c", "load1", "inactive_ms"):
        f["opal." + k] = p.get(k)
    if prev is not None:
        pn = prev["net"]
        for k in ("rx_drop", "rx_errs", "tx_drop", "tx_errs"):
            if k in net and k in pn:
                f[f"host.eno1_{k}_delta"] = net[k] - pn[k]
        pp = prev["opal"]
        if p.get("tx_packets") is not None and pp.get("tx_packets") is not None:
            dp = p["tx_packets"] - pp["tx_packets"]
            dr = (p.get("tx_retries") or 0) - (pp.get("tx_retries") or 0)
            f["opal.tx_retry_ratio"] = (dr / dp) if dp > 0 else None
            f["opal.tx_pkts_per_s"] = dp / max(1e-6, f["t"] - prev["t"])
    prev = {"t": f["t"], "net": net, "opal": p}
    flat.append(f)
SIGNALS = sorted({k for f in flat for k in f if k != "t"})


def window_mean(key, t0, t1):
    v = [f[key] for f in flat if t0 <= f["t"] < t1 and f.get(key) is not None]
    return st.mean(v) if v else None


# ---- sessions -> minutes --------------------------------------------------
minutes = []   # dicts: session, idx, t0, t1, audio, video
for s in SESS:
    p = os.path.join(RUNS, f"heartbeat_{s}.jsonl")
    if not os.path.exists(p):
        continue
    hb = [json.loads(l) for l in open(p) if l.strip()]
    hb = [x for x in hb if "audio_lost_packets" in x]
    for i in range(0, len(hb) - 1, 30):
        g = hb[i:i + 31]
        if len(g) < 31:
            break
        minutes.append({"session": s, "idx": i // 30 + 1,
                        "t0": ts(g[0]["received_at_utc"]), "t1": ts(g[-1]["received_at_utc"]),
                        "audio": g[-1]["audio_lost_packets"] - g[0]["audio_lost_packets"],
                        "video": g[-1]["lost_packets"] - g[0]["lost_packets"]})
for m in minutes:
    for k in SIGNALS:
        m[k] = window_mean(k, m["t0"], m["t1"])

idx = {}
for line in open(os.path.join(RUNS, "index.txt")):
    w = line.split()
    if w and w[0] in ("idle_begin", "idle_end"):
        idx[w[0]] = ts(w[1])

print("== per session: audio / video loss per minute (heartbeat)")
by = {s: [m for m in minutes if m["session"] == s] for s in SESS}
for s in SESS:
    if by[s]:
        print(f"  {s} audio {[m['audio'] for m in by[s]]}  total {sum(m['audio'] for m in by[s])}")
        print(f"  {s} video {[m['video'] for m in by[s]]}  total {sum(m['video'] for m in by[s])}")


def opening(s, n=3):
    return st.mean(m["audio"] for m in by[s][:n])


def ending(s, n=3):
    return st.mean(m["audio"] for m in by[s][-n:])


summary = {"sessions": {}, "rho": {}, "reset": {}, "timeline": []}
for s in SESS:
    if by[s]:
        summary["sessions"][s] = {"opening": opening(s), "ending": ending(s),
                                  "audio_total": sum(m["audio"] for m in by[s]),
                                  "video_total": sum(m["video"] for m in by[s])}
        print(f"  {s}: opening {opening(s):.1f}/min, ending {ending(s):.1f}/min")

# ---- timeline (per minute of wall clock, whole run) ------------------------
print("\n== timeline, per wall-clock minute (signals) with audio loss where streaming")
KEY = ["host.hottest_c", "host.k10temp/Tctl", "host.amdgpu/edge", "host.cpu_mhz_min", "host.encoder_cpu_pct",
       "onn.cpu_thermal_c", "onn.thermal_status", "onn.rssi_dbm", "onn.tx_link_mbps", "onn.rx_link_mbps",
       "opal.signal_avg_dbm", "opal.tx_bitrate_mbps", "opal.tx_mcs", "opal.tx_retry_ratio", "opal.soc_temp_c", "opal.load1"]
KEY = [k for k in KEY if k in SIGNALS]
t_first, t_last = flat[0]["t"], flat[-1]["t"]
print("  utc    " + " ".join(f"{k.split('.',1)[1][:10]:>10s}" for k in KEY) + "  audio/min")
t = t_first - (t_first % 60)
while t < t_last:
    row = {k: window_mean(k, t, t + 60) for k in KEY}
    aud = [m["audio"] for m in minutes if t <= (m["t0"] + m["t1"]) / 2 < t + 60]
    label = datetime.fromtimestamp(t, timezone.utc).strftime("%H:%M")
    summary["timeline"].append({"utc": label, **row, "audio_per_min": aud[0] if aud else None})
    print(f"  {label}  " + " ".join(f"{row[k]:10.2f}" if row[k] is not None else f"{'-':>10s}" for k in KEY)
          + (f"  {aud[0]:6d}" if aud else "       -"))
    t += 60

# ---- correlations -------------------------------------------------------
print("\n== Spearman rho, audio loss/min vs signal, all session minutes (n = %d)" % len(minutes))
aud = [m["audio"] for m in minutes]
elapsed = []
acc = 0
for s in SESS:
    for m in by[s]:
        acc += 1
        elapsed.append(acc)
summary["rho"]["streaming_minutes_since_run_start (context)"] = spearman(elapsed, aud)
for k in SIGNALS:
    r = spearman([m[k] for m in minutes], aud)
    summary["rho"][k] = r
for k, r in sorted(summary["rho"].items(), key=lambda kv: -abs(kv[1] or 0)):
    if r is not None:
        print(f"  {r:+.3f}  {k}" + ("   <-- |rho| >= 0.6" if abs(r) >= 0.6 else ""))
video = [m["video"] for m in minutes]
summary["rho_video_audio"] = spearman(video, aud)
print(f"  video loss/min vs audio loss/min: {summary['rho_video_audio']:+.3f}")

# ---- idle recovery --------------------------------------------------------
print("\n== idle recovery: S-a opening -> S-b ending -> idle end -> S-c opening")
if by["Sa"] and by["Sb"] and "idle_end" in idx:
    a0, a1 = by["Sa"][0]["t0"], by["Sa"][2]["t1"]
    b0, b1 = by["Sb"][-3]["t0"], by["Sb"][-1]["t1"]
    i0, i1 = idx["idle_end"] - 120, idx["idle_end"]
    c0, c1 = (by["Sc"][0]["t0"], by["Sc"][2]["t1"]) if by["Sc"] else (None, None)
    for k in SIGNALS:
        va, vb, vi = window_mean(k, a0, a1), window_mean(k, b0, b1), window_mean(k, i0, i1)
        vc = window_mean(k, c0, c1) if c0 else None
        if None in (va, vb, vi):
            continue
        base = [f[k] for f in flat if a0 <= f["t"] < a1 and f.get(k) is not None]
        noise = max(0.5, 2 * (st.pstdev(base) if len(base) > 1 else 0))
        rise = vb - va
        if abs(rise) < noise:
            state, rec = "FLAT", None
        else:
            rec = (vb - vi) / rise
            state = "RESET" if rec >= 0.75 else ("NOT RESET" if rec < 0.5 else "PARTIAL")
        summary["reset"][k] = {"sa_open": va, "sb_end": vb, "idle_end": vi, "sc_open": vc,
                               "recovered": rec, "state": state}
    for k in sorted(summary["reset"], key=lambda k: (summary["reset"][k]["state"], k)):
        d = summary["reset"][k]
        rec = f"{d['recovered']:.0%}" if d["recovered"] is not None else "-"
        sc = f"{d['sc_open']:.2f}" if d["sc_open"] is not None else "-"
        print(f"  {d['state']:9s} {k:32s} {d['sa_open']:9.2f} -> {d['sb_end']:9.2f} -> {d['idle_end']:9.2f} -> {sc:>9s} (recovered {rec})")
    if by["Sc"]:
        print(f"  audio loss: S-a opening {opening('Sa'):.1f} -> S-b ending {ending('Sb'):.1f} -> S-c opening {opening('Sc'):.1f}")

# ---- the reading ------------------------------------------------------------
def implicated(prefix):
    return {k: r for k, r in summary["rho"].items() if k.startswith(prefix) and r is not None and abs(r) >= 0.6}


reading, why = None, []
if by["Sa"] and by["Sb"]:
    oa, ob = opening("Sa"), opening("Sb")
    if oa < 15 and ob < 15 and abs(ob - oa) <= 0.2 * max(oa, ob, 1e-9):
        reading = "NOT REPRODUCED"
        why.append(f"S-a opens {oa:.1f}, S-b {ob:.1f}: within 20 %, both low")
host_imp = {k: r for k, r in implicated("host.").items()
            if "_c" in k or "cpu_mhz" in k or "Tctl" in k or "edge" in k or "Composite" in k or "Sensor" in k}
onn_imp = implicated("onn.")
ap_imp = {k: r for k, r in implicated("opal.").items()
          if any(x in k for x in ("bitrate", "mcs", "signal"))}
other_imp = {**implicated("host."), **implicated("onn."), **implicated("opal.")}
if reading is None and host_imp:
    reset_host = [k for k in host_imp if summary["reset"].get(k, {}).get("state") == "RESET"]
    others_reset = [k for k in other_imp if k not in host_imp
                    and summary["reset"].get(k, {}).get("state") == "RESET"]
    if reset_host and not others_reset:
        reading = "HOST THERMAL / CLOCK"
        why.append(f"implicated and reset: {reset_host}; no other implicated signal reset")
    else:
        why.append(f"host signals implicated {list(host_imp)} but reset test: host {reset_host}, others {others_reset}")
if reading is None:
    status_changed = len({f.get('onn.thermal_status') for f in flat if f.get('onn.thermal_status') is not None}) > 1
    onn_link = {k: r for k, r in onn_imp.items() if any(x in k for x in ("link", "rssi"))}
    if status_changed or onn_link:
        reading = "ONN-SIDE"
        why.append(f"thermal status changed {status_changed}; link/RSSI implicated {list(onn_link)}")
if reading is None and ap_imp and not host_imp and not onn_imp:
    reading = "AP-SIDE"
    why.append(f"Opal rate/signal implicated {ap_imp}, host and onn flat")
if reading is None and not other_imp and by["Sc"] and by["Sb"]:
    if opening("Sc") >= 0.8 * ending("Sb"):
        reading = "TIME ONLY"
        why.append(f"nothing |rho| >= 0.6; S-c opens {opening('Sc'):.1f} vs S-b ending {ending('Sb'):.1f}")
if reading is None:
    reading = "MIXED"
    why.append(f"implicated: {sorted(other_imp)}")
summary["reading"] = {"reading": reading, "why": why}
print(f"\n== READING: {reading}\n  " + "\n  ".join(why))

# ---- thresholds (proposals) --------------------------------------------------
summary["thresholds"] = {}
for k in sorted(other_imp):
    warn = next((m[k] for m in minutes if m["audio"] >= 30 and m[k] is not None), None)
    act = next((m[k] for m in minutes if m["audio"] >= 100 and m[k] is not None), None)
    summary["thresholds"][k] = {"warn_at_30_per_min": warn, "act_at_100_per_min": act}
    print(f"  threshold proposal {k}: warn (loss >= 30/min first) {warn}, act (>= 100/min first) {act}")

json.dump(summary, open(os.path.join(HERE, "t2_summary.json"), "w"), indent=1, default=str)
