# G8-S4 — the encoder's rate headroom: the design, written before the code

Session B, 2026-10-18, baseline `1fc2e19`, after G4-W1 and G4-W2. Hashed before the
first G8-S4 code edit. (The task file is dated 2026-10-17; its record is written
under today's date, 2026-10-18, as this queue runs it.)

## 0. What exists (read before this design)

- **The command builder** (`native_stream._build_linux_ffmpeg_command`):
  `-c:v h264_vaapi -profile:v high -b:v T -maxrate M -bufsize B [-max_frame_size 90000]
  -g 15 -bf 0`.
  - At a start, T = M = the profile's 7000 (or G8-S2's rung).
  - **B = M**, unless the diagnostic `PRIVYHUB_ENC_BUFSIZE_K` is set.
  - No `-rc_mode`, so ffmpeg's `auto` applies. The driver logs (verified on the host
    with a 1-s testsrc2 encode): **"RC mode: CBR. RC target: 100 % of T over 1000 ms.
    RC buffer: T bits, initial fullness 3/4."**
  - Today is therefore CBR with a **1-second** VBV window. Within a second a frame can
    run far over the per-frame share, which G8-S3 saw: at 5000 the per-second payload
    had p95 5,944, max 7,886, and 52 % of seconds over target.
- **The live actuator** (`diagnostics/c3_linux_actuator_probe.py`, reached through
  `adaptive_level_transition` → `diagnostic_c3_validated_bitrate_transition` or
  `run_c3_linux_level_transition`):
  - it is an encoder-only restart;
  - **every replacement argv comes from the same `_build_linux_ffmpeg_command(...,
    bitrate_kbps=target, max_bitrate_kbps=target[, width, height])`.**
  - G8-S2's start rung uses the same call.
  - So one hook inside the builder covers the start, every live rung change, and the
    sized 1080p rung.
