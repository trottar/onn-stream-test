---
memory_schema: 1
as_of: 2026-11-17
status: TASK HANDOFF — PP-H4, the four-person sitting with the board, both mini-game titles under their cheat setups (everything unlocked) (session A, hardware; part 1 UNATTENDED on the bench ~10 min, then ATTENDED ~30 min at the TV with four people and four pads paired to the onn). Offered because H7-V5b was MET (2026-11-17: T88 recognised at 9-10 s, T89 at 2.0 s, the ends, places and scores right, SAVE / LOAD refused, every file before = after). B125's sketch (SESSION_B_DONE_2026-11-17AR.md §PP-H4) with B128's changes (SESSION_B_DONE_2026-11-17AS.md §PP-H4) and B132's (SESSION_B_DONE_2026-11-17AT.md §PP-H4), and Cowork's below. PRIVYHUB_H7=1 and PRIVYHUB_PARTY=1 for the task only (twenty lines, back to eighteen). No new code. Pre-registered; nothing perceptual. Nobody sits down unless part 1 is MET. Nothing adopted; nothing committed
---

# PP-H4 — four people, the board, a duel and the round's end, everything unlocked

Read first: the three sketches above in that order (B125's is the base: PP-H3b's stage 1, watchers, part 1 and close; the lines; cells J, D, P, X, R, H, E, C, U; B128 adds the setups, cell L and the unlocked lines; B132 adds `recognise_s` 15.0 and keeps the SAVE / LOAD line); `H7_V5B_2026-11-17.md`; the PP-H3b record and task; `docs/memory/CURRENT.md`.

**T88** = H7's 2-player PS1 title (the duel); **T89** = the users' N64 four-player title (the round's end); "T88's cheat setup" / "T89's cheat setup". In the replies to the user the titles may be named; **in every record only T88 / T89** — no title, character name, cheat name, serial, game id, `profile_id`, path or picture in git.

## Cowork's changes to the sketches

1. **The window and the preconditions:** outside 04:30-05:30Z and not within 45 min before it — else reply only "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that". **H7-V5b's record committed** (else "YOU, now: commit H7-V5b's record first, then send the read line again"). B128's two board-repo checks are **stops**: B124's two files committed (sha256 `e246478b…`, `b016167d…`) and `grep -c PRIVYPARTY_ON_HUB <board repo>/game/minigame_picker.gd` → 1 — each with B128's own "YOU, now:" line.
2. **The rules folder as H7-V5b left it,** checked read only as B132's step 3-6 checks (both specs' numbers, both begins' sha256, both sidecars' `cheat` matching `cheat-profiles`); nothing written there.
3. **Part 1 is the gate.** Part 1 (B125's + B128's additions: the list 2 and 4; a T88 bench mini game to `end_P1` [1, 0] and a T89 one, seats 3,1,4,2, to places [1, 2, 3, 4] / scores [4, 3, 2, 1]; each `"cheat": true, "profile_matches": true`, `"begin": "setup"`, `"recognise_s": 15.0`, `recognised` true; the concurrent calls; the refusals of wrong seat counts) runs with nobody at the TV. **If any of it is not met, stop there:** one plain sentence of what failed, the close, and "YOU, now: commit" — **no line asks anyone to sit down.**
4. **The lines are B128's** (four pads joined in order; the board's four players; a duel and the round's end with every character there to pick; "don't choose SAVE or LOAD on the onn's bar" kept — B131 is not adopted; the per-mini-game line asking who won / the Place row and the payout, and whether any character showed locked), then B125's Home / RESUME line after the first round's end, the END line after one duel and two rounds' ends, and B125's "stuck" and "close" lines unchanged. Each reply to the user is short: "YOU, now:" and the one step.
5. **What the hub already decided is said first:** on each of the user's per-mini-game lines, A answers with the hub's own `ended` row (class, places, scores, seats) before comparing it with the user's line; a disagreement is recorded as it stands, never argued at the TV.
6. **Cell U as B128's:** the setups' slots and slot pictures before = after (every sha256); **the setups' in-game saves recorded before and after, not a cell** (the players' matches may write the titles' own records into them); every normal state and save before = after; no `.state8`; the board repo's status after = before.

## Pre-registered (hashed before part 1) — nothing perceptual

B125's J, D, P, X, R, H, E, C, U with B128's L (every `minigame_launch` `"cheat": true, "profile_matches": true`; every `watching` `"begin": "setup"`; `status`'s `cheat_session.profile_id` the title's setup while it plays) and U changed, B128's lock line recorded, B132's C addition (each mini game's `recognised` second). **MET = part 1 met and J, D (every duel), P (every round's end), X, R, H, E, L, U met.**

## The close

As B125's / B128's: both drop-ins removed; daemon-reload; the companion restarted (no SIGKILL); **eighteen** lines, `--check` ok; `party-minigames` and `bench-release` → 400; nothing running; the rules folder as found. **The record** `evidence/PP_H4_<the UTC date>.md` + `pph4_<the UTC date>/` in PP-H3b's shape with `part2/places.md` (each round's end: the user's row, the hub's, the board's) and `part2/lines.md` (the user's lines verbatim, titles and names replaced). `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` §PrivyParty (one paragraph); `logs/pph4_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action).

**The last reply begins "YOU, now: commit"** (this repo; the board's repo only if its status changed), then one line each: part 1 met or not; each duel — the user's winner, the hub's, the board's credit; each round's end — the user's Place row, the hub's places and scores, the board's payout; any "stuck" or "locked"; Home / RESUME and END; the seconds each way (median); the users' slots before = after and which in-game saves changed; MET / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, adb only as PP-H3b used it; no network addresses, titles, serials, game ids, `profile_id`s, character names, cheat names or paths anywhere in git; no picture in git; nothing written to the drive; nothing fetched or installed; nothing deleted; the users' slots, setups and the rules folder read only (scratch slot 8 only in part 1, removed at once); B's code and the board's repo not edited; no `e3_flag.conf`; both bench flags absent at the close; nothing adopted; nothing committed.
