#!/usr/bin/env python3
"""E4-S2 -- the CPU-time and memory ladder, run and judged as pre-registered (e4_s2_preregistration.txt §2-§3).

    e4_s2_ladder.py run      the CPU ladder (400/300/200/150/100 %), its INCONCLUSIVE repeats, then the memory ladder
                             (4G/2G/1G at one CPU step above each row's CPU floor), its repeats; resumable (ladder.json)
    e4_s2_ladder.py judge    re-judge every run from ladder.json's run list (read-only) -> prints the verdicts

Each step is one tools/e1_suite.py invocation (--e2 --window 1200, idle gap 120 s), every run carrying its constraint
in the drop-in e4_constraint.conf (written before the run's restart, removed + daemon-reload + restart at its
teardown, the unit's properties read back; the runner's own code). This script only decides which rows run at which
step and judges each run by the pass rule; it changes nothing itself.
"""
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
SUITE = os.path.join(REPO, "tools/e1_suite.py")
PRE = os.path.join(HERE, "e4_s2_preregistration.txt")
OUT = os.path.join(HERE, "runs")
STATE = os.path.join(HERE, "ladder.json")
ROWS = ["E1-PS1-STREAM", "E1-SNES-STREAM", "E1-CONC", "E1-META"]       # the control (PS1-STREAM at 400 %) first
CPU = [400, 300, 200, 150, 100]
MEM = ["4G", "2G", "1G"]
CHANNELS = 6
LINK = {"rendered_fps", "spikes_20ms_per_min", "stale_drops_per_min"}   # observed at the client, across the link


def log(*a):
    line = f"[e4s2 {time.strftime('%H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
    print(line, flush=True)
    with open(os.path.join(HERE, "ladder_console.log"), "a") as fh:
        fh.write(line + "\n")


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


# the CFS period every constrained run carries, as the probe chose it (pre-registration §1): [] = the default (100 ms)
PERIOD = []


def tag(cons):
    """The runner's run-dir suffix (tools/e1_suite.py constraint_tag)."""
    return "_".join(("cpu" + v.rstrip("%")) if n == "CPUQuota" else ("per" + v) if n == "CPUQuotaPeriodSec"
                    else ("mem" + v) for n, _, v in (kv.partition("=") for kv in cons))


def latest_summary(row, cons):
    d = os.path.join(OUT, f"{row}_{tag(cons)}")
    runs = sorted((int(x[3:]) for x in os.listdir(d) if x.startswith("run") and x[3:].isdigit()), reverse=True) \
        if os.path.isdir(d) else []
    for n in runs:
        p = os.path.join(d, f"run{n}", "summary.json")
        if os.path.exists(p):
            return os.path.relpath(p, HERE)
    return None


def _t(x):
    return time.mktime(time.strptime(x[:19], "%Y-%m-%dT%H:%M:%S")) + float("0." + x[20:-1] if len(x) > 20 else 0)


def capture(rd, s):
    """The encoder's capture fps and dup+drop per min over the window, SEGMENT-AWARE: summed over consecutive
    progress records of one encoder (frame not decreasing, <= 3 s apart); an encoder restart (the live ladder's
    transition, a recovery) starts a new segment and its dead time is not counted. (The sampler's own figure is
    first-to-last over the window and is broken by any restart.)"""
    t0, t1 = s["window"]["from"], s["window"]["to"]
    rows = []
    try:
        for l in open(os.path.join(rd, "encoder.jsonl")):
            r = json.loads(l)
            if r.get("records") and t0 <= r["at_utc"] <= t1:
                rows.append(r)
    except (OSError, ValueError):
        return {}
    fr = dt = dd = 0.0
    segs = 1 if rows else 0
    for a, b in zip(rows, rows[1:]):
        d = _t(b["at_utc"]) - _t(a["at_utc"])
        if b["frame"] < a["frame"] or d > 3 or b["dup"] < a["dup"] or b["drop"] < a["drop"]:
            segs += 1
            continue
        fr += b["frame"] - a["frame"]
        dt += d
        dd += (b["dup"] - a["dup"]) + (b["drop"] - a["drop"])
    return {"capture_fps": round(fr / dt, 3) if dt else None, "dupdrop_per_min": round(dd / (dt / 60), 3) if dt else None,
            "segments": segs, "counted_s": round(dt, 1)}


