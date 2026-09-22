---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Baseline stream health.** Reach seamless local play on the Linux host ->
onn native game stream, against the target in
`investigations/BASELINE_STREAM_HEALTH.md`. Phase C **SUSPENDED** till it
closes. Decision: `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`.

## Current Work Item

**Overnight queue** (`handoffs/OVERNIGHT_2026-09-22_QUEUE.md`) — complete:

- **`D-BASE-P6a` — RUNTIME VALIDATED**, `evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`.
- **`D-BASE-S3` — SOAK VALIDATED**, `evidence/D_BASE_S3_CAP_SOAK_2026-09-22.md`.
- **`D-BASE-P7` — CHARACTERIZED**, `evidence/D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`.
- **`H2-PREP` — INVENTORY RECORDED**, `evidence/H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`.
- **`M1` — DOCS RECONCILED**, `CHECKPOINT_PROPOSAL_2026-09-22.md`.

**The 90 KB frame cap is adopted and in force.**
`max_frame_size_bytes = 90,000` is a declared field of
`native_game_720p60_reference` (Linux `h264_vaapi`), **nothing set in the
environment**. The user checked the picture first — "could barely tell it
was over the LAN", **their words, not instruments.** All ten `P6a` gates
passed; **`PRIVYHUB_ENC_MAX_FRAME_SIZE=0` still runs uncapped** and
`any_override` is **false when only the profile decides**. Over three
hours (`S3`): **5.4 losses/min**, ~25x below uncapped, 0 resyncs, 0 socket
drops, fps 59.96, both logs rotated twice with zero lost rows. **The
residual tracks nothing** (every Spearman under 0.08) — **the loss column
is closed at this level**. Two frames came **9-11 bytes over**: the cap
is a target, **check with a tolerance**.

**`prolonged_starvation_events` is named** (`P7`): **one event per hole in
the audio arrival stream longer than ~15 ms**, latched, episodes not
polls. Rho **+0.684** against the max arrival gap, **+0.020** against
audio loss: **jitter, not loss**. The host paces to 5.0 ms; the client
sees a **55-60 ms hole about once every 2 s** — a path property (75.9/min
PC → 32/min capped Opal). The only client lever is a deeper cushion at
**+45 ms audio latency**.

**`M1` reconciled the top-level docs** and found one disagreement: the
synthetic UDP pathology **was** replayed from a Linux sender and
reproduced — **not Windows-only** — but never on the post-`B2` topology.
**PAUSED, and separate from the in-session loss.**

Earlier, **in full in `handoffs/CURRENT_HANDOFF.md`** — read it before
touching the encoder or any log slicing: `P6` (the transfer function),
`P5` (0 of 4,349 socket drops), `O1` (neither the air nor the Opal), `R5`
(**rotation breaks offset-based slicing**), `P4`, `P3`, `B2`, `T1`, `S2`
(**`C5` FALSIFIED**), `S1`, `P2b` → **`P2a` VALIDATED**, and **`R3b`
refused by the classifier**.

## Verified State

Target table against the 128-session pre-`C3.L2c` corpus and the current
build. **`S1`/`S2` are the PC-path reference**: fps 59.42-59.64, spikes
92-103/min, loss 115-129/min, no stall over 1 s.

| metric | target | corpus | now |
| --- | --- | ---: | ---: |
| spikes >= 20 ms / min | < 200 | 2,535 | **15-245** |
| rendered fps | >= 59.5 | 55.5 | **59.65** |
| received-AU fps | — | 59.2 | 59.8 |
| max output gap (ms) | <= 100 | 287 | 123-463 |
| stale output drops / min | < 20 | 193 | **9.3** |
| lost packets / min | < 10 | 197 (2-3x under) | 109-144; **5-20 capped** |
| audio underruns / session | < 5/min (note) | 207 | **13-20** |

