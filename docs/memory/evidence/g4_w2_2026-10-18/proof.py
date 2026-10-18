#!/usr/bin/env python3
"""G4-W2: the Opus path proved offline, in process. No stream, no companion, no socket.

    PYTHONDONTWRITEBYTECODE=1 python3 -I docs/memory/evidence/g4_w2_2026-10-18/proof.py <scratch_dir>

<scratch_dir> must hold `bgm_48k_s16le_60s.pcm` (ffmpeg on the tree's RetroArch menu
music, the command in the record); the synthetic source is generated here (seeded).

1. Flag absent: HEAD's `native_session_io.py` (git) and today's (flag absent) run their
   real `_linux_sender_loop` over the same 60-s capture with the same stubs (the pacer
   returns at once; the "reader" feeds the buffer at the real-time rate; a capturing
   socket) -> the datagrams compared byte for byte, in order.
2. Flag on (`opus`, defaults; and frame 5 / 20): today's module with the flag, the hook
   path (`AUDIO_CODEC.prepare` then `_linux_sender_loop`) -> wire bytes and datagrams
   per second, the encoder's CPU, the decode RMS error against the source.
3. Loss: G8-P1's `Impairer` (loss-1, loss-5; seeds 1-30) over each path's datagrams ->
   holes per minute and audio-ms lost per minute.
4. The start handler (`_start_linux_locked`, G8-S2's stub manager): HEAD vs today with
   the flag absent (identical); with the flag on: an old client refused before
   anything is spawned, a declaring client configured for Opus.
"""

from __future__ import annotations

import array
import importlib.util
import ipaddress
import json
import math
import os
import random
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tests" / "start_rung"))
TMP = Path(tempfile.mkdtemp(prefix="g4_w2_proof_"))
SECONDS = 60
BYTES_PER_S = 48_000 * 4
LAN = str(ipaddress.ip_address(0xC0A80117))
OVERLAY = str(ipaddress.ip_network((0x64400000, 10))[77])


def load_head(rel: str, name: str):
    src = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"], capture_output=True, text=True,
                         check=True).stdout
    p = TMP / f"{name}.py"
    p.write_text(src)
    return load_path(p, name)


