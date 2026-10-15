---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S5B, queue item 2: exercise the SNES capture fix (`PRIVYHUB_SNES_CAPTURE_FIX=output_rate`, E4-S5 §3) on the case it exists for — a bad input-rate probe — which E4-S5's two flagged runs never met (every probe read 60). The probe is chance per encoder start, so sample it often: a bench of 60-s encoder sessions, many of them, with and without the flag, beside one live SNES-STREAM. Host-side bar only; the link is not involved. Plus PS1-STREAM ×1 with the flag (the flag applies to every x11grab session). Nothing adopted; nothing committed
---

# E4-S5B — the SNES capture fix on bad probes

**What E4-S5 established.** ffmpeg estimates the x11grab input's frame
rate from its first frames ("tbr"); for the 897×672 SNES window the
estimate is 60 in most sessions, 59.94 in some, 59 in a few. With no
output rate set, the encoder adopts the estimate for the whole session
and drops the surplus input frames: tbr 59 → exactly one drop per second
(the fault), 59.94 → one per ~16 s, 60 → none. 20 sessions so far: 4 bad
(2 × 59, 2 × 59.94) plus a 19-s 59 segment in E4-S5 run3. The fix adds
`-r <profile fps>` to the encoder's output. Under the flag, E4-S5's two
20-min runs showed 0 drops — but both probes read 60, so the fix was
never tested on the case it exists for. One probe per encoder start:
long sessions sample it rarely; short sessions sample it often.

Read first: `evidence/E4_S5_SNES_CAPTURE_59FPS_2026-10-10.md`,
`e4_s5_2026-10-10/offline.md`, `segments.txt`, `e4_s5_change.diff`,
`e4_s5_sidecar.py` (how the header's tbr and output rate were read),
`companion/native_stream.py` (the command builder, the E4-S5 block).

## 1. The bench (pre-registered, hashed before it)

- **Setting:** one live E1-SNES-STREAM session (the suite, no flag for
  the companion's own encoder; window long enough to hold the bench,
  ~75 min; its own metrics reported, not gated). Beside it, a bench
  script (`e4_s5b_bench.py`, in the task's directory) runs the encoder
  command **exactly as the companion builds it** — the builder imported
  with the environment set or unset, nothing retyped — against the same
  RetroArch window, each session **60 s**, output to `-f null -` (no
  file, no socket; the mechanism is encoder-internal: probe → output
  rate → drops). As E4-S5's sidecar did, a second x11grab beside the
  companion's is the precedent.
- **Arms, interleaved** (A B A B …): **A** = the command without the
  flag; **B** = with `PRIVYHUB_SNES_CAPTURE_FIX=output_rate`. **24
  sessions per arm** (48 × ~70 s ≈ 1 h). Per session: the header's probed
  tbr, the output rate, the final `drop` and `dup` counters, frames, wall
  time. `bench.jsonl`.
- **Reading rule, written before the data:** a session is a **bad
  probe** if its tbr ≠ 60. **The mechanism reproduces** if every bad-probe
  session in A has output rate = tbr and drops ≈ (60 − tbr) × 60 ± 20 %.
  **The fix works** if every bad-probe session in B has output rate 60
  and drops ≤ 2 in the minute. **Sampled enough** if arm B holds ≥ 3
  bad-probe sessions; if not after 24, continue to 48 per arm; if still
  < 3, INCONCLUSIVE (the probe did not misread tonight) — the bad-probe
  rate per arm is reported either way.
- **Bar, ACCEPTED only if all hold:** sampled enough; the mechanism
  reproduces in A; the fix works in B; and the live session's
  companion-side metrics are host-clean (RetroArch ≥ 59.9, host CPU
  within E1's band of E4-S1's SNES 7.4 % + the bench's own cost,
  reported separately). REJECTED if any bad-probe B session drops > 2 or
  outputs ≠ 60. The link (loss, rendered fps) is **reported, not
  gated** — the fix does not touch it.

## 2. PS1-STREAM with the flag (after the bench)

The flag applies to every x11grab session. **E1-PS1-STREAM ×1 at 20 min
with the flag** (the 1920×1080 window probes "1000k tbr" and already
falls back to 60): capture 60 ± 0.1, dup+drop ≤ 0.2/min, RetroArch ≥
59.9, host CPU within E1's band of E4-S1's PS1-STREAM 10.9 % — i.e. the
flag changes nothing for PS1. Gated host-side; the link reported.

## 3. The record

`evidence/E4_S5B_SNES_CAPTURE_PROBE_BENCH_<date>.md` + `e4_s5b_<date>/`
(the bench script, the pre-registration + `.sha256`, `bench.jsonl`, the
bench table per arm (sessions, bad probes, output rates, drops), the live
session and the PS1 run, `manifest.sha256`, `--check`, `validity.json`,
verdict, `redact_check.txt`); `docs/KNOWN_ISSUES.md` (the fault: fix
verified / not); **if ACCEPTED, the one-line adoption** (a drop-in
`snes-capture.conf`, `Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`)
and its revert, written, not applied; `patches/` if a tool changed;
`logs/e4_s5b_git_status.txt`. Flag absent; the adopted state restored;
then queue item 3.
