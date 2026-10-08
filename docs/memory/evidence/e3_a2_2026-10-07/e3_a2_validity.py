#!/usr/bin/env python3
"""E3-A2 -- the addendum's validity rule (e3_a2_preregistration_addendum.txt): for each stream run under the given dirs,
any recovery event leaving PLAYING (desync_pause / gave_up_* / a PAUSED_* state) inside its window, from
logs/games/native_stream_recovery.log and its archive. Read-only. -> validity.json in this dir (merged by run dir)."""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
LOGS = sorted(glob.glob(os.path.join(REPO, "logs/games/stream_log_archive/native_stream_recovery.log*"))) + \
    [os.path.join(REPO, "logs/games/native_stream_recovery.log")]


def events():
    seen = set()
    for f in LOGS:
        try:
            lines = open(f, errors="replace").read().splitlines()
        except OSError:
            continue
        for l in lines:
            if l in seen:
                continue
            seen.add(l)
            try:
                r = json.loads(l)
            except ValueError:
                continue
            yield r


def main(dirs):
    ev = list(events())
    path = os.path.join(HERE, "validity.json")
    out = json.load(open(path)) if os.path.exists(path) else {}
    for d in dirs:
        for sp in sorted(glob.glob(os.path.join(d, "*", "run*", "summary.json"))):
            s = json.load(open(sp))
            if s.get("kind") != "stream" or not s.get("window"):
                continue
            t0, t1 = s["window"]["from"], s["window"]["to"]
            bad = [{"at_utc": r.get("at_utc"), "event": r.get("event"), "state": r.get("state"), "trigger": r.get("trigger")}
                   for r in ev if t0 <= (r.get("at_utc") or "") <= t1
                   and (r.get("event") in ("desync_pause",) or str(r.get("event", "")).startswith("gave_up")
                        or str(r.get("state", "")).startswith("PAUSED"))]
            rel = os.path.relpath(os.path.dirname(sp), HERE)
            out[rel] = {"window": [t0, t1], "valid": not bad, "events": bad}
    json.dump(out, open(path, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or [os.path.join(HERE, "runs")]))
