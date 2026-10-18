#!/usr/bin/env python3
"""G8-S4: PSNR / SSIM on the content area only (C5-M3's method: the 879-wide game picture,
pillarboxed in 1280x720 by the companion's pad; the black bars inflate whole-frame numbers).

    PYTHONDONTWRITEBYTECODE=1 python3 -I docs/memory/evidence/g8_s4_2026-10-18/quality_content.py <scratch_dir>

Crop 876x720 at x=202 (inside the 879-wide picture at x=200, even-aligned), one ffmpeg pass per
pair (split -> psnr + ssim). Each encode vs the lossless reference; each profile vs flag absent.
Writes quality_content.json next to this script. ffmpeg on files only.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
REF = REPO / "runtime" / "c5_m3" / "reference.mkv"
CROP = "crop=876:720:202:0"


def pair(a: Path, b: Path) -> dict:
    flt = (f"[0:v]{CROP},split[a1][a2];[1:v]{CROP},split[b1][b2];[a1][b1]psnr;[a2][b2]ssim")
    out = subprocess.run(["/usr/bin/ffmpeg", "-nostdin", "-hide_banner", "-i", str(a), "-i", str(b),
                          "-filter_complex", flt, "-f", "null", "-"], capture_output=True, text=True).stderr
    p = re.search(r"PSNR .*average:([0-9.]+) min:([0-9.]+)", out)
    s = re.search(r"SSIM .*All:([0-9.]+)", out)
    return {"psnr_avg_db": float(p.group(1)) if p else None, "psnr_min_db": float(p.group(2)) if p else None,
            "ssim_all": float(s.group(1)) if s else None}


def main(scratch: Path) -> int:
    res = {}
    for t in (4000, 5000, 7000):
        for prof in ("absent", "tight", "headroom"):
            enc = scratch / f"enc_{t}_{prof}.mkv"
            r = {"vs_reference": pair(enc, REF)}
            if prof != "absent":
                r["vs_absent"] = pair(enc, scratch / f"enc_{t}_absent.mkv")
            res[f"{t}|{prof}"] = r
            print(t, prof, json.dumps(r), flush=True)
    (HERE / "quality_content.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
