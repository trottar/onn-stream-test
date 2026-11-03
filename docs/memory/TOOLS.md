---
memory_schema: 1
as_of: 2026-11-03
---

# Proven Tools and Entry Points

Linux is the only platform. Inspect an existing tool before creating a new
one; the answer to "what evidence exists" is usually a file already being
written.

**History.** Everything else this file held through 2026-10-09 is verbatim in
`archive/memory/TOOLS_HISTORY_2026-11-02.md`: the H1 SSH console, the Opal and
onn radio reads, packets per frame, the frame-size cap override, the UDP
socket drops, the per-minute loss series and the heartbeat fields, the audio
knobs, the streaming probes, the FEC / profile / PS1 / 1080p flags, the `nft`
night harness, the E1 suite's first notes, recovery v2, the E3 flags, the
Linux subsystem probes and the Windows-era list. A record or `MEMORY.md` line
that says "fields in `TOOLS.md`" means that file.

## The fourteen adopted lines (`tools/e1_suite.py` `ADOPTED`)

Each line is its own drop-in under
`~/.config/systemd/user/privyhub-companion.service.d/`, holding `[Service]` and
`Environment=<line>`. The user manager's environment carries no `PRIVYHUB_*`.

| # | Line | Drop-in | Gate |
|---|---|---|---|
| 1 | `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` | `adaptive.conf` | C3-L4 |
| 2 | `PRIVYHUB_EPG_GUIDE_INDEX=cached` | `epg-index.conf` | E3-S6A |
| 3 | `PRIVYHUB_SNES_CORE=snes9x` | `snes-core.conf` | E3-A2 |
| 4 | `PRIVYHUB_RECOVERY_TRIGGER=v2` | `recovery.conf` | E3-A3B |
| 5 | `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` | `snes-capture.conf` | E4-S5D |
| 6 | `PRIVYHUB_OVERLAY_PROVIDER=tailscale` | `overlay.conf` | G-A1 |
| 7 | `PRIVYHUB_SESSION_IDENTITY=v2` | `session-identity.conf` | G-A1 |
| 8 | `PRIVYHUB_AUDIO_CODEC=opus` | `audio-codec.conf` | G-A2 |
| 9 | `PRIVYHUB_LINK_REPORT=1` | `link-report.conf` | G-A3 |
| 10 | `PRIVYHUB_LINK_RECOVERY=1` | `link-recovery.conf` | G-A4 |
| 11 | `PRIVYHUB_RESTART_FAST=1` | `restart-fast.conf` | G-A5 |
| 12 | `PRIVYHUB_RESTART_FAST_UNLOCK=1` | `restart-fast-unlock.conf` | G-A7 |
| 13 | `PRIVYHUB_REMOTE=1` | `remote.conf` | G-A9 |
| 14 | `PRIVYHUB_STEP_IN_PLACE=1` | `step-in-place.conf` | G-A10 |

- Line 10 implies six sub-lines (`tools/e3_state.py` prints them as
  `link_recovery`); B33 is live inside it (off: `PRIVYHUB_REWIND_NEEDS_LOSS=0`).
- Line 13 acts only on a remote-class session (`docs/REMOTE_TRUST.md` §14).
- **The off switch, the same for every line**
  (`evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md` §5):
  1. delete the line's drop-in;
  2. `systemctl --user daemon-reload`, then
     `systemctl --user restart privyhub-companion`;
  3. reverse the line's applied `tools/e1_suite.py` diff (in its adoption
     record), so the check expects one line fewer.
- **Per-run flags** go in the drop-in `e3_flag.conf` (a run's resource limit
  in `e4_constraint.conf`), written before the run's restart and removed, with
  `daemon-reload` and a restart, at its teardown. The adopted state has
  neither.

## The companion unit

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

The unit runs `./companion/privyhub_service.py` from the repository root with
`KillSignal=SIGINT` (the companion shuts down cleanly only on SIGINT).

**`pgrep -f` and `pkill -f` match this shell's own wrapper**, because the
pattern text appears in its command line — the kill then takes out the
shell too (exit 144). Select the pid explicitly instead:
By executable basename, or for the companion its unit's MainPID (above); the hand-launch
snippet that stood here is in the archive.

**Stopping the companion with a game active orphans RetroArch**; a restarted
companion reports `active: false` and does not reclaim it. End the game
first, or clean up afterwards (`tools/recover_orphan_game_session.py`, or
kill the AppImage directly when the session holds nothing worth keeping).

## The live tools (usage from each tool's docstring)

- **`tools/e1_suite.py`** — the Phase E workload suite; also the home of
  `ADOPTED`, `EXPECT_APK` (the CONFIRMED APK pin) and the preflight. It runs
  only pre-registered (it refuses without `--prereg` and a matching
  `.sha256`).
  ```
  python3 tools/e1_suite.py --list
  python3 tools/e1_suite.py run --out <dir> --prereg <e1_preregistration.txt> [--only ID[,ID]] [--runs 2] [--window 300] [--gap 120] [--e2] [--plan …]
  python3 tools/e1_suite.py compare <dir>
  python3 tools/e1_suite.py manifest <dir>
  python3 tools/e1_suite.py --check <dir>     # manifest intact; every run has a summary with a full window
  python3 tools/e1_suite.py --self-test
  ```
