---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G8-S4 (session B, unattended, after G4-S2 Part 2 has exited): the encoder's per-second rate control behind a flag, so a rung's wire rate stays near its target second by second — G8-S3 §3 showed the 5000 rung averaging 6,039 kbit/s on the wire but swinging to 7.9 Mbit/s payload in single seconds (52 % of seconds over target), which a cap near the mean tail-drops at 6.75 %. Proved offline with ffmpeg on the host against a file source; no stream, no restart. The live test is a later session-A task (G8-S5: G8-S3's cell 1 repeated with the flag)
---

# G8-S4 — the encoder's rate headroom

Read first: `G8_S3_CAP_CELLS_START_RUNG_2026-10-17.md` §3 (the per-second payload distribution at the 5000 target: mean 5,012, p95 5,944, max 7,886; the shim input p95 6,989, max 9,422; the per-second drop p95 23 %), `companion/native_stream.py` (the encoder command: the VAAPI H.264 options as adopted — `-b:v`, any `-maxrate` / `-bufsize` / `rc_mode`, the GOP, the 90,000-byte frame cap of D-BASE-P6), `D_BASE_P6_…` / `P6A_…` (why the frame cap exists and what it was measured against), `E4_S5B_…` (the masked-hash method for "the encoder command byte for byte"), `C3_L4_…` (how the ladder changes the encoder's rate live — the actuator's `-b:v` transition — so the new options follow a rung change).

## 1. The design (in the record §1 before the code, hashed)

- **The flag:** `PRIVYHUB_ENCODER_RC=<profile>` with named profiles in a table in the module and the record — at least `tight` (per-second output held near the target: `-maxrate` = target, `-bufsize` = target × 0.25 s or the VAAPI equivalent `rc_mode` that the host's driver accepts — read `ffmpeg -h encoder=h264_vaapi` on the host and state what it offers) and `headroom` (the same with `-maxrate` = target × 1.10). Absent → today's command, byte for byte (the masked-hash method). Invalid → logged once, ignored.
- **The actuator:** when the ladder changes the rung live, the rate options follow the new target the same way `-b:v` does today; say exactly where in the actuator that happens and that it is inside the same `if`.
- **Not in this task:** the frame cap (stays), the GOP, the preset, the FEC, the client. Nothing is adopted.

## 2. The proof (offline, on the host, no stream)

- **A file source:** the best available recording of real game content in the tree (say which; if none, ffmpeg's `testsrc2` plus `mandelbrot` at 1280×720/60 as a stand-in, stated as a limit) encoded through the **same VAAPI encoder and the same command builder** at targets 4000 / 5000 / 7000, 60 s each, flag absent and each profile: the per-second output bitrate distribution (mean, p95, max, share of seconds over target and over target × 1.10) — a table. The flag-absent row must reproduce G8-S3's shape (p95 well above the mean) or the source is not representative — say so.
- **Through the shim's cap profiles, in process** (G8-S2's harness): the encoded streams at 5000 under cap-6000 and at 4000 under cap-4500, flag absent vs `tight` vs `headroom`: the drop fraction per second (median, p95) and overall. No claim about PLAYING or picture.
- **Picture cost, measured not judged:** PSNR/SSIM of each profile against flag-absent at the same target (ffmpeg's `psnr` / `ssim` filters) — a number, no verdict.
- **Host cost:** the encoder's CPU over the 60-s encodes, flag absent vs profiles.
- Unit tests (parsing, the command builder with and without the flag, the actuator's follow-through); the suites green; the redactor.

## 3. The record

`evidence/G8_S4_ENCODER_RATE_HEADROOM_2026-10-17.md` + `g8_s4_2026-10-17/` (design + hash, the diff, the tables, the test output, `redact_check.txt`, `manifest.sha256`); `patches/G8-S4_…md`; ROADMAP §G8 ("rate headroom built behind a flag; live test pending"); `logs/g8_s4_git_status.txt`. **Proposed next (not run):** G8-S5 — G8-S3's cell 1 (cap-6000, 5000 start) repeated with each profile, ~30 min, the drop fraction and rendered fps against G8-S3's. Then `SESSION_B_DONE_2026-10-17C.md` (ten lines).

Rules as QUEUE_2026-10-17's hard rules, plus: **any recorded run used for a replay or a proof is copied into the evidence directory first** (the ladder's log rotates — G8-S2's disclosure); ffmpeg runs on files only, never on the display, never with the companion's ports; nothing in `logs/` is written by tests. No sudo, no nft, the Opal read-only, no addresses; nothing fetched, nothing deleted; nothing adopted; nothing committed.
