---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-R3 — link-drop self-recovery

## Classification

**DEVELOPMENT.** The state machine, the client detector, the recovery save
and the launcher prompt are implemented, built, installed and exercised
against live sessions. **Two of the four fault-injection runs miss their
expected column**, and the specified injection method could not be used at
all, so this is not RUNTIME VALIDATED.

- The **0.5 s** and **150 s** runs match their expected column.
- The **3 s** run pauses and auto-resumes correctly but records
  `recovery.restarts` **1** where the table expects 0, and resumes in 3.4 s
  where the table expects ~2 s. Reproduced twice. Cause identified below.
- The **15 s** run does **not** resume at all. The first encoder restart
  fails and leaves the stream with no encoder, after which nothing can
  recover it. Part of that failure is an artifact of the substitute fault
  injection; **part of it is a real defect** and is recorded as one.

## The specified fault injection could not be run — INDETERMINATE

The design note's plan requires root:

```
sudo nft add table inet privyhub_fault
```

This host has no non-interactive root. The exact command, run twice and not
retried further:

```
$ sudo -n nft add table inet privyhub_fault
sudo: a password is required
$ sudo -n /usr/sbin/nft add table inet privyhub_fault
sudo: a password is required
```

`/usr/sbin/nft` exists and the account is in the `sudo` group, but no
passwordless rule covers it and no password is available to an autonomous
run. **No `inet privyhub_fault` table was ever created**, so none was left
behind; the teardown step that deletes it was not applicable.

**Substitute used, and how it differs.** The runs below stop the managed
x11grab/VAAPI encoder process (`SIGSTOP`, re-applied every 200 ms so a
restarted encoder is stopped again, then `SIGCONT`) for N seconds. Like the
nft rule it stops host->client video while leaving the controller channel
(UDP 48102, client->host) and the control HTTP port untouched — which is the
differential the rule creates and the reason the **client-side** desync
trigger is the one that fires in every run.

Three differences that matter, all of which are stated again where they
affect a result:

1. **Audio keeps flowing.** The nft rule drops 48101 as well. The design
   does not pause on audio starvation, so the trigger under test is
   unaffected, but "Audio: Active" appears in the client overlay during the
   outage where the real fault would show it stopped.
2. **RTP stops at the source instead of being dropped on the wire.** The
   client sees an arrival gap rather than lost packets, so the receiver's
   sequence-resync path is exercised less than it would be.
3. **A stopped encoder cannot be killed by `SIGTERM` and a restarted one is
   immediately stopped again.** This breaks the recovery's own encoder
   restart, which is why the 15 s run cannot be read as a verdict on the
   restart path. It is the reason that run is reported with its cause split
   into artifact and defect.

## Raw numbers

Constants in force, read back from `GET /plugins/games/status`:
`desync_ms` 1000, `recovery_clean_ticks` 3, `give_up_ms` 120000,
`end_ms` 1800000, `restart_after_ms` 2000, `restart_backoff_ms` 5000,
`restart_backoff_cap_ms` 30000.

All four runs below are on the final build (APK
`6140c894354034cc9823caf8ab5439bea6e391b1d872e4a30f44a90703709fee`), each from a fresh attract-mode session of
the PS1 reference title with 25 s of settled play before the fault, zero
input, opened through RESUME PLAYING and ended with BACK.

| run | N | time to pause | time to resume after clear | restarts | gate ticks | save file | expected column | verdict |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| F05 | 0.5 s | **no pause** | n/a | 0 | n/a | no | no pause; receiver resyncs alone; gap row recorded | **match** |
| F3 | 3 s | **1.302 s** | **3.374 s** | **1** | 3 (`RECOVERY_CLEAN_TICKS`) | no | pause ~1.3 s; auto-resume ~2 s; restarts 0 | **miss** (restarts, resume time) |
| F15 | 15 s | **1.727 s** | **never resumed** | 3 (all failed) | — | no | pause; one restart; resume via gate | **miss** |
| F150 | 150 s | **1.621 s** | n/a (gave up first) | 5 (all failed) | — | **yes** | pause; `GIVE_UP_MS` reached; state saved; launcher shows it; RESUME PLAYING restores play | **match** |

Per-run detail, from `logs/games/native_stream_recovery.log`:

