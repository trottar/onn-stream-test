---
memory_schema: 1
as_of: 2026-11-07
status: G-A13 (host half) ADOPTED (the user's "Reconnect by default yes", 2026-11-06; the host half now, 2026-11-07): PRIVYHUB_VOD_LOG=1 is the FIFTEENTH adopted line (vod-log.conf). --check ok on fifteen; one local range request wrote one row. The client's retry default comes in B's queue O. Session A 2026-11-07 17:41-17:46Z. Nothing else adopted; nothing committed
---

# G-A13 (host): `PRIVYHUB_VOD_LOG=1`, the fifteenth line

Task: `handoffs/G9-CHECKPOINT_AND_G-A13_TASK.md` §1. The decision rests on HOME-3 C5''
(`HOME_3_DEFAULTS_PROMPT_VOD_2026-11-06.md`): with this line set in the bench drop-in, a `drop 45` reconnected and
resumed at the position and a companion restart with the movie open resumed in 3.6 s; these rows were the evidence.
B35's host half (`companion/vod_log.py`), widened by B43. Directory: `g_a13_2026-11-07/`.

## 1. Precondition (17:41Z; `preconditions.txt`, `check_before.json`)

All met: fourteen lines; `--check` ok, `8ba4d996…` CONFIRMED; `privyhub-diag` active; no `e3_flag.conf`; no game;
**no movie** (no connection on the range server or the control API; the onn on its screensaver); one device paired,
identity v2, Hub host empty; the newest `token_issued` lan; 5 GHz; the eleven properties empty; the companion and
`privyhub-diag` only; HEAD `953231d6` (HOME-3 committed). **The tree** held the prompt and this task's file, and also
the user's `_cowork_prompt_b.txt` (modified) and `handoffs/QUEUE_2026-11-07O.md` (untracked): B's queue O, not this
task's, left untouched.

## 2. The adoption diff (`patches/G-A13_VOD_LOG_ADOPTION.md`, `g_a13_applied.diff`)

- **The form** is G-A10's applied form: `tools/e1_suite.py` defines `VOD_LOG` (the comment `G-A13 (adopted
  2026-11-07, the user)`) and puts it in `ADOPTED`, making **fifteen**; the preflight reads `drop_in_vod_log` and
  requires it in `ok`; `e3_state.py`, `e1_remote.py`, `test_e1_remote.py` wording only; `ADOPTED_E3` as it is.
- **Checks:** predecessor and after sha256 recorded; `git apply --check` OK, then applied; the tree's hunks equal the
  applied diff's (only the hunk headers' function context differs); `git diff --check` clean.
- **Tests, green from the tree** (`tests.txt`): `e1_suite --self-test` OK; `test_e1_remote` 21 OK;
  `test_c3_l4_nft_night` 33 OK; `tests/vod_log` 12 OK (a first invocation with `-t .` failed to import the start
  directory: an invocation error, not a test; rerun as `discover -s tests/vod_log`).

## 3. The drop-in and the restart

- **The drop-in** `~/.config/systemd/user/privyhub-companion.service.d/vod-log.conf`, written with the file tool
  (`vod-log.conf.copy`): `[Service]` / `Environment=PRIVYHUB_VOD_LOG=1`.
- **The restart:** `daemon-reload` and the restart as their own command at 17:43:52Z, with no game and no movie
  (re-read just before).
- **Fifteen lines read back** in the companion's environ (`environ_after_restart.txt`); the range server, a child,
  inherits it.
- **`--check` ok on fifteen:** `drop_in_vod_log` true; APK CONFIRMED (`check_after_restart.json`). The journal since:
  no error or traceback.

## 4. The confirmation (no player, no user)

- One `GET` with `Range: bytes=0-1023` from the hub to its own range server, for the first movie file over 1 MB; the
  response (206, 1024 B) discarded (`vod_request.txt`; no address, path or title written).
- **One row** in `logs/vod_range.jsonl` (`vod_range_row_redacted.jsonl`, the `id` redacted):
  `range` `bytes=0-1023`, `status` 206, `length` 1024, `bytes` 1024, `duration_ms` 3, `closed` `complete`.
- `vod_client.jsonl` rows come only from a client with the retry on; the onn's `vod_retry` is empty until queue O's
  default, so none are expected now. `privyhub-diag` copies both files.
- `PRIVYHUB_VOD_DROP_TEST` stays off (never a line).

**The cost:** one JSON row (~260 B) per range request, written when the request closes. A movie playing straight makes
a handful (a few per start or seek, one per reconnect: HOME-3's whole C5'', with a drop and a restart, wrote 21 rows,
5.4 kB). The file rotates at 5 MB × 3 (≤ 15 MB). No per-frame or per-byte work beyond a counting write wrapper.

## 5. The state now

- **The fifteen adopted lines:** the fourteen of `G_A10_…` §5, and **15. `PRIVYHUB_VOD_LOG=1` (`vod-log.conf`,
  G-A13 host).**
- **Checks:** `--check` ok on fifteen (`check_end.json`); APK `8ba4d996…` CONFIRMED; no `e3_flag.conf`; the eleven
  client properties empty (`properties_end.txt`).
- **Units:** only `privyhub-companion` and `privyhub-diag` (`units_end.txt`).
- **Off:** delete `vod-log.conf`; `systemctl --user daemon-reload`, then `systemctl --user restart privyhub-companion`;
  reverse `g_a13_applied.diff`. The range server then writes no rows; the client is unchanged.
- **A note for B's bench drop-ins:** a drop test now needs only `PRIVYHUB_VOD_DROP_TEST=1` in its drop-in (the log is
  already on).
- **Disclosed:** one empty temp file (`vod-log.conf.tmp`) was created and removed in the same command before the
  drop-in was written with the file tool; nothing pre-existing was removed.