# ---------------------------------------------------------------- the pass rule (pre-registration §2)
def metrics(s, rd):
    rf = k(s, "teardown", "report_fields") or {}
    mins = (rf.get("duration_ms") or 0) / 60000
    enc = k(s, "host", "encoder") or {}
    cap = capture(rd, s) if s.get("kind") == "stream" else {}
    m = {"rendered_fps": k(s, "key", "heartbeat", "rendered_fps"),
         "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"),
         "capture_fps": cap.get("capture_fps"), "encoder_segments": cap.get("segments"),
         "capture_fps_sampler_first_to_last": enc.get("capture_fps"),
         "spikes_20ms_per_min": round(rf["decoder.spike_20_ms"] / mins, 2) if mins and "decoder.spike_20_ms" in rf else None,
         "stale_drops_per_min": round(rf["decoder.stale_output_drops"] / mins, 3) if mins and "decoder.stale_output_drops" in rf else None,
         "encoder_dupdrop_per_min": cap.get("dupdrop_per_min"),
         "grabs_failed": k(s, "key", "epg", "grabs_failed"),
         "grabs_ok_min_per_channel": (min((k(s, "key", "epg", "grabs_ok_per_channel") or {}).values(), default=0)
                                      if len(k(s, "key", "epg", "grabs_ok_per_channel") or {}) == CHANNELS else 0)
                                     if k(s, "key", "epg") else None,
         "guide_serves": k(s, "guide_at_end", "serves"),
         # reported, not gated
         "video_loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
         "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "underruns": k(s, "key", "heartbeat", "audio_underruns"),
         "throttled_s": k(s, "key", "cgroup", "throttled_s"), "throttled_period_frac": k(s, "key", "cgroup", "throttled_period_frac"),
         "usage_cores": k(s, "key", "cgroup", "usage_cores"), "memory_current_max_mb": k(s, "key", "cgroup", "memory_current_max_mb"),
         "memory_peak_mb": k(s, "key", "cgroup", "memory_peak_mb"), "swap_current_max_mb": k(s, "key", "cgroup", "swap_current_max_mb"),
         "memory_events_high": k(s, "key", "cgroup", "memory_events_high"), "memory_events_max": k(s, "key", "cgroup", "memory_events_max"),
         "oom_kill_run": k(s, "key", "cgroup", "oom_kill_run"),
         "bitrate_kbps_min": k(s, "key", "status_poll", "bitrate_kbps_min"), "bitrate_kbps_max": k(s, "key", "status_poll", "bitrate_kbps_max"),
         "transitions": k(s, "key", "decisions", "transitions"),
         "grab_s_median": k(s, "key", "epg", "grab_s_median"), "grabs_ok": k(s, "key", "epg", "grabs_ok"),
         "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
         "socket_w": k(s, "host", "host", "gpu.socket_power_w", "mean"), "tctl": k(s, "host", "host", "gpu.tctl_c", "mean"),
         "controller_pauses": len(k(s, "key", "recovery", "controller_pauses") or []) if k(s, "key", "recovery") else None,
         "client_pauses": len(k(s, "key", "recovery", "client_pauses") or []) if k(s, "key", "recovery") else None}
    return m


REF_RUNS = os.path.join(HERE, "..", "e4_s1_2026-10-09", "runs")
# the reference-relative clause (pre-registration §3): a gated metric the row's own E4-S1 run (unconstrained, the
# adopted state) already fails is judged against that run's value within the gate's own tolerance
REL = {"rendered_fps": 0.5, "retroarch_fps": 0.1, "capture_fps": 0.5, "encoder_dupdrop_per_min": 0.2}
_REF = {}


def reference(row):
    if row not in _REF:
        rd = os.path.join(REF_RUNS, row, "run1")
        try:
            s = json.load(open(os.path.join(rd, "summary.json")))
            _REF[row] = metrics(s, rd)
        except (OSError, ValueError):
            _REF[row] = {}
    return _REF[row]


