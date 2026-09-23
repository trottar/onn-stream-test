---
memory_schema: 1
as_of: 2026-09-23
status: HISTORY — CURRENT_HANDOFF.md sections moved out verbatim on 2026-09-23 (size limit); nothing rewritten
---

# Handoff sections moved 2026-09-23

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

**Answered by `P8` (2026-09-22):** not the heartbeat, not the adb socket
sampler — the path (`../evidence/D_BASE_P8_AUDIO_HOLE_ORIGIN_2026-09-22.md`).


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

