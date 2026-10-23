# B12 — the savestate path for every core, and the stall's resume: design, written before any B12 code

Baseline HEAD 3eb900c (+ B11, client only). Queue: `handoffs/QUEUE_2026-10-23E.md` §B12. Data: BENCH-R3 §3 A (snes9x's
hold-path rewind PAUSED after, 7 / 7; 47.5-48.7 unattended per blackout), B (`@down`: the stall pause at 420-484 ms,
then **resumed by the client's gate `ready` through recovery's plain `note_stream_ready`, 5.5-7.7 s `recovering_ms`, an
encoder restart in 3 of 5 — v2's `_maybe_restart_encoder`, which runs for any `PAUSED_RECOVERING` once the client has
been present 2 s — and the ladder 7000→5000 after the third**; then an in-gate stall paused again and only that pause
got `stall_end` and a 2-3-frame rewind), D (PS1 `state`: saved 403-408 ms in, ack 4-11 ms after the send for a
16,777,240-byte state, loaded into a running core, playing, net 24).

## 1. `PRIVYHUB_INPUT_HOLD_REWIND`: `1` = `state` for every core; `rewind` = B9's allow-list

| value | before (B9) | B12 |
| --- | --- | --- |
| absent | nothing imported | the same |
| `1` | rewind, snes9x / bsnes only | **`state`, every core** (no rewind keys in any launch config) |
| `rewind` | (ignored) | B9's `1`: rewind for snes9x / bsnes, `rewind_skipped` elsewhere |
| `all` | B4, every core | the same |
| `state` | the scratch savestate | the same |

- In `hold_rewind.py`: `rewind` is accepted as on (an added remap statement), and B9's two `('1', 'state')` routing
  tuples gain `'rewind'` (two changed nodes, stated in the proof). In `rewind_cores.mode`: `1` → `state`,
  `rewind` → `allow`.
- **The cost per save:** snes9x 823,536 B (B4's measured savestate), bsnes 284,304 B, Beetle PSX HW 16,777,240 B. From
  D's rows the acknowledgement came 4-11 ms after the send (the write itself is RetroArch's own task, not timed by the
  NCI); the fake core's round trip is measured in the tests and stated, not claimed for RetroArch. One save per
  silence ≥ 400 ms (B9's cost table), plus one per stall episode (§2).
- B9's tests that meant `1` = the allow-list switch to `rewind` (disclosed); B2 / B4 / B6 / B7 / B8 suites unchanged.
- `rewind_cores.wire` tolerates a detector without `on_quiet` (B4's test passes an `object()`): no mark set there.

## 2. The stall's resume, inside the one owner (`PRIVYHUB_STALL_RESUME=1`, needs `PRIVYHUB_STALL_SIGNAL`)

New `companion/stall_owner.py`; hooks are guarded statements in `stall_signal.py`, `link_drop_recovery.py`,
`plugins/games.py`; small stated additions in `rewind_cores.py`.

- **The save at the stall** (`state` only): the client sends stalls from its own 150 ms; the host pauses at 400 (B9).
  At the **first stall datagram of an episode** while the core is PLAYING, B12 asks B9's worker for a
  `SAVE_STATE_SLOT 9` with `kind = stall` and `onset` = receive − age (the client's last displayed frame, B7's onset).
  The stall pause's own pending (B7's `set_pending`, onset = receive − age of the pausing datagram) matches a stall save
  within **100 ms** (two estimates of the same frame); a silence save still matches within 5 ms (B9). So the load
  restores the core to ~150 ms after the client's last frame (~9-12 frames) instead of none.
- **The resume:** a stall-owned pause (reason `client_stall`, not B8's hold episode) resumes, through the owner, with
  B4's `rewind()` (the state load, or nothing) **on the first of**:
  - `stall_end` — B7's own resume, unchanged;
  - **the client's gate `ready`** — today recovery's plain `note_stream_ready` resumes it *without* the load, and the
    client's next gate-bit stall pauses again (B's second pause). B12 takes it in the plugin's ready action before its
    own status read (the core still paused, as B8): load, `resume_game()`, PLAYING, `resumed via client_ready_stall`,
    B7's 20-s ready window set (so the ready itself is `client_ready_after_stall`, not a session). In a `@down` drop
    ≥ 1 s the client's own gate is always entered (output silence ≥ 1,000 ms), and its `ready` precedes its
    `stall_end` (sent when gameplay is shown, after the release); so in practice the resume is at the ready, one
    request after the client can see — disclosed against the queue's "on `stall_end`".
  - After that resume, gate-bit stalls over fresh output (age < the threshold) are ignored and the late `stall_end` is
    a logged no-op (`stall_end_late`), as B8 does for a hold.
- **v2 holds off:** while a stall owns the pause and it is younger than **v2's own threshold, 5,000 ms** (E3-R1's
  controller-silence trigger), the monitor skips v2's encoder restart (`_maybe_restart_encoder`) — so no restart and no
  `recovery_escalation` / ladder step for a picture-only drop the client will recover from. **At 5,000 ms v2 owns it,
  once:** one `stall_handover_v2` row (held ms), and from then on the tick runs as today (restarts, the gate, the
  give-up). GIVE_UP_MS still applies throughout.
- Absent: nothing imported; every hook a no-op; B7's behaviour as BENCH-R3 measured.

## 3. Tests (`tests/stall_owner`; the loopback fake core of B9's tests)

- `REWIND=1` → `state` on snes9x and PSX (no rewind keys); `rewind` → B9's allow-list; the save at 0.40 s and the load
  for a snes9x silence (frames restored, net ≈ 24); the fake core's save / load round trips stated.
- **`@down`** (a fake client's stalls from age 150, every 50 ms): one save at the first stall, the pause at age ≥ 400,
  the monitor ticking 6 s with the client present → **no encoder restart, no escalation**; the gate's `ready` → one
  resume via `client_ready_stall` with the stall's state loaded (PAUSE_TOGGLE + LOAD_STATE_SLOT 9, the core running),
  the ready window → `client_ready_after_stall`; gate stalls ignored; `stall_end` → `stall_end_late`; **one pause, one
  resume**. The `stall_end`-first variant: B7's resume with the load.
- **The long stall:** the pause aged past 5,000 ms → one `stall_handover_v2`, then v2's restart allowed; never twice.
- Absent: B7's sequence (the restart happens after 2 s present — today); the flag needs the stall signal.
- B2 / B4 / B6 / B7 / B8 / B9 suites green (B9's `1` lines → `rewind`); the AST proofs.
