---
memory_schema: 1
as_of: 2026-09-23
baseline_commit: 3e6cde5
durable_memory_updated: true
---

# D-BASE-P10 — audio redundancy: send every audio datagram twice

## Purpose

`T3` located the warm-state audio loss between the host's NIC and the
onn's IP stack, where neither end can recover the same packet; Cowork's
correction to `T3` showed video loses there too but its XOR FEC recovers
it, while audio has none. This sends each audio datagram a second time
`offset` 5 ms ticks later and keeps the first to arrive on the client — a
profile setting, **default off** (`copies: 1`). Built and installed
directly under the task authorization (`handoffs/D-BASE-P10_TASK.md`).

## Changed scope

Pre/post SHA-256 in `evidence/d_base_p10_2026-09-23/{pre,post}_patch_sha256.txt`.

**`companion/native_stream_profiles.py`** — `audio_redundancy_copies`
(1 | 2, default 1) and `audio_redundancy_offset_packets` (1-16, default
4) beside the cushion fields, validated, in `to_dict()`;
`AUDIO_REDUNDANCY_MAX_OFFSET = 16`.

**`companion/native_stream.py`** — `PRIVYHUB_AUDIO_REDUNDANCY_COPIES` /
`_OFFSET_PACKETS` (each independently; invalid → ignored,
`env_ignored`); `audio_redundancy()` → `native-stream-status.audio_redundancy`
{copies, offset_packets, offset_ms, source, env_ignored, defaults} — in
the stream-start response, so the client gets it; handed to the Linux
sender (`set_redundancy`) right before `session_io.start`. Not in
`encoder_overrides`.

**`companion/native_session_io.py`** — `NativeAudioStreamer.set_redundancy`;
in `_linux_sender_loop`, with copies = 2, each tick sends packet *n*
**then** the stored datagram *n − offset* (same bytes: sequence,
timestamp, payload) from a `deque(maxlen=offset+1)` — a second `sendto`
in the same tick; the pacer's deadline untouched. `packets_sent` still
counts originals; new `duplicates_sent`, `duplicate_send_errors`, and
`copies`/`offset_packets`, in `audio` and `helper_status.redundancy`.
Windows path untouched.

**`PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt`**

- **De-duplication first**: a 64-slot seen-window keyed `sequence & 63`
  (exact match, so wraparound-safe); a sequence already seen is dropped
  and counted `duplicates_dropped` before the arrival-gap (`P7`/`P8`) and
  loss logic, which therefore see each sequence once, as with it off.
- **Late packets** (a sequence behind the expected one — a copy whose
  original was lost): **the old code counted nothing, reset
  `expectedSequence` backwards and queued the packet at the tail, out of
  order; the next in-order packet then read as a false gap.** Now a late
  packet fills its concealment slot in place if the slot is still queued
  (`recovered_by_duplicate`, and `lost_packets` is decremented, so it
  keeps meaning "sequences never received") or is dropped
  (`late_unplaced`); `expectedSequence` never moves backwards.
- **Concealment slots carry the sequence they stand for**: `PcmPacket`
  is a class with `sequence` and an `AtomicInteger state` (0 pending,
  1 filled late, 2 consumed); the playback thread claims an item with
  CAS 0→2 and the filler with CAS 0→1, so exactly one side wins; a
  trimmed slot is marked consumed. Slots per gap: 2 as before, **2 +
  offset** with redundancy on, for the most recent missing sequences.
- `sequence_gap_packets` and a gap-event histogram (1, 2, 3, 4-7, 8+),
  counted at first arrival before recovery.
- `configureRedundancy(copies, offset)`. Cushion, startup hold, the
  starvation counter, `P8` ring: unchanged. **With redundancy off the
  only behaviour change is the late-packet path, which this path has
  never exercised** (`late_or_reordered_packets` 0 throughout).

**`PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt`** — reads
`audio_redundancy` from the start response; report fields
`audio.redundancy_{copies,offset_packets,source}`, `duplicates_dropped`,
`recovered_by_duplicate`, `late_unplaced`, `sequence_gap_packets`,
`sequence_gap_histogram`. Schema stays `_v2` (additive).

## Validation performed

- `py_compile` (three companion files); `git diff --check` clean.
- `sh ./gradlew :app:assembleDebug --no-daemon` — BUILD SUCCESSFUL, first
  attempt. APK
  `f31b1c180c5d0849230860d2f5b7ab1b4a8637f7be56a7dcf1f71aba77668ae7`,
  installed, device package hash equal.
- 60 s smoke, copies 2 from the environment: sender 13,266 originals +
  13,262 duplicates, 0 errors; client `duplicates_dropped` 13,073, four
  1-packet gaps **all recovered by their copies**, `lost_packets` 0,
  `concealed_loss_packets` 0, `late_unplaced` 0.
- The sessions: `evidence/D_BASE_P10_AUDIO_REDUNDANCY_2026-09-23.md`.

## Status

**INSTALLED; ADOPTED as the profile default 2 / 4 by the user**
(`decisions/D-BASE-P10_AUDIO_REDUNDANCY.md`): warm, interleaved, audio
loss −96.4 / −98.2 % at +1.6 Mbps. `native_stream_profiles.py` after
adoption → `67c12d5bb84443b342ecf5d96c55c10031110cbdd6e4bb2106a0ea1b2a8754d4`.
