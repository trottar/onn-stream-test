#!/usr/bin/env python3
"""G5-S3: flag absent, byte for byte -- HEAD's file against the edited one, in process.

    PYTHONDONTWRITEBYTECODE=1 python3 docs/memory/evidence/g5_s3_2026-10-17/flag_absent_proof.py [out_dir]

Read-only; offline; no stream. This process carries no PRIVYHUB_REMOTE_LADDER.

1. The actuator (`diagnostics/c3_linux_actuator_probe.py`): HEAD's (from git) and
   the edited module, each over every entry point (the validated transition, the
   sized level transition, recovery's same-level restart, the C3.L3 fixed cycle)
   x every current level x every target (3000 ... 12600, incl. 4000), against C3-F1's
   fake manager (the real cycle and argv builder; nothing spawned). Compared: the
   payload, the argv, the exception (type and text) and the manager's level after.
2. The games plugin (`plugins/games.py`): HEAD's and the edited
   `handle_post_request("native-stream-start")` with the same stubs -- the payload
   (or the exception) and every stub call, for a started stream, an inactive game
   and a failing start; and `_adaptive_bitrate_context`. The modules are loaded
   from their files alone (the `plugins` package would construct every plugin).
3. The ladder: G5-S2's own `replay.py`, unchanged, re-run -- the four runs'
   recorded decisions and HEAD's vs the edited `LiveController` (flag absent);
   its flag-present (`PRIVYHUB_WAN_ADAPTATION`) tables compared with the ones G5-S2
   recorded (the edited `wan_adaptation.py` without this flag).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tools"))

import test_c3_f1_recovery_restart as f1  # noqa: E402
import adaptive_bitrate_live as live  # noqa: E402

LEVELS = (3000, 3500, 4000, 5000, 5500, 6000, 7000, 12600)
TMP = Path(tempfile.mkdtemp(prefix="g5_s3_absent_"))


def load(rel: str, name: str, rev: str | None):
    if rev is None:
        path = REPO / rel
    else:
        src = subprocess.run(["git", "-C", str(REPO), "show", f"{rev}:{rel}"], capture_output=True, text=True,
                             check=True).stdout
        path = TMP / (name + ".py")
        path.write_text(src)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canon(o) -> str:
    return json.dumps(o, sort_keys=True, default=repr)


# ------------------------------------------------------------- 1. actuator ---
def run_probe(mod, entry: str, current: int, target: int | None) -> dict:
    m = f1.fake_manager(current)
    m._active_width, m._active_height = (1920, 1080) if current == 12600 else (1280, 720)
    spawned = []

    def popen(argv, **k):
        p = f1.FakeProc(argv)
        spawned.append(p)
        return p
    clock = f1.Clock()
    kw = dict(popen_factory=popen, monotonic=clock, sleep=lambda s: None, perf_counter_ns=lambda: int(clock() * 1e9))
    fn = getattr(mod, entry)
    try:
        if entry == "run_c3_linux_recovery_restart":
            out = fn(m, **kw)
        elif entry == "run_c3_linux_fixed_bitrate_cycle":
            out = fn(m, target, **kw)
        else:
            out = fn(m, target_bitrate_kbps=target, **kw)
        res = {"ok": True, "payload": out}
    except Exception as exc:
        res = {"ok": False, "exc": f"{type(exc).__name__}: {exc}"}
    res["argv"] = [p.argv for p in spawned]
    res["level_after"] = (m._active_bitrate_kbps, getattr(m, "_active_width", None), getattr(m, "_active_height", None))
    res["killed"] = len(m.killed)
    return res


def actuator_comparison(lines: list[str]) -> bool:
    head = load("companion/diagnostics/c3_linux_actuator_probe.py", "probe_head", "HEAD")
    edited = load("companion/diagnostics/c3_linux_actuator_probe.py", "probe_edited", None)
    assert edited.REMOTE_LADDER is None and not hasattr(head, "REMOTE_LADDER")
    entries = ("run_c3_linux_validated_bitrate_transition", "run_c3_linux_level_transition",
               "run_c3_linux_fixed_bitrate_cycle", "run_c3_linux_recovery_restart")
    cases = same = ok_cases = 0
    diffs = []
    for entry in entries:
        for cur in LEVELS:
            for tgt in ((None,) if entry == "run_c3_linux_recovery_restart" else LEVELS):
                a, b = run_probe(head, entry, cur, tgt), run_probe(edited, entry, cur, tgt)
                cases += 1
                ok_cases += a["ok"]
                if canon(a) == canon(b):
                    same += 1
                else:
                    diffs.append((entry, cur, tgt))
    four = [(e, c, t) for e in entries for c in LEVELS for t in ((None,) if e.endswith("restart") else LEVELS)
            if 4000 in (c, t)]
    four_ok = sum(1 for e, c, t in four if run_probe(edited, e, c, t)["ok"])
    lines += ["## 1. The actuator: HEAD vs edited `c3_linux_actuator_probe.py` (flag absent)", "",
              f"- cases (entry x current x target): {cases}; identical: **{same}**; differing: {len(diffs)}",
              f"- of which the cycle succeeded: {ok_cases} (the rest refused, identically)",
              f"- cases touching 4000: {len(four)}; accepted by the edited module: **{four_ok}** (refused as at HEAD)",
              ""]
    if diffs:
        lines.append(f"- DIFFER: {diffs[:10]}")
    return not diffs and four_ok == 0


# ----------------------------------------------------------- 2. the plugin ---
class Recorder:
    def __init__(self, name, calls, ret=None, exc=None):
        self.name, self.calls, self.ret, self.exc = name, calls, ret, exc

    def __call__(self, *a, **kw):
        self.calls.append((self.name, a, sorted(kw.items())))
        if self.exc:
            raise self.exc
        return self.ret() if callable(self.ret) else self.ret


def run_plugin(mod, scenario: str) -> dict:
    calls: list = []
    p = object.__new__(mod.GamesPlugin)
    active = scenario != "inactive"
    p._emulator = types.SimpleNamespace(
        status=Recorder("emulator.status", calls, ret=lambda: {"active": active, "paused": False, "pid": 4242}),
        pause=Recorder("emulator.pause", calls, ret={"active": True, "paused": True, "pid": 4242}))
    p._recovery = types.SimpleNamespace(note_stream_start=Recorder("recovery.note_stream_start", calls),
                                        current_state=Recorder("recovery.current_state", calls, ret="PLAYING"))
    start_exc = mod.NativeStreamError("encoder failed") if scenario == "start_fails" else None
    p._native_stream = types.SimpleNamespace(
        start=Recorder("native_stream.start", calls, ret=lambda: {"ok": True, "active": True}, exc=start_exc),
        stop=Recorder("native_stream.stop", calls))
    p._diagnostic_heartbeat_interval_ms = Recorder("heartbeat_interval", calls, ret=2000)
    overlay_target = str(__import__("ipaddress").ip_network((0x64400000, 10))[77])
    try:
        out = {"payload": p.handle_post_request("native-stream-start", "port=48100&audio_port=48102", overlay_target)}
    except Exception as exc:
        out = {"exc": f"{type(exc).__name__}: {exc}"}
    out["calls"] = calls
    out["recovery_start_args"] = getattr(p, "_recovery_start_args", None)
    out["context"] = mod.GamesPlugin._adaptive_bitrate_context(p)
    return json.loads(canon(out).replace(overlay_target, "<overlay-class target>"))


def plugin_comparison(lines: list[str]) -> bool:
    head = load("companion/plugins/games.py", "games_head", "HEAD")
    edited = load("companion/plugins/games.py", "games_edited", None)
    ok = True
    lines += ["## 2. The games plugin: HEAD vs edited `handle_post_request(\"native-stream-start\")` (flag absent)", "",
              "| scenario | HEAD | edited | identical |", "| --- | --- | --- | --- |"]
    for sc in ("started", "inactive", "start_fails"):
        a, b = run_plugin(head, sc), run_plugin(edited, sc)
        same = canon(a) == canon(b)
        ok &= same
        what = lambda r: ("payload" if "payload" in r else r["exc"].split(":")[0]) + f", {len(r['calls'])} stub calls"
        lines.append(f"| {sc} | {what(a)} | {what(b)} | {'**yes**' if same else 'NO'} |")
    lines.append("")
    return ok


# ------------------------------------------------- 3. G5-S2's replay, re-run ---
def g5_s2_rerun(lines: list[str], out_dir: Path) -> bool:
    rerun = out_dir / "g5_s2_replay_rerun"
    rerun.mkdir(parents=True, exist_ok=True)
    script = REPO / "docs/memory/evidence/g5_s2_2026-10-16/replay.py"
    proc = subprocess.run([sys.executable, "-B", str(script), str(rerun)], capture_output=True, text=True,
                          env={k: v for k, v in __import__("os").environ.items() if not k.startswith("PRIVYHUB_")} | {"PYTHONDONTWRITEBYTECODE": "1"})
    (rerun / "replay_console.txt").write_text(proc.stdout + proc.stderr)
    recorded = json.loads((script.parent / "replay_tables.json").read_text())
    now = json.loads((rerun / "replay_tables.json").read_text())
    tables_same = canon(recorded) == canon(now)
    passed = proc.returncode == 0 and "-> flag absent: PASS" in proc.stdout
    lines += ["## 3. G5-S2's `replay.py`, unchanged, re-run with the new code present", "",
              "```"] + [x for x in proc.stdout.splitlines() if x.startswith("|") and ("exact" in x or "identical" in x
                                                                                     or "run |" in x)] + [
              "```", "",
              f"- flag absent (recorded decisions exact, HEAD vs edited controller identical): "
              f"**{'PASS' if passed else 'FAIL'}** (exit {proc.returncode})",
              f"- its flag-present tables (`PRIVYHUB_WAN_ADAPTATION`, the edited `wan_adaptation.py`, this flag "
              f"absent) equal G5-S2's recorded `replay_tables.json`: **{'yes' if tables_same else 'NO'}**", ""]
    return passed and tables_same


def main(out_dir: Path) -> int:
    lines = ["# G5-S3 — flag absent, byte for byte (in process)", "",
             f"`PRIVYHUB_REMOTE_LADDER` in this process: {'absent' if live.REMOTE_LADDER is None else 'SET'}; "
             f"HEAD from git; temp files under the system temp directory (`g5_s3_absent_*`), left in place.", ""]
    ok = actuator_comparison(lines)
    ok = plugin_comparison(lines) and ok
    ok = g5_s2_rerun(lines, out_dir) and ok
    lines.append(f"-> flag absent: **{'PASS' if ok else 'FAIL'}**")
    (out_dir / "flag_absent_output.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent))
