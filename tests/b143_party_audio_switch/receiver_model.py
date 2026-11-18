"""B143: the onn's audio receive rule, modelled from the app's source (the app is not changed; nothing here runs on it).

Ported line for line (PrivyHub/app/src/main/java/streaming/):
- `NativeAudioReceiver.receiveLoop` (lines 1101-1225): the PHA1 magic, then version, channels, the 16-bit sequence;
  the sample timestamp is read and skipped (`header.int // sample timestamp`, line 1204); version 2 → `receiveOpus`.
- `NativeAudioReceiver.receiveOpus` (lines 1418-1549): the de-duplication by `seenSequences[sequence & 63]`
  (lines 1434-1444, SEEN_WINDOW 64, line 167), then `OpusReorder.offer` with k = `OpusFraming.copyOffsetFrames`.
- `OpusReorder` (OpusFraming.kt lines 76-170): `offer` (101-135) — the first frame starts the run (102-107); a frame
  more than half the 16-bit space behind `next` is LATE (110); 64 or more ahead a JUMP (111-119); a duplicate in the
  window (122); else in order / recovered (123-134); `drain` (145-163) releases `next` when held, gives it up as lost
  once a frame more than k ahead has arrived; `flush` (166-169).
- `OpusFraming.copyOffsetFrames` (46-50).

`Receiver.feed(t, seq)` returns the frames released by that datagram: [(seq, played)] — played False for a frame given
up as lost. A released frame goes to the decoder and the PCM queue at once; the playback loop takes it within one 5-ms
poll (`STARVATION_POLL_MS`, line 185).
"""
from __future__ import annotations

SEEN_WINDOW = 64
SEEN_WINDOW_MASK = SEEN_WINDOW - 1


def copy_offset_frames(copies: int, offset_pcm_packets: int, frame_samples: int) -> int:
    if copies < 2:
        return 0
    frame_ms = frame_samples * 1000 // 48_000
    return max(1, int(round(offset_pcm_packets * 5.0 / frame_ms)))


class OpusReorder:
    IN_ORDER, RECOVERED, LATE, DUPLICATE, JUMP = "in_order", "recovered", "late", "duplicate", "jump"

    def __init__(self, window: int = 64):
        self.window = window
        self.slots: list = [None] * window
        self.slot_seq = [-1] * window
        self.next = -1
        self.highest = -1
        self.held = 0

    @staticmethod
    def ahead(a: int, b: int) -> int:
        return (a - b) & 0xFFFF

    def offer(self, seq: int, payload, k: int, emit, on_jump=lambda n: None):
        if self.next < 0:
            self.next = seq
            self.highest = seq
            self._store(seq, payload)
            self._drain(k, emit)
            return self.IN_ORDER, 0
        behind_next = self.ahead(seq, self.next)
        if behind_next > 32767:
            return self.LATE, 0
        if behind_next >= self.window:
            self.flush(emit)
            skipped = self.ahead(seq, self.highest) - 1
            on_jump(max(0, skipped))
            self.next = seq
            self.highest = seq
            self._store(seq, payload)
            self._drain(k, emit)
            return self.JUMP, max(0, skipped)
        idx = seq % self.window
        if self.slot_seq[idx] == seq:
            return self.DUPLICATE, 0
        past_highest = self.ahead(seq, self.highest)
        if 1 <= past_highest <= 32767:
            kind, gap = self.IN_ORDER, past_highest - 1
            self.highest = seq
        else:
            kind, gap = self.RECOVERED, 0
        self._store(seq, payload)
        self._drain(k, emit)
        return kind, gap

    def _store(self, seq, payload):
        idx = seq % self.window
        self.slots[idx] = payload
        self.slot_seq[idx] = seq
        self.held += 1

    def _drain(self, k, emit):
        while True:
            distance = self.ahead(self.highest, self.next)
            if distance > 32767:
                return
            idx = self.next % self.window
            if self.slot_seq[idx] == self.next:
                p = self.slots[idx]
                self.slots[idx] = None
                self.slot_seq[idx] = -1
                self.held -= 1
                emit(self.next, p)
            elif distance > k:
                emit(self.next, None)
            else:
                return
            self.next = (self.next + 1) & 0xFFFF

    def flush(self, emit):
        if self.next < 0:
            return
        self._drain(-1, emit)


class Receiver:
    """One client session's receiver (a new one per client session, as the app builds one per session)."""

    def __init__(self, copies: int = 2, offset_pcm_packets: int = 4, frame_samples: int = 480):
        self.seen = [-1] * SEEN_WINDOW
        self.reorder = OpusReorder(SEEN_WINDOW)
        self.k = copy_offset_frames(copies, offset_pcm_packets, frame_samples)
        self.counts = {"late": 0, "duplicate": 0, "jump": 0, "in_order": 0, "recovered": 0, "dedup": 0}

    def feed(self, seq: int) -> list[tuple[int, bool]]:
        slot = seq & SEEN_WINDOW_MASK
        if self.seen[slot] == seq:
            self.counts["dedup"] += 1
            return []
        self.seen[slot] = seq
        out: list[tuple[int, bool]] = []
        kind, _gap = self.reorder.offer(seq, b"x", self.k, lambda s, p: out.append((s, p is not None)))
        self.counts[kind] += 1
        return out
