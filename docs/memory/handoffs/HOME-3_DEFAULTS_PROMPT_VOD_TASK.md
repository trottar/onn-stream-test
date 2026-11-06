---
memory_schema: 1
as_of: 2026-11-06
status: TASK HANDOFF — HOME-3 (session A, hardware, attended, ~40 min at the TV with two pads and the onn remote; five stages by the user's message). Install queue N's APK `8ba4d996…` with every property empty; C1'' the hold with no property, C4'' two pads with no property, C6 the player prompt, C5'' the movie (the 45-s drop, then a companion restart with the movie open); the close, the CONFIRMED rule, the record, G-A13 and the prompt's default as the user's questions. Measurement only; nothing adopted; nothing committed
---

# HOME-3 — the defaults, the prompt, the movie

Read first: `SESSION_B_DONE_2026-11-06N.md` §A items 1-8 (**the exact APK hash, properties, commands and pass rows — use theirs**), `B41_…`, `B42_…`, `B43_…`, `HOME_2_HOLD_PADS_VOD_2026-11-03.md` (C1' / C4' / C5' as met and not met), `CL_B7_…` §6, `docs/memory/CURRENT.md`.

**The stage is the user's message.** The read line alone = stage 1. "Stage 2" … "Stage 5" and "drop" / "Stage 6" as below. **Every reply begins "YOU, now:" and the one thing the user does next, in plain words.** Where a reply lists what the screen must show, say it in the user's terms ("you'll see 'Player 1 — press any button' at the bottom").

## Stage 1 — the install (unattended ~10 min)

- Precondition: fourteen lines, `--check` ok (`0132b944…` CONFIRMED), `privyhub-diag` active, no `e3_flag.conf`, no game, one device paired, the client on the LAN, the band 5 GHz, every property empty (HOME-2's ten plus `player_prompt`), no `privyhub-*` unit but the companion and `privyhub-diag`, HEAD named (queue N committed), the tree clean but the prompt and this file.
- Pre-registration hashed before the install: C1'' / C4'' / C6 / C5'' (a) (b) pass rows as B items 2-5; validity; the CONFIRMED rule; the reading (G-A13 and the prompt's default per cell met).
- The install per B item 1: preserve `0132b944…` (`home2_installed/`); `queue_n_built/` → `home3_installed/`, sha256 **`8ba4d996a96c14d01b1e368c20e656f767062d34b17b9308d984b8c43834605f`**, the signer the same; `adb install -r`; read back; paired; every property empty; **the companion restart**; fourteen lines; `--check` MISMATCH on the APK only.
- Exit: "YOU, now: come to the TV with the onn remote and ONE pad; start any game; when it's running, send 'Stage 2'."

## Stage 2 — C1'', the hold with no property (attended ~5 min)

- `getprop surface_hold` empty (read). Reply: "YOU, now: press the remote's Home, count to 2, come straight back — the game should still be running where it was. Play ~30 s, exit with Back. Then send 'Stage 3'."
- On "Stage 3": C1'''s rows (B item 2); then the off check: `setprop surface_hold 0`, and tell the user: "YOU, now: start a game again, press Home, count to 2, come back — THIS time it is allowed to restart. Then exit and send 'Stage 3b' and pair the second pad." On "Stage 3b": today's restart (`restart_fast`, no `surface_lost`); the property cleared (`""`) and read back empty.

## Stage 3 — C4'', two pads with no property (attended ~5 min)

- `getprop pad_slots` empty (read). Reply: "YOU, now, both pads paired: start a two-player PS1 game (multitap off); press a button on pad B first, then pad A; exit; relaunch; press pad A first. Then, in the game, press only pad A for 5 s, then only pad B for 5 s. Then send 'Stage 4'."
- On "Stage 4": C4'''s rows (B item 3: both starts `count` 2, slots 0 / 1, the same two hashes, no `google` entry; `updates_by_player` only on the pressed pad's slot while `packets_by_player` rises on all four); the off check `setprop pad_slots off` → no `pad_slots` row or key in the next session (the user relaunches once when told), then cleared and read back empty.

## Stage 4 — C6, the player prompt (attended ~8 min)

- `setprop player_prompt 1` (read back). Reply, in the user's terms: "YOU, now, both pads: start the same two-player PS1 game. You'll see 'Player 1 — press any button' at the bottom. (1) Press X on pad B — 'P1' shows for 2 s, then 'Player 2 — press any button'. (2) Press X on pad A — 'P2' shows and the prompt goes. (3) On pad B, hold Select and Start together for 2 s — 'P1 released', and the prompt comes back; press X on pad B again — P1. (4) Exit; start a single-player game — there should be no prompt at all. Then send 'Stage 5' with one line on what you saw."
- On "Stage 5": C6's rows (B item 4: `players` 2 and 1 in the start responses; the `pad_slots` rows' `claimed_by` `prompt` / `stable`; the report's `players` and `pad_claims`; the game running throughout; the user's line as the gate on what was on screen). The property cleared and read back empty; with it empty no `players` / `pad_claims` / `claimed_by`.

## Stage 5 — C5'', the movie (attended ~10 min)

- No game running (confirm). B item 5's setup (`b43-vod-drop.conf`, daemon-reload, restart; `setprop vod_retry 1`, read back). Reply: "YOU, now: start a movie and let it play a full minute, touching nothing. Then send 'drop'."
- On "drop": `echo "drop 45" >> runtime/vod_drop_test.trigger` (B item 5 (a)). Reply: "YOU, now: watch for about a minute. The movie should stutter, show 'reconnecting…', then carry on from the same spot — no 'Playback error'. When it's playing again, keep it playing and send 'Stage 6'."
- On "Stage 6": (a)'s rows (`vod_drop_injected` `dropped: 1` `how: rst` `refuse_s: 45.0`, `vod_refuse_ended` with `vod_refused` ≥ 4; `vod_client.jsonl` `vod_error` reason `reset` → `vod_retry`×n → `vod_resumed` ~30-35 s after the injection; `vod_range.jsonl` `client_reset` then `bytes=<P>-` 206; invalid if `dropped: 0` or no `vod_error` — then once more with `drop 60`, the user told). Then (b): with the movie still playing ≥ 1 min, `systemctl --user restart privyhub-companion`; reply: "YOU, now: watch again — the movie should pause briefly and resume by itself; do not press Retry. Send 'Stage 7' with one line on what you saw." On "Stage 7": (b)'s rows (`vod_retry` reason `"401"` `token_refetched: true` → `vod_resumed`; `vod_range.jsonl` 401 then 206; no "connection to hub lost"). Then B item 5's close (the drop-in removed, restart, `vod_retry` cleared).

## Stage 7 continued — the close, the rule, the record

- Every property empty (eleven read back); the drop-ins removed; fourteen lines; `--check` ok; `flags_absent`; `privyhub-diag` active.
- **The CONFIRMED rule as CL-B7 §6:** every cell valid and today's behaviours where no flag was set (B42's intended defaults aside) → `8ba4d996…` CONFIRMED and the pin moved (the three places; tests green); else `0132b944…` reinstalled from `home2_installed/`, read back, paired, the user told why.
- **The record `evidence/HOME_3_DEFAULTS_PROMPT_VOD_2026-11-06.md` + dir:** the per-cell tables beside HOME-2's, the user's lines verbatim, the decision, the APK on the onn named; `KNOWN_ISSUES.md`, ROADMAP lines, `logs/home3_git_status.txt`, the redactor; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after): **G-A13 and the prompt's default in B's words, only for the cells met**; the G9 checkpoint as the next A task (the draft applied); H0 slice 1a as the next B queue with B45's four questions for the user (a real BIOS or OpenBIOS; `.m3u` for multi-disc titles or refuse; a "NEW" tag; hide PS1 `.iso`). The reply: "YOU, now: commit, then answer: G-A13 yes/no; the prompt by default yes/no; and B45's four questions." Plus the cells' one-line results.

No sudo, no nft, the Opal read-only, adb for the install, the `setprop`s named (`surface_hold 0`, `pad_slots off`, `player_prompt 1`, `vod_retry 1`) and their clears, and state reads; no addresses or identifiers anywhere; nothing fetched, nothing deleted; fourteen lines and no `e3_flag.conf` at every teardown; nothing adopted; nothing committed.
