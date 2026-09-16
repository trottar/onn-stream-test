---
memory_schema: 1
as_of: 2026-09-16
baseline_commit: 88c797ea3a7659035ef4a45380789cfe8c5cbc53
---

# Current Handoff

<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:HANDOFF:BEGIN -->
## D-103 handoff — D5.2 EPG ingestion probe

D5.1 Live TV playback/catalog is runtime accepted. The unresolved symptom remains
2 EPG mappings / 0 cached programmes and empty Program Guide content.

Run the read-only D-103 probe. It compares:
`guides.json -> Android-equivalent parser -> catalog channel IDs -> optional onn
SQLite snapshot -> bounded XMLTV programme sample`.

Do not clear EPG/cache state before the probe.

Return:
`cat logs/tv/d103_epg_ingestion_probe.txt`

Do not patch production EPG behavior until the first divergent boundary is
measured.
<!-- PRIVYHUB_D103_D5_EPG_INGESTION_PROBE:HANDOFF:END -->



<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:HANDOFF:BEGIN -->
## D-102 handoff — D5 TV/EPG and Linux state sync

D5 storage is already runtime accepted and must not be reopened without fresh
regression evidence.

Fresh onn Live TV result:
- normal TV categories/navigation work;
- normal Live TV playback works;
- English / All Countries;
- 3356 streams, 22 favorites, 49 reliable, 4 hidden, 3 enabled providers;
- catalog refreshed 2026-09-16 15:55:38 local;
- EPG mappings 2, cached programmes 0;
- Program Guide opens, but tested channels have no actual guide listings.

Classification:
- D5.1 Live TV catalog/playback: **COMPLETE / runtime validated**.
- EPG data: **NOT ACCEPTED**.
- D5.2 next: one diagnostic-only EPG ingestion probe; no speculative production
  guide patch.

Accepted TV-state direction:
Linux is durable authority for TV user intent; onn remains a local cache/client.
Reuse the existing Android TV export/import representation rather than copying
SQLite databases.

D5 sequence:
D5.2 EPG diagnostic -> D5.3 narrow EPG repair -> D5.4 sync contract ->
D5.5 Linux state store/API -> D5.6 onn sync -> D5.7 sync runtime acceptance ->
D5.8 integrated media/diagnostics regression -> D5.9 checkpoint.

Browser/app and camera/live native streaming remain C6 after D7/D8.
<!-- PRIVYHUB_D102_D5_TV_SYNC_CHECKPOINT:HANDOFF:END -->

<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:HANDOFF:BEGIN -->
## D-101 handoff — browser/camera deferred to C6

External VOD hotplug is accepted.

Do not proceed by porting `start_browser.ps1` / `start_camera.ps1` into Linux
runner equivalents.

D5 next:
1. Live TV playback/EPG runtime acceptance;
2. diagnostics/Self-Test/media regression;
3. D7/D8 Linux baseline checkpoint.

After D8:
return to remaining Phase C on Linux. C6 owns generalized browser/app and
camera/live source streaming using the shared native
capture/profile/transport/decoder architecture.

Potential C6 browser input extension:
onn/client Bluetooth keyboard + mouse forwarding for a stationary/headless
server.

Phase I still owns broader smart-home camera/device integration.
<!-- PRIVYHUB_D101R1_BROWSER_CAMERA_C6_RECLASSIFICATION:HANDOFF:END -->

### D-101R1 local-roadmap correction

The earlier D-101 attempt failed before modification because its
installer incorrectly required `ROADMAP.md` at the Linux repository
root. The roadmap file reviewed in chat was uploaded reference material;
the repo's durable roadmap state is maintained in
`docs/memory/roadmap/STATUS.md`.

D-101R1 records the same accepted reclassification entirely through the
actual durable-memory/decision files and does not create or require a
new root-level roadmap file.

<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:HANDOFF:BEGIN -->
## D-100 handoff — external VOD storage accepted

D-096 through D-099R1 external-VOD work is runtime accepted.

Final onn E2E:
- unplug: no Companion failure; VOD showed no movies;
- refresh: successful;
- reinsert: movies returned automatically;
- Continue Watching returned and worked;
- unplug again: same clean no-movies state;
- refresh: successful.

