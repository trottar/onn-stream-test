#!/usr/bin/env python3
"""G5-S3: the flag-present replay. Read-only; offline; no stream.

    PYTHONDONTWRITEBYTECODE=1 python3 docs/memory/evidence/g5_s3_2026-10-17/replay.py [out_dir]

The runs: G5-S2's four (whole sessions from the live log, as G5-S2's replay takes
them) and G4-S1's run 1 and run 2 (every live-log session whose reports fall in
the run: their first report between PLAYING and the window's end). Inputs per report are G5-S2's: the
ladder's own recorded sample row (fps, queue, gap, loss, resync, freshness) plus
the run's stale-output drops; recovery's state from the recovery logs.

`path_class` per session:
- G5-S2's four: `lan`, as recorded (LAN runs); and, hypothetically, read as
  `remote` (the same reports, the class forced) -- labelled as such;
- G4-S1: from the session's setup, the routing evidence of the last
  `token_issued` before the session's first report (G4-S1's reduced audit in
  `g4_s1_read.json`): run 1 `overlay` -> `remote`; run 2 `overlay` -> `remote` to
  the hotspot toggle, then the 23:15:01Z LAN setup -> `lan`.

0. FLAG ABSENT on G4-S1's sessions: G5-S2's `replay_recorded` (the policy's plain
   `feed`) must reproduce the recorded decisions exactly (an extra check; G5-S2's
   four are re-run by `flag_absent_proof.py`).
1. FLAG PRESENT: the edited `LiveController` in process (`observe`,
   `note_recovery_restart`, `session_ended`), its globals set as the flag would
   (one `RemoteLadder` shared with `wan_adaptation` and the actuator probe), the
   replayed clock, and a synchronous actuator that is the REAL encoder-only cycle
   (`run_c3_linux_validated_bitrate_transition` / recovery's restart) on C3-F1's
   fake manager -- so a 4000 the probe refuses is refused here too. The stream's
   level is the one the controller chose (closed loop on the level, open loop on
   the reports: later reports are the recorded ones, which a lower rung would
   itself have changed). G5-S2's rules off and on.
   Per run: whether and when 4000 is reached, by which rule or trigger, how long
   it stays (and what ends it), the transitions, the 4000 refusals. **No claim
   that any run would have played better.**
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))

_spec = importlib.util.spec_from_file_location("g5_s2_replay", REPO / "docs/memory/evidence/g5_s2_2026-10-16/replay.py")
g5s2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g5s2)

import adaptive_bitrate_live as live  # noqa: E402
import remote_ladder as rl  # noqa: E402
import wan_adaptation as wa  # noqa: E402
import test_c3_f1_recovery_restart as f1  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

n2 = g5s2.n2
EVID = REPO / "docs" / "memory" / "evidence"
G4 = EVID / "g4_s1_2026-10-16"
G4_RUNS = [("G4-S1 run 1 (overlay)", G4 / "runs/E1-PS1-STREAM-REMOTE/run1"),
           ("G4-S1 run 2 (overlay, then a LAN setup)", G4 / "runs/E1-PS1-STREAM-REMOTE/run2")]


# ------------------------------------------------------------ the sessions ---
def audit_tokens() -> list[tuple[str, str]]:
    ev = json.loads((G4 / "g4_s1_read.json").read_text())["evening"]["audit"]
    return [(a["t"], a["routing_evidence"]) for a in ev if a.get("event") == "token_issued"]


def evidence_at(tokens, t_utc: str) -> str:
    last = None
    for t, e in tokens:
        if t <= t_utc[:19] + "Z":
            last = e
    return last or "unknown"


def g4_sessions(run_dir: Path, sessions, tokens):
    s = json.loads((run_dir / "summary.json").read_text())
    lo, hi = s["playing_utc"], s["window"]["to"]       # sessions that start after the window are not the run's
    out = []
    for sess in sessions:
        samples = [r for r in sess if r.get("event") == "sample"]
        if samples and lo <= samples[0]["at_utc"] <= hi:
            ev = evidence_at(tokens, samples[0]["at_utc"])
            out.append((sess, ev))
    return out


# -------------------------------------------------- 1. the controller, flag on ---
class _SyncThread:
    def __init__(self, target, args=(), **kw):
        self._t, self._a = target, args

    def start(self):
        self._t(*self._a)


def _cycle(m, fn, **kw):
    clock = f1.Clock()
    return fn(m, popen_factory=lambda argv, **k: f1.FakeProc(argv), monotonic=clock, sleep=lambda s: None,
              perf_counter_ns=lambda: int(clock() * 1e9), **kw)


def drive(segments, rec, stale, rules_on: bool) -> dict:
    """segments: [(session rows, routing evidence)] in order. One controller, as one companion."""
    remote = rl.RemoteLadder()
    saved = (live.REMOTE_LADDER, live.WAN_ADAPTATION, wa.REMOTE_LADDER, probe.REMOTE_LADDER, live.time,
             live.threading)
    root = Path(tempfile.mkdtemp(prefix="g5_s3_replay_"))
    state = {"recovery": "PLAYING", "t": 0.0}
    mgr = f1.fake_manager(7000)
    actuations = []

    def actuator(kbps):
        try:
            out = _cycle(mgr, probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=int(kbps))
            actuations.append((int(kbps), "ok"))
            return out
        except RuntimeError as exc:
            actuations.append((int(kbps), str(exc)))
            return {"ok": False, "from_bitrate_kbps": mgr._active_bitrate_kbps}

    try:
        live.REMOTE_LADDER = wa.REMOTE_LADDER = probe.REMOTE_LADDER = remote
        live.WAN_ADAPTATION = wa.WanAdaptation() if rules_on else None
        live.threading = types.SimpleNamespace(Thread=_SyncThread, RLock=live.threading.RLock)
        live.time = types.SimpleNamespace(monotonic=lambda: state["t"], time=lambda: state["t"])
        c = live.LiveController(root, environ={})
        c.bind(actuator=actuator,
               context=lambda: {"game_active": True, "game_paused": False, "recovery_state": state["recovery"]},
               serial_lock=None, recovery_state=lambda: state["recovery"])
        utc_of: dict[int, str] = {}
        for i, (sess, evidence) in enumerate(segments):
            if i:
                c.session_ended()
            mgr._active_bitrate_kbps = 7000                    # a stream start is a full start at 7000 (C1)
            remote.set_routing_evidence(rl.EVIDENCE_OVERLAY if evidence == "overlay" else rl.EVIDENCE_NOT_OVERLAY)
            for r in sess:
                ev = r.get("event")
                t = n2.ts(r["at_utc"])
                state["t"] = t
                state["recovery"] = rec.state_at(t) or "PLAYING"
                if ev == "sample" and r.get("disposition") != "dropped_actuating":
                    kbps = mgr._active_bitrate_kbps
                    ns = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID,
                          "profile": {"bitrate_kbps": live.REFERENCE_KBPS},
                          "encoder_overrides": {"any_override": False}, "bitrate_kbps": kbps}
                    if isinstance(r.get("session_elapsed_ms"), (int, float)):
                        utc_of[(i, int(r["session_elapsed_ms"]))] = r["at_utc"]
                    c.observe(g5s2.tel_from_sample(r, stale), stream_bitrate_kbps=kbps, native_status=ns)
                elif ev == "ssrc_change":
                    try:
                        _cycle(mgr, probe.run_c3_linux_recovery_restart)
                        actuations.append((mgr._active_bitrate_kbps, "recovery_restart ok"))
                    except RuntimeError as exc:
                        actuations.append((mgr._active_bitrate_kbps, f"recovery_restart {exc}"))
                    c.note_recovery_restart(r.get("source") or "recovery_restart")
        rows = [json.loads(x) for x in c.log_path.read_text().splitlines()]
    finally:
        (live.REMOTE_LADDER, live.WAN_ADAPTATION, wa.REMOTE_LADDER, probe.REMOTE_LADDER, live.time,
         live.threading) = saved
    return {"rows": rows, "actuations": actuations, "utc_of": utc_of, "segments": len(segments)}


def summarise(res: dict) -> dict:
    rows = res["rows"]
    seg = 0
    timeline = []                     # (segment, elapsed, event row); one session_ended_reset per new segment
    for r in rows:
        if r.get("event") == "session_ended_reset":
            seg += 1
        if r.get("event") in ("controller_start", "session_ended_reset"):
            continue
        timeline.append((seg, r.get("session_elapsed_ms"), r))
    trans = [(s, el, r) for s, el, r in timeline if r.get("event") == "transition"]
    samples = [(s, el, r) for s, el, r in timeline if r.get("event") == "sample"]
    first4 = next(((s, el, r) for s, el, r in trans if r.get("to_kbps") == 4000), None)
    stay = None
    if first4:
        s0, el0, _ = first4
        leave = next(((s, el, r) for s, el, r in trans if (s, el or 0) > (s0, el0) and r.get("from_kbps") == 4000),
                     None)
        if leave:
            stay = {"ended_by": f"{leave[2].get('reason')} -> {leave[2].get('to_kbps')}",
                    "s": round(((leave[1] or 0) - el0) / 1000.0, 1)}
        else:
            tail = [el for s, el, r in samples if s == s0 and isinstance(el, (int, float))]
            stay = {"ended_by": "end of the session (still at 4000)",
                    "s": round(((max(tail) if tail else el0) - el0) / 1000.0, 1)}
    refused4 = [r for _, _, r in timeline if r.get("event") == "refused" and r.get("to_kbps") == 4000]
    sugg = [r for _, _, r in timeline if r.get("event") == "wan_suggestion"]
    by_rule: dict[str, int] = {}
    for r in sugg:
        by_rule[r["rule"]] = by_rule.get(r["rule"], 0) + 1
    paths = sorted({r.get("path_class") for r in rows})
    return {
        "segments": res["segments"],
        "reports": len(samples),
        "transitions": [{"segment": s, "elapsed_s": round((el or 0) / 1000, 1),
                         "utc": res["utc_of"].get((s, el)), "from": r["from_kbps"], "to": r["to_kbps"],
                         "reason": r.get("reason"), "trigger": r.get("trigger"),
                         "wan_rule": (r.get("measurements") or {}).get("wan_rule"), "path_class": r.get("path_class")}
                        for s, el, r in trans],
        "reached_4000": None if not first4 else {
            "segment": first4[0], "elapsed_s": round(first4[1] / 1000, 1), "utc": res["utc_of"].get(first4[:2]),
            "by": first4[2].get("reason"), "trigger": first4[2].get("trigger"),
            "wan_rule": (first4[2].get("measurements") or {}).get("wan_rule"), "stay": stay},
        "refused_to_4000": sorted({r.get("reason") for r in refused4}),
        "min_level": min([7000] + [r["to_kbps"] for _, _, r in trans]),
        "wan_suggestions": len(sugg), "wan_by_rule": by_rule,
        "floor_4000_suggestions": sum(1 for r in sugg if r.get("suggestion") == "floor_4000"),
        "path_classes_in_rows": paths,
        "rows_without_path_class": sum(1 for r in rows if "path_class" not in r),
        "actuations": res["actuations"],
    }


def why_not(g4_runs) -> list[str]:
    """The ladder's own step-down evidence in G4-S1's evaluated reports (sliding 5-report windows)."""
    out = ["## 3. Why G4-S1 did not step down: the ladder's evidence windows (sliding, evaluated reports)", "",
           "| run | session (path) | evaluated reports | median fps | median lost / report | windows | "
           "loss >= 50 on >= 3 of 5 | fps < 57 on >= 4 of 5 | both (capacity_mild) | fps < 50 on all 5 |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    import statistics
    for label, segs, _, _ in g4_runs:
        for i, (sess, ev) in enumerate(segs):
            rows = [r for r in sess if r.get("event") == "sample" and r.get("disposition") == "evaluated"]
            if len(rows) < 5:
                continue
            fps = [r.get("fps") for r in rows]
            lost = [r.get("lost_packets_delta") for r in rows]
            w = loss3 = fps4 = both = strict = 0
            for k in range(len(rows) - 4):
                f5, l5 = fps[k:k + 5], lost[k:k + 5]
                a = sum(1 for v in l5 if isinstance(v, (int, float)) and v >= 50) >= 3
                b = sum(1 for v in f5 if isinstance(v, (int, float)) and v < 57) >= 4
                w += 1
                loss3 += a
                fps4 += b
                both += a and b
                strict += all(isinstance(v, (int, float)) and v < 50 for v in f5) and a
            med = lambda xs: round(statistics.median([v for v in xs if isinstance(v, (int, float))]), 1)
            out.append(f"| {label.split(' (')[0]} | {i + 1} ({'remote' if ev == 'overlay' else 'lan'}) | {len(rows)} | "
                       f"{med(fps)} | {med(lost)} | {w} | {loss3} | {fps4} | {both} | {strict} |")
    out += ["", "A window must meet both clauses for `capacity_mild` (one rung down, the only step that reaches "
            "4000 from 5000); the strict trigger names 5000. G5-S2's R2 / R3 need `latency-limited` / `starved` / "
            "`capacity-limited` windows; a `lossy` window alone moves nothing (R4: FEC, not a rung).", ""]
    return out


def loss_shape() -> list[str]:
    """G4-S1's post-FEC loss in each run's window, from the run's own telemetry.jsonl: the total and the
    largest single report (a sequence-resync jump is counted in lost_packets_delta)."""
    out = ["## 4. The shape of G4-S1's loss (the run's `telemetry.jsonl`, fresh reports in the window)", "",
           "| run | fresh reports | lost (sum) | largest single report | when (UTC) | that report: waiting_for_idr / "
           "forward gaps | lost without it | per min without it |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for label, d in G4_RUNS:
        s = json.loads((d / "summary.json").read_text())
        lo, hi = s["window"]["from"], s["window"]["to"]
        rows = [json.loads(x) for x in (d / "telemetry.jsonl").read_text().splitlines() if x.strip()]
        w = [r for r in rows if lo <= r["at_utc"] <= hi and r.get("fresh")]
        lost = [((r.get("receiver") or {}).get("lost_packets_delta") or 0) for r in w]
        k = max(range(len(lost)), key=lambda i: lost[i])
        top = w[k]
        rest = sum(lost) - lost[k]
        mins = (len(w) * 2) / 60.0
        out.append(f"| {label.split(' (')[0]} | {len(w)} | {sum(lost):,} | {lost[k]:,} | {top['at_utc'][11:23]}Z | "
                   f"{(top.get('receiver') or {}).get('waiting_for_idr')} / "
                   f"{(top.get('receiver') or {}).get('forward_gap_events_delta')} | {rest:,} | "
                   f"{rest / mins:.1f} |")
    out += ["", "Run 1's largest report is the first after the 24.5-s controller-silence pause (22:55:48.9Z → "
            "22:56:13.4Z, G4-S1 §2): the sequence jump across the outage. Run 2's is the first report of the "
            "LAN-set-up stream after the toggle. Reported as read; G4-S1's record is not rewritten.", ""]
    return out


def cell(x: dict) -> str:
    r = x["reached_4000"]
    if not r:
        return "no"
    by = r["by"] + (f" ({r['wan_rule']})" if r.get("wan_rule") else "") + (
        f", trigger {r['trigger']}" if r.get("trigger") and r["trigger"] != r["by"] else "")
    return (f"**yes** at {r['elapsed_s']} s{' (' + r['utc'][11:19] + 'Z)' if r.get('utc') else ''} by {by}; "
            f"stayed {r['stay']['s']} s, ended by {r['stay']['ended_by']}")


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = n2.RecoveryTimeline(n2.recovery_rows())
    sessions = n2.exact_sessions(n2.live_log_rows())
    tokens = audit_tokens()
    lines = ["# G5-S3 replay — the remote ladder, flag present (open loop on the reports; no claim of improvement)",
             ""]
    ok = True

    # 0. flag absent on G4-S1's sessions
    lines += ["## 0. Flag absent on G4-S1's sessions (G5-S2's `replay_recorded`, the plain `feed`)", "",
              "| run | session | first report (UTC) | routing evidence at setup | reports | recorded events | "
              "reproduced |", "| --- | --- | --- | --- | --- | --- | --- |"]
    runs = []
    for label, d in G4_RUNS:
        segs = g4_sessions(d, sessions, tokens)
        stale = g5s2.stale_by_elapsed(d)
        for i, (sess, ev) in enumerate(segs):
            mism, _, _, cnt = g5s2.replay_recorded(sess, rec, stale, g5s2.flag_absent_feed)
            ok &= not mism
            first = next(r for r in sess if r.get("event") == "sample")["at_utc"]
            lines.append(f"| {label.split(' (')[0]} | {i + 1} | {first[11:19]}Z | {ev} | {cnt['samples']} | "
                         f"{cnt['events']} | {'exact' if not mism else f'{len(mism)} MISMATCH'} |")
        runs.append((label, segs, stale, "as set up"))
    lines.append("")
    for label, d in g5s2.RUNS:
        sess = g5s2.session_for(d, sessions)
        stale = g5s2.stale_by_elapsed(d)
        runs.append((label, [(sess, "lan")], stale, "lan (as recorded)"))
        runs.append((label, [(sess, "overlay")], stale, "read as remote (hypothetical)"))

    # 1. flag present
    table = {}
    lines += ["## 1. Flag present (`PRIVYHUB_REMOTE_LADDER=1`), G5-S2's rules off and on", "",
              "| run | path_class | rules | reports | transitions (from→to, reason) | reached 4000 | 4000 refused | "
              "min level |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for label, segs, stale, path_label in runs:
        for rules_on in (False, True):
            res = summarise(drive(segs, rec, stale, rules_on))
            key = f"{label} / {path_label} / rules {'on' if rules_on else 'off'}"
            table[key] = res
            tr = "; ".join(f"{t['from']}→{t['to']} {t['reason']}" + (f" ({t['wan_rule']})" if t["wan_rule"] else "")
                           for t in res["transitions"]) or "—"
            ok &= res["rows_without_path_class"] == 0
            ok &= res["min_level"] >= 4000
            if path_label.startswith("lan"):
                ok &= res["reached_4000"] is None
            lines.append(f"| {label} | {path_label} | {'on' if rules_on else 'off'} | {res['reports']} | {tr} | "
                         f"{cell(res)} | {', '.join(res['refused_to_4000']) or '—'} | {res['min_level']} |")
    lines += ["", "Checks over every replay: every row carries `path_class`; nothing below 4000; never 4000 on a "
              "`lan` path.", "", f"-> {'PASS' if ok else 'FAIL'}", ""]
    lines += ["## 2. WAN rules' suggestions per run (rules on)", "",
              "| run | path_class | ticks with a suggestion | by rule | `floor_4000` ticks |", "| --- | --- | --- | --- | --- |"]
    for k, v in table.items():
        if k.endswith("rules on"):
            lab, path_label, _ = k.rsplit(" / ", 2)
            lines.append(f"| {lab} | {path_label} | {v['wan_suggestions']} | "
                         f"{', '.join(f'{a} {b}' for a, b in sorted(v['wan_by_rule'].items())) or '—'} | "
                         f"{v['floor_4000_suggestions']} |")
    lines.append("")
    lines += why_not(runs[:len(G4_RUNS)])
    lines += loss_shape()
    (out_dir / "replay_output.md").write_text("\n".join(lines) + "\n")
    (out_dir / "replay_tables.json").write_text(json.dumps(table, indent=1, default=str) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
