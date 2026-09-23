---
memory_schema: 1
as_of: 2026-09-22
status: COWORK HANDOFF — context for a new Cowork chat taking over the PrivyHub baseline-stream-health work from the 2026-09-20..22 chat; read with docs/memory/CURRENT.md and handoffs/CURRENT_HANDOFF.md
---

# Cowork handoff, 2026-09-22 (afternoon)

## How this work runs

- The repo is `/home/privyhub/Projects/onn-stream-test` on the Linux host (user `privyhub`), reached from Cowork only through the file bridge (list / stage / commit files). There is no host shell in Cowork. Claude Code runs **on the host** in tmux (`claude --remote-control`), and it is the thing that changes code and runs sessions.
- The loop: Cowork writes a task handoff into `docs/memory/handoffs/<NAME>_TASK.md`; the user sends Claude Code a one-line prompt (`Run docs/memory/handoffs/<NAME>_TASK.md`) — that prompt is the user's authorization; the user reports "Code is done"; Cowork then **verifies from the raw artifacts** (stage the record, the `evidence/<item>_<date>/` directory, `p*_sha256.txt`; check hashes; recompute the headline numbers from the jsonl/json files) before saying anything is true, and appends corrections to the record if the session over-claimed.
- Handoff style that has worked: read-first list; one narrow question; pre-registered readings before the run; classification rule (RUNTIME VALIDATED / CHARACTERIZED / INDETERMINATE / DEVELOPMENT-ONLY); record raw numbers first; the memory files to update (CURRENT.md fixed headings, `python3 tools/check_memory_health.py` healthy, MEMORY.md, CURRENT_HANDOFF.md, ACTIVE.md, KNOWN_ISSUES.md, TOOLS.md, dated file); teardown per TOOLS.md; "never retry a failing action more than twice".
- Overnight queues are one `OVERNIGHT_<date>_QUEUE.md` listing task files in order with gates.

## Non-negotiables

- Never ask the user for, and never write anywhere, IP addresses, MACs, BSSIDs, SSIDs, ADB endpoints, serials, credentials or device identifiers. Placeholders only (`<host-address>`). Topology by role only (host, Opal, onn, PC).
- The Opal (GL-SFT1200, Dropbear) is reached as `ssh opal` from the host, **read-only**: `iw`, `iwinfo`, `uci show`, `/proc`, `/sys`, `logread`. Never `uci set/commit`, `wifi`, `reboot`, `opkg`. Its password is never stored.
- ROM/ISO/BIOS/keys and `logs/` stay out of git and out of support bundles.
- The Claude Code classifier refuses `nft` writes even with allow rules — fault injection is run by the user by hand (`evidence/d_base_r3b_2026-09-21/r3b_run.sh`).
- Nothing perceptual is an acceptance gate; the user's own look at the picture is recorded as user-stated, never as instrument evidence.
- No memory in Cowork about this project beyond what `docs/memory/` holds; the repo's memory is the bridge between chats.

## Where things stand (verified)

- **Loss mechanism found and fixed.** Video loss on the production path (host wired to the Opal, onn on the Opal's 5 GHz) was the encoder's frame-size tail: scene-change frames of 80-207 packets burst-overflowed a queue on the wireless hop. `P6` proved it by intervention (cap at 90,000 bytes → 100 % of ≥80-packet frames gone, loss 7-9× lower, bitrate/CPU unchanged); `P6a` adopted `max_frame_size_bytes = 90000` into the C1 profile (`any_override: false` is the default now; `PRIVYHUB_ENC_MAX_FRAME_SIZE=0` runs uncapped for comparison); `S3` soaked it 3 h at 5.4 losses/min, residual tracks nothing. The user looked at it and called it good. Records: `D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md`, `D_BASE_P6A_CAP_ADOPTED_2026-09-22.md`, `D_BASE_S3_CAP_SOAK_2026-09-22.md`.
- **`prolonged_starvation_events` named** (`P7`): one event per audio arrival hole > ~15 ms; the hole is ~55-60 ms once every ~2 s; jitter not loss; origin unknown. `P8` (queued) tests whether the 2 s heartbeat or the adb sampler causes it.
- **Link-drop recovery** (`R3`/`R3a`, constants DESYNC 1 s, RECOVERY_CLEAN_TICKS 3, GIVE_UP 120 s, END 30 min): `R3b` N3/N15/N150 by hand all PASS 2026-09-22; N05/N15b/E30 not run, so R3+R3a are not yet RUNTIME VALIDATED. Two post-run defects, one cause (`R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`): `native-stream-stop` pauses but keeps the session, and `recovery-resume` loaded a state into that live core, producing a 3-4-frame loop. **User decision 2026-09-22:** recovery never loads into a live core; tile = Resume when a session is live; prompt only when none is; resume-from-recovery ends stale session, launches fresh, loads, then deletes the recovery file. Handoff `D-BASE-R3C_TASK.md` (probe first, fix gated on it). The N150 `.state.recovery` for Tekken 3 is still in the states directory on purpose.
- **Host console and boot** (`H1_VERIFY_SSH_CONSOLE_2026-09-22.md`): sshd key-only, root off; LightDM autologin (`/etc/lightdm/lightdm.conf.d/10-autologin.conf`); the login keyring given a blank password so no unlock dialog blocks a headless boot; Claude desktop copied into `~/.config/autostart/`; X answers with only `DISPLAY=:0`; the companion is still started by hand (`python3 ./companion/privyhub_service.py` from the repo) and nothing starts it at boot; `Linger=no`. adb to the onn is wireless only; the user pinned it to port 5555 (`adb tcpip 5555`) — a TV power cycle can undo that.
- **Headless cutover `H2`** (`handoffs/D-BASE-H2_TASK.md`, rewritten from `H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`): DisplayPort dummy plug (4K@17 / 2K@30 / 1080p@60), connector X `DisplayPort-0` = DRM `card0-DP-1`, required mode 1920x1080@60, the one allowed write `/etc/X11/xorg.conf.d/10-monitor.conf` only if the plug prefers 4K@17; two reboots; the console is SSH from the user's PC on the Opal wifi. Gate: the user says the plug is in and the monitor is off.
- **Checkpoint**: committed this morning; a second commit + push before H2 was recommended (`CHECKPOINT_PROPOSAL_2026-09-22.md` describes the tree; `.claude/` and `_prel2b/` were untracked-and-unignored, user's call).

## Queue

1. `H2` — when the plug is in (user-run swap, then `The dummy plug is installed and the monitor is off. Run docs/memory/handoffs/D-BASE-H2_TASK.md`). Verify from `evidence/h2_<date>/` and the inventory diff.
2. Tonight: `Run docs/memory/handoffs/OVERNIGHT_2026-09-23_QUEUE.md` (R3c, then P8).
3. Later, user-run: E30 (`./r3b_run.sh E30 output 48100,48101 150 60 25 1`, wait 30 min, then `sudo -n nft delete table inet privyhub_fault`), N05, N15b — to close R3+R3a. Companion autostart at boot (systemd user unit with `DISPLAY=:0`, or linger) is not designed yet. Thermal thresholds deferred. `END_MS`, `host_link`, Group C, C6 remain on the roadmap list.

## Reading order for the new chat

`docs/memory/CURRENT.md` → `handoffs/CURRENT_HANDOFF.md` → this file → the records named above as needed. `docs/memory/TOOLS.md` for how sessions are driven. Trust the newest record over any summary, including this one.
