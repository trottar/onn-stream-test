#!/usr/bin/env python3
"""E3-R2 §1 -- the offline replay, made faithful where the records allow (the first half of the bar,
e3_r2_preregistration.txt). Reads E3-R1's reconstructed timelines (../e3_r1_2026-10-08/timelines.json, read-only;
R1's own scripts are not run). -> replay.json, replay.md in this dir.

R1's model (its e3_r1_replay.py docstring), unchanged:
- controller channel, per second: silent fraction s (ctrl_gap_s_est, from the 1-s sampler's rx packets/s). Contiguous
  silence is an UPPER BOUND: a run opens with a partial second (its silence placed at that second's end), continues
  through seconds with s >= 0.95 and may close with a partial second (its silence placed at its start). Where no
  sampler ran (the R3/R3b real drops) the channel is continuous when every heartbeat in +/-10 s arrived within 0.5 s
  of its expected time (the nft rule and R3's substitute stopped host->client traffic only), else "no data".
- today's controller rule fires when a run first exceeds 1.0 s (fire time = run start + 1.0 s); v2's when it exceeds
  5.0 s and is still over it 0.25 s later (fire = run start + 5.25 s).
- the client's own detector (client_* triggers) is the client's and unchanged by v2: both rules replay it as the
  recorded post (fire time = the recorded at_utc).

THE FIX (R1 §3, "a replay-model defect"): the recovery state of NEIGHBOURING events is carried. Every recorded
recovery line in the event's rows BEFORE its own recorded time (t < 0) moves the replayed state: desync_pause and
gave_up_* -> paused, resumed / session_started -> PLAYING, session_ended / ended_* -> ended. A replayed controller
firing whose time falls while that state is not PLAYING does not happen, and that silence episode does not fire later
either (the receive loop reports once per episode; the state machine ignores it when not PLAYING). Rows at t >= 0
are the event's own consequences under today's rule and are not carried. Nothing else changes.

THE EXIT (part 3), replayed for the four controller false pauses (r4), conservatively at 1-s resolution:
- return_s: the end of the controller silent run in which the recorded pause fired (the packets' first return);
- a_s: (a) -- the end of the first second k at or after return_s's second with s_k < 0.5 and s_(k+1) < 0.5 (packets
  flowing on two checks >= 250 ms apart, taken at the later bound);
- resume_s: (b) -- the end (t + 1) of the first row t >= a_s carrying a heartbeat with out_age_ms <= 300; for
  E2-1080P r1, which has no heartbeat log, the client telemetry's out_gap_ms <= 300 in a row t >= a_s (the
  pre-registered substitute);
- r4 holds for the event when resume_s - return_s <= 10 s.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TL = os.path.join(HERE, "..", "e3_r1_2026-10-08", "timelines.json")
DESYNC_S, V2_S, CONFIRM_S = 1.0, 5.0, 0.25
EXIT_OUT_MS = 300
EXIT_WITHIN_S = 10.0
EXCLUDED_R1 = {"S1-CONC-r2a": "resolution limit of the 1-s records (R1 §3): a ~1.0-s silence across two sampler "
                              "seconds whose catch-up burst lands in the same seconds; not reproducible from them"}
CONTROLLER_FALSE = ["E2-1080P-r1", "S1-CONC-r1b", "S1-CONC-r2a", "A2-PS1-r1"]
CLIENT_FALSE = ["S1-control", "S1-CONC-r1a", "S1-CONC-r2b"]
REAL = ["R3b-N3", "R3b-N15", "R3b-N15b", "R3b-N150", "R3b-E30", "R3-F3", "R3-F15", "R3-F150"]
NOFIRE = ["R3b-N05", "R3-F05"]
MOVE = {"desync_pause": "PAUSED", "gave_up_saved": "PAUSED", "resumed": "PLAYING", "session_started": "PLAYING",
        "session_ended": "ENDED", "ended_after_link_loss": "ENDED"}


def ctrl_runs(rows):
    if not any("ctrl_gap_s_est" in r for r in rows):
        return None
    runs, start, length = [], None, 0.0
    for r in rows:
        s = r.get("ctrl_gap_s_est", 0.0) or 0.0
        k = r["t"]
        if start is None:
            if s > 0:
                start, length = k + 1 - s, s
        elif s >= 0.95:
            length += s
        else:
            length += s
            runs.append((start, length))
            start, length = None, 0.0
    if start is not None:
        runs.append((start, length))
    return runs


def hb_continuous(rows):
    d = [r["hb"].get("arrival_delay_s") for r in rows if "hb" in r and -10 <= r["t"] <= 10]
    d = [x for x in d if x is not None]
    return bool(d) and max(d) < 0.5


def carried(rows):
    """[(t, state)] state changes from recorded lines before the event's own time (t < 0)"""
    ch = []
    for r in rows:
        if r["t"] >= 0:
            break
        for x in r.get("rec") or []:
            if x.get("event") in MOVE:
                ch.append((r["t"], MOVE[x["event"]]))
    return ch


