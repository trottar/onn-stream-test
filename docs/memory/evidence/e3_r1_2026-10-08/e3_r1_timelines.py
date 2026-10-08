#!/usr/bin/env python3
"""E3-R1 probe, part 1 -- per-second timelines (+/-60 s) around every recorded desync_pause: the five suite runs'
false pauses (and the same type outside the suite on 10-05/10-06), and every real drop (R3b/R3d nft outages; R3's
09-20 substitute outages). Read-only. -> timelines.json, timelines.md

Per second t (relative to the event's at_utc, whole seconds):
  rx_pps / tx_kBps  -- eno1 from the run's 1-s sampler (samples.jsonl) where one ran: rx is the client->host direction,
                       ~450-480 packets/s of it the controller channel; tx is the stream (host->client)
  ctrl_gap_s_est    -- the controller channel's silence inside that second, estimated from rx_pps against the run's
                       median (1 - rx/median, clipped to [0,1]); a whole silent second is 1.0
  hb                -- a heartbeat RECEIVED in that second: its sequence, its arrival delay (received - expected from the
                       client's own elapsed_ms, anchored on the median offset of the +/-60 s), last_output_age_ms (the
                       client's output age), lost_packets delta since the previous heartbeat
  tel               -- the C2 telemetry poll (2 s, runs only): fresh, receiver lost delta, output gap
  rec               -- recovery events in that second (event, trigger, age_ms)
  dec               -- ladder decisions in that second (runs only): event/class
"""
import glob
import json
import os
import statistics
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
EV = os.path.join(REPO, "docs/memory/evidence")


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def jl(path):
    out = []
    try:
        for line in open(path, errors="replace"):
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def live_logs(name):
    rows, seen = [], set()
    for f in sorted(glob.glob(os.path.join(REPO, f"logs/games/stream_log_archive/{name}*"))) + \
            [os.path.join(REPO, f"logs/games/{name}")]:
        try:
            lines = open(f, errors="replace").read().splitlines()
        except OSError:
            continue
        for l in lines:
            if l in seen:
                continue
            seen.add(l)
            try:
                rows.append(json.loads(l))
            except ValueError:
                pass
    return rows


R3 = os.path.join(EV, "d_base_r3_2026-09-20")
R3B = os.path.join(EV, "d_base_r3b_2026-09-21")
# (id, kind, event at_utc, run dir or None, heartbeat source, recovery source, fault on/off epoch or None)
EVENTS = [
    ("E2-1080P-r1", "false", "2026-10-05T23:50:31.718Z", f"{EV}/e2_s1_2026-10-05/runs/E1-PS1-1080P/run1", "live", "live", None),
    ("S1-control", "false", "2026-10-06T03:30:38.177Z", f"{EV}/e3_s1_2026-10-06/runs/E1-PS1-STREAM/run1", "live", "live", None),
    ("S1-CONC-r1a", "false", "2026-10-06T03:50:03.115Z", f"{EV}/e3_s1_2026-10-06/runs/E1-CONC_flag/run1", "live", "live", None),
    ("S1-CONC-r1b", "false", "2026-10-06T03:50:24.116Z", f"{EV}/e3_s1_2026-10-06/runs/E1-CONC_flag/run1", "live", "live", None),
    ("S1-CONC-r2a", "false", "2026-10-06T04:22:51.591Z", f"{EV}/e3_s1_2026-10-06/runs/E1-CONC_flag/run2", "live", "live", None),
    ("S1-CONC-r2b", "false", "2026-10-06T04:24:49.995Z", f"{EV}/e3_s1_2026-10-06/runs/E1-CONC_flag/run2", "live", "live", None),
    ("A2-PS1-r1", "false", "2026-10-07T23:00:07.545Z", f"{EV}/e3_a2_2026-10-07/runs/E1-PS1-STREAM/run1", "live", "live", None),
    ("out-10-05-0401", "false-outside", "2026-10-05T04:01:34.533Z", None, "live", "live", None),
    ("out-10-05-0402", "false-outside", "2026-10-05T04:02:51.851Z", None, "live", "live", None),
    ("out-10-05-1514", "false-outside", "2026-10-05T15:14:46.056Z", None, "live", "live", None),
]
for lab in ("N3", "N15", "N15b", "N150", "E30", "N05"):
    tm = dict(l.strip().split("=", 1) for l in open(os.path.join(R3B, lab, "timings.txt")) if "=" in l)
    on = float(tm["t_on"])
    off = float(tm["t_off"]) if tm.get("t_off") else None
    rec = [r for r in jl(os.path.join(R3B, lab, "recovery_lines.jsonl")) if r.get("event") == "desync_pause"]
    at = rec[0]["at_utc"] if rec else datetime.fromtimestamp(on, timezone.utc).isoformat().replace("+00:00", "Z")
    EVENTS.append((f"R3b-{lab}", "real" if rec else "real-nofire", at, None, os.path.join(R3B, lab, "heartbeat_lines.jsonl"),
                   os.path.join(R3B, lab, "recovery_lines.jsonl"), (on, off)))