No Linux/file-manager interaction was required for either recovery cycle.

Do not reopen the external-VOD hotplug/storage investigation without new
evidence.

D5 remains active at the next substep:
1. inspect/port Linux browser runner;
2. inspect/port Linux camera runner;
3. validate Live TV/EPG and media diagnostics;
4. finish D5.
<!-- PRIVYHUB_D100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE:HANDOFF:END -->

<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:HANDOFF:BEGIN -->
## D-099 handoff

Absent-drive timing after D-098: companion alive and 8765 listening; `/status` ~3s; `/sources` and stale Aviator start >12s; port 8000 absent. D-099 replaces path-triggered presence checks with nonblocking backing-device checks and decouples Range server startup from VOD. Validate with the disk physically absent, then reinsert without file-manager interaction and verify automatic recovery.
<!-- PRIVYHUB_D099_NONBLOCKING_VOD_PRESENCE_V1:HANDOFF:END -->

### D-099R1 installer correction

The first D-099 attempt failed before modification on
`docs/memory/CURRENT.md`. Cause: older optional D-097 post-state overwrote newer
D-098 post-state during precheck. D-099R1 sorts predecessor receipts by actual
receipt time before merging. Production D-099 logic is unchanged.

<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:HANDOFF:BEGIN -->
## D-098 handoff

External VOD unplug reproduced:
`OSError: [Errno 19] No such device` from `_scan_media_directory()` during
`GET /sources`.

A Continue Watching item also attempted source-start against the absent library
and then Companion became unavailable because the same dynamic scan exception
escaped.

Reinserting the disk restored Companion behavior, so the stable mount/logical
VOD architecture remains valid.

D-098 is a narrow production fix in `companion/privyhub_service.py`:
dynamic removable-storage filesystem errors now mean an unavailable/empty
dynamic library for that request.

Next E2E:
- drive present: normal VOD works;
- stop playback, unplug without Linux interaction;
- `/sources` stays available and VOD becomes unavailable/empty;
- click stale Continue Watching: controlled failure only;
- Companion remains available immediately afterward;
- reinsert without file manager;
- refresh/re-enter VOD and verify same movies/IDs/playback return.
<!-- PRIVYHUB_D098_ABSENT_VOD_CATALOG_RESILIENCE_V1:HANDOFF:END -->

<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:HANDOFF:BEGIN -->
## D-097 handoff

D-096 storage boundary is host-runtime validated.

Hotplug evidence:
- stopping both `.mount` and `.automount` prevented automatic recovery;
- restarting only the automount and accessing the stable path restored all
  movies in the onn GUI and playback worked.

D-097 therefore keeps the automount permanently active and makes normal VOD
storage read-only.

Next acceptance:
- install D-097 appliance mode;
- run D-097 probe;
- start companion and confirm normal VOD playback/Continue Watching;
- stop playback and physically unplug **without any Linux command**;
- confirm movies disappear/unavailable;
- reinsert **without file-manager interaction**;
- refresh/open VOD and confirm movies automatically return and play.

If that passes, record D-096 through D-097 as runtime validated and checkpoint.
<!-- PRIVYHUB_D097_VOD_APPLIANCE_MODE:HANDOFF:END -->

<!-- PRIVYHUB_D096R3_PROBE_LISTENER_LIFECYCLE:HANDOFF:BEGIN -->
## D-096R3 handoff

D-096 storage functionality remains healthy.

Direct lifecycle evidence after the last probe:
- no PrivyHub processes;
- no LISTEN socket on 8765;
- no LISTEN socket on 8000;
- no owning PIDs.

D-096R3 updates only the probe to use that lifecycle definition and fixes the
false-zero exit code for `NOT_CONFIRMED`.

Next:
rerun the D-096 probe. If confirmed, start companion normally and test onn
Aviator playback + Continue Watching, then perform eject/reinsert recovery
without opening the Linux file manager.
<!-- PRIVYHUB_D096R3_PROBE_LISTENER_LIFECYCLE:HANDOFF:END -->

<!-- PRIVYHUB_D096R2R1_PROBE_INSTALLER_PRESTATE:HANDOFF:BEGIN -->
## D-096R2R1 handoff

