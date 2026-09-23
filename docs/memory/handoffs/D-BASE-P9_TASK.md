---
memory_schema: 1
as_of: 2026-09-23
status: TASK HANDOFF — D-BASE-P9, spend the +45 ms audio cushion the user decided on 2026-09-23 (queue target 3 → 12 packets, 15 → 60 ms) as a declared client setting, and measure it against the P8 arm-A baseline; one client change, two 20-minute sessions; authorized by the user 2026-09-23
---

# D-BASE-P9 — the deeper audio cushion

**The user's decision (2026-09-23):** spend the +45 ms. `P7` and `P8`
established the holes are the path's (p90 ≈ 60 ms, ~100/min ≥ 40 ms,
neither the heartbeat nor the sampler), and the only client lever is a
cushion that absorbs the p90: **`queue_target_packets` 3 → 12 (15 → 60 ms
at 5 ms/packet)**, with `queue_capacity_packets` raised from 8 to hold it
(**24**, so the target sits at half of capacity as it does today: 3 of 8
≈ 12 of 24 — say if the ratio in the code argues otherwise).

Read first: `evidence/D_BASE_P7_STARVATION_COUNTER_2026-09-22.md` §5-§7
(the arithmetic, the levers), `evidence/D_BASE_P8_AUDIO_HOLE_ORIGIN_2026-09-22.md`
(arm A is the baseline: 158.9 holes/min, 35.0 `prolonged_starvation_events`/min,
its report `d_base_p8_2026-09-22/runs/report_A.json` for every audio
field), `evidence/D_BASE_P2A_AUDIO_STARTUP_HOLD_2026-09-21.md` (the startup
hold — must be untouched), `PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`
and wherever `queue_target_packets` / `queue_capacity_packets` /
`track_buffer_frames` are set, `TOOLS.md`.

**The host now runs the companion as a systemd user unit** (`H3`,
installed by the user 2026-09-23): restart it with
`systemctl --user restart privyhub-companion` — never `kill` + `nohup`;
`h3_verify.sh` shows the state. Check `ss -lnt | grep 8765` is owned by
the unit's MainPID before every session.

## The change — one coherent client change

- Make the cushion a **declared setting** with the old value kept as the
  comparison: the target and capacity read from one place (a constant
  pair or an intent extra / stream-start parameter the companion passes —
  say which; if the companion passes it, add it to the stream profile as
  `audio_queue_target_packets` / `audio_queue_capacity_packets` beside
  `max_frame_size_bytes`, default **12 / 24**, and expose both in
  `native-stream-status`). No other audio behaviour changes: the startup
  hold (`P2a`), the concealment, `smooth_latency_trims`, the starvation
  counter and the `P8` ring stay as they are.
- Report the values in force in the decoder session report
  (`audio.queue_target_packets` / `queue_capacity_packets` already exist —
  confirm they reflect the new numbers).
- Build and install per `TOOLS.md`; record APK hash; `git diff --check`;
  restart the companion through systemd; `any_override: false` confirmed.

## Two 20-minute attract-mode sessions of the PS1 reference title, zero input, per TOOLS.md, BACK to end, teardown between

- **A2** — the old cushion (3 / 8) through the new setting, so the setting
  itself is exercised and the day's baseline is fresh.
- **B** — the new cushion (12 / 24).

Sampler off, heartbeat default, adopted profile, no other adb traffic
during the holds (the `P8` monitor pattern).

## Analysis, raw numbers first

Per session from the report: `audio.underruns` (the total, not a rate —
`P2`), `prolonged_starvation_events` /min, `concealed_underruns`,
`stale_drops`, `smooth_latency_trims`, `lost_packets`,
`avg_queue_residence_ms` and `max_queue_residence_ms` (the latency cost,
measured), `buffered_ms`, `max_queue_depth`, the `P8` hole count and
length histogram (must be unchanged within 20 % — the cushion does not
change arrivals), and `first_write_elapsed_ms` (the startup hold must not
move). Video rows beside them (rendered fps, spikes, max gap) to show the
video path is untouched.

**Pre-registered reading.** **Cushion works** if B's
`prolonged_starvation_events`/min is ≥ 80 % below A2's, `underruns` ≤
A2's, and `avg_queue_residence_ms` rises by 35-55 ms (the promised cost,
no more); then B stays installed as the default and the record says the
audio latency went up by the measured amount. **Partial** if the drop is
20-80 %: report the residual holes' lengths against the new 60 ms cushion
and state whether a 16-packet target would cover them, implement nothing
more. **Does not work** if the drop is < 20 % or underruns rise: revert
the default to 3 / 8 (the setting stays), classify FALSIFIED, and say what
the counter did instead.

The user's own listen for lip-sync or lag on the TV is **their words,
recorded as user-stated, never a gate** — leave a line for it.

## Record and memory

`evidence/D_BASE_P9_AUDIO_CUSHION_<date>.md` (raw first) with the two
reports, heartbeat logs, hole histograms and SHA-256s under
`evidence/d_base_p9_<date>/`; patch record and `PATCH_INDEX.md`; a
decision record in `decisions/` (the +45 ms as the user's choice, the
measured cost); `CURRENT.md` (fixed headings, `python3
tools/check_memory_health.py` healthy — trim; Next Action: thermal
thresholds); `MEMORY.md` (the cushion in force and its measured latency);
`handoffs/CURRENT_HANDOFF.md`; `investigations/ACTIVE.md`;
`KNOWN_ISSUES.md`; `TOOLS.md` (the setting, the systemd restart);
`docs/PROJECT_STATUS.md` (the reference profile block gains the audio
cushion). Teardown per `TOOLS.md`; companion left running under systemd.
Never retry a failing action more than twice. No addresses or device
identifiers in any memory or evidence file. Nothing committed.
