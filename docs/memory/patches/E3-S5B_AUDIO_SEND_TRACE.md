---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: bf2120c
durable_memory_updated: true
---

# E3-S5B: the audio sender's send-timing trace (measurement only), and interleaved plan items in the runner

## Purpose

E3-S5B (`handoffs/E3-S5B_AUDIO_SENDER_PACING_DECISIVE_TASK.md`, record
`evidence/E3_S5B_AUDIO_SENDER_PACING_DECISIVE_2026-10-06.md`) decides
E3-S5's flag without changing it. Its probe needs the time of every
`sendto`.

**Measurement only.** E3-S5's flag remains NOT ADOPTED (REJECTED again).

## Change

**`companion/native_session_io.py`, `_linux_sender_loop`:** with
`PRIVYHUB_AUDIO_SEND_TRACE=<path>`, the sender records `perf_counter_ns`
of each original and each duplicate `sendto`, starting 30 s after it
starts, for 60 s. A helper thread then writes them (`<ns> o|d` per
line). Absent: one `is None` check per send.

**`tools/e1_suite.py`:** plan items for the same row continue its run
numbers (C, F, C, F, F → `run1`, `run2` and `run1`-`run3`), so
interleaved plans do not overwrite runs.

**Tools:** `tools/e3_state.py` (E2's final state as one JSON line).

## Validation

- `py_compile`; `e1_suite.py --self-test`.
- The probe: 24,000 sends traced per session.

## Rollback

Revert the trace lines in `_linux_sender_loop` and `_linux_send_trace`,
and the `done` counter in `run_suite`.
