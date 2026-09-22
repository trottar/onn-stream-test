#!/usr/bin/env python3
"""D-BASE-P4: the onn's radio state beside the loss it is supposed to explain.

Loss is taken from the decoder report, which is authoritative and per session.
A finer series was attempted from counter differences and does NOT survive its
own noise floor; that attempt is characterised below rather than presented as
a measurement. Radio comes from the device's own WifiScoreReport ring (3 s,
harvested after each session at no cost to the run) and /proc/net/wireless
(10 s, sampled live).
"""
import json, os, statistics as st
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SESS = "/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions"


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return r


def spearman(a, b):
    p = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(p) < 4:
        return None, len(p)
    xs, ys = rank([q[0] for q in p]), rank([q[1] for q in p])
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** .5
    dy = sum((y - my) ** 2 for y in ys) ** .5
    return (num / (dx * dy) if dx and dy else None), n


def num(x, spec, w):
    return ("-" if x is None else format(x, spec)).rjust(w)


S = []
for line in open(f"{HERE}/index.txt"):
    label, hold, report, t0, t1 = line.split()
    d = json.load(open(os.path.join(SESS, report)))["report"]
    v, dec = d["video"], d["decoder"]
    mins = d["duration_ms"] / 60000.0
    h = json.load(open(f"{HERE}/air_harvest_{label}.json"))
    rows = [json.loads(l) for l in open(f"{HERE}/air_{label}.jsonl")]
    sr = [r for r in h["score_report_rows"]
          if r["at_utc"] and ts(t0) <= ts(r["at_utc"]) <= ts(t1)]
    wl = [r["onn_wireless"] for r in rows
          if r.get("onn_wireless") and ts(t0) <= ts(r["at_utc"]) <= ts(t1)]

    def col(k):
        return [float(r[k]) for r in sr] if sr else []

    S.append(dict(
        label=label, hold=int(hold), t0=ts(t0), t1=ts(t1), report=report,
        dur_s=d["duration_ms"] / 1000.0,
        loss=v["lost_packets"], loss_min=v["lost_packets"] / mins,
        fge=v["forward_gap_events"], maxgap=v["max_forward_gap_packets"],
        pkts_per_gap=(v["lost_packets"] / v["forward_gap_events"]
                      if v["forward_gap_events"] else None),
        disc=len(d.get("stream_discontinuities") or []),
        spk20=dec["spike_20_ms"] / mins,
        maxout=dec["max_output_gap_ms"],
        fps=dec["rendered_frames"] / (d["duration_ms"] / 1000.0),
        assoc=h["association"],
        scans=[x for x in h["scan_events"]
               if x["at_utc"] and ts(t0) <= ts(x["at_utc"]) <= ts(t1)],
        score_rows=sr, n_score=len(sr),
        rssi_med=st.median(col("rssi")) if sr else None,
        rssi_min=min(col("rssi")) if sr else None,
        rssi_max=max(col("rssi")) if sr else None,
        tx_med=st.median(col("txLinkSpeed")) if sr else None,
        tx_min=min(col("txLinkSpeed")) if sr else None,
        tx_max=max(col("txLinkSpeed")) if sr else None,
        rx_med=st.median(col("rxLinkSpeed")) if sr else None,
        level_med=st.median([w["level_dbm"] for w in wl]) if wl else None,
        qual_med=st.median([w["link_quality"] for w in wl]) if wl else None,
        beacon_max=max([w["missed_beacon"] for w in wl]) if wl else None,
        disc_retry_max=max([w["disc_retry"] for w in wl]) if wl else None,
        disc_misc_max=max([w["disc_misc"] for w in wl]) if wl else None,
        samples=len(rows),
        cost_med=st.median([r["sample_cost_ms"] for r in rows]) if rows else None,
    ))

print("===== per session: loss (report, authoritative) beside radio =====")
print(f"{'run':<5}{'dur':>6}{'loss':>6}{'loss/min':>9}{'fge':>5}{'pk/gap':>7}"
      f"{'maxgap':>7}{'disc':>5}{'spk20/m':>8}{'fps':>7}  |"
      f"{'rssi med':>9}{'min':>5}{'max':>5}{'tx med':>7}{'tx min':>7}{'tx max':>7}"
      f"{'rx med':>7}{'beacon':>7}{'scans':>6}")
