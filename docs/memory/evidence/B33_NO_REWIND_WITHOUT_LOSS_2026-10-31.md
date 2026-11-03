---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8 (companion/ tools/ tests/ PrivyHub/ clean at the start; B33 uncommitted)
---

# B33 — no rewind without loss: a stall or silence under 1 s with no loss behind it resumes, not loads

**Classification: BUILT** inside the adopted `PRIVYHUB_LINK_RECOVERY=1`, with `PRIVYHUB_REWIND_NEEDS_LOSS=0` as the
off switch.
- **Tests:** `tests/rewind_needs_loss` 14 green (three runs). Every `tests/` suite is the same as the queue-L
  baseline. Two mutations caught.
- **Proof:** absent = today, PROVEN (three states, row for row).
- **The replay:** of the trip's 5 loads, **4 would have resumed**, the three golf ones among them. The fifth is the
  05:28 link loss, which still loads.
- **Status:** live only at the next companion restart. NOT ADOPTED as a new line; no live run; nothing committed.

Design `b33_2026-10-31/design_written_before_code.md`, sha256 `ea64af8a…147d`, hashed **17:40:01Z, before any B33
code**. The code was built in `/tmp/b_q31l_b33` only. The coordinator integrates it and applies it to the tree.

## 0. What happens today (the code at 1904fe8)

- **One place loads.** Every release that can load goes through `Rewinder.rewind` → `rewind_cores.Cores.release`.
  This is the `state` mode, which the umbrella implies through `PRIVYHUB_INPUT_HOLD_REWIND=1`. The callers are:
  - B2's hold release (`input_release`, a silence);
  - B7's `stall_end` / `stall_quiet`;
  - B12's `client_ready_stall`;
  - B8's and v2's resumes.
- **Every such release loads slot 9 when a matching save exists.**
  - The save is B9's at 400 ms of silence, or B16's at the stall signal.
  - Friday's 5 loads were all `stall_end`: 519-574 ms from onset to pause, the release 25-30 ms after the pause, and
    25-28 net unattended frames undone each.

## 1. Built (`b33.diff`)

**The rule** (`companion/rewind_needs_loss.py`, new). It decides at the release from what the host already holds.
- **When it resumes.** It returns `resume` only when all five terms hold:
  - **short:** release − onset < 1,000 ms. The onset is the one `Cores.release` already reads: the client's last
    displayed frame for a stall, the last controller packet for a silence.
  - **evidence:** a client heartbeat was received in [onset − 2.5 s, release], with a predecessor.
  - **post-FEC loss 0:** no heartbeat in the window shows a rise in `lost_packets` (WAN telemetry's `post_fec`) or in
    `fec_unrecoverable_groups`. A counter that fell is `counter_reset`, treated as loss.
  - **no dark span:** no heartbeat in the window shows `audio_max_arrival_gap_ms` ≥ 250. Audio rides the same
    downlink every 20 ms.
  - **the uplink alive:** the host's own controller-sequence loss counter (`_lost_packets`, the receive loop's count
    of missing sequence numbers) is unchanged from the onset's heartbeat-time sample to the release. A silence whose
    packets come back in sequence means the client stopped sending; the network did not drop them.
- **When it does not resume,** the release is today's load, and `why` names the first term that failed: `long` /
  `no_heartbeat` / `loss` / `counter_reset` / `dark_span` / `uplink_loss` / `uplink_unknown`.
- **The resume.** It writes one `input_release` row with `method` `resume`, `why` `no_loss_under_1s`, `held_ms` and
  the terms read: `heartbeats_in_window`, `window_lost_packets`, `window_unrecoverable_groups`,
  `window_audio_max_gap_ms`, `uplink_lost_packets`.
  - No command goes to the core: no `PAUSE_TOGGLE`, no `LOAD`.
  - The caller's own `_resume_game()` resumes the paused core as it does after a load today.
  - The pause still happened, so the release "pauses at most".
  - **The save is unchanged.** It is still taken and stays on disk, and B9's `last_save` is cleared: one release per
    save.
- **The load.** Today's path byte for byte, plus `why`, `held_ms` and the terms on its row.

**The limit, stated.** The decision cannot wait for the heartbeat that covers the stall itself, which arrives up to
2 s after the release. The rule is therefore "no loss *known* behind it at the release".
- Loss before or around the onset is seen.
- Loss confined to the stall's own 0.5 s shows only in the next heartbeat.
- In the first heartbeats of a session there is no predecessor, so the rule reads `no_heartbeat` → the load (today).

