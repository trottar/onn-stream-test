#!/usr/bin/env python3
"""G8-P1: the in-process proof. Loopback only; no stream; no companion.

    python3 docs/memory/evidence/g8_p1_2026-10-16/proof.py [out_dir]

A. Per profile, 60 s: a synthetic ~7 Mbit/s RTP source (60 fps x 12 packets of
   1200 B) -> the shim -> a capture socket read by its own thread. Measured
   against the profile within the stated tolerances; the shim thread's CPU.
B. The real FEC sender (`native_fec_relay.NativeVideoFecRelay`, imported) with
   the shim in each placement, 60 s per case. A capture plays the client: it
   counts recovered groups (one missing, the parity present), unrecoverable
   groups, and packets lost after FEC. Per 2-s report (fps from complete
   frames, post-FEC lost) G5-S1's `classify_window` reads the result.
C. Flag absent:
   - the encoder command's masked hash: HEAD's builder vs today's, with the
     flag absent and set;
   - the FEC sender, HEAD's (from git) vs the edited one, byte for byte on
     the same stream;
   - in a fresh process with no flag: the module not imported, the sender's
     own port bound, no shim thread.
Writes proof_tables.md / proof.json. Addresses: the loopback only, built from
an integer.
"""

from __future__ import annotations

import hashlib
import importlib.util
import ipaddress
import json
import os
import socket
import statistics
import struct
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "companion"))

import impairment as imp  # noqa: E402
import native_fec_relay as relay_mod  # noqa: E402
import wan_telemetry as wt  # noqa: E402

LOOP = str(ipaddress.ip_address(0x7F000001))
FPS, PER_FRAME, PKT = 60, 12, 1200
SECONDS = int(os.environ.get("G8_P1_SECONDS", "60"))   # 60 for the record; a smaller value only smoke-tests the code


def rtp(seq, ts, marker, send_ns):
    hdr = struct.pack("!BBHII", 0x80, (0x80 if marker else 0) | 96, seq & 0xFFFF, ts, 0x1234ABCD)
    body = struct.pack("!QI", send_ns, seq) + bytes(PKT - 12 - 12)
    return hdr + body


def source(target, seconds, stop=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4 * 1024 * 1024)
    seq, t0 = 0, time.perf_counter()
    for f in range(FPS * seconds):
        due = t0 + f / FPS
        while True:
            d = due - time.perf_counter()
            if d <= 0:
                break
            time.sleep(min(d, 0.002))
        for k in range(PER_FRAME):
            s.sendto(rtp(seq, f * 1500, k == PER_FRAME - 1, time.perf_counter_ns()), target)
            seq += 1
    s.close()
    return seq


class Capture:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
        self.sock.bind((LOOP, 0))
        self.sock.settimeout(0.2)
        self.got: list[tuple[int, bytes]] = []
        self.done = threading.Event()
        self.t = threading.Thread(target=self._run, daemon=True)
        self.t.start()

    @property
    def addr(self):
        return (LOOP, self.sock.getsockname()[1])

    def _run(self):
        idle = 0
        while not self.done.is_set() or idle < 5:
            try:
                self.got.append((time.perf_counter_ns(), self.sock.recv(65535)))
                idle = 0
            except socket.timeout:
                idle += 1

    def finish(self):
        self.done.set()
        self.t.join(timeout=10)
        self.sock.close()
        return self.got


def pct(xs, q):
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


