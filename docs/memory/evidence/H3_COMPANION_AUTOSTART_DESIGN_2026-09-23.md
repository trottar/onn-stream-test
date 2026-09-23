---
memory_schema: 1
as_of: 2026-09-23
status: H3 — DESIGN RECORDED, not installed. Route A, a systemd user unit on default.target with an explicit DISPLAY=:0, a bounded wait for X, KillSignal=SIGINT; install and undo are user steps below
---

# H3 — the companion starts itself after a power cycle (design)

Task: `handoffs/H3_COMPANION_AUTOSTART_TASK.md`, third in
`handoffs/OVERNIGHT_2026-09-23B_QUEUE.md`. **Nothing was installed or
enabled**: no file under `~/.config/systemd/`, `~/.config/autostart/` or
`/etc`, no `systemctl enable/start`, no linger, no reboot. Evidence:
`h3_2026-09-23/` (SHA-256 in `h3_sha256.txt`): `h3_session_facts.txt`
(redacted, `h2_prep_redact.py --check` 0 residual), the unit
`privyhub-companion.service`, `h3_verify.sh`, `h3_verify_preinstall.txt`.

## Facts first (`h3_session_facts.txt`)

1. **The user manager has the session's environment**:
   `systemctl --user show-environment` → `DISPLAY=:0`,
   `XAUTHORITY=/home/privyhub/.Xauthority`, `XDG_SESSION_TYPE=x11`,
   `XDG_SESSION_DESKTOP=xfce`, a session bus. (XFCE imports it at login.)
2. **`graphical-session.target` is `inactive (dead)`** — XFCE on this host
   never activates it; **`default.target` is active** and is the default.
   A unit wanted by `graphical-session.target` would never start.
3. `Linger=no`, `State=active`; the user manager is **running** after
   autologin (143 units loaded). No `~/.config/systemd/user/` exists. No
   crontab. Enabled user units are desktop plumbing (pulseaudio, keyring,
   gpg/ssh agents, IBus, portals) — **`pulseaudio.service` is a user
   unit**.
4. The companion (`companion/privyhub_service.py`): paths from `__file__`
   (working directory irrelevant; subprocesses get `cwd=PROJECT_ROOT`);
   foreground `serve_forever()`; binds **`0.0.0.0:8765`** (all addresses —
   tolerant of the link coming up later); **only `KeyboardInterrupt`
   (SIGINT) runs its `finally`** — `shutdown_plugins()`, which stops a
   game through the validated POST-stop lifecycle (SAVE_FILES, RetroArch
   closed). **No SIGTERM handler**: SIGTERM ends it at once, the `finally`
   never runs, a live game is orphaned. Stdout is **block-buffered** when
   redirected — the two companions stopped by SIGTERM on 2026-09-22 left
   0-byte logs.
5. `~/.config/autostart/`: `claude-desktop.desktop` (the H1 route),
   `expressvpn-client` (Hidden), two XFCE plugins.
6. The capture window is looked up **per stream start** (`xdotool search
   --onlyvisible --pid`, 2 s deadline), so a companion started before any
   RetroArch is fine.

## The choice — route A, a systemd user unit

From the facts: the user manager is up after autologin and already holds
`DISPLAY=:0` (item 1), but `graphical-session.target` never fires (item 2),
so the unit is **`WantedBy=default.target`** with **`DISPLAY=:0` set
explicitly** (not relying on the import having happened yet at boot) and an
**`ExecStartPre` that waits up to 60 s for `xrandr --current` on `:0`**.
Route A gives restart on failure, the journal, and `systemctl --user
start|stop|restart|status` from SSH. Two settings follow directly from
item 4: **`KillSignal=SIGINT`** (so `stop`/`restart` run the companion's
clean shutdown instead of orphaning a game) and **`python3 -u` /
`PYTHONUNBUFFERED=1`** (so the journal gets lines as they happen).

**Linger stays `no`**: with autologin the user manager comes up at every
boot's login, which is all the unit needs; linger matters only if the
session ever logs out, and nothing here does.

**Recorded alternative — route B, XFCE autostart**
(`~/.config/autostart/privyhub-companion.desktop`, `Exec=sh -c 'cd
~/Projects/onn-stream-test && exec python3 -u ./companion/privyhub_service.py
>> logs/companion_autostart.log 2>&1'`): inherits the real session
environment with no target question, but no restart on failure, no
journal, stop only by `kill` — and `kill` is SIGTERM, which orphans a game
(item 4). Not chosen.

