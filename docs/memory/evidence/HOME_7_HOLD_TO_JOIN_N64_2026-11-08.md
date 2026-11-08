---
memory_schema: 1
as_of: 2026-11-08
status: HOME-7+N64 DONE (session A; stage 1 21:53-21:57Z, stages 2-10 21:57-22:38Z, the close 22:39-22:50Z, the user at the TV). The N64 core fetched on the user's "go N64". Queue T's APK `9aa00ba2…` installed with every property empty; C15 MET, C16 MET, C17 MET (player 2 broken on that title with the multitap — to B), C18 MET (B55 works), C20 MET (B57 works), C19 a reading (one entry per disc), C21 MET, C22 MET, C23 NOT MET (the Home hold froze the N64 game; a title's buttons). `9aa00ba2…` CONFIRMED and the pin moved. G-A15 ADOPTED on the user's word: `PRIVYHUB_N64=1` the seventeenth line. Nothing committed
---

# HOME-7+N64: hold-to-join, PS2 recovery, the first N64 game

Task: `handoffs/HOME-7_JOIN_PS2_N64_TASK.md`; B's rows: `handoffs/SESSION_B_DONE_2026-11-08V.md` §A (the order, stage
1, C19 / C21-C23) and `handoffs/SESSION_B_DONE_2026-11-08U.md` §A (C15-C18, C20). The directory is
`home7_2026-11-08/`: `stage1/`, `c15/`, `c16/`, `c17/`, `c18/`, `c19/`, `c20/`, `c21/`, `c22/`, `c23/`, `ga15/`, `pin/`,
`close/`, `preregistration.md` and its `.sha256`, `LABELS.txt`, `redact_check.txt`, `manifest.sha256`. Times are UTC.
Titles as T-labels (`LABELS.txt`); no title, serial or path.

## The user's lines (verbatim)

- "go N64. Read _cowork_prompt.txt in the repo root and follow it as my prompt."
- C15: "Stage 2". C16: "Stage 3, only P1 showed".
- C17: "Stage 4, game paused to initiate more players and hold to add 4 as expected" / "Player 2 buttons not working now".
- C18: "Stage 5" / "Player 2 still doesn't work (has worked in the past for this game as you know)" / "Other 2 player game
  worked as expected including gameplay and home"; "I literally just did that?"; "Stage 5" / "Worked as expected with
  gameplay and home".
- C20: "Stage 6" / "About 15 seconds to come back, game was paused when it returned" / "Player one and two worked as
  expected."
- C19: "Stage 7" / "PlayStation (80)" / "I see a game with disc one then disc two versions".
- C21: "Stage 8" / "13 games" / "Felt good to play, no issues". C22: "Stage 9" / "All worked as expected".
- C23: "Stage 10" / "Multiple issues" / "Half the buttons didn't work so I  couldn't jump as any player and the game
  froze on returning to PrivyHub after home hit".
- G-A15: **"Yes keep on but we should try to  resolve the issues too"**.

## Stage 1 (`stage1/STAGE1.md`)

- HEAD `32abb425` (queue V committed), the tree clean; `/tmp` 6.6 GB; seventeen lines (+ `b56-import.conf`);
  `cfe0211c…` CONFIRMED; the eleven properties empty; the two units.
- **The N64 core** on "go N64": stable 1.22.2 lists no per-core files → the nightly per-core zip; zip `35b91ceb…10d1`,
  `.so` `26f2b4ec…775e`; `n64_core_check --keys` bundled, 12 / 12 keys; nothing started.
- `b56-import.conf` removed; `N64_DIR=` added to the gitignored paths file; `b59-n64.conf`; restart: seventeen lines;
  "PlayStation (80)", "Nintendo 64 (13)".
- **The install:** `cfe0211c…` → `home7_previous/`; `9aa00ba2…` (`home7_installed/`, the same signer) `adb install -r`
  Success, read back, paired, every property empty.
- Pre-registration `preregistration.md` (sha256 `11ad3784…b9b9`, 21:56:00Z).

## The cells

