---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 7f3f71d (+ B17; B18 uncommitted)
---

# B18 — the save at each session's end came before the host could know the end; the client now says "bye" before its sender stops, and the owner saves and holds nothing after it

**Classification: SETTLED + BUILT**, inside `PRIVYHUB_INPUT_HOLD_REWIND=1` (`state`), with its client half in B7's stall
monitor (`debug.privyhub.stall_signal`; B19 makes it default-on).
- **Tests:** host `tests/session_end` 8; client `StallByeTest` 2; JVM **132 / 132**.
- **The suites:** B8 / B9 / B12 / B16 / B7 / B2 / B6 / B4 all green from the copy.
- **Proof PROVEN:** the recovery and the plugin are identical with B18's items removed; B7's / B9's modules and the
  StallMonitor are listed; the activity has added lines only.
- NOT ADOPTED; no live run; nothing committed.

Design `b18_2026-10-24/design_written_before_code.md`, sha256 `78aac1d9…8d8044b`, hashed **15:59:06Z, before any B18
code**.

## 0. Settled (CL-B11 cells 2, 3)

| cell | `state_saved` silence | the client's report received | `session_ended` | the hold |
| --- | --- | --- | --- | --- |
| 2 | 10:47:14.071 (400.9 ms in) | 14.225 (+154 ms) | 14.276 (+205) | skipped at 952.7 ms, state ENDED |
| 3 | 11:01:29.086 (401.0 ms in) | 29.267 (+181 ms) | 29.293 (+207) | skipped at 952.5 ms, state ENDED |

- The suite's teardown is an adb BACK, which on the client runs: BACK → the paused-frame capture → `finish()` →
  **`surfaceDestroyed` stops the controller sender (the silence's onset)** → `onDestroy` → `stopSession` → the report
  (~50 KB), then the stop.
- **The host hears of the end ~550-600 ms after the silence began; B9's save fires at 400 ms.** At 400 ms a session's
  end and a two-way drop look the same to the host.
- The hold was already skipped by the ENDED state.
- **A save cannot wait.** It captures the core at the moment it is written, so a later save restores a later point.
- So the end must be said **before** the silence, by the one party that knows it: the activity, which is `isFinishing`
  at `surfaceDestroyed`. A Home press is not finishing.

## 1. Built (`b18.diff`)

**Client:**
- `StallMonitor.requestBye()`: **`PHS1` kind 3 (`bye`) on the next 3 controller ticks** (~8 ms apart), whatever the
  stall state (`StallSignal.kt` +24).
- `surfaceDestroyed`, when `isFinishing`, before `stopLocalPipeline()`: the request, then the UI thread waits
  **≤ 60 ms** for the first to go out (`NativeStreamActivity.kt` +11, added only).
- **Not on a Home press**, so the guard's return path, and its hold and save, are untouched.

**Host:**
- **`SessionEnd`** (B9's `rewind_cores.py`, +86), wired by B9's own `wire` for `state` onto the mark and the recovery.
  It knows the end from:
  - **the client's `bye`** (B7 decodes kind 3 and hands it over; `stall_signal.py` +8 −1), for the same PLAYING period
    and ≤ 30 s;
  - **any state but PLAYING** (the stop request, `native-stream-stop`, B17's `guard_end`: ENDED);
  - **the stream no longer produced:** the stream sender's packet count has not moved for **250 ms**. The plugin wires
    the count (`plugins/games.py` +3).
    - *Deviation from the design, disclosed:* the design said "video packets". `native_session_io`'s counter is the
      **audio** sender's: one packet per 10 ms, sent while the stream runs. It answers the same question.
- **No save:** B9's `StateMark` asks `ending()` first. On an end: one `state_save_skipped` (`reason`), no save.
- **No hold:** `note_input_hold` asks first (`link_drop_recovery.py` +6). On the `bye`: `input_hold_skipped_ending`.
- **Without the client's `bye`** (an APK before this), the end is known only at the stop, after the 400-ms save.
  **The row needs the new APK.**

## 2. The row, and the tests (`tests_host.txt`, `tests_jvm.txt`, `tests_stall_bye.xml`)

| row (hashed) | here |
| --- | --- |
| **zero `state_saved` outside the blackouts in a 600-s cell with a normal teardown** | **met in the model:** the `bye`, then the silence past 400 ms, the hold's 950 ms and the stop → **0 `state_saved`**, one `state_save_skipped` client_bye, one `input_hold_skipped_ending`, no pause. Live: CL-B12 |

**`tests/session_end`, 8:**
- the normal teardown (above);
- a blackout with no `bye` saves at 400 ms as today;
- the sender's count flat → `stream_stopped`, no save;
- ENDED → `state_ended`, no save;
- **a new session after a `bye` saves again;**
- B7 decodes kind 3 and ignores it without B9 (no rows, no stall counted);
- only `state` wires it;
- **flag absent: nothing imported, the class attribute None.**

**`StallByeTest`, 2:** three kind-3 datagrams after the request whatever the state, then today's tick; none without a
request.

## 3. For CL-B12 (A)

- **`@both` and `@down` with the stack** (`PRIVYHUB_LINK_RECOVERY=1`, B20) **and the new APK with every property
  empty** (B19: the stall signal on by default), each with the suite's normal teardown (adb BACK):
  - one `session_end_bye` ~0-10 ms before the controller silence;
  - one `state_save_skipped` reason `client_bye` at ~400 ms;
  - **0 `state_saved` outside the blackouts**;
  - then the report and `session_ended` as today.
- **The Home press** (not finishing): no `bye`. The hold and the silence save at the press are expected there (the
  player left mid-game).

## 4. Files

- **`b18_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b18.diff`, `proof_flag_absent.py` / `.md`;
  - `tests_host.txt`, `tests_jvm.txt`, `tests_stall_bye.xml`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/rewind_cores.py`, `stall_signal.py`, `games/link_drop_recovery.py`, `plugins/games.py`;
  - `StallSignal.kt`, `NativeStreamActivity.kt`, `StallByeTest.kt` (new);
  - `tests/session_end/` (new);
  - `patches/B18_NO_SAVE_AT_SESSION_END.md`, `logs/b18_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
