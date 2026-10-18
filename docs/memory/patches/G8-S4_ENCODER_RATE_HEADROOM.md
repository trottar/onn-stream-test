---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: 1fc2e19
durable_memory_updated: true
---

# G8-S4: the encoder's rate-control profile, behind `PRIVYHUB_ENCODER_RC=<tight|headroom>`

## Purpose

G8-S3 measured the 5000 rung live with a mean of 5,012 kbit/s and single seconds up to 7.9 Mbit/s. A cap near the
mean then tail-drops. Today's encoder is CBR over a **1-s** VBV (`-bufsize` = `-maxrate` = target). With the flag, a
named profile narrows the window, so each second stays nearer the target. Record:
`evidence/G8_S4_ENCODER_RATE_HEADROOM_2026-10-18.md`.

## Change

- **New `companion/encoder_rc.py`:**
  - the profiles:
    - `tight`: `-rc_mode CBR -maxrate T -bufsize T×0.25`;
    - `headroom`: `-rc_mode VBR -maxrate T×1.10 -bufsize T×0.25`;
  - an invalid value is logged once and ignored;
  - `apply` rewrites `-maxrate` / `-bufsize` and inserts `-rc_mode` after the `-bufsize` value. Nothing else in the
    argv changes. The frame cap, GOP, `-bf` and sink stay as they are.
- **`companion/native_stream.py`:**
  - a module global `ENCODER_RC`, built only under the flag, with the import inside the `if`;
  - one `if` at the end of `_build_linux_ffmpeg_command`, which computes the profile from that call's own target.
  - The start, every live rung change and the sized rung all build their argv here, so they all follow the
    profile.
- **New tests:** `tests/encoder_rc/test_encoder_rc.py` (16).
- **Docs:** ROADMAP §G8 (the G8-S4 line).

## Validation

See the record:

- `tests/encoder_rc` 16 OK; the suites green (C3-F1's pre-existing error aside), run from a slim /tmp copy of the
  tree (companion/, tools/, tests/ only);
- flag absent: HEAD's builder and today's are identical over 7 targets × the bufsize override (masked sha256), and
  the start handler is identical;
- the offline encodes (9 × 60 s, the host's VAAPI on the C5-M3 lossless reference): `tight` at 5000 p95 5,605 →
  5,298 kbit/s, max 5,976 → 5,535, seconds over 1.10 T 11.7 % → 1.7 %; `headroom` runs ~8.5 % over T on busy seconds;
- the shim cells (real FEC sender → RelayShim, in process): 5000 @ cap-6000 tail drop 4.67 % → 3.42 % (`tight`),
  8.72 % (`headroom`); 4000 @ cap-4500 9.86 % → 8.78 % / 14.34 %;
- PSNR / SSIM: `tight` −0.45 dB avg, −2.4 to −3.4 dB min at 4000 / 5000 against the lossless reference;
- CPU: no measurable difference (±0.3 s of ~10 s per 60 s).

## Result

BUILT behind the flag; NOT ADOPTED; unvalidated live (G8-S5 is the proposed live test); nothing committed.
`PATCH_INDEX.md` was not updated (not session B's file).
