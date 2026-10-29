---
memory_schema: 1
as_of: 2026-10-28
baseline_commit: 42a2ab6 (B28 / B29 / B30 / B31 uncommitted beside it)
---

# B29 — the loss guard and the stall signal: a hold with frames arriving is not a stall; the cap on the hold's own clock; APK `9719ea82…` built, NOT installed

**Classification: SETTLED + BUILT** in the client, inside the default-on guard (B27) and the default-on stall signal
(B19). `debug.privyhub.loss_guard=0` and `debug.privyhub.stall_signal=0` still turn each off.
- **Tests:** JVM **161 / 161** (7 new, `GuardQuietStallTest`); B7's, B10's and B27's tests unedited; the mutation
  fails 2.
- **Proof:** the guard off = today's monitor, PROVEN (byte for byte against the predecessor's `tick`).
- **APK (B5 … B27 + B29) `9719ea822ed5f7d13799ff7e02ba814cd0a2abe79b8a2e3d631d0aecb13c0110`**, pinned, NOT installed.
- No host change. NOT ADOPTED; no live run; nothing committed.

Design `b29_2026-10-28/design_written_before_code.md`, sha256 `89777f2a…3d41`, hashed **03:14:59Z, before any B29
code**.

## 0. Settled (the code; CL-B15 cell L)

1. **Why a guard hold reaches the stall signal.** The client's monitor reads the decoder's output age. A held frame
   is never queued, so a hold ages the output exactly as a link stall does.
   - At 150 ms the client sends `PHS1`. The host's adopted stall signal (B9's 400, through
     `PRIVYHUB_LINK_RECOVERY=1`) acts at 400: B12's save, `client_stall`, `desync_pause`, B4's 2-3-frame rewind,
     `resumed`.
   - CL-B15's 9 holds of 406-433 ms did exactly that.
2. **The "685 ms past the 600-ms cap" was not a late cap.**
   - **`loss_guard_max_wait_ms` is the episode's span, from the first drop to the next complete IDR**, set at the IDR.
     B10's own test records 640 for a hold capped at 600.
   - The hold ended at the cap (`loss_guard_timeouts` 1). Then **7 corrupted frames passed** until the IDR that came
     685 ms after the drop.
   - The cap was checked only when a complete frame arrived, at 600 ms plus up to a frame (later if the next frames
     were dropped).
   - For a hold to reach 600 ms, the IDRs every 250 ms after the drop were not delivered complete: at least two in a
     row, at 1 % loss on 57-77-packet IDRs.

## 1. Built (`b29.diff`)

- **`LossGuard.kt`:**
  - `lastArrivalMs`: the last access unit seen in an episode, held or dropped (the link still delivers);
  - **`holdingAgeMs()`**: the time since it while holding, else −1;
  - **`tick()`**: the cap on the hold's own clock, run by the controller sender's ~8-ms loop through today's
    `keyframeTick`, then the episode's request as before;
  - **`maxHoldObservedMs`**: the hold's own length, ≤ the cap + one loop;
  - `onDrop` / `deliver` / `tick` synchronized;
  - the cap (600), B10's rule, `count` and the request are unchanged.
- **`StallSignal.kt`:**
  - `StallInputs.holdingAgeMs` (default −1);
  - the monitor decides on `min(outputAgeMs, holdingAgeMs)` while the guard holds, else `outputAgeMs` as today; the
    stall / end datagrams carry that age.
  - **Suppressed, not "holding":** no datagram for a hold with frames arriving.
  - **A real stall inside a hold** is sent as today, aged from the last frame received.
- **`NativeStreamActivity.kt`, three lines, each on the guard:**
  - the input (`lossGuard?.holdingAgeMs() ?: -1L`);
  - the tick (`g.tick()`);
  - the report key **`loss_guard_max_hold_ms`** beside `loss_guard_max_wait_ms`, which is unchanged.

**What the host does: nothing new.**
- It sees no stall datagram for a guard hold.
- For a link stall it acts at 400 ms of no frames arriving, today's sensitivity.
- **The one consequence, stated:** for a stall that begins inside a hold, B4's rewind onset is the last frame
  received, not the last frame shown. The rewind can be short by up to the hold so far (≤ 0.6 s, mean ~0.13 s).

