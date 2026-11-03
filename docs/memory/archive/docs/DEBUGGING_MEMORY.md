# PrivyHub Debugging Memory / Durable Rules

This file is intentionally kept in the repository so future debugging work does not depend on chat memory.

## Source of truth

- The local working tree at `L:\Projects\onn-stream-test` is authoritative between checkpoints.
- GitHub is reference/history unless the user explicitly says otherwise.

## Reuse proven infrastructure

Do not rewrite working infrastructure during unrelated debugging.

Networking:

1. Android stores the companion host.
2. The onn initiates the request to the companion.
3. The companion learns the live client address from the request.
4. Games/native streaming uses that live client address.

Therefore:

- do not ask the user to paste IP addresses;
- do not add a second hard-coded onn address;
- do not invent parallel mDNS/history-based endpoint discovery;
- ADB development transport is separate from production endpoint routing.

Controller/A8:

- Android PHI1/XUSB transport is validated and remains unchanged.
- Windows ViGEm is validated and remains unchanged.
- PS1 Digital vs DualShock remains a separate existing feature.
- A8 named gameplay profiles belong between canonical XUSB and RetroPad.
- Save / Load / Pause / End are not gameplay-profile mappings.

## Canonical debug entry point

Game/video:

```powershell
.\tools\run_privyhub_debug.ps1 -Mode GameSmear
```

Transport history:

```powershell
.\tools\run_privyhub_debug.ps1 -Mode TransportHistory
```

Audio baseline history:

```powershell
.\tools\run_privyhub_debug.ps1 -Mode AudioHistory
```

For each mode, ask the user for the single resulting `SHARE_ME.zip`, not a long list of commands/files.

## Existing diagnostic infrastructure

Game diagnostics:

- `logs/games/save_state_probe.txt`
- `logs/games/retroarch_control_probe.txt`
- `logs/games/native_video_alpha.log`
- `logs/games/decoder_sessions/*.json`
- `logs/games/host_telemetry/*.json`
- `logs/games/audio_timing/*.json`
- `logs/games/capture_diagnostics/*`
- `tools/collect_game_session_diagnostics.py`
- `logs/games/latest_game_diagnostic_bundle.txt`

Transport diagnostics:

- `logs/transport_probe`
- `logs/transport_reverse`
- `logs/transport_loopback`

Never request raw PktMon text/ETL when privacy-safe summaries answer the question.

## Current investigation checkpoints

### Screen smear

- Severe smear correlated with severe RTP/AU damage.
- Host capture/encoding was healthy.
- Android-local UDP loopback was clean.
- onn-only reboot did not materially change external-path loss/bursting.
- GL-iNet reboot removed forward synthetic packet loss in one run, though burst/gap timing remained.
- A subsequent game run no longer visibly smeared.
- Treat the catastrophic smear blocker as mitigated; do not reopen it unless fresh evidence requires it.

### A8

- A8.1 named input profile schema / CRUD / assignment backend: runtime validated.
- A8.2 RetroArch adapter installer attempt failed **before modification** because its expected-state verifier was too brittle.
- Do not treat that failed A8.2 installer as a source modification.
- Resume A8.2 only after the current game-audio regression is understood or fixed.

### Game audio regression

A4 requirement remains:

> TV gets game audio; PC should not duplicate audible game audio.

Production A4 process-loopback uses temporary relative session attenuation plus digital gain compensation.

Fresh silent-audio evidence showed:

- Windows capture/sender active;
- Android audio reception/playback active;
- no send/write errors explaining silence;
- compensated audio amplitude near silence;
- `local_output.original_volumes` already at approximately 1% before the helper's additional relative attenuation;
- the current helper run reported `restored: true`, restoring to that already-low starting value.

Do **not** conclude from that one run that a failed helper restore caused the low baseline.

Use `AudioHistory` to determine:

1. the first retained audio log with a low starting baseline;
2. the immediately preceding baseline;
3. whether the preceding helper log reports clean final/restored state or evidence consistent with abnormal termination.

Do not remove A4 PC-silencing behavior merely to restore TV volume.

## Patch discipline

Before production changes:

1. inspect exact current source/context;
2. determine exact expected pre-patch state;
3. make one coherent logical change;
4. validate actual generated/installed output;
5. package a verified ZIP installer;
6. runtime/E2E validate before calling the stage complete.

