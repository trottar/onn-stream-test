#!/usr/bin/env python3
"""LINK-R1 Part 1's reader (read-only over link_r1_2026-10-23/; writes record_read.json and prints the tables).

The session = the recovery log's session_started .. session_ended in runs/logs_run1/ (the window's copy).
  - the link report per heartbeat (BENCH-R3's reader's `placed` map: sequence order, the client's elapsed placed on the
    host clock) -> per UTC minute: RSSI / tx / rx median and min, frequency, standard, post-FEC lost, FEC-unrecoverable
    groups, rendered fps; and the distribution of each link key;
  - the uplink silences >= 250 ms per 10 min and their distribution: B6's gap_distribution.py `measure`, exec'd unedited;
  - hitch seconds per 10 min and the longest run: UX-R3's `evening` / `counts`, exec'd unedited;
  - the Opal (opal/air.jsonl, wlan1, every 60 s, redacted): stations followed between rounds by connected-time continuity;
    the onn's station = the one whose AP->station tx bytes rise most while the session runs (O1's behaviour method,
    no identifier); its row per round: signal, signal avg, tx / rx bitrate, MCS / NSS / width, tx retries / packets as
    deltas (retry rate), tx failed, inactive time; and the radio's channel / utilization / noise.
    python3 -B link_r1_read.py
"""
import collections, hashlib, json, statistics, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent
LD = HERE / "runs/logs_run1"
UX = EV / "ux_r3_2026-10-21/ux_r3_seconds.py"
GD = EV / "b6_2026-10-22/gap_distribution.py"
PINS = {l.split()[1].rsplit("/", 1)[-1]: l.split()[0] for l in (HERE / "tools_at_preregistration_sha256.txt").read_text().splitlines()}


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
g = GDNS["measure"]("LINK-R1 5 GHz", LD, s0, s1)
res["silences"] = {k: g[k] for k in ("streaming_s", "gaps", "per10", "bins", "bins_per10", "max_ms", "gaps_ms")}
res["silences"]["ge_per10"] = {str(h): g["ge_per10"][h] for h in (250, 400, 500, 800, 950, 1000, 1500)}
hrows, _, cover, play_s = UXNS["evening"]({"dir": str(LD), "start": utc(s0)[:19], "end": utc(s1 + 1)[:19]})
res["hitch"] = UXNS["counts"](hrows, play_s)

# ---- the Opal
op = jl(HERE / "opal/air.jsonl")
tracks, prev = {}, []         # track id -> [(round t, station row)]
nid = 0
for r in op:
    t = ts(r["at_utc"])
    cur = []
    for s in r.get("stations") or []:
        ct = s.get("connected_time_s")
        match = None
        for (pt, pid, pct) in prev:
            if ct is not None and pct is not None and abs((ct - pct) - (t - pt)) <= 15:
                match = pid
                break
        if match is None:
            nid += 1
            match = nid
        tracks.setdefault(match, []).append((t, s, r))
        cur.append((t, match, ct))
    prev = cur


def rate(tr, a, b):
    pts = [(t, s.get("tx_bytes")) for t, s, _ in tr if a <= t <= b and s.get("tx_bytes") is not None]
    return (pts[-1][1] - pts[0][1]) * 8 / 1e6 / (pts[-1][0] - pts[0][0]) if len(pts) >= 2 and pts[-1][0] > pts[0][0] else None


rates = {tid: rate(tr, s0, s1) for tid, tr in tracks.items()}
onn = max((tid for tid in rates if rates[tid] is not None), key=lambda tid: rates[tid], default=None)
res["opal"] = {"rounds": len(op), "stations_per_round": [len(r.get("stations") or []) for r in op],
               "tracks": len(tracks), "track_tx_mbit_s_in_session": {str(k): (round(v, 2) if v else v) for k, v in rates.items()},
               "onn_track": onn, "radio": [{"at": r["at_utc"][11:19], "channel": (r.get("airtime") or {}).get("channel"),
                                            "width": (r.get("airtime") or {}).get("width_mhz"),
                                            "util_pct": (r.get("airtime") or {}).get("utilization_pct"),
                                            "noise_dbm": (r.get("airtime") or {}).get("noise_dbm"),
                                            "log_events": len(r.get("log_events") or [])} for r in op]}
srows = []
tr = tracks.get(onn) or []
for (t, s, r), nxt in zip(tr, tr[1:] + [None]):
    row = {"at": r["at_utc"][11:19], "in_session": s0 <= t <= s1, "signal": s.get("signal_dbm"), "signal_avg": s.get("signal_avg_dbm"),
           "tx_mbps": s.get("tx_bitrate_mbps"), "rx_mbps": s.get("rx_bitrate_mbps"), "tx_mcs": s.get("tx_mcs"),
           "tx_nss": s.get("tx_nss"), "tx_width": s.get("tx_width_mhz"), "expected_tput": s.get("expected_tput_mbps"),
           "inactive_ms": s.get("inactive_time_ms")}
    if nxt:
        t2, s2, _ = nxt
        dp = (s2.get("tx_packets") or 0) - (s.get("tx_packets") or 0)
        dr = (s2.get("tx_retries") or 0) - (s.get("tx_retries") or 0)
        df = (s2.get("tx_failed") or 0) - (s.get("tx_failed") or 0)
        row.update({"next_s": round(t2 - t), "tx_pkts_d": dp, "tx_retries_d": dr, "tx_failed_d": df,
                    "retry_rate": round(dr / dp, 4) if dp > 0 else None,
                    "tx_mbit_s": round(((s2.get("tx_bytes") or 0) - (s.get("tx_bytes") or 0)) * 8 / 1e6 / (t2 - t), 2)})
    srows.append(row)
res["opal"]["onn_rows"] = srows
ins_r = [x for x in srows if x["in_session"] and x.get("tx_pkts_d")]
res["opal"]["onn_in_session"] = {
    "signal_med": med([x["signal"] for x in srows if x["in_session"]]),
    "signal_min": min((x["signal"] for x in srows if x["in_session"] and x["signal"] is not None), default=None),
    "tx_mbps_med": med([x["tx_mbps"] for x in srows if x["in_session"]]),
    "rx_mbps_med": med([x["rx_mbps"] for x in srows if x["in_session"]]),
    "retry_rate_overall": round(sum(x["tx_retries_d"] for x in ins_r) / sum(x["tx_pkts_d"] for x in ins_r), 4) if ins_r else None,
    "tx_failed_total": sum(x["tx_failed_d"] for x in ins_r)}

(HERE / "record_read.json").write_text(json.dumps(res, indent=1, default=list) + "\n")
print(json.dumps({k: res[k] for k in ("session", "session_min", "heartbeats", "link_distribution", "post_fec_lost_per_min")}, indent=1))
print("silences", json.dumps({k: res["silences"][k] for k in ("streaming_s", "gaps", "per10", "bins", "max_ms")}))
print("hitch", json.dumps(res["hitch"]))
print("minute | hb | MHz | std | RSSI med/min | tx med/min | rx med/min | lost | unrec | fps")
for m, r in res["per_minute"].items():
    print(m[11:], r["hb"], r["freq_mhz"], r["standard"], r["rssi_med"], r["rssi_min"], r["tx_med"], r["tx_min"], r["rx_med"],
          r["rx_min"], r["post_fec_lost"], r["fec_unrec"], r["fps"], sep=" | ")
print("opal", json.dumps({k: res["opal"][k] for k in ("rounds", "stations_per_round", "tracks", "track_tx_mbit_s_in_session", "onn_track", "onn_in_session")}))
for x in srows:
    print(json.dumps(x))