| cell | read | result |
| --- | --- | --- |
| **C15** hold-to-join (T1, 2-player PS1, multitap off) | no change row before the holds (the tap claimed nothing); `change` P1 (21:57:47) / P2 (21:57:51), `join hold`, `players_joined` 1 → 2, `claimed_by` prompt; heartbeats `players_joined` 2; no `relaunch_ports`; the exit report `players_joined` 2, `ports_set` 2 / no multitap / `metadata`, `relaunches` 0. Not shown: the start row (an empty map on the first start after the install) and slot 1's `updates_by_player` (the heartbeat log rewritten at the next start) — disclosed | **MET** |
| **C16** a 1-player title (T2) | P1 by the hold (21:59:56, `players_joined` 1), no slot-1 entry, `players_joined` 1 on the heartbeats; "only P1 showed". A stale pre-session row (the previous game's P1 / P2) before `session_started` — to B | **MET** |
| **C17** the multitap at once (T1) | `relaunch_ports` ok, **state loaded**, retroarch, `total_ms` **4318** (save 286 … stream_start 1019), within budget; `ports_set` relaunch / 4 / multitap; `PS1 multitap: port1`; `--device` 1-4; the ready; P3 (players_joined 3). The time ~6.4 s (the user gave no count). "game paused … hold to add 4 as expected" | **MET** (B's row) — **but player 2 stopped working**: on T1 with the port-1 multitap (after the relaunch, and from boot on the next launch with the stored count 3) player 2 does nothing; with the multitap off it works (C15; HOME-4+ C7). To B: the stored count keeps T1 on the multitap |
| **C18** the PS2 hold through PINE (T4) | `state_saved` slot 9 pcsx2 stall pine; `input_release` pine **`load_ms` 400.9**, `line` true; `ps2_states` **verdict ok** 0.9 s; `resumed` via stall_end; the game log's three lines. The first "Stage 5" was a PS1 title's Home (worked; `c18/not_yet.txt`). "Worked as expected with gameplay and home" | **MET → B55 works** |
| **C20** the PS2 multitap relaunch (T4) | `relaunch_ports` ok, **state loaded**, pcsx2, slot 7, pine, `total_ms` **12148** (load 2243, stream_start 4532); `ports_set` relaunch / 4 / multitap true; save 0.5 s, exit 0.5 s, **load picture ok 1.6 s**; ELF before `Loaded state from slot 7.`, 0 TLB Miss; `MultitapPort1 = true`; slot 9 untouched; the exit report = the host. The time ~13.3 s, the user's count ~15 s. "game was paused when it returned"; P1 / P2 worked (the pause likely the game's own — a reading for B) | **MET → B57 works** |
| **C19** the list without the import flag | "PlayStation (80)", no "(OpenBIOS)", no NEW; **one entry per disc** ("disc one then disc two") | **a reading** (the `.m3u` question) |
| **C21** the first N64 title (T5) | "Nintendo 64 (13)"; `N64 launch: core=mupen64plus_next ports=4`, `N64 core options: 12 keys`; `--device=1:1 … 4:1` (read on T6's launch); `ports_set` 4 / no multitap / not available / `n64`; P1 / P2 by the hold, no `relaunch_ports`; GL HW render initialised (GLideN64's own line not printed — disclosed), no core error; the ready. "Felt good to play, no issues" | **MET** (the mapping: no issue on T5) |
| **C22** SAVE / LOAD (T5) | both 200; RetroArch's `[State]` save / load **16793440 B** (~16 MB; 1.5 MB on disk); "All worked as expected" | **MET** |
| **C23** 10 min, the hitches, the Home hold (T6) | the capture: **internal 60 fps**, distinct median 60 / min 3, **3 hitch s → 16.5 per 10 min**; the Home hold: **`state_save_failed` (ack null) — RetroArch's network commands timed out (GET_STATUS)**, 46 `stall_resume_failed`, **the game froze**; diag_read: the N64 session **28.7** hitch s / 10 min vs PS1 C15 0.0 / C17 10.5; T6: "Half the buttons didn't work … couldn't jump as any player". The freeze fell inside A's window capture (disclosed: not excluded) | **NOT MET** → B61 |

## The close (`close/close.txt`)

- Nothing of RetroArch / PCSX2 running; the eleven properties empty; the drive's N64 folder before = after.
- **G-A15 applied** (`ga15/`, `patches/G-A15_N64_ADOPTION.md`, indexed): `N64` in `ADOPTED` (the comment `G-A15
  (adopted 2026-11-08, the user)`), `drop_in_n64` in `ok`, the wording files, `ADOPTED_E3` as it is; `git apply --check`
  ok, applied, `git diff --check` clean; `e1_suite --self-test`, `test_e1_remote` 21, `test_c3_l4_nft_night` 33,
  `tests/ps2_session` 93, `tests/n64_session` 28 green. `n64.conf` written, `b59-n64.conf` removed, restart:
  **seventeen** lines; **`--check` ok on seventeen**; **`flags_absent` true**, adopted 17. **Off:** delete `n64.conf`,
  `daemon-reload`, restart, reverse `ga15/g_a15_applied.diff`.

## The CONFIRMED rule (CL-B7 §6)

- C15, C16, C17 valid and met with every property empty (none was set) → **`9aa00ba2afe19a7f36b869454d7d5e683185dc97fc116cc6f8f75878bc5fe73f`
  CONFIRMED**; the pin moved (`pin/`, `patches/HOME-7_APK_PIN.md`, indexed; tests green; `--check` ok).
- **Disclosed with it:** C17's player-2 failure on T1 under the multitap (host-side ports / the stored count), to B.
- C18 → **B55 works**; C20 → **B57 works**; C19 a reading; C21-C23 the N64 reading → B61 and G-A15.

**On the onn now:** `9aa00ba2…` (queue T's), CONFIRMED, every property empty. **The adopted environ: seventeen lines.**

## To B (B61 and beside it)

1. **N64 Home hold freezes** (C23): RetroArch's network command port stops answering at the stall save (GET_STATUS timed
   out; `state_save_failed` ack null; 46 resume failures) — reproduce without a window capture.
2. **N64 per-title mapping** (C23, T6): jump and others dead for every player (T5 fine).
3. **PS1 multitap and player 2** (C17): T1 reads player 2 from port 2 with the multitap in; the stored count 3 keeps
   T1 on the multitap at every launch — the switch / the stored count per title.
4. Stale pre-session `pad_slots` rows carrying the previous game's joins (C16, C17, C21).
5. PS2 after the relaunch: the game's own pause (C20), an extra press.
6. The multi-disc `.m3u` on the user's word (C19); the GameCube launch kind after H2-P1 (Dolphin on the user's go).

Nothing else adopted; nothing committed.
