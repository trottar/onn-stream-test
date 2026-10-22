"""G8-P1: a user-space network-impairment shim on the loopback media hop.

Behind `PRIVYHUB_IMPAIRMENT=<profile>[@pre-fec|@post-fec][,seed=N]`. **Absent =
today**: `native_fec_relay` never imports this module; no thread, no port, no
file. The design is
`docs/memory/evidence/g8_p1_2026-10-16/design_written_before_code.md` (hashed
before this code).

A UDP relay thread on the loopback, no privileges:

- `@pre-fec` (the default): encoder -> shim -> FEC sender. The shim takes the
  sender's own port, so the encoder command is unchanged. Loss here is never
  FEC-recoverable: the sender emits parity only for gap-free groups.
- `@post-fec`: encoder -> FEC sender -> shim -> client. RTP and parity alike
  are impaired, as on a WAN or under the nft harness.

Video only: the audio sender and the controller return path do not use this
hop. Every queue is bounded (ROADMAP §G5: no ever-growing buffer). One JSON
line per second to `logs/impairment.jsonl`, with no address.

B1 (2026-10-22): `blackout-<D>s@both|@down[,every=<P>s][,first=<F>s]` -- the
downlink dark for D s every P s (at `@post-fec`), and with `@both` the uplink
too: the controller packets, the heartbeat and the client-health report are
dropped at the host's receive points (`UplinkGate`), on ONE shared wall-clock
scheduler (`shared_blackout`). Design:
`docs/memory/evidence/b1_2026-10-22/design_written_before_code.md`.
"""

from __future__ import annotations

import heapq
import ipaddress
import json
import random
import re
import select
import socket
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

FLAG_ENV = "PRIVYHUB_IMPAIRMENT"
SCHEMA = "privyhub_impairment_v1"
PRE_FEC, POST_FEC = "pre-fec", "post-fec"
BOTH, DOWN = "both", "down"      # B1: blackout placements (the downlink at post-fec; BOTH adds the uplink)
BLACKOUT_RE = re.compile(r"^blackout-(\d+(?:\.\d+)?)s$")
BLACKOUT_EVERY_S = 120.0         # B1 defaults: 4 s dark every 120 s, the first at 120 s
UPLINK_KINDS = ("controller", "heartbeat", "client_health")
LOOPBACK = str(ipaddress.ip_address(0x7F000001))   # built from an integer, no literal
QUEUE_LIMIT_S = 0.100            # the cap's FIFO holds at most 100 ms of the cap's bytes
REORDER_HOLD_MAX_S = 0.050       # a held packet with nothing behind it waits at most this
RECV_BYTES = 65535

# name -> parameters (one table; the record's profile table is this one)
PROFILES: dict[str, dict[str, Any]] = {
    # G8-S1: the control -- the shim in the path with no stage (its own cost), selectable through the flag
    "none": {},
    "loss-1": {"loss": 0.01},
    "loss-5": {"loss": 0.05},
    "burst-50x20": {"burst_packets": 50, "burst_every_s": 20.0, "burst_first_s": 10.0},
    "delay-50": {"delay_ms": 50.0},
    "delay-150": {"delay_ms": 150.0},
    "jitter-30": {"jitter_ms": 30.0},
    "reorder-5": {"reorder": 0.05},
    "cap-6000": {"cap_kbps": 6000},
    "cap-4500": {"cap_kbps": 4500},
}


@dataclass
class Profile:
    names: tuple[str, ...]
    placement: str = PRE_FEC
    seed: int = 1
    loss: float = 0.0
    burst_packets: int = 0
    burst_every_s: float = 0.0
    burst_first_s: float = 0.0
    delay_ms: float = 0.0
    jitter_ms: float = 0.0
    reorder: float = 0.0
    cap_kbps: int = 0
    blackout_s: float = 0.0          # B1
    blackout_every_s: float = 0.0
    blackout_first_s: float = 0.0
    uplink: bool = False

    @property
    def label(self) -> str:
        return "+".join(self.names)


