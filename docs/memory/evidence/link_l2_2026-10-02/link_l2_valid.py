#!/usr/bin/env python3
"""LINK-L2 -- is a hold valid under the pre-registration's shadow clause? Read-only.

    link_l2_valid.py <runs dir> <hold>      prints one line; exit 0 VALID, 1 EXCLUDED, 2 NO DATA

VALID when all of:
  * the disable route answered ok (disable_<hold>.json);
  * the status re-read after it (abr_after_disable_<hold>.json) reads adaptive_bitrate mode shadow, acts false;
  * the status at the end of the hold, before BACK (status_end_<hold>.json), reads mode shadow, acts false,
    transitions_this_session 0;
  * the decision log sliced to the hold (decision_log_<hold>.jsonl) has no row with acted true and no
    transition / transition_done row.
Otherwise EXCLUDED (the controller acted, or shadow was not confirmed), with the reason.
"""
import json, os, sys

R, h = sys.argv[1], sys.argv[2]


def load(name):
    p = os.path.join(R, name)
    try:
        return json.load(open(p))
    except Exception:
        return None


d, after, end = load(f"disable_{h}.json"), load(f"abr_after_disable_{h}.json"), load(f"status_end_{h}.json")
if after is None or end is None:
    print(f"{h} NO DATA (disable/after/end status missing)")
    sys.exit(2)
a = after.get("adaptive_bitrate") or {}
e = end.get("adaptive_bitrate") or {}
rows = []
p = os.path.join(R, f"decision_log_{h}.jsonl")
if os.path.exists(p):
    for line in open(p, errors="replace"):
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
acted = [r for r in rows if r.get("acted") is True or r.get("event") in ("transition", "transition_done")]
why = []
if not (d or {}).get("ok"):
    why.append("disable route did not answer ok")
if not (a.get("mode") == "shadow" and a.get("acts") is False):
    why.append(f"after disable: mode {a.get('mode')} acts {a.get('acts')}")
if not (e.get("mode") == "shadow" and e.get("acts") is False and (e.get("transitions_this_session") or 0) == 0):
    why.append(f"end of hold: mode {e.get('mode')} acts {e.get('acts')} transitions {e.get('transitions_this_session')}")
if acted:
    why.append(f"{len(acted)} decision-log rows acted/transition")
ev = {}
for r in rows:
    ev[r.get("event")] = ev.get(r.get("event"), 0) + 1
if why:
    print(f"{h} EXCLUDED: " + "; ".join(why) + f" | decision log {len(rows)} rows {json.dumps(ev)}")
    sys.exit(1)
print(f"{h} VALID: disable ok, shadow / acts false after it and at the end, 0 transitions, 0 acted rows "
      f"| decision log {len(rows)} rows {json.dumps(ev)}")
