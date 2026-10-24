#!/usr/bin/env python3
"""G4-P1: the suite's off-site row — `tools/e1_suite.py run --remote …`.

A PS1-STREAM row against a client reached **over the overlay**. Reached
only through `e1_suite.main` when `--remote` is given (a guarded import);
without it the suite is today's.

    python3 tools/e1_suite.py run --remote --out <dir> --prereg <file.txt> \\
        [--runs 3] [--window 600] [--gap 300] [--wait 900] [--adb]

What differs from the home row:

- **Preflight.** The companion must run with
  `PRIVYHUB_SESSION_IDENTITY=v2` **and** `PRIVYHUB_OVERLAY_PROVIDER=tailscale`,
  read back from its environ; else the row refuses with one line.
  `PRIVYHUB_WAN_TELEMETRY=1` is optional (G5-S1's `wan` object is sampled if
  present). Nothing is restarted, no flag is set, no drop-in is written.
- **The launch is the user's.** They start the PS1 game on the onn (over
  the overlay; the onn on another uplink). The suite waits for PLAYING
  (`--wait`, default 900 s).
- **The endpoint.** Remote or not is read from the client's control
  connections to the companion (`/proc/net/tcp`, `tcp6`, local port 8765).
  A peer address in the overlay's range makes the row remote. G3 makes the
  declared media host share the source's class. **The address is never
  written**: the record carries "overlay" and a 12-hex hash only.
- **The path.** Every 10 s: `/status`'s `overlay` (connected, path direct /
  relayed / no-peer, MTU, endpoint present + hash) and `wan` if present →
  `path.jsonl`.
- **adb is optional.** If an adb device answers (adb over the overlay, set up
  by hand) and `--adb` is given, the client's session report is harvested
  at teardown. Otherwise the record says `client: not harvested`, and the
  row does not fail for it.
- **The window** defaults to 10 min for the first test. The E2 warm-up is
  kept (PS1-STREAM's 90 s from PLAYING).

The host sampler, telemetry, heartbeat and status-poll figures are the home
row's own functions (`e1_suite`).

G4-P2: gate 3 (the host side) is recorded as the home row records it:

- the home row's per-run RetroArch counter override (`TEKKEN["override"]`,
  `COUNTER` + `E1_COUNTER_EXTRA`), written before the sampler starts, refused if
  a file is already there, removed at teardown. It is per game: it applies when the
  user starts the PS1-STREAM fixture, Tekken 3;
- the sampler started with `--e2`, so `encoder.jsonl` is written and kept;
- the summary's `key["retroarch"]` (the home row's key) and `key["gate3"]`:
  `retroarch_fps` (`frames_per_s`), `capture_fps` and `dupdrop_per_min` (E4-S5's
  `segcap` over `encoder.jsonl`), as the gates' clauses compute them.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

REQUIRED_FLAGS = ("PRIVYHUB_SESSION_IDENTITY=v2", "PRIVYHUB_OVERLAY_PROVIDER=tailscale")
OPTIONAL_FLAGS = ("PRIVYHUB_WAN_TELEMETRY=1",)
CONTROL_PORT = 8765
PS1_WARMUP_S = 90           # E1-PS1-STREAM's warm-up (e1_suite WORKLOADS)
DEFAULTS = {"runs": 3, "window": 600, "gap": 300, "wait": 900}

# The overlay's address space (G3-S1's classes), built from integers: the
# shared CGNAT block and the Tailscale IPv6 ULA prefix.
OVERLAY_NETWORKS = (
    ipaddress.ip_network((0x64400000, 10)),
    ipaddress.ip_network((0xFD7A115CA1E0 << 80, 48)),
)


# ---- arguments ------------------------------------------------------------------

def parse_args(argv: list[str]) -> dict[str, Any]:
    """`run --remote --out D --prereg P [--runs N] [--window S] [--gap S] [--wait S] [--adb]`."""
    def value(flag: str, cast: Callable = str, default: Any = None):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 >= len(argv):
                raise ValueError(f"{flag} needs a value")
            return cast(argv[i + 1])
        return default

    a = {
        "out": value("--out", Path),
        "prereg": value("--prereg", Path),
        "runs": value("--runs", int, DEFAULTS["runs"]),
        "window": value("--window", int, DEFAULTS["window"]),
        "gap": value("--gap", int, DEFAULTS["gap"]),
        "wait": value("--wait", int, DEFAULTS["wait"]),
        "adb": "--adb" in argv,
    }
    if a["out"] is None:
        raise ValueError("--out <dir> is required")
    if a["runs"] < 1 or a["window"] < 60 or a["gap"] < 0 or a["wait"] < 60:
        raise ValueError("--runs >= 1, --window >= 60, --gap >= 0, --wait >= 60")
    return a


# ---- the endpoint: class and hash, never the address -----------------------------

def _hex_addr(h: str) -> Any:
    """A /proc/net/tcp{,6} address field ("0100007F:1F49") -> (ip, port)."""
    addr, port = h.split(":")
    raw = bytes.fromhex(addr)
    if len(raw) == 4:
        ip = ipaddress.IPv4Address(raw[::-1])
    else:   # four little-endian 32-bit words
        ip = ipaddress.IPv6Address(b"".join(raw[i:i + 4][::-1] for i in range(0, 16, 4)))
        if ip.ipv4_mapped:
            ip = ip.ipv4_mapped
    return ip, int(port, 16)


def classify(ip: Any) -> str:
    if ip.is_loopback:
        return "local"
    if any(ip.version == n.version and ip in n for n in OVERLAY_NETWORKS):
        return "overlay"
    if ip.is_private:
        return "lan"
    return "unknown"


def endpoint_hash(ip: Any) -> str:
    return hashlib.sha256(str(ip).encode()).hexdigest()[:12]


def control_peers(proc_texts: list[str], port: int = CONTROL_PORT) -> dict[str, Any]:
    """Classes and hashes of the peers connected to the control port. No address leaves this function."""
    classes: dict[str, set] = {}
    for text in proc_texts:
        for line in text.splitlines()[1:]:
            parts = line.split()
            if len(parts) < 3:
                continue
            try:
                (_, lport), (rip, _) = _hex_addr(parts[1]), _hex_addr(parts[2])
            except ValueError:
                continue
            if lport != port or rip.is_unspecified:
                continue
            classes.setdefault(classify(rip), set()).add(endpoint_hash(rip))
    return {cls: sorted(hashes) for cls, hashes in sorted(classes.items())}


def read_control_peers() -> dict[str, Any]:
    texts = []
    for p in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            texts.append(Path(p).read_text())
        except OSError:
            pass
    return control_peers(texts)


# ---- preflight ------------------------------------------------------------------------

def preflight_remote(environ_has: Callable[[str], bool], adb_devices: Callable[[], str],
                     adopted: tuple[str, ...] | list[str] = ()) -> dict[str, Any]:
    # G-A2: the callers pass the home row's adopted set (e1_suite.ADOPTED, nine lines since G-A3); each must be read back too
    need = list(REQUIRED_FLAGS) + [kv for kv in adopted if kv not in REQUIRED_FLAGS]
    d = {
        "flags": {kv: environ_has(kv) for kv in need},
        "optional": {kv: environ_has(kv) for kv in OPTIONAL_FLAGS},
        "adb_device": any(l.endswith("\tdevice") for l in adb_devices().splitlines()[1:]),
    }
    d["ok"] = all(d["flags"].values())
    if not d["ok"]:
        missing = [kv for kv, ok in d["flags"].items() if not ok]
        d["refusal"] = ("refusing: --remote needs the companion running with "
                        + " and ".join(REQUIRED_FLAGS) + (" and the adopted set" if adopted else "")
                        + "; not read back: " + ", ".join(missing))
    return d


# ---- the path sampler ---------------------------------------------------------------

class PathPoller(threading.Thread):
    """Every 10 s: /status's overlay (and wan if present) -> path.jsonl. No address is in either."""

    def __init__(self, path: Path, stop: threading.Event, http: Callable, utc: Callable[[], str]):
        super().__init__(daemon=True)
        self.path, self.stop, self.http, self.utc = path, stop, http, utc

    def run(self):
        with open(self.path, "w") as fh:
            while not self.stop.is_set():
                code, d = self.http("GET", "/status", 10)
                ov = (d or {}).get("overlay") or {}
                wan = (d or {}).get("wan") or {}
                fh.write(json.dumps({
                    "at_utc": self.utc(), "http": code,
                    "overlay": {k: ov.get(k) for k in ("connected", "path", "peer_ready", "mtu", "reason",
                                                       "endpoint", "endpoint_hash")},
                    "wan": ({"class": wan.get("class"), "classes": wan.get("classes"),
                             "last_window": (wan.get("last_window") or {}).get("primary"),
                             "loss_per_min_post_fec": wan.get("loss_per_min_post_fec")} if wan else None),
                }) + "\n")
                fh.flush()
                self.stop.wait(10)


