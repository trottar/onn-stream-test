---
memory_schema: 1
as_of: 2026-11-18
status: TASK HANDOFF — PP-H4, the four-person sitting with the board: selection, load screen, ready check, practice, a duel to T88 for two and a round's end to T89 for four, both under their cheat setups (session A, hardware; part 1 UNATTENDED on the bench ~15 min; then the user ALONE for the streamed self-proof ~2 min; then ATTENDED ~35 min with four people and four pads paired to the onn). B150's sketch (SESSION_B_DONE_2026-11-18AY.md §B150) with B152's changes (SESSION_B_DONE_2026-11-18AZ.md §B152), and Cowork's below. This file replaces every earlier PP-H4 task. PRIVYHUB_H7=1 and PRIVYHUB_PARTY=1 for the task only (twenty lines, back to eighteen). No new code. Pre-registered; nothing perceptual. Nobody but the user sits down unless part 1 and the self-proof's sound cell are MET. Nothing adopted; nothing committed
---

# PP-H4 — four people, four pads: choose, load, ready, practice, play

Read first: `SESSION_B_DONE_2026-11-18AY.md` §"B150" (the whole sketch: stage 1, part 1, the self-proof, S, the sitting's lines, the cells, the close, the record) and `SESSION_B_DONE_2026-11-18AZ.md` §"B152" (its exact changes: a practice is left by Select, not Start); `PP_H3D_2026-11-18.md` and its `part2/` (how the solo sitting was run and recorded; its "No audio" — the board's import, now B148's); `PP_H3C2_2026-11-18.md` (adb as its second try used it); `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title (a duel); **T89** = the users' N64 four-player title (a round's end); "T88's cheat setup" / "T89's cheat setup". In the replies to the users the games may be named; **in every record only T88 / T89** — no title, character name, cheat name, serial, game id, `profile_id`, path, address or picture in git; no answer carrying a `"title"` copied into a record.

## Run B150's sketch with B152's changes as written, with these changes

1. **The window and the preconditions:** outside 04:30-05:30Z and not within 45 min before it — else reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that". **Queue AZ committed** (B152's line). The board's repo as B150's stage 1, 3 with B152's additions: clean, `674407d` an ancestor of HEAD, **any later commit of the PC side's accepted** (HEAD and the changed names recorded; part 1's checks are the gate), B's two files at `3f32d339…` / `01301ec5…`.
2. **Three stages, and who is asked for what:**
   - **Part 1 — nobody.** If any of it is not met: one plain sentence of what failed, the close, "YOU, now: commit". No line asks anyone to pick up a pad.
   - **The self-proof — the user alone.** B150's line 1 as written. **A does nothing streamed until the user's "ok".** The title held 6 s; then S read on both of its switches. **Not met → stop**: one plain sentence, the close, "YOU, now: commit" — the other three are never asked to sit down.
   - **The sitting — four people**, only after the self-proof's S is met. The first line to the four begins: "YOU, now: the check passed — bring the other three in."
3. **S is B150's wording, and it is the only wording:** every planned switch whose next switch begins 4 s or more after it is read (a row with `audio_queue_depth` > 0 within 4 s; `audio_underruns` rising ≤ 20 a row to the next switch's start); a switch followed sooner is listed, not read. (PP-H3d was recorded NOT MET on a switch that could not be read; this wording is why.)
4. **Part 1 (e)'s reason reads Select now:** on the bench no pad presses anything, so T89's practice ends by its own bound (`"by": "time"`, ~90 s). Everything else of (e) as written.
5. **The button's name at the TV:** the lines say "the Select button — Share on a PlayStation pad". If any pad's `class` in the onn's heartbeat `pad_slots` is not `sony`, add once: "on an Xbox pad it is the View button, the two small squares".
6. **Say to the four, in the "started" line, one sentence more:** "A practice lasts about 90 seconds at most, so in <T89> it may end in the middle of a fight — that is expected." (The game named in the reply; T89 in the record.)
7. **The hub's own decision first:** on each of the users' per-mini-game lines A answers with the hub's `minigame_ended` row (class, places or scores, seats) and the board's `scores … for seats …` line before comparing with the users' words; a disagreement is recorded as it stands, never argued at the TV.
8. **Every reply to the users is short:** "YOU, now:" and the one complete step, naming only what the onn or the board offers. Nothing about adb is ever asked at the TV.
9. **Files:** the users' slots, slot pictures and every normal state and save before = after (every sha256); **the setups' in-game saves recorded before and after, not a cell**; no `.state8`; the board's repo status after = before; the board's folder written only by B148's own import at a launch (its git-ignored cache), recorded by its row.

## Pre-registered (hashed before part 1) — nothing perceptual

B150's cells with B152's strings: **MET = part 1, the self-proof's S, and J, D, X, PR, S, L, C, F, H, E, U.** PR's band words `PRACTICE — press Select (Share) to go back`, in every practice's encoder argv and in no other; `minigame_practice_end` `"by": "select_button"` or `"time"`; `load screen again` once a practice. Recorded, no bar: the users' words on the band and the sound (B150's one question at the END), each `prepare_s`, `held_s`, `mute_ms`, `frames`, each switch's `seconds`, `audio_max_arrival_gap_ms` at each switch, which practices were left by Select and which by time.

## The close

As B150's: the board quit; A's watchers stopped; both drop-ins removed; daemon-reload; the companion restarted (no SIGKILL); **eighteen** lines, `--check` ok; `party-minigames` and `bench-release` → 400; nothing running; the rules folder and the board's repo as found. **The record** `evidence/PP_H4_<the UTC date>.md` + `pph4_<the UTC date>/` in B150's shape. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §PrivyParty (one paragraph); `logs/pph4_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action).

**The last reply begins "YOU, now: commit"**, then one line each: part 1 (and B148's row); the self-proof and its S; joining; each duel (the hub's row, the users' words, the board's credit); each round's end (places, the payout); each practice (which title, how it ended, the band, `load screen again`); S over the sitting (read / listed); Home / RESUME; END; the users' words on the band and the sound; files before = after and which in-game saves changed; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb only as PP-H3c's second try used it; no network addresses, titles, serials, game ids, `profile_id`s, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots, setups and the rules folder read only (scratch slot 8 only in part 1, removed at once); B's code and the board's repo not edited; no `e3_flag.conf`; both bench flags absent at the close; nothing adopted; nothing committed.
