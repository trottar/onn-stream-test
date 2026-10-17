# G8-S2 — the start rung: the design (written before the code)

Baseline `80f3fc4`. Session B, unattended. Task: `handoffs/G8-S2_START_RUNG_TASK.md`.
Session A's LAN smoke had exited: `G5_S3_LAN_SMOKE_2026-10-17.md` present, no
`e3_flag.conf`. Its uncommitted files are not touched.

Read before writing:
- G8-S1 final record: §5 (cap cells) and §2c;
- G8-P1 §2 and `proof.py`;
- `companion/native_stream.py`: `start` → `_start_linux_locked` →
  `_build_linux_ffmpeg_command`, `_stop_locked`, `status`;
- `adaptive_bitrate_live.py`: the reset at a session start, `level_sync`, the
  increase rule;
- `native_fec_relay.py`: a parity group flushes at 8 packets or at a frame's
  marker;
- G5-S3 / G5-S4's modules.

## 0. Where the session's first target is chosen (from the code)

The ladder does not choose it. Every stream start (`NativeStreamManager.start`)
does two things:

- `_stop_locked()` resets `_active_bitrate_kbps` to the profile's `BITRATE_KBPS`
  (7000);
- `_start_linux_locked` builds the encoder argv with
  `_build_linux_ffmpeg_command(ffmpeg, capture_target)`, defaulting to 7000.

The ladder then *follows* the stream:

- at the session's release, `session_ended` resets the policy to 7000;
- the first report's `level_sync` adopts whatever `status().bitrate_kbps`
  (= `_active_bitrate_kbps`) says.

So the first target is chosen at that one argv call, and that is where the hook
goes.

## 1. The flag and the module

**`PRIVYHUB_START_RUNG=<floor|cap|kbps>`**, parsed by a new module
`companion/start_rung.py`. One shared instance per process.

- **Absent or empty:** today, byte for byte. No import, the same argv call,
  `_active_bitrate_kbps` 7000, no row.
- **The active list,** decided at each start from the start's own client target:
  - **remote:** G5-S3's flag set **and** the target overlay-class under G3's
    overlay test (`remote_ladder.routing_evidence_of`, the same function G5-S3's
    plugin hook uses) → `4000 / 5000 / 5500 / 6000 / 7000`;
  - **otherwise:** the ladder's validated list, `5000 / 5500 / 6000 / 7000`.
  - Classifying here is needed because G5-S3's plugin hook runs *after* the
    stream has started.
- **The values:**
  - `floor` → the lowest rung of the active list (5000 on the LAN, 4000
    remote).
  - `cap` → G5-S4's cap when it is active and the path is remote (where G5-S4
    applies); otherwise `floor`, with the source saying so.
  - `<kbps>` → that rung if it is in the active list. A number outside the list
    is logged once and falls to `floor`.
  - **Anything else is invalid:** logged once and ignored, so the start is
    today's 7000.
- **Logged once** means one line on the companion's stdout (its journal) per
  distinct problem.