D-096R2 did not install. It failed before modification because its installer
allowed only D-096R1 post-state paths and rejected legitimate uncommitted D-096
production/memory files.

D-096R2R1 supersedes that failed installer attempt. It validates the merged
D-096 + D-096R1 installed state, with R1 authoritative on overlapping paths,
then installs the same lifecycle-aware D-096 probe.

After install:
rerun `tools/probes/d096_storage_boundary_probe.py`.
<!-- PRIVYHUB_D096R2R1_PROBE_INSTALLER_PRESTATE:HANDOFF:END -->

<!-- PRIVYHUB_D096R1_STORAGE_DEVICE_DISCOVERY:HANDOFF:BEGIN -->
## D-096R1 handoff

D-096 application code is installed and remains the active development patch.

First storage-helper run:
- returned `ROLLED BACK`;
- failure occurred before stable mount configuration completed;
- cause was automount pseudo-source `systemd-1` being passed to `blkid`.

D-096R1 replaces only `tools/storage/configure_vod_storage.py` with
major:minor -> lsblk real-device discovery.

Next:
rerun the root storage configurator, then run the existing D-096 storage-boundary
probe. Do not reinstall or alter the D-096 production media code.
<!-- PRIVYHUB_D096R1_STORAGE_DEVICE_DISCOVERY:HANDOFF:END -->

<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:HANDOFF:BEGIN -->
## D-096 handoff — stable physical VOD root

D-095 confirmed the external disk has a stable filesystem UUID and the current
failure mode is desktop/user automount ownership.

D-096 implements:
1. optional machine-local `data/storage.json` VOD root;
2. logical `/vod` -> configured physical-root mapping for scanner, health, and
   Linux byte-range server;
3. explicit VOD storage availability in API status/catalog;
4. root-only helper that migrates the current desktop-mounted filesystem to a
   stable `/mnt/privyhub-media` systemd/fstab automount by UUID;
5. removal of the old VOD symlink only after successful mount/config validation.

Internal live/HLS storage stays under project `media/live`.

Next validation:
- D-096 boundary probe;
- normal onn Aviator playback + Continue Watching identity;
- safe eject/reinsert without opening the Linux file manager;
- verify catalog/storage state goes unavailable then recovers automatically.

Do not mix Linux browser/camera runner changes into this validation.
<!-- PRIVYHUB_D096_CONFIGURABLE_VOD_STORAGE:HANDOFF:END -->

<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:HANDOFF:BEGIN -->
## D-094 handoff — remount boundary identified

External-VOD runtime path remains validated.

New evidence:
after drive eject/reinsert, Linux did not automatically remount the external
filesystem. The VOD symlink stayed dangling and the onn library remained empty.
Opening the drive in the Linux file manager triggered the mount. PrivyHub then
repopulated the library automatically and playback worked, without restarting
the companion.

Therefore:
- do not diagnose this as a scanner/recovery defect;
- do not make GUI/desktop automount part of product architecture;
- next D5 storage work is deterministic mount ownership + configurable
  bulk-media root + explicit unavailable-storage state.

Browser/camera runner work remains separate and should not be mixed into this
storage change.
<!-- PRIVYHUB_D094_EXTERNAL_STORAGE_REMOUNT:HANDOFF:END -->

<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:HANDOFF:BEGIN -->
## D-093R2 handoff — external VOD validated, configurable root next

D-092 is runtime validated.

Normal onn result:
- representative external movie launches;
- playback works;
- Continue Watching works.

Closed defect:
dynamic VOD beneath the temporary external-storage symlink no longer fails
`/sources/<id>/start` with HTTP 503.

D-093 and D-093R1 were documentation-checkpoint installer failures only and both
rolled back cleanly. D-093R2 supersedes them.

Next D5 storage step:
replace the symlink-specific deployment assumption with a first-class
configurable bulk-media root while preserving:
- dynamic library scanning;
- stable source/content identity;
- byte-range serving;
- Continue Watching state;
- clean storage-unavailable semantics;
- internal-disk ownership of lightweight PrivyHub state where practical.

After the storage boundary, continue D5 with Linux browser/camera runners and
integrated media/TV/diagnostics regression.
<!-- PRIVYHUB_D093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION:HANDOFF:END -->

