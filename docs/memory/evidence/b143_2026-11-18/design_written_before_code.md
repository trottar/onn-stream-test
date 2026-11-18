# B143 — the sound across a planned switch: design (written and hashed before any code)

Queue: `handoffs/QUEUE_2026-11-18AX.md` §B143. Baseline `baseline_head.txt`. Behind `PRIVYHUB_PARTY=1` (and
`PRIVYHUB_H7=1`): only the party layer arms it. Absent = today.

## Settled from the code (read only; the app not changed)

**What the hub's sender starts over at every `native_stream.start`** (`companion/native_stream.py`
`_start_linux_locked` → `_stop_locked` → `session_io.stop_stream` → `audio.stop`, then `session_io.start` →
`audio.start` → a new sender thread): the hub runs `PRIVYHUB_AUDIO_CODEC=opus` (its drop-in), so the sender is
`audio_codec.run_opus_sender`: **`sequence = 0`, `sample_timestamp = 0`, a new `OpusEncoder`**, the PHA1 header
`<4sBBHII>` (magic, version 2, channels, **16-bit sequence**, 32-bit timestamp, frames). The PCM loop
(`NativeAudioStreamer._linux_sender_loop`) the same with version 1. **There is no SSRC, no marker, no session field in
PHA1.** Nothing is carried from the stream before.

**What the app does with audio behind what it has played** (`PrivyHub/app/src/main/java/streaming/`):
`NativeAudioReceiver.receiveLoop` reads the sequence, **skips the timestamp** (`header.int // sample timestamp`,
line 1204) and for version 2 calls `receiveOpus`: de-duplicated by `seenSequences[sequence & 63]` (line 1438), then
`OpusReorder.offer` (`OpusFraming.kt` 101-135): `behindNext = (seq - next) & 0xffff`; **`> 32767` → `Kind.LATE`:
dropped, `next` not moved** (line 110); `>= 64` → a JUMP (taken: what is held flushed, the new run starts, line
111-119); else in order / recovered. `next` moves only with frames released. The PCM path the same (`gap > 32767` →
late, line 1302). **What makes it accept a new beginning:** a jump ahead of 64 to 32767 sequences, or a new receiver
(`next = -1`, the first frame taken, line 102-107). **Why Home / RESUME clears it:** a new client session builds a new
`NativeAudioReceiver` (its `OpusReorder` with `next = -1`); and the app's own restart (B11, `NativeStreamActivity`
line 983: "the host restarted its audio at sequence 0: a fresh receiver") rebuilds it — **only for a restart the app
itself asked for.** A hub-side planned switch is not one: the app is not told, keeps its receiver, and drops the new
stream's frames as LATE until the new sequence passes its `next`.

**The rule replayed on the sitting** (`replay_rule.py` → `replay_rule_result.jsonl`): within one client session a
stream's first min(L, M) / 100 s are silent (M the furthest sequence played, L the stream's frames, 100 frames / s);
then M = max(M, L). On the sitting's 12 streams (two client sessions, ten planned switches): **predicted vs observed
silent stretch within one heartbeat row (max error 2.0 s; rows every 2 s)** — e.g. the first real match 110.7 s
predicted / 110.9 s observed (until 03:41:34), the second real match 99.3 / 99.4 s (until 03:51:28), every practice and
board stretch shorter than 99.3 s silent from end to end. The rule predicts them; nothing else is needed.

## The design — continuity across a party's planned switch, by what the app already honours

The app plays a frame whose sequence is the one after the last it released (`OpusReorder`: in order, released at once).
So **the new process's sender continues the old one's sequence and timestamp** — the app sees the stream go on.

1. `NativeAudioStreamer` (companion/native_session_io.py):
   - every sender run, at its end, records where it stopped: `(next sequence, next timestamp)` —
     `_audio_sent_next`, written only by the run that is still the streamer's current one (a token per run), so a
     sender that outlives its stop's join cannot write over a newer run's.
   - **`party_continue_next(pid)`** — B143's arm: the next audio start **for this process id** begins at the recorded
     `(sequence, timestamp)`; `party_continue_next(None)` disarms. `_audio_start_counters(process_id)` (called once in
     `_start_linux_locked`, after the old run is stopped): the recorded pair when armed for that pid and a pair is
     recorded, else `(0, 0)`; the arm cleared either way; the record cleared too (a stale pair is never reused).
   - both sender loops (`_linux_sender_loop`, `audio_codec.run_opus_sender`) start from
     `getattr(streamer, "_audio_start", (0, 0))` instead of the literal 0, 0 and record at their end. With `(0, 0)` the
     datagrams are byte for byte today's.
2. `PartyMinigames._switch_stream` (companion/party_minigame.py, only imported with both flags): just before the
   switch's `ns.start(...)`, `ns._session_io.audio.party_continue_next(pid)`; in its `finally`,
   `party_continue_next(None)`. Every planned switch (the way in, a practice's way back, the end's way back) goes
   through it; nothing else arms it.
3. **Not changed:** the users' own starts (the onn's `native-stream-start`, RESUME, the recovery's restarts, any start
   without the party layer) — the arm is never set for them: sequence and timestamp 0 as today; the Opus encoder is new
   per stream as today (the app's decoder continues: a click or not is not a cell); **the video's own switch (B115)
   untouched** (no change in `native_stream.py`); the encoder's command, the relay, the controller, the planned-switch
   window — unchanged.

**What the switch then costs in the sound:** the old process's sound stops when the switch begins (`_stop_locked`) and
the new one's is sent from its sender's first datagram — the switch's own gap, **unchanged by this fix: in the sitting
the ten switches took 1.71-3.60 s (`minigame_stream` `seconds`), the sender's first datagram ~0.25 s before the row**,
so ~1.5-3.3 s of no sound, the same time the picture switches. **The fix adds 0 ms**; the new process's first frame is
released by the app at once (in order), played at its next 5-ms poll behind the 3-packet target. **The bound the tests
use: from the new stream's first datagram to the first frame the modelled app releases ≤ 50 ms after every planned
switch** (HEAD: L seconds).

## Tests (`tests/b143_party_audio_switch/`)

- **The model** (`receiver_model.py`): `OpusReorder.offer` / `drain` and the receive path's de-duplication ported line
  for line from the app's source (the lines cited in the file); its own checks: in order, a duplicate, a lost frame
  given up after k, a LATE frame, a JUMP.
- **The real sender through two and five planned switches:** the real `NativeAudioStreamer._start_linux_locked` (Opus,
  as the hub runs) on stubs — `pactl` answers stubbed, the capture a made-up process writing silence at the real rate,
  the datagrams to a UDP socket on loopback — driven by the real `PartyMinigames._switch_stream` with a stream object
  whose `start` stops and starts that audio streamer for the given pid (a users' start: the same call without the
  party layer). Each stretch 0.6-1.6 s. The datagrams fed to the model: **no silent stretch longer than 50 ms after
  any switch; every frame released; sequences continuous across every switch.**
- **HEAD's code, the same scenario** (its modules from the `/tmp/b_` copy): the silent stretches appear — each switch's
  stream silent for min(L, M) (the mutation that shows the fault).
- **A users' start byte for byte today** with the flags set: two starts without the arm — the datagrams' headers and
  payloads equal to HEAD's (sequence 0, timestamp 0); an arm for another pid does not touch it.
- **The flags absent → today:** B114's flag test (the real routes on HEAD's code against mine); the party module not
  imported, nothing arms. **The client contract's tests green;** the audio codec's suite green.
- Temp dirs removed.
