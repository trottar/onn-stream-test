---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d (+ B17, B18; B19 uncommitted)
---

# B19 — `stall_signal` and `restart_guard` on by default in the client (`0` turns each off); `link_notice` stays opt-in; the APK `20e3e339…` built, NOT installed

**Classification: BUILT**, as B13 did for `link_report`.
- **Tests:** `ClientDefaultsTest` 4; JVM **136 / 136**.
- **Proof** `proof_zero_is_today.md`: **PROVEN**. Only the two flag objects changed, and `0` gives the old absent
  value.
- **The APK** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19) **`20e3e339…563d`**, pinned, **NOT
  installed.**
- NOT ADOPTED; no live run; nothing committed.

Design `b19_2026-10-24/design_written_before_code.md`, sha256 `956c73eb…78e62a`, hashed **16:05:12Z, before any B19
code**.

## 1. Built (`b19.diff`)

| property | before | **now** |
| --- | --- | --- |
| `debug.privyhub.stall_signal` | absent / junk = off; `1` = 150; 121-2000 | **absent / empty / junk = ON at 150**; `0` = off; `1` and 121-2000 as before; a failed read = on |
| `debug.privyhub.restart_guard` | `1` = on, else off | **on unless `0`**; a failed read = on |
| `debug.privyhub.link_notice` | opt-in (`1`) | **unchanged** (the user's call) |
| `debug.privyhub.link_report` | on unless `0` (B13) | unchanged |

**Why:** `debug.*` properties vanish at a reboot, and adopting the stack (B20, G-A4) needs the client half on by
itself.

## 2. The costs when on, and today's host

- **The stall signal:**
  - a 24-byte datagram every 50 ms **only while the output is ≥ 150 ms old or the recovery gate stands** (20/s,
    ~0.5 KB/s, only then), one `stall_end`, and 3 `bye`s at a finishing session (B18);
  - a comparison in the controller loop every ~8 ms.
  - **On a host without `PRIVYHUB_STALL_SIGNAL`:** the datagram fails the controller's 36-byte size check and is
    counted in `bad_packets`. It is dropped before the silence clock (`_last_any_packet_at` moves only on a valid
    controller packet; `native_session_io` read).
  - **So today's host behaves as today:** no pause, no resume, no save. B7 / B8 / B12 / B16 / B18 are all behind the
    host's flags. B16's fast ready is armed only by the host's `stall_resume` key.
- **The restart guard:**
  - at each surface loss, the report (already built today) written to `noBackupFilesDir`: ~40-50 KB, a few ms;
  - at each return, B15 / B17's flow: the audio held, the start with `guard_end=1`, the old report after it.
  - **On a host without B17's half:** `guard_end` is ignored, and the start alone ends the old stream as today's start
    does, with no `session_ended` row. **The old report now arrives instead of being lost.**
  - These are the guard's product changes, and they need no host flag.

## 3. Tests (`tests_jvm.txt`, `tests_client_defaults.xml`)

- **`ClientDefaultsTest`, 4:**
  - absent / empty → on and `0` → off for both; `link_notice` absent = off; `link_report` unchanged;
  - **the three B15 paths with the property absent:** the guard built as the activity's lazy property builds it runs
    `surface` / `recreate` / `process` (B17's order: `start&guard_end=1`, then the report);
  - **`0` → today** (no guard: `start`);
  - the stall monitor from an absent property: a stall at 150 ms, then the `bye`.
- **Moved, disclosed** (as B13 moved B3's; listed in the proof):
  - `StallSignalTest.flagTable` / `noAndroidPropertyIsOn`;
  - `RestartGuardTest.flagTable`;
  - the last line of `RestartGuardAllPathsTest.theFlagAbsentIsToday` and of `RestartGuardAudioOrderTest.theFlagAbsentIsToday`
    (now `parse("0")` false).

## 4. The APK (`apk_sha256.txt`, `build_console.txt`)

**`20e3e3392b3853a598ecee651b291f4654fa6aa46d63157e649f9c07d6b5563d`**, 9,633,230 B.
- Built offline in `/tmp/b_q24g/PrivyHub` (`--no-configuration-cache`), only the companion and `privyhub-link-n1`
  active. **0 tree files newer than the build marker.** JVM 136 / 136 in the same run.
- **Signer = `e2db0aa0…`'s** (digests compared, not printed); `apksigner verify` OK.
- 944 entries; **only `classes3.dex` differs** (374,604 → 377,988 B).
- **NOT installed;** `e2db0aa0…` stays CONFIRMED. A copy is at `/tmp/b_q24g_scratch/apk/`.

## 5. For CL-B12 (A)

**Every client property EMPTY** (read them back empty before each cell): the defaults are the test.
- The heartbeats carry the link keys (B13).
- The client report carries `stall_signal_ms` 150 and `restart_cause` after a return, with no property set.

## 6. Files

- **`b19_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b19.diff`, `proof_zero_is_today.py` / `.md`;
  - `tests_jvm.txt`, `tests_client_defaults.xml`, `apk_sha256.txt`, `build_console.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `StallSignal.kt`, `RestartGuard.kt`, `ClientDefaultsTest.kt` (new), and the four moved tests;
  - `patches/B19_CLIENT_DEFAULTS_ON.md`, `logs/b19_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