def state_at(ch, x):
    st = "PLAYING"
    for t, s in ch:
        if t <= x:
            st = s
    return st


def replay(ev, carry=True):
    s, rows = ev["summary"], ev["rows"]
    recorded_client = s["trigger"] if s["trigger"] and s["trigger"].startswith("client_") else None
    runs = ctrl_runs(rows)
    if runs is None:
        runs = [] if hb_continuous(rows) else None
    ch = carried(rows) if carry else []
    out = {"carried_state_changes": ch}
    for rule, thr, conf in (("today", DESYNC_S, 0.0), ("v2", V2_S, CONFIRM_S)):
        fires, suppressed = [], []
        if recorded_client:
            fires.append((0.0, recorded_client))
        if runs is None:
            ctl = "no data"
        else:
            ctl = []
            for st, ln in runs:
                if ln > thr + conf:
                    at = round(st + thr + conf, 2)
                    (ctl if state_at(ch, at) == "PLAYING" else suppressed).append((at, "controller_silence"))
            fires += ctl
        fires.sort()
        out[rule] = {"first_fire": fires[0] if fires else None, "all": fires[:6], "controller": ctl,
                     "suppressed_by_carried_state": suppressed}
    out["controller_runs_s"] = [(round(a, 2), round(b, 2)) for a, b in runs] if runs else runs
    return out


