---
memory_schema: 1
as_of: 2026-11-19
status: BUILT (session B, queue BD) — learn's real picture source starts on the hub: RetroArch "exited during startup" because it was given no display (its own log: no X display, no Wayland server, KMS could not switch mode, "Cannot open video driver"); the capture now starts as the hub starts the title (the hub's display, its own core, its own core options), says why in name-free words when it cannot, and keeps RetroArch's log beside the tool's scratch. Proved by six real runs of rehearse T88: every picture made, the real rules read T88's kept endings (captured without the setup's cheats) as their own — no cheat loading needed. **rehearse T88 is still FAIL — on learn's own bars:** from one still save per ending the learner cannot separate T88's two end screens. Found on the way and fixed: the begin for a title already added, learn's labels anchored on the screen that stays. No bar loosened, the learner not changed, no companion change. Nothing adopted; nothing committed
---

# B167 — learn's real picture source starts

Queue: `handoffs/QUEUE_2026-11-19BD.md` §B167. The directory is `b167_2026-11-19/`: the design + `.sha256` (hashed
23:22:29Z, after the first run's diagnosis and before any code), **an addendum + `.sha256` (hashed 23:36:52Z, before
the label change; it discloses two changes made between the hashes)**, `runs.md` and `run_times.txt` (the six real
runs), `b167_b169.diff` (B167 and B169 together — one tool file holds both; applies on `df81c762`), the test runs, the
mutations, `scripts/`, the checks, `manifest.sha256`. Patch: `patches/B167_ADD_GAME_PICTURES_START.md`.

## Why RetroArch exited at startup

**It was given no display.** The tool runs from a shell with no `DISPLAY` / `XAUTHORITY` (A's and mine); the hub's
user manager has both, and the companion's RetroArch and A's H7-V1 capture ran with them. RetroArch's own log (run 1,
copied out before the tool's cleanup; it stays off the repo): the core asks for an OpenGL context → `[Wayland] Failed to
connect to Wayland server` → `[KMS] Error when switching mode` → **`[Video] Cannot open video driver. Exiting...`**.
The game file (on the hub's own disk, under the library's `games/`), the AppImage, the core and the config were
all found.

Beside it, what H7-V1 passed that the tool did not: **the hub's own core options** (the core's `.opt` and the title's
own; the render scale 4x) with `game_specific_options` on; and for SNES the tool's core list (B95's) said `snes9x`
where **the hub launches SNES with `bsnes`**, whose states the other core cannot load.

## Built (`tools/party_add_game_capture.py`, `tools/party_add_game.py`)

- **The hub's display:** `DISPLAY` / `XAUTHORITY` from the caller, else from the user manager (`systemctl --user
  show-environment`), the one the companion runs under. The window opens on the hub's display, as H7-V1's did; nothing
  is streamed.
- **Never beside a user's session:** the hub's `status` and `native-stream-status` — a game or a client's stream up →
  nothing started (`busy`).
- **The hub's own core** per system (`emulators.json`'s Linux core; the N64 session's) and its states folder; **the
  hub's own core options** read from the user's RetroArch config and copied into the capture's temp config.
- **Every failure a reason**, fixed words, no name: busy, display, content not found, core missing, config (an
  unreadable base config too), exited (RetroArch stopped, its log naming none of these), not playing, state refused.
  learn's cell **"pictures made"** carries it with where RetroArch's log is ("logs/<role>.retroarch.log in the title's
  add_game folder"); rehearse carries it as `learn: pictures made` / `rehearse's pictures made`. **Never "ProofError"
  alone.** A failure not of RetroArch's (the tool's own) names its type, its trace kept beside the log, off the repo.
- **RetroArch's log stays off the repo:** copied to the title's add_game folder, `logs/`, whatever the end.
- **Disclosed, after the design's hash (in the addendum):** the screenshot read whole (run 2: a PNG read while
  RetroArch still wrote it — PIL's `OSError` / `SyntaxError`; at the 4x render scale the file is large): the size the
  same twice 20 ms apart and the picture loads, up to 1.5 s, else the frame skipped. **For a title already added,
  rehearse takes the begin its mini game starts from** — the rules folder's own (run 3: T88's kept `begin.state` is the
  rules folder's **plain** begin from before its setup, sha256 equal; not the setup's begin the party mini game loads);
  a kept begin that differs is listed unused. **A kept extra ending's cell** is met when the scratch rules read it
  exactly as the real rules do (an extra the real rules do not end on — T88's `end_p1_b` / `end_p2_b`, `other` on every
  frame — is not failed for not ending; one they end on must be its own); a role's ending stays strict.
