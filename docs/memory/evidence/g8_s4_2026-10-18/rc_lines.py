#!/usr/bin/env python3
"""G8-S4: the driver's own rate-control lines for each profile's file argv (encode_proof.py's), 1 s,
at -loglevel verbose, to -f null. The builder's argv runs at -loglevel info, which hides them.

    PYTHONDONTWRITEBYTECODE=1 python3 -I docs/memory/evidence/g8_s4_2026-10-18/rc_lines.py
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import encode_proof as e  # noqa: E402

out = []
for t in e.TARGETS:
    for p in e.PROFILES:
        a = e.to_file(e.build(p, t), Path("/dev/null"))
        a[a.index("-loglevel") + 1] = "verbose"
        k = a.index("-f", a.index("-c:v"))
        a[k:] = ["-frames:v", "60", "-f", "null", "-"]
        log = subprocess.run(a, capture_output=True, text=True).stderr
        for line in log.splitlines():
            if any(s in line for s in ("RC mode", "RC target", "RC buffer", "max frame size")):
                out.append(f"{t}|{p or 'absent'}: {line.split('] ', 1)[-1]}")
(HERE / "rc_lines.txt").write_text("\n".join(out) + "\n")
print("\n".join(out))
