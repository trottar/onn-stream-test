---
memory_schema: 1
as_of: 2026-10-27
baseline_commit: 2cd392c (G-A7 applied beside it by A, uncommitted; B26 and B27 uncommitted)
---

# B27 — the client's loss guard on by default (`debug.privyhub.loss_guard`: absent / empty / junk = ON, `0` off); the replay; G-A8 PREPARED; APK `8b0fbb74…` built, NOT installed

**Classification: BUILT**, as B19 / B25 did, on the user's "Also adopt" (2026-10-27).
- **The replay ran first:** B10's rule over every client report since CL-B10, 47 sessions (34 LAN, 13 G4-S4
  off-site), §1.
- **The client:** only `LossGuardFlag`'s parse and catch changed. JVM **154 / 154** (4 new; B10's flag lines moved,
  disclosed). A mutation back to B10's parse fails 3. **`0` = today's absent, PROVEN.**
- **The host:** no change. `PRIVYHUB_LOSS_GUARD=1`'s adoption is **PREPARED** as
  `patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`, **nothing applied**.
- **APK (B5 … B25 + B27) `8b0fbb74d110ad89b6c1f9e69355abc3b5713b69055d3e8fa02b898108ee3f4e`**, pinned, **NOT
  installed**.
- NOT ADOPTED; no live run; nothing committed.

Design `b27_2026-10-27/design_written_before_code.md`, sha256 `633a78dc…993d`, hashed **22:03:22Z, before the replay
and any B27 code**. Preconditions checked first, at the queue's start (B26).

## 0. The cost, with and without the host flag (from the code)

- **The guard is the client's alone.** On a dropped access unit (outside a resync's own wait), no non-IDR frame is
  queued until the next complete IDR, so the surface keeps the last good frame.
  - The natural IDR comes every 15 frames (250 ms). The wait is capped at 600 ms, after which frames pass, counted
    as `loss_guard_timeouts`.
  - Each episode sends one 24-byte `PHK1` keyframe request on the controller socket.
