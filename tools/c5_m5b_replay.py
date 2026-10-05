#!/usr/bin/env python3
"""C5-M5B sections 1-2: the rung's entry threshold and loss leave, replayed. Read-only; offline.

    python3 tools/c5_m5b_replay.py [out_dir]                -> c5_m5b_replays.txt / .json
    python3 tools/c5_m5b_replay.py --stop-rule [out_dir]    -> c5_m5b_stop_rule.txt (after the build)

Pre-registered in docs/memory/evidence/c5_m5b_2026-10-03/c5_m5b_preregistration.txt (sections 1
and 2: the candidate grids, the strictness order, the selection rules, the clock of the bounds).
Extends tools/c5_m5_replay.py (its series loaders, its LEAVE_SET / ENTRY_SET and its stop rule are
imported, not copied).

ENTRY: E405..E435 (>= k of 450) and E300 (>= 280 of 300), the policy with the rung flag from the
session's start, the existing leave triggers after an entry. Candidates are applied by setting the
live module's RUNG_WINDOW_REPORTS / RUNG_CLEAN_NEEDED before the policy is built (the policy reads
them at construction and per report), and restored after.

LEAVE: L-A..L-D as a subclass of the live policy (the module is not changed before the
selection): rung-only, over the evaluated reports at the rung since the last SSRC change; named
only when no existing trigger named a class; class ROUTINE, one rung down (12600 -> 7000), through
every gate of the existing path (the mild bar's one-rung-down target computation is reused, the
trigger then renamed rung_loss in the emitted rows).
"""

from __future__ import annotations

import json
import sys
from collections import deque
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import c5_m5_replay as m5  # noqa: E402

EVID = REPO / "docs" / "memory" / "evidence"
M5 = EVID / "c5_m5_2026-10-03"
GUARDS = m5.GUARDS

ENTRY_CANDIDATES = [  # strictest first (the pre-registered order)
    ("E435", 450, 435), ("E430", 450, 430), ("E425", 450, 425), ("E420", 450, 420),
    ("E300", 300, 280), ("E415", 450, 415), ("E410", 450, 410), ("E405", 450, 405),
]
REAL_TEN = [
    ("C3-L4-N1 silent live hold", EVID / "c3_l4_n1_2026-09-29" / "runs", "H"),
    ("C3-L4-N2 hold", EVID / "c3_l4_n2_2026-09-29" / "runs", "H"),
    ("C3-L4-D1 B3b 30-min default hold", EVID / "c3_l4_d1_2026-10-01" / "runs", "H"),
] + [(f"LINK-L2 H{k}", EVID / "link_l2_2026-10-02" / "runs", f"H{k}") for k in range(1, 7)] \
  + [("C5-M4A V5 (adopted 7000, 4x source)", EVID / "c5_m4a_2026-10-01" / "runs", "b_adopted")]
PROXIES = [(f"C3-L4-S1 H{k}", EVID / "c3_l4_s1_2026-09-24" / "runs", f"H{k}") for k in range(1, 5)] \
  + [(f"LINK-L1 H{k}", EVID / "link_l1_2026-10-01" / "runs", f"H{k}") for k in range(1, 7)]

S1_START, S1_END = "2026-10-02T23:45:40.569Z", "2026-10-02T23:47:59.489Z"
S3_ENTRY_DECISION, S3_START = "2026-10-03T06:57:33.368Z", "2026-10-03T06:57:34.630Z"

LEAVE_CANDIDATES = ("L-A", "L-B", "L-C", "L-D")
TRIGGER_RUNG_LOSS = "rung_loss"


def c2_rows(path: Path, start: str | None = None, end: str | None = None) -> list[dict]:
    rows = [r for r in m5.jl(path) if isinstance(r.get("elapsed_ms"), (int, float))]
    if start:
        rows = [r for r in rows if r.get("at_utc", "") >= start]
    if end:
        rows = [r for r in rows if r.get("at_utc", "") < end]
    return rows


def tel_c2(r: dict) -> dict:
    t = m5.tel_from_c2(r)
    t["decoder"]["stale_output_drops_delta"] = (r.get("decoder") or {}).get("stale_output_drops_delta")
    return t


