---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-R1 — Group A live half, and the resync-loss counter

## Purpose

Run the two live measurements the Group A record owed (A1-live on-wire
bitstream, A3-live grab cadence), read the host side of A4, and fix the
`lost_packets` metric defect found by A2.2. Tier 1: one source change the
build validates, plus memory.

## Expected predecessor

Commit `cbfd2d03321e1be936aa5b94a512695a1d2b03af` with the 2026-09-20
Group A memory edits uncommitted on top of it. Per-file SHA-256 before this
patch:

| file | predecessor SHA-256 |
| --- | --- |
| `PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt` | `f26a3c0ef2b43a3453f0bd2e1d414e314a8ac5c5d347dd8fdb0f3248e0010884` |
| `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt` | `c46a35aa09df4386006937336313abdbe82be6e5a058a45a01af7109f98c453b` |
| `docs/memory/evidence/group_a_2026-09-20/a2_rescore_decoder_sessions.py` | `bf1dc0c96897fa3e156d60eb2f5da60e3a2d8e42e3707322ce257b5a8ba59da7` |

After:

| file | SHA-256 |
| --- | --- |
| `RtpH264Receiver.kt` | `41c0db2097290f8cea894279c692fb5412cfa449619612954861266b36977b54` |
| `NativeStreamActivity.kt` | `94f13294ddeda7e2d6b5f8285dc22d9ed81ec2179350fbe11f0a69bcb92eb8a5` |
| `a2_rescore_decoder_sessions.py` | `3a6e7df679537f3043a83249ab0ea830ab84953af8de622673da1d023bbdefa3` |

## Source change (diagnostic accounting only; no streaming constant changed)

`RtpH264Receiver.kt`:

- new `lostPacketsInResyncs` counter next to `lostPackets`;
- `beginStreamResync`: when `jumpPackets > 0` (a `sequence_resync`; an
  `ssrc_change` carries 0), add the jump to both `lostPackets` and
  `lostPacketsInResyncs`, before `recordDiscontinuity`;
- `NativeStreamMetrics` gains `lostPacketsInResyncs`, filled by `snapshot()`.

`NativeStreamActivity.kt`: `video.lost_packets_in_resyncs` written next to
`video.lost_packets` in both the status payload and the session report.

Reading rule going forward: a report **with** `lost_packets_in_resyncs`
already counts jumps in `lost_packets`; a report **without** it is pre-fix,
and corrected loss is `lost_packets` + sum of
`stream_discontinuities[].jump_packets`. The A2 re-score script applies
both rules.

## Validation performed

- `git diff --check` clean.
- `bash ./gradlew :app:assembleDebug` on the host: **BUILD SUCCESSFUL in
  16s** (`compileDebugKotlin` executed), APK
  `PrivyHub/app/build/outputs/apk/debug/app-debug.apk`, SHA-256
  `812bea87b6fb90fcbaf934b8f1e166cb285bd4be7f59d98cfca1a290831e1876`.
  The string `lost_packets_in_resyncs` is present in the built dex.
- `python3 -m py_compile` on the A2 script.
- `tools/check_memory_health.py` — result recorded in the session summary.

**Not performed:** install on the onn, and a runtime session showing the
field. The counter fix is *not runtime-confirmed* until that happens (no
client was part of this session by design). `gradlew` in the tree is not
executable; it was run through `bash` rather than `chmod`ed.

## Runtime confirmation (added 2026-09-20, night)

Installed on the onn (`adb install -r`, same APK hash) and read in one
ordinary 127.5 s session: `video.lost_packets_in_resyncs` 493 = the sum of
the session's three resync jumps; `lost_packets` 695 = 202 gap-counted +
493. **Runtime-confirmed.** Record:
`../evidence/D_BASE_R1_RESYNC_LOSS_COUNTER_RUNTIME_2026-09-20.md`.

## Live measurements (evidence, not this patch's payload)

Recorded in `../evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md`, "Live
half": A1-live falsified (bitstream correct and explicit on the wire),
A3-live falsified (capture 60 fps clean), A4 host half measured (wired,
`r8169`). Raw files: `logs/games/a1_sample.h264`,
`logs/games/a3_grab_framemd5.txt` (both under the git-ignored `logs/`),
`../evidence/group_a_2026-09-20/a1_first_sps_pps_sei_trace.txt`,
`a1_a3_live_summary.json`, `a1_a3_live_summarize.py`.

Host process hygiene: RetroArch was launched directly (not through the
companion) with the last managed session config and stopped after the
captures; no ffmpeg or RetroArch process left running; no companion or
client involved.

## Memory files updated

`CURRENT.md`, `2026-09-20.md`, `MEMORY.md`, `handoffs/CURRENT_HANDOFF.md`,
`investigations/BASELINE_STREAM_HEALTH.md`,
`investigations/SEAMLESS_LOCAL_PLAY_TEST_BATTERY.md`,
`evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md`, `docs/KNOWN_ISSUES.md`,
`patches/PATCH_INDEX.md`, this record.

## Privacy

No network addresses, MACs, SSIDs or device identifiers. The host link is
described by interface name and driver.
