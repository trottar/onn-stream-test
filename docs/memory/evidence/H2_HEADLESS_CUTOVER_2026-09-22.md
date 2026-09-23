---
memory_schema: 1
as_of: 2026-09-22
status: H2 — headless cutover behind the DisplayPort dummy plug; RUNTIME VALIDATED (checks 1-5 PASS, check 5 user-run 2026-09-22 18:06 boot); no write made
---

# H2 — the host goes headless (2026-09-22)

Task: `handoffs/D-BASE-H2_TASK.md`. Gate: the user, "The dummy plug is
installed and the monitor is off." Evidence: `h2_2026-09-22/`, SHA-256 of
every file in `h2_2026-09-22/h2_sha256.txt`.

## Classification

**RUNTIME VALIDATED — checks 1-5 all PASS.** The host comes back
streaming after an unattended power cycle with nothing attached but the
dummy plug: autologin desktop, 1920x1080 @ 60 Hz, adb recovered from the
host, and a 120 s session inside the monitor-attached bounds — **given the
companion is started by hand** (nothing starts it at boot; `Linger=no`).
Check 5 was run by the user from a fresh SSH shell after a second
plug-only reboot (`h2_check5.sh --session`); see "Check 5 — result".

*History (superseded by the result below):* checks 1-4 were run by
Claude Code on the first plug-only boot; check 5 was left pending because
that session had been started from SSH without tmux and a reboot would
have ended it with nothing to record the result.

**No write was made.** The plug prefers 1920x1080 at 60 Hz by its own
EDID, so `/etc/X11/xorg.conf.d/10-monitor.conf` was not needed and does
not exist. No kernel parameter, no `/etc` change, no XFCE Display dialog.

## Raw numbers first

### Check 1 — the plug, before any change (`xrandr_verbose.txt`, `h2_inventory_plug.txt`)

The host had already been booted with the plug in and the monitor off
(boot at 17:42:50 local, uptime 1 min when the task started), so check 1
was read on a plug-only boot and serves as check 2's boot too.

| | monitor (H2-PREP) | plug (now) |
| --- | --- | --- |
| X output | `DisplayPort-0` | **`DisplayPort-1`** |
| DRM connector | `card0-DP-1` | **`card0-DP-2`** |
| subconnector | `VGA` (active DP→VGA adapter) | `DVI-D` |
| current mode | 1440x900 @ **59.89** Hz, preferred | **1920x1080 @ 60.00 Hz, `*current +preferred`** |
| mode list | 1440x900 max | 1920x1080, 3840x2160@17.00, 2560x1600@29.99, 2560x1440@30.00, 1920x1200 … 640x480 |
| physical size | 408 x 255 mm | 480 x 270 mm |
| EDID vendor / model | (H2-PREP) | **`TCT`, product `0x0270`, name `DP1080P60`**, 2018, 256 bytes (serial not recorded) |
| desktop | 1440x900 | 1920x1080, screen 0 on `DisplayPort-1` |

**The plug is on a different connector from the one the task named.**
`DisplayPort-0` / `card0-DP-1` — the monitor's connector — now reads
`disconnected`; the plug is in the next port, X `DisplayPort-1` = DRM
`card0-DP-2` (the same off-by-one). It does not matter to anything
measured here, because no config names a connector; it **would** matter
to the task's fallback: a `Monitor` section would need
`Identifier "DisplayPort-1"`, and the kernel parameter would be
`video=DP-2:1920x1080@60e`, not `DP-1`.

**The refresh rate moved from 59.89 Hz to 60.00 Hz.** The desktop's
vsync (RetroArch runs `gl` with vsync) is now on a 60.00 Hz output.

Blanking: `xset q` — `DPMS is Disabled`, screensaver `timeout: 0`.
`light-locker` running (autostart), not locked.

### Check 2 — the plug-only boot (`check2_boot1.txt`)

- **Session:** `Type=x11`, `Service=lightdm-autologin`, `Desktop=xfce`,
  `State=active`, `Display=:0` — the desktop, **not the greeter**. No
  password typed.
- **Mode:** `DisplayPort-1` 1920x1080 **60.00*+**. Not 4K/17 Hz.
- **Companion:** started by hand per `TOOLS.md` —
  `DISPLAY=:0 nohup python3 ./companion/privyhub_service.py` — pid 4678,
  the only listener on 8765, `DISPLAY=:0` read from its
  `/proc/<pid>/environ`.
