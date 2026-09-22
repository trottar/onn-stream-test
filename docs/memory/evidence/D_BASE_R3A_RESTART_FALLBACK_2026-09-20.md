---
memory_schema: 1
as_of: 2026-09-20
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# D-BASE-R3a — restart fallback and restart-trigger freshness

## Classification

**RUNTIME VALIDATED FOR THE SUBSTITUTE FAULT ONLY.** Both `D-BASE-R3`
defects are fixed and both fixes are confirmed on live sessions. Three of
the five runs meet their pass criterion in full; two miss a timing clause,
in both cases for a reason that is measured below and is a property of the
substitute fault injection or of the gate, not of these fixes.

**The nftables runs are still owed.** This host has no non-interactive root,
so the design note's injection plan could not be used — as in `D-BASE-R3`,
and per this task's instruction no `sudo` was attempted. Until those runs
exist, nothing here says how the recovery behaves against a real one-way
link drop, where packets are lost on the wire rather than never produced.

## The two fixes

**Fix 1 — failed-restart recovery.** `_maybe_restart_encoder` now asks
whether the session still has an encoder before choosing a primitive. With
an encoder it runs the `C3.L1` cycle as before; without one — the state the
cycle's own failure path leaves behind (`manager._process = None`,
`_running_locked()` false) — it calls the same
`NativeStreamManager.start()` that `native-stream-start` uses, with the
client target and port remembered from that action and the managed RetroArch
process as it stands. It does **not** go through the `native-stream-start`
action, because that action pauses the game and during a recovery the game
is already paused and must stay as it is. Every `encoder_restart` line now
carries `method: "restart" | "full_start"`. The `C3.L1` primitive and its
failure path are unchanged; the backoff schedule is unchanged.

**Fix 2 — restart trigger freshness.** The single-heartbeat check is
replaced by: the two newest heartbeats both read `last_output_age_ms >=
DESYNC_MS`, the newer is not lower than the older, **and** the newer was
received after the restart became eligible (`state_since + RESTART_AFTER_MS`,
or `last_restart_at + backoff`). Every `encoder_restart` line carries
`age_pair_ms: [older, newer]`.

Nothing else changed: not the constants, not the client, not the recovery
save, not the launcher prompt.

## Raw numbers

Five runs, each from a fresh attract-mode session of the PS1 reference
title, 25 s settled before the fault, zero input, opened through RESUME
PLAYING and ended with BACK. Fault injection is the `D-BASE-R3` substitute:
`SIGSTOP` on the managed x11grab encoder, re-applied every 200 ms, then
`SIGCONT`.

| run | N | time to pause | time to resume after clear | restarts | methods | verdict |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| G3 | 3 s | **1.599 s** | **3.066 s** | **0** | — | pause ✓, restarts ✓, resume ✗ (2.5 s) |
| G15 | 15 s | **1.219 s** | **13.401 s** | 2 | restart(fail) → **full_start(ok)** | method ✓, timing ✗ |
| G15b | 15 s | **1.211 s** | **3.728 s** | 1 | restart(**ok**) | fallback not reached |
| G15c | 15 s | **1.222 s** | **12.853 s** | 2 | restart(fail) → **full_start(ok)** | method ✓, timing ✗ |
| G150 | 150 s | **1.209 s** | n/a | 4 | restart(ok) → restart(fail) → **full_start(ok)** → restart(fail) | ✓ |

G150's give-up fired **120.428 s** after the pause against `GIVE_UP_MS`
120,000.

### G3 — fix 2, confirmed

```
20:53:14.906 fault start
20:53:16.505 desync_pause   trigger=client_output_silence age_ms=1359   (+1.599 s)
20:53:17.987 fault cleared
20:53:21.053 resumed        recovering_ms=4646 restarts=0
```

**`restarts` 0.** On the same fault shape the pre-fix build restarted twice
out of two (`D-BASE-R3` F3 and its pre-fix repeat), each time on a heartbeat
written before the fault cleared, and each time costing ~1.5 s. No
`encoder_restart` line was written at all here: the two newest heartbeats
never satisfied the rising-and-fresh test.

**The resume missed the 2.5 s criterion at 3.066 s, and the heartbeat says
why.** The client's own readings through the clear:

```
20:53:15.881  age  858   rendered 1781
20:53:17.917  age 2888   rendered 1781      <- still in the outage
20:53:19.945  age   43   rendered 1968      <- video back, +1.96 s after the clear
20:53:21.982  age    5   rendered 2090
```

Video was flowing again within ~2 s of the clear and the resume followed
1.1 s later. That 1.1 s is the gate: one tick to set its baseline and then
`RECOVERY_CLEAN_TICKS` = 3 clean ticks on a 500 ms cadence, a 2.0 s floor
from the first tick after video returns. **2.5 s is not reachable while the
gate costs 4 ticks and the encoder needs ~1-2 s to resume**, and neither is
a defect in fix 2. Lowering it would mean either dropping the baseline tick
or a shorter tick, both of which are changes to the gate and were not
authorized here.

