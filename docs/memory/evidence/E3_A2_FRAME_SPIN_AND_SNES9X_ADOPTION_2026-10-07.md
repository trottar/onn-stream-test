---
memory_schema: 1
as_of: 2026-10-08
baseline_commit: e553673
---

# E3-A2 — adopting `frame_spin` and the Snes9x core

**Classification, per item, by the pre-registered bar (`e3_a2_verdict.json`):**

- **Snes9x (`PRIVYHUB_SNES_CORE=snes9x`): ADOPTION STANDS.** Every
  clause holds in the SNES-STREAM run: RetroArch 8.9 % of a core, host
  8.05 %, 60.0 fps, and the title names Snes9x.
- **`frame_spin` (`PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`): ADOPTION
  REVERTED.** Valid PS1-STREAM run 2 had **24 audio underruns against
  the limit of 20** (clause f2). Every other clause held in every valid
  run: sender 5.7-5.9 %, companion 17.3-17.5 %, in E1's bands, D-BASE
  spikes and stale drops. The replacement run met all four clauses (14
  underruns). `audio-pacing.conf` was removed at 01:05Z and its name
  taken out of the state checks.
- **The guide index with the others present:**
  - m1 (PSS 33.9 MB) and m2 (256 / 0 grabs) hold;
  - **m3 fails on the high side**: 343 programmes against the pre-run
    285 ± 5 %. The guide served all six channels; the pre-run read was
    taken just after a background refresh.
  - As pre-registered, this is the index's and reverts neither new item.
    The index stays adopted; that is the user's call.
- **One run was invalid and was replaced**, under an addendum hashed
  before any further data (§3). The companion's link recovery paused the
  game for 17 of run 1's 20 minutes.
- **Adopted now:** live, the guide index, **the Snes9x core**. Nothing
  else adopted; nothing committed.

**Context:**

- Task: `handoffs/E3-A2_FRAME_SPIN_AND_SNES9X_ADOPTION_TASK.md`, under
  `QUEUE_2026-10-07.md`'s rules.
- **The user's words, 2026-10-07:**
  - "Adopt frame_spin if you think helps";
  - after the look by hand at Super Mario World on Snes9x: **"Sure it
    ran smoothly from what I can tell"**. That look decides the core;
    nothing perceptual was measured.
