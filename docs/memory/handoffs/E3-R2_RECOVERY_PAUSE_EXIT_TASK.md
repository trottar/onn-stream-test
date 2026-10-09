---
memory_schema: 1
as_of: 2026-10-08
status: TASK HANDOFF — E3-R2, queue B item 1 (the user's go, 2026-10-08, "Both"): fix the false pause E3-R1 located. Three parts, one flag: a silence-gap log (so the replay is faithful), E3-R1's 5-s / two-check controller-silence threshold, and an exit for a controller-silence pause when the packets return. Offline replay bar, then PS1-STREAM ×2 and CONC ×2. The real-drop check on the air is the user's nft paste afterwards; adoption waits for it. Nothing adopted; nothing committed
---

# E3-R2 — the false pause, fixed: threshold, exit, and a faithful replay

**What E3-R1 established** (`evidence/E3_R1_RECOVERY_FALSE_PAUSE_2026-10-08.md`).
The harmful pause is the host's `controller_silence` trigger: a 1-s
threshold, first check, on a client→host stall of ~1-3 s (the onn's
uplink dips, the controller packets arrive late in a burst) while the
picture never stops. Idle, the client sends ~460 controller packets/s
(max age 295 ms in 10 min). A `controller_silence` pause **has no exit**
while the client keeps playing — the client never runs its re-entry
gate — so it sits 120 s, gives up and saves. The replay of today's rule
missed two events: a replay-model defect (a neighbouring pause's state
not carried) and a resolution limit (1-s packet counts cannot see a
~1-s silence whose catch-up burst lands in the same second). R1's v2
(5,000 ms, two checks ≥ 250 ms apart) is in the tree, dormant.

**The one change, in three parts, all behind `PRIVYHUB_RECOVERY_TRIGGER=v2`**
(absent = today, byte for byte):

1. **The gap log** — a measurement hook, on with the flag and also
   available alone as `PRIVYHUB_RECOVERY_GAP_LOG=1`: the controller
   receive loop logs every silence > 250 ms once, at its end: start,
   length, and the packets of the catch-up burst in the next 500 ms.
   One line per gap; a bounded file beside the recovery log. This is
   what a faithful replay needs (R1 §3).
2. **The threshold** — R1's v2 as written: 5,000 ms, confirmed on two
   checks ≥ 250 ms apart with no packet between.
3. **The exit** — a pause whose trigger was `controller_silence`
   **resumes by itself** when (a) controller packets are flowing again
   (age < 500 ms on two checks ≥ 250 ms apart) **and** (b) the next
   client heartbeat shows a fresh output age (≤ the idle max, 300 ms,
   or whatever R1's `idle_stats.json` says). The resume uses the
   existing resume primitive (the unpause the client-side gate uses;
   R3c2's "never into a live core" is untouched — nothing is loaded).
   The 120-s give-up still applies if (a)/(b) never come. A pause
   triggered by `client_output_silence` keeps its existing exit.

Read first: the R1 record and `e3_r1_2026-10-08/` (`probe.md`,
`timelines.md`, `replay.md`, `e3_r1_replay.py`, `e3_r1_trigger_v2.diff`,
`idle_stats.json`); the recovery code in `companion/plugins/games.py`
and `native_session_io.py`; `D_BASE_R3_…`, `R3C2`, the R3c decision;
`d_base_r3b_2026-09-21/r3b_run.sh` (the user's harness);
`e3_a2_2026-10-07/e3_a2_validity.py`.

## 1. Before any run: the replay, made faithful (the first half of the bar)

- **Fix R1's replay model** (carry a neighbouring pause's state) and
  re-run today's rule over R1's timelines: it must now reproduce
  S1-CONC r1b. S1-CONC r2a stays unreproducible from 1-s records; say
  so; it is excluded from r1 by name, before the hash.
- **A 10-min gap-log probe** with a PS1 stream PLAYING and the gap log
  on (flag absent otherwise): the distribution of gaps > 250 ms
  (count, max), the catch-up burst sizes. This is the first data at the
  resolution the replay needs. If a gap > 1,000 ms occurs in the probe,
  today's rule would have paused — note it beside R1's five.
- **Pre-registration, hashed before the replay is scored:**
  - r1: today's rule reproduces every recorded event except the one
    named above (±2 s); no fire on N05 / F05;
  - r2: v2 fires on every real drop within +2 s of today's rule (R3b
    N3, N15, N15b, N150, E30; R3 F3, F15, F150);
  - r3: v2 fires on none of the four **controller** false pauses
    (E2-1080P r1, S1-CONC r1b, S1-CONC r2a by its recorded time, A2 r1);
    the three `client_output_silence` pauses are the client's and are
    reported, not gated (R1 §1);
  - r4: in the replay, the exit rule (part 3) would have resumed each
    of the four controller pauses within **10 s** of the packets'
    return, using the recorded heartbeat ages.
- Unit tests for the confirm and the exit logic (synthetic timelines),
  not data.

## 2. The runs (the second half of the bar)

- E1-PS1-STREAM ×2 and E1-CONC ×2 with the flag (E2's windows and gaps;
  drop-in for those runs only; environ checked against the adopted
  three lines + the flag; the gap log on in those runs).
- **Bar, ACCEPTED only if all hold:** (i) §1's r1-r4 held; (ii) **no
  `gave_up_saved` in any window**, and no `desync_pause` from
  `controller_silence` at all (with v2's threshold none is expected; one
  that fires and then exits by part 3 within 10 s is reported, and
  counts against (ii) only if it fails to exit); (iii) each row within
  E1's bands of its reference (host CPU ± 2; rendered ± 0.5 of E2's
  PS1-STREAM / of E3-S6A's CONC) — loss, underruns, resyncs reported;
  (iv) the companion's stream cost ± 2 points of a core; (v) the gap
  log's cost: ≤ 0.5 point of a core, no gap caused by its own write.
- E3-A2's validity rule applies as always; with the flag, a run whose
  pause does not exit is a failure of (ii), not an invalid attempt.

## 3. The hand step for the user (written into the record)

The real-drop check on the air: R1's four `r3b_run.sh` runs (V2-N3,
V2-N15 host→client; V2-C2, V2-C8 client→host), as one paste from the
repo root with the flag in `e3_flag.conf`, removed after, `e3_state.py`
ok at the end. **What the reply must contain**, per run, from
`recovery_lines.jsonl`: N3 / N15 — `desync_pause client_output_silence`
at ~+1.3 s then `resumed` (unchanged real-drop path); **C2 — no
`desync_pause`**; **C8 — `desync_pause controller_silence` at ~+5.25 s,
then `resumed` within ~10 s of the clear, no `gave_up_saved`** (the exit
working). Say in the record that adoption waits for this, and that
`c3_l4_nft_night.py`'s preflight refuses an unadopted flag so the
harness is `r3b_run.sh`.

## 4. The record

`evidence/E3_R2_RECOVERY_PAUSE_EXIT_<date>.md` + `e3_r2_<date>/` (the
gap-log probe, the fixed replay and its output, the pre-registration +
`.sha256`, the diff, unit tests, 4 runs, `manifest.sha256`, `--check`,
`validity.json`, the gap logs, table, verdict, `redact_check.txt`);
`patches/`; `docs/KNOWN_ISSUES.md` (the false pause: fix behind a flag,
pending the air check); `TOOLS.md` (the flag, the gap log);
`investigations/ACTIVE.md`; `logs/e3_r2_git_status.txt`. Flag absent;
the adopted state restored; then queue item 2.
