---
memory_schema: 1
as_of: 2026-11-20
status: RECORD — G6-SCREEN1 part 1 done: the portrait video box 4:3 (1200 x 900), SNES and N64 cropped to fill it (PS2, PS1 and the rest not: not provable 4:3), SELECT / START / End moved down, the cluster unchanged on the screen; candidate e4263fd9… for the tablet only; the run pre-registered (eddc7ddc…, 06:25:50Z). The onn keeps ca53df0d…. Nothing adopted. Part 2 after the run.
---

# G6-SCREEN1 — a 4:3 picture in portrait handheld mode (part 1: notes, code, build, pre-registration; 2026-11-20)

Task: `../handoffs/G6-SCREEN1_4X3_PICTURE_TASK.md` (a byte-for-byte copy of the Cowork file). Patch note: `../patches/G6_SCREEN1_4X3_PICTURE.md`.
Files: `g6_screen1_2026-11-20/`. G6-HM5 and G6-HM6 stay reserved as in the plan.

**The user's request (verbatim, 2026-11-20, with a photo of the tablet in a PS2 game):** "We can easily increase the
screen presence. Select, start and end shift closer to the controller and a 4:3 picture would fit perfectly"

**Preflight (06:10Z, `preflight.txt`):** no game process; no gradle or Kotlin daemon; two other Claude Code session
processes idle (no children, last activity 2026-11-19 23:59Z or earlier); only this session active. Baseline
`daf72e10`. The last tablet session had ended at 06:05:14Z.

## 0. Two notes for the record (read only, from the raw logs)

