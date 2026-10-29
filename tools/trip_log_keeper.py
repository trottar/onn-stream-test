#!/usr/bin/env python3
"""B30: the trip's log-keeper -- read-only; it copies the hub's rotating logs for a date range, redacted.

    python3 tools/trip_log_keeper.py --out docs/memory/evidence/trip_2026-10-30 --cap 2026-11-01T23:59Z
        [--start <UTC>] [--copy-s 300] [--sample-s 60] [--once]

From --start (default now) until the cap (written to <out>/cap_utc.txt at launch) or <out>/STOP:
- every --copy-s: the new bytes of G4-S4's logs (the ladder, heartbeat, recovery, control-gap, frame-size,
  host-sampler, audio and video logs in logs/games/; the hub's wan_sessions, session_audit and impairment rows; each
  game log; the companion's journal) into a NEW chunk file raw/<log>/<NNNNNN>_<UTC><ext> (never a reused name, never
  an existing file opened for writing), following rotation by inode into stream_log_archive/<log>.1..3; the new files
  in decoder_sessions/ and audio_timing/ once each; one sha256sum line per kept file appended to manifest.sha256;
- every --sample-s: the overlay state (connected, path, peer_ready, mtu, reason; online peers by count) and the
  session state (active, paused, the system's class, the stream) into samples/*.jsonl;
- the redactor on everything kept: the tailnet's names, the nodes' names, addresses and endpoints (re-read every copy),
  the host's addresses, the paired devices' ids and keys, and any IPv4 / IPv6 / MAC / client id / long hex literal ->
  placeholders, counted per kind; no value is printed;
- status.txt (one line), and a last copy at the end. It holds no file open between steps, so a companion restart is
  just a rotation or a gap. No stream, no restart, no adb, no game; nothing deleted.
Design: docs/memory/evidence/b30_2026-10-28/design_written_before_code.md (hashed before this code).
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

REPO = Path(__file__).resolve().parents[1]
GAMES_TAILS = ["adaptive_bitrate_shadow.jsonl", "native_stream_heartbeat.log", "native_stream_recovery.log",
               "native_stream_ctrl_gaps.log", "native_frame_sizes.jsonl", "host_resource_samples.jsonl",
               "native_pulseaudio.log", "native_video_alpha.log"]
TOP_TAILS = ["wan_sessions.jsonl", "session_audit.jsonl", "impairment.jsonl"]
NEWDIRS = ["decoder_sessions", "audio_timing"]
GAME_LOG = re.compile(r"^\d{8}-\d{6}-game_[a-z0-9]+_[0-9a-f]+\.log$")
UNIT = "privyhub-companion"
STATUS_URL = "http://127.0.0.1:8765/plugins/games/status"
QUIET_S = 10.0
SKIP_NAMES = {"privyhub", "localhost"}

# ---------------------------------------------------------------- time


def utc(t: float | None = None) -> str:
    return datetime.fromtimestamp(time.time() if t is None else t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def stamp(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def parse_utc(s: str, now: float) -> float:
    s = s.strip()
    if s.lower() == "now":
        return now
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%MZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            continue
    raise ValueError(f"not a UTC time: {s!r}")

# ---------------------------------------------------------------- the redactor

IPV4 = re.compile(r"(?<![\w.])(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})(?![\w.])")
IPV6 = re.compile(r"(?<![\w:.])((?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4})(?![\w:])")
MAC = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
CLIENT = re.compile(r"\bdev-[0-9a-f]{8,}\b")
HEX = re.compile(r"\b[0-9a-fA-F]{32,}\b")


def load_secrets() -> list[tuple[str, str]]:
    """(value, placeholder) pairs, read in process, never printed."""
    out: list[tuple[str, str]] = []
    try:
        ts = json.loads(subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True,
                                       timeout=20).stdout or "{}")
    except (OSError, subprocess.SubprocessError, ValueError):
        ts = {}
    tn = ts.get("CurrentTailnet") or {}
    out += [(tn.get("Name"), "<tailnet>"), (tn.get("MagicDNSSuffix"), "<tailnet>"), (ts.get("MagicDNSSuffix"), "<tailnet>")]
    for n in [ts.get("Self") or {}] + list((ts.get("Peer") or {}).values()):
        out += [((n.get("DNSName") or "").rstrip("."), "<node-name>"), (n.get("HostName"), "<node-name>")]
        out += [(a, "<tailnet-address>") for a in n.get("TailscaleIPs") or []]
        for ep in [n.get("CurAddr")] + list(n.get("Addrs") or []):
            if ep:
                out += [(ep, "<endpoint>"), (ep.rsplit(":", 1)[0].strip("[]"), "<endpoint-host>")]
    try:
        text = subprocess.run(["ip", "-4", "addr"], capture_output=True, text=True, timeout=10).stdout
        out += [(a, "<host-address>") for a in re.findall(r"inet (\d+\.\d+\.\d+\.\d+)", text)
                if not a.startswith("127.")]
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        store = json.loads((Path.home() / ".config/privyhub/paired_devices.json").read_text())
        for d in store.get("devices", []):
            out += [(d.get("device_id"), "<device-id>"), (d.get("key_hex"), "<key>")]
    except (OSError, ValueError, AttributeError):
        pass
    return out


def online_peers() -> int | None:
    """Online peers, by count only."""
    try:
        ts = json.loads(subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True,
                                       timeout=20).stdout or "{}")
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return sum(1 for p in (ts.get("Peer") or {}).values() if p.get("Online"))


class Redactor:
    def __init__(self, source: Callable[[], Iterable[tuple[Any, str]]] = load_secrets) -> None:
        self._source = source
        self._pairs: list[tuple[re.Pattern[str], str]] = []
        self.refresh()

    def refresh(self) -> None:
        try:
            pairs = list(self._source())
        except Exception:
            pairs = []
        keep = {}
        for value, ph in pairs:
            v = str(value or "").strip()
            if len(v) >= 4 and v.lower() not in SKIP_NAMES:
                keep[v] = ph
        self._pairs = [(re.compile(r"(?<![\w.-])" + re.escape(v) + r"(?![\w-])"), ph)
                       for v, ph in sorted(keep.items(), key=lambda kv: -len(kv[0]))]

    def apply(self, text: str) -> tuple[str, dict[str, int]]:
        counts: dict[str, int] = {}

        def count(ph: str, n: int = 1) -> None:
            if n:
                counts[ph] = counts.get(ph, 0) + n

        for rx, ph in self._pairs:
            text, n = rx.subn(ph, text)
            count(ph, n)
        text, n = CLIENT.subn("<client-id>", text)
        count("<client-id>", n)
        text, n = MAC.subn("<mac>", text)
        count("<mac>", n)

        def v4(m: re.Match[str]) -> str:
            try:
                ip = ipaddress.ip_address(m.group(1))
            except ValueError:
                return m.group(0)
            if ip.is_loopback or str(ip) == "0.0.0.0":
                return m.group(0)
            count("<ipv4>")
            return "<ipv4>"

        def v6(m: re.Match[str]) -> str:
            try:
                ip = ipaddress.ip_address(m.group(1))
            except ValueError:
                return m.group(0)
            if ip.is_loopback or ip.is_unspecified:
                return m.group(0)
            count("<ipv6>")
            return "<ipv6>"

        text = IPV4.sub(v4, text)
        text = IPV6.sub(v6, text)
        text, n = HEX.subn("<hex>", text)
        count("<hex>", n)
        return text, counts

    def bytes(self, data: bytes) -> tuple[bytes, dict[str, int]]:
        text, counts = self.apply(data.decode("utf-8", errors="surrogateescape"))
        return text.encode("utf-8", errors="surrogateescape"), counts

# ---------------------------------------------------------------- the sources


def read_from(p: Path, off: int) -> bytes:
    with open(p, "rb") as fh:
        fh.seek(off)
        return fh.read()


class Tail:
    """One log by path: its new bytes since the last step, following rotation by inode (G4-S4's)."""

    def __init__(self, live: Path, archive: Path | None, from_start: bool = False) -> None:
        self.live, self.archive = live, archive
        try:
            st = live.stat()
            self.ino, self.off = st.st_ino, (0 if from_start else st.st_size)
        except OSError:
            self.ino, self.off = None, 0

    def step(self) -> tuple[bytes, bool]:
        out, rotated = b"", False
        try:
            st = self.live.stat()
        except OSError:
            return b"", False                                   # gone for now (a restart); followed when back
        if self.ino is not None and st.st_ino != self.ino:
            rotated = True
            if self.archive is not None:
                for i in (1, 2, 3):
                    a = self.archive / f"{self.live.name}.{i}"
                    try:
                        if a.stat().st_ino == self.ino:
                            out += read_from(a, self.off)
                            break
                    except OSError:
                        continue
            self.off = 0
        self.ino = st.st_ino
        if st.st_size < self.off:
            self.off, rotated = 0, True                         # truncated
        got = read_from(self.live, self.off)
        self.off += len(got)
        return out + got, rotated


class Keeper:
    def __init__(self, out: Path, cap: float, start: float, logs_root: Path = REPO / "logs",
                 redactor: Redactor | None = None, overlay: Callable[[], dict[str, Any]] | None = None,
                 session: Callable[[], dict[str, Any]] | None = None, journal: Callable[[int, int], bytes] | None = None,
                 peers: Callable[[], int | None] = online_peers, clock: Callable[[], float] = time.time,
                 sleep: Callable[[float], None] = time.sleep, copy_s: float = 300.0, sample_s: float = 60.0) -> None:
        self.out, self.cap, self.start = Path(out), cap, start
        self.logs = Path(logs_root)
        self.games = self.logs / "games"
        self.arch = self.games / "stream_log_archive"
        self.raw, self.samples = self.out / "raw", self.out / "samples"
        self.redactor = redactor if redactor is not None else Redactor()
        self._overlay = overlay if overlay is not None else overlay_state
        self._session = session if session is not None else session_state
        self._journal = journal if journal is not None else read_journal
        self._peers = peers
        self.clock, self.sleep = clock, sleep
        self.copy_s, self.sample_s = copy_s, sample_s
        self.tails: dict[str, Tail] = {}
        self.seen: dict[str, set[str]] = {}
        self.jsince: int | None = None
        self.copies = self.samples_n = 0
        self.last_copy = "-"
        self.last_sample = "-"
        self.phase = "starting"

    # -- the files ------------------------------------------------------------------------------------------------
    def stop_file(self) -> Path:
        return self.out / "STOP"

    def why_end(self) -> str | None:
        if self.stop_file().exists():
            return "STOP"
        if self.clock() >= self.cap:
            return "the cap"
        return None

    def _keep(self, sub: str, name_tail: str, data: bytes) -> dict[str, Any]:
        """A new kept file: redacted, created exclusively (never an existing name), its hash appended."""
        red, counts = self.redactor.bytes(data)
        d = self.raw / sub
        d.mkdir(parents=True, exist_ok=True)
        n = len([x for x in d.iterdir()])
        while True:
            p = d / f"{n:06d}_{name_tail}"
            try:
                with open(p, "xb") as fh:
                    fh.write(red)
                break
            except FileExistsError:
                n += 1
        with open(self.out / "manifest.sha256", "a") as fh:
            fh.write(f"{hashlib.sha256(red).hexdigest()}  {p.relative_to(self.out).as_posix()}\n")
        return {"file": p.relative_to(self.out).as_posix(), "bytes": len(red), "redacted": counts}

    def _status(self) -> None:
        line = (f"{utc(self.clock())} | {self.phase} | copies {self.copies}, last {self.last_copy} | samples "
                f"{self.samples_n}, last {self.last_sample} | cap {utc(self.cap)} | stop: touch {self.stop_file()}\n")
        tmp = self.out / "status.txt.new"
        tmp.write_text(line)
        tmp.replace(self.out / "status.txt")

    def _row(self, name: str, row: dict[str, Any]) -> None:
        self.samples.mkdir(parents=True, exist_ok=True)
        text, _ = self.redactor.apply(json.dumps(row, sort_keys=True, default=str))
        with open(self.samples / name, "a") as fh:
            fh.write(text + "\n")

    # -- the copy ---------------------------------------------------------------------------------------------------
    def begin(self) -> None:
        """At the start: every source's position now (only what comes after is kept)."""
        for n in GAMES_TAILS:
            self.tails[f"games/{n}"] = Tail(self.games / n, self.arch)
        for n in TOP_TAILS:
            self.tails[n] = Tail(self.logs / n, None)
        for sub in NEWDIRS:
            d = self.games / sub
            self.seen[sub] = set(os.listdir(d)) if d.is_dir() else set()
        self.seen["game_logs"] = {f for f in (os.listdir(self.games) if self.games.is_dir() else []) if GAME_LOG.match(f)}
        self.jsince = int(self.clock())

    def copy(self, final: bool = False) -> dict[str, Any]:
        now = self.clock()
        self.redactor.refresh()
        row: dict[str, Any] = {"at_utc": utc(now), "final": final, "kept": []}
        # new game logs become tails from their first byte
        if self.games.is_dir():
            for f in sorted(os.listdir(self.games)):
                if GAME_LOG.match(f) and f not in self.seen["game_logs"]:
                    self.seen["game_logs"].add(f)
                    self.tails[f"games/{f}"] = Tail(self.games / f, None, from_start=True)
        for key, t in self.tails.items():
            try:
                data, rotated = t.step()
            except OSError as exc:
                row.setdefault("errors", {})[key] = type(exc).__name__
                continue
            if data:
                ext = "".join(Path(key).suffixes) or ".txt"
                kept = self._keep(key.replace("/", "__"), f"{stamp(now)}{ext}", data)
                kept["rotated"] = rotated
                row["kept"].append(kept)
        for sub in NEWDIRS:
            d = self.games / sub
            if not d.is_dir():
                continue
            for f in sorted(os.listdir(d)):
                if f in self.seen[sub]:
                    continue
                p = d / f
                try:
                    if not final and now - p.stat().st_mtime < QUIET_S:
                        continue
                    data = p.read_bytes()
                except OSError:
                    continue
                self.seen[sub].add(f)
                row["kept"].append(self._keep(f"games__{sub}", f, data))
        until = int(now)
        try:
            j = self._journal(self.jsince or until, until)
            self.jsince = until
            if j:
                row["kept"].append(self._keep("companion_journal", f"{stamp(now)}.txt", j))
        except Exception as exc:
            row.setdefault("errors", {})["journal"] = type(exc).__name__
        self.copies += 1
        self.last_copy = f"{utc(now)} ({sum(k['bytes'] for k in row['kept'])} B in {len(row['kept'])} files)"
        self.samples.mkdir(parents=True, exist_ok=True)
        with open(self.samples / "copies.jsonl", "a") as fh:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        return row

    def sample(self) -> None:
        now = self.clock()
        try:
            ov = dict(self._overlay())
        except Exception as exc:
            ov = {"error": type(exc).__name__}
        try:
            ov["peers_online"] = self._peers()
        except Exception:
            ov["peers_online"] = None
        self._row("overlay.jsonl", {"at_utc": utc(now), **ov})
        try:
            ss = dict(self._session())
        except Exception as exc:
            ss = {"error": type(exc).__name__}
        self._row("session.jsonl", {"at_utc": utc(now), **ss})
        self.samples_n += 1
        self.last_sample = f"{utc(now)} ({ov.get('path', '?')}, {ss.get('state', '?')})"

    # -- the run ----------------------------------------------------------------------------------------------------
    def run(self, once: bool = False) -> str:
        self.out.mkdir(parents=True, exist_ok=True)
        cap_p = self.out / "cap_utc.txt"
        if cap_p.exists() and cap_p.read_text().strip() != utc(self.cap):
            raise SystemExit(f"{cap_p} holds another cap; not overwritten")
        if not cap_p.exists():
            cap_p.write_text(utc(self.cap) + "\n")
        self.phase = f"waiting for the start {utc(self.start)}"
        self._status()
        while self.clock() < self.start:
            if self.why_end():
                break
            self.sleep(min(30.0, max(0.5, self.start - self.clock())))
        self.begin()
        self.phase = "running"
        next_copy, next_sample = self.clock() + self.copy_s, self.clock()
        why = None
        while True:
            why = self.why_end()
            if why:
                break
            now = self.clock()
            if now >= next_sample:
                self.sample()
                next_sample = now + self.sample_s
            if now >= next_copy:
                self.copy()
                next_copy = now + self.copy_s
            self._status()
            if once:
                why = "once"
                break
            self.sleep(max(0.5, min(next_copy, next_sample, self.cap) - self.clock()))
        self.copy(final=True)
        self.phase = f"done ({why})"
        self._status()
        return why

# ---------------------------------------------------------------- the real readers


def overlay_state() -> dict[str, Any]:
    r = subprocess.run([sys.executable, "-m", "companion.overlay", "--state", "--provider", "tailscale"],
                       capture_output=True, text=True, timeout=30, cwd=str(REPO))
    st = (json.loads(r.stdout) or {}).get("state") or {}
    return {k: st.get(k) for k in ("connected", "path", "peer_ready", "mtu", "reason")}


def session_state() -> dict[str, Any]:
    with urllib.request.urlopen(STATUS_URL, timeout=10) as resp:
        g = json.loads(resp.read().decode() or "{}")
    game = g.get("game") if isinstance(g.get("game"), dict) else {}
    ns = g.get("native_stream") if isinstance(g.get("native_stream"), dict) else {}
    active, paused, streaming = bool(g.get("active")), g.get("paused"), bool(ns.get("active"))
    state = "PLAYING" if active and streaming and not paused else ("paused" if active and paused else
                                                                   ("game, no stream" if active else "idle"))
    return {"state": state, "game_active": active, "paused": paused, "system": game.get("system"),
            "native_stream_active": streaming}


def read_journal(since: int, until: int) -> bytes:
    return subprocess.run(["journalctl", "--user", "-u", UNIT, "-o", "short-iso-precise", "--no-pager",
                           "--since", f"@{since}", "--until", f"@{until}"], capture_output=True, timeout=120).stdout


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--cap", required=True, help="the end, UTC (e.g. 2026-11-01T23:59Z)")
    ap.add_argument("--start", default="now", help="UTC, or now")
    ap.add_argument("--copy-s", type=float, default=300.0)
    ap.add_argument("--sample-s", type=float, default=60.0)
    ap.add_argument("--once", action="store_true", help="one sample and one copy, then stop (a check)")
    a = ap.parse_args(argv)
    now = time.time()
    cap, start = parse_utc(a.cap, now), parse_utc(a.start, now)
    if cap <= start:
        ap.error("the cap is not after the start")
    k = Keeper(a.out, cap, start, copy_s=a.copy_s, sample_s=a.sample_s)
    why = k.run(once=a.once)
    print(f"trip log-keeper: done ({why}); {k.copies} copies, {k.samples_n} samples; {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
