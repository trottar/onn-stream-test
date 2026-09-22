---
memory_schema: 1
as_of: 2026-09-22
status: TASK HANDOFF — H2, headless cutover verification once the DisplayPort dummy plug is installed; gate is the user's word; measurement and documentation, plus at most one named write; rewritten 2026-09-22 from the H2-PREP inventory
---

# H2 task handoff — the host goes headless

**Gate.** Run only when the user has said the DisplayPort dummy plug is
installed and the monitor is disconnected. If `xrandr` still lists the
real monitor (**`DisplayPort-0` at 1440x900, `subconnector: VGA`**), stop
and say so.

Read first: `evidence/H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md` (the
inventory this task is built on — every name and path below came from it),
`handoffs/PLAN_WEEK_2026-09-21.md`, `TOOLS.md`,
`companion/native_stream.py` (`_select_capture_target`,
`_find_retroarch_window`, `_linux_display`),
`evidence/GROUP_A_DIAGNOSTIC_AUDIT_2026-09-20.md` (A3: capture is 60 fps
clean with a real monitor — the reference).

**Why.** The game capture is `x11grab` of the managed RetroArch window on
the X display. Without a monitor the GPU may drop the output, the session
may not start or may come up at a different resolution or refresh rate,
and the stream would fail in a way that looks like a capture fault. The
plug makes the GPU see a fixed monitor; this task proves the capture path
is the same as with the real monitor, across a reboot.

---

## Before you unplug the monitor — check this list first

**`H2` is unrecoverable without these.** H2-PREP found all four missing or
absent as of 2026-09-22. Any one of them still missing is a **stop**, not
a workaround.

1. **`H1` is done: SSH reachable from the PC.** `openssh-server` was **not
   installed** at inventory time — `/usr/sbin/sshd` absent, no unit file,
   nothing on 22. Verify from the PC, on the Opal wifi, *before* the
   monitor comes off: `ssh <user>@<host> "echo key-login-ok"`. Without
   this there is no console once the screen is gone.
2. **Autologin is configured.** Every `autologin-*` line in
   `/etc/lightdm/lightdm.conf` is commented out, so a reboot stops at the
   LightDM greeter: no X session, no RetroArch window, and check 5 cannot
   pass. This is a **root write the user makes**, not this task —
   `/etc/lightdm/lightdm.conf.d/10-autologin.conf` with
   `[Seat:*]` / `autologin-user=privyhub` /
   `autologin-session=xfce` — and it must be verified by a reboot **with
   the monitor still attached** so the greeter is visible if it goes
   wrong.
3. **tmux is alive and the companion command is known.**
   `loginctl show-user privyhub -p Linger` reads **`Linger=no`**: user
   processes are killed at logout. Start the console session from SSH per
   `PLAN_WEEK` and keep it. Companion, per `TOOLS.md`, from the project
   directory: `python3 ./companion/privyhub_service.py` — and it must
   inherit **`DISPLAY=:0`**, because `_linux_display()` reads `DISPLAY`
   from the environment and nowhere else. A bare SSH shell does not have
   it; export it.
4. **The plug's expected modes are known.** It advertises 4K at 17 Hz, 2K
   at 30 Hz and 1080p at 60 Hz. Nothing starts at boot today — no
   `privyhub`/`companion`/`retroarch` unit, empty crontab, `Linger=no` —
   so an unattended power cycle leaves **nothing** running. Expect to
   start the companion by hand after every reboot in this task.

## The connector, in both spellings

| | |
| --- | --- |
| X / `xrandr` | **`DisplayPort-0`** |
| DRM / `/sys/class/drm` | **`card0-DP-1`** |

They are **off by one** on this host: X `DisplayPort-N` is DRM
`DP-(N+1)`. `DisplayPort-1`/`DisplayPort-2` (DRM `DP-2`/`DP-3`) are the
two unused connectors. Use the X spelling for `xrandr` and for an
`xorg.conf.d` Monitor section; use the DRM spelling only for a kernel
`video=` parameter.

**The plug goes on the same connector the monitor uses today.** The
monitor is reached through an **active DP→VGA adapter**
(`subconnector: VGA`); the plug is a native DP sink with its own EDID, so
re-read `xrandr` after the swap rather than assuming continuity.

## The mode, and the one write this task may make

**The required mode is 1920x1080 at 60 Hz.** A display server that picks
the largest advertised mode would run the desktop at 3840x2160 at
**17 Hz**, and the capture — and every timing number this project
measures — would follow it.

Select it live:

```bash
xrandr --output DisplayPort-0 --mode 1920x1080 --rate 60
```

**Persist it only if the plug does not already prefer it.** The plug
carries its own EDID; if `xrandr` shows `1920x1080 … 60.00*+` after the
swap, **write nothing** and record that. If it prefers 4K@17 Hz, the one
write this task is authorized to make is
**`/etc/X11/xorg.conf.d/10-monitor.conf`**, which does not exist today
(`/etc/X11/xorg.conf.d/` is empty and there is no `/etc/X11/xorg.conf`):

```
Section "Monitor"
    Identifier  "DisplayPort-0"
    Option      "PreferredMode" "1920x1080"
EndSection
```

A `Monitor` section whose `Identifier` matches an **output name** is bound
to that output by RandR 1.2, which is why the X spelling goes here. This
host runs the **`xf86-video-amdgpu` DDX** (selected by
`/usr/share/X11/xorg.conf.d/10-amdgpu.conf`) with **no competing Monitor,
Screen or Device section anywhere**, so this is the route the stack is set
up for. **Verify it rather than trusting it**: `sudo systemctl restart
lightdm`, then `xrandr` — no reboot needed. If the mode does not take,
the fallback is the kernel parameter **`video=DP-1:1920x1080@60e`** in
`GRUB_CMDLINE_LINUX_DEFAULT` + `update-grub` + reboot (DRM spelling,
heavier, edits `/etc/default/grub`) — **record it as the smallest fix and
do not apply it without the user's word.**

