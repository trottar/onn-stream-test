#!/usr/bin/env python3
"""LAN-R2: which host signal separates random loss from Sunday's bidirectional degradation? Read-only.

    python3 -I lan_r2_analysis.py   -> per_minute.md, signals.json, rule_search.md, rule_search.json

The per-report series is LAN-R1's (each live ladder `sample` joined to the nearest client heartbeat, lan_r1_series),
over LAN-R1's inputs (the evenings, the clean windows) plus BENCH-R1's own logs (`bench_r1_2026-10-22/logs_bench/`,
read only; cells 1-4 by their client-session spans), and the control-gap logs (`inputs/`, frozen copies of the live
`logs/games/native_stream_ctrl_gaps.log*`). Per evaluated report (2 s):
    unrec       FEC-unrecoverable groups (heartbeat delta; live: telemetry fec.unrecoverable_groups_delta)
    up_n / up_max   uplink silences >= 250 ms STARTING in (t - 2 s, t], and the longest (host's control-gap log)
    out_gap     the client's output gap (the sample's output_gap_ms; live: telemetry latency.output_gap_ms)
    audio_gap   the heartbeat's audio_max_arrival_gap_ms (the client's audio arrival gap in that 2-s window)
The rule's windows are LAN-R1's: K = 2 non-overlapping 5-evaluated-report windows, session age >= 60 s, base
`unrec >= 4 in both` (T 4 K 2). A second term is searched; it must hold in at least one of the two windows.
A two-signal AND can only fire where LAN-R1's rule fired, so the clean windows (0 there) stay 0 by construction.
"""
from __future__ import annotations

import bisect
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
sys.path.insert(0, str(EV / "lan_r1_2026-10-21"))
import lan_r1_series as L  # noqa: E402
import lan_r1_analysis as A  # noqa: E402

BENCH = EV / "bench_r1_2026-10-22"
CELLS = json.loads((BENCH / "record" / "record_read.json").read_text())["cells"]
CELL_SPANS = [(f"BENCH-R1 {k}", "cell", *CELLS[k]["session"]) for k in
              ("01_loss-1_plain", "02_loss-1_lan_rule", "03_loss-5_lan_rule", "04_burst-50x20_lan_rule")]
GAP_FILES = [HERE / "inputs" / "ctrl_gaps_archive.log.1", HERE / "inputs" / "ctrl_gaps_live.log"]


def ladder_rows() -> list[dict]:
    rows = {}
    for p in L.LADDER_FILES + [BENCH / "logs_bench" / "adaptive_bitrate_shadow.jsonl"]:
        for r in L.jl(p):
            if r.get("mode") == "live" and r.get("at_utc"):
                rows[(r["at_utc"], r.get("event"), r.get("session_elapsed_ms"))] = r
    return sorted(rows.values(), key=lambda r: r["at_utc"])


def heartbeats() -> list[tuple[float, int, dict, dict]]:
    """[(t, elapsed, deltas, raw)] as lan_r1_series.heartbeat_deltas, plus the raw row (audio_max_arrival_gap_ms)."""
    rows = {}
    for p in L.HEARTBEAT_FILES + [BENCH / "logs_bench" / "native_stream_heartbeat.log"]:
        for r in L.jl(p):
            if r.get("received_at_utc") and isinstance(r.get("elapsed_ms"), (int, float)):
                rows[(r["received_at_utc"], r["elapsed_ms"])] = r
    seq = sorted(rows.values(), key=lambda r: r["received_at_utc"])
    out, prev = [], None
    for r in seq:
        t = L.ts(r["received_at_utc"])
        if prev is not None and r["elapsed_ms"] > prev["elapsed_ms"] and t - L.ts(prev["received_at_utc"]) < 30:
            d = {}
            for k, src in L.HB_KEYS.items():
                a, b = r.get(src), prev.get(src)
                d[k] = (a - b) if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a >= b else None
            out.append((t, int(r["elapsed_ms"]), d, r))
        prev = r
    return out


