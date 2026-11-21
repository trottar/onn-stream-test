---
memory_schema: 1
as_of: 2026-11-20
status: TASK — session G6. Score G6-JOIN1's run as pre-registered (preregistration.md, ce8fdb41…), read only, and record it with the user's remark. No code, no build, no candidate. Nothing adopted; nothing committed by you.
---

# G6-JOIN1 — score the run (read only)

## Preflight (stop and say so if any fails)

- G6-JOIN1 is committed (`git log`), and `git status --short` shows nothing of it.
- No game, gradle or other Claude Code session running.

## Steps

1. Check `docs/memory/evidence/g6_join1_2026-11-20/preregistration.md` still hashes to `ce8fdb41…` (hashed 17:31:57Z).
2. Pick the session by its "Which session" rule, exactly. Cowork's reading, which you must confirm from the raw files:
   - **skipped, older app:** 17:31:58Z → 17:39:15Z, `native_decoder_20261120_173916_032.json` (`stick_mapping` present,
     no `p1_join_via` key: G6-STICK1's app);
   - **scored:** 17:43:11Z → 17:46:46Z, `native_decoder_20261120_174647_052.json`, and its launch's PS2 game log.
3. Score c1–c13 exactly as written, each with its value. Cowork's preview, which you must confirm or correct:
   - c1 met; c2 met (59.51 fps); c3 met (decoder 8 / 13168; video 1 / 13168);
   - **c4 NOT MET**: `max_rx_to_decode_ms` 62 (met) but `max_output_gap_ms` **283** (bound ≤ 250); show the slow-event
     rows behind it as they are;
   - **c5 met**: `touch_slot` 0; `p1_join_via` `"hold"`; `p1_join_hold_ms` 500; `p1_join_after_release_ms` 2530;
   - c6 met (all 16);
   - **c7 NOT MET**: left stick 1 in all four; right stick up **0.823**, down 0.942, left **0.706**, right 1 (≥ 0.9 each);
   - c8 met (one End; bye after ≈ 216 s PLAYING); c9 and c10 met (`1200x900`, `1200x1100`, `"4:3"`,
     `"160,0,960x720"`); c11 from the game log (expected met);
   - **c12 NOT MET**: left 1.0, right **0.93** end to end (≥ 0.95);
   - c13 met.

   The verdict follows the rule: **NOT MET** on c4, c7 and c12, unless your reading differs. Record plainly that the
   change under test, the hold-to-join (c5), was met, and that c7 and c12 are the right stick not pushed fully up, left
   and into a corner in this session (figures only; no cause beyond the files). Context: `touch_writes`, `takeovers`,
   `back_swallowed`, lost packets (2), resyncs (0), link rows, class `remote-direct`.
4. **The user's remark, verbatim (2026-11-20):** "done, worked just as expected". The other remarks were not given:
   record them as not given. Do not ask the user.
5. **Record:** part 2 of `docs/memory/evidence/G6_JOIN1_HOLD_TO_JOIN_2026-11-20.md`; the plan's dated line and
   `CURRENT.md`'s G6 line. Nothing adopted.

## Rules

No code change, no build, no adb, no install, no stream, no restart, nothing fetched; `companion/`, `tools/`, `data/`
untouched. Touch no other session's files and no other prompt file. No address, serial, token or pairing code; device
ids as 4 hex digits and "…"; no game title. `tools/check_memory_health.py` passes. Nothing committed by you.

Your last reply begins "YOU, now: commit", then: the thirteen cells with values and the verdict; the commit command in
session B's style (commit the tree; `logs/` is git-ignored).