def sample(t: dict) -> dict:
    s = ab._sample(t)
    s["stale_output_drops_delta"] = (t.get("decoder") or {}).get("stale_output_drops_delta")
    return s


# ------------------------------------------------------------------ leave ---
def leave_met(cand: str, ev: deque) -> bool:
    lost = [r["lost"] for r in ev]
    last10 = lost[-10:]
    a = sum(1 for v in last10 if v is not None and v >= 100) >= 2
    if cand == "L-A":
        return a
    if cand == "L-B":
        return len(lost) >= 15 and sum(v for v in lost[-15:] if v is not None) >= 300
    if cand == "L-C":
        return sum(1 for v in last10 if v is not None and v >= 50) >= 3
    if cand == "L-D":
        st = ev[-1]["stale"] if ev else None
        return a or (st is not None and st >= 5)
    raise ValueError(cand)


class CandidatePolicy(live.LivePolicy):
    """The live policy with the rung flag and ONE pre-registered loss leave candidate (None = as built)."""

    def __init__(self, leave: str | None) -> None:
        self.leave_cand = leave
        self.rung_eval: deque = deque(maxlen=15)
        super().__init__(top_1080p=True)

    def _window_restart(self) -> None:
        super()._window_restart()
        if hasattr(self, "rung_eval"):
            self.rung_eval.clear()

    def _evidence(self):
        at_rung = self.level_kbps == live.RUNG_KBPS
        if at_rung and self.window:
            s = self.window[-1]
            self.rung_eval.append({"lost": self._num(s.get("lost_packets_delta")),
                                   "stale": self._num(s.get("stale_output_drops_delta"))})
        cls, m = super()._evidence()
        if cls in ("FALLBACK", "ROUTINE") or not at_rung or self.leave_cand is None:
            return cls, m
        if leave_met(self.leave_cand, self.rung_eval):
            m["trigger"] = TRIGGER_RUNG_LOSS
            m["rung_loss_candidate"] = self.leave_cand
            return "ROUTINE", m
        return cls, m

    def _decide(self, kind, m, elapsed, ctx, *, injected=False):
        if m.get("trigger") != TRIGGER_RUNG_LOSS:
            return super()._decide(kind, m, elapsed, ctx, injected=injected)
        # One rung down through every gate: the mild bar's path computes exactly that target.
        m["trigger"] = live.TRIGGER_CAPACITY_MILD
        evs = super()._decide(kind, m, elapsed, ctx, injected=injected)
        m["trigger"] = TRIGGER_RUNG_LOSS
        for e in evs:
            if e.get("trigger") == live.TRIGGER_CAPACITY_MILD:
                e["trigger"] = TRIGGER_RUNG_LOSS
            if e.get("reason") == live.TRIGGER_CAPACITY_MILD:
                e["reason"] = TRIGGER_RUNG_LOSS
        if self.reason == live.TRIGGER_CAPACITY_MILD:
            self.reason = TRIGGER_RUNG_LOSS
        return evs


def leave_series(tels: list[dict], cand: str | None) -> dict:
    p = CandidatePolicy(cand)
    p.reset(None, level_kbps=live.RUNG_KBPS)
    p.last_direction, p.reports_since_action, p.blackout_remaining = "up", 0, live.BLACKOUT_REPORTS
    t0 = t_permit = leave = None
    for t in tels:
        el = t.get("session_elapsed_ms")
        if not isinstance(el, (int, float)):
            continue
        t0 = el if t0 is None else t0
        t2 = json.loads(json.dumps(t))
        t2["session_elapsed_ms"] = int(el) + 60_000
        s = sample(t2)
        evs = p.feed(s, {"guards": GUARDS, "clock_ms": int(el) + 60_000})
        if t_permit is None and p.last_disposition == "evaluated" and p.hold_left("ROUTINE") == 0:
            t_permit = (el - t0) / 1000.0
        for e in evs:
            if e["event"] == "transition" and e.get("from_kbps") == live.RUNG_KBPS and leave is None:
                leave = {"t": (el - t0) / 1000.0, "trigger": e.get("trigger") or e.get("reason"),
                         "class": e.get("class"), "to": e.get("to_kbps")}
        if p.pending:
            p.actuation_done(True, actual_kbps=p.pending["to_kbps"])
        if leave is not None:
            break
    span = None
    raw_first = raw_bar_first(tels, cand) if cand else None
    if tels and isinstance(tels[-1].get("session_elapsed_ms"), (int, float)) and t0 is not None:
        span = round((tels[-1]["session_elapsed_ms"] - t0) / 1000.0, 1)
    out = {"span_s": span, "t_permit_s": t_permit, "leave": leave, "raw_bar_first_s": raw_first}
    if leave and t_permit is not None:
        out["after_permit_s"] = round(leave["t"] - t_permit, 1)
    return out