for lab, on, off, at in (("F05", "2026-09-20T20:03:00.250Z", "2026-09-20T20:03:01.000Z", None),
                         ("F3", "2026-09-20T20:04:14.356Z", "2026-09-20T20:04:17.446Z", "2026-09-20T20:04:15.658Z"),
                         ("F15", "2026-09-20T20:05:38.341Z", "2026-09-20T20:05:53.591Z", "2026-09-20T20:05:40.068Z"),
                         ("F150", "2026-09-20T20:07:16.748Z", "2026-09-20T20:09:51.343Z", "2026-09-20T20:07:18.369Z")):
    EVENTS.append((f"R3-{lab}", "real" if at else "real-nofire", at or on, None,
                   os.path.join(R3, "native_stream_heartbeat_2026-09-20.log"),
                   os.path.join(R3, "native_stream_recovery_2026-09-20.log"), (t(on), t(off))))


def build(ev, LH, LR):
    eid, kind, at, rd, hbsrc, recsrc, fault = ev
    T = t(at)
    hb = LH if hbsrc == "live" else jl(hbsrc)
    rec = LR if recsrc == "live" else jl(recsrc)
    hb = sorted([r for r in hb if "received_at_utc" in r and abs(t(r["received_at_utc"]) - T) <= 75],
                key=lambda r: r["received_at_utc"])
    # one session: keep the heartbeats whose elapsed_ms is consistent with the event's session
    offs = [t(r["received_at_utc"]) - r["elapsed_ms"] / 1000 for r in hb if isinstance(r.get("elapsed_ms"), (int, float))]
    base = statistics.median(offs) if offs else None
    sam = jl(os.path.join(rd, "samples.jsonl")) if rd else []
    sam = [r for r in sam if abs(t(r["at_utc"]) - T) <= 61]
    rxs = [((r.get("net") or {}).get("eno1") or {}).get("rx_pps") for r in jl(os.path.join(rd, "samples.jsonl"))] if rd else []
    rxs = [x for x in rxs if isinstance(x, (int, float))]
    rx_med = statistics.median(rxs) if rxs else None
    tel = [r for r in jl(os.path.join(rd, "telemetry.jsonl"))] if rd else []
    dec = [r for r in jl(os.path.join(rd, "decisions.jsonl"))] if rd else []
    rows = []
    prev_lost = None
    for k in range(-60, 61):
        s0 = T + k
        row = {"t": k}
        for r in sam:
            if s0 - 0.5 <= t(r["at_utc"]) < s0 + 0.5:
                e = (r.get("net") or {}).get("eno1") or {}
                row["rx_pps"], row["tx_kBps"] = e.get("rx_pps"), e.get("tx_kBps")
                if rx_med and e.get("rx_pps") is not None:
                    row["ctrl_gap_s_est"] = round(min(1.0, max(0.0, 1 - e["rx_pps"] / rx_med)), 2)
        for r in hb:
            ra = t(r["received_at_utc"])
            if s0 <= ra < s0 + 1:
                d = {"seq": r.get("sequence"), "out_age_ms": r.get("last_output_age_ms"), "lost": r.get("lost_packets")}
                if base is not None and isinstance(r.get("elapsed_ms"), (int, float)):
                    d["arrival_delay_s"] = round(ra - (base + r["elapsed_ms"] / 1000), 2)
                row["hb"] = d
        for r in tel:
            if s0 <= t(r["at_utc"]) < s0 + 1 and r.get("fresh"):
                row["tel"] = {"lost_delta": (r.get("receiver") or {}).get("lost_packets_delta"),
                              "out_gap_ms": (r.get("latency") or {}).get("output_gap_ms")}
        for r in rec:
            if s0 <= t(r["at_utc"]) < s0 + 1 and r.get("event") not in ("session_started",):
                row.setdefault("rec", []).append({k2: r.get(k2) for k2 in ("event", "trigger", "age_ms", "state") if r.get(k2) is not None})
        for r in dec:
            ts = r.get("at_utc")
            if ts and s0 <= t(ts) < s0 + 1 and (r.get("event") == "transition" or r.get("kind") == "transition"):
                row.setdefault("dec", []).append(r.get("event") or r.get("kind"))
        rows.append(row)
    # summary facts
    ev_rec = [r for r in rec if abs(t(r["at_utc"]) - T) < 0.6 and r.get("event") == "desync_pause"]
    fired = ev_rec[0] if ev_rec else None
    after = sorted([r for r in rec if 0 < t(r["at_utc"]) - T <= 200 and r.get("event") in
                    ("resumed", "gave_up_saved", "encoder_restart", "session_ended", "desync_pause")], key=lambda r: r["at_utc"])
    hbd = [(r["t"], r["hb"]) for r in rows if "hb" in r]
    gaps = [b[0] - a[0] for a, b in zip(hbd, hbd[1:])]
    near = [h for k, h in hbd if -6 <= k <= 6]
    summ = {"id": eid, "kind": kind, "at_utc": at, "trigger": fired.get("trigger") if fired else None,
            "fired_age_ms": fired.get("age_ms") if fired else None,
            "fault": [datetime.fromtimestamp(x, timezone.utc).isoformat()[11:23] if x else None for x in fault] if fault else None,
            "fault_s": round(fault[1] - fault[0], 2) if fault and fault[1] else None,
            "fired_after_fault_s": round(T - fault[0], 2) if fault and fired else None,
            "then": [(round(t(r["at_utc"]) - T, 1), r["event"], r.get("trigger")) for r in after][:8],
            "max_hb_arrival_gap_s_near": max([b - a for (a, _), (b, _) in zip(hbd, hbd[1:]) if -10 <= a <= 10], default=None),
            "max_hb_arrival_delay_s_near": max([h.get("arrival_delay_s", 0) for h in near], default=None),
            "max_out_age_ms_near": max([h.get("out_age_ms") or 0 for h in near], default=None),
            "out_age_ms_next_hb": next((h.get("out_age_ms") for k, h in hbd if k > 0), None),
            "ctrl_silent_s_est_near": round(sum(r.get("ctrl_gap_s_est", 0) for r in rows if -3 <= r["t"] <= 3), 2) if rd else None,
            "rx_pps_near": [r.get("rx_pps") for r in rows if -3 <= r["t"] <= 4] if rd else None,
            "rx_median": rx_med}
    return {"summary": summ, "rows": rows}


