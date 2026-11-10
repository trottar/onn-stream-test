---
memory_schema: 1
as_of: 2026-11-10
status: TASK HANDOFF — ART-1 (session A, unattended, no TV, ~20 min + the fetch; the user's word "fetch" or "skip" is the only hand step, from the phone). Queue AC's host parts go live at a companion restart; the art + details dry run for N64 / PS2 / GameCube (counts only), then on "fetch" the art and details for the three systems and the N64 cheat lists (the user's yes to G1 and G3a, 2026-11-09: each found title's name is sent to RetroArch's picture server, as PS1's). Nothing adopted; nothing installed on the onn; nothing committed
---

# ART-1 — box art, details and the N64 cheat lists

Read first: `SESSION_B_DONE_2026-11-09AC.md` §"A — ART-1" (**the steps, the commands and the replies are B's — use them exactly**), `B76_ART_THREE_SYSTEMS_2026-11-09.md` (the fetcher's map, the dry run, what a fetch sends), `B78_N64_CHEATS_2026-11-09.md` (the cheat tool; the disclosed stop at the first N64 title with the knob `0`), `HOME_11_DISC_SAFE_2026-11-09.md` (the state: eighteen lines, `85220f99…` CONFIRMED), `docs/memory/CURRENT.md`.

**The user's answers on record (2026-11-09):** G1 "fetch N64 / PS2 / GameCube box art and details from RetroArch's library as for PS1 (each title's name is sent)" — **yes**; G3a "N64 cheats from RetroArch's database (each matched title's name is sent)" — **yes**. The fetch still waits for the user's "fetch" after the dry run's counts (B's form), so a poor match is seen before anything is sent.

**The stages by the user's message:** the read line = stage 1 (the restart and the dry run, unattended); "fetch" = stage 2 (the fetch, the read-backs, the record); "skip" = the record with the dry run only. **Every reply begins "YOU, now:".**

## Stage 1 — the restart and the dry run (unattended; outside 04:30-05:30Z; no game, no movie)

B's ART-1 steps 1-4 exactly: HEAD named — **queue AC committed; if B76-B81's files are uncommitted, stop: "YOU, now: commit queue AC first, then send the read line again"**; `/tmp` ≥ 1 GB (the tools run with `TMPDIR` on the main disk); eighteen `PRIVYHUB_` lines, `--check` ok, `85220f99…` CONFIRMED on the onn, only the two units; **the companion restart** (B77-B81's host parts live; nothing adopted, no drop-in; eighteen lines, `--check` ok, the journal clean, the systems' counts as before; the keeper not restarted); the dry run with the companion's own `PRIVYHUB_` environment **plus `PRIVYHUB_ART_SYSTEMS=1` in that command only** (`tools/update_game_metadata.py --dry-run --json`): per system matched / ambiguous / no match / list unavailable, the misses as labels; **disclosed in the reply:** this step downloads RetroArch's three whole system lists (one file per system, cached); nothing about the titles is sent. Exit with B's reply: "YOU, now: box art and details — N64 a of b titles found in RetroArch's library, PS2 c of d, GameCube e of f (the rest are listed as labels). Fetching sends each found title's name to RetroArch's picture server, as for PS1, and also fetches the N64 cheat lists the same way. Send 'fetch' to go ahead, or 'skip'."

## Stage 2 — on "fetch" (unattended)

B's step 5 exactly, the same environment with `PRIVYHUB_ART_SYSTEMS=1` in the commands only: `tools/update_game_metadata.py --system n64`, then `--system ps2`, then `--system gamecube`; then `PRIVYHUB_N64=1 tools/update_game_cheats.py --system n64 --no-download` (the report), then without `--no-download`; the read-backs: the art downloaded / cached / missing per system; one title's `details` per system by label (year, genre, players, `box_art_available`); the N64 titles with cheats (count); `provider_cache/libretro/<n64|ps2|gamecube>/` present, the box-art files counted; whether the list on the hub's control API now carries `box_art_available` for the three systems **without** any drop-in (if the art only shows with `PRIVYHUB_ART_SYSTEMS=1` in the companion's environment, say so — then HOME-12 needs a bench drop-in for C44, written into its stage 1; nothing adopted here). Nothing else is sent; no title in any record (labels and counts).

## The close and the record

- Nothing running but the two units; eighteen lines; `--check` ok; `85220f99…` CONFIRMED; the drive untouched (the fetch reads file names only).
- **The record** `evidence/ART_1_2026-11-10.md` + dir (the counts per system, the labels of the misses, the commands, the restart's checks, the cache's counts, the one-title details per system by label, the N64 cheat count, whether the companion needs the flag to show the art; no title, serial, game id or path; `redact_check`); `KNOWN_ISSUES.md` (insertions only); ROADMAP §H6 lines (B76 / B78's fetch run); `logs/art1_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after): the art result one line per system; Next Action — HOME-12 at the TV (B's sketch: the APK `de6682db…`, C44-C48), with the art drop-in note if needed.
- The reply: "YOU, now: commit" plus per system found / fetched / missing, the N64 titles with cheats, and one line: "the art shows on the onn now / at HOME-12 (and why)".

No sudo, no nft, the Opal read-only, adb for `--check`'s reads only, no `setprop`; the fetches are the ones named (RetroArch's lists, the picture server by title name, the N64 cheat lists) and only on the user's "fetch"; nothing written to the drive; nothing deleted; no address, title, serial, game id or path anywhere in git or the reply; nothing adopted; nothing committed.
