#!/usr/bin/env python3
"""G8-S2: the start rung at `floor`, replayed. Read-only; offline; no stream.

    PYTHONDONTWRITEBYTECODE=1 python3 docs/memory/evidence/g8_s2_2026-10-17/replay.py [out_dir]

G5-S3's harness (`g5_s3_2026-10-17/replay.py`): the live log's sample rows as the inputs, the
recovery logs, the edited `LiveController` in process on the replayed clock, the real encoder-only
cycle on C3-F1's fake manager as the actuator. Here each stream session starts where
`PRIVYHUB_START_RUNG=floor` would start it (the stream's level at the session's first report),
and the controller carries a `StartRung` (its record on the first sample row).

- G4-S1 run 1 and run 2: the path class from each session's setup (G5-S3's reading), G5-S3 on,
  so the floor is 4000 remote and 5000 after run 2's LAN setup; G5-S2's rules off and on.
- G8-S1 cells 6 (loss-5, rules on), 7 (burst-50x20, rules off), 12 (delay-150, rules on): LAN, so
  the floor is 5000; the arm as recorded.

Per run: the start rung, the climb (each transition, when), the level at the cell's first
recorded acted transition and what the floor-started ladder did then, the reports at each level.
Open loop on the reports (recorded at 7000). **No claim of improvement.**
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

_spec = importlib.util.spec_from_file_location("g5_s3_replay", REPO / "docs/memory/evidence/g5_s3_2026-10-17/replay.py")
g5s3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(g5s3)

import adaptive_bitrate_live as live  # noqa: E402
import remote_ladder as rl  # noqa: E402
import start_rung as sr  # noqa: E402
import wan_adaptation as wa  # noqa: E402
import test_c3_f1_recovery_restart as f1  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

n2, g5s2 = g5s3.n2, g5s3.g5s2
G8 = REPO / "docs/memory/evidence/g8_s1_2026-10-16/runs"
CELLS = [("G8-S1 cell 6 loss-5 on", "06_loss-5_on", True), ("G8-S1 cell 7 burst-50x20 off", "07_burst-50x20_off", False),
         ("G8-S1 cell 12 delay-150 on", "12_delay-150_on", True)]


class ReplayStartRung(sr.StartRung):
    """The flag's choice with the session's routing evidence given directly (no address in a replay)."""

    def _remote(self, evidence):
        return getattr(self._ladder_module(), "REMOTE_LADDER", None) is not None and evidence == "overlay"


def drive(segments, rec, stale, rules_on: bool, floor: bool) -> dict:
    remote = rl.RemoteLadder()
    start = ReplayStartRung("floor", log=lambda *_: None) if floor else None
    saved = (live.REMOTE_LADDER, live.WAN_ADAPTATION, live.START_RUNG, wa.REMOTE_LADDER, probe.REMOTE_LADDER,
             live.time, live.threading)
    root = Path(tempfile.mkdtemp(prefix="g8_s2_replay_"))
    state = {"recovery": "PLAYING", "t": 0.0}
    mgr = f1.fake_manager(7000)
    level_by_utc: list[tuple[str, int]] = []

    def actuator(kbps):
        try:
            return g5s3._cycle(mgr, probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=int(kbps))
        except RuntimeError:
            return {"ok": False, "from_bitrate_kbps": mgr._active_bitrate_kbps}

    try:
        live.REMOTE_LADDER = wa.REMOTE_LADDER = probe.REMOTE_LADDER = remote
        live.START_RUNG = start
        live.WAN_ADAPTATION = wa.WanAdaptation() if rules_on else None
        live.threading = types.SimpleNamespace(Thread=g5s3._SyncThread, RLock=live.threading.RLock)
        live.time = types.SimpleNamespace(monotonic=lambda: state["t"], time=lambda: state["t"])
        c = live.LiveController(root, environ={})
        c.bind(actuator=actuator,
               context=lambda: {"game_active": True, "game_paused": False, "recovery_state": state["recovery"]},
               serial_lock=None, recovery_state=lambda: state["recovery"])
        for i, (sess, evidence) in enumerate(segments):
            if i:
                c.session_ended()
            # the stream start: 7000 today; with the flag, the start rung (the stream's own first level)
            mgr._active_bitrate_kbps = start.choose(evidence)["kbps"] if start else 7000
            remote.set_routing_evidence(rl.EVIDENCE_OVERLAY if evidence == "overlay" else rl.EVIDENCE_NOT_OVERLAY)
            for r in sess:
                t = n2.ts(r["at_utc"])
                state["t"] = t
                state["recovery"] = rec.state_at(t) or "PLAYING"
                if r.get("event") == "sample" and r.get("disposition") != "dropped_actuating":
                    kbps = mgr._active_bitrate_kbps
                    level_by_utc.append((r["at_utc"], kbps))
                    ns = {"active": True, "profile_id": live.REFERENCE_PROFILE_ID,
                          "profile": {"bitrate_kbps": live.REFERENCE_KBPS},
                          "encoder_overrides": {"any_override": False}, "bitrate_kbps": kbps}
                    c.observe(g5s2.tel_from_sample(r, stale), stream_bitrate_kbps=kbps, native_status=ns)
                elif r.get("event") == "ssrc_change":
                    try:
                        g5s3._cycle(mgr, probe.run_c3_linux_recovery_restart)
                    except RuntimeError:
                        pass
                    c.note_recovery_restart(r.get("source") or "recovery_restart")
        rows = [json.loads(x) for x in c.log_path.read_text().splitlines()]
    finally:
        (live.REMOTE_LADDER, live.WAN_ADAPTATION, live.START_RUNG, wa.REMOTE_LADDER, probe.REMOTE_LADDER, live.time,
         live.threading) = saved
    return {"rows": rows, "levels": level_by_utc}


def level_at(levels, t_utc):
    last = None
    for t, k in levels:
        if t <= t_utc:
            last = k
    return last


def summarise(res: dict, first_action_utc: str | None, utc_of: dict) -> dict:
    rows = res["rows"]
    trans = [r for r in rows if r.get("event") == "transition"]
    marks = [r["start_rung"] for r in rows if "start_rung" in r]
    by_level: dict[int, int] = {}
    for _, k in res["levels"]:
        by_level[k] = by_level.get(k, 0) + 1
    out = {"start_rungs": [(m["kbps"], m["source"], m["path_class"]) for m in marks],
           "transitions": [(r.get("session_elapsed_ms", 0) / 1000, r["from_kbps"], r["to_kbps"], r.get("reason"))
                           for r in trans],
           "reports_by_level": dict(sorted(by_level.items())),
           "reached_7000_again": any(r["to_kbps"] == 7000 for r in trans)}
    if first_action_utc:
        out["level_at_first_recorded_action"] = level_at(res["levels"], first_action_utc)
        near = [r for r in rows if r.get("event") in ("transition", "refused", "hold")
                and abs(n2.ts(utc_of.get(r.get("session_elapsed_ms"), "1970-01-01T00:00:00Z")) - n2.ts(first_action_utc))
                <= 4]
        out["floor_ladder_at_that_time"] = [(r["event"], r.get("class"), r.get("reason"), r.get("to_kbps"))
                                            for r in near][:3] or "no decision within 4 s"
    return out


def first_acted(run_dir: Path) -> tuple[str, str] | None:
    p = run_dir / "decisions.jsonl"
    for line in p.read_text().splitlines() if p.exists() else []:
        r = json.loads(line)
        if r.get("event") == "transition" and r.get("acted"):
            return r["at_utc"], f"{r['from_kbps']}→{r['to_kbps']} {r.get('reason')}"
    return None


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = n2.RecoveryTimeline(n2.recovery_rows())
    sessions = n2.exact_sessions(n2.live_log_rows())
    tokens = g5s3.audit_tokens()
    runs = []
    for label, d in g5s3.G4_RUNS:
        runs.append((label, g5s3.g4_sessions(d, sessions, tokens), g5s2.stale_by_elapsed(d), (False, True), None))
    for label, cell, rules in CELLS:
        rd = G8 / cell / "E1-PS1-STREAM_flag" / "run1"
        runs.append((label, [(g5s2.session_for(rd, sessions), "lan")], g5s2.stale_by_elapsed(rd), (rules,),
                     first_acted(rd)))
    table = {}
    lines = ["# G8-S2 replay — `PRIVYHUB_START_RUNG=floor` (open loop on the recorded reports; no claim of "
             "improvement)", "",
             "| run | rules | start rung (source, path) per session | transitions (elapsed s: from→to reason) | "
             "reports at each level | back at 7000 | the recorded first acted transition | the floor-started "
             "ladder's level then | its decisions within 4 s |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    ok = True
    for label, segs, stale, arms, fa in runs:
        utc_of = {}
        for sess, _ in segs:
            for r in sess:
                if r.get("event") == "sample" and isinstance(r.get("session_elapsed_ms"), (int, float)):
                    utc_of[int(r["session_elapsed_ms"])] = r["at_utc"]
        for rules_on in arms:
            today = summarise(drive(segs, rec, stale, rules_on, floor=False), fa[0] if fa else None, utc_of)
            floor = summarise(drive(segs, rec, stale, rules_on, floor=True), fa[0] if fa else None, utc_of)
            ok &= len(floor["start_rungs"]) == len(segs) and all(k in (4000, 5000) for k, _, _ in floor["start_rungs"])
            table[f"{label} / rules {'on' if rules_on else 'off'}"] = {"today": today, "floor": floor,
                                                                      "first_recorded_action": fa}
            fmt_t = "; ".join(f"{t:.0f}: {a}→{b} {why}" for t, a, b, why in floor["transitions"]) or "—"
            lines.append(
                f"| {label} | {'on' if rules_on else 'off'} | "
                + ", ".join(f"{k} ({s}, {p})" for k, s, p in floor["start_rungs"])
                + f" | {fmt_t} | " + " / ".join(f"{k}: {n}" for k, n in floor["reports_by_level"].items())
                + f" | {'yes' if floor['reached_7000_again'] else 'no'} | "
                + (f"{fa[0][11:19]}Z {fa[1]} (today's level then: {today.get('level_at_first_recorded_action')})"
                   if fa else "none recorded")
                + f" | {floor.get('level_at_first_recorded_action', '—')} | {floor.get('floor_ladder_at_that_time', '—')} |")
    lines += ["", "Check: every session's first sample row carries the start rung, at the floor of its path's list "
              f"-> {'PASS' if ok else 'FAIL'}.", "",
              "Today's arm (start 7000) is replayed through the same harness; each cell's recorded first acted "
              "transition is the live one (`decisions.jsonl`).", ""]
    (out_dir / "replay_output.md").write_text("\n".join(lines) + "\n")
    (out_dir / "replay_tables.json").write_text(json.dumps(table, indent=1, default=str) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