- **`tools/e3_state.py`** — the adopted state as one JSON line, read-only, no
  arguments: the preflight (every drop-in, no `e3_flag.conf` /
  `e4_constraint.conf`), PS1 files, APK `CONFIRMED` / `MISMATCH`, no game /
  RetroArch / encoder, MainPID serves 8765; `ok` true when all hold. The
  records call this "`--check` ok on fourteen".
  `python3 tools/e3_state.py`
- **`tools/e1_remote.py`** — the off-site row, reached only through the suite:
  `python3 tools/e1_suite.py run --remote --out <dir> --prereg <file.txt> [--runs 3] [--window 600] [--gap 300] [--wait 900] [--adb]`.
  It needs lines 6 and 7 in the environ; the launch is the user's; the peer
  address is never written (class + a 12-hex hash).
- **`tools/diag_keeper.py`** — the always-on diagnostics keeper, the unit
  `privyhub-diag` (B36; the unit file is `tools/privyhub-diag.service`,
  installed by the user at HOME-1, 2026-11-03).
  `python3 tools/diag_keeper.py [--root ~/privyhub_diag] [--copy-s 300] [--sample-s 60] [--once]`.
  Status `~/privyhub_diag/status.txt`; stop with `touch ~/privyhub_diag/STOP`
  or `systemctl --user stop privyhub-diag`. Retention: day dirs older than 30
  days, its one deletion. The root may not be inside the repo.
- **`tools/diag_read.py`** — the one-line read from the keeper's copies
  (per-session and per-10-min tables, every restart / rewind / pause with its
  cause, the ±60-s view); writes one Markdown file under
  `docs/memory/evidence/reads/`.
  `python3 tools/diag_read.py "last night" | today | "<UTC date> HH:MM..HH:MM" | trip [--source DIR …] [--live] [--root …] [--around HH:MM:SS …] [--around-saves] [--out FILE]`
- **`tools/diag_check.py`** — six read-only lines: adopted, apk, overlay,
  routing, band, diag-keeper. `python3 tools/diag_check.py [--root ~/privyhub_diag]`
- **Trip-era (B30), kept:** `tools/trip_log_keeper.py` (the trip keeper; its
  unit `privyhub-trip-log` ended 2026-11-01; it must stay in the tree because
  `diag_keeper.py` reuses its redactor, tails and readers) and
  `tools/trip_check.py` (`diag_check.py`'s lines 1-5 are its own).
- **`tools/check_memory_health.py`** — the memory gate (`MAINTENANCE.md`).
  `python3 tools/check_memory_health.py [--repo <repo>] [--json-out FILE] [--self-test]`
- **`tools/capability_probe.py`** — E5-S1's capability probe, host reads only.
  `python3 tools/capability_probe.py [--repo <path>] > probe.json`, then
  `tools/e3_redact_check.sh <paths>` over the output.
- **`tools/host_resource_sampler.py`** — below.
- **`tools/c3_l4_nft_night.py`** — the `nft` night harness; the user runs it
  (sessions cannot run `nft` or real `sudo`). It carries the APK pin
  `ADOPTED_APK_SHA256` beside `EXPECT_APK`.

**Long unattended runs** are detached transient units, as LINK-N1 launched
(`evidence/LINK_N1_LAUNCH_2026-10-23.md` §1):
`systemd-run --user --unit=<name> --collect -p WorkingDirectory=<repo> /usr/bin/python3 <script>`,
with a one-line `status.txt`, a `STOP` file the tool checks and never removes,
and `systemctl --user status <name>` / `journalctl --user -u <name>`.

## Android build and install

The CONFIRMED APK is the one pinned in `tools/e1_suite.py` `EXPECT_APK`
(`fcd924c2…` today; the rule is in `MEMORY.md`). The Gradle wrapper is in
`PrivyHub/`, not the repository root:

```bash
cd PrivyHub && sh ./gradlew :app:assembleDebug --no-daemon   # ~16 s warm
adb install -r PrivyHub/app/build/outputs/apk/debug/app-debug.apk
adb shell am force-stop com.safeiot.privyhub
```

**Confirm the installed bytes are the ones just built** — hash the APK
locally and hash `pm path com.safeiot.privyhub` on the device; they must
match before any session is treated as evidence.

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

## Driving the onn

**Wake the device and open the launcher immediately before the tap.** The
TV's screensaver (`com.google.android.apps.tv.dreamx`) takes over an idle
launcher within about a minute and swallows the tap; a 2026-09-20 run lost
its first session attempt that way. A session in progress is safe —
`NativeStreamActivity` holds `FLAG_KEEP_SCREEN_ON` — so only the idle gap
between `am start` and the tap is at risk. Keep that gap short rather than
changing the device's screensaver settings.

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

With the unit, that last step is `systemctl --user stop privyhub-companion` (or a
restart), never `kill`.

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

## Host resources

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

## Privacy

Do not ask for raw address-bearing captures when a redacted summary answers the
question, and never ask the user for IP addresses. Shareable diagnostics redact
network identity; keep it that way.
