---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
durable_memory_updated: true
---

# D-BASE-P6a — the 90 KB frame cap becomes a profile field

## Purpose

`D-BASE-P6` measured the cap and `D-BASE-P6` plus the user's own
perceptual check decided it. This patch **adopts** it: the cap stops being
an environment override and becomes a declared parameter of the reference
profile, so the `h264_vaapi` argv carries `-max_frame_size 90000` with
nothing set in the environment.

One coherent product change. No other encoder flag, no pacing, no FEC, no
client change.

## Changed scope

**`companion/native_stream_profiles.py`**
-> `cd8b95cd9ded9a7b1a257ccaef372b7cf7a54a150775018c5510a68e8de8ddc5`
(was `3d9f2400770a801603d8da5c943fb547e05a217fd2e52854c214d74a3004de68`).

- `NativeStreamProfile` gains **`max_frame_size_bytes: int = 0`**, with 0
  meaning uncapped, validated `>= 0` in `__post_init__` and carried in
  `to_dict()`. The default of 0 means any profile that does not declare it
  behaves exactly as before.
- `NATIVE_GAME_720P60_REFERENCE` declares **90,000**.
- The field's docstring records *why* it is a profile parameter rather than
  a tuning knob: the loss on this link is a per-frame micro-burst meeting
  the wireless queue, the burst is the frame, so the cap is a transport
  parameter wearing an encoder's clothes. It also records that **only the
  `h264_vaapi` builder honours it.**

**`companion/native_stream.py`**
-> `84e08aac9c2514a01aba5ad61e63829385cf41b27333590efd61a10f43eda28f`
(was `21874eefc66692b44f313bb25d3fd1a297ab30138a5b0ffb5f5ec63c01e1e9f3`).

- **`_env_int_or_none()`** beside the existing `_env_int()`. The old helper
  folds "unset" and "0" into the same answer, and `P6a` needs them apart:
  **`PRIVYHUB_ENC_MAX_FRAME_SIZE=0` must run uncapped** so the `P6`
  baseline can be re-run at any time. None means unset or unparseable.
- **`_effective_max_frame_size()`** returns `(bytes, source)` — the
  override when one is set, otherwise the profile. One place decides, and
  both the argv builder and the status block read it.
- `_build_linux_ffmpeg_command` takes the cap from that helper instead of
  from the environment directly. At 0, from either source, the flag is
  absent and the argv is byte for byte the pre-`P6` command.
- **`encoder_overrides()` changed meaning and says so.** `any_override` is
  now **false when only the profile is in force** — that is the "default is
  in force" reading from now on — and true only when a variable is actually
  set, *including* `=0`. New fields: `default_max_frame_size_bytes`,
  `uncapped`, `max_frame_size_env`; `max_frame_size_source` now reports
  `profile` or the variable's name rather than always the variable's name.
- **`_build_ffmpeg_command` (Windows NVENC, deferred) ignores the field**
  and emits one log line saying so. NVENC has a different rate-control
  vocabulary and there is no measurement behind a translation, so it is not
  translated.
- **`_log_line()`**, a small helper for the few notices that belong with
  the encoder's own output. Swallows errors: a log that cannot be written
  must not stop a stream starting.

## Validation

**`evidence/d_base_p6a_2026-09-22/test_profile_cap.py`** — 10 groups over
the real builder, no socket and no thread. The three source states (unset →
profile, set → override, **`=0` → uncapped with the flag absent**); the
uncapped argv differing from the capped one by **exactly the two flag
tokens**; malformed, negative and zero-profile cases; `-bufsize` untouched;
and a negative profile value rejected at construction. **All pass**, and
the `P5`/`P6` relay suites still pass unchanged.

**Runtime**: one 20-minute session with **no `PRIVYHUB_ENC_*` set**, all
ten pre-registered gates passed — frames >= 80 packets **0**, max frame
**89,874 B**, loss **249**, bitrate **6,929.6 kbps**, fps **59.90**, 0
resyncs, 0 socket drops, 0 send errors, encoder CPU **26.6 %**. Then one
60 s `=0` check producing a **90,438-byte** frame with the flag absent,
proving the uncapped path still runs. Record:
`evidence/D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`.

`git diff --check` clean. Python compiles.

## Not done

- **No client change**, no pacing change, no FEC change.
- **`-bufsize` untouched** at 7000k; `PRIVYHUB_ENC_BUFSIZE_K` unchanged and
  still default off (`P6` measured VBV and it was not adopted).
- **No other encoder backend changed** — NVENC logs and ignores.
- **Nothing committed**; the commit is the user's.
