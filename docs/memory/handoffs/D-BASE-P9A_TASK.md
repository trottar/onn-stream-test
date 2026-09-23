---
memory_schema: 1
as_of: 2026-09-23
status: TASK HANDOFF — D-BASE-P9a, decide the 12/17 audio cushion on an interleaved A/B/A/B design so that the underrun total and the audio-loss trend are read against noise instead of one pair; no code change (the P9 setting is in place); authorized by the user 2026-09-23
---

# D-BASE-P9a — the cushion against noise, interleaved

**Why.** `P9` FALSIFIED 12/17 on one clause of a rule Cowork wrote too
tightly: "underruns rise" with **20 → 25** on totals that read 4 (`P7`),
9 (`P8`-A), 20 (`P9`-A2), 16 (`P9`-B′) for the *same* 3/8 and near-3/8
configurations — that spread is the noise, and B's excess was **one
8-underrun playback stall at 76 s**. Meanwhile the cushion did what it was
bought for: starvation episodes **-98 %**, concealed glitches
**5,501 → 1,118**, at **+36.0 ms** measured. Separately, audio
`lost_packets` climbed 282 → 990 → 1,380 **in arm order across the hour**,
and the cushion cannot cause loss (counted before queueing), so arm order
and elapsed time are confounded. This task un-confounds both with an
interleaved design and a pre-registered rule that compares against the
noise it measures.

Read first: `evidence/D_BASE_P9_AUDIO_CUSHION_2026-09-23.md` (all of it,
especially "what the two numbers do", and the state at the end: profile
default 3/8, the setting via `PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS` /
`PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS` in the user manager's environment,
restart with `systemctl --user restart privyhub-companion`),
`decisions/D-BASE-P9_AUDIO_CUSHION.md`, `d_base_p9_2026-09-23/p9_run.sh`
and `p9_all.sh` (reuse), `TOOLS.md`.

**No code change.** The `P9` setting and APK stay as installed. Nothing
in the environment at the end.

## Four 20-minute attract-mode sessions of the PS1 reference title, zero input, per TOOLS.md, BACK to end, game stopped between, interleaved

| # | arm | cushion | how |
| --- | --- | --- | --- |
| 1 | A3 | 3 / 8 | environment 3 / 8 |
| 2 | B2 | 12 / 17 | environment 12 / 17 |
| 3 | A4 | 3 / 8 | environment 3 / 8 |
| 4 | B3 | 12 / 17 | environment 12 / 17 |

Companion restarted through systemd per arm with the arm's variables set
(`set-environment` → restart → `unset-environment` at the end), 8765 owned
by the unit's MainPID, `armcheck` recording `audio_cushion` and
`any_override: false` each time, sampler off, heartbeat default, 0 foreign
adb processes during holds (the `P8` monitor).

## Analysis, raw numbers first

Per session, the `P9` table's fields: `underruns` (total), the underrun
rows of `audio.tick_series` (first 200 s) and — since the series stops
there — the **heartbeat log's `audio_underruns` deltas per 2 s tick for
the whole session** (if the heartbeat carries them; `R5`'s ten audio
fields — check the key whitelist in `plugins/games.py`), so every underrun
is placed in time and grouped into events (consecutive ticks);
`prolonged_starvation_events`/min; `concealed_underruns`;
`smooth_latency_trims`; audio `lost_packets` with its per-minute series;
`avg_` / `max_queue_residence_ms`; `first_write_elapsed_ms`; the `P8` hole
count and length histogram; rendered fps, spikes, `max_output_gap_ms`,
video loss/min.

Then, across the six 3/8 sessions now on record (`P8`-A, `P9`-A2, A3, A4
and, at 3/8-equivalent behaviour, `P7`'s) the **underrun total's spread**
— min, max, median — is the noise band.

**Pre-registered reading.**

- **Adopt 12/17** if, in both B arms, `prolonged_starvation_events`/min is
  ≥ 80 % below the mean of A3/A4, `avg_queue_residence_ms` is +30-55 ms,
  the hole histogram is within 20 % of the A arms, **and** each B arm's
  underrun total is **inside the 3/8 noise band (≤ its max)** or above it
  by no more than one event (a run of consecutive ticks) — i.e. the count
  does not rise by more than the largest single 3/8 event. Then set the
  profile default to 12/17 (one-line change, `audio_cushion.source:
  profile`), rebuild is **not** needed if the default lives in the
  companion profile — say where it lives; if it needs the client, say so
  and stop for the user (DEVELOPMENT-ONLY pending a build).
- **Keep 3/8** if either B arm's underrun total exceeds the band by more
  than one event, or the starvation drop is under 80 % in either B, or the
  residence cost is outside 30-55 ms. Say which.
- **Audio loss**: report the per-minute series of all four arms in run
  order. **Time-driven** if A4 ≥ A3 and B3 ≥ B2 with the B arms not
  systematically above their neighbouring A arms — then note it as a
  session-length effect for the roadmap (it is not the cushion's) and
  leave it. **Cushion-linked** if both B arms exceed both A arms by ≥ 50 %
  regardless of order — then say so plainly; it would contradict the
  counter's definition and needs its own probe (name it, do not run it).

## Record and memory

`evidence/D_BASE_P9A_CUSHION_INTERLEAVED_<date>.md` (raw first, the four
arms in run order, the noise band, the reading) with reports, heartbeat
logs, hole histograms and SHA-256s under `evidence/d_base_p9a_<date>/`;
the `P9` decision record updated with the outcome; patch record only if
the default changed; `CURRENT.md` (fixed headings, `python3
tools/check_memory_health.py` healthy — trim; Next Action: thermal
thresholds); `MEMORY.md` (the cushion's final state and measured cost,
and the underrun-total noise band as a durable fact); `handoffs/
CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`; `KNOWN_ISSUES.md` (the
audio-loss trend, open or closed); `TOOLS.md` (how to switch the cushion,
and that a 20-minute underrun total is noisy — read events, not totals);
`docs/PROJECT_STATUS.md` if the default changed. Teardown per `TOOLS.md`;
no `PRIVYHUB_*` in the user manager's environment at the end; companion
running under systemd. Never retry a failing action more than twice. No
addresses or device identifiers in any memory or evidence file. Nothing
committed.
