---
memory_schema: 1
as_of: 2026-09-23
status: TASK HANDOFF — D-BASE-P10, audio redundancy (a delayed duplicate of every audio datagram, de-duplicated on the client) as a profile setting, default off, measured warm against off in interleaved 10-minute holds; one companion + client change; authorized by the user 2026-09-23
---

# D-BASE-P10 — send audio twice

**Why.** `T3` located the warm-state audio loss *between* the host's NIC
and the onn's IP stack (0 send errors, 0 socket/stack drops at either
end). Cowork's correction to `T3` adds: video is lost there too, but its
8+1 XOR FEC recovers it (`fec_recovered_packets` steps up with the audio
loss, rho +0.5 to +0.8), while audio has no FEC — and every lost audio
packet becomes a crossfade (`T3`: 843 crossfades ≈ 848 lost). Audio is
~200 datagrams/s of ~962 B (1.5 Mbps); sending each one twice costs
+1.5 Mbps on a 260 Mbps link and recovers any loss that does not take
both copies.

Read first: `evidence/D_BASE_T3_AUDIO_LOSS_LOCATION_2026-09-23.md` (all,
including the corrections), `evidence/D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md`
(the warm state, the 6-7 minute cold plateau), `companion/native_session_io.py`
(`_linux_sender_loop`: the 5 ms pacer, the RTP header it writes, sequence
handling), `companion/native_stream_profiles.py` (where `audio_cushion`
lives — the new field goes beside it), `PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`
(receive loop, `lost_packets` from sequence gaps, the queue), `TOOLS.md`.

## The change — one coherent change, companion + client

- **Profile field** `audio_redundancy: {copies: 2, offset_packets: 4}`
  in `native_game_720p60_reference`, **default `copies: 1`** (off) until
  this task passes; `PRIVYHUB_AUDIO_REDUNDANCY_COPIES` /
  `_OFFSET_PACKETS` environment overrides for the arms, reported in
  `native-stream-status.audio` (`copies`, `offset_packets`, `source`) and
  in the decoder session report.
- **Companion sender**: with `copies: 2`, each audio datagram is sent
  again `offset_packets` ticks later (**same RTP sequence and timestamp,
  same payload**), from the same 5 ms pacer — i.e. tick *n* sends packet
  *n* and the copy of packet *n − offset* (two `sendto` per tick, no
  second thread, no change to the pacer's deadline). `packets_sent` counts
  originals; a new `duplicates_sent` counts copies. 4 packets = 20 ms
  separation, so a burst has to span > 20 ms to take both copies.
- **Client receiver**: de-duplicate by RTP sequence before anything else —
  a small seen-window (e.g. the last 64 sequences, wraparound-safe): a
  copy whose original arrived is dropped and counted `duplicates_dropped`;
  a copy whose original is missing is queued **in sequence order** (the
  queue's ordering/late handling must accept a packet up to 20 ms late —
  say how the existing queue treats it; with the 12/17 cushion (60 ms) it
  arrives well inside the cushion) and counted `recovered_by_duplicate`.
  `lost_packets` keeps its meaning (sequence gaps after de-duplication).
  Add to the report an **audio sequence-gap histogram** (gap sizes 1, 2,
  3, 4-7, 8+; counted from the original stream, before recovery) so the
  offset is judged against the burst lengths actually seen.
- No change to the cushion, the startup hold, video, FEC, the recovery
  state machine, or `native-stream-stop`.

Inspect exact current source and record pre-patch hashes; compile Python;
`git diff --check`; Android build and install per `TOOLS.md` (record the
APK hash); restart through systemd; `any_override: false` confirmed;
12/17 from the profile in every arm.

## Sessions — warm, interleaved 10-minute holds

The warm state is the condition; `T2` showed it persists across
back-to-back sessions and resets only with ≥ 30 min idle. So:

| # | hold | redundancy | purpose |
| --- | --- | --- | --- |
| 0 | W | off (1) | 12 min, from whatever state — the warm-up; not scored |
| 1 | A1 | off (1) | 10 min |
| 2 | B1 | **on (2 / 4)** | 10 min |
| 3 | A2 | off (1) | 10 min |
| 4 | B2 | **on (2 / 4)** | 10 min |

Each started within 1 minute of the previous, PS1 reference title, zero
input, `p9_run.sh`'s shape, companion restarted through systemd per arm
with the arm's variables (unset at the end), `T2`'s thermal sampler at
10 s throughout so the onn's `cpu-thermal` confirms the warm state (≥ 67 °C
at every scored hold's start — if not, extend W and say so). Sampler off,
heartbeat default, 0 foreign adb.

## Analysis, raw first

Per hold: audio `lost_packets`/min (after de-duplication), `recovered_by_duplicate`,
`duplicates_dropped`, `duplicates_sent`, the sequence-gap histogram,
`crossfaded_packets`, `concealed_loss_packets`, `underruns`,
`prolonged_starvation_events`, `avg_queue_residence_ms`, the `P8` hole
count; video rows (rendered fps, spikes, `max_output_gap_ms`, video loss,
`fec_recovered_packets`); the audio bitrate on the wire (from
`native_frame_sizes`' audio column if it has one, else `eno1` tx bytes
delta minus video bytes) and the encoder CPU %.

**Pre-registered reading.**
- **Adopt** if in both B holds audio `lost_packets`/min is ≥ 80 % below
  the mean of A1/A2, `crossfaded_packets` falls in step, `recovered_by_duplicate`
  ≈ the A-level loss, `underruns` inside the 3/8 noise band (4-20, `P9a`),
  `avg_queue_residence_ms` within ±10 ms of the A holds, the `P8` hole
  count within 20 %, and video rows unchanged (fps, spikes, `fec_recovered`
  within their A range) — then set the profile default to `copies: 2`,
  `offset_packets: 4` and record the measured bitrate cost.
- **Partial** (20-80 %): report the gap histogram — if bursts of ≥ 4
  packets carry the residual, say what offset (8? 16?) would cover the
  p90 burst; implement nothing more.
- **Does not work** (< 20 %, or underruns / residence / holes / video
  rows move): default stays `copies: 1`; say which clause failed and, from
  the histogram, whether the loss comes in bursts long enough that
  duplication cannot help (then XOR FEC across a group is the next lever,
  named, not built).

The user's listen with redundancy on — their words, never a gate.

## Record and memory

`evidence/D_BASE_P10_AUDIO_REDUNDANCY_<date>.md` (raw first, the five
holds, the histogram, the reading, the cost) with reports, heartbeat logs,
thermal jsonl and SHA-256s under `evidence/d_base_p10_<date>/`; patch
record and `PATCH_INDEX.md`; a decision record in `decisions/` if adopted;
`CURRENT.md` (fixed headings, `python3 tools/check_memory_health.py`
healthy — trim; Next Action: the roadmap list — `host_link` with `T3`'s
fact, `B1`/`B3`, Group C, C6 — and the C1 profile now carrying cap,
cushion and redundancy); `MEMORY.md`; `handoffs/CURRENT_HANDOFF.md`;
`investigations/ACTIVE.md`; `KNOWN_ISSUES.md` (the warm-state loss:
mitigated or not, cause still between the ends); `TOOLS.md`;
`docs/PROJECT_STATUS.md` (reference profile block) if adopted. Teardown
per `TOOLS.md`; companion under systemd; no `PRIVYHUB_*` set; no recovery
file. Never retry a failing action more than twice. No addresses, MACs,
SSIDs or device identifiers in any memory or evidence file. Nothing
committed.
