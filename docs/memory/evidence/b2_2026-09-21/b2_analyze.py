#!/usr/bin/env python3
"""B2 analysis: the Opal-path arm against the PC-path reference arm.

Fields absent from a report are printed as '-' and excluded from medians;
they are never substituted with zero.
"""
import json, os, statistics as st

REPO = "/home/privyhub/Projects/onn-stream-test"
EV = os.path.join(REPO, "docs/memory/evidence")
SESS = os.path.join(REPO, "logs/games/decoder_sessions")
HERE = os.path.dirname(os.path.abspath(__file__))

P2A = sorted(n for n in os.listdir(f"{EV}/d_base_p2a_2026-09-21") if n.endswith(".json"))
REF = ([("A60", f"{EV}/d_base_p1_2026-09-20/native_decoder_20260920_224005_823.json"),
        ("B60", f"{EV}/d_base_p1_2026-09-20/native_decoder_20260920_224847_830.json"),
        ("C60", f"{EV}/d_base_p1_2026-09-20/native_decoder_20260920_225631_151.json")]
       + [(f"Q{i+1}", f"{EV}/d_base_p2a_2026-09-21/{n}") for i, n in enumerate(P2A)]
       + [("R1", f"{EV}/c5a_2026-09-21/native_decoder_20260921_010028_882.json"),
          ("R2", f"{EV}/c5a_2026-09-21/native_decoder_20260921_010755_679.json"),
          ("R3", f"{EV}/c5a_2026-09-21/native_decoder_20260921_011115_368.json")])

OPAL = []
for line in open(f"{HERE}/index.txt"):
    lab, mode, name = line.split()
    OPAL.append((lab, mode, os.path.join(SESS, name)))


def metrics(path):
    d = json.load(open(path))["report"]
    v, dec, aud = d["video"], d["decoder"], d["audio"]
    dur_ms = d["duration_ms"]; mins = dur_ms / 60000.0
    disc = [dict(x) for x in (d.get("stream_discontinuities") or [])]
    # the per-discontinuity IDR fields live in a parallel array
    for i, extra in enumerate(d.get("first_idr_after_discontinuity") or []):
        if i < len(disc):
            disc[i].update({k: v for k, v in extra.items() if k != "elapsed_ms"})
            disc[i]["idr_elapsed_ms"] = extra.get("elapsed_ms")
    has_field = "lost_packets_in_resyncs" in v
    in_resync = v.get("lost_packets_in_resyncs")
    # D-BASE-R1 reading rule
    lost = v["lost_packets"] if has_field else \
        v["lost_packets"] + sum(x.get("jump_packets", 0) for x in disc)
    fge = v["forward_gap_events"]
    non_resync = lost - (in_resync or 0)
    g = v.get
    return dict(
        dur_s=dur_ms / 1000.0, packets=v["packets"], lost=lost,
        in_resync=in_resync, has_field=has_field, loss_min=lost / mins, fge=fge,
        pkts_per_gap=(non_resync / fge) if fge else None,
        max_fwd_gap=v["max_forward_gap_packets"],
        late_reord=v["late_or_reordered_packets"],
        resyncs=v["sequence_resyncs"], ssrc=v["ssrc_changes"],
        largest_jump=v["largest_resync_jump_packets"],
        n_disc=len(disc), disc=disc,
        idr_rej=g("idr_aus_rejected_waiting_for_idr"),
        nonidr_drop=g("non_idr_aus_dropped_waiting_for_idr"),
        pkts_wait_idr=g("packets_dropped_waiting_for_idr"),
        resync_to_idr=g("resync_to_idr_ms"),
        max_resync_to_idr=g("max_resync_to_idr_ms"),
        first_clean_idr=g("first_clean_idr_ms"),
        gap_au_drops=g("sequence_gap_au_drops"), fec_unrec=g("fec_unrecoverable_groups"),
        max_gap_ms=dec["max_output_gap_ms"], spike20=dec["spike_20_ms"],
        spike20_min=dec["spike_20_ms"] / mins,
        fps=dec["rendered_frames"] / (dur_ms / 1000.0),
        stale_min=dec["stale_output_drops"] / mins,
        a_lost=aud["lost_packets"], a_under=aud["underruns"])


