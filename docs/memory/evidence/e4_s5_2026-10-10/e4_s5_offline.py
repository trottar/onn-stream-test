#!/usr/bin/env python3
"""E4-S5 §1 -- the offline pass over every recorded Snes9x window (13) and three PS1 windows (the contrast). Read-only
over the evidence directories and logs/games. -> offline.json, offline.md (in this dir).

Per window: the encoder's per-second capture (frames/s from encoder.jsonl) and its drop / dup counters; the fault
class (FAULT: capture 59.0 +/- 0.05 with ~1 drop/s for >= 2 min; CLEAN otherwise); from the encoder session log
(logs/games/native_video_alpha.log, the session overlapping the window): x11grab's input line (size, fps, tbr, tbn),
the discovered window size and the window title; from RetroArch's session log: the core's reported rate, the audio
input rate, the video size, the GL resolution, the swap function and SET_GEOMETRY count; the summary's launch
(s to PLAYING, the onn's attempt), what ran just before, the time of day, the profile at PLAYING.
READING RULE (E4-S5 task §1): a value that differs between every faulty window and every clean window names the cause;
if none does, the fault is not visible in the records."""
import glob
import json
import os
import re
import statistics
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
EV = os.path.join(REPO, "docs/memory/evidence")
LG = os.path.join(REPO, "logs/games")
SNES = sorted(glob.glob(f"{EV}/e3_a2_2026-10-07/runs/E1-SNES-STREAM/run1") + glob.glob(f"{EV}/e3_s4_2026-10-07/runs/E1-SNES-STREAM_flag/run*")
              + glob.glob(f"{EV}/e4_s1_2026-10-09/runs/E1-SNES-STREAM/run1") + glob.glob(f"{EV}/e4_s2_2026-10-09/runs/E1-SNES-STREAM_*/run*"))
PS1 = [f"{EV}/e4_s1_2026-10-09/runs/E1-PS1-STREAM/run1", f"{EV}/e4_s2_2026-10-09/runs/E1-PS1-STREAM_cpu400/run1",
       f"{EV}/e4_s2_2026-10-09/runs/E1-PS1-STREAM_cpu200/run1"]
ep = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def jl(p):
    out = []
    try:
        for l in open(p, errors="replace"):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    except OSError:
        pass
    return out


def encoder_sessions():
    """Each 'Starting PrivyHub Linux native-video backend' block: start epoch, title core, discovered size, input line,
    the last progress values (frame, fps, dup, drop)."""
    raw = open(os.path.join(LG, "native_video_alpha.log"), "rb").read().decode("utf-8", "replace")
    blocks = raw.split("Starting PrivyHub Linux native-video backend")[1:]
    out = []
    for b in blocks:
        m = re.search(r"start: (\d+\.\d+)", b)
        title = re.search(r"Window title: RetroArch (\S+)", b)
        disc = re.search(r"discovered=(\d+x\d+)", b)
        inp = re.search(r"Stream #0:0: Video: rawvideo[^\n]*", b)
        outl = re.search(r"Stream #0:0: Video: h264[^\n]*", b)
        prog = re.findall(r"frame=\s*(\d+) fps=\s*([\d.]+)[^\r\n]*?(?:dup=\s*(\d+))?\s*(?:drop=\s*(\d+))?\s+speed", b)
        drops = re.findall(r"drop=\s*(\d+)", b)
        dups = re.findall(r"dup=\s*(\d+)", b)
        out.append({"start": float(m.group(1)) if m else None, "core": title.group(1) if title else None,
                    "discovered": disc.group(1) if disc else None,
                    "input": re.sub(r"\s+", " ", inp.group(0))[len("Stream #0:0: Video: "):] if inp else None,
                    "input_tbr": (re.search(r"([\d.k]+) tbr", inp.group(0)).group(1) if inp and re.search(r"([\d.k]+) tbr", inp.group(0)) else None),
                    "output_fps": (re.search(r"([\d.]+) fps", outl.group(0)).group(1) if outl and re.search(r"([\d.]+) fps", outl.group(0)) else None),
                    "last_frame": int(prog[-1][0]) if prog else None, "last_fps": float(prog[-1][1]) if prog else None,
                    "drop_last": int(drops[-1]) if drops else 0, "dup_last": int(dups[-1]) if dups else 0,
                    "exit": "signal 15" if "received signal 15" in b else ("other" if "Exiting" in b else None)})
    return out


