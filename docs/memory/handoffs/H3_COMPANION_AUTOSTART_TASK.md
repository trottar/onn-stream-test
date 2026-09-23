---
memory_schema: 1
as_of: 2026-09-22
status: TASK HANDOFF — H3, design the companion's start-at-boot on the headless host from measured session facts; writes only under docs/memory/ and evidence/; nothing installed, nothing enabled, no reboot
---

# H3 — the companion starts itself after a power cycle (design only)

**Why.** `H2` is RUNTIME VALIDATED with one standing caveat: nothing starts
the companion at boot (`Linger=no`, no unit, no crontab), so an unattended
power cycle leaves the onn with no server until someone runs
`python3 ./companion/privyhub_service.py` by hand with `DISPLAY=:0`
(`evidence/H2_HEADLESS_CUTOVER_2026-09-22.md`, `TOOLS.md` §console).
This task produces the one file that fixes that and the exact commands the
user runs to install it — **it does not install it**. Starting a network
service at boot is the user's decision and a user-side write.

Read first: `TOOLS.md` (console, companion start, teardown),
`evidence/H1_VERIFY_SSH_CONSOLE_2026-09-22.md` §3-4 (what the companion
needs from its environment: `DISPLAY=:0` and nothing else — X grants
`SI:localuser:privyhub`), `evidence/H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md`
§4 (what starts at boot and after login today), `companion/privyhub_service.py`
(entry point, working-directory assumptions, log paths, how it exits),
`companion/native_stream.py` (`_linux_display`).

## Part 1 — measure what the running session offers (read-only)

From the autologin desktop session (SSH shell, `DISPLAY=:0`), record:

1. `systemctl --user show-environment | grep -E '^(DISPLAY|XAUTHORITY|XDG_SESSION|DBUS_SESSION)'` — whether XFCE imported `DISPLAY` into the user manager.
2. `systemctl --user list-units --type=target --all | grep -E 'graphical-session|default'` and `systemctl --user is-active graphical-session.target` — whether the session activates it (decides `After=`/`WantedBy=`).
3. `loginctl show-user privyhub -p Linger -p State`; `systemctl --user status` header (is the user manager up at all after autologin).
4. The companion's own needs: its working directory (relative paths it opens), where it logs, whether it daemonises or stays in the foreground, its exit code on SIGTERM, and whether it tolerates the network coming up after it (the Opal link is wired; note if it binds 0.0.0.0 or a specific address — record as "specific address" only).
5. `~/.config/autostart/` contents (the XFCE route already in use for the Claude desktop).
6. Whether a companion started before RetroArch exists still finds the window later (it does today — the window is found per launch — confirm from `_select_capture_target`).

Write the raw output to `evidence/h3_<date>/h3_session_facts.txt`, redacted
with `evidence/h2_prep_2026-09-22/h2_prep_redact.py`, `--check` clean.

## Part 2 — choose and write the unit, from the facts

Two routes; pick from Part 1, state why, and write the other as the
recorded alternative:

- **A. systemd user unit** `~/.config/systemd/user/privyhub-companion.service`:
  `Environment=DISPLAY=:0`, `WorkingDirectory=%h/Projects/onn-stream-test`,
  `ExecStart=/usr/bin/python3 ./companion/privyhub_service.py`,
  `Restart=on-failure`, `RestartSec=5`, `KillMode=mixed`, `TimeoutStopSec=20`;
  `After=`/`WantedBy=` **exactly what Part 1 item 2 showed is active**
  (`graphical-session.target` if XFCE activates it, else `default.target`
  with an `ExecStartPre` that waits for `xrandr --current` to answer on
  `:0`, bounded at 60 s). Logs go to the journal (`journalctl --user -u
  privyhub-companion`). Gives restart-on-failure and stop/start from SSH.
- **B. XFCE autostart** `~/.config/autostart/privyhub-companion.desktop`
  running the same command: inherits the real session environment, no
  target guesswork, no restart on failure, no log unless redirected.

Also state, from Part 1 item 3, whether `loginctl enable-linger` is
needed at all (with autologin the user manager comes up at login; linger
matters only if the session ever logs out) — recommend leaving `Linger=no`
unless a fact says otherwise.

Write the chosen file's full text into the record and into
`evidence/h3_<date>/privyhub-companion.service` (or `.desktop`), plus
`evidence/h3_<date>/h3_verify.sh`: after a reboot, from a fresh SSH shell,
prints the unit state, the companion pid and its `DISPLAY`, the 8765
listener, `native-stream-status` `ready`/`any_override`, and whether tmux
is up — the same shape as `h2_check5.sh`, redacted the same way.

## What this task does NOT do

No file under `~/.config/systemd/`, `~/.config/autostart/` or `/etc`;
no `systemctl enable`/`start`; no `loginctl enable-linger`; no reboot.
The **user-side install block** (create the file, `daemon-reload`,
`enable --now`, then `h3_verify.sh`; and the undo: `disable --now` and
delete the file) goes in the record as numbered paste-ready steps, with
what the user should see after each one.

## Record and memory

`evidence/H3_COMPANION_AUTOSTART_DESIGN_<date>.md` — facts first, then
the choice, the unit text, the install/undo steps, the verify script;
SHA-256s under `evidence/h3_<date>/`. Classify **DESIGN RECORDED — not
installed**. `CURRENT.md` (fixed headings, `python3
tools/check_memory_health.py` healthy — trim), `MEMORY.md` (one line:
autostart designed, route chosen, not installed), `handoffs/
CURRENT_HANDOFF.md`, `TOOLS.md` (a pointer to the install steps; the
"start it by hand" line stays true until the user installs), `KNOWN_ISSUES.md`
(the open item narrowed to "designed, awaiting user install"), the dated
memory file. Never retry a failing action more than twice. No addresses,
MACs, SSIDs, serials or device identifiers in any memory or evidence file.
Nothing committed to git.
