---
memory_schema: 1
as_of: 2026-09-22
status: D-BASE-R3c — Part 1 probe CHARACTERIZED (a mid-FMV recovery state loaded into a PAUSED core loops, fresh core or not; loaded into a RUNNING core it plays; a gameplay state loaded paused plays); the fix INDETERMINATE and NOT APPLIED — Part 2 not run, stopped by the task's own rule; no source changed
---

# D-BASE-R3c — does a recovery state play in a fresh core?

Task: `handoffs/D-BASE-R3C_TASK.md`, run first in
`handoffs/OVERNIGHT_2026-09-23_QUEUE.md` (authorized by the user
2026-09-22, unattended). Evidence: `d_base_r3c_2026-09-22/`, SHA-256 of
every file in `d_base_r3c_2026-09-22/r3c_sha256.txt`. The host is
headless (H2); the onn was not needed for Part 1.

## Classification

- **Part 1 (probe): CHARACTERIZED.** Eight arms, 30 s `framemd5` each.
- **The fix: INDETERMINATE — not applied. Part 2 NOT RUN.** The task's
  rule: if the fresh-core load *also loops*, stop before Part 2 and put the
  change to the user. It does, through today's load path, so it stopped.
- **The user decision (2026-09-22) is recorded unchanged** in
  `decisions/D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE.md`: recovery never
  loads into a live core; Resume when a session is live; prompt only when
  none is. The probe shows that decision is **necessary but not
  sufficient**: a fresh core fixes defect 1 (the load routed into a stale
  session) but not defect 2 (the loop).

## Raw numbers first

The N150 recovery save was copied before anything touched it:
`recovery_copy/Tekken 3 (USA).state.recovery` (1,231,354 B,
`05bd85c7…abbd8040`), its `.png` (`95711998…81e49b5`) and the index
`privyhub_recovery_save.json` — `recovery_copy_sha256.txt`. The slot-0
scratch file (`Tekken 3 (USA).state`, which `load_recovery_state` stages
into) was also copied, `pre_state/`. **The save's own thumbnail shows
Tekken 3's intro FMV** (helicopters, searchlights, fires): the N150
give-up landed mid-cutscene, not in a fight.

Harness `r3c_probe.py`, log `r3c_probe_run.log`, one JSON per arm
(`probe_<arm>.json`), the full `framemd5` per arm, window snapshots
before/after each grab (`snap_*.png`, second pass), RetroArch's own
`[State]` lines per session (`retroarch_state_lines.txt`). Every arm:
companion idle → `POST /plugins/games/launch` (the normal launch path,
which returns with the core **paused**) → the arm's action → 2 s → 30 s
`x11grab -framerate 60 -window_id … -f framemd5` (A3-live) →
`POST /plugins/games/stop`. Unpause is `PAUSE_TOGGLE`, the command
`manager.resume()` sends; there is no HTTP resume without a stream.

| arm | what | load while | distinct / 1,800 | distinct per s (s 1-29) | top two hash counts | picture |
| --- | --- | --- | ---: | --- | --- | --- |
| C, C2 | control, no load | — | 460, 458 | BIOS then FMV, 20-21/s | 575, 108 | BIOS cube → intro FMV |
| **P, P2** | `recovery-resume` 3 s after launch, then unpause | **PAUSED** | **22, 22** | **2** every second | **926+816**, 933+817 | "Loaded state from slot: 0" on the save's frame; **the same frame 32 s later** |
| **Q** | run 20 s, pause, `recovery-resume`, unpause | **PAUSED** | **22** | **2** every second | 939+823 | (same) |
| R, R2 | run 20 s, `LOAD_STATE_SLOT 0` over the wire | **PLAYING** | 615, 614 | 20-21/s (FMV rate) | 4, 4 | FMV **advances** to a later scene |
| G | run to the attract fight (140 s), `SAVE_STATE_SLOT 0`, 15 s, pause, `LOAD_STATE_SLOT 0`, unpause | **PAUSED** | **1,640** | **60**/s (a held card at 20-22 s) | 82, 80 | fight moving |

