#!/usr/bin/env python3
"""C3-L4-L2(B): the `nft` fault-injection night for the live controller -- started by the USER.

    python3 tools/c3_l4_nft_night.py              # the night (~75-90 min)
    python3 tools/c3_l4_nft_night.py --only F1,F3 # night 2: just F1 and F3 (~45 min)
    python3 tools/c3_l4_nft_night.py --dry-run    # the whole flow, no fault, no sudo (~20 min)

One window: start it in tmux on the host, type your sudo password once when
asked, press Enter to accept the pre-registration, then wait. Nothing is
pasted and nothing else is typed.

**The harness runs the fault commands itself**, as `sudo -n nft ...` with
argument lists (no shell), built only from a fixed allow-list (`NFT_ALLOW`:
the table `inet privyhub_fault`, its output-hook chain, the counter rule, the
cap rule, the 2 % loss rule, the 15 s drop of the video and audio ports,
`list table`, `list tables`, `flush chain`, `delete table`). Anything else is
refused before it reaches sudo. `sudo -v` runs once at the start in the
foreground (the password prompt); a background `sudo -n -v` every 4 minutes
keeps it alive. If sudo stops accepting `-n`, the harness removes the fault
(if it can) and asks for the password again before it continues. Every
command, its exit code and its output go to `<run dir>/nft_commands.jsonl`;
every listing to `<run dir>/nft_tables.txt`. Each step is verified from the
listing (table present with the expected rule, or absent) before the night
moves on; a mismatch removes the fault and stops the night cleanly.

**To stop at any point: press Ctrl-C -- the fault is removed automatically.**
Ctrl-C, a dropped SSH connection (SIGHUP), SIGTERM, an error and the normal
end all go the same way: `sudo -n nft delete table inet privyhub_fault`, then
`nft list tables` to confirm it is gone, then the teardown (flag unset,
companion restarted through its unit, game ended, samplers stopped).

What it does (the L1 record's section 7, with the blend's expectations, and
the pre-registration `c3_l4_l2_nft_preregistration.txt`, printed at start):

  preflight -> PRIVYHUB_ADAPTIVE_BITRATE_MODE=live (never INJECT) -> recorders
  F1  capacity cap between the 5500 and 6000 wire rates (calibrated first
      with a counter rule), 12 min on, then removed, 5 min
  F2  2 % random loss on the video port, 10 min on, then removed, 5 min
  F3  the cap until the stream is at 5000, then a 15 s full drop of video
      and audio (the R3b shape), then removed; recovery must own it
  K   the cap again; the disable route called twice by the harness; the
      controller must turn to shadow and the stream stay where it is
  teardown -> the fault table confirmed absent; the flag unset and confirmed
      absent; everything collected

C3-L4-N1: `--only F1,F3` (any subset of F1, F2, F3, K, run in that order)
runs just those parts; the preflight, the setup, the teardown and every
always-clear path are the same whatever the subset. The default
pre-registration is night 2's (`c3_l4_n1_2026-09-29/
c3_l4_nft_night2_preregistration.txt`); night 1's is still selectable with
`--prereg`. The live controller now also carries the capacity trigger and the
recovery-escalation backstop (the user's decision of 2026-09-29).

Everything is written to `logs/streaming/c3_l4_nft_night_<stamp>/` (or
`--out`); the directory is printed at the end. Scoring is a later Code task.
Privacy: the onn's adb endpoint is held in memory only; the journal copy is
redacted; no addresses are written.

Test-only options: `--sudo-cmd <path>` points the harness at a fake sudo
(`tools/c3_l4_fake_sudo.py`) that logs its argv and answers `nft` with canned
listings; `--fast` shortens the holds to 60 s and runs the real command path.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
UNIT = "privyhub-companion"
API = "http://localhost:8765"
TITLE = "game_ps1_b0a5986638f61a11"          # the attract-mode title every C3 session used
PKG = "com.safeiot.privyhub"
ADOPTED_APK_SHA256 = "f31b1c180c5d0849230860d2f5b7ab1b4a8637f7be56a7dcf1f71aba77668ae7"
REFERENCE_PROFILE = "native_game_720p60_reference"
MODE_ENV = "PRIVYHUB_ADAPTIVE_BITRATE_MODE"
VIDEO_PORT, AUDIO_PORT = 48100, 48101
TABLE = "inet privyhub_fault"
DELETE = "sudo nft delete table inet privyhub_fault"   # what the user types if the harness is gone
STOP_LINE = "To stop: press Ctrl-C -- the fault is removed automatically."
KEEPALIVE_S = 240
EVID = REPO / "docs" / "memory" / "evidence" / "c3_l4_l2_2026-09-29"
PREREG_NIGHT1 = EVID / "c3_l4_l2_nft_preregistration.txt"
PREREG = REPO / "docs" / "memory" / "evidence" / "c3_l4_n1_2026-09-29" / "c3_l4_nft_night2_preregistration.txt"
SESSIONS = ("F1", "F2", "F3", "K")          # the parts, in the order they always run
T2 = EVID / "t2_sample.py"
GAMES_LOGS = REPO / "logs" / "games"
SESSDIR = GAMES_LOGS / "decoder_sessions"

# Wire rate per rung relative to 7000 (L1 rung_load.txt: 7000 ~1,083 kB/s,
# 5000 ~775 measured; 5500 ~850 and 6000 ~930 interpolated). The cap is the
# midpoint of 5500 and 6000, scaled from the counter's 7000 reading.
CAP_FRACTION_OF_7000 = ((850 + 930) / 2) / 1083
ESTIMATE_7000_BYTES_PER_S = 1_083_000

REAL = {"baseline_s": 120, "f1_on_s": 720, "f1_off_s": 300, "f2_on_s": 600, "f2_off_s": 300,
        "f3_reach_s": 240, "f3_drop_s": 15, "f3_after_s": 180, "k_first_s": 120, "k_on_s": 120,
        "k_off_s": 60, "calib_gap_s": 60}
DRY = {"baseline_s": 60, "f1_on_s": 30, "f1_off_s": 60, "f2_on_s": 30, "f2_off_s": 60,
       "f3_reach_s": 30, "f3_drop_s": 15, "f3_after_s": 60, "k_first_s": 30, "k_on_s": 30,
       "k_off_s": 60, "calib_gap_s": 5}
# --fast (tests with the fake sudo): the real command path, holds shortened to 60 s.
FAST = {"baseline_s": 60, "f1_on_s": 60, "f1_off_s": 60, "f2_on_s": 60, "f2_off_s": 60,
        "f3_reach_s": 60, "f3_drop_s": 15, "f3_after_s": 60, "k_first_s": 60, "k_on_s": 60,
        "k_off_s": 60, "calib_gap_s": 10}

PRIVATE_IP = re.compile(r"\b(10\.\d{1,3}|192\.168|172\.(1[6-9]|2\d|3[01])|169\.254)\.\d{1,3}\.\d{1,3}\b")
MAC = re.compile(r"\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")

# -- the nft allow-list ----------------------------------------------------------------
# The only nft commands the harness may run (argv after `sudo -n`), built only from
# the L1 record's section 7 steps. "<CAP>" is the one variable: an integer rate in
# kbytes/second inside CAP_RANGE. Anything else is refused before it reaches sudo.
CAP_RANGE = (200, 2000)
_T = ["inet", "privyhub_fault"]
_R = ["add", "rule", *_T, "flt", "udp", "dport"]
NFT_ALLOW: dict[str, list[str]] = {
    "add_table": ["nft", "add", "table", *_T],
    "add_chain": ["nft", "add", "chain", *_T, "flt", "{ type filter hook output priority 0; }"],
    "counter_rule": ["nft", *_R, str(VIDEO_PORT), "counter"],
    "cap_rule": ["nft", *_R, str(VIDEO_PORT), "limit", "rate", "over", "<CAP>", "kbytes/second",
                 "burst", "64", "kbytes", "counter", "drop"],
    "loss_rule": ["nft", *_R, str(VIDEO_PORT), "numgen", "random", "mod", "1000", "<", "20", "counter", "drop"],
    "drop_rule": ["nft", *_R, f"{{ {VIDEO_PORT}, {AUDIO_PORT} }}", "counter", "drop"],
    "list_table": ["nft", "list", "table", *_T],
    "list_tables": ["nft", "list", "tables"],
    "flush_chain": ["nft", "flush", "chain", *_T, "flt"],
    "delete_table": ["nft", "delete", "table", *_T],
}


class NftRefused(Exception):
    pass


def parse_only(text: str) -> list[str]:
    """`--only F1,F3` -> ['F1', 'F3']: a non-empty subset of F1, F2, F3, K, in
    the fixed order; an unknown or repeated name is refused before anything runs."""
    names = [x.strip().upper() for x in (text or "").split(",") if x.strip()]
    bad = [x for x in names if x not in SESSIONS]
    if not names or bad or len(set(names)) != len(names):
        raise ValueError(f"--only takes a subset of {','.join(SESSIONS)} (got {text!r})")
    return [x for x in SESSIONS if x in names]


def _cap_ok(tok: str) -> bool:
    return bool(re.fullmatch(r"[0-9]{1,5}", tok)) and CAP_RANGE[0] <= int(tok) <= CAP_RANGE[1]


def nft_check(argv: list[str]) -> str:
    """The allow-list name `argv` matches exactly, or NftRefused."""
    for name, tpl in NFT_ALLOW.items():
        if len(argv) == len(tpl) and all(_cap_ok(a) if t == "<CAP>" else a == t for a, t in zip(argv, tpl)):
            return name
    raise NftRefused(f"not on the nft allow-list: {argv!r}")


def nft_argv(name: str, cap: int | None = None) -> list[str]:
    """Build an allow-listed nft command (argv, no shell)."""
    if name not in NFT_ALLOW:
        raise NftRefused(f"no such allow-listed nft command: {name!r}")
    tpl = NFT_ALLOW[name]
    if "<CAP>" in tpl:
        if not isinstance(cap, int) or isinstance(cap, bool) or not _cap_ok(str(cap)):
            raise NftRefused(f"cap {cap!r} is not an integer in {CAP_RANGE} kbytes/second")
    elif cap is not None:
        raise NftRefused(f"{name} takes no cap")
    argv = [str(cap) if t == "<CAP>" else t for t in tpl]
    nft_check(argv)
    return argv


def rule_pattern(name: str, cap: int | None = None) -> re.Pattern:
    """How `nft list table` prints each allow-listed rule (counters included)."""
    cnt = r"counter packets \d+ bytes \d+"
    if name == "counter_rule":
        return re.compile(rf"^udp dport {VIDEO_PORT} {cnt}$")
    if name == "cap_rule":
        rate = rf"{cap} kbytes/second" + (rf"|{cap // 1024} mbytes/second" if cap and cap % 1024 == 0 else "")
        return re.compile(rf"^udp dport {VIDEO_PORT} limit rate over (?:{rate}) burst 64 kbytes {cnt} drop$")
    if name == "loss_rule":
        return re.compile(rf"^udp dport {VIDEO_PORT} numgen random mod 1000 < 20 {cnt} drop$")
    if name == "drop_rule":
        return re.compile(rf"^udp dport \{{ {VIDEO_PORT}, {AUDIO_PORT} \}} {cnt} drop$")
    raise NftRefused(f"{name} is not a rule")


def table_rules(listing: str) -> list[str] | None:
    """The rule lines of chain flt in a `list table inet privyhub_fault` listing; None if no such table."""
    if not re.search(r"^table inet privyhub_fault \{", listing, re.M):
        return None
    m = re.search(r"chain flt \{(.*?)\n\s*\}", listing, re.S)
    if not m:
        return []
    return [" ".join(l.split()) for l in m.group(1).splitlines()
            if l.strip() and not l.strip().startswith("type ")]


def sudo_refused(out: str) -> bool:
    """`sudo -n` refusing (no cached credential), as opposed to nft failing."""
    o = out.lower()
    return "a password is required" in o or "a terminal is required" in o or o.startswith("sudo:")


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sh(cmd: list[str] | str, timeout: float = 30) -> str:
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)   # adb shell would otherwise read the keyboard
        return (r.stdout or "") + (r.stderr or "")
    except Exception as exc:  # the harness must survive a slow adb
        return f"<error {type(exc).__name__}>"


def api(path: str, method: str = "GET", timeout: float = 15) -> tuple[int, dict]:
    req = urllib.request.Request(API + path, method=method, data=b"" if method == "POST" else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}
    except Exception as exc:
        return 0, {"error": type(exc).__name__}


class Refused(Exception):
    pass


class StepMismatch(Refused):
    pass


class Signalled(BaseException):
    """SIGHUP / SIGTERM, raised in the main thread (like KeyboardInterrupt for Ctrl-C)."""


class Night:
    def __init__(self, args: argparse.Namespace) -> None:
        self.dry = args.dry_run
        self.t = DRY if self.dry else FAST if args.fast else REAL
        self.fast = args.fast
        self.sudo = args.sudo_cmd
        self.keepalive_s = args.keepalive_s
        self.fail_at = args.test_fail_at
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        default = REPO / "logs" / "streaming" / f"c3_l4_nft_night_{'dryrun_' if self.dry else ''}{stamp}"
        self.out = Path(args.out) if args.out else default
        self.out.mkdir(parents=True, exist_ok=True)
        self.prereg = Path(args.prereg)
        self.sessions = parse_only(args.only)
        self.nft_file = self.out / "nft_tables.txt"
        self.flag_set = False
        self.fault_may_be_on = False
        self.poller_stop = threading.Event()
        self.series: list[dict] = []
        self.sampler: subprocess.Popen | None = None
        self.poller: threading.Thread | None = None
        self.started_utc = utc()
        self.cap_kbytes: int | None = None
        self.onn: str | None = None
        self.summary: dict = {"dry_run": self.dry, "fast": self.fast, "sudo_cmd": self.sudo,
                              "started_utc": self.started_utc, "sessions": {}}
        self.current = "setup"
        self.sudo_ok = False                   # sudo -v succeeded; the final clear runs from here on
        self.sudo_lost = threading.Event()     # set by the keepalive when `sudo -n -v` is refused
        self.keepalive_stop = threading.Event()
        self.keepalive: threading.Thread | None = None
        self.cmd_lock = threading.Lock()
        self.recipe: list[tuple[str, int | None]] = []   # the commands that rebuild the table as it is now
        self.hung_up = False

    # -- output ----------------------------------------------------------------
    def log(self, msg: str) -> None:
        line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%SZ')}] {msg}"
        try:
            print(line, flush=True)
        except OSError:   # the terminal is gone (SSH dropped outside tmux); the log file still gets it
            pass
        with open(self.out / "harness.log", "a") as fh:
            fh.write(line + "\n")

    def event(self, name: str, **kw) -> None:
        with open(self.out / "events.jsonl", "a") as fh:
            fh.write(json.dumps({"at_utc": utc(), "session": self.current, "event": name, **kw}) + "\n")

    def banner(self, title: str) -> None:
        self.log("=" * 72)
        self.log(title)
        self.log(f"  {STOP_LINE}")
        self.log("=" * 72)

    def enter(self, prompt: str) -> float:
        """Wait for Enter (auto in the dry run); returns the epoch it was pressed."""
        if self.dry:
            self.log(f"  [{prompt}] -- dry run: auto-advance")
            time.sleep(1)
        else:
            try:
                input(f"  >>> {prompt} -- press Enter to accept (Ctrl-C to stop): ")
            except EOFError:
                print()
                raise KeyboardInterrupt
        t = time.time()
        self.event("enter", prompt=prompt)
        return t

    def test_point(self, name: str) -> None:
        """--test-fail-at: raise an exception at a named point (tests of the abort path only)."""
        if self.fail_at == name:
            raise RuntimeError(f"test exception at {name}")

    def tick(self) -> None:
        """Called once a second while waiting: honours a refused keepalive."""
        if self.sudo_lost.is_set():
            self.reauth("the keepalive `sudo -n -v` was refused")

    def expect(self, text: str) -> None:
        self.log(f"  EXPECT: {text}")
        self.event("expect", text=text)

    # -- companion / adb helpers --------------------------------------------------
    def status(self) -> dict:
        return api("/plugins/games/native-stream-status")[1]

    def abr(self) -> dict:
        return self.status().get("adaptive_bitrate") or {}

    def main_pid(self) -> str:
        return sh(["systemctl", "--user", "show", "-p", "MainPID", "--value", UNIT]).strip()

    def serving_pid(self) -> str:
        m = re.search(r"pid=(\d+)", sh("ss -lntp 2>/dev/null | grep ':8765 '"))
        return m.group(1) if m else ""

    def env_counts(self) -> tuple[int, int, list[str]]:
        mgr = [l for l in sh(["systemctl", "--user", "show-environment"]).splitlines() if l.startswith("PRIVYHUB_")]
        pid = self.main_pid()
        try:
            env = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
            envp = [e.decode(errors="replace") for e in env if e.startswith(b"PRIVYHUB_")]
        except Exception:
            envp = ["<unreadable>"]
        return len(mgr), len(envp), sorted(set(mgr) | set(envp))

    def restart_unit(self) -> None:
        sh(["systemctl", "--user", "restart", UNIT], timeout=60)
        for _ in range(30):
            if self.serving_pid():
                break
            time.sleep(1)
        time.sleep(2)

    def adb_ok(self) -> bool:
        lines = [l for l in sh(["adb", "devices"]).splitlines()[1:] if l.strip().endswith("device")]
        if lines:
            self.onn = self.onn or lines[0].split()[0]
            return True
        if self.onn:
            sh(["adb", "connect", self.onn])
            time.sleep(3)
            return any(l.strip().endswith("device") for l in sh(["adb", "devices"]).splitlines()[1:])
        return False

    def game_active(self) -> bool:
        return bool(api("/plugins/games/status")[1].get("active"))

    def recovery_state(self) -> str:
        return (api("/plugins/games/status")[1].get("recovery") or {}).get("state", "")

    # -- recorders ---------------------------------------------------------------
    def _poll(self) -> None:
        with open(self.out / "abr_series.jsonl", "a") as fh:
            while not self.poller_stop.is_set():
                d = self.status()
                a = d.get("adaptive_bitrate") or {}
                p = a.get("policy") or {}
                row = {"at_utc": utc(), "session": self.current, "bitrate_kbps": d.get("bitrate_kbps"),
                       "active": d.get("active"), "mode": a.get("mode"), "state": a.get("state"),
                       "level": a.get("level"), "transitions_this_session": a.get("transitions_this_session"),
                       "rate_limited": a.get("rate_limited"), "last_action": a.get("last_action"),
                       "reason": p.get("reason"), "blackout": p.get("blackout_remaining_reports"),
                       "holds": p.get("hold_down_remaining_reports"), "window": p.get("increase_window"),
                       "oscillation_hold": p.get("oscillation_hold"), "refused": p.get("refused"),
                       "recovery": (d.get("recovery") or {}).get("state")}
                self.series.append(row)
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                self.poller_stop.wait(5)

    def start_recorders(self) -> None:
        samp = self.out / "t2_samples.jsonl"
        Path(str(samp) + ".stop").unlink(missing_ok=True)
        self.sampler = subprocess.Popen([sys.executable, str(T2), str(samp), "10"],
                                        stdout=open(self.out / "t2_sampler.log", "a"), stderr=subprocess.STDOUT,
                                        stdin=subprocess.DEVNULL)
        self.poller = threading.Thread(target=self._poll, daemon=True)
        self.poller.start()
        self.log(f"recorders: T2 sampler (10 s) pid {self.sampler.pid}; status poller (5 s)")

    def stop_recorders(self) -> None:
        Path(str(self.out / "t2_samples.jsonl") + ".stop").touch()
        self.poller_stop.set()
        if self.poller:
            self.poller.join(timeout=10)
        if self.sampler:
            try:
                self.sampler.wait(timeout=20)
            except Exception:
                self.sampler.kill()

    # -- the decision log since a time ---------------------------------------------
    def log_rows(self, name: str, key: str, since: str, until: str | None = None) -> list[dict]:
        files = sorted(glob.glob(str(GAMES_LOGS / "stream_log_archive" / (name + "*"))), reverse=True)
        files.append(str(GAMES_LOGS / name))
        rows, seen = [], set()
        for f in files:
            if not os.path.exists(f):
                continue
            for line in open(f, errors="replace"):
                line = line.strip()
                if not line or line in seen:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                ts = str(r.get(key, ""))
                if ts >= since and (until is None or ts <= until):
                    seen.add(line)
                    rows.append(r)
        rows.sort(key=lambda r: str(r.get(key, "")))
        return rows

    def did(self, since: str, label: str) -> dict:
        rows = self.log_rows("adaptive_bitrate_shadow.jsonl", "at_utc", since)
        tr = [r for r in rows if r.get("event") in ("transition", "would_act")]
        ref: dict[str, int] = {}
        for r in rows:
            if r.get("event") == "refused":
                ref[r.get("reason")] = ref.get(r.get("reason"), 0) + 1
        holds = [r for r in rows if r.get("event") == "hold"]
        armed = [r for r in rows if r.get("event") == "escalation_armed"]
        by_trigger: dict[str, int] = {}
        for r in rows:
            if r.get("event") in ("transition", "would_act", "refused") and r.get("trigger"):
                k = f"{r.get('event')}:{r.get('trigger')}"
                by_trigger[k] = by_trigger.get(k, 0) + 1
        after = [x for x in self.series if x["at_utc"] >= since]
        last = after[-1] if after else {}
        rl = any(x.get("rate_limited") for x in after)
        rec = [r.get("event") for r in self.log_rows("native_stream_recovery.log", "at_utc", since)]
        text = (f"DID ({label}): " + (", ".join(f"{r['at_utc'][11:19]}Z {r.get('event')} {r.get('class')} "
                                               f"{r.get('from_kbps')}->{r.get('to_kbps')} ({r.get('reason')})"
                                               for r in tr) or "no transition")
                + (f"; escalation armed x{len(armed)}" if armed else "")
                + (f"; HOLD {holds[0].get('reason')}" if holds else "")
                + (f"; refused {ref}" if ref else "")
                + f"; rate_limited ever {rl}; now level {last.get('level')} state {last.get('state')} "
                  f"mode {last.get('mode')} recovery {last.get('recovery')}"
                + (f"; recovery log {rec}" if rec else ""))
        self.log("  " + text)
        out = {"label": label, "since": since, "transitions": [
            {k: r.get(k) for k in ("at_utc", "event", "class", "from_kbps", "to_kbps", "injected", "acted",
                                   "reason", "trigger")} for r in tr],
            "holds": len(holds), "refused": ref, "decisions_by_trigger": by_trigger,
            "escalation_armed": len(armed), "rate_limited_ever": rl, "level": last.get("level"),
            "state": last.get("state"), "mode": last.get("mode"), "recovery_events": rec}
        self.event("did", **out)
        return out

    def hold(self, seconds: int, label: str) -> None:
        end = time.time() + seconds
        nxt = time.time() + 30
        while time.time() < end:
            time.sleep(min(1.0, max(0.0, end - time.time())))
            self.tick()
            if time.time() >= nxt and self.series:
                x = self.series[-1]
                w = x.get("window") or {}
                self.log(f"    {label}: {int(seconds - (end - time.time()))}/{seconds} s -- level {x.get('level')} "
                         f"state {x.get('state')} transitions {x.get('transitions_this_session')} "
                         f"window {w.get('reports')}/{w.get('clean')} recovery {x.get('recovery')}")
                nxt += 30

    # -- sudo and nft ---------------------------------------------------------------------
    def record_cmd(self, kind: str, argv: list[str], rc: int | None, out: str) -> None:
        with self.cmd_lock, open(self.out / "nft_commands.jsonl", "a") as fh:
            fh.write(json.dumps({"at_utc": utc(), "session": self.current, "kind": kind, "argv": argv,
                                 "rc": rc, "output": out}) + "\n")

    def sudo_validate(self, why: str) -> bool:
        """`sudo -v` in the foreground: the user types the password in this window."""
        argv = [self.sudo, "-v"]
        self.log(f"  sudo needs your password ({why}) -- type it below.")
        try:
            rc = subprocess.run(argv, timeout=300).returncode
        except subprocess.TimeoutExpired:
            rc = None
        self.record_cmd("sudo_validate", argv, rc, "")
        self.log(f"  sudo -v -> {'OK' if rc == 0 else f'FAILED (rc {rc})'}")
        return rc == 0

    def _keepalive(self) -> None:
        while not self.keepalive_stop.wait(self.keepalive_s):
            argv = [self.sudo, "-n", "-v"]
            try:
                r = subprocess.run(argv, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
                rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
            except Exception as exc:
                rc, out = None, f"<error {type(exc).__name__}>"
            self.record_cmd("sudo_keepalive", argv, rc, out)
            if rc != 0:
                self.event("sudo_keepalive_refused", rc=rc, output=out.strip()[:200])
                self.sudo_lost.set()

    def start_keepalive(self) -> None:
        self.keepalive = threading.Thread(target=self._keepalive, daemon=True)
        self.keepalive.start()

    def _nft_once(self, name: str, cap: int | None = None) -> tuple[int | None, str]:
        argv = nft_argv(name, cap)                  # the allow-list: NftRefused for anything else
        full = [self.sudo, "-n", *argv]
        try:
            r = subprocess.run(full, capture_output=True, text=True, timeout=30, stdin=subprocess.DEVNULL)
            rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = None, "<timeout>"
        self.record_cmd(name, full, rc, out)
        if name.startswith("list"):
            with open(self.nft_file, "a") as fh:
                fh.write(f"# {utc()} {self.current} {' '.join(argv)} -> rc {rc}\n{out}")
                if out and not out.endswith("\n"):
                    fh.write("\n")
        return rc, out

    def nft(self, name: str, cap: int | None = None, reauth: bool = True) -> tuple[int | None, str]:
        """One allow-listed nft command as `sudo -n nft ...`; a refused sudo asks for the password again."""
        rc, out = self._nft_once(name, cap)
        if rc != 0 and sudo_refused(out) and reauth:
            self.reauth(f"`sudo -n` was refused on {name}")
            rc, out = self._nft_once(name, cap)
        return rc, out

    def show(self, name: str, cap: int | None, rc: int | None) -> None:
        self.log(f"    sudo -n {' '.join(nft_argv(name, cap))}   -> rc {rc}")

    def reauth(self, why: str) -> None:
        """sudo stopped accepting -n: clear the fault if possible, ask for the password, put the fault back."""
        self.sudo_lost.clear()
        t0 = time.time()
        self.log(f"  !! PAUSED: {why}.")
        cleared = False
        if self.recipe:
            rc, _ = self._nft_once("delete_table")
            cleared = rc == 0
            self.log(f"  the fault was {'removed' if cleared else 'NOT removable without the password'}")
        self.event("sudo_reauth_start", why=why, fault_cleared=cleared)
        for attempt in (1, 2, 3):
            if not self.hung_up and self.sudo_validate(f"again, attempt {attempt} of 3"):
                break
        else:
            raise Refused("sudo was not re-validated (the password was not accepted)")
        rebuilt = False
        if self.recipe:
            if cleared or table_rules(self._nft_once("list_table")[1]) is None:
                for n, c in self.recipe:
                    self._nft_once(n, c)
                rebuilt = True
            self.verify_present("re-applied after the password", [n for n, _ in self.recipe if n.endswith("_rule")],
                                cap=next((c for _, c in self.recipe if c), None))
        gap = round(time.time() - t0, 1)
        self.log(f"  resumed after {gap} s" + (" (the fault was re-applied)" if rebuilt else
                                               " (the fault stayed on; verified)" if self.recipe else ""))
        self.event("sudo_reauth_done", gap_s=gap, reapplied=rebuilt, fault_on=bool(self.recipe))

    # -- verified steps ---------------------------------------------------------------------
    def mismatch(self, text: str) -> None:
        self.log(f"  !! MISMATCH: {text}")
        self.log("  !! the fault is removed and the night stops here (teardown follows).")
        self.event("step_mismatch", text=text)
        raise StepMismatch(text)

    def verify_present(self, what: str, rules: list[str], cap: int | None = None) -> str:
        rc, out = self.nft("list_table")
        got = table_rules(out) if rc == 0 else None
        want = [rule_pattern(r, cap) for r in rules]
        ok = got is not None and len(got) == len(want) and all(p.match(g) for p, g in zip(want, got))
        self.log(f"    VERIFY ({what}): table inet privyhub_fault {'present' if got is not None else 'ABSENT'}"
                 f", rules {got if got is not None else '-'} -> {'OK' if ok else 'NOT AS EXPECTED'}")
        self.event("verify", what=what, expect=rules, got=got, ok=ok)
        if not ok:
            self.mismatch(f"{what}: expected rules {rules}, listing shows {got}")
        return out

    def verify_absent(self, what: str) -> bool:
        rc, out = self.nft("list_tables")
        ok = rc == 0 and "privyhub_fault" not in out
        self.log(f"    VERIFY ({what}): privyhub_fault {'absent' if ok else 'STILL LISTED' if rc == 0 else f'unknown (rc {rc})'}"
                 f" -> {'OK' if ok else 'NOT AS EXPECTED'}")
        self.event("verify", what=what, expect="absent", ok=ok, rc=rc)
        return ok

    def run_steps(self, steps: list[tuple[str, int | None]], what: str) -> None:
        for name, cap in steps:
            rc, out = self.nft(name, cap)
            self.show(name, cap, rc)
            if rc != 0:
                self.mismatch(f"{what}: `{' '.join(nft_argv(name, cap))}` failed (rc {rc}): {out.strip()[:200]}")

    def apply(self, steps: list[tuple[str, int | None]], recipe: list[tuple[str, int | None]], what: str,
              rules: list[str]) -> float:
        """Run `steps`; the table must then hold exactly `rules`. `recipe` rebuilds that state from nothing."""
        self.log(f"  APPLY ({what}):")
        self.fault_may_be_on = True
        self.run_steps(steps, what)
        t = time.time()
        self.recipe = list(recipe)
        self.verify_present(what, rules, cap=self.cap_kbytes)
        self.event("fault_on", what=what, steps=[nft_argv(n, c) for n, c in steps])
        return t

    def remove(self, what: str) -> float:
        self.log(f"  REMOVE ({what}):")
        rc, out = self.nft("delete_table")
        self.show("delete_table", None, rc)
        t = time.time()
        if not self.verify_absent(what):
            rc, out = self.nft("delete_table")
            self.show("delete_table", None, rc)
            if not self.verify_absent(what + ", second delete"):
                self.mismatch(f"{what}: privyhub_fault still listed after two deletes")
        self.recipe = []
        self.fault_may_be_on = False
        self.event("fault_off", what=what)
        return t

    def clear_fault_final(self, why: str) -> None:
        """Every exit: delete the table, confirm with `list tables`. Never raises."""
        if self.dry or not self.sudo_ok:
            return
        self.log(f"  CLEAR THE FAULT ({why}): sudo -n nft delete table inet privyhub_fault, then list tables")
        ok = False
        for attempt in (1, 2):
            try:
                rc, out = self._nft_once("delete_table")
                self.log(f"    delete table -> rc {rc}" + ("" if rc == 0 else f" ({(out.strip().splitlines() or [''])[0][:120]})"))
                if rc != 0 and sudo_refused(out):
                    if attempt == 1 and not self.hung_up and sys.stdin.isatty():
                        self.sudo_validate("to remove the fault")
                        continue
                    break
                ok = self.verify_absent("at the end")
            except BaseException as exc:   # a second Ctrl-C must not skip the delete's retry or the teardown
                self.log(f"    clear interrupted ({type(exc).__name__}); retrying once")
                continue
            break
        self.summary["no_fault_table_at_end"] = ok
        self.fault_may_be_on = not ok
        self.event("fault_cleared_final", ok=ok, why=why)
        if not ok:
            self.log("  !! COULD NOT CONFIRM THE FAULT IS GONE. Type this yourself:")
            self.log(f"  !!     {DELETE}")
            self.log("  !!     sudo nft list tables")

    # -- preflight -------------------------------------------------------------------
    def preflight(self) -> None:
        self.banner("PREFLIGHT")
        if not self.dry:
            if self.sudo != "sudo":
                self.log(f"  TEST RUN: sudo is the fake at {self.sudo} (no real nft is run)")
            if not os.environ.get("TMUX"):
                self.log("  note: not inside tmux -- if the SSH connection drops, sudo may refuse the automatic "
                         "removal; start it inside `tmux new -s nft` next time")
            if not self.sudo_validate("once, at the start"):
                raise Refused("sudo -v failed; nothing was changed -- start again and type the sudo password")
            self.sudo_ok = True
            self.start_keepalive()
            self.log(f"  sudo is cached; a keepalive (`sudo -n -v`) runs every {self.keepalive_s} s")
        mp, sp = self.main_pid(), self.serving_pid()
        if not mp or mp == "0" or mp != sp:
            raise Refused(f"the companion unit's MainPID ({mp or 'none'}) does not serve 8765 ({sp or 'none'})")
        if self.game_active():
            raise Refused("a game is active; end it first (POST /plugins/games/stop)")
        m, e, names = self.env_counts()
        if m or e:
            raise Refused(f"PRIVYHUB_* set (manager {m}, companion environ {e}): {names}")
        d = self.status()
        o, c, r = d.get("encoder_overrides") or {}, d.get("audio_cushion") or {}, d.get("audio_redundancy") or {}
        adopted = (d.get("profile_id") == REFERENCE_PROFILE and o.get("any_override") is False
                   and o.get("max_frame_size_bytes") == 90000 and o.get("max_frame_size_source") == "profile"
                   and (c.get("queue_target_packets"), c.get("queue_capacity_packets"), c.get("source")) == (12, 17, "profile")
                   and (r.get("copies"), r.get("offset_packets"), r.get("source")) == (2, 4, "profile")
                   and d.get("bitrate_kbps") == 7000)
        if not adopted:
            raise Refused("the stream is not on the adopted profile at 7000 with no override")
        if (d.get("adaptive_bitrate") or {}).get("mode") != "off":
            raise Refused("adaptive_bitrate.mode is not off")
        if not self.adb_ok():
            raise Refused("no onn in `adb devices` (adb connect <onn-address>:<port> once, then retry)")
        path = sh(["adb", "shell", "pm", "path", PKG]).strip().replace("package:", "").splitlines()
        apk = sh(["adb", "shell", "sha256sum", path[0].strip()]).split()[0] if path else ""
        if apk != ADOPTED_APK_SHA256:
            raise Refused(f"installed APK is not the adopted one ({apk[:8]}...)")
        self.log(f"  companion MainPID serves 8765; no game; no PRIVYHUB_*; adopted profile at 7000; "
                 f"any_override false; APK {apk[:8]}...{apk[-4:]} (adopted); onn in adb")
        if not self.prereg.exists():
            raise Refused(f"no pre-registration at {self.prereg}")
        text = self.prereg.read_text()
        h = hashlib.sha256(text.encode()).hexdigest()
        shutil.copy(self.prereg, self.out / "preregistration.txt")
        (self.out / "preregistration.sha256").write_text(f"{h}  {self.prereg.name}\n")
        self.log(f"  pre-registration {self.prereg.name} sha256 {h[:16]}... (copied into the run dir):")
        for line in text.splitlines():
            self.log("  | " + line)
        self.summary["preregistration_sha256"] = h
        if self.dry:
            self.log(f"  (dry run: no sudo; would run  sudo -n {' '.join(nft_argv('list_tables'))})")
        else:
            self.log("  No fault table may exist before the night:")
            if not self.verify_absent("before the night"):
                self.log("  a privyhub_fault table was left from before -- removing it")
                rc, _ = self.nft("delete_table")
                self.show("delete_table", None, rc)
                if not self.verify_absent("before the night, after the delete"):
                    raise Refused("a privyhub_fault table exists and could not be removed")
                self.event("leftover_table_removed")
        self.log(f"  {STOP_LINE}")
        self.enter("the pre-registration above is the one for tonight")
        self.event("preflight_ok", apk=apk[:8] + "..." + apk[-4:])

    # -- setup / teardown -------------------------------------------------------------
    def setup(self) -> None:
        self.banner("SETUP: live mode on, recorders on")
        sh(["systemctl", "--user", "set-environment", f"{MODE_ENV}=live"])
        self.flag_set = True
        self.restart_unit()
        m, e, names = self.env_counts()
        a = self.abr()
        self.log(f"  flag set: {names}; MainPID {self.main_pid()} serves 8765 "
                 f"{self.main_pid() == self.serving_pid()}; adaptive_bitrate mode {a.get('mode')} level "
                 f"{a.get('level')} transitions {a.get('transitions_this_session')}")
        if names != [f"{MODE_ENV}=live"] or a.get("mode") != "live" or a.get("level") != 7000:
            raise Refused("live mode did not come up as expected (mode live, level 7000, only the one flag)")
        self.event("live_on", flags=names)
        self.start_recorders()
        time.sleep(20)

    def teardown(self) -> None:
        self.current = "teardown"
        self.banner("TEARDOWN")   # the fault was already removed and confirmed absent by finish()
        self.stop_recorders()
        api("/plugins/games/stop", "POST", timeout=30)
        for _ in range(20):
            if not self.game_active():
                break
            time.sleep(1)
        sh(["systemctl", "--user", "unset-environment", MODE_ENV, "PRIVYHUB_ADAPTIVE_BITRATE_INJECT"])
        self.restart_unit()
        m, e, names = self.env_counts()
        d = self.status()
        a = d.get("adaptive_bitrate") or {}
        ok = (m == 0 and e == 0 and a.get("mode") == "off" and d.get("bitrate_kbps") == 7000
              and not self.game_active() and self.main_pid() == self.serving_pid())
        self.log(f"  flag unset: PRIVYHUB_* manager {m}, companion environ {e}; MainPID serves 8765 "
                 f"{self.main_pid() == self.serving_pid()}; adaptive_bitrate mode {a.get('mode')}; stream "
                 f"{d.get('bitrate_kbps')}; game active {self.game_active()} -> {'CLEAN' if ok else 'CHECK BY HAND'}")
        if self.onn is not None or self.adb_ok():
            sh(["adb", "shell", "input", "keyevent", "KEYCODE_HOME"])
            sh(["adb", "shell", "am", "start", "-n", f"{PKG}/.MainActivity"])
            time.sleep(6)
            sh(["adb", "shell", "uiautomator", "dump", "/sdcard/l4night.xml"])
            banner = sh(["adb", "shell", "cat", "/sdcard/l4night.xml"]).count("NOW PLAYING")
            sh(["adb", "shell", "rm", "-f", "/sdcard/l4night.xml"])
            self.log(f"  launcher NOW PLAYING banners: {banner}")
            self.summary["banner_count_at_end"] = banner
        self.summary.update({"teardown_clean": ok, "flags_after": names, "ended_utc": utc()})
        self.event("teardown", clean=ok)

    def collect(self) -> None:
        since, until = self.started_utc, utc()
        for name, key, out in (("adaptive_bitrate_shadow.jsonl", "at_utc", "decision_log.jsonl"),
                               ("native_stream_heartbeat.log", "received_at_utc", "heartbeat.jsonl"),
                               ("native_frame_sizes.jsonl", "at_utc", "frames.jsonl"),
                               ("native_stream_recovery.log", "at_utc", "recovery_log.jsonl")):
            rows = self.log_rows(name, key, since, until)
            with open(self.out / out, "w") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
        j = sh(["journalctl", "--user", "-u", UNIT, "--since", since[:19].replace("T", " "), "--no-pager",
                "-o", "short-iso"], timeout=60)
        j = MAC.sub("<MAC_REDACTED>", PRIVATE_IP.sub("<IP_REDACTED>", j))
        (self.out / "companion_journal_redacted.log").write_text(j)
        want = ["harness.log", "events.jsonl", "abr_series.jsonl", "t2_samples.jsonl", "decision_log.jsonl",
                "heartbeat.jsonl", "frames.jsonl", "recovery_log.jsonl", "companion_journal_redacted.log",
                "preregistration.txt", "preregistration.sha256"]
        for s in self.sessions:
            want += [f"armcheck_{s}.json", f"status_end_{s}.json", f"report_{s}.json"]
        present = {w: (self.out / w).exists() and (self.out / w).stat().st_size > 0 for w in want}
        rows = {w: sum(1 for _ in open(self.out / w)) for w in want
                if w.endswith(".jsonl") and (self.out / w).exists()}
        dl = [json.loads(l) for l in open(self.out / "decision_log.jsonl")] if present["decision_log.jsonl"] else []
        self.summary["files"] = present
        self.summary["rows"] = rows
        self.summary["decision_log_sample_rows"] = sum(1 for r in dl if r.get("event") == "sample")
        self.summary["complete"] = all(present.values())
        (self.out / "summary.json").write_text(json.dumps(self.summary, indent=1, default=str))
        self.log(f"  files: {sum(present.values())}/{len(present)} present"
                 + ("" if all(present.values()) else f" -- MISSING {[k for k, v in present.items() if not v]}"))
        self.log(f"  rows: {rows}; sample rows in the decision log {self.summary['decision_log_sample_rows']}")

    # -- one session ---------------------------------------------------------------------
    def launch(self, name: str) -> None:
        self.current = name
        if self.game_active():
            api("/plugins/games/stop", "POST", timeout=30)
            for _ in range(20):
                if not self.game_active():
                    break
                time.sleep(1)
        if not self.adb_ok():
            raise Refused("the onn left adb")
        self.reports_before = set(os.listdir(SESSDIR)) if SESSDIR.exists() else set()
        api(f"/plugins/games/launch?id={TITLE}", "POST", timeout=60)
        opened = False
        for _ in range(2):
            sh(["adb", "shell", "am", "force-stop", PKG])
            sh(["adb", "shell", "input", "keyevent", "KEYCODE_WAKEUP"])
            sh(["adb", "shell", "am", "start", "-n", f"{PKG}/.MainActivity"])
            time.sleep(7)
            sh(["adb", "shell", "uiautomator", "dump", "/sdcard/l4night.xml"])
            if "now_playing_preview_host" in sh(["adb", "shell", "cat", "/sdcard/l4night.xml"]):
                sh(["adb", "shell", "input", "tap", "1008", "298"])
                time.sleep(3)
                top = [l for l in sh("adb shell dumpsys activity activities").splitlines() if "topResumedActivity" in l]
                if top and "NativeStreamActivity" in top[0]:
                    opened = True
                    break
        sh(["adb", "shell", "rm", "-f", "/sdcard/l4night.xml"])
        if not opened:
            raise Refused(f"{name}: the stream did not open on the onn")
        for _ in range(45):
            if self.recovery_state() == "PLAYING":
                break
            time.sleep(1)
        d = self.status()
        (self.out / f"armcheck_{name}.json").write_text(json.dumps(d, indent=1))
        anyo = (d.get("encoder_overrides") or {}).get("any_override")
        self.log(f"  {name}: PLAYING ({self.recovery_state()}); any_override {anyo}; "
                 f"adaptive_bitrate {(d.get('adaptive_bitrate') or {}).get('mode')} level "
                 f"{(d.get('adaptive_bitrate') or {}).get('level')}")
        self.summary["sessions"].setdefault(name, {})["any_override_at_playing"] = anyo
        self.event("playing", any_override=anyo)

    def back(self, name: str) -> None:
        (self.out / f"status_end_{name}.json").write_text(json.dumps(self.status(), indent=1))
        sh(["adb", "shell", "input", "keyevent", "KEYCODE_BACK"])
        new = None
        for _ in range(30):
            time.sleep(1)
            now = set(os.listdir(SESSDIR)) if SESSDIR.exists() else set()
            fresh = sorted(now - self.reports_before)
            if fresh:
                new = fresh[-1]
                break
        if new:
            shutil.copy(SESSDIR / new, self.out / f"report_{name}.json")
        time.sleep(2)
        a = self.abr()
        self.log(f"  {name}: BACK; decoder report {'stored' if new else 'MISSING'}; controller after BACK: "
                 f"mode {a.get('mode')} level {a.get('level')} transitions {a.get('transitions_this_session')}")
        self.event("back", report=bool(new), level_after=a.get("level"), mode_after=a.get("mode"))
        api("/plugins/games/stop", "POST", timeout=30)
        for _ in range(20):
            if not self.game_active():
                break
            time.sleep(1)
        time.sleep(20)

    # -- the calibration ----------------------------------------------------------------
    TABLE_STEPS = [("add_table", None), ("add_chain", None)]

    def calibrate(self) -> None:
        self.log("  CALIBRATE the cap: a counter-only rule on the video port (no drop).")
        readings: list[tuple[float, int | None]] = []
        if self.dry:
            self.log("  (dry run: no sudo; would run " + "; ".join(
                " ".join(nft_argv(n)) for n in ("add_table", "add_chain", "counter_rule")) + ")")
        else:
            steps = self.TABLE_STEPS + [("counter_rule", None)]
            self.apply(steps, steps, "calibration counter", ["counter_rule"])
            for i in (1, 2):
                if i == 2:
                    self.log(f"  waiting {self.t['calib_gap_s']} s between the two readings ...")
                    end = time.time() + self.t["calib_gap_s"]
                    while time.time() < end:
                        time.sleep(min(1.0, max(0.0, end - time.time())))
                        self.tick()
                rc, out = self.nft("list_table")
                t = time.time()
                m = re.findall(r"udp dport %d counter packets (\d+) bytes (\d+)" % VIDEO_PORT, out)
                readings.append((t, int(m[-1][1]) if (rc == 0 and m) else None))
                self.log(f"    counter reading {i}: {readings[-1][1]} bytes")
        (t1, b1), (t2, b2) = readings if readings else ((0.0, None), (0.0, None))
        rate = (b2 - b1) / (t2 - t1) if (b1 is not None and b2 is not None and t2 > t1) else None
        if rate is None or not (500_000 <= rate <= 1_800_000):
            self.log(f"  counter rate {rate!r} B/s not usable -> the L1 estimate {ESTIMATE_7000_BYTES_PER_S} B/s"
                     + (" (dry run)" if self.dry else " -- recorded"))
            rate_used, source = ESTIMATE_7000_BYTES_PER_S, "estimate"
        else:
            rate_used, source = rate, "counter"
        self.cap_kbytes = int(round(rate_used * CAP_FRACTION_OF_7000 / 1024))
        self.log(f"  7000 wire rate {rate_used / 1000:.0f} kB/s ({source}); CAP = {CAP_FRACTION_OF_7000:.3f} x that "
                 f"= {self.cap_kbytes} kbytes/second (nft kbytes = 1024 B)")
        self.summary["calibration"] = {"rate_7000_bytes_per_s": rate, "used": rate_used, "source": source,
                                       "cap_kbytes_per_s": self.cap_kbytes}
        self.event("calibrated", **self.summary["calibration"])

    # -- the four sessions -----------------------------------------------------------------
    def fault_or_wait(self, steps: list[tuple[str, int | None]], recipe: list[tuple[str, int | None]],
                      what: str, rules: list[str]) -> float:
        if self.dry:
            self.log(f"  (dry run: the fault '{what}' is replaced by a wait; not run: "
                     + "; ".join(" ".join(nft_argv(n, c)) for n, c in steps) + ")")
            self.event("fault_on", what=what, dry=True)
            return time.time()
        return self.apply(steps, recipe, what, rules)

    def clear_or_wait(self, what: str) -> float:
        if self.dry:
            self.log(f"  (dry run: not run: {' '.join(nft_argv('delete_table'))})")
            self.event("fault_off", what=what, dry=True)
            return time.time()
        return self.remove(what)

    def cap_steps(self) -> list[tuple[str, int | None]]:
        return self.TABLE_STEPS + [("cap_rule", self.cap_kbytes)]

    def session_f1(self) -> None:
        self.banner("F1 -- capacity cap (the controller's main case)")
        self.launch("F1")
        self.log(f"  baseline {self.t['baseline_s']} s at 7000 ...")
        self.hold(self.t["baseline_s"], "F1 baseline")
        self.calibrate()
        # after the calibration the table exists: flush it and add the cap (the dry run builds it whole)
        steps = [("flush_chain", None), ("cap_rule", self.cap_kbytes)] if not self.dry else self.cap_steps()
        self.expect("within ~60 s (night 1's samples: ~14 s) ONE decrease: FALLBACK (capacity) 7000->5000; "
                    "~186 s later INCREASE 5000->5500 (fits the cap); ~186 s later INCREASE 5500->6000 (over the "
                    "cap); a capacity FALLBACK back to 5000 no sooner than 120 s after that; then, instead of a "
                    "third direction change inside 10 min, HOLD (oscillation) at 5000. Or, if the cap lets 6000 "
                    "through, 'climbed to 6000 and stayed'. rate_limited never true; never two transitions closer "
                    "than the hold-downs; no ramp; at most one recovery cycle under the cap.")
        since = utc()
        self.fault_or_wait(steps, self.cap_steps(), "F1 cap", ["cap_rule"])
        self.test_point("F1_cap_on")
        self.hold(self.t["f1_on_s"], "F1 cap on")
        self.summary["sessions"]["F1"]["cap_on"] = self.did(since, "F1 cap on")
        self.expect("after the cap is removed: at 5000 for the rest of the session if HOLD was reached; "
                    "otherwise one rung per ~186 s back towards 7000.")
        since = utc()
        self.clear_or_wait("F1 cap")
        self.hold(self.t["f1_off_s"], "F1 cap off")
        self.summary["sessions"]["F1"]["cap_off"] = self.did(since, "F1 cap off")
        self.expect("BACK -> session_ended_reset: the controller back at 7000, transitions 0.")
        self.back("F1")

    def session_f2(self) -> None:
        self.banner("F2 -- 2 % random loss (the controller must not chase it)")
        self.launch("F2")
        self.hold(self.t["baseline_s"], "F2 baseline")
        steps = self.TABLE_STEPS + [("loss_rule", None)]
        self.expect("FEC recovers part of it; loss alone is never evidence. Either no transition, or AT MOST ONE "
                    "decrease (ROUTINE ->6000 or FALLBACK ->5000) and then only at_or_below_target / at_floor / "
                    "hold_down refusals. No second decrease, never a ramp.")
        since = utc()
        self.fault_or_wait(steps, steps, "F2 2% loss", ["loss_rule"])
        self.test_point("F2_loss_on")
        self.hold(self.t["f2_on_s"], "F2 loss on")
        self.summary["sessions"]["F2"]["loss_on"] = self.did(since, "F2 loss on")
        self.expect("after removal: a stream that stepped down climbs one rung per ~186 s; otherwise nothing.")
        since = utc()
        self.clear_or_wait("F2 2% loss")
        self.hold(self.t["f2_off_s"], "F2 loss off")
        self.summary["sessions"]["F2"]["loss_off"] = self.did(since, "F2 loss off")
        self.back("F2")

    def session_f3(self) -> None:
        self.banner("F3 -- a link drop while off the reference (recovery and the controller)")
        self.launch("F3")
        self.hold(self.t["baseline_s"], "F3 baseline")
        self.expect("the cap brings the stream to 5000: one capacity FALLBACK 7000->5000 (night 1's samples: ~17 s).")
        since = utc()
        self.fault_or_wait(self.cap_steps(), self.cap_steps(), "F3 cap", ["cap_rule"])
        end = time.time() + self.t["f3_reach_s"]
        while time.time() < end and (self.series[-1].get("level") if self.series else None) != 5000:
            time.sleep(2)
            self.tick()
        reached = (self.series[-1].get("level") if self.series else None) == 5000
        self.log(f"  at 5000: {reached}")
        self.summary["sessions"]["F3"]["cap_to_5000"] = self.did(since, "F3 cap")
        self.expect("recovery owns the drop: desync_pause, encoder_restart AT 5000 (C3-F1, level-preserving), "
                    "resumed. The controller does NOTHING while recovery is not PLAYING (a refused/guard "
                    "recovery_playing row, or no rows because reports stop); then ssrc_change "
                    "(recovery_restart) and a 3-report blackout; the level still 5000 (no level_sync). If "
                    "recovery restarted twice within 180 s, the backstop's one decision is refused at_floor.")
        drop = [("flush_chain", None), ("drop_rule", None)]
        since = utc()
        if self.dry:
            self.fault_or_wait(drop, drop, "F3 full drop", ["drop_rule"])
            time.sleep(self.t["f3_drop_s"])
            self.clear_or_wait("F3 full drop")
        else:
            self.log(f"  the DROP: the harness applies it, counts {self.t['f3_drop_s']} s, and removes it.")
            t_on = self.apply(drop, self.TABLE_STEPS + [("drop_rule", None)], "F3 full drop", ["drop_rule"])
            end = t_on + self.t["f3_drop_s"]
            while time.time() < end:
                left = end - time.time()
                try:
                    print(f"\r    drop on: {int(left) + 1:2d} s left ", end="", flush=True)
                except OSError:
                    pass
                time.sleep(min(1.0, max(0.0, left)))
                self.test_point("F3_drop")
            try:
                print()
            except OSError:
                pass
            t_off = self.remove("F3 full drop")
            self.summary["sessions"]["F3"]["drop_s_measured"] = round(t_off - t_on, 2)
            self.log(f"  the drop was on for {t_off - t_on:.1f} s (from its apply to its delete)")
        self.log(f"  observing {self.t['f3_after_s']} s (recovery should resume) ...")
        self.hold(self.t["f3_after_s"], "F3 after the drop")
        self.summary["sessions"]["F3"]["drop"] = self.did(since, "F3 drop and recovery")
        self.back("F3")

    def session_k(self) -> None:
        self.banner("K -- the kill switch during a fault")
        self.launch("K")
        self.hold(self.t["baseline_s"], "K baseline")
        since = utc()
        self.fault_or_wait(self.cap_steps(), self.cap_steps(), "K cap", ["cap_rule"])
        end = time.time() + self.t["k_first_s"]
        while time.time() < end and not (self.series and self.series[-1].get("transitions_this_session")):
            time.sleep(2)
            self.tick()
        self.expect("disable #1 -> already_disabled false; disable #2 -> already_disabled true; status mode "
                    "shadow, configured_mode live, acts false; further decisions logged as would_act (acted "
                    "false); the stream stays where it is.")
        r1 = api("/plugins/games/adaptive-bitrate/disable", "POST")
        r2 = api("/plugins/games/adaptive-bitrate/disable", "POST")
        a = self.abr()
        self.log(f"  disable #1 HTTP {r1[0]} already_disabled {r1[1].get('already_disabled')}; #2 HTTP {r2[0]} "
                 f"already_disabled {r2[1].get('already_disabled')}; status mode {a.get('mode')} configured "
                 f"{a.get('configured_mode')} acts {a.get('acts')} level {a.get('level')}")
        self.summary["sessions"]["K"]["disable"] = {"first": r1, "second": r2,
                                                    "status": {k: a.get(k) for k in ("mode", "configured_mode", "acts", "level")}}
        self.event("disable", first=r1, second=r2)
        self.hold(self.t["k_on_s"], "K cap on, disabled")
        self.summary["sessions"]["K"]["disabled_cap_on"] = self.did(since, "K cap, then disabled")
        self.clear_or_wait("K cap")
        self.hold(self.t["k_off_s"], "K cap off")
        self.expect("BACK -> the next session is live again (the disable is for the session only).")
        self.back("K")
        a = self.abr()
        self.log(f"  after K: adaptive_bitrate mode {a.get('mode')} (live expected)")
        self.summary["sessions"]["K"]["mode_after_back"] = a.get("mode")

    def on_signal(self, signum: int, _frame) -> None:
        name = signal.Signals(signum).name
        if signum == signal.SIGHUP:
            self.hung_up = True
        raise Signalled(name)

    def finish(self, why: str) -> None:
        """Every exit after sudo was validated: the fault first, then the teardown, then the files."""
        for s in (signal.SIGINT, signal.SIGHUP, signal.SIGTERM):
            signal.signal(s, signal.SIG_IGN)
        self.clear_fault_final(why)
        self.keepalive_stop.set()
        if self.flag_set:
            self.teardown()
            self.collect()
        elif not self.dry and self.sudo_ok:
            (self.out / "summary.json").write_text(json.dumps(self.summary, indent=1, default=str))

    def run(self) -> int:
        self.log(f"C3-L4-L2B/N1 nft night harness {'(DRY RUN)' if self.dry else '(FAST TEST)' if self.fast else ''}; "
                 f"run dir {self.out}")
        self.log(f"sessions {self.sessions}; timings {self.t}")
        # Ctrl-C is KeyboardInterrupt even if the parent started us with SIGINT ignored (e.g. `cmd &` in a script)
        signal.signal(signal.SIGINT, signal.default_int_handler)
        signal.signal(signal.SIGHUP, self.on_signal)
        signal.signal(signal.SIGTERM, self.on_signal)
        rc = 0
        try:
            self.preflight()
        except Refused as exc:
            self.log(f"REFUSED at preflight: {exc}")
            self.summary["refused"] = str(exc)
            self.finish("refused at preflight")
            (self.out / "summary.json").write_text(json.dumps(self.summary, indent=1, default=str))
            return 2
        except (KeyboardInterrupt, Signalled) as exc:
            self.log(f"aborted at preflight ({type(exc).__name__} {exc}); nothing was set")
            self.summary["aborted_at_preflight"] = f"{type(exc).__name__} {exc}"
            self.finish("aborted at preflight")
            (self.out / "summary.json").write_text(json.dumps(self.summary, indent=1, default=str))
            return 130
        why = "normal end"
        try:
            self.setup()
            if self.cap_kbytes is None and "F1" not in self.sessions:
                self.cap_kbytes = int(round(ESTIMATE_7000_BYTES_PER_S * CAP_FRACTION_OF_7000 / 1024))
            for s in self.sessions:
                self.summary["sessions"].setdefault(s, {})
                {"F1": self.session_f1, "F2": self.session_f2, "F3": self.session_f3, "K": self.session_k}[s]()
        except KeyboardInterrupt:
            self.log("")
            self.log("ABORTED (Ctrl-C). Removing the fault, then tearing down.")
            self.summary["aborted_utc"] = utc()
            self.summary["aborted_by"] = "SIGINT"
            why, rc = "Ctrl-C", 130
        except Signalled as exc:
            self.log(f"ABORTED ({exc}). Removing the fault, then tearing down.")
            self.summary["aborted_utc"] = utc()
            self.summary["aborted_by"] = str(exc)
            why, rc = str(exc), 129 if str(exc) == "SIGHUP" else 143
        except Refused as exc:
            self.log(f"STOPPED: {exc}. Removing the fault, then tearing down.")
            self.summary["stopped"] = str(exc)
            why, rc = "stopped", 3
        except Exception as exc:
            self.log(f"ERROR {type(exc).__name__}: {exc}. Removing the fault, then tearing down.")
            self.summary["error"] = f"{type(exc).__name__}: {exc}"
            why, rc = "error", 4
        finally:
            self.finish(why)
            self.log(f"RUN DIRECTORY: {self.out}")
        return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="the whole flow with each fault replaced by a 30 s wait, holds 60 s, no sudo, prompts auto")
    ap.add_argument("--prereg", default=str(PREREG), help="the night's pre-registration (printed and hashed)")
    ap.add_argument("--out", default=None, help="run directory (default logs/streaming/c3_l4_nft_night_<stamp>)")
    ap.add_argument("--only", default=",".join(SESSIONS),
                    help="which parts to run: any subset of F1,F2,F3,K (always run in that order; default all)")
    ap.add_argument("--sessions", dest="only", help=argparse.SUPPRESS)   # L2's name, kept
    ap.add_argument("--fast", action="store_true", help="TEST ONLY: the real command path with 60 s holds")
    ap.add_argument("--sudo-cmd", default="sudo", help="TEST ONLY: a fake sudo (tools/c3_l4_fake_sudo.py)")
    ap.add_argument("--keepalive-s", type=float, default=KEEPALIVE_S, help=argparse.SUPPRESS)
    ap.add_argument("--test-fail-at", default=None, choices=["F1_cap_on", "F2_loss_on", "F3_drop"],
                    help=argparse.SUPPRESS)
    args = ap.parse_args()
    try:
        parse_only(args.only)
    except ValueError as exc:
        ap.error(str(exc))
    if args.dry_run and (args.fast or args.sudo_cmd != "sudo"):
        ap.error("--dry-run runs no sudo; it does not combine with --fast or --sudo-cmd")
    if args.fast != (args.sudo_cmd != "sudo") or (args.test_fail_at and not args.fast):
        ap.error("--fast, --sudo-cmd and the test hooks are for tests with the fake sudo; they go together")
    return Night(args).run()


if __name__ == "__main__":
    sys.exit(main())