**0.1 The green-screen hiccup, 2026-11-20 ≈ 04:20Z.** Observed; the cause of the leave is not known (the user was not
asked).
- **The leave** (`logs/games/native_stream_recovery.log`): `surface_lost` at 04:20:35.437Z with `reason`
  `user_leave`, `away_ms` 12109 against `bound_ms` 12000, `outcome` `restarted`. The tablet left the stream activity
  (Android's "user leave": a Home or recents gesture) for 12.1 s, just past the surface hold, so the hub restarted the
  stream.
- **The heartbeats** (`native_stream_heartbeat.log`): the last at 04:20:18.232Z (sequence 67); the next session's
  first at 04:20:35.433Z with `rendered_frames` 0.
- **The hub's stall recovery while the tablet was away** (`logs/games/20261119-231800-ps2.log`): five save / pause /
  load cycles, 04:20:20.058Z to 04:20:32.433Z (slot 9, every PINE save and load `ok`). The `ps2_states` picture checks
  that followed: three `static` (04:20:31.8, 04:20:31.9, 04:20:35.9Z) and two `ok` (04:20:33.2, 04:20:36.1Z).
  The fast restart: `session_ended` 04:20:34.7Z, `session_started` 04:20:35.9Z.
- **The hub held up** (`native_frame_sizes.jsonl`, `host_resource_samples.jsonl`): 60 frames in every second while
  the tablet was away (04:20:18–04:20:33Z), 44 and 43 in the two seconds of the restart (04:20:34, 04:20:35Z);
  load 2.0–2.5 and GPU edge 35–41 °C in 04:19–04:21Z, GPU ≤ 47 °C over the whole session.
- **Read beside Cowork's note:** the picture verdicts were not all `static` (two `ok`), and the 60 fps dipped in the
  restart's two seconds; otherwise as Cowork read it.

**0.2 The tablet now reaches the hub over Tailscale from the user's home Wi-Fi** (the user, 2026-11-20: "I downloaded
tailscale and am running from my home wifi").
- The hub classes these sessions `remote-direct` (`remote_config` from 05:48:24Z), the remote ladder in force:
  start at the floor rung, cap 7000 kbps.
- **The 05:49:24Z → 05:57:36Z session** ran 8 min 12 s:
  - no `client_stall` and no `link_notice_shown` (hub and heartbeats: `link_notice` 0 throughout);
  - 7 lost video packets, 0 resyncs, `fec_unrecoverable_groups` 0 (decoder report `native_decoder_20261120_055737_065.json`);
  - 59.98 fps rendered (heartbeats, 05:49:20–05:57:36Z);
  - −64 … −73 dBm, 5 GHz.
- **Beside it, as context:** the client sent one stall signal and its end (`stall_signal_stalls_sent` 1, 150 ms
  bound; the hub logged no `client_stall`); worst output gap 190 ms; `recent_fps` 58.95 at the end. Four shorter
  sessions followed, 05:58–06:05Z, all `remote-direct`.
- **One session; not yet a finding. G6-WIFI1 is held**, not run, not withdrawn (its task file unchanged).

No address, overlay address, network name or device name in either note.

## 1. The change (part 1)

### 1.1 The video box and the pad region

- `HandheldGeometry.videoBoxHeight(w)` = **w · 3 / 4** (1200 → 900). G6-HM3's 16:9 stays as `videoBoxHeight16x9(w)`.
- The box on a real screen is `videoBoxHeight(w, h)`: 4:3 when the region left under it keeps at least the PS2
  layout's reference shape (`REF_H / REF_W` of the width: 1100 for 1200), else G6-HM3's 16:9. **On the tablet it fits
  exactly:** 2000 − 900 = 1100. A taller-than-wide screen shorter than 1200 x 2000 (for example 1200 x 1920) keeps
  16:9 and is never cropped.
- `padRegionHeight(w, h)` = h − that box: 1100 on the tablet.
- The handheld report: `video_box` `1200x900`, `pad_region` `1200x1100`.

### 1.2 The crop (the client only; the hub unchanged)

**Which systems are cropped** (`g6_screen1_2026-11-20/crop_decision.txt`, every file named there):

| System | Cropped | Rests on |
|---|---|---|
| SNES | **yes** | snes9x (the `snes-core.conf` drop-in); `Snes9x.opt` `snes9x_aspect = "4:3"`; no per-game override; every snes9x launch log (69) reports aspect 1.3333 |
| N64 | **yes** | `n64_session.py` writes `mupen64plus-aspect` `4:3` at each launch; the core `.opt` the same; no per-game override; every N64 launch log (30) reports 1.3333 |
| PS1 | no | the core's "corrected" aspect with smart overscan crop is **1.219**, not 4:3, in all 825 PS1 launch logs (C5-M4: content 876 x 720 of the stream); widescreen hack off everywhere |
| PS2 | no | `PCSX2.ini` `AspectRatio = Auto 4:3/3:2`; B80's widescreen patch on for **4 titles** (`EnableWideScreenPatches = true`) |
| GameCube | no | Dolphin's aspect not set (`GFX.ini`): Auto follows each game's own 16:9 flag |
| Party, NES, Genesis | no | not proven (no 4:3 setting found; no NES or Genesis launch logged) |

- **How the client knows the system:** the hub's start reply already carries the launched game's catalog entry
  (`game_session.game.system`); the base activity passes it through hook **H10** (`onGameSystem`, a no-op by
  default). No hub field, no `MainActivity` change.
- **The way it crops:** the video surface is sized at 16:9 of the box's height, **1600 x 900, centred at x −200**, so
  the stream's side bars fall off the screen's left and right edges and the box shows exactly the stream's centre
  960 x 720. Not cropped: the surface is 1200 x 675 at the top of the box; the 225 px below are the black background.
- **The report:** `video_crop` `"4:3"` / `"none"`; `video_source_rect` `"160,0,960x720"` / `"0,0,1280x720"`.
- **Overlays:** they are children of the stream layer, which is the whole 1200 x 900 box, so they keep working inside
  it. **The paused picture** (End's copy, shown on the main screen) is cropped the same way through hook **H11**
  (`pausedFramePreview`, by default the expression it replaced): when cropped, the centre 4:3 of the surface, stored
  at 360 x 270 instead of 480 x 270.
- **Said plainly: the pre-registered run is a PS2 game, and PS2 is not cropped,** so its picture stays 1200 x 675 at
  the top of the box; on the PS2 only SELECT / START / End move. The bigger picture shows in SNES and N64 games.
  PS1's 1.219 would lose no picture to a 4:3 crop (about 42 stream px of black each side): Cowork's to decide.

### 1.3 The pad region (1200 x 1100; `Ps2TouchLayout.REF_H` 1100, so `sy` = 1 on the tablet)

- **The cluster does not move on the screen:** every y but SELECT / START / End is B2's minus 225 (D-pad and right
  stick 295, shoulders 549, R3 565, left stick 805, L3 815, the face buttons 715 / 805 / 895). x, radii, the 0.875
  throw, the press areas and every hit scale unchanged.
- **SELECT and START** at x 400 / 600, y 70 of the region: on the screen at y 970 (G6-HM4b: 745), 225 px nearer the
  controls.
- **End at x 1080** (from 960), y 70: the smallest whole x with ≥ 0.5 cm to the right stick's press area.
- The footer text, the status panel and the side-edge gesture exclusions (they follow the shoulders) are unchanged.

### 1.4 The geometry check (`layout_check_screen1.py`, output `layout_check_screen1_output.txt`; 94.49 px per cm)

| Check | Result |
|---|---|
| 1 the 13 cluster controls' on-screen centres vs G6-HM4b | largest move **0.00 px** — **OK** |
| 2 overlaps, drawn and press (240 pairs, End included) | none — **OK** |
| 3 End ↔ nearest press area (the right stick) | **47.58 px = 0.504 cm** (≥ 0.5 cm) — **OK**; at x 1079 it would be 47.07 px = 0.498 cm. End ↔ START 3.32 cm, ↔ R1 3.40 cm. End spans x 1004.5–1155.5 |
| 4 SELECT ↔ D-pad (reported) | drawn **54.18 px = 0.573 cm**; press **12.01 px = 0.127 cm** |
| 4 START ↔ right stick (reported) | drawn **170.69 px = 1.807 cm**; press **110.06 px = 1.165 cm** |
| 5 SELECT / START / End drawn | 151 x 95 px, smaller side **1.01 cm** each — **OK** |

As before: every press area inside the region and above its bottom tenth; the shoulders ≥ 1 cm above it.

## 2. Tests and build (`tests_jvm.txt`, `build_console.txt`)

- `gradlew --offline :app:testDebugUnitTest :app:assembleDebug`: **BUILD SUCCESSFUL. 365 tests, 0 failures, 0
  errors, 0 skipped** (06:21Z; G6-HM4b had 358).
- **New, `G6Screen1Test` (7):** the 4:3 box and the 16:9 fallback; `REF_H` 1100 and the cluster's on-screen centres
  equal to G6-HM4b's; SELECT / START at y 70 (970 on the screen); End at 1080 and the smallest such x; the crop per
  system (SNES and N64 only; PS2, PS1, GameCube, party, NES, Genesis, empty, unknown and none not); the source
  rectangle and the surface's place; no press-area overlap.
- **Updated to the new geometry, as the task asks:** `G6TouchPs2Test` (the region 1100, B2's y − 225, End's
  rectangle, the scaling test) and `G6TouchPadStateTest`'s video-box test (now 900 / 1100, with G6-HM3's 16:9 values
  pinned on `videoBoxHeight16x9`). Every other test unchanged and passing.
