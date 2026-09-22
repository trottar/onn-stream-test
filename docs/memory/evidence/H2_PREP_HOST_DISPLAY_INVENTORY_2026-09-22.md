---
memory_schema: 1
as_of: 2026-09-22
status: EVIDENCE — H2-PREP, read-only inventory of the host's display / session / boot path, taken with the monitor still attached; nothing on the host was changed
---

# H2-PREP — the display path, read before the monitor goes

Task: `handoffs/H2_PREP_TASK.md`. Queue: `handoffs/OVERNIGHT_2026-09-22_QUEUE.md`
item 3. Harness and redacted raw output under
`evidence/h2_prep_2026-09-22/`.

**Read-only, and it stayed read-only.** No `sudo`, no `xrandr --output`,
no file created or edited under `/etc`, no unit enabled, no reboot. Every
number below came from a command that reads.

---

## 0. The three findings that change `H2`

`H2` as written assumes the host can be rebooted with only the dummy plug
attached and come back streaming. **Today it cannot**, for three reasons
that have nothing to do with the plug:

1. **`openssh-server` is not installed.** Not disabled — absent.
   `/usr/sbin/sshd` does not exist, no `ssh`/`sshd` unit file exists, and
   nothing listens on 22. **`H1` has not been started.** Once the monitor
   is gone there is no console at all. This is the hard gate on `H2`.
2. **There is no autologin.** Every `autologin-*` line in
   `/etc/lightdm/lightdm.conf` is commented out. After a reboot LightDM
   stops at the greeter: **no X session, no RetroArch window, no capture**
   — `xdotool search --onlyvisible` would return nothing and
   `_select_capture_target` would raise *"No visible window owned by the
   project-managed RetroArch session was found."* `H2` check 5 (survive a
   power cycle with nothing but the plug) **cannot pass** until this is
   set.
3. **Nothing starts the companion at boot, and `Linger=no`.** No
   `privyhub`/`companion`/`retroarch` unit exists, the user crontab is
   empty, and user processes are killed at logout. An unattended power
   cycle leaves **nothing** running — that is the answer to item 4, not a
   gap in the search.

A fourth, smaller one: **the monitor attached today cannot do 1920x1080 at
all** (§2). `H2`'s "must be 1920x1080@60, not the plug's 4K/17 Hz" is
still right for the *plug*, but there is no before/after comparison to be
made at that resolution — the reference sessions were all captured with
the desktop at 1440x900.

---

## 1. Session type and display server

| | |
| --- | --- |
| `XDG_SESSION_TYPE` | **`x11`** |
| `DISPLAY` | `:0.0` |
| `WAYLAND_DISPLAY` | unset |
| session 2 | `Type=x11`, `Class=user`, `Service=lightdm`, `Desktop=lightdm-xsession`, `Active=yes` |
| display manager | **LightDM**, `enabled`, up since 2026-09-21 10:40 EDT |
| X server | `/usr/lib/xorg/Xorg :0 -seat seat0 -auth … -nolisten tcp vt7 -novtswitch`, **running as `root`** |
| desktop | **XFCE** — `xfce4-session` (pid owned by `privyhub`, parented to `lightdm --session-child`) |

**This is a real X11 session, not XWayland**, so `x11grab` attaches to the
X server directly and nothing about the capture changes headless. There is
no Wayland compositor on this host to fall back to.

**Autologin: none.** `grep -rniE '^[^#]*autologin' /etc/lightdm/` matches
nothing; `lightdm.conf` is the stock file with every section header empty.

## 2. Outputs and modes today

```
Monitors: 1
 0: +DisplayPort-0 1440/408x900/255+0+0  DisplayPort-0

DisplayPort-0 connected 1440x900+0+0   408mm x 255mm
   1440x900      59.89*+  74.98
   1280x1024     75.02    60.02
   1280x800      59.81
   1152x864      75.00
   1280x720      59.89
   1024x768      75.03    70.07    60.00
   …
DisplayPort-1 disconnected
DisplayPort-2 disconnected
```