<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:HANDOFF:BEGIN -->
## D-092 handoff

D5 VOD first failing boundary is source-start health, not storage readability,
Range serving, client networking, or codec.

Pre-patch symptom:
dynamic external movie is listed, but onn source-start receives HTTP 503
`VOD source is unavailable`; therefore no media request reaches port 8000.

D-092 production change:
`companion/privyhub_service.py::_vod_is_healthy()` now treats only
scanner-generated dynamic VOD as eligible for scanner-mediated symlink
resolution, while confirming lexical-path safety and exact resolved-target
identity.

After install:
1. restart companion;
2. run `tools/probes/d092_dynamic_vod_source_start_probe.py`;
3. if confirmed, retry Aviator on onn;
4. continue only from fresh playback evidence.

Final explicit configurable bulk-media root remains later D5 work.
<!-- PRIVYHUB_D092_DYNAMIC_VOD_SYMLINK_HEALTH:HANDOFF:END -->

<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:HANDOFF:BEGIN -->
## D-091 D5 resume point

D4 is closed. D5 is active.

Already measured on Linux:
- control/catalog/diagnostics/IPTV endpoints reachable;
- 91 VOD sources visible;
- normal byte-range VOD serving works;
- current external movie symlink is readable and cataloged;
- a representative symlinked movie receives correct HTTP 206 Range serving
  from the existing media server.

Do not change the external filesystem or symlink based on the current playback
failure; the host storage/HTTP boundary is healthy.

Next:
run the read-only D-091 onn -> port-8000 request-boundary probe while reproducing
one exact movie failure. If the exact request reaches the server with 200/206,
move to Android Media3/container/codec evidence. If no request arrives, remain
at client URL/network construction.

Still queued later in D5:
- explicit configurable external/bulk media root;
- Linux browser runner;
- Linux camera runner;
- integrated VOD/TV/diagnostics acceptance.
<!-- PRIVYHUB_D091_D5_MEDIA_BASELINE:HANDOFF:END -->

<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:HANDOFF:BEGIN -->
## D-090 handoff — D4 complete, D5 next

D4 Linux Games normal-use parity is accepted.

Fresh final regression passed:
- library/search/art;
- SNES launch/video/audio/input/End;
- PS1 launch/video/audio/input/pause/Save/Load/resume/End;
- cheat profile;
- IPS mod profile;
- named A8 profile;
- post-teardown relaunch/recovery.

D-088 four-player/multitap acceptance remains part of the D4 result.

Explicit coverage gaps:
- NES: no local fixture;
- Genesis: no local fixture.

Do not claim those two systems were runtime exercised on Linux.

### Resume point

Start D5 media/server restoration.

D5 must verify existing companion/control API, VOD, Live TV/EPG, browser/live,
camera, diagnostics/Self-Test, Phase-C profile/telemetry/stabilization
infrastructure, and media state/cache behavior without broadening scope.

Prototype-1 storage constraint:
bulk VOD may use an external hard drive. Keep media-root handling configurable,
do not copy the library onto the internal NVMe merely for D5, and treat an
unavailable external root as storage unavailable rather than library deletion.
<!-- PRIVYHUB_D090_D4_LINUX_GAMES_ACCEPTANCE:HANDOFF:END -->

<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:HANDOFF:BEGIN -->
## D5 storage handoff constraint

Immediate next work remains D4 final Games regression.

When D5 media/server restoration begins, do not assume VOD content is stored
under the Linux project or internal system disk. The current deployment will use
an external hard drive for bulk movie files.

D5 should first audit the existing media-root contract and mount/unavailable
behavior before changing media code. Preserve:
- configurable media root;
- small internal metadata/catalog/cache where practical;
- no bulk-media copying into project storage;
- unavailable external root != deleted library;
- portability toward later dedicated server/storage infrastructure.

No external-drive mount path has been standardized yet; do not hard-code one.
<!-- PRIVYHUB_D089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT:HANDOFF:END -->

<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:HANDOFF:BEGIN -->
## D-088 checkpoint handoff

### Newly closed

