#!/usr/bin/env python3
"""G4-W1: read the recorded files, term by term, after the arithmetic was hashed.

Read only. Every input is a file already in the evidence tree, or the copy of the
relay's frame log in ./inputs/ (copied before reading). Writes reading.json and
reading_tables.md next to this script. Run from the repo root:

    python3 -I docs/memory/evidence/g4_w1_2026-10-18/read_files.py
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent

# Constants from the code (read after the hash; §2 of the record):
AUDIO_HEADER = 16          # native_session_io LINUX_HEADER "<4sBBHII"
AUDIO_PAYLOAD = 960        # 240 frames x 2 ch x 2 B (48 kHz s16le)
AUDIO_DATAGRAMS_S = 400    # 200 originals + 200 copies (2/4), every 5 ms tick, silence included
UDP_IP = 28                # UDP 8 + IPv4 20
RTP = 12
FEC_HDR = 23               # native_fec_relay FEC_HEADER "!4sBBHIIBBBHH"
AUDIO_IP = AUDIO_PAYLOAD + AUDIO_HEADER + UDP_IP   # 1,004 B
KIB = 1024                 # tools/e1_sampler.py: tx_kBps = bytes / 1024 / dt
ETH = 14                   # eno1 (a physical device) counts the Ethernet header; tailscale0 (a TUN) does not


def ts(s: str) -> float:
    return datetime.strptime(s.replace("Z", "+00:00"), "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open() if line.strip()]


def in_window(rows, t0, t1, key="at_utc"):
    return [r for r in rows if t0 <= ts(r[key]) < t1]


def mean(xs):
    return statistics.fmean(xs) if xs else None


def med(xs):
    return statistics.median(xs) if xs else None


def iface(samples, name):
    tx_b = [r["net"][name]["tx_kBps"] * KIB for r in samples]
    tx_p = [r["net"][name]["tx_pps"] for r in samples]
    return {
        "n": len(samples),
        "tx_kbps_mean": mean(tx_b) * 8 / 1000,
        "tx_kbps_median": med(tx_b) * 8 / 1000,
        "tx_pps_mean": mean(tx_p),
        "bytes_per_packet": sum(tx_b) / sum(tx_p),
    }


def frames(rows):
    pay = [r["payload_bytes"] for r in rows]
    pk = [r["packets"] for r in rows]
    fr = [r["frames"] for r in rows]
    return {
        "n": len(rows),
        "payload_kbps_mean": mean(pay) * 8 / 1000,
        "payload_kbps_p95": sorted(pay)[int(0.95 * (len(pay) - 1))] * 8 / 1000,
        "data_pps_mean": mean(pk),
        "frames_s": mean(fr),
        "data_pkts_per_frame": sum(pk) / sum(fr),
        "mean_payload_per_data_pkt": sum(pay) / sum(pk),
    }


def receiver_pps(telemetry, t0, t1):
    rows = [r for r in in_window(telemetry, t0, t1) if r.get("fresh") and r.get("receiver")]
    # packets_delta is over the telemetry interval (2 s in these runs): use elapsed_ms deltas.
    pts = [(r["elapsed_ms"], r["receiver"]["packets_delta"], r["receiver"].get("lost_packets_delta", 0)) for r in rows
           if r["receiver"].get("packets_delta") is not None and r.get("elapsed_ms") is not None]
    if len(pts) < 2:
        return None
    dur = (pts[-1][0] - pts[0][0]) / 1000
    got = sum(p[1] for p in pts[1:])
    lost = sum(p[2] for p in pts[1:])
    return {"n": len(pts), "data_pps_received": got / dur, "lost_pps": lost / dur,
            "recent_mbps_median": med([r["receiver"]["recent_mbps"] for r in rows if r["receiver"].get("recent_mbps")])}


def split_parity_control(rest_pps, rest_bytes, parity_len, control_len):
    """Two equations: n_p + n_c = rest_pps; n_p*(parity_len) + n_c*(control_len) = rest_bytes."""
    n_p = (rest_bytes - control_len * rest_pps) / (parity_len - control_len)
    n_c = rest_pps - n_p
    return n_p, n_c


def tailnet_terms(label, samples, fr, video_payload_kbps, data_pps, parity_len_ip):
    tn = iface(samples, "tailscale0")
    en = iface(samples, "eno1")
    total_b = tn["tx_kbps_mean"] * 1000 / 8
    video_b = video_payload_kbps * 1000 / 8
    rtp_b = data_pps * RTP
    data_udpip_b = data_pps * UDP_IP
    audio_b = AUDIO_DATAGRAMS_S * AUDIO_IP
    rest_b = total_b - video_b - rtp_b - data_udpip_b - audio_b
    rest_p = tn["tx_pps_mean"] - data_pps - AUDIO_DATAGRAMS_S
    # control packets: assumed ~100 B IP (TCP ACK / small JSON); parity: UDP/IP + 23 + group max payload
    n_p, n_c = split_parity_control(rest_p, rest_b, parity_len_ip, 100)
    return {
        "label": label,
        "tailnet": tn,
        "eno1": en,
        "video_payload_kbps": video_payload_kbps,
        "data_pps": data_pps,
        "rtp_header_kbps": rtp_b * 8 / 1000,
        "data_udpip_kbps": data_udpip_b * 8 / 1000,
        "audio_kbps": audio_b * 8 / 1000,
        "rest_kbps": rest_b * 8 / 1000,
        "rest_pps": rest_p,
        "parity_pps_solved": n_p,
        "control_pps_solved": n_c,
        "parity_kbps_ip": n_p * parity_len_ip * 8 / 1000,
        "parity_kbps_udp_payload": n_p * (parity_len_ip - UDP_IP) * 8 / 1000,
        "parity_udpip_kbps": n_p * UDP_IP * 8 / 1000,
        "control_kbps": n_c * 100 * 8 / 1000,
        "parity_per_data_pkt": n_p / data_pps,
        "underlay_minus_tailnet_bytes_per_pkt": (en["tx_kbps_mean"] - tn["tx_kbps_mean"]) * 1000 / 8 / tn["tx_pps_mean"],
        "underlay_minus_tailnet_kbps": en["tx_kbps_mean"] - tn["tx_kbps_mean"],
        "underlay_minus_tailnet_pps": en["tx_pps_mean"] - tn["tx_pps_mean"],
    }


def idle_eno1(samples):
    idle = [r for r in samples if r["net"]["tailscale0"]["tx_pps"] < 5]
    return {"n": len(idle),
            "kbps_median": med([r["net"]["eno1"]["tx_kBps"] * KIB * 8 / 1000 for r in idle]),
            "pps_median": med([r["net"]["eno1"]["tx_pps"] for r in idle])}


def overlay_cost(t, idle):
    """Per tailnet packet: (eno1 - tailnet - eno1's idle median), less the Ethernet header."""
    extra_b = (t["eno1"]["tx_kbps_mean"] - t["tailnet"]["tx_kbps_mean"] - idle["kbps_median"]) * 1000 / 8
    per_pkt = extra_b / t["tailnet"]["tx_pps_mean"]
    return {"eno1_idle": idle, "underlay_extra_kbps": extra_b * 8 / 1000,
            "underlay_extra_bytes_per_tailnet_pkt": per_pkt,
            "of_which_ethernet": ETH, "outer_ip_udp_wg_pad_bytes_per_pkt": per_pkt - ETH,
            "outer_ip_level_kbps": (per_pkt - ETH) * t["tailnet"]["tx_pps_mean"] * 8 / 1000,
            "underlay_pkts_over_tailnet_minus_idle": t["eno1"]["tx_pps_mean"] - t["tailnet"]["tx_pps_mean"] - idle["pps_median"]}


def shim_parity(shim_rows, frame_rows, label):
    """Align the shim's per-second counters to the frame log by packet count (as G8-S3 did), then
    parity = shim - data (packets and UDP-payload bytes)."""
    sp = [r["packets_in"] for r in shim_rows]
    fp = [r["packets"] for r in frame_rows]
    best = None
    for lag in range(-len(fp) + 30, len(sp) - 30):
        pairs = [(sp[i + lag], fp[i]) for i in range(len(fp)) if 0 <= i + lag < len(sp)]
        if len(pairs) < 60:
            continue
        # parity scales with data: score the spread of the ratio
        ratios = [a / b for a, b in pairs if b > 0]
        score = statistics.pstdev(ratios) / statistics.fmean(ratios)
        if statistics.fmean(ratios) < 1.0:
            continue
        if best is None or score < best[0]:
            best = (score, lag, len(pairs))
    score, lag, n = best
    idx = [i for i in range(len(fp)) if 0 <= i + lag < len(sp)]
    s_b = sum(shim_rows[i + lag]["bytes_in"] for i in idx)
    s_p = sum(shim_rows[i + lag]["packets_in"] for i in idx)
    f_b = sum(frame_rows[i]["payload_bytes"] for i in idx)
    f_p = sum(frame_rows[i]["packets"] for i in idx)
    f_f = sum(frame_rows[i]["frames"] for i in idx)
    secs = len(idx)
    par_p = s_p - f_p
    par_b = s_b - f_b - RTP * f_p
    return {
        "label": label, "aligned_seconds": secs, "lag_s": lag, "alignment_score": round(score, 4),
        "shim_kbps_mean": s_b * 8 / 1000 / secs, "shim_pps": s_p / secs,
        "payload_kbps_mean": f_b * 8 / 1000 / secs, "data_pps": f_p / secs, "frames_s": f_f / secs,
        "data_pkts_per_frame": f_p / f_f,
        "parity_pps": par_p / secs, "parity_kbps_udp_payload": par_b * 8 / 1000 / secs,
        "parity_per_data_pkt": par_p / f_p, "parity_per_frame": par_p / f_f,
        "bytes_per_parity_pkt": par_b / par_p,
    }


def main() -> int:
    out: dict = {}
    fl = load(HERE / "inputs" / "native_frame_sizes.jsonl")

    # ---- 4000, tailnet: G4-S2 run 1, the steady window of the record (18:03:10-18:08:30Z) ----
    g4s2 = EV / "g4_s2_2026-10-17" / "runs" / "run1_capped" / "E1-PS1-STREAM-REMOTE" / "run1"
    t0, t1 = ts("2026-10-18T18:03:10.000Z"), ts("2026-10-18T18:08:30.000Z")
    s = in_window(load(g4s2 / "samples.jsonl"), t0, t1)
    f = in_window(fl, t0, t1)
    fr4 = frames(f)
    rx4 = receiver_pps(load(g4s2 / "telemetry.jsonl"), t0, t1)
    out["frames_4000"] = fr4
    out["receiver_4000"] = rx4
    out["tailnet_4000"] = tailnet_terms("G4-S2 run 1 @4000, 18:03:10-18:08:30Z", s, fr4,
                                         fr4["payload_kbps_mean"], fr4["data_pps_mean"], UDP_IP + FEC_HDR + 1188)
    # the whole PLAYING span's idle-gap check is in the record (0.2 kbit/s); the stream poll's 10-s reads:
    out["overlay_cost_4000"] = overlay_cost(out["tailnet_4000"], idle_eno1(load(g4s2 / "samples.jsonl")))
    sp = [r for r in load(g4s2.parent.parent / "stream_poll.jsonl") if r.get("active") and r.get("tailnet_tx_kbps")
          and t0 <= ts(r["at_utc"]) < t1]
    out["stream_poll_4000_median_kbps"] = med([r["tailnet_tx_kbps"] for r in sp])
    out["stream_poll_4000_n"] = len(sp)

    # ---- 7000, the parity: G8-S1 cell 22 (shim post-fec) against the frame log 04:23-04:30Z ----
    c22 = EV / "g8_s1_2026-10-16" / "runs" / "22_delay-50+loss-1_on"
    f7 = [r for r in fl if ts("2026-10-17T04:23:13.000Z") <= ts(r["at_utc"]) <= ts("2026-10-17T04:30:00.000Z")]
    out["shim_7000"] = shim_parity(load(c22 / "impairment_run1.jsonl"), f7, "G8-S1 cell 22 @7000 vs frame log")

    # ---- 5000, the parity, the same method on G8-S3 cell 1 (the record's §3 as a check of the method) ----
    c1 = EV / "g8_s3_2026-10-17" / "runs" / "01_cap-6000_floor_off"
    f5 = [r for r in fl if ts("2026-10-17T17:41:06.000Z") <= ts(r["at_utc"]) <= ts("2026-10-17T17:52:51.000Z")]
    out["shim_5000"] = shim_parity(load(c1 / "impairment_run1.jsonl"), f5, "G8-S3 cell 1 @5000 vs frame log")

    # ---- 7000, tailnet: G4-S1 run 1's window (22:52:26-23:02:26Z); no frame log for it ----
    g4s1 = EV / "g4_s1_2026-10-16" / "runs" / "E1-PS1-STREAM-REMOTE" / "run1"
    u0, u1 = ts("2026-10-16T22:52:26.224Z"), ts("2026-10-16T23:02:26.225Z")
    s1 = in_window(load(g4s1 / "samples.jsonl"), u0, u1)
    rx7 = receiver_pps(load(g4s1 / "telemetry.jsonl"), u0, u1)
    out["receiver_7000"] = rx7
    # video payload at 7000: the frame log's two 7000 segments (G8-S1 cell 22; the 15:58Z LAN smoke)
    f7b = [r for r in fl if ts("2026-10-17T15:58:49.000Z") <= ts(r["at_utc"]) <= ts("2026-10-17T16:10:31.000Z")]
    fr7 = frames(f7 + f7b)
    out["frames_7000"] = fr7
    # data packets: primary = the frame log's 7000 rate (what the relay sends); alternative = the client's
    # received + lost count, which misses whatever the client did not see as a sequence gap
    out["tailnet_7000"] = tailnet_terms("G4-S1 run 1 @7000, window 22:52:26-23:02:26Z", s1, fr7,
                                         fr7["payload_kbps_mean"], fr7["data_pps_mean"], UDP_IP + FEC_HDR + 1188)
    out["tailnet_7000_alt_receiver_count"] = tailnet_terms("G4-S1 run 1 @7000 (receiver count)", s1, fr7,
                                         fr7["payload_kbps_mean"], rx7["data_pps_received"] + rx7["lost_pps"],
                                         UDP_IP + FEC_HDR + 1188)
    out["overlay_cost_7000"] = overlay_cost(out["tailnet_7000"], idle_eno1(load(g4s1 / "samples.jsonl")))
    # closure at 7000 with the shim-measured parity (cell 22) in place of the solved split
    sh = out["shim_7000"]
    par7_ip = sh["parity_pps"] * UDP_IP + sh["parity_kbps_udp_payload"] * 125
    t7 = out["tailnet_7000"]
    out["closure_7000_with_shim_parity"] = {
        "parity_kbps_ip": par7_ip * 8 / 1000,
        "control_kbps_remainder": t7["rest_kbps"] - par7_ip * 8 / 1000,
        "control_pps_remainder": t7["rest_pps"] - sh["parity_pps"]}
    # the G4-S1 record's 11.42: the same sampler field x 8 / 1000 (KiB read as kB)
    out["g4_s1_record_unit_check"] = {"tailnet_kibps_x8_over_1000": t7["tailnet"]["tx_kbps_mean"] / 1.024 / 1000,
                                      "decimal_mbit": t7["tailnet"]["tx_kbps_mean"] / 1000}
    # the same window without the relayed 31 s and the controller pause is not separated (10-s path polls)

    # ---- 7000, LAN: G5-S3's LAN smoke (15:58-16:10Z) eno1 against the frame log ----
    sm = EV / "g5_s3_smoke_2026-10-17" / "runs" / "E1-PS1-STREAM_flag" / "run1"
    v0, v1 = ts("2026-10-17T16:00:30.000Z"), ts("2026-10-17T16:10:00.000Z")
    sl = in_window(load(sm / "samples.jsonl"), v0, v1)
    fl_l = in_window(fl, v0, v1)
    frl = frames(fl_l)
    out["frames_lan_7000"] = frl
    en = iface(sl, "eno1")
    out["lan_7000"] = en
    lan_b = en["tx_kbps_mean"] * 1000 / 8 - ETH * en["tx_pps_mean"]
    lan_rest = lan_b - frl["payload_kbps_mean"] * 125 - frl["data_pps_mean"] * (RTP + UDP_IP) - AUDIO_DATAGRAMS_S * AUDIO_IP
    lan_rest_p = en["tx_pps_mean"] - frl["data_pps_mean"] - AUDIO_DATAGRAMS_S
    n_p, n_c = split_parity_control(lan_rest_p, lan_rest, UDP_IP + FEC_HDR + 1188, 100)
    out["lan_7000_terms"] = {"ip_level_kbps": lan_b * 8 / 1000, "rest_kbps": lan_rest * 8 / 1000, "rest_pps": lan_rest_p, "parity_pps_solved": n_p,
                             "control_pps_solved": n_c, "parity_per_data_pkt": n_p / frl["data_pps_mean"]}

    (HERE / "reading.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