- **Baseline commit: `e553673`** (the user's queue-C commit).
- Files: `e3_a2_2026-10-07/`.
- Timeline (UTC):

  | date | time | what |
  | --- | --- | --- |
  | 10-07 | 22:51:47 | preconditions held; **the look drop-in `e3_flag.conf` was already absent** (the user removed it; the drop-in dir last changed 22:45:54Z) |
  | 10-07 | **22:52:28** | `audio-pacing.conf` and `snes-core.conf` written, `daemon-reload`, restart: four lines |
  | 10-07 | 22:53:02 | the state checks extended; `e3_state.py` ok |
  | 10-07 | 22:53:18 | the companion's own background refresh re-downloaded the TTL-expired guide metadata and rebuilt the index (6 refreshes, 0 failed) |
  | 10-07 | **22:54:47** | **pre-registration hashed** (`854a4fc2…c145`) |
  | 10-07 | 22:54:47-00:39:12 | PS1-STREAM ×2, SNES-STREAM, META; all OK by the suite |
  | 10-07 | 23:00:07 | run 1: `desync_pause` (`controller_silence`), then 23:02:07 `gave_up_saved`; paused to the end |
  | 10-07 | **23:21:42** | **validity addendum hashed** (`2a274290…49d5`), before run 2's window |
  | 10-08 | 00:39:46-01:04:15 | the replacement PS1-STREAM run (`runs_retry1/`), OK and valid |
  | 10-08 | **01:05** | **`frame_spin` reverted**; the final state is three lines |

## 1. The adoption, as made

- **Two drop-ins** in `~/.config/systemd/user/privyhub-companion.service.d/`
  (copies in the dir):
  - `audio-pacing.conf` with `Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`
    (**removed at the revert**);
  - `snes-core.conf` with `Environment=PRIVYHUB_SNES_CORE=snes9x`.
  - `adaptive.conf`, `epg-index.conf`, the unit file and `emulators.json`
    are untouched; `emulators.json` still names bsnes, and the flag
    overrides it.
- **The environ after:** exactly four `PRIVYHUB_*` (`environ_after.txt`);
  the manager none; `systemctl --user cat` listed four drop-ins.
- **The state checks** (`patches/E3-A2_ADOPTED_STATE_CHECKS.md`):
  - `tools/e1_suite.py`: `ADOPTED` gained both names. The preflight
    checks both drop-ins. **The SNES row's counter override moved to
    `config/Snes9x/`**, because the adopted core reads its own per-core
    dir.
  - `tools/d7_regression.py` and `tools/c3_l4_nft_night.py`: the
    one-name extension E3-S6A described, as `ADOPTED_E3`; the nft tests
    went to 33/33.
  - At the revert, `frame_spin`'s name came out of all three. Final
    diff: `e3_a2_state_checks_final.diff`. The hashed adoption-time diff
    is `e3_a2_state_checks.diff`.

## 2. The runs and the bar

From `e3_a2_table.md` (`tools/e3_table.py`), `e3_a2_verdict.json`,
`loss_per_minute.txt`, `validity.json` and `retry1_clauses.json`
(`e3_a2_analysis.py`, `e3_a2_validity.py`):

| | PS1 r1 (**invalid**) | PS1 r2 | PS1 r1 replacement | SNES | META | E3-S5C F2 | E3-S4 r1 | E2 PS1-STREAM / SNES r1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| valid (no recovery pause in the window) | **no** | yes | yes | yes | — | yes | yes | yes / yes |
| audio sender, % of a core | 5.6 | 5.9 | 5.7 | 5.9 | — | 6.1 | 13.4 | 12.8 / 12.9 |
| companion, % of a core | 17.3 | 17.3 | 17.5 | 17.4 | 0.22 | 17.6 | 24.8 | 24.3 / 24.9 |
| host CPU % | 7.7 | 10.4 | 10.6 | **8.05** | 10.5 | 10.8 | 7.4 | 11.7 / 43.4 |
| RetroArch, % of a core | 4.3 | 33.8 | 33.6 | **8.9** | — | 33.7 | 8.2 | 33.6 / 436 |
| RetroArch / rendered fps | 60.0 / 59.82 | 60.0 / 59.76 | 60.0 / 59.94 | 60.0 / 59.78 | — | 60.0 / 59.94 | 60.0 / 59.99 | 60.0 / 59.81; 60.0 / 59.66 |
| **audio underruns** | 11 | **24** | 14 | 46 (not gated) | — | 9 | 7 | 11 / 7 |
| video loss/min; per-minute median; minutes > 100 | 40.5; 20.4; 1 | 58.4; 50.0; 3 | 10.8; 9.5; 0 | 35.6; 28.9; 1 | — | 9.4; 6; 0 | 1.9; —; — | 32.3 / 49.1 |
| spikes ≥ 20 ms/min; stale/min | 41.4; 1.75 | 72.7; 2.54 | 41.5; 0.93 | 78.0; 1.94 | — | 30.9; 0.74 | 37.9; — | 59.8 / 39.1 |
| max output gap ms (report; C2) | 291; 66 | 314; 131 | 132; 75 | 362; 154 | — | 117; 69 | 111; 64 | 378; 280 / 182; 74 |
| socket W | 15.7 | 18.6 | 19.9 | 14.2 | 15.4 | 19.8 | 15.0 | 20.4 / 21.7 |
| Tctl mean °C | 49.3 | 58.3 | 57.8 | 49.0 | 57.7 | 56.7 | 47.8 | 59.8 / 58.6 |
| companion PSS end MB | 43.6 | 41.7 | — | 43.4 | **33.9** | 42.1 | 42.3 | 40.2 / 41.4 |

**`frame_spin`** — judged on the valid PS1 runs (r2 and the replacement)
and on SNES for f1:

| clause | needed | r2 | replacement | SNES | holds |
| --- | --- | --- | --- | --- | --- |
| f1. sender ≤ 8 %, companion ≤ 20 % | every run | 5.9; 17.3 | 5.7; 17.5 | 5.9; 17.4 | yes |
| **f2. underruns ≤ 20** | both PS1 | **24** | 14 | — | **no (r2)** |
| f3. rendered ≥ 59.5; host 11.69 ± 2; rendered 59.81 ± 0.5 | both PS1 | 59.76; 10.40 | 59.94; 10.59 | — | yes |
| f4. spikes < 200/min; stale < 20/min | both PS1 | 72.7; 2.54 | 41.5; 0.93 | — | yes |

**`frame_spin`: ADOPTION REVERTED** (f2, r2). The invalid run 1 is not
judged; it would have failed f3 (host 7.7) because the game was paused.

**Snes9x** — the SNES-STREAM run:

| clause | needed | got | holds |
| --- | --- | --- | --- |
| s1. RetroArch CPU | ≤ 150 % | 8.9 | yes |
| s2. host CPU | ≤ 20 % | 8.05 | yes |
| s3. RetroArch ≥ 59.9; capture 60 ± 0.5; rendered ≥ 59.5 | | 59.998; 60.02; 59.78 | yes |
| s4. the title names Snes9x | | "RetroArch Snes9x 1.63 fae2fea" | yes |

**Snes9x: ADOPTION STANDS.**

**The index with the others present** — META: m1 PSS 33.9 MB ≤ 60
(growth 3.6 %), yes; m2 256 ok / 0 failed, yes; **m3 343 programmes vs
271-299, no** (6 channels serve). Recorded as the index's; it reverts
neither item.

**Read beside the bar:**

- **Tonight's link was noisy.**
  - Per-minute loss medians were 20-50 in the first runs, against
    E3-S5C's 2-6 with the same flag.
  - Spikes were 72-78 per minute, against ~30.
  - The calmer replacement run (median 9.5) had 14 underruns.
  - The bar has no same-night control, so this cannot be separated
    from the flag. E3-S5C's interleaved controls could.
- **The underrun record for `frame_spin`** across its valid flagged
  sessions:
  - E3-S5C: 13 / 9 / 5;
  - tonight's valid PS1 runs: 24 / 14;
  - SNES: 46 (not gated; E3-S4's unflagged SNES runs had 7 / 11).
  - The SNES figure is the largest of any session and points the same
    way as r2.
- **What Snes9x does on the host:** host CPU 8.05 % (bsnes 43-50),
  socket 14.2 W (~21.5), Tctl 49 °C (~59). Its stream rows are the
  same as tonight's PS1 rows: the link's.

## 3. The invalid run and the addendum

- **What happened** (`native_stream_recovery.log`):
  - PS1-STREAM run 1 reached PLAYING at 22:57:23Z.
  - At 23:00:07Z the companion's link-drop recovery paused the game
    (`desync_pause`, trigger `controller_silence`).
  - At 23:02:07Z it gave up and saved (`gave_up_saved`; the
    `Tekken 3 (USA).state` and `.recovery` files were written then).
  - It stayed `PAUSED_SAVED` to the end of the window.
  - RetroArch's own log: content ran 2 min 44 s. RetroArch was at
    4.3 % of a core, so the host CPU of 7.7 % was a paused game, not a
    lighter load.
  - The suite marks a run OK without reading the recovery state.
- **The addendum** (`e3_a2_preregistration_addendum.txt`, hashed
  23:21:42Z, before run 2's window and before any later data was read):
  - it extends the existing "never reaches PLAYING" rule to the window;
  - a stream run whose recovery state leaves PLAYING inside its window
    is an invalid attempt;
  - it is replaced within the two-retry limit and reported, not judged;
  - **the bar itself is unchanged.**
  - `e3_a2_validity.py` applies it from the recovery logs only.
- **The replacement** (`runs_retry1/`) was valid and met f1-f4. It
  could not change the verdict, because r2 had already failed f2. It
  ran because the addendum says invalid attempts are replaced.
- **The same check on every earlier E1/E2/E3 stream run**
  (`prior_runs_validity.txt`):
  - every run behind E3-S5B, S5C, S6, S6A and S4 is clean;
  - **E2's PS1-1080P run 1 and E3-S1's control and both CONC runs had
    pauses** inside their windows;
  - not re-judged here; an open item.

## 4. The kill switches and the state at the end

- **Snes9x off:** delete `snes-core.conf`, `daemon-reload`, restart. The
  SNES core is bsnes again, byte for byte.
  - Then take `PRIVYHUB_SNES_CORE=snes9x` out of `ADOPTED` /
    `ADOPTED_E3`, and move `SMW`'s override in `tools/e1_suite.py` back
    to `config/bsnes/`.
  - The `.so` and RetroArch's `Snes9x/` files stay.
  - **Saves and states are per core:** `saves/Snes9x/`,
    `states/Snes9x/` vs `saves/bsnes/`.
- **`frame_spin`:** off since 01:05Z. The code stays dormant, as for
  every unadopted E3 flag.
- **Final state** (`final_state.json`, 01:05:05Z):
  - manager none;
  - environ **exactly three lines**: live, the index, Snes9x
    (`environ_final.txt`);
  - three drop-ins: `adaptive.conf`, `epg-index.conf`, `snes-core.conf`;
  - no e3 drop-in; no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The index file was rebuilt by the companion at 22:53:18Z, keyed to
  the re-downloaded metadata.
- No `nft`, no real `sudo`, the Opal untouched.
- Nothing fetched by this task. The only file deleted is
  `audio-pacing.conf`, which this task created; the pre-registered
  revert removes it.
- Files (`e3_a2_2026-10-07/`):
  - `precondition.json`, `precondition_dropins.json`,
    `environ_before.txt`, `environ_after.txt`, `environ_final.txt`;
  - `audio-pacing.conf`, `snes-core.conf`, `adopted_at_utc.txt`,
    `frame_spin_reverted_at_utc.txt`, `emulators_json_before.sha256`;
  - `e3_a2_state_checks.diff` (hashed), `e3_a2_state_checks_final.diff`;
  - `epg_status_before.json`, `guide_read_before.json`,
    `guide_read_after.json`;
  - the pre-registration, the addendum and their `.sha256`;
  - `runs/` (4 runs; `manifest.sha256`, `--check` OK), `runs_retry1/`
    (1 run; the same), the consoles;
  - `e3_a2_analysis.py`, `e3_a2_validity.py`, `validity.json`,
    `prior_runs_validity.txt`, `retry1_clauses.json`;
  - `e3_a2_table.md/.json`, `e3_a2_verdict.json`,
    `loss_per_minute.txt`, `final_state.json`, `redact_check.txt`.
- Git status: `logs/e3_a2_git_status.txt`.
