---
memory_schema: 1
as_of: 2026-11-18
status: BUILT (session B, queue AW) — a party mini game's title launched with RetroArch's on-screen text off, behind PRIVYHUB_PARTY=1 (and PRIVYHUB_H7=1). Settled first (B61's form, made-up fixtures, 24 runs: both cores, full screen and 960 x 720, six configs): video_font_enable = "false" in the session config leaves nothing of RetroArch's on the window — no notices, no "Paused.", no content banner — paused and running; GET_STATUS, the command port, the load line and the cheat log lines as before; menu_show_load_content_animation = "false" removes the banner alone; menu_enable_widgets = "false" leaves the notices in the old font; the notification_show_* keys leave all three. No text is left: no mask. Why the mask made T88 worse: on H7-D2's own pictures it did not (masked 54 / 54 start at 0.0036, unmasked other 0.086-0.091) — the hub's masked reads were taken before the begin was on the window. Built: only a launch made by party-minigame-start writes the two keys; the users' launches byte for byte today with the flags set; the watch reads unmasked. Expected prepare_s T88 ~1.3-1.6 s, T89 ~1.3-2.5 s; RECOGNISE_SETUP_S stays. Tests 5 (one offline, on the hub's own pictures) x3; mutations 2 / 2. Nothing adopted; nothing committed
---

# B139 — a party mini game's title launched with RetroArch's on-screen text off

