# B33 — no rewind without loss: the design, written and hashed before any B33 code

Queue `handoffs/QUEUE_2026-10-31L.md` §B33. Facts (TRIP-R2 §2): three stall pauses in golf (04:19:18, 04:30:10,
04:37:43) each ended `input_release` via `stall_end`, method `state` — `LOAD_STATE_SLOT 9`, 25-28 net unattended
frames, ~0.45 s of play and the presses in it undone. Five such loads all evening (also 05:07:17, 05:28:39), every one
a stall of 519-574 ms onset → pause, released by `stall_end` 25-30 ms after the pause.

## 1. Where the load happens today (the code, base 1904fe8)

Every release that can load goes through one call: `hold_rewind.Rewinder.rewind(recovery, via)` →
`rewind_cores.Cores.release` (mode `state`, which `PRIVYHUB_INPUT_HOLD_REWIND=1` means since B12, and which
`PRIVYHUB_LINK_RECOVERY=1` implies). Callers: B2's `note_input_release` (via `input_release`, a silence), B7's
`StallSignal.resume` (via `stall_end` / `stall_quiet`), B12's `StallOwner.ready_resume` (`client_ready_stall`), B8 /
v2's resumes. The save (B9's silence mark at 400 ms, B16's stall save at the stall signal) is taken before the pause
and is not touched here.

## 2. The rule (decided at the release, from what the host already holds)

The episode's **length** = release time − onset (the pending's onset as `Cores.release` already reads it:
`b8_hold_onset` else `onset`: the client's last displayed frame for a stall, the last controller packet for a
silence).

**`resume` (no load)** only when all of these hold; otherwise today's load, with the first failing term as `why`:
1. **short:** length < 1,000 ms (`why` `long` otherwise — "any silence ≥ 1 s, as today"; a stall ≥ 1 s too);
2. **evidence:** at least one client heartbeat received in the window [onset − 2.5 s, release] and a predecessor for
   the first of them (`no_heartbeat` otherwise: no evidence is not "no loss"). 2.5 s = the heartbeat's 2-s interval +
   margin, so the window always holds the heartbeat that covers the time just before the onset;
3. **post-FEC loss 0 in the window:** every heartbeat in the window shows, against its predecessor,
   Δ`lost_packets` = 0 (the receiver's post-FEC loss, WAN telemetry's `post_fec`) and Δ`fec_unrecoverable_groups` = 0
   (`loss`; a counter that went down = a reset = `counter_reset`, treated as loss);
4. **no dark span:** every heartbeat in the window has `audio_max_arrival_gap_ms` < 250 (`dark_span`): audio rides
   the same downlink every 20 ms, so a gap ≥ 250 ms means the downlink delivered nothing (B1's "dark");
5. **the uplink alive:** the host's own controller-sequence loss counter (`controller._lost_packets`, the receive
   loop's count of missing sequence numbers) unchanged from the newest heartbeat-time sample at or before the onset
   to the release (`uplink_loss`; unreadable = `uplink_unknown`, treated as loss). A silence whose packets come back
   in sequence is the client not sending (an activity pause), not the network dropping them.

The decision cannot wait for the heartbeat that covers the stall itself (it arrives up to 2 s after the release; the
resume cannot wait). So the rule is "no loss known behind it at the release": loss before or around the onset that the
host has seen. Stated as the rule's limit.

**On `resume`:** `input_release` row, `method` `resume`, `why` `no_loss_under_1s`, the length, the terms read; no
command to the core (no PAUSE_TOGGLE, no LOAD); the caller's own `_resume_game()` then resumes the paused core
exactly as today's resume after the load. The pause still happened ("pauses at most"). The save stays on disk and
B9's `last_save` is cleared (one release per save, as after a load).

**On the load:** today's path byte for byte, plus `why` on its row (`long` / `loss` / `dark_span` / `uplink_loss` /
`uplink_unknown` / `no_heartbeat` / `counter_reset`), and `held_ms`.

