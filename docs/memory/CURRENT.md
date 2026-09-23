---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: 3e6cde5
---

# Current State

Headings are fixed by `tools/check_memory_health.py`; do not rename.
## Active Objective

**Baseline stream health.** Reach seamless local play on the Linux host ->
onn native game stream, against the target in
`investigations/BASELINE_STREAM_HEALTH.md`. Phase C **SUSPENDED** till it
closes. Decision: `decisions/D-BASE_BASELINE_BEFORE_ADAPTATION.md`.

## Current Work Item

**`D-BASE-P10` — audio redundancy ADOPTED** (the user;
`evidence/D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md`,
`decisions/D-BASE-P10_AUDIO_REDUNDANCY.md`). Every audio datagram is sent
twice, the copy 20 ms later; the client keeps the first. Warm,
interleaved: audio loss **78 → 1.4-2.8/min (−96-98 %)**, crossfades in
step, **+1.6 Mbps**, no added latency. The warm-state loss is single
packets (98-99 % of gaps). The pre-registered rule failed one clause on
the favourable side (video FEC recoveries lower with it on). APK
`f31b1c18…8ae7` (also fixes a latent late-packet bug).

Before it: `T3` — the warm-state loss is lost **between** the ends (host
sends all, onn drops none); `T2` — it steps up ~7 min from cold, idle
resets it; 12/17 adopted; `P9a`, `P9`.

**`H3` installed by the user** 2026-09-23 (user-stated, verified across
a reboot): the companion runs as the systemd user unit
`privyhub-companion` — restart it with `systemctl --user restart`.
Before that: `R3c2` RUNTIME VALIDATED, N05 → `R3`+`R3a` RUNTIME
VALIDATED for real loss, `P8` (audio holes are the path's).

**`H2` — the host is headless: RUNTIME VALIDATED** (2026-09-22,
`evidence/H2_HEADLESS_CUTOVER_2026-09-22.md`): the dummy plug on X
**`DisplayPort-1`** = DRM `card0-DP-2`, 1920x1080 @ 60 by EDID; capture
unchanged. adb after a host reboot: **`adb connect <onn-address>:5555`**.

**The 90 KB frame cap is adopted and in force** (`P6a`, profile field,
nothing in the environment; `=0` runs uncapped; `any_override` false when
only the profile decides). `S3`: **5.4 losses/min over three hours**, the
residual tracks nothing — **the loss column is closed at this level**; the
cap is a target, check with a tolerance (two frames 9-11 B over).
`M1`: the synthetic UDP pathology is PAUSED, not Windows-only.

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
- **Installed now**: the `P10` build (the `R3c2` tiles, P8's ring, schema
  `_v2`, the cushion setting, audio de-duplication), APK `f31b1c18…8ae7`.
  Profile: cushion **12 / 17**, redundancy **2 / 4**.
  `PRIVYHUB_HEARTBEAT_MS` and `PRIVYHUB_AUDIO_QUEUE_*` unset.
- **Host-shell operation**: open `MainActivity`, wake, tap RESUME PLAYING
  (`TOOLS.md`); `am start` cannot open `NativeStreamActivity`.
- **`logs/games/native_frame_sizes.jsonl`** (`P5`/`P6`): packets and
  payload bytes per frame, a line a second (`TOOLS.md`).
- **`.claude/` and `_prel2b/` are untracked and unignored** — the user's
  call before any commit (`CHECKPOINT_PROPOSAL_2026-09-22.md`).

## Next Action

**The roadmap list**: `host_link` (first fact: `T3` — the warm-state loss
is lost between the host's NIC and the onn's IP stack, cause not
located), `B1`/`B3`, Group C, C6. The C1 profile now carries the frame
cap (90 KB), the audio cushion (12/17) and audio redundancy (2/4).
Open for the user: their listen with redundancy on; the `T2`/`T3`
threshold proposals (none enforced).

Also open: `host_link`; `B1`/`B3`; Group C; C6. Done 09-20/22:
Group A; `R1`-`R5`; `P1`-`P7` incl. `P6a`; `C3.L2c`; `C5`; `C5a`;
`S1`-`S3`; `T1`; `B2`; `O1`; `H2-PREP`; `M1`; `H1`; `H2`; `R3`/`R3a`/`R3b`/`R3d`; `R3c`; `R3c2`; `P8`; `H3`; `P9`; `P9a`; `T2`; `T3`; `P10`.

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
- **The host display path** (`H2-PREP`, `H2`): X11/LightDM/XFCE,
  autologin, no `xorg.conf`; the dummy plug on X `DisplayPort-1` = DRM
  `card0-DP-2` at 1920x1080@60 by EDID. Re-run the inventory; do not
  re-derive. Headless does not change the capture (`H2` checks 3-4).
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
`patches/PATCH_INDEX.md` lists all 119. A classification per record is
in `evidence/RUNTIME_VALIDATION.md`.

- **2026-09-23** — `D_BASE_P10_AUDIO_REDUNDANCY` (decision of the same name),
  `D_BASE_T3_AUDIO_LOSS_LOCATION`,
  `D_BASE_T2_STREAMING_ACCUMULATION`,
  `D_BASE_P9A_CUSHION_INTERLEAVED`,
  `D_BASE_P9_AUDIO_CUSHION` (decision of the same name),
  `D_BASE_R3C2_RECOVERY_FLOW`, `H3_COMPANION_AUTOSTART_DESIGN`.
- **2026-09-22** — `D_BASE_P6A_CAP_ADOPTED` (decision of the same name),
  `D_BASE_S3_CAP_SOAK`, `D_BASE_P7_STARVATION_COUNTER`,
  `H2_PREP_HOST_DISPLAY_INVENTORY`, `H1_VERIFY_SSH_CONSOLE`,
  `H2_HEADLESS_CUTOVER`; `../CHECKPOINT_PROPOSAL_2026-09-22.md`.
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
