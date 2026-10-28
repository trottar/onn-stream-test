#!/usr/bin/env python3
"""G-A7's reader (G-A5's g_a5_read.py, itself G-A4's g_a4_read.py plus restart_fast_config and the restart_fast* rows;
G-A7 adds restart_fast_unlock_config and the heartbeats' link_notice; read-only over g_a7_2026-10-27/;
writes record_read.json and prints the tables).
  - the recovery log: link_recovery_config and the six module config rows (first after session_started's wire),
    state_saved / holds / stall rows with their times, the teardown's session_end_bye / state_save_skipped;

The session = the recovery log's session_started .. session_ended in runs/logs_run1/ (the window's copy).
  - the link report per heartbeat (BENCH-R3's reader's `placed` map: sequence order, the client's elapsed placed on the
    host clock) -> per UTC minute: RSSI / tx / rx median and min, frequency, standard, post-FEC lost, FEC-unrecoverable
    groups, rendered fps; and the distribution of each link key;
  - the uplink silences >= 250 ms per 10 min and their distribution: B6's gap_distribution.py `measure`, exec'd unedited;
  - hitch seconds per 10 min and the longest run: UX-R3's `evening` / `counts`, exec'd unedited;
  (B6's and UX-R3's tools are asserted against LINK-R1's pins: the same files.)
    python3 -B g_a3_read.py
"""
import collections, hashlib, json, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
LD = HERE / "runs/logs_run1"
UX = EV / "ux_r3_2026-10-21/ux_r3_seconds.py"
GD = EV / "b6_2026-10-22/gap_distribution.py"
PINS = {l.split()[1].rsplit("/", 1)[-1]: l.split()[0] for l in (EV / "link_r1_2026-10-23/tools_at_preregistration_sha256.txt").read_text().splitlines()}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ts(v):
    v = str(v)
    return datetime.fromisoformat(v.replace("Z", "+00:00")).timestamp() if ("+" in v or v.endswith("Z")) \
        else datetime.fromisoformat(v).replace(tzinfo=timezone.utc).timestamp()


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def jl(p):
    out = []
    for l in open(p, errors="replace"):
        try:
            out.append(json.loads(l))
        except ValueError:
            pass
    return out


