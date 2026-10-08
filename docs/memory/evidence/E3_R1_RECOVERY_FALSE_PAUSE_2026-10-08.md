---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: def1ad1
---

# E3-R1 — recovery's false pause

**Classification: INCONCLUSIVE (the replay is not faithful).** The task
stops at its own stop rule, before any suite run.

- The pre-registered offline replay of **today's** rule did not
  reproduce two recorded in-suite events. Two reasons, both stated in §3:
  - a replay-model defect: an earlier pause's state was not carried;
  - a resolution limit of the records: 1-s packet counts cannot see a
    ~1.0-s silence whose late packets land in the same second.
- No benchmark ran.
- The change sits in the tree, dormant, behind
  `PRIVYHUB_RECOVERY_TRIGGER=v2`. **NOT ADOPTED**; nothing committed.

**What the probe found** (§1; the useful part of this task):

- **The harmful false pause is the host's `controller_silence` trigger
  on a client→host stall.**
  - In four suite pauses the onn's uplink stalled for ~1-3 s: the
    controller packets dipped, then arrived late in a burst.
  - The host→client stream and the client's own output stayed fine. The
    client never stopped playing.
  - Recovery has no way back from that pause: the client never saw an
    output stall, so it never runs its re-entry gate. **Three of the four
    sat 120 s, gave up, saved, and stayed paused.**
- **The client's own `client_output_silence` false pauses are a
  different thing.**
  - They were real 1.0-3.2-s output stalls, all on 10-06, before the
    index removed the per-grab parse.
  - Each resumed by itself, as designed.
  - The host cannot tell them from R3's shortest real drops (N3, F3) at
    any signal it has.
- **Idle, the client sends 460 controller packets/s** with no input. Max
  age was 295 ms in 10 min, so silence-while-idle (hypothesis b) is
  ruled out.

**Context:**

- Task: `handoffs/E3-R1_RECOVERY_FALSE_PAUSE_TASK.md`, item 1 of
  `handoffs/QUEUE_2026-10-08.md`.
- **Baseline commit: `def1ad1`**, the user's E3-A2 commit.
- It ran on the adopted state (live, the guide index, Snes9x).
- Files: `e3_r1_2026-10-08/`.
- Timeline (UTC, 2026-10-08):

  | time | what |
  | --- | --- |
  | 03:39 | preconditions held (`precondition.json`, the three-line state) |
  | 03:39-03:45 | the timelines reconstructed |
  | 03:45-03:57 | the idle probe (window 03:46:17-03:56:17), PLAYING throughout; teardown clean |
  | 03:57 | the change applied (dormant); a unit check of its logic |
  | **03:58:40** | **pre-registration hashed** (`e8a8d97a…12be`) |
  | 03:58:41 | the replay: today's rule not faithful → stop |

## 1. The probe (`probe.md`)

**The timelines** (`e3_r1_timelines.py` → `timelines.json`; per second,
±60 s):

- every recorded `desync_pause` in the five suite runs (seven events);
- three of the same type outside the suite (10-05);
- every real drop: R3b/R3d's nft outages N05, N3, N15, N15b, N150, E30,
  and R3's 09-20 substitute outages F05, F3, F15, F150.

| event | trigger, age | what the client→host channel did | the client's output | then |
| --- | --- | --- | --- | --- |
| E2 PS1-1080P r1 (10-05) | `controller_silence`, 1,002.5 | 458 → 256 → **15** pkt/s, then a 1,031/s catch-up | — (no heartbeat log that night) | +120 s `gave_up_saved` |
| E3-S1 CONC r1b (10-06) | `controller_silence`, 1,003.2 | 393 → **18** → 641 / 978 / 985 | next heartbeat 26 ms | +120 s `gave_up_saved` |
| E3-S1 CONC r2a (10-06) | `controller_silence`, 1,002.1 | 404 → 1,117 (a ~1-s gap inside two seconds) | next heartbeat 144 ms | resumed +32 s (a later client-side stall ran the gate) |
| **E3-A2 PS1 r1** (10-07) | `controller_silence`, 1,003.6 | 266 → **48** → 931 → 71 → **6** → 1,410; heartbeats **3.1 s late** | 13 / 174 ms | +120 s `gave_up_saved` |
| E3-S1 control (10-06) | `client_output_silence`, 1,149 | steady | 1,669 → **0** ms | resumed +2.8 s |
| E3-S1 CONC r1a (10-06) | `client_output_silence`, 1,011 | steady | up to 3,198 ms | resumed +18.3 s |
| E3-S1 CONC r2b (10-06) | `client_output_silence`, 1,206 | steady | 703 → 149 ms | resumed +24.8 s |
| *real:* R3b N3 (3.06 s) | `client_output_silence`, 1,132 at +1.27 s | untouched (heartbeats on time) | 2,166 → **23** ms | resumed +3.6 s |
| *real:* R3 F3 (3.09 s) | `client_output_silence`, 1,095 at +1.30 s | untouched | 1,614 → **0** ms | resumed +5.2 s |
| *real:* N15, N15b, N150, E30, F15, F150 | `client_output_silence`, 1,147-1,492 at +1.28 to +1.73 s | untouched | rising 2 s per heartbeat | restarts; resumed or saved as R3 recorded |
| *real:* N05 (0.56 s), F05 (0.75 s) | — (no pause) | untouched | ≤ 158 ms | — |