Prefer a diagnostic-only probe when the architecture or cause is still uncertain.
## September 9 A4 root-cause checkpoint — v3

This is the authoritative A4 debugging checkpoint after the failed v2 orphan-recovery attempt.

### Architecture reconstructed from repo/history

Normal game stop is already correct:

```text
Games stop
→ EmulatorManager.stop()
→ SAVE_FILES + targeted WM_CLOSE (+ network QUIT fallback)
→ NativeStreamManager.end_game_session()
→ NativeSessionIO.stop()
→ NativeAudioStreamer.stop()
→ CTRL_BREAK_EVENT to PrivyHubProcessAudio.exe
→ helper restores exact Windows session volume/mute
```

`PrivyHubProcessAudio.exe` is intentionally launched with `CREATE_NEW_PROCESS_GROUP`.

The missing ownership edge was in `privyhub_service.py`: its top-level `finally` did not shut down plugins. Therefore companion Ctrl+C/exit during an active game could orphan plugin-owned RetroArch/native-stream/audio processes.

Fresh runtime evidence:

```text
companion localhost:8765 unavailable
PrivyHubProcessAudio.exe still alive
Managed RetroArch target alive: False
```

The v2 recovery process tried to send `CTRL_BREAK_EVENT` from a new unrelated Python process and Windows returned:

```text
WinError 87: The parameter is incorrect
```

This does **not** invalidate the normal `NativeAudioStreamer.stop()` design. The normal owner retains the actual `Popen`/process-group relationship; the later recovery process does not.

### Dead-target orphan rule

If an orphan helper's target RetroArch process is still alive:

- fail closed;
- do not force-kill;
- preserve the possibility of live mixer restoration.

If all of the following are true:

- companion is not running;
- exactly one process-audio helper exists;
- its image is exactly the project-local helper binary;
- its status identifies the target;
- the target RetroArch PID is already dead;

then exact termination of that helper is permitted. There is no live target mixer session left for the helper to restore, and leaving it running provides no recovery value.

Legacy mixer repair then occurs on the next managed RetroArch session using the established retained history (`1.0 -> 0.01`).

### Companion lifecycle repair

Patch `privyhub_service.py` to call plugin shutdown in its `finally`.

Games shutdown must reuse the existing `handle_post("stop", "")` lifecycle. Do not create a second game-stop implementation.

### Crash-safe A4 mixer repair

Process-audio v0.25 persists exact pre-suppression volume/mute plus expected suppressed values before attenuation.

Recover only when the next live session still matches the stored suppressed state.

### Failed-v2 file-state note

`privyhub_a4_audio_lifecycle_recovery_v2` failed before changing production source, but its installer had already copied:

```text
tools/recover_orphan_game_session.py
```

into the project before the failure. Therefore the exact pre-v3 local state includes that v2 recovery tool. Future installers must not falsely call that state completely unmodified.

### ZIP durable-memory invariant

Every delivered PrivyHub ZIP must:

- update this durable repository memory (or its explicitly named successor);
- include the updated memory in the package;
- set `durable_memory_updated: true` in the manifest;
- validate that invariant before delivery.

Do not deliver a ZIP that omits the memory checkpoint.

### Roadmap

- A7: complete/runtime validated.
- catastrophic screen smear: mitigated; transport pathology deferred unless it recurs.
- A8.1: complete/runtime validated.
- A8.2: pending; prior installer failed before production modification.
- A4 audio/lifecycle: current blocker.
- Resume A8.2 immediately after the integrated A4 audio/lifecycle E2E probe passes.


## September 9 A4 installer compatibility checkpoint — v4

`privyhub_a4_audio_lifecycle_recovery_v3` passed all exact-state checks and source patcher self-tests, then failed at its backup stage because the installer called:

```text
[System.IO.Path]::GetRelativePath(...)
```

The development PC's PowerShell/.NET Framework does not expose that API.

Important state distinction:

- no production source/runtime file had been written by the v3 patch installer when this failure occurred;
- v3 orphan cleanup runs before the backup/write stage, so its dead-target helper cleanup may already have occurred;
- `tools/recover_orphan_game_session.py` remains the exact file left by the earlier failed v2 attempt until a successful replacement installer writes v3/v4 tooling.

v4 changes only installer compatibility relative to v3:

- use a project-root-validated `GetFullPath` + `Substring` helper for backup-relative paths;
- do not use `[System.IO.Path]::GetRelativePath` in PrivyHub installers unless PowerShell/.NET compatibility has first been established.

The production A4 repair remains:

```text
companion finally
→ plugin shutdown
→ existing Games stop
→ EmulatorManager graceful stop
→ native session stop
→ audio CTRL_BREAK restoration
```

plus process-audio v0.25 crash-safe mixer recovery.

### Installer compatibility durable rule

PrivyHub ZIP installers must target the actual Windows PowerShell environment in the prototype.

Avoid APIs introduced only in newer .NET runtimes when an equivalent PowerShell-5-compatible implementation is straightforward.

Every installer must continue to distinguish:

- FAILED BEFORE MODIFICATION
- ROLLED BACK
- INSTALLED SUCCESSFULLY

Runtime side effects that intentionally occur before file modification (such as a verified dead-target orphan cleanup) must be reported separately from project-file modification state.


## September 9 A4 E2E probe bug checkpoint — v5

The first `probe_a4_audio_lifecycle_recovery.py` runtime attempt produced this user-confirmed result before its diagnostic failure:

```text
TV game audio audible: yes
PC duplicate game audio effectively silent: yes
```

The probe then raised:

```text
RuntimeError: No fresh audio timing log was created
```

This was a probe implementation error.

### Correct process-audio log semantics

While process audio is running:

```text
data/games/native_stream/process_audio_status.json
```

is the live status source. It is written initially and refreshed while capture is active.

After controlled process-audio shutdown:

```text
logs/games/audio_timing/*.json
```

is the final historical session record.

Do not require a fresh `audio_timing/*.json` before shutdown.

### Correct A4 E2E ordering

```text
launch game
→ confirm TV audible / PC duplicate silent
→ read fresh live process_audio_status.json
→ validate v0.25 + baseline 1.0 + active recovery marker
→ shut down companion
→ Games stop lifecycle executes
→ RetroArch/audio helper exit
→ read fresh final audio_timing JSON
→ require final=true + restored=true
→ require recovery marker cleared
```

The failed first E2E probe's exception cleanup attempts to Ctrl+Break the companion it owns. Therefore it may already have consumed the one-time legacy recovery marker. Future validation must test the stable invariant (pre-suppression baseline restored to `1.0`) and must not require that one-time legacy marker to remain.

### Diagnostic discipline addition

Before adding a probe assertion about a log file, verify whether that file is:

- live/periodic state; or
- final/session-completion history.

A diagnostic must not fail a working subsystem merely because it sampled the wrong lifecycle artifact.

### ZIP memory invariant remains mandatory

Every PrivyHub ZIP update must include the updated durable memory/checkpoint and set:

```text
durable_memory_updated: true
```

in its manifest.
## September 9 A8.2 resume checkpoint

A4 audio/lifecycle recovery is now **runtime validated**.

Observed final invariants after normal game End:

```text
probe_version                = process_loopback_float_crash_safe_recovery_v0.25
final                        = True
original_volumes             = 1
restored                     = True
recovery_found               = True
recovery_applied             = True
recovery_source              = active_helper
recovery_marker_still_exists = False
helper_still_running         = False
```

The user also confirmed:

```text
TV game audio audible
PC duplicate game audio suppressed
```

Do not reopen A4 without new evidence.

### A8.2 verifier correction

The first A8.2 installer failed before modification because it rebuilt an
"exact A8.1" state from Git/checkpoint bytes. For PrivyHub, the validated local
tree is authoritative.

A8.1 already wrote:

```text
logs/games/a8_1_input_profiles_install.txt
```

containing exact post-install SHA-256 values for:

```text
companion/games/emulator_manager.py
companion/plugins/games.py
```

and:

```text
Storage probe: PASS
Storage restored: True
```

The corrected A8.2 installer must require the successful A8.1 receipt and
require the current files to match those exact receipt hashes. It must also
require the expected A8.1 markers and A8.1 documentation state.

Do not reconstruct authoritative local state from historical Git bytes when a
validated local installer receipt already records exact installed state.

### A8.2 scope

A8.2 changes only the RetroArch session gameplay-binding adapter in:

```text
companion/games/emulator_manager.py
```