- **adb:** `adb devices` listed **nothing** after the reboot (daemon
  freshly started). Reconnected from the host with
  **`adb connect <onn-address>:5555`** — first try, `device`. The TV had
  not been power-cycled, so the `adb tcpip 5555` pin set before H1 held.
  **This closes the gap `TOOLS.md` recorded** ("cannot be recovered from
  the host alone"): with the port pinned, a *host* reboot is recovered
  from the host. A *TV* power cycle can still undo the pin (untested here).
- **Console:** Claude Code came back from the SSH shell (`sshd` session,
  `Type=tty`), but **not inside tmux** — `tmux ls`: no server. Recorded as
  a deviation from `PLAN_WEEK`; it is why check 5 is pending.

### Check 3 — one 120 s attract-mode session (`S1/`, `h2_analysis.txt`)

PS1 reference title (Tekken 3), zero input, opened through RESUME PLAYING,
BACK to end, harness `h2_session.sh` (B2's shape). Report
`native_decoder_20260922_214956_342.json`.

| | B2 O1-O6 (monitor, uncapped) | P6a V1 / S3 (monitor, capped) | **H2 S1 (plug, capped)** |
| --- | --- | --- | --- |
| `capture_description` | `RetroArch window  879x720` | same | **same** |
| capture source (ffmpeg input) | 879x720 bgr0, 60 fps | 879x720, 60 fps | **879x720 bgr0, 60 fps** |
| encoder output | 1280x720, 60 fps, 7000k | same | **1280x720, 60 fps, 7000k, `-max_frame_size 90000`** |
| rendered fps | 59.63-59.71 | 59.90 / 59.96 | **59.68** — within B2 |
| spikes >= 20 ms / min | 46.4-54.4 | 25.9 / 26.7 | **50.0** — within B2 |
| `max_output_gap_ms` | 139-231 | 141 / 162 | **93** — below B2 (better) |
| stale drops / min | 5.2-8.0 | 0.35 / 0.08 | 7.55 — within B2 |
| lost packets / min | 7.0-24.1 | 12.4 / 5.4 | 1.89 (4 packets, 1 gap) |
| audio lost / underruns | 5-27 / 1-3 | — | 10 / 3 |
| onn thermal (report) | status samples 13 | 121 / 1078 | **13 samples, status 0** |
| host thermal | 58.25 °C | 52.6 / 55.5 | **47.88 °C**, 5 sampler lines |

**`S2`, after the second reboot (check 5)**, same columns: capture
`RetroArch window  879x720`, source 879x720 bgr0 60 fps, encoder 1280x720
60 fps 7000k `-max_frame_size 90000`; fps **59.69**; spikes **46.34**/min;
`max_output_gap_ms` **184**; stale **2.84**/min; loss **21.75**/min (46
packets, 15 gaps); audio lost/underruns 70 / 3; onn thermal 13 samples,
status 0; host **48.38 °C**, 5 sampler lines.

Mid-session `native-stream-status`:
`capture_target = {type: window, process: retroarch, width: 879,
height: 720, backend: x11grab_window}` — **the window, not the screen,
exactly the 879x720 expected**; `max_frame_size_bytes: 90000`,
`max_frame_size_source: profile`, `any_override: false`;
`host_resource_sampler.running: true`.

Reading against the task's rule: capture description, source size and
encoder fps **identical**; rendered fps and spike rate **within** B2;
`max_output_gap_ms` **outside B2's range on the low side** — better, not
worse. The task wrote "within B2's range"; the intent is "no
degradation", and 93 ms is the lowest max-gap of any session in either
reference, so it is recorded as a pass **with that literal exception
named**. One 127 s session does not show that headless *improves* the
gap — B2 was uncapped and n=1 is n=1.

**Harness deviation.** The first attempt failed to open: the launcher
raised the **R3b N150 recovery-save prompt** ("Resume from recovery save
… / Not now") over the preview, so the tap never landed, twice. The save
is kept on disk on purpose for `R3c`. `h2_session.sh` now sends **BACK
only when the dialog is up**, which fires the dialog's cancel listener —
`recoveryPromptVisible = false` and nothing else, no request to the
companion (`MainActivity.kt` `showRecoveryPrompt`). The recovery file's
SHA-256 was **identical before and after** (`05bd85c7…d8040`). Any
harness that opens a Tekken 3 session will hit this until `R3c` lands.

### Check 4 — 30 s `x11grab -> framemd5` of the managed window (`h2_grab_*`)

Method: A3-live's — **no client, no companion game**; RetroArch launched
directly with the exact argv of the companion's managed launch
(`privyhub-session.cfg`, Beetle PSX HW, Tekken 3), window 879x720 found by
`xdotool search --onlyvisible --pid`, 2 s probes until the attract demo
was moving, then the A3 command verbatim (`-framerate 60 -window_id …
-t 30 -f framemd5`). A companion-launched game stays paused with no
client, which is why the direct launch.

| | A3-live (monitor, 2026-09-20) | **H2 (plug)** |
| --- | --- | --- |
| frames | 1,800 | **1,800** |
| PTS delta | 1 on all 1,799 | **1 on all 1,799** (min 1, max 1, mean 1.000) |
| duplicates, total | 140 | 211 |
| — isolated repeats during motion | **7** | **0** |
| — in static stretches (fade / held card) | 133 (last 3 s) | 211, in 4 runs: 80 + 82 frames at 17.9-20.5 s, 4 + 49 at the end |
| seconds at 60 unique | 24 of 27 in motion | **24 of 30** (every motion second) |

**PASS as A3 was read**: exact 1/60 cadence, no missed or doubled grab
slot, zero repeated frames while the picture moves. The literal "duplicates
in the low single digits" holds for motion (0) and not for the total,
exactly as A3's own total (140) did not; the totals are content — the
Tekken 3 demo holds a still card between bouts. **No beat repeat in 30 s**
where A3 saw one every ~9-17 s; consistent with the output now running at
60.00 Hz instead of 59.89 Hz, **not proven** by one sample.

### Inventory diff (`h2_inventory_diff.txt`)

`h2_prep_inventory.sh` re-run with the plug in, redacted with
`h2_prep_redact.py` (`--check`: 0 residual matches, on both files), then
`diff -u` against `h2_prep_raw.txt`. What the cutover changed:

- output `DisplayPort-0` connected → disconnected; `DisplayPort-1`
  disconnected → connected; DRM `card0-DP-1` ↔ `card0-DP-2` the same;
- 1440x900 @ 59.89 → 1920x1080 @ 60.00; subconnector VGA → DVI-D;
- session `Service=lightdm` / `Desktop=lightdm-xsession` →
  `lightdm-autologin` / `xfce` (H1's autologin, first boot on the plug);
- `/etc/lightdm/lightdm.conf.d/10-autologin.conf` present (H1);
- an `sshd` session present (H1).

Nothing else of substance: same Xorg command line, same DDX, no new
`xorg.conf.d`, same blanking settings.

## Check 5 — pending (SUPERSEDED by "Check 5 — result" below; kept as history)

Reboot the host from the SSH console (the user, or a session inside tmux
that expects to die). Then, from a new SSH shell:

```bash
cd ~/Projects/onn-stream-test/docs/memory/evidence/h2_2026-09-22
ONN=<onn-address> ./h2_check5.sh --session
```

It writes `check5_postboot.txt` (session type/service, mode, adb, the
companion started with `DISPLAY=:0`, the cap, tmux) and, with
`--session`, a second 120 s session `S2` into `h2_analysis.txt`. **PASS**
= the same readings as check 2 and S2 within the same bounds as S1. **If
the greeter comes back instead, record it and stop** — the fix is
autologin, not a workaround. When it passes, classify H2 **RUNTIME
VALIDATED** and update this record.

## Check 5 — result (user-run, 2026-09-22)

Raw readings, `h2_2026-09-22/check5_postboot.txt` (written
22:07:42Z, uptime 1 min, boot 0 at 18:06:08 local — the third boot of
the day, the second with only the plug):

1. **Session** — seat session `Type=x11`, `Service=lightdm-autologin`,
   `Desktop=xfce`, `State=active`, `Display=:0`; one `xfce4-session`, no
   `lightdm-gtk-greeter`. **The desktop, not the greeter. PASS.**
2. **Display** — `DisplayPort-1 connected 1920x1080+0+0`,
   `1920x1080 60.00*+`; `DisplayPort-0`/`-2` disconnected; `card0-DP-2`
   connected, `card0-DP-1`/`-3` disconnected; `DPMS is Disabled`,
   `timeout: 0`. **PASS.**
3. **adb** — `adb connect <onn-address>:5555` → `connected`; device in
   state `device`. The pin held across a second host reboot. **PASS.**
4. **Companion** — started by the script (`pre-existing: no`, as
   expected: nothing starts it at boot), pid the only listener on 8765,
   `DISPLAY=:0` in its environ, `capture_backend x11grab_window`,
   `max_frame_size_bytes 90000 source profile any_override False`.
   **PASS.**
5. **tmux** — `error connecting … (No such file or directory)`: no tmux
   server when the script ran. Informational, not a gate. (The user
   started a `h2` tmux session afterwards, from which this close-out ran.)

**`S2`** (`h2_analysis.txt`, `S2/`, report
`native_decoder_20260922_221016_882.json`), against the bounds `S1` was
read against:

| bound | S2 | verdict |
| --- | --- | --- |
| capture_description / source | `RetroArch window  879x720` / 879x720 | identical — PASS |
| rendered fps in 59.63-59.71 | 59.69 | PASS |
| spikes ≥ 20 ms/min in 46.4-54.4 | **46.34** | 0.02 below B2's floor — **fewer** spikes; PASS on "no degradation", literal exception named |
| `max_output_gap_ms` ≤ 231 | 184 | PASS |
| stale drops/min ≤ 8.0 | 2.84 | PASS |
| thermal, both ends | onn 13 samples status 0; host 48.38 °C + 5 sampler lines | PASS |
| mid-session `any_override` | `false` (90000, `profile`); `capture_target` window 879x720 | PASS |

Loss (21.75/min) and audio loss (70) are higher than `S1` and inside B2's
7.0-24.1 range; loss is not a check-5 bound and one 127 s session carries
the day-to-day swing `B2` documents. `S1` 93 ms / `S2` 184 ms max gap
bracket the reference — **n=2 does not show headless improves the gap.**

**Classification: H2 RUNTIME VALIDATED.**

Redaction: `h2_prep_redact.py --check` over `check5_postboot.txt` and
every `S2/` file — **5 residual matches, all non-identifiers, left as
is**: `check5_postboot.txt` line 42 is the script's own `<redacted>` adb
placeholder (the redactor's adb-devices pattern matches any token before
`device`); the report, `native_stream_status_mid.json` and
`status_end.json` carry the core version `0.9.44.1` (the dotted-quad
pattern), and `native_stream_status_mid.json` carries loopback
`127.0.0.1` in the encoder's RTP target. `heartbeat_lines.jsonl`,
`host_resource_samples.jsonl`, `native_video_alpha_lines.log`,
`recovery_lines.jsonl`: 0. No address, MAC, SSID, endpoint or serial.
The report JSON was not rewritten to silence the version-string match.

## Smallest fixes, if a later boot disagrees (none applied)

- mode not 1080p60 → `/etc/X11/xorg.conf.d/10-monitor.conf` with
  **`Identifier "DisplayPort-1"`** (the plug's connector, not the
  task's `DisplayPort-0`), `Option "PreferredMode" "1920x1080"`;
- that not taking → `video=DP-2:1920x1080@60e` (DRM spelling of the
  plug's connector);
- greeter instead of desktop → autologin (`10-autologin.conf`).

## Files (`h2_2026-09-22/`)

`xrandr_verbose.txt` (EDID hex removed), `check2_boot1.txt`,
`h2_session.sh`, `S1/` (report, mid-session status, heartbeat, recovery,
host-sampler and redacted encoder-log lines, end status),
`h2_analyze.py`, `h2_analysis.txt`, `h2_grab_framemd5.txt`,
`h2_grab_ffmpeg_stderr.txt`, `h2_grab_summarize.py`,
`h2_grab_summary.json`, `h2_inventory_plug.txt`, `h2_inventory_diff.txt`,
`h2_check5.sh`, `h2_index.txt`, `h2_sha256.txt`.

## Privacy

No addresses, MACs, SSIDs, serials or device identifiers. The EDID hex
(which carries a serial) is stripped from both xrandr captures; adb output
is redacted to `<redacted>`; the onn's address is passed to `h2_check5.sh`
from the environment and never written.