def ra_log(t_launch):
    """RetroArch's session log for a launch: the game log whose local-time name is nearest after the launch."""
    best = None
    for p in glob.glob(os.path.join(LG, "*-game_*.log")):
        n = os.path.basename(p)
        try:
            t = time.mktime(time.strptime(n[:15], "%Y%m%d-%H%M%S"))   # local time in the name
        except ValueError:
            continue
        if 0 <= t - t_launch <= 120 and (best is None or t < best[0]):
            best = (t, p)
    if not best:
        return {}
    txt = open(best[1], errors="replace").read()
    g = lambda r: (re.search(r, txt).group(1) if re.search(r, txt) else None)
    return {"log": os.path.basename(best[1]), "core_fps": g(r"Geometry: .*FPS: ([\d.]+)"),
            "audio_input_rate": g(r"Set audio input rate to: ([\d.]+)"), "video_size": g(r"Set video size to: (\d+x\d+)"),
            "gl_resolution": g(r"\[GL\] Using resolution (\d+x\d+)"), "swap_fn": g(r"Found swap function: (\S+)"),
            "set_geometry": txt.count("SET_GEOMETRY"), "screen": g(r"Detecting screen resolution: (\d+x\d+)"),
            "audio_buffer": g(r'reports a (\d+)-byte buffer'), "runtime": g(r"total of: ([\d hoursminutesecond,]+)")}


def per_second(rd, t0, t1):
    rows = [r for r in jl(os.path.join(rd, "encoder.jsonl")) if r.get("records")]
    fps, drops, dups, faulty_s = [], [], [], 0
    for a, b in zip(rows, rows[1:]):
        if not (t0 <= a["at_utc"] <= t1) or b["frame"] < a["frame"]:
            continue
        d = ep(b["at_utc"]) - ep(a["at_utc"])
        if d <= 0 or d > 3:
            continue
        f = (b["frame"] - a["frame"]) / d
        dr = (b["drop"] - a["drop"]) / d
        fps.append(round(f, 2))
        drops.append(dr)
        dups.append((b["dup"] - a["dup"]) / d)
    # fault seconds: a rolling 10-s mean of capture within 59.0 +/- 0.05 and of drops within 1 +/- 0.1
    fs = 0
    for i in range(len(fps) - 9):
        if abs(statistics.mean(fps[i:i + 10]) - 59.0) <= 0.05 and abs(statistics.mean(drops[i:i + 10]) - 1.0) <= 0.1:
            fs += 1
    return {"seconds": len(fps), "capture_mean": round(statistics.mean(fps), 3) if fps else None,
            "drops_per_s": round(statistics.mean(drops), 3) if drops else None,
            "dups_per_s": round(statistics.mean(dups), 4) if dups else None, "fault_s": fs,
            "first_min_capture": round(statistics.mean(fps[:60]), 2) if fps else None,
            "last_min_capture": round(statistics.mean(fps[-60:]), 2) if fps else None}


def window(rd, sessions):
    s = json.load(open(os.path.join(rd, "summary.json")))
    t0, t1 = s["window"]["from"], s["window"]["to"]
    ps = per_second(rd, t0, t1)
    cls = "FAULT (whole window)" if ps["fault_s"] >= 0.9 * max(ps["seconds"] - 9, 1) else \
        "FAULT (partial, >= 2 min)" if ps["fault_s"] >= 120 else "CLEAN"
    g0 = ep(s["gap"]["from"]) if s.get("gap") else ep(s["started_utc"])
    enc = [x for x in sessions if x["start"] and g0 <= x["start"] <= ep(t1)]
    # what ran just before: the previous run dir's summary in the same runs/ tree by start time
    tree = os.path.dirname(os.path.dirname(rd))
    prev = None
    for p in glob.glob(os.path.join(tree, "*", "run*", "summary.json")):
        o = json.load(open(p))
        if o.get("ended_utc") and o["ended_utc"] <= s["started_utc"] and (prev is None or o["ended_utc"] > prev[0]):
            prev = (o["ended_utc"], o.get("workload"))
    return {"run": os.path.relpath(rd, EV), "class": cls, **ps,
            "window_utc": [t0, t1], "launch": (s.get("launch") or {}).get("stream"),
            "previous_row": prev[1] if prev else None, "constraint": s.get("constraint"),
            "encoder_sessions": [{k: v for k, v in x.items() if k != "start"} for x in enc],
            "retroarch": ra_log(ep(s["gap"]["to"]) if s.get("gap") else g0),
            "profile_at_playing": s.get("profile_at_playing"),
            "status_end": s.get("status_end"), "hour_utc": t0[11:13]}