It must not change:

- `companion/plugins/games.py` behavior;
- Android input transport;
- PHI1/XUSB;
- ViGEm;
- audio/video;
- PS1 Digital/DualShock device selection;
- Save/Load/Pause/End meta controls.

Runtime bindings remain session-only in:

```text
data/games/retroarch/config/privyhub-input.cfg
```

### Minor Game Session banner latency

During the post-A4 test, the Game Session/banner took a solid couple of seconds
to appear.

Record this as a **deferred UI-latency polish item**, not an A8.2 blocker.

Do not change the currently stable launch/pause/audio/controller lifecycle for
this symptom until A8 is complete or a dedicated latency diagnostic identifies
the measured stage responsible.

### Roadmap

- A7: complete/runtime validated.
- A8.1: complete/runtime validated.
- A4 regression repair: complete/runtime validated.
- A8.2 RetroArch adapter: active.
- A8.3 Android editor: pending.
- A8.4 per-game UI/diagnostics: pending.
- A9 emulator regression/checkpoint: pending.


## September 9 A8.2 CTR probe packaging failure — v4

The A8.2 CTR runtime-probe v3 ZIP was **not installed**.

Its `install.ps1` failed at PowerShell parse time:

```text
Missing closing ')' in expression.
Unexpected token ')' in expression or statement.
```

Root cause: the installer split an `-and` boolean expression across lines in a
form not accepted by the development PC's Windows PowerShell parser.

Because the script did not parse, it did not execute and did not modify project
files. The authoritative local pre-v4 state therefore remains the successful
A8.2 v2 state.

### Validation rule — mandatory for every ZIP

"Validate everything always" is now an explicit PrivyHub packaging rule.

Before delivery, validate every applicable layer that is available:

- exact expected local pre-state/hash assumptions;
- payload hashes;
- Python syntax/compile;
- deterministic fixture behavior for probes/transformers;
- failure-path restoration;
- idempotence/wrong-state rejection where practical;
- ZIP integrity and required contents;
- durable-memory update and `durable_memory_updated: true`;
- real component builds for production changes;
- PowerShell installer syntax against an actual PowerShell parser whenever a
  PowerShell runtime is available in the validation environment.

When the validation environment cannot run the exact target PowerShell version,
do not claim that it did. The user-side installation block must first invoke:

```text
System.Management.Automation.Language.Parser.ParseFile(...)
```

and refuse to execute the installer if any parse error is returned.

Do not let the installer itself be the first syntax check.

### CTR runtime probe

The corrected diagnostic requires `Crash Team Racing` by catalog search and has
no arbitrary title fallback.

This correction changes no production A8.2 code.


## September 9 A8.2 runtime evidence — physical A/B swap probe defect

CTR runtime evidence showed:

```text
A/B swap observed: False
Result: A8_RUNTIME_MAPPING_NOT_CONFIRMED
Input profile storage restored: True
```

The generated session config contained:

```text
input_player1_a_btn = "1"
input_player1_a_axis = "nul"
input_player1_b_btn = "0"
input_player1_b_axis = "nul"
```

Installed RetroArch XInput/Xbox autoconfigs consistently establish the normal
Xbox-to-RetroPad translation:

```text
input_b_btn = "0"
input_a_btn = "1"
input_y_btn = "2"
input_x_btn = "3"
```

This proves the A8.2 runtime probe's temporary profile was wrong for the test.
It created:

```text
RetroPad A <- physical B
RetroPad B <- physical A
```

which is the normal Xbox autoconfig, not a physical A/B gameplay swap.

A8.1/A8.2 semantics are explicitly:

```text
RetroPad target <- physical canonical XUSB source
```

The production adapter's source IDs remain correct:

```text
physical A = 0
physical B = 1
physical X = 2
physical Y = 3
```

Therefore the production A8.2 adapter is not changed for this finding.

The correct runtime probe profile for a physical A/B gameplay swap relative to
normal Xbox autoconfig is:

```text
RetroPad A <- physical A
RetroPad B <- physical B
```

which must generate:

```text
input_player1_a_btn = "0"
input_player1_b_btn = "1"
```

The corrected runtime probe now validates those generated session binds itself
in addition to asking for the observed CTR behavior.

### Packaging rule reinforcement

