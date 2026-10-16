#!/usr/bin/env python3
"""G5-S2: the replay harness. Read-only; offline; no stream.

    python3 docs/memory/evidence/g5_s2_2026-10-16/replay.py [out_dir]

For each named run, its whole stream session is taken from the live ladder's
log (logs/games/adaptive_bitrate_shadow.jsonl and its archives; the run's own
decisions.jsonl starts mid-session). Recovery's state per report comes from
the recovery logs (tools/c3_l4_n2_replay.RecoveryTimeline).

1. FLAG ABSENT, THE RECORDED DECISIONS. Every report is fed through the entry
   the hook uses when the flag is absent (`policy.feed`), in the recorded
   order. SSRC changes and actuation completions are applied where the log
   recorded them. Every recorded sample row's decision fields and every
   recorded decision event must be reproduced exactly.
2. FLAG ABSENT, THE CONTROLLER IN PROCESS. HEAD's adaptive_bitrate_live.py
   (from git) and the edited one (the hook present) are driven through
   `LiveController.observe` / `note_recovery_restart` with the same inputs: a
   synchronous actuator, a temporary log. Every row written must be
   identical, apart from `at_utc` and the actuation duration.
3. FLAG PRESENT. The same reports through `WanAdaptation.feed`, read as LAN (as
   recorded) and as a remote path. Per run, tabulated:
   - suggestions by rule;
   - ticks where the ladder's decision differs from the recorded one;
   - whether R5 allowed the rung back;
   - whether the remote floor would have engaged.
   The replay is open loop: later reports are the recorded ones, which the
   changed decisions would themselves have changed. **No claim of
   improvement.**
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))

import adaptive_bitrate as ab  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402
import c3_l4_n2_replay as n2  # noqa: E402
import c3_l4_l1_replay as l1  # noqa: E402
import wan_adaptation as wa  # noqa: E402

EVID = REPO / "docs" / "memory" / "evidence"
RUNS = [
    ("e4_s4b run3 (lossy)", EVID / "e4_s4b_2026-10-10/runs/E1-PS1-STREAM/run3"),
    ("e4_s4b run2 (cleanest)", EVID / "e4_s4b_2026-10-10/runs/E1-PS1-STREAM/run2"),
    ("cl_b3 run1 (today's best link)", EVID / "cl_b3_2026-10-16/runs/E1-PS1-STREAM/run1"),
    ("e4_s4 E1-CONC_flag run1 (grab bursts)", EVID / "e4_s4_2026-10-10/runs/E1-CONC_flag/run1"),
]
SAMPLE_FIELDS = ("disposition", "clean", "window_reports", "window_clean", "state", "reason",
                 "level_kbps", "blackout_remaining", "holds", "escalation_armed")
CONTROLLER_ROWS = ("transition_done", "transition_aborted", "actuator_failed", "controller_start",
                   "inject", "disabled", "session_ended_reset")
DECISIONS = ("transition", "would_act", "refused", "hold")


def jl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()] if path.exists() else []


def session_for(run_dir: Path, sessions: list[list[dict]]) -> list[dict]:
    first = next(r for r in jl(run_dir / "decisions.jsonl") if r.get("event") == "sample")["at_utc"]
    for s in sessions:
        if s[0]["at_utc"] <= first <= s[-1]["at_utc"]:
            return s
    raise SystemExit(f"no live-log session holds {run_dir}")


def stale_by_elapsed(run_dir: Path) -> dict[int, int]:
    out = {}
    for r in jl(run_dir / "telemetry.jsonl"):
        el = r.get("elapsed_ms")
        st = (r.get("decoder") or {}).get("stale_output_drops_delta")
        if isinstance(el, (int, float)) and isinstance(st, (int, float)):
            out[int(el)] = int(st)
    return out


def tel_from_sample(r: dict, stale: dict[int, int]) -> dict:
    t = {"available": True, "fresh": bool(r.get("fresh")), "session_elapsed_ms": r.get("session_elapsed_ms"),
         "receiver": {"recent_fps": r.get("fps"), "waiting_for_idr": r.get("waiting_for_idr"),
                      "lost_packets_delta": r.get("lost_packets_delta")},
         "decoder": {"queue_depth": r.get("queue_depth")},
         "latency": {"output_gap_ms": r.get("output_gap_ms")}, "fec": {}}
    el = r.get("session_elapsed_ms")
    if isinstance(el, (int, float)) and int(el) in stale:
        t["decoder"]["stale_output_drops_delta"] = stale[int(el)]
    return t


def guards_at(rec, t: float) -> dict:
    st = rec.state_at(t)
    return dict(l1.GUARDS_OK, recovery_playing=(st == "PLAYING"), game_not_paused=(st == "PLAYING"))


def canon(o) -> str:
    return json.dumps(o, sort_keys=True, default=str)


# ------------------------------------------------------------ 1. recorded ---
def replay_recorded(sess, rec, stale, feed, policy=None, path_ctx=None):
    """Drive one session; return (mismatches, decisions, suggestions, counts)."""
    p = policy or live.LivePolicy()
    mism, decisions, suggestions = [], [], []
    expected: list[dict] = []          # recorded decision rows, in order
    produced: list[dict] = []          # the policy's decision events, in order
    samples = 0
    for r in sess:
        ev = r.get("event")
        t = n2.ts(r["at_utc"])
        clock = int(t * 1000)
        if ev == "sample":
            if r.get("disposition") == "dropped_actuating":
                continue
            samples += 1
            ctx = {"guards": guards_at(rec, t), "clock_ms": clock, "stream_kbps": r.get("stream_kbps"),
                   **(path_ctx or {})}
            tel = tel_from_sample(r, stale)
            evs = feed(p, ab._sample(tel), ctx, tel)
            got = {"disposition": p.last_disposition, "clean": p.last_clean, "window_reports": len(p.inc_window),
                   "window_clean": p.clean_count, "state": p.state, "reason": p.reason, "level_kbps": p.level_kbps,
                   "blackout_remaining": p.blackout_remaining,
                   "holds": {"fallback": p.hold_left("FALLBACK"), "routine": p.hold_left("ROUTINE"),
                             "increase": p.hold_left("INCREASE")},
                   "escalation_armed": p.escalation is not None}
            want = {k: r.get(k) for k in SAMPLE_FIELDS}
            if canon(got) != canon(want):
                mism.append(("sample", r["at_utc"], {k: (want[k], got[k]) for k in SAMPLE_FIELDS
                                                     if canon(want[k]) != canon(got[k])}))
            for e in evs:
                if e.get("event") == "state" and e.get("from") == e.get("to"):
                    continue
                if e.get("event") == "wan_suggestion":
                    suggestions.append((r.get("session_elapsed_ms"), e))
                    continue
                produced.append(e)
                if e.get("event") in DECISIONS:
                    decisions.append((r.get("session_elapsed_ms"), e))
        elif ev == "ssrc_change":
            for e in p.note_ssrc_change(r.get("source") or "recovery_restart", clock_ms=clock):
                produced.append(e)
            expected.append(r)
        elif ev in ("transition_done", "transition_aborted", "actuator_failed"):
            if p.pending is not None:
                p.actuation_done(ev == "transition_done", actual_kbps=r.get("level_kbps") or r.get("to_kbps"),
                                 aborted=ev == "transition_aborted")
        elif ev == "disabled":
            p.acting = False
        elif ev in CONTROLLER_ROWS:
            pass
        else:
            expected.append(r)
    # the decision / state events, in order: every key the policy emitted must equal the recorded row's
    for i in range(max(len(expected), len(produced))):
        e = produced[i] if i < len(produced) else None
        w = expected[i] if i < len(expected) else None
        if e is None or w is None or any(canon(w.get(k)) != canon(v) for k, v in e.items()):
            mism.append(("event", i, {"recorded": w and {k: w.get(k) for k in ("at_utc", "event", "from", "to",
                                                                               "reason", "class")},
                                      "replayed": e and {k: e.get(k) for k in ("event", "from", "to", "reason", "class")}}))
            break
    return mism, decisions, suggestions, {"samples": samples, "events": len(expected)}


def flag_absent_feed(policy, s, ctx, tel):
    return policy.feed(s, ctx)      # what the hook runs when WAN_ADAPTATION is None


# ------------------------------------------------------- 2. the controller ---
def load_head_module():
    src = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:companion/adaptive_bitrate_live.py"],
                         capture_output=True, text=True, check=True).stdout
    p = Path(tempfile.mkdtemp(prefix="g5_s2_head_")) / "adaptive_bitrate_live_head.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location("adaptive_bitrate_live_head", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _SyncThread:
    def __init__(self, target, args=(), **kw):
        self._t, self._a = target, args

    def start(self):
        self._t(*self._a)


def drive_controller(mod, sess, rec, stale) -> list[str]:
    root = Path(tempfile.mkdtemp(prefix="g5_s2_ctl_"))
    mod.threading = types.SimpleNamespace(Thread=_SyncThread, RLock=mod.threading.RLock)
    state = {"recovery": "PLAYING", "t": 0.0}
    # the replayed clock: the log's own time, so both controllers see the same gaps
    mod.time = types.SimpleNamespace(monotonic=lambda: state["t"], time=lambda: state["t"])
    c = mod.LiveController(root, environ={})
    c.bind(actuator=lambda kbps: {"ok": True, "target_bitrate_kbps": kbps},
           context=lambda: {"game_active": True, "game_paused": False, "recovery_state": state["recovery"]},
           serial_lock=None, recovery_state=lambda: state["recovery"])
    for r in sess:
        ev = r.get("event")
        t = n2.ts(r["at_utc"])
        state["t"] = t
        state["recovery"] = rec.state_at(t) or "PLAYING"
        if ev == "sample" and r.get("disposition") != "dropped_actuating":
            kbps = r.get("stream_kbps")
            ns = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID,
                  "profile": {"bitrate_kbps": live.REFERENCE_KBPS}, "encoder_overrides": {"any_override": False},
                  "bitrate_kbps": kbps}
            c.observe(tel_from_sample(r, stale), stream_bitrate_kbps=kbps, native_status=ns)
        elif ev == "ssrc_change":
            c.note_recovery_restart(r.get("source") or "recovery_restart")
    rows = []
    for line in c.log_path.read_text().splitlines():
        row = json.loads(line)
        row.pop("at_utc", None)
        row.pop("actuation_ms", None)
        rows.append(canon(row))
    return rows


# ------------------------------------------------------------------ main ---
def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = n2.RecoveryTimeline(n2.recovery_rows())
    sessions = n2.exact_sessions(n2.live_log_rows())
    head = load_head_module()
    lines = ["G5-S2 replay over the four named runs (whole sessions from the live log)", ""]
    table = {}
    ok_all = True
    lines.append("## 1-2. Flag absent")
    lines.append("")
    lines.append("| run | session reports | recorded decision / state events | 1. recorded reproduced | "
                 "2. controller HEAD vs edited (rows) |")
    lines.append("| --- | --- | --- | --- | --- |")
    per_run = []
    for label, d in RUNS:
        sess = session_for(d, sessions)
        stale = stale_by_elapsed(d)
        mism, decs, _, cnt = replay_recorded(sess, rec, stale, flag_absent_feed)
        a = drive_controller(head, sess, rec, stale)
        b = drive_controller(live, sess, rec, stale)
        same = a == b
        ok = not mism and same
        ok_all &= ok
        lines.append(f"| {label} | {cnt['samples']} | {cnt['events']} | "
                     f"{'exact' if not mism else f'{len(mism)} MISMATCH'} | "
                     f"{'identical' if same else 'DIFFER'} ({len(a)} rows) |")
        if mism:
            for m in mism[:5]:
                lines.append(f"    mismatch: {m}")
        per_run.append((label, d, sess, stale, decs))
    lines.append("")
    lines.append(f"-> flag absent: {'PASS' if ok_all else 'FAIL'}")
    lines.append("")
    lines.append("## 3. Flag present (`WanAdaptation.feed`), open loop; no claim of improvement")
    lines.append("")
    for path_label, path_ctx in (("LAN (as recorded)", {}), ("read as remote", {"path_class": "remote"})):
        lines.append(f"### {path_label}")
        lines.append("")
        lines.append("| run | ticks with a suggestion | by rule | ladder decisions changed | blocked increases | "
                     "forced step-downs (taken / refused) | R5 let the rung back | remote floor would engage |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for label, d, sess, stale, recorded_decs in per_run:
            adapt = wa.WanAdaptation()
            _, decs, sugg, _ = replay_recorded(sess, rec, stale, adapt.feed, path_ctx=path_ctx)
            by_rule: dict[str, int] = {}
            for _, e in sugg:
                by_rule[e["rule"]] = by_rule.get(e["rule"], 0) + 1
            rec_set = {(el, e.get("event"), e.get("class"), e.get("to_kbps")) for el, e in recorded_decs
                       if e.get("event") in ("transition", "hold")}
            new_set = {(el, e.get("event"), e.get("class"), e.get("to_kbps")) for el, e in decs
                       if e.get("event") in ("transition", "hold")}
            changed = len(rec_set ^ new_set)
            blocked = sum(1 for _, e in sugg if e["ladder_result"] == "blocked_increase")
            forced_t = sum(1 for _, e in decs if e.get("reason") == wa.SOURCE and e.get("event") == "transition")
            forced_r = sum(1 for _, e in decs if e.get("trigger") == wa.SOURCE and e.get("event") == "refused")
            down = any(e.get("direction") == "down" for _, e in decs if e.get("event") == "transition")
            up_after = any(e.get("direction") == "up" for _, e in decs if e.get("event") == "transition")
            r5 = ("yes" if up_after else "no") if down else "n/a (never below the reference)"
            floor = sum(1 for _, e in sugg if e["suggestion"] == "floor_4000")
            lines.append(f"| {label} | {len(sugg)} | {', '.join(f'{k} {v}' for k, v in sorted(by_rule.items())) or '—'} "
                         f"| {changed} | {blocked} | {forced_t} / {forced_r} | {r5} | "
                         f"{'yes (' + str(floor) + ' ticks)' if floor else 'no'} |")
            table[f"{label} / {path_label}"] = {
                "suggestions": len(sugg), "by_rule": by_rule, "decisions_changed": changed,
                "blocked_increases": blocked, "forced_step_downs": [forced_t, forced_r],
                "r5_recovered": r5, "floor_4000_ticks": floor,
                "transitions": [(el, e.get("class"), e.get("from_kbps"), e.get("to_kbps"), e.get("reason"))
                                for el, e in decs if e.get("event") == "transition"],
                "recorded_transitions": [(el, e.get("class"), e.get("from_kbps"), e.get("to_kbps"), e.get("reason"))
                                         for el, e in recorded_decs if e.get("event") == "transition"]}
        lines.append("")
    lines.append(f"R4: {wa.R4_NOTE}; no suggestion is FEC-related.")
    (out_dir / "replay_output.md").write_text("\n".join(lines) + "\n")
    (out_dir / "replay_tables.json").write_text(json.dumps(table, indent=1, default=str) + "\n")
    print("\n".join(lines))
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent))