**F05 — 0.5 s.** Fault 20:03:00.250 → 20:03:01.000. The recovery log holds
only `session_started` (20:02:34.412) and `session_ended` (20:03:22.360):
the state never left `PLAYING`. `max_output_gap_ms` 704 ms, below
`DESYNC_MS`, with no sequence resync — the receiver absorbed it. This is the
expected column exactly. (An earlier run of the same shape, N05 on the
pre-fix build, recorded a 688 ms gap with its own slow-event row
`[31908, 10, 0, 9, 1, 0, 688]` and one sequence resync of 348 packets; on
F05 the row for the 704 ms gap had been evicted — the recent segment was
full at 64/64. That is the standing `D-BASE-R2` retention limit, not a
regression.)

**F3 — 3 s.** Fault 20:04:14.356 → 20:04:17.446.

```
20:04:15.658 desync_pause      trigger=client_output_silence age_ms=1095  (+1.302 s)
20:04:18.916 encoder_restart   attempt=1 last_output_age_ms=1614  cycle ok, first_rtp_resume_ms=419.6
20:04:20.820 resumed           from=PAUSED_RECOVERING recovering_ms=5251 restarts=1
```

The pause is on time and the client's overlay changed as designed. The
restart at 20:04:18.916 fired **1.47 s after the fault had already
cleared**, on a heartbeat whose `last_output_age_ms` of 1614 ms was up to
2 s stale. The restart succeeded (a clean C3.L1 cycle: encoder down 266 ms,
first RTP resume 420 ms) but forced a fresh SSRC and therefore a fresh
resync, and the resume landed 3.374 s after the clear instead of the
expected ~2 s.

**Reproduced.** The same sequence on the earlier build: pause +1.291 s,
restart at +1.44 s after clear on `last_output_age_ms` 2635, resume at
+2.815 s, restarts 1.

**F15 — 15 s.** Fault 20:05:38.341 → 20:05:53.591.

```
20:05:40.068 desync_pause     age_ms=1492                         (+1.727 s)
20:05:53.629 encoder_restart  attempt=1  restart_error=RuntimeError
20:06:03.635 encoder_restart  attempt=2  restart_error=RuntimeError
20:06:23.645 encoder_restart  attempt=3  restart_error=RuntimeError
20:06:24.473 session_ended    state=PAUSED_RECOVERING   (BACK, 30 s after the clear)
```

Attempt 1 was due at pause + `RESTART_AFTER_MS` = 20:05:42.1 and did not log
until 20:05:53.6. The missing ~11.5 s is `_kill_managed_process`:
`terminate()` then `wait(timeout=5)` then `SIGKILL`, against a process that
cannot act on `SIGTERM` because the injector has it stopped — **an artifact
of the substitute fault**. The failure itself is
`replacement_rtp_did_not_resume`: the replacement encoder was stopped by the
injector within 200 ms of spawning — **also an artifact**.

**The defect is what happens next.** The C3.L1 primitive's failure path
kills the partial replacement and sets `manager._process = None`, leaving
the session with no encoder. `_running_locked()` is then false, so every
later restart raises before it can do anything, and the client never sees
video again. The run ended in `PAUSED_RECOVERING` 30 s after the fault had
gone. **A failed encoder restart is terminal for the session**, and the
recovery loop cannot detect that it is now retrying something that can never
succeed. This would hold for a real link drop that happened to fail one
restart; it is not created by the injector, only reached by it.

**F150 — 150 s.** Fault 20:07:16.748 → 20:09:51.343.

```
20:07:18.369 desync_pause     age_ms=1418                          (+1.621 s)
20:07:32.524 encoder_restart  attempt=1  backoff_ms=5000   error
20:07:42.529 encoder_restart  attempt=2  backoff_ms=10000  error
20:08:02.538 encoder_restart  attempt=3  backoff_ms=20000  error
20:08:32.554 encoder_restart  attempt=4  backoff_ms=30000  error
20:09:02.570 encoder_restart  attempt=5  backoff_ms=30000  error
20:09:18.612 gave_up_saved    restarts=5
             state_file=data/games/retroarch/states/Beetle PSX HW/Tekken 3 (USA).state.recovery
```

- **Give-up fired at 120.243 s after the pause** against `GIVE_UP_MS`
  120,000 — the constant, observed.
- **The backoff is exactly as decided**: 5,000 → 10,000 → 20,000 → 30,000 →
  30,000 ms, capped.
- **The recovery save is its own file**, `<stem>.state.recovery`,
  1,975,320 bytes, SHA-256 `10bb7087162589d2198f1cdd316eb2b646c992987f01d4cebac62bb1b3af7bf1`.
  It is never listed as a slot, and `_normalize_save_state_slot` still
  rejects anything but 1-3 (`recovery-copy?slot=0` →
  "Save-state slot must be 1, 2, or 3").