## 2. Tests (`tests_jvm.txt`, `tests_guard_quiet_stall.xml`, `tests_mutation.txt`)

`GuardQuietStallTest`, 7: the guard on a fake clock beside B7's monitor at 150 ms, ticked every 8 ms.
- **A 450-ms hold, frames every 16 ms, all held** (the output 450 ms old): **no stall datagram**, 0 timeouts; the IDR
  ends it.
- **A real stall with no hold:** the first datagram at 150-157 ms, the host's 400 reached as today.
- **A hold, then the frames stop:** the first datagram 150-157 ms after the last frame (not after the hold's start).
- **The cap on the hold's own clock:** the drop at 0, a frame held at 584, then none.
  - The loop's ticks end the hold at 600-608 (timeouts 1, `maxHold` ≤ 608); the next frame passes.
  - The IDR at 700 → `max_wait` 700 (the episode) and `maxHold` ≤ 608 (the hold).
- **A hold ended by its IDR** records its length; `count` holds nothing (`maxHold` 0).
- **No guard:** 5,000 scripted ticks against the predecessor's `tick` (copied): **byte for byte**, the same stall /
  end counts.
- **B10's receiver harness** on loopback: I P P I P; the request through the new tick, once.
- **Unedited and green:** B7's `StallSignalTest` (6), `StallByeTest` (2), B10's `LossGuardTest` (8), B27's
  `LossGuardDefaultOnTest` (4).
- **The mutation** (the decision back to `outputAgeMs`, in a copy): `a450MsHoldWithFramesArrivingSendsNoStall` and
  `aHoldThenTheFramesStopIsAStallFromTheLastFrame` fail.

**The target rows** (CL-B16 cell 3, measured, not promised):
- 0 stall pauses drawn by guard holds;
- every corrupted frame held but those after a cap;
- **0 timeouts only where no two IDRs in a row are lost.** A hold whose next good IDR is > 600 ms away still times out
  by design: CL-B15 1 / 320, BENCH-R3 0 / 394;
- the clean LAN as CL-B15 cell C.

## 3. The APK (`apk_sha256.txt`, `build_console.txt`)

**`9719ea822ed5f7d13799ff7e02ba814cd0a2abe79b8a2e3d631d0aecb13c0110`**, 9,639,374 B: B5 … B27 + B29, i.e.
`8b0fbb74…`'s sources + B29.
- **The build:** offline in a fresh `/tmp/b_q28k29/PrivyHub` copy, with
  `:app:testDebugUnitTest :app:assembleDebug --rerun-tasks --offline --no-configuration-cache`.
  - A rebuild gave the same bytes.
  - Only the companion and `privyhub-link-n1` were active.
  - 0 tree files newer than the build marker.
- **The checks:** `apksigner verify` OK; the signer is `8b0fbb74…`'s (digest lines compared, not printed); 944
  entries; **only `classes3.dex` differs** (389,064 → 392,084 B).
- **NOT installed;** `8b0fbb74…` stays CONFIRMED on the onn. A copy is at `/tmp/b_q28k29_scratch/apk/app-debug.apk`.

## 4. Files

- **`b29_2026-10-28/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `started_at.txt`;
  - `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b29.diff`, `proof_flag_absent.py` / `.md`;
  - `tests_jvm.txt`, `tests_guard_quiet_stall.xml`, `tests_mutation.txt`;
  - `build_console.txt`, `apk_sha256.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `LossGuard.kt`, `StallSignal.kt`, `NativeStreamActivity.kt`, `GuardQuietStallTest.kt` (new);
  `patches/B29_GUARD_QUIET_STALL.md`; `logs/b29_git_status.txt`.
- **Left in /tmp:** `b_q28k29` (the build copy), `b_q28k29_scratch/` (`apk/`, the first build's copy, `mut1/`),
  `b_q28k29_*`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; nothing installed, fetched, deleted, adopted or
  committed.
