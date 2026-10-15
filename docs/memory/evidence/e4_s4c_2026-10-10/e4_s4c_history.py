#!/usr/bin/env python3
"""E4-S4C -- the link history (pre-registration §7), read-only over link_watch.jsonl, ping.jsonl and deferral.json.
-> link_history.md, link_history.json. Hours and days are US Eastern (the probe's start). Spearman's rho across probes
(no-play probes excluded), stated as seen, not as cause."""
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ET = ZoneInfo("America/New_York")


def jl(p):
    out = []
    if os.path.exists(p):
        for l in open(p, errors="replace"):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def g(r, *p):
    for x in p:
        r = r.get(x) if isinstance(r, dict) else None
    return r


def rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for t in range(i, j + 1):
            r[order[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 5:
        return None, len(pairs)
    ra, rb = rank([p[0] for p in pairs]), rank([p[1] for p in pairs])
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = (sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb)) ** 0.5
    return (round(num / den, 3) if den else None), len(pairs)


def f(v, n=1):
    return "—" if v is None else (f"{v:.{n}f}" if isinstance(v, float) else str(v))


def main():
    P = jl(os.path.join(HERE, "link_watch.jsonl"))
    ping = [r for r in jl(os.path.join(HERE, "ping.jsonl")) if "bin_utc" in r]
    d = json.load(open(os.path.join(HERE, "deferral.json"))) if os.path.exists(os.path.join(HERE, "deferral.json")) else {}
    ok = [r for r in P if not r.get("no_play")]
    md = ["# E4-S4C — the link history", "",
          f"{len(P)} probes ({len(ok)} played, {sum(1 for r in P if r.get('no_play'))} no_play), "
          f"{sum(1 for r in ok if r['clean'])} clean; ping bins {len(ping)}. Times US Eastern.", "",
          "## Every probe, in time order", "",
          "| # | start (ET) | loss/min | rendered | resyncs | stale/min | pauses | client RSSI | station signal | retries % | air util % | ping loss % (40 min) | RTT med / p99 ms | clean |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in P:
        pb = r.get("ping_40min_before") or {}
        md.append(f"| {r['probe']} | {r['start_et'][5:16].replace('T', ' ')} {r['weekday_et']} | "
                  + ("no_play | | | | | | | | | | | |" if r.get("no_play") else
                     f"{f(r['loss_per_min'])} | {f(r['rendered_fps'], 2)} | {r['resyncs']} | {f(r.get('stale_per_min'), 2)} | "
                     f"{r.get('client_pauses')} | {f(g(r, 'client', 'rssi_median'), 0)} | {f(g(r, 'air', 'client_station', 'signal_dbm_median'), 0)} | "
                     f"{f(g(r, 'air', 'client_station', 'retry_pct'), 1)} | {f(g(r, 'air', 'utilization_mean_pct'), 2)} | "
                     f"{f(pb.get('loss_pct'), 2)} | {f(pb.get('rtt_median'), 1)} / {f(pb.get('rtt_p99'), 1)} | {'**yes**' if r['clean'] else 'no'} |"))
    # by hour-of-day and by day
    out = {"probes": len(P), "played": len(ok), "clean": sum(1 for r in ok if r["clean"])}
    for key, label in (("hour_et", "hour-of-day (ET)"), ("day_et", "day (ET)")):
        grp = defaultdict(list)
        for r in ok:
            grp[r[key]].append(r)
        tab = {}
        md += ["", f"## Loss by {label}", "", f"| {label} | probes | clean | loss median | min | max | rendered median |", "| --- | --- | --- | --- | --- | --- | --- |"]
        for h in sorted(grp):
            L = [r["loss_per_min"] for r in grp[h]]
            tab[str(h)] = {"n": len(L), "clean": sum(1 for r in grp[h] if r["clean"]), "median": statistics.median(L), "min": min(L), "max": max(L),
                           "rendered_median": statistics.median([r["rendered_fps"] for r in grp[h]])}
            t = tab[str(h)]
            md.append(f"| {h} | {t['n']} | {t['clean']} | {f(t['median'])} | {f(t['min'])} | {f(t['max'])} | {f(t['rendered_median'], 2)} |")
        out["by_" + key] = tab
    # the clean windows: runs of consecutive clean probes
    wins, cur = [], None
    for r in P:
        if r.get("clean"):
            if cur is None:
                cur = {"first_probe": r["probe"], "start_et": r["start_et"], "probes": 0}
            cur["probes"] += 1
            cur["last_probe"], cur["last_start_et"] = r["probe"], r["start_et"]
        elif cur:
            wins.append(cur)
            cur = None
    if cur:
        wins.append(cur)
    ran = []
    for c in d.get("controls") or []:
        ran.append(("control", c.get("start_utc"), c.get("probe")))
    for sl, att in (d.get("slots") or {}).items():
        for a in att:
            ran.append((sl, a.get("start_utc"), None))
    md += ["", "## Clean windows (consecutive clean probes)", "", "| from (ET) | to (ET, last clean probe's start) | clean probes | what ran in it |", "| --- | --- | --- | --- |"]
    for w in wins:
        what = [x[0] for x in ran if x[2] is not None and w["first_probe"] <= x[2] <= w["last_probe"]]
        md.append(f"| {w['start_et'][5:16]} | {w['last_start_et'][5:16]} | {w['probes']} | {', '.join(what) or 'probes only'} |")
    out["clean_windows"] = wins
    # ping loss by hour (ET), all bins and idle-only bins
    ph = defaultdict(lambda: [0, 0, 0, 0, []])
    for b in ping:
        h = datetime.strptime(b["bin_utc"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).astimezone(ET).hour
        x = ph[h]
        x[0] += b["sent"]
        x[1] += b["lost"]
        if b.get("running") == ["idle"]:
            x[2] += b["sent"]
            x[3] += b["lost"]
        if b.get("rtt_median") is not None:
            x[4].append(b["rtt_median"])
    md += ["", "## Ping by hour-of-day (ET)", "", "| hour | echoes | loss % (all) | loss % (idle bins) | RTT median of bin medians ms |", "| --- | --- | --- | --- | --- |"]
    out["ping_by_hour"] = {}
    for h in sorted(ph):
        s, l, si, li, rt = ph[h]
        e = {"sent": s, "loss_pct": round(100 * l / s, 3) if s else None, "idle_loss_pct": round(100 * li / si, 3) if si else None,
             "rtt_median": round(statistics.median(rt), 2) if rt else None}
        out["ping_by_hour"][h] = e
        md.append(f"| {h} | {s} | {f(e['loss_pct'], 3)} | {f(e['idle_loss_pct'], 3)} | {f(e['rtt_median'], 2)} |")
    # what moves with the loss
    loss = [r["loss_per_min"] for r in ok]
    cand = {"air utilisation (Opal, mean %)": [g(r, "air", "utilization_mean_pct") for r in ok],
            "station signal (Opal, dBm)": [g(r, "air", "client_station", "signal_dbm_median") for r in ok],
            "station tx retries (%)": [g(r, "air", "client_station", "retry_pct") for r in ok],
            "station tx bitrate (Mbps)": [g(r, "air", "client_station", "tx_bitrate_mbps_median") for r in ok],
            "Opal stations (count)": [g(r, "air", "stations_median") for r in ok],
            "client RSSI (dBm)": [g(r, "client", "rssi_median") for r in ok],
            "client Tx link (Mbps)": [g(r, "client", "tx_link_mbps_median") for r in ok],
            "ping loss, 40 min before (%)": [g(r, "ping_40min_before", "loss_pct") for r in ok],
            "ping RTT p99, 40 min before (ms)": [g(r, "ping_40min_before", "rtt_p99") for r in ok],
            "hour of day (ET, linear)": [r["hour_et"] for r in ok],
            "client pauses": [r.get("client_pauses") for r in ok],
            "client cpu-thermal (C)": [g(r, "client_thermal", "cpu_thermal_c") for r in ok],
            "host CPU (%)": [r.get("host_cpu") for r in ok]}
    md += ["", "## What moves with the loss (Spearman across played probes; as seen, not cause)", "", "| reading | rho | n |", "| --- | --- | --- |"]
    out["spearman_vs_loss"] = {}
    for name, xs in cand.items():
        rho, n = spearman(loss, xs)
        out["spearman_vs_loss"][name] = {"rho": rho, "n": n}
        md.append(f"| {name} | {f(rho, 3)} | {n} |")
    json.dump(out, open(os.path.join(HERE, "link_history.json"), "w"), indent=1, default=str)
    open(os.path.join(HERE, "link_history.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({x: out[x] for x in ("probes", "played", "clean")}), len(wins), "clean windows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