def _seconds(value: str, what: str) -> float:
    v = value.strip().lower()
    if not v.endswith("s") or not re.fullmatch(r"\d+(?:\.\d+)?", v[:-1]):
        raise ValueError(f"impairment: bad {what} {value!r}")
    return float(v[:-1])


def parse(spec: str) -> Profile:
    """`loss-1+delay-50@post-fec,seed=7` -> a Profile. Unknown names raise ValueError.

    B1: `blackout-4s@both,every=120s,first=120s,seed=1`; options are `key=value`, any order."""
    raw = spec.strip()
    seed = 1
    opts: dict[str, float] = {}
    if "," in raw:
        raw, _, tail = raw.partition(",")
        for part in tail.split(","):
            key, _, value = part.partition("=")
            key = key.strip()
            if key == "seed" and value.strip().lstrip("-").isdigit():
                seed = int(value)
            elif key in ("every", "first") and key not in opts:
                opts[key] = _seconds(value, key)
            else:
                raise ValueError(f"impairment: bad option {part!r}")
    placement = PRE_FEC
    if "@" in raw:
        raw, _, placement = raw.partition("@")
        placement = placement.strip().lower()
        if placement not in (PRE_FEC, POST_FEC, BOTH, DOWN):
            raise ValueError(f"impairment: bad placement {placement!r}")
    names = tuple(n.strip() for n in raw.split("+") if n.strip())
    if not names:
        raise ValueError("impairment: empty profile")
    uplink = placement == BOTH
    if placement in (BOTH, DOWN):
        placement = POST_FEC
    p = Profile(names=names, placement=placement, seed=seed, uplink=uplink)
    for n in names:
        m = BLACKOUT_RE.match(n)
        if m:
            d = float(m.group(1))
            if not 0.1 <= d <= 60.0:
                raise ValueError(f"impairment: blackout length out of range {n!r}")
            p.blackout_s = max(p.blackout_s, d)
            continue
        if n not in PROFILES:
            raise ValueError(f"impairment: unknown profile {n!r}")
        for k, v in PROFILES[n].items():
            # a combination of two of a kind keeps the stronger
            cur = getattr(p, k)
            setattr(p, k, max(cur, v) if isinstance(v, (int, float)) else v)
    if p.blackout_s:
        p.blackout_every_s = opts.get("every", BLACKOUT_EVERY_S)
        p.blackout_first_s = opts.get("first", p.blackout_every_s)
        if p.blackout_every_s <= p.blackout_s:
            raise ValueError("impairment: blackout every= must exceed its length")
    elif opts or uplink or "@" + DOWN in spec.lower():
        raise ValueError("impairment: every= / first= / @both / @down need a blackout-<D>s profile")
    return p


def from_environ(environ: Mapping[str, str]) -> Profile | None:
    raw = (environ.get(FLAG_ENV) or "").strip()
    return parse(raw) if raw else None


# ---- B1: the blackout's one scheduler, and the uplink gate ----------------------

class Blackout:
    """Pure: dark for `d_s` every `every_s`, the first at `epoch + first_s`. Monotonic seconds."""

    def __init__(self, d_s: float, every_s: float, first_s: float, epoch: float) -> None:
        self.d_s, self.every_s, self.first_s, self.epoch = float(d_s), float(every_s), float(first_s), float(epoch)

    def active(self, now: float) -> bool:
        t = now - self.epoch - self.first_s
        return t >= 0.0 and (t % self.every_s) < self.d_s


class UplinkGate:
    """The uplink's drop decision at the host's receive points, on the shared schedule; counted by kind."""

    def __init__(self, blackout: Blackout, clock=time.monotonic) -> None:
        self.blackout = blackout
        self._clock = clock
        self._lock = threading.Lock()
        self.dropped = {k: 0 for k in UPLINK_KINDS}

    @property
    def total(self) -> int:
        return sum(self.dropped.values())

    def drop(self, kind: str) -> bool:
        if not self.blackout.active(self._clock()):
            return False
        with self._lock:
            self.dropped[kind] = self.dropped.get(kind, 0) + 1
        return True


