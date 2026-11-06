---
memory_schema: 1
as_of: 2026-11-06
status: HOME-2 DONE (session A, 2026-11-06 16:30-16:56Z; the user at the TV for stages 2-5). Queue M's APK `0132b944…` installed with every property empty; C1' MET, C4' MET, C5' NOT MET (valid); `0132b944…` CONFIRMED and the pin moved. G-A11 and G-A12 are the user's questions; G-A13 back to B. Nothing adopted; nothing committed
---

# HOME-2: the hold, the pads, the movie

Task: `handoffs/HOME-2_HOLD_PADS_VOD_TASK.md`; B's strings: `handoffs/SESSION_B_DONE_2026-11-02M.md` §A items 1-6.
The directory is `home2_2026-11-03/` (named for the task's date; run 2026-11-06): `stage1/`, `c1/`, `c4/`, `c5/`,
`close/`, `pin/`, `preregistration.md` and its `.sha256`, `redact_check.txt`, `manifest.sha256`. Times are UTC.

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- Then: "Stage 2", "Stage 3", "Stage 4", "Go".
- C5': "Drop"; then "I don't see that"; "Try again"; "Back, nothing it just went back? What?".
- Stage 5: "Stage 5 I saw nothing, just the movie".
- After the close: "Reconnecting showed up and now a playback error connection to hub lost".
- Then: "I hit retry and it was stuck reconnecting. I heard stopped the movie then resumed".

## Stage 1: the install (`stage1/STAGE1.md`)

- **Preconditions met:** fourteen lines; `--check` ok with `fcd924c2…` CONFIRMED; `privyhub-diag` active; no
  `e3_flag.conf`; no game; one device paired (identity v2, Hub host empty); the newest `token_issued` lan; 5 GHz (5180
  MHz); the ten properties empty; only the companion and `privyhub-diag`; HEAD `1f7a6fd8`, the tree clean.
- **Pre-registration** `preregistration.md` (sha256 `4d42eb50…6b8f`), hashed 16:31:46Z, before the install.
- **The install** (16:32Z): `queue_m_built/` → `home2_installed/`, sha256 `0132b944…e24f` = B's, the signer the same
  as `fcd924c2…`'s; `adb install -r` Success; read back, paired, the ten properties empty. `fcd924c2…`
  (`cl_b14_installed/`) and `554ccf61…` (`home1_installed/`) preserved.
- **The companion restart** 16:32:10Z: queue M's host code live; `--check` MISMATCH on the APK only until stage 5.

## The cells, beside HOME-1's

| cell | HOME-1 (2026-11-02, `554ccf61…`) | HOME-2 (2026-11-06, `0132b944…`) | result |
| --- | --- | --- | --- |
| **C1 / C1'** the hold (`surface_hold=1`) | the hold kept the session (`held`, away 4429 ms), but the report read `held` 0, `losses` 0, `duration_ms` 16270 (start → first loss); the guide key became Home | `surface_lost` `held`, `away_ms` **3451**, `reason: user_leave`; no `restart_fast` / `session_ended`, heartbeat 1 → 23 continuous; the exit's report **`held` 1, `losses` 1, `restarted` 0, `duration_ms` 51066** (the whole session) | **MET** (valid) |
| **C4 / C4'** two pads (`pad_slots=stable`) | `count` 3: the onn's virtual-remote took slot 0; `updates_by_player` rose equally on all four | both starts `count` **2**, slots 0 / 1 `sony`, the same two hashes, **no `google` entry**; slot 0 = controller number 3 (the lower), slot 1 = 4; pad A only → `updates_by_player` [0,0,0,0] → **[11,0,0,0]**, pad B only → **[11,6,0,0]**, `packets_by_player` rising on all four; `/status` `changes_by_player` **[11,6,0,0]**; property empty → no `pad_slots` row or key in 57 heartbeat rows | **MET** (valid) |
| **C5 / C5'** the movie drop (`vod_retry=1`, `PRIVYHUB_VOD_LOG=1`) | INVALID: the Wi-Fi was turned off from the onn's settings, so the player had left | B40's drop twice with the movie in front: `vod_drop_injected` **`dropped: 1`, `how: rst`** both times; `client_reset` with bytes < length; then **`bytes=13910928-` 206** 12.8 s later. **No `vod_error` / `vod_retry` / `vod_resumed`, no `vod_client.jsonl`, no "reconnecting…"**: the player's own loader reopened the stream and played on; no player error, so B35 never ran | **NOT MET** (valid) |

Each cell's file: `c1/C1.md`, `c4/C4.md`, `c5/C5.md`. Every cell: the ten properties read back with only its own set,
and empty after.

- **C1' note:** the user's first game began before the property was set (it is read at the activity's creation), so
  they relaunched; that first session's report has no `surface_hold` object (today's behaviour).
- **C5' note:** a single reset cannot reach B35 while the hub answers: the movie must stay unreachable long enough
  for the player's own retries to give up. The user saw the movie unbroken ("I saw nothing, just the movie").

## The close (`close/`)

- `b40-vod-drop.conf` removed, `daemon-reload`, restart (16:53Z); `vod_retry` cleared; **all ten properties empty**.
- Fourteen drop-ins; no `e3_flag.conf`; **`flags_absent: true`** (`flags_absent.json`, e1_suite's own terms).
- `privyhub-companion` and `privyhub-diag` active; `diag_check`: 14 lines, host check ok, 5 GHz, keeper running.

## The CONFIRMED rule (CL-B7 §6, as pre-registered)

- **Every cell that ran was valid:** C1', C4' and C5' (C5' with `dropped: 1`, the movie in front, nothing pressed).
- **Today's behaviours where no flag was set:** C1's first session (property empty) wrote no hold object; with
  `pad_slots` empty no `pad_slots` row or key and no `packets_by_player`; the movie's recovery from a reset is the
  player's own, the same with or without the flag; the seven defaults unchanged; `--check` ok and `flags_absent` at
  the close.
- **So `0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f` is CONFIRMED.** C5' not met bears on its
  question, not on the rule.
- **The pin moved** (`pin/`: `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `home2_pin.diff`, `git diff
  --check` clean): `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test.
  Tests (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK.
- **`--check` ok, APK CONFIRMED** on fourteen lines (`close/check_end.json`); the client read back paired, identity
  v2 (`close/client_end.json`).

**On the onn now:** `0132b94430d40e4e5ae78d2679fbee085f4f44273a804bc0ce8dcd040bdae24f` (queue M's), CONFIRMED, every
property empty: the hold, stable slots and the movie retry are all off until a default is chosen.

## The reading: the user's questions (B's words, only for cells met)

**G-A11 (C1' met).** "Turn the screen-loss hold on by default in the next APK (`debug.privyhub.surface_hold`)? A Home
press, a guide press or a system panel of up to 12 s then keeps the session." C1' met every row: a 3.5-s Home kept the
same session, and the report now counts it (`held` 1, `losses` 1, `restarted` 0) over the whole session's duration.

**G-A12 (C4' met).** "Turn stable player slots on by default (`debug.privyhub.pad_slots=stable`)? Real pads keep their
player number across launches; the onn's remote never takes one." C4' met every row: two pads in slots 0 and 1 both
times regardless of press order, the remote in no slot, and the host counts only the pad that moved.

**Not asked; back to B with the rows:**
- **G-A13 (C5' not met):** the hub's reset was real and the movie survived it, but by the player's own reconnect; the
  retry (B35) was never reached, so whether it works is still unmeasured. B40 needs a drop that outlasts the player's
  own retries.

**After the close (`c5/C5.md` addendum).** The movie was still playing when the session restarted the companion
for the close (16:53:44Z; an open movie connection was there and the session restarted anyway: a session error). The
restart ended the movie's media token; every reconnect got 401. B35 then ran (the flag was read at that playback's
start): "reconnecting…", ~2.5 min of retries all refused 401 with the hub up, then "Playback error" / "connection to
hub lost". The error screen's Retry was refused 401 too; only stopping and restarting the movie (a new token,
17:00:02Z) played again. So B35 surfaces and retries, but cannot survive a companion restart (it keeps the dead token) and names a
401 as a lost hub. Both go to B with C5'. The CONFIRMED rule is unchanged (a flagged player).

`PRIVYHUB_VOD_DROP_TEST` is never a question. Later items: the guard's return (G-A8 the prepared candidate); the G9
checkpoint draft.
