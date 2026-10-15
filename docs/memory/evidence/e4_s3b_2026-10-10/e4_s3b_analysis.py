#!/usr/bin/env python3
"""E4-S3B -- the memory floor at 1G swap off, analysed as pre-registered (e4_s3b_preregistration.txt §3-§5). Read-only
over runs/, ladder.json and E4-S3's e4_s3_verdict.json. -> e4_s3b_ladder_table.md, e4_s3b_memory.md (the cgroup per
run), e4_s3b_floor.md (the closed four-row table: E4-S3 + this task), validity.json, e4_s3b_verdict.json. A copy of
e4_s3_2026-10-10/e4_s3_analysis.py, changed for this ladder. Every run is re-judged with e4_s3b_ladder.py's code; any
disagreement is printed."""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ladder", os.path.join(HERE, "e4_s3b_ladder.py"))
L = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L)
CAVEAT = ("MemorySwapMax=0: no swap for the stack's cgroup. The floor is the smallest MemoryMax at which the stack runs "
          "with page cache reclaim only; a host with swap would degrade more softly below it. It is a memory floor for "
          "the STACK's cgroup (companion, RetroArch, the encoder, the grabber children), not for the host: Xorg, "
          "pulseaudio, the desktop and the OS are outside it.")
E4S3 = os.path.join(HERE, "..", "e4_s3_2026-10-10", "e4_s3_verdict.json")
MB = {"384M": 384, "512M": 512, "768M": 768, "1G": 1024, "1536M": 1536, "2G": 2048}
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
    AD = json.load(open(os.path.join(HERE, "addendum.json"))) if os.path.exists(os.path.join(HERE, "addendum.json")) else {"steps": []}
    SM = L.suite_mod()
    all_runs = list(st["runs"]) + [{"step": "addendum:" + x["step"], "row": "E1-CONC", "constraint": x["constraint"],
                                    "summary": x["summary"], "verdict": x["verdict"], "why": x["why"], "failing": x["failing"]}
                                   for x in AD["steps"]]
    for r in all_runs:
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
            "run_span_kills": (SM.journal_kills(s["gap"]["from"], s["window"]["to"])["count"]
                               if s and s.get("gap") and s.get("window") else None),
            "summary": r["summary"], "status": s.get("status"), "valid": s.get("status") == "OK",
            "replaced_attempts": len([x for x in os.listdir(rd) if x.startswith("summary_failed_attempt")]) if rd else None,
            "constraint": r["constraint"],
            "readback_under": {k: (s.get("constraint_readback") or {}).get(k) for k in
                               ("MemoryMax", "MemorySwapMax", "CPUQuotaPerSecUSec", "memory.max", "memory.swap.max", "cpu.max")},
            "readback_after": {k: (td.get("constraint_readback_after") or {}).get(k) for k in
                               ("MemoryMax", "MemorySwapMax", "CPUQuotaPerSecUSec", "memory.max", "memory.swap.max", "dropin_present")},
            "constraint_lifted": td.get("constraint_lifted"), "flags_absent": td.get("flags_absent"),
            "membership": [s.get("cgroup_membership"), s.get("cgroup_membership_end")],
            "epg_jsonl_bytes": os.path.getsize(os.path.join(rd, "epg.jsonl")) if rd and os.path.exists(os.path.join(rd, "epg.jsonl")) else None,
            "controller_pauses": j["metrics"].get("controller_pauses"), "client_pauses_reported": j["metrics"].get("client_pauses")}
    json.dump(val, open(os.path.join(HERE, "validity.json"), "w"), indent=1)
    G = ["rendered_fps", "retroarch_fps", "capture_fps", "spikes_20ms_per_min", "stale_drops_per_min", "encoder_dupdrop_per_min",
         "grabs_failed", "grabs_ok_min_per_channel", "guide_serves", "no_oom_kill", "no_journal_kill", "unit_not_restarted"]
    md = [f"# E4-S3B — the memory ladder at 1G swap off, every run\n\n**{CAVEAT}**\n",
          f"Control (PS1-STREAM, unconstrained) video loss/min: {f(control)} -> the link "
          f"{'FAILS' if control is not None and control >= 10 else 'holds'} D-BASE's loss row.\n",
          "| step | row | constraint | verdict | failing | " + " | ".join(G) + " | loss/min | grab median s | fail streaks / attempts | epg.jsonl KB | run-span kills (addendum reading) |",
          "| --- | --- | --- | --- | --- |" + " --- |" * (len(G) + 5)]
    for r in runs:
        j = r["judged"]
        gv = [("**" + f(j["gates"][g]["value"], 2) + "**") if g in j["gates"] and not j["gates"][g]["passes"]
              else (f(j["gates"][g]["value"], 2) if g in j["gates"] else "") for g in G]
        md.append(f"| {r['step']} | {SHORT[r['row']]} | {'+'.join(r['constraint'])} | **{j['verdict']}** | {', '.join(j['failing']) or '—'} | "
                  + " | ".join(gv) + f" | {f(j['metrics'].get('video_loss_per_min'))} | {f(j['metrics'].get('grab_s_median'), 2)} | "
                  + (lambda e: f"{e.get('fail_streaks')} / {e.get('fail_streak_attempts')}" if e else "—")((r["s"].get("key") or {}).get("epg"))
                  + f" | {f(val[r['step'] + ' ' + r['row']]['epg_jsonl_bytes'] / 1024 if val[r['step'] + ' ' + r['row']]['epg_jsonl_bytes'] else None)}"
                  + f" | {val[r['step'] + ' ' + r['row']]['run_span_kills']} |")
    open(os.path.join(HERE, "e4_s3b_ladder_table.md"), "w").write("\n".join(md) + "\n")
    md = [f"# E4-S3B — the cgroup's memory per run\n\n**{CAVEAT}**\n",
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
    open(os.path.join(HERE, "e4_s3b_memory.md"), "w").write("\n".join(md) + "\n")
    v = L.final_verdicts(st, "mem")
    prev = json.load(open(E4S3))["floor"]
    floor = {}
    for row in ("E1-PS1-STREAM", "E1-SNES-STREAM"):            # E4-S3's, unchanged
        p = prev[row]
        floor[row] = {"floor": p["floor"], "source": "E4-S3", "floor_text": p["floor_text"], "cpu_quota": p["cpu_quota"],
                      "at_floor": p["at_floor"],
                      "steps": {"E1-PS1-STREAM": "768M INCONCLUSIVE (link, repeated), 512M INCONCLUSIVE (link, repeated), 384M PASS (E4-S3)",
                                "E1-SNES-STREAM": "768M PASS, 512M PASS, 384M PASS (E4-S3)"}[row]}
    for row in L.ROWS:                                          # CONC, META: E4-S3's 768M FAIL + this ladder
        passed = [m for m in L.MEM if v.get((row, m)) == "PASS"]
        fl = passed[0] if passed else None
        a_run = next((r for r in reversed(runs) if r["row"] == row and r["step"].split(":")[-1] == fl), None) if fl else None
        addendum = row == "E1-CONC" and fl is None and AD.get("conc_floor_addendum") not in (None, "above 2G")
        if addendum:
            fl = AD["conc_floor_addendum"]
            a_run = next(r for r in runs if r["step"] == "addendum:" + fl)
        c = ((a_run["s"].get("key") or {}).get("cgroup") or {}) if a_run else {}
        steps = ["768M FAIL (E4-S3)"] + [f"{m} {v[(row, m)]}" for m in L.MEM if (row, m) in v]
        if row == "E1-CONC":
            steps = (["768M FAIL (E4-S3)", "1G INCONCLUSIVE x2 as judged -- OOM-killed before the window in both (run-span kills 3, 3)"]
                     + [f"{x['step']} {x['verdict']}, run-span kills {x['run_span_kills']['count']} (addendum)" for x in AD["steps"]])
        below = [m for m in L.MEM if (row, m) in v and v[(row, m)] == "FAIL"]
        text = (f"{fl} (ADDENDUM reading: 1G OOM-killed before the window x2; 768M failed)" if addendum
                else f"{fl} (768M failed" + (", " + ", ".join(below) + " failed" if below else "") + ")" if fl
                else "above 2G" if v.get((row, "2G")) == "FAIL"
                else "not determined (" + ", ".join(steps[1:]) + ")")
        floor[row] = {"floor": fl, "source": "E4-S3 + E4-S3B" + (" addendum" if addendum else ""), "floor_text": text, "cpu_quota": L.CPU_Q[row],
                      "at_floor": {k: c.get(k) for k in ("memory_current_max_mb", "memory_peak_mb", "anon_mb_at_peak",
                                                          "file_mb_at_peak", "anon_mb_max", "memory_events_high",
                                                          "memory_events_max", "memory_psi_some_ms_per_s",
                                                          "memory_psi_full_ms_per_s", "swap_current_max_mb")},
                      "steps": "; ".join(steps)}
    fls = [x["floor"] for x in floor.values()]
    stack = None if any(x is None for x in fls) else max(fls, key=lambda m: MB[m])
    md = [f"# E4-S3B — the memory floor, closed (four rows, swap off)\n\n**{CAVEAT}**\n",
          "| row | memory floor, swap off (CPU quota) | steps | at the floor: max / peak MB; anon / file MB at the peak; events high / max; PSI some / full ms/s | from |",
          "| --- | --- | --- | --- | --- |"]
    for row, x in floor.items():
        a = x["at_floor"]
        md.append(f"| {SHORT[row]} | **{x['floor_text']}** ({x['cpu_quota'] or 'CPU unset'}{' %' if x['cpu_quota'] else ''}) | {x['steps']} | "
                  f"{f(a.get('memory_current_max_mb'))} / {f(a.get('memory_peak_mb'))}; "
                  f"{f(a.get('anon_mb_at_peak'))} / {f(a.get('file_mb_at_peak'))}; {a.get('memory_events_high', '—')} / {a.get('memory_events_max')}; "
                  f"{f(a.get('memory_psi_some_ms_per_s'), 2)} / {f(a.get('memory_psi_full_ms_per_s'), 2)} | {x['source']} |")
    md += ["", f"**The stack's swap-off memory floor** (the maximum over the four rows): "
               f"{stack or 'not determined (a row has no floor)'}"
               + (" -- resting on the addendum reading for CONC (e4_s3b_addendum.txt)." if any("addendum" in x["source"] for x in floor.values()) else ".")]
    open(os.path.join(HERE, "e4_s3b_floor.md"), "w").write("\n".join(md) + "\n")
    out = {"caveat": CAVEAT, "control_video_loss_per_min": control, "floor": floor, "stack_memory_floor_swap_off": stack,
           "steps": st["steps"], "runs": [{k: r[k] for k in ("step", "row", "constraint", "summary", "verdict", "why", "failing")} for r in runs],
           "rejudge_disagreements": disagree, "addendum": {k: v for k, v in AD.items() if k != "steps"},
           "addendum_steps": [{k: x[k] for k in ("step", "verdict", "why", "failing", "missing", "run_span_kills", "holds")} for x in AD["steps"]]}
    json.dump(out, open(os.path.join(HERE, "e4_s3b_verdict.json"), "w"), indent=1, default=str)
    print(json.dumps({"stack_memory_floor_swap_off": stack, "floors": {SHORT[r]: x["floor_text"] for r, x in floor.items()},
                      "rejudge_disagreements": disagree}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