_SHARED: dict[str, Blackout] = {}
_GATES: dict[str, UplinkGate] = {}
_SHARED_LOCK = threading.Lock()


def _key(p: Profile) -> str:
    return f"{p.blackout_s}/{p.blackout_every_s}/{p.blackout_first_s}"


def shared_blackout(p: Profile, clock=time.monotonic) -> Blackout | None:
    """The process's one scheduler for this blackout (epoch = the first call)."""
    if not p.blackout_s:
        return None
    with _SHARED_LOCK:
        b = _SHARED.get(_key(p))
        if b is None:
            b = _SHARED[_key(p)] = Blackout(p.blackout_s, p.blackout_every_s, p.blackout_first_s, clock())
        return b


def uplink_gate(p: Profile) -> UplinkGate | None:
    """The shared uplink gate, only for a blackout `@both`."""
    if not (p.blackout_s and p.uplink):
        return None
    b = shared_blackout(p)
    with _SHARED_LOCK:
        g = _GATES.get(_key(p))
        if g is None:
            g = _GATES[_key(p)] = UplinkGate(b)
        return g


def uplink_gate_from_environ(environ: Mapping[str, str]) -> UplinkGate | None:
    """What the receive loops hold: a gate for `@both`, None for anything else (today's profiles included)."""
    try:
        p = from_environ(environ)
    except ValueError:
        return None
    return uplink_gate(p) if p is not None else None


@dataclass
class Counters:
    packets_in: int = 0
    packets_out: int = 0
    bytes_in: int = 0
    bytes_out: int = 0
    dropped_loss: int = 0
    dropped_burst: int = 0
    dropped_queue: int = 0
    delayed: int = 0
    reordered: int = 0
    dropped_blackout: int = 0        # B1: the downlink's dark spans
    uplink_dropped: int = 0          # B1: the uplink gate's total (with @both)
    queue_max: int = 0
    send_errors: int = 0
    cpu_s: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return dict(self.__dict__)


@dataclass(order=True)
class _Due:
    at: float
    seq: int
    data: bytes = field(compare=False)