def raw_bar_first(tels: list[dict], cand: str) -> float | None:
    """Reported only: the first report at which the candidate's bar is met on the series' own
    fresh, non-resync reports after the first 3 (no gate, no hold-down) -- where a leave could
    first have been named had nothing held it."""
    ev: deque = deque(maxlen=15)
    t0, n = None, 0
    for t in tels:
        el = t.get("session_elapsed_ms")
        if not isinstance(el, (int, float)):
            continue
        t0 = el if t0 is None else t0
        s = sample(t)
        if not (s.get("available") and s.get("fresh")) or s.get("waiting_for_idr"):
            continue
        n += 1
        if n <= live.BLACKOUT_REPORTS:
            continue
        ev.append({"lost": s.get("lost_packets_delta"), "stale": s.get("stale_output_drops_delta")})
        if leave_met(cand, ev):
            return round((el - t0) / 1000.0, 1)
    return None


def leave_sets():
    sets = []
    for lab, d, n in m5.LEAVE_SET:
        src, tels = m5.series(d, n, "c")
        if src == "C2 telemetry":   # re-read to carry the stale field
            tels = [tel_c2(r) for r in c2_rows(d / f"{n}_telemetry.jsonl")]
        sets.append((lab, src, tels, "13"))
    sets.append(("C5-M5 S1 1080p stretch (injected entry -> injected leave)", "C2 telemetry",
                 [tel_c2(r) for r in c2_rows(M5 / "s1" / "S1_telemetry.jsonl", S1_START, S1_END)], "S1"))
    sets.append(("C5-M5 S3 1080p stretch (own entry -> session end)", "C2 telemetry",
                 [tel_c2(r) for r in c2_rows(M5 / "s3" / "S3_telemetry.jsonl", S3_START)], "S3"))
    return sets


# ------------------------------------------------------------------ entry ---
def entry_series(tels: list[dict], n: int, k: int) -> dict:
    saved = (live.RUNG_WINDOW_REPORTS, live.RUNG_CLEAN_NEEDED)
    live.RUNG_WINDOW_REPORTS, live.RUNG_CLEAN_NEEDED = n, k
    try:
        p = live.LivePolicy(top_1080p=True)
        t0, first, entries, best, after, after_unclean, leaves = None, None, 0, 0, 0, 0, []
        for t in tels:
            el = t.get("session_elapsed_ms")
            if not isinstance(el, (int, float)):
                continue
            t0 = el if t0 is None else t0
            s = sample(t)
            if first is not None and s.get("available") and s.get("fresh"):
                after += 1
                after_unclean += 0 if p.increase_clean(s) else 1
            for e in p.feed(s, {"guards": GUARDS, "clock_ms": int(el)}):
                if e["event"] == "transition" and e.get("to_kbps") == live.RUNG_KBPS:
                    entries += 1
                    if first is None:
                        first = (el - t0) / 1000.0
                elif e["event"] == "transition" and e.get("from_kbps") == live.RUNG_KBPS:
                    leaves.append(((el - t0) / 1000.0, e.get("trigger") or e.get("reason")))
            if p.pending:
                p.actuation_done(True, actual_kbps=p.pending["to_kbps"])
            if p.level_kbps == live.REFERENCE_KBPS:
                best = max(best, sum(p.rung_window))
        span = round((tels[-1]["session_elapsed_ms"] - t0) / 1000.0, 1) if tels and t0 is not None else None
        return {"entries": entries, "first_entry_s": first, "best_window": best, "span_s": span,
                "after_reports": after, "after_unclean_frac": (round(after_unclean / after, 4) if after else None),
                "leaves": leaves}
    finally:
        live.RUNG_WINDOW_REPORTS, live.RUNG_CLEAN_NEEDED = saved


