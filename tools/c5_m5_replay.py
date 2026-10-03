#!/usr/bin/env python3
"""C5-M5 section 3: the 1080p rung's replays and the stop rule. Read-only; offline.

    python3 tools/c5_m5_replay.py [out_dir]       -> c5_m5_replays.txt / c5_m5_replays.json

Pre-registered in docs/memory/evidence/c5_m5_2026-10-03/c5_m5_preregistration.txt (section 3).

1. STOP RULE. With PRIVYHUB_ADAPTIVE_BITRATE_TOP absent, the patched live
   policy and the CLOSED controller's policy (companion/adaptive_bitrate_live.py
   at the baseline commit, loaded from git) are fed identical inputs on every
   recorded series below and on every series C3-L4-N2's replay reads (every
   live sample session in the companion's log and archive, every heartbeat
   series on disk); every event either emits is compared exactly (JSON with
   sorted keys). Any difference -> STOP (no rung session).
2. LEAVE, on every recorded 1080p series (C5-M1's A holds, C5-M2's six C
   holds, C5-M4's c_1x / c_2x / c_4x / c_8x): the policy with the flag starts
   AT the rung as if it had just entered it (last direction up, 0 reports since,
   the 3-report blackout); the series' elapsed is offset by 60 s so the
   session-age guard reads as it would mid-session. Reported: when it would
   have left (trigger, target), the first report that met the raw mild bar,
   and the reports before the leave that were not clean.
3. ENTRY, on every recorded 720p series at 7000 (C3-L4-S1's shadow night H1-H4,
   N1's and N2's silent holds, D1's B3b hold, LINK-L1 H1-H6, LINK-L2 H1-H6,
   C5-M4A's V5; C5-M4's b holds listed beside): the policy with the flag from
   the session's start; where it would have entered (increase_1080p), and,
   continuing on the SAME hold's reports (720p data -- a preview, not a 1080p
   measurement), where the rules would then have taken it out, every
   re-entry, the rung hold.

Sources, best first: the C2 telemetry (c5_m4_sampler --telemetry: the client's
own report fields, the inputs live reads), else the live log's `sample` rows
for the hold (the inputs as live was fed them), else the heartbeat proxies
(C4-D1's: fps from rendered frames, queue = queued - rendered in the interval,
gap = the output age at the row, loss = the lost_packets delta). Each series
names its source.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import c3_l4_l1_replay as l1  # noqa: E402
import c3_l4_n2_replay as n2  # noqa: E402

EVID = REPO / "docs" / "memory" / "evidence"
BASELINE_COMMIT = "5005615"
GUARDS = dict(l1.GUARDS_OK)
DECISIONS = ("transition", "would_act", "hold", "refused")


def load_baseline():
    src = subprocess.run(["git", "-C", str(REPO), "show", f"{BASELINE_COMMIT}:companion/adaptive_bitrate_live.py"],
                         capture_output=True, text=True, check=True).stdout
    d = Path(tempfile.mkdtemp())
    p = d / "adaptive_bitrate_live_base.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location("adaptive_bitrate_live_base", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def jl(p: Path) -> list[dict]:
    return n2.jl(p)


# ------------------------------------------------------------------ series ---
def tel_from_c2(r: dict) -> dict:
    rec, dec, lat = r.get("receiver") or {}, r.get("decoder") or {}, r.get("latency") or {}
    return {"available": True, "fresh": bool(r.get("fresh")), "session_elapsed_ms": r.get("elapsed_ms"),
            "receiver": {"recent_fps": rec.get("recent_fps"), "waiting_for_idr": rec.get("waiting_for_idr"),
                         "lost_packets_delta": rec.get("lost_packets_delta")},
            "decoder": {"queue_depth": dec.get("queue_depth")},
            "latency": {"output_gap_ms": lat.get("output_gap_ms")}, "fec": {}}


def tel_from_sample(r: dict) -> dict:
    return {"available": True, "fresh": bool(r.get("fresh")), "session_elapsed_ms": r.get("session_elapsed_ms"),
            "receiver": {"recent_fps": r.get("fps"), "waiting_for_idr": r.get("waiting_for_idr"),
                         "lost_packets_delta": r.get("lost_packets_delta")},
            "decoder": {"queue_depth": r.get("queue_depth")},
            "latency": {"output_gap_ms": r.get("output_gap_ms")}, "fec": {}}


def hb_series(path: Path) -> list[dict]:
    rs = [r for r in jl(path) if isinstance(r.get("elapsed_ms"), (int, float))]
    rs.sort(key=lambda r: r["elapsed_ms"])
    out = []
    for a, b in zip(rs, rs[1:]):
        dt = b["elapsed_ms"] - a["elapsed_ms"]
        if dt <= 0 or not all(isinstance(x.get("rendered_frames"), (int, float)) for x in (a, b)):
            continue
        fps = max(0.0, (b["rendered_frames"] - a["rendered_frames"]) * 1000.0 / dt)
        q = None
        if all(isinstance(x.get("queued_frames"), (int, float)) for x in (a, b)):
            q = max(0, (b["queued_frames"] - a["queued_frames"]) - (b["rendered_frames"] - a["rendered_frames"]))
        lost = None
        if all(isinstance(x.get("lost_packets"), (int, float)) for x in (a, b)):
            lost = max(0, b["lost_packets"] - a["lost_packets"])
        age = b.get("last_output_age_ms") if isinstance(b.get("last_output_age_ms"), (int, float)) else None
        t = l1.tel(int(b["elapsed_ms"]), round(fps, 2), q, age)
        t["receiver"]["lost_packets_delta"] = lost
        out.append(t)
    return out


def series(path_glob_base: Path, name: str, kind: str):
    """(source, [telemetry dicts]) for one hold, best source first."""
    d = path_glob_base
    for p in (d / f"{name}_telemetry.jsonl",):
        if p.exists():
            rows = [r for r in jl(p) if isinstance(r.get("elapsed_ms"), (int, float))]
            if rows:
                return "C2 telemetry", [tel_from_c2(r) for r in rows]
    p = d / f"decision_log_{name}.jsonl"
    if p.exists():
        rows = [r for r in jl(p) if r.get("event") == "sample" and r.get("disposition") != "dropped_actuating"]
        if rows:
            return "live sample rows", [tel_from_sample(r) for r in rows]
    p = d / f"heartbeat_{name}.jsonl"
    if p.exists():
        return "heartbeat proxies", hb_series(p)
    return None, []


LEAVE_SET = [
    ("C5-M1 A1 (1080p candidate, parity)", EVID / "c5_m1_2026-09-28" / "runs", "A1"),
    ("C5-M1 A2", EVID / "c5_m1_2026-09-28" / "runs", "A2"),
    ("C5-M1 A3", EVID / "c5_m1_2026-09-28" / "runs", "A3"),
    ("C5-M2 n1 C1 (parity, cap 90)", EVID / "c5_m2_2026-09-29" / "runs_n1", "C1"),
    ("C5-M2 n1 C2 (80 %, cap 160)", EVID / "c5_m2_2026-09-29" / "runs_n1", "C2"),
    ("C5-M2 n1 C3 (80 %, cap 90 = the rung)", EVID / "c5_m2_2026-09-29" / "runs_n1", "C3"),
    ("C5-M2 n1r C1", EVID / "c5_m2_2026-09-29" / "runs_n1r", "C1"),
    ("C5-M2 n1r C2", EVID / "c5_m2_2026-09-29" / "runs_n1r", "C2"),
    ("C5-M2 n1r C3 (= the rung)", EVID / "c5_m2_2026-09-29" / "runs_n1r", "C3"),
    ("C5-M4 c_1x (c3 at 1080p, 1x source)", EVID / "c5_m4_2026-10-01" / "runs", "c_1x"),
    ("C5-M4 c_2x", EVID / "c5_m4_2026-10-01" / "runs", "c_2x"),
    ("C5-M4 c_4x (the rung on the adopted source)", EVID / "c5_m4_2026-10-01" / "runs", "c_4x"),
    ("C5-M4 c_8x", EVID / "c5_m4_2026-10-01" / "runs_8x", "c_8x"),
]
ENTRY_SET = [
    ("C3-L4-S1 shadow night H1", EVID / "c3_l4_s1_2026-09-24" / "runs", "H1"),
    ("C3-L4-S1 H2", EVID / "c3_l4_s1_2026-09-24" / "runs", "H2"),
    ("C3-L4-S1 H3", EVID / "c3_l4_s1_2026-09-24" / "runs", "H3"),
    ("C3-L4-S1 H4", EVID / "c3_l4_s1_2026-09-24" / "runs", "H4"),
    ("C3-L4-N1 silent live hold", EVID / "c3_l4_n1_2026-09-29" / "runs", "H"),
    ("C3-L4-N2 hold", EVID / "c3_l4_n2_2026-09-29" / "runs", "H"),
    ("C3-L4-D1 B3b 30-min default hold", EVID / "c3_l4_d1_2026-10-01" / "runs", "H"),
] + [(f"LINK-L1 H{k}", EVID / "link_l1_2026-10-01" / "runs", f"H{k}") for k in range(1, 7)] \
  + [(f"LINK-L2 H{k}", EVID / "link_l2_2026-10-02" / "runs", f"H{k}") for k in range(1, 7)] \
  + [("C5-M4A V5 (adopted 7000, 4x source)", EVID / "c5_m4a_2026-10-01" / "runs", "b_adopted")]
ENTRY_BESIDE = [(f"C5-M4 {n} (720p at 7000, {n[2:]} source; 5-min)", EVID / "c5_m4_2026-10-01" / d, n)
                for d, n in (("runs", "b_1x"), ("runs", "b_2x"), ("runs", "b_4x"), ("runs_8x", "b_8x"))]


# ------------------------------------------------------------- 1. stop rule ---
def drive(policy, steps, record):
    for st in steps:
        if st[0] == "feed":
            evs = policy.feed(ab._sample(st[1]), st[2])
            record.extend(json.dumps(e, sort_keys=True, default=str) for e in evs)
            if policy.pending:
                policy.actuation_done(True, actual_kbps=policy.pending["to_kbps"])
        elif st[0] == "ssrc":
            record.extend(json.dumps(e, sort_keys=True, default=str)
                          for e in policy.note_ssrc_change(st[1], clock_ms=st[2]))
        elif st[0] == "disable":
            policy.acting = False


def steps_from_series(tels):
    out = []
    for t in tels:
        el = t.get("session_elapsed_ms")
        out.append(("feed", t, {"guards": GUARDS, "clock_ms": int(el) if isinstance(el, (int, float)) else 0}))
    return out


def steps_from_exact(sess, rec):
    out = []
    for r in sess:
        ev = r.get("event")
        t = n2.ts(r["at_utc"])
        clock = int(t * 1000)
        if ev == "ssrc_change":
            out.append(("ssrc", r.get("source") or "recovery_restart", clock))
        elif ev == "disabled":
            out.append(("disable",))
        elif ev == "sample" and r.get("disposition") != "dropped_actuating":
            st = rec.state_at(t)
            g = dict(GUARDS, recovery_playing=(st == "PLAYING"), game_not_paused=(st == "PLAYING"))
            out.append(("feed", tel_from_sample(r), {"guards": g, "clock_ms": clock}))
    return out


def stop_rule(lines, base):
    rec = n2.RecoveryTimeline(n2.recovery_rows())
    groups = []
    for lab, d, n in LEAVE_SET + ENTRY_SET + ENTRY_BESIDE:
        src, tels = series(d, n, "x")
        if tels:
            groups.append((f"{lab} [{src}]", steps_from_series(tels)))
    for si, sess in enumerate(n2.exact_sessions(n2.live_log_rows()), 1):
        groups.append((f"live log session {si} {sess[0]['at_utc'][:19]}Z", steps_from_exact(sess, rec)))
    for s in n2.heartbeat_sessions():
        if len(s["pts"]) < 5:
            continue
        tels = []
        for p in s["pts"]:
            age = p["age"] if isinstance(p["age"], (int, float)) else None
            t = l1.tel(p["elapsed"], p["fps"], p.get("q"), age)
            t["receiver"]["lost_packets_delta"] = p["lost"]
            tels.append(t)
        groups.append((f"heartbeat series {s['label'][:60]}", steps_from_series(tels)))
    diffs, feeds, events = [], 0, 0
    for lab, steps in groups:
        a, b = [], []
        drive(base.LivePolicy(), steps, a)
        drive(live.LivePolicy(), steps, b)          # top_1080p defaults to False: the flag absent
        feeds += sum(1 for s in steps if s[0] == "feed")
        events += len(a)
        if a != b:
            i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            diffs.append((lab, len(a), len(b), i, a[i] if i < len(a) else None, b[i] if i < len(b) else None))
    lines.append(f"series compared: {len(groups)} ({feeds} reports fed to each policy); events emitted by the "
                 f"closed controller's policy: {events}")
    lines.append(f"series with ANY difference (flag absent vs closed controller): {len(diffs)}")
    for d in diffs[:20]:
        lines.append(f"   {d[0]}: {d[1]} vs {d[2]} events, first difference at #{d[3]}:\n      closed  {d[4]}\n      patched {d[5]}")
    return not diffs, len(groups), feeds, events


# ---------------------------------------------------------------- 2. leave ---
def mild_bar(window):
    fps = [w["fps"] for w in window]
    lost = [w["lost"] for w in window]
    return (sum(1 for v in fps if v is not None and v < live.CAPACITY_MILD_FPS_BELOW) >= live.CAPACITY_MILD_FPS_OF
            and sum(1 for v in lost if v is not None and v >= live.CAPACITY_MILD_LOSS_AT_LEAST) >= live.CAPACITY_MILD_LOSS_OF)


def leave_one(lab, d, n):
    src, tels = series(d, n, "c")
    if not tels:
        return {"label": lab, "source": None}
    p = live.LivePolicy(top_1080p=True)
    p.reset(None, level_kbps=live.RUNG_KBPS)
    p.last_direction, p.reports_since_action, p.blackout_remaining = "up", 0, live.BLACKOUT_REPORTS
    t0 = None
    raw, first_bar, unclean, leave, evs = [], None, 0, None, []
    for t in tels:
        el = t.get("session_elapsed_ms")
        if not isinstance(el, (int, float)):
            continue
        t0 = el if t0 is None else t0
        t2 = json.loads(json.dumps(t))
        t2["session_elapsed_ms"] = int(el) + 60_000
        s = ab._sample(t2)
        if s.get("fresh"):
            raw.append({"fps": s.get("fps"), "lost": s.get("lost_packets_delta")})
            if first_bar is None and len(raw) >= 5 and mild_bar(raw[-5:]):
                first_bar = (el - t0) / 1000.0
        if leave is None and s.get("fresh") and not p.increase_clean(s):
            unclean += 1
        for e in p.feed(s, {"guards": GUARDS, "clock_ms": int(el) + 60_000}):
            if e["event"] in DECISIONS:
                evs.append(((el - t0) / 1000.0, e["event"], e.get("class"), e.get("trigger"), e.get("reason"),
                            e.get("from_kbps", e.get("level_kbps")), e.get("to_kbps", e.get("would_target_kbps"))))
                if leave is None and e["event"] == "transition" and e.get("from_kbps") == live.RUNG_KBPS:
                    leave = evs[-1]
        if p.pending:
            p.actuation_done(True, actual_kbps=p.pending["to_kbps"])
        if leave is not None:
            break
    return {"label": lab, "source": src, "reports": len(tels), "first_mild_bar_s": first_bar,
            "leave": leave, "unclean_before_leave": unclean, "decisions": evs[:12],
            "span_s": round((tels[-1]["session_elapsed_ms"] - tels[0]["session_elapsed_ms"]) / 1000.0, 1)
            if isinstance(tels[-1].get("session_elapsed_ms"), (int, float)) else None}


# ---------------------------------------------------------------- 3. entry ---
def entry_one(lab, d, n):
    src, tels = series(d, n, "b")
    if not tels:
        return {"label": lab, "source": None}
    p = live.LivePolicy(top_1080p=True)
    t0, evs, level_time = None, [], {}
    last_el, longest, run = None, 0, 0
    for t in tels:
        el = t.get("session_elapsed_ms")
        if not isinstance(el, (int, float)):
            continue
        t0 = el if t0 is None else t0
        if last_el is not None:
            level_time[p.level_kbps] = level_time.get(p.level_kbps, 0) + (el - last_el) / 1000.0
        last_el = el
        s = ab._sample(t)
        for e in p.feed(s, {"guards": GUARDS, "clock_ms": int(el)}):
            if e["event"] in ("transition", "would_act", "hold"):
                evs.append(((el - t0) / 1000.0, e["event"], e.get("class"), e.get("trigger") or "", e.get("reason"),
                            e.get("from_kbps", e.get("level_kbps")), e.get("to_kbps", e.get("would_target_kbps"))))
        if p.pending:
            p.actuation_done(True, actual_kbps=p.pending["to_kbps"])
        if p.level_kbps == live.REFERENCE_KBPS:
            longest = max(longest, sum(p.rung_window))
    entries = [e for e in evs if e[1] == "transition" and e[6] == live.RUNG_KBPS]
    return {"label": lab, "source": src, "reports": len(tels),
            "span_s": round((last_el - t0) / 1000.0, 1) if last_el is not None else None,
            "entries": entries, "events": evs, "rung_closed": p.rung_closed,
            "seconds_by_level": {k: round(v, 1) for k, v in sorted(level_time.items())},
            "best_rung_window_clean": longest}


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVID / "c5_m5_2026-10-03"
    out_dir.mkdir(parents=True, exist_ok=True)
    base = load_baseline()
    lines = ["C5-M5 replays: the 1080p rung (PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p) and the stop rule",
             f"rung: {live.RUNG_KBPS} kbps at {live.RUNG_LEVELS[live.RUNG_KBPS]}, entry from 7000 at >= "
             f"{live.RUNG_CLEAN_NEEDED} of the last {live.RUNG_WINDOW_REPORTS} clean, re-entry hold "
             f"{live.RUNG_REENTRY_HOLD_MS // 1000} s, leave by the existing triggers (mild bar -> 7000)",
             f"closed controller: companion/adaptive_bitrate_live.py at {BASELINE_COMMIT} (git)", ""]
    lines.append("== 1. STOP RULE: the flag absent vs the closed controller, every series")
    ok, ngroups, feeds, events = stop_rule(lines, base)
    lines.append(f"   -> {'PASS: zero differences' if ok else 'STOP: differences found; no rung session'}")
    lines.append("")
    lines.append("== 2. LEAVE on every recorded 1080p series (the policy starts AT the rung, just entered; "
                 "elapsed +60 s for the session-age guard)")
    leaves = [leave_one(*x) for x in LEAVE_SET]
    for r in leaves:
        if not r["source"]:
            lines.append(f"   {r['label']}: no series on disk")
            continue
        lv = r["leave"]
        lines.append(f"   {r['label']} [{r['source']}, {r['reports']} reports, {r['span_s']} s]: "
                     f"first raw mild bar at {r['first_mild_bar_s']} s; "
                     + (f"LEAVES at {lv[0]:.1f} s ({lv[3] or lv[4]}, {lv[2]}) {lv[5]} -> {lv[6]}; "
                        f"{r['unclean_before_leave']} unclean reports before it" if lv else
                        f"never leaves in the series ({r['unclean_before_leave']} unclean reports)"))
        for e in r["decisions"]:
            if e is not lv:
                lines.append(f"        t={e[0]:7.1f}s {e[1]:10s} {str(e[2]):9s} {str(e[3] or ''):16s} {e[4]} {e[5]} -> {e[6]}")
    lines.append("")
    lines.append("== 3. ENTRY on every recorded 720p series at 7000 (the policy with the flag from the session start; "
                 "after an entry the SAME hold's 720p reports continue -- a preview, not a 1080p measurement)")
    entries = [entry_one(*x) for x in ENTRY_SET]
    beside = [entry_one(*x) for x in ENTRY_BESIDE]
    for tag, rs in (("", entries), ("   beside (5-min holds):", beside)):
        if tag:
            lines.append(tag)
        for r in rs:
            if not r["source"]:
                lines.append(f"   {r['label']}: no series on disk")
                continue
            lines.append(f"   {r['label']} [{r['source']}, {r['reports']} reports, {r['span_s']} s]: "
                         f"entries {len(r['entries'])}"
                         + (f" (first at {r['entries'][0][0]:.0f} s)" if r["entries"] else
                            f"; best rung window {r['best_rung_window_clean']} clean of {live.RUNG_WINDOW_REPORTS} needed "
                            f"{live.RUNG_CLEAN_NEEDED}")
                         + f"; seconds by level {r['seconds_by_level']}" + ("; RUNG CLOSED (oscillation)" if r["rung_closed"] else ""))
            for e in r["events"]:
                lines.append(f"        t={e[0]:7.1f}s {e[1]:10s} {str(e[2]):9s} {str(e[3]):16s} {e[4]} {e[5]} -> {e[6]}")
    n_ent = sum(1 for r in entries if r.get("entries"))
    n_left = sum(1 for r in entries if any(e[1] == "transition" and e[5] == live.RUNG_KBPS for e in r.get("events", [])))
    lines.append("")
    lines.append(f"SUMMARY: stop rule {'PASS' if ok else 'STOP'} ({ngroups} series, {feeds} reports, {events} events); "
                 f"entry reached on {n_ent} of {sum(1 for r in entries if r['source'])} 720p holds, and left again on "
                 f"{n_left} of those; leave reached on {sum(1 for r in leaves if r.get('leave'))} of "
                 f"{sum(1 for r in leaves if r['source'])} 1080p series")
    text = "\n".join(lines) + "\n"
    (out_dir / "c5_m5_replays.txt").write_text(text)
    (out_dir / "c5_m5_replays.json").write_text(json.dumps({"stop_rule_pass": ok, "series": ngroups, "reports": feeds,
                                                            "events": events, "leave": leaves, "entry": entries,
                                                            "entry_beside": beside}, indent=1, default=str))
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
