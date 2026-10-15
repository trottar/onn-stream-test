#!/usr/bin/env python3
"""E4-S4C -- the deferral verdict as pre-registered (e4_s4c_preregistration.txt §3-§6; E4-S4's bar verbatim). Read-only
over deferral.json, runs/ and the guide reads. -> e4_s4c_table.md, e4_s4c_verdict.json, validity.json.

E4-S4B's analysis (e4_s4b_analysis.py, itself E4-S4's) with THE control and each flagged slot taken from deferral.json:
a slot is judged on its last attempt; clause (c) of an attempt is read against the guide read taken before it; a slot
whose every attempt was link_voided is INCONCLUSIVE on its link clauses ((a)'s loss / rendered / resyncs; (d)'s link
gates), its host clauses still read. Clause (d) uses E4-S2's pass rule (e4_s4c_passrule.py, a copy of E4-S4B's copy)."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("passrule", os.path.join(HERE, "e4_s4c_passrule.py"))
P = importlib.util.module_from_spec(spec)
spec.loader.exec_module(P)
REF_HOST, REF_RENDERED = 10.9, 59.53          # E4-S1 PS1-STREAM
GRAB_S = 5.3                                   # E4-S1 CONC's median grab
SLOTS = ["conc_flag_r1", "conc_flag_r2", "conc_flag_cpu150"]


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


def load(rel):
    p = os.path.join(HERE, rel, "summary.json") if rel else None
    return (json.load(open(p)), os.path.dirname(p)) if p and os.path.exists(p) else (None, None)


def row(s, rd):
    """E4-S4B's row(), unchanged."""
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
    d = json.load(open(os.path.join(HERE, "deferral.json")))
    if d.get("control") is None:
        out = {"verdict": "INCONCLUSIVE (link): no clean control" + (" -- no probe was ever clean" if not d["controls"] else
                                                                       f" in {len(d['controls'])} control(s) launched by clean probes") +
               "; no flagged run", "controls": d["controls"]}
        json.dump(out, open(os.path.join(HERE, "e4_s4c_verdict.json"), "w"), indent=1, default=str)
        json.dump({"controls": [{x: c.get(x) for x in ("run", "status", "flags_absent_after", "apk")} for c in d["controls"]]},
                  open(os.path.join(HERE, "validity.json"), "w"), indent=1)
        print(json.dumps(out, indent=1, default=str))
        return 0
    ctl_s, ctl_rd = load(d["control"]["run"])
    c = row(ctl_s, ctl_rd)
    pick, val, rows, all_voided = {}, {"control": {"run": d["control"]["run"], "status": ctl_s.get("status"),
                                                   "flags_absent_after": k(ctl_s, "teardown", "flags_absent")}}, {"control": c}, {}
    for sl in SLOTS:
        att = d["slots"].get(sl) or []
        if not att:
            pick[sl] = None
            continue
        a = att[-1]
        s, rd = load(a["run"])
        pick[sl] = (a, s, rd)
        all_voided[sl] = all(x["link_voided"] for x in att)
        val[sl] = {"attempts": [{x: y.get(x) for x in ("run", "status", "loss_per_min", "link_voided", "flags_absent_after")} for y in att],
                   "judged_on": a["run"], "valid": bool(s and s.get("status") == "OK" and s.get("window")),
                   "replaced_attempts": len([x for x in os.listdir(rd) if x.startswith("summary_failed_attempt")]) if rd else None,
                   "constraint_lifted": k(s, "teardown", "constraint_lifted")}
        rows[sl] = row(s, rd) if val[sl]["valid"] else None
    json.dump(val, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    out = {"rows": rows, "all_attempts_voided": all_voided}
    if any(pick[sl] is None for sl in SLOTS):
        out["verdict"] = "INCONCLUSIVE (the set never completed before the cap: " + ", ".join(sl for sl in SLOTS if pick[sl] is None) + " not run)"
    elif not all(val[sl]["valid"] for sl in SLOTS):
        out["verdict"] = "INCONCLUSIVE (a run never reached PLAYING after two replacements)"
    else:
        comp = abs(c["host_cpu"] - REF_HOST) <= 2 and abs(c["rendered_fps"] - REF_RENDERED) <= 0.5
        out["comparability"] = {"control_host_cpu": c["host_cpu"], "control_rendered": c["rendered_fps"], "holds": comp}
        cl, link_inc = {}, []
        a_det = []
        for sl in ("conc_flag_r1", "conc_flag_r2"):
            x = rows[sl]
            link_ok = x["loss_per_min"] <= 3 * c["loss_per_min"] and x["loss_per_min"] <= 100 and x["rendered_fps"] >= 59.5 and x["resyncs"] <= 10
            host_ok = abs(x["host_cpu"] - c["host_cpu"]) <= 2
            a_det.append({"run": sl, "link_part": link_ok, "host_part": host_ok, "voided": all_voided[sl]})
            if not link_ok and all_voided[sl]:
                link_inc.append(f"a:{sl}")
        cl["a"] = all((r["link_part"] or r["voided"]) and r["host_part"] for r in a_det)
        bb, cc = [], []
        for sl in SLOTS:
            x = rows[sl]
            dd = x["drain"] or {}
            ld = dd.get("last_drain") or {}
            q = ld.get("queued") or dd.get("pending_at_start") or 0
            ok = (x["samples_with_epg_child"] == 0 and x["grabs_run_in_window"] == 0 and x["deferred_pending_max"] >= 6
                  and dd.get("pending_at_end") == 0 and (ld.get("failed") == 0) and ld.get("ok") == q and q > 0
                  and (ld.get("s") or 1e9) <= 2 * GRAB_S * q)
            bb.append({"run": sl, "holds": ok, "epg_child_samples": x["samples_with_epg_child"], "grabs_in_window": x["grabs_run_in_window"],
                       "pending_max": x["deferred_pending_max"], "queued": q, "drain_ok": ld.get("ok"), "drain_failed": ld.get("failed"),
                       "drain_s": ld.get("s"), "limit_s": round(2 * GRAB_S * q, 1), "cap_fired": dd.get("cap_fired"),
                       "waited_s": dd.get("waited_s")})
            pre = d["guide_reads"][pick[sl][0]["guide_read"]]
            g = dd.get("guide_after") or {}
            okc = g.get("channels_serving") == 6 and pre.get("programmes_total") and \
                abs(g.get("programmes_total", 0) - pre["programmes_total"]) <= 0.05 * pre["programmes_total"]
            cc.append({"run": sl, "holds": bool(okc), "serving": g.get("channels_serving"), "programmes": g.get("programmes_total"),
                       "pre_programmes": pre.get("programmes_total"), "pre_read": pick[sl][0]["guide_read"]})
        cl["b"] = all(x["holds"] for x in bb)
        cl["c"] = all(x["holds"] for x in cc)
        _, s150, rd150 = pick["conc_flag_cpu150"]
        j = P.judge("E1-PS1-STREAM", s150, c["loss_per_min"], rd150)   # judged as a stream row (no grabs ran)
        d_link_only = j["verdict"] != "PASS" and j["failing"] and all(n in P.LINK for n in j["failing"])
        if d_link_only and all_voided["conc_flag_cpu150"]:
            link_inc.append("d:conc_flag_cpu150")
        cl["d"] = j["verdict"] == "PASS" or bool(d_link_only and all_voided["conc_flag_cpu150"])
        un = [rows["conc_flag_r1"], rows["conc_flag_r2"]]
        cl["e"] = all(abs(x["companion_cpu"] - c["companion_cpu"]) <= 2 for x in un)
        out.update({"clauses": cl, "a_detail": a_det, "b_detail": bb, "c_detail": cc, "link_inconclusive": link_inc,
                    "d_detail": {"verdict": j["verdict"], "why": j["why"], "gates": j["gates"],
                                 "throttled_s": rows["conc_flag_cpu150"]["throttled_s"], "usage_cores": rows["conc_flag_cpu150"]["usage_cores"]}})
        if not comp:
            out["verdict"] = "INCONCLUSIVE (the control is outside E1's bands of E4-S1's PS1-STREAM)"
        elif not all(cl.values()):
            out["verdict"] = "REJECTED (" + ", ".join(kk for kk, v in cl.items() if not v) + ")"
        elif link_inc:
            out["verdict"] = "INCONCLUSIVE (link): every host clause holds; link clauses of voided slots unread: " + ", ".join(link_inc)
        elif j["verdict"] == "INCONCLUSIVE":
            out["verdict"] = "INCONCLUSIVE (clause d is link-INCONCLUSIVE; every other clause holds)"
        else:
            out["verdict"] = "ACCEPTED"
    out["control"] = d["control"]
    out["controls"] = d["controls"]
    out["guide_reads"] = d["guide_reads"]
    json.dump(out, open(os.path.join(HERE, "e4_s4c_verdict.json"), "w"), indent=1, default=str)
    names = ["control"] + SLOTS
    md = ["# E4-S4C — grab deferral on the watch's clean window: the table", "",
          "Controls launched by clean probes (clean: loss/min < 10, rendered >= 59.5, resyncs <= 10):", "",
          "| probe | run | loss/min | rendered | resyncs | clean |", "| --- | --- | --- | --- | --- | --- |"]
    md += [f"| {x['probe']} | {x['run']} | {x['loss_per_min']} | {x['rendered_fps']} | {x['resyncs']} | {x['clean']} |" for x in d["controls"]]
    md += ["", "Flagged attempts:", "", "| slot | run | start | loss/min | rendered | resyncs | link_voided |", "| --- | --- | --- | --- | --- | --- | --- |"]
    md += [f"| {sl} | {a['run']} | {a['start_utc']} | {a['loss_per_min']} | {a['rendered_fps']} | {a['resyncs']} | {a['link_voided']} |"
           for sl in SLOTS for a in d["slots"].get(sl) or []]
    md += ["", "| | control (PS1-STREAM, no flag) | CONC + flag r1 | CONC + flag r2 | CONC + flag at 150 % |", "| --- | --- | --- | --- | --- |"]
    for key in ("host_cpu", "companion_cpu", "rendered_fps", "loss_per_min", "resyncs", "underruns", "samples_with_epg_child",
                "grabs_run_in_window", "deferred_rows", "deferred_pending_max", "client_pauses", "controller_pauses",
                "socket_w", "usage_cores", "throttled_s"):
        md.append(f"| {key} | " + " | ".join(str(round(rows[n][key], 2) if isinstance((rows.get(n) or {}).get(key), float) else (rows.get(n) or {}).get(key))
                                            for n in names) + " |")
    md.append("| drain (queued / ok / failed / s) | — | " + " | ".join(
        (lambda dd: f"{dd.get('queued')} / {dd.get('ok')} / {dd.get('failed')} / {dd.get('s')}")((((rows.get(n) or {}).get("drain") or {}).get("last_drain") or {}))
        for n in names[1:]) + " |")
    md += ["", f"**Verdict: {out['verdict']}**", "", "```",
           json.dumps({kk: out.get(kk) for kk in ("comparability", "clauses", "link_inconclusive")}, indent=1), "```"]
    open(os.path.join(HERE, "e4_s4c_table.md"), "w").write("\n".join(md) + "\n")
    print(json.dumps({kk: out.get(kk) for kk in ("verdict", "comparability", "clauses", "link_inconclusive")}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