def med(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def fmt(x, f, w):
    return ("-" if x is None else f.format(x)).rjust(w)


COLS = [("dur_s", "dur_s", "{:.1f}"), ("lost", "lost", "{:.0f}"),
        ("in_resync", "lost_in_res", "{:.0f}"), ("loss_min", "loss/min", "{:.1f}"),
        ("fge", "fwd_gaps", "{:.0f}"), ("pkts_per_gap", "pkt/gap", "{:.2f}"),
        ("max_fwd_gap", "maxgap_pk", "{:.0f}"), ("late_reord", "late/reord", "{:.0f}"),
        ("n_disc", "disc", "{:.0f}"), ("max_gap_ms", "maxout_ms", "{:.0f}"),
        ("spike20_min", "spk20/min", "{:.1f}"), ("stale_min", "stale/min", "{:.1f}"),
        ("fps", "fps", "{:.2f}"), ("a_lost", "aud_lost", "{:.0f}"),
        ("a_under", "aud_under", "{:.0f}")]
C5A = [("resyncs", "resyncs"), ("ssrc", "ssrc_chg"), ("largest_jump", "max_jump_pk"),
       ("idr_rej", "idr_rejected"), ("nonidr_drop", "nonidr_dropped"),
       ("pkts_wait_idr", "pkts_wait_idr"), ("resync_to_idr", "resync_idr_ms"),
       ("max_resync_to_idr", "max_res_idr_ms"), ("first_clean_idr", "first_idr_ms"),
       ("gap_au_drops", "gap_au_drops"), ("fec_unrec", "fec_unrec")]

arms = {"PC path (reference)": [(l, metrics(p)) for l, p in REF],
        "Opal path (B2)": [(l, metrics(p)) for l, m, p in OPAL if m == "clean"]}
pulse = [(l, metrics(p)) for l, m, p in OPAL if m == "pulse"]


def table(name, rows):
    print(f"\n===== {name}  (n={len(rows)}) =====")
    print("run   " + "".join(h.rjust(11) for _, h, _ in COLS))
    for lab, m in rows:
        print(f"{lab:<6}" + "".join(fmt(m[k], f, 11) for k, _, f in COLS))
    if len(rows) > 1:
        print(f"{'MED':<6}" + "".join(
            fmt(med([m[k] for _, m in rows]), f, 11) for k, _, f in COLS))
    print("  C5a counters:")
    print("  run   " + "".join(h.rjust(15) for _, h in C5A))
    for lab, m in rows:
        print(f"  {lab:<6}" + "".join(fmt(m[k], "{:.0f}", 15) for k, _ in C5A))


for n, r in arms.items():
    table(n, r)
table("Opal PULSE  (single 3 s SIGSTOP/SIGCONT at 60 s)", pulse)

print("\n===== per-discontinuity rows (all sessions, both arms) =====")
hdr = (f"{'arm':<22}{'run':<6}{'elapsed_ms':>11}{'type':>18}{'jump_pk':>9}"
       f"{'res_idr_ms':>11}{'rej_idr':>9}{'drop_nonidr':>12}{'au_complete':>12}")
print(hdr)
any_d = False
for name, rows in list(arms.items()) + [("Opal PULSE", pulse)]:
    for lab, m in rows:
        for x in m["disc"]:
            any_d = True
            print(f"{name:<22}{lab:<6}{x.get('elapsed_ms','-'):>11}"
                  f"{x.get('type','-'):>18}{x.get('jump_packets','-'):>9}"
                  f"{x.get('resync_to_idr_ms','-'):>11}{x.get('rejected_idr_aus','-'):>9}"
                  f"{x.get('dropped_non_idr_aus','-'):>12}"
                  f"{str(x.get('au_complete','-')):>12}"
                  f"   idr_at={x.get('idr_elapsed_ms','-')}"
                  f" fec_unrec_grp={x.get('au_fec_unrecoverable_group','-')}")
if not any_d:
    print("  (none in any session of either arm)")

print("\n===== medians side by side =====")
ref, op = arms["PC path (reference)"], arms["Opal path (B2)"]
for k, h, f in COLS:
    if k == "dur_s":
        continue
    a, b = med([m[k] for _, m in ref]), med([m[k] for _, m in op])
    line = f"{h:<12} PC {fmt(a,f,10)}   Opal {fmt(b,f,10)}"
    if a not in (None, 0) and b not in (None, 0):
        line += f"   ratio {a/b:>7.2f}x"
    print(line)

print("\nfull per-session lists (the day-to-day swing is larger than most effects):")
for key, h, f in (("loss_min", "loss per minute", "{:.1f}"),
                  ("pkts_per_gap", "packets per gap event", "{:.2f}")):
    for name, rows in arms.items():
        vals = sorted(m[key] for _, m in rows if m[key] is not None)
        print(f"  {h:<22} {name:<22} " + ", ".join(f.format(x) for x in vals))
