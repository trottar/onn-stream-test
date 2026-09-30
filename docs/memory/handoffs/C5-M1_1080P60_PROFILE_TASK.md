---
memory_schema: 1
as_of: 2026-09-28
status: TASK HANDOFF — C5-M1: characterize 1080p60 as a stream/client capability — a second, explicit profile (never the default) selectable only by an environment override, measured against the close-out table in interleaved holds against the adopted 720p60 profile with pre-registered rules; capability-gated outcome; nothing adopted; the adopted profile and APK untouched; authorized by the user 2026-09-28 ("yes now")
---

# C5-M1 — 1080p60, characterized as a capability

**Why.** `docs/ROADMAP.md` §C5: characterize 1080p60 on this host and
this onn as a **stream/client capability test**, so 1080p60 becomes
capability-gated rather than assumed. C1 made the profile explicit
(`native_stream_profiles.py`: one constant, `native_game_720p60_reference`,
adopted). There is no 1080p profile; nothing measures whether the
encoder, the link and the client's decoder sustain 1920×1080 at 60 fps
inside the close-out rows. The host's headless display is already
1920×1080 @ 60 Hz (`H2`), so capture needs no display change.

Read first: `native_stream_profiles.py` (every field and its note),
`architecture/NATIVE_SOURCE_CONTRACT.md` (the profile stage; the capture
seam — where the 1280×720 comes from today: capture size, scale filter, or
both), `evidence/C1_STATIC_PROFILE_AND_STATUS_PRIVACY_VALIDATED_2026-09-14.md`,
`evidence/H2_HEADLESS_CUTOVER_2026-09-22.md` (display 1920×1080 @ 60),
`evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md` (the comparison-arm
discipline; `any_override` semantics), `evidence/C4_M1_FEC_ARM_2026-09-25.md`
(the six-hold interleaved night and its harness — reuse it), `evidence/D_BASE_CLOSEOUT_2026-09-23.md`
(the rows and targets), `evidence/D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md`
(the thermal sampler), `evidence/C3_L3_LINUX_FIXED_BITRATE_CHARACTERIZATION_2026-09-19.md`
(bitrate vs the rows at 720p; the bits-per-pixel reasoning starts there),
`PrivyHub/app/src/main/java/streaming/AvcLowLatencyDecoder.kt` and
`NativeStreamActivity.kt` (what the decoder is configured for; whether
1080p needs a client change), `TOOLS.md`.