**The switch** (design §3). `PRIVYHUB_REWIND_NEEDS_LOSS`:

| value | the rule |
| --- | --- |
| absent | on iff `PRIVYHUB_LINK_RECOVERY=1` |
| `0` | off: today, byte for byte |
| `1` | on without the umbrella |
| other | as absent, noted in the config row |

- **Why no new line.** The queue places the rule inside the adopted line, and B26's convention is that a fix inside an
  adopted line needs no new adoption line.
- **Why `link_recovery.py` is untouched.** B20's umbrella means "exactly the six stack lines … and nothing more", and
  B20 / B21's `describe`, `config_row` and tests read six. So the rule keys on the umbrella directly and leaves that
  file alone.
- **It changes live behaviour at the next companion restart.** The umbrella is adopted, so this is the queue's ask.
  The one-line rollback is `PRIVYHUB_REWIND_NEEDS_LOSS=0` in the drop-in.

**The hooks, smallest.**
- `rewind_cores.py`:
  - `Cores.no_loss = None`;
  - one guarded branch in `release`;
  - in `wire`, a guarded import and wire (mode `state` only), with one `rewind_needs_loss_config` row.
- `games/link_drop_recovery.py`: `_rewind_needs_loss = None` and one guarded call at the top of `note_heartbeat`.
- `plugins/games.py` is not edited: the wire rides `rewind_cores.wire`, which the plugin already calls.

## 2. Tests (`tests_rewind_needs_loss.txt`, three runs; `tests_mutations.txt`; `tests_regression_after.txt`)

The harness is B9's loopback fake core with the real recovery, Rewinder, Cores, B7 `StallSignal` and B12
`StallOwner`, driven by B12's `Down` client in real time. The rule is wired as `rewind_cores.wire` wires it.

| case | result |
| --- | --- |
| a 450-ms stall, 0 loss | pause; the stall save taken; `input_release` `resume` `no_loss_under_1s` via `stall_end`, `held_ms` 400-1000; **no LOAD and no PAUSE_TOGGLE at the core**; `resumed` |
| the same with Δ`lost_packets` 3 | the load as today (`state`, slot 9, `why` `loss`) |
| Δ`fec_unrecoverable_groups` alone | the load (`loss`) |
| a dark span (audio gap 300 ms) | the load (`dark_span`) |
| uplink loss 2 | the load (`uplink_loss`) |
| no heartbeat in the window | the load (`no_heartbeat`) |
| a counter reset | the load (`counter_reset`) |
| a 2-s silence | the load (`long`) |
| a 0.93-s silence, 0 loss | `resume` |
| the switch | `mode()` for absent / umbrella / `0` / `1` / junk |
| the umbrella | wires the rule through `hold_rewind.wire` → `rewind_cores.wire`, with the config row; the recovery's `note_heartbeat` feeds it |
| `0`, absent, junk alone | wire nothing |
| a fresh process with no line | imports nothing |
| the hook shape | one guarded import |

**Mutations:**
- the loss term removed: 2 fail;
- the 1-s bound raised to 3 s: 2 fail.

**Every suite** (`tests_regression_after.txt` against `tests_regression_baseline.txt`) is the baseline's outcomes plus
`tests/rewind_needs_loss` 14 OK. B9 (`rewind_cores`), B12 (`stall_owner`), B16 (`stall_resume_speed`), B4 / B7 / B8 /
B18 and B20 / B21 (`link_recovery`) are unedited and green. The four `tools/` tests fail in a copy, as at every
baseline.

## 3. Proof: absent = today (`proof_flag_absent.md` / `.py`, `proof_flag_absent_output.txt`)

- **Row for row.** A scripted set (a 450-ms stall, a 2-s silence and a 0.93-s silence, with heartbeats through the
  real hook) was run in fresh processes against the base tree and the B33 tree. The rows were equal with times
  masked, and the core's loads were equal.
- **Three states:** no line; umbrella + `=0`; junk alone. **PROVEN.**

## 4. The replay (`replay_trip_releases.py`, `replay_output.json`, `replay_run_at.txt`; read-only over `trip_r2_2026-10-31/copies/`)