def med(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return statistics.median(xs) if xs else None


assert sha(UX) == PINS["ux_r3_seconds.py"], "ux_r3_seconds.py changed"
assert sha(GD) == PINS["gap_distribution.py"], "gap_distribution.py changed"
src = UX.read_text()
UXNS = {"__file__": str(UX)}
exec(compile(src[:src.index("out, L = {}, []")], str(UX), "exec"), UXNS)
gsrc = GD.read_text()
GDNS = {"__file__": str(GD)}
exec(compile(gsrc[:gsrc.index("R1 = EV /")], str(GD), "exec"), GDNS)

rec = jl(LD / "native_stream_recovery.log")
s0 = next(ts(r["at_utc"]) for r in rec if r.get("event") == "session_started")
s1 = next(ts(r["at_utc"]) for r in reversed(rec) if r.get("event") == "session_ended")
res = {"session": [utc(s0), utc(s1)], "session_min": round((s1 - s0) / 60, 2)}

# ---- the heartbeats, placed (BENCH-R3's map)
hb = [h for h in jl(LD / "native_stream_heartbeat.log") if "sequence" in h and "elapsed_ms" in h]
hb = sorted(hb, key=lambda h: h["sequence"])
sessions = sum(1 for x, y in zip(hb, hb[1:]) if y["sequence"] <= x["sequence"]) + 1
off = statistics.median(ts(h["received_at_utc"]) * 1000 - h["elapsed_ms"] for h in hb)
for h in hb:
    h["_t"] = (off + h["elapsed_ms"]) / 1000
late = [{"seq": h["sequence"], "late_s": round(ts(h["received_at_utc"]) - h["_t"], 1)} for h in hb
        if ts(h["received_at_utc"]) - h["_t"] > 2.0]
ins = [h for h in hb if s0 - 5 <= h["_t"] <= s1 + 5]
KEYS = ("link_frequency_mhz", "link_wifi_standard", "link_rssi_dbm", "link_tx_mbps", "link_rx_mbps")
res["heartbeats"] = {"in_session": len(ins), "with_all_link_keys": sum(1 for h in ins if all(k in h for k in KEYS)),
                     "client_sessions": sessions, "late_gt2s": late}
res["link_distribution"] = {k: dict(sorted(collections.Counter(h.get(k) for h in ins if k in h).items()))
                            for k in KEYS}
rows = {}
for h in ins:
    r = rows.setdefault(utc(h["_t"])[:16], {"hb": 0, "rssi": [], "tx": [], "rx": [], "f": set(), "std": set(),
                                             "lost": 0, "unrec": 0, "rendered": 0, "s": 0.0})
    r["hb"] += 1
    for k, x in (("rssi", "link_rssi_dbm"), ("tx", "link_tx_mbps"), ("rx", "link_rx_mbps")):
        if isinstance(h.get(x), (int, float)):
            r[k].append(h[x])
    if "link_frequency_mhz" in h:
        r["f"].add(h["link_frequency_mhz"])
    if "link_wifi_standard" in h:
        r["std"].add(h["link_wifi_standard"])
for x, y in zip(ins, ins[1:]):
    if y["sequence"] <= x["sequence"]:
        continue
    r = rows[utc(y["_t"])[:16]]
    d = lambda k: max(0, (y.get(k) or 0) - (x.get(k) or 0))
    r["lost"] += d("lost_packets")
    r["unrec"] += d("fec_unrecoverable_groups")
    r["rendered"] += d("rendered_frames")
    r["s"] += (y["elapsed_ms"] - x["elapsed_ms"]) / 1000
res["per_minute"] = {m: {"hb": r["hb"], "freq_mhz": sorted(r["f"]), "standard": sorted(r["std"]),
                         "rssi_med": med(r["rssi"]), "rssi_min": min(r["rssi"], default=None),
                         "tx_med": med(r["tx"]), "tx_min": min(r["tx"], default=None),
                         "rx_med": med(r["rx"]), "rx_min": min(r["rx"], default=None),
                         "post_fec_lost": r["lost"], "fec_unrec": r["unrec"],
                         "fps": round(r["rendered"] / r["s"], 1) if r["s"] else None} for m, r in sorted(rows.items())}
tot_lost = sum(r["post_fec_lost"] for r in res["per_minute"].values())
res["post_fec_lost_per_min"] = round(tot_lost / ((s1 - s0) / 60), 1)

# ---- silences (B6) and hitches (UX-R3)
g = GDNS["measure"]("G-A7 twelve lines", LD, s0, s1)
res["silences"] = {k: g[k] for k in ("streaming_s", "gaps", "per10", "bins", "bins_per10", "max_ms", "gaps_ms")}
res["silences"]["ge_per10"] = {str(h): g["ge_per10"][h] for h in (250, 400, 500, 800, 950, 1000, 1500)}
hrows, _, cover, play_s = UXNS["evening"]({"dir": str(LD), "start": utc(s0)[:19], "end": utc(s1 + 1)[:19]})
res["hitch"] = UXNS["counts"](hrows, play_s)

# ---- the recovery log's link-recovery rows (G-A4)
CFG = ("restart_fast_config", "restart_fast_unlock_config", "link_recovery_config", "input_hold_config", "input_hold_b6_config", "input_hold_b8_config", "input_hold_rewind_config",
       "input_hold_rewind_cores_config", "stall_signal_config", "stall_resume_config")
HOLDS = ("input_hold_carry", "input_hold_handover", "input_release", "desync_pause", "client_ready_after_hold")
w0 = 0                 # the whole copy span: the config rows are logged at the suite's start, ~154 s before session_started
span = [r for r in rec if w0 <= ts(r["at_utc"]) <= s1 + 60]
strip = lambda r: {k: v for k, v in r.items() if k not in ("schema",)}
res["config_rows"] = {c: [strip(r) for r in span if r.get("event") == c] for c in CFG}
res["event_counts"] = dict(sorted(collections.Counter(r.get("event") for r in span).items()))
res["state_saved"] = [strip(r) for r in span if r.get("event") == "state_saved"]
res["holds"] = [strip(r) for r in span if r.get("event") in HOLDS]
res["stall_rows"] = [strip(r) for r in span if str(r.get("event", "")).startswith(("stall_", "fast_ready")) and
                     not str(r.get("event")).endswith("_config")]
res["restart_fast_rows"] = [strip(r) for r in span if str(r.get("event", "")).startswith("restart_fast") and
                          r.get("event") not in ("restart_fast_config", "restart_fast_unlock_config")]
res["link_notice"] = {"heartbeats": len(ins), "values": dict(collections.Counter(h.get("link_notice", "<absent>") for h in ins)),
                      "rows": [strip(r) for r in span if r.get("event") in ("link_notice_shown", "link_notice_cleared")]}
res["teardown"] = [strip(r) for r in span if r.get("event") in ("session_end_bye", "state_save_skipped", "session_ended",
                                                                   "input_hold_skipped_paused")]

(HERE / "record_read.json").write_text(json.dumps(res, indent=1, default=list) + "\n")
print(json.dumps({k: res[k] for k in ("session", "session_min", "heartbeats", "link_distribution", "post_fec_lost_per_min")}, indent=1))
print("config rows", json.dumps({k: [{x: y for x, y in r.items() if x != "at_utc"} for r in v] for k, v in res["config_rows"].items()}))
print("event counts", json.dumps(res["event_counts"]))
print("state_saved", len(res["state_saved"]), "holds", len(res["holds"]), "stall rows", len(res["stall_rows"]))
print("restart_fast rows (not config)", json.dumps(res["restart_fast_rows"]))
print("teardown", json.dumps(res["teardown"]))
print("link_notice", json.dumps(res["link_notice"]))
print("silences", json.dumps({k: res["silences"][k] for k in ("streaming_s", "gaps", "per10", "bins", "max_ms")}))
print("hitch", json.dumps(res["hitch"]))
print("minute | hb | MHz | std | RSSI med/min | tx med/min | rx med/min | lost | unrec | fps")
for m, r in res["per_minute"].items():
    print(m[11:], r["hb"], r["freq_mhz"], r["standard"], r["rssi_med"], r["rssi_min"], r["tx_med"], r["tx_min"], r["rx_med"],
          r["rx_min"], r["post_fec_lost"], r["fec_unrec"], r["fps"], sep=" | ")
