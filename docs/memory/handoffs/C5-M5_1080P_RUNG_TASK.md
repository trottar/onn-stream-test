---
memory_schema: 1
as_of: 2026-10-02
status: TASK HANDOFF — C5-M5 (C5-M4 Part 2): the 1080p rung on the live ladder, behind its own flag, off by default. §1 first and gating: a mid-session size change on the encoder restart (720p/7000 → 1080p/12,600 → back), on injection, measured; if the client cannot take it, stop and list the client work. Then the rung as C5-M4 §4 designed it (entered from 7000 only after a long pre-registered clean window; left on the first capacity_mild bar to 7000/720p), the actuator changes, tests, replays of the leave rule on every recorded 1080p series, an injection session, a 30-min live hold with the rung on, and one pre-registered 2-hour session in the 00:00-08:00 local window. Nothing adopted; the user's picture look after
---

# C5-M5 — the 1080p rung

**Why.** The user's reading of 2026-10-01: Phase C's adaptive machinery
exists so a higher rung becomes usable; 1080p has never been a rung. The
source now renders at 1920×1080 / 4x (C5-M4A), so a 1080p stream carries
real detail (+0.03 content SSIM over the 720p stream of the same source,
C5-M4 §3). The link is the link: LINK-L1/L2 say the loss row is a coin
flip by day and better overnight (00:00-08:00 local, 4 of 4 holds met
across two days); the width is back at 80 MHz. **So the rung is built
and shown on injection and on a clean hold, and its one night runs in
the overnight window.** The `nft` capacity night for the rung is later
and the user's.

Read first: `evidence/C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md` §4
("What the 1080p rung would need", the six actuator changes),
`C5_M2_1080P60_FOLLOWUP_2026-09-29.md` (the c3 arm; its argv and golden
files), `architecture/ADAPTIVE_BITRATE.md` (the controller as closed),
`companion/adaptive_bitrate_live.py`, `companion/native_stream.py` (the
restart path, scale/pad, `_active_bitrate_kbps`), the actuator's
validated level list and `c3-validated-bitrate-transition`,
`C3_F1_RECOVERY_RESTART_LADDER_2026-09-25.md` (level-preserving
restart), `C3_L4_L1_LIVE_CONTROLLER_2026-09-28.md` (the injection
route and its session shape), `C3_L4_N2_MILD_CAPACITY_2026-09-29.md`
(replay tool, stop rule), `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`
(live is the default; kill switches), `TOOLS.md`, `CURRENT.md`. The
shadow stays byte-identical, as every C3.L4 task kept it.

## 1. First and gating: the mid-session size change (`c5_m5_r0_*`)

