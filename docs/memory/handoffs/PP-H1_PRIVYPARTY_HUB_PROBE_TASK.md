---
memory_schema: 1
as_of: 2026-11-16
status: TASK HANDOFF — PP-H1, PrivyParty on the hub, step 1 of four: the probe with no stream (session A, hardware, UNATTENDED ~40 min; no user, no onn, no pads; nothing asked of the user but the read line). Godot 4.7.2-stable (standard build) fetched on the user's recorded go and checked against its published checksum; the board game's 25 scripted checks run on the hub; the game drawn on the hub's own display with the owner's pictures under each renderer, frame rate and load measured in its heaviest scene; closed the clean way. No stream, no companion change, no flag (eighteen lines before and after). Pre-registered. Nothing adopted; nothing committed in either repo
---

# PP-H1 — does the board game run on the hub at all, and with which renderer?

Read first: `handoffs/PRIVYPARTY_PC_HANDBACK_2026-11-12.md` (the PC side's hand-back and Cowork's note: where the repo and the pictures are on the hub, the user's go for the downloads, the four steps agreed, "close with the `quit` action, never SIGTERM"); the board game repo's own `README` ("Tools", "Controls", "Control from outside", "Modules") and `checks/`; `H7_V4_2026-11-16.md` (where H7 stands — the hub now says who won a mini game from its end screen); `docs/memory/CURRENT.md`.

**Where things are (by the user's hand, 2026-11-12):** the board game's repo beside this one (`~/Projects/privyparty`, its own git repo — **never written to by this task beyond what Godot's own import step creates, and nothing in it committed**); the owner's pictures on the hub's disk outside both repos (`~/privyparty_content/private`). **Real photos never enter git: no picture, screenshot, face, file name or listing of that folder in any record — a file count and a total size only.**

**The user's go for the fetch, verbatim:** asked "Do I have your go for the Godot and repo downloads when we reach step 1?" — "Yes you have my permission when step 1 is reached". The repo is already on the hub. **So exactly one thing is fetched here: the Godot 4.7.2-stable Linux x86_64 standard build (not .NET) and its release's checksum file, from the Godot project's own release page.** Nothing else is fetched or installed (no package, no template, no driver).

## Stage 1 — before anything is fetched

- Outside 04:30-05:30Z and not starting within 45 min before it (else: "YOU, now: the hub's nightly window runs until 12:30 am Eastern; send the read line again after that").
- This repo: HEAD named with H7-V4 committed and the tree clean but for this task's files (else stop: "YOU, now: commit H7-V4 first, then send the read line again"); only the companion and `privyhub-diag`; no game running, no stream; eighteen `PRIVYHUB_` lines; `--check` (not ok on adb alone is noted, not a stop).
- The board game's repo: its HEAD, `git status --short` (clean), the count of files in `checks/` (25 expected, `step0`-`step24`), whether Godot's cache folder is git-ignored there. The pictures' folder: exists, file count, total size.
- The hub: CPU, memory free, disk free, the graphics device and driver, whether Vulkan and OpenGL are offered (from tools already on the hub — whichever of `vulkaninfo`, `glxinfo`, the kernel's own files exist; none installed), the X display the emulators use and its mode, load and temperatures at rest.
- **The pre-registration hashed** (below), before the fetch.

## Stage 2 — the fetch (the one exception to "nothing fetched")

The standard Linux x86_64 zip for tag `4.7.2-stable` and that release's SHA-512 sums file, from the Godot project's own release location (the exact addresses used go in the record — they are public web addresses, not ours). **The zip's SHA-512 must equal the published line**; if not: the file moved aside (not deleted), nothing run, NOT MET. Unpacked off both repos into a tools folder under the user's home (stated in the record as "the tools folder", no path); the executable's own `--version` recorded; its `--help` kept (the flags below are confirmed against it before use).

## Stage 3 — the 25 checks (headless, as the hand-back gives them)

From the board game's repo root: the import step once, then each script in `checks/` in order — for each: the last line (`STEP N CHECK: PASS (K assertions)`), the exit code, the seconds, the hub's load meanwhile. They use none of the owner's pictures. A failure: its whole output kept, the run goes on to the next script.

## Stage 4 — the game on the hub's display (no stream; nobody at the controls)

On the X display the emulators use, 1920 × 1080, with the owner's pictures (`--content=` after the `--`), for each of **Forward+ (Vulkan)**, **Mobile (Vulkan)** and **Compatibility (OpenGL)** — the renderer chosen per run by the command line, the project's files untouched:

1. **Does it start?** The window appears (its id, size and title class from the X server — how the hub's capture would find it), no error or crash line in its output, the renderer and device it reports.
2. **Frame rate and load in the heaviest scene** — the dark half of the second board with fog, mist and lamps on (the hand-back's worst case). How the scene is reached with nobody at the controls is A's to settle from the repo and state: the on-screen checks or the game's own nobody-at-the-controls play (`play_headless`) run with a window and Godot's own frame-rate print; if no such run shows that scene, the nearest that does, named. For each renderer, **≥ 60 s with vsync on** and **≥ 60 s with vsync off** (headroom): the frames a second per printed second (median, lowest, seconds under 50 and under 30), Godot's CPU (% of one core), the graphics device's busy share and memory if the kernel offers them, the hub's load and temperature. The same once with "Fog and lamps" off if a command-line or settings way exists without editing the repo (else skipped, stated).
3. **Closed the clean way:** the `quit` action (F10 to the window) or a window close request, with a tool already on the hub — which one, the exit code, the seconds it took, no crash line. If neither is possible with what is installed: say so (it decides the hub's launch kind later) and end the process the plain way — recorded as such.
4. Nothing left running (counted); the X display as before.

A picture taken to check a scene is A's own, off both repos, and is described in words only (no names, no faces): "the dark board with fog and lamps, four figures".

## Pre-registered (hashed at stage 1) — nothing perceptual; nothing here adopts anything

- **F — the fetch:** the zip's SHA-512 equals the published one; the executable reports 4.7.2 stable.
- **C — the checks:** 25 of 25 end with their PASS line and exit code 0 on the hub.
- **G — the game starts and stops:** under at least one renderer the game starts on the hub's display with the owner's pictures, with no error or crash line, and closes by the `quit` action or a window close request with exit code 0.
- **R — a renderer is "fit" for the next step** when, in the heaviest scene at 1920 × 1080 with fog and lamps on and vsync on, the frames a second have a median ≥ 59 and no second under 50, over ≥ 60 s. Each renderer is marked fit / not fit / did not start; with vsync off the median is its headroom. **The one to carry forward** = the fit renderer with the most headroom (stated, not adopted). No renderer fit → said plainly, with the numbers with fog and lamps off if they could be taken.
- **U — nothing else touched:** eighteen lines before = after, `--check` as at stage 1; the two units only; this repo's tree changed only by this record; the board game's repo `git status --short` after = before (Godot's cache git-ignored — if it is not, what appeared is listed and left, nothing deleted); the pictures' folder count and size before = after; the hub's saves untouched (no emulator started).
- **MET** = F, C, G and U met and at least one renderer fit. F, C, G, U met with no renderer fit = "MET but for R", reported as such.

## The record

`evidence/PP_H1_<the UTC date>.md` + dir: `pre/` (both repos' heads and status, the hub's facts, the pre-registration and its hash), `fetch/` (the addresses, the published line and the computed one, `--version`, `--help`), `checks/` (a table: step | PASS line | assertions | exit | seconds; any failure's output), `display/` (per renderer: the start, the window's facts, the frame-rate rows and their summary with vsync on and off, CPU, graphics busy, temperature, the close; how the heaviest scene was reached), `close/`, title and redact checks (no title, no path, no file name from the pictures' folder, no address of ours), manifest. `KNOWN_ISSUES.md` (insertions only); `docs/ROADMAP.md` — PrivyParty on the hub: step 1's verdict and what waits (step 2: a streamed probe — the virtual pads as Godot's devices 0-3, pause and quit from the onn, capture and sound, the encoder's cost with the board's busy textures; step 3: the adapter mini game behind `play(players) -> scores` calling the hub's start and result; step 4: the stream switched between the board's window and the emulator's); `logs/pph1_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after; eighteen lines; Next Action — step 2's design, Cowork's).

**The reply begins "YOU, now: commit"**, then in one line each: the fetch (checksum equal or not, the version); the checks (how many of 25 passed, the total minutes); per renderer — started or not, frames a second with vsync on (median, lowest) and off (median), fit or not; the renderer to carry forward; how the game was closed and whether that was clean; whether anything else was touched; MET / MET but for R / NOT MET; the eighteen lines.

No sudo, no nft, the Opal read-only, no adb use beyond `--check`; no stream; no companion or keeper restart; no flag; no emulator started; no network addresses of ours, titles, serials, paths or names from the pictures' folder anywhere in git; no picture in git; nothing written to the drive; nothing fetched but the one build and its checksum file; nothing installed; nothing deleted; the board game's files not edited; nothing adopted; nothing committed in either repo.
