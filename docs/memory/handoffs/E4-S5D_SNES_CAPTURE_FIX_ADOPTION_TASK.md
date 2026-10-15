---
memory_schema: 1
as_of: 2026-10-15
status: TASK HANDOFF — E4-S5D, session A item 1: ADOPT the SNES capture fix. The user's decision (2026-10-15) on E4-S5 (cause located: ffmpeg's x11grab input-rate probe sets the output rate), E4-S5B (4/4 bad probes under the flag output 60, 0 drops; the companion's own encoder dropped on bad probes live) and E4-S5C (with the companion's sink mode: 59 → 58 drops, 59.94 → 2, the flag → 0 at every bad probe). The fifth adopted line. One 20-min SNES-STREAM on the adopted state confirms it
---

# E4-S5D — adopt `PRIVYHUB_SNES_CAPTURE_FIX=output_rate`

Read first: `evidence/E4_S5C_…`, `E4_S5B_…` §3 (the adoption line as
written there), `E3_A3B_…` (the last adoption's record shape),
`tools/e3_state.py` (the `ADOPTED` list).

## 1. The adoption

- Precondition: the four-line adopted state, no flag, no constraint, no
  game (`precondition.json`).
- Write `~/.config/systemd/user/privyhub-companion.service.d/snes-capture.conf`:
  `[Service]` / `Environment=PRIVYHUB_SNES_CAPTURE_FIX=output_rate`.
  `systemctl --user daemon-reload`, restart the companion; read back the
  unit's environment: **five** `PRIVYHUB_*` lines (live, cached, snes9x,
  v2, output_rate). `tools/e3_state.py`'s `ADOPTED` list gains the name;
  `--check` passes on the new state. The revert, written in the record:
  delete the drop-in, `daemon-reload`, restart.
- The kill switch is the drop-in's absence; no code changes.

## 2. The confirmation run (host-side gates; the link reported)

**E1-SNES-STREAM ×1 at 20 min** on the adopted state, E2's warm-up, the
sidecar-free suite: the encoder's command carries `-r 60` (from the
companion's log, the header line); every encoder start's probed tbr
reported; **capture 60.0 ± 0.1 over the window, dup+drop ≤ 0.2/min,
RetroArch ≥ 59.9, host CPU within E1's band of E4-S1's SNES 7.4 %**.
Loss and rendered reported, not gated (the link). If a gate fails:
revert, say so, stop — the user decides.

Then **E1-PS1-STREAM ×1 at 10 min** (`--window 600`): capture 60.0 ± 0.1,
dup+drop ≤ 0.2/min — the flag changes nothing for PS1 (E4-S5B showed it).

## 3. The record

`evidence/E4_S5D_SNES_CAPTURE_FIX_ADOPTION_2026-10-15.md` +
`e4_s5d_2026-10-15/` (the drop-in's text, the environment read-back
before and after, the two runs with `manifest.sha256`, `--check`,
`validity.json`, `redact_check.txt`); `docs/KNOWN_ISSUES.md` (the SNES
59-fps fault: FIXED, adopted); `logs/e4_s5d_git_status.txt`. **The final
state is the five-line adopted state** — the watch (session A item 2)
runs on it. Not committed (the user commits tonight).
