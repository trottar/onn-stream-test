#!/usr/bin/env python3
"""C3-L4-L1: offline replays through the LIVE decision path.

    python3 tools/c3_l4_l1_replay.py [out_dir]

1. PARITY -- the C3-L4-S1 shadow night (4 holds, 3,598 evaluated reports).
   The night did not store every report: the shadow log holds one line per
   (state, reason) change, 1,048 lines, each with the sample that caused it.
   Between two lines every report kept the earlier line's (state, reason), so
   the series is rebuilt by holding each logged sample until the next line
   (report count from the elapsed gap at the 2 s cadence). CONTROL: the
   unchanged shadow engine is run on the rebuild and must reproduce the
   logged (state, reason) sequence; then shadow and live decide over the same
   rebuild and must agree -- zero actions.

2. RECORDED LOSS -- the C4-D1 heartbeat set (82 files) and the CTRL-L1 holds
   (3 files). A heartbeat is the client's 2 s counter row; it carries
   rendered frames (-> fps over the interval) and the output age at the
   sample, not the decoder queue depth or the interval's max output gap. So
   each series is scored twice:
     proxy  -- C4-D1's substitutions: fps from the frame counter, queue =
               frames queued but not rendered in the interval (the
               queued_frames - rendered_frames delta), gap = last_output_age_ms
               (a lower bound on the interval's largest gap);
     bound  -- the same fps, and every report under 57 fps scored as queue 2,
               every report under 50 fps as gap 300 ms: the most the recorded
               fps could ever make the policy do (an upper bound on firing).
   Output: the would-fire list (file, elapsed, class, from, to), the maximum
   transitions in any 10-minute window, and whether the rate limit tripped.
"""

from __future__ import annotations

import glob
import json
import os
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "companion"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402

EVID = REPO / "docs" / "memory" / "evidence"
GUARDS_OK = {"stream_active": True, "game_active": True, "game_not_paused": True,
             "recovery_playing": True, "reference_profile": True, "no_override": True,
             "actuator_bound": True}


def tel(elapsed, fps, queue, gap, idr=False):
    return {"available": True, "fresh": True, "session_elapsed_ms": elapsed,
            "receiver": {"recent_fps": fps, "waiting_for_idr": idr, "lost_packets_delta": None},
            "decoder": {"queue_depth": queue}, "latency": {"output_gap_ms": gap}, "fec": {}}


# ---------------------------------------------------------------- parity ---
def rebuild_shadow_night(path: Path):
    rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    sessions, cur = [], []
    for r in rows:
        if cur and r["session_elapsed_ms"] < cur[-1]["session_elapsed_ms"]:
            sessions.append(cur)
            cur = []
        cur.append(r)
    if cur:
        sessions.append(cur)
    out = []
    for rows_s in sessions:
        series = []
        for i, r in enumerate(rows_s):
            smp = r["sample"]
            e0 = r["session_elapsed_ms"]
            series.append((e0, smp, (r["to"], r["reason"])))
            if i + 1 < len(rows_s):
                e1 = rows_s[i + 1]["session_elapsed_ms"]
                n_fill = max(0, round((e1 - e0) / ab.REPORT_INTERVAL_MS) - 1)
                for k in range(n_fill):
                    series.append((e0 + (k + 1) * (e1 - e0) / (n_fill + 1), smp, None))
        out.append(series)
    return out, len(rows)