- **Without `PRIVYHUB_LOSS_GUARD=1` on the host** (today's twelve lines):
  - the `PHK1` reaches the controller receive loop, is 24 B ≠ 36, and counts **one `bad_packets`** in the
    controller status. It is discarded; nothing else happens;
  - the heartbeat's three loss-guard fields are not recorded by the host;
  - the **report** carries every `loss_guard_*` key regardless: the host stores the client's body whole.
- **With it:** the request is parsed, counted and rate-limited, and `control.force_idr()` is called, which **forces
  nothing** (`NoRuntimeIdr`: no runtime IDR path, B10 §0.3). The host also logs the per-minute `keyframe_requests`
  rows and `loss_guard_config`, and records the heartbeat fields.
- **So the picture is the same either way:** freezes of up to ~0.25 s per episode (cap 0.6 s) in place of the frames
  drawn from a lost reference. The host flag buys only the host's own count, and no `bad_packets` for the requests.
- **Measured at 1 % post-FEC loss (BENCH-R3 E, on 2.4 GHz):**

  | | the guard on | the guard off |
  | --- | --- | --- |
  | hitch seconds / 10 min | 125.7 | 68.8 |
  | rendered fps | 55.2 | 57.8 |
  | max output gap | 597 ms | 787 ms |
  | timeouts | 0 | — |

- **B7's stall signal is on by default (B19).** A freeze ≥ 150 ms also sends a stall datagram. No adopted host line
  acts on it: without `PRIVYHUB_STALL_SIGNAL` it is a bad packet too.
- **With no loss the guard does nothing:** no drop, no episode, no datagram. On the LAN at 5 GHz it acts only at
  real drops (§1).

## 1. The replay (`replay_loss_guard.py`, `replay_output.json`, `replay_table.md`, `replay_run_at.txt`)

Every report received since CL-B10's first cell (2026-10-23T18:42:13Z), read-only. G4-S4's span
(2026-10-24T19:15Z – 2026-10-25T17:40Z) is off-site; the rest is the LAN. **No report carried the guard's own keys**:
no property was set in any of them.

**The method is a bound, not a frame-by-frame replay.** The reports and heartbeats carry no per-drop timeline. So per
session:
- drops `D` = `sequence_gap_au_drops` + `incomplete_au_drops`. This over-counts: some may sit in a resync's own wait;
- episodes ≤ min(`D`, IDRs + 1);
- held ≤ 14 per episode, estimated at BENCH-R3 E-on's measured 7.64;
- the longest hold ≤ min(`max_frames_between_idr` − 1, 36) frames;
- `max_frames_between_idr` reads 14 (no IDR missed), 27-30 (one missed) or 40-42 (two in a row).

| | sessions | streaming | with drops | drops | frames held ≤ | **held, estimate** | longest hold ≤ | a hold > 0.5 s possible |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **LAN** | 34 | 211.6 min | 33 | 894 | 12,516 | **~6,830 (~32 / min, ~0.5 s of held picture a minute)** | 600 ms (the cap) | **9 sessions** |
| **G4-S4 off-site** | 13 | 122.3 min | 13 | 244 | 3,416 | **~1,860 (~15 / min)** | 600 ms (the cap) | **1 session** |

- **What the guard would have done on the user's own sessions:** about one freeze of ≤ 0.25 s every ~15-30 s of
  play on the LAN (894 drops in 212 min), and fewer off-site (244 in 122 min). Each freeze replaces frames drawn
  from a lost reference.
- **In most sessions the longest hold is ≤ 450 ms:** 27 frames, a drop just after an IDR with the next IDR lost too.
- **The sessions where a hold > 0.5 s is possible** (two IDRs in a row missed, `M` 40-42, and drops > 0). Each would
  have ended at the 600-ms cap, a `loss_guard_timeouts` +1, with frames passing as today:

  | received (UTC) | where | s | drops | `M` | resyncs | `non_idr_aus_dropped_waiting_for_idr` |
  | --- | --- | --- | --- | --- | --- | --- |
  | 2026-10-24 15:26:02 | LAN | 238 | 36 | 42 | 0 | 0 |
  | 2026-10-24 16:53:56 | LAN | 699 | 30 | 42 | 6 | 45 |
  | 2026-10-24 18:28:56 | LAN | 699 | 47 | 41 | 0 | 0 |
  | 2026-10-24 21:02:47 | **off-site** | 2,486 | 53 | 42 | 4 (4 SSRC) | 0 |
  | 2026-10-25 22:13:28 | LAN | 700 | 72 | 42 | 0 | 0 |
  | 2026-10-25 23:01:30 | LAN | 164 | 20 | 42 | 1 (1 SSRC) | 11 |
  | 2026-10-25 23:24:36 | LAN | 699 | 110 | 40 | 6 | 64 |
  | 2026-10-25 23:39:04 | LAN | 697 | 54 | 42 | 5 | 38 |
  | 2026-10-26 03:22:16 | LAN | 699 | 89 | 42 | 1 | 13 |
  | 2026-10-26 15:40:50 | LAN | 699 | 94 | 42 | 0 | 0 |

  - **Four** of them (15:26, 18:28, 22:13, 15:40) had no resync at all, so their 42-frame run is two IDRs lost in
    a row on the link.
  - In the others the run may also come from a resync wait, in which the guard does not act. **Flagged, not
    separated.**
- **The CL-B14 / G-A7 sessions** (2026-10-27): 4-37 drops each, longest ≤ 450 ms, no > 0.5-s case.

## 2. Built (`b27.diff`)

**`LossGuard.kt`, `LossGuardFlag` only:**
- `parse`: `"0"` → null (off), `"count"` → COUNT (as before), anything else (absent, empty, junk, `"1"`) → GUARD;
- `fromSystem()` on a failed read → `parse(null)`, i.e. on;
- one KDoc line added.

The guard, the receiver, the activity (`fromSystem()?.let { LossGuard(it) }`), the controller sender, the report and
the heartbeat are unchanged: they already follow the object. **Every report and heartbeat now carries the guard's
keys** when the property is not `0`.

## 3. Tests (`tests_jvm.txt`, `tests_loss_guard_default_on.xml`, `tests_mutation.txt`)

- **`LossGuardDefaultOnTest` (new), 4:**
  - **the table:** null / "" / " " / "1" / "on" / "true" / "2" / "yes" / "guard" → GUARD; "0" / " 0 " / "0\n" →
    off; `count` → COUNT; `fromSystem()` off-device → GUARD;
  - **`zeroIsTodaysAbsent`:** `parse("0")` = B10's `parse(null)` (null, so no object). B10's stream
    I P P [lost] P P P P I P through the real receiver with `0` queues **I P P P P P I P**, the same as with no
    guard;
  - **`absentIsTheGuard`:** the same stream queues **I P P I P**; counter 3, held 3, 1 episode, 0 timeouts; one
    `PHK1`, taken once; the heartbeat fragment;
  - **`countIsAsBefore`:** today's list, counter 3, held 0, no request.
- **Disclosed, B10's flag lines moved:** in `LossGuardTest.flagTable`, `null` / `""` / `"on"` / `"guard"` / `"2"` now
  give GUARD, `"0"` is off and `fromSystem()` gives GUARD. Its seven other tests are unedited.
- **JVM 154 / 154** (150 + 4), in the APK's build run.
- **Mutation** (`LossGuard.kt` = HEAD's, in a copy): `theTable`, `absentIsTheGuard` and `flagTable` fail;
  `zeroIsTodaysAbsent` and `countIsAsBefore` pass, as they must.
- **`proof_zero_is_today.md` PROVEN:**
  - `LossGuard.kt`'s 10 changed lines all lie inside `object LossGuardFlag` (or the KDoc line);
  - HEAD's absent and the new `0` are both null;
  - every other main source is unchanged against HEAD.
- **Host:** unchanged by B27. Every suite under `tests/` is green in the copy (`tests_regression_after_b27.txt`,
  which includes B26's final suite).

## 4. The APK (`apk_sha256.txt`, `build_console.txt`)

**`8b0fbb74d110ad89b6c1f9e69355abc3b5713b69055d3e8fa02b898108ee3f4e`**, 9,638,182 B. It carries B5 + B7 + B10 + B11 +
B13 + B14 + B15 + B16 + B17 + B18 + B19 + B22 + B25 + B27, i.e. `fcd924c2…`'s sources + B27.
- **The build:** offline in a fresh `/tmp/b_q27j27/PrivyHub` copy (companion/, tools/, tests/, PrivyHub/ only, no
  build outputs or gradle caches from the tree), with
  `:app:testDebugUnitTest :app:assembleDebug --rerun-tasks --offline --no-configuration-cache`.
  - A rebuild (`--rerun-tasks :app:assembleDebug`) gave the same bytes.
  - Only the companion and `privyhub-link-n1` were active.
  - **0 tree files newer than the build marker** (this record's own dir aside).
- **The checks:**
  - `apksigner verify` OK; the signer is `fcd924c2…`'s (certificate digest lines compared, not printed);
  - 944 entries, the same names; **only `classes3.dex` differs** (389,056 → 389,064 B), and it carries the property.
- **NOT installed;** `fcd924c2…` stays CONFIRMED on the onn. A copy is at `/tmp/b_q27j27_scratch/apk/app-debug.apk`.

## 5. G-A8 PREPARED (`patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`, `g_a8_prepared.diff`)

G-A7's applied form:
- `tools/e1_suite.py`: `LOSS_GUARD = "PRIVYHUB_LOSS_GUARD=1"` with its comment, **`ADOPTED` to thirteen**, the
  preflight's **`drop_in_loss_guard`** and its `ok` term;
- `e3_state.py` / `e1_remote.py` / `test_e1_remote.py`: wording ("thirteen lines since G-A8");
- the drop-in `loss-guard.conf`, the off steps, and the predecessors' sha256 (the tree's current files, with G-A7
  applied).

It was checked in /tmp only: `git apply --check` clean on copies, `e1_suite --self-test` OK, `ADOPTED` 13,
`test_e1_remote` as unpatched. **Nothing applied to the tree.**

## 6. Files

- **`b27_2026-10-27/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `started_at.txt`;
  - `predecessors/` (+ `predecessor_note.txt`), `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - the replay's four files;
  - `b27.diff`, `proof_zero_is_today.py` / `.md`;
  - `tests_jvm.txt`, `tests_loss_guard_default_on.xml`, `tests_mutation.txt`, `tests_regression_after_b27.txt`;
  - `build_console.txt`, `apk_sha256.txt`, `g_a8_prepared.diff`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `PrivyHub/app/src/main/java/streaming/LossGuard.kt`,
  `PrivyHub/app/src/test/java/streaming/LossGuardTest.kt`, `LossGuardDefaultOnTest.kt` (new);
  `patches/B27_LOSS_GUARD_DEFAULT_ON.md`, `patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md`; `logs/b27_git_status.txt`.
- **Left in /tmp:**
  - `b_q27j27` (the build copy), `b_q27j27_scratch/` (`apk/`, the first build's copy, `mut1/`);
  - `b_q27j27_scratch_rebuild.txt`, `b_q27j27_sync.sh` / `_junit.py` / `_build_marker`;
  - `b_q27j_scratch/ga8/` (the G-A8 diff's copies).
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft; the Opal untouched;
  - nothing of `privyhub-link-n1`'s files touched; the reports only read;
  - nothing of A's touched (its G-A7 edits left as they are; G-A8 prepared against them, not applied);
  - nothing fetched, deleted, adopted or committed in B27.
