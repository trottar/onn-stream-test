---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — G6-HM3 NOT MET by its pre-registered rule (c4: max_output_gap_ms 936 > 250); c1–c3, c5, c6 met; c7 met for End. Candidate APK 1d658a3f… on the tablet only; the onn keeps ca53df0d…. Nothing adopted.
---

# G6-HM3 — the portrait screen with an inert touch pad (2026-11-19)

The user's "Proceed" after G6-HM2 (`G6_HM2_TOUCH_PAD_LOGIC_2026-11-19.md`). Design (hashed before code):
`g6_hm1_2026-11-19/design_written_before_code.md` with `user_answers_2026-11-19.md`. Patch note:
`../patches/G6_HM3_PORTRAIT_SCREEN.md`.

**Preflight (12:30Z).** No game, gradle or other session running; the last stream ended 06:33Z. **HM1 and HM2 were
still uncommitted.** HM3 builds on that working tree (`git_status_at_start.txt`, `predecessor_sha256.txt`), and
`g6_hm3.diff` is relative to it.

## 1. What was written

| File | What |
|---|---|
| `NativeStreamActivity.kt` (+34, −9) | `open class`; the hooks H1–H9. The 9 replaced lines: the class line, the orientation value (H1), `setContentView(root)` (H2), the touch guard's line (H3), and the five `AndroidPadDevice.connected()` calls (H4, as `connectedPadDevices()`). Plus no-op calls to H5 (after the prompt's start response), H6 (at the gameplay release) and H7 (before the report is returned) |
| `HandheldStreamActivity.kt` (new) | the portrait activity: `HandheldLayout` (the box W × W·9/16 on top from the measured width, the pad region below), `TouchPadView` (draws `TouchPadState`'s layout, feeds it the fingers, releases on cancel / hide / detach, edge-gesture exclusion on API 29+), the status panel (Q1 (c)), the **End** button and Back swallowed (Q5 (c)), the `handheld` report block (H7). **`TOUCH_LIVE = false`:** the pad takes no slot and writes nothing (HM3 is the inert stage); the 5-s rule, the countdown, the takeover and the writes are wired behind it for G6-HM4 |
| `TouchPadState.kt` (+10) | `drawn()` for the view |
| `AndroidManifest.xml` (+6, 0 deleted) | `.streaming.HandheldStreamActivity`, `exported="false"`, `screenOrientation="portrait"`, after today's entry |
| `MainActivity.kt` (+34, −1) | "Handheld game screen (portrait, touch buttons)" in Settings, only with `FEATURE_TOUCHSCREEN`; stored in `privyhub_game_screen` / `mode`, default `tv`. The launch picks `HandheldStreamActivity` only when chosen on a touchscreen device. The one replaced line is the launch's activity class |

**Disclosed changes from the design and the answers:**
- **H5 is added as well as H6.** The answers file said "H6, not H5". But `TouchP1Rule` (G6-HM2) must know which
  starts clear the slots: a game's start and every unpause, not a self-restart. Only the start response tells it.
  H6 alone would also re-arm at a link recovery's release.
- **H4 is named `connectedPadDevices()`,** not `connectedPads()`, to avoid confusion with the sender's
  `connectedPads` property inside the `also` block at the sender's construction.
- **End is a tap.** If accidental presses happen at G6-HM4, a press-and-hold is the obvious change; it is not built.
- **Q1 (c) edge, left for G6-HM4:** after a real P1 releases its slot, the pad shows again but has no slot until the
  next start.

## 2. Build and tests

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL**. 346 / 346 JVM tests pass
  (`tests_jvm.txt`). The two compiler warnings are in existing lines (`MainActivity.kt:10106`,
  `NativeStreamActivity.kt:4229`) (`build_console.txt`).
- **The candidate:** `PrivyHub/app/build/g6_hm3_candidate/app-debug.apk`,
  sha256 `1d658a3fb96a3281816e1900af54c00479bff74d19fa4281281c0e186d9cf64e` (also copied as
  `PrivyHub-handheld-preview-1d658a3f.apk` for sending).
- The previous `build/outputs/apk/debug/app-debug.apk` (`043891e1…`, 2026-10-18) was copied first to
  `PrivyHub/app/build/g6_hm3_preserved_outputs/`.

## 3. The onn is unchanged (design §9; `onn_unchanged_checks.txt`)

1. The manifest's `NativeStreamActivity` element is byte for byte the same (sha256 `4d36c0bb…` before and after); the
   manifest diff deletes nothing.
2. The `NativeStreamActivity.kt` diff deletes 9 lines, each replaced as listed. Every hook's default body is the
   replaced expression (checked line by line by script).
3. `PadSlots.kt` and `PointerGuard.kt` are unchanged.
4. `PlayerPrompt.kt` and `NativeControllerSender.kt` are as G6-HM2 left them.
5. `MainActivity.kt`'s only deleted line is `NativeStreamActivity::class.java` in the launch. It is now the `else`
   of the choice, and the intent and its extras are unchanged.
6. Every existing JVM test passes, and the real `assembleDebug` ran.

The onn's run of this code and its confirmation are **not done**. `ca53df0d…` stays on the onn, and the pins are not
touched.

`git diff --check` is clean; `git apply -R --check g6_hm3.diff` is OK. The redactor is clean on the Kotlin files and
the records.

## 4. Part 2 — the tablet run, scored (2026-11-19; scored by G6-HM3S, docs only)

**Pre-registration intact:** `preregistration.md` sha256 `bcbeff14…` checks OK against `preregistration.sha256`.

**The run (verified in the logs):**
- the tablet, the candidate `1d658a3f…`, a PS2 game (`launch_ports` 15:44:47.9Z, `pcsx2`), recovery-log session 12;
- `session_started` 15:44:55.9Z, `session_end_bye` 15:48:11.5Z (`client_frame` 11697), `session_ended` 15:48:11.6Z:
  195.5 s PLAYING;
- decoder report `logs/games/decoder_sessions/native_decoder_20261119_154811_583.json` (received 15:48:11.583Z,
  `duration_ms` 199487).

| Cell | Read | Value | Bound | Verdict |
|---|---|---|---|---|
| G6-HM3.c1 decode | `decoder.codec_name`, `hardware_accelerated`, `low_latency_enabled` | `OMX.Exynos.avc.dec`, true, true | hardware, low latency | **MET** |
| G6-HM3.c2 rate | `video.recent_fps` | 60.16 | ≥ 58 | **MET** |
| G6-HM3.c3 drops | `decoder.dropped_frames` / `queued_frames`; `video.dropped_frames` / `video.frames` | 53 / 11764 = 0.45 %; 32 / 11764 = 0.27 % | each ≤ 1 % | **MET** |
| G6-HM3.c4 latency | `decoder.max_rx_to_decode_ms`; `decoder.max_output_gap_ms` | 74 ms; **936 ms** | ≤ 100; ≤ 250 | **NOT MET** (the gap) |
| G6-HM3.c5 the box | `handheld.mode`, `video_box`, `pad_region` | `portrait`, `1200x675` (= 1200·9/16), `1200x1325` (= 2000 − 675) | as stated | **MET** |
| G6-HM3.c6 the inert pad | `touch_live`, `touch_events`, `touch_writes`, `touch_slot`, `pointer_exempted_events` | false, 174, 0, −1, 182 | false; > 0; 0; −1; > 0 | **MET** |
| G6-HM3.c7 Back and End | `back_swallowed`; `end_presses`; the bye | 0 (Back not tried); 1; one bye after 195.5 s PLAYING | ≥ 1 if tried; 1; one bye after ≥ 60 s | **MET for End**; Back untested |

**Verdict by the pre-registered rule: G6-HM3 NOT MET.** The rule needs c1–c6 met; c4 missed with
`max_output_gap_ms` 936. No threshold changes after the hash.

**Where c4's gap falls (verified).** The report's largest output gap (936 ms, slow-event row at `elapsed_ms` 56967)
lands at 15:45:49.06Z. The decoder session started about 15:44:52.10Z (the report's receipt minus `duration_ms`).
At that moment:
- the decoder logged a `sequence_resync` with `jump_packets` 455 (`elapsed_ms` 57003);
- the hub logged `client_stall` / `desync_pause` at 15:45:49.059Z (`age_ms` 415);
- `input_release` followed, `why` `dark_span` (the hub's window counted 0 lost packets), and `resumed` at
  15:45:49.995Z.

**So the gap is inside a stall: a dark span of the link, not a decode or display delay.**
`max_rx_to_decode_ms` was 74 ms across the session. The other large gaps line up the same way:
- 929 ms at 153.9 s with a 433-packet resync, matching a stall at 15:47:26.04Z;
- 868 ms at 104.8 s with a 431-packet resync, matching the stall run at 15:46:36.9–15:46:39.5Z.

The five resyncs come at 6.9, 57.0, 104.8 / 105.5 and 154.0 s, about every 48–50 s. That is recorded as seen; no
cause is claimed. The verdict stands as NOT MET.

**Context (not cells):**
- `video.lost_packets` 1738, of which `lost_packets_in_resyncs` 1627;
- `fec_unrecoverable_groups` 1; 5 sequence resyncs;
- `stall_signal_stalls_sent` 90 (ends 21);
- 7 `client_stall` / `desync_pause` rows in the recovery log;
- Opus 19658 packets, 203 lost;
- one `link_notice_shown` at 15:45:45.4Z, `rssi_weak`: 5180 MHz, −72 dBm, tx 65 Mb/s (heartbeat 27).

**The user's remarks, verbatim (2026-11-19):**
- "Handheld games, portrait PrivyHub menu is cutoff." Asked which screen: **the main app** (the catalog and Settings
  outside a game, held upright).
- "R\L buttons need to be lower, there positioning isn't goood either."
- "I decided we should be using PS2 setup for everything because this literally won't work for PS2 and GameCube."
- "I also get a persistent wifi weak signal message even if I'm right next to the router."

**Next:** the design amendment G6-HM1a (`g6_hm1a_2026-11-19/design_amendment_written_before_code.md`), hashed before
any code. Whether c4 is re-run as pre-registered, or carried into G6-HM4's cells, is the user's call (the amendment's
open questions).

## 5. The re-run (2026-11-19, the placement test's minute P1)

**G6-HM3 re-run: MET** by its own pre-registered rule and cells (`bcbeff14…`), as G6-PLACE's minute P1. The tablet lay
flat about 1 m from the travel router (session 14, 16:59–17:04Z).
- c4: `max_output_gap_ms` 64, `max_rx_to_decode_ms` 56;
- c7: Back tried (`back_swallowed` 5) and End;
- every other cell met.

Record: `G6_PLACE_PLACEMENT_TEST_2026-11-19.md`. The first run above stays NOT MET; both are on record.