| DRM | status |
| --- | --- |
| `card0-DP-1` | **connected, enabled** |
| `card0-DP-2` | disconnected |
| `card0-DP-3` | disconnected |

**The connector, in both spellings.** The monitor is on X's
**`DisplayPort-0`** = DRM's **`DP-1`**. The two namings are **off by one**
on this host: X `DisplayPort-N` is DRM `DP-(N+1)`. Both routes in §3 need
the right one and they are not interchangeable.

**Maximum mode 1440x900 at 59.89 Hz.** `1920x1080` appears in neither
`xrandr` nor `/sys/class/drm/card0-DP-1/modes`. The panel EDID reports
**vendor `DEL` (Dell), model `1909W`** (serial deliberately not recorded;
the EDID hex block is stripped by the redactor).

**One detail worth carrying:** `xrandr --verbose` reports
`subconnector: VGA` on `DisplayPort-0`. The monitor is reached through an
**active DP→VGA adapter**, not a native DP sink. The dummy plug will
attach to the same connector as a **native DP sink with its own EDID** —
a different kind of device on the same wire, which is a reason to re-read
`xrandr` after the swap rather than assume continuity.

## 3. GPU, kernel parameters and the two persistence routes

| | |
| --- | --- |
| GPU | AMD Renoir (Radeon Vega, integrated), `05:00.0`, `Kernel driver in use: amdgpu` |
| kernel | `6.12.107+deb13-amd64` |
| `/proc/cmdline` | `BOOT_IMAGE=… root=UUID=<redacted> ro quiet` — **no `video=` and no `amdgpu.` parameter** |
| X driver | `xf86-video-amdgpu` DDX, selected by `/usr/share/X11/xorg.conf.d/10-amdgpu.conf` (`OutputClass` → `Driver "amdgpu"`) |
| `/etc/X11/xorg.conf` | **does not exist** |
| `/etc/X11/xorg.conf.d/` | **empty** |
| Monitor/Screen/Device sections | **none anywhere** — `grep -rniE 'Section *"(Monitor\|Screen\|Device\|ServerLayout\|ServerFlags)"'` over `/etc/X11/` and `/usr/share/X11/xorg.conf.d/` matches nothing |

Xorg.0.log confirms the autoconfigured path:

```
(==) Using system config directory "/usr/share/X11/xorg.conf.d"
    loading driver: amdgpu
(II) AMDGPU(0): Output DisplayPort-0 has no monitor section
(II) AMDGPU(0): Output DisplayPort-0 using initial mode 1440x900 +0+0
```

**There is no `AllowEmptyInitialConfiguration`.** With the amdgpu DDX and
no connected output at server start, X exits with *no screens found*. This
does not bite with the plug in (the plug *is* a connected output) but it
is exactly what would happen if the plug were ever seated badly on a cold
boot: no X, and with §0's finding 1, no way to look.

**Route (a) — `xorg.conf.d`, X spelling.** Create
`/etc/X11/xorg.conf.d/10-monitor.conf`:

```
Section "Monitor"
    Identifier  "DisplayPort-0"
    Option      "PreferredMode" "1920x1080"
EndSection
```

The RandR-1.2 rule is that a `Monitor` section whose `Identifier` matches
an **output name** is bound to that output automatically, which is why the
X spelling (`DisplayPort-0`) is the one that goes here. Applies on the
next X start — `sudo systemctl restart lightdm`, no reboot. **This host's
stack honours this route**: it runs the amdgpu DDX, which implements
output-name Monitor sections, and there is no competing config to fight.

**Route (b) — kernel parameter, DRM spelling.** `video=DP-1:1920x1080@60e`
in `GRUB_CMDLINE_LINUX_DEFAULT`, then `update-grub` and a reboot. Forces
the mode below X, so it survives any X reconfiguration. Heavier: it edits
`/etc/default/grub`, needs a reboot to take, and gets the mode wrong in a
way that is hard to see if the DRM name ever shifts.

