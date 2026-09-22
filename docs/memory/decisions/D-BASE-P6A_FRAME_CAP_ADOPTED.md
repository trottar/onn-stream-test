---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
status: DECIDED 2026-09-22 by the user
---

# Decision — the 90 KB frame cap is the native stream profile default

## The decision

**`max_frame_size_bytes = 90,000` is a declared parameter of the
`native_game_720p60_reference` profile**, honoured by the `h264_vaapi`
(Linux) encoder path. It is in force with nothing set in the environment.

Taken by the user on 2026-09-22, on `D-BASE-P6`'s measurements plus their
own perceptual check.

## Why

`D-BASE-P5` located the loss at a per-frame micro-burst meeting the
wireless queue. `D-BASE-P6` intervened on it across seven arms with
baseline bookends:

- capping the largest frame at 90,000 bytes removed **100 % of the
  >= 80-packet frames** (718 → 0) and **7-9x of the loss** on two
  independent pairs (2,696 → 311; 2,896 → 408);
- **achieved bitrate, fps, encoder CPU and GPU power did not move** — the
  encoder spends the same bits, the cap changes only when it may spend
  them;
- the small-frame loss buckets were **not** raised, which is the
  bucket-specific pattern that distinguishes cause from coincidence.

**The one cost instrumentation cannot see is picture quality on the ~1 %
of scene-change frames the cap binds on.** The user checked it themselves
on 2026-09-22, playing the `A1` arm for about a minute: **no stutters,
"could barely tell it was over the LAN."** That is a user-stated
perceptual result, not instrument evidence. With it, the user decided to
adopt.

`D-BASE-P6a` then validated the adopted form: **RUNTIME VALIDATED**, all
ten gates, loss 249, max frame 89,874 B, zero >= 80-packet frames.

## What was considered and not chosen

- **A 60,000-byte cap.** Measured at 299 loss against 90 KB's 311 — a
  tie — while constraining a third harder. **The benefit saturates once
  the >= 80-packet population is gone**, so the tighter cap buys nothing on
  loss and costs more of the quality that was not measured. Still
  available via the override.
- **VBV (`-bufsize` at the one-frame budget).** Flattens hardest of all
  and gives the best spike rate (15.0/min), but **loses 3x more than the
  cap** and is the only arm that *raised* loss in windows that had none.
  It trades the tail for a higher floor. Still available via
  `PRIVYHUB_ENC_BUFSIZE_K`.
- **Intra-refresh and slices.** Not available: neither option exists in
  this host's `h264_vaapi`.
- **A larger client receive buffer.** Ruled out by `D-BASE-P5` — the onn's
  socket dropped 0 of 4,349.

## What stays available

**`PRIVYHUB_ENC_MAX_FRAME_SIZE` overrides the profile, and `=0` runs
uncapped** with the flag absent from the argv. The `D-BASE-P6` baseline is
therefore re-runnable at any time without editing source, which is the
condition under which adopting a measured setting is safe.

`encoder_overrides` on `native-stream-status` reports which source is in
force (`profile` or the variable), the profile's value as
`default_max_frame_size_bytes`, and `any_override` — **false when only the
profile decides**.

## Scope

**Linux `h264_vaapi` only.** The deferred Windows NVENC path ignores the
field and logs one line saying so; it is not translated, because there is
no measurement behind a translation. No client change, no pacing change,
no FEC change, `-bufsize` untouched.

## What this decision does not settle

- **The target table is not met.** `max output gap` still misses, and
  `prolonged_starvation_events` is still unexplained.
- **The Windows-era UDP burst pathology** stays a separate deferred note.
  This cap fixes the Linux host path; it is not a claim about that.
- **The perceptual evidence is one minute of one person's judgement.** If
  a scene change ever looks wrong, the cap is the first thing to raise,
  and the alternatives above are already measured.

Records: `evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`,
`evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`,
`patches/D-BASE-P6A_FRAME_CAP_PROFILE_DEFAULT.md`.
