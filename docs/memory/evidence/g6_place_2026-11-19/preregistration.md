# G6-PLACE — the grip and placement test (also G6-HM3's re-run): pre-registration, written and hashed before the run

Task: `../../handoffs/G6-HM1B_ANSWERS_SHOULDERS_PLACEMENT_TASK.md`. The user's picks: Q-B5 (c) and Q-HM3 (a)
(`../g6_hm1a_2026-11-19/user_answers_2026-11-19.md`). **Nothing new is built.** The APK on the tablet is still the
G6-HM3 candidate `1d658a3fb96a3281816e1900af54c00479bff74d19fa4281281c0e186d9cf64e`. The onn keeps `ca53df0d…`.

## Before both minutes (the user)

- The tablet on the **travel router's 5 GHz network**, not the home Wi-Fi. The network's name is kept out of this
  record. The logs carry no network name, so this is the user's statement.
- On the tablet: Settings → Location → Location services → **Wi-Fi scanning off**, and **Bluetooth scanning off**
  (the user's statement; not in the logs).
- PrivyHub's "Handheld game screen" on (G6-HM3's Settings choice).
- **The same PS2 game both times.**
- No other session running, the onn not streaming, and outside 03:45–05:30Z (plan §3).

## Minute P1 — G6-HM3's re-run

- The tablet **flat on a table, screen up, within about 1 m of the travel router.**
- G6-HM3's steps exactly. The install and the Settings choice are already done.
  - Start the game.
  - Touch the drawn buttons a few times.
  - **Try Back once:** a swipe in from a side edge, or the Back button.
  - Leave it running for **at least a minute** (about two minutes, for the pattern below).
  - Tap **End.**
- No other touching.
- **Scored with G6-HM3's cells c1–c7, unchanged** (`../g6_hm3_2026-11-19/preregistration.md`, `bcbeff14…`), with the
  bounds as written there.
- **The verdict rule is G6-HM3's:** met when c1–c6 are met and c7 is met for End. c7's Back part is scored too:
  `back_swallowed` ≥ 1, since Back is tried.
- G6-HM3's first run stays on record as NOT MET; P1 is a second, scored run beside it.

## Minute P2 — the grip

- The tablet **held upright in both hands at the user's usual seat,** for at least 60 s (about two minutes, for the
  pattern below), then **End.**
- **No cells.** The figures are recorded for the user's Q-B5 decision.

## Which session is which

- P1 is the first tablet game session that starts after this file's hash time (`preregistration_hashed_at.txt`), and
  P2 is the next one.
- A tablet session is one whose decoder report has `decoder.codec_name` `OMX.Exynos.avc.dec` and a `handheld` block.
- Each is matched across the decoder report (its receipt time), the recovery log (`session_started` →
  `session_end_bye`) and the heartbeat link rows.
- An extra tablet session in between (a false start) is noted and skipped, and the next two count.

## Recorded for both minutes

The heartbeat link rows come from `privyhub-diag`'s raw copies (`~/privyhub_diag/<day>/raw/games__native_stream_heartbeat.log/`,
deduplicated by receipt time), from `session_started` − 10 s to `session_end_bye` + 2 s. The rest comes from the
session's decoder report and the recovery log.

| Figure | Source |
|---|---|
| RSSI median and [min..max] | heartbeat `link_rssi_dbm` |
| rows at −72 dBm or below, of all rows | heartbeat |
| tx median, and rows at 54 Mb/s or below | heartbeat `link_tx_mbps` |
| the band | heartbeat `link_frequency_mhz` |
| `link_notice_shown`, with the reading that tripped it | the recovery log's `link_notice_shown` row (frequency, RSSI, tx) |
| sequence resyncs: the count and their times into the session | the decoder report's `stream_discontinuities` (`sequence_resync`, `elapsed_ms`) |
| stall signals | `stall_signal_stalls_sent` / `stall_signal_ends_sent`; the recovery log's `client_stall` rows |
| `lost_packets` and `lost_packets_in_resyncs` | the decoder report's `video` |
| `max_output_gap_ms` | the decoder report's `decoder` |

## The ~48–50 s pattern (the reading, fixed now)

**The definition.** G6-HM3's first run had resyncs at about 6.9, 57.0, 104.8 / 105.5 and 154.0 s into the session.
- Resyncs less than 1 s apart count as one; 104.8 / 105.5 is one.
- Each minute is classed by its decoder report's `stream_discontinuities` and its `duration_ms`:
  - **present:** two consecutive resyncs (after that merging) are **45–55 s apart**;
  - **absent:** no such pair, over at least **110 s** of `duration_ms` (two periods);
  - **not decidable:** no such pair, over less than 110 s, because one period's resync may fall outside the run.

**The reading:**
- **If either minute is present**, the user's Q-B5 note says: "turning Wi-Fi scanning off did not remove the ~48–50 s
  pattern."
- **If neither is present and at least one is absent** (with Wi-Fi scanning off), the note says: "the ~48–50 s pattern
  went with the Wi-Fi scanning setting in this test." No cause is claimed beyond that.
- **If both are not decidable**, the note says: "not tested (the runs were too short)."
- The user is asked for about two minutes per run so that the reading can be decided. G6-HM3's own step ("at least a
  minute") is unchanged.

**Not claimed by either result:** that scanning caused the pattern; anything about the onn; a choice among Q-B5's (a),
(b) and (d), which stays the user's after these figures.
