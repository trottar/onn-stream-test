#!/usr/bin/env python3
"""C5-M4 section 3 -- offline quality on the real 1080p source. C5-M3's method (c5_m3_quality.py),
extended to a 1920x1080 reference, temporal alignment between separate captures, and the frame-size
data the link would carry. No companion stream runs at any point.

  c5_m4_offline.py capture <work> <label> <kind> <offset_s> <seconds>
      The attract title is launched through the companion WITHOUT a stream (the caller has set the
      source with c5_m4_source.sh), unpaused through RetroArch's command port, and <offset_s> after the
      unpause x11grab records the window for <seconds> s, lossless (libx264 -qp 0 -preset ultrafast,
      4:2:0), with c5_m4_sampler.py running (RetroArch's frame counter during the capture).
        kind 1080: the 1920x1080 window as is            -> <work>/<label>.mkv (1920x1080)
        kind 720 : today's 879x720 window through the companion's scale/pad to 1280x720 (C5-M3's
                   capture, unchanged)                    -> <work>/<label>.mkv (1280x720)
      Emulation from power-on with zero input is deterministic, so the same <offset_s> after the
      unpause is the same attract segment to within the command's timing; the residual offset is
      found in `score` (align) and reported.
  c5_m4_offline.py encode <work> <ref1080> <ref720_T>
      Each arm through the companion's h264_vaapi argv (native_stream.py _build_linux_ffmpeg_command:
      the same scale/pad/format/hwupload filter at the arm's size, -profile:v high -b:v K -maxrate K
      -bufsize K -max_frame_size CAP -g GOP -bf 0), into Matroska.
  c5_m4_offline.py score <work> <ref1080> <ref720_T> <out_dir> [<ref1080_repeat>]
      Each arm decoded and compared with the 1080p reference AS SHOWN on a 1920x1080 TV: T and S720
      are scaled 1280x720 -> 1920x1080 with a BILINEAR scaler (a stand-in for the onn's compositor,
      as C5-M3); the S1080 arms as they are. ffmpeg ssim (whole frame, and content-only = the 4:3
      picture box found in the reference, pillars excluded) and psnr (content-only). T comes from a
      separate capture: it is aligned in time (the frame lag minimising the mean absolute difference of
      32x24 content signatures) and in space (the integer shift, |dx|,|dy| <= 3, maximising content SSIM
      on every 60th frame). <ref1080_repeat> (a second capture of the same segment at the same scale) is
      scored the same way as a control: its SSIM against the reference is the alignment floor.
      Frame-size data per arm from the encoded packets: IDR bytes p50/p90/max, the per-second largest
      frame p50/p90/max, frames >= 80 RTP packets per minute (1,186 payload bytes per packet: 1,200 minus
      the RTP and FU-A headers), cap hits (seconds whose largest frame >= 95 % of the cap) per minute,
      mean and peak (largest 1 s window) bitrate.
"""
import json, math, os, statistics, subprocess, sys, time, urllib.request

FF, FP = "/usr/bin/ffmpeg", "/usr/bin/ffprobe"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = "/home/privyhub/Projects/onn-stream-test"
TITLE = "game_ps1_b0a5986638f61a11"
ENV = dict(os.environ, DISPLAY=":0")
PKT = 1186
# arm, source, size, kbps, cap, gop
ARMS = [("T", "T", 1280, 720, 7000, 90000, 15), ("S720", "S", 1280, 720, 7000, 90000, 15),
        ("S1080_c3", "S", 1920, 1080, 12600, 90000, 15), ("S1080_par", "S", 1920, 1080, 15750, 90000, 15),
        ("S1080_g30", "S", 1920, 1080, 12600, 90000, 30), ("S1080_cap", "S", 1920, 1080, 12600, 120000, 15)]


def companion_vf(w, h):
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease:flags=fast_bilinear,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black")


def run(argv, log):
    with open(log, "w") as fh:
        return subprocess.run(argv, stdout=fh, stderr=subprocess.STDOUT, text=True).returncode


def http(method, path):
    req = urllib.request.Request("http://localhost:8765" + path, method=method)
    return json.load(urllib.request.urlopen(req, timeout=10))


def ra(port, cmd):
    return subprocess.run(["python3", os.path.join(HERE, "ra_cmd.py"), str(port), cmd], capture_output=True,
                          text=True).stdout.strip()


