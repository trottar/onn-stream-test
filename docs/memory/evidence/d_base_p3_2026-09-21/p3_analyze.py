#!/usr/bin/env python3
"""D-BASE-P3: paired off/on comparison of the relay sender pacer.

Two blocks: PACING_US=150 (5 pairs, strictly alternating, starting off) and
PACING_US=400 (2 pairs, the scaling probe). Fields absent from a report print
as '-' and are excluded from medians; they are never read as zero.
"""
import json, os, sys, statistics as st

REPO = "/home/privyhub/Projects/onn-stream-test"
SESS = f"{REPO}/logs/games/decoder_sessions"
HERE = os.path.dirname(os.path.abspath(__file__))
IDX = sys.argv[1] if len(sys.argv) > 1 else f"{HERE}/index.txt"


def metrics(name, label, pacing):
    d = json.load(open(os.path.join(SESS, name)))
    r = d["report"]; v, dec = r["video"], r["decoder"]
    dur = r["duration_ms"]; mins = dur / 60000.0
    disc = r.get("stream_discontinuities") or []
    in_res = v.get("lost_packets_in_resyncs")
    has = "lost_packets_in_resyncs" in v
    # D-BASE-R1 reading rule
    lost = v["lost_packets"] if has else v["lost_packets"] + sum(
        x.get("jump_packets", 0) for x in disc)
    fge = v["forward_gap_events"]
    pac = (d.get("host") or {}).get("fec_pacing") or {}
    m = dict(
        label=label, report=name, pacing_us=pacing,
        arm=("on" if pacing > 0 else "off"),
        dur_s=dur / 1000.0, lost=lost, loss_min=lost / mins, fge=fge,
        pkts_per_gap=((lost - (in_res or 0)) / fge) if fge else None,
        max_fwd_gap=v["max_forward_gap_packets"], n_disc=len(disc),
        early_disc=len([x for x in disc if x.get("elapsed_ms", 10**9) < 30000]),
        max_gap_ms=dec["max_output_gap_ms"],
        spike20_min=dec["spike_20_ms"] / mins,
        max_rx2dec=dec["max_rx_to_decode_ms"],
        fps=dec["rendered_frames"] / (dur / 1000.0),
        pac_enabled=pac.get("enabled"), pac_cfg=pac.get("configured_us"),
        p50=pac.get("achieved_spacing_p50_us"), p99=pac.get("achieved_spacing_p99_us"),
        clamped=pac.get("clamped_frames"), late=pac.get("late_frames"),
        paced_frames=pac.get("paced_frames"),
        max_start_delay_us=pac.get("max_start_delay_us"),
        send_call_max_us=None,
    )
    f = f"{HERE}/relay_{label}.json"
    if os.path.exists(f):
        try:
            s = json.load(open(f))
            m["send_call_max_us"] = (
                s.get("native_stream", s).get("fec", {}).get("send_call_max_us"))
        except Exception:
            pass
    return m


rows = []
for line in open(IDX):
    label, pacing, name = line.split()
    rows.append(metrics(name, label, int(pacing)))

COLS = [("dur_s", "dur_s", "{:.1f}"), ("loss_min", "loss/min", "{:.1f}"),
        ("fge", "fwd_gaps", "{:.0f}"), ("pkts_per_gap", "pkt/gap", "{:.2f}"),
        ("max_fwd_gap", "maxgap_pk", "{:.0f}"), ("n_disc", "disc", "{:.0f}"),
        ("max_gap_ms", "maxout_ms", "{:.0f}"), ("spike20_min", "spk20/min", "{:.1f}"),
        ("max_rx2dec", "max_rx2dec", "{:.0f}"), ("fps", "fps", "{:.2f}"),
        ("p50", "space_p50", "{:.1f}"), ("p99", "space_p99", "{:.1f}"),
        ("send_call_max_us", "sendmax_us", "{:.1f}")]


def fmt(x, f, w):
    return ("-" if x is None else f.format(x)).rjust(w)


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


print("===== per session, in run order =====")
print("run       cfg" + "".join(h.rjust(11) for _, h, _ in COLS))
for m in rows:
    print(f"{m['label']:<10}{m['pacing_us']:<4}"
          + "".join(fmt(m[k], f, 11) for k, _, f in COLS))

rej = [m for m in rows if m["early_disc"]]
print()
print(f"Rejected (discontinuity in first 30 s): {len(rej)} of {len(rows)}"
      + ("" if not rej else ": " + ", ".join(m['label'] for m in rej))
      + ". None re-run was needed.")
print(f"Last session in run order: {rows[-1]['label']}, "
      f"pacing enabled={rows[-1]['pac_enabled']}, configured_us={rows[-1]['pac_cfg']}")