def parity(out_lines):
    path = EVID / "c3_l4_s1_2026-09-24" / "shadow_log.jsonl"
    sessions, n_lines = rebuild_shadow_night(path)
    total_reports = sum(len(s) for s in sessions)
    out_lines.append("== 1. PARITY: the C3-L4-S1 shadow night through the live path")
    out_lines.append(f"source {path.relative_to(REPO)}: {n_lines} logged lines, {len(sessions)} sessions")
    out_lines.append(f"rebuilt reports: {total_reports} (the night's status counters: 602 + 600 + 1,796 + 600 = 3,598)")
    ok_all = True
    tot = Counter()
    for si, series in enumerate(sessions, 1):
        sp = ab.ShadowPolicy()
        lp = live.LivePolicy()
        logged_seq, replay_seq = [], []
        shadow_acts, live_acts, live_refused = [], [], []
        for elapsed, smp, logged in series:
            s = ab._sample(tel(int(elapsed), smp.get("fps"), smp.get("queue_depth"), smp.get("output_gap_ms"),
                               bool(smp.get("waiting_for_idr"))))
            ev_s = sp.feed(s)
            for e in ev_s:
                if e["event"] == "state":
                    replay_seq.append((e["to"], e["reason"]))
                if e["event"] in ("would_act", "hold"):
                    shadow_acts.append((int(elapsed), e))
            ev_l = lp.feed(s, {"guards": GUARDS_OK, "clock_ms": int(elapsed)})
            for e in ev_l:
                if e["event"] in ("transition", "would_act", "hold"):
                    live_acts.append((int(elapsed), e))
                if e["event"] == "refused":
                    live_refused.append((int(elapsed), e))
            if lp.pending:
                lp.actuation_done(True, actual_kbps=lp.pending["to_kbps"])
            if logged is not None:
                logged_seq.append(logged)
        control = logged_seq == replay_seq
        ok_all &= control and not shadow_acts and not live_acts
        tot["reports"] += len(series)
        tot["shadow_acts"] += len(shadow_acts)
        tot["live_transitions"] += len(live_acts)
        tot["live_refused"] += len(live_refused)
        out_lines.append(
            f"  session {si}: reports {len(series)}; control (shadow on the rebuild reproduces the "
            f"logged sequence) {'MATCH' if control else 'MISMATCH'} ({len(logged_seq)} logged / "
            f"{len(replay_seq)} replayed changes); shadow would-acts {len(shadow_acts)}; "
            f"live transitions {len(live_acts)}; live refusals {len(live_refused)}; "
            f"live reports evaluated {lp.reports}; live level at end {lp.level_kbps}")
        if not control:
            for a, b in zip(logged_seq, replay_seq):
                if a != b:
                    out_lines.append(f"    first divergence: logged {a} vs replayed {b}")
                    break
    out_lines.append(f"PARITY: reports {tot['reports']}; shadow would-acts {tot['shadow_acts']}; live "
                     f"transitions {tot['live_transitions']}; live refusals {tot['live_refused']} -> "
                     f"{'SAME DECISIONS (zero actions)' if ok_all else 'NOT THE SAME'}")
    return ok_all


# ---------------------------------------------------------- loss replays ---
C4_D1_CUTOFF_UTC = "2026-09-24T16:13:00"   # c4_d1_analysis.txt written 16:13Z; the live logs have rotated since


def heartbeat_files():
    files = []
    inputs = EVID / "c4_d1_2026-09-24" / "inputs_sha256.txt"
    for line in inputs.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and "heartbeat" in parts[1]:
            files.append(("C4-D1", REPO / parts[1]))
    for f in sorted(glob.glob(str(EVID / "ctrl_l1_2026-09-24" / "runs" / "heartbeat_*.jsonl"))):
        files.append(("CTRL-L1", Path(f)))
    return files


def _label(path: Path) -> str:
    try:
        return str(path.relative_to(EVID))
    except ValueError:
        return str(path.relative_to(REPO))