### G15 and G15c — fix 1, confirmed twice

G15:

```
20:54:49.299 fault start
20:54:50.518 desync_pause   age_ms=1006                                   (+1.219 s)
20:55:04.539 fault cleared
20:55:04.643 encoder_restart attempt=1 method=restart  age_pair_ms=[1006,3043]
                              restart_error=C3 actuator continuity diagnostic failed
20:55:16.299 encoder_restart attempt=2 method=full_start age_pair_ms=[8048,10073]
                              restart_error=null
20:55:17.940 resumed         recovering_ms=27516 restarts=2
```

G15c is the same sequence: attempt 1 `restart` fails at 20:58:55.237
(`age_pair_ms` [1540, 3565]), attempt 2 `full_start` succeeds at
20:59:07.204 (`age_pair_ms` [23835, 25863]), resumed 0.868 s later at
20:59:08.072.

**This is the defect fixed.** On the pre-fix build the identical sequence
ended with the session stuck in `PAUSED_RECOVERING` 30 s after the fault had
gone, because every attempt after the first re-entered a primitive whose
precondition the first attempt had destroyed. Both runs here recover, and
the `method` field makes the two primitives countable.

**Both missed the "within one backoff interval of the clear" clause**
(13.401 s and 12.853 s against a 10 s interval), and the cost is in attempt
1, not in the fallback. Attempt 1 became eligible at pause + 2 s
(20:54:52.5 in G15) and did not log until 20:55:04.643 — ~12 s inside
`NativeStreamManager._kill_managed_process`, which sends `SIGTERM` and waits
5 s before `SIGKILL`, against an encoder the injector is holding stopped. A
`SIGSTOP`ped process cannot act on `SIGTERM`. **That delay is an artifact of
the substitute injection**: under the nftables rule the encoder is running
and killable, and the note's record already lists this as one of the three
differences. Once attempt 1 returned, the fallback itself was fast — 1.64 s
from `full_start` to resume in G15, 0.87 s in G15c.

### G15b — the fallback was not needed

Attempt 1 chose `method: restart` and **succeeded** (`ffmpeg_spawn_ms`
5002.3 — the 5 s `SIGTERM` wait again — `first_rtp_resume_ms` 5163.9), so
the session still had an encoder and the fallback never applied. Resume came
3.728 s after the clear.

Whether a `C3.L1` cycle survives depends on a race between the injector's
200 ms `SIGSTOP` sweep and the replacement encoder's first RTP packet. That
race exists only under this substitute. G15b is reported as it happened: it
is not a second confirmation of fix 1, which is why G15c was run.

### G150 — give-up, and the method choice under repetition

```
21:00:22.772 fault start
21:00:23.981 desync_pause    age_ms=1019                          (+1.209 s)
21:00:33.572 encoder_restart attempt=1 method=restart    ok        age_pair_ms=[2540,4573]
21:00:55.838 encoder_restart attempt=2 method=restart    fail      age_pair_ms=[8705,10738]
21:01:19.047 encoder_restart attempt=3 method=full_start ok        age_pair_ms=[41122,43147]
21:02:02.575 encoder_restart attempt=4 method=restart    fail      age_pair_ms=[75573,77597]
21:02:24.409 gave_up_saved   restarts=4                            (+120.428 s after the pause)
21:02:56.176 fault cleared
```

The method selection tracks the session's real state through four attempts:
`restart` while an encoder exists, `full_start` after one has been lost, and
`restart` again after the `full_start` put one back. `age_pair_ms` rises
monotonically throughout, as it must during an outage.

Give-up at **120.428 s** against `GIVE_UP_MS` 120,000; state `PAUSED_SAVED`,
`save_available` true, `saved_at` 2026-09-20T21:02:24Z,
`save_game_title` "Tekken 3 (USA)", file
`data/games/retroarch/states/Beetle PSX HW/Tekken 3 (USA).state.recovery`.

**Return path, through the launcher** (`g150_launcher_prompt.txt`):

> **Recovery Save** — "The stream was lost at 17:02 and Tekken 3 (USA) was
> saved automatically."
> Resume from recovery save / Copy to slot 1 / Copy to slot 2 / Copy to
> slot 3 / Discard / Not now

Chose **Resume from recovery save** → status line "Recovery save loaded",
game `active: true, paused: true`. Then **RESUME PLAYING** → the stream
opened and the game unpaused 7 s later; `recovery.state` **PLAYING**,
`restarts` 0. Video confirmed flowing from the client's own heartbeats:

```
21:04:34.231 age  8  rendered 1175  rx 16322
21:04:36.244 age  2  rendered 1293  rx 18110
21:04:38.250 age 14  rendered 1407  rx 19695
21:04:40.252 age  6  rendered 1524  rx 21233
```

## Decoder reports

