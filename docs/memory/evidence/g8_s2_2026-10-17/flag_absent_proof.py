#!/usr/bin/env python3
"""G8-S2: flag absent, byte for byte. Read-only; offline; no stream.

    PYTHONDONTWRITEBYTECODE=1 python3 docs/memory/evidence/g8_s2_2026-10-17/flag_absent_proof.py [out_dir]

1. The first-target handler: HEAD's `native_stream.py` (from git) and today's, each
   running the real `_start_linux_locked` on the same stubbed manager
   (`tests/start_rung/stub_manager.py`: nothing spawned, no socket), for a LAN-class
   and an overlay-class target. Compared: the encoder argv, `_active_bitrate_kbps`,
   the payload, every stub call in order, the alpha-log text. Targets are masked.
2. The ladder: G5-S2's `replay.py`, unchanged code, re-run (the recorded decisions exact;
   HEAD's vs today's `LiveController` rows identical -- today's carries G8-S2's
   `_write` hook, flag absent), over the sessions the ladder's log still holds.
3. G5-S3's `replay.py`, unchanged code, re-run with G5-S3's flag on and G8-S2's absent:
   its tables and output equal G5-S3's recorded ones, entry for entry.
   (The ladder's log rotated on 2026-10-17; one of G5-S2's four sessions is gone.)
4. In addition, HEAD's vs today's `LiveController` over every session the log holds.
"""

from __future__ import annotations

import filecmp
import importlib.util
import ipaddress
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tests" / "start_rung"))

import native_stream as today  # noqa: E402
import stub_manager as stub  # noqa: E402

OVERLAY = str(ipaddress.ip_network((0x64400000, 10))[77])
LAN = str(ipaddress.ip_address(0xC0A80117))
TMP = Path(tempfile.mkdtemp(prefix="g8_s2_absent_"))


def load_head(rel, name):
    src = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"], capture_output=True, text=True,
                         check=True).stdout
    p = TMP / f"{name}.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_path(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canon(out, target):
    o = {k: out[k] for k in ("argv", "active_bitrate_kbps", "payload", "calls", "log")}
    text = json.dumps(o, sort_keys=True, default=str)
    return text.replace(target, "<target>").replace(str(out["manager"].project_root), "<tmp>")


