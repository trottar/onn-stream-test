#!/usr/bin/env python3
"""G8-S4 (and G4-W2's native_stream hook): flag absent, the encoder command byte for byte.

    PYTHONDONTWRITEBYTECODE=1 python3 -I docs/memory/evidence/g8_s4_2026-10-18/flag_absent_proof.py

HEAD's `native_stream.py` (git) and today's, each `_build_linux_ffmpeg_command` on G8-S2's stub
manager, no PRIVYHUB_* in the process: targets 4000 / 5000 / 5500 / 6000 / 7000 (7000 also with no
kwargs, as a start calls it), the sized 12,600 at 1920x1080, and each again with the diagnostic
PRIVYHUB_ENC_BUFSIZE_K=300 set at build time. Compared: the argv (exact), and its masked sha256
(E4-S5B's method: window, display, device, ffmpeg path, sink masked). Then the start handler
(`_start_linux_locked`, LAN- and overlay-class targets): argv, level, payload, calls, log.
Writes flag_absent_output.md next to this script.
"""

from __future__ import annotations

import hashlib
import importlib.util
import ipaddress
import json
import os
import re
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

TMP = Path(tempfile.mkdtemp(prefix="g8_s4_absent_"))
LAN = str(ipaddress.ip_address(0xC0A80117))
OVERLAY = str(ipaddress.ip_network((0x64400000, 10))[77])


def load_head():
    src = subprocess.run(["git", "-C", str(REPO), "show", "HEAD:companion/native_stream.py"], capture_output=True,
                         text=True, check=True).stdout
    p = TMP / "native_stream_head.py"
    p.write_text(src)
    spec = importlib.util.spec_from_file_location("native_stream_head", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def masked(argv):
    text = "\x00".join(argv).replace("4242", "<window>").replace(":0", "<display>")
    text = text.replace("/fixture/renderD128", "<device>").replace("/fixture/ffmpeg", "<ffmpeg>")
    return hashlib.sha256(re.sub(r"rtp://[^\x00]*", "<sink>", text).encode()).hexdigest()


def build(mod, kw):
    m = stub.stub_manager(mod, [])
    return m._build_linux_ffmpeg_command(ffmpeg=Path("/fixture/ffmpeg"), capture_target={"_window_id": 4242}, **kw)


def canon(out, target):
    o = {k: out[k] for k in ("argv", "active_bitrate_kbps", "payload", "calls", "log")}
    text = json.dumps(o, sort_keys=True, default=str)
    return text.replace(target, "<target>").replace(str(out["manager"].project_root), "<tmp>")


def main() -> int:
    env_absent = all(not k.startswith("PRIVYHUB_") for k in os.environ)
    head = load_head()
    cases = [("7000 (no kwargs)", {})]
    cases += [(str(t), {"bitrate_kbps": t, "max_bitrate_kbps": t}) for t in (4000, 5000, 5500, 6000, 7000)]
    cases += [("12600 @1920x1080", {"bitrate_kbps": 12600, "max_bitrate_kbps": 12600, "width": 1920, "height": 1080})]
    lines = ["# G8-S4 — flag absent, the encoder command byte for byte (in process)", "",
             f"No `PRIVYHUB_*` in this process: {env_absent}; today's `ENCODER_RC` = {today.ENCODER_RC!r}, "
             f"`AUDIO_CODEC` = {today.AUDIO_CODEC!r}; HEAD has `ENCODER_RC`: {hasattr(head, 'ENCODER_RC')}.", "",
             "| case | PRIVYHUB_ENC_BUFSIZE_K | rate args (today) | masked sha256 (HEAD = today) | identical |",
             "| --- | --- | --- | --- | --- |"]
    ok = env_absent and today.ENCODER_RC is None
    for label, kw in cases:
        for buf in (None, "300"):
            if buf:
                os.environ["PRIVYHUB_ENC_BUFSIZE_K"] = buf
            try:
                a, b = build(head, kw), build(today, kw)
            finally:
                os.environ.pop("PRIVYHUB_ENC_BUFSIZE_K", None)
            same = a == b and masked(a) == masked(b)
            ok &= same
            rate = " ".join(b[b.index("-b:v"):b.index("-g")])
            lines.append(f"| {label} | {buf or 'unset'} | `{rate}` | `{masked(b)[:16]}…` | {same} |")
    lines += ["", "## The start handler (`_start_linux_locked`), HEAD vs today", "",
              "| target class | identical (argv, level, payload, calls, log) | calls |", "| --- | --- | --- |"]
    for label, target in (("LAN", LAN), ("overlay", OVERLAY)):
        x, y = stub.run_start(head, target), stub.run_start(today, target)
        same = canon(x, target) == canon(y, target)
        ok &= same
        lines.append(f"| {label} | {same} | {len(y['calls'])} |")
    lines += ["", f"**All identical: {ok}.**", ""]
    (HERE / "flag_absent_output.md").write_text("\n".join(lines))
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