- **One fix before the green run:** the first build failed 4 tests because the region's minimum was computed in
  float (1200 × 1100/1200 = 1100.00004, rounded up to 1101), so the tablet fell back to 16:9. It is now whole-pixel
  integer arithmetic.
- **The candidate:** `PrivyHub/app/build/g6_screen1_candidate/app-debug.apk`, sha256
  `e4263fd9a5f6d644bf3e7919f856d01ab733dbbf7f61e168049b54395d21cb49` (also `PrivyHub-handheld-preview-e4263fd9.apk`).
  The previous `build/outputs` APK (G6-HM4b's `965d4f19…`) was copied first to
  `PrivyHub/app/build/g6_screen1_preserved_outputs/`.

## 3. The onn is unchanged (`onn_unchanged_checks.txt`, by `onn_checks_screen1.py`)

1. The manifest's `NativeStreamActivity` element is byte for byte as before any G6 code (`4d36c0bb…`); the manifest
   is not touched.
2. `NativeStreamActivity.kt`: 17 lines added, 5 removed. The removed lines are the paused copy's
   `Bitmap.createScaledBitmap(source, 480, 270, true)`, now H11's default; the rest is H10 (no-op, one call after H5),
   H11 and the read-only accessor `streamSurface` (H8's kind). **Hook defaults today's: 9 / 9** (H1–H7, H10, H11).
3. `PadSlots.kt` and `PointerGuard.kt` unchanged since `f52ce75b`.
4. `MainActivity.kt` not touched; its G6 statement is still inside `useHandheldGameScreen()`.
5. `companion/` and `tools/` untouched. The onn keeps `ca53df0d…`; the pins are not moved.

The code files changed: `HandheldInput.kt`, `HandheldStreamActivity.kt`, `TouchPadState.kt`,
`NativeStreamActivity.kt` (hooks only), and the tests. `git diff --check` is clean; `git apply -R --check
g6_screen1.diff` is OK. The redactor is clean on the Kotlin files and the records.

## 4. The run, pre-registered (`preregistration.md`)

- sha256 **`eddc7ddc8ba20926257535d5d723dc8f1ad67997c8f4c702fac8ac5445776a81`**, hashed at **2026-11-20T06:25:50Z**.
- G6-HM4b's copied exactly, changing only:
  - the candidate's hash;
  - the conditions: Tailscale from the home Wi-Fi, the session's class as context;
  - two added cells:
    - c9: `video_box` `1200x900`, `pad_region` `1200x1100`;
    - c10: for the PS2 session `video_crop` `"none"`, `video_source_rect` `"0,0,1280x720"`, with the reason fixed
      before the run;
  - two added remarks: the bigger picture; End pressed by mistake.

## 5. Part 2 — the run (after it)

**Not run; superseded by G6-SCREEN1b** (`G6_SCREEN1B_PS2_PS1_FILL_2026-11-20.md`), on the user's decisions of
2026-11-20 (PS2's widescreen patch off for handheld launches; PS1 stretched). No verdict. The pre-registration stays
as hashed (`eddc7ddc…`).