def heartbeat_sessions():
    """Every heartbeat row once (C4-D1's dedupe), the companion's own logs cut
    at C4-D1's analysis time; split into sessions by time order (elapsed_ms
    falling, or > 30 s between rows). Each session is labelled with its source
    set, the file its first row came from and its start time."""
    rows = {}
    for src, path in heartbeat_files():
        live_log = "docs/memory/evidence" not in str(path)
        if not path.exists():
            continue
        for line in path.read_text(errors="replace").splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            at = r.get("received_at_utc") or ""
            if not isinstance(r.get("elapsed_ms"), (int, float)) or not at:
                continue
            if live_log and at[:19] > C4_D1_CUTOFF_UTC:
                continue
            key = (at, r.get("sequence"), r.get("elapsed_ms"))
            if key not in rows:
                rows[key] = (src, _label(path), r)
    ordered = sorted(rows.values(), key=lambda x: x[2]["received_at_utc"])
    sessions, cur = [], []
    from datetime import datetime

    def ts(r):
        return datetime.strptime(r["received_at_utc"][:23], "%Y-%m-%dT%H:%M:%S.%f").timestamp()
    for item in ordered:
        r = item[2]
        if cur and (r["elapsed_ms"] <= cur[-1][2]["elapsed_ms"] or ts(r) - ts(cur[-1][2]) > 30):
            sessions.append(cur)
            cur = []
        cur.append(item)
    if cur:
        sessions.append(cur)
    out = []
    for sess in sessions:
        rs = [x[2] for x in sess]
        pts = []
        for a, b in zip(rs, rs[1:]):
            dt = b["elapsed_ms"] - a["elapsed_ms"]
            if dt <= 0 or not isinstance(b.get("rendered_frames"), (int, float)) \
                    or not isinstance(a.get("rendered_frames"), (int, float)):
                continue
            fps = max(0.0, (b["rendered_frames"] - a["rendered_frames"]) * 1000.0 / dt)
            qproxy = None
            if isinstance(a.get("queued_frames"), (int, float)) and isinstance(b.get("queued_frames"), (int, float)):
                # C4-D1's substitution for queue depth: frames queued but not
                # rendered in the interval (queued_frames - rendered_frames delta)
                qproxy = max(0, (b["queued_frames"] - a["queued_frames"])
                             - (b["rendered_frames"] - a["rendered_frames"]))
            pts.append({"elapsed": int(b["elapsed_ms"]), "fps": round(fps, 2),
                        "age": b.get("last_output_age_ms"), "q": qproxy})
        srcs = sorted({x[0] for x in sess})
        files = Counter(x[1] for x in sess)
        label = f"{'+'.join(srcs)} {rs[0]['received_at_utc'][:19]}Z {files.most_common(1)[0][0]}"
        # R3b's deliberate link drops, and P8's first-run arm B, which its
        # record says a concurrent R3b E30 link drop disturbed
        # (D_BASE_P8_AUDIO_HOLE_ORIGIN_2026-09-22.md, item 2).
        deliberate = any("d_base_r3b" in f or "R3b" in f or "d_base_p8_2026-09-22/runs_v1/heartbeat_B" in f
                         for f in files)
        out.append({"label": label, "pts": pts, "deliberate_link_drop": deliberate})
    return out


def run_series(pts, variant):
    lp = live.LivePolicy()
    sp = ab.ShadowPolicy()
    fires, shadow_fires, refused = [], [], Counter()
    for p in pts:
        fps = p["fps"]
        age = p["age"] if isinstance(p["age"], (int, float)) else None
        if variant == "proxy":
            q, gap = p.get("q"), age
        else:
            q = 2 if fps < ab.ROUTINE_FPS_BELOW else 0
            gap = max(age or 0, 300 if fps < ab.FALLBACK_FPS_BELOW else 0)
        s = ab._sample(tel(p["elapsed"], fps, q, gap))
        for e in lp.feed(s, {"guards": GUARDS_OK, "clock_ms": p["elapsed"]}):
            if e["event"] in ("transition", "hold"):
                fires.append((p["elapsed"], e.get("class"), e.get("from_kbps", e.get("level_kbps")),
                              e.get("to_kbps", e.get("would_target_kbps")), e["event"]))
            if e["event"] == "refused":
                refused[e["reason"]] += 1
        if lp.pending:
            lp.actuation_done(True, actual_kbps=lp.pending["to_kbps"])
        for e in sp.feed(s):
            if e["event"] == "would_act":
                shadow_fires.append((p["elapsed"], e["class"], e["from_kbps"], e["to_kbps"]))
    times = [f[0] for f in fires if f[4] == "transition"]
    max_win = 0
    for i, t in enumerate(times):
        max_win = max(max_win, sum(1 for u in times[i:] if u - t < live.RATE_LIMIT_WINDOW_MS))
    return fires, shadow_fires, max_win, lp.rate_limited_events, refused, lp.reports