PTS delta 1 on every interval of every arm. RetroArch logged
`Loading state "…Tekken 3 (USA).state", 16777240 bytes` in every load
arm, so every load took. All eight stops were clean (`active: false`),
and the recovery file's hash was unchanged after every arm.

**Reading.**

1. **A fresh core does not fix the loop.** P (3 s after boot) and Q (20 s
   after boot) loop exactly like the R3b post-run session did: two
   frames alternating, `GET_STATUS PLAYING`. "How long the core had run"
   and "a stale session" are both ruled out.
2. **Paused-at-load is the factor, for this state.** The same bytes loaded
   into a **running** core (R) play the FMV on.
3. **It is specific to a state captured mid-FMV.** A gameplay state saved
   and loaded through the same paused precondition (G) plays at 60 fps.
   The ordinary Save/Load path — which also loads paused — is therefore
   not shown broken for gameplay.
4. What the loop is, mechanically, is **not proven**: two alternating
   frames under `PLAYING` fits PS1 FMV double-buffering with the CD/MDEC
   stream not resuming after a load into a paused core. GL hardware
   rendering is **not** implicated by these arms (G ran the same renderer).

The task's gameplay band (IDR spread 53-74 KB) was not measured: the
relay was not running (the task allows that), and distinct-frame counts
decided every arm without it.

## What the fix would have to change — the user's decision

Today's `load_recovery_state` **requires a paused core** (it raises
"Load State requires the game to be paused") and the companion's launch
leaves the core paused, so a fresh-launch-then-load **loops for any
recovery save taken mid-FMV**. Options, none applied:

- **A. Load recovery saves into a running core** — launch fresh, unpause,
  `LOAD_STATE_SLOT 0`, then pause for the stream handoff. Arm R says this
  plays. It relaxes the paused precondition for the recovery path only —
  **a change to the Save/Load path `AGENTS.md` calls stable**, so it is
  the user's call. Needs its own check that a *gameplay* recovery save
  loaded running also plays (not measured).
- **B. Keep loading paused and accept the FMV case** — gameplay recovery
  saves play (G); a give-up during a cutscene would come back looping.
  The attract-mode test sessions always give up mid-FMV, so every test
  would hit it.
- **C. Don't save during FMV** — skip or defer the recovery save while
  the title is in a cutscene. No reliable FMV signal is known here.

The task named "a software-rendered state or a core option" as candidates;
the arms point away from the renderer and toward the paused-load
precondition, so neither is proposed.

## State of the host at the end

- The recovery save was **removed from the states directory** through
  the companion's own `recovery-discard` (index gone,
  `save_available: false`), per the queue's rule that R3c leaves none
  there. **The bytes are kept**: `recovery_copy/` holds the file, its
  `.png` and the index, hash-verified before the discard. To put it back:
  copy the three files to `data/games/retroarch/states/Beetle PSX HW/`
  and `data/games/retroarch/privyhub_recovery_save.json`.
- The slot-0 scratch `Tekken 3 (USA).state` was overwritten by arm G's
  gameplay save and **restored to the recovery bytes** afterwards (hash
  equal), i.e. the pre-probe state (`pre_state/`).
- The launcher's recovery prompt no longer appears (nothing to offer), so
  scripted session opens no longer need `h2_session.sh`'s BACK step.
- `save_state_probe.txt` is **reset at every launch**, so the harness's
  per-arm slice of it came back empty; the RetroArch session logs carry
  the load evidence instead (`retroarch_state_lines.txt`).
- No source, no build, no install. Companion idle.

**`recovery_copy/` and `pre_state/` hold game savestates** (binary,
~1.2 MB each). Nothing was committed; whether savestates belong in git is
the user's call at the next checkpoint.

## Privacy

No addresses, endpoints or identifiers. The RetroArch command port is
replaced by `<n>` in `retroarch_state_lines.txt`.
