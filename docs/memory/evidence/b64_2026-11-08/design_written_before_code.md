# B64 — design, written before any B64 code (the stale pre-session `pad_slots` rows)

Queue: `handoffs/QUEUE_2026-11-08W.md` §B64. Built after B63 in `/tmp/b_q15w_work` (the diff is against the after-B63
snapshot). Host logging only, no behaviour.

## 0. Settled (HOME-7's recovery log, 21:55-22:37Z, read in place)

- **Every start after the first** is followed by one `pad_slots` `change` row:
  - `heartbeat_sequence` **1**, state `ENDED` (before `session_started`);
  - **the previous game's `players_joined`**, with labels `P1…` but **no `claimed_by` on any slot**.
  - **14 of 14** starts with a previous session show it. For example, C16's 1-player title read `joined 2` (C15's
    count), and C23's restart read `joined 3`.
  - The real joins follow, with claims (`claimed_by: prompt`), from seq 2 or later; some also fall before
    `session_started`, so the state alone does not tell stale from real.
- **Where it comes from:**
  - the host's `SlotsLog.start` (at `native-stream-start`) writes the client's map with no join fields (the start
    query carries none) and resets `last_joined` to None;
  - the client's first heartbeat then sends the count its prompt still holds from the last game (its process-level
    carry-over) before the new prompt has claimed a pad;
  - the host sees a change and writes it.
- **The order on the client is a client change (an APK), not built.** The host fixes what it writes.

## 1. The fix: the row tagged `stale: true` (and not taken as the session's count)

- **`SlotsLog`** keeps `since_start` (set by `start`, cleared by the first row carrying a claim, or `players_joined`
  0).
- **A heartbeat change while `since_start` holds, with `players_joined` > 0 and no slot carrying `claimed_by`:**
  - the recovery row gets **`stale: true`**, and the heartbeat row `pad_slots_stale: true`;
  - **`last_joined` is not updated from it,** so the first real join is still a change row, compared with the start's
    None.
- **Everything else is unchanged:**
  - a client without claims (B34-B46 era, no `pad_claims`) never sends `players_joined`, so it is never tagged;
  - rows after the first claim are never tagged;
  - the start row is unchanged.
- **Disclosed:** a real pre-claim count (none exists in the client's flow: a join always comes with a claim) would be
  tagged too.

## 2. Tests (`tests/b64_stale_pad_rows/`)

- **HOME-7's sequence replayed:** start (no join) → seq 1 `joined 2`, no claims → `stale: true`, and the heartbeat
  values `pad_slots_stale` → seq 3 `joined 1` + claims → a change row without `stale` → seq 4 `joined 2` + claims →
  not stale.
- **A restart replayed:** a second start → its seq-1 carry-over → tagged again.
- **Not tagged:**
  - a client with no `players_joined` key (B46's rows byte for byte);
  - `players_joined` 0;
  - a row with claims before `session_started` (C23's 22:33:30 row).
- **Mutation:** the tag condition dropped (every pre-claim row untagged) → caught.
