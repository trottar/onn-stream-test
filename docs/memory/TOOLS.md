---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: 6abe47d2f7adf1eae847d3b23b12b760586f6d41
---

# Proven Tools and Entry Points

Linux is the current platform. Windows-era entry points are listed at the bottom
as history; do not use them on this host.

Inspect an existing tool before creating a new one. Most diagnostic questions in
this project already have a probe, and the answer to "what evidence exists" is
usually a file that is already being written.

## Normal development commands

Companion launch:

`python3 ./companion/privyhub_service.py`

Restart the companion whenever companion Python changes. D-068 durable rule:
stale-process behavior is not evidence.

**Since `H3` (installed 2026-09-23) the companion is the systemd user unit
`privyhub-companion`.** Restart it through systemd — never `kill` +
`nohup`, which the unit would fight — and confirm the unit's MainPID owns
8765 before any session:

```bash
systemctl --user restart privyhub-companion
MP=$(systemctl --user show -p MainPID --value privyhub-companion)
ss -lntp | grep ':8765 ' | grep -q "pid=$MP," && echo "8765 owned by $MP"
journalctl --user -u privyhub-companion --since "10 min ago"   # its log
```

A per-session companion variable goes in the user manager's environment,
not the unit file, and comes out after:
`systemctl --user set-environment VAR=value`, restart, … then
`systemctl --user unset-environment VAR` and restart again; check
`/proc/$MP/environ`. The by-hand notes below predate `H3`.