def loss_replays(out_lines):
    out_lines.append("")
    out_lines.append("== 2. RECORDED LOSS: C4-D1 (82 heartbeat files) + CTRL-L1 (3 holds) through the live path")
    sessions = heartbeat_sessions()
    out_lines.append(f"sessions {len(sessions)} (rows deduplicated across files; companion logs cut at "
                     f"{C4_D1_CUTOFF_UTC}Z); with >= 5 intervals: {sum(1 for x in sessions if len(x['pts']) >= 5)}")
    summary = {}
    for variant in ("proxy", "bound"):
        tot = Counter()
        fire_rows, worst = [], 0
        for sess in sessions:
            pts = sess["pts"]
            if len(pts) >= 5:
                fires, sfires, max_win, rl, refused, reports = run_series(pts, variant)
                tot["series"] += 1
                tot["reports"] += reports
                tot["transitions"] += sum(1 for f in fires if f[4] == "transition")
                tot["holds"] += sum(1 for f in fires if f[4] == "hold")
                tot["rate_limited"] += rl
                tot["shadow_would_acts"] += len(sfires)
                worst = max(worst, max_win)
                for f in fires:
                    fire_rows.append(f"    {sess['label']} t={f[0] / 1000:8.1f}s "
                                     f"{f[4]:10s} {str(f[1]):8s} {f[2]} -> {f[3]}"
                                     + ("  [link drop (R3b, or P8 v1 B hit by R3b E30): live, recovery / pause guards block this]"
                                        if sess["deliberate_link_drop"] else ""))
        out_lines.append(f"-- variant {variant}: series {tot['series']}, reports {tot['reports']}, "
                         f"transitions {tot['transitions']}, oscillation holds {tot['holds']}, "
                         f"max transitions in any 10-min window {worst}, RATE_LIMITED {tot['rate_limited']} "
                         f"(shadow would-acts on the same series, ROUTINE included: {tot['shadow_would_acts']})")
        out_lines.append("   would-fire list (source, file#session, elapsed, event, class, from -> to):")
        out_lines.extend(fire_rows if fire_rows else ["    (none)"])
        summary[variant] = {"transitions": tot["transitions"], "max_window": worst,
                            "rate_limited": tot["rate_limited"], "series": tot["series"],
                            "reports": tot["reports"]}
    # How close the recorded fps ever came: longest run under 50 and under 57.
    runs50, runs57 = Counter(), Counter()
    for sess in sessions:
        if sess["deliberate_link_drop"]:
            continue
        for pts in (sess["pts"],):
            r50 = r57 = 0
            for p in pts:
                r50 = r50 + 1 if p["fps"] < 50 else 0
                r57 = r57 + 1 if p["fps"] < 57 else 0
                runs50[r50] += 1 if r50 else 0
                runs57[r57] += 1 if r57 else 0
    out_lines.append(f"   outside the link-drop sessions, longest run of consecutive reports under 50 fps: {max(runs50) if runs50 else 0}; "
                     f"under 57 fps: {max(runs57) if runs57 else 0} (FALLBACK needs 5 under 50; "
                     f"ROUTINE 4 of 5 under 57)")
    return summary


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVID / "c3_l4_l1_2026-09-28"
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["C3-L4-L1 offline replays through the live decision path",
             f"live constants: targets {live.TARGET_KBPS}; hold-downs {dict((f'{k[0]}/{k[1]}', v) for k, v in live.HOLDDOWN_REPORTS.items())}; "
             f"blackout {live.BLACKOUT_REPORTS}; increase after {live.CLEAN_REPORTS_FOR_INCREASE} clean; "
             f"rate limit {live.RATE_LIMIT_TRANSITIONS}/{live.RATE_LIMIT_WINDOW_MS // 60000} min; "
             f"session age {live.MIN_SESSION_AGE_MS // 1000} s; routine defer {live.ROUTINE_ESCALATION_DEFER_REPORTS}",
             ""]
    ok = parity(lines)
    summary = loss_replays(lines)
    text = "\n".join(lines) + "\n"
    (out_dir / "c3_l4_l1_replays.txt").write_text(text)
    print(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