def path_figures(path: Path, t0: str, t1: str) -> dict[str, Any]:
    rows = []
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            if t0 <= r["at_utc"] <= t1:
                rows.append(r)
    if not rows:
        return {"reads": 0}
    paths = [(r.get("overlay") or {}).get("path") for r in rows]
    changes = sum(1 for a, b in zip(paths, paths[1:]) if a != b)
    wan = [r["wan"]["class"] for r in rows if r.get("wan")]
    return {"reads": len(rows), "path_counts": {p: paths.count(p) for p in sorted(set(map(str, paths)))},
            "path_changes": changes,
            "connected_all": all((r.get("overlay") or {}).get("connected") for r in rows),
            "wan_last_class": wan[-1] if wan else "not sampled (PRIVYHUB_WAN_TELEMETRY absent)"}


# ---- gate 3: the host side, as the home row's gates read it (G4-P2) --------------------------

def _ep(t: str) -> float:
    return datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp()


def segcap(rd: Path, t0: str, t1: str) -> tuple[float | None, float | None]:
    """E4-S5's segcap, verbatim in effect (E4-S5D's copy): frames / s and (dup + drop) / min over the
    window from `encoder.jsonl`, a counter reset or a > 3-s hole skipping its pair."""
    rows = []
    p = Path(rd) / "encoder.jsonl"
    if p.exists():
        for line in p.read_text(errors="replace").splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("records") and t0 <= r["at_utc"] <= t1:
                rows.append(r)
    fr = dt = dd = 0.0
    for a, b in zip(rows, rows[1:]):
        d = _ep(b["at_utc"]) - _ep(a["at_utc"])
        if b["frame"] < a["frame"] or d > 3 or b["dup"] < a["dup"] or b["drop"] < a["drop"]:
            continue
        fr += b["frame"] - a["frame"]
        dt += d
        dd += (b["dup"] - a["dup"]) + (b["drop"] - a["drop"])
    return (round(fr / dt, 3) if dt else None, round(dd / (dt / 60), 3) if dt else None)