def gates(row, m):
    """{metric: (value, passes)} for the row's gated metrics."""
    g = {}
    if row != "E1-META":
        g["rendered_fps"] = (m["rendered_fps"], m["rendered_fps"] is not None and m["rendered_fps"] >= 59.5)
        g["retroarch_fps"] = (m["retroarch_fps"], m["retroarch_fps"] is not None and m["retroarch_fps"] >= 59.9)
        g["capture_fps"] = (m["capture_fps"], m["capture_fps"] is not None and abs(m["capture_fps"] - 60) <= 0.5)
        g["spikes_20ms_per_min"] = (m["spikes_20ms_per_min"], m["spikes_20ms_per_min"] is not None and m["spikes_20ms_per_min"] < 200)
        g["stale_drops_per_min"] = (m["stale_drops_per_min"], m["stale_drops_per_min"] is not None and m["stale_drops_per_min"] < 20)
        g["encoder_dupdrop_per_min"] = (m["encoder_dupdrop_per_min"], m["encoder_dupdrop_per_min"] is not None
                                        and m["encoder_dupdrop_per_min"] <= 0.2)
    if row in ("E1-CONC", "E1-META"):
        g["grabs_failed"] = (m["grabs_failed"], m["grabs_failed"] == 0)
    if row == "E1-META":
        g["grabs_ok_min_per_channel"] = (m["grabs_ok_min_per_channel"], (m["grabs_ok_min_per_channel"] or 0) >= 20)
        g["guide_serves"] = (m["guide_serves"], m["guide_serves"] is True)
    ref = reference(row)
    for n, tol in REL.items():
        if n not in g or ref.get(n) is None:
            continue
        r = ref[n]
        ref_fails = not gates_abs_pass(n, r)
        if ref_fails and g[n][0] is not None:
            v = g[n][0]
            ok = (v <= r + tol) if n == "encoder_dupdrop_per_min" else (v >= r - tol and (n != "capture_fps" or v <= 60.5))
            g[n] = (v, ok)
    return g


def gates_abs_pass(n, v):
    return {"rendered_fps": v >= 59.5, "retroarch_fps": v >= 59.9, "capture_fps": abs(v - 60) <= 0.5,
            "encoder_dupdrop_per_min": v <= 0.2}[n]


def relative_gates():
    """{row: {metric: reference value}} -- where the reference-relative clause applies."""
    out = {}
    for row in ROWS:
        ref = reference(row)
        out[row] = {n: ref[n] for n in REL if ref.get(n) is not None and not gates_abs_pass(n, ref[n])}
    return out


def judge(row, s, control_loss, rd=None):
    """PASS / FAIL / INCONCLUSIVE, with the failing metrics. control_loss: the night's control's video loss/min."""
    if s is None or s.get("status") != "OK" or not s.get("window"):
        return {"verdict": "FAIL", "why": "never reached PLAYING / never ran (after the runner's two replacements)",
                "failing": ["reaches PLAYING / runs"], "metrics": {}, "gates": {}}
    m = metrics(s, rd)
    g = gates(row, m)
    missing = [n for n, (v, ok) in g.items() if v is None]
    failing = [n for n, (v, ok) in g.items() if v is not None and not ok]
    out = {"metrics": m, "gates": {n: {"value": v, "passes": ok} for n, (v, ok) in g.items()}, "failing": failing,
           "missing": missing, "control_loss_per_min": control_loss}
    link_bad = control_loss is not None and control_loss >= 10
    if failing and all(n in LINK for n in failing) and link_bad:
        out.update(verdict="INCONCLUSIVE", why="fails only on link-observed metrics while the control fails D-BASE's loss row")
    elif failing:
        out.update(verdict="FAIL", why="fails " + ", ".join(failing))
    elif missing:
        out.update(verdict="INCONCLUSIVE", why="a gated metric could not be read: " + ", ".join(missing))
    else:
        out.update(verdict="PASS", why="every gated metric holds")
    return out


# ---------------------------------------------------------------- running
def load():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"steps": [], "runs": [], "control": None}


def save(st):
    json.dump(st, open(STATE + ".tmp", "w"), indent=1, default=str)
    os.replace(STATE + ".tmp", STATE)


def run_step(st, label, items):
    """items: [(row, cons)] -> one suite invocation; each run judged against the control."""
    done = {x["label"] for x in st["steps"]}
    if label in done:
        return [r for r in st["runs"] if r["step"] == label]
    plan = ",".join(f"{r}:1:120::{'+'.join(c)}" for r, c in items)
    log(f"step {label}: {[(r, '+'.join(c)) for r, c in items]}")
    t0 = time.time()
    with open(os.path.join(HERE, "runs_console.log"), "a") as fh:
        subprocess.run([sys.executable, SUITE, "run", "--out", OUT, "--prereg", PRE, "--e2", "--window", "1200",
                        "--gap", "120", "--plan", plan], stdout=fh, stderr=subprocess.STDOUT)
    if os.path.exists(os.path.join(OUT, "final_state.json")):
        shutil.copy(os.path.join(OUT, "final_state.json"), os.path.join(OUT, f"final_state_{label}.json"))
    res = []
    for r, c in items:
        sp = latest_summary(r, c)
        s = json.load(open(os.path.join(HERE, sp))) if sp else None
        if st["control"] is None and r == "E1-PS1-STREAM" and c == ["CPUQuota=400%"] + PERIOD:
            st["control"] = {"summary": sp, "video_loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min") if s else None}
        j = judge(r, s, (st["control"] or {}).get("video_loss_per_min"),
                  os.path.dirname(os.path.join(HERE, sp)) if sp else None)
        rec = {"step": label, "row": r, "constraint": c, "summary": sp, "verdict": j["verdict"], "why": j["why"],
               "failing": j["failing"], "judged": j}
        st["runs"].append(rec)
        res.append(rec)
        log(f"  {r} {'+'.join(c)}: {j['verdict']} ({j['why']})")
    st["steps"].append({"label": label, "items": [[r, c] for r, c in items], "s": round(time.time() - t0)})
    save(st)
    return res


