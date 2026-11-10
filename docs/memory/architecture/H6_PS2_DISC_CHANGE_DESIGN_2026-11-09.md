---
memory_schema: 1
as_of: 2026-11-09
status: DESIGN ONLY (session B, queue AC) — how a two-disc PS2 game moves to its next disc from the onn, with PCSX2 2.8.2 run without its GUI. No code, nothing adopted, nothing committed. PCSX2 was not started; its AppImage and the hub's files were read as data. No title, serial, path or identifier is written here. GameCube's disc change is deferred by the user
---

# H6 — the PS2 disc change (design)

**The user (2026-11-09, B75's G6):** two-disc titles — **yes on PS2**; GameCube deferred ("I have more which might").

**On the drive (counts only, read-only):** 115 PS2 titles; 5 files carry a `(Disc N)` tag; they make **one complete
two-disc set** and three titles of which only one disc is on the drive.

## 1. How PCSX2 2.8.2 is run here

`-datapath data/games/ps2/config -nogui -fullscreen -logfile … -- <the disc file>` (B49 / B53). No Qt main window,
no menu bar; PrivyHub drives it through PINE (B51: save / load / status), SIGSTOP / SIGCONT and the pause hotkey
(B50). The two memory cards (`Mcd001.ps2`, `Mcd002.ps2`) are **shared by every PS2 title** (B50).

## 2. The ways to change the disc without the GUI (read from PCSX2 2.8.2's binary as data)

| Way | What 2.8.2 has | Verdict |
| --- | --- | --- |
| **PINE** | Read / write memory, version, title, id, UUID, game version, status, save / load state. **No disc message** (B51's reading; nothing in the strings names one). | **none** |
| **A hotkey** | The hotkey table's names (`TogglePause`, `OpenPauseMenu`, `ToggleFullscreen`, `Screenshot`, `SaveStateToSlot*`, `LoadStateFromSlot*`, `SwapMemCards`, `ResetVM`, `ShutdownVM`, …; the hub's `[Hotkeys]` binds the defaults). A bare `ChangeDisc` string sits among UI keys, but every change-disc path in the binary is a UI action (`actionChangeDiscFromFile` / `FromDevice` / `FromGameList`, `FullscreenUI::RequestChangeDisc` → `DoChangeDiscFromFile`): **each ends in a file or game-list chooser**, so a key would only open a chooser on the TV. | **none usable** |
| **The Qt menu by `xdotool`** | `-nogui` has no menu bar. The fullscreen UI's pause menu has "Change Disc", which opens its own file browser (ImGui): reaching disc 2 means key-walking a list whose order and focus are not under PrivyHub's control. | **fragile** (rejected) |
| **A multi-disc list (`.m3u`-like)** | 2.8.2 has no playlist; `actionGroupChangeDiscSubImages` is for one image's sub-images (a `.chd` with several tracks), not for separate disc files. Each disc is its own `.chd`. | **none** |
| **A relaunch on the next disc with a state carried over** (B57's shape: save slot 7 through PINE, relaunch, load) | States are named per title (`<serial> (<CRC>).NN.p2s`); disc 2 has its own serial, so the state is not offered to it. Copying it under disc 2's name and loading it would put disc 1's machine state over disc 2 — PCSX2's own disc-state bookkeeping is then inconsistent. | **unsafe** (rejected) |
| **A relaunch on the next disc with the memory card carrying the game** | What a real PS2 does: at the end of disc 1 the game asks the player to **save to the memory card**, then to insert disc 2; disc 2 boots and loads that save. PrivyHub's cards are shared by every PS2 title, so disc 2 sees disc 1's save with no copying. | **recommended** |

## 3. The recommended way, in the user's words

"When the game says to put in the next disc, save in the game first (it usually asks you to). Then press Back →
**DISC** and pick the next disc. The game restarts from that disc; load your save from the memory card."

## 4. What would be built (one queue, **size M**, host + a small client part)

1. **One title per set (host).** PS2 titles whose file names differ only by `(Disc N)` are listed as **one** title
   (disc 1's id kept, so favourites / history / saves stay put), with `discs = n` in its details, as B74 does for a
   PS1 `.m3u`. A set missing a disc stays as separate titles (today's listing).
2. **Start on disc… (client, already built).** B74's Extras entry reads `discs` from the details: no new client code
   for the start; the host's PCSX2 launch takes `disc=j` and opens disc j's file.
3. **DISC on the paused bar for a PS2 set.** B71 / B73's button reads the session's disc count. For PS2 it means
   "end and start disc j": the host stops PCSX2 (its normal stop), and launches disc j of the same set at once (the
   same players, the same Input Profile, patches and cheats per disc — each disc has its own serial).
   - **B74's warning, with PS2's own words** (a new string on the client): *"Save in the game first — the game
     restarts on the disc you pick and loads your save from the memory card."* Once per onn, as B74's.
   - The stream is kept across the relaunch the way B57's multitap relaunch keeps it (its tested path).
4. **The record per relaunch** (`ps2_disc_relaunch`: from, to, the stop's and the launch's times; no title).
5. **Tests:** the grouping (a full set; a set with a missing disc → separate; one-disc titles untouched); `disc=j`
   opens disc j; the relaunch keeps the players; the knob (`PRIVYHUB_PS2_DISCS=0` = today); B74's client test
   extended for the PS2 string.

**Not built:** a live swap during play (no non-GUI way exists in 2.8.2, §2). A game that asks for the next disc
**without** offering a save is not served by this design; none is known on the drive, and the user would see the
warning's advice first.

## 5. A at the TV (when built)

One cell on the two-disc set: play disc 1 to a save (or use an existing memory-card save), DISC → disc 2, the game
boots disc 2 and offers the save. The user's line is the verdict.

## 6. GameCube

**Deferred by the user** ("I have more which might"). For the record (B75 G6a): Dolphin 2609b opens `.m3u` lists and
has `AutoDiscChange`, so its change would be a listing and a config line (size S-M), with no relaunch.
