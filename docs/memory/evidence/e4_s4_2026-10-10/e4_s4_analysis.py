#!/usr/bin/env python3
"""E4-S4 -- the verdict as pre-registered (e4_s4_preregistration.txt §2-§3). Read-only over runs/ and pre_guide.json.
-> e4_s4_table.md, e4_s4_verdict.json, validity.json. Clause (d) uses E4-S2's pass rule (e4_s4_passrule.py, a copy)."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
spec = importlib.util.spec_from_file_location("passrule", os.path.join(HERE, "e4_s4_passrule.py"))
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
REF_HOST, REF_RENDERED = 10.9, 59.53          # E4-S1 PS1-STREAM
GRAB_S = 5.3                                   # E4-S1 CONC's median grab


def k(s, *p):
    for x in p:
        s = s.get(x) if isinstance(s, dict) else None
    return s


def jl(p):
    out = []
    if os.path.exists(p):
        for l in open(p, errors="replace"):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def load(d):
    p = os.path.join(R, d, "summary.json")
    return (json.load(open(p)), os.path.dirname(p)) if os.path.exists(p) else (None, None)


def row(s, rd):
    t0, t1 = s["window"]["from"], s["window"]["to"]
    samples = [x for x in jl(os.path.join(rd, "samples.jsonl")) if t0 <= x.get("at_utc", "") <= t1]
    epg_rows = sum(1 for x in samples if (x.get("procs") or {}).get("epg"))
    deferred = [x for x in jl(os.path.join(rd, "epg.jsonl")) if x.get("kind") == "deferred" and t0 <= x["start_utc"] <= t1]
    grabs = [x for x in jl(os.path.join(rd, "epg.jsonl")) if x.get("kind") == "grab" and t0 <= x["start_utc"] <= t1]
    hh = lambda key: k(s, "host", "host", key, "mean")
    return {"window": [t0, t1], "host_cpu": hh("cpu.mean_pct"), "companion_cpu": hh("procs.companion.cpu_pct"),
            "rendered_fps": k(s, "key", "heartbeat", "rendered_fps"), "loss_per_min": k(s, "key", "heartbeat", "video_loss_per_min"),
            "resyncs": k(s, "key", "heartbeat", "stream_resyncs"), "underruns": k(s, "key", "heartbeat", "audio_underruns"),
            "samples_in_window": len(samples), "samples_with_epg_child": epg_rows, "grabs_run_in_window": len(grabs),
            "deferred_rows": len(deferred), "deferred_pending_max": max((x.get("pending") or 0 for x in deferred), default=0),
            "drain": k(s, "teardown", "deferred_drain"), "socket_w": hh("gpu.socket_power_w"),
            "client_pauses": len(k(s, "key", "recovery", "client_pauses") or []), "controller_pauses": len(k(s, "key", "recovery", "controller_pauses") or []),
            "gaps": k(s, "key", "gaps"), "throttled_s": k(s, "key", "cgroup", "throttled_s"),
            "usage_cores": k(s, "key", "cgroup", "usage_cores")}


def main():
    pre = json.load(open(os.path.join(HERE, "pre_guide.json")))
    ctl_s, ctl_rd = load("E1-PS1-STREAM/run1")
    runs = {"control": (ctl_s, ctl_rd), "conc_flag_r1": load("E1-CONC_flag/run1"), "conc_flag_r2": load("E1-CONC_flag/run2"),
            "conc_flag_cpu150": load("E1-CONC_flag_cpu150/run1")}
    rows, val = {}, {}
    for name, (s, rd) in runs.items():
        val[name] = {"status": (s or {}).get("status"), "valid": bool(s and s.get("status") == "OK" and s.get("window")),
                     "replaced_attempts": len([x for x in os.listdir(rd) if x.startswith("summary_failed_attempt")]) if rd else None,
                     "flags_absent_after": k(s, "teardown", "flags_absent"), "constraint_lifted": k(s, "teardown", "constraint_lifted")}
        rows[name] = row(s, rd) if val[name]["valid"] else None
    json.dump(val, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    out = {"rows": rows}
    if not all(v["valid"] for v in val.values()):
        out["verdict"] = "INCONCLUSIVE (a run never reached PLAYING after two replacements)"
    else:
        c = rows["control"]
        comp = abs(c["host_cpu"] - REF_HOST) <= 2 and abs(c["rendered_fps"] - REF_RENDERED) <= 0.5
        out["comparability"] = {"control_host_cpu": c["host_cpu"], "control_rendered": c["rendered_fps"], "holds": comp}
        cl = {}
        un = [rows["conc_flag_r1"], rows["conc_flag_r2"]]
        cl["a"] = all(x["loss_per_min"] <= 3 * c["loss_per_min"] and x["loss_per_min"] <= 100 and x["rendered_fps"] >= 59.5
                      and x["resyncs"] <= 10 and abs(x["host_cpu"] - c["host_cpu"]) <= 2 for x in un)
        bb, cc = [], []
        for name in ("conc_flag_r1", "conc_flag_r2", "conc_flag_cpu150"):
            x = rows[name]
            d = x["drain"] or {}
            ld = d.get("last_drain") or {}
            q = ld.get("queued") or d.get("pending_at_start") or 0
            ok = (x["samples_with_epg_child"] == 0 and x["grabs_run_in_window"] == 0 and x["deferred_pending_max"] >= 6
                  and d.get("pending_at_end") == 0 and (ld.get("failed") == 0) and ld.get("ok") == q and q > 0
                  and (ld.get("s") or 1e9) <= 2 * GRAB_S * q)
            bb.append({"run": name, "holds": ok, "epg_child_samples": x["samples_with_epg_child"], "grabs_in_window": x["grabs_run_in_window"],
                       "pending_max": x["deferred_pending_max"], "queued": q, "drain_ok": ld.get("ok"), "drain_failed": ld.get("failed"),
                       "drain_s": ld.get("s"), "limit_s": round(2 * GRAB_S * q, 1), "cap_fired": d.get("cap_fired"),
                       "waited_s": d.get("waited_s")})
            g = d.get("guide_after") or {}
            okc = g.get("channels_serving") == 6 and pre.get("programmes_total") and \
                abs(g.get("programmes_total", 0) - pre["programmes_total"]) <= 0.05 * pre["programmes_total"]
            cc.append({"run": name, "holds": bool(okc), "serving": g.get("channels_serving"), "programmes": g.get("programmes_total"),
                       "pre_programmes": pre.get("programmes_total")})
        cl["b"] = all(x["holds"] for x in bb)
        cl["c"] = all(x["holds"] for x in cc)
        s150, rd150 = runs["conc_flag_cpu150"]
        j = P.judge("E1-PS1-STREAM", s150, c["loss_per_min"], rd150)   # judged as a stream row (no grabs ran)
        cl["d"] = j["verdict"] == "PASS"
        cl["e"] = all(abs(x["companion_cpu"] - c["companion_cpu"]) <= 2 for x in un)
        out.update({"clauses": cl, "b_detail": bb, "c_detail": cc,
                    "d_detail": {"verdict": j["verdict"], "why": j["why"], "gates": j["gates"],
                                 "throttled_s": rows["conc_flag_cpu150"]["throttled_s"], "usage_cores": rows["conc_flag_cpu150"]["usage_cores"]}})
        if not comp:
            out["verdict"] = "INCONCLUSIVE (the control is outside E1's bands of E4-S1's PS1-STREAM)"
        elif all(cl.values()):
            out["verdict"] = "ACCEPTED"
        elif not cl["d"] and j["verdict"] == "INCONCLUSIVE" and all(v for kk, v in cl.items() if kk != "d"):
            out["verdict"] = "INCONCLUSIVE (clause d is link-INCONCLUSIVE; every other clause holds)"
        else:
            out["verdict"] = "REJECTED (" + ", ".join(kk for kk, v in cl.items() if not v) + ")"
    json.dump(out, open(os.path.join(HERE, "e4_s4_verdict.json"), "w"), indent=1, default=str)
    md = ["# E4-S4 — grab deferral while streaming: the table", "",
          "| | control (PS1-STREAM, no flag) | CONC + flag r1 | CONC + flag r2 | CONC + flag at 150 % |", "| --- | --- | --- | --- | --- |"]
    names = ["control", "conc_flag_r1", "conc_flag_r2", "conc_flag_cpu150"]
    for key in ("host_cpu", "companion_cpu", "rendered_fps", "loss_per_min", "resyncs", "underruns", "samples_with_epg_child",
                "grabs_run_in_window", "deferred_rows", "deferred_pending_max", "client_pauses", "controller_pauses",
                "socket_w", "usage_cores", "throttled_s"):
        md.append(f"| {key} | " + " | ".join(str(round(rows[n][key], 2) if isinstance((rows[n] or {}).get(key), float) else (rows[n] or {}).get(key))
                                            for n in names) + " |")
    md.append("| drain (queued / ok / failed / s) | — | " + " | ".join(
        (lambda d: f"{d.get('queued')} / {d.get('ok')} / {d.get('failed')} / {d.get('s')}")(((rows[n] or {}).get("drain") or {}).get("last_drain") or {})
        for n in names[1:]) + " |")
    md += ["", f"**Verdict: {out['verdict']}**", "", "```", json.dumps({kk: out.get(kk) for kk in ("comparability", "clauses")}, indent=1), "```"]
    open(os.path.join(HERE, "e4_s4_table.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({kk: out.get(kk) for kk in ("verdict", "comparability", "clauses")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