def final_verdicts(st, ladder):
    """{(row, step_key): final verdict} -- a repeat's verdict replaces its INCONCLUSIVE original."""
    v = {}
    for r in st["runs"]:
        if not r["step"].startswith(ladder):
            continue
        key = (r["row"], r["step"].replace("_repeat", "").split(":")[-1])
        v[key] = r["verdict"]
    return v


def floor_of(order, verdicts, row):
    fl, cond = None, []
    for step in order:
        x = verdicts.get((row, str(step)))
        if x == "PASS":
            fl = step
        elif x == "INCONCLUSIVE":
            cond.append(step)
        else:      # FAIL or not run
            break
    return fl, cond


def repeats(st, ladder, order, cons_of):
    """The INCONCLUSIVE runs of a ladder, repeated once at its end (one invocation, ladder order)."""
    v = final_verdicts(st, ladder)
    items = [(row, cons_of(row, step)) for step in order for row in ROWS if v.get((row, str(step))) == "INCONCLUSIVE"]
    if items:
        # each repeated run gets its own step label so the verdict maps back to its step
        for row, c in items:
            step = next(s for s in order if cons_of(row, s) == c)
            run_step(st, f"{ladder}_repeat:{step}:{row}", [(row, c)])
            st["runs"][-1]["step"] = f"{ladder}_repeat:{step}"
            save(st)


def main(argv):
    st = load()
    if argv[:1] == ["judge"]:
        for r in st["runs"]:
            s = json.load(open(os.path.join(HERE, r["summary"]))) if r["summary"] else None
            j = judge(r["row"], s, (st["control"] or {}).get("video_loss_per_min"),
                      os.path.dirname(os.path.join(HERE, r["summary"])) if r["summary"] else None)
            print(r["step"], r["row"], j["verdict"], j["why"])
        return 0
    if argv[:1] != ["run"]:
        print(__doc__)
        return 2
    log("start; state", "resumed" if st["steps"] else "new")
    # ---- the CPU ladder
    active = list(ROWS)
    for q in CPU:
        if not active:
            break
        res = run_step(st, f"cpu:{q}", [(r, [f"CPUQuota={q}%"] + PERIOD) for r in ROWS if r in active])
        for x in res:
            if x["verdict"] == "FAIL":
                active.remove(x["row"])
    st["cpu_ladder_ended"] = {"remaining_rows_after_100": active}
    repeats(st, "cpu", CPU, lambda row, q: [f"CPUQuota={q}%"] + PERIOD)
    v = final_verdicts(st, "cpu")
    st["cpu_floor"] = {r: dict(zip(("floor", "inconclusive_steps"), floor_of(CPU, v, r))) for r in ROWS}
    save(st)
    log("CPU floors:", json.dumps(st["cpu_floor"]))
    # ---- the memory ladder, one CPU step above each row's CPU floor (unset above 400 % or with no CPU floor)
    above = {}
    for r in ROWS:
        fl = st["cpu_floor"][r]["floor"]
        above[r] = None if fl is None or CPU.index(fl) == 0 else CPU[CPU.index(fl) - 1]
    st["memory_cpu_quota"] = above
    save(st)
    cons_m = lambda row, m: ([f"CPUQuota={above[row]}%"] + PERIOD if above[row] else []) + [f"MemoryMax={m}"]
    active = list(ROWS)
    for m in MEM:
        if not active:
            break
        res = run_step(st, f"mem:{m}", [(r, cons_m(r, m)) for r in ROWS if r in active])
        for x in res:
            if x["verdict"] == "FAIL":
                active.remove(x["row"])
    repeats(st, "mem", MEM, cons_m)
    v = final_verdicts(st, "mem")
    st["memory_floor"] = {r: dict(zip(("floor", "inconclusive_steps"), floor_of(MEM, v, r))) for r in ROWS}
    save(st)
    log("memory floors:", json.dumps(st["memory_floor"]))
    log("ladder done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
