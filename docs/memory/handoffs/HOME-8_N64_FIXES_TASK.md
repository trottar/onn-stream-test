---
memory_schema: 1
as_of: 2026-11-08
status: TASK HANDOFF — HOME-8 (session A, hardware, attended ~30 min; ONE short sitting at the TV, the user with the onn and the pads paired to the onn over Bluetooth as always; nothing asked on the hub; the stages move on the user's "Stage N"; every reply begins "YOU, now:"). Queue W's four fixes checked: C24 T6's buttons (△ / ○ = C-up / C-right), C25 the N64 Home hold (plain pause / resume, no freeze), C26 T1 with three pads (no multitap, player 2 works), C27 a multitap-capable PS1 title with three pads (the relaunch, players 1-3), C28 10 min of N64 with the hitch rate and no capture; T6's reproduction unattended in stage 1. Nothing to adopt (all inside adopted flags or the default host path); nothing committed
---

# HOME-8 — the N64 and multitap fixes, checked

Read first: `SESSION_B_DONE_2026-11-08W.md` §A (**the stage-1 steps, the cells C24-C28, the hub reads, the "You should see" lines and the replies are B's — use them exactly**), `B61_…` / `B62_…` / `B63_…` / `B64_…` (the strings and rows), `HOME_7_HOLD_TO_JOIN_N64_2026-11-08.md` (T1 / T6 as labelled there — the same labels here), `docs/memory/CURRENT.md`.

**The stages by the user's message:** the read line = stage 1 (unattended, incl. T6's reproduction); "Stage 2" C24; "Stage 3" C25; "Stage 4" C26; "Stage 5" C27; "Stage 6" C28; then the close. **Every reply begins "YOU, now:" with what to press and what the TV shows, in the user's terms (B's lines).**

## Stage 1 — unattended (~10 min; no game, no movie; outside 04:30-05:30Z)

B §A stage 1 items 1-6 exactly: `/tmp` ≥ 1 GB; seventeen `PRIVYHUB_` lines, `--check` ok, `9aa00ba2…` CONFIRMED read back on the onn, the eleven properties empty, only the two units, HEAD named — **queue W committed; if B61-B64's files are uncommitted, stop: "YOU, now: commit queue W first, then send the read line again"**; the companion restart (B61-B64 live; seventeen lines; `--check` ok); the N64 remap verified before any launch (`n64_core_check.py --keys --remap`); **T6's reproduction** (B item 4: B61's `repro` script with temp folders, the title read in place on the drive, ≤ 60 s, the acks and the longest silence for a running save and a paused save, "running save hangs T6: yes / no" — no title); the pre-registration hashed (C24-C28 as B's rows; what each decides). Exit with B's stage-1 reply (T6's details line read out, then the join and the △ jump, "Stage 2").

## Stages 2-6 — attended, B's cells in B's words

- **Stage 2 — C24** (B): the remap lines, `layout face_c`, `updates_by_player` moving; the details line as shown (glyphs or boxes recorded); the user's line on △ / ○ jumping for each player. Reply: B's (Home, count to 2, back; "Stage 3").
- **Stage 3 — C25** (B): `state_save_skipped` "n64: no save into a running core", `desync_pause` clean, `rewind_skipped` "plain resume", `resumed`; **no `command_port_silent`, no `stall_resume_failed`**; the CPU as before; the user's line (back and playable). Reply: B's (T1 with three pads; "Stage 4").
- **Stage 4 — C26** (B): `ports_set` 2 / `multitap_available` false / `capable` false / `capped_from`; `PS1 multitap: off`, the cap line; T1's `.opt` corrected (the migration recorded); `--device` 1-2; **no `relaunch_ports`** at the third hold; the TV's note (today's words); the user's line (player 2 works). Reply: B's (a four-player title; "Stage 5").
- **Stage 5 — C27** (B): `capable` true; the relaunch (`state loaded`) or the multitap from the start; `--device` 1-4; P3 joined; the user's line (players 1-3 work). Reply: B's (10 min of N64; "Stage 6").
- **Stage 6 — C28** (B): `diag_read` over the sitting with **no capture running** — the N64 session's hitch seconds per 10 min beside C26's / C27's PS1 session; CPU, Tctl; any Home hold as C25; the user's line. Reply: "YOU, now: that's all — thank you. I'll tidy up on the hub."

## The close and the record (unattended)

- Every property empty; the two units; nothing running; the drive as it was (the N64 / PS1 folders' listings); seventeen lines; `--check` ok.
- **The record** `evidence/HOME_8_N64_FIXES_2026-11-08.md` + dir (the cells' tables, the user's lines verbatim, T6's reproduction result, the times, what each cell decided — C24 → B62, C25 + the reproduction → B61, C26 / C27 → B63, C28 the N64 hitch reading, B64 read on every start; a not-met → B; T-labels; `redact_check`); `KNOWN_ISSUES.md` (insertions only; the HOME-7 items closed where met); ROADMAP (§H1 lines; §D4 the multitap rule as checked); `logs/home8_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after): Verified State unchanged (seventeen lines, `9aa00ba2…`); Next Action — queue X for B: the next APK (B's four client items: the N64 layout shown once; "This game supports 2 players"; the stored count capped on the onn; the pad-slot order) + the multi-disc `.m3u` if the user says yes; then H2-P1 (Dolphin on the user's go) and B's GameCube launch kind.
- The reply: "YOU, now: commit, then (if not answered yet): (1) one entry per multi-disc PS1 game — yes / no; (2) may Code download Dolphin for the GameCube probe — yes / no" plus per cell met / not met in one line each, T6's reproduction in one line, and the N64 hitch rate vs PS1's.

No sudo, no nft, the Opal read-only, adb for state reads only, no `setprop` (every property stays empty); no addresses, titles, serials or paths anywhere; nothing written to the drive; nothing fetched (the N64 core is already on the hub); nothing deleted but the reproduction's temp folders on the main disk; no `e3_flag.conf`; nothing adopted; nothing committed.
