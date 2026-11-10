# ART-1R ADDITION 2 — do the fetched records survive a companion start without the art knob?

**Yes — they survive.** No re-fetch was needed; nothing adopted.

- The restart 03:02:16Z (`restart_at.txt`; no game, no movie; the art knob not in the companion: eighteen lines, no
  `PRIVYHUB_ART_SYSTEMS`, `environ_after_restart.txt`); the journal clean (`journal.txt`).
- Its reconcile (`reconcile_after_restart.json`, ~3 s): `SKIPPED_CURRENT`, discovered 271, metadata before 271,
  incomplete before 10 (the art misses: PS1 2, SNES 1, PS2 5, GameCube 2; retried at most once per 7 days), no update.
- `data/games/metadata.json` and `data/games/cheats.json` byte-identical before / after (sha256).
- The read-back after (`readback_after_restart.json`) equals the one after the fetch for all five systems:

| system | records before / after | art files present before / after | API: `box_art_available` true before / after | API: art served (200) before / after |
| --- | --- | --- | --- | --- |
| N64 | 13 / 13 | 13 / 13 | 13 / 13 | 13 / 13 |
| PS2 | 115 / 115 | 100 / 100 | 100 / 100 | 100 / 100 |
| GameCube | 27 / 27 | 24 / 24 | 24 / 24 | 24 / 24 |

- **A later full update without the knob** (the 7-day retry of the 10 incomplete, or a library change) — read from
  the code, not run: for a system without the knob `prepare_system` raises `ProviderUnavailable`, whose match carries
  `preserve_prior`, so the fetched record is kept (`prior_preserved`), not rewritten to `provider_unavailable`. (The
  open item of queue AD stands: a full update drops the records of titles it did not scan, e.g. a drive folder
  unreachable at that moment.)
- **So the art knob need not be in the companion's environment to keep or show the art; HOME-12 needs no bench
  drop-in for C44.**
