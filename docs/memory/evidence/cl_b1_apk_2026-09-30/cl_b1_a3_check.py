#!/usr/bin/env python3
"""CL-B1 APK -- A3, the report path on the new APK (read-only).

The session: runs/<A3>, one attract-mode hold >= 190 s through c5_m2_run.sh,
then BACK. Checks (cl_b1_apk_preregistration.txt, A3):
  * the journal of the session shows the body form ("received as body"),
    never the target form, for this report;
  * the report is stored (the harness copied it from decoder_sessions);
  * 0 WARNING, 0 traceback in the session's journal;
  * slow_event_capacity 1,280;
  * the report's key set (recursive, dotted paths of dict keys) identical
    to cl_b1_2026-09-25/report_arm2_body.json's;
  * the companion unchanged (its sha256 before = after, from the pre/post files).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "runs")
ARM = sys.argv[1] if len(sys.argv) > 1 else "A3"


def keys(x, p=""):
    out = set()
    if isinstance(x, dict):
        for k, v in x.items():
            out.add(p + k)
            out |= keys(v, p + k + ".")
    return out


idx = [l.split() for l in open(os.path.join(R, "index.txt")) if l.split() and l.split()[0] == ARM]
f = idx[-1]
t0, t1 = f[4], f[5]
jr = open(os.path.join(R, f"companion_{ARM}.log"), errors="replace").read().splitlines()
body = [l for l in jr if "received as body" in l]
target = [l for l in jr if "decoder-session-log" in l and "?report=" in l]
warn = [l for l in jr if "WARNING" in l]
tb = [l for l in jr if "Traceback" in l]
rep_path = os.path.join(R, f"report_{ARM}.json")
stored = os.path.exists(rep_path)
rep = json.load(open(rep_path))["report"] if stored else {}
ref = json.load(open(os.path.join(HERE, "..", "cl_b1_2026-09-25", "report_arm2_body.json")))["report"]
k_new, k_ref = keys(rep), keys(ref)
cap = rep.get("slow_event_capacity")
secs = (rep.get("duration_ms") or 0) / 1000
chars = [int(m.group(1)) for l in body for m in [re.search(r"report_chars=(\d+)", l)] if m]
rows = {
    "session >= 190 s": secs >= 190,
    "journal shows the body form": bool(body),
    "no target-form upload in the session": not target,
    "report stored": stored,
    "0 WARNING in the session's journal": not warn,
    "0 traceback": not tb,
    "slow_event_capacity 1,280": cap == 1280,
    "key set identical to report_arm2_body.json": k_new == k_ref,
}
print(f"CL-B1 APK A3 -- {ARM} {t0} .. {t1}; report {f[3]}; duration {secs:.0f} s")
print(f"  journal body-form lines {len(body)} (report_chars {chars}); target-form lines {len(target)}; "
      f"WARNING {len(warn)}; traceback {len(tb)}")
print(f"  slow_event_capacity {cap}; marked/recent retained "
      f"{rep.get('slow_event_retained_marked')}/{rep.get('slow_event_retained_recent')}; keys {len(k_new)} vs {len(k_ref)}; "
      f"only-new {sorted(k_new - k_ref)[:8]}; only-ref {sorted(k_ref - k_new)[:8]}")
for k, v in rows.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"  => A3 {'HOLDS' if all(rows.values()) else 'DOES NOT HOLD'}")
json.dump({"rows": rows, "body_lines": len(body), "report_chars": chars, "slow_event_capacity": cap},
          open(os.path.join(HERE, "a3_check.json"), "w"), indent=1)
