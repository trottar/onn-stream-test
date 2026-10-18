#!/usr/bin/env python3
"""G8-S4: the rate profiles proved offline on the host's VAAPI encoder, on a file. No stream.

    PYTHONDONTWRITEBYTECODE=1 python3 -I docs/memory/evidence/g8_s4_2026-10-18/encode_proof.py <scratch_dir>

1. The commands: the companion's own `_build_linux_ffmpeg_command` on G8-S2's stub manager
   (the adopted profile, the 90,000-B cap), flag absent / tight / headroom, targets 4000 /
   5000 / 7000; each hashed with the window, display, device and ffmpeg path masked.
2. The only edits: the x11grab input -> `-i <reference.mkv>`, the RTP sink -> `-f matroska
   <scratch file>`. ffmpeg runs on files only (the render node for the encoder).
3. Per encode: the per-second output (ffprobe packets by pts), the largest frame, ffmpeg's CPU
   (user + sys of the child) against a decode-only baseline; the driver's RC lines.
4. PSNR / SSIM of each encode against the lossless reference, and of each profile against the
   flag-absent encode at the same target.
Writes encode_proof.json, encode_tables.md, rc_lines.txt next to this script; the encodes stay
in <scratch_dir> (hashes recorded).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import resource
import statistics
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "companion"))
sys.path.insert(0, str(REPO / "tests" / "start_rung"))

import encoder_rc as erc  # noqa: E402
import native_stream as ns  # noqa: E402
import stub_manager as stub  # noqa: E402

REF = REPO / "runtime" / "c5_m3" / "reference.mkv"
DEVICE = "/dev/dri/renderD128"
FFMPEG = "/usr/bin/ffmpeg"
FFPROBE = "/usr/bin/ffprobe"
TARGETS = (4000, 5000, 7000)
PROFILES = (None, "tight", "headroom")
WINDOW = 4242
FIXTURE_DEVICE = "/fixture/renderD128"


def build(profile: str | None, target: int) -> list[str]:
    m = stub.stub_manager(ns, [])
    saved = ns.ENCODER_RC
    ns.ENCODER_RC = erc.EncoderRc(profile, log=lambda s: None, environ={}) if profile else None
    try:
        kw = {} if target == m.BITRATE_KBPS else {"bitrate_kbps": target, "max_bitrate_kbps": target}
        return m._build_linux_ffmpeg_command(ffmpeg=Path("/fixture/ffmpeg"), capture_target={"_window_id": WINDOW},
                                             **kw)
    finally:
        ns.ENCODER_RC = saved


def masked_hash(argv: list[str]) -> str:
    text = "\x00".join(argv).replace(str(WINDOW), "<window>").replace(":0", "<display>")
    text = text.replace(FIXTURE_DEVICE, "<device>").replace("/fixture/ffmpeg", "<ffmpeg>")
    text = re.sub(r"rtp://[^\x00]*", "<sink>", text)
    return hashlib.sha256(text.encode()).hexdigest()


def to_file(argv: list[str], out: Path) -> list[str]:
    a = list(argv)
    i = a.index("-f")
    assert a[i + 1] == "x11grab"
    j = a.index("-i", i)
    a[i:j + 2] = ["-i", str(REF)]
    k = a.index("-payload_type")
    a[k:] = ["-f", "matroska", str(out)]
    a[0] = FFMPEG
    a = [DEVICE if x == FIXTURE_DEVICE else x for x in a]
    a[1:1] = ["-y"]
    return a


def run(argv: list[str], log: Path) -> dict:
    r0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    t0 = time.monotonic()
    with log.open("w") as fh:
        rc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT).returncode
    wall = time.monotonic() - t0
    r1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {"rc": rc, "wall_s": round(wall, 2), "cpu_user_s": round(r1.ru_utime - r0.ru_utime, 2),
            "cpu_sys_s": round(r1.ru_stime - r0.ru_stime, 2)}


def packets(path: Path) -> list[tuple[float, int, bool]]:
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "packet=pts_time,size,flags", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    rows = []
    for line in out.splitlines():
        parts = line.split(",")
        if len(parts) >= 3 and parts[0] not in ("", "N/A"):
            rows.append((float(parts[0]), int(parts[1]), "K" in parts[2]))
    rows.sort()
    return rows


def per_second(rows, target: int) -> dict:
    bins: dict[int, int] = {}
    for t, size, _ in rows:
        bins[int(t)] = bins.get(int(t), 0) + size
    secs = sorted(s for s in bins if 0 <= s < 60)
    kb = [bins[s] * 8 / 1000 for s in secs]
    srt = sorted(kb)
    p95 = srt[min(len(srt) - 1, int(round(0.95 * (len(srt) - 1))))]
    return {"seconds": len(kb), "mean": round(statistics.fmean(kb), 1), "median": round(statistics.median(kb), 1),
            "p95": round(p95, 1), "max": round(max(kb), 1), "min": round(min(kb), 1),
            "share_over_target": round(sum(1 for x in kb if x > target) / len(kb), 4),
            "share_over_1_10": round(sum(1 for x in kb if x > 1.10 * target) / len(kb), 4),
            "p95_over_mean": round(p95 / statistics.fmean(kb), 3),
            "max_over_mean": round(max(kb) / statistics.fmean(kb), 3),
            "largest_frame_bytes": max(s for _, s, _ in rows), "frames": len(rows),
            "keyframes": sum(1 for *_, k in rows if k)}


def quality(a: Path, b: Path, log: Path) -> dict:
    res = {}                                   # one pass per filter
    for name, flt in (("psnr", "[0:v][1:v]psnr"), ("ssim", "[0:v][1:v]ssim")):
        argv = [FFMPEG, "-nostdin", "-hide_banner", "-i", str(a), "-i", str(b), "-lavfi", flt, "-f", "null", "-"]
        out = subprocess.run(argv, capture_output=True, text=True).stderr
        with log.open("a") as fh:
            fh.write("\n".join(l for l in out.splitlines() if "Parsed_" in l) + "\n")
        if name == "psnr":
            m = re.search(r"average:([0-9.inf]+)", out)
            res["psnr_avg_db"] = float(m.group(1)) if m and m.group(1) != "inf" else None
            m = re.search(r"min:([0-9.inf]+)", out)
            res["psnr_min_db"] = float(m.group(1)) if m and m.group(1) != "inf" else None
        else:
            m = re.search(r"All:([0-9.]+)", out)
            res["ssim_all"] = float(m.group(1)) if m else None
    return res


def main(scratch: Path) -> int:
    scratch.mkdir(parents=True, exist_ok=True)
    env_absent = all(not k.startswith("PRIVYHUB_") for k in os.environ)
    report: dict = {"env_absent": env_absent, "ns_ENCODER_RC": repr(ns.ENCODER_RC),
                    "reference": {"path": "runtime/c5_m3/reference.mkv",
                                  "sha256": hashlib.sha256(REF.read_bytes()).hexdigest()},
                    "commands": {}, "encodes": {}, "quality": {}, "baseline": None}
    rc_lines: list[str] = []
    # decode-only baseline: the same input and filter without hwupload or encode
    vf = build(None, 5000)[build(None, 5000).index("-vf") + 1].replace(",hwupload", "")
    base = run([FFMPEG, "-y", "-nostdin", "-hide_banner", "-i", str(REF), "-vf", vf, "-an", "-f", "null", "-"],
               scratch / "baseline_decode.log")
    report["baseline"] = base
    for target in TARGETS:
        for profile in PROFILES:
            key = f"{target}|{profile or 'absent'}"
            argv = build(profile, target)
            out = scratch / f"enc_{target}_{profile or 'absent'}.mkv"
            fargv = to_file(argv, out)
            report["commands"][key] = {
                "built_masked_sha256": masked_hash(argv),
                "rate_args": argv[argv.index("-b:v"):argv.index("-g")],
                "file_argv_masked": [("<reference>" if x == str(REF) else "<out>" if x == str(out) else x)
                                     for x in fargv]}
            log = scratch / f"enc_{target}_{profile or 'absent'}.log"
            r = run(fargv, log)
            for line in log.read_text(errors="replace").splitlines():
                if "RC mode" in line or "RC target" in line or "RC buffer" in line or "max frame size" in line:
                    rc_lines.append(f"{key}: {line.split('] ', 1)[-1]}")
            rows = packets(out)
            r.update(per_second(rows, target))
            r["sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
            r["cpu_s"] = round(r["cpu_user_s"] + r["cpu_sys_s"], 2)
            r["cpu_over_baseline_s"] = round(r["cpu_s"] - base["cpu_user_s"] - base["cpu_sys_s"], 2)
            report["encodes"][key] = r
            (scratch / f"frames_{target}_{profile or 'absent'}.json").write_text(
                json.dumps([[round(t, 6), s] for t, s, _ in rows]))
            print(key, json.dumps({k: r[k] for k in ("rc", "mean", "p95", "max", "share_over_target",
                                                       "share_over_1_10", "cpu_s")}), flush=True)
    for target in TARGETS:
        for profile in PROFILES:
            enc = scratch / f"enc_{target}_{profile or 'absent'}.mkv"
            q = {"vs_reference": quality(enc, REF, scratch / "quality.log")}
            if profile:
                q["vs_absent"] = quality(enc, scratch / f"enc_{target}_absent.mkv", scratch / "quality.log")
            report["quality"][f"{target}|{profile or 'absent'}"] = q
            print("quality", target, profile, json.dumps(q), flush=True)
    (HERE / "rc_lines.txt").write_text("\n".join(rc_lines) + "\n")
    (HERE / "encode_proof.json").write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