Every release of the trip went through `decide`, with the heartbeats the host had received by each release. The onset
is taken from the stall save's time less its `save_after_onset_ms`.

| release (UTC) | what happened | then | **B33** | held ms | window: hb / lost / audio gap | the next heartbeat (after the release) |
| --- | --- | --- | --- | --- | --- | --- |
| 04:19:18.518 | golf, the activity losing the foreground | load, 25 frames | **resume** | 511 | 1 / 0 / 63 | +339 ms: lost 0, unrec 0 |
| 04:30:10.847 | golf, the activity losing the foreground | load, 28 | **resume** | 564 | 1 / 0 / 26 | +84 ms: lost 0, unrec 0 |
| 04:37:43.889 | golf, the step-up's encoder restart | load, 25 | **resume** | 525 | 1 / 0 / 34 | +977 ms: lost 2, unrec 1, resyncs 2 (the SSRC change) |
| 05:07:17.104 | hockey, the step-up's encoder restart | load, 25 | **resume** | 519 | 2 / 0 / 64 | +1,395 ms: lost 2, unrec 1, resyncs 2 |
| 05:28:39.098 | the brawler, the onn leaving | load, 25 | **load** (`no_heartbeat`) | 680 | 0 | none: the link was gone |

- **The three golf rewinds would have resumed.** No ~0.45 s of play would have been undone.
- **The two step-up stalls also resume.** The 2 packets lost at the encoder's SSRC change show only in the heartbeat
  after the release: this is the rule's limit at work. B32's step in place removes that gap at its source.
- **The uplink term is not in any log.** The host's controller-sequence counter is only in `/status`. The replay holds
  it flat and lists the ctrl-gap rows that overlap each episode: one, at 04:30:10, of 292 ms, followed by 126 packets
  in 500 ms — about twice the normal rate. The packets came late, as a burst, which is consistent with no sequence
  loss (inference).

## 5. Settled, not built: showing that "the stream is live again"

For the user to choose later. The client knows its own two moments: a restart's first rendered frame, and its own
`stall_end`. A host-side hold release would reach it through the heartbeat's answer.

| option | what the user sees | cost / where | risk |
| --- | --- | --- | --- |
| **a. nothing** (today) | the picture moving again | none | after a resume with no load the game simply goes on, which may be enough now that nothing is undone |
| **b. a corner mark for 1 s** (recommended) | a small "● live" in a corner for 1 s after a restart's first frame, or after a resume from a pause ≥ 400 ms | client only: a TextView beside B14's link notice (the same pattern), a `debug.privyhub.live_mark` property, a `live_mark_shown` report count | small; clear about the "live" moment without covering play |
| c. a one-frame tint | the whole picture flashes faintly (~30 % for 1-2 frames) | client: a full-screen View with a short alpha animation | easily taken for a game effect; a flash on every resume |
| d. a short tone | a tick in the audio | client audio path; mixes into the game's sound | intrusive in music and dialogue |
| e. gate the input | presses count only after the first fresh frame is shown | already close: B16's fast ready; a resume with no load happens at `stall_end`, when frames are already shown | none further to build |

## 6. Files

- **`b33_2026-10-31/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` (`rewind_cores.py`, `link_drop_recovery.py`) with `predecessor_sha256.txt`, and
    `after_sha256.txt`;
  - the design, `design.sha256`, `design_hashed_at.txt`;
  - `b33.diff` (`git apply --check` OK against the tree);
  - `proof_flag_absent.md` / `.py` / `_output.txt`;
  - `tests_rewind_needs_loss.txt`, `tests_mutations.txt`, `tests_regression_baseline.txt`,
    `tests_regression_after.txt`;
  - `replay_trip_releases.py`, `replay_output.json`, `replay_run_at.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - in the diff, not yet in the tree: `companion/rewind_needs_loss.py` (new), `companion/rewind_cores.py`,
    `companion/games/link_drop_recovery.py`, `tests/rewind_needs_loss/` (new);
  - `patches/B33_NO_REWIND_WITHOUT_LOSS.md`.
- **Left in /tmp:** `b_q31l_b33` (the copy); `b_q31l_b33_scratch/` (`mut1/`, `mut2/`, outputs).
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft;
  - the trip keeper and `trip_2026-10-30/` untouched; `trip_r2_2026-10-31/` only read;
  - the real tree's code not edited;
  - nothing fetched, deleted, adopted or committed.
