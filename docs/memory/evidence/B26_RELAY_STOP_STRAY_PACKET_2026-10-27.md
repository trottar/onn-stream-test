---
memory_schema: 1
as_of: 2026-10-27
baseline_commit: 2cd392c (G-A7 applied beside it by A, uncommitted; B26 uncommitted)
---

# B26 — the stray 8-byte packet at an unlocked restart: an old frame's first packet held across the relay's stop, not an exit packet; fixed inside `PRIVYHUB_RESTART_FAST_UNLOCK=1`

**Classification: SETTLED + BUILT**, inside the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1` (G-A7). No new flag: the
fix is the adopted behaviour byte for byte but the one packet (§2).
- **Tests:** `tests/restart_fast_unlock_relay` 5 green (three runs), with the real FEC relay on loopback. B24's 10
  (`tests/restart_fast_unlock`) and B22's 13 (`tests/restart_fast`) are unedited and green. Every suite under
  `tests/` is green. **The mutation (the fix removed = B24 as adopted) is caught 5 / 5** after the trigger offset
  (§3).
- **Proof:** `proof_flag_absent.md` **PROVEN**.
- No client change. NOT ADOPTED beyond the line it sits in; no live run; nothing committed.

Design `b26_2026-10-27/design_written_before_code.md`, sha256 `836df692…9653`, hashed **21:48:17Z, before any B26
code**. Preconditions checked first: G-A7's record present; only the companion and `privyhub-link-n1` active.

## 0. Settled (from the code and CL-B14's rows)

1. **What it is:** one ordinary packet of the **old encoder's** stream: its SSRC, the next sequence number, no
   marker. It is **the first packet of the frame that followed the relay's stop call.**
   - It is not an end-of-stream marker, not a NAL flushed at exit and not an echo of the relay's stop.
   - In the held picture every frame is the same 14 packets / 14,614 B: 840 packets and 876,856 B in every second
     before each return.
   - Its first packet carries an **8-byte payload**: one small NAL unit sent alone ahead of the frame's large
     fragmented NAL. Which NAL (the P slice or a per-frame SEI) is not in the rows; no capture was kept.
2. **How it got through.** `NativeVideoFecRelay.stop()` takes the relay's lock and sets `_running` false. With the
   impairment shim on (CL-B14's `none@post-fec`), it then calls `self._shim.stop()`, which joins the shim's thread
   (a ≤ 50-ms select).
   - **That join runs under the relay's lock, before the receive socket is closed.** The old encoder is still
     running at 60 fps.
   - So the receive thread reads the next frame's first packet and **waits on the lock**. The frame's other 13
     packets die in the socket when `stop()` closes it.
   - `stop()` then closes the frame in flight (none: the last one was marked), rolls the bucket and releases the
     lock.
   - The receive thread then notes the one packet (a new open frame: 1 packet, 8 B, unmarked) and `_send`s it. The
     send socket and `_client` are cleared only at the end of `stop()`, after its joins. Then it exits.
3. **Why its row reads "100-140 ms after the stop, within 1 ms of `released_ms`":** that is not when it was sent.
   - A per-second row times a frame at its **close**. This open frame was closed by the **new** relay's `start()`,
     whose first act is `stop()` → `_close_frame_locked(time.time(), marked=False)`. That runs 1-2 ms after
     `released_ms`.
   - The 100-140 ms is `released` − `relay_stopped`: the 100-ms kill grace and the reap.
   - **The packet itself was sent inside the first `stop()`, before `relay_stopped_ms`.** The receive thread is
     joined before `stop()` returns: a timed-out join would make `relay_stopped_ms` ≥ 1 s, and it read 50-500 ms.
   - `relay_stopped_ms` is mostly the frame-log thread's join (it sleeps 0.5 s). The receive socket closes at the
     stop's start, which is why the old picture frames end at the entry (CL-B14 R2).
   - **The live log's write order agrees:** the old bucket, then the stray, then the new encoder's first bucket, at
     all four returns. The run dir's copy (`cl_b14_2026-10-26/…/native_frame_sizes.jsonl`) is sorted
     lexicographically (710 / 710 lines in sorted order), so its order says nothing.
4. **4 / 4 in CL-B14, never in CL-B13:**
   - G-A5's worker kills the old encoder before the relay's stop, so nothing is in flight.
   - Under B24 the relay stops while the old encoder runs, and the shim's ≤ 50-ms join is longer than a frame
     interval (16.7 ms).
   - The old buckets show `unmarked_frames` 0 at all four returns, so the stop always fell between frames: the
     held packet was a first packet.
5. **Whether it reached the onn:**
   - **In CL-B14: no.** With the post-fec shim, `_client` is the shim's loopback port. `shim.stop()` had closed both
     shim sockets inside the same `stop()` before the packet was sent, so the host's kernel dropped it.
   - **On the twelve lines without a shim:** `stop()`'s locked section lasts microseconds. A packet the receive
     thread has already read but not yet noted when the stop takes the lock is forwarded **straight to the onn**,
     during the joins. That is rare but possible, and it can be a mid-frame fragment.
6. **What the onn does with one** (`RtpH264Receiver`, read): it is in sequence on the old SSRC. The new receiver
   already holds that SSRC from the old frames that arrived before the stop: CL-B14 sessions 2-5 report
   `ssrc_changes` 1 / `sequence_resyncs` 1.
   - Its access unit stays open until the new SSRC's first packet runs `beginStreamResync`, which resets it
     **without counting it**.
   - So it counts in `packets` / `bytes` only: **no frame, no `dropped_frames`, no `incomplete_au_drops`.** The
     client has no `bad_packet` counter.
   - The receiver is `waitingForIdr` in any case, and the restart guard's switch (the `ssrcChanges` rise) is
     unchanged.

## 1. Built (`b26.diff`)

**`companion/restart_fast_unlock.py` only.** In `_restart_unlock_locked`, `m._fec_relay.stop()` becomes
`self._stop_relay(m._fec_relay)`, a new static method:
- under the relay's lock, `relay._client = None`: `_send` reads it under that lock, so **nothing more is
  forwarded**, data or parity;
- `relay.stop()`, unchanged;
- under the lock again (the receive thread already joined), the frame in flight and `_frame_bucket` are cleared:
  what was noted after the close is not left for the new `start()` to close as a 1-packet row;
- a relay without these internals (B22's / B24's `FakeRelay`) is just stopped. That is why B24's 10 run unedited.

`native_fec_relay.py`, `restart_fast.py`, `plugins/games.py` and `impairment.py` are not edited.

## 2. Why no new flag: the adopted behaviour byte for byte but the one packet

- `_client` is read only by `_send`. `stop()` sets it to None at its own end anyway, and `start()` sets it again.
- The cleared frame fields are reset by the new `start()` in any case. They are non-empty after the join only when
  the receive thread noted a packet after the close.
- **The order, the timings, every row and every field are unchanged:** `restart_fast_done` has the same six keys;
  no row was added.
- **The only difference:** what the receive thread forwards after the stop was called (the held packet, and its
  parity if it completed a group) is not sent, and the frame log has no 1-packet row for it.
- Absent the flag, the module is not imported (B24, `test_nothing_imported`, green).
- `proof_flag_absent.md`, **PROVEN:**
  - the new module's AST, with `_stop_relay` removed and its call put back as `m._fec_relay.stop()`, equals HEAD's;
  - `native_fec_relay.py`, `restart_fast.py` and `plugins/games.py` are sha256-identical to HEAD;
  - `git diff HEAD` is empty for those, `native_stream` and `impairment`.

## 3. Tests (`tests_restart_fast_unlock_relay.txt`, `tests_mutation.txt`, `timelines_fixed/`, `timelines_mutation/`)

`tests/restart_fast_unlock_relay/` (new) imports B24's harness (and through it B22's), both unedited. It replaces the
fake relay with **the real `NativeVideoFecRelay`** on loopback:
- one fixed free port for the old and the new relay, as in production;
- a fake onn: a UDP socket recording every arrival;
- fake encoders sending the held picture's 14-packet frames at 60 fps (an 8-byte unmarked first packet); SSRC A
  old, B new.

| test | with B26 | the mutation (B24 as adopted) |
| --- | --- | --- |
| **8 bytes at exit** (the queue's case: the old encoder sends one 8-byte packet when SIGTERMed) | 0 old packets at the onn > 10 ms after the stop's call; no 1-packet row | passes too: the socket is closed by then. **An exit packet cannot be forwarded**, which is §0's point |
| **CL-B14's window on the onn's path** (a fake shim holding the relay's lock 50 ms, the target the onn) | 0 old packets, 0 old parity; no 1-packet row | **fails 5 / 5:** the old frame's 8-byte first packet at the onn **50.5-50.8 ms after the call** |
| **CL-B14 reproduced** (the real `none@post-fec` shim) | no 1-packet row; nothing at the onn | **fails 5 / 5 on the row:** the 1-packet, 8-byte, unmarked row in its own bucket, **and nothing at the onn**, exactly CL-B14's reading |
| the restart still works | 980 new packets forwarded; every old frame sent before the call forwarded whole; the `restart_fast_done` keys B24's; `max_live` 1 | — |
| the helper on a relay without internals | stopped as is | — |

- **Disclosed: the trigger offset.** The first mutation batch (three runs) caught it 2 / 3 on the onn's path. It
  missed when the stop landed while the Python receive thread was still handling the previous burst, so the held
  packet had already been sent before the lock. CL-B14's stops fell between frames (§0.4). The test now posts the
  restart 6 ms after a burst. Both mutation tests then failed 5 / 5, with the packet's payload 8 B every time. The
  first batch's misses and its 1,188-B mid-frame strays are kept in `tests_mutation.txt`.
- **Every suite** (`tests_regression_after_b26.txt` against `tests_regression_baseline_predecessor.txt`, both in the
  copy): the baseline's outcomes plus `tests/restart_fast_unlock_relay`. B24's suite is 10 with one skipped in the
  copy (its predecessor hash needs `docs/`); that hash was checked by hand and is equal. The four `tools/` tests
  fail in the copy as at the baseline (as at B24).
- **Disclosed: a deletion.** `rm -rf /tmp/b_q27j_scratch/mut1`, the first mutation copy, which I had made minutes
  before. It held only a copy of companion/ and tests/. "Nothing deleted" was broken by it. It was replaced by
  `mut1b`; nothing else was removed.

## 4. For A (not a row of CL-B15)

At the next Home cell, `native_frame_sizes.jsonl` (the live file, read in write order) should show **no** 1-packet
unmarked row between the old encoder's last bucket and the new one's first. CL-B14 showed one at every return.

## 5. Files

- **`b26_2026-10-27/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `started_at.txt`, `units_at_start.txt`;
  - `predecessors/` (+ `predecessor_note.txt`), `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b26.diff`, `proof_flag_absent.py` / `.md`;
  - `tests_restart_fast_unlock_relay.txt`, `tests_mutation.txt`, `timelines_fixed/`, `timelines_mutation/`,
    `tests_regression_baseline_predecessor.txt`, `tests_regression_after_b26.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `companion/restart_fast_unlock.py`, `tests/restart_fast_unlock_relay/` (new);
  `patches/B26_RELAY_STOP_STRAY_PACKET.md`; `logs/b26_git_status.txt`.
- **Left in /tmp:**
  - `b_q27j` (the copy), `b_q27j_base` (the baseline copy);
  - `b_q27j_scratch/` (`mut1b`, `tl_mut1`, `tl_mut1b`, `base_excluded_restart_fast_unlock_relay`);
  - `b_q27j_sync.sh` / `_regress.sh` / `_base_regress.sh`.
- **The rules held** (but the deletion above):
  - no stream, no companion restart, no adb, no sudo, no nft; the Opal untouched;
  - nothing of `privyhub-link-n1`'s files touched; the live logs only read;
  - nothing of A's touched; nothing fetched, adopted or committed.
