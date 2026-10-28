# B26 — design, written before any code (QUEUE_2026-10-27J item 1)

## Settled (from the code and CL-B14's rows; read before this design)

1. **The 8-byte packet is not sent at the old encoder's exit.** It is one RTP packet of the old encoder's ordinary
   stream (its SSRC, the next sequence number, no marker): the first packet of the frame that followed the relay's
   stop call. In the held picture every frame is 14 packets / 14,614 B (840 packets and 876,856 B per second, flat),
   and its first packet carries an 8-byte payload: one small NAL unit sent alone ahead of that frame's large
   fragmented NAL. Which NAL (the P slice or a per-frame SEI) is not in the rows; no capture was kept.
2. **How it got in.** `NativeVideoFecRelay.stop()` takes the relay's lock and sets `_running` false. With the
   impairment shim on (CL-B14's `none@post-fec`), it then calls `self._shim.stop()`, which joins the shim's thread
   (its select timeout is 50 ms), **while holding the relay's lock and before it closes the receive socket**. The old
   encoder keeps sending at 60 fps, so the receive thread `recvfrom`s the next frame's first packet. It then blocks
   on the relay's lock in `_note_frame_packet`. `stop()` closes the socket, so the frame's other 13 packets are
   dropped in it. It closes the frame in flight (none; the last one was marked), rolls the bucket and releases the
   lock. The receive thread then notes the one packet (a new open frame: 1 packet, 8 B) and `_send`s it. The send
   socket and `_client` are cleared only at the end of `stop()`, after the joins. It then sees `_running` false and
   exits, and `stop()` joins it.
3. **Why its row reads 100-140 ms after the stop.** That time is not when it was forwarded. The per-second row times
   a frame at its close (`max_at_utc`). This open frame is closed by the **new** relay's `start()`, whose first act is
   `stop()` → `_close_frame_locked(time.time(), marked=False)`. That runs right after `released_ms`: the new spawn
   begins 1-2 ms after it. Hence "within 1 ms of `released_ms`" and "100-140 ms after `relay_stopped_ms`"
   (`released` − `relay_stopped` = the 100-ms kill grace + the reap). The packet itself was noted and sent inside
   the first `stop()`, before `relay_stopped_ms`. The receive thread is joined before `stop()` returns: a join that
   timed out would make `relay_stopped_ms` ≥ 1 s, and it read 50-500 ms. `relay_stopped_ms` itself is mostly the
   join of the frame-log thread, which sleeps 0.5 s. The live log's write order confirms it: the old bucket, then
   the stray, then the new encoder's. The run dir's copy is sorted lexicographically, so its order says nothing.
4. **Why 4 / 4 in CL-B14 and never in CL-B13.** G-A5's worker kills the old encoder before the relay's stop, so
   nothing is in flight. Under B24 the relay stops while the old encoder runs. The shim's ≤ 50-ms join inside the
   lock is longer than a frame interval (16.7 ms), so a frame's first packet always arrives in it.
5. **Whether it reached the onn.**
   - **In CL-B14: no.** With the post-fec shim, `_client` is the shim's loopback port, and the shim's sockets were
     closed by `shim.stop()` inside the same `stop()` before the packet was sent. The host's kernel dropped it
     (unconnected UDP: no error to the sender).
   - **On the twelve lines without a shim:** `stop()`'s locked section lasts microseconds. A packet the receive
     thread has already read but not yet noted when the stop takes the lock (GIL or lock contention) is noted and
     forwarded straight to the onn, during the joins. This is rare but possible, and a mid-frame fragment is
     possible too.
   - **What the onn does with it** (`RtpH264Receiver`): it is in sequence on the old SSRC (the new receiver has
     already taken the old SSRC from the old frames that arrived before the stop; sessions 2-5 of CL-B14 report
     `ssrc_changes` 1 either way). Its access unit stays open. The new SSRC's first packet runs
     `beginStreamResync`, which resets the unit without counting it. So it counts in `packets` / `bytes` only: no
     frame, no `dropped_frames`, no `incomplete_au_drops`. There is no `bad_packet` counter. The receiver is
     `waitingForIdr` in any case, and the restart guard's switch count is unchanged.

## The fix: inside the adopted `PRIVYHUB_RESTART_FAST_UNLOCK=1`, no new flag

**In `RestartFastUnlock._restart_unlock_locked` only:** `m._fec_relay.stop()` becomes
`self._stop_relay(m._fec_relay)`:
- under the relay's lock: `relay._client = None`, so nothing more is forwarded (`_send` reads `_client` under that
  lock and returns on None). This covers data and its parity alike;
- `relay.stop()`, unchanged;
- under the relay's lock again: the frame in flight (`_frame_packets`, `_frame_payload_bytes`, `_frame_timestamp`)
  and `_frame_bucket` cleared. After `stop()` the receive thread has been joined, so anything there was noted after
  the close; the new `start()`'s `stop()` would otherwise close it as a 1-packet row.
- `native_fec_relay.py`, `restart_fast.py` and `plugins/games.py` are not edited.

**Why it is the adopted behaviour byte for byte but the one packet:**
- `_client` is read only by `_send`; `stop()` sets it to None at its own end anyway, and `start()` sets it again.
- The cleared fields are reset by `start()`'s `stop()` / reset anyway. They are non-empty after the join only when
  the receive thread noted a packet after the close.
- The order, the timings, every row and every field are unchanged, and no new row or field is added. The only
  difference: what the receive thread forwards after the stop was called (the held packet, and its parity if it
  completed a group) is not sent, and the frame log has no 1-packet row for it.
- Absent the flag, the module is not imported (B24).

## Tests (`tests/restart_fast_unlock_relay/`, new; B24's file and B22's file unedited)

B24's harness (`Unlocked`, imported) with the **real** `NativeVideoFecRelay` on loopback (one fixed free port for
the old and the new relay, as in production), a fake onn (a UDP socket recording each arrival) and a fake old
encoder (a thread sending 14-packet frames at 60 fps, an 8-byte unmarked first packet, the marker on the last;
SSRC A).
1. **8 bytes at exit:** the fake encoder sends one 8-byte unmarked packet when SIGTERMed. **0 old packets
   forwarded after the stop's call**, and no 1-packet row in the frame log. This passes without the fix too: the
   socket is already closed. That is the settlement's point.
2. **CL-B14's window, production target:** a fake shim whose `stop()` holds the relay's lock for 50 ms (as the
   real shim's join), sending straight to the fake onn. **0 packets of any old frame begun after the stop's call
   forwarded;** no 1-packet row in the frame log. A mutation (the fix removed) must fail it.
3. **CL-B14 reproduced:** the real `none@post-fec` shim. Without the fix the frame log shows the 1-packet,
   8-byte, unmarked row in its own bucket, closed at the new start, and the fake onn does not receive it; with
   the fix there is no row and nothing received.
4. The new encoder's frames are forwarded after the restart (the relay works); `restart_fast_done`'s fields are
   the same set as B24's.
5. Plus B24's 10 and B22's 13 unedited and green; every `tests/` suite green in the /tmp copy.

**Proof (flag absent and `=1` but the one packet):** `restart_fast_unlock.py`'s AST, with the `_stop_relay`
method removed and its call put back as `m._fec_relay.stop()`, equals HEAD's. `native_fec_relay.py`,
`restart_fast.py` and `games.py` are sha256-identical to HEAD.
