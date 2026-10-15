#!/usr/bin/env python3
"""E4-S5B -- the bench and the PS1 run, read as pre-registered (e4_s5b_preregistration.txt §2-§4). Read-only over
bench/bench.jsonl, runs_bench/, runs_ps1/ and the companion's encoder log. -> e4_s5b_table.md, e4_s5b_verdict.json,
validity.json. Capture and dup+drop are segment-aware (E4-S2 / E4-S5's reading, the function copied here)."""
import glob
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
ENC_LOG = os.path.join(REPO, "logs/games/native_video_alpha.log")
REF_SNES_HOST, REF_SNES_XORG, REF_PS1_HOST = 7.4, 7.692, 10.9    # E4-S1 SNES-STREAM host CPU / Xorg (% of a core); PS1
CORES = 12


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def ep(x):
    return time.mktime(time.strptime(x[:19], "%Y-%m-%dT%H:%M:%S")) + (float("0." + x[20:-1]) if len(x) > 20 else 0)


def jl(p):
    out = []
    if os.path.exists(p):
        for l in open(p, errors="replace"):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def segcap(rd, s):
    """Segment-aware capture fps and dup+drop per min over the window (E4-S5's segcap)."""
    t0, t1 = s["window"]["from"], s["window"]["to"]
    rows = [r for r in jl(os.path.join(rd, "encoder.jsonl")) if r.get("records") and t0 <= r["at_utc"] <= t1]
    fr = dt = dd = 0.0
    segs = 1 if rows else 0
    for a, b in zip(rows, rows[1:]):
        d = ep(b["at_utc"]) - ep(a["at_utc"])
        if b["frame"] < a["frame"] or d > 3 or b["dup"] < a["dup"] or b["drop"] < a["drop"]:
            segs += 1
            continue
        fr += b["frame"] - a["frame"]
        dt += d
        dd += (b["dup"] - a["dup"]) + (b["drop"] - a["drop"])
    return (round(fr / dt, 3) if dt else None, round(dd / (dt / 60), 3) if dt else None, segs)


def companion_probes(size):
    """The companion's own encoder headers (input tbr -> output fps) for the last contiguous run of encoder starts
    whose input is <size> in the log's last 20 MB (read-only)."""
    with open(ENC_LOG, "rb") as fh:
        fh.seek(max(0, os.path.getsize(ENC_LOG) - 20_000_000))
        txt = fh.read().decode("utf-8", "replace")
    heads = re.findall(r"Stream #0:0: Video: rawvideo[^\n]*?(\d+x\d+),[^\n]*?([\d.k]+) tbr[\s\S]*?Stream #0:0: Video: h264[^\n]*?([\d.]+) fps", txt)
    groups, cur = [], []
    for sz, tbr, fps in heads:
        if sz == size:
            cur.append((tbr, fps))
        elif cur:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups[-1] if groups else []          # the last contiguous run of <size> encoder starts


def live(rd):
    s = json.load(open(os.path.join(rd, "summary.json")))
    if s.get("status") != "OK":
        return {"run": os.path.relpath(rd, HERE), "status": s.get("status")}
    cap, dd, segs = segcap(rd, s)
    hh = lambda key: k(s, "host", "host", key, "mean")
    return {"run": os.path.relpath(rd, HERE), "status": "OK", "window": s["window"],
            "window_s": ep(s["window"]["to"]) - ep(s["window"]["from"]),
            "retroarch_fps": k(s, "key", "retroarch", "frames_per_s"), "host_cpu": hh("cpu.mean_pct"),
            "xorg_core_pct": hh("procs.xorg.cpu_pct"), "encoder_core_pct": hh("procs.encoder.cpu_pct"),
            "capture_fps": cap, "dupdrop_per_min": dd, "encoder_segments": segs,
            "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"), "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
            "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "underruns": k(s, "key", "heartbeat", "audio_underruns"),
            "socket_w": hh("gpu.socket_power_w"), "flags_absent_after": k(s, "teardown", "flags_absent"),
            "apk": k(s, "teardown", "apk"), "dropin": s.get("dropin"),
            "replaced_attempts": len(glob.glob(os.path.join(rd, "summary_failed_attempt*")))}


SNES_PROBES = None