def main():
    sessions = encoder_sessions()
    rows = [window(rd, sessions) for rd in SNES] + [dict(window(rd, sessions), contrast="PS1") for rd in PS1]
    json.dump(rows, open(os.path.join(HERE, "offline.json"), "w"), indent=1, default=str)
    keys = ["capture_mean", "drops_per_s", "first_min_capture", "previous_row", "hour_utc"]
    md = ["# E4-S5 §1 — the offline pass (13 Snes9x windows, 3 PS1 for contrast)", "",
          "| run | class | capture / drops per s | 1st min | before it | encoder input (x11grab) | discovered | RetroArch: core fps / audio rate / video size / GL res / SET_GEOMETRY | launch |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in rows:
        e = r["encoder_sessions"][0] if r["encoder_sessions"] else {}
        ra = r["retroarch"]
        md.append(f"| {r['run'].replace('/runs', '').replace('E1-', '')} | **{r['class']}** | {r['capture_mean']} / {r['drops_per_s']} | "
                  f"{r['first_min_capture']} | {r['previous_row']} | {e.get('input')} ({len(r['encoder_sessions'])} sess.) | {e.get('discovered')} | "
                  f"{ra.get('core_fps')} / {ra.get('audio_input_rate')} / {ra.get('video_size')} / {ra.get('gl_resolution')} / {ra.get('set_geometry')} | "
                  f"{(r['launch'] or {}).get('attempt')}, {(r['launch'] or {}).get('s_to_playing')} s |")
    # the reading rule: fields whose values separate every faulty from every clean Snes9x window
    snes = [r for r in rows if "contrast" not in r]
    fault = [r for r in snes if r["class"].startswith("FAULT")]
    clean = [r for r in snes if r["class"] == "CLEAN"]
    cand = {}
    flat = lambda r: {"previous_row": r["previous_row"], "hour_utc": r["hour_utc"],
                      "launch_attempt": (r["launch"] or {}).get("attempt"),
                      "encoder_sessions": len(r["encoder_sessions"]),
                      **{"enc_" + k: (r["encoder_sessions"][0] if r["encoder_sessions"] else {}).get(k) for k in ("input", "discovered", "core")},
                      **{"ra_" + k: r["retroarch"].get(k) for k in ("core_fps", "audio_input_rate", "video_size",
                                                                   "gl_resolution", "swap_fn", "set_geometry", "screen",
                                                                   "audio_buffer")}}
    for k in flat(snes[0]):
        fv = {str(flat(r)[k]) for r in fault}
        cv = {str(flat(r)[k]) for r in clean}
        cand[k] = {"fault": sorted(fv), "clean": sorted(cv), "separates": bool(fault and clean and not (fv & cv))}
    names = [k for k, v in cand.items() if v["separates"]]
    md += ["", f"Faulty: {len(fault)} ({', '.join(r['run'].split('/')[-2] + '/' + r['run'].split('/')[-1] for r in fault)}); clean: {len(clean)}.", "",
           "**The reading rule** (a value that differs between every faulty window and every clean window names the cause):", "",
           "| field | faulty values | clean values | separates? |", "| --- | --- | --- | --- |"]
    for k, v in cand.items():
        md.append(f"| {k} | {', '.join(v['fault'])} | {', '.join(v['clean'])} | {'**yes**' if v['separates'] else 'no'} |")
    md += ["", f"**Separating fields:** {', '.join(names) if names else 'none -- the fault is not visible in the records'}."]
    # every Snes9x encoder session in the log (not only the 13 windows): x11grab's probed tbr vs the output rate
    md += ["", "## Every Snes9x encoder session in `native_video_alpha.log`: x11grab's probed frame rate (tbr) vs the encoder's output rate", "",
           "| session start (UTC) | input tbr | output fps | drops at the session's end | frames |", "| --- | --- | --- | --- | --- |"]
    for x in sessions:
        if x["core"] == "Snes9x":
            md.append(f"| {datetime.fromtimestamp(x['start'], timezone.utc).isoformat(timespec='seconds') if x['start'] else '—'} | "
                      f"{x['input_tbr']} | {x['output_fps']} | {x['drop_last']} | {x['last_frame']} |")
    ps1 = [x for x in sessions if x["core"] == "Beetle"]
    md += ["", f"PS1 (Beetle PSX HW) sessions: {len(ps1)}; input tbr values {sorted({str(x['input_tbr']) for x in ps1})}; "
           f"output fps values {sorted({str(x['output_fps']) for x in ps1})}."]
    open(os.path.join(HERE, "offline.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({"faulty": [r["run"] for r in fault], "clean": len(clean), "separating": names}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