- **The idle probe** (`e3_r1_idle_probe.py`, `idle_stats.json`): a PS1
  stream PLAYING, nobody at the controller, 10 min.
  - Controller packets with no input: **yes, 460/s** (every ~2.2 ms;
    minimum 417/s).
  - The age the recovery monitor reads: median 3 ms, p99 28 ms, **max
    295 ms**, never over 500.
  - The client's output age: max 144 ms.
  - Heartbeat arrival gaps: max 2.23 s. PLAYING throughout.
- **The reading (the task's rule):**
  - **(b) no**: idle, the controller age never grows.
  - **(c) no**: the fired ages (1,002-1,004 ms) agree with the
    neighbouring seconds.
  - **(a) yes, for the controller trigger**: every controller false
    pause sits on a client→host stall longer than the 1-s threshold
    (est. 1.2-3.2 s). The real drops (3-150 s) never used that trigger,
    because the nft rule and the substitute stopped only host→client
    traffic (R3's "unexercised" note).
  - **For the client trigger, no length separates false from real.** The
    false output stalls reach 3.2 s; the real drops start at 3.06 s. That
    detector is the client's (the APK).

## 2. The change, as pre-registered (dormant)

`PRIVYHUB_RECOVERY_TRIGGER=v2` (`patches/E3-R1_RECOVERY_TRIGGER_V2.md`,
`e3_r1_trigger_v2.diff`, +22 lines in `companion/plugins/games.py` and
`companion/native_session_io.py`):

- The host's controller-silence trigger fires only after **5,000 ms** of
  silence, seen on **two checks ≥ 250 ms apart** with no packet between.
- 5 s sits ~1.8 s above the longest false uplink stall (~3.2 s, A2).
- The client-posted desync, the give-up timer, the restart path and the
  save-and-prompt flow are unchanged.
- Absent: 1,000 ms, first check, as today.
- A unit check of the confirm logic passed (not data).
- `tools/test_c3_f1_recovery_restart.py`: 7/8. The one error fails at
  `def1ad1` too: its `restart_encoder=(` source probe no longer matches
  the wiring's text. It predates this change.

## 3. The replay (`e3_r1_replay.py`, `replay.json`, `replay.md`)

| clause | needed | got | holds |
| --- | --- | --- | --- |
| **r1. today's rule reproduces every recorded event** (±2 s; no fire on N05 / F05) | all | 15 of 17 gated events. **Not** S1-CONC r1b (replayed at −5.24 s) and **not** S1-CONC r2a (first replayed fire +24.9 s) | **no → STOP** |
| r2. v2 fires on every real drop within +2 s; not on N05 / F05 | all | +0.0 s on all eight; neither N05 nor F05 | *(would hold)* |
| r3. v2 fires on none of the five false pauses | none | not on E2-1080P r1 or A2 r1; **fires on S1 control, S1-CONC r1, S1-CONC r2** (their client-trigger pauses, as stated before the replay) | *(would fail)* |

**Why r1 failed, read by hand** (the bar unchanged):

- **S1-CONC r1b:** the replay fired on a 1.09-s silence 5 s before the
  recorded event.
  - At that moment the recorded state was **already paused** by r1a,
    which resumed only 3 s before r1b.
  - The replay applies the PLAYING check only to its own firings, not
    to a pause from a neighbouring event.
  - With that state carried, its next silence (1.13 s at −0.17 s) fires
    at +0.83 s, which is faithful. **A replay-model defect.**
- **S1-CONC r2a:** the recorded ~1.0-s silence fell across two sampler
  seconds (404 → 1,117 packets/s), and the late packets' burst landed in
  the same seconds. 1-s counts cannot see it. **A resolution limit of the
  records**, not fixable in the model.
- Not gated: the out-of-suite controller event of 10-05 15:14 has no
  sampler or heartbeat data. Its replay is reported as such.

**What a faithful replay needs:** the receive loop's silences with their
exact times (e.g. every gap > 250 ms, logged once per gap: start, length,
and the packets of the catch-up burst). One measurement hook, off by
default. It is not added here; it would be a task of its own.

## 4. What this cannot show, and the hand step (if the user wants the change tested on the air)

Adoption is not on the table (INCONCLUSIVE). If the user wants v2 tested
on the air anyway, the harness is R3b's.

`d_base_r3b_2026-09-21/r3b_run.sh` drops given UDP ports with
`sudo -n nft` for N seconds and records the recovery lines.
`tools/c3_l4_nft_night.py` is the ladder's harness and its preflight
refuses an unadopted flag.

One paste, from the repo root, by the user:

```bash
printf '[Service]\nEnvironment=PRIVYHUB_RECOVERY_TRIGGER=v2\n' > ~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
systemctl --user daemon-reload && systemctl --user restart privyhub-companion
(cd docs/memory/evidence/d_base_r3b_2026-09-21 && ./r3b_run.sh V2-N3 output 48100,48101 3 30 && ./r3b_run.sh V2-N15 output 48100,48101 15 40 \
  && ./r3b_run.sh V2-C2 input 48102 2 30 && ./r3b_run.sh V2-C8 input 48102 8 40)
rm ~/.config/systemd/user/privyhub-companion.service.d/e3_flag.conf
systemctl --user daemon-reload && systemctl --user restart privyhub-companion && python3 tools/e3_state.py
```

**What the reply must contain** (each run's `recovery_lines.jsonl`):

| run | expected |
| --- | --- |
| V2-N3, V2-N15 (host→client dropped) | `desync_pause` `client_output_silence` at ~+1.3 s, then `resumed`, as R3b N3 / N15. **The real-drop path is unchanged.** |
| **V2-C2** (client→host dropped 2 s) | **no `desync_pause`**. Today's rule pauses at +1 s and never comes back. |
| **V2-C8** (client→host dropped 8 s) | `desync_pause` `controller_silence` at ~+5.25 s. After the clear the client is still playing, so the pause will not resume by itself. This is the open design question below. |

The last line of the reply: `e3_state.py` `"ok": true`, three lines.

**The open design question this task surfaces:** a `controller_silence`
pause has no exit when the client is still playing. A pause that
cleared itself on the controller packets' return, plus a fresh output
age on the next heartbeat, would remove the 120-s give-up and save in
every such case. That changes the resume path, which this task kept
fixed.

## 5. State at the end; files

- **Final state:** the adopted state (`e3_state.py` ok, 03:57Z and
  after). Manager none; environ exactly live + the index + Snes9x; no e3
  drop-in; no game; the PS1 files identical; **APK CONFIRMED**.
- The flag was never set; the v2 code is dormant.
- No `nft`, no real `sudo`, the Opal untouched; nothing fetched,
  nothing deleted.
- **E3-A2's validity rule:** this task ran no suite run. The idle
  probe's session stayed PLAYING throughout (`idle_stats.json`
  `states_seen`).
- Files (`e3_r1_2026-10-08/`):
  - `precondition.json`;
  - `e3_r1_timelines.py`, `timelines.json`, `timelines.md`, `probe.md`;
  - `e3_r1_idle_probe.py`, `idle_probe/`, `idle_probe_console.log`,
    `idle_stats.json`;
  - `e3_r1_trigger_v2.diff`;
  - the pre-registration and its `.sha256`;
  - `e3_r1_replay.py`, `replay.json`, `replay.md`, `replay_console.txt`;
  - `redact_check.txt`.
- Git status: `logs/e3_r1_git_status.txt`.
