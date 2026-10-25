#!/usr/bin/env python3
"""B23: the recorded control-gap logs (every client -> host silence >= 250 ms) through the real B2 detector with B6's
tuning attached, at the old H (950) and the new remote-direct H (450); 10-ms quiet checks; a hold on a gap >= 3 s is
real (WAN-R1's rule), else false. Whole logs, no session-edge exclusion (WAN-R1 excluded 10 s at each edge: this is
the stricter count). LAN-R1's form: the real code in process, fed from the recorded rows. Read only.
    python3 -B replay_holds.py   (writes replay_holds.md / .json beside itself)"""
import json, sys
from datetime import datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
EV = HERE.parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "companion"))
import hold_tuning, input_hold  # noqa: E402

LOGS = [  # (label, class as WAN-R1 reads it, path)
    ("G4-S4 (friend's broadband)", "direct", "g4_s4_2026-10-24/copies/logs/games/native_stream_ctrl_gaps.log"),
    ("G4-S1 run 1 (hotspot)", "direct", "wan_r1_2026-10-24/copies/s1r1/native_stream_ctrl_gaps.log"),
    ("G4-S1 run 2 (hotspot; incl. the no-peer span after the toggle)", "direct + no-peer", "wan_r1_2026-10-24/copies/s1r2/native_stream_ctrl_gaps.log"),
    ("G4-S2 run 1 (hotspot)", "direct", "wan_r1_2026-10-24/copies/s2r1/native_stream_ctrl_gaps.log"),
    ("G4-S3 (hotspot)", "direct", "wan_r1_2026-10-24/copies/s3r1/native_stream_ctrl_gaps.log"),
    ("LINK-R1 (5 GHz)", "lan", "link_r1_2026-10-23/runs/logs_run1/native_stream_ctrl_gaps.log"),
    ("G-A3 (5 GHz)", "lan", "g_a3_2026-10-23/runs/logs_run1/native_stream_ctrl_gaps.log"),
    ("CL-B10 cell 1 (5 GHz)", "lan", "cl_b10_2026-10-23/runs/1_snes_5ghz_restart_guard/logs_run1/native_stream_ctrl_gaps.log"),
    ("CL-B11 cell 1 (5 GHz)", "lan", "cl_b11_2026-10-24/runs/1_snes_5ghz_restart_guard_all_paths/logs_run1/native_stream_ctrl_gaps.log"),
    ("CL-B12 cell 1 (5 GHz)", "lan", "cl_b12_2026-10-24/runs/1_snes_5ghz_two_home_presses/logs_run1/native_stream_ctrl_gaps.log"),
    ("CL-B10 cell 4 (2.4 GHz; reference, not a WAN-R1 window)", "lan 2.4", "cl_b10_2026-10-23/runs/4_snes_24ghz_notice/logs_run1/native_stream_ctrl_gaps.log"),
]
REAL_MS = 3000.0

def t(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()

def replay(gaps, hold_ms, guard=False):
    emitted = []
    det = input_hold.InputHoldDetector(250, emitted.append)
    det.hold_s = hold_ms / 1000.0
    det.tuning = hold_tuning.Tuning(hold_ms)
    real = false = 0; false_ms = []
    for g in gaps:
        a, b = t(g["start_utc"]), t(g["end_utc"])
        det.on_packet(a)
        n0 = sum(1 for e in emitted if e[0] == "hold")
        x = a
        while x < b:
            x += 0.010
            det.on_quiet(min(x, b), a)
        det.on_packet(b)
        if sum(1 for e in emitted if e[0] == "hold") > n0:
            if float(g["gap_ms"]) >= REAL_MS: real += 1
            else:
                false += 1; false_ms.append(round(float(g["gap_ms"])))
                if guard:   # addendum 1: the first non-drop hold on direct reverts to the wired 950
                    det.hold_s, det.tuning.hold_ms = 0.950, 950
    return {"real": real, "false": false, "false_gap_ms": false_ms[:12], "capped": det.capped}

rows = []
for label, cls, rel in LOGS:
    p = EV / rel
    gaps = [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.is_file() else None
    r = {"label": label, "class": cls, "log": rel, "silences": None if gaps is None else len(gaps)}
    if gaps is not None:
        r["drops_ge_3s"] = sum(1 for g in gaps if float(g["gap_ms"]) >= REAL_MS)
        r["h950"] = replay(gaps, 950); r["h450"] = replay(gaps, 450); r["h450_guard"] = replay(gaps, 450, guard=True)
    rows.append(r)
out = ["# B23 — the recorded silences through the real hold detector at H 950 and H 450", "",
       "Whole logs (no 10-s edge exclusion: stricter than WAN-R1); a hold on a gap ≥ 3 s is real, else false. "
       "`replay_holds.py`, read only.", "",
       "H 450 + guard (addendum 1): the session starts at 450 and reverts to 950 at its first non-drop hold.", "",
       "| log | class | silences ≥ 250 | drops ≥ 3 s | H 950: real / false | H 450: real / false | H 450 + guard: real / false | false gaps at 450 (ms) |",
       "| --- | --- | ---: | ---: | --- | --- | --- | --- |"]
for r in rows:
    if r["silences"] is None:
        out.append(f"| {r['label']} | {r['class']} | (no log) | | | | | |"); continue
    a, b, c = r["h950"], r["h450"], r["h450_guard"]
    out.append(f"| {r['label']} | {r['class']} | {r['silences']} | {r['drops_ge_3s']} | {a['real']} / **{a['false']}** | "
               f"{b['real']} / **{b['false']}** | {c['real']} / **{c['false']}** | {', '.join(map(str, b['false_gap_ms'])) or '—'} |")
(HERE / "replay_holds.json").write_text(json.dumps(rows, indent=1) + "\n")
(HERE / "replay_holds.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