def entry_sets():
    out = []
    for group, items in (("real", REAL_TEN), ("proxy", PROXIES), ("beside", m5.ENTRY_BESIDE)):
        for lab, d, n in items:
            src, tels = m5.series(d, n, "b")
            out.append((lab, src, tels, group))
    out.append(("C5-M5 S2 daytime hold", "C2 telemetry",
                [tel_c2(r) for r in c2_rows(M5 / "s2" / "S2_telemetry.jsonl")], "m5"))
    out.append(("C5-M5 S3 7000 stretch (start -> its real entry)", "C2 telemetry",
                [tel_c2(r) for r in c2_rows(M5 / "s3" / "S3_telemetry.jsonl", None, S3_ENTRY_DECISION)], "m5"))
    return out


def fmt(v, nd=1):
    return "-" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def main_replays(out_dir: Path) -> int:
    lines = ["C5-M5B replays: the rung's entry threshold and loss leave (pre-registration sha256 6ba1e522...)",
             f"live module: companion/adaptive_bitrate_live.py as at a402272 (unchanged before the selection)", ""]
    res = {"entry": {}, "leave": {}}

    # ---- entry
    lines.append("== 1. ENTRY candidates (strictest first); per hold: first entry min / entries / unclean after "
                 "entry % / best window")
    esets = entry_sets()
    for cname, n, k in ENTRY_CANDIDATES:
        res["entry"][cname] = []
        lines.append(f"-- {cname}: >= {k} of {n}")
        for lab, src, tels, group in esets:
            if not tels:
                lines.append(f"   [{group}] {lab}: no series")
                continue
            r = entry_series(tels, n, k)
            r.update({"label": lab, "source": src, "group": group, "reports": len(tels)})
            res["entry"][cname].append(r)
            fe = r["first_entry_s"]
            lines.append(f"   [{group:6s}] {lab} [{src}, {len(tels)} rep, {r['span_s']} s]: "
                         f"first entry {fmt(fe / 60.0 if fe is not None else None)} min; entries {r['entries']}; "
                         f"unclean after {fmt(r['after_unclean_frac'] * 100 if r['after_unclean_frac'] is not None else None)} %"
                         f"; best window {r['best_window']}/{n}"
                         + (f"; leaves {r['leaves']}" if r["leaves"] else ""))
    lines.append("")
    lines.append("ENTRY TABLE (the ten real-input holds): candidate -> holds entered within 20 min (<= 1200 s)")
    chosen_entry = None
    for cname, n, k in ENTRY_CANDIDATES:
        rs = [r for r in res["entry"][cname] if r["group"] == "real"]
        within = [r for r in rs if r["first_entry_s"] is not None and r["first_entry_s"] <= 1200.0]
        prox = [r for r in res["entry"][cname] if r["group"] == "proxy"]
        pw = sum(1 for r in prox if r["first_entry_s"] is not None and r["first_entry_s"] <= 1200.0)
        fr = [r["after_unclean_frac"] for r in rs if r["after_unclean_frac"] is not None]
        lines.append(f"   {cname}: {len(within)} of {len(rs)} real (proxies {pw} of {len(prox)}); "
                     f"median minutes to first entry (real, entered) "
                     f"{fmt(sorted(r['first_entry_s'] / 60 for r in within)[len(within) // 2] if within else None)}; "
                     f"unclean after entry, real holds: "
                     f"{', '.join(f'{x * 100:.1f}%' for x in fr) if fr else '-'}")
        if chosen_entry is None and len(within) >= 7:
            chosen_entry = cname
    res["entry_selected"] = chosen_entry
    lines.append(f"ENTRY SELECTION (strictest with >= 7 of 10 within 20 min): "
                 + (chosen_entry if chosen_entry else "NONE -- E405 not enough; the entry stays at 435 of 450"))
    lines.append("")

    # ---- leave
    lines.append("== 2. LEAVE candidates; per series: leave s from start (trigger) / t_permit / s after permit")
    lsets = leave_sets()
    for cand in (None,) + LEAVE_CANDIDATES:
        cname = cand or "as built (mild bar)"
        res["leave"][cname] = []
        lines.append(f"-- {cname}")
        for lab, src, tels, grp in lsets:
            r = leave_series(tels, cand)
            r.update({"label": lab, "source": src, "group": grp, "reports": len(tels)})
            res["leave"][cname].append(r)
            lv = r["leave"]
            lines.append(f"   [{grp:2s}] {lab} [{src}, {len(tels)} rep, {r['span_s']} s]: "
                         + (f"LEAVES at {lv['t']:.1f} s ({lv['trigger']}, {lv['class']}) -> {lv['to']}; "
                            f"permit {fmt(r['t_permit_s'])} s; {fmt(r.get('after_permit_s'))} s after permit"
                            if lv else f"no leave (permit {fmt(r['t_permit_s'])} s)")
                         + (f"; raw bar first met {fmt(r['raw_bar_first_s'])} s" if cand else ""))
    lines.append("")
    lines.append("LEAVE TABLE: candidate -> (1) S1 within 60 s of permit, (2) n1r C3 within 120 s of permit, "
                 "(3) no leave on S3, fires on k of 13")
    qualifying = []
    for cand in LEAVE_CANDIDATES:
        rs = res["leave"][cand]
        s1 = next(r for r in rs if r["group"] == "S1")
        s3 = next(r for r in rs if r["group"] == "S3")
        c3 = next(r for r in rs if r["label"].startswith("C5-M2 n1r C3"))
        c1 = s1["leave"] is not None and s1.get("after_permit_s") is not None and s1["after_permit_s"] <= 60.0
        c2 = c3["leave"] is not None and c3.get("after_permit_s") is not None and c3["after_permit_s"] <= 120.0
        c3ok = s3["leave"] is None
        fires = sum(1 for r in rs if r["group"] == "13" and r["leave"] is not None)
        lines.append(f"   {cand}: (1) {'MET' if c1 else 'not met'} (S1 "
                     + (f"{s1['leave']['t']:.1f} s from start, {s1['after_permit_s']} s after permit" if s1["leave"] else "no leave")
                     + f"); (2) {'MET' if c2 else 'not met'} (n1r C3 "
                     + (f"{c3['leave']['t']:.1f} s from start, {c3['after_permit_s']} s after permit" if c3["leave"] else "no leave")
                     + f"); (3) {'MET' if c3ok else 'NOT MET: FALSE LEAVE'} (S3 "
                     + (f"leaves at {s3['leave']['t']:.1f} s" if s3["leave"] else "no leave")
                     + f"); fires on {fires} of 13"
                     + ("  <- meets all three" if (c1 and c2 and c3ok) else ""))
        if c1 and c2 and c3ok:
            qualifying.append((fires, cand))
    chosen_leave = None
    if qualifying:
        best = max(f for f, _ in qualifying)
        chosen_leave = next(c for c in LEAVE_CANDIDATES if (best, c) in qualifying)
    res["leave_selected"] = chosen_leave
    lines.append("LEAVE SELECTION (all three hard conditions; most of 13; ties simplest): "
                 + (chosen_leave if chosen_leave else "NONE -- the mild bar is kept (the user decides)"))
    text = "\n".join(lines) + "\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "c5_m5b_replays.txt").write_text(text)
    (out_dir / "c5_m5b_replays.json").write_text(json.dumps(res, indent=1, default=str))
    print(text)
    return 0


def main_stop_rule(out_dir: Path) -> int:
    base = m5.load_baseline()
    lines = ["C5-M5B stop rule: PRIVYHUB_ADAPTIVE_BITRATE_TOP absent, the built live policy vs the closed "
             f"controller ({m5.BASELINE_COMMIT}, loaded from git), every series C5-M5 compared", ""]
    ok, ngroups, feeds, events = m5.stop_rule(lines, base)
    lines.append(f"-> {'PASS: zero differences' if ok else 'STOP: differences found; no session'} "
                 f"({ngroups} series, {feeds} reports, {events} events)")
    text = "\n".join(lines) + "\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "c5_m5b_stop_rule.txt").write_text(text)
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = Path(args[0]) if args else EVID / "c5_m5b_2026-10-03"
    sys.exit(main_stop_rule(out) if "--stop-rule" in sys.argv else main_replays(out))