def load_path(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def synthetic() -> bytes:
    """60 s stereo: 440 Hz (L) / 660 Hz (R) with a slow amplitude sweep, + seeded noise at -20 dB."""
    rng = random.Random(20261018)
    out = array.array("h")
    n = 48_000 * SECONDS
    b1 = b2 = 0.0
    for i in range(n):
        t = i / 48_000
        amp = 0.25 + 0.2 * math.sin(2 * math.pi * 0.1 * t)
        w = rng.uniform(-1, 1)
        b1 = 0.97 * b1 + 0.03 * w          # a crude low-passed ("pink-ish") noise
        b2 = 0.90 * b2 + 0.10 * rng.uniform(-1, 1)
        left = amp * math.sin(2 * math.pi * 440 * t) + 0.1 * 3 * b1
        right = amp * math.sin(2 * math.pi * 660 * t) + 0.1 * b2
        out.append(max(-32767, min(32767, int(left * 32767))))
        out.append(max(-32767, min(32767, int(right * 32767))))
    if sys.byteorder != "little":
        out.byteswap()
    return out.tobytes()


class CaptureSocket:
    def __init__(self, log: list):
        self.log = log

    def setsockopt(self, *a):
        pass

    def setblocking(self, *a):
        pass

    def sendto(self, data, addr):
        self.log.append(bytes(data))
        return len(data)

    def close(self):
        pass


def fake_socket_module(log: list):
    import socket as real
    return types.SimpleNamespace(socket=lambda *a, **k: CaptureSocket(log), AF_INET=real.AF_INET,
                                 SOCK_DGRAM=real.SOCK_DGRAM, SOL_SOCKET=real.SOL_SOCKET, SO_SNDBUF=real.SO_SNDBUF)


def run_sender(mod, source: bytes, tick_ms: int, configure=None, codec_mod=None) -> tuple[list, Any]:
    """The module's real `_linux_sender_loop` on a real streamer with stubs; returns (datagrams, streamer)."""
    st = mod.NativeAudioStreamer(TMP / "root")
    st._client_ip, st._client_port = LAN, 48101
    st.set_redundancy(copies=2, offset_packets=4)
    st._linux_prepare_sender_scheduler = lambda: True
    sent: list = []
    fed = {"n": 0, "first": None}
    tick_ns = tick_ms * 1_000_000

    def wait_until(deadline_ns: int) -> bool:
        if fed["first"] is None:
            fed["first"] = deadline_ns
        elapsed = deadline_ns - fed["first"] + tick_ns
        if elapsed > SECONDS * 1_000_000_000:
            return False
        want = min(len(source), (elapsed * BYTES_PER_S // 1_000_000_000) // 4 * 4)
        if want > fed["n"]:
            with st._linux_buffer_condition:
                st._linux_buffer.extend(source[fed["n"]:want])
            fed["n"] = want
        return True

    st._linux_wait_until = wait_until
    if configure is not None:
        configure(st)
    saved = mod.socket
    mod.socket = fake_socket_module(sent)
    saved_c = None
    if codec_mod is not None:
        saved_c = codec_mod.socket
        codec_mod.socket = fake_socket_module(sent)
    t0 = time.thread_time_ns()
    try:
        mod.NativeAudioStreamer._linux_sender_loop(st)
    finally:
        mod.socket = saved
        if codec_mod is not None:
            codec_mod.socket = saved_c
    st._g4_w2_loop_cpu_ns = time.thread_time_ns() - t0
    return sent, st


def parse_dgram(d: bytes):
    import struct
    magic, version, channels, seq, ts, frames = struct.unpack("<4sBBHII", d[:16])
    return {"version": version, "seq": seq, "ts": ts, "frames": frames, "payload": d[16:]}


def per_second(datagrams: list, frame_ms: int) -> dict:
    """IP-level bytes and datagrams per second, binned by the original's send tick (from its timestamp)."""
    bins_b: dict[int, int] = {}
    bins_p: dict[int, int] = {}
    seen: set = set()
    for d in datagrams:
        h = parse_dgram(d)
        sec = h["ts"] // 48_000
        bins_b[sec] = bins_b.get(sec, 0) + len(d) + 28
        bins_p[sec] = bins_p.get(sec, 0) + 1
        seen.add(h["seq"])
    # the copy of the last packets in a second falls in the next tick; use the full seconds 1..58
    secs = [s for s in sorted(bins_b) if 1 <= s <= SECONDS - 2]
    kb = [bins_b[s] * 8 / 1000 for s in secs]
    pp = [bins_p[s] for s in secs]
    return {"seconds": len(secs), "kbit_s_mean": sum(kb) / len(kb), "kbit_s_min": min(kb), "kbit_s_max": max(kb),
            "datagrams_s_mean": sum(pp) / len(pp), "datagram_bytes": sorted({len(d) for d in datagrams}),
            "total_datagrams": len(datagrams)}


def snr_db(ref: bytes, out: bytes, skip_samples: int) -> dict:
    a = array.array("h")
    a.frombytes(ref)
    b = array.array("h")
    b.frombytes(out)
    off = skip_samples * 2
    n = min(len(a), len(b) - off)
    sig = err = 0.0
    for i in range(n):
        x = a[i]
        e = b[i + off] - x
        sig += x * x
        err += e * e
    rms_err = math.sqrt(err / n)
    return {"samples_compared": n // 2, "rms_error": round(rms_err, 2), "rms_error_dbfs": round(
        20 * math.log10(rms_err / 32768), 2) if rms_err else None, "snr_db": round(10 * math.log10(sig / err), 2)
            if err else None}


def holes(datagrams: list, frame_ms: int, profile_name: str, seed: int, imp) -> dict:
    p = imp.parse(f"{profile_name},seed={seed}")
    im = imp.Impairer(p, 0.0)
    got: set = set()
    seqs: set = set()
    t = 0.0
    for d in datagrams:
        h = parse_dgram(d)
        key = h["ts"]                      # unique over 60 s (the u16 sequence wraps on PCM)
        seqs.add(key)
        t = h["ts"] / 48_000
        im.offer(t, d)
        for out in im.due(t):
            got.add(parse_dgram(out)["ts"])
    for out in im.due(t + 10):
        got.add(parse_dgram(out)["ts"])
    keys = sorted(seqs)[8:-8]              # the first / last few have no copy (history fill, stream end)
    lost = [k for k in keys if k not in got]
    minutes = len(keys) * frame_ms / 60_000
    return {"sequences": len(keys), "holes": len(lost), "holes_per_min": len(lost) / minutes,
            "audio_ms_lost_per_min": len(lost) * frame_ms / minutes,
            "datagrams_dropped": im.counters.dropped_loss, "datagrams_in": im.counters.packets_in}


def main(scratch: Path) -> int:
    report: dict = {"libopus": None, "sources": {}, "flag_absent": {}, "opus": {}, "loss": {}, "start": {}}
    env_absent = all(not k.startswith("PRIVYHUB_") for k in os.environ)
    report["env_absent_at_start"] = env_absent
    sources = {"synthetic": synthetic(), "bgm": (scratch / "bgm_48k_s16le_60s.pcm").read_bytes()[: BYTES_PER_S * SECONDS]}
    import hashlib
    for k, v in sources.items():
        report["sources"][k] = {"bytes": len(v), "sha256": hashlib.sha256(v).hexdigest()}

    # 1. flag absent: HEAD vs today, datagram for datagram
    head = load_head("companion/native_session_io.py", "nsio_head")
    today = load_path(REPO / "companion" / "native_session_io.py", "nsio_today_absent")
    report["flag_absent"]["today_AUDIO_CODEC"] = repr(today.AUDIO_CODEC)
    pcm_dgrams = {}
    for name, src in sources.items():
        a, _ = run_sender(head, src, 5)
        b, _ = run_sender(today, src, 5)
        pcm_dgrams[name] = b
        first_diff = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), None)
        report["flag_absent"][name] = {"head_datagrams": len(a), "today_datagrams": len(b),
                                       "identical": a == b, "first_difference": first_diff,
                                       "sha256_head": hashlib.sha256(b"".join(a)).hexdigest(),
                                       "sha256_today": hashlib.sha256(b"".join(b)).hexdigest(),
                                       "wire": per_second(b, 5)}

    # 2. flag on
    os.environ["PRIVYHUB_AUDIO_CODEC"] = "opus"
    import audio_codec as ac
    report["libopus"] = ac.libopus_version()
    flagged = load_path(REPO / "companion" / "native_session_io.py", "nsio_today_flag")
    report["opus"]["module_AUDIO_CODEC_is_shared"] = flagged.AUDIO_CODEC is ac.shared_from_environ(os.environ)
    opus_dgrams = {}
    for spec in ("opus", "opus,frame=5", "opus,frame=20"):
        codec = ac.AudioCodec(spec, log=lambda s: None)
        cfg = codec.config
        frame_ms = cfg["frame_ms"]
        codec.note_setup({"media_host": LAN, "audio_codecs": ["opus"]}, 200, {"ok": True})
        saved = flagged.AUDIO_CODEC
        flagged.AUDIO_CODEC = codec
        try:
            for name, src in sources.items():
                d, st = run_sender(flagged, src, frame_ms,
                                   configure=lambda s: codec.prepare(s, LAN), codec_mod=ac)
                sess = st._audio_codec_opus
                dec = ac.OpusDecoder()
                out = bytearray()
                for x in d:
                    h = parse_dgram(x)
                    if h["version"] != 2:
                        raise SystemExit("not v2")
                # originals in order: the first datagram for each timestamp
                firsts: dict[int, bytes] = {}
                for x in d:
                    h = parse_dgram(x)
                    firsts.setdefault(h["ts"], h["payload"])
                for ts_ in sorted(firsts):
                    out += dec.decode(firsts[ts_], 48 * frame_ms)
                dec.close()
                r = {"spec": spec, "frame_ms": frame_ms, "bitrate_kbps": cfg["bitrate_kbps"],
                     "wire": per_second(d, frame_ms), "predicted": ac.wire_numbers(cfg["bitrate_kbps"], frame_ms),
                     "encoded_frames": sess.encoded_frames,
                     "encoder_cpu_s": sess.encoder_cpu_ns / 1e9,
                     "encoder_cpu_pct_of_one_core": 100 * sess.encoder_cpu_ns / 1e9 / SECONDS,
                     "loop_cpu_s_incl_stub": st._g4_w2_loop_cpu_ns / 1e9,
                     "underflows": st._linux_sender_underflows, "originals": st._linux_packets_sent,
                     "duplicates": st._linux_duplicates_sent,
                     "decode": snr_db(src, bytes(out), 120)}
                report["opus"][f"{spec}|{name}"] = r
                if spec == "opus":
                    opus_dgrams[name] = d
        finally:
            flagged.AUDIO_CODEC = saved
    # PCM's own decode is the identity: the payload bytes are the source bytes
    for name, src in sources.items():
        firsts: dict[int, bytes] = {}
        for x in pcm_dgrams[name]:
            h = parse_dgram(x)
            firsts.setdefault(h["ts"], h["payload"])
        body = b"".join(firsts[k] for k in sorted(firsts))
        report["flag_absent"][name]["pcm_payload_equals_source"] = body == src[: len(body)]
        report["flag_absent"][name]["pcm_payload_seconds"] = len(body) / BYTES_PER_S

    # 3. loss
    import impairment as imp
    for prof in ("loss-1", "loss-5"):
        for name in sources:
            for path, dg, fm in (("pcm_2_4", pcm_dgrams[name], 5), ("opus_dup", opus_dgrams[name], 10)):
                rows = [holes(dg, fm, prof, seed, imp) for seed in range(1, 31)]
                report["loss"][f"{prof}|{name}|{path}"] = {
                    "seeds": rows,
                    "holes_per_min_mean": sum(r["holes_per_min"] for r in rows) / len(rows),
                    "audio_ms_lost_per_min_mean": sum(r["audio_ms_lost_per_min"] for r in rows) / len(rows)}

    # 4. the start handler
    import stub_manager as stub
    os.environ.pop("PRIVYHUB_AUDIO_CODEC", None)
    ns_head = load_head("companion/native_stream.py", "ns_head")
    ns_absent = load_path(REPO / "companion" / "native_stream.py", "ns_today_absent")

    def canon(out, target):
        o = {k: out[k] for k in ("argv", "active_bitrate_kbps", "payload", "calls", "log")}
        text = json.dumps(o, sort_keys=True, default=str)
        return text.replace(target, "<target>").replace(str(out["manager"].project_root), "<tmp>")

    for label, target in (("LAN", LAN), ("overlay", OVERLAY)):
        a = stub.run_start(ns_head, target)
        b = stub.run_start(ns_absent, target)
        report["start"][f"absent|{label}"] = {"identical": canon(a, target) == canon(b, target),
                                              "calls": len(b["calls"]), "AUDIO_CODEC": repr(ns_absent.AUDIO_CODEC)}
    os.environ["PRIVYHUB_AUDIO_CODEC"] = "opus"
    ns_flag = load_path(REPO / "companion" / "native_stream.py", "ns_today_flag")
    for label, declared in (("old_client", None), ("declaring_client", ["pcm_s16le", "opus"])):
        codec = ac.AudioCodec("opus", log=lambda s: None)
        body = {"media_host": LAN}
        if declared is not None:
            body["audio_codecs"] = declared
        codec.note_setup(body, 200, {"ok": True})
        ns_flag.AUDIO_CODEC = codec
        calls: list = []
        try:
            out = stub.run_start(ns_flag, LAN, calls)
            report["start"][f"flag|{label}"] = {"started": True, "argv_spawned": out["argv"] is not None,
                                                "opus_session": ac.AudioCodec.session_for(
                                                    out["manager"]._session_io.audio) is not None,
                                                "calls": [c[0] for c in calls]}
        except ns_flag.NativeStreamError as exc:
            report["start"][f"flag|{label}"] = {"started": False, "error": str(exc),
                                                "calls_before_refusal": [c[0] for c in calls]}
    os.environ.pop("PRIVYHUB_AUDIO_CODEC", None)

    (HERE / "proof.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    from typing import Any  # noqa: F401  (annotations above)
    sys.exit(main(Path(sys.argv[1])))