Linux PS1 multitap / four-player parity is runtime validated:
- Crash Bash launches with Multitap On;
- Players 3 and 4 are available;
- four remotes operate independently.

The validated chain now includes:
`stored per-game multitap -> Linux RetroArch Config tree -> content-specific Beetle PSX HW .opt -> Port-1 topology -> P1-P4 uinput/udev -> four-player gameplay`

Preserve D-087/D-087R1 and the D-085 controller foundation.

### Next

Return to the Phase-D outline at D4 final normal-use Games regression/acceptance.
Cover the required Games behaviors without reopening validated subsystems unless
fresh evidence contradicts them. Once D4 is accepted, move to D5 media/server
restoration.
<!-- PRIVYHUB_D088_MULTITAP_RUNTIME_VALIDATION:HANDOFF:END -->

<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:HANDOFF:BEGIN -->
## D-087R1 multitap resume point

D-087 found and wrote the correct Linux RetroArch Config path. Launch then
failed only while formatting that external path as project-relative metadata.

D-087R1 fixes the metadata representation only.

After install/restart:
1. Multitap On for the same four-player PS1 title;
2. launch;
3. confirm launch proceeds past options preparation;
4. reach player selection;
5. report whether Players 3/4 are available and whether all four controllers
   operate independently.

If launch reaches the game but topology is wrong, use the read-only Linux
multitap runtime probe against that active session.
<!-- PRIVYHUB_D087R1_LINUX_PS1_MULTITAP_METADATA_PATH:HANDOFF:END -->

<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:HANDOFF:BEGIN -->
## D-087 multitap resume point

First Linux multitap divergence is classified.

The launch failed before RetroArch because the old Phase-A adapter searched the
Windows executable-adjacent Config tree. The Linux seed file is actually:
`~/.config/retroarch/config/Beetle PSX HW/Beetle PSX HW.opt`

D-087 changes only this host filesystem adapter. Preserve D-085 lower controller
parity and the generic per-game multitap materializer.

After installation/restart:
1. Multitap On for a known four-player PS1 title;
2. launch must pass core-options preparation;
3. confirm Players 3/4 are available;
4. confirm all four controllers remain independent.

If launch succeeds but topology still fails, run the read-only active-session
multitap probe before any further production change.
<!-- PRIVYHUB_D087_LINUX_PS1_MULTITAP_CONFIG_PATH:HANDOFF:END -->

<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:HANDOFF:BEGIN -->
## D-086 checkpoint handoff

### Newly closed

Linux gameplay controller parity is now runtime validated after D-085:

- 3 different games;
- 3 different input profiles;
- all reported correct in integrated onn gameplay.

Preserve:
- Android controller sender;
- PHI1;
- Linux uinput generation;
- RetroArch `udev` selection and P1-P4 project autoconfig;
- D-085 `h0*` D-pad mapping;
- D-084 host-specific A8 translation;
- working video/audio/save/lifecycle paths.

### Active next issue

PS1 multiplayer / multitap does not currently work on Linux.

Do not treat this as evidence that the lower controller path regressed. Windows
Phase-A evidence previously validated the feature end-to-end, including
`PS1_MULTITAP_ONOFF_CTR_CONFIRMED`.

Start with a diagnostic-only Linux adaptation of the old multitap runtime check.
Measure, in order:

1. game ID and stored `ps1_multitap` override;
2. content-specific Beetle PSX HW `.opt` path and exact Port-1/Port-2 values;
3. managed P1-P4 uinput/RetroArch configuration during the same launch;
4. Players 3/4 availability;
5. controller independence.

One narrow hypothesis -> one probe -> fresh evidence -> one coherent patch.
<!-- PRIVYHUB_D086_CONTROLLER_PARITY_CHECKPOINT:HANDOFF:END -->

<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:HANDOFF:BEGIN -->
## D-085 controller handoff

Older evidence was re-read before changing code.

Windows Phase A is the gameplay reference: normal 1P/2P/4P sessions were
runtime-confirmed through Android -> PHI1 -> ViGEm/XInput -> RetroArch.

Linux D-076 did not reach equivalent gameplay acceptance. It proved host
controller integration and session lifecycle, while its own patch record still
listed gameplay controls as pending.

