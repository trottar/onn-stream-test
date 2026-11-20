---
memory_schema: 1
as_of: 2026-11-20
status: TASK — session G6. Score G6-STICK1's run as pre-registered (preregistration_v2.md, 3cb6fe05…), read only, and record it with the user's remarks. No code, no build, no candidate. Nothing adopted; nothing committed by you.
---

# G6-STICK1 — score the run (read only)

## Preflight (stop and say so if any fails)

- G6-STICK1 is committed (`git log`), and `git status --short` shows nothing of it.
- No game, gradle or other Claude Code session running.

## Steps

1. Check `docs/memory/evidence/g6_stick1_2026-11-20/preregistration_v2.md` still hashes to `3cb6fe05…` (hashed
   16:56:07Z).
2. Pick the session by its "Which session" rule, exactly. Cowork's reading, which you must confirm from the raw files:
   decoder report `logs/games/decoder_sessions/native_decoder_20261120_171554_547.json`
   (`stick_mapping` `"ds2-square-0.75-c1.33"`); the recovery log's `session_started` 17:11:42.363Z →
   `session_end_bye` 17:15:54.413Z; its launch's game log `logs/games/20261120-121123-ps2.log` (17:11:23Z). Say whether
   any session after the hash and before it showed this mapping (Cowork found none).
3. Score c1–c13 exactly as written, each with its value. Cowork's preview, which you must confirm or correct:
   - c1 met (OMX.Exynos.avc.dec, hardware, low latency); c2 met (60.12 fps);
     c3 met (decoder 51 / 15885; video 0 / 15885);
   - **c4 NOT MET**: `max_rx_to_decode_ms` **126** (bound ≤ 100); `max_output_gap_ms` 148 (≤ 250, met). The
     `slow_events_top_latency` rows over 100 ms sit at elapsed 3.28–3.34 s and 7.31–7.38 s, mostly `feed_delay_ms`
     (73–108); report them as they are and do not explain them beyond what the files show;
   - c5 met (slot 0; join 5021 ms); c6 met (all 16); c7 met (every direction ≥ 0.999);
     c8 met (one End; bye after ≈ 252 s PLAYING); c9 met (`1200x900`, `1200x1100`); c10 met (`"4:3"`,
     `"160,0,960x720"`); c11 met (the handheld line at 17:11:23.423Z); c12 met (left 0.992, right 1.0 end to end);
     c13 met.

   The verdict follows the rule: **NOT MET on c4 alone**, unless your reading of the files differs. Context:
   `touch_writes` 7556, `takeovers` 0, `back_swallowed` 0, lost packets 0, resyncs 0, no link notice, class
   `remote-direct`, `stick_edge_frac` left 0.657 / right 0.668, `stick_mag_hist`.
4. Compare c4's figure with the earlier handheld sessions' `max_rx_to_decode_ms` (G6-HM3, HM4, HM4b and the
   2026-11-20 free play): a table, figures only. G6-STICK1 changed no decode code; say so from the diff.
5. **The user's remark, verbatim (2026-11-20):** "Done, it feels a lot better. Much more smooth and responsive". The
   other remarks were not given: record them as not given. Do not ask the user.
6. **Record:** part 2 of `docs/memory/evidence/G6_STICK1_DUALSHOCK2_FEEL_2026-11-20.md`; the plan's dated line and
   `CURRENT.md`'s G6 line. Nothing adopted.

## Rules

No code change, no build, no adb, no install, no stream, no restart, nothing fetched; `companion/`, `tools/`, `data/`
untouched. Touch no other session's files and no other prompt file. No address, serial, token or pairing code; device
ids as 4 hex digits and "…"; no game title. `tools/check_memory_health.py` passes. Nothing committed by you.

Your last reply begins "YOU, now: commit", then: the thirteen cells with values and the verdict; the c4 comparison
table; the commit command in session B's style (commit the tree; `logs/` is git-ignored).