**Scope.** Companion: one new profile constant
`NATIVE_GAME_1080P60_CANDIDATE` (`id="native_game_1080p60_candidate"`,
1920×1080, 60 fps, GOP 15, bframes 0, FEC 8; bitrate and cap per step 1;
**audio cushion 12/17 and redundancy 2/4 copied unchanged**), and a
selector: `PRIVYHUB_NATIVE_PROFILE_ID` (unset = the adopted profile,
byte-for-byte the same argv as today — golden test; set = the named
profile, `any_override` true, `native-stream-status` showing the profile
id, width, height and bitrate). No other companion change. The adopted
profile's values do not change. Client: only if step 1 shows the decoder
config must change for 1080p (say what and why); if it does, the arm APK
carries that change **and `CL-B1`** (the user's bundle call, 2026-09-28);
the adopted APK `f31b1c18…8ae7` is reinstalled at the end and its hash
confirmed. No encoder flag change beyond width/height/bitrate/cap. No
`nft`. Attract mode, no controller in any mode; the shadow flag and
`PRIVYHUB_FEC_SCHEME` unset throughout.

**Stop rules.** (a) If the onn's decoder does not advertise 1080p60 H.264
(`adb shell dumpsys media.codec` / the codec's `VideoCapabilities` read
from a tiny instrumentation or the app's own log at start — say how),
record NOT CAPABLE (client) and stop after step 1. (b) If the host's
encoder cannot sustain 60 fps at 1080p offline (step 1c), record NOT
CAPABLE (host) with the number and stop. (c) If the arm smoke fails to
reach PLAYING or drops below 55 rendered fps in its 3 minutes, stop,
record NOT CAPABLE (stream) with the numbers, teardown. (d) Never more
than two retries of a failing action.

## Steps

1. **Design, on paper first** (`c5_m1_design.txt`):
   a. Where 1280×720 is produced today (x11grab size, `-video_size`, a
      `scale` filter, or the desktop itself) and what changes for 1080p.
   b. **Bitrate.** State the bits-per-pixel of the adopted profile
      (7000 kbps at 1280×720×60) and the 1080p bitrate at parity
      (≈ 15,750 kbps) and at 80 % of parity; **pick parity as the
      candidate** and record the on-air estimate with FEC 8+1 and audio
      redundancy (≈ +12.5 % + 1.6 Mbps). Say whether that sits inside the
      5 GHz link's measured headroom (`O1`, `B2`) — if the estimate is
      above the measured usable rate, the candidate is 80 % of parity
      and the record says why.
   c. **Encoder headroom offline**: a 60 s `x11grab` 1920×1080 at 60 fps
      through the same `h264_vaapi` argv to `-f null`, encoder fps and
      host CPU/GPU load recorded; the same at 1280×720 for comparison.
      Rule: proceed only if 1080p60 encodes at ≥ 60 fps mean with p5 ≥ 58.
   d. **Frame cap.** Scale the adopted cap (90,000 B at 7 Mbps) by the
      candidate bitrate ratio and round to the nearest 10 KB; state it.
      Say what the cap does to an IDR at 1080p (GOP 15: an IDR every
      250 ms) — if the scaled cap is below the expected IDR size at the
      candidate bitrate, say so and use the IDR size + 20 % instead, with
      the reasoning; the rule is the adopted profile's own (`P6A`).
   e. **The client decoder**: the configured max width/height and any
      surface or buffer sizing; whether a change is needed (stop rule a).
2. **Build**: the profile constant, the selector, the golden test (unset
   → argv identical to today's), a unit test that the candidate validates
   and that the adopted constant's `to_dict()` is unchanged, `py_compile`;
   the client change and APK only if step 1e requires it (Android build
   as `R3C2` did; hashes recorded).
3. **Smoke**: 3 minutes each — adopted (unset) and candidate (set), the
   companion restarted through its unit before each; PLAYING, heartbeats,
   rendered fps, `any_override`, `native-stream-status` profile fields.
   Stop rule (c).
4. **The holds**: six 20-minute attract-mode holds, strictly
   B (adopted) / A (candidate) / B / A / B / A, companion restarted through
   its unit before each with the selector set or unset, `T2` sampler on,
   `any_override` recorded at PLAYING every time, the first hold ≥ 40 min
   after the last `session_ended`. One thing on the host at a time.
5. **Score, pre-registered** (written before step 4, not changed after):
   - **CAPABLE** if every close-out row meets its target on **all three
     A holds**: spikes ≥ 20 ms < 200/min, rendered fps ≥ 59.5, stale
     drops < 20/min, video loss post-FEC < 10/min, max output gap ≤ 250 ms
     (the transport bound; ≤ 100 stays the open row), audio underruns
     reported per hold; **and** the B holds meet the baseline (the
     baseline must stay met).
   - **CAPABLE WITH COST** if all A holds meet the targets but a cost row
     is worse than noise by the `S1` rule (all three A worse than the worst
     B and the A median beyond it by more than the B spread) — name it.
   - **NOT CAPABLE** if any A hold misses any row — name the row and the
     hold; a single miss is a miss.
   - Reported, not gated: host CPU and GPU load, thermal (T2), on-air
     Mbps, encoder frame size distribution vs the cap (cap hits per
     minute), the client's decoder queue depth and `codec_ms`.
6. **Teardown**: selector unset and confirmed absent in the manager and
   the companion's environ, companion under systemd, profile adopted,
   adopted APK installed and hash confirmed (if an arm APK was built),
   stream at 7000, game inactive, banner cleared, samplers stopped.

## Record and memory

`evidence/C5_M1_1080P60_PROFILE_<date>.md` (the design with its numbers,
the offline encoder result, the profile as built, the smokes, the six
holds in the close-out table shape, the rule outcome and its
classification, what adoption would mean — a capability gate in the
profile/status contract, the user's call); evidence dir with the design,
offline encoder logs, harness, reports, heartbeats, thermal jsonl,
manifest; `patches/C5-M1_*.md` with per-file SHA-256s; `PATCH_INDEX.md`;
`decisions/C5_1080P60_CAPABILITY_<date>.md` (outcome; adoption pending
the user); `docs/ROADMAP.md` C5 and C7 lines; `docs/PROJECT_STATUS.md`;
`CURRENT.md`; `investigations/ACTIVE.md`; `TOOLS.md` (the selector; never
leave it set); the daily file; `evidence/RUNTIME_VALIDATION.md`. No
addresses or device identifiers. Nothing adopted. Nothing committed.
