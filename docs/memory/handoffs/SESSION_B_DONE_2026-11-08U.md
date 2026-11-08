# SESSION B — done, 2026-11-08 U (QUEUE_2026-11-08U: B57, B58; run 19:38-20:12Z)

- **Baseline:** `d618a20a` — IMPORT-1 committed.
- **Checked first:** only the companion and `privyhub-diag` active; `git status --short` empty (the prompt files are
  tracked and unchanged).
- **Not done:** nothing committed, adopted or installed; no stream, no companion or keeper restart, no adb, no sudo,
  no nft; PCSX2 not started; no APK built (no client change needed).
- **Nothing imported, nothing written to the drive, no real game file read, nothing deleted, nothing fetched.** The
  hub's library was counted by file name only.

## What was built (both diffs applied to the tree, uncommitted)

1. **B57, the PS2 multitap relaunch through PINE** (`evidence/B57_PS2_RELAUNCH_STATE_2026-11-08.md`; inside
   `PRIVYHUB_PS2=1`):
   - PINE's **slot 7** is reserved for the relaunch, beside B55's 9 (hold / stall) and 8 (give-up);
   - the sequence: save (B52's file-complete check) → SIGTERM → the launch with `MultitapPort1` per the new count →
     the hold to the ELF → load → B52's picture check → `relaunch_ports` `state: loaded`;
   - a failed step → the title restarts without the state (`state: restarted` and the reason), never a dead session;
   - **expected ~9.5-13 s** against B54's 15 s (the boot dominates; PS1 ~6-10 s);
   - `tests/relaunch_ports` 19 ×3; 12 mutations caught;
   - **the `.gitignore` line `PrivyHub-Import/`**, checked with `git check-ignore` (`data/import/` was already
     ignored).
2. **B58, import slice 1b** (`evidence/B58_IMPORT_SLICE_1B_2026-11-08.md`, `docs/IMPORT.md`; behind
   `PRIVYHUB_IMPORT=1`):
   - **a plain source folder:** `--source <folder> --system <ps1|snes|nes|genesis>`, read in place, no symlink root;
     the stick form as before;
   - **SNES / NES / Genesis** with header checks and the per-system duplicate check; NEW for every system; the hidden
     rule PS1's only;
   - N64 / GameCube reported "not supported yet"; **PS2 reported "stays on the external drive"**, nothing planned;
   - **the journal:** an interrupted apply is cleaned by the next apply, and resumed if its plan still accepts it; the
     list (with the flag) never shows a half-placed title;
   - `tests/import_usb` 40 ×3 (B56's 21 unchanged); 16 mutations caught (2 after strengthened tests);
   - fixture trees only.
3. **Checks:** every host suite on the baseline copy, each item's copy and the combined copy. The same six `tools/`
   tests fail in every copy, identically. The touched suites are green in the tree.

**One line for the user (B57):** when a third controller holds in a two-player PS2 game, the TV shows "Setting up 4
players…" for about 10-13 seconds, then the game comes back where it was with that controller as Player 3 (PS1 does
it in about 6-10).

**One line for the user (B58):** the import tool can now read a folder directly (the drive's `games/snes/` and so
on) and takes SNES, NES and Genesis games too; PS2 games stay on the drive.

## A — HOME-7 (~50 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

Queue T's sketch, carried forward: **the install and C15-C18 as written**; then **C20** (the PS2 multitap relaunch,
B57) and **C19** (the import's onn check), and the close with the bench drop-in removed. The changes to queue T's
text, both in replies (no row changed): Stage 4's reply asks for a two-player PS2 title the user has not played with
three pads (C20 reuses it), and Stage 5's reply leads to C20 (the PS2 game is already running).

**The properties** (all eleven, read back empty at the start and the close): `restart_guard`, `stall_signal`,
`link_notice`, `link_report`, `loss_guard`, `wifi_lock`, `opus_decode`, `surface_hold`, `pad_slots`, `vod_retry`,
`player_prompt` (`debug.privyhub.*`).

**Stage 1 (A alone; no game, no movie; outside 04:30-05:30Z):**
1. `/tmp` ≥ 1 GB free. **Seventeen** `PRIVYHUB_` lines: the sixteen adopted + the bench drop-in `b56-import.conf`
   (`PRIVYHUB_IMPORT=1`, on since IMPORT-1), so `e3_state.py --check` is not ok on the environ only, the bench flag
   named; `cfe0211c…` CONFIRMED; the eleven properties empty; only the two units.
2. **The companion restart** (queue T's and queue U's host code live: B54's relaunch and rows, B55's PINE states,
   **B57's PS2 relaunch state**, **B58's list hiding of a journaled import** — no journal exists on the hub, so the
   list is unchanged), then seventeen lines read back. No keeper restart is needed.
3. **The install:**
   - preserve `cfe0211c…` (`home7_previous/`);
   - copy `PrivyHub/app/build/queue_t_built/app-debug.apk` to `PrivyHub/app/build/home7_installed/`;
   - `adb install -r`, and read back `9aa00ba2…`, paired;
   - **every property empty** (hold-to-join is on by default).
4. **Pre-register** the rows below (C15-C20), hashed.
5. **Reply:** "YOU, now: open Games → PlayStation and start a two-player PS1 game. When 'Hold any button to join'
   shows, tap X once on controller 1, quickly, and nothing should happen. Then hold X on controller 1 for about a
   second, then hold X on controller 2 the same way. Send 'Stage 2'."
   - **Pick a title whose PS1 multitap is off:** the start response's `ports_set` reads `players 2`, `multitap false`.
     It is needed again for C17.

**Stage 2 — C15, hold-to-join on a two-player PS1 title:**
- **You should see:**
  - "Hold any button to join";
  - the tap: no change;
  - the hold: `P1` for 2 s, then "P1 joined — hold to add Player 2";
  - controller 2's hold: `P2`, and the line goes;
  - both controllers play their players.
- **Hub reads:**
  - the start's `pad_slots` row `join: "hold"`, `players_joined` 0;
  - a `change` row `players_joined` 1, then 2, with `label` P1 / P2 and `claimed_by` prompt;
  - the heartbeats' `players_joined` 2;
  - `updates_by_player` moving on slots 0 and 1;
  - **no `relaunch_ports` row**;
  - the launch's `ports_set` `source` `join` if the title had a stored count, else `metadata`.
- **Met:** the tap claimed nothing (no `players_joined` 1 row before the hold) and both joined by a hold.
- **Reply:** "YOU, now: Back, Stop, start a one-player PS1 game, hold X on controller 1, then hold X on controller 2,
  and send 'Stage 3'."

**Stage 3 — C16, a 1-player title:**
- **You should see:** P1 by the hold, then no line; controller 2's hold does nothing.
- **Hub reads:** the start response `players` 1; `players_joined` stays 1; no slot-1 entry.
- **Reply:** "YOU, now: Back, Stop, start the two-player game from Stage 2 again. Join with controllers 1 and 2, play a
  few seconds, then hold X on a third controller. Count the seconds until the game moves again, then send 'Stage 4'
  with the number."

**Stage 4 — C17, the multitap at once:**
- **You should see:**
  - the paused frame with "**Setting up 4 players…**" ("The game restarts with 4 controller ports and comes back where
    it was");
  - then the game **back where it was**;
  - `P3`, and "P1, P2, P3 joined — hold to add Player 4";
  - controller 3 drives player 3 (in a game that uses it).
- **Hub reads:**
  - `relaunch_ports` (`ok` true, `state` **`loaded`**, `steps_ms`, `total_ms`, `within_budget`);
  - the `ports_set` row `source: relaunch`, `players` 4;
  - the relaunch's game log `PS1 multitap: port1` and `--device=1:1` … `--device=4:1`;
  - RetroArch's `[State] Loading` after the launch;
  - the `native-stream-ready` after it;
  - `players_joined` 3; `updates_by_player[2]` moving;
  - the exit report's `relaunches` `{count 1, last {ok, state, total_ms}}`.
- **The time:** the `relaunch_ports` row's start (its time minus `total_ms`) to the ready, beside the user's count;
  the budget is 15 s.
- **Met:** the game resumed at the save point (the user's line) with four ports.
- **Note:** the title's stored count is now 3, so its next launch has the multitap from the start (no relaunch).
- **Reply:** "YOU, now: Back and Stop, then start a two-player PS2 game and play about a minute (one controller is
  enough for now). Press Home on the remote, count to 2, and go back to PrivyHub (the recent apps or its tile). Send
  'Stage 5' and say whether the game was where you left it."
  - **Pick a PS2 title the user has not played with three pads:** its start's `ports_set` must read `players 2`,
    `multitap false` (a stored count of 3 would start it with the multitap and C20 would not relaunch). It is needed
    again for C20.

**Stage 5 — C18, the PS2 hold's return through PINE:**
- **Expected in the recovery log:**
  - at the loss, `state_saved` `slot 9`, `core pcsx2`, `kind stall`, `ps2_states pine`;
  - at the return, `input_release` `ps2_states pine`, `load_ms` < 450, `line` true;
  - then `ps2_states` `verdict ok`;
  - `resumed via client_ready_stall` (or `stall_end`).
- **Expected in the game log:** `PS2 state save: slot 9 pine 0x09 ok (stall)`, `PS2 state load: slot 9 pine 0x0a ok;
  <ms> ms`, `PS2 state load: slot 9 picture ok <s>s`.
- **The time:** the resume minus the client's return (B16's R1: ≤ 1.0 s).
- **The stall resume** is the same path; read one if a link stall happens.
- A `rewind_failed` "…(picture static|fault)" is the failure row.
- **Met:** the game where it was (the user's line) and `verdict ok`.
- **Reply (changed: it leads to C20):** "YOU, now: stay in the PS2 game. Hold X on controller 1 and then on controller
  2 so both have joined, play a few seconds, then hold X on a third controller. Count the seconds until the game moves
  again, then send 'Stage 6' with the number and whether the game was where you left it."

**Stage 6 — C20, the PS2 multitap relaunch (B57):**
- **You should see:**
  - the paused frame with "**Setting up 4 players…**";
  - then the game **back where it was** (not at its start screen);
  - `P3`, and "P1, P2, P3 joined — hold to add Player 4"; controller 3 drives player 3 in a game that uses it.
- **Hub reads:**
  - `relaunch_ports`: `ok` true, **`state: loaded`**, `kind: pcsx2`, **`slot` 7**, `ps2_states: pine`, `steps_ms`
    (`save` ~500, `launch`, `resume`, `load` ≈ the boot to the ELF + ~1 s, no `settle`), `total_ms`, `within_budget`;
  - the `ports_set` row `source: relaunch`, `players` 4, `multitap` true;
  - the game log `PS2 relaunch save: slot 7 pine 0x09 ok; file complete <s>s`, `PS2 exit: sigterm <s>s`, `PS2
    relaunch load: slot 7 pine 0x0a ok; picture ok <s>s`;
  - the relaunch's per-launch PCSX2 log: `ELF Loading:` before `Loaded state from slot 7.`, **0 `TLB Miss`**; the
    merged ini's `[Pad] MultitapPort1 = true`;
  - the `native-stream-ready` after it; `players_joined` 3; `updates_by_player[2]` moving;
  - slots 8 / 9 untouched by the relaunch (their files' mtimes as before it); no new Game State slot.
- **The time:** the row's start (its time minus `total_ms`) to the ready, beside the user's count; budget 15 s,
  **expected ~9.5-13 s**.
- **Met:** the game resumed where it was (the user's line) with four ports and `state: loaded`.
- **Not met, to B:** `state: restarted` with its `reason` (`ps2_relaunch_save_failed`, `ps2_relaunch_picture_static`
  / `_fault`, `ps2_relaunch_load_failed`) — the game will have restarted from its boot, never a dead session.
- **Also read:** the exit report's `relaunches.last.ok` beside the host row's `ok`. Client false with host true = the
  onn's 30-s wait for the answer ran out (B54's client timeout; a client change, to B).
- **Note:** the PS2 title's stored count is now 3 (its next launch starts with the multitap).
- **Reply:** "YOU, now: Back and Stop the PS2 game. Open Games → PlayStation and tell me what the PlayStation entry in
  the Games list is called. Scroll the list and tell me how many entries you see for any game that has several
  discs (just the counts, no names needed). Then start any PS1 game, play about 30 seconds, Back, Stop, and send
  'Stage 7'."

**Stage 7 — C19, the import's onn check (I5 from IMPORT-1; the bench flag on):**
- **You should see / read:**
  - the system named **"PlayStation (OpenBIOS) (<n>)"** (no BIOS on the drive, none imported; `<n>` as at IMPORT-1's
    "(80)");
  - **no " · NEW"** anywhere (IMPORT-1 placed nothing);
  - **each multi-disc PS1 set listed once — expected NOT met as written, and not the import's doing:** the hub's
    library holds 14 disc cue files and **no `.m3u`** (counted by name, this queue), and IMPORT-1 placed nothing, so
    today each disc of those sets is its own entry. Record the user's counts (no titles). A one-entry list for sets
    already in the library would need an `.m3u` written into the library for each — a B item, with the user's word
    first (not built);
  - **a PS1 title launching under the import flag:** the start, the ready, the user's "it plays".
- **Hub reads:** the games list's PlayStation node name; the launch and `native-stream-ready`; no `data/import/journal.json`;
  `data/import/marks.json` absent (nothing placed).
- **Met:** "(OpenBIOS)" shown; no NEW; the PS1 title launched and played; the multi-disc reading recorded (expected per
  disc).
- **Reply:** "YOU, now: that's all for the games — thank you. I'll tidy up on the hub."

**Stage 8 — the close and the CONFIRMED rule (CL-B7 §6):**
- Every property empty.
- **The bench drop-in removed** (nothing was placed, so no NEW tags to keep):
  `rm ~/.config/systemd/user/privyhub-companion.service.d/b56-import.conf && systemctl --user daemon-reload &&
  systemctl --user restart privyhub-companion` → **sixteen lines** read back; `--check` ok; the two units active. The
  list then reads "PlayStation (<n>)" again (no "(OpenBIOS)" without the flag).
- If C15, C16 and C17 are valid and met with every property empty, **`9aa00ba2…` is CONFIRMED** and the pin moves:
  `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise
  `cfe0211c…` goes back on.
- C18 decides B55, **C20 decides B57** (both inside the adopted `PRIVYHUB_PS2=1`; no adoption needed); a failure goes
  to B. C19 is a reading (no adoption; `PRIVYHUB_IMPORT` stays a bench flag).
- The record is `evidence/HOME_7_HOLD_TO_JOIN_<date>.md` (no title, serial or path; titles as T1, T2…).

## A — IMPORT-2 (a later day; unattended, with the user's word; `docs/IMPORT.md` is the user's page)

The drive's SNES / NES / Genesis folders through **the plain-folder form** (B58): no symlink root, the drive only
read. **Duplicates expected for SNES** (the hub holds 44 `.sfc`) — the test of the per-system check. **NES and Genesis
are empty on the hub**, so whatever the drive holds there is expected ACCEPT: that is a real import into
`games/nes/` / `games/genesis/` on the hub's disk, so **the user's word covers the apply** (ask once, with the plan's
summary).

0. **Before:** HOME-7 closed; no game, no movie; `/tmp` ≥ 1 GB; the drive mounted **read-only** (as IMPORT-1); its
   three folders found (`<drive>/games/snes`, `nes`, `genesis`; any absent is recorded and skipped). The flag on the
   tool's command line only (no drop-in needed; NEW tags show on the TV only with the companion's flag — ask the user
   whether they want them, as at IMPORT-1).
1. **The listing hashes before** (read-only): `find <folder> -printf '%P %s %T@\n' | sort | sha256sum` for each.
2. **For each system `s` in snes, nes, genesis, in turn:**
   - **I1 inspect:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py inspect --source <drive>/games/<s> --system <s>`
     → exit 0 (3 if empty); the labels and kinds; the rejections by reason;
   - **I2 plan:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py plan --source <drive>/games/<s> --system <s>` → each
     T's ACCEPT / DUPLICATE / REJECT; space ok; the plan and the log. SNES: mostly "duplicate: already in the
     library" or "title present"; an ACCEPT of a title the hub holds is a duplicate-check miss (to B, not applied);
   - **the user's word** on the summary (labels and counts only);
   - **I3 apply / verify:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py apply`, then `verify` — exit 0; each
     ACCEPT `placed`; no `.import-*` under `games/`; **no `data/import/journal.json` left**;
   - one system at a time (apply takes the latest plan).
3. **I4 the log:** `data/import/logs/` checked against the plans' file names and stems with a one-line grep: 0 hits;
   no mount, path or hash.
4. **I6 idempotent:** each `plan` again → every one DUPLICATE; `apply` → nothing copied.
5. **The drive's listing hashes after = before** (all three).
6. **The onn (when the user is next at the TV):** Games → SNES / NES / Genesis show any new titles (" · NEW" only with
   the companion's flag); one launches.
7. The record is `evidence/IMPORT_2_<date>.md` (labels, counts, codes; no title, file name, folder or mount).

## Files

- **Records:** `evidence/B57_PS2_RELAUNCH_STATE_2026-11-08.md`, `B58_IMPORT_SLICE_1B_2026-11-08.md`; the dirs
  `b57_2026-11-08/`, `b58_2026-11-08/`.
- **Patch notes:** `patches/B57_PS2_RELAUNCH_STATE.md`, `B58_IMPORT_SLICE_1B.md`.
- **The user's page:** `docs/IMPORT.md` (extended).
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (the queue U section), `docs/ROADMAP.md` (§H0 slice 1b, §H3 B57).
- **Logs:** `logs/b57_git_status.txt`, `logs/b58_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left (not deleted):** `/tmp/b_q13u_{base,b57,b58,all,scratch}` (~62 MB); `~/.cache/b_q13u_tmp/` (~47 MB of the
  other host suites' temp; this queue's suites clean up); queue T's leftovers as listed there.
- **To B next:** whatever HOME-7's C20 finds; one list entry for the library's own multi-disc PS1 sets (an `.m3u` per
  set in the library — the user's word first; C19's reading); IMPORT-2's findings.