# ------------------------------------------------------------------ A ---
CHECKS = {
    "none": lambda m: m["loss_pct"] == 0 and m["reordered_pct"] == 0,
    "loss-1": lambda m: 0.7 <= m["loss_pct"] <= 1.3,
    "loss-5": lambda m: 4.5 <= m["loss_pct"] <= 5.5,
    "burst-50x20": lambda m: m["bursts"] == 3 and m["burst_sizes"] == [50, 50, 50],
    "delay-50": lambda m: 45 <= m["delay_mean_ms"] <= 56 and m["loss_pct"] == 0,
    "delay-150": lambda m: 145 <= m["delay_mean_ms"] <= 156 and m["loss_pct"] == 0,
    "jitter-30": lambda m: 10 <= m["delay_mean_ms"] <= 30 and 18 <= m["jitter_spread_ms"] <= 34
                           and m["reordered_pct"] == 0,
    "reorder-5": lambda m: 4.0 <= m["reordered_pct"] <= 6.0 and m["loss_pct"] == 0,
    "cap-6000": lambda m: 5700 <= m["out_kbps"] <= 6300 and m["queue_max"] <= m["queue_bound"],
    "cap-4500": lambda m: 4275 <= m["out_kbps"] <= 4725 and m["queue_max"] <= m["queue_bound"],
    "loss-1+delay-50+jitter-30": lambda m: 0.7 <= m["loss_pct"] <= 1.3 and 55 <= m["delay_mean_ms"] <= 80,
}
TOLERANCE = {
    "none": "no loss, no reorder (the baseline delay is subtracted from the rest)",
    "loss-1": "loss 0.7-1.3 %", "loss-5": "loss 4.5-5.5 %",
    "burst-50x20": "3 bursts of exactly 50 (at 10 / 30 / 50 s)",
    "delay-50": "mean added delay 45-56 ms, no loss", "delay-150": "mean added delay 145-156 ms, no loss",
    "jitter-30": "mean 10-30 ms, p95-p5 spread 18-34 ms, order kept",
    "reorder-5": "reordered 4-6 %, no loss", "cap-6000": "out 5700-6300 kbit/s, queue within its bound",
    "cap-4500": "out 4275-4725 kbit/s, queue within its bound",
    "loss-1+delay-50+jitter-30": "loss 0.7-1.3 %, mean added delay 55-80 ms",
}


def measure_profile(spec, base_delay_ms):
    cap = Capture()
    p = imp.Profile(names=("none",)) if spec == "none" else imp.parse(spec)
    shim = imp.Shim(p, listen_port=0, forward=cap.addr)
    shim.start()
    t0 = time.perf_counter()
    sent = source((LOOP, shim.port), SECONDS)
    dur = time.perf_counter() - t0
    time.sleep(0.5)
    shim.stop()
    got = cap.finish()
    c = shim.counters()
    seqs, delays, max_seen, late = [], [], -1, 0
    first_ns = last_ns = None
    nbytes = 0
    for at, data in got:
        send_ns, seq = struct.unpack("!QI", data[12:24])
        seqs.append(seq)
        delays.append((at - send_ns) / 1e6)
        if seq < max_seen:
            late += 1
        max_seen = max(max_seen, seq)
        first_ns = at if first_ns is None else first_ns
        last_ns = at
        nbytes += len(data)
    missing = sorted(set(range(sent)) - set(seqs))
    runs, prev = [], None
    for s in missing:
        if prev is None or s != prev + 1:
            runs.append(1)
        else:
            runs[-1] += 1
        prev = s
    added = [d - base_delay_ms for d in delays]
    span = (last_ns - first_ns) / 1e9 if first_ns and last_ns and last_ns > first_ns else dur
    m = {
        "sent": sent, "received": len(got), "loss_pct": round(100.0 * (sent - len(got)) / sent, 3),
        "bursts": sum(1 for r in runs if r >= 10), "burst_sizes": [r for r in runs if r >= 10],
        "delay_mean_ms": round(statistics.fmean(added), 2) if added else None,
        "delay_p50_ms": round(pct(added, 0.5), 2) if added else None,
        "delay_p95_ms": round(pct(added, 0.95), 2) if added else None,
        "jitter_spread_ms": round(pct(added, 0.95) - pct(added, 0.05), 2) if added else None,
        "reordered_pct": round(100.0 * late / max(1, len(got)), 3),
        "in_kbps": round(sent * PKT * 8 / dur / 1000, 1), "out_kbps": round(nbytes * 8 / span / 1000, 1),
        "queue_max": c["queue_max"],
        "queue_bound": (int(p.cap_kbps * 1000 / 8 * imp.QUEUE_LIMIT_S / PKT) + 2) if p.cap_kbps else None,
        "dropped": {"loss": c["dropped_loss"], "burst": c["dropped_burst"], "queue": c["dropped_queue"]},
        "cpu_pct_of_core": round(100.0 * c["cpu_s"] / dur, 2),
        "lines": len(shim.lines),
    }
    return m, delays


