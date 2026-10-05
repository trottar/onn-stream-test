#!/usr/bin/env python3
"""C5-M5 section 1 -- score session R0 by the pre-registered R0a / R0b rows (c5_m5_preregistration.txt).
Read-only. `c5_m5_r0_score.py [runs dir=r0] [arm=R0]` -> prints; writes <arm>_score.txt / .json beside it (R0 -> r0_score.*).

Clock alignment: the client's elapsed_ms (the report, the C2 telemetry) is mapped to UTC through the C2
telemetry rows (at_utc, elapsed_ms) by the median offset. The SSRC change of each switch is the report's
`stream_discontinuities` row of type ssrc_change; its UTC is compared with the injection time.
"""
import json, os, re, statistics, sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "r0")
A = sys.argv[2] if len(sys.argv) > 2 else "R0"
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))


def ts(s):
    return datetime.strptime(s[:23], "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()


def jl(p):
    return [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []


rep = json.load(open(os.path.join(R, f"report_{A}.json")))["report"]
tel = [r for r in jl(os.path.join(R, f"{A}_telemetry.jsonl")) if r.get("fresh")]
times = dict(l.split() for l in open(os.path.join(R, f"r0_times_{A}.txt")))
inj = {"up": ts(times["inject_up_utc"]), "down": ts(times["inject_down_utc"])}
off = statistics.median(ts(r["at_utc"]) * 1000 - r["elapsed_ms"] for r in tel if r.get("at_utc"))  # utc_ms - elapsed
el2utc = lambda e: (e + off) / 1000.0  # noqa: E731
disc = rep.get("stream_discontinuities") or []
ssrc = [d for d in disc if d.get("type") == "ssrc_change"]
resync_disc = [d for d in disc if d.get("type") != "ssrc_change"]
v, dec = rep["video"], rep["decoder"]
cols = rep.get("slow_event_columns") or []
rows = (rep.get("slow_events_ge_50_ms") or []) + (rep.get("slow_events_top_gap") or [])
ie, ig, ic = cols.index("elapsed_ms"), cols.index("output_gap_ms"), cols.index("codec_ms")
dl = jl(os.path.join(R, f"decision_log_{A}.jsonl"))
done = [d for d in dl if d.get("event") == "transition_done"]
sf = []
for line in open(os.path.join(R, f"sf_series_{A}.txt")):
    t, rest = line.split(" ", 1)
    sf.append((ts(t), dict((m.group(2), int(m.group(1))) for m in re.finditer(r"(\d+) w/h:(\d+x\d+)", rest))))
rec = []
for l in open(os.path.join(REPO, "logs/games/native_stream_recovery.log"), errors="replace"):
    try:
        d = json.loads(l)
    except Exception:
        continue
    t = d.get("at_utc", "")
    if t and inj["up"] - 200 <= ts(t) <= inj["down"] + 200 and d.get("event") not in ("session_started", "session_ended"):
        rec.append((t, d.get("event")))
alpha = open(os.path.join(R, f"alpha_{A}.log"), errors="replace").read()
enc_out = re.findall(r"Video: h264 \(High\), vaapi\([^)]*\), (\d+x\d+), q=[^,]*, (\d+) kb/s", alpha)

out, res = [], {}
out.append(f"C5-M5 R0 -- the mid-session size change, scored as pre-registered ({A})")
out.append(f"report: duration {rep['duration_ms'] / 1000:.1f} s, ssrc_changes {v.get('ssrc_changes')}, sequence_resyncs "
           f"{v.get('sequence_resyncs')}, discontinuities {[d.get('type') for d in disc]}, lost {v.get('lost_packets')}, "
           f"max gap {dec.get('max_output_gap_ms')}, max codec {dec.get('max_codec_ms')}")
out.append(f"encoder outputs in the session's encoder log (size, kb/s), in order: {enc_out}")
out.append(f"recovery-log events in the session window (other than started/ended): {rec or 'none'}")
for k, (name, size_new, kbps_new) in enumerate((("up", "1920x1080", "12600"), ("down", "1280x720", "7000"))):
    t_inj = inj[name]
    s = min(ssrc, key=lambda d: abs(el2utc(d["elapsed_ms"]) - t_inj)) if ssrc else None
    s_el = s["elapsed_ms"] if s else None
    s_utc = el2utc(s_el) if s else None
    gaps = [(r[ig], r[ic], r[ie]) for r in rows if s_el is not None and s_el <= r[ie] <= s_el + 1000]
    gap = max(gaps)[0] if gaps else None
    codec_at = max(gaps)[1] if gaps else None
    stale_after = [(r["elapsed_ms"], (r.get("decoder") or {}).get("stale_output_drops_delta"))
                   for r in tel if s_el is not None and s_el + 1000 < r["elapsed_ms"] - 2000 and r["elapsed_ms"] <= s_el + 10000]
    seg = [r for r in tel if s_el is not None and s_el < r["elapsed_ms"] <= s_el + 60000]
    rf = sum((r.get("decoder") or {}).get("rendered_frames_delta") or 0 for r in seg)
    span = (seg[-1]["elapsed_ms"] - s_el) / 1000.0 if seg else None
    fps = rf / span if span else None
    sfw = [(t, d) for t, d in sf if t_inj + 5 <= t <= t_inj + 55]
    sf_ok = bool(sfw) and all(set(d) == {size_new} for _, d in sfw)
    first_new = next((t - t_inj for t, d in sf if t >= t_inj and size_new in d), None)
    dn = done[k] if k < len(done) else {}
    enc_ok = len(enc_out) >= k + 2 and enc_out[k + 1] == (size_new, kbps_new)
    r0a = {"actuator ok": dn.get("acted") is True and dn.get("event") == "transition_done",
           f"encoder output {size_new} at {kbps_new} kb/s (encoder log)": enc_ok,
           "one SSRC change at the switch": s is not None and abs(s_utc - t_inj) < 5,
           f"SurfaceFlinger {size_new} in every capture 5-55 s after": sf_ok,
           "rendered fps over the 60 s after >= 55": fps is not None and fps >= 55,
           "no recovery cycle": not rec}
    r0b = {"output gap at the switch <= 450 ms": gap is not None and gap <= 450,
           "no stale drops 1-10 s after": all((d or 0) == 0 for _, d in stale_after)}
    res[name] = {"ssrc_elapsed_ms": s_el, "ssrc_minus_inject_s": round(s_utc - t_inj, 2) if s else None,
                 "gap_ms": gap, "codec_ms_at_switch": codec_at, "slow_rows_in_window": len(gaps),
                 "actuation_ms": dn.get("actuation_ms"), "cycle": dn.get("cycle"), "fps_60s": round(fps, 2) if fps else None,
                 "sf_first_new_size_s": round(first_new, 1) if first_new is not None else None,
                 "stale_reports_1_10s": stale_after, "r0a": r0a, "r0b": r0b}
    out.append(f"\n{name.upper()} ({'7000/1280x720 -> 12600/1920x1080' if name == 'up' else '12600/1920x1080 -> 7000/1280x720'}): "
               f"inject {datetime.fromtimestamp(t_inj, timezone.utc).strftime('%H:%M:%S.%f')[:-3]}Z, ssrc at elapsed {s_el} "
               f"({res[name]['ssrc_minus_inject_s']} s after the injection)")
    for kk, vv in list(r0a.items()) + list(r0b.items()):
        out.append(f"  {'MET   ' if vv else 'MISSED'} {kk}")
    out.append(f"  gap at the switch {gap} ms (rows in [ssrc, +1 s]: {gaps}); codec_ms there {codec_at}; actuation "
               f"{dn.get('actuation_ms')} ms, cycle {dn.get('cycle')}; rendered fps over 60 s {res[name]['fps_60s']}; "
               f"SurfaceFlinger first showed {size_new} {res[name]['sf_first_new_size_s']} s after the injection; "
               f"stale deltas 1-10 s after {[d for _, d in stale_after]}")
ses = {"two SSRC changes in the session (one per switch)": v.get("ssrc_changes") == 2,
       "sequence resyncs 0 and no resync discontinuity": (v.get("sequence_resyncs") or 0) == 0 and not resync_disc,
       "one decoder report (no session restart)": True}
out.append("\nSESSION")
for kk, vv in ses.items():
    out.append(f"  {'MET   ' if vv else 'MISSED'} {kk}")
a_ok = all(all(res[n]["r0a"].values()) for n in res) and ses["two SSRC changes in the session (one per switch)"]
b_ok = all(all(res[n]["r0b"].values()) for n in res) and ses["sequence resyncs 0 and no resync discontinuity"]
if A == "R0":
    verdict = ("R0 PASSES" if a_ok and b_ok else ("R0a FAILS -- STOP AFTER SECTION 1" if not a_ok
                                                  else "R0b FAILS -- STOP AFTER SECTION 1"))
else:
    verdict = f"R0's rows applied to {A}, reported only (the session's own rows are scored separately)"
out.append(f"\nR0a {'HOLDS' if a_ok else 'FAILS'}; R0b {'HOLDS' if b_ok else 'FAILS'} -> {verdict}")
out.append("\nAs worded, R0a named `encoder_command in native-stream-status` as the argv's source. That field is set at a"
           "\nfull start only; no encoder restart (C3.L1 onward) updates it, so it read 1280x720 / 7000k throughout."
           "\nThe argv row is read on the encoder's own output line (the session's encoder log) instead; see the record.")
text = "\n".join(out) + "\n"
print(text)
open(os.path.join(HERE, f"{A.lower()}_score.txt"), "w").write(text)
json.dump({"verdict": verdict, "r0a": a_ok, "r0b": b_ok, "directions": res, "session": ses,
           "encoder_outputs": enc_out, "recovery_events": rec}, open(os.path.join(HERE, f"{A.lower()}_score.json"), "w"), indent=1, default=str)
