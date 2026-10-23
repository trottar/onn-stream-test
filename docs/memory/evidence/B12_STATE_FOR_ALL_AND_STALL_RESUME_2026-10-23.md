---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c (+ B11 uncommitted, client only)
---

# B12 — `state` for every core, and the stall's resume inside the one owner

**Classification: BUILT.**
- **`PRIVYHUB_INPUT_HOLD_REWIND=1` now means `state` for every core.** B9's allow-list rewind is `rewind`; `all` and
  `state` are unchanged.
- **`PRIVYHUB_STALL_RESUME=1`** (with the stall signal) makes a stall-owned pause:
  - save at the stall;
  - resume once, with that load, when the client can see;
  - keep v2's encoder restarts off until v2's own 5 s, then hand over to v2 once.
- **Tests:** 10 new (the loopback fake core, a fake client), 3 runs green. B2 19 / B4 22 / B6 16 / B7 12 / B8 14 / B10
  10 unchanged and green. B9's 13 are green with three lines moved from `1` to `rewind` (disclosed).
- **Proof:** the B12 items removed = HEAD for four files; B9's module changes are listed.
- NOT ADOPTED; no live run; nothing committed.

Design `b12_2026-10-23/design_written_before_code.md`, sha256 `e1547a98…107133`, hashed **17:18:24Z, before any B12
code**.

## 1. `state` for every core (`rewind_cores.py` +15 −9, `hold_rewind.py` +5 −2)

| `PRIVYHUB_INPUT_HOLD_REWIND` | before | now |
| --- | --- | --- |
| absent | nothing imported | the same |
| `1` | rewind, snes9x / bsnes only | **`state`, every core; no rewind keys in any launch config** |
| `rewind` | ignored | B9's `1`: rewind for snes9x / bsnes, `rewind_skipped` elsewhere |
| `all`, `state` | B4; the savestate | the same |

- **Why:** BENCH-R3 A read PAUSED after all 7 of snes9x's hold-path rewinds (and 118 / 123 on PS1 in R2). D's `state`
  loaded and played on PS1 (net 24).