- **After the addendum's hash: learn's labels anchored on the screen that stays** (run 5's pictures, copied off the
  repo for study, no title started for it): T88's kept `end_p1` was saved a moment before its end screen settled — the
  real rules read `other` for ~1-2 s, then `end_P1`; learn's labels measured "moved" against each run's **first**
  frame, so they took that transitional frame as `end_P1` and ignored the 19 frames of the real end screen. Now a begin
  or an ending is labelled by the frame most of its run stays near (B140's measure; the earliest on a tie); the rest
  `ignore`. A new title's ending saved a beat early would have been learnt from the wrong screen — and could have passed.

## The setup's cheats (BC's item 4): settled — not needed for T88

Runs 3-6: T88's kept `end_p1` / `end_p2` and the user's slot are under its setup; the capture loads no cheats; **the
real rules read the captured endings as end_P1 / end_P2** on every run (they were learnt in part from H7-V1's
pictures, which loaded no cheats either). A state holds the game's memory, so what the setup unlocked is in it; a title
whose cheats change the picture continuously (not unlocks) would show otherwise — not seen here, not built.

## rehearse T88, as I ran it: FAIL — on learn's own bars (`runs.md`)

Six runs, each after `status` and `native-stream-status` showed nothing running and no client: run 1 as at the TV
(no display); run 2 started RetroArch (the screenshot read); **runs 3-6 made every picture**. Run 6, the final code:
**FAIL** — `learn: every class separable` [end_P1, end_P2], `margin_needed` 0.0164 (bar 0.0796), held-out unknown
0.6552, the endings' replays not ended; with no scratch spec, the four "read as the real rules" cells not met; **the
real rules folder 15 files, 0 changed — met; the scratch removed — met**. Every run's real-rules cell met.

**Why the learner cannot meet its bar here** (computed offline on run 5's pictures, no title started): T88's end screen
is its select screen with a per-side win tally. learn treats all of a title's runs as one source, so its outcome mask is
wherever start and the endings differ; end_P1 and end_P2 differ only in the tally's few pixels inside it. With the
labels right (the screen that stays) the margin is 0.0169, and with the old first-frame labels 0.0303 — only because
that frame was the wrong screen. The real T88 spec reached 0.0921 from three recorded sittings: different matches and
characters vary inside each class, which is what narrows the mask to the tally. **No bar was loosened and the learner
was not changed.**

## What this proves of learn for a new title, and what it does not

**Proves, on the hub:** the picture source starts and runs for a PS1 title on the hub's own disk under a setup — the hub's
display, its PS1 core, its core options (the title's own found), a kept state and a user's slot loaded, every picture
made at the hub's render scale, RetroArch's log kept; the real rules read those pictures as their own; learn's whole
path runs and says its verdict as cells; the real rules folder untouched. **Does not prove:** that learn's bars can be
met from one save per ending — for T88 they cannot, and any title whose ending screens differ only in a small part
will be the same (each ending saved in two different matches would give the learner what the sittings gave); another
core (N64's, `bsnes` for SNES — chosen by the code, never run here); a title on the drive rather than the hub's own disk
(the same path in the code — the library's `games/` — not run); four players and `places` (T89's kept folder lacks three rows); a title whose
cheats act on the picture continuously.

## Tests (`tests/b167_pictures_start/`, 9; B163's updated, 7)

A made-up RetroArch (`fake_ra.py`, for the AppImage), made-up cores, a made-up user RetroArch config, a made-up base
config, a made-up hub: **each reason** — busy (nothing started, no log), display (none given; and RetroArch's own video
line), content not found and core missing (before the start), config (the log's line; an unreadable base config),
exited, not playing, state refused — the words fixed, no name or path, RetroArch's log kept; **the display from the user
manager** (the fake sees `:77`); **the hub's core** (bsnes for SNES, Beetle PSX HW for PS1, Mupen64Plus-Next for N64),
**the core's and the title's own core options copied** (another title's not), `game_specific_options` on, frames made;
**learn's cell names the reason** and where the log is, no name, no "ProofError"; **the labels of an ending saved a
moment early** (two frames of another screen, then the end: those two ignored). B163: the rules folder's begin taken;
a kept begin that differs listed unused. Runs and mutations: `tests_x3.txt`, `tests_mutations.txt`.

**Runs:** B167 9 OK ×3, B169 5 OK ×3, B163 7 OK ×2, B157 17 OK ×1; B162 once FAIL (its close cell, from B169 — B169's
record), then **17 OK ×2** after its test was updated; 0 temp dirs left. **Mutations 9 / 9 caught**
(`tests_mutations.txt`): the reason swallowed, B95's core list back, the display not passed, the busy check off,
RetroArch's log lines not read, the labels back to the first frame (B167); the rules folder's begin off (B163's tests);
the card cell always met, no before at solo (B169). No companion change: the flags untouched, the hub's routes as HEAD's.

**Kept off the repo:** RetroArch's logs of run 6 in the title's add_game folder (`logs/`); run 1's two logs and run 5's
pictures were in my own scratch on the main disk for the diagnosis — the pictures removed after this record, the logs
kept there (they name the game).
