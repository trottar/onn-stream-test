# G5-S4 — the remote rung cap: the design (written before the code)

Baseline `1dab25d`, with G5-S3's uncommitted work in the tree (this builds on it).
Session B, unattended. Task: `handoffs/G5-S4_REMOTE_RUNG_CAP_TASK.md`. Read before
writing: G5-S3's record (the context's `path_class`; the remote list 4000-7000;
`remote_ladder.py`), `adaptive_bitrate_live.py` (`LivePolicy._decide`'s target
selection, the hold-downs, `observe`), G4-S1 §9 (5.1 GB/h at 7000; 2.3 at 4000).

## 0. Reading the handoff (disclosed)

"A session starts at the cap or below" and "the cap never forces a step-down by
itself" meet at the session's start: every stream starts at 7000 (C1: a full
start is the reference profile), and the cap is a data saver, so on a clean link
it must bring the stream down to the cap or it saves nothing. This design reads
the two as: **the cap moves the stream down to the cap, and never further** --
below the cap every step down is the ladder's own (or G5-S2's), and the cap never
lowers the floor (every valid cap is a rung >= 4000). The move to the cap is a
ladder decision through every existing gate, so it comes after the ladder's 60-s
session-age guard: a session runs its first minute at 7000 (about 86 MB at G4-S1's
11.42 Mbit/s). Starting the encoder itself at the cap would be a change to the
stream start's profile, not to the ladder: not in this task; listed.

## 1. The flag

- **`PRIVYHUB_REMOTE_RUNG_CAP=<kbps>`**. Absent or empty = today, byte for byte:
  nothing imported, no row, no clamp.
- **Valid** only at a rung of G5-S3's remote list: 4000 / 5000 / 5500 / 6000 / 7000
  (an integer after stripping spaces). Anything else: **one** ladder-log row at
  the controller's start (`event: remote_cap_config`, `active: false`, `reason:
  not_a_remote_rung`; a non-numeric value is recorded as `non-numeric`, never
  echoed), then ignored.
- **Depends on G5-S3:** valid but `PRIVYHUB_REMOTE_LADDER` absent -> one row
  (`active: false`, `reason: remote_ladder_flag_absent`), and nothing else.
- Valid with G5-S3's flag -> one row (`active: true`, `cap_kbps`), and the effect
  below. The user's setting, by a drop-in; never automatic.

## 2. The effect (remote path only; `path_class` from G5-S3's shared instance)

- **The clamp, in the ladder's target selection** (`LivePolicy._decide`, after the
  target is chosen, one guarded `if`):
  - a decrease whose target is above the cap goes to the cap instead (e.g. 7000,
    ROUTINE -> 6000, cap 4000 -> 4000; FALLBACK -> 5000, cap 4000 -> 4000);
  - an increase whose target is above the cap is refused `remote_cap` (the
    ladder's wish recorded); at or below the cap it proceeds;
  - a decrease already at or below the cap is untouched.
- **The move to the cap** (after the feed in `LiveController.observe`, one guarded
  `if`): on a remote path with the stream above the cap, on an evaluated report
  where the ladder decided nothing and nothing is pending, one ROUTINE decision
  with trigger `remote_cap` through `_decide` -- so the hold-downs, the blackout,
  the guards (incl. 60 s), the rate limit and the oscillation guard all apply; its
  target is clamped to the cap; the row's reason is `remote_cap`.
- **On the LAN** (or the class not remote): nothing at all.
- G5-S2's rules keep working under the cap: `floor_4000` under a 5000 cap still
  lands on 4000 (a decrease below the cap is not clamped); R5 can only block.

## 3. Recorded

- The config row, once per controller.
- **Every clamp** that changes the ladder's target: the `transition` row (or a
  `refused` row) carries `source: remote_cap`, `wish_kbps` (the ladder's
  target), `capped_kbps`, `cap_kbps` (G5-S3's `annotate` hoists them from the
  measurements). An increase blocked at the cap is a `refused` row with reason
  `remote_cap` -- logged once per run of identical refusals (the ladder's own
  convention), every report's `sample` row then reading `reason: remote_cap`;
  the cap counts every block (`clamps` in its status).

## 4. Not in this task

A client-side setting (G3's Settings dialog, session A's APK work); a data
counter; the encoder starting at the cap (§0); any live run.

## 5. The proof (no stream)

- **Unit tests** `tests/remote_cap/`: the flag absent / empty / invalid (3000,
  4500, 8000, text) / valid at each rung; G5-S3 absent -> inactive with one row;
  LAN unaffected; remote: the move to the cap after the 60-s guard, at each cap;
  an increase never above it; the ladder's own steps below it; FALLBACK clamped;
  `floor_4000` under a 5000 cap lands on 4000; the guarded imports (AST).
- **Flag absent, byte for byte:** the in-process comparisons of
  `flag_absent_proof.py` (G5-S3's, re-run with the cap code present: the actuator,
  the games plugin, G5-S2's replay exact and identical) and G5-S3's own replay
  re-run with the cap absent: its tables equal G5-S3's recorded ones.
- **Flag present, replay** (`replay.py` here): G4-S1's runs 1 and 2 with the cap
  at 4000 and at 5000 (G5-S3 on; G5-S2's rules off and on): the target per tick
  (time at each level), the clamps, and the wire rate each level implies from the
  measured figures (C5-M3: 8.60 Mbit/s at 7000, 5.02 at 4000; 5000 has no wire
  measurement -- L1's estimate 6.20 is used and labelled as an estimate; G4-S1's
  overlay-interface 11.42 at 7000) -> the data per hour at each cap, **as
  arithmetic, not as a result**.
- The suites green; the redactor.