def capture(work, label, kind, offset, seconds):
    os.makedirs(work, exist_ok=True)
    meta = {"label": label, "kind": kind, "offset_s": offset, "seconds": seconds}
    if http("GET", "/plugins/games/status").get("active"):
        sys.exit("a game is active")
    http("POST", f"/plugins/games/launch?id={TITLE}")
    w = None
    for _ in range(30):
        time.sleep(1)
        r = subprocess.run(["xdotool", "search", "--onlyvisible", "--name", "^RetroArch "], capture_output=True,
                           text=True, env=ENV).stdout.split()
        if r:
            w = r[0]
            break
    time.sleep(4)
    port = open(os.path.join(REPO, "data/games/retroarch/config/privyhub-session.cfg")).read().split(
        'network_cmd_port = "')[1].split('"')[0]
    geo = subprocess.run(["xdotool", "getwindowgeometry", w], capture_output=True, text=True, env=ENV).stdout
    meta["window"] = [t for t in geo.split() if "x" in t and t[0].isdigit()][-1]
    meta["status_before"] = ra(port, "GET_STATUS")
    stop = os.path.join(work, label + ".stop")
    if os.path.exists(stop):
        os.remove(stop)
    smp = subprocess.Popen(["python3", os.path.join(HERE, "c5_m4_sampler.py"), os.path.join(work, label)])
    t_unpause = time.time()
    ra(port, "PAUSE_TOGGLE")
    meta["status_after_unpause"] = ra(port, "GET_STATUS")
    while time.time() < t_unpause + offset:
        time.sleep(0.01)
    vf = "format=yuv420p" if kind == "1080" else companion_vf(1280, 720) + ",format=yuv420p"
    argv = [FF, "-hide_banner", "-nostdin", "-y", "-f", "x11grab", "-framerate", "60", "-window_id", w, "-i", ":0",
            "-t", str(seconds), "-vf", vf, "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            os.path.join(work, label + ".mkv")]
    meta["capture_started_after_unpause_s"] = round(time.time() - t_unpause, 3)
    meta["capture_rc"] = run(argv, os.path.join(work, label + "_capture_ffmpeg.log"))
    meta["argv"] = argv
    open(stop, "w").close()
    smp.wait()
    os.remove(stop)
    meta["status_end"] = ra(port, "GET_STATUS")
    ra(port, "PAUSE_TOGGLE")
    meta["status_after_pause"] = ra(port, "GET_STATUS")
    http("POST", "/plugins/games/stop")
    for _ in range(20):
        time.sleep(1)
        if not http("GET", "/plugins/games/status").get("active"):
            break
    json.dump(meta, open(os.path.join(work, label + "_meta.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in meta.items() if k != "argv"}))


def encode(work, ref1080, ref720):
    for arm, src, w, h, kbps, cap, gop in ARMS:
        ref = os.path.join(work, ref720 if src == "T" else ref1080)
        argv = [FF, "-hide_banner", "-nostdin", "-y", "-vaapi_device", "/dev/dri/renderD128", "-i", ref,
                "-vf", companion_vf(w, h) + ",format=nv12,hwupload", "-an", "-c:v", "h264_vaapi", "-profile:v", "high",
                "-b:v", f"{kbps}k", "-maxrate", f"{kbps}k", "-bufsize", f"{kbps}k", "-max_frame_size", str(cap),
                "-g", str(gop), "-bf", "0", os.path.join(work, f"enc_{arm}.mkv")]
        rc = run(argv, os.path.join(work, f"enc_{arm}_ffmpeg.log"))
        print(json.dumps({"arm": arm, "rc": rc, "argv": argv}))


def gray_sig(path, pre, box):
    """32x24 gray signature of the content box, one 768-byte record per frame."""
    x, y, bw, bh = box
    vf = (pre + "," if pre else "") + f"crop={bw}:{bh}:{x}:{y},scale=32:24:flags=area,format=gray"
    out = subprocess.run([FF, "-v", "error", "-nostdin", "-i", path, "-vf", vf, "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    return [out[i:i + 768] for i in range(0, len(out) - 767, 768)]


def lag_of(sig_ref, sig_x, max_lag=1800):
    """x[i] ~ ref[i + lag]. Coarse: the per-frame mean of the signature over every lag within +-max_lag
    frames (C5-M3's capture start after the unpause is not recorded); fine: the full 32x24 signatures
    over +-15 frames around the coarse best. Returns (lag, mean absolute difference per pixel)."""
    mr = [sum(f) / 768 for f in sig_ref]
    mx = [sum(f) / 768 for f in sig_x]
    best = None
    for lag in range(-max_lag, max_lag + 1):
        idx = [i for i in range(0, len(mx), 2) if 0 <= i + lag < len(mr)]
        if len(idx) < 600:
            continue
        d = statistics.fmean(abs(mx[i] - mr[i + lag]) for i in idx)
        if best is None or d < best[1]:
            best = (lag, d)
    coarse = best[0]
    best = None
    for lag in range(coarse - 15, coarse + 16):
        pairs = [(i, i + lag) for i in range(0, len(sig_x), 8) if 0 <= i + lag < len(sig_ref)]
        if len(pairs) < 75:
            continue
        mad = statistics.fmean(sum(abs(a - b) for a, b in zip(sig_x[i], sig_ref[j])) / 768 for i, j in pairs)
        if best is None or mad < best[1]:
            best = (lag, mad)
    return best


def content_box(path):
    """The picture box of the reference: the per-pixel maximum over every 60th frame (lagfun, no decay)."""
    W, H = 1920, 1080
    out = subprocess.run([FF, "-v", "error", "-nostdin", "-i", path, "-vf",
                          "select='not(mod(n,60))',format=gray,lagfun=decay=1", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    out = out[-W * H:]
    cols = [max(out[r * W + c] for r in range(0, H, 4)) for c in range(W)]
    rows = [max(out[r * W + c] for c in range(0, W, 4)) for r in range(H)]
    xs = [c for c in range(W) if cols[c] > 24]
    ys = [r for r in range(H) if rows[r] > 24]
    x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
    return [x0, y0, (x1 - x0 + 1) // 2 * 2, (y1 - y0 + 1) // 2 * 2]


def chain(lag_trim, up):
    t = f"trim=start_frame={lag_trim}," if lag_trim > 0 else ""
    return f"{t}setpts=N/60/TB,{up}format=yuv420p"


def sample_clip(work, path, shown, trim, tag):
    """Every 60th frame (after the alignment trim, as shown) to a small lossless clip, for the shift search."""
    out = os.path.join(work, f"sample_{tag}.mkv")
    up = "scale=1920:1080:flags=bilinear," if shown else ""
    run([FF, "-hide_banner", "-nostdin", "-y", "-i", path, "-vf", chain(trim, up) + ",select='not(mod(n,60))',setpts=N/60/TB",
         "-c:v", "libx264", "-qp", "0", "-preset", "ultrafast", out], os.path.join(work, f"sample_{tag}_ffmpeg.log"))
    return out


def ssim_mean(work, a, b, box, shift, tag):
    x, y, bw, bh = box
    dx, dy = shift
    st = os.path.join(work, f"ssim_{tag}.txt")
    run([FF, "-hide_banner", "-nostdin", "-i", a, "-i", b, "-lavfi",
         f"[0:v]crop={bw}:{bh}:{x + dx}:{y + dy}[d];[1:v]crop={bw}:{bh}:{x}:{y}[r];[d][r]ssim=stats_file={st}:shortest=1",
         "-f", "null", "-"], os.path.join(work, f"ssim_{tag}_ffmpeg.log"))
    s = ssim_series(st)
    return statistics.fmean(s) if s else 0.0


def ssim_series(stats):
    out = []
    for line in open(stats):
        kv = dict(t.split(":", 1) for t in line.split() if ":" in t)
        out.append(float(kv["All"]))
    return out


def psnr_series(stats):
    out = []
    for line in open(stats):
        kv = dict(t.split(":", 1) for t in line.split() if ":" in t)
        v = kv.get("psnr_avg", "inf")
        out.append(100.0 if v == "inf" else min(100.0, float(v)))
    return out


def compare(work, dec, ref, shown, box, lag, shift, tag):
    """ssim whole + ssim content + psnr content of `dec` (as shown) against `ref`; frames paired by index
    (setpts=N/60/TB on both) after the alignment trim. lag: dec[i] ~ ref[i + lag]."""
    x, y, bw, bh = box
    dx, dy = shift
    up = "scale=1920:1080:flags=bilinear," if shown else ""
    sf = {k: os.path.join(work, f"{k}_{tag}.txt") for k in ("ssim_full", "ssim_content", "psnr_content")}
    lav = (f"[0:v]{chain(max(0, -lag), up)},split=2[d0][d1];[1:v]{chain(max(0, lag), '')},split=2[r0][r1];"
           f"[d0][r0]ssim=stats_file={sf['ssim_full']}:shortest=1[o0];[o0]nullsink;"
           f"[d1]crop={bw}:{bh}:{x + dx}:{y + dy},split=2[dc0][dc1];[r1]crop={bw}:{bh}:{x}:{y},split=2[rc0][rc1];"
           f"[dc0][rc0]ssim=stats_file={sf['ssim_content']}:shortest=1[o1];[o1]nullsink;"
           f"[dc1][rc1]psnr=stats_file={sf['psnr_content']}:shortest=1")
    rc = run([FF, "-hide_banner", "-nostdin", "-i", dec, "-i", ref, "-lavfi", lav, "-f", "null", "-"],
             os.path.join(work, f"cmp_{tag}_ffmpeg.log"))
    return rc, ssim_series(sf["ssim_full"]), ssim_series(sf["ssim_content"]), psnr_series(sf["psnr_content"])


def packets(path):
    out = subprocess.run([FP, "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=size,flags",
                          "-of", "json", path], capture_output=True, text=True).stdout
    return [(int(p["size"]), "K" in p.get("flags", "")) for p in json.loads(out)["packets"]]


def q(a, p):
    a = sorted(a)
    return a[min(len(a) - 1, int(round(p * (len(a) - 1))))] if a else None


def gop_share(s, idr, gop):
    n = len(s)
    m = statistics.fmean(s)
    d = [v - m for v in s]
    var = sum(v * v for v in d) / n if n else 0.0
    k = round(n * (60 / gop) / 60)
    re_ = sum(v * math.cos(2 * math.pi * k * i / n) for i, v in enumerate(d))
    im_ = sum(v * math.sin(2 * math.pi * k * i / n) for i, v in enumerate(d))
    p_f = 2 * (re_ * re_ + im_ * im_) / (n * n)
    off = idr[1] % gop if len(idr) > 1 else 0
    ph = [[] for _ in range(gop)]
    for i, v in enumerate(d):
        ph[(i - off) % gop].append(v)
    fold = statistics.pvariance([statistics.fmean(p) for p in ph if p]) / var if var else 0.0
    return (round(p_f / var, 4) if var else None), round(fold, 4)


def frame_sizes(pk, cap, seconds_per_min=60):
    sizes = [p[0] for p in pk]
    idr = sorted(p[0] for p in pk if p[1])
    n = len(sizes)
    mins = n / 60 / 60
    per_s = [max(sizes[i:i + 60]) for i in range(0, n - 59, 60)]
    sums = [sum(sizes[i:i + 60]) * 8 / 1000 for i in range(0, n - 59, 60)]
    return {"idr_p50_p90_max": [q(idr, .5), q(idr, .9), idr[-1] if idr else None],
            "sec_max_p50_p90_max": [q(per_s, .5), q(per_s, .9), max(per_s) if per_s else None],
            "ge80_pkts_per_min": round(sum(1 for s in sizes if math.ceil(s / PKT) >= 80) / mins, 1),
            "max_pkts": math.ceil(max(sizes) / PKT),
            "cap_hit_s_per_min": round(sum(1 for m in per_s if m >= 0.95 * cap) / mins, 1),
            "mean_kbps": round(8 * sum(sizes) / (n / 60) / 1000), "peak_1s_kbps": round(max(sums)) if sums else None}


def score(work, ref1080, ref720, out_dir, repeat=None):
    os.makedirs(out_dir, exist_ok=True)
    R = os.path.join(work, ref1080)
    box = content_box(R)
    res = {"content_box_xywh": box}
    sig_ref = gray_sig(R, "", box)
    rows = []
    jobs = [(a[0], os.path.join(work, f"enc_{a[0]}.mkv"), a[2] == 1280, a) for a in ARMS]
    if repeat:
        jobs.append(("repeat", os.path.join(work, repeat), False, ("repeat", "S", 1920, 1080, 0, 0, 15)))
    for arm, path, shown, a in jobs:
        lag, shift, mad = 0, (0, 0), None
        if arm in ("T", "repeat"):
            sig = gray_sig(path, "scale=1920:1080:flags=bilinear" if shown else "", box)
            lag, mad = lag_of(sig_ref, sig)
            sa = sample_clip(work, path, shown, max(0, -lag), arm)
            sr = sample_clip(work, R, False, max(0, lag), arm + "_ref")
            best = None
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    v = ssim_mean(work, sa, sr, box, (dx, dy), f"{arm}_shift")
                    if best is None or v > best[1]:
                        best = ((dx, dy), v)
            shift = best[0]
        rc, sf, sc, pc = compare(work, path, R, shown, box, lag, shift, arm)
        n = len(sc)
        row = {"arm": arm, "size": f"{a[2]}x{a[3]}", "kbps": a[4], "cap": a[5], "gop": a[6], "shown": "bilinear x1.5" if shown else "as is",
               "lag_frames": lag, "shift_px": list(shift), "align_mad": round(mad, 2) if mad is not None else None,
               "frames": n, "ssim_full": round(statistics.fmean(sf), 5), "ssim_content": round(statistics.fmean(sc), 5),
               "ssim_content_p5": round(q(sc, .05), 5), "psnr_content_db": round(statistics.fmean(pc), 2), "cmp_rc": rc}
        if arm != "repeat":
            pk = packets(path)
            idr = [i for i, p in enumerate(pk) if p[1]]
            idr_c = [i - (max(0, -lag)) for i in idr if 0 <= i - max(0, -lag) < n]
            pulse = [abs(sc[i] - sc[i - 1]) for i in idr_c if i > 0]
            row["idr_pulse"] = round(statistics.fmean(pulse), 5) if pulse else None
            row["share_4hz_bin"], row["share_gop_fold"] = gop_share(sc, idr_c, 15)
            if a[6] != 15:
                row["share_own_gop_bin"], row["share_own_gop_fold"] = gop_share(sc, idr_c, a[6])
            row.update(frame_sizes(pk, a[5]))
        row["series_ssim_content"] = [round(v, 5) for v in sc]
        rows.append(row)
        print(json.dumps({k: v for k, v in row.items() if not k.startswith("series")}))
    res["arms"] = rows
    json.dump(res, open(os.path.join(out_dir, "offline_quality.json"), "w"), indent=1)
    F = lambda v: "-" if v is None else str(v)
    lines = [f"C5-M4 offline table -- reference {ref1080}, T from {ref720}; content box {box} (x, y, w, h)", "",
             f"{'arm':<10} {'size':>9} {'kbps':>6} {'cap':>7} {'GOP':>3} {'shown':>13} {'lag':>4} {'shift':>7} "
             f"{'SSIM full':>9} {'SSIM cont':>9} {'p5 cont':>8} {'PSNR c':>7} {'IDR pulse':>9} {'4Hz bin':>7} {'GOP fold':>8}"]
    for r in rows:
        lines.append(f"{r['arm']:<10} {r['size']:>9} {r['kbps']:>6} {r['cap']:>7} {r['gop']:>3} {r['shown']:>13} "
                     f"{r['lag_frames']:>4} {str(r['shift_px']):>7} {r['ssim_full']:>9} {r['ssim_content']:>9} "
                     f"{r['ssim_content_p5']:>8} {r['psnr_content_db']:>7} {F(r.get('idr_pulse')):>9} "
                     f"{F(r.get('share_4hz_bin')):>7} {F(r.get('share_gop_fold')):>8}")
    lines += ["", "frame-size data (what the link would carry)",
              f"{'arm':<10} {'IDR B p50/p90/max':>24} {'1s-max B p50/p90/max':>24} {'>=80pkt/min':>11} {'max pkts':>8} "
              f"{'cap s/min':>9} {'mean kbps':>9} {'peak 1s':>8}"]
    for r in rows:
        if "mean_kbps" not in r:
            continue
        lines.append(f"{r['arm']:<10} {'/'.join(map(F, r['idr_p50_p90_max'])):>24} {'/'.join(map(F, r['sec_max_p50_p90_max'])):>24} "
                     f"{r['ge80_pkts_per_min']:>11} {r['max_pkts']:>8} {r['cap_hit_s_per_min']:>9} {r['mean_kbps']:>9} "
                     f"{F(r['peak_1s_kbps']):>8}")
    text = "\n".join(lines) + "\n"
    open(os.path.join(out_dir, "offline_table.txt"), "w").write(text)
    print(text)


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "capture":
        capture(sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5]), float(sys.argv[6]))
    elif c == "encode":
        encode(sys.argv[2], sys.argv[3], sys.argv[4])
    elif c == "score":
        score(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6] if len(sys.argv) > 6 else None)
