# Current Handoff

Authoritative state: `../CURRENT.md`. **Start there.**

## READ FIRST

**The 90 KB frame cap is ADOPTED and in force.**
`max_frame_size_bytes = 90,000` is a declared field of
`native_game_720p60_reference` (Linux `h264_vaapi`), running with
**nothing set in the environment**. The user checked the picture first —
"could barely tell it was over the LAN", **their words, not instrument
evidence**. **Loss runs 5.4-12.4/min against an uncapped 110-145**, zero
≥80-packet frames, bitrate/fps/CPU unchanged, holding over three hours.

**Three things before touching the encoder.** **`any_override: false`
means "only the profile decided"**, not "no cap" — an uncapped run is
`any_override: true` with `uncapped: true`.
**`PRIVYHUB_ENC_MAX_FRAME_SIZE=0` runs uncapped**, flag absent, which
re-runs the `P6` baseline without editing source. And **60 KB and VBV are
measured alternatives, not rejected ones** — reopen on a picture
complaint, not on more loss measurement.

The path is **host wired -> Opal -> onn wireless, one hop** (`B2`).

**`D-BASE-R3b` RAN 2026-09-22, by hand** — the classifier still refuses
every `nft` write, so the user drove
`../evidence/d_base_r3b_2026-09-21/r3b_run.sh`. **N3, N15 and N150 all
PASS**; N15 caught an encoder restart **succeeding while the fault was still
dropping every packet**, and N150's give-up landed at **120.42 s** with the
`.state.recovery` file written. **`R3d` (hand runs, 2026-09-22): N15b
PASS, E30 PASS → `END_MS` RUNTIME VALIDATED; N05 PASS on 2026-09-23 →
`R3` + `R3a` RUNTIME VALIDATED for real loss**
(`../evidence/D_BASE_R3D_HAND_RUNS_2026-09-22.md`).
Record: `../evidence/D_BASE_R3B_NFTABLES_LINK_DROP_2026-09-22.md`.

**Read the loss numbers with the restart caveat.** A 3 s outage with no
restart counted **2 348** lost packets; 15 s and 150 s outages that restarted
counted **22** and **40** — a new SSRC makes the return an `ssrc_change`, not
loss. **`max_output_gap_ms` is the honest column for outages.**

**Two post-run defects are open**
(`../evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`): a stream-stop leaves
the game session live, so the launcher resolves to `recovery-resume` and
reports "Loaded" with no window; and after a recovery-state load the source
picture cycles through about four frames. The Tekken 3 `.state.recovery` is
**kept on purpose** as their evidence.

## 2026-09-23 — `H3`: companion autostart DESIGNED, not installed

`../evidence/H3_COMPANION_AUTOSTART_DESIGN_2026-09-23.md`: a systemd user
unit on `default.target`, `DISPLAY=:0`, wait for X, `KillSignal=SIGINT`,
`Restart=on-failure`; paste-ready install/undo steps and `h3_verify.sh`.
**The companion's clean shutdown runs only on SIGINT** — stop it with
`kill -INT`, not `kill`. Also tonight: **N05 PASS → `R3`+`R3a` RUNTIME
VALIDATED for real loss** (`../evidence/D_BASE_R3D_HAND_RUNS_2026-09-22.md`).

## 2026-09-23 — `D-BASE-R3c2`: recovery flow RUNTIME VALIDATED

`../evidence/D_BASE_R3C2_RECOVERY_FLOW_2026-09-23.md`. Tile = **Resume** for
a live session (same pid, no load); the recovery prompt only with no live
session; resume-from-recovery = launch fresh → unpause → load into the
**running** core → pause → delete the recovery files. The N150 mid-FMV
save now plays; a gameplay save plays at 60 fps. Both R3b post-run defects
closed. APK `21e3d089…9dcb`.

## 2026-09-22 — `H2`: the host is headless — RUNTIME VALIDATED

`../evidence/H2_HEADLESS_CUTOVER_2026-09-22.md` (built on `H2-PREP`'s
inventory; `H1` gave SSH + autologin). **No write made.**

**The plug is not where the task said.** X **`DisplayPort-1`** = DRM
**`card0-DP-2`**; the monitor's `DisplayPort-0` now reads disconnected.
The plug prefers **1920x1080 @ 60.00 Hz** by EDID (4K@17 is listed, not
chosen). Any future `xorg.conf.d` / `video=` fix must name the plug's
port — `DisplayPort-1` / `DP-2`.

**Capture is unchanged headless**: `capture_target` the 879x720 window;
fps 59.68 and spikes 50.0/min inside `B2`; max gap 93 ms (below `B2`);
x11grab PTS delta 1 on all 1,799, 0 repeats in motion. adb after a host
reboot: **`adb connect <onn-address>:5555`** (the pin held).

**Check 5 PASS** (user-run after a second plug-only reboot): autologin
desktop, 1080p60, adb back on the pinned port, companion started by the
script with `DISPLAY=:0`, `S2` in bounds (fps 59.69, spikes 46.34/min,
max gap 184 ms). **Nothing starts the companion at boot** — start it by
hand. Run Claude Code **inside tmux**. **The R3b recovery prompt covers
RESUME PLAYING** until `R3c`; `h2_session.sh` dismisses it with BACK only
when it is up (no action, file untouched).

**`M1` corrected one thing the handoffs had wrong.** The synthetic UDP
burst/gap/**duplication** pathology is **not Windows-only**:
`investigations/DEFERRED.md` records it reproducing from a Linux sender,
bidirectionally, while idle. It has never been replayed on the post-`B2`
topology. **PAUSED**, and **a different fault** from the in-session loss
the cap fixed. `KNOWN_ISSUES.md` carries two entries.

**Nothing is committed.** `.claude/` and `_prel2b/` are untracked and
**unignored** — the user's call first.

## Earlier handoff sections

`P7`, `S3`, `P6a` (09-22) and `P6`/`P5`/`O1` (09-21) moved verbatim to
`../history/HANDOFF_SECTIONS_THROUGH_2026-09-22.md`; their evidence
records are authoritative.

## 2026-09-20 and before

`../2026-09-20.md` is the chronology; conclusions in `../MEMORY.md`. Two
facts hard to find again: **`R4`**'s `diagnostic_retention.py` policy
SHA-256 `b13fbc32…71b5`, which an `--apply` run must quote, and
**`R3`+`R3a`**'s recovery save, which goes to `<stem>.state.recovery`,
**never a slot**. **`P2`**: 98.7 % of underruns fall in the first 3 s —
read the per-session total, never a rate. **`P1`**: the stale default is
60. **`B2` has run; `B1`/`B3` have not.**