Probe-only packaging should prefer a Python installer when that permits the
installer to be executed end-to-end in the validation environment.

The final user PowerShell block must use absolute paths rooted at:

```text
L:\Projects\onn-stream-test
```

for ZIP, staging, installer, project root, and runtime probe.

Do not rely on PowerShell's current-location semantics for paths passed to .NET
APIs or subprocesses.

"Validate everything always" remains mandatory.


## September 9 A8.2 runtime root cause — controller launch order

Fresh CTR runtime evidence established:
- the temporary named profile was assigned;
- `privyhub-input.cfg` generated the intended physical A/B swap;
- `privyhub-session.cfg` retained the same explicit bindings;
- CTR still behaved unswapped;
- the RetroArch log showed configured `xinput` failed to initialise, then the
  two Xbox 360 controllers autoconfigured later;
- authoritative local `companion/plugins/games.py` showed
  `ensure_game_controller(client_ip)` ran only after
  `handle_post("launch", ...)` had already completed the emulator launch.

The production correction moves only the existing controller readiness call
before the normal launch call. Controller-preflight failure now fails closed
before game launch. If the subsequent normal launch fails, the prestarted
controller session is torn down and the original launch exception is re-raised.
The existing successful pause/handoff/library logic remains unchanged.

Intentionally unchanged:
- PHI1/XUSB transport;
- NativeControllerBridge report mapping;
- ViGEm VX360 implementation;
- A8 profile schema/mapping;
- RetroArch named-profile binding generation;
- Save/Load/Pause/End;
- Android;
- audio/video.

The A8.2 runtime probe now also classifies the matching fresh RetroArch log.
Runtime success requires:
`A/B swap observed: True`,
`Generated swapped RetroPad binds: True`,
`XInput startup fallback observed: False`,
`Result: A8_RUNTIME_MAPPING_OBSERVED`, and
`Input profile storage restored: True`.

A8.2 remains development-only until runtime/E2E passes.
"Validate everything always" remains mandatory.


## September 9 A8.2 assignment-boundary diagnostic

After the controller-preflight ordering fix, runtime evidence showed:

```text
A/B swap observed: False
Generated swapped RetroPad binds: True
XInput startup fallback observed: False
Xbox controllers autoconfigured: True
Result: A8_RUNTIME_MAPPING_NOT_CONFIRMED
```

This proves the ordering fix removed the XInput startup fallback but did not
make the A8 gameplay mapping observable in CTR.

The next diagnostic must measure the controller path boundary-by-boundary,
before making another production change.

### Boundary diagnostic order

Checkpoint 0 — no RetroArch/game:

```text
synthetic PHI1 A -> real NativeControllerBridge -> real ViGEm/XInput
synthetic PHI1 B -> real NativeControllerBridge -> real ViGEm/XInput
```

Expected canonical transport:

```text
PHI1 A -> XInput A
PHI1 B -> XInput B
```

A8 must not modify this transport layer.

Checkpoint 1 — still before RetroArch/game:

Use the production A8 profile generator for the temporary CTR profile and
record the generated explicit RetroArch assignment.

Expected physical A/B gameplay swap assignment:

```text
input_player1_a_btn = "0"
input_player1_b_btn = "1"
```

Checkpoint 2 — after normal Android -> companion -> RetroArch/CTR launch:

Measure actual XInput face-button state from the real Android/PHI1/ViGEm path,
then compare the post-launch `privyhub-input.cfg` and
`privyhub-session.cfg` assignments with the pre-launch snapshot.

The diagnostic classification should identify the first failing boundary:

```text
PRELAUNCH_TRANSPORT_FAIL
PRELAUNCH_ASSIGNMENT_FAIL
POSTLAUNCH_ANDROID_XINPUT_FAIL
POSTLAUNCH_ASSIGNMENT_CHANGED
POSTLAUNCH_XINPUT_STARTUP_FALLBACK
BOUNDARIES_PASS_GAMEPLAY_FAIL
BOUNDARY_END_TO_END_PASS
```

If the result is `BOUNDARIES_PASS_GAMEPLAY_FAIL`, the canonical transport,
pre-launch A8 assignment, post-launch Android/XInput path, and post-launch
session assignment all passed. The remaining fault is downstream inside
RetroArch/core input processing.

The diagnostic restores `input_profiles.json`, `privyhub-input.cfg`, and
`privyhub-session.cfg` byte-for-byte after the run.

