---
memory_schema: 1
as_of: 2026-11-20
status: TASK — session G6. G6-SCREEN1: in portrait handheld mode the video box becomes 4:3 (1200 x 900 on the tablet), 4:3 games are cropped to fill it, SELECT / START / End move down with it, and the stick / D-pad / face / shoulder cluster stays exactly where it is on the screen. A new tablet-only candidate; its run pre-registered and hashed before it. The onn keeps ca53df0d…. Nothing adopted; nothing committed by you.
---

# G6-SCREEN1 — a 4:3 picture in portrait handheld mode

The id is G6-SCREEN1 on purpose: G6-HM5 (latency video) and G6-HM6 (rotation, customization) are already reserved in
`docs/memory/architecture/G6_HANDHELD_PLAN_2026-11-19.md`. Do not reuse or renumber them.

## The user's request, verbatim (2026-11-20, with a photo of the tablet in a PS2 game)

"We can easily increase the screen presence. Select, start and end shift closer to the controller and a 4:3 picture
would fit perfectly"

Cowork's reading of the photo and the code: the video box is 1200 x 675 (16:9) and the PS2 picture sits pillarboxed
inside it, about 900 x 675. Below it, between the SELECT / START / End row and the D-pad / right-stick row, there is an
empty band of about 245 px. A 4:3 box at full width is 1200 x 900: the picture grows by a third in each direction
(about 1.78 x the area) and the 225 px it needs come out of that empty band.

## Part A — two notes for the record (read only)

Write these as dated lines in the plan and as a short §0 of the new evidence file. Cowork read them from the raw logs;
confirm each from the files before writing it.

1. **The green-screen hiccup, 2026-11-20 ≈ 04:20:20Z.** `native_stream_recovery.log` has `surface_lost` with
   `reason: user_leave`, `away_ms: 12109` against `bound_ms: 12000`, `outcome: restarted`; heartbeats stop at
   04:20:18.2Z and the next session's first heartbeat is 04:20:35.4Z with `rendered_frames: 0`. The tablet left the
   stream activity (Android's "user leave": a Home or recents gesture) for 12.1 s, just past the surface hold, so the
   hub restarted the stream. While it was away the hub's stall recovery ran five save / pause / load cycles
   (`20261119-231800-ps2.log`, 04:20:20–04:20:32Z), with `ps2_states` picture verdicts `static`. Record it as observed;
   the cause of the leave is not known (the user was not asked). The hub kept 60 fps throughout
   (`native_frame_sizes.jsonl`) with load ≈ 2 and GPU ≤ 47 °C (`host_resource_samples.jsonl`).
2. **The tablet now reaches the hub over Tailscale from the user's home Wi-Fi** (the user, 2026-11-20: "I downloaded
   tailscale and am running from my home wifi"). The hub classes these sessions `remote-direct` (from 05:48:24Z), with
   the remote ladder in force (start at the floor rung, cap 7000 kbps). The 05:49:24Z → 05:57:36Z session ran 8 min
   12 s with no `client_stall`, no `link_notice_shown`, 7 lost video packets, 0 resyncs, 59.98 fps rendered, at
   −64 … −73 dBm. One session; not yet a finding. G6-WIFI1 is **held**, not run, not withdrawn.

No address, overlay address, SSID or device name in either note.

## Part B — G6-SCREEN1 (code for the tablet only)

### B1. The video box

- `HandheldGeometry.videoBoxHeight(w)` becomes **w · 3 / 4** (1200 → 900); `padRegionHeight(w, h)` stays
  `h − videoBoxHeight(w)` (2000 − 900 = 1100 on the tablet). If that leaves the pad region shorter than the cluster
  needs on some other screen shape, keep 16:9 there and say so; on the tablet it fits.
- The handheld report's `video_box` and `pad_region` then read `1200x900` and `1200x1100`.

### B2. The crop (4:3 games fill the box)

- The stream stays as it is: the hub is not changed at all. The crop is on the client, in handheld mode only.
- For a session whose picture the hub presents as **4:3 pillarboxed inside the 16:9 stream**, show the centre 4:3 of
  the stream (960 x 720 of 1280 x 720) scaled to fill the box. With a full-width box the simple way is to size the
  video view at 16:9 of the box's height (1600 x 900) centred, so the bars fall off the screen's left and right edges;
  use that or anything equivalent, and say which.
- **Which systems are cropped.** Prove it from the hub's files on disk, read only: each emulator's aspect setting as
  the hub launches it (PCSX2 for PS2, the PS1 core, and any other system the handheld can launch), including per-game
  overrides and any widescreen patch or setting. Crop a system only where every game the hub can launch for it is
  shown 4:3. A system not proven, or with any widescreen game, is **not cropped**: its 16:9 picture sits at the top of
  the 4:3 box, full width, and the rest of the box is the background fill. List what you found per system.
- How the client knows the system: from what it already has when the game is launched (the catalog entry). If it
  doesn't have it, say so and do not add a hub field in this task.
- Add to the handheld report: `video_crop` = `"4:3"` or `"none"`, and `video_source_rect` = the shown rectangle of the
  stream in stream pixels (for example `"160,0,960x720"`).
- Overlays in the video box (the paused picture, the "P1 joined" note, the status texts) keep working; the paused
  picture is cropped the same way as the live one.

### B3. The pad region (1200 x 1100 on the tablet)

The PS2 layout's reference height becomes **1100** (`Ps2TouchLayout.REF_H`), so on the tablet `sy = 1`.

- **The cluster does not move on the screen.** Every control except SELECT, START and End keeps its exact on-screen
  centre and size from G6-HM4b: in the reference numbers, its y becomes **y − 225** (D-pad and right stick 520 → 295,
  shoulders 774 → 549, R3 790 → 565, left stick 1030 → 805, L3 1040 → 815, the face buttons 940 / 1030 / 1120 →
  715 / 805 / 895). x, radii, the 0.875 throw, the press areas and every hit scale stay as they are.
- **SELECT and START** keep their size and x (400 and 600) at **y 70** from the top of the (now lower) region: on the
  screen they move down 225 px, toward the controls, as the user asked.
- **End** stays at y 70 but moves right, to the smallest x that gives **≥ 0.5 cm** between its rectangle and the right
  stick's press area. Cowork's arithmetic at 94.5 px per cm: x ≈ 1080 (from 960). End must stay inside the region and
  clear of R1 / R2.
- The footer text and the status panel are unchanged; the side-edge gesture exclusions follow the shoulders as today.

### B4. The geometry check

Write `docs/memory/evidence/g6_screen1_2026-11-20/layout_check_screen1.py` (from `layout_check_b.py`) and its output
file. In px and cm (94.5 px per cm, the figure G6-HM4b used), on the tablet's 1200 x 2000 screen:

1. every cluster control's on-screen centre equals G6-HM4b's within 1 px;
2. no drawn shape overlaps another, and no press area overlaps another;
3. the clearance between End's rectangle and every press area — **≥ 0.5 cm** required;
4. the clearances SELECT ↔ D-pad and START ↔ right stick, drawn and press, reported (Cowork's arithmetic: SELECT's press
   area is ≈ 12 px from the D-pad's, drawn ≈ 52 px; report the real figures; nearest-centre already settles a shared
   point, so this is reported, not a gate);
5. every SELECT / START / End drawn size ≥ 1 cm in its smaller side, as before.

### Rules

- The onn's code paths stay as they are, shown as at G6-HM4b (`onn_unchanged_checks.txt`'s five checks again). Any
  change in `NativeStreamActivity` goes through a hook whose default is today's expression, like H1–H9.
