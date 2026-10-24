# B19 — the client switches default-on: design, written before any B19 code

Baseline HEAD 7f3f71d + B17 + B18 (uncommitted). Queue: `handoffs/QUEUE_2026-10-24G.md` §B19. Pattern:
`B13_LINK_REPORT_DEFAULT_ON_2026-10-23.md` (`link_report` absent = ON, `0` off).

## 0. Why

The properties are `debug.*` system properties, which a reboot clears. The stack's adoption (B20's umbrella, G-A4)
needs the client half to be on by itself, as `link_report` is since B13. CL-B11 ran with both set; no cell has run
with them empty.

## 1. The design

- **`debug.privyhub.stall_signal`:**
  - absent or empty → **ON at 150 ms** (B7's `1`);
  - `0` → off;
  - `1` / `121`-`2000` as today;
  - any other value → on at 150 (a typo cannot silently disable it, as B13 chose);
  - a failed read → as absent, so on.
- **`debug.privyhub.restart_guard`:** absent / empty / anything but `0` → **ON**; `0` → off; a failed read → on.
- **`debug.privyhub.link_notice`: unchanged, opt-in** (the user's call; it showed when set).
- **The change is two parse functions and their failure branches.** No hook moves. `0` gives exactly the old absent
  value (null / false), so `0` = today byte for byte (the proof).

**Costs when on with no host flag (today's host):**
- **The stall signal:** a 24-byte datagram on the controller socket every 50 ms **only while the output is ≥ 150 ms old
  or the recovery gate stands** (20/s, ~0.5 KB/s, only then), plus one `stall_end`, plus 3 `bye` at a finishing
  session (B18). The monitor's tick runs in the controller loop every ~8 ms (a comparison).
  - **On a host without `PRIVYHUB_STALL_SIGNAL`:** the 24-byte datagram fails the 36-byte size check and is counted in
    the controller's `bad_packets`, before it can touch the silence clock (`_last_any_packet_at` moves only on a valid
    controller packet). **So no pause, no resume, no save: today's behaviour.** B7 / B8 / B12 / B16 are all behind
    the host's flags.
  - The client's report gains `stall_signal_*` keys. B16's fast ready stays armed only by the host's `stall_resume`
    key.
- **The restart guard:**
  - at each surface loss, the report built (today's code already builds it) and written to `noBackupFilesDir`: ~40-50 KB
    (CL-B11's reports 37-50 K chars), a few ms on the UI thread;
  - **at each return:** the start with `guard_end=1`, the old report posted after it, and the audio held until the start
    is answered (B15 / B17).
  - On a host without B17's half, `guard_end` is ignored: the start alone ends the old stream (its `_stop_locked()`),
    with no `session_ended` row. That is today's start, and the old report now arrives instead of being lost.
  - With B17's host: `session_ended` at the start's entry.
  - **These are the guard's intended product changes; they need no host flag.**

## 2. Tests (JVM)

- **The flag tables:** absent / empty / `1` / junk → on (150 / true); `0`, ` 0 ` → off. The off-device read → on.
- **The three B15 paths with the property absent:** the guard built from `RestartGuardFlag.parse(null)` runs the
  `surface`, `recreate` and `process` paths (B15's / B17's models), and with `0` it is today's (start, start).
- **The stall monitor built from `parse(null)`:** stalls from 150 ms, the `bye`.
- **Disclosed: B7's / B11's / B15's / B17's tests that asserted "absent = off" are moved to "absent = on, `0` = off"**
  (B13 moved B3's the same way).
- **The APK** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19) built offline with
  `--no-configuration-cache` in the copy, pinned (its sha256 in this item's dir), **NOT installed**.

## 3. Files

Record `evidence/B19_CLIENT_DEFAULTS_ON_2026-10-24.md` + `b19_2026-10-24/`; `patches/B19_CLIENT_DEFAULTS_ON.md`;
`logs/b19_git_status.txt`.