def block(title, prefix, on_pacing):
    sel = [m for m in rows if m["label"].startswith(prefix)]
    pairs = {}
    for m in sel:
        pairs.setdefault(m["label"][:2], {})[m["arm"]] = m
    pairs = {k: v for k, v in sorted(pairs.items()) if "off" in v and "on" in v}
    off = [m for m in sel if m["arm"] == "off"]
    on = [m for m in sel if m["arm"] == "on"]

    print()
    print(f"===== {title} =====")
    print(f"{'pair':<6}{'loss/min off':>14}{'on':>9}{'fall':>8}   "
          f"{'pkt/gap off':>13}{'on':>8}{'fall':>8}   "
          f"{'spk20 off':>11}{'on':>8}   {'rx2dec off':>12}{'on':>7}")
    lf = gf = sr = rr = 0
    for name, p in pairs.items():
        a, b = p["off"], p["on"]
        lr = a["loss_min"] / b["loss_min"] if b["loss_min"] else float("inf")
        gr = a["pkts_per_gap"] / b["pkts_per_gap"] if b["pkts_per_gap"] else float("inf")
        lf += b["loss_min"] < a["loss_min"]
        gf += b["pkts_per_gap"] < a["pkts_per_gap"]
        sr += b["spike20_min"] > a["spike20_min"]
        rr += b["max_rx2dec"] > a["max_rx2dec"]
        print(f"{name:<6}{a['loss_min']:>14.1f}{b['loss_min']:>9.1f}{lr:>7.2f}x   "
              f"{a['pkts_per_gap']:>13.2f}{b['pkts_per_gap']:>8.2f}{gr:>7.2f}x   "
              f"{a['spike20_min']:>11.1f}{b['spike20_min']:>8.1f}   "
              f"{a['max_rx2dec']:>12.0f}{b['max_rx2dec']:>7.0f}")
    n = len(pairs)
    print(f"  loss/min fell in    {lf} of {n} pairs")
    print(f"  pkt/gap  fell in    {gf} of {n} pairs")
    print(f"  spike20/min ROSE in {sr} of {n} pairs")
    print(f"  max_rx2dec ROSE in  {rr} of {n} pairs")
    print(f"  medians ({prefix}, off n={len(off)} / on n={len(on)} at {on_pacing} us):")
    for k, h, f in COLS:
        a, b = med([m[k] for m in off]), med([m[k] for m in on])
        line = f"    {h:<12} off {fmt(a,f,10)}   on {fmt(b,f,10)}"
        if a not in (None, 0) and b not in (None, 0):
            line += f"   ratio {a/b:>7.2f}x"
        print(line)
    for k, h, f in (("loss_min", "loss per minute", "{:.1f}"),
                    ("pkts_per_gap", "packets per gap", "{:.2f}"),
                    ("spike20_min", "spikes>=20ms/min", "{:.1f}"),
                    ("max_rx2dec", "max_rx_to_decode", "{:.0f}")):
        for arm, g in (("off", off), ("on", on)):
            vals = sorted(m[k] for m in g if m[k] is not None)
            print(f"    {h:<17} {arm:<4} " + ", ".join(f.format(x) for x in vals))
    return pairs


block("BLOCK A - PACING_US = 150, five pairs, strictly alternating from off", "P", 150)
block("BLOCK B - PACING_US = 400, scaling probe, two pairs", "S", 400)

print()
print("===== does the effect scale with PACING_US? =====")
a150 = [m for m in rows if m["pacing_us"] == 150]
a400 = [m for m in rows if m["pacing_us"] == 400]
alloff = [m for m in rows if m["pacing_us"] == 0]
print(f"{'arm':<10}{'n':>3}{'achieved p50':>14}{'achieved p99':>14}"
      f"{'clamped/frames':>17}{'late':>7}{'loss/min med':>14}{'pkt/gap med':>13}{'spk20 med':>11}")
for name, g in (("off", alloff), ("150 us", a150), ("400 us", a400)):
    pf = med([m["paced_frames"] for m in g]) or 0
    cl = med([m["clamped"] for m in g]) or 0
    print(f"{name:<10}{len(g):>3}{fmt(med([m['p50'] for m in g]),'{:.1f}',14)}"
          f"{fmt(med([m['p99'] for m in g]),'{:.1f}',14)}"
          f"{(f'{cl:.0f}/{pf:.0f}' if pf else '-'):>17}"
          f"{fmt(med([m['late'] for m in g]),'{:.0f}',7)}"
          f"{fmt(med([m['loss_min'] for m in g]),'{:.1f}',14)}"
          f"{fmt(med([m['pkts_per_gap'] for m in g]),'{:.2f}',13)}"
          f"{fmt(med([m['spike20_min'] for m in g]),'{:.1f}',11)}")

print()
print("===== pacing fidelity and cost, on-arm sessions =====")
for m in rows:
    if m["pacing_us"] <= 0:
        continue
    print(f"  {m['label']:<10} cfg={m['pac_cfg']:<4} p50={m['p50']:<7} p99={m['p99']:<7} "
          f"paced_frames={m['paced_frames']:<6} clamped={m['clamped']:<6} "
          f"late={m['late']:<5} max_start_delay_us={m['max_start_delay_us']}")
