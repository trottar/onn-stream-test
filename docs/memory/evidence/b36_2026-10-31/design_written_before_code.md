# B36 — the always-on diagnostics keeper: design, written and hashed before any B36 code

Queue: `handoffs/QUEUE_2026-10-31L.md` §B36. Base: HEAD 1904fe8, copy `/tmp/b_q31l_b36`. B30's
`tools/trip_log_keeper.py` is **not edited** (the running `privyhub-trip-log` imported it at its start; the file stays
byte for byte). `tools/trip_check.py` is **not edited and not removed** (the runbook tells the user to run it from the
friend's house; nothing is deleted). Everything below is new files only: `tools/diag_keeper.py`, `tools/diag_read.py`,
`tools/diag_check.py`, `tools/privyhub-diag.service`, `tests/diag_keeper/`, `tests/diag_read/`, `tests/diag_check/`.

## 1. `tools/diag_keeper.py` — the permanent keeper (`privyhub-diag`)

- **Reuse:** imports B30's `Redactor`, `Tail`, `overlay_state`, `session_state`, `online_peers`, `read_journal`,
  `GAMES_TAILS`, `TOP_TAILS`, `NEWDIRS`, `GAME_LOG` from `trip_log_keeper` (so `trip_log_keeper.py` must stay in the
  tree while `privyhub-diag` exists — stated in the record). `DiagKeeper` subclasses B30's `Keeper` and overrides
  only where the output place, the cap, the summary and retention differ.
- **Sources:** B30's exact lists (G4-S4's: the ladder, heartbeat, recovery, control-gap, frame-size, host-sampler,
  audio and video logs in `logs/games/`, following rotation by inode into `stream_log_archive/<log>.1..3`; the hub's
  `wan_sessions` / `session_audit` / `impairment` rows; each game log from its first byte; new files in
  `decoder_sessions/` and `audio_timing/` once each; the companion's journal) **plus** the two new top-level rows of
  B35: `logs/vod_client.jsonl` and `logs/vod_range.jsonl`. The client's new rows of B32 / B34 / B33 / B32-host
  (`surface_lost`, `pad_slots` in the recovery log; `pad_slots` on heartbeat rows; `input_release` `why`; ladder
  `transition` `in_place`) arrive inside logs already tailed — nothing extra to copy, the reader reads them.
- **Where:** a root `~/privyhub_diag/` (default; `--root` to change; **refused if it resolves inside the repo**). Each
  copy and sample goes into the **UTC date's day-dir** `<root>/<YYYY-MM-DD>/` (`raw/<log>/<NNNNNN>_<UTC><ext>` never
  overwritten, `samples/{overlay,session,copies}.jsonl`, `manifest.sha256` growing) — B30's layout per day, so
  `diag_read` reads a day-dir and the trip dir the same way. The tails are one set across days (a day boundary is not
  a gap). At the root: `status.txt` (one line), `STOP` (touch to end), `state.json` (each tail's inode + offset and the
  seen-file sets, rewritten atomically after each copy, so a unit restart or a reboot resumes where it left off when
  the inode is the same, else from the file's current end as B30), `sessions.jsonl`, `retention.jsonl`.
- **Cadence:** copies every 300 s, samples every 60 s (B30's), **no cap** (permanent: it runs until `STOP` or the unit
  stops; a final copy on SIGTERM/STOP). Nothing held open between steps; no stream, no restart, no adb, no game.
- **Redaction:** every kept chunk, sample row and summary row through B30's redactor (the tailnet's names, the
  nodes' names / addresses / endpoints, the host's addresses, the paired devices' ids and keys, any IPv4 / IPv6 /
  MAC / client id / long hex literal), refreshed every copy, counted per kind, no value printed.
- **Retention (the one deletion this tool makes, stated):** once at the start and at every UTC date change, every
  entry **directly under the root** whose name matches `^\d{4}-\d{2}-\d{2}$`, **is a real directory (not a symlink)**,
  and whose date is **more than 30 days before today's UTC date** (`date < today − 30 d`) is removed whole
  (`shutil.rmtree`). Nothing else is ever deleted: not files at the root, not other names, not anything outside the
  root. Each removal is one row in `<root>/retention.jsonl` (the dir name, its file count, when).
