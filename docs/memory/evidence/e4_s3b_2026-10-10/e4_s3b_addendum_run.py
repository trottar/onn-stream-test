#!/usr/bin/env python3
"""E4-S3B addendum (e4_s3b_addendum.txt §B): E1-CONC at 1536M then (only if it does not hold) 2G, swap off; judged by
e4_s3b_ladder.py's judge() with the same control, plus the run-span kill reading. -> addendum.json"""
import importlib.util, json, os, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("ladder", os.path.join(HERE, "e4_s3b_ladder.py"))
L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)
P = os.path.join(HERE, "addendum.json")


def main():
    st = L.load()
    ctl = st["control"]["video_loss_per_min"]
    ad = json.load(open(P)) if os.path.exists(P) else {"control_loss_per_min": ctl, "steps": []}
    m = L.suite_mod()
    for step in ("1536M", "2G"):
        if any(x["step"] == step for x in ad["steps"]):
            if ad["steps"][-1]["holds"]:
                break
            continue
        cons = [f"MemoryMax={step}", "MemorySwapMax=0"]
        L.log(f"addendum step {step}: E1-CONC {'+'.join(cons)}")
        stop = threading.Event()
        rb = L.readback_thread(f"addendum:{step}", stop)
        with open(os.path.join(HERE, "runs_console.log"), "a") as fh:
            import subprocess
            subprocess.run([sys.executable, L.SUITE, "run", "--out", L.OUT, "--prereg", L.PRE, "--e2", "--window", "1200",
                            "--gap", "120", "--plan", f"E1-CONC:1:120::{'+'.join(cons)}"], stdout=fh, stderr=subprocess.STDOUT)
        stop.set(); rb.join(timeout=90)
        import shutil
        shutil.copy(os.path.join(L.OUT, "final_state.json"), os.path.join(L.OUT, f"final_state_addendum_{step}.json"))
        sp = L.latest_summary("E1-CONC", cons)
        s = json.load(open(os.path.join(HERE, sp))) if sp else None
        j = L.judge("E1-CONC", s, ctl, os.path.dirname(os.path.join(HERE, sp)) if sp else None)
        span = m.journal_kills(s["gap"]["from"], s["window"]["to"]) if s and s.get("window") and s.get("gap") else None
        link_only = j["verdict"] == "INCONCLUSIVE" and not j.get("missing") and all(n in L.LINK for n in j["failing"])
        holds = (j["verdict"] == "PASS" or link_only) and span is not None and span["count"] == 0
        ad["steps"].append({"step": step, "constraint": cons, "summary": sp, "verdict": j["verdict"], "why": j["why"],
                            "failing": j["failing"], "missing": j.get("missing"), "run_span_kills": span, "holds": holds,
                            "judged": j})
        json.dump(ad, open(P, "w"), indent=1, default=str)
        L.log(f"  addendum {step}: verdict {j['verdict']} ({j['why']}); run-span kills {span and span['count']}; HOLDS {holds}")
        if holds:
            break
    ad["conc_floor_addendum"] = next((x["step"] for x in ad["steps"] if x["holds"]), "above 2G")
    json.dump(ad, open(P, "w"), indent=1, default=str)
    L.log("addendum done:", ad["conc_floor_addendum"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