Pre-register before the session (`c5_m5_preregistration.txt`, hashed;
it holds §1, §4 and §5's rows together):

- **R0a** On injection, a transition 7000/1280×720 → 12,600/1920×1080
  mid-session: the encoder restarts with the new scale/pad, new SSRC,
  new SPS; the client decodes 1920×1080 (SurfaceFlinger buffers at
  1920×1080, the decoder report's size) with **no recovery cycle and no
  session restart**; and back 12,600/1080 → 7000/720 the same way.
- **R0b** Each direction's cost: the output gap at the switch ≤ 2× the
  measured bitrate-only restart (C3.L3a-S1: median 186 ms, max 225 →
  bound **450 ms**), `codec_ms` at the switch reported, sequence resyncs
  0 outside the SSRC change, no stale-drop burst beyond the first
  second.
- If R0a fails: **stop after §1**, record what the client did (the
  decoder's reaction to the new SPS mid-stream, logcat lines redacted),
  and list the client change the rung needs (a decoder reconfigure on
  SPS change, or a decoder restart on SSRC change with a size field).
  The rest of this file waits for the user.

How: a minimal, test-only path — the injection route gains a `size`
with its class, the restart builds the argv at the injected size, no
policy change yet. Two injections in one attract session, 60 s apart,
with the C2 telemetry, the decoder report and SurfaceFlinger captures.

## 2. The rung, as designed (only after §1 passes)

- **The level**: `1080p_12600` — 1920×1080, 12,600 kbps, cap 90,000 B,
  GOP 15, 8+1 FEC, the adopted cushion and redundancy (the c3 arm's
  argv). A level now carries a size; every 720p level carries 1280×720.
- **Ladder**: 5000 / 5500 / 6000 / 7000 / `1080p_12600`.
- **Entry**: from 7000 only, class INCREASE, reason `increase_1080p`,
  when **≥ N−15 of the last N reports since the last SSRC change are
  clean** (the blend's clean definition). N is pre-registered by Code
  with its reason, in the range 300-600 reports (10-20 min at the
  report rate), and the increase hold-down after it is 60 reports as
  now.
- **Leave**: on the **first** `capacity_mild` bar (fps < 57 on ≥ 4/5,
  lost ≥ 50 on ≥ 3/5) → ROUTINE one rung down = 7000 at 720p, with
  ROUTINE's hold-downs; strict capacity → FALLBACK 5000 as now; the
  recovery backstop as now. **No re-entry for 10 minutes** after a
  leave (a new hold-down, pre-registered), and a leave then an entry
  then a leave counts as the oscillation guard's third direction change
  → HOLD at 7000 for the session.
- **Flag**: `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p` enables the rung;
  absent → the ladder tops at 7000 exactly as today (golden: the live
  policy's decisions on every recorded series are byte-identical with
  the flag absent). Off by default; **not adopted by this task.**
- **Status**: the level's width/height in `native-stream-status`; the
  rows carry `reason: increase_1080p` / the leave's `capacity_mild`.
- **The actuator** (C5-M4 §4's six items): the validated level list
  carries sizes; the restart rebuilds scale/pad per level; the
  `reference_profile` / `no_override` guards accept the 1080p level as a
  ladder level (it is not the selector; `any_override` stays false);
  recovery's level-preserving restart covers it (a drop at 1080p
  restarts at 1080p; the backstop still falls back to 5000); the source
  is already 1920×1080.

## 3. Tests and replays, before any session

- `tools/test_adaptive_bitrate_live.py`: the entry (fires at N−15 of N,
  not at N−16; only from 7000; not under the flag's absence), the leave
  (first mild bar → 7000/720p; strict → 5000; the 10-min re-entry
  hold-down; the oscillation count), the size on every level, the
  golden with the flag absent, the shadow suite unchanged, mutations
  caught. The harness suite (`test_c3_l4_nft_night.py`) still passes.
- **Replays** (N2's tool extended):
  - **the leave rule on every recorded 1080p series** — C5-M1's holds,
    C5-M2's six C holds, C5-M4's c_1x…c_8x: when it would have left,
    and how long each sat degraded before that (the mild bar met at
    ~10 s in C5-M4's c holds is the expectation; report it);
  - **the entry rule on every recorded clean-link 720p series at 7000**
    (the S1/N1/N2/D1 holds, the LINK-L1/L2 holds, C5-M4A's V5): where
    it would have entered, and where the mild bar would then have taken
    it back out on the same hold's loss — this is the honest preview of
    what the rung does on this link;
  - the **stop rule**: with the flag absent, zero differences from the
    closed controller on every series.

## 4. Sessions

- **S1, injection**: attract, flag on, live by default: inject the entry
  (the policy's own `increase_1080p` path, not a raw size injection),
  then inject the mild bar → leave; both costs as R0b; `any_override`
  false throughout.
- **S2, a 30-min live hold with the flag on**, on the clean link in the
  daytime: pre-registered **RUNG SHOWN** if the controller enters 1080p
  by its own rule and leaves by its own rule or stays, with every
  transition one the rules name at the spacing they allow, 0 recovery
  cycles, client rows met; loss and gap reported (the day's link). If
  the mild bar never lets it in, that is recorded as "entry not reached,
  N clean reports never accumulated" with the longest clean run.
- **S3, the night**: one 2-hour attract session in the **00:00-08:00
  local window** (start ≥ 01:00), flag on, T2 on. Pre-registered
  **WORKS AS A RUNG** if: every transition is one the rules name, at the
  spacing the hold-downs allow; the time at 1080p and the time at each
  720p rung reported; at 1080p the client rows (spikes, fps, stale,
  audio) met over the 1080p minutes; no oscillation HOLD, or one with
  its three changes listed; 0 recovery cycles or each explained; the
  close-out rows per rung reported. The night is not a link test; its
  loss is reported.
- Teardown after each: flag unset and absent, live default intact,
  stream 7000, adopted profile, no game, 0 banners, APK `de072762…835e`.

## 5. Record and memory

`evidence/C5_M5_1080P_RUNG_<date>.md` and `c5_m5_<date>/` (manifest,
`--check`); `patches/C5-M5_1080P_RUNG.md`; `PATCH_INDEX.md`;
`architecture/ADAPTIVE_BITRATE.md` (the ladder with sizes; the entry /
leave rules; the flag); `docs/ROADMAP.md` C5 (the rung built, shown,
behind its flag); `decisions/C5_1080P60_CAPABILITY_2026-09-28.md`
(append: the rung as the path, the user's reading); `investigations/ACTIVE.md`;
`evidence/RUNTIME_VALIDATION.md`; `TOOLS.md` (the flag, the kill
switches, the injection `size`); the daily file;
`check_memory_health.py`; `git status --short` and `git diff --stat` to
`logs/c5_m5_git_status.txt`; `CURRENT.md` last — Next Action 1: the
user's commit; 2: **the user's picture look at 1080p on the TV** (hand
steps: flag on for one session, the rung entered, what to look at: the
IDR pulse at 90 KB, the sharpness against 720p; nothing perceptual as a
gate; the look decides whether the rung is worth adopting); 3: the
user's call on adopting the flag by default, and the `nft` capacity
night for the rung (the user's); 4: the dither mode at 4x, when they
like.

Adopted profile, source and APK throughout; the rung behind its flag,
off by default, nothing adopted; the shadow byte-identical; no `nft`, no
real `sudo`, the Opal read-only; no addresses, MACs, SSIDs, ADB
endpoints, serials or credentials anywhere; the two-retry limit;
pre-registered rows never tightened or loosened after data. Nothing
committed.
