# Current Handoff

Authoritative state: `../CURRENT.md`. **Start there.**

## READ FIRST

**The 90 KB frame cap is ADOPTED and in force.**
`max_frame_size_bytes = 90,000` is a declared field of
`native_game_720p60_reference` (Linux `h264_vaapi`), running with
**nothing set in the environment**. The user checked the picture first —
"could barely tell it was over the LAN", **their words, not instrument
evidence**. **Loss runs 5.4-12.4/min against an uncapped 110-145**, zero
≥80-packet frames, bitrate/fps/CPU unchanged, holding over three hours.

**Three things before touching the encoder.** **`any_override: false`
means "only the profile decided"**, not "no cap" — an uncapped run is
`any_override: true` with `uncapped: true`.
**`PRIVYHUB_ENC_MAX_FRAME_SIZE=0` runs uncapped**, flag absent, which
re-runs the `P6` baseline without editing source. And **60 KB and VBV are
measured alternatives, not rejected ones** — reopen on a picture
complaint, not on more loss measurement.

The path is **host wired -> Opal -> onn wireless, one hop** (`B2`).

**`D-BASE-R3b` RAN 2026-09-22, by hand** — the classifier still refuses
every `nft` write, so the user drove
`../evidence/d_base_r3b_2026-09-21/r3b_run.sh`. **N3, N15 and N150 all
PASS**; N15 caught an encoder restart **succeeding while the fault was still
dropping every packet**, and N150's give-up landed at **120.42 s** with the
`.state.recovery` file written. **N05, N15b and E30 did not run, so `R3` +
`R3a` are still NOT runtime validated** and `END_MS` is still unexercised.
Record: `../evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`.

**Read the loss numbers with the restart caveat.** A 3 s outage with no
restart counted **2 348** lost packets; 15 s and 150 s outages that restarted
counted **22** and **40** — a new SSRC makes the return an `ssrc_change`, not
loss. **`max_output_gap_ms` is the honest column for outages.**

**Two post-run defects are open**
(`../evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`): a stream-stop leaves
the game session live, so the launcher resolves to `recovery-resume` and
reports "Loaded" with no window; and after a recovery-state load the source
picture cycles through about four frames. The Tekken 3 `.state.recovery` is
**kept on purpose** as their evidence.

## 2026-09-22 — `H2-PREP` and `M1`, the two non-stream tasks

`../evidence/H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`;
`../CHECKPOINT_PROPOSAL_2026-09-22.md`. Neither touched source.

**Three things block `H2`, none about the plug.** **No
`openssh-server`** — absent, not disabled, so `H1` has not started and
there is no console once the monitor is gone. **No autologin** — a
reboot stops at the LightDM greeter: no X session, no window, no capture.
**Nothing starts the companion at boot**, `Linger=no`. All three are
user-side root writes; `D-BASE-H2_TASK.md` is rewritten round them.

**Names you will need:** X **`DisplayPort-0`** = DRM **`card0-DP-1`**,
**off by one**; today's monitor maxes at **1440x900** through a DP→VGA
adapter. **The capture is a `-window_id`, not the screen**, and
`xdotool --onlyvisible` means X-mapped, so it should survive headless —
*"Whole-desktop capture is intentionally disabled"* means **no window**,
not a capture fault.