def main():
    LH, LR = live_logs("native_stream_heartbeat.log"), live_logs("native_stream_recovery.log")
    out = {ev[0]: build(ev, LH, LR) for ev in EVENTS}
    json.dump(out, open(os.path.join(HERE, "timelines.json"), "w"), indent=1)
    md = ["# E3-R1 timelines -- summaries (rows +/-60 s per second in timelines.json)", "",
          "| id | kind | trigger, age ms | fault s; fired after s | then (s, event) | ctrl silent s est (-3..+3); rx pps -3..+4 | hb arrival gap max s; delay max s | client out age max ms (+/-6 s); next hb |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k, v in out.items():
        s = v["summary"]
        md.append(f"| {k} | {s['kind']} | {s['trigger']}, {s['fired_age_ms']} | {s['fault_s']}; {s['fired_after_fault_s']} | "
                  f"{'; '.join(f'{a} {b}' + (f' ({c})' if c else '') for a, b, c in s['then'][:5])} | "
                  f"{s['ctrl_silent_s_est_near']}; {s['rx_pps_near']} | {s['max_hb_arrival_gap_s_near']}; {s['max_hb_arrival_delay_s_near']} | "
                  f"{s['max_out_age_ms_near']}; {s['out_age_ms_next_hb']} |")
    open(os.path.join(HERE, "timelines.md"), "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