## 3. The switch (no new adoption; the queue says "inside the adopted `PRIVYHUB_LINK_RECOVERY=1`")

`PRIVYHUB_REWIND_NEEDS_LOSS`:
- **absent:** on iff `PRIVYHUB_LINK_RECOVERY=1` (the adopted umbrella; B26's convention: a fix inside the adopted
  line needs no new adoption line). Live at the next companion restart.
- **`0`:** off — today byte for byte under the umbrella (the one-line rollback).
- **`1`:** on without the umbrella (a bench with the individual lines).
- **other:** as absent, with the value noted in the config row.

Why not a seventh implied line in the umbrella: B20's umbrella "means exactly the six stack lines … and nothing
more", and B20 / B21's `describe` / `config_row` / tests read six; the new rule is a behaviour of the sixth's release,
so it keys on the umbrella directly and leaves `link_recovery.py` untouched.

**Absent = today byte for byte:** with neither the umbrella nor `=1` (every B9 / B12 / B16 suite, which set the
individual lines), and with `=0`: the module is never imported, no row or field is added, `Cores.release` and
`note_heartbeat` take today's path (one `is None` test each). Proven by: B9 / B12 / B16 / B4 / B7 / B8 suites
unedited and green; a scripted episode run against the base modules and the new with the rule off, rows equal with
times masked; a fresh process imports nothing.

## 4. Code (smallest)

- `companion/rewind_needs_loss.py` (new): `mode(environ)`, `Rule` (heartbeat samples: rx time, `lost_packets`,
  `fec_unrecoverable_groups`, `audio_max_arrival_gap_ms`, the controller's uplink counter; `decide(onset, now)`),
  `wire(cores, recovery, controller, environ)` → the rule on `Cores.no_loss` and `recovery._rewind_needs_loss`, one
  `rewind_needs_loss_config` row.
- `companion/rewind_cores.py`: `Cores.no_loss = None` (class attr); in `release` (state mode), one guarded branch
  after the method fields: the rule decides; `resume` → the row and return; else `why` / `held_ms` into the fields
  and today's path. In `wire`: the guarded import and wire when `mode(environ)` is on.
- `companion/games/link_drop_recovery.py`: `_rewind_needs_loss = None` (class attr); `note_heartbeat`: one guarded
  call feeding the rule the record.
- Nothing in `plugins/games.py` (the wire rides `rewind_cores.wire`, which the plugin already calls).

## 5. Tests (`tests/rewind_needs_loss/`, B9's fake core, the real recovery / Rewinder / Cores / StallSignal / StallOwner)

- a 450-ms stall, 0 loss (heartbeats flat, the uplink counter flat) → pause, the save taken, `input_release`
  `resume` `no_loss_under_1s`, **no LOAD** at the fake core, `resumed`;
- the same with Δ`lost_packets` > 0 in a window heartbeat → the load as today, `why` `loss`;
- a 2-s silence (hold) → the load, `why` `long`; a 0.97-s silence with no loss → `resume`;
- a dark span (audio gap 300) → load; uplink loss → load; no heartbeat → load;
- the switch: absent / umbrella / `0` / `1` / junk; the config row; a fresh process imports nothing without it;
- absent = today: the scripted episode against `/tmp/b_q31l_base`'s modules and the new (rule off), rows equal;
- mutations: the loss term ignored (the loss test fails); the 1-s bound raised to 3 s (the 2-s test fails).

## 6. The replay (read-only, `trip_r2_2026-10-31/copies/`)

Every `input_release` of the trip (5, the three golf ones among them) through `decide` with the heartbeats the host
had received by each release (the uplink counter is not in any log: stated, with the ctrl-gap rows beside it).

## 7. Settle, not built: "the stream is live again"

Options for the user (to choose later), after a restart or a resume: a one-frame tint; a corner mark for 1 s; a
short tone; nothing. In the record with what each costs and where it would live.