- **Status after the save**: `state PAUSED_SAVED`, `restarts 5`,
  `save_available true`, `saved_at 2026-09-20T20:09:18Z`,
  `save_game_title "Tekken 3 (USA)"`.
- **The client overlay at give-up** (`client_overlay_at_giveup.xml`):
  "Reconnecting…  The game is paused until the stream returns  Tekken 3
  (USA) … Stream: Checking stability".
- The session did **not** auto-resume when the fault cleared, for the same
  reason as F15: the stream had no encoder left.

**The launcher prompt and the recovery save, end to end**
(`launcher_recovery_prompt.xml`):

> **Recovery Save** — "The stream was lost at 16:09 and Tekken 3 (USA) was
> saved automatically."
> Resume from recovery save / Copy to slot 1 / Copy to slot 2 / Copy to
> slot 3 / Discard / Not now

- **Resume from recovery save** → status line "Recovery save loaded";
  `load_recovery_state` staged `<stem>.state.recovery` as `<stem>.state`
  and `LOAD_STATE_SLOT 0` was acknowledged. Confirmed through the launcher
  UI, twice.
- **Copy to slot 3** → `data/games/retroarch/states/Beetle PSX HW/Tekken 3
  (USA).state3`, slot 3 then reported `exists: true` by
  `save_state_slot_details`. **The test artifact was removed afterwards and
  the slot index entry deleted; all three slots read empty again, as they
  did before this work.**
- **Discard** → file and `.png` removed, `save_available` false.

## Heartbeat through a fault

`logs/games/native_stream_heartbeat.log`, F15's outage, one line per 2 s:

```
elapsed 35267 age    989   20:05:39.466
elapsed 37308 age   3030   20:05:41.536
elapsed 39349 age   5071   20:05:43.552
...
elapsed 71963 age  37685   20:06:16.190
```

`last_output_age_ms` rises monotonically by ~2,040 ms per heartbeat for the
whole outage and is what the host's restart logic reads. It is also the
evidence that the **2 s sampling interval is the cause of the F3 miss**: the
value the host acted on at 20:04:18.916 was written at 20:04:16.064, before
the fault cleared.

## What did not work, and what is not known

- **The restart decision reads a stale heartbeat.** The design note says to
  restart "if the client reports `last_output_age_ms` still rising
  `RESTART_AFTER_MS` after reappearing". The implementation checks the
  newest value, not that it is *still rising*, and that value can be 2 s
  old. On a short outage this fires a restart into a stream that has already
  recovered and costs ~1.5 s of extra interruption. **Fix: require two
  consecutive heartbeats with non-decreasing age, and require the newest to
  be fresher than `RESTART_AFTER_MS`.** Not made here — the task was to
  build the note as written, and this is a correction to it.
- **A failed encoder restart is terminal** (F15, above). The recovery loop
  keeps calling a primitive whose precondition it has itself destroyed.
  Neither the note nor this patch handles it. It needs its own decision:
  either the failure path should leave the previous encoder alive, or the
  recovery should fall back to a full `native-stream-start`.
- **The restart path was never observed succeeding against a real outage.**
  It succeeded once (F3) — against a fault that had already ended. Under the
  substitute injection it cannot succeed while the fault is active, so the
  15 s row is not a verdict on it.
- **The host-side desync trigger (controller silence) never fired.** Every
  run was triggered by `client_output_silence`, because neither the nft rule
  nor the substitute interrupts the client->host controller channel. The
  code path exists and is wired into the controller receive loop, but it is
  **unexercised**. It is the trigger that matters when the client itself
  dies, and nothing here tests that.
- **`END_MS` (30 minutes) was not exercised.** No run waited that long.
- **The 3 s and 15 s misses were reproduced twice each**, on both builds;
  the two build-level fixes between them (recovery-file resolution, prompt
  rendering) touch neither path.
- **The slow-event row for the worst gap was evicted in two of three
  reports** (recent segment 64/64). The standing `D-BASE-R2` retention item.
- **F15's report does not show its own stall.** `native_decoder_20260920_200624_439.json`
  reads `max_output_gap_ms` 135 for a session whose output stopped at
  20:05:38 and never returned before BACK at 20:06:24 (~46 s). The field
  only updates on the next output, so a terminal stall is invisible — the
  standing "terminal stall unrecorded" item in `docs/KNOWN_ISSUES.md`,
  reached here for the first time by a real recovery failure. (Added on
  cross-check of the raw artifacts, 2026-09-20.)
- **No perceptual observation was made.** Every figure here is
  instrumentation, by standing instruction.

## Two defects found in this patch by its own validation, and fixed

Both were found by the runtime checks and fixed before the final build; the
runs in the table above are all on the fixed build.

