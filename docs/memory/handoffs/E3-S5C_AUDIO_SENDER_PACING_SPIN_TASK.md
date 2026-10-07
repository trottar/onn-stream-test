---
memory_schema: 1
as_of: 2026-10-07
status: TASK HANDOFF — E3-S5C, queue item 2 (the user's go, 2026-10-07: "2. One more task"): the audio sender pacing variant E3-S5B named — one timed wait to just before the packet's deadline, then today's short final spin — behind a new flag value, `PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`. Probe the send timing, then five interleaved E1-PS1-STREAM runs (C, F, C, F, F) under E3-S5B's bar with the CPU clause widened for the spin. Nothing adopted; nothing committed
---

# E3-S5C — the audio sender's pacing: one timed wait plus the final spin

**Where E3-S5B left it.** `=frame` (one `Event.wait` to the deadline)
cut the sender from 13 % to 2.0-2.35 % of a core and the companion from
24.6 % to 13.3-14.3 %, −2 to −2.7 W; no loss bursts in 60 flagged
minutes. It was REJECTED by 2 underruns in one run (18 vs 16), and the
only measured difference the probe found is a wider tick jitter (sd
0.17 vs 0.07 ms; p99 5.52 vs 5.19 ms) — the one timed wait oversleeps
by up to ~1.6 ms. Flagged sessions averaged 13 underruns per 20 min vs
10.7 unflagged.

**Narrow hypothesis.** The extra underruns come from the oversleep: a
timed wait that ends ~0.25 ms early, followed by today's spin to the
deadline, keeps the CPU saving (one wake-up per packet instead of ~86)
and restores today's jitter, and with it today's underrun count.

**The one change.** In `companion/native_session_io.py`'s
`_linux_wait_until`, a new value **`frame_spin`**: one `Event.wait` to
(deadline − 250 µs), then the existing final spin to the deadline.
`frame` keeps its E3-S5 behaviour; absent = today's wait, byte for
byte. Packetization, redundancy 2/4, `SCHED_RR`/1, the relay unchanged.
≤ ~10 lines.

Read first: `evidence/E3_S5B_AUDIO_SENDER_PACING_DECISIVE_2026-10-06.md`,
`e3_s5b_2026-10-06/probe.md`, `probe_stats.json`, `e3_s5b_probe.py`,
`e3_s5b_analysis.py`, `e3_s5b_preregistration.txt`,
`evidence/E3_S5_AUDIO_SENDER_COST_2026-10-06.md` §2.

## 1. Probe (before the runs)

E3-S5B's 60-s send trace (`PRIVYHUB_AUDIO_SEND_TRACE`, the dormant
hook), three ways in one session each: no flag, `frame`, `frame_spin`
(a flagged restart between; drop-in removed after). Report tick gap
median / p99 / max / sd, gaps > 10 and > 20 ms, bunches ≥ 4, voluntary
context switches/s, wake-ups per packet, and the sender's CPU %.
**Stated before the runs:** `frame_spin` is expected at sd ≈ 0.07 ms and
~1.4 wake-ups per packet; if its sd is not ≤ 0.10 ms the hypothesis is
already in doubt and the record says so (the runs still go).

## 2. Pre-registration (hashed before any benchmark run)

- **Runs, in order, all E1-PS1-STREAM at E2's windows and gaps:** C1
  (no flag), F1 (`frame_spin`), C2, F2, F3. Drop-in for F runs only,
  removed at each teardown, the environ checked against the adopted
  state (two lines: live, and the index).
- **Comparability (else INCONCLUSIVE):** both controls within E1's bands
  of E2's PS1-STREAM (host CPU 11.7 ± 2; rendered 59.81 ± 0.5) and
  within ± 0.5 fps of each other.
- **Bar, ACCEPTED only if all hold:**
  - (a) every F: sender ≤ **8 %** and companion ≤ **20 %** of a core (the
    spin is ~5 % of the period; today's are 13 and 24.6);
  - (b) every F: audio underruns ≤ max(C) + 5 and ≤ 20 — **unchanged
    from E3-S5B**, the clause this variant exists to meet;
  - (c) every F: rendered ≥ 59.5; RetroArch 60 ± 0.5;
  - (d) pooled minutes as E3-S5B: median loss/min of F ≤ 3 × C's; share
    of minutes > 100 lost in F ≤ C's + 0.10;
  - (e) D-BASE: spikes ≥ 20 ms/min < 200, stale drops/min < 20 in every F.
- **Reported:** the probe's three-way table; socket W; max output gap;
  the C2 block; the per-minute loss lists; the ladder's decisions.

## 3. The runs, the record

`evidence/E3_S5C_AUDIO_SENDER_PACING_SPIN_<date>.md` + `e3_s5c_<date>/`
(probe traces and stats, the diff, pre-registration + `.sha256`, 5
runs, `manifest.sha256`, `--check`, table, verdict, `loss_per_minute.txt`,
`redact_check.txt`): the verdict; the one-line adoption
(`Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`) with its
measured gain and cost beside `frame`'s; the revert.
`patches/E3-S5C_...md`; `logs/e3_s5c_git_status.txt`. Flag absent; the
adopted state restored; then queue item 3.