def gate3_figures(rd: Path, host: dict[str, Any], t0: str, t1: str) -> dict[str, Any]:
    cap, dd = segcap(rd, t0, t1)
    ra = (host or {}).get("retroarch") or {}
    return {"retroarch_fps": ra.get("frames_per_s"), "retroarch_titles": ra.get("titles"),
            "capture_fps": cap, "dupdrop_per_min": dd,
            "clauses": "retroarch_fps >= 59.9; capture_fps 60 +/- 0.1; dupdrop_per_min <= 0.2 (E4-S4 / E4-S5)"}


# ---- one run -------------------------------------------------------------------------------

def run_remote_once(E: Any, run_no: int, out: Path, window: int, gap: int, wait: int, use_adb: bool) -> dict:
    rd = out / "E1-PS1-STREAM-REMOTE" / f"run{run_no}"
    rd.mkdir(parents=True, exist_ok=True)
    rec: dict[str, Any] = {"workload": "E1-PS1-STREAM-REMOTE", "run": run_no, "started_utc": E.utc(),
                           "window_s": window, "gap_s": gap, "warmup_s": PS1_WARMUP_S, "status": "STARTED"}
    stop_ev = threading.Event()
    threads: list[threading.Thread] = []
    samp = None
    try:
        mp = E.mainpid()
        rec["preflight"] = pf = preflight_remote(lambda kv: E.environ_has(mp, kv), lambda: E.adb("devices"), getattr(E, "ADOPTED", ()))
        if not pf["ok"]:
            raise RuntimeError(pf["refusal"])
        # G4-P2: the home row's per-run counter override (RetroArch's title then carries "FPS / Frames")
        override = E.TEKKEN["override"]
        if override.exists():
            raise RuntimeError("a file already sits at the counter override's path; refusing to overwrite")
        override.parent.mkdir(parents=True, exist_ok=True)
        override.write_text(E.COUNTER + os.environ.get("E1_COUNTER_EXTRA", "").replace("\\n", "\n"))
        rec["counter_override"] = "set"
        samp = subprocess.Popen([sys.executable, str(E.REPO / "tools/e1_sampler.py"), "run", str(rd), "--telemetry",
                                 "--title", "--e2"], stdout=open(rd / "sampler.log", "w"), stderr=subprocess.STDOUT)
        E.log("E1-PS1-STREAM-REMOTE", f"run{run_no}: idle gap {gap}s")
        g0 = E.utc()
        time.sleep(gap)
        rec["gap"] = {"from": g0, "to": E.utc()}
        E.log("E1-PS1-STREAM-REMOTE", f"run{run_no}: waiting up to {wait}s -- start a PS1 game on the onn")
        E.log("E1-PS1-STREAM-REMOTE", f"run{run_no}: gate 3 reads RetroArch's counter for the PS1-STREAM fixture "
                                      f"only ({override.stem}; the override is per game)")
        deadline = time.time() + wait
        while time.time() < deadline:
            if E.games_status().get("active") and E.stream_status().get("active"):
                break
            time.sleep(2)
        else:
            raise RuntimeError(f"no stream reached PLAYING within {wait}s")
        playing_t = time.time()
        rec["playing_utc"] = E.utc()
        time.sleep(4)                                    # the client's first control calls
        rec["control_peers"] = peers = read_control_peers()
        rec["endpoint"] = {"class": "overlay" if "overlay" in peers else "not overlay",
                           "hash": (peers.get("overlay") or [None])[0]}
        E.log("E1-PS1-STREAM-REMOTE", f"run{run_no}: PLAYING; client control peer class {sorted(peers)}, "
                                      f"overlay hash {rec['endpoint']['hash']}")
        if "overlay" not in peers:
            raise RuntimeError("the stream's client is not reached over the overlay (no overlay peer on 8765)")
        st = E.stream_status()
        rec["profile_at_playing"] = {k: st.get(k) for k in ("profile_id", "bitrate_kbps", "width", "height")}
        for t in (E.Poller(rd / "status_poll.jsonl", stop_ev), PathPoller(rd / "path.jsonl", stop_ev, E.http, E.utc)):
            t.start()
            threads.append(t)
        time.sleep(max(0, PS1_WARMUP_S - (time.time() - playing_t)))
        t0 = E.utc()
        E.log("E1-PS1-STREAM-REMOTE", f"run{run_no}: window {t0} + {window}s")
        time.sleep(window)
        rec["window"] = {"from": t0, "to": E.utc()}
        rec["status"] = "WINDOW_DONE"
    except Exception as exc:  # noqa: BLE001
        rec["status"] = "FAILED" if rec.get("preflight", {}).get("ok", True) else "REFUSED"
        rec["error"] = f"{type(exc).__name__}: {exc}"[:600]
        E.log("E1-PS1-STREAM-REMOTE", f"run{run_no}: {rec['status']} -- {rec['error']}")
    finally:
        stop_ev.set()
        for t in threads:
            t.join(timeout=30)
        td: dict[str, Any] = {}
        if use_adb and rec.get("preflight", {}).get("adb_device"):
            try:
                before = set()
                td["report"] = E.back_and_report(before)
                td["report_fields"] = E.report_fields(td["report"])
                td["client"] = "harvested over adb"
            except Exception as exc:  # noqa: BLE001
                td["client"] = f"not harvested ({type(exc).__name__})"
        else:
            td["client"] = "not harvested (no adb device or --adb not given)"
        if rec.get("playing_utc"):
            td["stopped"] = E.stop_game()
        if rec.get("counter_override") == "set":       # G4-P2: only the file this run wrote
            try:
                E.TEKKEN["override"].unlink()
            except FileNotFoundError:
                pass
            td["counter_override_removed"] = not E.TEKKEN["override"].exists()
        td["game_active"] = E.games_status().get("active")
        if samp:
            (rd / "sampler.stop").touch()
            try:
                samp.wait(timeout=30)
            except subprocess.TimeoutExpired:
                samp.kill()
        rec["teardown"] = td
        rec["ended_utc"] = E.utc()
    if rec.get("window"):
        t0, t1 = rec["window"]["from"], rec["window"]["to"]
        rec["host"] = E.S.summarize(str(rd), t0, t1)
        rec["key"] = {
            "heartbeat": E.heartbeat_figures(t0, t1),
            "telemetry": E.telemetry_figures(rd / "telemetry.jsonl", t0, t1),
            "status_poll": E.poll_figures(rd / "status_poll.jsonl", t0, t1),
            "path": path_figures(rd / "path.jsonl", t0, t1),
            "retroarch": rec["host"].get("retroarch"),            # G4-P2: the home row's key
            "gate3": gate3_figures(rd, rec["host"], t0, t1),      # G4-P2: as the gates' clauses read it
        }
        rec["status"] = "OK" if rec["status"] == "WINDOW_DONE" else rec["status"]
    (rd / "summary.json").write_text(json.dumps(rec, indent=1))
    return rec