# ------------------------------------------------------------------ B ---
def fec_case(spec, seconds=SECONDS, relay_module=None, use_shim=True):
    mod = relay_module or relay_mod
    cap = Capture()
    old = getattr(mod, "_impairment", None)
    if use_shim:
        os.environ[imp.FLAG_ENV] = spec
        mod._impairment = imp
    try:
        r = mod.NativeVideoFecRelay(local_port=0, pacing_us=0)
        r.start(LOOP, cap.addr[1])
        target = (LOOP, r._shim.shim.port) if (use_shim and r._shim.profile.placement == imp.PRE_FEC) \
            else (LOOP, r._recv_socket.getsockname()[1])
        sent = source(target, seconds)
        time.sleep(0.5)
        shim = getattr(r, "_shim", None)
        counters = shim.shim.counters() if shim else None
        r.stop()
    finally:
        if use_shim:
            mod._impairment = old
        os.environ.pop(imp.FLAG_ENV, None)
    return sent, cap.finish(), counters


def client_view(sent, got):
    """What the client would count: recovered groups, unrecoverable groups, lost after FEC, per-report fps."""
    rtp_seqs, parity = set(), []
    for _, data in got:
        if data[:4] == relay_mod.FEC_MAGIC:
            h = relay_mod.FEC_HEADER.unpack(data[:relay_mod.FEC_HEADER.size])
            parity.append((h[3], h[2]))              # base sequence, count
        else:
            rtp_seqs.add(struct.unpack("!H", data[2:4])[0])
    have = set(rtp_seqs)
    recovered = unrecoverable = 0
    for base, n in parity:
        group = [(base + i) & 0xFFFF for i in range(n)]
        miss = [s for s in group if s not in rtp_seqs]
        if len(miss) == 1:
            recovered += 1
            have.add(miss[0])
        elif len(miss) > 1:
            unrecoverable += 1
    lost = [s for s in range(sent) if (s & 0xFFFF) not in have]
    # per 2-s report: complete frames and post-FEC lost packets
    per_report = 2 * FPS
    reports = []
    lost_set = set(lost)
    for r0 in range(0, sent // PER_FRAME, per_report):
        frames = range(r0, min(r0 + per_report, sent // PER_FRAME))
        complete = sum(1 for f in frames if all((f * PER_FRAME + k) not in lost_set for k in range(PER_FRAME)))
        lost_n = sum(1 for f in frames for k in range(PER_FRAME) if (f * PER_FRAME + k) in lost_set)
        reports.append(wt.Report(elapsed_ms=(r0 // per_report + 1) * 2000, fps=complete / 2.0, queue=0,
                                 gap_ms=16, lost=lost_n, packets=len(frames) * PER_FRAME, mbps=None,
                                 jitter_ms=None, rtt_ms=None, stale=0, waiting_for_idr=False, queue_delta=0))
    classes: dict[str, int] = {}
    for i in range(0, len(reports) - 4, 5):
        c = wt.classify_window(reports[i:i + 5], [])["primary"]
        classes[c] = classes.get(c, 0) + 1
    return {"groups": len(parity), "recovered_groups": recovered, "unrecoverable_groups": unrecoverable,
            "lost_after_fec": len(lost), "lost_per_min": round(len(lost) * 60.0 / (sent / (FPS * PER_FRAME)), 1),
            "window_primary": classes}


# ------------------------------------------------------------------ C ---
def load_head(name, path):
    src = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{path}"], capture_output=True, text=True,
                         check=True).stdout
    d = Path(tempfile.mkdtemp(prefix="g8_p1_head_"))
    p = d / f"{name}.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod            # dataclasses resolve the module by name
    spec.loader.exec_module(mod)
    return mod


def encoder_hashes():
    import native_stream
    head = load_head("native_stream_head", "companion/native_stream.py")
    wid = 0x5A5A5A                     # a fixed fake window id, masked
    os.environ.setdefault("DISPLAY", ":0")   # the builder requires an X11 display name (read, not opened)
    out = {}
    for label, mod in (("HEAD", head), ("today", native_stream)):
        for flag in (None, "loss-1@pre-fec"):
            if flag:
                os.environ[imp.FLAG_ENV] = flag
            try:
                m = object.__new__(mod.NativeStreamManager)
                m.project_root = REPO
                m._log_handle = None
                m._apply_profile_selection()
                cmd = m._build_linux_ffmpeg_command(ffmpeg=Path("/fixture/ffmpeg"), capture_target={"_window_id": wid})
            except Exception as exc:        # pragma: no cover
                cmd = [f"unavailable: {type(exc).__name__}"]
            finally:
                os.environ.pop(imp.FLAG_ENV, None)
            masked = ["<window>" if a == str(wid) else a for a in cmd]
            out[f"{label}, flag {'set' if flag else 'absent'}"] = {
                "sha256_masked": hashlib.sha256(" ".join(masked).encode()).hexdigest(),
                "sink": (masked[-1].replace(LOOP, "<loopback>") if masked else None)}
    return out


def fec_sender_byte_for_byte(seconds=10):
    head = load_head("native_fec_relay_head", "companion/native_fec_relay.py")
    a_sent, a, _ = fec_case(None, seconds, relay_module=head, use_shim=False)
    b_sent, b, _ = fec_case(None, seconds, relay_module=relay_mod, use_shim=False)
    # the payload carries the send time; compare everything else: the datagram sequence, sizes,
    # RTP headers and the parity packets whole (parity covers payloads, so compare its header + length)
    def norm(got):
        out = []
        for _, d in got:
            out.append(d[:relay_mod.FEC_HEADER.size].hex() + f":{len(d)}" if d[:4] == relay_mod.FEC_MAGIC
                       else d[:12].hex() + d[20:24].hex() + f":{len(d)}")
        return out
    return {"sent": [a_sent, b_sent], "datagrams": [len(a), len(b)], "identical": norm(a) == norm(b)}


def fresh_process_check():
    code = (
        "import sys, socket, threading; sys.path.insert(0, %r)\n"
        "import native_fec_relay as r\n"
        "s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind((%r, 0)); port = s.getsockname()[1]; s.close()\n"
        "x = r.NativeVideoFecRelay(local_port=port, pacing_us=0); x.start(%r, 9)\n"
        "print(int(x._recv_socket.getsockname()[1] == port), int(x._client == (%r, 9)),"
        " int('impairment' in sys.modules), int(any(t.name == 'PrivyHub-Impairment' for t in threading.enumerate())))\n"
        "x.stop()\n" % (str(REPO / "companion"), LOOP, LOOP, LOOP))
    env = {k: v for k, v in os.environ.items() if k != imp.FLAG_ENV}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env).stdout.split()
    keys = ("own_port_bound", "target_is_the_client", "impairment_imported", "shim_thread")
    return dict(zip(keys, (int(v) for v in out)))


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    res: dict = {"A": {}, "B": {}, "C": {}}
    lines = ["# G8-P1 proof tables", ""]
    # A
    base, base_delays = measure_profile("none", 0.0)
    base_ms = statistics.median(base_delays)
    base["baseline_delay_ms"] = round(base_ms, 3)
    res["A"]["none"] = base
    for spec in ("loss-1", "loss-5", "burst-50x20", "delay-50", "delay-150", "jitter-30", "reorder-5",
                 "cap-6000", "cap-4500", "loss-1+delay-50+jitter-30"):
        m, _ = measure_profile(spec, base_ms)
        res["A"][spec] = m
        print(spec, json.dumps(m)[:200], flush=True)
    lines += ["## A. Each profile, 60 s, synthetic 7 Mbit/s RTP (60 fps x 12 x 1200 B)", "",
              f"Baseline loopback delay (no impairment), median: {base_ms:.3f} ms, subtracted below.", "",
              "| profile | tolerance | loss % | bursts | added delay mean / p95 ms | spread p95-p5 ms | reordered % "
              "| out kbit/s | queue max (bound) | shim CPU % of a core | verdict |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    ok_a = True
    for spec, m in res["A"].items():
        good = CHECKS[spec](m)
        ok_a &= good
        m["verdict"] = "PASS" if good else "FAIL"
        lines.append(f"| `{spec}` | {TOLERANCE[spec]} | {m['loss_pct']} | {m['bursts']} | {m['delay_mean_ms']} / "
                     f"{m['delay_p95_ms']} | {m['jitter_spread_ms']} | {m['reordered_pct']} | {m['out_kbps']} | "
                     f"{m['queue_max']} ({m['queue_bound'] if m['queue_bound'] else '—'}) | {m['cpu_pct_of_core']} | "
                     f"**{m['verdict']}** |")
    cpu = max(m["cpu_pct_of_core"] for m in res["A"].values())
    lines += ["", f"Shim CPU, the highest profile: {cpu} % of a core (the bar: <= 1 point) -> "
              f"{'PASS' if cpu <= 1.0 else 'OVER THE BAR'}", ""]
    # B
    lines += ["## B. The real FEC sender (`NativeVideoFecRelay`) with the shim, 60 s each", "",
              "| case | groups | recovered | unrecoverable | lost after FEC (per min) | G5-S1 window classes (primary) |",
              "| --- | --- | --- | --- | --- | --- |"]
    for spec in ("loss-1@pre-fec", "loss-1@post-fec", "burst-50x20@pre-fec", "burst-50x20@post-fec",
                 "cap-4500@post-fec"):
        sent, got, counters = fec_case(spec)
        v = client_view(sent, got)
        v["shim"] = counters
        res["B"][spec] = v
        print(spec, json.dumps(v)[:200], flush=True)
        lines.append(f"| `{spec}` | {v['groups']} | {v['recovered_groups']} | {v['unrecoverable_groups']} | "
                     f"{v['lost_after_fec']} ({v['lost_per_min']}) | "
                     f"{', '.join(f'{k} {n}' for k, n in sorted(v['window_primary'].items()))} |")
    # C
    res["C"]["encoder_masked_hashes"] = encoder_hashes()
    res["C"]["fec_sender_head_vs_edited"] = fec_sender_byte_for_byte()
    res["C"]["fresh_process"] = fresh_process_check()
    hashes = {v["sha256_masked"] for v in res["C"]["encoder_masked_hashes"].values()}
    lines += ["", "## C. Flag absent", "",
              "| check | result |", "| --- | --- |"]
    for k, v in res["C"]["encoder_masked_hashes"].items():
        lines.append(f"| encoder command, {k} | `{v['sha256_masked'][:16]}…` (sink `{v['sink']}`) |")
    lines.append(f"| encoder command: one hash across all four | {'yes' if len(hashes) == 1 else 'NO'} |")
    fb = res["C"]["fec_sender_head_vs_edited"]
    lines.append(f"| FEC sender, HEAD vs edited, 10 s, datagram sequence | "
                 f"{'identical' if fb['identical'] else 'DIFFER'} ({fb['datagrams'][0]} / {fb['datagrams'][1]}) |")
    fp = res["C"]["fresh_process"]
    lines.append(f"| fresh process, no flag | own port bound {fp.get('own_port_bound')}, target the client "
                 f"{fp.get('target_is_the_client')}, impairment imported {fp.get('impairment_imported')}, "
                 f"shim thread {fp.get('shim_thread')} |")
    built = all(str(v["sink"]).startswith("rtp://") for v in res["C"]["encoder_masked_hashes"].values())
    lines.append(f"| encoder command built (ends in the rtp sink) | {'yes' if built else 'NO'} |")
    ok_c = (built and len(hashes) == 1 and fb["identical"] and fp == {"own_port_bound": 1, "target_is_the_client": 1,
                                                           "impairment_imported": 0, "shim_thread": 0})
    lines += ["", f"-> A {'PASS' if ok_a else 'FAIL'}; C {'PASS' if ok_c else 'FAIL'}; B is read, not gated."]
    (out_dir / "proof_tables.md").write_text("\n".join(lines) + "\n")
    (out_dir / "proof.json").write_text(json.dumps(res, indent=1) + "\n")
    print("\n".join(lines))
    return 0 if ok_a and ok_c else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent))