- **The encoder argv:** a start rung below 7000 calls
  `_build_linux_ffmpeg_command(..., bitrate_kbps=r, max_bitrate_kbps=r)`.
  - That is exactly the ladder's own transition argv for that rung (`-b:v /
    -maxrate / -bufsize` at r).
  - `_active_bitrate_kbps` is r.
  - A chosen 7000 makes the argv call **unchanged**.
  - Nothing else in the encoder changes (size, GOP, frame cap, FEC).
- **Every start.** It applies to every `native_stream.start`, recovery's full
  start included (C1 said a full start resets to 7000; with the flag it resets
  to the start rung).
  - Disclosed, and unchanged: the ladder's escalation bookkeeping labels a full
    start's level 7000 (`note_ssrc_change`). It is not edited ("nothing else in
    the ladder").

## 2. The hooks (each a guarded `if`, a patch)

1. **`native_stream.py`:**
   - a module global `START_RUNG`, built only under the flag, with the import
     inside the `if`;
   - in `_start_linux_locked`, at the first-target argv call: `start_kw = {}`;
     `if START_RUNG is not None:` the chosen rung's kwargs, and
     `_active_bitrate_kbps` set;
   - then `_build_linux_ffmpeg_command(ffmpeg=…, capture_target=…, **start_kw)`.
2. **The record, `adaptive_bitrate_live.py`:**
   - a module global `START_RUNG`;
   - in `LiveController._write`, `if START_RUNG is not None: base =
     START_RUNG.annotate(base)`.
   - It puts the start rung, its source (`floor` / `cap` / `value` /
     `cap→floor` / `value→floor` / `invalid→today` / `absent`), the requested
     value and the active list on **the session's first `sample` row after each
     stream start**: the session's first decision-log row of substance. Every
     later row is as today.
   - **Disclosed:** the start (in the native stream) does not write the ladder's
     log, so recording it in the session's rows needs this second guarded `if`.
     It annotates only; no decision changes.
   - **Note:** a run's `decisions.jsonl`, as the suite extracts it (the window,
     after the warm-up), will not hold that row. It is in the ladder's log.

No change to the ladder's increase / decrease rules, the hold-downs, the FEC, the
frame cap, or the client.

## 3. The climb (arithmetic from the ladder's constants, not a result)

**The per-step timing:**
- At a session start the increase window is empty.
- An increase needs the window full (90 evaluated reports) with ≥ 85 clean, and
  60 s of session age.
- After each increase come the blackout (3 reports) and an empty window again
  (90). The `INCREASE` hold-down (30) is shorter.
- **So, on a clean link where every report is clean:** the first step comes at
  report 90, each next one 93 reports later. Reports are 2 s apart.

| start | steps to 7000 | reports | time |
| --- | --- | --- | --- |
| 5000 (LAN floor) | 3 | 90 + 93 + 93 = 276 | 552 s ≈ 9.2 min |
| 4000 (remote floor) | 4 | 90 + 3 × 93 = 369 | 738 s ≈ 12.3 min |
| 4000 remote, G5-S2's rules on | 4 | R5 needs 36 consecutive clean 5-report windows (180 reports) before the first step; then 93 per step → 180 + 3 × 93 = 459 | 918 s ≈ 15.3 min |

The rate limit (4 transitions in 10 min) does not bind on either climb. A
non-clean report or a decrease restarts the count.

## 4. The wire arithmetic (written before the proof)

**The ratio.** G8-S1's steady shim input at 7000 was 8.25-8.30 Mbit/s: video
plus FEC 8+1 parity. The shim carries the video hop only; audio is not on that
hop, so the task's "and audio" does not apply to this ratio. The ratio is
8.25 / 7.0 ≈ **1.179**, applied to each rung. The expected tail-dropped fraction
under a cap C is 1 − C / input when the input is above C.

| rung | wire (×1.179) | under cap-6000 | under cap-4500 |
| --- | --- | --- | --- |
| 7000 (today) | 8.25 | over by 37.5 % → drop ≈ 27 % (G8-S1: 0.27) | over by 83 % → drop ≈ 45 % (G8-S1: 0.44) |
| 6000 | 7.07 | over → drop ≈ 15 % | drop ≈ 36 % |
| 5500 | 6.48 | over → drop ≈ 7 % | drop ≈ 31 % |
| 5000 | 5.89 | **under → drop ≈ 0** | drop ≈ 24 % |
| 4000 | 4.71 | under → drop ≈ 0 | **over by ≈ 4.8 % → drop ≈ 4.5 % ("about 4 %")** |

**So `cap-4500` is not expected to pass even at 4000.**

- The floor still sits about 4 % over the cap. That is a finding about the floor
  (the rung list ends at 4000), not a bug to hide.
- **A second prediction from a measurement:** C5-M3 measured video + parity at
  4000 as 4.06 + 0.77 = **4.83 Mbit/s**, which predicts a drop of about 6.8 %.
- **The model behind the ratio:** frames whose last packet is partial, and a
  parity packet per group of up to 8, flushed at each frame end. With it, the
  ratio is not exactly constant across rungs, so the proof measures the input
  rather than assuming it.
- **Predicted:** 5000 under cap-6000 drops about 0; 4000 under cap-4500 drops
  about 4-7 %.
- **No claim about PLAYING:** whether a client decoder starts under a few
  percent of tail drop is the live test's (G8-S3).

## 5. The proof (no stream)

- **Unit tests** `tests/start_rung/`:
  - the flag: absent / empty / `floor` / `cap` with and without G5-S4 (and
    G5-S4 on the LAN) / a value in and out of the list / invalid text / 7000;
  - LAN vs remote lists (G5-S3 on and off, an overlay-class and a LAN target);
  - the argv: 7000's unchanged, a rung's equal to the ladder's transition argv
    for it;
  - `_active_bitrate_kbps` and `status().bitrate_kbps`;
  - the annotation on the first sample row after a start, once;
  - logged once;
  - the guarded imports (AST).
- **Flag absent, byte for byte:**
  - the first-target handler comparison: HEAD's vs the edited
    `_start_linux_locked`, with the same stubs, for a LAN and an overlay target
    (the argv, `_active_bitrate_kbps`, the payload, every stub call);
  - HEAD's vs the edited controller rows (G5-S2's replay);
  - G5-S2's and G5-S3's replays re-run identical.
- **In process, against the shim's cap profiles.** G8-P1's proof is extended:
  the real `NativeVideoFecRelay` → the shim `@post-fec` → a capture playing the
  client.
  - The cases: cap-6000 and cap-4500 × starts of 7000 / 5000 / 4000.
  - Two sources:
    - (a) synthetic frames at the rung's encoder rate, 60 fps;
    - (b) **the real encoder's recorded start**, from the evidence tree:
      `c3_l4_nft_night3_2026-09-30/frames.jsonl` (the stream start at
      13:15:23Z) and `c3_l4_nft_night1_2026-09-29/frames.jsonl`'s first start.
      Both are per-second aggregates (frames, packets, payload bytes, the
      largest frame and its time). They are re-timed into frames: the largest
      at its recorded instant, the rest evenly. They are scaled to the rung by
      rung / 7000 (the encoder is CBR), which is an assumption. They hold no
      per-frame series.
  - Tabulated:
    - the shim's input and output kbps;
    - the tail-dropped fraction (whole run, and steady after 2.5 s);
    - FEC recovered / unrecoverable groups;
    - post-FEC loss;
    - complete frames;
    - G5-S1's window classes.
  - No claim about PLAYING.
- **The replay:** G4-S1 runs 1-2 (remote) and G8-S1 cells 6, 7, 12 (LAN) with
  `floor`, run with G5-S3's controller harness at the floor start. Reported: the
  start rung, when the ladder climbs, and where it would be at each cell's first
  rules action (the recorded first acted transition). Open loop on the recorded
  reports; **no claim of improvement.**
- The suites green; the redactor.

## 6. Proposed next (not run here)

**G8-S3:** the four cap cells re-run with `PRIVYHUB_START_RUNG=floor`, and once
with `=cap` (cap 4000 under cap-4500), using G8-S1's driver scaffolding, about
1 h. Session A's.
