---
memory_schema: 1
as_of: 2026-09-25
status: TASK HANDOFF — C4-M1: the measured arm C4-D1 asked for — recover the two-packet residual that 8+1 leaves, first by depth-2 interleaved 8+1 (zero overhead) and only if that fails by 8+2, as a comparison arm behind an override (nothing adopted), interleaved against the adopted 8+1 over one night with pre-registered rules against the night's own noise; companion + client change on a comparison path, APK rebuilt and installed for the night and the adopted APK reinstalled at the end; authorized by the user 2026-09-25 ("Proceed")
---

# C4-M1 — the FEC arm, measured

**Why.** `decisions/C4_ADAPTIVE_FEC_2026-09-24.md`: BUILD (static, not
adaptive), first step a measured arm. `C4_D1_FEC_EVIDENCE_2026-09-24.md`:
8+1 leaves ~9.1 lost/min post-FEC at the median and **55 % of the residual
is two consecutive packets lost inside one group** (a gap event of size 2).
The video-loss row is marginal — 7.7-9.2/min on the shadow night's holds,
14-24/min on `CTRL-L1`'s holds the same evening, 37/19 on `S1`'s T1/T2 —
against a target of < 10. Two candidates recover a two-consecutive-packet
gap: **depth-2 interleaving of the existing 8+1** (even and odd packets in
separate groups, so consecutive losses land in different groups — no extra
bandwidth, parity arrives one group later) and **8+2** (a true two-erasure
code, +12.5 % more parity, a new decoder on the client). Try the free one
first.

Read first: `C4_D1_FEC_EVIDENCE_2026-09-24.md` (§1 gap-size table, §4
latency), `companion/native_fec_relay.py` (group formation, the flush on
marker/timestamp, the FEC header: version `xor8_1`, group size — what a
receiver needs to know), `PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt`
and the FEC decode path (how a group is assembled and repaired; what the
header version gates), `evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`
(the comparison-arm discipline: env override, restart through the unit,
`any_override` shown in status), `TOOLS.md` (overrides, APK install,
teardown), `evidence/d_base_p9a_2026-09-23/` (an interleaved-pairs night
and its harness), `evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md` (an
unattended APK build + install + reinstall, the precedent).

**Scope.** Companion: the relay gains a scheme selectable **only** by
`PRIVYHUB_FEC_SCHEME` (unset/`xor8_1` = adopted behaviour byte-for-byte;
`xor8_1_i2` = interleaved; `xor8_2` only if step 2 is reached) — the
profile is **not** changed, `any_override` reads true during the arm and
false after; the wire header carries the scheme so the client selects its
decoder from the packet, never from a setting. Client: decode the new
scheme(s) and keep decoding `xor8_1` unchanged; counters
(`fec_recovered_packets`, `fec_unrecoverable_groups`, `lost_packets`,
forward gaps) keep their meaning per group. **No encoder flag, profile
value, cap, cushion or redundancy change.** The adopted APK
(`f31b1c18…8ae7`) is kept and **reinstalled at the end of the night**;
the arm APK's hash is recorded. Stop rules: if the client's FEC header
has no version field that can gate a second scheme, or the receiver's
group assembly cannot take interleaving without touching the H.264
reassembly path, **stop before any build**, do the offline simulation
only (step 0) and record DESIGN-ONLY.

## Steps

0. **Offline first.** Replay the recorded gap series (the `C4-D1` inputs)
   through both schemes in a script: for each session, post-FEC loss/min
   under 8+1 (must reproduce the recorded value), under interleaved 8+1,
   under 8+2. Pre-registered: proceed to build **interleaved** if it
   recovers ≥ 40 % of the residual at the corpus median; else build 8+2
   if it recovers ≥ 40 %; else DEFER with the numbers and stop.
1. **Build** the chosen scheme (relay + receiver), unit-test the codec
   pair in isolation (every single-loss and every two-consecutive-loss
   pattern in a group recovers; three-consecutive does not for
   interleaved; the adopted scheme's bytes are unchanged — golden test
   against a recorded group), `py_compile`, the Android build as
   `R3C2` did, install to the onn, record both APK hashes.
2. **Smoke** 3 minutes each: adopted scheme (override unset) and the arm
   scheme — stream reaches PLAYING, heartbeats flow, `fec_recovered` /
   `unrecoverable_groups` count, no resyncs; if the arm smoke fails, stop,
   reinstall the adopted APK, record.
3. **The night**: six 20-minute attract-mode holds, strictly alternating
   B (adopted, override unset) / A (arm) / B / A / B / A, companion
   restarted through its unit before each with the override set or
   unset, `T2` sampler on, `any_override` recorded at PLAYING every time.
4. **Score, pre-registered, against the night's own noise.** Per hold
   the close-out rows plus `fec_recovered/min`, `unrecoverable_groups/min`,
   gap-size distribution, group-completion delay (the receiver's repair
   latency if it is counted; else the relay's parity emit offset). Rule:
   the arm **RECOVERS THE RESIDUAL** if video loss/min post-FEC is lower
   in the A hold of **≥ 2 of 3 pairs** and the pooled A median is ≤ 60 %
   of the pooled B median; **NOT SHOWN** otherwise. Cost rows: spikes,
   fps, stale drops, max gap, audio underruns — **WITHIN NOISE** unless
   all three A holds are worse than the worst B hold **and** the A median
   is beyond it by more than the B holds' own spread (the `S1` rule);
   and the recovery latency stated as a number. Say plainly which side
   each fell on.
5. **Teardown**: override unset and confirmed absent, adopted APK
   reinstalled and its hash confirmed, companion under systemd with the
   profile as adopted, stream at 7000, game inactive.

## Record and memory

`evidence/C4_M1_FEC_ARM_<date>.md` (the simulation, the scheme, the
codec tests, both APK hashes, the six holds, the rule outcomes, what
adoption would mean — it is the user's), evidence dir with the
simulation outputs, reports, heartbeats, thermal jsonl, harness, manifest;
`patches/C4-M1_*.md` with per-file SHA-256s (companion and client);
`PATCH_INDEX.md`; `decisions/C4_ADAPTIVE_FEC_2026-09-24.md` (append the
arm's outcome; adoption pending the user); `docs/ROADMAP.md` C4 line;
`CURRENT.md`; `investigations/ACTIVE.md`; `TOOLS.md` (the override; never
leave it set); the daily file; `evidence/RUNTIME_VALIDATION.md`. No
addresses or device identifiers. Nothing committed.
