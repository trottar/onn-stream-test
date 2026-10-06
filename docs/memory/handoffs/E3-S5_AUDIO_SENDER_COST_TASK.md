---
memory_schema: 1
as_of: 2026-10-06
status: TASK HANDOFF — E3-S5, queue item 5 (the user's go, 2026-10-06): streaming's fixed cost, the companion's audio sender (12.9 % of a core at PS1-STREAM). Probe its loop; one change behind a flag; benchmark E1-PS1-STREAM ×2 with the flag and ×1 as the same-night control; the D-BASE close-out table must stay met. Accept/reject by the pre-registered bar. Nothing adopted; nothing committed
---

# E3-S5 — the audio sender's cost

**Measured bottleneck (E2-S1 §6, "the companion's stream cost by
thread").** At PS1-STREAM the companion costs 24-30 % of a core: the
audio sender (the `SCHED_RR` thread) 12.9 %, the FEC relay 7.8 %, the
other poll thread 3.0 %, the audio reader 0.1 %. The encoder's 36 % and
Xorg's 10 % are not this task's.

**Narrow hypothesis.** The audio sender spends most of its 13 % waking
and polling, not sending: its loop's period or its poll timeout is
shorter than the audio frame it carries (the stream's audio packets per
second bound the useful work).

## 1. Probe (measurement first)

With a PS1 stream PLAYING for 3 min: the sender thread's voluntary /
involuntary context switches per second (`/proc/<pid>/task/<tid>/status`
and `schedstat`), its `syscall` mode as E2 sampled it, and the audio
packets sent per second (the companion's own counters). Wake-ups per
packet is the figure. `e3_s5_<date>/probe.md`. If wake-ups per packet
≤ 1.5, the hypothesis is already wrong: record **NOT RUN (hypothesis
falsified by the probe)** — the thread is busy sending — and stop the
task (the queue is done).

## 2. The one change

The sender blocks on its input for one audio frame (or its poll timeout
matches the frame period) instead of its current shorter wait; no
change to packetization, redundancy (2/4), `SCHED_RR`, or the relay —
**behind `PRIVYHUB_AUDIO_SENDER_PACING=frame`** (absent = today, byte
for byte). ≤ ~20 lines at one site.

## 3. Pre-registration (hashed before any benchmark run)

- **Runs**: E1-PS1-STREAM ×1 flag absent (the control), then ×2 with the
  flag (E2's window and gaps; drop-in for those runs only).
- **Bar, ACCEPTED only if all hold, both flagged runs:**
  - the audio sender thread ≤ **4 %** of a core and the companion's CPU
    ≤ **17 %** of a core (E2: 12.9 and 24.3);
  - audio underruns per session ≤ the control's + 5 and ≤ 20 (E2: 11;
    D-BASE target 17/14);
  - rendered fps ≥ 59.5; RetroArch 60 ± 0.5; video loss/min ≤ 3× the
    control's;
  - **the D-BASE close-out table met** (`evidence/D_BASE_CLOSEOUT_2026-09-23.md`:
    spikes ≥ 20 ms/min < 200, stale drops/min < 20, loss < 10 — the
    loss row by the control's hour, reported if the control itself
    fails it; max output gap the open row, reported);
  - the control within E1's bands of E2's PS1-STREAM (else
    **INCONCLUSIVE**).
- **Reported:** wake-ups per packet before/after, the relay's and the
  other poll thread's CPU (unchanged expected), the C2 latency block.

## 4. The record

`evidence/E3_S5_AUDIO_SENDER_COST_<date>.md` + `e3_s5_<date>/` per the
queue; `patches/E3-S5_...md`; `logs/e3_s5_git_status.txt`. Flag absent;
E2's final state restored. **Then the queue's close**:
`handoffs/CURRENT_HANDOFF.md` (the five verdicts in one table), the
daily file, `check_memory_health.py`, the redactor `--check` over every
file the queue wrote, **`CURRENT.md` last** as the queue says.