1. **The recovery file was looked for in the wrong directory.**
   `_recovery_state_path_for_active()` built `<state_root>/<stem>.state.recovery`,
   but RetroArch's `sort_savestates` puts states under a per-core
   subdirectory (`states/Beetle PSX HW/`), which `save_state` learns from
   the probe diff rather than guessing. Every resume and copy failed with
   "No recovery save exists for this game" while the file sat on disk. Now
   resolved from the index written at save time, with a recursive search as
   the fallback.
2. **The launcher prompt rendered no options.** `AlertDialog` ignores
   `setItems` when `setMessage` is also set: the first prompt showed the
   sentence and nothing but "Not now". The sentence now goes in a custom
   title view above the five items. Also `save_game_title` read the wrong
   key and the message said "null was saved automatically".

## What ran, in order (all times UTC, 2026-09-20)

| time | step | result |
| --- | --- | --- |
| 19:40 | patch written; Python compiled; `git diff --check` clean | 4 companion files + 1 new module, 2 client files |
| 19:41 | `sh ./gradlew :app:assembleDebug --no-daemon` | `BUILD SUCCESSFUL in 22s` |
| 19:41 | `adb install -r`; companion restarted on the new code (D-068), 8765 checked free first | recovery block live in `status` |
| 19:42-19:44 | **N05** (0.5 s), pre-fix build | no pause; gap row present |
| 19:46-19:47 | **N3** (3 s), pre-fix build | pause +1.291 s, resume +2.815 s, restarts 1 |
| 19:48-19:49 | **N15** (15 s), pre-fix build | never resumed; restarts failed |
| 19:51-19:54 | **N150** (150 s), pre-fix build | gave up and saved at +120.21 s |
| 19:54 | launcher prompt shown for the first time | rendered no options — defect 2 |
| 19:55-20:01 | defects 1 and 2 fixed, rebuilt, reinstalled, companion restarted | endpoints verified by direct call |
| 20:02-20:03 | **F05** (0.5 s) | match |
| 20:03-20:04 | **F3** (3 s) | miss: restarts 1, resume 3.374 s |
| 20:05-20:06 | **F15** (15 s) | miss: never resumed |
| 20:06-20:09 | **F150** (150 s) | match: gave up and saved at +120.243 s |
| 20:09-20:11 | launcher prompt, Resume, Copy to slot 3, Discard | all confirmed; slot-3 artifact removed |
| 20:12 | teardown | recovery save discarded; game ended from the client ("Don't Save"); banner confirmed gone; then the companion stopped. No companion, RetroArch, ffmpeg or FEC relay process and no listener on 8765 / 48100-48102 / 48110 left. No stopped process left behind. No nft table was ever created. |

## Artifacts

Under `evidence/d_base_r3_2026-09-20/`:

| file | SHA-256 | bytes |
| --- | --- | ---: |
| `native_stream_recovery_2026-09-20.log` (F05-F150) | `8f4b687d86eb071536506f2fb48c28a12269e69f5ae2190ca2902f97e72438a7` | 5,309 |
| `native_stream_recovery_prefix_runs_2026-09-20.log` (N05-N150) | `8e515b8aacfffa4ce91c0ea91525f411567c743b83ceb5896e3db607718cc4ab` | 4,990 |
| `native_stream_heartbeat_2026-09-20.log` | `51a4e27491503fe8dcd5bf7b00cef40be97c92f5d7e778cd506284f9159dd392` | 50,703 |
| `native_decoder_20260920_200322_290.json` (F05) | `2d83877720de0819bc63ec1070ac2eb14f3b1461a094052e792588b3dd017098` | 10,593 |
| `native_decoder_20260920_200443_372.json` (F3) | `d2206d636fd9cb5272874e7a0d1d81f6092b91ddef7068b87a68011bac03e38b` | 12,097 |
| `native_decoder_20260920_200624_439.json` (F15) | `2d46f15bac258661957ef14b7c83818df56c91281c9b9edaf902e14bd52a4d0a` | 10,552 |
| `client_overlay_at_giveup.xml` | `c8f09fbebf82cac162edb1a84f16053d23442a3277eea12a11367f780aa1d6b5` | 2,346 |
| `launcher_recovery_prompt.xml` | `80d1cdc6aa3d22b31125ee194a33354047cd89e7496f103856de4cce8855ccdb` | 7,607 |

The F150 decoder report was not written: that session ended in
`PAUSED_SAVED` with no encoder, and BACK posted no report.

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts. The recovery log records host time
and state only, by design. The launcher dump was filtered to element text.
