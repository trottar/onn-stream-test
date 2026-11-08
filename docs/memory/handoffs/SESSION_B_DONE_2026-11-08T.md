# SESSION B — done, 2026-11-08 T (QUEUE_2026-11-08T: B54, B55, B56; run 18:06-18:52Z)

- **Baseline:** `0eb115d9` — HOME-6 committed as `68386b32`, then the user's commit of the prompt / queue files.
- **Checked first:** only the companion and `privyhub-diag` active; the tree held only the prompt files.
- **Not done:** nothing committed or adopted; no stream, no companion or keeper restart, no adb; PCSX2 not started.
- **Nothing imported, nothing written to the drive, nothing deleted, nothing fetched.**

## What was built (queue T's combined diff applied to the tree, uncommitted)

The diff is `evidence/b56_2026-11-08/queue_t_combined.diff`: B54 + B55 + B56 against the baseline.

1. **B54, hold-to-join** (`evidence/B54_HOLD_TO_JOIN_2026-11-08.md`; the client on by default, `player_prompt 0` =
   none):
   - **The join:**
     - at every start and every unpause the line reads "Hold any button to join";
     - **a 500-ms hold** of a face button or Start makes that pad the next player ("P1 joined — hold to add Player 2");
     - a tap does nothing;
     - a 1-player title closes after P1; two ports close after P2.
   - **A third pad holding asks the host for the multitap at once:**
     - the paused frame and "Setting up 4 players…";
     - the companion relaunches the title with four ports;
     - PS1 comes back where it was (a relaunch save, then the running-core load);
     - budget 15 s, ~6-10 s expected;
     - **a PS2 relaunch restarts the title** (B55's slot not yet wired into it).
   - JVM 228 / 228; host 19 + 10; 11 mutations caught.
2. **B55, PS2 recovery through PINE** (`evidence/B55_PS2_RECOVERY_STATES_2026-11-08.md`; inside `PRIVYHUB_PS2=1`):
   - **live:**
     - the slot-9 save;
     - its load at the hold's return and the stall resume. The load ≤ 0.31 s blocks; B52's picture is checked after
       the resume, which keeps B16's ≤ 1.0 s;
     - the give-up save (slot 8), with the prompt's Resume / Copy / Discard;
   - **off:** the rewind;
   - `tests/ps2_session` 93; 8 mutations caught.
3. **B56, the PS1 USB import** (`evidence/B56_IMPORT_SLICE_1A_2026-11-08.md`, `docs/IMPORT.md`; behind
   `PRIVYHUB_IMPORT=1`):
   - `tools/import_usb.py` inspect / plan / apply / verify, with the user's four defaults: a real BIOS ("(OpenBIOS)"
     until then); multi-disc as one `.m3u` entry; " · NEW" 7 days; an `.iso` hidden beside its `.chd`;
   - 21 tests; 10 mutations caught;
   - fixture trees only.
4. **The APK** `9aa00ba2afe19a7f36b869454d7d5e683185dc97fc116cc6f8f75878bc5fe73f` (B5 … + B46 + B47 + **B54**; B27 / B29
   out), 9,702,680 B (`evidence/queue_t_2026-11-08/APK.md`):
   - the same tree without queue T rebuilds `cfe0211c…` byte for byte; the new one rebuilds to the same bytes;
   - the same signer; JVM 217 / 217;
   - **pinned `PrivyHub/app/build/queue_t_built/app-debug.apk`, NOT installed.** `cfe0211c…` stays CONFIRMED.
5. **Checks:** every host suite on each item's copy and on the combined copy as the baseline. The same six `tools/`
   tests fail in every copy, identically. The four touched suites are green in the tree.

**One line for the user (B54):** hold any button for half a second to join. When a third controller holds on a
two-player game, the TV stays on the game's paused picture with "Setting up 4 players…" for about 6-10 seconds (15 at
most), then the game comes back where it was with that controller as Player 3.

## A — HOME-7 (~40 min at the TV; the user's pads on the onn over Bluetooth, nothing on the hub; every reply starts "YOU, now:")

**The properties** (all eleven, read back empty at the start and the close): `restart_guard`, `stall_signal`,
`link_notice`, `link_report`, `loss_guard`, `wifi_lock`, `opus_decode`, `surface_hold`, `pad_slots`, `vod_retry`,
`player_prompt` (`debug.privyhub.*`).

**Stage 1 (A alone; no game, no movie; outside 04:30-05:30Z):**
1. `/tmp` ≥ 1 GB free. Sixteen adopted lines; `e3_state.py --check` ok; `cfe0211c…` CONFIRMED; the eleven properties
   empty; only the two units.
