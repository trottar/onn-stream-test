#!/usr/bin/env python3
"""D-BASE-T3 analysis: where the warm-state audio loss happens.

Inputs: runs/heartbeat_T3.jsonl (client cumulative audio_lost_packets and
video lost_packets, 2 s), runs/socket_T3.jsonl (the onn's /proc/net/udp6
rows for 48101 audio / 48100 video: rx_queue, drops; 2 s), t3_host.jsonl
(the sender's packets_sent / send_errors / underflows, host kernel UDP
SndbufErrors, eno1; 2 s), t3_onn_stack.jsonl (the onn's /proc/net/snmp Udp
and wlan0 rx counters; 10 s; added during the run), t2_samples.jsonl
(temperatures; 10 s), runs/report_T3.json.

Fixed before the data:
  * a MINUTE = 30 heartbeat deltas; the STEP minute = the first minute with
    audio loss >= 30 that follows at least 3 minutes < 10 (the cold
    plateau). AFTER = from the step minute's start to the session end.
  * other counters are differenced between the samples nearest (<= 3 s) the
    heartbeat rows bounding a window.
  * sequence advance at the host = packets_sent + send_errors (the sender
    increments the sequence for both); host-side loss = send_errors + the
    host kernel's Udp SndbufErrors (a qdisc/sndbuf drop behind a successful
    sendto). A 2 s tick with < 390 packets sent is a timer OVERRUN.

Readings (handoffs/D-BASE-T3_TASK.md), checked in order:
  NOT REPRODUCED  no step within the session (no minute >= 30 after a
                  3-minute plateau < 10)
  ONN RECEIVE     AFTER: audio-socket drops >= 70 % of the client's loss,
                  video-socket drops ~0
  HOST SENDER     AFTER: host-side loss >= 70 % of the client's loss, or
                  overruns cluster at the step, while the audio socket's
                  drops stay < 10 % of the loss
  AIR             AFTER: audio-socket drops < 10 % and host-side loss < 10 %
                  of the client's loss
  otherwise       MIXED
"""
import json, os, statistics as st
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")


def ts(s):
    fmt = "%Y-%m-%dT%H:%M:%S.%f" if "." in s[:23] else "%Y-%m-%dT%H:%M:%S"
    return datetime.strptime(s[:23].rstrip("Z"), fmt).replace(tzinfo=timezone.utc).timestamp()