| run | report | duration | `max_output_gap_ms` | row for it | `max_codec_ms` | resyncs |
| --- | --- | ---: | ---: | --- | ---: | ---: |
| G3 | `native_decoder_20260920_205343_872.json` | 59,030 | 3,005 | evicted | 100 | 1 |
| G15 | `native_decoder_20260920_205540_430.json` | 81,052 | 15,253 | `[45399, 10, 0, 10, 3, 2, 15253]` | 85 | 2 |
| G15b | `native_decoder_20260920_205736_106.json` | 83,115 | 10,013 | `[42164, 8, 0, 8, 1, 2, 10013]` | 129 | 3 |
| G15c | `native_decoder_20260920_205931_120.json` | 84,114 | 26,485 | `[59663, 10, 0, 9, 2, 0, 26485]` | 110 | 1 |

The gap rows are the outages themselves, each ending on a frame with
`rx_to_decode_ms` 8-10 and `codec_ms` 8-10 — the decoder holding nothing,
the `D-BASE-R2` signature of an arrival gap. G3's row was evicted (the
standing 64-entry retention limit). G150 wrote no report: that session ended
through the recovery prompt rather than a stream BACK.

## What this does not show

- **Nothing about a real one-way link drop.** The substitute stops RTP at
  the source; the nftables rule drops it on the wire. Loss, sequence jumps
  and FEC behaviour during the outage are therefore untested, and so is a
  `C3.L1` restart whose replacement encoder is alive but unheard. **The
  nftables runs are still owed.**
- **The restart-attempt timing is distorted** by `_kill_managed_process`
  blocking 5 s per `SIGTERM` against a stopped encoder. Every "time to
  resume" on a 15 s run carries that.
- **The host-side controller-silence trigger is still unexercised.** All
  five runs were triggered by the client's notice, because no host-side
  fault interrupts the client->host controller channel. Unchanged from
  `D-BASE-R3`.
- **`END_MS` (30 minutes) is still unexercised.**
- **Fix 1 has two observations** (G15, G15c) and one run where the condition
  did not arise (G15b). Fix 2 has one (G3).
- **No perceptual observation was made**, by standing instruction.

## What ran, in order (all times UTC, 2026-09-20)

| time | step | result |
| --- | --- | --- |
| 20:51 | both fixes written; `ast.parse` on both changed files; `git diff --check` clean | 2 companion files |
| 20:52 | 8765 confirmed free, companion started on the new code (D-068) | `recovery` block live |
| 20:52-20:53 | **G3** (3 s) | pause 1.599 s, **restarts 0**, resume 3.066 s |
| 20:54-20:55 | **G15** (15 s) | `full_start` fallback, resumed |
| 20:56-20:57 | **G15b** (15 s) | `restart` succeeded; fallback not reached |
| 20:58-20:59 | **G15c** (15 s) | `full_start` fallback, resumed |
| 21:00-21:03 | **G150** (150 s) | give-up at 120.428 s; prompt; resume; RESUME PLAYING restored play |
| 21:05 | teardown | recovery save discarded; game ended from the client ("Don't Save"); banner confirmed gone (0 occurrences); companion stopped last. No companion, RetroArch or encoder process, **no process left in state T**, no listener on 8765 / 48100-48102 / 48110. |

## Artifacts

Under `evidence/d_base_r3a_2026-09-20/`:

| file | SHA-256 | bytes |
| --- | --- | ---: |
| `native_stream_recovery_2026-09-20.log` | `3f48e4e37d356b0a2638dbae354918af0a39f96c4d4a791a1f8d44d483f33e4d` | 7,377 |
| `native_stream_heartbeat_2026-09-20.log` | `6f116b37cce4c3af77e3031b9ac3ac454f4982374f0d3e34bb257e3223d70786` | 69,100 |
| `native_decoder_20260920_205343_872.json` (G3) | `9219cd1724f29347aeeaeb34f01c3623a2466081df201322768a3cc6f2d1a9a8` | 15,776 |
| `native_decoder_20260920_205540_430.json` (G15) | `430b55c2ffe050b8974f9bbf0cae31515e9b1d7b06751d2b7314fd3275d09e50` | 12,064 |
| `native_decoder_20260920_205736_106.json` (G15b) | `a5238971929c8b6b978fdafb460a6d0a78fc3a944f726b3e48ef632273315387` | 12,593 |
| `native_decoder_20260920_205931_120.json` (G15c) | `3cb2a68dabb5af6a3ad83b0a0bdc01c1f29f94641d4f5ad0108a4bea2d0e07d2` | 11,586 |
| `g150_launcher_prompt.txt` | `b5a5ac530635cba48760d7ff7de6ab5f2e4a2af71b7536a99b876e5ffd369011` | 350 |

## Privacy

No network addresses, ADB endpoints, MACs, SSIDs or device identifiers
appear here or in the copied artifacts. The launcher dump was filtered to
element text and bounds.
