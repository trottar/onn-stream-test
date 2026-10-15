#!/usr/bin/env python3
"""E4-S3 -- the memory floor, analysed as pre-registered (e4_s3_preregistration.txt §2-§4). Read-only over runs/ and
ladder.json. -> e4_s3_ladder_table.md, e4_s3_memory.md (the cgroup per run), e4_s3_floor.md, validity.json,
e4_s3_verdict.json. Every run is re-judged with e4_s3_ladder.py's code; any disagreement is printed."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ladder", os.path.join(HERE, "e4_s3_ladder.py"))
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)
CAVEAT = ("MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs "
          "with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for "
          "the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, "
          "pulseaudio, the desktop and the OS are outside it.")
SHORT = {"E1-PS1-STREAM": "PS1-STREAM", "E1-SNES-STREAM": "SNES-STREAM", "E1-CONC": "CONC", "E1-META": "META"}


def f(v, nd=1):
    if v is None:
        return "—"
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, float):
        return f"{v:,.{nd}f}"
    return f"{v:,}" if isinstance(v, int) else str(v)


def main():
    st = json.load(open(L.STATE))
    control = (st.get("control") or {}).get("video_loss_per_min")
    runs, disagree, val = [], [], {}
    for r in st["runs"]:
        sp = os.path.join(HERE, r["summary"]) if r["summary"] else None
        s = json.load(open(sp)) if sp else None
        rd = os.path.dirname(sp) if sp else None
        j = L.judge(r["row"], s, control, rd)
        if j["verdict"] != r["verdict"]:
            disagree.append([r["step"], r["row"], r["verdict"], j["verdict"]])
        runs.append(dict(r, judged=j, s=s or {}, rd=rd))
        s = s or {}
        td = s.get("teardown") or {}
        val[f"{r['step']} {r['row']}"] = {
            "summary": r["summary"], "status": s.get("status"), "valid": s.get("status") == "OK",
            "replaced_attempts": len([x for x in os.listdir(rd) if x.startswith("summary_failed_attempt")]) if rd else None,
            "constraint": r["constraint"],
            "readback_under": {k: (s.get("constraint_readback") or {}).get(k) for k in
                               ("MemoryMax", "MemorySwapMax", "CPUQuotaPerSecUSec", "memory.max", "memory.swap.max", "cpu.max")},
            "readback_after": {k: (td.get("constraint_readback_after") or {}).get(k) for k in
                               ("MemoryMax", "MemorySwapMax", "CPUQuotaPerSecUSec", "memory.max", "memory.swap.max", "dropin_present")},
            "constraint_lifted": td.get("constraint_lifted"), "flags_absent": td.get("flags_absent"),
            "membership": [s.get("cgroup_membership"), s.get("cgroup_membership_end")],
            "controller_pauses": j["metrics"].get("controller_pauses"), "client_pauses_reported": j["metrics"].get("client_pauses")}
    json.dump(val, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    G = ["rendered_fps", "retroarch_fps", "capture_fps", "spikes_20ms_per_min", "stale_drops_per_min", "encoder_dupdrop_per_min",
         "grabs_failed", "grabs_ok_min_per_channel", "guide_serves", "no_oom_kill", "no_journal_kill", "unit_not_restarted"]
    md = [f"# E4-S3 — the memory ladder, every run\n\n**{CAVEAT}**\n",
          f"Control (the first PS1-STREAM, at 768M) video loss/min: {f(control)} -> the link "
          f"{'FAILS' if control is not None and control >= 10 else 'holds'} D-BASE's loss row.\n",
          "| step | row | constraint | verdict | failing | " + " | ".join(G) + " | loss/min | grab median s |",
          "| --- | --- | --- | --- | --- |" + " --- |" * (len(G) + 2)]
    for r in runs:
        j = r["judged"]
        gv = [("**" + f(j["gates"][g]["value"], 2) + "**") if g in j["gates"] and not j["gates"][g]["passes"]
              else (f(j["gates"][g]["value"], 2) if g in j["gates"] else "") for g in G]
        md.append(f"| {r['step']} | {SHORT[r['row']]} | {'+'.join(r['constraint'])} | **{j['verdict']}** | {', '.join(j['failing']) or '—'} | "
                  + " | ".join(gv) + f" | {f(j['metrics'].get('video_loss_per_min'))} | {f(j['metrics'].get('grab_s_median'), 2)} |")
    open(os.path.join(HERE, "e4_s3_ladder_table.md"), "w").write("\n".join(md) + "\n")
    md = [f"# E4-S3 — the cgroup's memory per run\n\n**{CAVEAT}**\n",
          "| step | row | memory.current mean / max MB | memory.peak MB | anon / file MB at the peak | anon max MB | swap MB | events high / max / oom / oom_kill | PSI some / full ms/s | major faults | companion PSS MB |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in runs:
        c = ((r["s"].get("key") or {}).get("cgroup")) or {}
        m = r["judged"]["metrics"]
        md.append(f"| {r['step']} | {SHORT[r['row']]} | {f(c.get('memory_current_mean_mb'))} / {f(c.get('memory_current_max_mb'))} | "
                  f"{f(c.get('memory_peak_mb'))} | {f(c.get('anon_mb_at_peak'))} / {f(c.get('file_mb_at_peak'))} | {f(c.get('anon_mb_max'))} | "
                  f"{f(c.get('swap_current_max_mb'))} | {c.get('memory_events_high')} / {c.get('memory_events_max')} / "
                  f"{c.get('memory_events_oom')} / {c.get('memory_events_oom_kill')} | {f(c.get('memory_psi_some_ms_per_s'), 2)} / "
                  f"{f(c.get('memory_psi_full_ms_per_s'), 2)} | {c.get('pgmajfault')} | {f(m.get('companion_pss_mb'))} |")
    open(os.path.join(HERE, "e4_s3_memory.md"), "w").write("\n".join(md) + "\n")
    v = L.final_verdicts(st, "mem")
    floor = {}
    for row in L.ROWS:
        fl, cond = L.floor_of(L.MEM, v, row)
        at = lambda step: next((r for r in reversed(runs) if r["row"] == row and r["step"].split(":")[-1] == step), None)
        below = None if fl is None else (L.MEM[L.MEM.index(fl) + 1] if L.MEM.index(fl) + 1 < len(L.MEM) else None)
        first_fail = at(L.MEM[0]) if fl is None else (at(below) if below else None)
        a = at(fl) if fl else None
        c = ((a["s"].get("key") or {}).get("cgroup") or {}) if a else {}
        floor[row] = {"floor": fl,
                      "floor_text": (f"{fl}" if fl and below else f"<= {fl} (384M passed)" if fl
                                     else "above 768M (failed at 768M; E4-S2 passed 1G with swap)" if v.get((row, "768M")) == "FAIL"
                                     else "not determined"),
                      "inconclusive_steps": cond, "cpu_quota": L.CPU_Q[row],
                      "at_floor": {k: c.get(k) for k in ("memory_current_max_mb", "memory_peak_mb", "anon_mb_at_peak",
                                                          "file_mb_at_peak", "anon_mb_max", "memory_events_max",
                                                          "memory_psi_some_ms_per_s", "memory_psi_full_ms_per_s")},
                      "step_below": None if not first_fail else {"step": first_fail["step"], "verdict": first_fail["verdict"],
                                                                 "failing": first_fail["failing"],
                                                                 "values": {g: first_fail["judged"]["gates"][g]["value"]
                                                                            for g in first_fail["failing"] if g in first_fail["judged"]["gates"]}}}
    order = L.MEM[::-1]   # 384M < 512M < 768M
    fls = [x["floor"] for x in floor.values()]
    stack = None if any(x is None for x in fls) else max(fls, key=order.index)
    md = [f"# E4-S3 — the memory floor\n\n**{CAVEAT}**\n",
          "| row | memory floor (CPU quota) | INCONCLUSIVE above it | at the floor: max / peak MB, anon / file MB at the peak, max events, PSI some / full | the step below: verdict, failing (value) |",
          "| --- | --- | --- | --- | --- |"]
    for row, x in floor.items():
        a = x["at_floor"]
        b = x["step_below"]
        md.append(f"| {SHORT[row]} | **{x['floor_text']}** ({x['cpu_quota'] or 'CPU unset'}{' %' if x['cpu_quota'] else ''}) | "
                  f"{', '.join(x['inconclusive_steps']) or '—'} | {f(a.get('memory_current_max_mb'))} / {f(a.get('memory_peak_mb'))}; "
                  f"{f(a.get('anon_mb_at_peak'))} / {f(a.get('file_mb_at_peak'))}; {a.get('memory_events_max')}; "
                  f"{f(a.get('memory_psi_some_ms_per_s'), 2)} / {f(a.get('memory_psi_full_ms_per_s'), 2)} | "
                  f"{(b['step'] + ': ' + b['verdict'] + ', ' + ', '.join(f'{g} ({f(val, 2)})' for g, val in b['values'].items())) if b else '—'} |")
    md += ["", f"**The stack's memory floor** (max over rows, swap off): {stack or 'not determined (a row has no floor in this ladder)'}."]
    open(os.path.join(HERE, "e4_s3_floor.md"), "w").write("\n".join(md) + "\n")
    out = {"caveat": CAVEAT, "control_video_loss_per_min": control, "floor": floor, "stack_memory_floor": stack,
           "steps": st["steps"], "runs": [{k: r[k] for k in ("step", "row", "constraint", "summary", "verdict", "why", "failing")} for r in runs],
           "rejudge_disagreements": disagree}
    json.dump(out, open(os.path.join(HERE, "e4_s3_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps({"stack_memory_floor": stack, "floors": {SHORT[r]: x["floor_text"] for r, x in floor.items()},
                      "rejudge_disagreements": disagree}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
