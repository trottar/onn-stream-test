#!/usr/bin/env python3
"""B33: absent = today byte for byte. One scripted episode set -- two heartbeats through the recovery's real hook, a
450-ms stall with 0 loss (B7 + B12, stall_end), a 2-s silence and a 0.93-s silence (B2's hold, B9's state path) --
run in a fresh process against a tree's companion/ with a given environment; the recovery rows compared with every
time-valued field masked (at_utc, *_ms, frame counts). Usage: proof_flag_absent.py BASE_TREE NEW_TREE."""
import json, subprocess, sys

SCENARIO = r'''
import json, sys, time
sys.path.insert(0, "companion"); sys.path.insert(0, "tests/rewind_cores")
import hold_rewind as hr, stall_signal as ss, stall_owner as so
import test_rewind_cores as b9
from games import link_drop_recovery as ldr
extra = json.loads(sys.argv[1])
out = []
def rig(core):
    from pathlib import Path; import tempfile, input_hold as ih
    st = Path(tempfile.mkdtemp(prefix="b33_proof_"))
    c = b9.FakeCore(st, "Game (USA)"); c.start()
    emu = b9.FakeEmulator(c, core); det = ih.InputHoldDetector(250, lambda ev: None)
    ctrl = b9.FakeController(det); ctrl._lost_packets = 0
    rec = b9.recovery()
    env = dict({"PRIVYHUB_INPUT_HOLD": "1", "PRIVYHUB_INPUT_HOLD_REWIND": "1", "PRIVYHUB_INPUT_HOLD_B6": "1"}, **extra)
    rw = hr.wire(rec, ctrl, emu, env)
    return c, emu, det, ctrl, rec, rw
def hbs(rec):
    for i in range(2):
        rec.note_heartbeat({"last_output_age_ms": 10, "lost_packets": 3, "fec_unrecoverable_groups": 1,
                            "audio_max_arrival_gap_ms": 40, "sequence": i})
# 1. the 450-ms stall
c, emu, det, ctrl, rec, rw = rig(b9.PSX)
hbs(rec)
rec._pause_game = lambda: (setattr(c, "playing", False), setattr(emu, "_paused", True))
rec._resume_game = lambda: (setattr(c, "playing", True), setattr(emu, "_paused", False))
sig = ss.StallSignal(rec, 400, threaded=False); rec._client_stall = sig
own = so.StallOwner(); rec._stall_owner = own
t0 = time.monotonic(); seq = 0
for age in range(150, 451, 50):
    seq += 1
    w = t0 + age / 1000.0 - time.monotonic()
    if w > 0: time.sleep(w)
    sig.handle((ss.KIND_STALL, False, seq, 5000 + seq, age), time.monotonic())
sig.handle((ss.KIND_END, False, seq + 1, 5100, 10), time.monotonic())
time.sleep(0.05)
out.append({"case": "stall_450", "rows": b9.rows(rec), "loads": c.loads}); c.stop()
# 2. / 3. the silences
for s in (2.0, 0.93):
    c, emu, det, ctrl, rec, rw = rig(b9.PSX)
    hbs(rec)
    last = time.monotonic() - s
    det.on_quiet(last + 0.41, last)
    end = time.monotonic() + 2
    while rw.b9.saves < 1 and time.monotonic() < end: time.sleep(0.01)
    c.playing = False; emu._paused = True
    rec._state = ldr.STATE_PAUSED_RECOVERING; rec._state_since = time.monotonic()
    rw._pending = {"onset": last, "paused_at": last + 0.95, "key": rec._state_since}
    rw.rewind(rec, "input_release")
    time.sleep(0.05)
    out.append({"case": f"silence_{s}", "rows": b9.rows(rec), "loads": c.loads}); c.stop()
print(json.dumps(out))
'''

MASK_SUFFIX = ("_ms",)
MASK_KEYS = {"at_utc", "counter_before", "requested_frames", "counter_after", "frames_restored",
             "net_unattended_frames", "client_frame", "seq"}


def masked(rows):
    res = []
    for r in rows:
        res.append({k: ("<t>" if (k in MASK_KEYS or k.endswith(MASK_SUFFIX)) else v) for k, v in r.items()})
    return res


def run(tree, extra):
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
    p = subprocess.run([sys.executable, "-c", SCENARIO, json.dumps(extra)], cwd=tree, capture_output=True, text=True,
                       env=env, timeout=120)
    if p.returncode:
        raise SystemExit(p.stderr)
    return [dict(c, rows=masked(c["rows"])) for c in json.loads(p.stdout)]


base, new = sys.argv[1], sys.argv[2]
U = {"PRIVYHUB_LINK_RECOVERY": "1"}
pairs = [("no umbrella, no line", {}, {}),
         ("the umbrella + PRIVYHUB_REWIND_NEEDS_LOSS=0", U, dict(U, PRIVYHUB_REWIND_NEEDS_LOSS="0")),
         ("a junk line alone", {}, {"PRIVYHUB_REWIND_NEEDS_LOSS": "yes"})]
ok_all = True
for label, eb, en in pairs:
    a, b = run(base, eb), run(new, en)
    ok = a == b
    ok_all &= ok
    print(f"{'EQUAL' if ok else 'DIFFER'}  {label}: base {json.dumps(eb)} vs new {json.dumps(en)}; "
          f"cases {[c['case'] for c in a]}; rows {[len(c['rows']) for c in a]}; loads {[c['loads'] for c in a]}")
    if not ok:
        for x, y in zip(a, b):
            if x != y:
                print("  base", json.dumps(x)[:1500]); print("  new ", json.dumps(y)[:1500])
on = run(new, U)
print("for contrast, the new with the umbrella alone: " + "; ".join(
    f"{c['case']}: {[(r['event'], r.get('method'), r.get('why')) for r in c['rows'] if r['event'] == 'input_release']} loads {c['loads']}"
    for c in on))
print("PROVEN" if ok_all else "NOT PROVEN")
