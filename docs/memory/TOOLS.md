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

Android build and install. **The wrapper is in `PrivyHub/`, not the
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
  picture judgement. `--plan` shows shape counts without running,
  `--finalize` analyses, `--aggregate` pools runs. Always returns the stream
  to 7000, including on error and Ctrl-C. Encodes no acceptance threshold.
- `tools/manual_checkout.py` — shared `yes()`, report writer in the existing
  `Classification:` convention, and non-blocking mark capture. **Existing
  checkout probes are deliberately not migrated to it**; other probes grep
  their reports for exact substrings, so that is its own work item.

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
