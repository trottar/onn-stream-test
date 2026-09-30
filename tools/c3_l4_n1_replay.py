#!/usr/bin/env python3
"""C3-L4-N1: every recorded series through the LIVE policy with the capacity
trigger and the recovery-escalation backstop. Read-only; offline.

    python3 tools/c3_l4_n1_replay.py [out_dir]

1. PARITY -- the C3-L4-S1 shadow night through live (tools/c3_l4_l1_replay.py,
   unchanged): must stay zero actions. Then the same rebuild WITH the shadow
   log's own `lost_packets_delta` (held between logged lines like every other
   field): the new rules' would-fire list.
2. EXACT -- every live `sample` row ever written (the companion's
   `logs/games/adaptive_bitrate_shadow.jsonl`; sample rows exist since
   C3-L4-L2: B2, the harness dry run, the L2B fake-sudo runs, night 1), split
   into sessions at `session_ended_reset`. Replayed OPEN-LOOP: fps, queue,
   gap, loss and freshness as recorded; recovery restarts from the log's
   `ssrc_change` rows (the clock from their `at_utc`); guards from the
   companion's recovery log (recovery PLAYING and not paused); the recorded
   controller transitions as blackouts; the disable route where it was
   called. A replayed transition is confirmed at once, but the data after it
   are still the recorded stream's: after a session's FIRST firing, later
   rows are a counterfactual (said so in the list).
3. HEARTBEATS -- every heartbeat row on disk (C4-D1's set incl. CTRL-L1, the
   companion's heartbeat log and its archive, every evidence heartbeat file),
   de-duplicated, split into sessions. C4-D1's proxies (fps from rendered
   frames, queue = frames queued but not rendered in the interval, gap = the
   output age at the row) and the LOSS PROXY: `lost_packets` delta between
   rows (the heartbeat's cumulative post-FEC count; absent from older
   schemas -> no loss -> capacity cannot fire there, counted). The would-fire
   list with each firing's trigger; and, independent of the controller's
   state, every 5-report window that meets the capacity bar.
4. BACKSTOP -- every recovery `encoder_restart` on disk (the companion's
   recovery log since 2026-09-20 and the evidence copies before it): every
   pair at one level within 180 s, with the session's cause.

STOP RULE (handoff section 3): if either new rule fires on a clean-link
session outside a deliberate fault or a recorded link drop, stop before any
session. This tool prints the verdict; it never retunes.
"""

from __future__ import annotations

import glob
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import c3_l4_l1_replay as l1  # noqa: E402

EVID = REPO / "docs" / "memory" / "evidence"
GAMES = REPO / "logs" / "games"
NEW = (live.TRIGGER_CAPACITY, live.TRIGGER_ESCALATION)

# Deliberate faults and recorded link drops (UTC windows), from their records.
NIGHT1 = ("2026-09-29T15:19:42", "2026-09-29T16:16:56")
DELIBERATE = [
    ("2026-09-20T00:00:00", "2026-09-20T23:59:59", "D-BASE-R3 / R3a / R4 substitute faults (SIGSTOP, K70)"),
    ("2026-09-22T15:15:00", "2026-09-22T15:25:00", "D-BASE-R3b N150 nft link drop"),
    ("2026-09-22T23:36:00", "2026-09-22T23:42:00", "D-BASE-P8 v1 arm B, hit by R3b E30"),
    ("2026-09-23T02:26:00", "2026-09-23T03:05:00", "D-BASE-R3b E30 nft link drop"),
    (NIGHT1[0], NIGHT1[1], "C3-L4 nft night 1 (F1 / F3 / K caps, F2 loss, F3 drop)"),
]