The first proven Linux gameplay-binding defect is the D-pad frontend translation:
the uinput device emits ABS_HAT0X/Y, but project RetroArch udev profiles used
ordinary axis binds +/-6/7. D-085 uses RetroArch udev hat tokens h0* instead and
makes the same correction in the Linux A8 explicit-binding adapter.

After installation:
1. restart the companion;
2. launch Crash with Default input profile;
3. verify physical D-pad movement;
4. do not use Crash analog-stick behavior to judge this patch unless the game is
   intentionally launched with an analog-capable PS1 controller mode;
5. then test one existing custom A8 profile.

If D-pad remains dead after D-085, collect the newest per-game RetroArch log and
the generated `data/games/retroarch/config/privyhub-session.cfg` before another
production change.
<!-- PRIVYHUB_D085_LINUX_UDEV_HAT_MAPPING:HANDOFF:END -->

<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:HANDOFF:BEGIN -->
## D-084 Linux A8 adapter handoff

Controller transport/uinput discovery is already proven. A source audit found
that the A8 custom-profile generator remained Windows/XInput-specific after the
Linux uinput migration.

The concrete mismatch is visible directly in current source:

- legacy A8 translator: LT `+4`, right stick X/Y `2/3`, X/Y physical buttons
  `2/3`, D-pad as XInput hat button tokens;
- Linux project udev profile: LT `+2`, right stick X/Y `3/4`, physical
  X/Y appear as joystick buttons `3/2`, D-pad as axes `6/7`, with Linux Y
  directions inverted relative to XInput.

D-084 changes only the final source-token -> RetroArch bind translation and the
existing deterministic A8 adapter probe. Windows translation is preserved in
behavior.

After installation:
1. deterministic A8 probe must pass and restore profile/config bytes;
2. restart the companion;
3. launch an already-assigned custom gameplay profile and verify its intended
   controls;
4. if gameplay still fails, return the fresh per-game RetroArch log and
   `logs/games/a8_2_input_adapter_probe.txt`.

Do not reopen Android PHI1, Linux uinput permissions, or controller enumeration
unless new evidence contradicts the established boundary.
<!-- PRIVYHUB_D084_LINUX_A8_PLATFORM_ADAPTER:HANDOFF:END -->

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:HANDOFF:BEGIN -->
## D4 resume point after Linux/network/controller reconciliation — 2026-09-16

The newest runtime evidence supersedes the older handoff bullets that still list
persistent `/dev/uinput` and realtime-priority setup as unfinished. Those
prerequisites now persist across reboot.

Normal Linux product progress has reached:

- companion reachable;
- PS1 game launch;
- native stream visible;
- controller buttons working;
- PHI1/controller transport healthy;
- Linux virtual gamepad present and detected by RetroArch;
- live analog `ABS_X` / `ABS_Y` events present.

The immediate fault boundary is now **RetroArch PS1 controller mode/session
configuration**. Investigate digital PlayStation pad versus DualShock/analog
behavior before changing any transport or uinput code.

### Network/VPN note

The temporary Windows routing bridge is characterized sufficiently for Phase D.
Keep `expressvpn-pkf` disabled on the physical Wi-Fi/Ethernet adapters for the
known-good PrivyHub routed path. With ExpressVPN itself connected, Windows keeps
Internet access but downstream Linux Internet does not traverse the VPN route.
When Linux needs Internet, disconnect ExpressVPN. This is deferred because the
Windows bridge is temporary.

Do not reopen ICS, firewall, uinput, RT-priority, or ExpressVPN bridge debugging
without new evidence.

The saved Opal/UDP burst-gap investigation remains separately paused; normal
stream success after the ExpressVPN-filter correction does not erase its saved
synthetic evidence.

Other remembered D4 observations:

- Android signing mismatch is a packaging/migration issue, not runtime behavior.
- A fixed-bitrate Linux audio characterization attempt was blocked because
  process audio was inactive; do not reinterpret that as proof the validated
  PulseAudio architecture is broken.
- A prior Linux hard freeze has no established root cause.

Older ADB recovery probe notes remain preserved below for history/tooling. The
newest normal companion/game runtime succeeded, so return to ADB only if
installation or wireless recovery fails again.

### Next