Frames under 20 ms receive-to-output: 28.4 % corpus median → **98.4 %**;
client fps deficit 3.5 → **0.08-0.28**. Four of six rows meet target on a
quiet link; `max output gap` does not (transport), and the audio row is
not a rate. Group A: SPS/SEI explicit and repeated with every IDR;
x11grab 60 fps clean; **host wired to the Opal since `B2`**. On the Opal
path, 42 sessions: loss/min **1.4-144**, spikes 35-68/min, fps
59.56-59.90. **Not pacing (`P3`), not the air (`P4`, `O1`), not the onn's
receive path (`P5`)**: it **is** the frame-size tail — `P6` capped it and
loss fell **7-9x** with bitrate unchanged. **Thermals (`T1`):** host
hottest sensor 54 → 60 °C over 10 min; **the onn reports status only**.

- **`R1`**: `lost_packets` includes resync jumps; **`C3.L2c`** kept.
- **Installed now**: the `P7` build (heartbeat v3, ten audio fields), APK
  `6d25dee0…400c`; `NativeStreamActivity` `96582702…b319c1d6`.
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); `am start` cannot open `NativeStreamActivity`.
- **`logs/games/native_frame_sizes.jsonl`** (`P5`/`P6`): packets and
  payload bytes per frame, a line a second (`TOOLS.md`).
- **`.claude/` and `_prel2b/` are untracked and unignored** — the user's
  call before any commit (`CHECKPOINT_PROPOSAL_2026-09-22.md`).

## Next Action

**`H1` is DONE** — the SSH console is up and key-only, autologin is in
force, and X answers a bare SSH shell on `DISPLAY=:0` alone
(`evidence/H1_VERIFY_SSH_CONSOLE_2026-09-22.md`; `TOOLS.md` has the
console section). **`H2` — the headless cutover** is now gated on **two**
things: the plug going in, and **the user reconnecting adb from the TV** —
the onn is not listed, its wireless-debugging port rotated, and no
reconnect is possible from the host, which blocks `H2` check 2.
`D-BASE-H2_TASK.md` is rewritten from the inventory (X `DisplayPort-0` =
DRM `card0-DP-1`, the mode line, the one write). Still true: `Linger=no`
with nothing starting the companion at boot leaves a power cycle running
nothing — start it by hand.

**`D-BASE-R3b` PARTLY DONE (2026-09-22)** — run by hand;
**N3, N15, N150 all PASS** (`evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`).
`GIVE_UP_MS` and the recovery save are exercised. **N05, N15b and E30 still
owed**, so `R3`+`R3a` are not runtime validated and `END_MS` is untouched.
**Two post-run defects open** — the launcher cannot launch while a stopped
stream leaves the game session live, and a recovery-state load leaves the
picture cycling through ~4 frames
(`evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`).

**Then whatever `S3` and `P7` left open**: the **~55-60 ms audio arrival
hole** `P7` could not locate (one maximum per 2 s tick aligns with
nothing), and **thermal thresholds**.

Also open: `END_MS`; `host_link`; `B1`/`B3`; Group C; C6. Done 09-20/22:
Group A; `R1`-`R5`; `P1`-`P7` incl. `P6a`; `C3.L2c`; `C5`; `C5a`;
`S1`-`S3`; `T1`; `B2`; `O1`; `H2-PREP`; `M1`.

## Success Criteria

Phase C resumes only when the target table above is met, or the attempt
is formally abandoned. **Pre-registered client decision** (`D-BASE`): if
after Steps 1-3 a healthy decode path on the production link still cannot
reach `spike_20_ms/min < 200` and fps `>= 59.5`, the onn is the ceiling
and the client changes. *Bearing: both are met in every `S1`/`S2` healthy
block and all 42 Opal-path sessions; the clause assumed the decode path
would bind and it does not. **Not resolving.*** No perceptual gate.

## Do Not Reopen Without New Evidence

- D4 Games and D5 media/server restoration; the Windows-era C3 record.
  The `C3.L2` classification: Linux is `video_only_restart`, not
  authorized for automatic adaptation during play; `C3.L3a` Part 1 —
  chained ladder transitions are clean.