2. **The companion restart** (queue T's host code live: B54's relaunch and rows, B55's PINE states), then sixteen
   lines read back. No keeper restart is needed.
3. **The install:**
   - preserve `cfe0211c…` (`home7_previous/`);
   - copy `PrivyHub/app/build/queue_t_built/app-debug.apk` to `PrivyHub/app/build/home7_installed/`;
   - `adb install -r`, and read back `9aa00ba2…`, paired;
   - **every property empty** (hold-to-join is on by default).
4. **Pre-register** the rows below, hashed.
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
- **Reply:** "YOU, now: Back and Stop, then start a PS2 game and play about a minute. Press Home on the remote, count to
  2, and go back to PrivyHub (the recent apps or its tile). Send 'Stage 5' and say whether the game was where you left
  it."

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
- **Reply:** "YOU, now: Back and Stop the game, and send 'Stage 6' — that's all for the games."

**Stage 6 — the close and the CONFIRMED rule (CL-B7 §6):**
- Every property empty; sixteen lines; `--check` ok.
- If C15, C16 and C17 are valid and met with every property empty, **`9aa00ba2…` is CONFIRMED** and the pin moves:
  `tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise
  `cfe0211c…` goes back on.
- C18 decides B55 (no adoption needed; it is inside the adopted `PRIVYHUB_PS2=1`); a failure goes to B.
- The record is `evidence/HOME_7_HOLD_TO_JOIN_<date>.md` (no title, serial or path; titles as T1, T2…).

## A — then IMPORT-1 (with the user's hand; `docs/IMPORT.md` is the user's page)

0. **The user, before:** a USB stick with `PrivyHub-Import/games/ps1/` holding one or two PS1 titles (`.chd`, or a
   `.cue` with its `.bin`s; one multi-disc set named `(Disc 1)`, `(Disc 2)` if they have one), and
   `PrivyHub-Import/bios/ps1/` with their own console's `scph5500` / `5501` / `5502.bin` if they have one. Into the hub.
1. **The bench drop-in** (the list's NEW / hide / "(OpenBIOS)" marks; seventeen `PRIVYHUB_` lines while it is in, so
   `--check` is not ok on the environ only):
   ```
   printf '[Service]\nEnvironment=PRIVYHUB_IMPORT=1\n' > ~/.config/systemd/user/privyhub-companion.service.d/b56-import.conf && systemctl --user daemon-reload && systemctl --user restart privyhub-companion
   ```
   - On the onn, Games shows "PlayStation (OpenBIOS) (<n>)" (the BIOS folder is empty today).
2. **Find the stick** (no mount by A unless it did not mount itself): `lsblk -o NAME,RM,MOUNTPOINT` and `ls
   /media/$USER/`. The record names it `<stick>`.
3. **Before:** `find /media/$USER/<stick>/PrivyHub-Import -printf '%P %s %T@\n' | sort | sha256sum` (the stick's
   listing hash, read-only).
4. **Inspect:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py inspect /media/$USER/<stick>`
   - **I1:** exit 0; the T labels with kinds and file counts; every rejection with its reason; the BIOS line.
5. **Plan:** `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py plan /media/$USER/<stick>`
   - **I2:** exit 0; each T's ACCEPT / DUPLICATE / REJECT with its reason; space ok; the plan file and the log.
   - **Show the user the summary, labels only** (in the reply; `--names` only on the hub's own screen if they want
     it).
   - Reply: "YOU, now: read the plan. Say 'import' to copy what it accepted, or tell me what to leave out."
6. **On the user's "import":**
   - make sure no game is active (`apply` refuses if one is);
   - `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py apply`, then `PRIVYHUB_IMPORT=1 python3 tools/import_usb.py
     verify`.
   - **I3:**
     - apply exit 0 and verify exit 0;
     - each accepted T `placed`;
     - `find games/ps1 -name '.import-*'` empty;
     - `data/import/marks.json` with one `new` per placed title;
     - a real BIOS copied (`BIOS copied: <region>` and the warning line), if one was on the stick;
     - **the stick's listing hash before = after.**
   - **I4, the log:** `data/import/logs/` holds no title, file name or hash. Check it against the plan's names with a
     one-line grep; the names stay out of the record.
7. **The onn:**
   - **I5:**
     - Games → PlayStation shows the new titles with **" · NEW"**;
     - a multi-disc set shows once;
     - "PlayStation (<n>)" without "(OpenBIOS)" if a BIOS was imported;
     - one new title launches and plays.
   - Tell the user: a PS1 save state made before a real BIOS may not load after it; memory-card saves are fine.
8. **Idempotent:**
   - **I6:** `plan` again → every one `DUPLICATE` ("already in the library"), exit 0. Then `apply` → nothing copied.
9. **The close:**
   - ask the user once: keep the NEW tags (the bench drop-in stays, not adopted) or remove the drop-in. To remove:
     `rm ~/.config/systemd/user/privyhub-companion.service.d/b56-import.conf && systemctl --user daemon-reload &&
     systemctl --user restart privyhub-companion` (sixteen lines again; the imported titles stay; the tags go);
   - the record is `evidence/IMPORT_1_<date>.md` (labels, counts, codes; no title, file name, label or mount).

## Files

- **Records:** `evidence/B54_HOLD_TO_JOIN_2026-11-08.md`, `B55_PS2_RECOVERY_STATES_2026-11-08.md`,
  `B56_IMPORT_SLICE_1A_2026-11-08.md`; the dirs `b54_2026-11-08/`, `b55_2026-11-08/`, `b56_2026-11-08/`,
  `queue_t_2026-11-08/` (the APK).
- **Patch notes:** `patches/B54_HOLD_TO_JOIN.md`, `B55_PS2_RECOVERY_STATES.md`, `B56_IMPORT_SLICE_1A.md`.
- **The user's page:** `docs/IMPORT.md`.
- **Docs, insertions only:** `docs/KNOWN_ISSUES.md` (the queue T section), `docs/ROADMAP.md` (§H0 slice 1a, §H3 B55).
- **Logs:** `logs/b54_` / `b55_` / `b56_git_status.txt`; `handoffs/SESSION_B_STATUS.txt`.
- **Left:**
  - `/tmp/b_q12t_{base,b54,b55,b56,all,apk,apko,scratch}` (the scratch holds the mutation copies and the first APK
    copy);
  - `~/.cache/b_q12t_tmp/` (~60 MB of the host suites' temp; the suites other than this queue's do not clean up);
  - 308 old `b46_*` dirs in `/tmp` from B46's runs (that suite now cleans up). None of these were deleted.
- **To B next:** B54's PS2 relaunch through B55's slot (now both are in the tree); the `.gitignore` line for
  `PrivyHub-Import/`; slice 1b (the journal's resume across a crash; other systems).