### Packaging correction

`privyhub_a8_2_assignment_boundary_probe_v1` was rejected before modification
because its installer was built against reconstructed pre-state hashes instead
of the exact immediately preceding installed patch state.

Authoritative predecessor hashes are:

```text
tools/probe_a8_2_controller_preflight_source.py
0C7F807E348E2D7FB1234D261BE64F349F4BC1093333A6E72E309DE23DB72C90

tools/probe_a8_2_runtime_mapping.py
769D7AE725A3A3AEB8448D624980F078709C908C23700EBB666EF32F69AD4935

docs/DEBUGGING_MEMORY.md
E9CA4477F8D8FC52654A3F779F162D8EB871C6C307A0A8F01AAD3BCC75C60CF5
```

The corrected v2 installer is validated against those exact fixture bytes.

"Validate everything always" remains mandatory.


## September 9 A8.2 assignment-boundary probe v3

The v2 boundary probe produced:

```text
CHECKPOINT 0 canonical PHI1 -> ViGEm transport: PASS
CHECKPOINT 1 prelaunch A8 assignment: PASS
postlaunch privyhub-input.cfg retains swap: True
postlaunch privyhub-session.cfg contains swap: True
A8 input assignment unchanged: True
XInput startup fallback observed: False
Xbox controllers autoconfigured: True
Physical A capture: A
Physical B capture: A
Result: POSTLAUNCH_ANDROID_XINPUT_FAIL
```

The postlaunch physical-button classifier is not sufficient evidence of an
Android mapping defect because v2:

- unioned every face-button state seen over a three-second window;
- observed every newly-created XInput slot together;
- did not require a stable neutral state before each capture;
- computed per-slot measurements but did not log them.

Therefore the v2 `POSTLAUNCH_ANDROID_XINPUT_FAIL` classification is treated as
diagnostic-measurement ambiguity, not as a production root cause.

### v3 measurement correction

v3 changes only the diagnostic probe.

For the postlaunch checkpoint it now:

1. requires a stable neutral XInput face-button state;
2. asks for one physical A tap;
3. records the first actual XInput face-button transition, exact XInput slot,
   raw per-slot face state, and release;
4. waits for neutral again;
5. repeats the same one-tap measurement for physical B;
6. requires both taps to occur on the same XInput slot;
7. stops after assignment boundaries are classified.

The user does not need to start a race, load a save, repeatedly tap buttons, or
judge gameplay in this diagnostic. CTR may remain on any visible screen.

If all assignment boundaries pass, the result is:

```text
ASSIGNMENTS_PASS_READY_FOR_GAMEPLAY_TEST
```

Only then should a separate downstream RetroArch/core gameplay test proceed.

No production source, Android source, PHI1 mapping, ViGEm mapping, A8 profile
schema, or RetroArch config generation is changed by v3.


## September 9 A8.2 closure / A8.3 Android editor

### A8.2 final status

A8.2 RetroArch runtime adapter is **COMPLETE / runtime validated**.

The corrected assignment-boundary v3 result was:

```text
CHECKPOINT 0 PRE-RETROARCH CANONICAL TRANSPORT: PASS
CHECKPOINT 1 A8 ASSIGNMENT BEFORE RETROARCH/GAME: PASS
Physical A XInput slot: 0
Physical A press face buttons: A
Physical B XInput slot: 0
Physical B press face buttons: B
Same XInput slot for physical A/B: True
Android -> PHI1 -> ViGEm canonical A/B: PASS
Postlaunch privyhub-input.cfg retains swap: True
Postlaunch privyhub-session.cfg contains swap: True
A8 input assignment unchanged from prelaunch snapshot: True
XInput startup fallback observed: False
Xbox controllers autoconfigured: True
Result: ASSIGNMENTS_PASS_READY_FOR_GAMEPLAY_TEST
```

The subsequent CTR gameplay test confirmed the intended **BUTTON A / BUTTON B
remap works**.

Terminology correction is durable:

```text
Player 1 / Player 2
    = controller/player assignment

Physical A button / Physical B button
    = buttons printed on the physical controller

RetroPad A / RetroPad B
    = libretro virtual gameplay controls
```

Do not use ambiguous "A/B swap" wording when it could mean player assignment.