- No adb, no install, no stream, no service restart, nothing fetched. The hub, the companion and `tools/` are
  untouched; the onn keeps `ca53df0d…`; the pins do not move. Reading the emulators' settings files is allowed; editing
  them is not.
- Preflight: no game, gradle or other Claude Code session running, or stop and say so. The user may be playing on the
  tablet: if a game is running, stop and say so.
- Touch no other session's files and no other prompt file. `Claude outputs/G6_tablet/G6-WIFI1_SEAT_DROPOUTS_TASK.md`
  stays as it is.

### Steps

1. **The change and its tests.** Tests pin: the 4:3 box height; the new REF_H and the cluster's on-screen centres
   unchanged; SELECT / START at y 70; End's new x; the crop decision per system and the source rectangle; no crop for an
   unproven system. Every earlier test passes.
2. **Build.** `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`. Preserve the previous `build/outputs` APK
   first. The candidate goes to `PrivyHub/app/build/g6_screen1_candidate/`, plus a copy named
   `PrivyHub-handheld-preview-<sha8>.apk`.
3. **The checks.** The onn-unchanged checks, the diff, `git diff --check`, `git apply -R --check`, the redaction check,
   and B4's geometry check.
4. **Pre-register the run, hashed before it:** `docs/memory/evidence/g6_screen1_2026-11-20/preregistration.md`. Copy
   G6-HM4b's pre-registration exactly (conditions, "Which session", cells, bounds, the verdict rule, the numbered
   steps with SELECT and START on their own lines, the remarks), changing only:
   - the candidate's hash;
   - **the conditions:** the tablet connects over Tailscale from the home Wi-Fi; the session's class is
     `remote-direct` or `lan`, whichever the hub logs, recorded as context, not a cell;
   - **two added cells:** the handheld report reads `video_box` `1200x900` and `pad_region` `1200x1100`; and, for the PS2
     session, `video_crop` `"4:3"` with `video_source_rect` `"160,0,960x720"` (or, if B2 found PS2 not provable, `"none"`
     and the reason, fixed now, before the run);
   - **two added remarks** (not cells): whether the bigger picture looks right with nothing cut off that matters, and
     whether End's new place is ever pressed by mistake.

   Hash it.
5. **Record:**
   - `docs/memory/evidence/G6_SCREEN1_4X3_PICTURE_2026-11-20.md`: §0 part A's notes, part 1 now, part 2 after the run;
   - a patch note and its `PATCH_INDEX.md` row;
   - the plan's dated lines (part A's two and this stage) and `CURRENT.md`'s G6 line;
   - `logs/g6_screen1_git_status.txt`: this task's files only.

### Gates

- every JVM test passes;
- BUILD SUCCESSFUL;
- the onn-unchanged checks pass;
- B4's checks 1, 2, 3 and 5 pass;
- `git diff --check` is clean;
- the redaction check is clean;
- `tools/check_memory_health.py` passes.

No address, serial, token or pairing code; device ids as 4 hex digits and "…"; no game title. Nothing adopted; nothing
committed by you.

Your last reply begins "YOU, now: commit", then:
- part A's two notes as written;
- the crop decision per system, with the files it rests on;
- the box, the region and End's new x, with B4's clearances in px and cm;
- the candidate's sha256;
- the tests;
- the onn checks;
- the pre-registration's sha256;
- the user's steps exactly as pre-registered.
