#!/usr/bin/env python3
"""E3-R1 offline replay (the first half of the bar, e3_r1_preregistration.txt): today's trigger rule and v2 over every
reconstructed timeline (timelines.json, e3_r1_timelines.py). Read-only. -> replay.json, replay.md

The model, at the resolution the records have (1-s sampler, 2-s heartbeats), fixed before the replay was run:
- controller channel, per second: silent fraction s = clip(1 - rx_pps / the run's median rx_pps, 0, 1) where a 1-s
  sampler ran. Where none ran (the R3/R3b real drops, the out-of-suite events) the channel is taken as continuous when
  every heartbeat in +/-10 s arrived within 0.5 s of its expected time (R3b's nft rule and R3's substitute stopped only
  host->client traffic; the controller channel, client->host 48102, was untouched); otherwise "no data".
- contiguous controller silence: an UPPER BOUND -- a run may start with a partial second (its silence placed at that
  second's end), continues through seconds with s >= 0.95, and may end with a partial second (its silence placed at
  that second's start). The run's length at each instant is what the receive loop's age would read.
- today's controller rule fires when that length first exceeds DESYNC_MS = 1.0 s (fire time = run start + 1.0 s).
- v2's controller rule fires when the length first exceeds 5.0 s and is still over it 0.25 s later (fire time = run
  start + 5.25 s): CONTROLLER_SILENCE_V2_MS 5000, confirm 250 ms.
- the client's own detector (client_* triggers) is the client's and is unchanged by v2; both rules replay it as the
  recorded post (fire time = the recorded at_utc). The host cannot see the client's output age finer than its 2-s
  heartbeats, so nothing finer is claimed.
- a firing pauses; while paused nothing fires again (the state machine's PLAYING check). The replay looks at the event's
  own +/-60 s and stops at the recorded resume, if any.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DESYNC_S, V2_S, CONFIRM_S = 1.0, 5.0, 0.25


def ctrl_runs(rows):
    """[(start_s, length_s)] upper-bound silent runs on the controller channel, from per-second fractions."""
    if not any("ctrl_gap_s_est" in r for r in rows):
        return None
    runs, start, length = [], None, 0.0
    for r in rows:
        s = r.get("ctrl_gap_s_est", 0.0) or 0.0
        k = r["t"]
        if start is None:
            if s > 0:
                start, length = k + 1 - s, s           # a run opens with this second's silence placed at its end
        elif s >= 0.95:
            length += s                                 # a (nearly) silent second continues it
        else:
            length += s                                 # a partial second closes it (its silence placed at its start)
            runs.append((start, length))
            start, length = None, 0.0
    if start is not None:
        runs.append((start, length))
    return runs


def hb_continuous(rows):
    d = [r["hb"].get("arrival_delay_s") for r in rows if "hb" in r and -10 <= r["t"] <= 10]
    d = [x for x in d if x is not None]
    return bool(d) and max(d) < 0.5


def replay(ev):
    s, rows = ev["summary"], ev["rows"]
    recorded_client = s["trigger"] if s["trigger"] and s["trigger"].startswith("client_") else None
    runs = ctrl_runs(rows)
    if runs is None:
        runs = [] if hb_continuous(rows) else None
    out = {}
    for rule, thr, conf in (("today", DESYNC_S, 0.0), ("v2", V2_S, CONFIRM_S)):
        fires = []
        if recorded_client:
            fires.append((0.0, recorded_client))
        if runs is None:
            ctl = "no data"
        else:
            ctl = [(round(st + thr + conf, 2), "controller_silence") for st, ln in runs if ln > thr + conf]
            fires += ctl
        fires.sort()
        first = fires[0] if fires else None
        out[rule] = {"first_fire": first, "all": fires[:6], "controller": ctl if runs is None else
                     [x for x in fires if x[1] == "controller_silence"]}
    out["controller_runs_s"] = [(round(a, 2), round(b, 2)) for a, b in runs] if runs else runs
    return out


def main():
    T = json.load(open(os.path.join(HERE, "timelines.json")))
    res, md = {}, ["| id | kind | recorded (s, trigger) | today first fire | v2 first fire | controller silent runs (start s, length s) |",
                   "| --- | --- | --- | --- | --- | --- |"]
    for eid, ev in T.items():
        r = replay(ev)
        s = ev["summary"]
        rec = (0.0, s["trigger"]) if s["trigger"] else None
        r["recorded"] = rec
        tf, vf = r["today"]["first_fire"], r["v2"]["first_fire"]
        r["today_faithful"] = (tf is None) if rec is None else \
            (tf is not None and tf[1] == rec[1] and abs(tf[0] - rec[0]) <= 2.0)
        r["kind"] = s["kind"]
        res[eid] = r
        md.append(f"| {eid} | {s['kind']} | {rec} | {tf} | {vf} | {r['controller_runs_s'] if r['controller_runs_s'] is not None else 'no data'} |")
    real = {k: v for k, v in res.items() if v["kind"] == "real"}
    nofire = {k: v for k, v in res.items() if v["kind"] == "real-nofire"}
    false_runs = {"E2-1080P-r1": ["E2-1080P-r1"], "S1-control": ["S1-control"], "S1-CONC-r1": ["S1-CONC-r1a", "S1-CONC-r1b"],
                  "S1-CONC-r2": ["S1-CONC-r2a", "S1-CONC-r2b"], "A2-PS1-r1": ["A2-PS1-r1"]}
    bar = {
        "faithful": all(res[k]["today_faithful"] for k in res if res[k]["kind"] != "false-outside"),
        "faithful_outside_suite": {k: res[k]["today_faithful"] for k in res if res[k]["kind"] == "false-outside"},
        "v2_fires_every_real_drop_within_2s": {k: (v["v2"]["first_fire"] is not None and v["today"]["first_fire"] is not None
                                                  and v["v2"]["first_fire"][0] - v["today"]["first_fire"][0] <= 2.0) for k, v in real.items()},
        "v2_no_fire_where_today_none": {k: v["v2"]["first_fire"] is None for k, v in nofire.items()},
        "v2_fires_on_false_run": {run: any(res[e]["v2"]["first_fire"] is not None for e in evs) for run, evs in false_runs.items()},
        "v2_fires_on_false_event": {e: res[e]["v2"]["first_fire"] for evs in false_runs.values() for e in evs},
    }
    bar["real_ok"] = all(bar["v2_fires_every_real_drop_within_2s"].values()) and all(bar["v2_no_fire_where_today_none"].values())
    bar["false_ok"] = not any(bar["v2_fires_on_false_run"].values())
    bar["replay_bar_holds"] = bar["faithful"] and bar["real_ok"] and bar["false_ok"]
    bar["verdict_replay"] = "INCONCLUSIVE (replay not faithful)" if not bar["faithful"] else ("HOLDS" if bar["replay_bar_holds"] else "FAILS")
    json.dump({"events": res, "bar": bar}, open(os.path.join(HERE, "replay.json"), "w"), indent=1)
    open(os.path.join(HERE, "replay.md"), "w").write("\n".join(md) + "\n\n```\n" + json.dumps(bar, indent=1) + "\n```\n")
    print("\n".join(md)); print(json.dumps(bar, indent=1))


if __name__ == "__main__":
    main()