def main_remote(argv: list[str], E: Any) -> int:
    try:
        a = parse_args(argv)
    except ValueError as exc:
        print(f"refusing: {exc}")
        return 2
    pre = a["prereg"]
    if not pre or not pre.exists():
        print("refusing: --prereg <file> is required (the suite runs only pre-registered)")
        return 2
    shaf = pre.with_suffix(".sha256")
    want = shaf.read_text().split()[0] if shaf.exists() else None
    if hashlib.sha256(pre.read_bytes()).hexdigest() != want:
        print("refusing: the pre-registration does not match its hash")
        return 2
    mp = E.mainpid()
    pf = preflight_remote(lambda kv: E.environ_has(mp, kv), lambda: E.adb("devices"), getattr(E, "ADOPTED", ()))
    if not pf["ok"]:
        print(pf["refusal"])
        return 2
    a["out"].mkdir(parents=True, exist_ok=True)
    E.log.path = a["out"] / "suite.log"
    results = []
    for n in range(1, a["runs"] + 1):
        results.append(run_remote_once(E, n, a["out"], a["window"], a["gap"], a["wait"], a["adb"]))
    print(json.dumps([{"run": r["run"], "status": r["status"], "endpoint": r.get("endpoint")} for r in results],
                     indent=1))
    return 0