### A8.3 development patch

A8.3 adds an Android editor under:

```text
Game -> Options -> Input Profile
```

It uses only the already-validated A8.1 API:

```text
GET  /plugins/games/input-profiles
POST /plugins/games/input-profile-create
POST /plugins/games/input-profile-update
POST /plugins/games/input-profile-delete
POST /plugins/games/input-profile-assign
```

Editor capabilities:

- assign reusable profile per game;
- create;
- edit Player 1 / Player 2 gameplay mappings;
- rename;
- duplicate;
- reset explicit mapping;
- delete unassigned profile.

Mapping wording in the UI is explicit:

```text
RetroPad target <- Physical controller input
```

A8.3 intentionally does not change PHI1/XUSB, ViGEm, controller preflight,
A8.2 runtime generation, game lifecycle, Save/Load/Pause/End, audio, or video.

A8.3 is a development patch until onn UI + gameplay validation passes.


## September 9 A8.3 installer v1 rollback / v2 correction

The first A8.3 Android editor installation attempt transformed the real local
`MainActivity.kt` successfully and the installed-source probe passed every
A8.3 source/API check. The transformed file measured:

```text
MainActivity.kt SHA256:
C435A41B461B05DDE15C2055558674C7693AD4F3ACA5D381B56628E8B12133DD
source probe Result: PASS
```

The installer then failed while invoking Gradle because its `cmd.exe /c`
command string used incorrect quoting around `gradlew.bat`:

```text
'\"L:\Projects\onn-stream-test\PrivyHub\gradlew.bat\"' is not recognized...
```

The installer classified the attempt as `ROLLED BACK` and restored the
pre-A8.3 source/docs bytes. This was an installer command-construction defect,
not an Android source-probe failure.

A8.3 v2 keeps the exact already-probed Android transformation and changes only
the installation/build validation path plus this durable record.

v2 requires both deterministic Android source hashes:

```text
pre-patch MainActivity.kt
2F9F6A785C232F2515D2738952D6A7AC64B0C07EC72DD538E9ECCCB5669C0083

post-patch MainActivity.kt
C435A41B461B05DDE15C2055558674C7693AD4F3ACA5D381B56628E8B12133DD
```

The real Gradle Kotlin compile is now invoked through PowerShell's call
operator using the absolute `gradlew.bat` path, avoiding the failed nested
`cmd.exe` quoting pattern.


## September 9 A8.3 v3 dialog-list correction

A8.3 v2 installed and its source probe passed with:

```text
MainActivity.kt SHA256: C435A41B461B05DDE15C2055558674C7693AD4F3ACA5D381B56628E8B12133DD
Result: PASS
```

Runtime UI evidence then showed `Game -> Options -> Input Profile` opened but
contained no selectable options.

Root cause was deterministic Android UI construction in
`showGameInputProfileMenu()`: the dialog used both `.setMessage(...)` and
`.setItems(...)`, causing the message content to occupy the dialog content path
instead of the selectable profile list on the tested Android TV UI.

v3 is UI-only. It removes message content from that list dialog and moves the
current profile into the title. The source probe now asserts:

```text
input_profile_menu_has_items: PASS
input_profile_menu_has_no_message_content: PASS
current_profile_visible_in_title: PASS
```

No production controller, emulator runtime, backend API, save/load, audio, or
video behavior changes.


## September 9 A8.3 v4 directional permutation editor

User requirement refined from button-only remapping to a complete input-signal
permutation editor. Custom mappings must expose D-pad, face/shoulder buttons,
triggers, stick clicks, Start/Select, and all four directions of both analog
sticks. Duplicate physical sources or unmapped RetroPad targets are invalid;
Android displays invalid rows in red and disables Save until the mapping is a
complete one-to-one permutation.

Architecture remains transport-neutral: PHI1/XUSB and ViGEm are unchanged.
Directional analog tokens are converted only in the RetroArch session binding
adapter. Legacy A8.2 whole-axis profiles remain accepted.

Validated Default baseline must preserve RetroArch Xbox autoconfig, including:

```text
RetroPad A <- Physical B
RetroPad B <- Physical A
RetroPad X <- Physical Y
RetroPad Y <- Physical X
```

First generalized directional runtime test is Emperor's New Groove (PS1):

