#!/usr/bin/env python3
"""LINK-L2 -- the air view tabled: this day's snapshots (40 MHz) beside LINK-L1's (80 MHz), counts only,
and the 30 s loop per hold (utilization, the onn's signal and the Opal's reported tx rate / MCS, retries).
Read-only. `link_l2_air_table.py` -> prints; writes air_table.txt."""
import json, os, statistics
HERE = os.path.dirname(os.path.abspath(__file__))
L1 = os.path.join(HERE, "..", "link_l1_2026-10-01")


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


def med(a):
    a = [x for x in a if x is not None]
    return statistics.median(a) if a else None


F = lambda x, s="": "-" if x is None else format(x, s)  # noqa: E731
out = []
for tag, path in (("LINK-L1 (80 MHz)", os.path.join(L1, "air.jsonl")), ("access check", os.path.join(HERE, "access_check.jsonl")),
                  ("LINK-L2 (40 MHz)", os.path.join(HERE, "air.jsonl"))):
    out += [f"== {tag} snapshots", f"{'label':<16} {'local':<17} {'ch':>3} {'wid':>3} {'util':>5} {'noise':>5} {'sig':>4} {'rate':>5} {'mcs':>3} "
            f"{'5g':>3} {'p36':>3} {'80blk(>=-70)':>12} {'36-40(>=-70)':>12} {'44-48(>=-70)':>12} {'52-64':>5} {'oth5':>4} {'2g':>3} {'2gch':>4} {'+/-':>6}"]
    for r in jl(path):
        n = r.get("neighbours") or {}
        if r.get("error"):
            out.append(f"{r['label']:<16} {r.get('local', ''):<17} ERROR {r['error']}")
            continue
        ad = "" if n.get("added_since_previous") is None else f"+{n['added_since_previous']}/-{n['removed_since_previous']}"
        p40 = lambda k: "-" if k not in n else f"{n[k]} ({n.get(k + '_signal_ge_-70', '-')})"  # noqa: E731
        out.append(f"{r['label']:<16} {r.get('local', ''):<17} {F(r.get('channel')):>3} {F(r.get('width_mhz')):>3} "
                   f"{F(r.get('channel_utilization_pct')):>5} {F(r.get('noise_dbm')):>5} {F(r.get('signal_dbm')):>4} "
                   f"{F(r.get('tx_bitrate_mbps')):>5} {F(r.get('tx_mcs')):>3} {F(n.get('band_5g')):>3} {F(n.get('5g_same_primary')):>3} "
                   f"{str(n.get('5g_in_use_80mhz_block', '-')) + ' (' + str(n.get('5g_in_block_signal_ge_-70', '-')) + ')':>12} "
                   f"{p40('5g_in_use_40mhz_pair'):>12} {p40('5g_pair_44_48'):>12} {F(n.get('5g_block_52_64', n.get('5g_adjacent_blocks'))):>5} "
                   f"{F(n.get('5g_other_5g')):>4} {F(n.get('band_2g')):>3} {F(n.get('2g_same_channel')):>4} {ad:>6}")
    out.append("")
out += ["== the 30 s loop per hold (medians; util mean / max)",
        f"{'day':<3} {'hold':<4} {'n':>3} {'util mean':>9} {'max':>5} {'sig':>4} {'tx rate':>7} {'tx mcs':>6} {'rx rate':>7} {'rx mcs':>6} {'tx retries':>10} {'tx failed':>9}"]
for tag, path in (("L1", os.path.join(L1, "air_loop.jsonl")), ("L2", os.path.join(HERE, "air_loop.jsonl"))):
    rows = [r for r in jl(path) if not r.get("error")]
    for h in sorted({r["label"] for r in rows}):
        w = [r for r in rows if r["label"] == h]
        u = [r.get("channel_utilization_pct") for r in w if r.get("channel_utilization_pct") is not None]
        o = [r for r in w if r.get("onn_row_found")]
        tr = [r.get("tx_retries") for r in o if r.get("tx_retries") is not None]
        tf = [r.get("tx_failed") for r in o if r.get("tx_failed") is not None]
        out.append(f"{tag:<3} {h:<4} {len(w):>3} {F(sum(u) / len(u) if u else None, '.2f'):>9} {F(max(u) if u else None):>5} "
                   f"{F(med([r.get('signal_dbm') for r in o])):>4} {F(med([r.get('tx_bitrate_mbps') for r in o])):>7} "
                   f"{F(med([r.get('tx_mcs') for r in o])):>6} {F(med([r.get('rx_bitrate_mbps') for r in o])):>7} "
                   f"{F(med([r.get('rx_mcs') for r in o])):>6} {F(tr[-1] - tr[0] if len(tr) > 1 else None, ','):>10} "
                   f"{F(tf[-1] - tf[0] if len(tf) > 1 else None, ','):>9}")
text = "\n".join(out) + "\n"
print(text)
open(os.path.join(HERE, "air_table.txt"), "w").write(text)
