---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
status: IMPLEMENTED as D-BASE-R3 and corrected by D-BASE-R3a, 2026-09-20; D-BASE-R3b ran the nftables fault 2026-09-22 and N3/N15/N150 all PASS against real on-the-wire loss — but N05, N15b and E30 were NOT run, so this is NOT yet RUNTIME VALIDATED (the handoff requires N05+N3+N15+N15b+N150). Two post-run defects open. Evidence: evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md, evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md, evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md, evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md; patches: patches/D-BASE-R3_LINK_DROP_SELF_RECOVERY.md, patches/D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS.md
---

# Link-drop self-recovery — design note

Behaviour was decided by the user on 2026-09-20 (`docs/KNOWN_ISSUES.md`,
"link-drop resilience"): **pause the game the moment the session feels
desynced; keep auto-recovering the stream; unpause only after a separate
resync check passes; after a bounded time, save and stay paused with the
launcher saying so.** This note proposes the numbers and the wiring. Every
number is a named constant; the user picks the values.

The freeze that motivated it: during play on 2026-09-20 the onn held a stale
frame while the host kept running, coincident with a house-network fault.
The game advanced blind. Nothing paused, nothing recovered, nothing was
recorded (`D_BASE_R2` now records it; still nothing acts).

## What already exists, and is reused unchanged

| step | existing piece | where |
| --- | --- | --- |
| host pauses / resumes the game | `EmulatorManager.pause()` / `.resume()` — RetroArch `PAUSE_TOGGLE` with state confirmation | `companion/games/emulator_manager.py` |
| host knows the client is alive, at 250 ms resolution | controller receiver tracks `_last_packet_at` per player and neutralizes inputs after 250 ms of silence; the client sends ~430 controller packets/s even with no input | `companion/native_session_io.py` |
| host knows the client is alive, at 2 s resolution | `native-stream-heartbeat` with `last_output_age_ms` (`D-BASE-R2`) | `companion/plugins/games.py` |
| client knows it is not getting video | `last_output_age_ms`, computed every 500 ms tick | `NativeStreamActivity.updateMetrics` |
| client resyncs after a gap that ends | sequence/SSRC resync + IDR wait, GOP 15 = an IDR within 250 ms | `RtpH264Receiver` |
| host restarts the encoder without touching capture, FEC, audio, controller or the emulator | the `C3.L1` encoder-only restart primitive (kill, RTP baseline, spawn, poll, 0.75 s stability) | `companion/diagnostics/c3_linux_actuator_probe.py` |
| "the stream is good, release the game" | the startup stabilization gate: 6 consecutive clean 500 ms ticks (rendered advancing, no drops, no overflow, queue 0, fps >= 45, gap <= 120 ms, rx->decode <= 150 ms), 15 s timeout, then `native-stream-ready` -> `resume()` | `NativeStreamActivity` + `games.py` |
| save state | `EmulatorManager.save_state(slot)` | `emulator_manager.py` |
| launcher reconciles from a failed poll | `D-BASE-R2` piece 3 | `MainActivity` |

The design is wiring between these. No new transport, no new decoder
configuration, no new emulator control path.

## The state machine (host side, in the companion)

```
PLAYING ──(client silent >= DESYNC_MS, or client posts desync)──> PAUSED_RECOVERING
PAUSED_RECOVERING ──(client posts native-stream-ready after passing the gate)──> PLAYING
PAUSED_RECOVERING ──(GIVE_UP_MS elapsed)──> PAUSED_SAVED
PAUSED_SAVED ──(user resumes from the launcher; gate passes)──> PLAYING
PAUSED_SAVED ──(END_MS elapsed)──> ENDED (graceful stop; save already taken)
```

The host is the authority. The client cannot ask for a pause while the link
is down, so the host pauses on its own evidence: **controller-packet
silence**, which it already measures. The client's own detector is
secondary (it freezes its display, shows an overlay, and posts a desync
notice if it can) so the two sides agree within a second even when only
one of them can see the fault.

### 1. Pause on desync

- **Host trigger:** no controller packet from the active client for
  `DESYNC_MS`. Checked in the existing 250 ms controller-receiver loop, so
  latency to pause is `DESYNC_MS` + <= 250 ms + the RetroArch pause
  round-trip (tens of ms).
