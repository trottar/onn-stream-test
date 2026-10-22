#!/usr/bin/env python3
"""LAN-R1 §1.3 and §2's threshold search, from inputs/ only.

    python3 -B lan_r1_analysis.py   -> what_live_saw.md, threshold_search.md, threshold_search.json

§1.3 -- per bad minute, what the adopted controller read and why none of its decrease bars was met. The bars
(adaptive_bitrate.py / adaptive_bitrate_live.py), over the last 5 EVALUATED reports:
    FALLBACK queue/gap  fps < 50 on all 5 AND (queue >= 2 on >= 3 OR gap > 250 ms on >= 2)
    capacity            fps < 50 on all 5 AND lost >= 50 on >= 3
    capacity_mild       fps < 57 on >= 4  AND lost >= 50 on >= 3      (ROUTINE, one rung down)
    ROUTINE queue/gap   fps < 57 on >= 4  AND queue >= 1 on >= 3
Every bar needs the fps term. Loss alone never meets one.

§2 -- the search. Metric per 5-evaluated-report window (10 s): the post-FEC loss the ladder reads
(`lost_packets_delta`), or the FEC-unrecoverable groups (heartbeat; live the telemetry's
fec.unrecoverable_groups_delta). Fires when the newest K non-overlapping windows each reach T, session age
>= 60 s. Windows run over each client session's evaluated reports (as the ladder's), cleared at a session reset.

Clean windows (must not fire): CL-B5 A/B/L, CL-B6 1/2, CL-B7's three arms, G4-S3 (remote; it has no LAN part),
and last night's clean minutes. A clean minute of last night is defined here, before the search, from the
UX-R2 per-minute table: hb_s >= 50, fps >= 59.5, resync 0, underruns <= 10, ctrl gaps > 1 s 0.
UX-R3 (the user's two "deaths" in Zelda) has not landed: a firing in a minute this definition calls clean is
counted as a false trigger, and flagged as possibly one of the deaths.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lan_r1_series as L  # noqa: E402

BAD_MIN_SUNDAY = ["04:31", "04:35", "05:06", "05:09", "05:10", "05:11", "05:20", "05:21"]
STEP_MIN_SUNDAY = ["04:56", "04:57", "04:58", "04:59", "05:00", "05:01", "05:02", "05:03", "05:04", "05:05"]
CHOSEN = ("unrec", 4, 2)   # chosen after the search, below; see the record §2
T_GRID = {"lost": [5, 10, 15, 20, 25, 30, 40, 50, 75, 100, 150, 200, 300], "unrec": [1, 2, 3, 4, 5, 6, 8, 10, 15, 20]}
K_GRID = list(range(1, 13))


def minutes_table(path: Path) -> dict[str, dict]:
    return {m["utc"]: m for m in json.loads(path.read_text())["minutes"]}


def clean_minute(m: dict) -> bool:
    return (m.get("hb_s", 0) >= 50 and (m.get("fps") or 0) >= 59.5 and m.get("resync", 0) == 0
            and m.get("underruns", 99) <= 10 and m.get("ctrl_gt1s", 0) == 0)


def sessions_of(series: list[dict]) -> list[list[dict]]:
    out, cur, last = [], [], None
    for x in series:
        el = x["elapsed_ms"]
        if last is not None and isinstance(el, (int, float)) and el < last:
            out.append(cur)
            cur = []
        cur.append(x)
        last = el if isinstance(el, (int, float)) else last
    if cur:
        out.append(cur)
    return out


def what_live_saw(sun: list[dict]) -> list[str]:
    lines = ["# §1.3 What `live` saw in Sunday's bad minutes (UX-R1, 2026-10-20), and why no bar was met", "",
             "Per minute, over every 5-evaluated-report window ending in it: the most reports meeting each term "
             "(max over the minute's windows), and the windows meeting each whole bar. The heartbeat column is the "
             "nearest-heartbeat join (lan_r1_series); where the two sends are offset it can split a burst across "
             "minutes differently from the ladder's own column, which is what the controller read.", "",
             "| minute (UTC) | reports (evaluated) | loss: ladder sum / nearest-heartbeat sum (in resyncs) | unrec | fps min / mean | "
             "max fps<57 of 5 | max fps<50 of 5 | max lost>=50 of 5 | max queue>=1 of 5 | max gap>250 of 5 | "
             "windows meeting capacity_mild / capacity / FALLBACK q-g / ROUTINE q-g | recorded states (reason) | why none acted |",
             "| --- | ---: | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |"]
    for sess in sessions_of(sun):
        win: list[dict] = []
        for x in sess:
            if x["disposition"] == "evaluated":
                win = (win + [x])[-5:]
            x["_win"] = list(win) if len(win) == 5 else None
    for minute in STEP_MIN_SUNDAY + BAD_MIN_SUNDAY:
        xs = [x for x in sun if x["at_utc"][11:16] == minute]
        if not xs:
            continue
        ev = [x for x in xs if x["disposition"] == "evaluated"]
        wins = [x["_win"] for x in xs if x.get("_win")]
        def mx(f):
            return max((sum(1 for w in W if f(w)) for W in wins), default=0)
        fps = [x["fps"] for x in xs if isinstance(x["fps"], (int, float))]
        f57 = lambda w: isinstance(w["fps"], (int, float)) and w["fps"] < 57
        f50 = lambda w: isinstance(w["fps"], (int, float)) and w["fps"] < 50
        l50 = lambda w: isinstance(w["lost"], (int, float)) and w["lost"] >= 50
        q1 = lambda w: isinstance(w["queue"], (int, float)) and w["queue"] >= 1
        q2 = lambda w: isinstance(w["queue"], (int, float)) and w["queue"] >= 2
        g250 = lambda w: isinstance(w["gap"], (int, float)) and w["gap"] > 250
        cm = sum(1 for W in wins if sum(map(f57, W)) >= 4 and sum(map(l50, W)) >= 3)
        cap = sum(1 for W in wins if sum(map(f50, W)) == 5 and sum(map(l50, W)) >= 3)
        fb = sum(1 for W in wins if sum(map(f50, W)) == 5 and (sum(map(q2, W)) >= 3 or sum(map(g250, W)) >= 2))
        rq = sum(1 for W in wins if sum(map(f57, W)) >= 4 and sum(map(q1, W)) >= 3)
        states = collections.Counter(f"{x['state']}({x['reason']})" for x in xs)
        disp = collections.Counter(x["disposition"] for x in xs)
        lost = sum(x["lost"] or 0 for x in xs)
        hbl = sum(x["hb_lost"] or 0 for x in xs)
        rsl = sum(x["hb_resync_lost"] or 0 for x in xs)
        un = sum(x["unrec"] or 0 for x in xs)
        why = []
        if cm or cap or fb or rq:
            why.append("a bar WAS met (see the recorded decision)")
        else:
            if mx(l50) >= 3 and mx(f57) < 4:
                why.append(f"loss >= 50 on >= 3 of 5 met, but fps < 57 on at most {mx(f57)} of 5")
            elif mx(l50) < 3:
                why.append(f"loss >= 50 on at most {mx(l50)} of 5 (the loss came in few reports)")
            if mx(f57) >= 4 and mx(l50) < 3:
                why.append("fps < 57 on >= 4 but the loss term not met in the same window")
            if mx(f57) >= 4 and mx(l50) >= 3:
                why.append("fps < 57 on >= 4 and lost >= 50 on >= 3 both reached, never in the same 5-report window")
            if disp.get("resync") or disp.get("blackout"):
                why.append(f"{disp.get('resync', 0)} resync / {disp.get('blackout', 0)} blackout reports are not evidence")
        lines.append(f"| {minute} | {len(xs)} ({len(ev)}) | {lost} / {hbl} ({rsl}) | {un} | "
                     f"{min(fps) if fps else '—':.1f} / {sum(fps) / len(fps) if fps else 0:.1f} | {mx(f57)} | {mx(f50)} | "
                     f"{mx(l50)} | {mx(q1)} | {mx(g250)} | {cm} / {cap} / {fb} / {rq} | "
                     f"{'; '.join(f'{k} {v}' for k, v in states.most_common(3))} | {'; '.join(why) or '—'} |")
    return lines


def fires(series: list[dict], metric: str, T: float, K: int) -> list[str]:
    """at_utc of every evaluated report at which the rule's condition holds (session age >= 60 s)."""
    out = []
    for sess in sessions_of(series):
        vals = []
        for x in sess:
            if x["disposition"] != "evaluated":
                continue
            v = x[metric]
            vals.append(v if isinstance(v, (int, float)) else 0)
            if len(vals) < 5 * K or not isinstance(x["elapsed_ms"], (int, float)) or x["elapsed_ms"] < 60_000:
                continue
            ws = [sum(vals[len(vals) - 5 * (i + 1): len(vals) - 5 * i]) for i in range(K)]
            if all(w >= T for w in ws):
                out.append(x["at_utc"])
    return out