Queue: `handoffs/QUEUE_2026-11-17AW.md` §B139. T88 = H7's two-player PS1 title; T89 = the users' four-player N64 title.
The directory is `b139_2026-11-17/`: the design + `.sha256` (hashed 00:30:18Z, before any code; the settle ran
before it), `scripts/` (`osd_probe.py` + `run_matrix.sh`, B137's fixtures, `t88_mask_check.py`, `change_measure.py`,
`run_all.sh`), `settle/` (the 24 runs' numbers), `t88_mask_check_result.json`, `b139.diff`, the runs, the checks,
`manifest.sha256`. Patch: `patches/B139_PARTY_CLEAN_WINDOW.md`. No title, id, `profile_id`, character or cheat name or
path; no picture, crop or reference image in git (the probes' grabs stayed in a scratch folder, removed). **Disclosed
probes (B61's form):** the hub's RetroArch AppImage with its N64 core on B137's made-up ROM and its PS1 core on the
made-up PS-EXE (OpenBIOS's own animation runs; no BIOS file exists or was used), temp folders, read-only copies of the
hub's two core option files, a made-up cheat file for the fixture (one code writing an unused word), the joypad driver
null (it falls back to udev; the hub has no joypad device); 25 runs of ~15 s on the hub's display (00:20Z-00:29Z), full
screen and 960 × 720. **Offline, read only:** T88's / T89's specs, H7-D2's kept pictures and the other kept T88 runs.

## Settled first — which settings leave nothing of RetroArch's on the window (`settle/`)

Each run: running from 0.3 s (the launch's banner and notices), paused, a state saved and loaded paused, an advance,
running again. Marks: full screen — bright pixels in the pillarbox bars (the cores draw nothing there); 960 × 720 —
pixels off their area's tone in the top-right, bottom-left and middle (the N64 fixture is flat colours).

| setting in the session config | content banner (launch) | "Paused." | notices ("Applying cheat changes.", "Saved / Loaded state …") |
| --- | --- | --- | --- |
| today (none of them) | **there**: 433,172 bar px at 0.3 s (full), the middle 11,236 (960 × 720) | **there**: 783 text px | **there**: 2,479 bar px after a load |
| `menu_show_load_content_animation = "false"` | **gone** | there | there |
| `menu_enable_widgets = "false"` | gone | gone | **there**, drawn by the old font (1,741-2,775 px) |
| `notification_show_{autoconfig, cheats_applied, patch_applied, remap_load, config_override_load, set_initial_disk} = "false"` | there | there | there |
| **`video_font_enable = "false"`** | **gone** | **gone** | **gone** |

**`video_font_enable = "false"`: 0 marks in every state, both cores, both shapes** (the PS1 960 × 720 runs: identical to
the run with both settings, the top-right box at the animation's own 2,320 where today's paused window had 3,094).
Every run: `GET_STATUS` answered (PLAYING / PAUSED as sent), `SAVE_STATE_SLOT` / `LOAD_STATE_SLOT` acknowledged,
RetroArch's load line in the session log, the cheat log lines as today (3). No `input_*` key is touched — the hotkeys
the hub uses (`input_enable_hotkey_btn` 6 with 4 / 5 / 7 / 9) unchanged. **No text is left; no mask is kept.**

## Why the mask made T88 worse — offline (`scripts/t88_mask_check.py`, H7-D2 pass P's 74 pictures)

| T88's pictures | unmasked | B137's mask as applied | the label's pixels blacked | the label removed (the bar's tone) |
| --- | --- | --- | --- | --- |
| boot frame, no begin yet (1-12) | other 0.224-0.280 | other 0.172-0.270 | 0.172-0.270 | 0.172-0.270 |
| **paused begin, 2-210 frames (13-47)** | **other 0.086-0.091; the right bar's cut stops at 31 columns** | **start 35 / 35, 0.0036; cut 300** | start 35 / 35 | start 35 / 35 |
| all paused (13-66) | start 6 / 54 | start 54 / 54 | 54 / 54 | 54 / 54 |
| running (67-74) | start 8 / 8 | 8 / 8 | 8 / 8 | 8 / 8 |

The same with one reader kept across the pictures, as a watch does. **In one line: the mask did not make T88 worse —
on these pictures it reads the start (0.0036) where the label alone keeps it out (0.089); the hub's masked reads (pass Q
0.17 → 0.12, H7-V6 0.164) sit with the boot frame's masked values (0.17-0.27): they were taken before the begin was on the
window (and while the launch's notices filled the left bar — begin + notices: 0.078 unmasked / 0.079 masked).** Pass Q's
own pictures were not kept, so its 0.12 is not reproduced exactly.

## Built (`b139.diff`: `companion/games/emulator_manager.py`, `companion/party_minigame.py`)

- **Only a launch made by `party-minigame-start` carries the settings.** The layer sets
  `emulator._party_session_settings = PARTY_SESSION_SETTINGS` inside its launch's one manager call (the lock held: no
  other launch between) and clears it in `finally`; the plain launch and the cheat launch (the plugin's own route with
  the onn's Extras query) both reach `_prepare_retroarch_session_config`, which — **only when it is set** — removes any
  assignment of the keys and appends `# PrivyHub B139 party mini game: RetroArch's on-screen text off` /
  **`video_font_enable = "false"`** / **`menu_show_load_content_animation = "false"`** (the banner by its own key too, so
  it stays off should a later RetroArch draw it apart from the notices). The class default `None`: **every other launch
  writes its config exactly as today, with the flags set or not.**
- **The watch reads unmasked** (`PARTY_LABEL_MASK = False`; B137's mask stays in `h7_minigame`, unused).
- **Expected `prepare_s`** (the preparation's start → `ready`; the launch ~1 s before it): with no text the start is
  read at the watch's first read, 1 s after its load — **T88 ~1.3-1.6 s; T89 ~1.3-2.5 s** (B140's steps); start →
  ready ~2.5 / ~3.5 s (H7-V5b / B133 expected ~12 s for T88, mostly RetroArch's notices). **`RECOGNISE_SETUP_S` (15.0)
  stays:** it bounds only a start never read.

## Tests (`tests/b139_party_clean_window/`, 5; B114's scenario — B101's fake RetroArch reads the session config it is started with)

| test | shown |
| --- | --- |
| party launches only (`nopress`) | **every party launch's config: the two keys once each (`["false"]`); the users' own launch of the same game in the same companion afterwards: neither**; the fake drew no "Paused.", the `watching` row has no `label_mask`, the start read, the match scored |
| under a cheat setup (B127's `cheat` mode) | the party's launches under T88's / T89's setups carry them; **the onn's Extras launches of both titles (the users') do not** |
| today | **the users' launch's session config byte for byte HEAD's** (`c1a66bc9`; normalised for the temp root and the per-launch port) — the flags absent, `PRIVYHUB_PARTY` alone, both set — and the same text inside a companion that has just run party mini games |
| offline, the hub's own pictures (run against the repo; elsewhere skipped) | **T88's paused pictures with the label's pixels removed as the settings remove them: start 54 / 54, least margin 0.1851; the boot frame 0 / 12 as the screen; 7 kept T88 runs, `other` read as the screen 0** |

B137's test 2 (the label masked on every paused read) now reads B139's rule (no label drawn, no mask). **Mutations**
(`tests_mutations.txt`): the settings emptied → 2 fail; the config writer ignoring them → 2 fail. **Runs:** `tests_x3.txt`,
`tests_others.txt` (in `b139_2026-11-17/`, shared by B139-B141).
