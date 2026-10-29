---
memory_schema: 1
as_of: 2026-10-28
baseline_commit: 42a2ab6
---

# B30 — `tools/trip_log_keeper.py` and `tools/trip_check.py`

**Result: BUILT; 12 + 8 tests green ×3; 2 mutations caught; one read-only `--once` smoke run, the real redactor 0 left;
nothing existing changed; nothing launched.** Record: `evidence/B30_TRIP_LOG_KEEPER_2026-10-28.md`. Diff:
`evidence/b30_2026-10-28/b30.diff`. Nothing committed.

- **The keeper:**
  - every 5 min, G4-S4's logs into new, never-overwritten, redacted chunk files by file and rotation, with a growing
    `manifest.sha256`;
  - every 60 s, the overlay and session samples;
  - `status.txt`, STOP, the cap; it holds nothing open between steps.
- **The check:** six plain lines (adopted, apk, overlay, routing, band, log-keeper), redacted.
- **Launch (A, Thursday):**
  `systemd-run --user --unit privyhub-trip-log --property=WorkingDirectory=<repo> python3 -B tools/trip_log_keeper.py --out docs/memory/evidence/trip_2026-10-30 --cap 2026-11-01T23:59Z`.
- **Rollback:** `touch docs/memory/evidence/trip_2026-10-30/STOP` (it ends with a last copy); the files are new and
  can be left.