def main():
    global SNES_PROBES
    SNES_PROBES = companion_probes("897x672")
    rows = jl(os.path.join(HERE, "bench", "bench.jsonl"))
    ses = [r for r in rows if r.get("event") == "session"]
    events = [r for r in rows if r.get("event") != "session"]
    arms = {}
    for a in "AB":
        x = [r for r in ses if r["arm"] == a]
        bad = [r for r in x if r.get("input_tbr") != "60"]
        arms[a] = {"sessions": len(x), "rc_nonzero": sum(1 for r in x if r["rc"] != 0),
                   "bad_probes": len(bad), "bad_rate": round(len(bad) / len(x), 3) if x else None,
                   "tbr_counts": {t: sum(1 for r in x if r.get("input_tbr") == t) for t in sorted({r.get("input_tbr") for r in x}, key=str)},
                   "output_fps_counts": {t: sum(1 for r in x if r.get("output_fps") == t) for t in sorted({r.get("output_fps") for r in x}, key=str)},
                   "built_has_output_r": sorted({r["built_has_output_r"] for r in x}),
                   "drops_good_probe": [r["drop"] for r in x if r.get("input_tbr") == "60"],
                   "dups_all_max": max((r["dup"] for r in x), default=None),
                   "bad": [{"index": r["index"], "tbr": r["input_tbr"], "output_fps": r["output_fps"], "drop": r["drop"],
                            "dup": r["dup"], "frames": r["frames"]} for r in bad],
                   "cpu_s_mean": round(sum(r["cpu_s"] for r in x) / len(x), 2) if x else None}
    # §2 the reading rule
    def exp_drops(t):
        return (60 - float(t)) * 60
    mech = [{"index": b["index"], "tbr": b["tbr"], "output_fps": b["output_fps"], "drop": b["drop"],
             "expected": round(exp_drops(b["tbr"]), 2),
             "holds": b["output_fps"] == b["tbr"] and abs(b["drop"] - exp_drops(b["tbr"])) <= 0.2 * exp_drops(b["tbr"])}
            for b in arms["A"]["bad"]]
    fix = [{"index": b["index"], "tbr": b["tbr"], "output_fps": b["output_fps"], "drop": b["drop"],
            "holds": b["output_fps"] == "60" and b["drop"] <= 2} for b in arms["B"]["bad"]]
    sampled = arms["B"]["bad_probes"] >= 3
    mech_ok = bool(mech) and all(m["holds"] for m in mech)
    fix_ok = all(f["holds"] for f in fix) if fix else None
    # §3 the live session(s): host-clean
    lives = [live(rd) for rd in sorted(glob.glob(os.path.join(HERE, "runs_bench", "E1-SNES-STREAM", "run*")))]
    host = []
    for L in lives:
        if L["status"] != "OK":
            host.append({"run": L["run"], "holds": False, "why": "the live session did not complete"})
            continue
        w0, w1 = ep(L["window"]["from"]), ep(L["window"]["to"])
        cpu_in = 0.0
        for r in ses:
            a, b = ep(r["start_utc"]), ep(r["end_utc"])
            ov = max(0.0, min(b, w1) - max(a, w0))
            cpu_in += r["cpu_s"] * (ov / (b - a) if b > a else 0)
        bench_ffmpeg = cpu_in / (L["window_s"] * CORES) * 100
        xorg_extra = max(0.0, (L["xorg_core_pct"] or 0) - REF_SNES_XORG) / CORES
        cost = bench_ffmpeg + xorg_extra
        net = L["host_cpu"] - cost
        host.append({"run": L["run"], "host_cpu": L["host_cpu"], "bench_ffmpeg_host_pct": round(bench_ffmpeg, 3),
                     "xorg_extra_host_pct": round(xorg_extra, 3), "bench_cost_host_pct": round(cost, 3),
                     "host_minus_bench": round(net, 3), "retroarch_fps": L["retroarch_fps"],
                     "holds": (L["retroarch_fps"] or 0) >= 59.9 and abs(net - REF_SNES_HOST) <= 2})
    host_ok = bool(host) and all(h["holds"] for h in host)
    # §4 PS1 with the flag
    ps1 = [live(rd) for rd in sorted(glob.glob(os.path.join(HERE, "runs_ps1", "E1-PS1-STREAM_flag", "run*")))]
    p = ps1[-1] if ps1 else {"status": None}
    ps1_cl = None
    if p["status"] == "OK":
        ps1_cl = {"capture_60_pm_0.1": p["capture_fps"] is not None and abs(p["capture_fps"] - 60) <= 0.1,
                  "dupdrop_le_0.2": p["dupdrop_per_min"] is not None and p["dupdrop_per_min"] <= 0.2,
                  "retroarch_ge_59.9": (p["retroarch_fps"] or 0) >= 59.9,
                  "host_cpu_pm_2": p["host_cpu"] is not None and abs(p["host_cpu"] - REF_PS1_HOST) <= 2}
    ps1_ok = bool(ps1_cl) and all(ps1_cl.values())
    ps1_probe = companion_probes("1920x1080")[-3:]
    # verdict (§3)
    if fix_ok is False or (ps1_cl is not None and not ps1_ok):
        verdict = "REJECTED (" + ", ".join(x for x, bad in (("a bad-probe B session drops > 2 or outputs != 60", fix_ok is False),
                                                            ("PS1 with the flag (§4)", ps1_cl is not None and not ps1_ok)) if bad) + ")"
    elif ps1_cl is None:
        verdict = "INCONCLUSIVE (the PS1 run did not complete)"
    elif not sampled:
        verdict = f"INCONCLUSIVE (not sampled enough: arm B held {arms['B']['bad_probes']} bad probes; the probe did not misread often enough tonight)"
    elif not mech_ok:
        verdict = "INCONCLUSIVE (the mechanism did not reproduce in arm A)"
    elif not host_ok:
        verdict = "INCONCLUSIVE (the live session was not host-clean)"
    else:
        verdict = "ACCEPTED"
    out = {"verdict": verdict, "arms": arms, "mechanism_A": mech, "mechanism_reproduces": mech_ok, "fix_B": fix,
           "fix_works": fix_ok, "sampled_enough": sampled, "live": lives, "host_clean": host, "host_clean_ok": host_ok,
           "ps1_flag": p, "ps1_clauses": ps1_cl, "ps1_ok": ps1_ok, "ps1_companion_probes_last": ps1_probe,
           "snes_companion_probes_live": SNES_PROBES,
           "bench_events": events}
    json.dump(out, open(os.path.join(HERE, "e4_s5b_verdict.json"), "w"), indent=1, default=str)
    json.dump({"bench_sessions": len(ses), "bench_rc_nonzero": sum(1 for r in ses if r["rc"] != 0),
               "live": [{x: L.get(x) for x in ("run", "status", "flags_absent_after", "apk", "replaced_attempts")} for L in lives],
               "ps1": {x: p.get(x) for x in ("run", "status", "flags_absent_after", "apk", "dropin", "replaced_attempts")}},
              open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    md = ["# E4-S5B — the SNES capture fix on bad probes: the bench", "",
          "| arm | sessions | bad probes (tbr ≠ 60) | tbr counts | output fps counts | drops at a 60 probe | output -r in the built command |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for a in "AB":
        x = arms[a]
        md.append(f"| {a} ({'flag' if a == 'B' else 'no flag'}) | {x['sessions']} | {x['bad_probes']} ({x['bad_rate']}) | {x['tbr_counts']} | "
                  f"{x['output_fps_counts']} | max {max(x['drops_good_probe'], default=None)} | {x['built_has_output_r']} |")
    md += ["", "Bad-probe sessions:", "", "| arm | index | tbr | output fps | drops | expected (A) | holds |", "| --- | --- | --- | --- | --- | --- | --- |"]
    md += [f"| A | {m['index']} | {m['tbr']} | {m['output_fps']} | {m['drop']} | {m['expected']} | {m['holds']} |" for m in mech]
    md += [f"| B | {f_['index']} | {f_['tbr']} | {f_['output_fps']} | {f_['drop']} | — | {f_['holds']} |" for f_ in fix]
    md += ["", "Live session(s) (no flag for the companion):", "",
           "| run | RetroArch | host CPU | bench cost (ffmpeg + Xorg extra) | host − bench | capture / dup+drop per min (companion, no flag) | rendered | loss/min |",
           "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for L, h in zip(lives, host):
        if L["status"] == "OK":
            md.append(f"| {L['run']} | {L['retroarch_fps']} | {round(L['host_cpu'], 2)} | {h['bench_cost_host_pct']} "
                      f"({h['bench_ffmpeg_host_pct']} + {h['xorg_extra_host_pct']}) | {h['host_minus_bench']} | "
                      f"{L['capture_fps']} / {L['dupdrop_per_min']} | {L['rendered_fps']} | {L['loss_per_min']} |")
    md += ["", "PS1-STREAM with the flag:", "", f"`{json.dumps({x: p.get(x) for x in ('status', 'capture_fps', 'dupdrop_per_min', 'retroarch_fps', 'host_cpu', 'rendered_fps', 'loss_per_min', 'resyncs')})}`",
           f"clauses: {ps1_cl}; the companion's last 1920x1080 probes (tbr, output fps): {ps1_probe}", "",
           f"Reading: mechanism reproduces in A: {mech_ok}; the fix works in B: {fix_ok}; sampled enough: {sampled}; "
           f"host-clean: {host_ok}; PS1: {ps1_ok}.", "", f"**Verdict: {verdict}**"]
    open(os.path.join(HERE, "e4_s5b_table.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({x: out[x] for x in ("verdict", "mechanism_reproduces", "fix_works", "sampled_enough", "host_clean_ok", "ps1_ok")}, indent=1))
    print(json.dumps({a: {x: arms[a][x] for x in ("sessions", "bad_probes", "tbr_counts")} for a in "AB"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