def gaps() -> list[tuple[float, float]]:
    rows = {}
    for p in GAP_FILES:
        for r in L.jl(p):
            if r.get("start_utc") and r.get("end_utc"):
                rows[(r["start_utc"], r["end_utc"])] = (L.ts(r["start_utc"]), (L.ts(r["end_utc"]) - L.ts(r["start_utc"])) * 1000)
    return sorted(rows.values())


def series(span, lad, hb, gl) -> list[dict]:
    _, _, a, b = span
    ta, tb = L.ts(a), L.ts(b)
    hb_t = [x[0] for x in hb]
    g_t = [x[0] for x in gl]
    out = []
    for r in lad:
        if r.get("event") != "sample":
            continue
        t = L.ts(r["at_utc"])
        if not ta <= t < tb:
            continue
        el = r.get("session_elapsed_ms")
        d, raw = None, None
        if isinstance(el, (int, float)):
            i = bisect.bisect_left(hb_t, t)
            best = None
            for j in (i - 1, i, i + 1):
                if 0 <= j < len(hb):
                    th, he, dd, rr = hb[j]
                    if abs(th - t) <= 1.5 and abs(he - el) <= 1500 and (best is None or abs(th - t) < best[0]):
                        best = (abs(th - t), dd, rr)
            if best:
                d, raw = best[1], best[2]
        lo, hi = bisect.bisect_right(g_t, t - 2.0), bisect.bisect_right(g_t, t)
        ups = [m for _, m in gl[lo:hi] if m >= 250]
        out.append({"at_utc": r["at_utc"], "t": t, "elapsed_ms": el, "disposition": r.get("disposition"),
                    "fps": r.get("fps"), "lost": r.get("lost_packets_delta"), "out_gap": r.get("output_gap_ms"),
                    "unrec": (d or {}).get("unrec"), "audio_gap": (raw or {}).get("audio_max_arrival_gap_ms"),
                    "up_n": len(ups), "up_max": max(ups, default=0), "joined": d is not None})
    return out


def num(v):
    return v if isinstance(v, (int, float)) else 0


SECOND = {   # name -> (label, per-window predicate factory over thresholds)
    "up": ("uplink silences >= G ms in the window >= N", lambda G, N: (lambda W: sum(1 for x in W if x["up_max"] >= G) >= N)),
    "out": ("client output gap max in the window >= X ms", lambda X, _n: (lambda W: max(num(x["out_gap"]) for x in W) >= X)),
    "audio": ("audio arrival gap max in the window >= Y ms", lambda Y, _n: (lambda W: max(num(x["audio_gap"]) for x in W) >= Y)),
    "cluster": ("one report holds >= Z of the window's unrec", lambda Z, _n: (lambda W: max(num(x["unrec"]) for x in W) >= Z)),
}
GRID = {"up": [(G, N) for G in (250, 300, 400, 500, 600, 800) for N in (1, 2, 3)],
        "out": [(X, 0) for X in (150, 200, 250, 300, 400, 600, 1000)],
        "audio": [(Y, 0) for Y in (80, 100, 150, 200, 300, 500)],
        "cluster": [(Z, 0) for Z in (2, 3, 4, 6, 8)]}


def fires(ser, second=None, T=4, K=2) -> list[str]:
    out = []
    for sess in A.sessions_of(ser):
        win = []
        for x in sess:
            if x["disposition"] != "evaluated":
                continue
            win.append(x)
            if len(win) < 5 * K or not isinstance(x["elapsed_ms"], (int, float)) or x["elapsed_ms"] < 60_000:
                continue
            ws = [win[len(win) - 5 * (i + 1): len(win) - 5 * i] for i in range(K)]
            if all(sum(num(y["unrec"]) for y in W) >= T for W in ws) and (second is None or any(second(W) for W in ws)):
                out.append(x["at_utc"])
    return out