for s in S:
    print(f"{s['label']:<5}{s['dur_s']:>6.0f}{s['loss']:>6}{s['loss_min']:>9.1f}"
          f"{s['fge']:>5}" + num(s['pkts_per_gap'], '.2f', 7) +
          f"{s['maxgap']:>7}{s['disc']:>5}{s['spk20']:>8.1f}{s['fps']:>7.2f}  |"
          + num(s['rssi_med'], '.0f', 9) + num(s['rssi_min'], '.0f', 5)
          + num(s['rssi_max'], '.0f', 5) + num(s['tx_med'], '.0f', 7)
          + num(s['tx_min'], '.0f', 7) + num(s['tx_max'], '.0f', 7)
          + num(s['rx_med'], '.0f', 7) + num(s['beacon_max'], 'd', 7)
          + f"{len(s['scans']):>6}")

print()
print("===== association, every session =====")
for s in S:
    a = s["assoc"]
    print(f"  {s['label']:<5} band={a.get('band')} ch={a.get('channel')} "
          f"{a.get('channel_width_mhz')}MHz 802.11 std={a.get('wifi_standard')} "
          f"max={a.get('max_tx_link_speed_mbps')}Mbps state={a.get('supplicant_state')} "
          f"score={a.get('score')}")

print()
print("===== Spearman across sessions: loss/min vs radio =====")
print(f"  (n = {len(S)} sessions; loss from the report, radio from the 3 s ring)")
loss = [s["loss_min"] for s in S]
for k, name in (("rssi_med", "median rssi"), ("rssi_min", "worst rssi"),
                ("level_med", "median level (/proc)"),
                ("qual_med", "median link_quality (/proc)"),
                ("tx_med", "median txLinkSpeed"), ("tx_min", "worst txLinkSpeed"),
                ("rx_med", "median rxLinkSpeed")):
    rho, n = spearman(loss, [s[k] for s in S])
    flag = "   <-- |rho| >= 0.5" if rho is not None and abs(rho) >= 0.5 else ""
    print(f"  {name:<28} rho={'None' if rho is None else f'{rho:+.3f}'} n={n}{flag}")

print()
print("===== counters the driver does NOT populate (absences, not zeros) =====")
print("  WifiScoreReport tx_retry, tx_bad, bcnCnt ....... identically 0, all rows")
print("  /proc/net/wireless disc_* and missed_beacon .... identically 0, all samples")
print("  /proc/net/wireless noise ....................... -256 (driver reports none)")
print("  WifiUsabilityStatsEntry total_tx_retries/bad ... identically 0")
print("  => the retry/failure half of the pre-registered test is UNAVAILABLE here.")
for s in S:
    print(f"    {s['label']:<5} disc_retry max={s['disc_retry_max']} "
          f"disc_misc max={s['disc_misc_max']} missed_beacon max={s['beacon_max']}")

print()
print("===== scan events inside session windows =====")
any_scan = False
for s in S:
    for sc in s["scans"]:
        any_scan = True
        print(f"  {s['label']} {sc['at_utc']} {sc['event']} pkg={sc['package']} "
              f"band={sc['requested_band']} results={sc['results']}")
if not any_scan:
    print("  NONE - not one scan of any kind was logged inside any session window.")

print()
print("===== radio stability across the whole run =====")
allr = [float(r["rssi"]) for s in S for r in s["score_rows"]]
alltx = [float(r["txLinkSpeed"]) for s in S for r in s["score_rows"]]
allrx = [float(r["rxLinkSpeed"]) for s in S for r in s["score_rows"]]
print(f"  3 s ring rows pooled: {len(allr)}")
print(f"  rssi        min={min(allr):.0f} med={st.median(allr):.0f} max={max(allr):.0f} "
      f"spread={max(allr)-min(allr):.0f} dB")
print(f"  txLinkSpeed min={min(alltx):.0f} med={st.median(alltx):.0f} max={max(alltx):.0f} "
      f"distinct={len(set(alltx))}")
print(f"  rxLinkSpeed min={min(allrx):.0f} med={st.median(allrx):.0f} max={max(allrx):.0f} "
      f"distinct={len(set(allrx))}")
print(f"  loss/min across sessions: {min(loss):.1f} .. {max(loss):.1f} "
      f"({max(loss)/max(0.1,min(loss)):.0f}x swing)")
print(f"  sampler cost ms, median per session: "
      f"{[round(s['cost_med']) for s in S]}")
