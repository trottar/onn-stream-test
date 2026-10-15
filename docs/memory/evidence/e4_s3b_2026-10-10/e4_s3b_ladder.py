#!/usr/bin/env python3
"""E4-S3B -- the memory floor at 1G, swap off: an unconstrained E1-PS1-STREAM control (the link clause only), then
E1-CONC (CPU unset) and E1-META (CPUQuota=150%) at MemoryMax=1G + MemorySwapMax=0; a row that FAILS ascends to 1536M
(1.5G), then 2G, stopping at its first PASS or at 2G (e4_s3b_preregistration.txt). The pass rule is E4-S3's,
unchanged. A copy of e4_s3_2026-10-10/e4_s3_ladder.py (sha256 below in the pre-registration), changed for this ladder
only; E4-S3's directory is not touched. Beside each step a thread reads the unit's constraint back every 60 s
(constraint_readback.jsonl: the drop-in under load).

    e4_s3b_ladder.py run      control, 1G, the ascents, the INCONCLUSIVE repeats at the end; resumable (ladder.json)
    e4_s3b_ladder.py judge    re-judge every run from ladder.json (read-only)
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
PRE = os.path.join(HERE, "e4_s3b_preregistration.txt")
OUT = os.path.join(HERE, "runs")
STATE = os.path.join(HERE, "ladder.json")
ROWS = ["E1-CONC", "E1-META"]                 # the ladder's rows; the control (E1-PS1-STREAM, unconstrained) first
MEM = ["1G", "1536M", "2G"]                    # ascending: a row climbs only on FAIL
SWAP = ["MemorySwapMax=0"]
CPU_Q = {"E1-PS1-STREAM": None, "E1-SNES-STREAM": 150, "E1-CONC": None, "E1-META": 150}   # E4-S2 memory_cpu_quota
CHANNELS = 6
LINK = {"rendered_fps", "spikes_20ms_per_min", "stale_drops_per_min"}   # observed at the client, across the link


def log(*a):
    line = f"[e4s3b {time.strftime('%H:%M:%SZ', time.gmtime())}] " + " ".join(str(x) for x in a)
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
                    else ("swap" + v) if n == "MemorySwapMax" else ("mem" + v)
                    for n, _, v in (kv.partition("=") for kv in cons))


def latest_summary(row, cons):
    # FIX (07:33Z, ladder_fix.md): an unconstrained run (the control) lives in <row>/, not <row>_/
    d = os.path.join(OUT, f"{row}_{tag(cons)}" if cons else row)
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
         "oom_kill_window": k(s, "key", "cgroup", "memory_events_oom_kill"),
         "memory_events_oom": k(s, "key", "cgroup", "memory_events_oom"),
         "journal_kills": k(s, "kills_in_window", "count"),
         "mainpid_same": (s.get("mainpid_window_start") is not None and s.get("mainpid_window_start") == s.get("mainpid_window_end")),
         "anon_mb_at_peak": k(s, "key", "cgroup", "anon_mb_at_peak"), "file_mb_at_peak": k(s, "key", "cgroup", "file_mb_at_peak"),
         "anon_mb_max": k(s, "key", "cgroup", "anon_mb_max"),
         "memory_psi_some_ms_per_s": k(s, "key", "cgroup", "memory_psi_some_ms_per_s"),
         "memory_psi_full_ms_per_s": k(s, "key", "cgroup", "memory_psi_full_ms_per_s"),
         "pgmajfault": k(s, "key", "cgroup", "pgmajfault"),
         "companion_pss_mb": (k(s, "host", "host", "procs.companion.pss_kb", "mean") or 0) / 1024 or None,
         "bitrate_kbps_min": k(s, "key", "status_poll", "bitrate_kbps_min"), "bitrate_kbps_max": k(s, "key", "status_poll", "bitrate_kbps_max"),
         "transitions": k(s, "key", "decisions", "transitions"),
         "grab_s_median": k(s, "key", "epg", "grab_s_median"), "grabs_ok": k(s, "key", "epg", "grabs_ok"),
         "host_cpu": k(s, "host", "host", "cpu.mean_pct", "mean"),
         "socket_w": k(s, "host", "host", "gpu.socket_power_w", "mean"), "tctl": k(s, "host", "host", "gpu.tctl_c", "mean"),
         "controller_pauses": len(k(s, "key", "recovery", "controller_pauses") or []) if k(s, "key", "recovery") else None,
         "client_pauses": len(k(s, "key", "recovery", "client_pauses") or []) if k(s, "key", "recovery") else None}
    return m


REF_RUNS = os.path.join(HERE, "..", "e4_s1_2026-10-09", "runs")
SUITE_MOD = None


def suite_mod():
    """tools/e1_suite.py as a module (unit_props for the read-back thread); loaded once."""
    global SUITE_MOD
    if SUITE_MOD is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("e1_suite", SUITE)
        SUITE_MOD = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(SUITE_MOD)
    return SUITE_MOD


def readback_thread(label, stop):
    """The drop-in under load: the unit's constraint properties and the cgroup's files every 60 s while a step runs."""
    import threading
    m = suite_mod()

    def run():
        with open(os.path.join(OUT, "constraint_readback.jsonl"), "a") as fh:
            while not stop.wait(60):
                p = m.unit_props()
                fh.write(json.dumps({"at_utc": m.utc(), "step": label, "game_active": m.games_status().get("active"),
                                     **{k: p.get(k) for k in ("MemoryMax", "MemorySwapMax", "CPUQuotaPerSecUSec",
                                                              "memory.max", "memory.swap.max", "cpu.max",
                                                              "dropin_present")}}) + "\n")
                fh.flush()
    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
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
    g["no_oom_kill"] = (m["oom_kill_window"], m["oom_kill_window"] == 0)
    g["no_journal_kill"] = (m["journal_kills"], m["journal_kills"] == 0)
    g["unit_not_restarted"] = (m["mainpid_same"], m["mainpid_same"] is True)
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
    plan = ",".join(f"{r}:1:120::{'+'.join(c)}" if c else f"{r}:1:120" for r, c in items)
    log(f"step {label}: {[(r, '+'.join(c)) for r, c in items]}")
    t0 = time.time()
    import threading
    os.makedirs(OUT, exist_ok=True)
    stop = threading.Event()
    rb = readback_thread(label, stop)
    with open(os.path.join(HERE, "runs_console.log"), "a") as fh:
        subprocess.run([sys.executable, SUITE, "run", "--out", OUT, "--prereg", PRE, "--e2", "--window", "1200",
                        "--gap", "120", "--plan", plan], stdout=fh, stderr=subprocess.STDOUT)
    stop.set()
    rb.join(timeout=90)
    return judge_step(st, label, items, t0)


def judge_step(st, label, items, t0):
    """The step's runs (already run by the suite) judged and recorded -- run_step's second half; also `record`."""
    if os.path.exists(os.path.join(OUT, "final_state.json")):
        shutil.copy(os.path.join(OUT, "final_state.json"), os.path.join(OUT, f"final_state_{label}.json"))
    res = []
    for r, c in items:
        sp = latest_summary(r, c)
        s = json.load(open(os.path.join(HERE, sp))) if sp else None
        if st["control"] is None and r == "E1-PS1-STREAM" and not c:
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
    if argv[:1] == ["repair-control"]:
        # FIX (ladder_fix.md): the control step was recorded with no summary (the <row>_ lookup); re-read it
        for r in st["runs"]:
            if r["step"] == "control":
                sp = latest_summary(r["row"], r["constraint"])
                s = json.load(open(os.path.join(HERE, sp))) if sp else None
                st["control"] = {"summary": sp, "video_loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min") if s else None}
                j = judge(r["row"], s, st["control"]["video_loss_per_min"], os.path.dirname(os.path.join(HERE, sp)) if sp else None)
                r.update(summary=sp, verdict=j["verdict"], why=j["why"], failing=j["failing"], judged=j,
                         repaired="control lookup fixed 07:33Z (ladder_fix.md)")
                log(f"  control repaired: {r['verdict']} ({r['why']}); loss/min {st['control']['video_loss_per_min']}")
        save(st)
        return 0
    if argv[:1] == ["record"]:
        # FIX (ladder_fix.md): a step the suite ran while the driver was stopped -> judged and recorded, not re-run
        label, m = argv[1], argv[1].split(":")[-1]
        if label in {x["label"] for x in st["steps"]}:
            print("already recorded", label)
            return 2
        cons_m = lambda row, mm: ([f"CPUQuota={CPU_Q[row]}%"] if CPU_Q[row] else []) + [f"MemoryMax={mm}"] + SWAP
        judge_step(st, label, [(r, cons_m(r, m)) for r in ROWS], time.time())
        st["steps"][-1]["recorded_after_driver_stop"] = True
        save(st)
        return 0
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
    cons_m = lambda row, m: ([f"CPUQuota={CPU_Q[row]}%"] if CPU_Q[row] else []) + [f"MemoryMax={m}"] + SWAP
    run_step(st, "control", [("E1-PS1-STREAM", [])])

    def need(row):
        """The row's next action (pre-registration §1): ('run', step) after a FAIL below 2G (or nothing run yet),
        ('repeat', step) after a first INCONCLUSIVE, None when the row is settled (PASS, a repeated INCONCLUSIVE, or
        FAIL at 2G)."""
        v = final_verdicts(st, "mem")
        ran = [m for m in MEM if (row, m) in v]
        if not ran:
            return ("run", MEM[0])
        last = ran[-1]
        if v[(row, last)] == "FAIL":
            i = MEM.index(last) + 1
            return ("run", MEM[i]) if i < len(MEM) else None
        if v[(row, last)] == "INCONCLUSIVE" and not any(x["row"] == row and x["step"] == f"mem_repeat:{last}"
                                                        for x in st["runs"]):
            return ("repeat", last)
        return None

    # the ascending ladder: each step runs every row that needs it, in row order, in one suite invocation
    for m in MEM:
        rows = [r for r in ROWS if need(r) == ("run", m)]
        if rows:
            run_step(st, f"mem:{m}", [(r, cons_m(r, m)) for r in rows])
    # then the INCONCLUSIVE repeats (once each), and any climb a repeat's FAIL calls for, until every row is settled
    while True:
        todo = [(r, need(r)) for r in ROWS if need(r)]
        if not todo:
            break
        r, (what, m) = todo[0]
        if what == "repeat":
            run_step(st, f"mem_repeat:{m}:{r}", [(r, cons_m(r, m))])
            if st["runs"][-1]["step"] == f"mem_repeat:{m}:{r}":
                st["runs"][-1]["step"] = f"mem_repeat:{m}"
        else:
            run_step(st, f"mem:{r}:{m}", [(r, cons_m(r, m))])
        save(st)
    v = final_verdicts(st, "mem")
    st["memory_floor"] = {}
    for r in ROWS:
        passed = [m for m in MEM if v.get((r, m)) == "PASS"]
        st["memory_floor"][r] = {"floor": passed[0] if passed else None,
                                 "verdicts": {m: v.get((r, m)) for m in MEM if (r, m) in v}}
    save(st)
    log("memory floors:", json.dumps(st["memory_floor"]))
    log("ladder done")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
