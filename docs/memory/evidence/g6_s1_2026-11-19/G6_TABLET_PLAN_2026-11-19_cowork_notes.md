# G6 — the Galaxy Tab S6 Lite (SM-P610) as the handheld client (Cowork notes, 2026-11-19, not in git)

Kept in `Claude outputs/` (gitignored) on purpose: nothing here shows in `git status`, so no running or later session's
"tree clean" / "files before = after" check is touched. It moves into `docs/memory/` only when no session is running
and the user says so.

## Where it belongs

`docs/ROADMAP.md` §G6 "Portable handheld validation" (DEFERRED — explicitly pending at the G9 checkpoint: no
representative handheld). The tablet is that hardware. The user's handoff steps T1–T6 are recorded here as
**G6-S1 … G6-S6**, because `T1` / `T2` / `T3` are D-BASE findings and `T88` / `T89` are game codes. Cells are named
`G6-S1.c1 …`, never bare `C<n>` (Phase C items and the global C58/C59-style cells).

| User's step | Id | What |
|---|---|---|
| T1 | G6-S1 | the CONFIRMED APK unchanged: install, launch, catalog, touch, connect, one stream |
| T2 | G6-S2 | tablet interface fixes (launcher, touch, scaling, orientation, navigation) |
| T3 | G6-S3 | 720p60 hardware decode, continuity, audio, UDP, latency with the existing diagnostics |
| T4 | G6-S4 | controller on the tablet (mappings, slots, latency) |
| T5 | G6-S5 | battery at 50 % brightness; reversible optimizations only after the baseline |
| T6 | G6-S6 | physical handheld (grips / telescopic pad); no purchase before software is validated |

Target from the plan: about four hours of streaming from 100 % to 20 %. Firefox video today: ~10 % per 30 min at 50 %.

## Conflict audit (2026-11-19 ~03:30Z)

- **Prompt files are per session** (`COMMUNICATION.md`): `_cowork_prompt.txt` = session A, `_b` = B, `_c` = C;
  `archive/prompts/_cowork_prompt_offsite.txt` retired. Cowork wrote over A's file by mistake and restored it byte
  for byte (2996 bytes). G6 gets **no** prompt file until it actually needs a Code session; then a new name
  (`_cowork_prompt_g6.txt`), never A's.
- **Session A's slot is spoken for:** queue BB (session B, running at the time) builds `ADD_GAME_TASK.md` /
  `ADD_GAME_PROMPT_TEMPLATE.txt` for session A, whose precondition is `git status --short` empty but for the prompt
  files. Any G6 file in the tracked tree would stop it.
- **The hub's tools call bare `adb`** (`e1_suite.py`, `c3_l4_nft_night.py`, no `-s`). A second adb device on the
  hub (the tablet over USB or wireless debugging) makes every one of them fail with "more than one device", including
  the nightly. **The tablet is never connected to the hub's adb.** G6-S1 installs by sideloading the APK file.
- **One companion, one stream.** The tablet's catalog reads are light HTTP like the onn's; a tablet **game stream**
  waits until no Code session is running, the onn is not streaming, and it is outside 04:30-05:30Z (and the 45 min
  before). G6 has secondary priority to every other chat and session.
- **The onn's pads stay paired to the onn.** No pad pairs to the tablet before G6-S4.
- Ids: `G6-*` unused anywhere in the repo docs (only the §G6 heading).

## G6-S1 — the hand route (no Code, no hub change)

- APK: `PrivyHub/app/build/home12v_installed/app-debug.apk`, sha256
  `ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d` (CONFIRMED, HOME-12V), sent to the user in chat.
- Fresh install opens on "Set companion host" (`MainActivity.loadCatalog`, `getCompanionHost()` blank): the user
  types the hub's address in the app's settings, as on the onn; it is never written down. Identity v2 stays off (the
  legacy LAN path); pairing is a later step on the user's word.
- The manifest's `android.software.leanback required="true"` is a store filter; whether the tablet's installer
  accepts it is G6-S1's first result.
- Evidence comes from the hub's always-on `privyhub-diag` and the companion's logs, read later by Cowork (read only)
  or by a G6 Code session when nothing else runs. No logcat in G6-S1 (that would need adb).

