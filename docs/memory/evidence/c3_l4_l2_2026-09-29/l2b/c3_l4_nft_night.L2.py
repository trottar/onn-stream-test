#!/usr/bin/env python3
"""C3-L4-L2: the `nft` fault-injection night for the live controller -- run by the USER.

    python3 tools/c3_l4_nft_night.py              # the night (~75-90 min)
    python3 tools/c3_l4_nft_night.py --dry-run    # the whole flow, no fault (~20 min)

Run it in tmux on the host, in one pane; keep a second pane open for `sudo`.
**This harness never runs `nft`** (nor `sudo`). At every fault step it
prints the exact `sudo nft ...` line to paste into the other pane and waits
for Enter, recording when Enter was pressed. Every `nft list ...` line it
prints ends in `| tee -a <run dir>/nft_tables.txt`, so the harness reads the
counters and the table state from that file itself.

**To abort at any point**: paste the delete line the harness prints first at
every step,

    sudo nft delete table inet privyhub_fault

then press Ctrl-C here. The harness prints the delete line again, asks you to
confirm, and tears down (flag unset, companion restarted through its unit,
game ended, samplers stopped).

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
  teardown -> the flag unset and confirmed absent; everything collected

Everything is written to `logs/streaming/c3_l4_nft_night_<stamp>/` (or
`--out`); the directory is printed at the end. Scoring is a later Code task.
Privacy: the onn's adb endpoint is held in memory only; the journal copy is
redacted; no addresses are written.
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
DELETE = "sudo nft delete table inet privyhub_fault"
EVID = REPO / "docs" / "memory" / "evidence" / "c3_l4_l2_2026-09-29"
PREREG = EVID / "c3_l4_l2_nft_preregistration.txt"
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

PRIVATE_IP = re.compile(r"\b(10\.\d{1,3}|192\.168|172\.(1[6-9]|2\d|3[01])|169\.254)\.\d{1,3}\.\d{1,3}\b")
MAC = re.compile(r"\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b")


def utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def sh(cmd: list[str] | str, timeout: float = 30) -> str:
    try:
        r = subprocess.run(cmd, shell=isinstance(cmd, str), capture_output=True, text=True, timeout=timeout)
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


class Night:
    def __init__(self, args: argparse.Namespace) -> None:
        self.dry = args.dry_run
        self.t = DRY if self.dry else REAL
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        default = REPO / "logs" / "streaming" / f"c3_l4_nft_night_{'dryrun_' if self.dry else ''}{stamp}"
        self.out = Path(args.out) if args.out else default
        self.out.mkdir(parents=True, exist_ok=True)
        self.prereg = Path(args.prereg)
        self.sessions = [s.strip() for s in args.sessions.split(",") if s.strip()]
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
        self.summary: dict = {"dry_run": self.dry, "started_utc": self.started_utc, "sessions": {}}
        self.current = "setup"

    # -- output ----------------------------------------------------------------
    def log(self, msg: str) -> None:
        line = f"[{datetime.now(timezone.utc).strftime('%H:%M:%SZ')}] {msg}"
        print(line, flush=True)
        with open(self.out / "harness.log", "a") as fh:
            fh.write(line + "\n")

    def event(self, name: str, **kw) -> None:
        with open(self.out / "events.jsonl", "a") as fh:
            fh.write(json.dumps({"at_utc": utc(), "session": self.current, "event": name, **kw}) + "\n")

    def banner(self, title: str) -> None:
        self.log("=" * 72)
        self.log(title)
        self.log(f"  TO CLEAR ANY FAULT, paste in the sudo pane:   {DELETE}")
        self.log("=" * 72)

    def paste(self, line: str) -> None:
        if self.dry:
            self.log(f"  (dry run -- do NOT paste)   {line}")
        else:
            self.log(f"  PASTE >>>   {line}")

    def enter(self, prompt: str) -> float:
        """Wait for Enter (auto in the dry run); returns the epoch it was pressed."""
        if self.dry:
            self.log(f"  [{prompt}] -- dry run: auto-advance")
            time.sleep(1)
        else:
            try:
                input(f"  >>> {prompt} -- press Enter here when done: ")
            except EOFError:
                raise KeyboardInterrupt
        t = time.time()
        self.event("enter", prompt=prompt)
        return t

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
                                        stdout=open(self.out / "t2_sampler.log", "a"), stderr=subprocess.STDOUT)
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
        after = [x for x in self.series if x["at_utc"] >= since]
        last = after[-1] if after else {}
        rl = any(x.get("rate_limited") for x in after)
        rec = [r.get("event") for r in self.log_rows("native_stream_recovery.log", "at_utc", since)]
        text = (f"DID ({label}): " + (", ".join(f"{r['at_utc'][11:19]}Z {r.get('event')} {r.get('class')} "
                                               f"{r.get('from_kbps')}->{r.get('to_kbps')}" for r in tr) or "no transition")
                + (f"; HOLD {holds[0].get('reason')}" if holds else "")
                + (f"; refused {ref}" if ref else "")
                + f"; rate_limited ever {rl}; now level {last.get('level')} state {last.get('state')} "
                  f"mode {last.get('mode')} recovery {last.get('recovery')}"
                + (f"; recovery log {rec}" if rec else ""))
        self.log("  " + text)
        out = {"label": label, "since": since, "transitions": [
            {k: r.get(k) for k in ("at_utc", "event", "class", "from_kbps", "to_kbps", "injected", "acted")} for r in tr],
            "holds": len(holds), "refused": ref, "rate_limited_ever": rl, "level": last.get("level"),
            "state": last.get("state"), "mode": last.get("mode"), "recovery_events": rec}
        self.event("did", **out)
        return out

    def hold(self, seconds: int, label: str) -> None:
        end = time.time() + seconds
        nxt = time.time() + 30
        while time.time() < end:
            time.sleep(min(1.0, max(0.0, end - time.time())))
            if time.time() >= nxt and self.series:
                x = self.series[-1]
                w = x.get("window") or {}
                self.log(f"    {label}: {int(seconds - (end - time.time()))}/{seconds} s -- level {x.get('level')} "
                         f"state {x.get('state')} transitions {x.get('transitions_this_session')} "
                         f"window {w.get('reports')}/{w.get('clean')} recovery {x.get('recovery')}")
                nxt += 30

    # -- nft file ---------------------------------------------------------------------
    def nft_read_new(self, offset: int) -> str:
        if not self.nft_file.exists():
            return ""
        with open(self.nft_file, errors="replace") as fh:
            fh.seek(offset)
            return fh.read()

    def nft_offset(self) -> int:
        return self.nft_file.stat().st_size if self.nft_file.exists() else 0

    def make_table_lines(self) -> list[str]:
        return [f"sudo nft add table {TABLE}",
                f"sudo nft add chain {TABLE} flt '{{ type filter hook output priority 0; }}'"]

    def cap_rule(self) -> str:
        return (f"sudo nft add rule {TABLE} flt udp dport {VIDEO_PORT} limit rate over "
                f"{self.cap_kbytes} kbytes/second burst 64 kbytes counter drop")

    def apply(self, lines: list[str], what: str) -> float:
        self.log(f"  APPLY ({what}) -- in the sudo pane, paste in order:")
        for l in lines:
            self.paste(l)
        self.paste(f"sudo nft list table {TABLE} | tee -a {self.nft_file}")
        t = self.enter(f"{what}: pasted and listed")
        self.fault_may_be_on = True
        self.event("fault_on", what=what, lines=lines)
        return t

    def remove(self, what: str) -> float:
        self.log(f"  REMOVE ({what}) -- paste:")
        self.paste(DELETE)
        self.paste(f"sudo nft list tables | tee -a {self.nft_file}")
        off = self.nft_offset()
        t = self.enter(f"{what}: deleted and listed")
        new = self.nft_read_new(off)
        if not self.dry:
            if "privyhub_fault" in new:
                self.log("  !! privyhub_fault is STILL listed -- paste the delete line again")
                self.paste(DELETE)
                self.enter("deleted again")
            elif not new.strip():
                self.log("  (nothing new in nft_tables.txt -- was the `list tables` line pasted with its tee?)")
        self.fault_may_be_on = False
        self.event("fault_off", what=what)
        return t

    # -- preflight -------------------------------------------------------------------
    def preflight(self) -> None:
        self.banner("PREFLIGHT")
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
        self.log("  No fault table may exist before the night:")
        self.paste(f"sudo nft list tables | tee -a {self.nft_file}")
        off = self.nft_offset()
        self.enter("listed the nft tables")
        new = self.nft_read_new(off)
        if not self.dry:
            if "privyhub_fault" in new:
                raise Refused(f"a privyhub_fault table exists -- paste `{DELETE}` and start again")
            if not new.strip():
                raise Refused("nothing was written to nft_tables.txt (paste the line with its `| tee -a ...`)")
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
        self.banner("TEARDOWN")
        if self.fault_may_be_on:
            self.log("  A fault may still be on. Paste now:")
            self.paste(DELETE)
            try:
                self.enter("the fault table is deleted")
            except KeyboardInterrupt:
                pass
        if not self.dry:
            self.log("  Confirm no fault table remains:")
            self.paste(f"sudo nft list tables | tee -a {self.nft_file}")
            off = self.nft_offset()
            try:
                self.enter("listed the nft tables")
            except KeyboardInterrupt:
                pass
            new = self.nft_read_new(off)
            self.summary["no_fault_table_at_end"] = bool(new.strip()) and "privyhub_fault" not in new
            self.log(f"  privyhub_fault absent at the end: {self.summary['no_fault_table_at_end']}")
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
    def calibrate(self) -> None:
        self.log("  CALIBRATE the cap: a counter-only rule on the video port (no drop).")
        lines = self.make_table_lines() + [f"sudo nft add rule {TABLE} flt udp dport {VIDEO_PORT} counter"]
        self.log("  paste in order:")
        for l in lines:
            self.paste(l)
        self.enter("counter table made")
        self.fault_may_be_on = True
        self.event("counter_on", lines=lines)
        readings = []
        for i in (1, 2):
            if i == 2:
                self.log(f"  waiting {self.t['calib_gap_s']} s between the two readings ...")
                time.sleep(self.t["calib_gap_s"])
            self.paste(f"sudo nft list table {TABLE} | tee -a {self.nft_file}")
            off = self.nft_offset()
            t = self.enter(f"counter reading {i} listed")
            m = re.findall(r"udp dport %d counter packets (\d+) bytes (\d+)" % VIDEO_PORT, self.nft_read_new(off))
            readings.append((t, int(m[-1][1]) if m else None))
        (t1, b1), (t2, b2) = readings
        rate = (b2 - b1) / (t2 - t1) if (b1 is not None and b2 is not None and t2 > t1) else None
        if rate is None or not (500_000 <= rate <= 1_800_000):
            self.log(f"  counter rate {rate!r} B/s not usable -> the L1 estimate {ESTIMATE_7000_BYTES_PER_S} B/s"
                     + (" (dry run)" if self.dry else " -- CHECK the tee'd listing"))
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
    def fault_or_wait(self, lines: list[str], what: str) -> float:
        if self.dry:
            self.log(f"  (dry run: the fault '{what}' is replaced by a wait; its lines are shown only)")
            for l in lines:
                self.paste(l)
            self.event("fault_on", what=what, dry=True)
            return time.time()
        return self.apply(lines, what)

    def clear_or_wait(self, what: str) -> float:
        if self.dry:
            self.paste(DELETE)
            self.event("fault_off", what=what, dry=True)
            return time.time()
        return self.remove(what)

    def session_f1(self) -> None:
        self.banner("F1 -- capacity cap (the controller's main case)")
        self.launch("F1")
        self.log(f"  baseline {self.t['baseline_s']} s at 7000 ...")
        self.hold(self.t["baseline_s"], "F1 baseline")
        if self.dry:
            self.calibrate()
            self.paste(DELETE)
            self.fault_may_be_on = False
        else:
            self.calibrate()
        lines = [f"sudo nft flush chain {TABLE} flt", self.cap_rule()] if not self.dry else \
            self.make_table_lines() + [self.cap_rule()]
        self.expect("within ~10-20 s ONE decrease: FALLBACK 7000->5000 (or ROUTINE 7000->6000, then FALLBACK "
                    "->5000 >= 60 s later); ~186 s later INCREASE 5000->5500 (fits the cap); ~186 s later "
                    "INCREASE 5500->6000 (over the cap); a FALLBACK back to 5000 >= 120 s after that; then, "
                    "instead of a third direction change inside 10 min, HOLD (oscillation) at 5000. "
                    "rate_limited never true; never two transitions closer than the hold-downs; no ramp.")
        t = time.time()
        since = utc()
        self.fault_or_wait(lines, "F1 cap")
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
        lines = self.make_table_lines() + [
            f"sudo nft add rule {TABLE} flt udp dport {VIDEO_PORT} numgen random mod 1000 < 20 counter drop"]
        self.expect("FEC recovers part of it; loss alone is never evidence. Either no transition, or AT MOST ONE "
                    "decrease (ROUTINE ->6000 or FALLBACK ->5000) and then only at_or_below_target / at_floor / "
                    "hold_down refusals. No second decrease, never a ramp.")
        since = utc()
        self.fault_or_wait(lines, "F2 2% loss")
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
        self.expect("the cap brings the stream to 5000 (one decrease).")
        since = utc()
        self.fault_or_wait(self.make_table_lines() + [self.cap_rule()], "F3 cap")
        end = time.time() + self.t["f3_reach_s"]
        while time.time() < end and (self.series[-1].get("level") if self.series else None) != 5000:
            time.sleep(2)
        reached = (self.series[-1].get("level") if self.series else None) == 5000
        self.log(f"  at 5000: {reached}")
        self.summary["sessions"]["F3"]["cap_to_5000"] = self.did(since, "F3 cap")
        self.expect("recovery owns the drop: desync_pause, encoder_restart AT 5000 (C3-F1, level-preserving), "
                    "resumed. The controller does NOTHING while recovery is not PLAYING (a refused/guard "
                    "recovery_playing row, or no rows because reports stop); then ssrc_change "
                    "(recovery_restart) and a 3-report blackout; the level still 5000 (no level_sync).")
        drop = [f"sudo nft flush chain {TABLE} flt",
                f"sudo nft add rule {TABLE} flt udp dport {{ {VIDEO_PORT}, {AUDIO_PORT} }} counter drop"]
        since = utc()
        if self.dry:
            self.fault_or_wait(drop, "F3 full drop")
            time.sleep(self.t["f3_drop_s"])
            self.paste(DELETE)
        else:
            self.log(f"  the DROP: paste the two lines, press Enter at once; the harness counts "
                     f"{self.t['f3_drop_s']} s and then asks for the delete line.")
            self.apply(drop, "F3 full drop")
            for s in range(self.t["f3_drop_s"], 0, -1):
                print(f"\r    drop on: {s:2d} s left ", end="", flush=True)
                time.sleep(1)
            print()
            self.remove("F3 full drop")
        self.log(f"  observing {self.t['f3_after_s']} s (recovery should resume) ...")
        self.hold(self.t["f3_after_s"], "F3 after the drop")
        self.summary["sessions"]["F3"]["drop"] = self.did(since, "F3 drop and recovery")
        self.back("F3")

    def session_k(self) -> None:
        self.banner("K -- the kill switch during a fault")
        self.launch("K")
        self.hold(self.t["baseline_s"], "K baseline")
        since = utc()
        self.fault_or_wait(self.make_table_lines() + [self.cap_rule()], "K cap")
        end = time.time() + self.t["k_first_s"]
        while time.time() < end and not (self.series and self.series[-1].get("transitions_this_session")):
            time.sleep(2)
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

    def run(self) -> int:
        self.log(f"C3-L4-L2 nft night harness {'(DRY RUN)' if self.dry else ''}; run dir {self.out}")
        self.log(f"sessions {self.sessions}; timings {self.t}")
        rc = 0
        try:
            self.preflight()
        except Refused as exc:
            self.log(f"REFUSED at preflight: {exc}")
            self.summary["refused"] = str(exc)
            (self.out / "summary.json").write_text(json.dumps(self.summary, indent=1, default=str))
            return 2
        except KeyboardInterrupt:
            self.log("aborted at preflight; nothing was set")
            return 130
        try:
            self.setup()
            if self.cap_kbytes is None and "F1" not in self.sessions:
                self.cap_kbytes = int(round(ESTIMATE_7000_BYTES_PER_S * CAP_FRACTION_OF_7000 / 1024))
            for s in self.sessions:
                self.summary["sessions"].setdefault(s, {})
                {"F1": self.session_f1, "F2": self.session_f2, "F3": self.session_f3, "K": self.session_k}[s]()
        except KeyboardInterrupt:
            self.log("")
            self.log(f"ABORTED (Ctrl-C). FIRST paste in the sudo pane:   {DELETE}")
            self.summary["aborted_utc"] = utc()
            self.fault_may_be_on = True
            rc = 130
        except Refused as exc:
            self.log(f"STOPPED: {exc}. If a fault is on, paste:   {DELETE}")
            self.summary["stopped"] = str(exc)
            self.fault_may_be_on = True
            rc = 3
        except Exception as exc:
            self.log(f"ERROR {type(exc).__name__}: {exc}. If a fault is on, paste:   {DELETE}")
            self.summary["error"] = f"{type(exc).__name__}: {exc}"
            self.fault_may_be_on = True
            rc = 4
        finally:
            if self.flag_set:
                signal.signal(signal.SIGINT, signal.SIG_IGN)
                self.teardown()
                self.collect()
            self.log(f"RUN DIRECTORY: {self.out}")
        return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="the whole flow with each fault replaced by a 30 s wait, holds 60 s, prompts auto")
    ap.add_argument("--prereg", default=str(PREREG), help="the night's pre-registration (printed and hashed)")
    ap.add_argument("--out", default=None, help="run directory (default logs/streaming/c3_l4_nft_night_<stamp>)")
    ap.add_argument("--sessions", default="F1,F2,F3,K", help="which sessions, in order (default F1,F2,F3,K)")
    args = ap.parse_args()
    return Night(args).run()


if __name__ == "__main__":
    sys.exit(main())
