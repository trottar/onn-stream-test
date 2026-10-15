#!/usr/bin/env python3
"""E4-S4D: e4_s4d_preregistration.txt = an E4-S4D header + E4-S4C's draft verbatim with its placeholders filled
(sha256 of the files as they stand at the hash) + the E4-S4D addendum (the cap, the stop file, the execution model)."""
import hashlib, os
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, "../../../.."))
h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
S4C = os.path.join(HERE, "../e4_s4c_2026-10-10")
fill = {"__EPG__": h(os.path.join(REPO, "companion/plugins/epg.py")), "__SUITE__": h(os.path.join(REPO, "tools/e1_suite.py")),
        "__WATCH__": h(os.path.join(S4C, "e4_s4c_watch.py")), "__OPAL__": h(os.path.join(HERE, "o1_opal_sample.sh")),
        "__RED__": h(os.path.join(HERE, "o1_redact.py")), "__PARSE__": h(os.path.join(HERE, "o1_parse.py")),
        "__P4__": h(os.path.join(HERE, "p4_harvest.py"))}
body = open(os.path.join(HERE, "e4_s4c_preregistration.draft")).read()
for a, b in fill.items():
    body = body.replace(a, b)
assert "__" not in body.replace("__pycache__", ""), "an unfilled placeholder"
head = """E4-S4D PRE-REGISTRATION -- the link watch, DETACHED. Written 2026-10-15 before the first probe; hash in
e4_s4d_preregistration.sha256. Task: docs/memory/handoffs/E4-S4D_LINK_WATCH_DETACHED_TASK.md under QUEUE_2026-10-15.md.
Below, between the rules, E4-S4C's pre-registration (e4_s4c_preregistration.draft, 2026-10-10) VERBATIM, its
placeholders filled with the sha256 of the files as they stand at this hash; then the E4-S4D addendum, which governs
where it differs (the cap, the stop file, the busy skip, the status file, the five-line adopted state, the execution).

==================================================================== E4-S4C §1-§9, verbatim
"""
add = f"""
==================================================================== E4-S4D ADDENDUM (governs where it differs)
A. THE CAP: 2026-10-20T04:00:00Z (replaces E4-S4C's 2026-10-15T04:00:00Z). No probe and no run starts after it; a
   run in flight finishes; then the watch closes.
B. THE STOP FILE: ~/privyhub_link_watch/STOP. If it exists, the probe or run in flight finishes (the runner's own
   teardown), no further probe or run starts, a final status line is written, the watch exits. The watch never
   removes it (to restart the watch, the user removes it).
C. THE BUSY SKIP: a game session active at probe time (the user playing) -> the probe is skipped and recorded busy
   (link_watch.jsonl, history.csv); the next probe is 45 min later. The ping trace continues through it.
D. THE STATUS FILE: ~/privyhub_link_watch/status.txt, one line rewritten after every probe and every run and every
   5 min as a heartbeat; history.csv beside it, one row per probe (E4-S4C's fields); watch.log beside it and the
   journal. Both are copied into e4_s4d_2026-10-15/ by the record task.
E. THE ADOPTED STATE is five lines (E4-S5D, 2026-10-15: live, cached, snes9x, v2, output_rate); every preflight and
   flags_absent read-back uses it (tools/e1_suite.py's ADOPTED; the runner sha256 above is after that one-line
   change, so §0's "unchanged since E4-S3B" reads: unchanged since E4-S3B except E4-S5D's ADOPTED line).
   PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1 is still the only flag the watch sets, for the flagged runs only.
F. THE DRIVER is e4_s4d_watch.py (sha256 {h(os.path.join(HERE, 'e4_s4d_watch.py'))}), e4_s4c_watch.py with A-E
   and the --dry mode added (e4_s4d_watch_vs_e4_s4c.diff); the probe, the readings, the gates, the deferral runs, the
   bar and the storage are E4-S4C's, unchanged. The run directories: probes under ~/privyhub_link_watch/probe_<n>/
   (outside the repo), copies into e4_s4d_2026-10-15/probes/<n>/, the control and flagged runs under
   e4_s4d_2026-10-15/runs/.
G. EXECUTION: systemd-run --user --unit=privyhub-link-watch --collect, WorkingDirectory the repo; not nohup, not a
   child of a Code session. The record of the watch itself is a later task, from the watch's files.
"""
open(os.path.join(HERE, "e4_s4d_preregistration.txt"), "w").write(head + body + add)
print("written")