def episodes(times: list[str]) -> int:
    n, last = 0, None
    for t in times:
        tt = L.ts(t)
        if last is None or tt - last > 3:
            n += 1
        last = tt
    return n


def main() -> int:
    rows, hb = L.ladder_rows(), L.heartbeat_deltas()
    ser = {sp[0]: L.series(sp, rows, hb) for sp in L.SPANS}
    sun, r2 = ser[L.SPANS[0][0]], ser[L.SPANS[1][0]]
    (HERE / "what_live_saw.md").write_text("\n".join(what_live_saw(sun)) + "\n")

    r2min = minutes_table(HERE / "inputs" / "ux_r2" / "timeline.json")
    r1min = minutes_table(HERE / "inputs" / "ux_r1" / "timeline.json")
    r2_clean = {m for m, v in r2min.items() if clean_minute(v)}
    clean_spans = [sp[0] for sp in L.SPANS[2:]]
    # the per-window distributions
    dist = {}
    for name, s in ser.items():
        for metric in ("lost", "unrec"):
            ws = []
            for sess in sessions_of(s):
                vals = [x[metric] or 0 for x in sess if x["disposition"] == "evaluated"]
                ws += [sum(vals[i:i + 5]) for i in range(0, len(vals) - 4, 5)]
            ws.sort()
            dist[f"{name} / {metric}"] = {"windows": len(ws), "max": ws[-1] if ws else None,
                                          "p99": ws[int(0.99 * (len(ws) - 1))] if ws else None,
                                          "p90": ws[int(0.9 * (len(ws) - 1))] if ws else None,
                                          "median": ws[len(ws) // 2] if ws else None}
    results = []
    for metric, Ts in T_GRID.items():
        for T in Ts:
            for K in K_GRID:
                fp = {n: episodes(fires(ser[n], metric, T, K)) for n in clean_spans}
                r2f = fires(r2, metric, T, K)
                r2_false = sorted({t[11:16] for t in r2f if t[11:16] in r2_clean})
                sf = fires(sun, metric, T, K)
                results.append({"metric": metric, "T": T, "K": K, "clean_false": fp,
                                "clean_false_total": sum(fp.values()) + len(r2_false),
                                "r2_fire_minutes": sorted({t[11:16] for t in r2f}), "r2_false_minutes": r2_false,
                                "sunday_first": sf[0] if sf else None,
                                "sunday_fire_minutes": sorted({t[11:16] for t in sf}),
                                "sunday_before_0506": any(t[11:19] < "05:06:00" and t[11:16] >= "04:51" for t in sf)})
    zero = [r for r in results if r["clean_false_total"] == 0 and r["sunday_first"]]
    zero.sort(key=lambda r: (r["sunday_first"], -r["T"], r["K"]))
    lines = ["# §2 The threshold search (T per 10-s window of 5 evaluated reports; K consecutive windows)", "",
             f"Clean minutes of last night by the stated definition: {len(r2_clean)} of {len(r2min)} "
             f"({', '.join(sorted(r2_clean))}).", "",
             "## Per-window distributions (sum over 5 evaluated reports)", "",
             "| span | metric | windows | median | p90 | p99 | max |", "| --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for k, v in dist.items():
        n, m = k.rsplit(" / ", 1)
        lines.append(f"| {n} | {m} | {v['windows']} | {v['median']} | {v['p90']} | {v['p99']} | {v['max']} |")
    lines += ["", "## Does any (T, K) fire on Sunday before 05:06 with 0 false triggers?", ""]
    pre = [r for r in zero if r["sunday_before_0506"]]
    lines.append(f"- (T, K) pairs with 0 false triggers in every clean window and a Sunday firing: {len(zero)}")
    lines.append(f"- of those, firing on Sunday between 04:51 and 05:06:00: **{len(pre)}**")
    for metric in ("lost", "unrec"):
        any_pre = [r for r in results if r["metric"] == metric and r["sunday_before_0506"]]
        if any_pre:
            best = min(any_pre, key=lambda r: r["clean_false_total"])
            lines.append(f"- {metric}: the pre-05:06 firing with the fewest false triggers is T {best['T']} K {best['K']} "
                         f"(first {best['sunday_first']}): {best['clean_false_total']} false triggers "
                         f"({ {k: v for k, v in best['clean_false'].items() if v} }, last night's clean minutes "
                         f"{best['r2_false_minutes']})")
    lines += ["", "## The zero-false-trigger pairs, earliest Sunday firing first (top 25)", "",
              "| metric | T | K | Sunday first fire | Sunday fire minutes | last night fire minutes (none clean) |",
              "| --- | ---: | ---: | --- | --- | --- |"]
    for r in zero[:25]:
        lines.append(f"| {r['metric']} | {r['T']} | {r['K']} | {r['sunday_first']} | {', '.join(r['sunday_fire_minutes'])} | "
                     f"{', '.join(r['r2_fire_minutes']) or '—'} |")
    lines += ["", f"## The false-trigger table at the chosen pair ({CHOSEN[0]} T {CHOSEN[1]} K {CHOSEN[2]}) and its neighbours",
              "", "Firing episodes per window (0 required); last night: the clean minutes it fired in.", ""]
    neigh = [(CHOSEN[0], t, k) for t in (CHOSEN[1] - 1, CHOSEN[1], CHOSEN[1] + 1) for k in (CHOSEN[2] - 1, CHOSEN[2], CHOSEN[2] + 1)]
    idx = {(r["metric"], r["T"], r["K"]): r for r in results}
    hdr = [f"{m} T{t} K{k}" for m, t, k in neigh if (m, t, k) in idx]
    lines.append("| window | " + " | ".join(hdr) + " |")
    lines.append("| --- | " + " | ".join("---:" for _ in hdr) + " |")
    for n in clean_spans:
        lines.append(f"| {n} | " + " | ".join(str(idx[x]["clean_false"][n]) for x in neigh if x in idx) + " |")
    lines.append("| last night's clean minutes | " + " | ".join(", ".join(idx[x]["r2_false_minutes"]) or "0"
                                                              for x in neigh if x in idx) + " |")
    lines.append("| Sunday: first fire | " + " | ".join((idx[x]["sunday_first"] or "—")[11:19] for x in neigh if x in idx) + " |")
    lines += ["", "## G8-S1's shim cells (7000 start), under the chosen pair; the recorded rung path from the record", "",
              "| cell | evaluated reports | post-FEC lost / unrec (sum) | fires (first; minutes) |", "| --- | ---: | --- | --- |"]
    for sp in L.G8_SPANS:
        g = L.series(sp, rows, hb)
        f = fires(g, *CHOSEN)
        lines.append(f"| {sp[0]} | {sum(1 for x in g if x['disposition'] == 'evaluated')} | "
                     f"{sum(x['lost'] or 0 for x in g)} / {sum(x['unrec'] or 0 for x in g)} "
                     f"(joined {sum(x['joined'] for x in g)}/{len(g)}) | "
                     f"{(f[0][11:19] + '; ' + ', '.join(sorted({t[11:16] for t in f}))) if f else 'none'} |")
    (HERE / "threshold_search.md").write_text("\n".join(lines) + "\n")
    (HERE / "threshold_search.json").write_text(json.dumps({"results": results, "distributions": dist,
                                                            "r2_clean_minutes": sorted(r2_clean)}, indent=1) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