## The unit (`h3_2026-09-23/privyhub-companion.service`)

```ini
[Unit]
Description=PrivyHub companion (control API :8765, native game stream)
After=pulseaudio.service

[Service]
Type=simple
WorkingDirectory=%h/Projects/onn-stream-test
Environment=DISPLAY=:0
Environment=PYTHONUNBUFFERED=1
ExecStartPre=/bin/sh -c 'i=0; while [ "$i" -lt 60 ]; do xrandr --current >/dev/null 2>&1 && exit 0; i=$((i+1)); sleep 1; done; echo "X on :0 did not answer within 60 s" >&2; exit 1'
ExecStart=/usr/bin/python3 -u ./companion/privyhub_service.py
KillSignal=SIGINT
KillMode=mixed
TimeoutStopSec=20
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

(The file carries short comments for each choice.) `systemd-analyze
--user verify` on it: clean. No `PRIVYHUB_*` variable is set, so the
adopted profile and the default heartbeat are what run.

## Install — user steps, from an SSH shell on the host

1. **End any game and stop the hand-started companion** (two companions
   cannot share 8765):
   ```bash
   cd ~/Projects/onn-stream-test
   curl -s -X POST localhost:8765/plugins/games/stop >/dev/null; sleep 4
   COMP=$(ps -eo pid,comm,args --no-headers | awk '$2=="python3" && /privyhub_service\.py/ {print $1}'); [ -n "$COMP" ] && kill -INT $COMP
   sleep 5; ss -lnt | grep ':8765 ' || echo "8765 free"
   ```
   Expect: `8765 free`.
2. **Install and start the unit:**
   ```bash
   mkdir -p ~/.config/systemd/user
   cp docs/memory/evidence/h3_2026-09-23/privyhub-companion.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now privyhub-companion.service
   ```
   Expect: `Created symlink …/default.target.wants/privyhub-companion.service …`.
3. **Check it:**
   `systemctl --user status privyhub-companion.service --no-pager | head -5`
   — expect `active (running)` and a `python3 -u ./companion/privyhub_service.py`
   line; then `./docs/memory/evidence/h3_2026-09-23/h3_verify.sh` — expect
   `enabled: enabled`, `active: active`, exactly one companion pid with
   `DISPLAY=:0` and no `PRIVYHUB_*` line, the 8765 listener owned by that
   pid, `ready True … any_override False`.
4. **Prove the reason it exists:** `sudo reboot`; after it, SSH in and run
   `h3_verify.sh` again — the same readings with no hand start, `NRestarts=0`.
   Then `adb connect <onn-address>:5555` if the onn needs it (H2).

**Undo:**
```bash
systemctl --user disable --now privyhub-companion.service
rm ~/.config/systemd/user/privyhub-companion.service
systemctl --user daemon-reload
```
then start the companion by hand as `TOOLS.md` describes.

**Once installed, change three habits:** restart the companion with
`systemctl --user restart privyhub-companion` (D-068), not `kill` + `nohup`
— a hand start collides on 8765; a harness that sets a diagnostic variable
(e.g. `P8`'s `PRIVYHUB_HEARTBEAT_MS`) must `systemctl --user stop` the unit
first and `start` it after; and a plain `kill` (SIGTERM) of the unit's
process counts as a clean exit for `Restart=on-failure`, so it will **not**
come back — use `systemctl`.

## Verification script

`h3_2026-09-23/h3_verify.sh` — unit enabled/active/MainPID/NRestarts, the
companion pid(s) and their `DISPLAY`/`PRIVYHUB_*`, the 8765 listener,
`native-stream-status` (`ready`, `any_override`), the unit's last journal
lines, tmux; every dotted quad replaced. The pre-install run
(`h3_verify_preinstall.txt`) reads `enabled: not-found`, `active:
inactive`, one hand-started companion (pid 160925, `DISPLAY=:0`), `ready
True`, `any_override False` — the baseline the post-install run is read
against.

## Classification

**DESIGN RECORDED — not installed.** Installing is the user's decision
and a user-side write.
