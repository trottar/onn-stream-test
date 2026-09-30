#!/usr/bin/env python3
"""C5-M3 section 1: offline objective quality, before any hold. Read-only on
the stream (no companion stream runs; the attract title is launched through
the companion without one and unpaused through RetroArch's command port, as
C5-M1's offline step did).

  c5_m3_quality.py capture <window_id> <work_dir> [seconds=60]
  c5_m3_quality.py encode  <work_dir>
  c5_m3_quality.py score   <work_dir> <out_dir>

capture: a lossless reference of the RetroArch window through the same
  x11grab source and the same scale/pad the companion's argv applies
  (1280x720, fast_bilinear, pad), to 4:2:0 (the encoder's nv12 input is
  4:2:0) with libx264 -qp 0 -preset ultrafast (lossless). ffmpeg's dup/drop
  counts are kept: a realtime capture should drop nothing.
encode: the reference through the companion's h264_vaapi argv (native_stream.py
  _build_linux_ffmpeg_command: -profile:v high -b:v K -maxrate K -bufsize K
  -max_frame_size 90000 -g 15 -bf 0) at 7000, 6000, 5500, 5000, 4000, 3000
  (1280x720) and 3500 (960x540: the reference scaled with the companion's own
  scaler flags, fast_bilinear). Into Matroska, so frame timing is kept.
score: each encode decoded and compared frame by frame with the reference
  (ffmpeg ssim and psnr, stats files). The 540p encode is scaled back to
  1280x720 with a BILINEAR scaler first (flags=bilinear -- a stand-in for the
  TV's upscale; the onn's own scaler is not measurable from here).
  Per arm: mean SSIM (All), p5 SSIM, mean PSNR (psnr_avg; an identical frame's
  inf is capped at 100 dB), the IDR pulse -- mean |SSIM(IDR) - SSIM(frame
  before)| over every GOP boundary -- and the 4 Hz share of the SSIM series'
  variance two ways: the periodogram bin at 4 Hz (60 fps / 15) and the
  GOP-phase fold (the variance of the 15 phase means over the total, i.e.
  every harmonic of 4 Hz); and the encoded IDR size p50/p90/max, frames and
  IDRs at >= 95 % of the 90,000-byte cap.
"""
import json
import math
import os
import statistics
import subprocess
import sys

FF = "/usr/bin/ffmpeg"
FP = "/usr/bin/ffprobe"
ARMS = [("720p_7000", 1280, 720, 7000), ("720p_6000", 1280, 720, 6000), ("720p_5500", 1280, 720, 5500),
        ("720p_5000", 1280, 720, 5000), ("720p_4000", 1280, 720, 4000), ("720p_3000", 1280, 720, 3000),
        ("540p_3500", 960, 540, 3500)]
CAP = 90_000
GOP = 15


def run(argv, log):
    with open(log, "w") as fh:
        p = subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT, text=True)
    return p.returncode


def capture(wid, work, seconds):
    os.makedirs(work, exist_ok=True)
    vf = ("scale=1280:720:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
          "pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,format=yuv420p")
    argv = [FF, "-hide_banner", "-nostdin", "-y", "-f", "x11grab", "-framerate", "60", "-window_id", str(wid),
            "-i", ":0", "-t", str(seconds), "-vf", vf, "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast",
            "-pix_fmt", "yuv420p", os.path.join(work, "reference.mkv")]
    rc = run(argv, os.path.join(work, "capture_ffmpeg.log"))
    print(json.dumps({"capture_rc": rc, "argv": argv}))


def encode(work):
    ref = os.path.join(work, "reference.mkv")
    for label, w, h, kbps in ARMS:
        pre = (f"scale={w}:{h}:flags=fast_bilinear," if (w, h) != (1280, 720) else "")
        argv = [FF, "-hide_banner", "-nostdin", "-y", "-vaapi_device", "/dev/dri/renderD128", "-i", ref,
                "-vf", pre + "format=nv12,hwupload", "-an", "-c:v", "h264_vaapi", "-profile:v", "high",
                "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{kbps}k", "-max_frame_size", str(CAP),
                "-g", str(GOP), "-bf", "0", os.path.join(work, f"enc_{label}.mkv")]
        rc = run(argv, os.path.join(work, f"enc_{label}_ffmpeg.log"))
        print(json.dumps({"label": label, "rc": rc, "argv": argv}))


def frames_info(path):
    out = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=size,flags",
                          "-of", "json", path], capture_output=True, text=True).stdout
    return [(int(p["size"]), "K" in p.get("flags", "")) for p in json.loads(out)["packets"]]


