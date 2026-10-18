"""G4-W2: a compressed (Opus) audio path, host side.

`PRIVYHUB_AUDIO_CODEC=opus[,bitrate=<kbps>][,frame=<ms>]`. **Absent (or empty) =
today**: nothing imports this module; the PCM sender is byte for byte as before.
The design is `docs/memory/evidence/g4_w2_2026-10-18/design_written_before_code.md`
(hashed before this code).

- Defaults: 128 kbit/s, 10-ms frames; bitrate 48-256, frame 5 / 10 / 20. `pcm`, an
  unknown codec or a malformed part -> logged once, ignored (today's PCM path).
- The encoder: the host's libopus through ctypes, RESTRICTED_LOWDELAY (CELT only,
  2.5-ms lookahead), hard CBR, complexity 10, no in-band FEC.
- The datagram: today's 16-B PHA1 header (`<4sBBHII`) with **version 2 = Opus**;
  frames = samples per channel; the payload one Opus packet. Old clients drop v2.
- Protection: today's duplication (the profile's copies), the copy the same ~20 ms
  behind its original: offset = round(offset_packets x 5 ms / frame), at least 1.
- The negotiation: the client's `/session/setup` body carries `"audio_codecs":
  ["opus"]`; the gate's `_setup` is wrapped from outside (the identity module is not
  edited) to record it per declared host. A stream start to a target that did not
  declare it is refused with a message (fails closed).
"""

from __future__ import annotations

import ctypes
import ctypes.util
import os
import socket
import threading
import time
from collections import deque
from typing import Any, Callable, Mapping

FLAG_ENV = "PRIVYHUB_AUDIO_CODEC"
CODEC_OPUS = "opus"
CAPABILITY_FIELD = "audio_codecs"
DEFAULT_BITRATE_KBPS = 128
DEFAULT_FRAME_MS = 10
BITRATE_MIN_KBPS = 48
BITRATE_MAX_KBPS = 256
FRAMES_MS = (5, 10, 20)
PHA_VERSION_OPUS = 2
SAMPLE_RATE = 48_000
CHANNELS = 2
PCM_PACKET_MS = 5                  # the PCM path's tick (native_stream_profiles.AUDIO_PACKET_MS)
MAX_PACKET_BYTES = 1500
DECLARED_MAX_HOSTS = 64

REFUSAL = ("audio codec opus is required by this host ({flag}) and the client did not "
           "declare it in session/setup").format(flag=FLAG_ENV)

# libopus constants (opus_defines.h)
OPUS_OK = 0
OPUS_APPLICATION_RESTRICTED_LOWDELAY = 2051
OPUS_SET_BITRATE_REQUEST = 4002
OPUS_SET_VBR_REQUEST = 4006
OPUS_SET_COMPLEXITY_REQUEST = 4010
OPUS_SET_INBAND_FEC_REQUEST = 4012
OPUS_GET_LOOKAHEAD_REQUEST = 4027


def parse(raw: Any) -> dict[str, Any]:
    """`opus[,bitrate=N][,frame=N]` -> {"codec": "opus", ...}; anything else -> {"invalid": why}."""
    text = str(raw or "").strip().lower()
    parts = [p.strip() for p in text.split(",")]
    if not parts or parts[0] != CODEC_OPUS:
        return {"invalid": f"codec {parts[0] if parts else ''!r} is not opus"}
    cfg: dict[str, Any] = {"codec": CODEC_OPUS, "bitrate_kbps": DEFAULT_BITRATE_KBPS, "frame_ms": DEFAULT_FRAME_MS}
    seen: set[str] = set()
    for part in parts[1:]:
        key, sep, value = part.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or key not in ("bitrate", "frame") or key in seen or not value.isdigit():
            return {"invalid": f"part {part!r} is not bitrate=<kbps> or frame=<ms>"}
        seen.add(key)
        number = int(value)
        if key == "bitrate":
            if not BITRATE_MIN_KBPS <= number <= BITRATE_MAX_KBPS:
                return {"invalid": f"bitrate {number} outside {BITRATE_MIN_KBPS}-{BITRATE_MAX_KBPS}"}
            cfg["bitrate_kbps"] = number
        else:
            if number not in FRAMES_MS:
                return {"invalid": f"frame {number} not one of {FRAMES_MS}"}
            cfg["frame_ms"] = number
    return cfg