- **Client trigger:** `last_output_age_ms >= DESYNC_MS` on the 500 ms tick,
  or no RTP packet for `DESYNC_MS`. The client stops rendering new frames
  (there are none), keeps the last frame, shows the stabilization overlay
  as "Reconnecting…", **keeps sending controller packets** (they are the
  host's liveness signal), and posts `native-stream-desync` best-effort.
- **Proposed `DESYNC_MS` = 1,000.** The corpus says why not lower: ordinary
  transport hiccups on this link end in 200-600 ms (`max_output_gap_ms`
  p50 287, p90 607 across 127 sessions) and the receiver already recovers
  from those by itself. A pause below ~700 ms would fire on a stall the
  stream was about to recover from anyway, and a pause costs the resync
  gate (below) on top of the stall. 1,000 ms is above p90, it is a freeze a
  player unambiguously feels, and only 8 of 127 sessions ever exceeded it.
  The user's "the moment it feels desynced" is the constant to tune; 750 is
  the reasonable floor, 1,500 the ceiling.

### 2. Auto-recover

While `PAUSED_RECOVERING`:

- **Host:** keeps the emulator paused and the encoder running (a paused
  game encodes a static frame at low cost; nothing needs to stop). Watches
  for the client to reappear: a controller packet, a heartbeat, or a fresh
  `native-stream-start`. On reappearance it does nothing special if RTP
  resumes on its own — GOP 15 delivers an IDR within 250 ms and the
  receiver's resync path takes over. If the client reports
  `last_output_age_ms` still rising `RESTART_AFTER_MS` after reappearing,
  the host runs the `C3.L1` encoder-only restart (fresh SPS/PPS, new SSRC,
  which forces the client's SSRC resync). At most one restart per
  `RESTART_BACKOFF_MS`.
- **Client:** if it is still alive, it just keeps receiving. If its
  `NativeStreamActivity` was killed (app swipe, low memory, reboot), the
  launcher's RESUME PLAYING path already re-enters the stream; that path
  posts `native-stream-start`, which the host must accept while a session
  is already `PAUSED_RECOVERING` (today it would try to pause an
  already-paused game — harmless, but it should be explicit).
- **Proposed:** `RESTART_AFTER_MS` = 2,000; `RESTART_BACKOFF_MS` = 5,000,
  doubling to a cap of 30,000. Restarts are logged with the `C3.L1` cycle
  record so they can be counted per session.

### 3. Resync check before resume

The client re-enters the **same stabilization gate it passes at startup**
and posts `native-stream-ready` when it clears; the host resumes the game
exactly as it does at startup. Same code, second use.

One parameter differs: `STABILIZATION_CLEAN_TICKS` is 6 (3 s) at startup.
For recovery, propose **`RECOVERY_CLEAN_TICKS` = 3** (1.5 s): the encoder,
capture and audio are already warm, so the startup allowance for first-IDR
and decoder spin-up does not apply, and every 500 ms here is felt. The
per-tick criteria (fps >= 45, gap <= 120, rx->decode <= 150, no drops)
stay as they are; they are what "resynced" means. If the gate times out
(15 s), the client stays in recovery and the host's restart logic applies.

### 4. Give up safely

- After `GIVE_UP_MS` in `PAUSED_RECOVERING`, the host writes a **recovery
  save that is not one of the three player slots**, then moves to
  `PAUSED_SAVED`. The game is not ended; the emulator stays paused. The
  launcher's status (from `/plugins/games/status`, which gains a `recovery`
  block) reads "Stream lost — paused and saved HH:MM". RESUME PLAYING still
  works and runs the gate.
- After `END_MS` in `PAUSED_SAVED`, the host ends the session gracefully
  (the recovery save is already on disk). The launcher shows "Game ended
  after connection loss — recovery save available".

**The recovery save, as the user decided it (2026-09-20):** its own file,
never one of slots 1-3, and the three slots stay the only slots.

- Mechanism: `save_state()` already has RetroArch write `<stem>.state`
  (RetroArch's slot 0) and then copies it into `<stem>.state{1,2,3}`. The
  recovery save is the same command with the copy going to
  **`<stem>.state.recovery`** in the same savestate directory. One file per
  game; a later recovery overwrites it. It is never listed as a slot and
  `_normalize_save_state_slot` keeps rejecting anything but 1-3, so no
  existing path can touch it by accident.
- **Prompt on return, not during the outage.** When the launcher next
  reaches the companion and `status.recovery.save_available` is true, it
  shows one dialog: *"The stream was lost at HH:MM and the game was saved
  automatically."* with **Resume from recovery save**, **Copy to slot 1 /
  2 / 3** (the existing occupied-slot confirmation applies), and **Discard**.
  Copying uses the same slot-write path as a manual save, so the slot
  rules are unchanged. Resume without copying loads the recovery file
  through the normal load path (`<stem>.state.recovery` -> `<stem>.state`
  -> `LOAD_STATE_SLOT 0`).
- If the session ended at `END_MS` and the user later launches the same
  game, the same prompt appears before the launch proceeds.

## Interfaces added (all additive; nothing existing changes shape)

- `POST /plugins/games/native-stream-desync` — client -> host, best-effort,
  `{reason: "output_silence"|"rx_silence", age_ms}`. Host treats it like
  controller silence.
- `GET /plugins/games/status` gains `recovery: {state, since_ms,
  restarts, last_client_seen_ms}`.
- `native-stream-heartbeat` unchanged; the host now reads it.
- Companion log line on every state transition, in
  `logs/games/native_stream_recovery.log` (JSON lines, host time, no
  addresses), so a recovery that happens at 2 a.m. can be read at 9 a.m.

## What it deliberately does not do

- Does not restart RetroArch, the FEC relay, audio or the controller
  transport. Those are the stable subsystems; only the encoder is
  restartable, and only via the validated primitive.
- Does not change any streaming constant, the decoder configuration, or
  the 60 ms stale-drop policy.
- Does not touch the receiver's resync/IDR logic. A gap that ends is
  still the receiver's job; this design owns only gaps that do not end.
- Does not pause on audio starvation alone. Audio loss with video flowing
  is a different fault and pausing would make it worse.

## Risks named now

- **PAUSE_TOGGLE is a toggle.** `pause()`/`resume()` confirm RetroArch's
  state after sending, so a desync between companion and emulator state is
  caught, but a recovery path that pauses twice or resumes twice must go
  through those methods, never send the command directly.
- **The heartbeat and controller channels are both UDP/HTTP over the same
  link.** When the link is down, the host sees silence on both and cannot
  tell "client dead" from "link dead". It does not need to: both mean
  pause. The distinction matters only for `END_MS`, and 30 minutes makes
  it moot.
- **A pause threshold that is too low turns every hiccup into a 2.5 s
  interruption** (1 s to detect + 1.5 s gate). That is the tension the
  user should decide with the corpus numbers above in view.
- **R2B** (`D_BASE_R2`) — one session with 3.5x the normal spike rate and
  the heartbeat active — is unexplained. If the heartbeat's HTTP post is
  ever shown to cost decode time, the desync notice must not add a second
  periodic post; it is one-shot by design.

## Validation plan (autonomous, host shell, no user action)

Fault injection is host-side so ADB to the onn stays up:

```
sudo nft add table inet privyhub_fault
sudo nft add chain inet privyhub_fault out '{ type filter hook output priority 0; }'
sudo nft add rule inet privyhub_fault out udp dport {48100,48101} drop   # video+audio to the onn
sleep <N>
sudo nft delete table inet privyhub_fault
```

Runs, each from a stable attract-mode session on the reference title:

| N | expected |
| --- | --- |
| 0.5 s | no pause (below `DESYNC_MS`); receiver resyncs alone; gap row recorded |
| 3 s | pause within ~1.3 s; client overlay; auto-resume via gate within ~2 s of the rule being deleted; `recovery.restarts` 0 |
| 15 s | as above; one encoder restart if the client does not resync on its own within `RESTART_AFTER_MS`; resume via gate |
| 150 s | pause; `GIVE_UP_MS` reached; state saved; launcher shows the saved status; deleting the rule then RESUME PLAYING restores play |

Evidence per run: the recovery log, the session report's gap row,
heartbeat lines through the fault, and `uiautomator dump` of the launcher
at give-up. Teardown per `TOOLS.md`.

## Decisions

All decided by the user, 2026-09-20. These are the constants the code uses.

1. `DESYNC_MS` = **1,000**.
2. Recovery save = **its own file (`<stem>.state.recovery`), never slots
   1-3, with a launcher prompt on return offering resume / copy to a
   chosen slot / discard.**
3. `RECOVERY_CLEAN_TICKS` = **3** (startup gate stays at 6).
4. `GIVE_UP_MS` = **120,000**; `END_MS` = **1,800,000**.
5. **Authorized as `D-BASE-R3`**: companion + client, one patch, validated
   with the plan above. Also fixed by this authorization:
   `RESTART_AFTER_MS` = 2,000; `RESTART_BACKOFF_MS` = 5,000 doubling to a
   30,000 cap.

Classification at authorization: DEVELOPMENT. It becomes RUNTIME VALIDATED
only when all four fault-injection runs match the expected column, with raw
evidence in `evidence/D_BASE_R3_LINK_DROP_RECOVERY_2026-09-20.md`.

## Outcome, 2026-09-20 — R3 then R3a

Built and installed; the pause, the gate-driven resume, the give-up save and
the launcher prompt all work. `D-BASE-R3` left two defects, both **fixed and
validated by `D-BASE-R3a`** on the same day. The validation plan above
**still cannot be run as written**: `sudo nft` needs a password this host
does not have non-interactively, so every run so far used a host-side
substitute (SIGSTOP on the managed encoder). **The nftables runs are owed.**
Read both evidence records before reusing this plan.

Three corrections this note needed. Two are **made** by `D-BASE-R3a`
(`evidence/D_BASE_R3A_RESTART_FALLBACK_2026-09-20.md`); the third stands.

1. ~~`RESTART_AFTER_MS` must test that the age is *still rising*~~
   **DONE (R3a fix 2).** The trigger now needs two newest heartbeats both
   at or above `DESYNC_MS` with the newer not lower, and the newer received
   at or after the moment the restart became eligible. A 3 s outage now
   records `restarts` 0 where the pre-fix build restarted every time.
2. ~~The note has no answer for a failed encoder restart~~
   **DONE (R3a fix 1).** When the session has no encoder, the recovery calls
   the same `NativeStreamManager.start()` `native-stream-start` uses instead
   of re-entering the `C3.L1` cycle, and logs `method: "full_start"`. The
   primitive's failure path is unchanged.
3. **The plan still never exercises the host-side controller-silence
   trigger.** Neither the nft rule nor any host-side substitute interrupts
   the client->host controller channel, so only the client's notice ever
   fires. Testing it needs the client stopped, not the link.

Two pass criteria in the plan above are not reachable as written, and
`D-BASE-R3a` measured why:

- **"resume within 2.5 s of the clear"** — the gate costs a baseline tick
  plus `RECOVERY_CLEAN_TICKS` clean ticks, a 2.0 s floor, and the encoder
  needs ~1-2 s to resume. Measured 3.066 s with the restart suppressed
  correctly. Changing it means changing the gate.
- **"resume within one backoff interval of the clear"** on a 15 s outage —
  the first restart attempt blocks ~12 s in `_kill_managed_process`
  (`SIGTERM`, 5 s wait) against an encoder the *substitute* injector holds
  stopped. Not a property of the recovery; it should disappear under the
  nftables rule.

## 2026-09-22 — R3c: the launcher rule and the paused-load loop

**The prompt's precondition and the live-session rule** (the user's
decision, `../decisions/D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE.md`): a
recovery state never loads into a live core; a live session makes the tile
**Resume** (no load); the recovery prompt appears **only when no live
session exists**, and resume-from-recovery launches a fresh core, loads,
then deletes the recovery file. **Not implemented yet.**

**Why not yet** (`../evidence/D_BASE_R3C_RECOVERY_SEMANTICS_2026-09-22.md`):
a recovery save taken mid-FMV **loops when loaded into a paused core, fresh
or not**, and plays when loaded into a running one; a gameplay state loaded
paused plays. `load_recovery_state` requires a paused core and the launch
path leaves the core paused, so the decided flow would still loop for a
cutscene give-up. The load ordering is the user's next decision.

## 2026-09-23 — R3c2: the resume sequence, implemented

Recovery prompt: offered by the game tile **before a launch**, only when no
session is live and a `.state.recovery` exists for that title; a live
session's tile is **Resume** (no load). **Resume from recovery:** end any
live session → the normal launch (paused handoff) → `resume()` → 1 s →
`LOAD_STATE_SLOT 0` into the **running** core, RetroArch's `[State]
Loading` line required → `pause()` → delete the file, `.png` and index;
failure keeps them. Copy-to-slot runs in a plain session of the title,
then deletes the recovery save; discard deletes it and the client launches
plain. RUNTIME VALIDATED (`../evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`).