- **The per-session summary (`<root>/sessions.jsonl`):** the keeper tails the live recovery log every sample step (its
  own read-only `Tail`, separate from the copy's). Each `session_ended` row seen schedules the session's summary
  **90 s later** (the client's decoder report and the WAN row that closes after the session's end must arrive first).
  The summary is computed by `diag_read`'s own session reader over the live logs (`logs/games/*` + the rotated
  archive, the decoder reports, `wan_sessions.jsonl`, the overlay samples) for the 3 h before the end, picks the
  session whose end is that `session_ended`, and appends one redacted JSON row:
  `start_utc, end_utc, length_s, core, title (class + tag), players, slot_map, path_class, rung_history, rungs,
  start_rung, lost_post_fec, rtt_p50_ms, rtt_p95_ms (the control echo), rendered_fps_med, rendered_fps_min, resyncs,
  pauses [time trigger], holds, stalls [time age_ms], rewinds [time method why], restarts [time trigger paused_ms
  away_ms], surface_lost [rows], end_kind, hitch_s, hitch_by {R,C,G,L}, hitch_s_per_10min, silences, silences_user,
  silences_per_10min, max_silence_ms, underruns, starvation, rssi`. `players` / `slot_map` come from B34's `pad_slots`
  (row or heartbeat key) and are `null` when the client sent none (today's client: TRIP-R2 §0). A summary that fails
  writes a row with `error` (the type only), never stops the keeper.
- **The unit** `tools/privyhub-diag.service` (a user unit, for A to install at home; nothing installed here):
  `ExecStart=/usr/bin/python3 -B %h/Projects/onn-stream-test/tools/diag_keeper.py`, `Restart=on-failure`,
  `Nice=10`, `WantedBy=default.target` — autostart as the companion's H3 (`systemctl --user enable --now
  privyhub-diag`; linger already on for the companion).

## 2. `tools/diag_read.py <range>` — the one-line read

- **Ranges:** `last night` (yesterday 17:00 → today 08:00, the hub's local time), `today` (local 00:00 → now),
  `YYYY-MM-DD HH:MM..HH:MM` (UTC; an end not after the start is the next day), `YYYY-MM-DD HH:MM..YYYY-MM-DD HH:MM`
  (UTC), `trip` (the trip keeper's dir `docs/memory/evidence/trip_2026-10-30/`, from its first to its last row).
- **Sources:** by default the day-dirs of `~/privyhub_diag/` that overlap the range (±1 day); `trip` reads the trip
  dir; `--source DIR` (repeatable) reads any keeper-shaped dir (a day-dir, the trip dir) or TRIP-R2's `copies/` shape;
  `--live` reads `logs/` directly (what the keeper's summary uses). Chunks are joined per log in day then chunk order.
  **Read-only:** the sources are opened for reading only.
- **The logic is TRIP-R2's `trip_r2_read.py`, copied and parameterised** (the window, the sources, the title tags; no
  import from `evidence/`): the client sessions from the recovery log (`remote_config` → class, `session_started`,
  `session_ended`, `session_end_bye`, `restart_fast`, `gave_up_saved`); UX-R3's hitch definition unchanged (R < 50 fps,
  C control gap ≥ 250 ms not the user's, G output gap ≥ 200 ms by the ladder sample or the client report's top-16 gap
  placed by the client's clock, L ≥ 30 lost after FEC); the RTT from the WAN row closed between the session's end and
  the next start; title class + tag from the game logs' names (local time → UTC by the hub's zone; the trip's tags as
  known, else `<SYSTEM> <4-hex>`).
- **Output:** one Markdown file `docs/memory/evidence/reads/diag_<label>_<generated UTC>.md` (or `--out`), never an
  existing name: the range and the sources; **the per-session table** (G4-S4's columns as in §1 + players / slot map);
  **the per-10-min table** (TRIP-R2's); **every restart / rewind / pause / hold / stall with its cause** (restart: the
  client's `restart_cause` trigger and paused / away ms from the next report, B32's `surface_lost` reason and keys
  when present, the uplink silence and stall in the 10 s before, the rung before → after, the last step-up's Δt and
  whether it was in the same session; rewind: `input_release` method and B33's `why`; pause: the trigger); the ladder
  transitions with `in_place`; the B34 `pad_slots` rows; the B35 VOD rows and the range log's per-request summary;
  **the ±60-s per-second view** (the seconds with any row, TRIP-R2's columns) around every restart, every stall,
  every `state_saved` mark with `--around-saves`, and every `--around HH:MM:SS` / `YYYY-MM-DDTHH:MM:SS`.
- **The standard reads:** the per-session table carries G4-S4's columns and UX-R3's hitch seconds; the dry run (§4)
  reproduces TRIP-R2 §1. UX-R3 / UX-R4 / G4-S4's own windows are re-run only if their logs are still on disk (the live
  logs rotate; if they are gone, the record says so rather than claiming a reproduction).

## 3. `tools/diag_check.py`

`tools/trip_check.py`'s six lines, copied, with the sixth line now `diag-keeper:` from `~/privyhub_diag/status.txt` and
`systemctl --user is-active privyhub-diag` (and `--root`); the redactor on every line. `trip_check.py` stays as is.

## 4. Tests and the dry run

- `tests/diag_keeper/`: a fake `logs/` tree that rotates (B30's fixture shape) + a fake clock: chunks go to the right
  day-dir and roll at UTC midnight without losing a byte; the two VOD logs are copied; redaction applied; `state.json`
  resumes a second keeper at the saved offset (same inode) and from the end (new inode); a `session_ended` → one
  `sessions.jsonl` row 90 s later with the columns (and `slot_map` from a `pad_slots` row; `null` without one; the
  restart's trigger from `surface_lost`); retention in a `/tmp` test root: dirs 31+ days old removed, 30 / today kept,
  a non-date name, a file named like a date, and a symlink named like a date all kept; `--root` inside the repo
  refused; STOP ends it with a final copy.
- `tests/diag_read/`: the range parser (last night / today / the UTC forms / trip) with a fixed clock and zone; a fake
  keeper dir with two sessions, a restart, a stall + rewind with `why`, a pause, an in-place transition, a `pad_slots`
  row, VOD rows → the tables and sections; the output never overwrites.
- `tests/diag_check/`: the six lines, the sixth naming `privyhub-diag`.
- Mutations: ≥ 1 caught (retention's age test off by one; the summary delay ignored).
- **The dry run (read-only):** `diag_read.py --source docs/memory/evidence/trip_2026-10-30 "2026-10-30 21:00..06:10"`
  and `trip`, output to `evidence/b36_2026-10-31/` — TRIP-R2 §1's six restarts compared cell for cell (time, session,
  title, rung before → after, last step-up Δt, the client's cause, paused / away ms, the silence / stall before); the
  joined recovery log compared byte-for-byte with TRIP-R2's `copies/` prefix.

## 5. Not done here

No unit installed or started, no `~/privyhub_diag/` created outside tests (the tests use `/tmp`), no live log read
by the tests; the companion, the trip keeper and its dir untouched.
