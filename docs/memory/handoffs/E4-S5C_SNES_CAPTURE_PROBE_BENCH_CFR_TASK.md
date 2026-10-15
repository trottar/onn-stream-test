---
memory_schema: 1
as_of: 2026-10-10
status: TASK HANDOFF — E4-S5C, queue item 1: E4-S5B's bench, re-run with the one thing it got wrong fixed — the sink. E4-S5B sent the bench's output to `-f null`, whose default frame-rate mode passes frames through, so the no-flag arm could not drop and the "mechanism reproduces" clause was unjudgeable. The companion's rtp sink is constant-frame-rate and drops. Same bench, the sink in constant-frame-rate mode. Host-side bar; the link not involved. Nothing adopted; nothing committed
---

# E4-S5C — the SNES capture fix on bad probes, the bench with the right sink

**What E4-S5B left.** Under the flag, 4 bad probes (59 ×1, 59.94 ×3) all
output 60 with 0 drops. Without the flag, the one bad probe (59.94) output
59.94 — the probe was adopted — but dropped nothing, because `-f null`
without `-r` is pass-through. The companion's own encoder beside the
bench (rtp, no flag) met a 59 and a 59.94 probe and dropped as E4-S5
described (2.25 dup+drop/min over the window); `vsync_check2.sh` showed
the same on a synthetic source (59 → 58 drops in constant-rate mode, 0
with `-r 60`). So the only missing piece is the no-flag arm dropping on a
bad probe **in the bench itself**, with the companion's command.

Read first: `evidence/E4_S5B_SNES_CAPTURE_PROBE_BENCH_2026-10-10.md`,
`e4_s5b_2026-10-10/e4_s5b_bench.py`, `e4_s5b_preregistration.txt`,
`vsync_check2.sh` / `.txt`, `bench/bench.jsonl`.

## 1. Pre-registration (hashed before the bench)

- **The bench = E4-S5B's**, byte for byte, except the sink: `-payload_type
  96 -f rtp <relay>` becomes **`-fps_mode cfr -t 60 -f null -`** (ffmpeg's
  constant-frame-rate mode, the rtp muxer's default; `-vsync cfr` if this
  ffmpeg predates `-fps_mode`). State the ffmpeg version and which form
  was used. The command is otherwise the companion's own builder, flag
  unset (A) or set (B), hashed per arm with the window masked.
- **The setting:** one live E1-SNES-STREAM session as E4-S5B (~75 min, no
  flag for the companion's encoder; its own metrics reported). **24
  interleaved 60-s sessions per arm** (A B A B …); per session: probed
  tbr, output rate, final `drop` / `dup`, frames, wall time.
- **Reading rule (E4-S5B's, now judgeable):** bad probe = tbr ≠ 60.
  **Mechanism reproduces** if every bad-probe A session has output rate =
  tbr and drops ≈ (60 − tbr) × 60 ± 20 % (59 → 60 ± 12; 59.94 → 3.6 ±
  0.7, i.e. 3-4). **Fix works** if every bad-probe B session has output
  60 and drops ≤ 2. **Sampled enough** if **each arm** holds ≥ 3 bad
  probes; if either does not after 24, continue both arms to 48; if still
  not, INCONCLUSIVE with the bad-probe rate per arm.
- **Bar, ACCEPTED only if all hold:** sampled enough; mechanism
  reproduces in A; fix works in B; the live session host-clean (RetroArch
  ≥ 59.9; host CPU within E1's band of E4-S1's SNES 7.4 % net of the
  bench's cost, reported separately). REJECTED if any bad-probe B session
  drops > 2 or outputs ≠ 60. The link reported, not gated.
- **Reported:** the companion's own encoder starts during the live
  session (probe per start, its capture fps and dup+drop over the window
  — E4-S5B saw 11 starts, 2 bad), the bench's cost.

(No PS1 run this time: E4-S5B's PS1-STREAM with the flag passed and is
not in question.)

## 2. The record

`evidence/E4_S5C_SNES_CAPTURE_PROBE_BENCH_CFR_<date>.md` + `e4_s5c_<date>/`
(the bench script, the pre-registration + `.sha256`, `bench/bench.jsonl`
**with its own `manifest.sha256` + `check.txt`**, the bench table per
arm, the live session with `manifest.sha256`, `--check`, `validity.json`,
verdict, `redact_check.txt`); `docs/KNOWN_ISSUES.md` (the fault: fix
verified / not); **if ACCEPTED, the one-line adoption** (`snes-capture.conf`,
`Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`) and its revert,
written, not applied; `logs/e4_s5c_git_status.txt`. Flag absent; the
adopted state restored; then queue item 2.
