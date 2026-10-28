# B27 — design, written before the replay and any code (QUEUE_2026-10-27J item 2; the user's "Also adopt", 2026-10-27)

## What the guard needs from the host (from the code; settled before the design)

- **The client alone does the guard's work.** On a dropped access unit (outside a resync's own IDR wait), no
  non-IDR frame is queued until the next complete IDR, so the surface shows the last good frame. The wait is capped
  at 600 ms, after which frames pass, counted as `loss_guard_timeouts`. The counters go into the report and the
  heartbeat. The natural IDR comes every 15 frames (250 ms).
- **What `PRIVYHUB_LOSS_GUARD=1` adds on the host** (`plugins/games.py`, `keyframe_request.py`):
  - the client's 24-byte `PHK1` request (one per episode) is parsed, counted and rate-limited (one per 500 ms acted
    on), and `control.force_idr()` is called. Today's control is `NoRuntimeIdr`, which **forces nothing**: there is
    no runtime IDR path, as settled in B10 §0.3;
  - a per-minute `keyframe_requests` row and a `loss_guard_config` row;
  - the heartbeat's three loss-guard fields recorded in `native_stream_heartbeat.log`.
- **Without the host flag:** the `PHK1` datagram reaches the controller receive loop, is 24 B ≠ 36, and counts one
  `bad_packets` (in the controller status). It is discarded with no other effect. The heartbeat's fields are not
  recorded by the host, and the client's report still carries the `loss_guard_*` keys (the host stores the report
  body whole).
- **So the cost, with or without the host flag, is the same picture:** a freeze of up to ~0.25 s per episode (cap
  0.6 s) in place of the frames drawn from a lost reference. BENCH-R3 E-on: hitch seconds 125.7 against 68.8 per
  10 min, rendered fps 55.2 against 57.8 at 1 % post-FEC loss.
  - The host flag buys only the host's own count of the requests (and no `bad_packets` for them). It never buys a
    shorter freeze today.
  - With B7's stall signal on by default (B19), a freeze ≥ 150 ms also sends a stall datagram. No adopted host line
    acts on it (it is a bad packet too without `PRIVYHUB_STALL_SIGNAL`).

## The replay first (read-only), before the default flips

**Sources:** every client report (`logs/games/decoder_sessions/native_decoder_*.json`) received since CL-B10's first
cell (2026-10-23T18:42:13Z) to now. G4-S4's span (2026-10-24T19:15Z – 2026-10-25T17:40Z, before the onn came home)
is off-site; the rest is the LAN. Only read.

**B10's rule on a report.** The guard holds the non-IDR frames between a dropped access unit and the next complete
IDR (`frames_after_dropped_reference`; `held` when on), capped at 600 ms. The reports carry no per-drop timeline.
For a report without `loss_guard_mode` the replay is therefore a bound from its counters, stated as one. For a
report that carries the guard's own keys (any property set), the counters are used as they are.
- drops `D = sequence_gap_au_drops + incomplete_au_drops`. Some may sit inside a resync's wait, which the guard does
  not count, so this is an over-count;
- the GOP `G = encoder_gop_frames` (15); the GOPs in the session `N ≈ idr_frames`;
- episodes `E ≤ min(D, N + 1)`: drops inside one GOP are one episode;
- **frames held:**
  - upper `≤ E × (G − 1)` (14 per episode with the next IDR intact);
  - estimate `E × 7.64` (BENCH-R3 E-on's measured 3,010 / 394 per episode), stated as an estimate;
  - lower 0;
- **the longest hold:** with `M = max_frames_between_idr` (delivered frames between two IDRs), a hold lies inside
  one such run, so the longest is `≤ min(M − 1, 36)` frames. 36 is the 600-ms cap at 60 fps. Times are ×16.7 ms;
  with `D = 0` it is 0.
- **Any session with a possible hold > 0.5 s** (`D > 0` and `min(M − 1, 36) ≥ 30`, i.e. ≥ 2 IDRs lost in a row) is
  listed with its counters. A session whose `M` comes from a resync wait is flagged as such.

Output: `replay_loss_guard.py`, `replay_output.json`, `replay_table.md` (per session: start, LAN / off-site, duration,
`D`, `E` bound, held upper / estimate, longest-hold bound, the > 0.5-s flag), and totals for the LAN and for G4-S4.

## The client: absent / empty / junk = ON, `0` off (as B19 / B25)

- `LossGuardFlag.parse`: `"0"` → null (off, today's absent byte for byte), `"count"` → COUNT (as before), anything
  else → GUARD (absent, empty, junk, `"1"`). `fromSystem()` on a failed read → GUARD, i.e. `parse(null)`.
- Nothing else changes: `LossGuard`, the receiver, the activity, the sender, the report and the heartbeat already
  follow the object.
- **Tests:** `LossGuardDefaultOnTest` (new):
  - the table;
  - absent → GUARD, and the real receiver on loopback (B10's I P P [lost] P P P P I P) queues I P P I P, counter 3,
    held 3, one request;
  - `0` → null, and the same stream queues today's I P P P P P I P with no request and no report keys (today's
    absent, byte for byte);
  - `count` as before.
- **B10's flag lines moved, disclosed:** `LossGuardTest.flagTable`'s `null` / `""` / `"on"` / `"guard"` / `"2"`
  lines now give GUARD, `"0"` stays null, and `fromSystem()` off-device gives GUARD. Its other tests are unedited.
- A mutation (B10's parse put back, in a copy) must fail the new tests.
- **Proof (`0` = today's absent):** `LossGuard.kt` differs from HEAD only in `LossGuardFlag`'s `parse` /
  `fromSystem` bodies (and their comment). `parse("0")` and HEAD's `parse(null)` both give null, and with null no
  object is built.
- **APK:** B5 … B25 + B27, built offline in a fresh /tmp copy with `--no-configuration-cache`, pinned, NOT installed.
  Same signer as `fcd924c2…`; only the dex that holds `LossGuardFlag` should differ.

## The host: G-A8 PREPARED, nothing applied

`patches/G-A8_LOSS_GUARD_ADOPTION_PREPARED.md` in G-A7's applied form:
- `tools/e1_suite.py`: `LOSS_GUARD = "PRIVYHUB_LOSS_GUARD=1"` with its comment, `ADOPTED` to thirteen, the preflight's
  `drop_in_loss_guard` and its `ok` term;
- `tools/e3_state.py`, `tools/e1_remote.py`, `tools/test_e1_remote.py`: the wording ("thirteen lines since G-A8");
- the drop-in `loss-guard.conf` text, off steps, the predecessors' sha256 (the tree's current files, G-A7 applied);
- the diff made in a /tmp copy and checked with `git apply --check` against copies of the files, never against
  the tree.