def exit_replay(ev):
    rows = ev["rows"]
    byt = {r["t"]: r for r in rows}
    runs = ctrl_runs(rows) or []
    # the run in which the recorded pause (t = 0) fired: today's fire = start + 1.0 s, at or before 0 (+/- 2 s)
    cand = [(st, ln) for st, ln in runs if ln > DESYNC_S and abs(st + DESYNC_S - 0.0) <= 2.0]
    if not cand:
        # S1-CONC-r2a: the silence is not resolvable at 1 s; take the run overlapping t = 0, or the second itself
        ov = [(st, ln) for st, ln in runs if st <= 0.0 <= st + ln + 1.0]
        cand = ov or [(-1.0, 1.0)]
        basis = "overlapping run (not resolvable at 1 s)"
    else:
        basis = "the firing run"
    st, ln = min(cand, key=lambda x: abs(x[0] + DESYNC_S))
    ret = st + ln
    s = lambda k: (byt.get(k) or {}).get("ctrl_gap_s_est", 0.0) or 0.0
    k = int(ret // 1)
    while k < 60 and not (s(k) < 0.5 and s(k + 1) < 0.5):
        k += 1
    a = k + 1.0
    res, via = None, None
    for r in rows:
        if r["t"] < a:
            continue
        if "hb" in r and r["hb"].get("out_age_ms") is not None and 0 <= r["hb"]["out_age_ms"] <= EXIT_OUT_MS:
            res, via = r["t"] + 1.0, f"heartbeat out_age_ms {r['hb']['out_age_ms']} at t={r['t']}"
            break
        if ev["summary"]["id"] == "E2-1080P-r1" and "tel" in r and r["tel"].get("out_gap_ms") is not None \
                and r["tel"]["out_gap_ms"] <= EXIT_OUT_MS:
            res, via = r["t"] + 1.0, f"telemetry out_gap_ms {r['tel']['out_gap_ms']} at t={r['t']} (substitute)"
            break
    return {"basis": basis, "firing_run": [round(st, 2), round(ln, 2)], "return_s": round(ret, 2), "a_s": a,
            "resume_s": res, "via": via, "resume_after_return_s": None if res is None else round(res - ret, 2),
            "holds": res is not None and res - ret <= EXIT_WITHIN_S}


def main():
    T = json.load(open(TL))
    res = {}
    md = ["| id | kind | recorded | today first fire (R1 model) | today first fire (fixed) | v2 controller fires (fixed) | carried state |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for eid, ev in T.items():
        s = ev["summary"]
        r = replay(ev)
        r_old = replay(ev, carry=False)
        rec = (0.0, s["trigger"]) if s["trigger"] else None
        tf = r["today"]["first_fire"]
        r["recorded"], r["kind"] = rec, s["kind"]
        r["today_first_fire_r1_model"] = r_old["today"]["first_fire"]
        r["today_faithful"] = (tf is None) if rec is None else (tf is not None and tf[1] == rec[1] and abs(tf[0] - rec[0]) <= 2.0)
        res[eid] = r
        md.append(f"| {eid} | {s['kind']} | {rec} | {r_old['today']['first_fire']} | {tf} | {r['v2']['controller']} | {r['carried_state_changes'] or '-'} |")
    gated = [k for k, v in res.items() if v["kind"] in ("false", "real", "real-nofire") and k not in EXCLUDED_R1]
    bar = {"r1_today_faithful": {k: res[k]["today_faithful"] for k in gated},
           "r1_excluded_by_name": EXCLUDED_R1,
           "r1_outside_suite_reported": {k: res[k]["today_faithful"] for k, v in res.items() if v["kind"] == "false-outside"},
           "r1_S1-CONC-r2a_reported": {"today_first_fire": res["S1-CONC-r2a"]["today"]["first_fire"]}}
    bar["r1"] = all(bar["r1_today_faithful"].values())
    bar["r2_v2_within_2s_of_today"] = {k: (res[k]["v2"]["first_fire"] is not None and res[k]["today"]["first_fire"] is not None
                                           and res[k]["v2"]["first_fire"][0] - res[k]["today"]["first_fire"][0] <= 2.0) for k in REAL}
    bar["r2_reported_v2_on_N05_F05"] = {k: res[k]["v2"]["first_fire"] for k in NOFIRE}
    bar["r2"] = all(bar["r2_v2_within_2s_of_today"].values())
    bar["r3_v2_controller_fires_in_window"] = {k: (res[k]["v2"]["controller"]) for k in CONTROLLER_FALSE}
    bar["r3"] = all(isinstance(v, list) and not v for v in bar["r3_v2_controller_fires_in_window"].values())
    bar["r3_client_pauses_reported"] = {k: res[k]["v2"]["first_fire"] for k in CLIENT_FALSE}
    ex = {k: exit_replay(T[k]) for k in CONTROLLER_FALSE}
    bar["r4_exit"] = ex
    bar["r4"] = all(v["holds"] for v in ex.values())
    bar["replay_bar_holds"] = bar["r1"] and bar["r2"] and bar["r3"] and bar["r4"]
    json.dump({"events": res, "bar": bar}, open(os.path.join(HERE, "replay.json"), "w"), indent=1)
    ex_md = ["| controller pause | basis | firing run (start s, len s) | packets back (s) | (a) by (s) | resume (s) | via | resume - back (s) | r4 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, v in ex.items():
        ex_md.append(f"| {k} | {v['basis']} | {v['firing_run']} | {v['return_s']} | {v['a_s']} | {v['resume_s']} | {v['via']} | "
                     f"{v['resume_after_return_s']} | {'holds' if v['holds'] else 'FAILS'} |")
    summ = {k: bar[k] for k in ("r1", "r2", "r3", "r4", "replay_bar_holds")}
    open(os.path.join(HERE, "replay.md"), "w").write(
        "# E3-R2 replay (fixed model)\n\n" + "\n".join(md) + "\n\n## r4, the exit\n\n" + "\n".join(ex_md) +
        "\n\n```\n" + json.dumps({k: v for k, v in bar.items() if k != "r4_exit"}, indent=1) + "\n```\n")
    print("\n".join(md)); print("\n".join(ex_md)); print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