def ts(t: str) -> float:
    return datetime.strptime(t[:23].ljust(23, "0"), "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()


def deliberate(t: str) -> str | None:
    for a, b, what in DELIBERATE:
        if a <= t[:19] <= b:
            return what
    return None


def jl(path: Path) -> list[dict]:
    out = []
    if not path.exists():
        return out
    for line in path.read_text(errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


# ------------------------------------------------------------ recovery log ---
def recovery_rows() -> list[dict]:
    rows = {}
    paths = [GAMES / "native_stream_recovery.log"] + sorted(GAMES.glob("stream_log_archive/native_stream_recovery*"))
    paths += [Path(p) for p in glob.glob(str(EVID / "**" / "*recovery*log*"), recursive=True)]
    paths += [Path(p) for p in glob.glob(str(EVID / "**" / "recovery_log*.jsonl"), recursive=True)]
    for p in paths:
        for r in jl(p):
            if r.get("at_utc") and r.get("event"):
                rows[(r["at_utc"], r["event"])] = r
    return sorted(rows.values(), key=lambda r: r["at_utc"])


class RecoveryTimeline:
    def __init__(self, rows):
        self.rows = rows
        self.times = [ts(r["at_utc"]) for r in rows]

    def state_at(self, t: float) -> str | None:
        import bisect
        i = bisect.bisect_right(self.times, t) - 1
        return self.rows[i].get("state") if i >= 0 else None


# ------------------------------------------------------------- 1. parity ---
def parity_with_loss(lines):
    path = EVID / "c3_l4_s1_2026-09-24" / "shadow_log.jsonl"
    sessions, _ = l1.rebuild_shadow_night(path)
    fires, total, with_loss = [], 0, 0
    for si, series in enumerate(sessions, 1):
        lp = live.LivePolicy()
        for elapsed, smp, _logged in series:
            total += 1
            lost = smp.get("lost_packets_delta")
            with_loss += lost is not None
            t = l1.tel(int(elapsed), smp.get("fps"), smp.get("queue_depth"), smp.get("output_gap_ms"),
                       bool(smp.get("waiting_for_idr")))
            t["receiver"]["lost_packets_delta"] = lost
            for e in lp.feed(ab._sample(t), {"guards": l1.GUARDS_OK, "clock_ms": int(elapsed)}):
                if e["event"] in ("transition", "would_act", "hold", "refused"):
                    fires.append((si, int(elapsed), e["event"], e.get("class"), e.get("trigger"), e.get("reason")))
            if lp.pending:
                lp.actuation_done(True, actual_kbps=lp.pending["to_kbps"])
    lines.append(f"   with the logged loss: {total} rebuilt reports, {with_loss} carrying a loss delta; "
                 f"decisions {len(fires)}; new-rule decisions {sum(1 for f in fires if f[4] in NEW)}")
    for f in fires:
        lines.append(f"      session {f[0]} t={f[1] / 1000:.1f}s {f[2]} {f[3]} trigger {f[4]} reason {f[5]}")
    return [f for f in fires if f[4] in NEW]


# -------------------------------------------------------------- 2. exact ---
def live_log_rows() -> list[dict]:
    rows = {}
    paths = [GAMES / ab.LOG_NAME] + sorted(GAMES.glob(f"stream_log_archive/{ab.LOG_NAME}*"))
    for p in paths:
        for r in jl(p):
            if r.get("mode") == "live" and r.get("at_utc"):
                rows[(r["at_utc"], r.get("event"), r.get("session_elapsed_ms"))] = r
    return sorted(rows.values(), key=lambda r: r["at_utc"])


def exact_sessions(rows):
    sessions, cur = [], []
    for r in rows:
        if r.get("event") in ("session_ended_reset", "controller_start"):
            if any(x.get("event") == "sample" for x in cur):
                sessions.append(cur)
            cur = []
            continue
        cur.append(r)
    if any(x.get("event") == "sample" for x in cur):
        sessions.append(cur)
    return sessions


def night1_phases():
    ev = jl(EVID / "c3_l4_nft_night1_2026-09-29" / "events.jsonl")
    ph = []
    for e in ev:
        if e["event"] in ("fault_on", "fault_off", "disable", "playing", "back"):
            ph.append((e["at_utc"], e["session"], e["event"], e.get("what")))
    return ph


def label_exact(t: str, phases) -> str:
    if NIGHT1[0] <= t[:19] <= NIGHT1[1]:
        last_on = None
        sess = None
        for at, s, what, w in phases:
            if at > t:
                break
            if what == "playing":
                sess, last_on = s, None
            if what == "fault_on" and w != "calibration counter":
                last_on = (at, w)
            if what == "fault_off":
                last_on = None
        if last_on:
            return f"night 1 {sess}, {last_on[1]} +{ts(t) - ts(last_on[0]):.1f} s"
        return f"night 1 {sess}, no fault on"
    if "2026-09-29T03:28" <= t[:16] <= "2026-09-29T03:57":
        return "C3-L4-L2 session B2 (clean link, injected + blend climb)"
    if "2026-09-29T03:58" <= t[:16] <= "2026-09-29T04:14":
        return "C3-L4-L2 harness dry run (no fault)"
    if "2026-09-29T14:20" <= t[:16] <= "2026-09-29T15:14":
        return "C3-L4-L2B fake-sudo runs (no fault)"
    return "other"


def run_exact(lines, rec: RecoveryTimeline):
    rows = live_log_rows()
    sessions = exact_sessions(rows)
    phases = night1_phases()
    all_fires = []
    lines.append(f"sources: the companion's live log (+ archive): {len(rows)} live rows, "
                 f"{sum(1 for r in rows if r.get('event') == 'sample')} sample rows, {len(sessions)} sessions with samples")
    for si, sess in enumerate(sessions, 1):
        lp = live.LivePolicy()
        first = sess[0]["at_utc"]
        n_samples = sum(1 for r in sess if r.get("event") == "sample")
        fires = []
        first_fire_at = None
        for r in sess:
            ev = r.get("event")
            t = ts(r["at_utc"])
            clock = int(t * 1000)
            if ev == "ssrc_change":
                out = lp.note_ssrc_change(r.get("source") or "recovery_restart", clock_ms=clock)
                for e in out:
                    if e["event"] == "escalation_armed":
                        cf = "" if first_fire_at is None else "[counterfactual: after the first firing]"
                        fires.append((r["at_utc"], "escalation_armed", None, None, e["level_kbps"], None, cf))
                continue
            if ev == "transition_done":
                lp.note_ssrc_change("controller_transition")       # the recorded change: a blackout, no clock
                continue
            if ev == "disabled":
                lp.acting = False
                continue
            if ev != "sample":
                continue
            st = rec.state_at(t)
            guards = dict(l1.GUARDS_OK, recovery_playing=(st == "PLAYING"), game_not_paused=(st == "PLAYING"))
            tele = {"available": True, "fresh": bool(r.get("fresh")), "session_elapsed_ms": r.get("session_elapsed_ms"),
                    "receiver": {"recent_fps": r.get("fps"), "waiting_for_idr": r.get("waiting_for_idr"),
                                 "lost_packets_delta": r.get("lost_packets_delta")},
                    "decoder": {"queue_depth": r.get("queue_depth")},
                    "latency": {"output_gap_ms": r.get("output_gap_ms")}, "fec": {}}
            for e in lp.feed(ab._sample(tele), {"guards": guards, "clock_ms": clock}):
                if e["event"] in ("transition", "would_act", "hold", "refused"):
                    cf = "" if first_fire_at is None else " [counterfactual: after the first firing]"
                    fires.append((r["at_utc"], e["event"], e.get("class"), e.get("trigger"),
                                  e.get("from_kbps", e.get("level_kbps")), e.get("to_kbps", e.get("would_target_kbps")),
                                  (e.get("reason") or "") + cf))
                    if e["event"] in ("transition", "would_act") and first_fire_at is None:
                        first_fire_at = r["at_utc"]
            if lp.pending:
                lp.actuation_done(True, actual_kbps=lp.pending["to_kbps"])
        lab = label_exact(first, phases)
        lines.append(f"  session {si}: {first[:19]}Z, {n_samples} sample rows -- {lab}")
        for f in fires:
            lines.append(f"      {f[0][11:23]}Z {f[1]:16s} {str(f[2]):8s} trigger {str(f[3]):20s} "
                         f"{f[4]} -> {f[5]} {f[6]}  [{label_exact(f[0], phases)}]")
            all_fires.append((si, lab, f))
    return all_fires


# --------------------------------------------------------- 3. heartbeats ---
def heartbeat_paths():
    paths = [(src, p) for src, p in l1.heartbeat_files()]
    paths += [("companion", GAMES / "native_stream_heartbeat.log")]
    paths += [("companion", Path(p)) for p in sorted(glob.glob(str(GAMES / "stream_log_archive" / "native_stream_heartbeat.log*")))]
    seen = {str(p) for _, p in paths}
    for p in sorted(glob.glob(str(EVID / "**" / "*heartbeat*.jsonl"), recursive=True)):
        if p not in seen:
            paths.append(("evidence", Path(p)))
    for p in sorted(glob.glob(str(REPO / "logs" / "streaming" / "**" / "heartbeat*.jsonl"), recursive=True)):
        if p not in seen:
            paths.append(("run dir", Path(p)))
    return paths


def heartbeat_sessions():
    rows = {}
    for src, path in heartbeat_paths():
        if not path.exists():
            continue
        lab = l1._label(path) if str(path).startswith(str(REPO)) else str(path)
        for r in jl(path):
            at = r.get("received_at_utc") or ""
            if not isinstance(r.get("elapsed_ms"), (int, float)) or not at:
                continue
            key = (at, r.get("sequence"), r.get("elapsed_ms"))
            prev = rows.get(key)
            if prev is None or (prev[0] == "companion" and src != "companion"):
                rows[key] = (src, lab, r)
    ordered = sorted(rows.values(), key=lambda x: x[2]["received_at_utc"])
    sessions, cur = [], []
    for item in ordered:
        r = item[2]
        if cur and (r["elapsed_ms"] <= cur[-1][2]["elapsed_ms"]
                    or ts(r["received_at_utc"]) - ts(cur[-1][2]["received_at_utc"]) > 30):
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
            if dt <= 0 or not all(isinstance(x.get("rendered_frames"), (int, float)) for x in (a, b)):
                continue
            fps = max(0.0, (b["rendered_frames"] - a["rendered_frames"]) * 1000.0 / dt)
            qproxy = None
            if all(isinstance(x.get("queued_frames"), (int, float)) for x in (a, b)):
                qproxy = max(0, (b["queued_frames"] - a["queued_frames"]) - (b["rendered_frames"] - a["rendered_frames"]))
            lost = None
            if all(isinstance(x.get("lost_packets"), (int, float)) for x in (a, b)):
                lost = max(0, b["lost_packets"] - a["lost_packets"])
            resync = None
            if all(isinstance(x.get("stream_resyncs"), (int, float)) for x in (a, b)):
                resync = max(0, b["stream_resyncs"] - a["stream_resyncs"])
            pts.append({"elapsed": int(b["elapsed_ms"]), "at": b["received_at_utc"], "fps": round(fps, 2),
                        "age": b.get("last_output_age_ms"), "q": qproxy, "lost": lost, "resync": resync})
        files = Counter(x[1] for x in sess if x[0] != "companion")
        start = rs[0]["received_at_utc"]
        known = label_exact(start, []) if start[:10] == "2026-09-29" else "other"
        label = f"{start[:19]}Z " + (files.most_common(1)[0][0] if files else "companion heartbeat log only") \
            + ("" if known in ("other",) or known.startswith("night 1") else f" ({known})")
        drop = any("d_base_r3b" in f or "R3b" in f or "d_base_p8_2026-09-22/runs_v1/heartbeat_B" in f for f in files)
        out.append({"label": label, "pts": pts, "start": start, "end": rs[-1]["received_at_utc"],
                    "deliberate": deliberate(start) or deliberate(rs[-1]["received_at_utc"])
                    or ("recorded link drop (file)" if drop else None)})
    return out


def run_heartbeats(lines, rec: RecoveryTimeline):
    sessions = [s for s in heartbeat_sessions() if len(s["pts"]) >= 5]
    tot = Counter()
    fire_rows, raw_rows, new_fires = [], [], []
    for sess in sessions:
        lp = live.LivePolicy()
        run = []
        for p in sess["pts"]:
            tot["reports"] += 1
            tot["with_loss"] += p["lost"] is not None
            age = p["age"] if isinstance(p["age"], (int, float)) else None
            t = ts(p["at"])
            st = rec.state_at(t)
            playing = st in (None, "PLAYING", "ENDED")
            tele = l1.tel(p["elapsed"], p["fps"], p.get("q"), age)
            tele["receiver"]["lost_packets_delta"] = p["lost"]
            for e in lp.feed(ab._sample(tele), {"guards": dict(l1.GUARDS_OK, recovery_playing=playing,
                                                                game_not_paused=playing),
                                                  "clock_ms": int(t * 1000)}):
                if e["event"] in ("transition", "hold") or (e["event"] == "refused" and e.get("trigger") in NEW):
                    row = (sess["label"], p["elapsed"], e["event"], e.get("class"), e.get("trigger"),
                           e.get("from_kbps", e.get("level_kbps")), e.get("to_kbps", e.get("would_target_kbps")),
                           e.get("reason"), sess["deliberate"], p["at"])
                    fire_rows.append(row)
                    if e.get("trigger") in NEW:
                        new_fires.append(row)
            if lp.pending:
                lp.actuation_done(True, actual_kbps=lp.pending["to_kbps"])
            # the raw capacity bar, whatever the controller's state
            run.append(p)
            w = run[-5:]
            if len(w) == 5 and all(x["fps"] < live.CAPACITY_FPS_BELOW for x in w) \
                    and sum(1 for x in w if x["lost"] is not None and x["lost"] >= live.CAPACITY_LOSS_AT_LEAST) \
                    >= live.CAPACITY_LOSS_OF:
                raw_rows.append((sess["label"], p["elapsed"], [x["fps"] for x in w], [x["lost"] for x in w],
                                 [x["resync"] for x in w], sess["deliberate"], p["at"]))
        tot["series"] += 1
        tot["series_with_loss"] += any(p["lost"] is not None for p in sess["pts"])
    lines.append(f"sessions {tot['series']} (>= 5 intervals), reports {tot['reports']}; reports with a loss delta "
                 f"{tot['with_loss']} ({100 * tot['with_loss'] / max(1, tot['reports']):.1f} %), in "
                 f"{tot['series_with_loss']} sessions (older heartbeat schemas carry no lost_packets)")
    lines.append("   would-fire list, every trigger (label, elapsed, event, class, trigger, from -> to, reason, cause):")
    for f in fire_rows:
        lines.append(f"      {f[0]} t={f[1] / 1000:8.1f}s {f[2]:10s} {str(f[3]):8s} {str(f[4]):20s} {f[5]} -> {f[6]} "
                     f"{f[7]}  [{f[8] or 'clean-link / no recorded fault'}]")
    if not fire_rows:
        lines.append("      (none)")
    lines.append(f"   raw capacity windows (5 consecutive reports at fps < 50 with >= 3 at lost >= 50), "
                 f"whatever the controller state: {len(raw_rows)}")
    by_sess = defaultdict(list)
    for r in raw_rows:
        by_sess[(r[0], r[5])].append(r)
    for (lab, cause), rs in by_sess.items():
        r0 = rs[0]
        lines.append(f"      {lab}: {len(rs)} windows, first at t={r0[1] / 1000:.1f}s ({r0[6][11:19]}Z) fps {r0[2]} "
                     f"lost {r0[3]} resyncs {r0[4]}  [{cause or 'clean-link / no recorded fault'}]")
    return new_fires, raw_rows


# ------------------------------------------------------------ 4. backstop ---
def run_backstop(lines, rows):
    sess_no, per = 0, defaultdict(list)
    for r in rows:
        if r["event"] == "session_started":
            sess_no += 1
        if r["event"] == "encoder_restart":
            per[sess_no].append(r)
    arms = []
    for s, ers in per.items():
        for a, b in zip(ers, ers[1:]):
            gap = ts(b["at_utc"]) - ts(a["at_utc"])
            if gap <= live.ESCALATION_WINDOW_MS / 1000:
                arms.append((s, a["at_utc"], b["at_utc"], round(gap, 1), deliberate(b["at_utc"])))
    lines.append(f"recovery rows on disk {len(rows)} ({rows[0]['at_utc'][:19]}Z .. {rows[-1]['at_utc'][:19]}Z); "
                 f"encoder_restart {sum(len(v) for v in per.values())} in {len(per)} sessions; consecutive pairs "
                 f"within {live.ESCALATION_WINDOW_MS // 1000} s: {len(arms)}")
    lines.append("   (the level of each restart: recovery restarted at 7000 in every one of these sessions -- before "
                 "C3-F1 always, and after it no controller had moved the level -- so every pair is 'at one level')")
    for a in arms:
        lines.append(f"      restart {a[1][:19]}Z then {a[2][11:19]}Z ({a[3]} s)  [{a[4] or 'CLEAN LINK -- NO RECORDED FAULT'}]")
    return arms


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else EVID / "c3_l4_n1_2026-09-29"
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = ["C3-L4-N1 replays: the live policy with the capacity trigger and the recovery-escalation backstop",
             f"capacity: fps < {live.CAPACITY_FPS_BELOW:g} on all {ab.WINDOW_REPORTS} and lost >= "
             f"{live.CAPACITY_LOSS_AT_LEAST} on >= {live.CAPACITY_LOSS_OF}; backstop: {live.ESCALATION_RESTARTS} "
             f"restarts at one level within {live.ESCALATION_WINDOW_MS // 1000} s; everything else as C3-L4-L2", ""]
    rec_rows = recovery_rows()
    rec = RecoveryTimeline(rec_rows)
    lines.append("== 1. PARITY (tools/c3_l4_l1_replay.py's parity, the new policy)")
    ok = l1.parity(lines)
    s1_new = parity_with_loss(lines)
    lines.append("")
    lines.append("== 2. EXACT: every live sample row, open-loop")
    exact = run_exact(lines, rec)
    lines.append("")
    lines.append("== 3. HEARTBEATS: every heartbeat series, C4-D1 proxies + the loss proxy")
    hb_new, raw = run_heartbeats(lines, rec)
    lines.append("")
    lines.append("== 4. BACKSTOP: every recovery encoder_restart on disk")
    arms = run_backstop(lines, rec_rows)
    lines.append("")
    clean_exact = [f for f in exact if f[2][3] in NEW and not f[1].startswith("night 1")]
    clean_hb = [f for f in hb_new if not f[8]]
    clean_raw = [r for r in raw if not r[5]]
    clean_arms = [a for a in arms if not a[4]]
    lines.append("== STOP RULE (a new rule firing on a clean-link session outside a deliberate fault or a recorded link drop)")
    lines.append(f"   parity (zero actions): {'MET' if ok else 'NOT MET'}; S1 with loss, new-rule decisions: {len(s1_new)}")
    lines.append(f"   exact sessions outside night 1, new-rule decisions: {len(clean_exact)}")
    lines.append(f"   heartbeat sessions without a recorded fault, new-rule decisions: {len(clean_hb)}; raw capacity "
                 f"windows: {len(clean_raw)}")
    lines.append(f"   recovery restart pairs outside a recorded fault: {len(clean_arms)}")
    fired = bool(s1_new or clean_exact or clean_hb or clean_arms or not ok)
    lines.append(f"   -> {'STOP: record with the samples; the user decides' if fired else 'PASS: neither rule fires on a clean link'}")
    text = "\n".join(lines) + "\n"
    (out_dir / "c3_l4_n1_replays.txt").write_text(text)
    print(text)
    return 1 if fired else 0


if __name__ == "__main__":
    sys.exit(main())