Results (user's words + hub reads):
- 2026-11-19, user: "Everything works so far" — the sideloaded APK installed (so the leanback `required` did not block it), launched, connected to the companion, catalog shown, touch works; a movie (VOD) played. Over the home 5 GHz network, not the Opal's.
- The Opal's 5 GHz network does not appear in the tablet's Wi-Fi list (home 5 GHz does). The Opal's recorded radio: channel 36 (`auto` over 36/40/44/48/149/153/157/161, no DFS), country US, 40 or 80 MHz — all channels the tablet supports, so a hidden network name or range is the likelier cause. Being checked by hand; the Opal stays the user's. Later the same night it appeared in the list (cause not known; nothing was changed).
- The game stream (T88, two tries, 03:52Z and 04:09Z): **refused by the hub, no fix needed in code.** The companion took both launches on the legacy LAN path (`session_audit.jsonl`: `legacy_setup` for launch and native-stream-start), RetroArch started, but no `session_started`; the client's decoder report (`decoder_sessions/native_decoder_20261119_041013_681.json`) reads 0 video / 0 audio packets and `host_metadata_error`: "audio codec opus is required by this host (PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup". Adopted line 8 (G-A2) needs the client to declare opus, which only the identity-v2 session/setup does; the unpaired legacy path never does. The controller uplink reached the hub (6924 packets, no send errors), so the tablet ↔ hub path itself works.
- (Done below.) Planned: pair the tablet as a second device (RUNBOOK "Away — the first time" step 1: the hub opens the 2-min window, the tablet's "Pair with hub…" takes the code), then tick "Use paired identity (identity v2)" on the tablet. Changes the hub's paired-device store (one → two devices); reversible by unpairing (CL-B2 §3 did it). No hub check counts paired devices (`e3_state.py`, `e1_suite.py`, `c3_l4_nft_night.py` grepped).
- **Paired and streamed (2026-11-19, user: "it just ran fine").** Audit: `pairing_open` 04:26:05Z → `pairing_ok` `dev-c320…`; a `pairing_refused` (window closed) 04:27:08Z; a second window 04:27:15Z → `pairing_ok` `dev-954a…`; `token_issued` to `dev-954a…` with `audio_codecs: opus` 04:27:43Z. **The hub's store now holds three devices: the onn, the tablet (`dev-954a…`) and a stale first tablet pairing (`dev-c320…`)** — removing the stale one is a later hub change on the user's word.
- Session 10 (T88): launch 04:27:49Z, `session_started` 04:27:54Z, `session_end_bye` 04:28:18Z (~24 s PLAYING, not the 3-min hold). Decoder report `native_decoder_20261119_042818_218.json`: **`OMX.Exynos.avc.dec`, low latency on** (hardware AVC); 1641 frames in 27.5 s, recent 59.4 fps, 0 dropped, 0 lost packets, FEC 8+1 recovered 1, 0 unrecoverable; 7000 kbps, GOP 15; first clean IDR 370 ms, first video out 401 ms; rx→decode 23 ms latest / 55 ms max; Opus 2670 packets, 0 lost, 0 underruns (14 concealed). One link notice `rssi_weak` (5180 MHz, −73 dBm, tx 65 Mb/s). No onn session ran in that window (recovery log sessions 8-10 are all the tablet's).
- **G6-S1: met** — install, launch, catalog, touch, connect (paired), a T88 stream on hardware decode. The 3-min hold, battery and fuller 720p60 numbers move to G6-S3 / G6-S5.

## Portrait handheld mode (read-only investigation, 2026-11-19)

The user's brief: `G6_PORTRAIT_INVESTIGATION_HANDOFF_2026-11-19.md` (inputs/). The full report is the user's own Claude doc (its link is kept out of the public repo). Its result, in short:

- **Feasible with no change to the companion, the decoder or the PHI1 packet.** A touch pad writes the existing pad state (XUSB bits, stick shorts, trigger bytes) through one new sender method; the video view is given a 1200x675 box at the top of the 1200x2000 portrait screen, leaving 1200x1325 for controls (no 50/50 split).
- **Blockers found (verified):** the stream activity is landscape-locked in the manifest and in `onCreate`; no `configChanges`, so a rotation rebuilds it and ends the session; B70 `PointerGuard` consumes every touchscreen event in a game (`SOURCE_TOUCHSCREEN` carries the pointer class bit); the overlays use fixed landscape margins.
- **Architecture (proposed):** a handheld subclass of the stream activity with its own manifest entry (today's entry byte for byte); `TouchPadState` (pure, JVM-tested) + `TouchPadView`; a `TouchPadDevice : PadDevice`; a touchscreen-only pointer-guard exemption in the subclass; a Settings choice in `MainActivity`. In-house view: the two mature on-screen pads (RadialGamePad, Moonlight's controls) are GPL-3.0.
- **Decisions (the user, 2026-11-19):** D2 — the touch pad becomes P1 by default when no real pad has joined as P1 (the existing long-press join) within **5 s** of the game starting; a later pad takes the next player. D3 — **PS1 layout first**. D4 — tablet landscape **keeps today's full-screen fill** (about 6.7 % stretched, inferred), no letterbox. D1 — partly settled by D2; open: portrait as a Settings choice or following the rotation.
- **Open:** whether a later pad should take over P1; what the lower region shows when a real pad is P1; D1's rest.
- **Stages (proposed, none started):** G6-HM1 design hashed before code; G6-HM2 bench logic + JVM tests; G6-HM3 portrait video with an inert pad (+ the onn confirmation sitting before any APK replaces `ca53df0d…`); G6-HM4 digital PS1 controls live; G6-HM5 sticks, L3/R3, latency video; G6-HM6 live rotation, customization, battery/heat comparison (feeds G6-S5).