**Recommendation: neither, until the plug is in and `xrandr` has been
read.** The plug carries its own EDID and is expected to offer
1920x1080@60 as a mode; if it also offers it as *preferred*, no
persistence file is needed and `H2` should write nothing. Route (a) is the
fallback if the plug prefers 4K@17 Hz, and it is the one write `H2` is
authorized to make.

**No desktop-level override to fight.** `~/.config/monitors.xml` does not
exist (that is a GNOME path; this is XFCE). XFCE's
`displays.xml` holds only `ActiveProfile=Default`, `Notify=1`,
`AutoEnableProfiles=3` — **no saved per-output geometry**, so nothing will
re-apply 1440x900 after login. If a profile is ever saved from the XFCE
Display dialog it *would* override an `xorg.conf.d` preferred mode at
login; do not open that dialog during `H2`.

**Blanking is already off**, which is one thing that will not need fixing:
`xset q` reports screensaver `timeout: 0` and **`DPMS is Disabled`**
(Standby/Suspend/Off all 0), and `xfce4-power-manager.xml` sets
`dpms-on-ac-sleep=0`, `dpms-on-ac-off=0`. **`light-locker` is running**
(pid present, from `/etc/xdg/autostart/light-locker.desktop`) — it locks
on suspend and on session switch. It has not fired during any session so
far; worth a glance in `H2` check 5, since a lock screen on top of the
RetroArch window would change what `x11grab` sees.

## 4. What starts at boot and after login

| | |
| --- | --- |
| enabled system units (filtered) | `getty@`, `lightdm`, `networking`, `NetworkManager` + dispatcher + wait-online |
| companion / privyhub / retroarch unit | **none** |
| enabled user units | keyring, gpg/ssh agent sockets, `pulseaudio`, `mpris-proxy`, IBus, portal — 17 stock entries, nothing project-owned |
| `~/.config/autostart/` | `claude-desktop.desktop`, `expressvpn-client.desktop`, `xfce4-notes-autostart.desktop` |
| `crontab -l` | `no crontab for privyhub` |
| `loginctl show-user privyhub -p Linger` | **`Linger=no`** |

**How the companion is started today:** by hand, per `TOOLS.md`, as
`python3 ./companion/privyhub_service.py` from the project directory
inside the desktop session. The running process (pid at inventory time)
has **`PPID=1`** — it was detached with `nohup … &`, so it outlives the
tmux pane — and carries **`DISPLAY=:0.0`** inherited from the X session.
`native_stream.py`'s `_linux_display()` reads `DISPLAY` **from the
environment and nowhere else**, so a companion started outside an X
session (from a bare SSH shell, or from a systemd unit without
`Environment=DISPLAY=:0`) would find no display and fail closed. That is a
real constraint on any future unit file.

**What an unattended power cycle leaves running: nothing.** LightDM comes
up to a greeter, no user session starts, no companion, no RetroArch.

## 5. The SSH console — not there yet

```
ssh          not-found
sshd         not-found
ssh.socket   not-found
ls: cannot access '/usr/sbin/sshd': No such file or directory
```