def wire_numbers(bitrate_kbps: int, frame_ms: int, copies: int = 2) -> dict[str, float]:
    """The datagram size and rate the design states (IP-level: + UDP 8 + IPv4 20)."""
    payload = bitrate_kbps * frame_ms // 8
    per_s = (1000 // frame_ms) * max(1, copies)
    ip_bytes = payload + 16 + 28
    return {"payload_bytes": payload, "datagrams_per_s": per_s, "ip_bytes": ip_bytes,
            "kbit_s": per_s * ip_bytes * 8 / 1000}


def copy_offset_packets(offset_pcm_packets: int, frame_ms: int) -> int:
    return max(1, int(round(int(offset_pcm_packets) * PCM_PACKET_MS / frame_ms)))


# ---- libopus through ctypes ------------------------------------------------------------

_LIB: Any = None
_LIB_LOCK = threading.Lock()


def libopus() -> Any:
    global _LIB
    with _LIB_LOCK:
        if _LIB is None:
            name = ctypes.util.find_library("opus") or "libopus.so.0"
            lib = ctypes.CDLL(name)
            lib.opus_get_version_string.restype = ctypes.c_char_p
            lib.opus_encoder_create.restype = ctypes.c_void_p
            lib.opus_encoder_create.argtypes = [ctypes.c_int32, ctypes.c_int, ctypes.c_int,
                                                ctypes.POINTER(ctypes.c_int)]
            lib.opus_encode.restype = ctypes.c_int32
            lib.opus_encode.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int,
                                        ctypes.c_char_p, ctypes.c_int32]
            lib.opus_encoder_destroy.argtypes = [ctypes.c_void_p]
            lib.opus_decoder_create.restype = ctypes.c_void_p
            lib.opus_decoder_create.argtypes = [ctypes.c_int32, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
            lib.opus_decode.restype = ctypes.c_int
            lib.opus_decode.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int32,
                                        ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
            lib.opus_decoder_destroy.argtypes = [ctypes.c_void_p]
            _LIB = lib
        return _LIB


def libopus_version() -> str:
    return libopus().opus_get_version_string().decode("ascii", "replace")


class OpusEncoder:
    def __init__(self, bitrate_kbps: int, frame_ms: int) -> None:
        lib = libopus()
        err = ctypes.c_int(0)
        self._lib = lib
        self._st = lib.opus_encoder_create(SAMPLE_RATE, CHANNELS, OPUS_APPLICATION_RESTRICTED_LOWDELAY,
                                           ctypes.byref(err))
        if err.value != OPUS_OK or not self._st:
            raise RuntimeError(f"opus_encoder_create failed ({err.value})")
        for request, value in ((OPUS_SET_BITRATE_REQUEST, int(bitrate_kbps) * 1000), (OPUS_SET_VBR_REQUEST, 0),
                               (OPUS_SET_COMPLEXITY_REQUEST, 10), (OPUS_SET_INBAND_FEC_REQUEST, 0)):
            rc = lib.opus_encoder_ctl(ctypes.c_void_p(self._st), ctypes.c_int(request), ctypes.c_int32(value))
            if rc != OPUS_OK:
                raise RuntimeError(f"opus_encoder_ctl({request}) failed ({rc})")
        look = ctypes.c_int32(0)
        lib.opus_encoder_ctl(ctypes.c_void_p(self._st), ctypes.c_int(OPUS_GET_LOOKAHEAD_REQUEST), ctypes.byref(look))
        self.lookahead_samples = int(look.value)
        self.frame_samples = SAMPLE_RATE * int(frame_ms) // 1000
        self._out = ctypes.create_string_buffer(MAX_PACKET_BYTES)

    def encode(self, pcm: bytes) -> bytes:
        n = self._lib.opus_encode(self._st, pcm, self.frame_samples, self._out, MAX_PACKET_BYTES)
        if n < 0:
            raise RuntimeError(f"opus_encode failed ({n})")
        return self._out.raw[:n]

    def close(self) -> None:
        if self._st:
            self._lib.opus_encoder_destroy(self._st)
            self._st = None

    def __del__(self) -> None:  # pragma: no cover - best effort
        try:
            self.close()
        except Exception:
            pass


class OpusDecoder:
    """For the proof and the tests (the client decodes with MediaCodec)."""

    def __init__(self) -> None:
        lib = libopus()
        err = ctypes.c_int(0)
        self._lib = lib
        self._st = lib.opus_decoder_create(SAMPLE_RATE, CHANNELS, ctypes.byref(err))
        if err.value != OPUS_OK or not self._st:
            raise RuntimeError(f"opus_decoder_create failed ({err.value})")
        self._out = ctypes.create_string_buffer(SAMPLE_RATE // 10 * CHANNELS * 2)

    def decode(self, packet: bytes | None, frame_samples: int) -> bytes:
        """packet None -> the decoder's loss concealment for one frame."""
        if packet is None:
            n = self._lib.opus_decode(self._st, None, 0, self._out, frame_samples, 0)
        else:
            n = self._lib.opus_decode(self._st, packet, len(packet), self._out, frame_samples, 0)
        if n < 0:
            raise RuntimeError(f"opus_decode failed ({n})")
        return self._out.raw[: n * CHANNELS * 2]

    def close(self) -> None:
        if self._st:
            self._lib.opus_decoder_destroy(self._st)
            self._st = None

    def __del__(self) -> None:  # pragma: no cover
        try:
            self.close()
        except Exception:
            pass


# ---- the session's choice and the sender -------------------------------------------------

class OpusSession:
    """What one stream start chose: set on the audio streamer by `prepare`."""

    def __init__(self, bitrate_kbps: int, frame_ms: int) -> None:
        self.bitrate_kbps = int(bitrate_kbps)
        self.frame_ms = int(frame_ms)
        self.encoder_cpu_ns = 0
        self.encoded_frames = 0
        self.payload_bytes = 0


def run_opus_sender(streamer: Any, session: OpusSession, client_ip: str, client_port: int,
                    sock_factory: Callable[[], Any] | None = None) -> None:
    """The PCM loop's twin (`NativeAudioStreamer._linux_sender_loop`): the same pacer,
    buffer, silence on underflow, duplication and counters, one Opus packet per frame."""
    frame_samples = SAMPLE_RATE * session.frame_ms // 1000
    frame_bytes = frame_samples * CHANNELS * 2
    frame_ns = session.frame_ms * 1_000_000
    silence = bytes(frame_bytes)
    encoder = OpusEncoder(session.bitrate_kbps, session.frame_ms)
    header = streamer.LINUX_HEADER
    # E3-S5 / E3-S5C pacing variants, read as the PCM loop reads them (the pacer uses them).
    streamer._linux_pacing_frame = os.environ.get("PRIVYHUB_AUDIO_SENDER_PACING") == "frame"
    streamer._linux_pacing_frame_spin = os.environ.get("PRIVYHUB_AUDIO_SENDER_PACING") == "frame_spin"
    sock = sock_factory() if sock_factory is not None else socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        if sock_factory is None:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 64 * 1024)
            sock.setblocking(False)
        sequence = 0
        sample_timestamp = 0
        copies = streamer._redundancy_copies
        offset = copy_offset_packets(streamer._redundancy_offset_packets, session.frame_ms)
        history: deque[bytes] = deque(maxlen=offset + 1)
        deadline_ns = time.perf_counter_ns()
        target = (client_ip, int(client_port))
        while not streamer._linux_stop_event.is_set():
            deadline_ns += frame_ns
            if not streamer._linux_wait_until(deadline_ns):
                break
            with streamer._linux_buffer_condition:
                if len(streamer._linux_buffer) >= frame_bytes:
                    pcm = bytes(streamer._linux_buffer[:frame_bytes])
                    del streamer._linux_buffer[:frame_bytes]
                else:
                    pcm = silence
                    streamer._linux_sender_underflows += 1
            t0 = time.thread_time_ns()
            packet = encoder.encode(pcm)
            session.encoder_cpu_ns += time.thread_time_ns() - t0
            session.encoded_frames += 1
            session.payload_bytes += len(packet)
            datagram = header.pack(b"PHA1", PHA_VERSION_OPUS, CHANNELS, sequence, sample_timestamp,
                                   frame_samples) + packet
            try:
                sock.sendto(datagram, target)
                now_ns = time.perf_counter_ns()
                if streamer._linux_last_send_ns > 0:
                    streamer._linux_send_intervals_ns.append(now_ns - streamer._linux_last_send_ns)
                streamer._linux_last_send_ns = now_ns
                streamer._linux_packets_sent += 1
            except (BlockingIOError, OSError):
                streamer._linux_send_errors += 1
            if copies >= 2:
                history.append(datagram)
                if len(history) > offset:
                    try:
                        sock.sendto(history[0], target)
                        streamer._linux_duplicates_sent += 1
                    except (BlockingIOError, OSError):
                        streamer._linux_duplicate_send_errors += 1
            sequence = (sequence + 1) & 0xFFFF
            sample_timestamp = (sample_timestamp + frame_samples) & 0xFFFFFFFF
    finally:
        encoder.close()
        try:
            sock.close()
        except OSError:
            pass


class AudioCodec:
    def __init__(self, raw: Any, log: Any = print, wall: Callable[[], float] = time.time) -> None:
        self.raw = str(raw or "").strip()
        self.config = parse(raw)
        self.active = "invalid" not in self.config
        self._log = log
        self._wall = wall
        self._logged: set[str] = set()
        self._lock = threading.Lock()
        self._declared: dict[str, tuple[tuple[str, ...], float]] = {}
        self.starts_opus = 0
        self.starts_refused = 0
        if not self.active:
            self._once("invalid", f"ignored ({self.config['invalid']}); audio stays PCM")

    def _once(self, key: str, text: str) -> None:
        if key not in self._logged:
            self._logged.add(key)
            try:
                self._log(f"PrivyHub audio codec ({FLAG_ENV}): {text}")
            except Exception:
                pass

    # -- the capability, captured from session/setup --
    def note_setup(self, body: Any, status: int, payload: Any) -> None:
        if status != 200 or not isinstance(payload, dict) or payload.get("ok") is not True:
            return
        if not isinstance(body, dict):
            return
        raw = body.get(CAPABILITY_FIELD)
        codecs: tuple[str, ...] = ()
        if isinstance(raw, list):
            codecs = tuple(sorted({str(c).strip().lower() for c in raw if isinstance(c, str)}))[:8]
        hosts = [str(body.get("media_host") or "").strip()]
        if body.get("sig_v") == 2 and not isinstance(body.get("sig_v"), bool):
            hosts.append(str(body.get("overlay_host") or "").strip())
        with self._lock:
            for host in hosts:
                if host:
                    self._declared.pop(host, None)
                    self._declared[host] = (codecs, self._wall())
            while len(self._declared) > DECLARED_MAX_HOSTS:
                self._declared.pop(next(iter(self._declared)))

    def install_setup_capture(self, gate: Any) -> bool:
        """Wrap the gate instance's `_setup` (the module file is not edited). Idempotent."""
        original = getattr(gate, "_setup", None)
        if original is None or getattr(original, "_g4_w2_capture", False):
            return False
        codec = self

        def _setup(body, routing, refused):
            status, payload = original(body, routing, refused)
            try:
                codec.note_setup(body, status, payload)
            except Exception:
                pass
            return status, payload

        _setup._g4_w2_capture = True  # type: ignore[attr-defined]
        gate._setup = _setup
        return True

    def declared(self, host: str) -> tuple[str, ...]:
        with self._lock:
            entry = self._declared.get(str(host))
        return entry[0] if entry else ()

    # -- the stream start --
    def prepare(self, streamer: Any, client_ip: str) -> str | None:
        """None = go on (Opus configured, or the flag invalid -> PCM); else the refusal text."""
        if not self.active:
            streamer._audio_codec_opus = None
            return None
        if CODEC_OPUS in self.declared(client_ip):
            streamer._audio_codec_opus = OpusSession(self.config["bitrate_kbps"], self.config["frame_ms"])
            with self._lock:
                self.starts_opus += 1
            self._once("opus", "opus {b} kbit/s, {f}-ms frames, libopus {v}".format(
                b=self.config["bitrate_kbps"], f=self.config["frame_ms"], v=libopus_version()))
            return None
        streamer._audio_codec_opus = None
        with self._lock:
            self.starts_refused += 1
        self._once("refused", "a start was refused: the client did not declare opus")
        return REFUSAL

    @staticmethod
    def session_for(streamer: Any) -> OpusSession | None:
        return getattr(streamer, "_audio_codec_opus", None)

    @staticmethod
    def run_sender(streamer: Any, client_ip: str, client_port: int) -> None:
        run_opus_sender(streamer, streamer._audio_codec_opus, client_ip, client_port)

    def status(self) -> dict[str, Any]:
        out: dict[str, Any] = {"flag": FLAG_ENV, "active": self.active, "starts_opus": self.starts_opus,
                               "starts_refused": self.starts_refused}
        out.update({k: v for k, v in self.config.items()})
        return out


_SHARED: AudioCodec | None = None
_SHARED_LOCK = threading.Lock()


def shared_from_environ(environ: Mapping[str, str]) -> AudioCodec | None:
    """The one instance the hooks share; None when the flag is absent or empty."""
    global _SHARED
    raw = environ.get(FLAG_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    with _SHARED_LOCK:
        if _SHARED is None:
            _SHARED = AudioCodec(raw)
        return _SHARED


def from_environ_fresh(environ: Mapping[str, str] = os.environ, log: Any = print) -> AudioCodec | None:
    """A new instance (tests and harnesses)."""
    raw = environ.get(FLAG_ENV)
    if raw is None or str(raw).strip() == "":
        return None
    return AudioCodec(raw, log=log)