class Impairer:
    """The pure part: given (arrival time, packet), decide drop / when to release.

    No socket, no clock of its own: `offer` and `due` take the time. One stage
    order: burst, loss, reorder, delay + jitter, cap."""

    def __init__(self, p: Profile, start: float, blackout: Blackout | None = None) -> None:
        self.p = p
        # B1: the shared scheduler when given; else this impairer's own, from its start
        self.blackout = blackout if blackout is not None else (
            Blackout(p.blackout_s, p.blackout_every_s, p.blackout_first_s, start) if p.blackout_s else None)
        self.rng = random.Random(p.seed)
        self.start = start
        self.counters = Counters()
        self._heap: list[_Due] = []
        self._seq = 0
        self._last_release = 0.0
        self._link_free_at = 0.0
        self._held: tuple[bytes, float] | None = None
        self._burst_left = 0
        self._next_burst = start + p.burst_first_s if p.burst_packets else None

    def _push(self, at: float, data: bytes) -> None:
        self._seq += 1
        heapq.heappush(self._heap, _Due(at, self._seq, data))
        depth = len(self._heap)
        if depth > self.counters.queue_max:
            self.counters.queue_max = depth

    def _schedule(self, now: float, data: bytes) -> None:
        p = self.p
        at = now
        if p.delay_ms or p.jitter_ms:
            at = now + (p.delay_ms + (self.rng.uniform(0.0, p.jitter_ms) if p.jitter_ms else 0.0)) / 1000.0
            at = max(at, self._last_release)        # FIFO: jitter never reorders
            self._last_release = at
            self.counters.delayed += 1
        if p.cap_kbps:
            depart = max(at, self._link_free_at)
            if depart - at > QUEUE_LIMIT_S:
                self.counters.dropped_queue += 1      # tail drop: the queue is bounded
                return
            self._link_free_at = depart + len(data) * 8.0 / (p.cap_kbps * 1000.0)
            at = depart
        self._push(at, data)

    def offer(self, now: float, data: bytes) -> None:
        p, c = self.p, self.counters
        c.packets_in += 1
        c.bytes_in += len(data)
        if self.blackout is not None and self.blackout.active(now):
            c.dropped_blackout += 1                    # B1: the link is dark
            return
        if self._next_burst is not None and now >= self._next_burst:
            self._burst_left = p.burst_packets
            self._next_burst += p.burst_every_s
        if self._burst_left > 0:
            self._burst_left -= 1
            c.dropped_burst += 1
            return
        if p.loss and self.rng.random() < p.loss:
            c.dropped_loss += 1
            return
        if self._held is not None:
            held, _ = self._held
            self._held = None
            self._schedule(now, data)
            self._schedule(now, held)                  # one slot later: a swap
            c.reordered += 1
            return
        if p.reorder and self.rng.random() < p.reorder:
            self._held = (data, now)
            return
        self._schedule(now, data)

    def due(self, now: float) -> list[bytes]:
        if self._held is not None and now - self._held[1] >= REORDER_HOLD_MAX_S:
            held, _ = self._held
            self._held = None
            self._schedule(now, held)
        out = []
        while self._heap and self._heap[0].at <= now:
            out.append(heapq.heappop(self._heap).data)
        return out

    def next_due(self) -> float | None:
        t = self._heap[0].at if self._heap else None
        if self._held is not None:
            h = self._held[1] + REORDER_HOLD_MAX_S
            t = h if t is None else min(t, h)
        return t

    def depth(self) -> int:
        return len(self._heap) + (1 if self._held is not None else 0)