def load(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


hb = [x for x in load(os.path.join(R, "heartbeat_T3.jsonl")) if "audio_lost_packets" in x]
sock = [x for x in load(os.path.join(R, "socket_T3.jsonl")) if x.get("sockets")]
host = [x for x in load(os.path.join(HERE, "t3_host.jsonl")) if (x.get("sender") or {}).get("packets_sent") is not None]
stack = load(os.path.join(HERE, "t3_onn_stack.jsonl"))
heat = load(os.path.join(HERE, "t2_samples.jsonl"))
for x in host:   # snmp keys carry dots ("Udp.SndbufErrors"): flatten
    x["snmp_sndbuf"] = (x.get("snmp") or {}).get("Udp.SndbufErrors")
for rows, key in ((hb, "received_at_utc"), (sock, "at_utc"), (host, "at_utc"), (stack, "at_utc"), (heat, "at_utc")):
    for x in rows:
        x["_t"] = ts(x[key])


def near(rows, t, tol=3.0):
    best = min(rows, key=lambda x: abs(x["_t"] - t), default=None)
    return best if best is not None and abs(best["_t"] - t) <= tol else None


def get(x, path):
    for k in path.split("."):
        if x is None:
            return None
        x = x.get(k) if isinstance(x, dict) else None
    return x


def delta(rows, path, t0, t1, tol=3.0):
    a, b = near(rows, t0, tol), near(rows, t1, tol)
    va, vb = get(a, path), get(b, path)
    return (vb - va) if va is not None and vb is not None else None


# ---- per minute -------------------------------------------------------
mins = []
for i in range(0, len(hb) - 30, 30):
    g0, g1 = hb[i], hb[i + 30]
    t0, t1 = g0["_t"], g1["_t"]
    th = [h for h in heat if t0 <= h["_t"] < t1]
    def hmean(path):
        v = [get(h, path) for h in th if get(h, path) is not None]
        return round(st.mean(v), 2) if v else None
    mins.append({
        "min": i // 30 + 1, "t0": t0, "t1": t1,
        "utc": datetime.fromtimestamp(t0, timezone.utc).strftime("%H:%M:%S"),
        "client_audio_lost": g1["audio_lost_packets"] - g0["audio_lost_packets"],
        "client_video_lost": g1["lost_packets"] - g0["lost_packets"],
        "client_audio_rx": (g1.get("audio_rx_packets") or 0) - (g0.get("audio_rx_packets") or 0) if "audio_rx_packets" in g1 else None,
        "onn_audio_sock_drops": delta(sock, "sockets.audio_48101.drops", t0, t1),
        "onn_video_sock_drops": delta(sock, "sockets.video_48100.drops", t0, t1),
        "onn_audio_rxq_max": max((get(s, "sockets.audio_48101.rx_queue") or 0 for s in sock if t0 <= s["_t"] < t1), default=None),
        "host_sent": delta(host, "sender.packets_sent", t0, t1),
        "host_send_errors": delta(host, "sender.send_errors", t0, t1),
        "host_underflows": delta(host, "sender.underflows", t0, t1),
        "host_sndbuf_errors": delta(host, "snmp_sndbuf", t0, t1),
        "host_eno1_tx_drop": delta(host, "eno1.tx_drop", t0, t1),
        "onn_udp_rcvbuferrors": delta(stack, "udp_rcvbuferrors", t0, t1, 10),
        "onn_udp_inerrors": delta(stack, "udp_inerrors", t0, t1, 10),
        "onn_wlan_rx_drop": delta(stack, "wlan_rx_drop", t0, t1, 10),
        "onn_wlan_rx_errs": delta(stack, "wlan_rx_errs", t0, t1, 10),
        "onn_cpu_c": hmean("onn.cpu_thermal_c"),
        "opal_soc_c": hmean("opal.soc_temp_c"),
        "host_tctl_c": hmean("host.temps_c.k10temp/Tctl"),
        "host_nvme_s2_c": hmean("host.temps_c.nvme/Sensor 2"),
    })

# overruns: 2 s host ticks with < 390 packets sent
over = []
for a, b in zip(host, host[1:]):
    d, dt = b["sender"]["packets_sent"] - a["sender"]["packets_sent"], b["_t"] - a["_t"]
    if 1.5 < dt < 2.5 and 0 < d < 390 and b["sender"].get("active"):
        over.append((datetime.fromtimestamp(b["_t"], timezone.utc).strftime("%H:%M:%S"), d, round(dt, 2)))

cols = ["min", "utc", "client_audio_lost", "client_video_lost", "onn_audio_sock_drops", "onn_video_sock_drops",
        "onn_audio_rxq_max", "host_sent", "host_send_errors", "host_sndbuf_errors", "host_underflows",
        "onn_udp_rcvbuferrors", "onn_wlan_rx_drop", "onn_wlan_rx_errs", "onn_cpu_c", "opal_soc_c", "host_tctl_c", "host_nvme_s2_c"]
print("== per minute (heartbeat minutes)")
print(" ".join(f"{c[:12]:>12s}" for c in cols))
for m in mins:
    print(" ".join(f"{str(m[c]):>12s}" for c in cols))

step = None
for i, m in enumerate(mins):
    if i >= 3 and m["client_audio_lost"] >= 30 and all(x["client_audio_lost"] < 10 for x in mins[:3]):
        step = m
        break
summary = {"minutes": mins, "overruns": over, "step": None, "reading": None}
print(f"\n== host timer overruns (2 s ticks < 390 sent while active): {len(over)} {over[:12]}")

def total(key, ms):
    v = [m[key] for m in ms if m[key] is not None]
    return sum(v) if v else None

if step is None:
    reading = "NOT REPRODUCED"
    why = [f"no step: minutes {[m['client_audio_lost'] for m in mins]}"]
else:
    after = [m for m in mins if m["min"] >= step["min"]]
    loss = total("client_audio_lost", after)
    sock_a = total("onn_audio_sock_drops", after) or 0
    sock_v = total("onn_video_sock_drops", after) or 0
    host_loss = (total("host_send_errors", after) or 0) + (total("host_sndbuf_errors", after) or 0)
    over_after = [o for o in over if o[0] >= step["utc"]]
    summary["step"] = {"minute": step["min"], "utc": step["utc"], "loss_after": loss,
                       "onn_audio_sock_drops_after": sock_a, "onn_video_sock_drops_after": sock_v,
                       "host_side_loss_after": host_loss, "overruns_after": len(over_after),
                       "onn_udp_rcvbuferrors_after": total("onn_udp_rcvbuferrors", after),
                       "onn_wlan_rx_drop_after": total("onn_wlan_rx_drop", after),
                       "onn_wlan_rx_errs_after": total("onn_wlan_rx_errs", after),
                       "thermal_at_step": {k: step[k] for k in ("onn_cpu_c", "opal_soc_c", "host_tctl_c", "host_nvme_s2_c")}}
    print(f"\n== step: minute {step['min']} ({step['utc']} UTC); after it the client lost {loss}")
    print(f"   onn audio-socket drops {sock_a} ({sock_a / loss:.1%}), video-socket drops {sock_v}")
    print(f"   host send_errors + SndbufErrors {host_loss} ({host_loss / loss:.1%}); overruns after {len(over_after)}")
    print(f"   onn stack after: Udp RcvbufErrors {summary['step']['onn_udp_rcvbuferrors_after']}, "
          f"wlan0 rx_drop {summary['step']['onn_wlan_rx_drop_after']}, rx_errs {summary['step']['onn_wlan_rx_errs_after']}")
    print(f"   thermal at the step: {summary['step']['thermal_at_step']}")
    if sock_a >= 0.7 * loss and sock_v <= 0.05 * max(loss, 1):
        reading, why = "ONN RECEIVE", ["audio-socket drops account for >= 70 %"]
    elif (host_loss >= 0.7 * loss or len(over_after) >= 5) and sock_a < 0.1 * loss:
        reading, why = "HOST SENDER", [f"host-side loss {host_loss}, overruns {len(over_after)}"]
    elif sock_a < 0.1 * loss and host_loss < 0.1 * loss:
        reading, why = "AIR", ["neither end's counters move"]
    else:
        reading, why = "MIXED", [f"socket {sock_a}, host {host_loss}, loss {loss}"]
summary["reading"] = {"reading": reading, "why": why}
print(f"\n== READING: {reading} -- {'; '.join(why)}")

rp = os.path.join(R, "report_T3.json")
if os.path.exists(rp):
    rep = json.load(open(rp))
    a = rep.get("report", rep)["audio"]
    last = host[-1]["sender"] if host else {}
    summary["totals"] = {"client_packets": a["packets"], "client_lost": a["lost_packets"],
                         "host_sent_final": last.get("packets_sent"), "host_send_errors_final": last.get("send_errors")}
    print(f"   totals: client received {a['packets']}, client lost {a['lost_packets']}; "
          f"host sent {last.get('packets_sent')}, send_errors {last.get('send_errors')}")

# thresholds (proposal): readings at the first minute >= 30 and >= 100
thr = {}
for k in ("onn_cpu_c", "opal_soc_c", "host_nvme_s2_c", "host_tctl_c"):
    thr[k] = {"warn_30": next((m[k] for m in mins if m["client_audio_lost"] >= 30), None),
              "act_100": next((m[k] for m in mins if m["client_audio_lost"] >= 100), None)}
summary["thresholds"] = thr
print(f"   thresholds (first minute >= 30 / >= 100): {thr}")
json.dump(summary, open(os.path.join(HERE, "t3_summary.json"), "w"), indent=1)