def per_minute(ser) -> dict[str, dict]:
    mins: dict[str, dict] = {}
    for x in ser:
        m = mins.setdefault(x["at_utc"][:16], {"reports": 0, "unrec": 0, "unrec_max_report": 0, "up_n": 0, "up_max": 0,
                                               "out_gap_max": 0, "audio_gap_max": 0, "lost": 0, "fps_min": None})
        m["reports"] += 1
        m["unrec"] += num(x["unrec"])
        m["unrec_max_report"] = max(m["unrec_max_report"], num(x["unrec"]))
        m["up_n"] += x["up_n"]
        m["up_max"] = max(m["up_max"], round(x["up_max"]))
        m["out_gap_max"] = max(m["out_gap_max"], num(x["out_gap"]))
        m["audio_gap_max"] = max(m["audio_gap_max"], num(x["audio_gap"]))
        m["lost"] += num(x["lost"])
        if isinstance(x["fps"], (int, float)):
            m["fps_min"] = x["fps"] if m["fps_min"] is None else min(m["fps_min"], x["fps"])
    return mins


def episodes(times):
    return A.episodes(times)


def main() -> int:
    lad, hb, gl = ladder_rows(), heartbeats(), gaps()
    spans = L.SPANS + CELL_SPANS
    ser = {sp[0]: series(sp, lad, hb, gl) for sp in spans}
    sun, r2 = ser[L.SPANS[0][0]], ser[L.SPANS[1][0]]
    r2_clean = {m for m, v in A.minutes_table(EV / "lan_r1_2026-10-21" / "inputs" / "ux_r2" / "timeline.json").items()
                if A.clean_minute(v)}
    r1_min = A.minutes_table(EV / "lan_r1_2026-10-21" / "inputs" / "ux_r1" / "timeline.json")
    r1_clean = {m for m, v in r1_min.items() if A.clean_minute(v)}
    cleans = [sp[0] for sp in L.SPANS[2:]]
    cells = [sp[0] for sp in CELL_SPANS]
    cov = {n: {"samples": len(s), "joined": sum(x["joined"] for x in s)} for n, s in ser.items()}

    # the per-minute table (the queue's ask): cells 1-4, Sunday's step / bad minutes, Sunday's and last night's clean
    pm = {n: per_minute(s) for n, s in ser.items()}
    sun_min = pm[L.SPANS[0][0]]
    r2_min = pm[L.SPANS[1][0]]

    def agg(name, minutes):
        ms = [m for m in minutes if m is not None]
        if not ms:
            return None
        n = len(ms)
        return {"name": name, "minutes": n,
                "unrec_per_min": round(sum(m["unrec"] for m in ms) / n, 2),
                "unrec_max_report": max(m["unrec_max_report"] for m in ms),
                "up_n_per_min": round(sum(m["up_n"] for m in ms) / n, 2),
                "minutes_with_up_ge_400": sum(1 for m in ms if m["up_max"] >= 400),
                "out_gap_max_median": sorted(m["out_gap_max"] for m in ms)[n // 2],
                "minutes_out_gap_ge_400": sum(1 for m in ms if m["out_gap_max"] >= 400),
                "audio_gap_max_median": sorted(m["audio_gap_max"] for m in ms)[n // 2],
                "minutes_audio_gap_ge_150": sum(1 for m in ms if m["audio_gap_max"] >= 150)}
    groups = [agg(c, list(pm[c].values())) for c in cells]
    groups.append(agg("Sunday step 04:56-05:05", [sun_min.get(f"2026-10-20T{m}") for m in A.STEP_MIN_SUNDAY]))
    groups.append(agg("Sunday bursts (05:06, 05:09-05:11, 05:20-05:21)",
                      [sun_min.get(f"2026-10-20T{m}") for m in ("05:06", "05:09", "05:10", "05:11", "05:20", "05:21")]))
    groups.append(agg("Sunday clean minutes (LAN-R1's definition)", [sun_min.get(f"2026-10-20T{m}") for m in sorted(r1_clean)]))
    groups.append(agg("Last night clean minutes", [r2_min.get(f"2026-10-21T{m}") for m in sorted(r2_clean)]))
    for c in cleans:
        groups.append(agg(c, list(pm[c].values())))
    groups = [g for g in groups if g]

    # the search: base T4 K2 AND one second term
    base_sun = fires(sun)
    res = []
    for key, (label, fac) in SECOND.items():
        for a, b in GRID[key]:
            pred = fac(a, b)
            row = {"signal": key, "label": label, "p1": a, "p2": b}
            row["cells"] = {c: episodes(fires(ser[c], pred)) for c in cells}
            row["clean_windows"] = sum(episodes(fires(ser[c], pred)) for c in cleans)
            r2f = fires(r2, pred)
            row["r2_clean_false_minutes"] = sorted({t[11:16] for t in r2f if t[11:16] in r2_clean})
            sf = fires(sun, pred)
            row["sunday_first"] = sf[0][11:19] if sf else None
            row["sunday_minutes"] = sorted({t[11:16] for t in sf})
            row["ok"] = (row["cells"][cells[0]] == 0 and row["cells"][cells[1]] == 0 and row["clean_windows"] == 0
                         and not row["r2_clean_false_minutes"] and row["sunday_first"] is not None
                         and row["sunday_first"] < "05:06:00")
            res.append(row)
    base = {"cells": {c: episodes(fires(ser[c])) for c in cells}, "clean_windows": sum(episodes(fires(ser[c])) for c in cleans),
            "sunday_first": base_sun[0][11:19] if base_sun else None}
    out = {"coverage": cov, "groups": groups, "base_T4K2": base, "search": res,
           "passing": [r for r in res if r["ok"]]}
    (HERE / "signals.json").write_text(json.dumps(out, indent=1) + "\n")

    md = ["# LAN-R2 — per-minute signals, random loss against Sunday (`lan_r2_analysis.py`)", "",
          "Per group of minutes (the means / medians of per-minute values). `up` = uplink silences >= 250 ms (the host's "
          "control-gap log); `out gap` = the client's output gap (ladder sample); `audio gap` = the client's audio "
          "arrival gap (heartbeat window); `unrec max/report` = the most FEC-unrecoverable groups in one 2-s report.", "",
          "| group | minutes | unrec / min | unrec max / report | up / min | min with up >= 400 | out gap max (median) | min out gap >= 400 | audio gap max (median) | min audio gap >= 150 |",
          "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for g in groups:
        md.append(f"| {g['name']} | {g['minutes']} | {g['unrec_per_min']} | {g['unrec_max_report']} | {g['up_n_per_min']} | "
                  f"{g['minutes_with_up_ge_400']} | {g['out_gap_max_median']} | {g['minutes_out_gap_ge_400']} | "
                  f"{g['audio_gap_max_median']} | {g['minutes_audio_gap_ge_150']} |")
    md += ["", "Coverage (samples / joined to a heartbeat): " + "; ".join(f"{k}: {v['samples']}/{v['joined']}" for k, v in cov.items())]
    (HERE / "per_minute.md").write_text("\n".join(md) + "\n")
    rs = ["# LAN-R2 — the rule search: LAN-R1's T 4 K 2 AND a second term (`lan_r2_analysis.py`)", "",
          f"Base (LAN-R1, one signal): cells 1-4 episodes {base['cells']}; clean windows {base['clean_windows']}; Sunday "
          f"first {base['sunday_first']}.", "",
          "| second term | p | cell 1 | cell 2 | cell 3 | cell 4 | clean windows | last night clean (false minutes) | Sunday first | Sunday minutes | passes |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- | --- |"]
    for r in res:
        cv = list(r["cells"].values())
        rs.append(f"| {r['label']} | {r['p1']}{'/' + str(r['p2']) if r['signal'] == 'up' else ''} | {cv[0]} | {cv[1]} | {cv[2]} | {cv[3]} | "
                  f"{r['clean_windows']} | {', '.join(r['r2_clean_false_minutes']) or '—'} | {r['sunday_first'] or '—'} | "
                  f"{', '.join(r['sunday_minutes'][:8]) or '—'} | {'**yes**' if r['ok'] else ''} |")
    (HERE / "rule_search.md").write_text("\n".join(rs) + "\n")
    (HERE / "rule_search.json").write_text(json.dumps({"base": base, "search": res}, indent=1) + "\n")
    print("\n".join(md)); print(); print("\n".join(rs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