- **The host's encoder** (`ffmpeg -h encoder=h264_vaapi`):
  - `-rc_mode auto | CQP | CBR | VBR | ICQ | QVBR | AVBR`, `-blbrc`, `-max_frame_size`,
    `-quality`, `-low_power`, `-async_depth`;
  - **the driver (Mesa radeonsi, renoir) supports CQP, CBR and VBR only** ("Driver does
    not support QVBR / AVBR RC mode (supported modes: CQP, CBR, VBR)");
  - VBR logs "RC target: b:v / maxrate % of maxrate over bufsize / maxrate ms".

## 1. The flag and the profiles

`PRIVYHUB_ENCODER_RC=<profile>`.

- **Absent (or empty) → today's command, byte for byte.** The module is not imported.
- **Invalid → logged once and ignored** (today's command).

| profile | `-rc_mode` | `-b:v` | `-maxrate` | `-bufsize` (VBV) | driver window |
| --- | --- | --- | --- | --- | --- |
| (absent) | auto → CBR | T | T | T (1 s) | 1000 ms |
| **`tight`** | **CBR** | T | **T** | **T × 0.25** | **250 ms** |
| **`headroom`** | **VBR** | T | **T × 1.10** | **T × 0.25** | ~227 ms (0.25 T / 1.1 T), target 91 % of maxrate |

- Values are integers in kbit (rounded), so 5000 gives tight `-maxrate 5000k -bufsize 1250k`
  and headroom `-maxrate 5500k -bufsize 1250k`.
- `-rc_mode` is inserted right after the `-bufsize` value. Nothing else in the argv
  moves.
- **Stays as it is:** `-max_frame_size 90000` (the frame cap of D-BASE-P6 / P6a), the
  GOP, `-bf`, the profile, the filter, the sink.
- The 90,000-B cap is 720 kbit, under the tight VBV at every rung ≥ 2,880 (4000 →
  1,000 kbit).
- When the flag's profile is valid, it **owns** `-maxrate` and `-bufsize`. The diagnostic
  `PRIVYHUB_ENC_BUFSIZE_K` is then overridden by the profile, and the module logs that
  once if both are set.

**The hook:** one `if` at the end of `_build_linux_ffmpeg_command`, before the E4-S5
`-r` insertion and the `return`:
`if ENCODER_RC is not None: command = ENCODER_RC.apply(command, target_bitrate_kbps)`.

- Because the actuator builds every replacement argv with this function, **the rate
  options follow a live rung change inside that same `if`.** The profile is computed
  from each call's own `target_bitrate_kbps`.
- The guarded import is one module global, `ENCODER_RC`, as G8-S2 did for its flag.

**Not in this task:** the frame cap, the GOP, the preset, the FEC, the client, the
ladder. Nothing is adopted.

## 2. The proof (offline, on the host, no stream)

- **The source:** `runtime/c5_m3/reference.mkv`. It is C5-M3's 60-s lossless x11grab of
  the attract title through the companion's own scale/pad: 1280×720, 3,600 frames,
  sha256 `2df8ffe5…dd4e`. It is real game content, an attract sequence rather than play
  (a limit). It stays where it is (120 MB, outside git); its hash is recorded.
- **The encodes.** The command comes from the companion's own builder, on G8-S2's stub
  manager (adopted profile, cap 90,000), with the flag absent / `tight` / `headroom` at
  targets 4000 / 5000 / 7000: 9 encodes of 60 s each, through `h264_vaapi` on the host's
  render node.
  - **The only edits to the built argv:** the x11grab input
    (`-f x11grab -framerate 60 -window_id W -i :D`) becomes `-i reference.mkv`, and the
    RTP sink (`-payload_type 96 -f rtp rtp://…`) becomes `-f matroska <file>`.
  - Each edited argv is hashed with the window, display, device and paths masked
    (E4-S5B's method). The unedited builder output is hashed the same way.
  - ffmpeg runs on files only, never on the display, never with the companion's ports.
- **Per encode:**
  - the per-second output (packet sizes by pts, `ffprobe`): mean, p95, max, the share of
    seconds over T and over T × 1.10;
  - the largest frame;
  - ffmpeg's CPU (user + sys of the child): the whole process, decode of the lossless
    source included, against a decode-only baseline (the same input and filter without
    hwupload or encode, to `-f null`).
- **Representativeness:** the flag-absent row must show G8-S3's shape (p95 well above
  the mean; G8-S3 live at 5000: p95 / mean 1.19, max / mean 1.57). Otherwise the source
  is not representative, and the record says so.
- **Through the shim, in process:** G8-S2's harness (the real `NativeVideoFecRelay` →
  `RelayShim` @post-fec with no log file → a loopback capture). The frames are the
  encodes' own per-frame sizes and pts, packetized at 1,188 B.
  - Cells: **5000 under cap-6000** and **4000 under cap-4500**, each flag absent / tight /
    headroom, 60 s each, in real time.
  - Reported: the overall tail-dropped fraction, and the per-second drop fraction (median,
    p95). **No claim about PLAYING or the picture.**
- **Picture cost, measured not judged:** PSNR and SSIM (`ffmpeg -lavfi psnr`, `ssim`) of
  each profile's encode against the flag-absent encode at the same target, and of every
  encode against the lossless reference. Numbers only.
- **Unit tests** in `tests/encoder_rc/`:
  - parsing and invalid values;
  - the builder with and without the flag, at each target, with the sized rung;
  - the actuator's follow-through (the real `run_c3_linux_validated_bitrate_transition`'s
    argv on a stub manager, if it can be driven offline; otherwise the builder call it
    makes, asserted by AST);
  - the guarded import.
- **Flag absent:** HEAD's builder vs today's over the targets 4000 / 5000 / 5500 / 6000 /
  7000, the sized 12,600, and `PRIVYHUB_ENC_BUFSIZE_K` set → identical argv (masked
  hash). The start handler is identical too (G8-S2's stub manager).
- **Expected (written now):**
  - `tight` cuts the per-second p95 and the max toward T. The share of seconds over T
    drops from ~50 % (CBR averages to T, so some seconds still exceed it), and the share
    over 1.10 T drops to near 0.
  - `headroom` sits between.
  - The shim's drop at 5000 / cap-6000 falls from G8-S2's 1.8-2.4 % bench toward 0 with
    `tight`.
  - PSNR against flag-absent lands around 35-45 dB; SSIM a little lower than flag-absent
    against the reference, because the tight VBV starves I-frames under the 15-frame GOP.
