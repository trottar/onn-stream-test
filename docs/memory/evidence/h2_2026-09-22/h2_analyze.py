#!/usr/bin/env python3
"""H2 check 3: the headless session against the monitor-attached references.

Primary reference: B2 O1-O6 (host on the Opal, monitor attached, uncapped).
Secondary: D-BASE-P6a V1 and D-BASE-S3 (same path, monitor attached, with the
adopted 90,000-byte cap -- the configuration H2 runs). Metric formulas are
B2's (b2_analyze.metrics), imported unchanged.
"""
import contextlib, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(EV, "b2_2026-09-21"))
with contextlib.redirect_stdout(io.StringIO()):  # b2_analyze prints its own report on import
    from b2_analyze import metrics  # noqa: E402

SESS = "/home/privyhub/Projects/onn-stream-test/logs/games/decoder_sessions"
B2 = [(l.split()[0], os.path.join(SESS, l.split()[2]))
      for l in open(os.path.join(EV, "b2_2026-09-21/index.txt")) if " clean " in l]
CAPPED = [("P6a-V1", os.path.join(EV, "d_base_p6a_2026-09-22/report_V1.json")),
          ("S3", os.path.join(SESS, "native_decoder_20260922_093808_689.json"))]
H2 = []
for line in open(os.path.join(HERE, "h2_index.txt")):
    p = line.split()
    if len(p) >= 3 and p[2] == "completed":
        H2.append((p[0], os.path.join(HERE, p[0], p[1])))

COLS = ["dur_s", "lost", "loss_min", "fge", "max_fwd_gap", "max_gap_ms",
        "spike20_min", "stale_min", "fps", "a_lost", "a_under"]


def row(lab, path):
    m = metrics(path)
    return lab + "  " + "  ".join(
        f"{c}={m[c]:.2f}" if isinstance(m[c], float) else f"{c}={m[c]}" for c in COLS), m


print("== per session ==")
ref = {}
for group, items in (("B2", B2), ("CAPPED", CAPPED), ("H2", H2)):
    for lab, path in items:
        if not os.path.exists(path):
            print(lab, "MISSING", path); continue
        line, m = row(lab, path)
        ref.setdefault(group, []).append(m)
        print(f"[{group}] {line}")

print("\n== B2 range vs H2 ==")
for c in ("fps", "spike20_min", "max_gap_ms", "loss_min", "stale_min"):
    b = [m[c] for m in ref["B2"]]
    for m in ref.get("H2", []):
        v = m[c]
        print(f"{c}: B2 {min(b):.2f}..{max(b):.2f}  H2 {v:.2f}  "
              f"{'within' if min(b) <= v <= max(b) else ('below' if v < min(b) else 'above')}")

print("\n== identity fields ==")
for lab, path in B2[-1:] + CAPPED + H2:
    if not os.path.exists(path):
        continue
    d = json.load(open(path))
    r = d["report"]
    print(lab, "| capture:", repr(r.get("capture_description")),
          "| backend:", r.get("capture_backend"),
          "| gop:", r.get("encoder_gop_frames"), "| kbps:", r.get("encoder_bitrate_kbps"),
          "| thermal.status_samples:", r.get("thermal", {}).get("status_samples"),
          "| host_thermal_c:", d.get("host", {}).get("host_thermal_c"))

for lab, _ in H2:
    s = json.load(open(os.path.join(HERE, lab, "native_stream_status_mid.json")))
    eo = s.get("encoder_overrides", {})
    print(f"\n{lab} mid-session native-stream-status:")
    print("  capture_target:", json.dumps(s.get("capture_target")))
    print("  capture_backend:", s.get("capture_backend"))
    print("  max_frame_size_bytes:", eo.get("max_frame_size_bytes"),
          "| source:", eo.get("max_frame_size_source"),
          "| any_override:", eo.get("any_override"))
    print("  host_resource_sampler:", json.dumps(s.get("host_resource_sampler"))[:200])
    vlog = open(os.path.join(HERE, lab, "native_video_alpha_lines.log"), errors="replace").read()
    cmds = re.findall(r"ffmpeg[^\n]*x11grab[^\n]*", vlog)
    for c in cmds[:2]:
        fr = re.search(r"-framerate (\S+)", c); win = re.search(r"-window_id (\S+)", c)
        mfs = re.search(r"-max_frame_size (\S+)", c)
        print("  encoder argv: framerate", fr and fr.group(1), "| window_id present:", bool(win),
              "| max_frame_size", mfs and mfs.group(1))
    for pat in (r"Stream #0:0[^\n]*x11grab[^\n]*|Stream #0:0: Video[^\n]*", r"\b\d{3,4}x\d{3,4}\b[^\n]*fps"):
        for mt in re.findall(pat, vlog)[:2]:
            print("  ffmpeg:", mt.strip()[:200])
    samp = [json.loads(l) for l in open(os.path.join(HERE, lab, "host_resource_samples.jsonl")) if l.strip()]
    print("  host_resource_samples:", len(samp))
