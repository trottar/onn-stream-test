---
memory_schema: 1
as_of: 2026-11-07
status: HOME-3 DONE (session A; stage 1 2026-11-06 23:45-23:48Z, stages 2-7 2026-11-07 16:41-17:12Z, the user at the TV). Queue N's APK `8ba4d996…` installed with every property empty; C1'' MET, C4'' MET (both off checks met), C6 NOT MET (valid; the user's requirement to B), C5'' (b) MET and (a) met on behaviour with two rows short; `8ba4d996…` CONFIRMED and the pin moved. G-A13 the user's question (with the disclosure); the prompt's default not asked. Nothing adopted; nothing committed
---

# HOME-3: the defaults, the prompt, the movie

Task: `handoffs/HOME-3_DEFAULTS_PROMPT_VOD_TASK.md`; B's strings: `handoffs/SESSION_B_DONE_2026-11-06N.md` §A items 1-8.
The directory is `home3_2026-11-06/` (named for the task's date): `stage1/`, `c1/`, `c4/`, `c6/`, `c5/`, `close/`,
`pin/`, `preregistration.md` and its `.sha256`, `LABELS.txt`, `redact_check.txt`, `manifest.sha256`. Times are UTC.
Pad hashes and the movie id are replaced by labels in every copied row (`LABELS.txt`).

## The user's lines (verbatim)

- Stage 1: "Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- "Stage 2"; "Stage 3" (sent before the exit; resent after it); "Stage 3b"; "Stage 4"; "Fine I'll do another game";
  "Stage 4b".
- C6: "There is no prompt"; "It should pop up every time a game is active or unpaused. It's like the connection
  diagnostics, it's to assure consistency and reliability each play session"; "1-4 didn't happen"; "You also ignored
  my comment"; "1-4 worked as expected now"; "Stage 5".
- C5'': "Drop"; "Cool worked. It went from pause to play but reconnecting still was in the corner. Play worked as
  expected though"; "Stage 6"; "Stage 7, reconnecting showed it paused reconnecting disappeared and it played";
  "Movie off".

## Stage 1: the install (`stage1/STAGE1.md`)

- **Preconditions met:** fourteen lines; `--check` ok with `0132b944…` CONFIRMED; `privyhub-diag` active; no
  `e3_flag.conf`; no game; one device paired (identity v2, Hub host empty); the newest `token_issued` lan; 5 GHz (5180
  MHz); the eleven properties empty; only the companion and `privyhub-diag`; HEAD `d9fd9688` (queue N committed), the
  tree clean.
- **Pre-registration** `preregistration.md` (sha256 `5125ee74…b728`), hashed 2026-11-06 23:46:45Z, before the install.
- **The install** (23:47Z): `queue_n_built/` → `home3_installed/`, sha256 `8ba4d996…605f` = B's, the signer the same as
  `0132b944…`'s; `adb install -r` Success; read back, paired, the eleven empty. `0132b944…` (`home2_installed/`),
  `fcd924c2…` and `554ccf61…` preserved.
- **The companion restart** 23:47:20Z: queue N's host code live; `--check` MISMATCH on the APK only until the close.

## The cells, beside HOME-2's

| cell | HOME-2 (2026-11-06, `0132b944…`, flag set) | HOME-3 (2026-11-07, `8ba4d996…`) | result |
| --- | --- | --- | --- |
| **C1' / C1''** the hold | `surface_hold=1`: `held`, away 3451 ms; report `held` 1, `losses` 1, `restarted` 0 | **property empty**: `surface_lost` `held`, away **2567** ms, `user_leave`; no `restart_fast` / `session_ended`, heartbeat 1 → 115 continuous; report **`held` 1, `losses` 1, `restarted` 0**, 234088 ms. **Off (`0`):** `restart_fast`, no `surface_lost`, no hold object | **MET** (valid); off check met |
| **C4' / C4''** two pads | `pad_slots=stable`: `count` 2 both starts, no `google`; [11,0] → [11,6] | **property empty**: both starts `count` **2**, slots 0 / 1 the same two pads whatever pressed first, no `google`; pad A only [4,4] → **[20,4]**, pad B only → **[20,40]**; `packets_by_player` on all four. **Off (`off`):** no `pad_slots` row or key. Disclosed: the title had the multitap on | **MET** (valid); off check met |
| **C6** the prompt (`player_prompt=1`) | — | no prompt at a start while pads hold slots from earlier in the process (as B41 built it); a release with **Start held last re-takes the slot at once**; with Start first and Select last, B → P1, A → P2, release → P1 again, as written; `players` 2 / 4 / 1; `claimed_by` `prompt` / `stable`; the report's `players` / `pad_claims` | **NOT MET** (valid); to B with the user's requirement |
| **C5' / C5''** the movie (`vod_retry=1`) | B40's single reset absorbed by the player; B35 never reached; after a restart 401s → "connection to hub lost" | **(a) `drop 45`:** `dropped: 1`, `rst`, `refuse_s` 45, `vod_refused` 19; `vod_error` `reset` → 4 retries → **`vod_resumed`** at the same position, no "Playback error"; first row **23.1 s** after (B: ~30-35); the resumed range row unwritten; "reconnecting…" left on screen. **(b) restart:** `vod_retry` `401` **`token_refetched: true`** → `vod_resumed` 3.6 s; 401 × 7 then 206; no "lost"; the user saw it resume | **(b) MET; (a) met on behaviour, two rows short** (valid) |

Each cell's file: `c1/C1.md`, `c4/C4.md`, `c6/C6.md`, `c5/C5.md`. Every cell: the eleven properties read back with
only its own set, and empty after.

## The close (`close/`)

- `b43-vod-drop.conf` removed (after the user stopped the movie), `daemon-reload`, restart (17:11:18Z); `vod_retry`
  cleared; **all eleven properties empty**.
- Fourteen drop-ins; no `e3_flag.conf`; **`flags_absent: true`** (`flags_absent.json`, e1_suite's own terms).
- `privyhub-companion` and `privyhub-diag` active; `diag_check`: 14 lines, host check ok, 5 GHz, keeper running.

## The CONFIRMED rule (CL-B7 §6, as pre-registered)

- **Every cell that ran was valid:** C1'' and its off check, C4'' and its off check, C6, C5'' (a) (`dropped: 1`, a
  `vod_error` in the window) and (b).
- **Today's behaviours where no flag was set (B42's intended defaults aside):** `surface_hold` `0` → the restart and no
  hold object; `pad_slots` `off` → no `pad_slots` row or key; `player_prompt` empty → no `players` / `pad_claims` /
  `claimed_by`; the seven defaults unchanged; `--check` ok and `flags_absent` at the close. C6's and C5'''s findings
  are under their flags and bear on their questions, not on the rule.
- **So `8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f` is CONFIRMED.**
- **The pin moved** (`pin/`: `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`, `home3_pin.diff`, `git
  diff --check` clean): `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`, and its test.
  Tests (`pin/tests.txt`): `e1_suite --self-test` OK; `test_c3_l4_nft_night` 33 OK; `test_e1_remote` 21 OK. Patch note
  `patches/HOME-3_APK_PIN.md` (indexed).
- **`--check` ok, APK CONFIRMED** on fourteen lines (`close/check_end.json`); the client read back paired, identity v2.

**On the onn now:** `8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f` (queue N's), CONFIRMED, every
property empty: **the hold and stable slots on by default (G-A11 / G-A12, B42); the prompt and the movie retry off.**

## The reading

**G-A11 / G-A12 (C1'' / C4'' met):** the user's yes of 2026-11-06 is now shown working by default on the onn, with
`0` / `off` giving the old behaviour.

**G-A13 (C5''), the user's question, with the disclosure.** B's words: "Turn the movie retry on by default
(`debug.privyhub.vod_retry`) and adopt `PRIVYHUB_VOD_LOG=1`? A dropped movie, or a hub restart, then reconnects and
resumes by itself." (b) met every row. (a) met every behaviour row (the error surfaced, the retries ran, the movie
resumed at the position, no "Playback error"), but two pre-registered rows are short: the first row came 23 s after
the drop, not ~30-35 s, and the resumed `bytes=<P>-` row was never written (a log row lost at (b)'s restart). Strictly
by the pre-registration (a) is not met on every row; the user may answer now or send (a) back to B for a re-run.
`PRIVYHUB_VOD_DROP_TEST` is never a question.

**The prompt's default (C6 not met): not asked.** To B: the user's requirement (verbatim above): the prompt at every
game start and every unpause, like the connection diagnostics, whatever the slot map holds; and the held-Start re-claim
at release (filter key repeats on the claim). The open question for the user then: a 1-player title, prompt or none.

**Also to B:** "reconnecting…" left on screen after (a)'s resume (cleared in (b)); a VOD range row is lost when the
companion restarts with the request open.

**Next:** A — the G9 checkpoint (`handoffs/G9_CHECKPOINT_DRAFT_2026-11-06.md` applied to ROADMAP §G9 and CURRENT; the
hub-overlay-down local check and the clean checkpoint commit are the user's). B — H0 slice 1a (PS1 inspect + dry run +
manifest), after B45's four questions to the user: a real BIOS or OpenBIOS; an `.m3u` for multi-disc titles or refuse;
a "NEW" tag; hide PS1 `.iso`. Plus C6's requirement and the two VOD items.