**`M1` corrected one thing the handoffs had wrong.** The synthetic UDP
burst/gap/**duplication** pathology is **not Windows-only**:
`investigations/DEFERRED.md` records it reproducing from a Linux sender,
bidirectionally, while idle. It has never been replayed on the post-`B2`
topology. **PAUSED**, and **a different fault** from the in-session loss
the cap fixed. `KNOWN_ISSUES.md` carries two entries.

**Nothing is committed.** `.claude/` and `_prel2b/` are untracked and
**unignored** — the user's call first.

## 2026-09-22 — `D-BASE-P7`, the starvation counter named. CHARACTERIZED.

`../evidence/D_BASE_P7_STARVATION_COUNTER_2026-09-22.md`; patch of the
same name.

**`prolonged_starvation_events` counts holes in the audio arrival
stream** — latched, so **one per hole longer than ~15 ms**, episodes not
polls. Rho **+0.684** against the per-tick max arrival gap, **+0.020**
against audio loss, and the packet deficit averages **+0.54 of ~400** —
**nothing is missing, it is late**.

**The hole is periodic and not the sender's**: 93 % of ticks peak at
**50-69 ms** while the host paces to **5.0 ms, max 5.08**. A path
property — 75.9/min PC, 32/min capped Opal. **Read it as a jitter rate,
not a fault**: 32/min came with **4 actual underruns in 20 minutes**. The
only client lever is a deeper cushion (**3 packets / 15 ms** against a p90
hole of 60 ms = **+45 ms audio latency**); sender pacing is closed by
measurement. **Nothing changed, no rename.**

**The heartbeat is schema v3** with ten audio fields. **Adding a field
takes TWO edits**: the client, *and* `plugins/games.py`'s key whitelist —
`P7`'s first session recorded no audio fields because of the second, and
had to be re-run.

**Still open:** what causes the 55-60 ms hole. One maximum per 2 s tick
aligns with nothing — not the video burst, the AP, or a client stall.

## 2026-09-22 — `D-BASE-S3`, three hours on the cap. SOAK VALIDATED.

`../evidence/D_BASE_S3_CAP_SOAK_2026-09-22.md`. No code change.

**5.4 losses/min over 180 minutes**, ~25x below uncapped. **0 resyncs, 0
SSRC changes, 0 onn socket drops**, fps **59.96**, hourly 380/340/253.
**The residual is a floor**: every Spearman **under 0.08** across 1,080
ten-second and 180 per-minute windows, bucketed table **flat** where
uncapped it rose 14-fold. **A tighter cap is not a lever.**

**How to test the cap:** `max_frame_size` is a **target, not a hard
ceiling**. Two frames came **9-11 bytes over** 90,000 — harmless, but
**check with a tolerance, never `<= 90000` exactly**.

**Rotation proven over hours**: both bounded logs rotated **twice**, **0
discontinuities across 10,801 rows**. **Thermals plateau**, but **`S2`'s
memory result does not reproduce**: RetroArch **+34.3 MB anonymous**
against `S2`'s +6.2 MB, still rising at the end. **The Opal**: mean
utilization **6.82 %**, and a **56.6 % excursion moved the loss not at
all** (rho +0.073).

## 2026-09-22 — `D-BASE-P6a`, the cap adopted. RUNTIME VALIDATED.

`../evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`; patch and decision of
the same name. **All ten gates** on one session with
`env | grep PRIVYHUB_ENC` empty, and the uncapped path **proven**: a 60 s
`=0` check gave a 90,438-byte frame, flag absent.

**The arithmetic that confuses people:** 90,000 B is **~76-79 packets**,
because a large frame's packets run near the 1,188-byte payload maximum,
not the 1,066-byte mean — which is why every capped session reports
`max_packets` **77** against an ≥80 threshold.

## 2026-09-21 — `P6`, `P5`, `O1` and the instruments

Each has its own record; conclusions in `../MEMORY.md`. Carry these:

**`P6` is the intervention behind the adoption** (arm numbers in
`../MEMORY.md`). **The causal pattern:** the ≥80-packet bucket carries
**93-95 % of baseline loss at ~14x the loss/window** of any bucket below,
capping deletes it, **`< 40` is not raised**. **Knee: a step at 100 KB.**
The benefit **saturates** at 60 KB; **VBV is not the same lever** (3x the
loss). **Baselines drift ±15 % — bookend every arm.** No achieved QP,
`slices` or intra-refresh on this encoder.

**Instrument traps, the expensive ones.**

- **`P5`**: the client's Java socket binds the **IPv6** wildcard — read
  **`/proc/net/udp6`**; a row there has **thirteen** fields, not the
  fourteen the header names, so `drops` is the **last**. **`wlan0
  rx_dropped` is broadcast filtering** — 16.6x the loss, rho 0.040,
  never stream loss. The socket discarded **0 of 4,349**.
- **`O1`**: **`tx failed` copies `tx retries`** on this AP, so retry
  exhaustion is unreadable. Every interface `dropped`/`errors` was
  **constant 0**, channel **~93 % idle**: not the air, not the Opal.
- **`R5`**: the heartbeat log **rotates mid-session, breaking
  offset-based slicing** — read archive + live and filter on time. **The
  Gradle wrapper is in `PrivyHub/`.**
- **`P4`**: **no retry, failure, airtime or channel-occupancy counter on
  this onn.** **`video.recent_fps` is a spot reading** — use
  `rendered_frames/duration_s`.

**`P3`** — the sender pacer (**default 0**) was **insufficient at its
8 ms budget, not ineffective**: it clamps above 53 packets a frame,
exactly the tail `P6` capped. **`B2`** — the Windows PC is **neither
implicated nor exonerated**; **`C5a`**/**`C5`** are falsified.
**`S2`/`S1`/`T1`** — recovery works on real link failure; **still owed
`GIVE_UP_MS`, `END_MS`, the recovery save**. **`P2a` is VALIDATED.**

## 2026-09-20 and before

`../2026-09-20.md` is the chronology; conclusions in `../MEMORY.md`. Two
facts hard to find again: **`R4`**'s `diagnostic_retention.py` policy
SHA-256 `b13fbc32…71b5`, which an `--apply` run must quote, and
**`R3`+`R3a`**'s recovery save, which goes to `<stem>.state.recovery`,
**never a slot**. **`P2`**: 98.7 % of underruns fall in the first 3 s —
read the per-session total, never a rate. **`P1`**: the stale default is
60. **`B2` has run; `B1`/`B3` have not.**