1. Test/fix RetroArch PS1 analog controller mode.
2. Run the complete Linux normal-use game regression.
3. Only then decide whether any remaining transport characterization is needed
   for Phase-D acceptance.

<!-- PRIVYHUB_D4_RUNTIME_RECONCILIATION_2026_09_16:HANDOFF:END -->

<!-- D4_LINUX_HANDOFF_FIX_01_HANDOFF -->
## Active D4 Linux handoff work — 2026-09-15

The unchanged Android app builds successfully on Linux. The active development patch changes `MainActivity.kt` only: Linux no longer fails auto-open on the unsupported Windows host-window policy, idempotent load-state transport failure gets one bounded retry, and literal IPv4 addresses are removed from game-facing errors. Host savestate/emulator code remains intentionally unchanged. Runtime validation is pending.


<!-- PRIVYHUB_MEMORY_NORMALIZATION_D083_2026_09_15 -->

## Resume point

Current work is **Phase D Linux migration / native Linux baseline**. Phase C is
not complete; it is paused at the Windows portability boundary and resumes on
Linux after the Phase-D baseline is usable.

Authoritative Phase-D Linux root:

`/home/privyhub/Projects/onn-stream-test`

The older Windows checkout is reference/history unless explicitly synchronized for a cross-platform regression. Linux local source and fresh runtime evidence outrank GitHub. GitHub checkpoint
`88c797ea3a7659035ef4a45380789cfe8c5cbc53` is the predecessor reference for
this memory normalization only.

## What already works on Linux

Do not reopen these without contradictory evidence:

- project-owned RetroArch Linux runtime/cores;
- existing EmulatorManager lifecycle and graceful End;
- D-074 exact owned X11 window -> x11grab -> VAAPI video backend;
- D-075R1 PulseAudio isolated process audio with sender-thread `SCHED_RR/1`;
- D-076/R1/R2 PHI1 -> four uinput controllers + managed project autoconfig;
- D-077 normal product runtime/core selection;
- D-078 normal Linux companion media-server startup;
- integrated PS1 launch, existing save load, exact X11 discovery, and near-60-fps
  VAAPI encode.

Windows remains a separate validated backend; do not damage it while finishing
Linux parity.

## Current integrated blocker

The representative Linux + home Opal + onn path reproduces severe UDP
burst/gap/duplication while idle in **both directions**.

Forward Test A:
- 3993 successful unique Linux sends;
- zero unique loss;
- 2626 same-stamp Android duplicates.

Reverse Test B:
- 4000 successful Android sends;
- 3894 unique Linux arrivals;
- 106 missing;
- 476 same-stamp duplicates.

This rules out a Linux-only sender and shows game/native-stream load is not
required. Production socket errors under load are secondary amplification.

Router work then showed zero-record packet captures at `wlan0`, `wlan1`, and
`br-lan` despite active endpoint traffic. Disabling exposed OpenWrt flow-offload
flags did not help. Proprietary Siflower networking components remain present.

D083/D083R1 are invalid as networking evidence. D082 is the last valid router
result. The router/Siflower reverse-engineering branch is **PAUSED**. Do not run
another router diagnostic by default.

Re-enter transport localization only if:

1. one bounded measurement would change a product decision; or
2. the same preserved synthetic suite can be run on a different representative
   network/router path.

## Separate confirmed Linux compatibility bug

Android automatic stream handoff still requires the Windows-only
`host_window_policy.window_found`. On Linux this can be false even though the
native backend later finds the correct X11 window.

This explains `Game ready, stream not opened` before manual banner entry. The
bug is confirmed and ready for a narrow code fix; no more diagnosis is needed.

**Next production patch after memory cleanup:** fix this Linux auto-open gate
without touching transport, video, audio, controllers, decoder policy, bitrate,
or FEC.

## Other Phase-D gaps

- Persistent service-scoped `/dev/uinput` access.
- Persistent `RLIMIT_RTPRIO=1`/equivalent for the Linux audio sender; do not use
  broad `CAP_SYS_NICE` on Python.
- Restore user-provided PS1 `scph5501.bin` before final PS1 acceptance.
- Final representative Android/onn E2E remains transport-blocked.

## Do not do next

Do not:

- tune Android stabilization thresholds to hide the transport problem;
- change bitrate/FEC based on the current failure;
- alter decoder policy;
- replace validated x11grab/VAAPI, PulseAudio, PHI1/uinput, or EmulatorManager
  lifecycle paths;
- continue open-ended Opal/Siflower reverse engineering;
- ask the user for an IP address.

## Roadmap

Execution order:

`Phase D Linux baseline -> remaining Phase C on Linux -> Phase E Linux characterization -> Phase F media/VOD/Live TV -> Phase G remote`

Windows C3 evidence to carry forward:
- explicit reference profile and C2 telemetry contract;
- startup stabilization;
- fixed 5500/6000/7000 ladder as test-environment evidence;
- 5000 rejected;
- restart-based actuator works bidirectionally but causes ~1 s visible
  interruption and is not the automatic actuator.

## Proven Linux command

From `/home/privyhub/Projects/onn-stream-test`:

`python3 ./companion/privyhub_service.py`

Do not substitute the historical Windows PowerShell build/install command into the Linux handoff.

For game-stream diagnosis, prefer existing logs and
`tools/collect_game_session_diagnostics.py` before adding new probes.

## Working rules

- one narrow hypothesis -> one targeted diagnostic -> fresh evidence -> one
  coherent patch;
- raw measurements outrank classifiers;
- restart the companion after Python changes before runtime judgment;
- preserve network privacy; never request or expose addresses;
- meaningful fixes update durable memory in the same work.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:HANDOFF:BEGIN -->
## Immediate ADB diagnostic note

A development patch aligns `tools/probe_adb_wireless_recovery.py` with the
accepted D-053 recovery sequence on Linux. The Linux companion itself was
healthy when the onn showed "Companion unavailable"; ADB and companion reachability
remain separate layers. After installing the probe patch, run it once and use
its sanitized recovery classification/log as the next evidence. Runtime
validation is pending until that run completes.

<!-- PRIVYHUB_ADB_RECOVERY_PROBE_LINUX_PARITY_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:HANDOFF:BEGIN -->
## Immediate ADB resume point

Do not spend more time swapping ADB versions or assuming the Opal's radio split
permanently blocks wireless ADB. The current development probe v4 tests the
stale-ephemeral-port hypothesis: reuse a privately known onn host, find the
current listening ADB TLS endpoint on that host only, authenticate with the
existing pairing, and refresh the private cache. Production installer parity is
intentionally deferred until this probe is runtime validated.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:HANDOFF:BEGIN -->
## Immediate ADB resume point — v5

V4 automatic ephemeral-port recovery failed, but manual local `adb connect` to
the current endpoint succeeded, so pairing/reachability are healthy. Install and
run the v5 diagnostic while the onn is still connected so it can seed the private
host and measured ephemeral-range cache. On a later stale endpoint it scans only
that host/range. If that still fails, the probe prompts for repair/re-pair and
retries once. Do not promote this into `build_install_onn.ps1` until runtime
validated.

<!-- PRIVYHUB_ADB_EPHEMERAL_PORT_RECOVERY_V5_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:HANDOFF:BEGIN -->
## Immediate ADB resume point — endpoint debug

Run `python3 ./tools/probe_adb_wireless_recovery.py --debug-endpoints` locally.
The terminal intentionally shows literal host/port selections; the normal log
remains redacted. Use the terminal evidence to identify whether the wrong host,
wrong cached port, wrong scan range, missed open port, or failed ADB validation
is responsible. Do not promote the v5 recovery into `build_install_onn.ps1` yet.

<!-- PRIVYHUB_ADB_ENDPOINT_DEBUG_V6_2026_09_15:HANDOFF:END -->

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:HANDOFF:BEGIN -->
## Immediate ADB resume point — watch known current port

Run the recovery probe with `--debug-watch-port <known-current-port>` locally.
Inspect only the WATCH lines: in-range status, scheduled batch, and OPEN versus
CLOSED/UNREACHABLE. Do not paste literal endpoint values into durable/shareable
logs. Use the result before changing the scanner or pairing logic again.

<!-- PRIVYHUB_ADB_ENDPOINT_WATCH_V7_2026_09_15:HANDOFF:END -->
