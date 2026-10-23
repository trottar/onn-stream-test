# B14 — the "any house" link notice: design, written before any B14 code

Baseline HEAD 3eb900c (+ B11-B13 uncommitted). Queue: `handoffs/QUEUE_2026-10-23E.md` §B14. Data: LINK-R1 (5 GHz: 0
silences / 0 hitch s per 10 min; 2.4 GHz: 16-22 / 20; RSSI −68 on both bands; tx ≤ 54 Mbps on 0 % of 5-GHz heartbeats,
1.7 % on 2.4 GHz), BENCH-R3 §7 (the tx collapse to 27-81 Mbps beside the 42-silence cluster), the onn on 2.4 GHz at
−68 dBm all month with nobody told.

## 1. The client (`debug.privyhub.link_notice=1`; absent = today: no object, no view, no key)

New `LinkNotice.kt` (pure, JVM-tested); added lines only in `NativeStreamActivity.kt` and `DiagnosticsActivity.kt`.
- **The input:** the client's own link reading (B3's `LinkSample`, `WifiManager.getConnectionInfo()`, no network call),
  through B3's `LinkSampler` (on by default since B13; if the user set `link_report=0`, the notice has its own sampler),
  read on the activity's existing 500-ms UI tick.
- **Shown when** (one evaluation per tick):
  - the band reads **2.4 GHz** (2,400-2,500 MHz) — at once;
  - or **RSSI ≤ −72 dBm for 10 s** continuously;
  - or **tx link rate ≤ 54 Mbps for 10 s** continuously.
- **Cleared when** the link has been good (not 2.4 GHz, RSSI > −72, tx > 54) for **30 s** continuously.
- **At most once per session unless the band changes** (cleared, then bad again on the same band: not shown again; a
  band change: may show again). A new session re-arms it.
- **What it shows** (a small, plain line at the stream's bottom-left, over the picture, not blocking it; and the same
  text, with when it was shown, as one line on the diagnostics page while the app runs):
  - what it sees: `Wi-Fi: 2.4 GHz` / `weak signal (−74 dBm)` / `slow link (48 Mbps)`, joined;
  - the one thing to do: on 2.4 GHz **"Use your router's 5 GHz Wi-Fi for this box."**; else for a weak signal
    "Move this box or the router closer, or use a wired connection."; else "Use the 5 GHz network or move closer to the
    router.";
  - the wording is in the record for the user to edit.
- **No behaviour change to the stream:** nothing is paused, stepped or restarted; no network call; one extra
  `TextView`.
- **The heartbeat** carries `&link_notice=<bits>` (0 = not shown; 1 band 2.4, 2 weak RSSI, 4 slow tx); the report
  carries `link_notice_shown` (count) and `link_notice_last_reasons`.

## 2. The host (rides on `PRIVYHUB_LINK_REPORT=1`, B3's flag — the line G-A3 would adopt)

New `companion/link_notice.py`; guarded statements in `plugins/games.py` and `games/native_stream_heartbeat.py`.
- The heartbeat's `link_notice` is parsed (int) and recorded in the heartbeat row with the link fields.
- **Transitions are logged** in the recovery log: `link_notice_shown` (reasons as bits and names) on 0 → non-zero,
  `link_notice_cleared` on non-zero → 0 — so a record can say the user was told.
- Absent (`PRIVYHUB_LINK_REPORT` unset): nothing imported, no field, no row. With it set and an older client (no
  `link_notice` key): nothing new (byte for byte). B3's shape tests stay as written (the new guards are spelled
  differently).

## 3. Tests

- **JVM `LinkNoticeTest`** with a fake `WifiInfo` feed (`LinkSample` sequences on a fake clock): 2.4 GHz → shown once,
  at once, the text; stays while on 2.4; 5 GHz good for 30 s → cleared (not at 29 s); back on 2.4 → shown again (the
  band changed); cleared then bad again on the same band → not shown; RSSI −72 for 10 s → shown (not at 9.5 s); −71 →
  never; tx 54 for 10 s → shown; a brief dip resets the 10 s; a new session re-arms; the flag table (absent → off);
  the query; null readings change nothing.
- **Host** (`tests/link_notice`): the heartbeat field recorded only with `PRIVYHUB_LINK_REPORT=1`; the transitions → one
  `link_notice_shown`, one `link_notice_cleared`; repeats → no rows; flag absent → no import.
- The APK rebuilt (B5 + B7 + B10 + B11 + B13 + B14), pinned, NOT installed; the client proof (added lines only); the
  host AST proof.