- The stall-tail-is-client-code hypothesis: falsified by the full-corpus
  re-score. Reopen only with a stall over 1,000 ms, no sequence jump, no
  IDR wait. **A1** and **A3** (x11grab not 60 fps clean): falsified on the
  wire; reopen A1 only with a production SPS/SEI differing from
  `evidence/group_a_2026-09-20/`.
- **The host display path** (`H2-PREP`): X11/LightDM/XFCE, monitor on X
  `DisplayPort-0` = DRM `card0-DP-1`, no `xorg.conf`, no autologin, no SSH
  server. Re-run the inventory after the plug; do not re-derive.
- **The synthetic UDP pathology is PAUSED, not Windows-only** (`M1`, from
  `DEFERRED.md`): it reproduced from a Linux sender, but never on the
  post-`B2` topology. Separate from the in-session loss.
- **The 2026-09-19 `C3.L2c` rollback** — the user **kept** the build.
  **The audio underrun rate per minute** — a startup burst (`P2`); read
  the total. **The completeness gate as slow-resync cause** and
  **RetroArch memory as a leak** — falsified by `S2` (but see `S3`'s
  +34.3 MB anonymous). **The short-SIGSTOP substitute as a source of
  resyncs** — true at 0.3 s only; `B2` falsified it at 3 s.
- **The onn's thermal zones/headroom** (`T1`) **and its retry/airtime
  counters** (`P4`) — absent on this device; reopen with other hardware.
- **The frame cap is adopted** (`P6a`): 90,000 bytes in the profile; `=0`
  runs uncapped for comparison. 60 KB and VBV are **measured
  alternatives, not rejected** — reopen with a picture complaint.
  **Intra-refresh, `slices` and average QP do not exist** in this
  `h264_vaapi` (`q=-0.0`).
- **The loss column is closed as a measurement.** Not airtime, the Opal's
  radio or a `sta0`/`sta1` uplink (`O1`); not environmental (`O1`: Pearson
  0.964); not the onn's receive path (`P5`: **0 of 4,349** socket drops —
  **a larger client buffer is not a fix**). **It is the frame-size tail**
  (`P6`: capping removed 100 % of ≥80-packet frames and 7-9x of the loss,
  twice), and capped the **residual tracks nothing** (`S3`). Reopen only
  with a sub-second airtime instrument, a driver whose `tx failed` is
  independent of `tx retries`, or a moving `drops` column. **Do not
  derive loss as host-sent minus client-received** (`P4`: 29x noise) —
  use `R5`'s counters.

## Relevant References

One evidence record per item, one patch record where code changed;
`patches/PATCH_INDEX.md` lists all 116. A classification per record is
in `evidence/RUNTIME_VALIDATION.md`.

- **2026-09-22** — `D_BASE_P6A_CAP_ADOPTED` (decision of the same name),
  `D_BASE_S3_CAP_SOAK`, `D_BASE_P7_STARVATION_COUNTER`,
  `H2_PREP_HOST_DISPLAY_INVENTORY`; `../CHECKPOINT_PROPOSAL_2026-09-22.md`.
- **2026-09-21** — `D_BASE_P6_FRAME_TAIL_CONTROL` (the arms, the knee,
  the quality caveat), `D_BASE_P5_WHICH_QUEUE`, `O1_OPAL_AIR_VIEW` (this
  AP's three counter traps), `D_BASE_R5_HEARTBEAT_LOSS_COUNTERS`,
  `D_BASE_P4_AIR_TELEMETRY`, `D_BASE_P3_SENDER_PACING`, `B2_HOST_ON_OPAL`.
- The rest of `D-BASE`, one file each:
  `D_BASE_{T1,S2,S1,P2B,P2A,P2,R3,R3A,R4,P1}_*`, `C5A_IDR_REJECTION_*`,
  `C3_L2C_DISTRIBUTION_*`, `GROUP_A_*`.
- `investigations/{BASELINE_STREAM_HEALTH,DEFERRED,ACTIVE}.md`;
  `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`; `docs/KNOWN_ISSUES.md`
  (two UDP entries + 2026-09-22 open items); `docs/PROJECT_STATUS.md`.