def main(out_dir: Path) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    env_absent = all(not k.startswith("PRIVYHUB_") for k in os.environ)
    head = load_head("companion/native_stream.py", "native_stream_head")
    lines = ["# G8-S2 — flag absent, byte for byte (in process)", "",
             f"No `PRIVYHUB_*` variable in this process: {env_absent}; `native_stream.START_RUNG` is "
             f"{today.START_RUNG!r}; HEAD from git; temp files `g8_s2_absent_*`, `g8_s2_stub_*` left in place.", "",
             "## 1. The first-target handler (`_start_linux_locked`), HEAD vs today", "",
             "| target class | argv -b:v / -maxrate / -bufsize | active kbps | stub calls | identical (argv, level, "
             "payload, calls, log) |", "| --- | --- | --- | --- | --- |"]
    ok = env_absent and today.START_RUNG is None and not hasattr(head, "START_RUNG")
    for label, target in (("LAN", LAN), ("overlay", OVERLAY)):
        a, b = stub.run_start(head, target), stub.run_start(today, target)
        same = canon(a, target) == canon(b, target)
        ok &= same
        r = lambda o: "/".join(o["argv"][o["argv"].index(f) + 1] for f in ("-b:v", "-maxrate", "-bufsize"))
        lines.append(f"| {label} | {r(a)} / {r(b)} | {a['active_bitrate_kbps']} / {b['active_bitrate_kbps']} | "
                     f"{len(a['calls'])} / {len(b['calls'])} | **{'yes' if same else 'NO'}** |")
    lines.append("")
    # 2-3. The replays, unchanged code, over the sessions the live log still holds
    ev = REPO / "docs/memory/evidence"
    g5s2 = load_path(ev / "g5_s2_2026-10-16/replay.py", "g5_s2_replay_rerun")
    sessions = g5s2.n2.exact_sessions(g5s2.n2.live_log_rows())
    held, gone = [], []
    for label, d in g5s2.RUNS:
        try:
            g5s2.session_for(d, sessions)
            held.append((label, d))
        except SystemExit:
            gone.append(label)
    lines += ["## 2-3. The replays (unchanged code) over the sessions the ladder's log still holds", "",
              f"- the ladder's log (`logs/games/adaptive_bitrate_shadow.jsonl` + 3 archives, `LOG_KEEP = 3`) rotated at "
              f"2026-10-17T03:57Z during G8-S1's night; it now starts 2026-10-10T08:59Z.",
              f"- G5-S2's four runs: held {len(held)} ({', '.join(l for l, _ in held)}); **rotated out: "
              f"{', '.join(gone) or 'none'}** (no copy in the evidence tree). The replays run over the held ones.", ""]
    rec2 = json.loads((ev / "g5_s2_2026-10-16/replay_tables.json").read_text())
    rec3 = json.loads((ev / "g5_s3_2026-10-17/replay_tables.json").read_text())
    g5s2.RUNS = held
    d2 = out_dir / "g5_s2_replay_rerun"
    d2.mkdir(exist_ok=True)
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc2 = g5s2.main(d2)
    (d2 / "replay_console.txt").write_text(buf.getvalue())
    now2 = json.loads((d2 / "replay_tables.json").read_text())
    s2_same = all(now2[k] == rec2[k] for k in now2) and set(now2) == {k for k in rec2 if k.split(" / ")[0] in
                                                                       {l for l, _ in held}}
    s2_ok = rc2 == 0 and "-> flag absent: PASS" in buf.getvalue()
    ok &= s2_ok and s2_same
    lines += ["**G5-S2's `replay.py`** (its `RUNS` restricted to the held sessions):", "", "```"] + [
        x for x in buf.getvalue().splitlines() if "exact" in x or "MISMATCH" in x] + ["```", "",
        f"- recorded decisions exact and HEAD's vs today's controller identical: **{'PASS' if s2_ok else 'FAIL'}**",
        f"- its WAN tables, entry for entry, equal G5-S2's recorded ones ({len(now2)} entries): "
        f"**{'yes' if s2_same else 'NO'}**", ""]
    g5s3 = load_path(ev / "g5_s3_2026-10-17/replay.py", "g5_s3_replay_rerun")
    g5s3.g5s2.RUNS = held
    d3 = out_dir / "g5_s3_replay_rerun"
    d3.mkdir(exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc3 = g5s3.main(d3)
    (d3 / "replay_console.txt").write_text(buf.getvalue())
    now3 = json.loads((d3 / "replay_tables.json").read_text())
    s3_same = rc3 == 0 and all(now3[k] == rec3[k] for k in now3) and len(now3) == len(rec3) - 4 * len(gone)
    rec_md = (ev / "g5_s3_2026-10-17/replay_output.md").read_text().splitlines()
    now_md = (d3 / "replay_output.md").read_text().splitlines()
    md_same = [x for x in rec_md if not any(g.split(" (")[0] in x for g in gone)] == now_md
    ok &= s3_same and md_same
    lines += ["**G5-S3's `replay.py`** (G5-S3 on, G8-S2 absent; its G5-S2 runs restricted the same way):", "",
              f"- exit {rc3}; its tables, entry for entry, equal G5-S3's recorded ones ({len(now3)} of {len(rec3)} "
              f"entries; the {len(rec3) - len(now3)} missing are the rotated session's): **{'yes' if s3_same else 'NO'}**",
              f"- `replay_output.md` equals the recorded one with the rotated session's rows removed: "
              f"**{'yes' if md_same else 'NO'}**", ""]
    # 4. In compensation: HEAD's vs today's controller over every session the log holds
    head_live = g5s2.load_head_module()
    import adaptive_bitrate_live as live_today
    rec = g5s2.n2.RecoveryTimeline(g5s2.n2.recovery_rows())
    n_s = n_rows = n_diff = 0
    for sess in sessions:
        if sum(1 for r in sess if r.get("event") == "sample") < 5:
            continue
        a = g5s2.drive_controller(head_live, sess, rec, {})
        b = g5s2.drive_controller(live_today, sess, rec, {})
        n_s += 1
        n_rows += len(a)
        n_diff += a != b
    ok &= n_diff == 0 and n_s > 0
    lines += ["## 4. In addition: HEAD's vs today's `LiveController` over every session the log holds", "",
              f"- sessions with >= 5 reports: {n_s}; rows written: {n_rows}; sessions differing: **{n_diff}**", "",
              f"-> flag absent: **{'PASS' if ok else 'FAIL'}**"]
    (out_dir / "flag_absent_output.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE))
