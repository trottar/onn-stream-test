---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-R3a — restart fallback and restart-trigger freshness

## Purpose

The two defects `D-BASE-R3`'s own validation found
(`evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md`):

1. **A failed encoder restart was terminal.** The `C3.L1` primitive's
   failure path leaves `manager._process = None`, so `_running_locked()` is
   false and every later cycle raises before doing anything. One validation
   run sat in `PAUSED_RECOVERING` 30 s after the fault had gone.
2. **The restart decision read a heartbeat up to 2 s stale.** Heartbeats are
   2 s apart and the code checked only the newest value, so a short outage
   got a restart into a stream that had already recovered — ~1.5 s of extra
   interruption, reproduced twice.

Authorized by the user 2026-09-20 for an unattended run without root.

## Expected predecessor

- `companion/games/link_drop_recovery.py`:
  `8e274eff47bfad9d8775767e1a9a5571eca6fae1f110b08eb0845d4d5c1853a2`
- `companion/plugins/games.py`:
  `2c07495c96a1fe9d27c38155002cb3784ed5aa87f2b190aea1641246c388fbd3`

## Changed scope

**`companion/games/link_drop_recovery.py`**
-> `f0e2fb920a04f11b72deb60d031955c82a11c05caad63105bd920c9b793b7f93`.

- `_maybe_restart_encoder` asks `stream_active()` before choosing a
  primitive: with an encoder it runs the `C3.L1` cycle as before, without
  one it calls `full_start_encoder()`. Every `encoder_restart` line gains
  `method: "restart" | "full_start"`.
- The single-heartbeat check is replaced by a two-heartbeat test: both
  newest readings `>= DESYNC_MS`, the newer not lower than the older, and
  the newer received at or after the moment the restart became eligible
  (`state_since + RESTART_AFTER_MS`, or `last_restart_at + backoff`). Every
  `encoder_restart` line gains `age_pair_ms: [older, newer]`. A session with
  fewer than two heartbeats does not restart, which delays only the first
  attempt of a session and never blocks one.
- `note_heartbeat` keeps the two newest `(received_monotonic, age_ms)`
  pairs; `session_started` clears them.

**`companion/plugins/games.py`**
-> `157dd7340cec87bd46274f39acfd50f377948ff0791f9b7a908e77cdfebc4d26`.
Two new callbacks and the state they need: `_recovery_stream_active()`
(reads `native_stream.status()["active"]`) and
`_recovery_full_start_encoder()`, which calls the same
`NativeStreamManager.start()` the `native-stream-start` action calls, with
the client target and port remembered when that action last succeeded
(`_recovery_start_args`) and the managed RetroArch pid as it stands. It
deliberately does **not** invoke the action, because the action pauses the
game and during a recovery the game is already paused and must stay as it
is.

**Unchanged**, as instructed: every constant, the `C3.L1` primitive and its
failure path, the backoff schedule, the client, the recovery save and the
launcher prompt.

## Validation performed

- `ast.parse` on both changed files; `git diff --check` clean;
- 8765 confirmed free, companion restarted on the new code (D-068);
- five runs from fresh attract-mode sessions of the PS1 reference title,
  25 s settled, zero input, driven per `TOOLS.md`;
- teardown per `TOOLS.md` and the `D-BASE-R3` teardown row: recovery save
  discarded, game ended from the client, banner confirmed gone, companion
  stopped last, **no process left in state T**, no listener left.

**Not performed:** the design note's nftables fault injection. This host has
no non-interactive root and, per the task, no `sudo` was attempted. The runs
used the `D-BASE-R3` substitute (`SIGSTOP`/`SIGCONT` on the managed
encoder).

## Result

**RUNTIME VALIDATED FOR THE SUBSTITUTE FAULT ONLY. The nftables runs are
still owed.** Record:
`evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md`.

| run | N | pause | resume after clear | restarts | methods | verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| G3 | 3 s | 1.599 s | 3.066 s | **0** | — | pause ✓ restarts ✓ resume ✗ |
| G15 | 15 s | 1.219 s | 13.401 s | 2 | restart(fail) → **full_start(ok)** | method ✓ timing ✗ |
| G15b | 15 s | 1.211 s | 3.728 s | 1 | restart(ok) | fallback not reached |
| G15c | 15 s | 1.222 s | 12.853 s | 2 | restart(fail) → **full_start(ok)** | method ✓ timing ✗ |
| G150 | 150 s | 1.209 s | n/a | 4 | restart(ok) → restart(fail) → **full_start(ok)** → restart(fail) | ✓ |

**Fix 1 works, on two observations.** Where the pre-fix build left the
session stuck, G15 and G15c both fall back to `full_start`, succeed, and
resume — 1.64 s and 0.87 s from the successful call to the resume. G150
shows the choice tracking the session's real state across four attempts.
G15b is reported as it happened: its first `C3.L1` cycle succeeded, so the
fallback never applied, which is why G15c was run.

**Fix 2 works.** G3 recorded **`restarts` 0** and wrote no `encoder_restart`
line at all; the pre-fix build restarted on two of two runs of the same
shape.

**Two timing clauses missed, both measured.**

- G3's resume was 3.066 s against a 2.5 s criterion. The client's own
  heartbeats show video back 1.96 s after the clear and the resume 1.1 s
  later: the gate costs one baseline tick plus `RECOVERY_CLEAN_TICKS` = 3
  clean ticks, a 2.0 s floor. **2.5 s is not reachable without changing the
  gate**, which was not authorized here.
- G15 and G15c resumed 13.4 s and 12.9 s after the clear against a one
  backoff interval (10 s) clause. The cost is attempt 1, which blocked ~12 s
  inside `_kill_managed_process` — `SIGTERM` then a 5 s wait against an
  encoder the injector holds stopped. **An artifact of the substitute
  injection**, already listed as one of its three differences; the fallback
  itself was fast.

**Still not shown:** anything about a real one-way link drop (loss, sequence
jumps and FEC during the outage, and a `C3.L1` restart whose replacement is
alive but unheard); the host-side controller-silence trigger, unexercised
again because no host-side fault interrupts the client->host channel; and
`END_MS`.
