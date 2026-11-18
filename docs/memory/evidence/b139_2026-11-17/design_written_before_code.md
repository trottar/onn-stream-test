# B139 — design, written before any code (hashed: `design.sha256`, the time in `design_hashed_at.txt`)

Queue: `handoffs/QUEUE_2026-11-17AW.md` §B139. Behind `PRIVYHUB_PARTY=1` (with `PRIVYHUB_H7=1`: the mini-game layer
exists only then); either flag absent → today byte for byte; **the users' own launches (the onn's, Extras' cheat
launches) byte for byte today with the flags set too.**

## What the settle showed (B61's form, made-up fixtures, disclosed; `scripts/osd_probe.py`, 24 runs: the N64 fixture and
the PS1 core's OpenBIOS × full screen and 960 × 720 × six configs; results in this folder)

| setting (written into the per-session config) | the content banner (at the launch) | "Paused." | the notices (cheat applied, state saved / loaded) |
| --- | --- | --- | --- |
| today (none) | there (433k bar pixels, full screen) | there (783 text px) | there |
| `menu_show_load_content_animation = "false"` | **gone** | there | there |
| `menu_enable_widgets = "false"` | gone | gone | **there** (the old font) |
| `notification_show_*` (autoconfig, cheats applied, patch, remap, override, initial disk) `= "false"` | there | there | there |
| **`video_font_enable = "false"`** | **gone** | **gone** | **gone** |

`video_font_enable = "false"`: **0 marks in every state** (running from 0.3 s, paused, after a paused load, after an
advance, running again), both cores, both shapes; `GET_STATUS` answered in every run; RetroArch's load line in the
session log; the cheat log lines as today (3); the command port answered. No `input_*` key is touched (the hotkeys the
hub uses: `input_enable_hotkey_btn` 6 with 4 / 5 / 7 / 9, unchanged). **No text is left: no mask is kept.**

**Why the mask made T88 worse on the hub** (offline, `scripts/t88_mask_check.py`, H7-D2 pass P's 74 pictures): it did
not, on those pictures — unmasked, the paused begin (13-66) reads `other` 0.086-0.091 because the label's text in the
right bar stops the bar cut (31 clean columns); **masked, label blacked or label removed: `start` 54 / 54 at 0.0036,
the right bar cut at 300** (a fresh reader and one kept across them alike). The boot frame before the begin reads 0.17-0.27
masked — the family of pass Q's and H7-V6's 0.12-0.17: those masked reads were taken in the first 15 s after the launch,
before the begin was on the window and while the launch's notices filled the left bar (begin + notices: 0.078 / 0.079
either way); pass Q's own pictures were not kept, so the exact 0.12 is not reproduced.

## The design

- **Only a launch made by `party-minigame-start` carries the settings.** The party layer, inside its launch's one
  manager call (the manager's lock held: no other launch can come between), sets
  `emulator._party_session_settings = PARTY_SESSION_SETTINGS` and clears it in `finally`; the plain launch
  (`emu.launch`) and the cheat launch (the plugin's own launch route with the onn's Extras query) alike reach
  `_prepare_retroarch_session_config`, which — **only when that attribute is set** — removes any assignment of those keys
  from the text and appends one block:
  `# PrivyHub B139 party mini game: RetroArch's on-screen text off` / `video_font_enable = "false"` /
  `menu_show_load_content_animation = "false"` (the banner by its own key too, so it stays off should a later
  RetroArch draw it apart from the notices). The attribute is a class default `None`: every other launch writes the
  config exactly as today.
- **The watch reads unmasked** (the party passes `mask_label=False`; B137's mask code stays in `h7_minigame`, unused).
- **Expected `prepare_s`** (from the preparation's start to `ready`; the launch before it ~1 s): with no notices the
  start is read at the watch's first read, 1 s after its load — **T88 ~1.3-1.6 s, T89 ~1.3-2.5 s** (B140's steps add
  0.3-2 s if T89 needs 14-30 frames); start → ready ~2.5 / ~3.5 s (was ~12 s for T88). **`RECOGNISE_SETUP_S` (15.0)
  stays** — it bounds only a start never read; no number says shorter.

## Tests (the real HTTP server; B101's fake RetroArch reading its session config at each launch)

A party launch's session config carries the two keys (once each), a users' launch of the same game in the same
companion does not — plain and with a cheat setup, before and after the party's, with the flags set; the flags absent
→ today (the config byte for byte against HEAD's code: the users' launch); the fake draws notices only when the config
leaves them on, and B137's cases then read the start with no mask; offline, H7-D2's T88 paused pictures with the label's
pixels removed as the settings would remove them → `start` (counts, least margin), `other` read as the screen 0 on
every kept run; B137 / B133 / B134 and the earlier suites green.
