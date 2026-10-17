#!/usr/bin/env python3
"""G5-S4: the remote rung cap over G4-S1's run 1 and run 2. Read-only; offline; no stream.

    PYTHONDONTWRITEBYTECODE=1 python3 docs/memory/evidence/g5_s4_2026-10-17/replay.py [out_dir]

The sessions, their `path_class` (from the setup's routing evidence) and the
inputs are G5-S3's (`g5_s3_2026-10-17/replay.py`): the live log's sample rows,
the recovery logs, the edited `LiveController` in process on the replayed clock,
the real encoder-only cycle on C3-F1's fake manager as the actuator. Here the
controller also carries a `RemoteCap` sharing that `RemoteLadder`, at 4000 and at
5000; G5-S2's rules off and on. Open loop on the reports (recorded at 7000).

Per run and cap: the target per tick (reports and seconds at each level), the
move to the cap and every clamp, and the wire rate each level implies from the
measured figures -> the data per hour, **as arithmetic, not as a result**:

- C5-M3 (`c5_m3_onair.txt`, home Wi-Fi, video + parity + headers): 7000 -> 8.60
  Mbit/s, 4000 -> 5.02. **5000 was not measured on the wire**; L1's rung-load
  estimate (6.20, quoted in C5-M3) is used and labelled.
- G4-S1 run 1: the overlay interface's tx, 11.42 Mbit/s at 7000 (window mean).
  The overlay rate at another rung is shown two ways, both arithmetic: scaled by
  G4-S1's ratio (11.42 / 8.60), and with G4-S1's difference (11.42 - 8.60) added.
- GB per hour = Mbit/s x 3600 / 8 / 1000 = Mbit/s x 0.45.
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
import remote_cap as rc  # noqa: E402
import remote_ladder as rl  # noqa: E402
import wan_adaptation as wa  # noqa: E402
import test_c3_f1_recovery_restart as f1  # noqa: E402
from diagnostics import c3_linux_actuator_probe as probe  # noqa: E402

n2, g5s2 = g5s3.n2, g5s3.g5s2
CAPS = (4000, 5000)
WIRE = {7000: (8.60, "C5-M3 measured"), 4000: (5.02, "C5-M3 measured"), 5000: (6.20, "L1 estimate (not measured)")}
OVERLAY_7000 = 11.42                      # G4-S1 run 1, overlay-interface tx, window mean
GB_PER_H = 3600 / 8 / 1000


def drive(segments, rec, stale, cap: int, rules_on: bool) -> dict:
    remote = rl.RemoteLadder()
    capper = rc.RemoteCap(str(cap), remote)
    saved = (live.REMOTE_LADDER, live.REMOTE_CAP, live.WAN_ADAPTATION, wa.REMOTE_LADDER, probe.REMOTE_LADDER,
             live.time, live.threading)
    root = Path(tempfile.mkdtemp(prefix="g5_s4_replay_"))
    state = {"recovery": "PLAYING", "t": 0.0}
    mgr = f1.fake_manager(7000)
    per_level: dict[int, int] = {}
    per_level_by_path: dict[str, dict[int, int]] = {}

    def actuator(kbps):
        try:
            return g5s3._cycle(mgr, probe.run_c3_linux_validated_bitrate_transition, target_bitrate_kbps=int(kbps))
        except RuntimeError:
            return {"ok": False, "from_bitrate_kbps": mgr._active_bitrate_kbps}

    try:
        live.REMOTE_LADDER = wa.REMOTE_LADDER = probe.REMOTE_LADDER = remote
        live.REMOTE_CAP = capper
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
            mgr._active_bitrate_kbps = 7000
            remote.set_routing_evidence(rl.EVIDENCE_OVERLAY if evidence == "overlay" else rl.EVIDENCE_NOT_OVERLAY)
            for r in sess:
                t = n2.ts(r["at_utc"])
                state["t"] = t
                state["recovery"] = rec.state_at(t) or "PLAYING"
                if r.get("event") == "sample" and r.get("disposition") != "dropped_actuating":
                    kbps = mgr._active_bitrate_kbps
                    per_level[kbps] = per_level.get(kbps, 0) + 1
                    d = per_level_by_path.setdefault(remote.path_class, {})
                    d[kbps] = d.get(kbps, 0) + 1
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
        (live.REMOTE_LADDER, live.REMOTE_CAP, live.WAN_ADAPTATION, wa.REMOTE_LADDER, probe.REMOTE_LADDER, live.time,
         live.threading) = saved
    return {"rows": rows, "per_level": per_level, "per_level_by_path": per_level_by_path, "cap": capper.status()}


def mix_rate(per_level: dict[int, int], basis: str) -> float | None:
    """The time-weighted wire rate the levels imply (reports are 2 s apart)."""
    n = sum(per_level.values())
    if not n:
        return None
    total = 0.0
    for lv, k in per_level.items():
        w = WIRE[lv][0]
        if basis == "overlay_scaled":
            w = w * OVERLAY_7000 / WIRE[7000][0]
        elif basis == "overlay_added":
            w = w + (OVERLAY_7000 - WIRE[7000][0])
        total += w * k
    return total / n


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = n2.RecoveryTimeline(n2.recovery_rows())
    sessions = n2.exact_sessions(n2.live_log_rows())
    tokens = g5s3.audit_tokens()
    lines = ["# G5-S4 replay — the remote rung cap over G4-S1 (open loop on the reports; arithmetic, not results)", ""]
    table = {}
    ok = True
    lines += ["## 1. The target per tick", "",
              "| run | cap | rules | reports on the remote path: at 7000 / 5000 / 4000 | on the LAN path | "
              "the move to the cap (session, elapsed) | other transitions | clamps (rows with `source: remote_cap`): "
              "moves / blocked increases | max level on the remote path after the move |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for label, d in g5s3.G4_RUNS:
        segs = g5s3.g4_sessions(d, sessions, tokens)
        stale = g5s2.stale_by_elapsed(d)
        for cap in CAPS:
            for rules_on in (False, True):
                res = drive(segs, rec, stale, cap, rules_on)
                rows = res["rows"]
                seg, trans = 0, []
                for r in rows:
                    if r.get("event") == "session_ended_reset":
                        seg += 1
                    if r.get("event") == "transition":
                        trans.append((seg, r))
                moves = [(s, r) for s, r in trans if r.get("reason") == "remote_cap"]
                others = [(s, r) for s, r in trans if r.get("reason") != "remote_cap"]
                blocked = [r for r in rows if r.get("event") == "refused" and r.get("reason") == "remote_cap"]
                remote_lv = res["per_level_by_path"].get("remote", {})
                lan_lv = res["per_level_by_path"].get("lan", {})
                after = [r["to_kbps"] for s, r in trans if r.get("path_class") == "remote"]
                ok &= all(r.get("path_class") == "remote" for _, r in moves)
                ok &= not [1 for _, r in trans if r.get("path_class") == "remote" and r["to_kbps"] > cap]
                ok &= not lan_lv or set(lan_lv) == {7000}
                fmt = lambda dct: " / ".join(str(dct.get(k, 0)) for k in (7000, 5000, 4000))
                lines.append(
                    f"| {label} | {cap} | {'on' if rules_on else 'off'} | {fmt(remote_lv)} | "
                    f"{('7000 ×' + str(lan_lv.get(7000, 0))) if lan_lv else '—'} | "
                    + ("; ".join(f"{s + 1}: {r['session_elapsed_ms'] / 1000:.0f} s, {r['from_kbps']}→{r['to_kbps']}"
                                 for s, r in moves) or "—")
                    + " | " + ("; ".join(f"{r['from_kbps']}→{r['to_kbps']} {r['reason']}" for _, r in others) or "—")
                    + f" | {len(moves)} / {len(blocked)} | {max(after) if after else '—'} |")
                table[f"{label} / cap {cap} / rules {'on' if rules_on else 'off'}"] = {
                    "remote_reports_by_level": remote_lv, "lan_reports_by_level": lan_lv,
                    "moves": [{"segment": s + 1, "elapsed_s": r["session_elapsed_ms"] / 1000, "from": r["from_kbps"],
                               "to": r["to_kbps"], "wish_kbps": r.get("wish_kbps"), "capped_kbps": r.get("capped_kbps")}
                              for s, r in moves],
                    "other_transitions": [(r["from_kbps"], r["to_kbps"], r.get("reason")) for _, r in others],
                    "blocked_increase_rows": len(blocked),
                    "blocked_wishes": sorted({r.get("wish_kbps") for r in blocked}),
                    "cap_status": res["cap"]}
    lines += ["", "Checks: every move is on a remote path; no remote transition above the cap; the LAN path stays at "
              "7000 (no effect).", "", f"-> {'PASS' if ok else 'FAIL'}", ""]

    # 2. the arithmetic
    lines += ["## 2. The wire rate and the data per hour, as arithmetic", "",
              "| level | wire rate (Mbit/s) | source | GB / h at that rate | overlay, scaled ×(11.42/8.60) | GB / h | "
              "overlay, +(11.42−8.60) | GB / h |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for lv in (7000, 5000, 4000):
        w, src = WIRE[lv]
        sc = w * OVERLAY_7000 / WIRE[7000][0]
        ad = w + OVERLAY_7000 - WIRE[7000][0]
        lines.append(f"| {lv} | {w:.2f} | {src} | {w * GB_PER_H:.2f} | {sc:.2f} | {sc * GB_PER_H:.2f} | {ad:.2f} | "
                     f"{ad * GB_PER_H:.2f} |")
    lines += ["", "G4-S1 run 1's measured 11.42 Mbit/s at 7000 is 5.14 GB / h (G4-S1 §9: about 5.1).", ""]
    lines += ["### The replayed mix on each run's remote path (time-weighted over the reports, the first minute at "
              "7000 included)", "",
              "| run | cap | rules | reports on the remote path | share at the cap | implied wire (C5-M3 basis) | GB / h | "
              "implied overlay (scaled) | GB / h | implied overlay (added) | GB / h |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for key, v in table.items():
        lab, cap_s, rules_s = key.split(" / ")
        lv = v["remote_reports_by_level"]
        n = sum(lv.values())
        cap = int(cap_s.split()[1])
        rates = {b: mix_rate(lv, b) for b in ("wire", "overlay_scaled", "overlay_added")}
        v["implied_mbps"] = rates
        lines.append(f"| {lab} | {cap} | {rules_s.split()[1]} | {n} | {100 * lv.get(cap, 0) / n:.0f} % | "
                     f"{rates['wire']:.2f} | {rates['wire'] * GB_PER_H:.2f} | {rates['overlay_scaled']:.2f} | "
                     f"{rates['overlay_scaled'] * GB_PER_H:.2f} | {rates['overlay_added']:.2f} | "
                     f"{rates['overlay_added'] * GB_PER_H:.2f} |")
    lines += ["", "Arithmetic on recorded inputs at 7000; the reports a capped stream would have produced are not "
              "these. The data volume at the cap is for the first off-site run with it to measure (G4-S2); the "
              "picture at the cap is the user's judgement.", ""]
    (out_dir / "replay_output.md").write_text("\n".join(lines) + "\n")
    (out_dir / "replay_tables.json").write_text(json.dumps(table, indent=1, default=str) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
