---
memory_schema: 1
as_of: 2026-10-16
status: TASK HANDOFF — E4-S4C's record, from the watch's files: stop the link watch cleanly (the user: the LAN loss row is parked; remote first), then write what it saw. Measurement record only
---

# E4-S4C — stop the watch; the record

1. `touch ~/privyhub_link_watch/STOP`; wait for the unit to exit
   (`systemctl --user is-active privyhub-link-watch` → inactive; the
   status file's final line). Copy `status.txt`, `history.csv`,
   `watch.log` into `e4_s4d_2026-10-15/` (the watch's own directory keeps
   its originals; nothing deleted).
2. `evidence/E4_S4C_LINK_WATCH_2026-10-16.md`: every probe in time order
   (local time, loss/min, rendered, resyncs, clean?, the AP's view of the
   client: signal dBm, tx rate, retry %, air utilisation; the client's
   RSSI and link rate; ping loss / RTT before it); the ping trace by
   hour; the deferral: **no clean probe → no control, no flagged run,
   INCONCLUSIVE (link)**, E4-S4's verdict stands; and the reading, stated
   as seen: whether the AP-side signal and tx rate moved between probes
   while the loss did, with the asymmetry (the client's RSSI vs the AP's)
   quoted. No cause claimed beyond what the numbers show.
3. `docs/KNOWN_ISSUES.md` LINK item: parked, with the watch's reading
   and the one hand option the user has (a wired adapter on the client);
   `logs/e4_s4c_git_status.txt`. `manifest.sha256` over the record's
   directory; the redactor.