Listening TCP ports: **631** (CUPS), **5037** (adb server), **8000**,
**8765** (the companion's two listeners). **Nothing on 22.** No addresses
recorded.

The SSH **client** is installed — `/usr/bin/ssh`, OpenSSH 10.0p2 — which
is why `ssh opal` works for the read-only router sampling. The **server**
is a separate package and is absent. `H1` in
`handoffs/PLAN_WEEK_2026-09-21.md` §"H1" is the user's step and needs
root; it has not been run.

## 6. Capture geometry today

The exact encoder argv from `logs/games/native_video_alpha.log` (address
redacted, everything else verbatim):

```
-f x11grab -framerate 60 -window_id 62914562 -i :0.0
-vf scale=1280:720:force_original_aspect_ratio=decrease:flags=fast_bilinear,
    pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,format=nv12,hwupload
-an -c:v h264_vaapi -profile:v high -b:v 7000k -maxrate 7000k -bufsize 7000k
-max_frame_size 90000 -g 15 -bf 0 -payload_type 96
-f rtp rtp://<redacted>:48110?pkt_size=1200
```

From `native-stream-status`: profile `native_game_720p60_reference`,
output **1280x720 at 60**, `max_frame_size_bytes: 90000`,
`max_frame_size_source: profile`, `any_override: false`,
`x11_display_found: true`, `x11_window_tool_found: true`,
`capture_target.width: 879`, `capture_target.height: 720`.

**The single most important fact for `H2`: the capture source is a
`-window_id`, not the screen.** `_select_capture_target()` fails closed —
it calls `xdotool search --onlyvisible --pid <managed RetroArch pid>` for
up to 2 s and raises rather than falling back to whole-desktop capture.
Consequences for the cutover:

- The **desktop resolution is not the capture resolution**. The last
  session captured an **879x720** window and scaled/padded it to 1280x720.
  1920x1080 buys headroom, not fidelity; a desktop as small as today's
  1440x900 already holds the window.
- **`--onlyvisible` means X-mapped, not physically displayed.** A mapped
  window on a dummy-plugged output is still visible to `xdotool`, so the
  search is expected to keep working headless.
- What *would* break it is the window being **iconified, or never created
  because no session started** (§0 finding 2). Both fail as
  *"Whole-desktop capture is intentionally disabled."* — so if `H2` sees
  that message, read it as **no window**, not as a capture bug.
- `xdotool` is present: `/usr/bin/xdotool`, version 3.20160805.1.

## 7. ADB after a host reboot

`adb devices` shows the onn in state `device` (serial redacted). The
host's key pair `~/.android/adbkey` / `adbkey.pub` exists and is dated
2026-09-15; **the onn's "always allow this computer" is bound to that
key**, so a host reboot does **not** require re-approving on the TV as
long as the key files are untouched.

What a host reboot *does* cost: the **adb server on port 5037 is gone**
and the TCP connection to the onn with it. The first `adb` command after
the reboot restarts the server, and for a network device the connection
must be re-established (`adb connect`) before `adb shell` works. `TOOLS.md`
documents no `adb connect`/`tcpip` procedure — every documented command
assumes an already-attached device — so **`H2` should record the exact
reconnect command it used**, because that is a gap in `TOOLS.md` rather
than something this task could look up.

If the **onn** is ever power-cycled it reverts to needing wireless
debugging re-enabled from its own settings, which is a TV-side step the
user does with a remote and a screen.

---

## Harness

`evidence/h2_prep_2026-09-22/`:

| file | sha256 |
| --- | --- |
| `h2_prep_inventory.sh` | `6f0e1fbc…b478` |
| `h2_prep_redact.py` | `4a3b01d4…30a4` |
| `h2_prep_raw.txt` | `92be6659…d6ce` |

`h2_prep_inventory.sh` is the whole inventory as one read-only script —
run it again with the plug in and diff. `h2_prep_redact.py` strips the
EDID hex block (it carries the panel serial), the root filesystem UUID,
IPv4/IPv6 addresses, MACs and the adb serial; its `--check` mode was run
against the redacted file and reported **0 residual matches**. The
unredacted intermediate was deleted and never written under `docs/`.

## What this task did not do

- No command needed root that was not skipped: `sshd -T` was unreadable as
  this user and is recorded as unreadable rather than guessed.
- The plug is not here, so **no claim is made about what modes it
  presents**. `H2`'s check 1 still has to read them.
- Nothing was changed. The rewritten `handoffs/D-BASE-H2_TASK.md` carries
  the one authorized write as a paste block; it was not applied.