```text
RetroPad L2 <- Physical Right Stick Left
RetroPad R2 <- Physical Right Stick Right
RetroPad Right Stick Left <- Physical LT trigger
RetroPad Right Stick Right <- Physical RT trigger
```

Expected: right-stick horizontal rotates the camera; the displaced physical
triggers no longer own those camera directions in the custom profile; assigning
Default restores original controls.

A8.3 v3 selectable Input Profile list was runtime validated before this patch.


## September 9 A8.3 v4 runtime UI observation / v5 correction

After installing A8.3 v4:

- game cover art was briefly missing for most games immediately after the APK
  reinstall/restart, then repopulated without intervention;
- because A6 artwork loading is asynchronous and its `LruCache` is in-memory,
  this is recorded as a transient cold-cache observation, **not** a persistent
  A6 regression; do not alter A6 unless the loss persists on a later normal
  launch;
- `Options -> Input Profile` still exposed profile selection but the mapping UI
  was not reachable.

Inspection of the exact v4 generated Android block found two remaining
`AlertDialog` message/list collisions:

```text
showInputProfileActionsDialog:
    setMessage(...) + setItems(...)

physical-source chooser inside showEditInputProfilePlayerDialog:
    setMessage(...) + setItems(...)
```

These are the same UI construction defect fixed at the top-level dialog in v3.

A8.3 v5 is intentionally Android-UI-only:

- removes both remaining message/list collisions;
- adds direct `Edit Current Player 1 Mapping` / `Edit Current Player 2 Mapping`
  entries for the active custom profile;
- opens Player 1 mapping immediately after profile creation;
- leaves the v4 generalized directional backend/runtime adapter unchanged;
- leaves PHI1/XUSB, ViGEm, Save/Load/Pause/End, audio/video, and A6 artwork code
  unchanged.

The Emperor's New Groove PS1 E2E target remains:

```text
RetroPad L2 <- Physical Right Stick Left
RetroPad R2 <- Physical Right Stick Right
```

with the displaced physical trigger sources reassigned so the 24-endpoint
permutation remains one-to-one.


## September 9 A8.3 v6 editor presentation decision

User-approved mapping-editor presentation:

```text
Destination control
Current: familiar physical input
[ Change ]
```

Example:

```text
L2
Current: LT Trigger
[ Change ]
```

Do not expose `RetroPad target <- Physical source` implementation terminology
in the normal editor. Use familiar labels such as L2, R2, LT Trigger, RT
Trigger, Right Stick Left, etc.

Conflicts/unmapped rows remain red and Save remains disabled until the complete
24-endpoint mapping is one-to-one and valid.

This is an Android UI-only change. The v4 directional runtime/backend model and
v5 reachability fix remain intact.

Transient cover-art disappearance immediately after APK reinstall was observed
to recover without intervention. Treat as cold in-memory artwork-cache
repopulation unless a persistent later regression is observed; A6 artwork code
was not changed for A8.3.


## September 9 A8.3 v6 runtime UI success and v7 polish

The user confirmed the v6 simple Current/Change input editor works well. Treat
that row/change/save interaction as runtime-validated and preserve it.

Remaining UI terminology issue: v6 mixed PlayStation-style destination labels
(`L1/L2/R1/R2/Select`) with Xbox physical-source labels. v7 standardizes all
normal editor labels on Xbox terminology only:

```text
A B X Y / LB RB LT RT / L3 R3 / Back Start / D-pad directions / stick directions
```

v7 also adds unsaved working-copy sync buttons between Player 1 and Player 2.
Sync does not bypass validation or Save. Directional backend/runtime behavior
is unchanged. Emperor's New Groove PS1 right-stick camera E2E remains pending.


## September 10 A8.3 v8 popup conflict visibility

User requested that overlaps be visible before choosing a replacement input.
The Change popup now computes source ownership from the current player's unsaved
working mapping. Any source already used by another destination row is rendered
red before selection.

The row currently being edited does not make its own source red by itself. If
that source is also used by another row, it remains a real conflict and is red.
Red sources remain selectable to allow intentional multi-step swaps; Save is
still disabled until all duplicates/unmapped rows are resolved.

v8 is Android-UI-only. Directional backend/runtime, PHI1/XUSB, ViGEm, player
sync, Save/Load/Pause/End, audio/video, and A6 artwork are unchanged.
