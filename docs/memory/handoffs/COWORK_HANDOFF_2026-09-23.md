---
memory_schema: 1
as_of: 2026-09-23
status: COWORK HANDOFF — context for a new Cowork chat taking over from the 2026-09-22/23 chat; read with docs/memory/CURRENT.md and handoffs/CURRENT_HANDOFF.md; supersedes COWORK_HANDOFF_2026-09-22.md
---

# Cowork handoff, 2026-09-23 (evening)

## How this work runs (unchanged, plus what was learned)

- Repo `/home/privyhub/Projects/onn-stream-test` on the Linux host, reached from Cowork through the file bridge only (list / stage / commit). Claude Code runs on the host in tmux; it changes code and runs sessions. The loop: Cowork writes `docs/memory/handoffs/<NAME>_TASK.md`; the user sends Claude Code one line — **the user cannot paste into Claude Code from the PC** (Claude Code reads the *host's* clipboard, no xclip), so Cowork writes the prompt into `_cowork_prompt.txt` at the repo root (untracked) and the user types `Read _cowork_prompt.txt in the repo root and follow it as my prompt.`; the user says "Code is done"; Cowork **verifies from the raw artifacts** (stage the record, the evidence directory, the SHA-256 manifest; `sha256sum -c`; recompute the headline numbers from the jsonl/json) and **appends corrections** to the record where it over- or under-claimed.
- **The file bridge can deliver a stale copy** when the same output path is rewritten: write each new prompt/task to a **new** local file name before committing, then re-stage the host file and read it back before telling the user it is ready.
- The user is often on a phone: numbered steps, one paste-ready block each, where they are (host SSH shell / PC PowerShell / TV), what they should see. Nothing pasted from the phone; outputs go to a file under `logs/` and Cowork reads it.
- Pre-registered rules must be written against the **noise the counters actually show**, not a single pair: `P9` failed 12/17 on "underruns rise" (20 → 25) when 3/8 sessions run 4-20; `P9a` failed on "holes within 20 % of each A arm" when the A arms differed by 28 %; `P10` failed on "FEC recoveries in the A range" when B was *better*. Each time the user was asked and adopted; each time the rule was Cowork's. Compare against a measured band, on the direction that matters.
- Two overlapping runs on one host disturb each other (the user's aborted E30 vs `P8`): never hand the user a fault-injection command while a queue is running.

## Non-negotiables (unchanged)

No addresses, MACs, BSSIDs, SSIDs, ADB endpoints, serials, credentials anywhere — placeholders only; `<onn-address>` in a command is for the **user** to substitute, say so. The Opal is read-only over `ssh opal`. ROMs/ISO/BIOS/keys/logs/savestates out of git (savestates under `evidence/` are now `.gitignore`d; hashes are in the records). The 90 KB cap is adopted; encoder flags unchanged. Nothing perceptual is a gate; the user's own listen/look is recorded in their words. Claude Code cannot run `nft`; fault injection is the user's by hand. The companion is a **systemd user unit** now: `systemctl --user restart privyhub-companion`, never `kill` + `nohup` (SIGTERM orphans a game; the unit uses SIGINT).

## Where things stand (all verified from artifacts)

- **Host**: headless behind a DP dummy plug on X `DisplayPort-1` = DRM `card0-DP-2` at 1080p60 by EDID (`H2`, RUNTIME VALIDATED across two boots); SSH key-only; LightDM autologin; companion autostarts under systemd with `DISPLAY=:0`, `KillSignal=SIGINT` (`H3`, installed by the user, verified across a reboot); adb after a host reboot: `adb connect <onn-address>:5555` (pinned port).
- **Link-drop recovery**: `R3`+`R3a` RUNTIME VALIDATED for real loss (N05/N3/N15/N15b/N150 by hand), `END_MS` validated (E30: `ENDED` 1,801.4 s after `PAUSED_SAVED`). `R3c2`: recovery never loads into a live core; resume-from-recovery launches fresh, unpauses, loads into the **running** core, pauses for handoff (a mid-FMV save loops if loaded paused — `R3c`); tile = Resume when live, prompt only when none; all seven checks pass. The only copy of the N150 save: `evidence/d_base_r3c_2026-09-22/recovery_copy/`.
- **Audio**: holes (~55-60 ms, ~100/min) are the path's, not the heartbeat or sampler (`P8`); cushion **12/17** adopted (starvation −98 %, +34-38 ms, `P9a`/`T2`); the warm-state loss steps up ~7 min from cold at onn ≈ 67 °C and resets with ≥ 30 min idle (`T2`), is lost **between** the host's NIC and the onn's IP stack — 0 send errors, 0 socket/stack drops (`T3`) — and is single packets (98-99 % one-packet gaps), so **audio redundancy 2 copies / 4-tick offset** is adopted: −96/−98 % warm, +1.6 Mbps, no latency (`P10`). Cowork's correction to `T3`: video is lost there too but its 8+1 FEC recovers it (FEC recoveries step with audio loss, rho +0.5-0.8).
- **Thresholds** (`T2`/`T3`): proposals only (onn cpu-thermal ≈ 67.5 °C as a status flag), none enforced; with redundancy the symptom is covered regardless.
- **Profile** `native_game_720p60_reference` now declares: `max_frame_size_bytes` 90000, `audio_queue_target/capacity_packets` 12/17, `audio_redundancy_copies/offset_packets` 2/4 — all `source: profile`, `any_override: false`.
- **Uncommitted since the 2026-09-23 checkpoint**: P9, P9a, T2, T3, P10 (companion + client changes, APK `f31b1c18…8ae7`, five records, `.gitignore` savestate rules already committed). Commit before anything else.

## Queue

1. **User**: listen with redundancy on (their words → the `P10` record); commit and push (block in the chat of 2026-09-23).
2. `Run docs/memory/handoffs/D-BASE-CLOSE_TASK.md` — score the target table cold + warm on the finished build, verdict MET / NOT MET, hand the roadmap back to Phase C (C1's explicit schema is effectively done). Needs ≥ 40 min idle first. Verify from `evidence/d_base_closeout_<date>/`.
3. Then the roadmap: Phase C from where `docs/ROADMAP.md` puts it after C1; `host_link` with `T3`'s fact; `B1`/`B3`; Group C; C6.

## Reading order for the new chat

`docs/memory/CURRENT.md` → `handoffs/CURRENT_HANDOFF.md` → this file → the records named above as needed (`TOOLS.md` for how sessions are driven and the systemd companion). Newest record beats any summary, including this one.
