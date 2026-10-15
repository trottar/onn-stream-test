#!/usr/bin/env python3
"""E4-S2 -- the floor, analysed as pre-registered (e4_s2_preregistration.txt §3-§5). Read-only over runs/ and ladder.json.

    e4_s2_analysis.py  -> e4_s2_ladder_table.md, e4_s2_floor.md, e4_s2_throttle.md, e4_s2_tables.md (E2's full table
                          per row: the E4-S1 reference then every step), validity.json, e4_s2_verdict.json (the gap
                          and recovery slices are each run's gaps.jsonl / recovery.jsonl)

The verdicts are e4_s2_ladder.py's (recorded in ladder.json as each step ran); every run is re-judged here with the
same code and any disagreement is printed. The table code is a copy of e4_s1_2026-10-09/e4_s1_analysis.py's
(e4_s2_tablecopy.py, beside this file), not an import of the other task's script.
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "e4_s1_2026-10-09", "runs")
OUTD = os.environ.get("E4S2_OUT", HERE)   # outputs (a scratch dir for a dry run while the ladder runs)


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


L = load("ladder", "e4_s2_ladder.py")
T = load("tablecopy", "e4_s2_tablecopy.py")
CAVEAT = ("CPUQuota= is CFS bandwidth: the stack gets at most N % of one core's time per period, on full-speed cores. "
          "This is a CPU-TIME floor, not a slow-core floor: a machine with fewer, equally fast cores behaves like this; "
          "a machine with slower cores does not, exactly. No lower-tier hardware claim.")
SHORT = {"E1-PS1-STREAM": "PS1-STREAM", "E1-SNES-STREAM": "SNES-STREAM", "E1-CONC": "CONC", "E1-META": "META"}


def f(v, nd=1):
    return T.f(v, nd)


def main():
    st = json.load(open(L.STATE))
    control = (st.get("control") or {}).get("video_loss_per_min")
    runs = []
    disagree = []
    for r in st["runs"]:
        sp = os.path.join(HERE, r["summary"]) if r["summary"] else None
        s = json.load(open(sp)) if sp else None
        j = L.judge(r["row"], s, control, os.path.dirname(sp) if sp else None)
        if j["verdict"] != r["verdict"]:
            disagree.append([r["step"], r["row"], r["verdict"], j["verdict"]])
        runs.append(dict(r, judged=j, s=s, rd=os.path.dirname(sp) if sp else None))
    # ---- validity
    val = {}
    for r in runs:
        s = r["s"] or {}
        failed = len([x for x in os.listdir(r["rd"]) if x.startswith("summary_failed_attempt")]) if r["rd"] else None
        val[f"{r['step']} {r['row']}"] = {
            "summary": r["summary"], "status": s.get("status"), "valid": s.get("status") == "OK",
            "replaced_attempts": failed, "constraint": r["constraint"],
            "readback_under": {k: (s.get("constraint_readback") or {}).get(k) for k in
                               ("CPUQuotaPerSecUSec", "CPUQuotaPeriodUSec", "MemoryMax", "cpu.max", "memory.max")},
            "readback_after": {k: ((s.get("teardown") or {}).get("constraint_readback_after") or {}).get(k) for k in
                               ("CPUQuotaPerSecUSec", "MemoryMax", "cpu.max", "memory.max", "dropin_present")},
            "constraint_lifted": (s.get("teardown") or {}).get("constraint_lifted"),
            "flags_absent": (s.get("teardown") or {}).get("flags_absent"),
            "membership": [s.get("cgroup_membership"), s.get("cgroup_membership_end")],
            "controller_pauses": r["judged"]["metrics"].get("controller_pauses"),
            "client_pauses_reported": r["judged"]["metrics"].get("client_pauses")}
    json.dump(val, open(os.path.join(OUTD, "validity.json"), "w"), indent=1)
    # ---- the ladder table
    G = ["rendered_fps", "retroarch_fps", "capture_fps", "spikes_20ms_per_min", "stale_drops_per_min",
         "encoder_dupdrop_per_min", "grabs_failed", "grabs_ok_min_per_channel", "guide_serves"]
    R = ["video_loss_per_min", "resyncs", "underruns", "usage_cores", "throttled_s", "throttled_period_frac",
         "memory_current_max_mb", "swap_current_max_mb", "memory_events_max", "oom_kill_run", "bitrate_kbps_min",
         "bitrate_kbps_max", "transitions", "encoder_segments", "capture_fps_sampler_first_to_last", "grab_s_median",
         "host_cpu", "socket_w", "tctl", "controller_pauses", "client_pauses"]
    md = [f"# E4-S2 — the ladder, every run\n\n**{CAVEAT}**\n",
          f"Control (400 % PS1-STREAM) video loss/min: {f(control)} -> the link {'FAILS' if control is not None and control >= 10 else 'holds'} D-BASE's loss row.\n",
          "| step | row | constraint | verdict | failing | " + " | ".join(G) + " | " + " | ".join(R) + " |",
          "| --- | --- | --- | --- | --- |" + " --- |" * (len(G) + len(R))]
    for r in runs:
        j = r["judged"]
        gv = [("**" + T.cell(j["gates"][g]["value"]) + "**") if g in j["gates"] and not j["gates"][g]["passes"]
              else (T.cell(j["gates"][g]["value"]) if g in j["gates"] else "") for g in G]
        md.append(f"| {r['step']} | {SHORT[r['row']]} | {'+'.join(r['constraint'])} | **{j['verdict']}** | "
                  f"{', '.join(j['failing']) or '—'} | " + " | ".join(gv) + " | " +
                  " | ".join(T.cell(j["metrics"].get(x)) for x in R) + " |")
    open(os.path.join(OUTD, "e4_s2_ladder_table.md"), "w").write("\n".join(md) + "\n")
    # ---- throttle stats
    md = [f"# E4-S2 — the cgroup per run (how much the quota bit)\n\n**{CAVEAT}**\n",
          "| step | row | constraint | CPU used (cores) | periods | throttled periods | share | throttled s (20 min) | "
          "memory.current mean / max MB | memory.peak MB | swap max MB | events high / max / oom / oom_kill |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in runs:
        c = ((r["s"] or {}).get("key") or {}).get("cgroup") or {}
        md.append(f"| {r['step']} | {SHORT[r['row']]} | {'+'.join(r['constraint'])} | {f(c.get('usage_cores'), 3)} | "
                  f"{c.get('nr_periods')} | {c.get('nr_throttled')} | {f(c.get('throttled_period_frac'), 3)} | "
                  f"{f(c.get('throttled_s'))} | {f(c.get('memory_current_mean_mb'))} / {f(c.get('memory_current_max_mb'))} | "
                  f"{f(c.get('memory_peak_mb'))} | {f(c.get('swap_current_max_mb'))} | {c.get('memory_events_high')} / "
                  f"{c.get('memory_events_max')} / {c.get('memory_events_oom')} / {c.get('memory_events_oom_kill')} |")
    open(os.path.join(OUTD, "e4_s2_throttle.md"), "w").write("\n".join(md) + "\n")
    # ---- the full table per row: the E4-S1 reference, then every step
    out_md = [f"# E4-S2 — E2's full table per row (the E4-S1 reference, then every step)\n\n**{CAVEAT}**\n"]
    for row in L.ROWS:
        cols = []
        for p in T.runs_of(REF, row):
            s = json.load(open(p))
            s["_rd"] = os.path.dirname(p)
            cols.append(("E4-S1 ref", s))
        for r in runs:
            if r["row"] == row and r["s"]:
                s = dict(r["s"])
                s["_rd"] = r["rd"]
                s["_e4"] = {"gaps": (s.get("key") or {}).get("gaps"), "recovery": (s.get("key") or {}).get("recovery")}
                cols.append((r["step"], s))
        out_md += [f"## {row}", "", "| metric | " + " | ".join(c for c, _ in cols) + " |", "| --- |" + " --- |" * len(cols)]
        for name, fn in T.TABLE:
            row_cells = [name]
            for _, s in cols:
                try:
                    row_cells.append(T.cell(fn(s)) if s.get("status") == "OK" else str(s.get("status")))
                except Exception:  # noqa: BLE001
                    row_cells.append("—")
            out_md.append("| " + " | ".join(row_cells) + " |")
        out_md.append("")
    open(os.path.join(OUTD, "e4_s2_tables.md"), "w").write("\n".join(out_md) + "\n")
    # ---- the floor
    vc, vm = L.final_verdicts(st, "cpu"), L.final_verdicts(st, "mem")
    floor = {}
    for row in L.ROWS:
        cf, ccond = L.floor_of(L.CPU, vc, row)
        mf, mcond = L.floor_of(L.MEM, vm, row)

        def at(ladder, step):
            c = [r for r in runs if r["row"] == row and r["step"].replace("_repeat", "").split(":")[0] == ladder
                 and r["step"].split(":")[-1] == str(step)]
            return c[-1] if c else None
        below_c = None if cf is None else (L.CPU[L.CPU.index(cf) + 1] if L.CPU.index(cf) + 1 < len(L.CPU) else None)
        first_c = L.CPU[0] if cf is None else None
        fail_c = at("cpu", below_c if below_c else first_c) if (below_c or first_c) else None
        below_m = None if mf is None else (L.MEM[L.MEM.index(mf) + 1] if L.MEM.index(mf) + 1 < len(L.MEM) else None)
        fail_m = at("mem", below_m if below_m else (L.MEM[0] if mf is None else None)) if (below_m or mf is None) else None
        atc = at("cpu", cf) if cf else None
        atm = at("mem", mf) if mf else None
        floor[row] = {
            "cpu_floor_pct": cf, "cpu_floor_text": (f"{cf} %" if cf and below_c else f"<= {cf} % (100 % passed)" if cf
                                                    else "above 400 % (failed at 400 %)" if vc.get((row, "400")) == "FAIL"
                                                    else "not determined"),
            "cpu_inconclusive_steps": ccond,
            "cpu_at_floor": None if not atc else {k: atc["judged"]["metrics"].get(k) for k in
                                                  ("usage_cores", "throttled_s", "throttled_period_frac", "bitrate_kbps_min",
                                                   "transitions", "rendered_fps", "video_loss_per_min")},
            "cpu_step_below": None if not fail_c else {"step": fail_c["step"], "verdict": fail_c["verdict"],
                                                       "first_failing": fail_c["failing"][:1], "failing": fail_c["failing"],
                                                       "values": {g: fail_c["judged"]["gates"][g]["value"] for g in fail_c["failing"]
                                                                  if g in fail_c["judged"]["gates"]}},
            "memory_cpu_quota": (st.get("memory_cpu_quota") or {}).get(row),
            "memory_floor": mf, "memory_floor_text": (f"{mf}" if mf and below_m else f"<= {mf} (1G passed)" if mf
                                                      else "above 4G (failed at 4G)" if vm.get((row, "4G")) == "FAIL"
                                                      else "not determined"),
            "memory_inconclusive_steps": mcond,
            "memory_at_floor": None if not atm else {k: atm["judged"]["metrics"].get(k) for k in
                                                     ("memory_current_max_mb", "memory_peak_mb", "swap_current_max_mb",
                                                      "memory_events_max", "oom_kill_run")},
            "memory_step_below": None if not fail_m else {"step": fail_m["step"], "verdict": fail_m["verdict"],
                                                          "failing": fail_m["failing"]}}
    cfs = [v["cpu_floor_pct"] for v in floor.values()]
    stack_cpu = None if any(x is None for x in cfs) else max(cfs)
    mfs = [v["memory_floor"] for v in floor.values()]
    stack_mem = None if any(x is None for x in mfs) else max(mfs, key=lambda m: L.MEM[::-1].index(m))
    md = [f"# E4-S2 — the floor\n\n**{CAVEAT}**\n",
          "| row | CPU floor | INCONCLUSIVE above it | CPU used / throttled s / share at the floor | the step below: verdict, first failing metric (value) | memory floor (at CPUQuota) | memory at the floor (max MB, swap MB) | the memory step below |",
          "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row, v in floor.items():
        a = v["cpu_at_floor"] or {}
        b = v["cpu_step_below"] or {}
        am = v["memory_at_floor"] or {}
        bm = v["memory_step_below"] or {}
        md.append(f"| {SHORT[row]} | **{v['cpu_floor_text']}** | {', '.join(f'{x} %' for x in v['cpu_inconclusive_steps']) or '—'} | "
                  f"{f(a.get('usage_cores'), 2)} cores / {f(a.get('throttled_s'))} s / {f(a.get('throttled_period_frac'), 3)} | "
                  f"{(b.get('step', '') + ': ' + b.get('verdict', '') + ', ' + ', '.join(f'{g} ({T.cell(x)})' for g, x in (b.get('values') or {}).items())) if b else '—'} | "
                  f"**{v['memory_floor_text']}** (CPUQuota {v['memory_cpu_quota'] or 'unset'}) | "
                  f"{f(am.get('memory_current_max_mb'))}, {f(am.get('swap_current_max_mb'))} | "
                  f"{(bm.get('step', '') + ': ' + bm.get('verdict', '') + ', ' + ', '.join(bm.get('failing') or [])) if bm else '—'} |")
    md += ["", f"**The stack's CPU-time floor** (max over rows): {stack_cpu if stack_cpu is None else str(stack_cpu) + ' %'}; "
               f"**memory floor** (max over rows): {stack_mem}."]
    open(os.path.join(OUTD, "e4_s2_floor.md"), "w").write("\n".join(md) + "\n")
    verdict = {"caveat": CAVEAT, "control_video_loss_per_min": control,
               "control_fails_dbase_loss_row": control is not None and control >= 10,
               "floor": floor, "stack_cpu_floor_pct": stack_cpu, "stack_memory_floor": stack_mem,
               "cpu_floor_by_ladder": st.get("cpu_floor"), "memory_floor_by_ladder": st.get("memory_floor"),
               "memory_cpu_quota": st.get("memory_cpu_quota"), "steps": st["steps"],
               "runs": [{k: r[k] for k in ("step", "row", "constraint", "summary", "verdict", "why", "failing")} for r in runs],
               "rejudge_disagreements": disagree}
    json.dump(verdict, open(os.path.join(OUTD, "e4_s2_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps({"stack_cpu_floor_pct": stack_cpu, "stack_memory_floor": stack_mem,
                      "floors": {SHORT[r]: [v["cpu_floor_text"], v["memory_floor_text"]] for r, v in floor.items()},
                      "rejudge_disagreements": disagree}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