class Shim:
    """The relay thread: listen on the loopback, impair, forward."""

    def __init__(self, profile: Profile, listen_port: int = 0, forward: tuple[str, int] | None = None,
                 log_path: Path | None = None, clock=time.monotonic, blackout: Blackout | None = None,
                 gate: UplinkGate | None = None) -> None:
        self.profile = profile
        self._clock = clock
        self.sock_in = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_in.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 * 1024 * 1024)
        self.sock_in.bind((LOOPBACK, int(listen_port)))
        self.sock_out = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_out.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2 * 1024 * 1024)
        self.forward = forward
        self.log_path = log_path
        self.impairer = Impairer(profile, clock(), blackout)
        self.gate = gate                                 # B1: the uplink's counters ride this shim's lines
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self.lines: list[dict[str, Any]] = []        # the per-second lines (also written, if a path)

    @property
    def port(self) -> int:
        return int(self.sock_in.getsockname()[1])

    def start(self) -> None:
        if self.forward is None:
            raise ValueError("impairment: no forward target")
        self._running = True
        self._thread = threading.Thread(target=self._run, name="PrivyHub-Impairment", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        t = self._thread
        if t is not None:
            t.join(timeout=2.0)
        for s in (self.sock_in, self.sock_out):
            try:
                s.close()
            except OSError:
                pass

    def counters(self) -> dict[str, Any]:
        with self._lock:
            if self.gate is not None:
                self.impairer.counters.uplink_dropped = self.gate.total
            return self.impairer.counters.as_dict()

    def _send(self, packets: list[bytes]) -> None:
        c = self.impairer.counters
        for data in packets:
            try:
                self.sock_out.sendto(data, self.forward)
                c.packets_out += 1
                c.bytes_out += len(data)
            except OSError:
                c.send_errors += 1

    def _write_line(self, now: float, prev: dict[str, Any]) -> dict[str, Any]:
        if self.gate is not None:
            self.impairer.counters.uplink_dropped = self.gate.total
        cur = self.impairer.counters.as_dict()
        line = {"schema": SCHEMA, "t_s": round(now - self.impairer.start, 3), "profile": self.profile.label,
                "placement": self.profile.placement, "seed": self.profile.seed,
                **{k: (round(cur[k] - prev.get(k, 0), 6) if k == "cpu_s" else cur[k] - prev.get(k, 0))
                   for k in cur if k != "queue_max"},
                "queue_depth": self.impairer.depth(), "queue_max": cur["queue_max"]}
        self.lines.append(line)
        if self.log_path is not None:
            try:
                self.log_path.parent.mkdir(parents=True, exist_ok=True)
                with self.log_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(line, sort_keys=True) + "\n")
            except OSError:
                pass
        return cur

    def _run(self) -> None:
        cpu0 = time.thread_time()
        next_line = self._clock() + 1.0
        prev: dict[str, Any] = {}
        sock = self.sock_in
        while self._running:
            now = self._clock()
            nd = self.impairer.next_due()
            timeout = 0.05 if nd is None else max(0.0, min(0.05, nd - now))
            try:
                ready, _, _ = select.select([sock], [], [], timeout)
            except (OSError, ValueError):
                break
            now = self._clock()
            if ready:
                for _ in range(64):              # drain what is there, bounded
                    try:
                        data = sock.recv(RECV_BYTES, socket.MSG_DONTWAIT)
                    except (BlockingIOError, InterruptedError):
                        break
                    except OSError:
                        self._running = False
                        break
                    with self._lock:
                        self.impairer.offer(now, data)
            with self._lock:
                out = self.impairer.due(self._clock())
            if out:
                self._send(out)
            if now >= next_line:
                with self._lock:
                    self.impairer.counters.cpu_s = time.thread_time() - cpu0
                    prev = self._write_line(now, prev)
                next_line += 1.0
        with self._lock:
            self.impairer.counters.cpu_s = time.thread_time() - cpu0


# ---- the FEC sender's hook (native_fec_relay, under the flag only) ------------

class RelayShim:
    """What `NativeVideoFecRelay.start()` asks for: where to bind, where to send."""

    def __init__(self, profile: Profile, relay_port: int, client: tuple[str, int], log_path: Path | None) -> None:
        self.profile = profile
        self.client = client
        b, g = shared_blackout(profile), uplink_gate(profile)    # B1: one scheduler with the uplink
        if profile.placement == PRE_FEC:
            # the shim takes the sender's port; the sender binds an ephemeral one
            self.shim = Shim(profile, listen_port=relay_port, forward=None, log_path=log_path, blackout=b, gate=g)
            self.relay_bind_port = 0
            self.relay_send_target = client
        else:
            self.shim = Shim(profile, listen_port=0, forward=client, log_path=log_path, blackout=b, gate=g)
            self.relay_bind_port = relay_port
            self.relay_send_target = (LOOPBACK, self.shim.port)

    def attach(self, relay_recv_port: int) -> None:
        if self.profile.placement == PRE_FEC:
            self.shim.forward = (LOOPBACK, int(relay_recv_port))
        self.shim.start()

    def stop(self) -> None:
        self.shim.stop()

    def status(self) -> dict[str, Any]:
        out = {"profile": self.profile.label, "placement": self.profile.placement, "seed": self.profile.seed,
               "counters": self.shim.counters()}
        if self.shim.gate is not None:                   # B1: the uplink's drops by kind
            out["uplink_dropped_by_kind"] = dict(self.shim.gate.dropped)
        return out


def relay_shim_from_environ(environ: Mapping[str, str], relay_port: int, client: tuple[str, int],
                            project_root: Path | None = None) -> RelayShim | None:
    p = from_environ(environ)
    if p is None:
        return None
    log = (Path(project_root) / "logs" / "impairment.jsonl") if project_root is not None else None
    return RelayShim(p, relay_port, client, log)