def stats(work, label, w, h):
    enc = os.path.join(work, f"enc_{label}.mkv")
    ref = os.path.join(work, "reference.mkv")
    up = "scale=1280:720:flags=bilinear," if (w, h) != (1280, 720) else ""
    res = {}
    for kind in ("ssim", "psnr"):
        sf = os.path.join(work, f"{kind}_{label}.txt")
        lav = f"[0:v]{up}format=yuv420p[d];[1:v]format=yuv420p[r];[d][r]{kind}=stats_file={sf}"
        rc = run([FF, "-hide_banner", "-nostdin", "-i", enc, "-i", ref, "-lavfi", lav, "-f", "null", "-"],
                 os.path.join(work, f"{kind}_{label}_ffmpeg.log"))
        res[kind] = (rc, sf)
    ssim = []
    for line in open(res["ssim"][1]):
        kv = dict(t.split(":", 1) for t in line.split() if ":" in t)
        ssim.append(float(kv["All"]))
    psnr = []
    for line in open(res["psnr"][1]):
        kv = dict(t.split(":", 1) for t in line.split() if ":" in t)
        v = kv.get("psnr_avg", "inf")
        psnr.append(100.0 if v == "inf" else min(100.0, float(v)))
    return ssim, psnr


def score(work, out_dir):
    rows = []
    for label, w, h, kbps in ARMS:
        ssim, psnr = stats(work, label, w, h)
        pk = frames_info(os.path.join(work, f"enc_{label}.mkv"))
        n = min(len(ssim), len(pk))
        idr = [i for i in range(n) if pk[i][1]]
        pulse = [abs(ssim[i] - ssim[i - 1]) for i in idr if i > 0]
        s = [x - statistics.fmean(ssim[:n]) for x in ssim[:n]]
        var = sum(x * x for x in s) / len(s) if s else 0.0
        # periodogram at 4 Hz: the DFT bin k = n * 4 / 60
        k = round(n * 4 / 60)
        re = sum(x * math.cos(2 * math.pi * k * i / n) for i, x in enumerate(s))
        im = sum(x * math.sin(2 * math.pi * k * i / n) for i, x in enumerate(s))
        p4 = 2 * (re * re + im * im) / (n * n)          # the variance a sinusoid at bin k carries
        # GOP-phase fold (phase 0 = the IDR's position in its GOP)
        off = idr[1] % GOP if len(idr) > 1 else 0
        ph = [[] for _ in range(GOP)]
        for i, x in enumerate(s):
            ph[(i - off) % GOP].append(x)
        pm = [statistics.fmean(p) for p in ph if p]
        fold = statistics.pvariance(pm) / var if var else 0.0
        sizes_idr = sorted(pk[i][0] for i in idr)
        sizes_all = [p[0] for p in pk]
        q = lambda a, p: a[min(len(a) - 1, int(round(p * (len(a) - 1))))] if a else None
        ssim_sorted = sorted(ssim[:n])
        row = {"arm": label, "size": f"{w}x{h}", "kbps": kbps, "frames": n, "idr_frames": len(idr),
               "gop_spacing": sorted(set(b - a for a, b in zip(idr, idr[1:]))),
               "ssim_mean": round(statistics.fmean(ssim[:n]), 5), "ssim_p5": round(q(ssim_sorted, 0.05), 5),
               "psnr_mean_db": round(statistics.fmean(psnr[:n]), 2),
               "idr_pulse_mean_abs_dssim": round(statistics.fmean(pulse), 5) if pulse else None,
               "share_4hz_bin": round(p4 / var, 4) if var else None, "share_gop_fold": round(fold, 4),
               "idr_bytes_p50_p90_max": [q(sizes_idr, .5), q(sizes_idr, .9), sizes_idr[-1] if sizes_idr else None],
               "frames_ge_95pct_cap": sum(1 for x in sizes_all if x >= 0.95 * CAP),
               "idr_ge_95pct_cap": sum(1 for x in sizes_idr if x >= 0.95 * CAP),
               "encoded_kbps": round(8 * sum(sizes_all) / (n / 60) / 1000) if n else None,
               "ssim_rc": 0, "series_ssim": [round(x, 5) for x in ssim[:n]]}
        rows.append(row)
    os.makedirs(out_dir, exist_ok=True)
    json.dump(rows, open(os.path.join(out_dir, "quality.json"), "w"), indent=1)
    hdr = (f"{'arm':<10} {'size':>8} {'kbps':>5} {'enc kbps':>8} {'SSIM':>8} {'p5 SSIM':>8} {'PSNR dB':>7} "
           f"{'IDR pulse':>9} {'4Hz bin':>7} {'GOP fold':>8} {'IDR B p50/p90/max':>22} {'>=95%cap f/IDR':>14}")
    lines = [hdr]
    for r in rows:
        i = r["idr_bytes_p50_p90_max"]
        lines.append(f"{r['arm']:<10} {r['size']:>8} {r['kbps']:>5} {r['encoded_kbps']:>8} {r['ssim_mean']:>8} "
                     f"{r['ssim_p5']:>8} {r['psnr_mean_db']:>7} {r['idr_pulse_mean_abs_dssim']:>9} "
                     f"{r['share_4hz_bin']:>7} {r['share_gop_fold']:>8} {str(i[0]) + '/' + str(i[1]) + '/' + str(i[2]):>22} "
                     f"{str(r['frames_ge_95pct_cap']) + '/' + str(r['idr_ge_95pct_cap']):>14}")
    text = "\n".join(lines) + "\n"
    open(os.path.join(out_dir, "quality_table.txt"), "w").write(text)
    print(text)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "capture":
        capture(sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 60)
    elif cmd == "encode":
        encode(sys.argv[2])
    elif cmd == "score":
        score(sys.argv[2], sys.argv[3])