**One persistent exception since 2026-10-01 (`C3-L4-D1`): live adaptive
bitrate is the default**, through the drop-in
`~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`. So
the companion's environ carries exactly
`PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, and the user manager carries
**none**. The section "Live adaptive bitrate is the default" below has
the drop-in and both kill switches.

**Check for an existing listener first, and check the log after.** Started
as `nohup … &`, a second companion dies on
`OSError: [Errno 98] Address already in use` into its redirected log and the
old process keeps answering — on 2026-09-20 that silently invalidated a
validation session against brand-new companion code. Before starting:

```bash
ps -eo pid,lstart,cmd | grep "[p]rivyhub_service.py"   # nothing, or stop it
ss -lntup | grep 8765                                  # must be free
```

and after starting, confirm the new pid is the one serving, not just that
something answers.

**`pgrep -f` and `pkill -f` match this shell's own wrapper**, because the
pattern text appears in its command line — the kill then takes out the
shell too (exit 144). Select the pid explicitly instead:

```bash
COMP=$(ps -eo pid,cmd | awk '/[p]ython3 \.\/companion\/privyhub_service\.py/{print $1}')
kill "$COMP"
```

**Stopping the companion with a game active orphans RetroArch**; a restarted
companion reports `active: false` and does not reclaim it. End the game
first, or clean up afterwards (`tools/recover_orphan_game_session.py`, or
kill the AppImage directly when the session holds nothing worth keeping).

Android build and install (the adopted APK since 2026-09-30:
`de072762…835e`, `runtime/cl_b1_apk/cl_b1_app-debug.apk`). **The wrapper is in `PrivyHub/`, not the
repository root** — running it from the root fails with
`sh: 0: cannot open ./gradlew: No such file` (cost `D-BASE-R5` a build):

```bash
cd PrivyHub && sh ./gradlew :app:assembleDebug --no-daemon   # ~16 s warm
adb install -r PrivyHub/app/build/outputs/apk/debug/app-debug.apk
adb shell am force-stop com.safeiot.privyhub
```

**Confirm the installed bytes are the ones just built** — hash the APK
locally and hash `pm path com.safeiot.privyhub` on the device; they must
match before any session is treated as evidence.

Patch installers that change Android source run the real Gradle build
themselves and roll back exact tracked bytes if it fails.

Driving a stream session from a host shell (2026-09-20): `adb install -r`
ends the old app process by itself, so the force-stop above is optional.
`NativeStreamActivity` is not exported — `adb shell am start` on it is
refused and `run-as … am start` exits 255 — so open the launcher and use its
RESUME PLAYING preview once the companion reports the game active:

```bash
adb shell input keyevent KEYCODE_WAKEUP          # see the screensaver note
adb shell am start -n com.safeiot.privyhub/.MainActivity
adb shell input tap 1008 298
adb shell input keyevent KEYCODE_BACK
```

The tap coordinates are the preview's centre on the 1920x1080 launcher
layout; confirm with `uiautomator dump` if the layout changes. BACK posts
the decoder session report and stops the stream; never force-stop to exit.
The companion stores a report of up to 48,000 decoded characters (`C3-L3A-R2B`; the URL-encoded
request line caps it at ~41.4K in practice). A refused one leaves
`WARNING decoder-session-log rejected (400): <reason>; report_chars=<n>` in the journal; the client
shows nothing, so after a session check the journal for that line or for `Native decoder session log:`.

**Wake the device and open the launcher immediately before the tap.** The
TV's screensaver (`com.google.android.apps.tv.dreamx`) takes over an idle
launcher within about a minute and swallows the tap; a 2026-09-20 run lost
its first session attempt that way. A session in progress is safe —
`NativeStreamActivity` holds `FLAG_KEEP_SCREEN_ON` — so only the idle gap
between `am start` and the tap is at risk. Keep that gap short rather than
changing the device's screensaver settings.

**Host temperature and per-process resources: `tools/host_resource_sampler.py`.**
One JSON line every 30 s to `logs/games/host_resource_samples.jsonl` —
`hwmon` temperatures by sensor name (`k10temp`, `amdgpu`, `nvme`), GPU
power, load average, and CPU %, RSS, RssAnon and threads for RetroArch, the
companion, the encoder and the FEC relay. **The companion starts and stops
it with every native stream session** (`nice 10`, its own process, failures
swallowed), so a session needs no harness to leave a host series behind;
`native-stream-status.host_resource_sampler` says whether it is running.
Rotates at 4 MiB keeping 3 into `logs/games/stream_log_archive/`, so the
existing `stream_log_archive` retention family bounds it.

```bash
python3 tools/host_resource_sampler.py --once      # one sample, prints, writes nothing
python3 tools/host_resource_sampler.py --interval 10
```

Its process matching excludes shells by executable basename, because an
explicit `ps` scan hits the same trap as `pgrep -f` otherwise: a
`/bin/bash -c` whose command line contains the needle is not the process
(observed again while building this tool).

**Between back-to-back sessions, stop the game first.** BACK ends the
client session but leaves the game **active and paused** on the host, so a
`POST /plugins/games/launch` for the same title is a no-op: the native
stream never starts and the session never reaches `PLAYING`. Issue
`POST /plugins/games/stop` and wait for `active: false` before each launch
(learned 2026-09-21, `C5a` session R2's first attempt).

**Teardown order — the companion is stopped last, and only after the
client has seen the game end.** The launcher's "NOW PLAYING" banner is
cleared only by its own END control or by an `onResume` poll of
`/plugins/games/status` that returns `active: false`; a poll that fails
because the companion is already gone leaves the banner up (learned
2026-09-20, the first autonomous session left the onn showing the banner).
So, after BACK and the report has landed:

```bash
adb shell input tap 1776 298              # preferred: END on the launcher
# END raises a modal: "Save a state before ending?"  Cancel / Don't Save / Save
adb shell input tap 1213 641              # Don't Save — writes no savestate
# or: POST /plugins/games/stop from the host, then make the client re-poll:
adb shell input keyevent KEYCODE_HOME && adb shell am start -n com.safeiot.privyhub/.MainActivity
curl -s localhost:8765/plugins/games/status   # must show "active": false
# only now:
kill <companion pid>
```

Confirm the banner is gone (`uiautomator dump` and grep for "NOW PLAYING")
before stopping the companion. If a run has already left the banner up,
starting the companion and reopening the launcher clears it; so does
`adb shell am force-stop com.safeiot.privyhub` followed by a relaunch, since
the banner state is in memory only.

## The host console — SSH from the PC (H1, verified 2026-09-22)

**The host is headless as of 2026-09-22 (`H2`)**: no monitor, a
DisplayPort dummy plug (EDID `DP1080P60`) in X **`DisplayPort-1`** = DRM
**`card0-DP-2`** — the port next to the old monitor's `DisplayPort-0`.
It prefers **1920x1080 at 60.00 Hz** by its own EDID, so no X config is
written; it also advertises 3840x2160@17, which must never become the
mode. Capture is unchanged: the 879x720 RetroArch window, 60 fps
(`evidence/H2_HEADLESS_CUTOVER_2026-09-22.md`). The console is **SSH
from the user's PC, with the PC joined to the Opal's wifi** — no
port-forward through the Opal, no VNC. Addresses live in the PC's
`~/.ssh` config, never here.

Check the display from SSH with
`DISPLAY=:0 xrandr | grep -E "connected|\*"` — expect
`DisplayPort-1 connected 1920x1080` and `60.00*+`. If the mode is wrong:
`DISPLAY=:0 xrandr --output DisplayPort-1 --mode 1920x1080 --rate 60`.
**If the plug is removed or swapped** (untested): put the plug — or a
monitor — back in a DisplayPort socket, then
`DISPLAY=:0 xrandr --output <the connected output> --auto` (the output
name follows the socket: `DisplayPort-0/1/2`); if X or the session is
gone, `sudo systemctl restart lightdm` brings the autologin desktop back
without a reboot. A persistent mode, if ever needed, is
`/etc/X11/xorg.conf.d/10-monitor.conf` with `Identifier` = **the X name
of the plug's output** and `Option "PreferredMode" "1920x1080"`.
**Do not open the XFCE Display dialog**: saving a profile there starts
overriding the mode at login.

`sshd` is **key-only**: `PasswordAuthentication no`,
`KbdInteractiveAuthentication no`, `PermitRootLogin no` in
`/etc/ssh/sshd_config` (`/etc/ssh/sshd_config.d/` is empty, so nothing
overrides them), one ED25519 key in `~/.ssh/authorized_keys` at mode 600.
A lost key means a keyboard on the host, so do not remove it.

Work is driven from that SSH session as:

```bash
tmux new -s privyhub          # or: tmux attach -t privyhub
claude --remote-control
```

**`DISPLAY=:0` is the only export the companion needs from SSH.** It is
required — `_linux_display()` in `companion/native_stream.py` reads
`DISPLAY` from the environment and nowhere else, and a bare SSH shell does
not have it:

```bash
cd ~/Projects/onn-stream-test && DISPLAY=:0 python3 ./companion/privyhub_service.py
```

**No `XAUTHORITY` is needed.** The X server's access list carries
`SI:localuser:privyhub`, so any local process running as the project user
is authorised whatever its environment — verified by reaching X with
`HOME` pointed at a non-existent path. `~/.Xauthority` exists and
`XAUTHORITY=/home/privyhub/.Xauthority` is set inside the desktop session;
passing it from SSH is optional. `:0` and `:0.0` are the same screen.

**Autologin is in force**, set by
`/etc/lightdm/lightdm.conf.d/10-autologin.conf`:

```
[Seat:*]
autologin-user=privyhub
autologin-session=xfce
```

A reboot therefore comes up with an active X11 session on `seat0` and no
password typed — `loginctl show-session <n>` reads `Type=x11`,
`State=active`, `Service=lightdm-autologin`. `light-locker` runs but has
no idle trigger (X screensaver `timeout: 0`, DPMS off on AC); if it ever
locks it switches to the greeter VT and takes the X session out from under
`x11grab`, so treat a locked session as a capture fault.

**`Linger=no`** — the tmux server is killed at logout. Autologin means a
reboot is not a logout, but a reboot still kills tmux and everything in
it, and **nothing starts the companion at boot**: no unit, no crontab, no
linger. Start it by hand after every reboot. **A systemd user unit is
designed and awaiting the user's install** (`H3`, 2026-09-23): the unit,
the paste-ready install/undo steps and `h3_verify.sh` are in
`evidence/H3_COMPANION_AUTOSTART_DESIGN_2026-09-23.md`. Once installed,
restart the companion with `systemctl --user restart privyhub-companion`,
never `kill` + `nohup`. **Stop the companion with SIGINT, not SIGTERM**
(`kill -INT <pid>`): only SIGINT runs its clean shutdown; SIGTERM
orphans a live game.

**adb after a host reboot: `adb connect <onn-address>:5555`** — verified
by `H2` (2026-09-22): `adb devices` is empty after the reboot and that
one command brings the onn back as `device`, from the host, no trip to
the TV. It works because the user pinned the listener with
`adb tcpip 5555` while connected. adb here is wireless only — there is no
USB path. The host key pair `~/.android/adbkey{,.pub}` persists and the
onn does not re-prompt. **A TV power cycle can undo the pin** (untested):
the TV's wireless-debugging listener then returns on a **new ephemeral
port**, stored endpoints answer `Connection refused`, `adb mdns services`
finds nothing, and the port is readable only on the TV, under
*Developer options → Wireless debugging* — connect to it, then
`adb tcpip 5555` to pin it again. `adb reconnect offline` then
`adb connect <endpoint>` recovers a merely-offline device (2026-09-20).
See `evidence/H1_VERIFY_SSH_CONSOLE_2026-09-22.md` section 5.

**Tile states and the recovery prompt (`D-BASE-R3c2`, 2026-09-23;
installed APK `21e3d089…9dcb`).** A game's tile dialog (GAMES → a list →
the title's tile, e.g. CONTINUE PLAYING → "Tekken 3 (USA) - PlayStation")
has one of three primary buttons: **Resume** when that title has a live
session (opens the stream on the same RetroArch process, no load);
**Launch on Companion** that first raises the **Recovery Save prompt**
when no session is live and a `.state.recovery` exists for the title;
otherwise the normal Start Fresh / Load Save dialog. The prompt is **no
longer raised by the launcher's status poll**, so it no longer covers
the RESUME PLAYING preview; **RESUME PLAYING** (the NOW PLAYING bar)
still opens the live session's stream exactly as before. "Resume from
recovery save" launches a fresh core, loads while it runs, pauses for
the handoff and deletes the recovery files. A title launched while
another is live ends the other through the normal stop. Scripted
navigation: find nodes by text in a `uiautomator dump`; **match the
tile's full text** — the NOW PLAYING bar also shows the bare title
(`evidence/d_base_r3c2_2026-09-23/r3c2_checks.py`).

## Reading the Opal, read-only over SSH (O1)

The host reaches the router as **`ssh opal`** — an alias in the host user's
`~/.ssh/config`, outside the repository, carrying the address so nothing
here has to. **Never record the address, a MAC, BSSID, SSID or password.**
It works: the public half is installed. Check with
`ssh -o BatchMode=yes opal true; echo $?` — 0 means ready.

**Read-only, without exception.** The only commands authorized on the Opal
are `iw` (`dev`, `info`, `link`, `station dump`, `survey dump`, `list`,
`phy`), `iwinfo`, `ubus call` for read-only wifi status, **`uci show
wireless` (show only)**, `cat` of `/proc/net/dev`, `/proc/net/wireless`,
`/proc/loadavg`, `/proc/meminfo` and `/sys/class/net/*/statistics/*`,
`logread`, `date` and `uptime`. **Never `uci set`, `uci commit`, `wifi`,
`reboot`, `opkg`, or any write to `/etc`.** Nothing is installed on the
Opal and nothing is written to it. `hostapd_cli` is not present on this
build.

**The sampler**, `evidence/o1_2026-09-21/o1_opal_sample.sh` — one
`ssh opal` per round, default 10 s, JSON lines, with `o1_run.sh` (one
session with the sampler running 60 s either side), `o1_analyze.py`
(per-minute), `o1_fine.py` (per 10 s) and `o1_encoder_burst.py` (the
content-lock and the encoder's own progress line):

```bash
docs/memory/evidence/o1_2026-09-21/o1_opal_sample.sh air.jsonl 10 wlan1
# Ctrl-C, or: touch air.jsonl.stop
```

**A round costs 1.66-1.73 s and does not move the Opal's load** (1.08-1.18
idle; a sampling-only run with no stream saw it *fall* 1.33 → 1.08). Load
through a streaming session runs 1.05-1.81, median 1.13 — that rise is the
stream and RetroArch's launch, not the sampler.

**`o1_redact.py` runs on every byte before it is displayed or stored** —
MACs and BSSIDs to stable per-run labels (`sta-A`, …), SSIDs, WPA keys,
IPv4/IPv6 and hostapd accounting ids replaced. **Two defects in its first
version leaked to a terminal before they were fixed**: its IPv6 pattern ate
any bare `HH:MM:SS` clock, and its SSID/secret patterns matched
`option ssid '…'` but **not** `uci show`'s `wireless.…ssid='…'` or
`.key='…'`, so one `uci show wireless` printed both SSIDs and both WPA
passphrases in clear. Both are closed. **If you add a command that prints a
new shape of identifier, extend the redactor in the same edit.**

### What this AP populates, and three traps (`O1`, 2026-09-21)

**Live and usable, per station:** `tx retries`, tx/rx packets and bytes,
`rx drop misc`, signal and signal avg, tx/rx bitrate with MCS/NSS/width,
connected and inactive time; per radio, `noise`; per interface, the
`/sys/class/net/*/statistics/*` counters.

1. **`survey dump` does not accumulate.** `channel active time` reads a
   fixed **29-30 ms** on every call — after 46 h of uptime — and `channel
   receive time`, `channel transmit time` and `extension channel busy time`
   are **absent entirely**. It is an instantaneous 30 ms window, **never
   difference it**. Non-in-use frequencies carry no data at all, and
   `iw list` advertises no survey capability.
2. **`channel utilization` on `iw dev <if> info` is that window rounded.**
   3.3 % is exactly 1 ms of 30, so the figure is quantised in **3.33 %
   steps**, and the radio is observed **30 ms in every 10,000 — a 0.3 %
   duty cycle**. The mean over many rounds is a fair estimate of occupancy;
   it **cannot see contention shorter than seconds**, and more rounds do
   not change that. Reference levels: **2.9-3.3 % idle, 6.9 % carrying the
   game stream** — the channel is ~93 % idle under load.
3. **`tx failed` is not independent of `tx retries`.** Their difference
   held at **6,790 → 6,792 across four hours and 240,000 retries**, so
   differencing `tx failed` measures retries. **Retry exhaustion cannot be
   read on this driver**, which is the gap that leaves air-versus-queue
   unresolved.

**Also all zeros here, as on the onn:** `/proc/net/wireless` link, level,
noise, every discard column and `missed beacon`. Retry rate under load is
**10-11 %** of tx packets at −70 dBm.

## Packets per frame, from the relay (D-BASE-P5)

Since `D-BASE-P5` the FEC relay counts the packets of every encoded frame
— the run of packets sharing one RTP timestamp, ended by the marker — and
writes **one JSON line per second** to
`logs/games/native_frame_sizes.jsonl` (schema
`privyhub_native_frame_sizes_v1`). **Counting only**: nothing forwards,
delays, reorders or drops differently, and the pacing knob stays at 0. Cost
is **0.36 us per packet**, 0.03 % of a core at the stream's rate.

Per second: `frames`, `packets`, `mean_packets`, `max_packets` with its own
`max_at_utc`, `frames_ge_40`, `frames_ge_80`, `unmarked_frames`, and since
`D-BASE-P6` the same frames **in payload bytes** — `payload_bytes`,
`mean_bytes`, `max_bytes` with `max_bytes_at_utc`, and `frames_over_cap`.
**`unmarked_frames` counts frames closed by a timestamp change rather than
a marker** — an encoder restart mid-frame — and is kept apart so it cannot
inflate the large-frame counts.

Rotates at **4 MiB keeping 3** into `logs/games/stream_log_archive/`, so
the existing `stream_log_archive` retention family bounds it; **slice it by
timestamp, never by line offset**, for the same reason as the heartbeat
log.

**The session summary and the percentiles** are on
`GET /plugins/games/native-stream-status` at `fec.frame_sizes`:
`p50_packets`, `p90_packets`, `p99_packets`, `max_packets`,
`frames_ge_40`, `frames_ge_80`, `log_lines`, `log_errors`. Percentiles come
off an exact histogram, not a sample.

**The 1,800-second ring is omitted from that endpoint unless you ask.**
`relay.status()` carries it in full, but the endpoint replaces it with
`buckets_omitted: <n>` unless the query has **`frame_series=1`** — several
`probe_c3_*` tools poll this endpoint every couple of seconds for a whole
session. The JSONL file always has every row.

```bash
curl -s "localhost:8765/plugins/games/native-stream-status?frame_series=1" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['fec']['frame_sizes'])"
```

**Reference distribution** (20-minute attract sessions, CBR 7000, GOP 15):
mean **13.6 packets / ~14.6 KB**, **p50 11 / 12 KB, p90 29 / 32 KB, p99
~80 / ~90 KB, max ~207 / ~245 KB**; **4.0 %** of frames >= 40 packets and
**1.0 %** >= 80. **Measured bytes per packet is 1,063-1,069**, not the
1,188 a `pkt_size=1200` payload maximum suggests, because the last packet
of a frame is partial — measure it, do not assume it. `D-BASE-P5` found
per-minute loss tracks `max_packets` at rho **0.78** and `frames_ge_80` at
**0.78**; `D-BASE-P6` then capped the tail and the loss fell with it.

**`PRIVYHUB_FRAME_BYTE_CAP`** (bytes, default unset) sets the yardstick
`frames_over_cap` counts against. **It sets nothing on the encoder** — it
is what the frames are measured against, not what constrains them.

## The frame-size cap, and how to override it (D-BASE-P6/P6a)

**The cap is ADOPTED and lives in the profile.**
`NativeStreamProfile.max_frame_size_bytes` is **90,000** on
`native_game_720p60_reference`, so the `h264_vaapi` argv carries
`-max_frame_size 90000` **with nothing set in the environment**. It cut
packet loss 7-9x at no measurable cost in bitrate, fps or encoder CPU.
Decision: `decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md`.

**Three source states, and the third is the one to remember:**

```bash
# 1. nothing set -> the profile's 90,000. This is the normal case.
python3 ./companion/privyhub_service.py

# 2. override with another cap (the measured 60 KB alternative)
PRIVYHUB_ENC_MAX_FRAME_SIZE=60000 python3 ./companion/privyhub_service.py

# 3. **=0 runs UNCAPPED** -- the flag is absent from the argv. This is how
#    the D-BASE-P6 baseline is re-run for comparison, without editing source.
PRIVYHUB_ENC_MAX_FRAME_SIZE=0 python3 ./companion/privyhub_service.py

# the VBV arm, measured and NOT adopted (3x the loss of the cap)
PRIVYHUB_ENC_BUFSIZE_K=117 python3 ./companion/privyhub_service.py
```

**Reading which source is in force**, from
`GET /plugins/games/native-stream-status`:

| field | meaning |
| --- | --- |
| `encoder_overrides.max_frame_size_source` | **`profile`** or the variable's name |
| `encoder_overrides.default_max_frame_size_bytes` | what the profile declares (90000) |
| `encoder_overrides.max_frame_size_bytes` | what is actually applied; `null` when uncapped |
| `encoder_overrides.uncapped` | true when no cap is applied |
| `encoder_overrides.any_override` | **false when only the profile decides** — this is "the default is in force" |
| `encoder_command` | the argv actually used, also written to `logs/games/native_video_alpha.log` at launch |

**`any_override: false` no longer means "no cap".** Since `P6a` it means
*nothing but the profile decided the argv*. An uncapped run is
`any_override: true` with `uncapped: true`, because running uncapped is now
the override.

**Only the Linux `h264_vaapi` path honours the field.** The deferred
Windows NVENC builder ignores it and writes one line to the host log
saying so.

**What this encoder does and does not offer** (FFmpeg 7.1.5, Mesa 25.0.7
radeonsi): `max_frame_size` **yes**; `rc_mode` yes (auto/CQP/CBR/VBR/ICQ/
QVBR/AVBR — **the mode in force is CBR**, and `max_frame_size` is
unavailable in CQP); `-maxrate`/`-bufsize` yes, and **the default already
sets both to 7000k**. **`slices` and intra-refresh do not exist** here.
**Average QP is not exposed** — the progress line reports `q=-0.0`, and the
`q=2-31` in the stream banner is a declared range, not an achieved value,
so **the quality cost of a cap cannot be read from instrumentation** and
has to be looked at.

## Reading the onn's UDP socket drops (D-BASE-P5)

The kernel counts datagrams discarded for a full receive buffer, per
socket, in the last column of `/proc/net/udp*`. Host-side over adb,
read-only, **nothing installed on the onn**:

```bash
adb shell cat /proc/net/udp6      # the stream's sockets are HERE
adb shell cat /proc/sys/net/core/rmem_max     # 8388608 on this device
docs/memory/evidence/d_base_p5_2026-09-21/p5_socket_sample.py out.jsonl 2
```

**Two traps, both of which silently return "no drops":**

- **The stream's sockets are in `/proc/net/udp6`, not `/proc/net/udp`.**
  The client's `DatagramSocket(port)` is a Java socket and binds the IPv6
  wildcard. Reading `udp` alone found the ports in **none of 76 rounds**.
  Read both.
- **A row has thirteen fields, not the fourteen the header names**, because
  `tx_queue:rx_queue` and `tr:tm->when` are each printed as one
  colon-joined token. `drops` is the **last** field and `inode` is index 9.
  A `len(parts) < 14` guard rejects **every** row of both files.

Ports in hex: **48100 video is `BBE4`**, **48101 audio is `BBE5`**. Record
only the ports' rows and never the local address.

**`ss -uanm` does not show `skmem` here**, so the socket's *granted*
`SO_RCVBUF` is not readable on this device; the client requests **2 MiB**
and `rmem_max` is 8 MiB, so the request is not capped. `ss` output carries
addresses — do not store it.

**A zero in `drops` is not "nothing was lost on the onn."** It counts
socket-buffer overflow only. For the layers below, read
`/proc/net/snmp`'s `Udp: InErrors`/`RcvbufErrors` and
`/sys/class/net/wlan0/statistics/rx_{errors,missed_errors,over_errors,fifo_errors}`
(`p5_onn_lowlevel.py`). **`wlan0 rx_dropped` is NOT stream loss** — it
advanced +36,988 in a session against 2,233 lost packets and correlates at
rho **0.040**. It is broadcast filtering.

## A per-minute loss series from the heartbeat log (D-BASE-R5)

**Schema is `privyhub_native_stream_heartbeat_v3` since `D-BASE-P7`**,
which added ten audio fields beside the loss counters:
`audio_prolonged_starvation_events`, `audio_lost_packets`,
`audio_rx_packets`, `audio_concealed_underruns`,
`audio_concealed_loss_packets`, `audio_underruns`, `audio_queue_depth`,
`audio_queue_ms`, and two arrival-gap figures —
**`audio_max_arrival_gap_ms`** (this tick's window, **reset on read**) and
**`audio_session_max_arrival_gap_ms`** (the whole session, never reset).
All are cumulative except the two gaps and the two spot queue readings, and
each is **absent rather than zero** when the client does not send it.

**Adding a heartbeat field takes TWO edits, not one.** The client must
send it *and* `plugins/games.py`'s `native-stream-heartbeat` handler must
name it in its **key whitelist** — anything not on that list is dropped
silently, which is how `P7`'s first session recorded no audio fields at
all despite the client sending them.

Since `D-BASE-R5` every 2 s heartbeat carries the receiver's **cumulative**
loss counters — the same ones the end-of-session report reads — so a
per-minute series is a subtraction, with no sampling and no estimation.
Schema `privyhub_native_stream_heartbeat_v2`. The fields are
`lost_packets`, `lost_packets_in_resyncs`, `forward_gap_events`,
`max_forward_gap_packets`, `stream_resyncs` (sequence resyncs + SSRC
changes), `fec_recovered_packets`, `fec_unrecoverable_groups`, beside the
existing `rx_packets` and `elapsed_ms`. At ~620 bytes a line the 4 MiB log
now fills in **≈3.7 h**.

```bash
python3 - <<'EOF'
import json, collections
rows = [json.loads(l) for l in open("logs/games/native_stream_heartbeat.log")]
rows = [r for r in rows if "lost_packets" in r]
# one session only: elapsed_ms increases within a session and restarts at 0
rows.sort(key=lambda r: r["elapsed_ms"])
per_min = collections.Counter()
for a, b in zip(rows, rows[1:]):
    per_min[a["elapsed_ms"] // 60000] += b["lost_packets"] - a["lost_packets"]
for m in sorted(per_min):
    print(m, per_min[m])
EOF
```

**Cut the log to one session before differencing**, and **do not slice it
by line offset.** The counters restart at zero each session, so a delta
across a session boundary comes out negative; and the log **rotates at
4 MiB mid-session** — `D-BASE-R5`'s 20-minute session rotated 17.9 minutes
in — which makes the file *shorter* than an offset taken before the
session and returns an empty slice. That is exactly what happened, and the
597 heartbeats had to be recovered from
`logs/games/stream_log_archive/native_stream_heartbeat.log.1` **and** the
fresh log together. **Read both files and filter on a rising `elapsed_ms`
run.** Rotation itself is clean: `D-BASE-R5` measured sequence step 1 and
elapsed step 2,007 ms across the boundary, so no line is lost.

**Deltas are exact, totals are not the report's.** The series accounts for
the stream between the first and last heartbeat; the report also counts the
head before the first heartbeat and the ~2 s tail after the last, so
`series + head + tail == report.lost_packets` exactly while `series` alone
is slightly short.

**Live, without waiting for the report:**
`GET /plugins/games/native-stream-status` carries `loss_per_min_recent` —
loss over the last 60 s of the current session, using the client's own
`elapsed_ms` as the clock so a companion restart does not distort it. It is
**None**, never 0, when there is no session, when the client is too old to
send the counters, or when the window holds fewer than two heartbeats.

**Do not rebuild the old derived series.** `D-BASE-P4` tried loss as
host-sent minus client-received and measured the noise at **86 packets per
10 s window against a 3.0-packet signal**; that approach is dead and this
one replaces it.

## Reading the onn's radio state (D-BASE-P4)

Host-side over adb; **nothing is installed on the onn and no client or
companion code is involved.** Every command below is read-only. Redact
MACs, BSSIDs, SSIDs and addresses before anything is stored — band, channel,
width and counters are what matter.

**Association, once per session** — `adb shell dumpsys wifi`, the `mWifiInfo`
line: RSSI, Tx/Rx link speed, Max Supported Tx link speed, Frequency,
Wi-Fi standard, Supplicant state. Channel width is a separate
`channelWidth = N` line, and **N is a code, not MHz**: 0=20, 1=40, 2=80,
3=160, 4=80+80. **This dump costs 368-387 ms of onn CPU** — too expensive to
run during a stream session.

**The device keeps its own 3 s radio series, and harvesting it costs the run
nothing.** `dumpsys wifi` contains a `WifiScoreReport` CSV whose header is

```text
time,session,netid,rssi,filtered_rssi,rssi_threshold,freq,txLinkSpeed,
rxLinkSpeed,txTput,rxTput,bcnCnt,tx_good,tx_retry,tx_bad,rx_pps,nudrq,nuds,
s1,s2,score
```

**3,600 rows at ~3 s covering about three hours**, append-only, so one dump
*after* a session recovers the whole session at 3 s resolution. Timestamps
are **device-local**; get the offset from `adb shell date '+%z'` (it read
`-0400` here) and convert. A second ring, `WifiUsabilityStatsEntry`
(`timestamp_ms=...` lines), holds the same sort of thing at 3 s but only
~440 entries with gaps — prefer the score report.

**Scan events** — `adb shell dumpsys wifiscanner`, **67 ms**, a wall-clock
log of `start scan` / `addSingleScanRequest` / `singleScanResults` with the
requesting package and result counts. Append-only, so it also harvests after
the fact. `schedule: base period:` shows the background-scan period.

**Cheap live sampling** — `cat /proc/net/wireless` (~30 ms) gives link
quality, level (dBm) and the discarded/missed-beacon columns for `wlan0`.
Combined with `dumpsys wifiscanner` a full round is **77-87 ms on-device**,
fine to run every 10 s beside a session.

**What this device does NOT report — absences, never read as zeros:**

- `tx_retry`, `tx_bad` and `bcnCnt` in the score report are **identically 0**
  across every row, and `total_tx_retries` / `total_tx_bad` in the usability
  ring likewise. **There is no retry or failure counter on this build.**
- `/proc/net/wireless` discarded columns and `missed beacon` are
  **identically 0**; its `noise` reads **-256**, meaning unreported.
- The usability ring's radio-time fields (`total_radio_on_time_ms`,
  `total_scan_time_ms`, …) are 0 as well.

So retry/airtime questions cannot be answered on this hardware, and a
measurement that needs them needs a different client. What *is* live: RSSI,
Tx/Rx link speed, link quality, `rx_pps`, channel utilisation and the scan
log.

**`iw` and `wpa_cli` are not present** on this build.

## Android source layout

Kotlin sources are **flat**: they sit directly in the Gradle source roots, not
in reversed-domain package directories.

```text
PrivyHub/app/src/main/java/MainActivity.kt
PrivyHub/app/src/main/java/diagnostics/DiagnosticsActivity.kt
PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt
```

Package declarations are unchanged and still read
`package com.safeiot.privyhub[.diagnostics|.streaming]`. Kotlin does not require
a file's directory to match its package; only Java does, and this app has no
Java sources. `namespace` and `applicationId` in `app/build.gradle.kts` are
independent of directory layout, and `AndroidManifest.xml` names classes by
fully-qualified name.

Two consequences worth knowing:

- Android Studio shows a "package directive does not match file location"
  inspection on these files and offers to move them back. **Decline it.** That
  quick-fix would undo the layout.
- If a Java source is ever added, it must live in package-matching directories.
  Do not flatten Java.

Patch `git add` allowlists and probe paths use the flat paths. Records written
before 2026-09-18 name the old `com/safeiot/privyhub/` paths and are history.

## Where dated history lives

One file per date at the memory root: `docs/memory/YYYY-MM-DD.md`.

Until 2026-09-18 there were two locations — the root and `docs/memory/memory/` —
with two different `2026-09-15.md` files. The directory is gone and that date is
merged. Do not recreate `docs/memory/memory/`.

## Audio arrival holes and the heartbeat knob (D-BASE-P8)

Since the `P8` build (schema `privyhub_native_decoder_session_v2`) the
decoder report carries **`audio.arrival_holes`**: every inter-arrival gap
> 15 ms lands in whole-session histograms (length; ms since the last
heartbeat send and since the last client-health send, 50 ms bins, all
holes and holes ≥ 40 ms), plus the last 300 raw rows.
`evidence/d_base_p8_2026-09-22/p8_analyze.py` reads it.

**`PRIVYHUB_HEARTBEAT_MS`** (companion environment, read at each
`native-stream-start`, clamped 1,000-10,000, default 2,000) slows the
client's heartbeat for a diagnostic session. Never leave it set: link-drop
recovery reads the heartbeat. `P8`'s harness restores the companion
without it.

**The report is a URL query, capped at 64 KiB encoded** — over that the
companion answers 414 and the report is lost (`P8`'s first build lost two
that way). Keep any new report field bounded; a normal report is ~25-40 KB
encoded.

**The adb socket sampler (`p5_socket_sample.py`) is safe during audio
measurements** — removing it moved the hole rate by 1 % (`P8`).

**The audio cushion (`D-BASE-P9`)** is a profile pair,
`audio_queue_target_packets` / `audio_queue_capacity_packets` (5 ms
packets; reference **12 / 17** since 2026-09-23, 3 / 8 before), sent to the client in the stream-start
response and shown in `native-stream-status.audio_cushion` (with
`source`). **The capacity sets the running latency** (residence ≈
capacity − 2 packets); the target is only the startup prefill and in
practice arrives after the first PCM. Per session, both or neither:

```bash
# e.g. back to the old 3 / 8 for one comparison session
systemctl --user set-environment PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS=3 PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS=8
systemctl --user restart privyhub-companion
# undo
systemctl --user unset-environment PRIVYHUB_AUDIO_QUEUE_TARGET_PACKETS PRIVYHUB_AUDIO_QUEUE_CAPACITY_PACKETS
systemctl --user restart privyhub-companion
```

The report's `audio.queue_cushion_source` says whether the host's values
were applied. **A 20-minute `audio.underruns` total is noisy** (4-20 at
3/8 across six sessions): read **events** — runs of non-zero 2 s deltas of
the heartbeat's cumulative `audio_underruns` — not totals
(`evidence/d_base_p9a_2026-09-23/p9a_analyze.py` does it). And **audio
loss builds over back-to-back sessions**: compare arms interleaved, never
in one block. `encoder_overrides.any_override` does not include them.
`evidence/d_base_p9_2026-09-23/p9_run.sh` is the systemd-era session
harness (derived from `P8`'s).

**Audio redundancy (`D-BASE-P10`)**: profile `audio_redundancy_copies` /
`_offset_packets`, reference **2 / 4** (each audio datagram sent again 4
ticks = 20 ms later; the client keeps the first). Shown in
`native-stream-status.audio_redundancy` (`source`) and, sender side,
`audio.duplicates_sent` / `duplicate_send_errors`; the report carries
`audio.recovered_by_duplicate`, `duplicates_dropped`, `late_unplaced`,
`sequence_gap_histogram`. Off for one comparison session:
`systemctl --user set-environment PRIVYHUB_AUDIO_REDUNDANCY_COPIES=1`,
restart, then `unset-environment` and restart. **The host sender advances
the sequence on a failed send too, so `audio.send_errors` is the host's
whole share of any client loss** (`T3`).

**Host + onn + Opal together, every 10 s (`D-BASE-T2`):**
`evidence/d_base_t2_2026-09-23/t2_sample.py <out.jsonl> 10` (stop:
`touch <out.jsonl>.stop`). Host hwmon temperatures by label, per-core
cpufreq, encoder / RetroArch CPU %, `eno1` counters; the onn in one
`adb shell` — **`dumpsys thermalservice` gives a live `cpu-thermal`
temperature** (the HAL; `/sys/class/thermal` stays denied), `cmd wifi
status` gives RSSI and link speeds (**`cmd wifi status` prints its own
`====` headers — never split its output on `===`**); the Opal in one
read-only `ssh opal` — the onn's `wlan1` station row (matched by the onn's
address held in memory only, never written), `iwinfo`, load, SoC
`thermal_zone0`. ~0.9 s per round; its adb calls are the only foreign
adb in a hold (safe, `P8`). `t2_analyze.py` / `t2_separation.py` read it
against the heartbeat's per-minute audio loss.

**`save_state_probe.txt` is reset at every game launch**; read the
RetroArch session logs' `[State]` lines to follow loads across launches
(`R3c`).

## Memory and repository health

`tools/check_memory_health.py --repo <repo>`

Required gate for any patch that touches `docs/memory/`. It checks required
files, size thresholds, and the seven exact `CURRENT.md` headings. Treat
`maintenance_required` as a validation failure with exact-byte rollback. The
checker is the specification; see `MAINTENANCE.md`.

`tools/audit_repo_checkpoint.py`

Checkpoint audit: Git whitespace state, critical tracked source, imported Games
modules, diagnostic source tracking, runtime/data leakage, game-content
candidates, legacy Sunshine/Moonlight files. Supplements, never replaces, real
build and runtime validation.

## Game session evidence

`tools/collect_game_session_diagnostics.py --root <repo>`

Writes `logs/games/latest_game_diagnostic_bundle.txt`, one privacy-safe file
containing: selected RetroArch runtime, session-critical RetroArch config, the
unified game session trace, the RetroArch network control trace, the latest
RetroArch verbose session log, the native video host log, the latest Android
decoder session JSON, the per-game state slot index, and the savestate
inventory. IPv4 addresses are replaced with `<IP_REDACTED>` on the way in.

Prefer this single bundle over requesting individual files.

Other evidence entry points:

- `tools/privyhub_debug_bundle.py` — broader support bundle;
- `tools/privyhub_audio_history.py` — audio transport/timing history;
- `tools/diagnostic_retention.py` — bounded diagnostic retention;
- `tools/recover_orphan_game_session.py` — recover a session left orphaned;
- `logs/games/save_state_probe.txt`, `logs/games/retroarch_control_probe.txt`,
  `logs/games/native_video_alpha.log`, `logs/games/decoder_sessions/*.json`;
- `logs/games/native_stream_heartbeat.log` — one JSON line every 2 s while a
  stream session is open (`D-BASE-R2`): `last_output_age_ms`,
  `rendered_frames`, `queued_frames`, `rx_packets`, `elapsed_ms`, host time.
  **A session that ends without a decoder report ends here instead** — the
  last line before the silence is what the client saw. The newest line is
  also on `GET /plugins/games/native-stream-status` as `last_heartbeat`.
  Append-only and unrotated; see `docs/KNOWN_ISSUES.md`.

### Reading the bundle — two retention limits that matter

Both limits silently discard the evidence a reader is most likely to want, so
check them before concluding anything from an absence.

- **The native video host log section is the last 500 lines only.** Earlier
  encoder runs in the same file are cut. A missing restart banner is not proof
  that no restart happened.
- **The decoder session's `slow_events_ge_50_ms` list is a fixed-capacity ring.**
  The report carries `slow_event_retained` and `slow_event_capacity`; when they
  are equal the buffer overflowed and only the most recent events survive. A
  cumulative maximum such as `max_output_gap_ms` can therefore name an event
  whose per-event row is gone.

Cumulative session totals and per-event rows answer different questions. Session
fields such as `max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are
whole-session values and cannot be attributed to one moment when the session
recorded more than one resync.

## Streaming probes

- `tools/probe_c1_stream_parameter_inventory.py` — stream parameter inventory;
- `tools/probe_c2_stream_telemetry_runtime.py` — C2 telemetry runtime
  validation;
- `tools/probe_c3_actuator_continuity.py` — actuator continuity cycle. The
  trigger phase takes **no flag**; `--finalize` is the only option and is run
  after a normal Back. It dispatches by platform inside
  `NativeStreamManager.diagnostic_c3_actuator_continuity_cycle()`, so on Linux
  it drives `companion/diagnostics/c3_linux_actuator_probe.py`.

The fixed-characterization probes **work on Linux as of `C3.L3`**
(2026-09-19). They were Windows-only and failed closed with
`wgc_runtime_unavailable`; the companion now dispatches by platform, so the
probe scripts themselves were never changed:

- `tools/probe_c3_fixed_5000_characterization.py`;
- `tools/probe_c3_fixed_5500_characterization.py`;
- `tools/probe_c3_fixed_6000_characterization.py`.

Trigger takes no flag; `--finalize` is run after play. **Check
`payload.decoder_session_log` and `session_duration_ms` in the written JSON
before using a finalize result** — the matching has picked up the previous
bitrate's session once. See `docs/KNOWN_ISSUES.md`.

`tools/probe_c3_bidirectional_actuator.py` remains Windows-only.

### C3.L3a gameplay acceptance

- `tools/probe_c3_l3a_gameplay_acceptance.py` — the `C3.L4` gate. Fires
  unannounced jump and ramp sequences during play, captures operator marks
  non-blocking, scores them against decoys, then parks at each rung for a
  picture judgement (anchored 1-10). `--plan` shows shape counts and the
  per-dwell decoy placement without running (and refuses a dwell too short
  for it), `--finalize` analyses, `--aggregate` pools runs. Always returns
  the stream to 7000, including on error and Ctrl-C. Encodes no acceptance
  threshold. Defaults since `C3-L3A-P2R1` (2026-09-23): `--traversals 10
  --dwell-min 55 --dwell-max 90 --window 5.0` (the pre-registered rerun);
  every finalize reports W 2.5, 5.0 and 8.0 whatever the primary.
  **`--finalize --state <state.json>`** scores a named run (read only; never
  written) and **`--decoder <native_decoder_*.json>`** names the decoder
  session; without `--decoder` it takes the *earliest* session posted after
  the run with enough SSRC changes (Phase A + parks + restores), never the
  newest. **Split sessions** (`C3-L3A-R1`): if no one session has enough,
  it takes the sessions posted after the run's start, in order, whose
  `ssrc_changes` *sum* to the expected count (or several named with
  `--decoder a.json b.json`), aligns each on its own fires, checks each mark
  in the session that covers it, and prints a CLIENT RESTARTS section and
  the sessions' close-out rows side by side; a sum that does not match is
  stated and the decoder axis skipped. **An accidental BACK mid-run splits
  the client session; the run stays valid and `--finalize` now scores it.**
  Writes `logs/streaming/c3_l3a_runs/<run_id>.{json,txt}` and the
  latest-run `c3_l3a_gameplay_acceptance.{json,txt}` (`logs/` is gitignored:
  copy what a record cites). **Every run also keeps its state** at
  `c3_l3a_runs/states/<run_id>_state.json` (outside `--aggregate`'s glob);
  the shared `c3_l3a_gameplay_acceptance_state.json` is overwritten by the
  next run. `--finalize` without `--state` uses the newest copy when the
  shared file holds a different, older run. Preflight refuses a run if telemetry is not
  fresh or the 12 s settling budget is under three client intervals.
  **`--aggregate` pools only pre-registered runs** (`C3-L3A-P2R3`): v2 state
  and config = `PREREGISTERED_CONFIG` (10 traversals, dwell 55-90 s, W 5.0,
  ramp gap 4.0, park 45 s); every other file in `c3_l3a_runs/` is listed as
  SKIPPED with the field that differs. **`--pool-all`** pools v2 runs
  outside it anyway (default off); the report title and first line say so —
  never cite a `--pool-all` table as the pre-registered result.
- `tools/manual_checkout.py` — shared `yes()`, `ask_int(..., anchors=)`
  (scale anchors printed above the prompt), report writer in the existing
  `Classification:` convention, and non-blocking mark capture. **Existing
  checkout probes are deliberately not migrated to it**; other probes grep
  their reports for exact substrings, so that is its own work item.

## The FEC comparison arm `xor8_2` (C4-M1) — never leave it set

`PRIVYHUB_FEC_SCHEME=xor8_2`, read by the relay at stream start. The relay
keeps sending the v1 XOR parity byte for byte and adds a v2 Reed-Solomon Q
parity datagram per group (`companion/native_fec_rs.py`). The client decodes
it only in an APK that has `FecRs82.kt`.

- **Unset** (or `xor8_1`) is the adopted scheme. Any other value reads
  `xor8_1`, flagged `env_ignored`.
- **While it is set**, `encoder_overrides.any_override` reads true and
  `fec.version` reads `xor8_2`.

```bash
systemctl --user set-environment PRIVYHUB_FEC_SCHEME=xor8_2 && systemctl --user restart privyhub-companion
systemctl --user unset-environment PRIVYHUB_FEC_SCHEME && systemctl --user restart privyhub-companion
```

- **Tests**: `python3 -m unittest tools/test_fec_xor8_2.py -v` (the codec,
  plus the golden check that the unset relay's bytes are unchanged), and
  `cd PrivyHub && sh ./gradlew :app:testDebugUnitTest --tests
  'com.safeiot.privyhub.streaming.FecRs82Test'`.
- **The previous adopted APK** `f31b1c18…8ae7` is kept at
  `runtime/c4_m1/adopted_app-debug.apk`, and the arm APK at
  `runtime/c4_m1/arm_app-debug.apk`.
- **The adopted APK since 2026-09-30 is `de072762…835e`** (CL-B1; the
  C4-M1 v2 decoder inside, inert while the scheme is unset). It is kept at
  `runtime/cl_b1_apk/cl_b1_app-debug.apk`
  (`decisions/CL-B1_APK_ADOPTION_2026-09-30.md`, with the rollback).
  - `tools/c3_l4_nft_night.py`'s preflight checks it.
  - **The C5 night scripts in `evidence/c5_m2_2026-09-29/` and
    `c5_m3_2026-09-29/` still carry `ADOPTED_SHA` / `ADOPTED_APK` for
    `f31b1c18…`**, and their teardown reinstalls it on a mismatch. Point
    them at the new APK before any reuse.

## The native profile selector (C5-M1, C5-M2, C5-M3) — never leave it set

`PRIVYHUB_NATIVE_PROFILE_ID`, read once at companion start
(`companion/native_stream_profiles.py` `select_native_profile`).

- **Unset or empty**: the adopted `native_game_720p60_reference`; the
  encoder argv is byte-for-byte as before the selector (golden test).
- **`native_game_1080p60_candidate`**: 1920x1080, 15,750 kbps, cap
  200,000 B, everything else as adopted. `encoder_overrides.any_override`
  reads true; `native-stream-status` shows `profile_id`, `width`, `height`,
  `bitrate_kbps` and `profile_selection`.
- **Any other value**: the adopted profile, flagged `profile_id_ignored`,
  and still `any_override` true (a variable is set).
- Under the candidate, the C3 ladder routes and recovery's encoder-restart
  refuse (their 7000 guard); a full stream start works.

```bash
systemctl --user set-environment PRIVYHUB_NATIVE_PROFILE_ID=native_game_1080p60_candidate && systemctl --user restart privyhub-companion
systemctl --user unset-environment PRIVYHUB_NATIVE_PROFILE_ID && systemctl --user restart privyhub-companion
```

- **C5-M2 (2026-09-29): three more 1080p60 ids.** Each is 1920x1080,
  GOP 15, B 0, FEC 8, the adopted cushion and redundancy; never the
  default.
  - `native_game_1080p60_c1_parity_cap90`: 15,750 kbps, cap 90,000;
  - `native_game_1080p60_c2_80pct_cap160`: 12,600 kbps, cap 160,000;
  - `native_game_1080p60_c3_80pct_cap90`: 12,600 kbps, cap 90,000.
- **C5-M3 (2026-09-30): three low rungs**, never the default, never on
  the live ladder, cap 90,000 each:
  - `native_game_720p60_4000`;
  - `native_game_720p60_3000`;
  - `native_game_540p60_3500` (960x540).

  Offline quality (lossless reference, SSIM / PSNR / IDR pulse):
  `evidence/c5_m3_2026-09-29/c5_m3_quality.py capture|encode|score`. The
  game is launched without a stream and unpaused through RetroArch's
  command port (`ra_cmd.py <port> PAUSE_TOGGLE`); the port is in
  `data/games/retroarch/config/privyhub-session.cfg`.
- **The C5 hold harness takes any id**:
  - `evidence/c5_m2_2026-09-29/c5_m2_night.sh <name>:<id> ...`, where an
    empty id means the adopted profile;
  - `c5_m2_run.sh`, one hold, with `ARM_PROFILE=<id>`;
  - `c5_m2_score.py screen|confirm <runs dir>`;
  - the teardown unsets the selector on every exit path.

Tests: `python3 -m unittest tools/test_c5_m1_profile_selector.py -v`.
Records: `evidence/C5_M1_1080P60_PROFILE_2026-09-28.md`,
`evidence/C5_M2_1080P60_FOLLOWUP_2026-09-29.md`.

## The PS1 source at 1080p, measured without touching the adopted files (C5-M4)

`evidence/c5_m4_2026-10-01/`. **Never leave the game-specific files in
place.** Every teardown deletes them; `c5_m4_source.sh show` lists what is
in force.

- **`c5_m4_source.sh set <1x|2x|4x|8x>`** writes, for Tekken 3 only:
  - `~/.config/retroarch/config/Beetle PSX HW/Tekken 3 (USA).cfg`, the
    window override: RetroArch fullscreen, a 1920×1080 window on the
    headless display;
  - `Tekken 3 (USA).opt`, the base options with the internal resolution
    set.

  `clear` deletes both. The core options come from `~/.config/retroarch`
  because the companion's environ carries `XDG_CONFIG_HOME`. **3x is not
  offered by this core**: RetroArch rewrites it to 1x on exit.
- **RetroArch's own frame counter.** The override also sets
  `fps_show`/`framecount_show` with the OSD font and widgets off, so
  nothing is drawn on the picture. The window title then carries
  "|| Frames: n", rewritten every 256 frames.
  - `c5_m4_sampler.py <prefix>` timestamps each rewrite with
    `xprop -spy`; a missed vsync is +16.7 ms on an interval.
  - It also writes 1 s per-core CPU, GPU busy, GPU power and temperature
    rows, and with `--telemetry`, the C2 telemetry.
  - **Paused frames count too.** A recovery pause inflates the counter.
- **The RetroArch process's `comm` is `RetroArch-Linux`** (truncated). T2's
  RetroArch CPU is the reliable reading.
- **The attract loop is deterministic from the unpause.** It starts from
  power-on with zero input, so `c5_m4_offline.py capture <work> <label>
  1080|720 <offset_s> <s>` reproduces a segment: a second capture is
  bit-identical after alignment. `encode` and `score` give the
  as-shown-at-1080 SSIM table and the frame-size data.
- **Each launch regenerates `privyhub-session.cfg` and `privyhub-input.cfg`
  with a new command port.** Read the port from the session cfg each
  time.

## The decoder report route's two forms (CL-B1)

`POST /plugins/games/decoder-session-log` takes two forms:

- **body**: JSON, or a form's `report`. The journal shows
  `decoder-session-log received as body: report_chars=<n>`. This is what
  the arm client sends.
- **`?report=`**: the target form, which the adopted APK sends. It is
  capped at ~41K by the request line.

`MAX_REPORT_CHARS` is 128,000. A refused report logs `WARNING
decoder-session-log rejected (400)`.

Tests: `python3 -m unittest tools/test_cl_b1_decoder_report_body.py -v`.
The arm APK is kept at `runtime/cl_b1/arm2_app-debug.apk`.

## Recovery's restart at any ladder level (C3-F1)

`NativeStreamManager.recovery_restart_encoder()` is what link-drop recovery
calls.

- At 7000 it is the `C3.L1` continuity cycle, unchanged.
- Off 7000 it restarts the encoder at the active level.
- To exercise it without link loss, use the loopback-only route (stream
  active):
  `curl -s -X POST localhost:8765/plugins/games/c3-recovery-restart`.
- The continuity route `c3-actuator-continuity-cycle` still refuses off
  7000, by design.
- Tests: `python3 -m unittest tools/test_c3_f1_recovery_restart.py -v`.

## The D7 regression script (D7-R1)

`python3 tools/d7_regression.py --out <dir> --pass-label P1` runs one pass,
one row per D7 item: PASS / FAIL / NEEDS USER / VALIDATED (cited).

- It restarts the companion through the unit, cold-starts the app and runs
  the D136 media probe.
- It launches Tekken 3 and reaches PLAYING through RESUME PLAYING, then
  holds 3 minutes.
- Pause/resume is BACK then RESUME PLAYING; there is no pause route.
- Save/Load uses **scratch slot 3**, which must be empty. The slot index and
  the slot-0 `.state` are backed up and restored, and the other state files
  are hashed before and after.
- It reads the cheat and mod state (the routes are POST-only), then runs
  End: BACK, the report, `POST stop`, and a banner check. The cheat count
  is summed over `sources[i].cheat_count` (fixed in D7-R2), and
  `active-cheats` needs a game active, as it is within a pass.
- Recovery is cited, not re-run.
- Wake the onn first; the harness does.

## The onn's screensaver ends diagnostic activities (D6-R1)

The onn dreams (`mWakefulness=Dreaming`) 600 s after the last input, and
the dream takes the foreground. Any diagnostic activity still running is
ended: the UDP probe activities, and a stream too. **Wake it first**:

```bash
adb shell input keyevent KEYCODE_WAKEUP
adb shell dumpsys power | grep -m1 mWakefulness=    # Awake
```

`p9_run.sh`-derived harnesses already do this before each launch. The
D6-R1 runner does too (`evidence/d6_r1_2026-09-24/d6_r1_run.sh`).

## Live adaptive bitrate is the default (C3-L4-D1, 2026-10-01) — the drop-in and its kill switches

**The user's authorization, 2026-09-30:** "do the loss row look first and
then the live default". The record is
`decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`.

**The drop-in.** It is the only persistent `PRIVYHUB_*`. The unit file
itself is unchanged, and no `set-environment` is used.
`~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`
(copy: `evidence/c3_l4_d1_2026-10-01/adaptive.conf`):

```ini
[Service]
Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live
```

**What shows when it is in force:**

- `systemctl --user cat privyhub-companion` lists it;
- the MainPID's environ carries exactly that one `PRIVYHUB_*`, and
  `systemctl --user show-environment` carries none;
- `native-stream-status` → `adaptive_bitrate.mode live`,
  `configured_mode live`, `acts true`;
- `encoder_overrides.any_override` stays **false**: the adaptive mode is
  not an encoder override.

```bash
systemctl --user cat privyhub-companion | grep -A2 adaptive.conf
MP=$(systemctl --user show -p MainPID --value privyhub-companion)
tr '\0' '\n' < /proc/$MP/environ | grep '^PRIVYHUB_'      # exactly PRIVYHUB_ADAPTIVE_BITRATE_MODE=live
systemctl --user show-environment | grep -c '^PRIVYHUB_'    # 0 -- no set-environment residue
```

**The kill switches:**

- **Off, persistently.** Delete the drop-in, then `daemon-reload`, then
  restart. The mode reads `off`.

  ```bash
  rm ~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf
  systemctl --user daemon-reload && systemctl --user restart privyhub-companion
  ```

- **Shadow, for one session.** At runtime,
  `curl -X POST localhost:8765/plugins/games/adaptive-bitrate/disable`.
  The next session is live again.

**What changed in `tools/` for it:**

- `c3_l4_nft_night.py`:
  - the preflight accepts that one name in the companion's environ, and
    nothing in the manager;
  - live comes up without `set-environment` when it is the default;
  - the teardown clears manager residue only, then confirms the
    **baseline it found** (live by default, off without the drop-in);
    it no longer ends at `off`.
- `d7_regression.py`'s boot row: the same rule.
- Tests: `tools/test_c3_l4_nft_night.py` 32/32.
- The harness's own exit path never touches the drop-in.

**Evidence copies of older scripts are history and were not edited.**
They still unset the mode into "off", or refuse any `PRIVYHUB_*`, and
would now refuse or misreport on the default-live companion:

- every `evidence/*/…_night.sh` and `…_run.sh`, including C5's and
  CL-B1's;
- `evidence/c3_l4_l2_2026-09-29/c3_l4_nft_night.py` and
  `l2b/c3_l4_nft_night.L2.py`.

Before any reuse, take the D1 pattern (`evidence/c3_l4_d1_2026-10-01/`).
Its rules:

- the mode comes from the drop-in;
- the manager carries only a session flag, and only for its session;
- the teardown checks for the default, not for off.

**An adaptive-off measurement** (the adopted profile "as adopted", as
in `LINK-L1`) now needs the drop-in removed for the session and put back
after, or the disable route once each session is up.

## The shadow adaptive-bitrate controller (C3-L4-S1) — never leave the flag set

`companion/adaptive_bitrate.py`. **It never acts in any mode.** Its state
is at `native-stream-status` → `adaptive_bitrate`
(`privyhub_adaptive_bitrate_v1`).

- **Modes.** Unset, `off` or any unknown value → `mode: off`: nothing is
  evaluated or logged. `shadow` evaluates every fresh client report and
  logs decisions and state changes to
  `logs/games/adaptive_bitrate_shadow.jsonl` (4 MiB × 3 into
  `stream_log_archive/`). There is no other mode.
- **Commands, for a shadow run only:**

```bash
systemctl --user set-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE=shadow
systemctl --user restart privyhub-companion        # the mode is read at startup
# ... holds ...
systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE
systemctl --user restart privyhub-companion
tr '\0' '\n' < /proc/$(systemctl --user show -p MainPID --value privyhub-companion)/environ | grep -c PRIVYHUB_   # must be 0
```

- **Tests**: `python3 -m unittest tools/test_adaptive_bitrate_shadow.py -v`
  (21 tests).
- **Harness**: `evidence/c3_l4_s1_2026-09-24/c3_l4_s1_night.sh`. It unsets
  the flag on every exit path.

## The live adaptive-bitrate controller (C3-L4-L1) — never leave `INJECT` set (live is the default since C3-L4-D1)

`companion/adaptive_bitrate_live.py`. `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`
makes the controller **act**: one encoder-only restart per event, through
the same actuator as the loopback `c3-validated-bitrate-transition` route.
Off (the default) and `shadow` behave exactly as above; they never build
the live controller.

- **Mapping**: FALLBACK → 5000, ROUTINE → 6000, an increase is one rung
  after 90 clean reports.
- **Timers**: the blackout is 3 reports after any SSRC change. The
  hold-downs are 30 / 60 reports. The rate limit is 4 transitions per 10
  min.
- **It never acts unless** the stream is PLAYING, the game is active and
  unpaused, recovery reads PLAYING, the reference profile is in force,
  `any_override` is false and the session is at least 60 s old.
- **Status**: `native-stream-status` → `adaptive_bitrate`. It carries
  `mode` (`live`, or `shadow` once disabled), `configured_mode`, `state`
  (`ACTUATING` during a restart), `level`, `last_action`,
  `transitions_this_session`, `rate_limited`, and `policy` (everything
  else).
- **Log**: `logs/games/adaptive_bitrate_shadow.jsonl`, rows `mode: live`.
  - `transition` (acted true) is followed by `transition_done`,
    `transition_aborted` or `actuator_failed`.
  - The other rows are `refused` (with its reason), `ssrc_change`,
    `level_sync`, `session_ended_reset`, `disabled` and `inject`.
- **Kill switches:**
  - **Since `C3-L4-D1` (2026-10-01), live comes from the drop-in**, not
    from the manager. Off is: delete the drop-in, `daemon-reload`,
    restart (section above). The pre-D1 rule, "unset the flag and
    restart: off", now only clears manager residue.
  - At runtime, the controller can be put into shadow for the rest of the
    session (idempotent, any caller). There is **no enable route**; the
    next session is live again:
    `curl -X POST localhost:8765/plugins/games/adaptive-bitrate/disable`.
- **Test-only injection.**
  - It needs `PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1` **and** live. Then
    `curl -X POST 'localhost:8765/plugins/games/adaptive-bitrate/inject?class=FALLBACK'`
    (or `ROUTINE`) feeds one synthetic degraded report through every gate.
  - It answers 403 unless the caller is loopback, both flags are set and
    the controller is not disabled.
  - `inject_enabled` appears in the status only when the flag is set.
- **Commands, pre-D1, history.** Since `C3-L4-D1` only the `INJECT`
  half applies: set it for the session, unset it after, and the
  environ's count is then 1, the drop-in's name. A live session only;
  the rule: unset both, restart, and
  confirm the count is 0 before anything else runs):

```bash
systemctl --user set-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE=live      # [+ PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1 for an injection session]
systemctl --user restart privyhub-companion
# ... session ...
systemctl --user unset-environment PRIVYHUB_ADAPTIVE_BITRATE_MODE PRIVYHUB_ADAPTIVE_BITRATE_INJECT
systemctl --user restart privyhub-companion
tr '\0' '\n' < /proc/$(systemctl --user show -p MainPID --value privyhub-companion)/environ | grep -c PRIVYHUB_ADAPTIVE   # must be 0
```

- **Tests**: `python3 -m unittest tools/test_adaptive_bitrate_live.py -v`
  (102 tests since C3-L4-N2; 43 at L1, 54 at L2, 85 at N1). Replays: `python3 tools/c3_l4_l1_replay.py <out_dir>`
  (shadow-night parity, and the loss would-fire lists).
- **Harness**: `evidence/c3_l4_l1_2026-09-28/c3_l4_l1_night.sh` with
  `c3_l4_l1_run.sh` (arms `H` for a plain live hold, `B` for the
  injection script). It unsets both flags on every exit path.
  `C3-L4-L2`'s B2 variant is `evidence/c3_l4_l2_2026-09-29/c3_l4_l2_night.sh`
  (it holds the full 25 minutes after the first injection).
- **`C3-L4-L2` changes:**
  - **The increase rule is the user's blend.** A report is clean when fps
    ≥ 57, queue ≤ 1 and gap ≤ 150. The window is the last 90 reports since
    the last SSRC change and its blackout; the controller steps up one
    rung when ≥ 85 of the 90 are clean. The constants are
    `INCREASE_*`. Status: `adaptive_bitrate.policy.increase_window`.
  - **Every client report now writes one `sample` row** to the log: fps,
    queue, gap, fresh, clean, disposition, the window count and its clean
    count, state, level, blackout, hold-downs. That is about 0.5 kB a row (527 B measured in B2),
    ~0.95 MB an hour; the log rotates at 4 MiB × 3.

- **`C3-L4-N1` changes (the user's decision of 2026-09-29, live only):**
  - **Capacity trigger**: FALLBACK → 5000 when fps < 50 on all 5 of the
    last 5 evaluated reports and `lost_packets_delta` ≥ 50 on ≥ 3 of
    them. Rows carry `trigger: capacity`.
  - **Recovery-escalation backstop**: two recovery encoder restarts at
    one level within 180 s arm it (an `escalation_armed` row). Then one
    FALLBACK decision comes once recovery is PLAYING and the blackout
    has passed; at 5000 it is `at_floor`.
  - **Status**: `policy.capacity_trigger` and
    `policy.recovery_escalation`; `sample` rows gain `escalation_armed`.
  - **Replays**: `python3 tools/c3_l4_n1_replay.py [out_dir]`. It runs
    parity, every live sample row open-loop, every heartbeat series with
    the loss proxy, and every recovery restart pair, and prints the stop
    rule's verdict.

- **`C3-L4-N2` change (the user's "Go", 2026-09-29, live only):**
  **`capacity_mild`**.
  - The rule: ROUTINE **one rung down** (7000 → 6000, 6000 → 5500,
    5500 → 5000; `at_floor` at 5000) when fps < 57 on ≥ 4 of the last 5
    evaluated reports and `lost_packets_delta` ≥ 50 on ≥ 3.
  - Strict capacity keeps precedence. ROUTINE's hold-downs (60 / 60) and
    L1's deferral apply.
  - The status carries `policy.capacity_mild`. After a session ends, the
    status `level` reads 7000 (the cached stream bitrate is cleared).
  - Replays: `python3 tools/c3_l4_n2_replay.py [out_dir]` (N1's tool, with
    the stop rule on `capacity_mild`).

## The `nft` night harness (C3-L4-L2, one window since L2B) — the user starts it; it runs `sudo -n nft` from an allow-list

`tools/c3_l4_nft_night.py` is the user's fault-injection night for the
live controller. **One window**: the user starts it in tmux over SSH,
types the sudo password once, presses Enter to accept the
pre-registration, and waits. Nothing is pasted.

- **It runs `sudo -n nft …` itself, and only when the user runs it.**
  Code never runs it against real `sudo` (tests use a fake, below).
  - Commands are argument lists (no shell), built only from the fixed
    allow-list `NFT_ALLOW`: table `inet privyhub_fault`, its output-hook
    chain `flt`, the counter rule, the cap rule (`<CAP>` an integer
    200-2000 kbytes/s), the 2 % loss rule, the 15 s drop of 48100 +
    48101, `list table`, `list tables`, `flush chain`, `delete table`.
    Anything else raises `NftRefused` before it reaches sudo.
  - `sudo -v` once at the start (foreground, the password); a keepalive
    `sudo -n -v` every 240 s. If `-n` is refused, the harness removes the
    fault if it can, asks for the password again (`sudo -v`), and puts
    the fault back before continuing.
  - Every call (argv, exit code, output) goes to
    `<run dir>/nft_commands.jsonl`; every listing to `nft_tables.txt`.
  - Each step is verified from `nft list table` (the table present with
    exactly the expected rule) or `nft list tables` (absent). A mismatch
    removes the fault and stops the night through the normal teardown.
- **Every exit removes the fault**: normal end, Ctrl-C, SIGHUP, SIGTERM,
  a stop, an exception → `delete table`, then `list tables` confirms it
  is absent, then the teardown. The on-screen line is `To stop: press
  Ctrl-C — the fault is removed automatically.`
  - Outside tmux, a real SSH drop can leave sudo's per-terminal ticket
    unusable, so the automatic removal may be refused. The harness then
    prints the delete line for the user. That is why the night starts
    inside `tmux new -s nft`, and the harness warns when `$TMUX` is
    unset.
- **The flow** (unchanged from L2):
  - preflight: the companion under its unit, no game, no `PRIVYHUB_*`,
    the adopted profile, the adopted APK hash, no `privyhub_fault`
    table (a leftover one is removed), and the pre-registration printed
    and hashed;
  - `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` (never `INJECT`), then the `T2`
    sampler and a 5 s status poller;
  - F1: the capacity cap, calibrated with a counter rule first, 12 min on
    and 5 min off;
  - F2: 2 % random loss, 10 min on and 5 min off;
  - F3: the cap to 5000, then a 15 s full drop of 48100 and 48101, timed
    and removed by the harness;
  - K: the disable route, called twice during the cap;
  - teardown: the fault table confirmed absent, the flag unset and
    confirmed absent, and everything collected into
    `logs/streaming/c3_l4_nft_night_<stamp>/`.
- **Before and after each fault** it prints one EXPECT line and one DID
  line; each command it runs is printed with its exit code.
- Every child process except the foreground `sudo -v` gets
  `stdin=/dev/null`, so `adb shell` cannot read the keyboard.
- **Commands:**

```bash
python3 tools/c3_l4_nft_night.py --dry-run     # the whole flow, no fault, no sudo, ~20 min
python3 tools/c3_l4_nft_night.py               # the night, ~75-90 min (asks for the sudo password)
python3 tools/c3_l4_nft_night.py --sessions F3,K   # a subset
# TEST ONLY (never real sudo): the real command path against the fake sudo, 60 s holds
FAKE_SUDO_DIR=<dir> python3 tools/c3_l4_nft_night.py --fast --sudo-cmd tools/c3_l4_fake_sudo.py
python3 -m unittest tools/test_c3_l4_nft_night.py -v   # the allow-list, the parser, the fake
```

- `tools/c3_l4_fake_sudo.py` (TEST ONLY) logs its argv and models the one
  table in `$FAKE_SUDO_DIR`. A `deny` file there makes `-n` refuse (the
  re-password path); a `mangle` file makes `list table` show no rule (the
  mismatch path). `--fast` and `--sudo-cmd` must be given together.
  `--test-fail-at F1_cap_on|F2_loss_on|F3_drop` (hidden) raises an
  exception at that point.
- **C3-L4-N1 (2026-09-29):**
  - `--only F1,F3` takes any subset of F1, F2, F3, K and always runs it
    in that order. An unknown, empty or repeated name is refused before
    anything runs. `--sessions` still works as a hidden alias.
  - The default pre-registration is night 2's,
    `evidence/c3_l4_n1_2026-09-29/c3_l4_nft_night2_preregistration.txt`;
    night 1's is `--prereg evidence/c3_l4_l2_2026-09-29/c3_l4_l2_nft_preregistration.txt`.
  - The `did` summary records each decision's trigger and the backstop's
    `escalation_armed` rows.
  - Night 2 is `python3 tools/c3_l4_nft_night.py --only F1,F3` (~45 min).
  - **C3-L4-N2:** the default pre-registration is night 3's,
    `evidence/c3_l4_n2_2026-09-29/c3_l4_nft_night3_preregistration.txt`;
    night 2's is `--prereg evidence/c3_l4_n1_2026-09-29/c3_l4_nft_night2_preregistration.txt`.
    Night 3 is `python3 tools/c3_l4_nft_night.py --only F1` (~25 min).
  - The fake-sudo tests of the subset are
    `evidence/c3_l4_n1_2026-09-29/n1_fake_tests.sh` (FULL, ABORT), with
    `n1_check.py`; run dirs go to `logs/streaming/c3_l4_n1_tests/`.
- **The rule**: never leave `live` or `INJECT` set, and never leave a
  `privyhub_fault` table. The harness unsets the flag and deletes the
  table on every exit path, and records whether `nft list tables` shows
  it absent.

## Linux subsystem probes

Under `tools/probes/`, named by the work item that created them:

- platform bring-up — `d075r1_linux_native_audio_rt_probe.py`,
  `d076_linux_controller_runtime_probe.py`, `d076r1_managed_retroarch_probe.py`,
  `d077_linux_runtime_selection_probe.py`,
  `d078_linux_companion_startup_probe.py`;
- VOD and storage — `d091_vod_client_request_boundary.py`,
  `d092_dynamic_vod_source_start_probe.py`, `d096_storage_boundary_probe.py`,
  `d097_vod_appliance_mode_probe.py`, `d098_absent_vod_catalog_probe.py`,
  `d099_absent_vod_timing_probe.py`;
- EPG — `d103_epg_ingestion_probe.py`,
  `d105_epg_local_source_viability_probe.py`,
  `d106_epg_provider_identity_probe.py`, `d107_epg_feed_identity_probe.py`,
  `d108_epg_local_grabber_viability_probe.py`,
  `d109_epg_portable_node_grabber_probe.py`, `d110_epg_plugin_runtime_probe.py`,
  `d111_android_companion_epg_probe.py`, `d124_tv_epg_latency_probe.py`,
  `d125_epg_background_warmer_probe.py`,
  `d126_android_epg_prefetch_probe.py`, `d132_favorites_epg_coverage_probe.py`,
  `d133_epg_status_accuracy_probe.py`;
- TV state and guide UX — `d113_stream_identity_audit.py`,
  `d115_tv_state_authority_probe.py`, `d116_android_tv_state_sync_probe.py`,
  `d117_linux_authority_pull_probe.py`, `d119_tv_entry_sync_trigger_probe.py`,
  `d120_tv_state_sync_diagnostics_probe.py`,
  `d121_tv_state_conflict_diagnostics_probe.py`,
  `d127_incorrect_guide_probe.py`, `d128_guide_style_ui_probe.py`,
  `d129_single_column_tv_guide_probe.py`, `d130_tv_entry_latency_probe.py`,
  `d131_tv_entry_nonblocking_probe.py`,
  `d134_favorites_load_latency_probe.py`,
  `d135_tv_state_executor_isolation_probe.py`;
- regression gates — `d122_d5_tv_media_regression_probe.py` and
  `d136_focused_tv_media_regression_probe.py`.

Storage administration lives in `tools/storage/configure_vod_storage.py` and
`tools/storage/enable_vod_appliance_mode.py`.

Games probes for Phase A input, multitap and four-player routing remain at the
top level as `tools/probe_a8_*.py`, `tools/probe_four_player_*.py`,
`tools/probe_ps1_multitap_*.py` and `tools/probe_phase_a_*.py`.

## Windows-era, archived

The Windows-only scripts were moved out of `tools/` on 2026-09-18 and now live
under `archive/windows_tools/`:

```text
archive/windows_tools/
    build_install_onn.ps1
    audit_repo_checkpoint.ps1
    run_privyhub_debug.ps1
    run_udp_transport_probe.ps1
    run_udp_reverse_transport_probe.ps1
    run_udp_loopback_probe.ps1
    probe_a4_minimize_wgc.py
    probe_a4_occluded_background_wgc.py
    a4_audio_mute_probe/
    a4_audio_float_attenuation_probe/
```

`archive/` is gitignored, so these are untracked on disk and out of the working
tree, while git history still holds every version. Do not consult them unless a
Windows question is explicitly raised; none of them run on this host.

The Opal router-boundary scripts — `tools/run_opal_*.sh` and
`tools/analyze_opal_*.py` — stay in `tools/`. They are POSIX shell and Python,
they run on this host, and D-083 allows re-entry for one bounded measurement
that would change a product or roadmap decision.

Windows-only code that is still imported by production dispatch stays where it
is: `companion/native_wgc_bridge.py`, `companion/process_audio/`,
`companion/diagnostics/c3_actuator_probe.py` and
`companion/diagnostics/c3_fixed_bitrate_probe.py` are selected by platform at
runtime and fail closed on Linux. Do not archive or delete them.

## Privacy

Do not ask for raw address-bearing captures when a redacted summary answers the
question, and never ask the user for IP addresses. Shareable diagnostics redact
network identity; keep it that way.