Two things that will *not* need fixing, already confirmed: blanking is off
(`xset q` reports `DPMS is Disabled`, screensaver `timeout: 0`,
`xfce4-power-manager` DPMS timers 0), and there is **no saved desktop
display profile** to override an X config — XFCE's `displays.xml` holds
only `ActiveProfile=Default` with no per-output geometry, and
`~/.config/monitors.xml` does not exist. **Do not open the XFCE Display
dialog during this task**: saving a profile from it would start
overriding the mode at login.

One thing to watch: **`light-locker` is running** from
`/etc/xdg/autostart/`. It locks on suspend and on session switch. A lock
screen over the RetroArch window would change what `x11grab` sees.

---

## Checks, in order, each recorded

1. **Before reboot, plug in:** `xrandr --verbose` (outputs, connected
   state, current mode and rate, preferred mode, the full mode list), the
   EDID **vendor/model string only** — **no serial** — and which output
   the desktop session is on. Confirm `DisplayPort-0` / `card0-DP-1` is
   the occupied one. If the mode is not 1920x1080@60, apply the `xrandr`
   line above and then the persistence decision.
2. **Reboot the host** (this task may do it; the user is present). After
   reboot: a desktop session is up on `:0` — **not the greeter** — at
   **1920x1080 at 60 Hz, not 4K/17 Hz**; the companion starts per
   `TOOLS.md` with `DISPLAY=:0` in its environment; `tmux` and Claude Code
   come back from the SSH console per `PLAN_WEEK`. Record `adb devices`
   and, if the device is not attached, **the exact reconnect command
   used** — `TOOLS.md` documents none, so this is a gap to fill rather
   than a lookup.
3. **One attract-mode session of the PS1 reference title, 120 s**, per
   `TOOLS.md`, BACK to end. The report's `capture_description`, source
   width/height and encoder fps must match the last monitor-attached
   session (`D-BASE-B2`'s reports); rendered fps, spike rate and
   `max_output_gap_ms` within B2's range; both thermal readings present
   (`D-BASE-T1`). Confirm from `native-stream-status` that the adopted
   profile is still in force: `max_frame_size_bytes: 90000`,
   `max_frame_size_source: profile`, `any_override: false`.
   **Expect `capture_target` to be a window of roughly 879x720**, not the
   screen — see below.
4. **A 30 s `x11grab -> framemd5` of the managed window**, the A3-live
   method, counting duplicate hashes and PTS deltas — must read as A3 did
   (PTS delta exactly 1, duplicates in the low single digits).
5. **Confirm the session survives a second reboot with nothing attached
   but the plug** (same checks as 2), so an unattended power cycle does
   not strand the server. **This check depends entirely on autologin**
   (pre-flight item 2). Without it the greeter is what comes back and the
   right answer is to record that and stop, not to work around it.

**Read the capture path correctly.** The source is a **`-window_id`, not
the screen**: `_select_capture_target()` calls
`xdotool search --onlyvisible --pid <managed RetroArch pid>` for up to 2 s
and **fails closed**, raising *"No visible window owned by the
project-managed RetroArch session was found. Whole-desktop capture is
intentionally disabled."* rather than falling back to the desktop.
`--onlyvisible` means **X-mapped, not physically displayed**, so it is
expected to keep working headless. If that message appears, it means
**there is no window** — no session, or an iconified one — **not a capture
fault**. The desktop resolution is not the capture resolution: the last
monitor-attached session captured an **879x720** window and scaled/padded
it to 1280x720, on a desktop of 1440x900. 1920x1080 buys headroom, not
fidelity.

**A note on the comparison.** The monitor attached until now maxes out at
**1440x900** — `1920x1080` is in neither its `xrandr` list nor
`/sys/class/drm/card0-DP-1/modes`. So checks 3 and 4 compare a 1080p
headless desktop against reference sessions taken on a 1440x900 desktop.
Since the capture follows the window and not the screen, that should not
move the numbers — **and if it does, that is itself the finding.**

## Record

Raw numbers first in `evidence/H2_HEADLESS_CUTOVER_<date>.md`, with the
report and framemd5 summary under `evidence/h2_<date>/` and SHA-256s.
Re-run `evidence/h2_prep_2026-09-22/h2_prep_inventory.sh` with the plug in
and **diff it against `h2_prep_raw.txt`** — that diff is the cleanest
statement of what the cutover changed. Redact with
`h2_prep_redact.py` and run its `--check` mode before anything is copied
into a memory file.

Classify **RUNTIME VALIDATED** if 2-5 all pass; otherwise name the failing
check and the smallest fix (the `xorg.conf.d` mode line, the kernel
`video=` parameter, autologin, or a different plug resolution) **without
applying it**.

Update `TOOLS.md` (the host is headless behind a dummy plug at the
recorded resolution; the console is SSH from the PC on the Opal wifi; the
adb reconnect command; how to bring the desktop back if the plug is
removed), `CURRENT.md` (fixed headings,
`python3 tools/check_memory_health.py` healthy), `MEMORY.md` (durable:
headless host, capture verified without a monitor),
`handoffs/CURRENT_HANDOFF.md`, the dated memory file, `KNOWN_ISSUES.md` if
anything failed. Teardown per `TOOLS.md`. Never retry a failing action
more than twice. **No addresses, MACs, SSIDs, serials or device
identifiers in any memory or evidence file.**