- **Tested on snes9x:** saved at 0.41 s; loaded into a running core at the release; net 20-30 frames.
- **The cost per save:**
  - **bytes:** snes9x 823,536 B, bsnes 284,304 B, Beetle PSX HW 16,777,240 B (B4's measured savestates);
  - **time:** D's rows: the acknowledgement came **4-11 ms** after the send on PS1. RetroArch writes the file in its
    own task, which the NCI does not time. The fake core's request → ack → row is ~10 ms (polling-bound); it is stated,
    not claimed for RetroArch;
  - **count:** one save per silence ≥ 400 ms (B9's table, 0.9-6.2 per 10 min on quiet cells), plus one per stall
    episode with `PRIVYHUB_STALL_RESUME`.

## 2. The stall's resume (`stall_owner.py` new, 172 lines; `stall_signal.py` +8, `link_drop_recovery.py` +6, `plugins/games.py` +11)

**What BENCH-R3 B shows, read in the code:**
- The stall paused at 420-484 ms.
- The client's own gate (output silence ≥ 1,000 ms) then sent `ready`. The plugin resumed the emulator and recovery's
  plain `note_stream_ready` logged `resumed`, with no load and no rewind.
- Meanwhile v2's `_maybe_restart_encoder` restarted the encoder (3 of 5; it runs for any paused recovery once the
  client has been present 2 s and two heartbeats show the output stale and rising). After the third restart came
  `recovery_escalation`, 7000→5000.
- Then a gate-bit stall paused again, and only that pause got `stall_end`.

**Built:**
- **The save at the stall** (`state` only): at the first stall datagram of an episode (the client sends from its own
  150 ms), while the core plays, B9's worker saves slot 9 with `kind = stall`, onset = receive − age.
  - The stall pause's pending (B7's onset) matches it within 100 ms.
  - Tested: **net 8-14 frames** (~150 ms after the client's last frame) instead of BENCH-R3 B's ~25.
- **One resume, with the load, through the owner, on the first of:**
  - `stall_end` (B7's own resume, unchanged);
  - **the client's gate `ready`.** The plugin's ready action calls B12 before its own status read (the core still
    paused, as B8 does). B12 loads, resumes (`resumed via client_ready_stall`) and sets B7's ready window, so the ready
    itself is `client_ready_after_stall`, not a session.
  - After either: gate-bit stalls over fresh output are ignored (`stall_gate_after_resume`), and the late `stall_end`
    is `stall_end_late`.
  - **Disclosed against the queue's "on `stall_end`":** in a `@down` drop ≥ 1 s the client always enters its own
    gate, and its `ready` comes before its `stall_end` (sent once gameplay is shown, after the release). So in practice
    the resume is at the ready.
- **v2 holds off:**
  - while a stall owns a pause younger than **5,000 ms** (E3-R1's v2 trigger), the monitor skips v2's encoder restart.
    So there is no restart and no ladder step;
  - **at 5,000 ms v2 owns it, once:** one `stall_handover_v2` row, then today's tick (restarts, the gate, the give-up);
  - GIVE_UP_MS applies throughout. B8's hold episodes are left to B8.

## 3. Tests (`tests_stall_owner.txt`, `tests_regression.txt`)

**`tests/stall_owner`: 10 OK, 3 runs:**
- `1` = state on snes9x / PSX / bsnes (no rewind keys); `rewind` = the allow-list; snes9x's save at 0.41 s and load
  (the cost line printed);
- **`@down`:**
  - stalls in real time from age 150: one stall save, the pause at age 400;
  - three monitor ticks with v2's restart conditions met (pause 2.5-4.5 s old, client present, two stale rising
    heartbeats): **0 restarts, no escalation**;
  - the ready: **one resume via `client_ready_stall` with the stall's state loaded** into a running core, net 8-14;
  - `client_ready_after_stall`; 6 gate stalls ignored (one row); `stall_end_late`;
  - **one `desync_pause`, one `resumed`**;
- `stall_end` first: B7's resume with the load;
- **the long stall:** at 3 s no restart; at 5.5 s one `stall_handover_v2` and one restart; the next tick neither;
- **absent = BENCH-R3 B:** one restart at 2.5 s, the gate's plain resume, a second pause;
- a hold episode is left to B8; the flag needs the stall signal; FlagAbsent; the hook shapes.

**The regression set:** every suite under `tests/` is green from the copy (`input_hold_rewind`'s 2 env skips as
before). The four `tools/` tests fail identically on an untouched HEAD copy (`tests_tools_at_head_copy.txt`).
- *Fixed during testing, disclosed:* the first plugin import guard began with `_stall_signal is not None`, which B7's
  hook-shape test counts. The condition was reordered, and B7's suite is unchanged.

**Proof** `proof_flag_absent_host.md`:
- link_drop_recovery (2 items), stall_signal (2), plugins/games (4): **identical** with them removed;
- hold_rewind (1 item + 2 tuples set back): identical;
- `rewind_cores.py`'s 24 changed lines are listed. It is B9's module, imported only with the flag.

## 4. For CL-B10 (A)

- **The `state` path on snes9x under the bench blackout:**
  - `PRIVYHUB_SNES_CORE=snes9x`, `PRIVYHUB_IMPAIRMENT=blackout-4s@both,every=120s,seed=1`;
  - `PRIVYHUB_INPUT_HOLD=1 PRIVYHUB_INPUT_HOLD_B6=1 PRIVYHUB_INPUT_HOLD_B8=1 PRIVYHUB_INPUT_HOLD_REWIND=1
    PRIVYHUB_STALL_SIGNAL=1 PRIVYHUB_STALL_RESUME=1`;
  - expect a `state_saved` (kind silence) ~0.40 s in, an `input_release` method `state` at the resume, net ≈ 24 by
    B9's row, and ≈ 0 only if a future save lands nearer the onset.
  - **The queue's "net ≈ 0 expected" is not what the state path gives:** it restores to the save, 0.40 s after the
    silence's onset.
- **The stall resume on `@down`:** the same flags with `blackout-4s@down,every=120s,seed=1`. Expect per blackout:
  - one `state_saved` (kind stall);
  - the pause at 400-460 ms;
  - **no `encoder_restart`, no `recovery_escalation`**;
  - one `resumed via client_ready_stall` with `input_release` method `state` (net ≈ 9-12);
  - `client_ready_after_stall`, `stall_end_late`, no second pause.

## 5. Files

- **`b12_2026-10-23/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b12.diff`, `proof_flag_absent_host.py` / `.md`;
  - `tests_stall_owner.txt`, `tests_regression.txt`, `tests_tools_at_head_copy.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `companion/stall_owner.py` (new), `rewind_cores.py`, `hold_rewind.py`, `stall_signal.py`,
    `games/link_drop_recovery.py`, `plugins/games.py`;
  - `tests/stall_owner/` (new), `tests/rewind_cores/test_rewind_cores.py` (3 lines);
  - `docs/memory/patches/B12_STATE_FOR_ALL_AND_STALL_RESUME.md`, `logs/b12_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
