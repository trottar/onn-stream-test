---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: e65e8f89604ce325e6e3e0537d0287070b8996c5
---

# Current Handoff

Continue PrivyHub from pushed commit `e65e8f89604ce325e6e3e0537d0287070b8996c5` on `main`. Treat
`L:\Projects\onn-stream-test` as authoritative between checkpoints.

Phase A emulator work is COMPLETE and checkpointed. The working tree was clean
after push.

## Runtime state to preserve

- native game capture/encode/transport/decode is stable;
- process-specific game audio is stable;
- PHI1 v1 and four ViGEm/XInput slots are runtime validated;
- Android P1-P4 assignment and RetroArch ports 1-4 are runtime validated;
- 1P/2P regressions passed;
- Crash Bash and CTR four-player PS1 Port-1 multitap passed;
- A8 named input profiles work for Players 1-4;
- Save/Load/Pause/Resume/End, cheats/mods and library behavior passed;
- wireless ADB recovery is runtime validated.

NES and Genesis had no local A9 fixtures. They are supported/configured but not
runtime validated and should be tested when real content is later added.

## Authoritative next roadmap

Use `docs/ROADMAP.md` v2.

Immediate sequence:

```text
Phase B1 existing-diagnostics inventory
        ↓
unified diagnostic schema + health snapshot
        ↓
GUI Diagnostics / Self-Test / sanitized bundle
        ↓
Sunshine/Moonlight dependency inventory
        ↓
legacy removal
        ↓
native-only regression
        ↓
clean-native checkpoint
```

Then Phase C adds explicit stream profiles and adaptive bitrate driven by
end-to-end path measurements, not GL-iNet WAN speed for local streaming.

VOD cover art/metadata is Phase D. Resource/Linux work is Phase E. OpenBIOS is a
non-blocking Phase F portability experiment and must preserve the current
compatibility BIOS path. Broader smart-home/client expansion is Phase G.

## Engineering rules

Never ask for IP addresses. Prefer durable diagnostics. Raw measurements beat
incorrect classifiers. Preserve stable subsystems. Fail closed. Update
`docs/memory/` with every meaningful result.

## Active B1.1 handoff — diagnostics inventory

Phase B has started. The first step is diagnostic-only.

Run:

`python .\tools\probe_b1_diagnostics_inventory.py`

Return:

`Get-Content .\logs\diagnostics\b1_diagnostics_inventory.txt`

The probe inventories current diagnostic producers/consumers, schemas, harness
modes, runtime-log families, privacy behavior, Android diagnostic surfaces and
common-schema gaps without reading/logging network-address values. Use the fresh
inventory to design B1.2; do not replace the existing one-command SHARE_ME
harness unless evidence shows it should be superseded.

## B1.2 handoff

B1.1 confirmed the common health contract is absent.

Install/run the B1.2 health-model foundation and return:

`Get-Content .\logs\diagnostics\b1_health_snapshot.txt`

The new model is deliberately not yet exposed by the companion HTTP API. It is
validated first as a pure adapter over existing companion/Games status and
existing host telemetry. If real runtime output is correct, the next coherent
patch integrates a read-only health endpoint and then the Android GUI consumer.

Resource fields are intentionally future-proofed for Phase E, but no benchmark
thresholds/hardware tiers are guessed in B1.

## B1.3 active handoff

B1.2 runtime model is validated.

Install/restart companion for the B1.3 read-only health endpoint, then run:

`python .\tools\probe_b1_health_endpoint.py`

Return:

`Get-Content .\logs\diagnostics\b1_health_endpoint.txt`

The endpoint must preserve the B1.2 schema/privacy behavior and recover
last-session host telemetry even after the required companion restart. No new
resource sampler or benchmark thresholds are allowed.

## B1.4 active handoff

B1.3 endpoint runtime validation passed.

Run the client-feedback source-context audit:

`python .\tools\probe_b1_client_feedback_source_context.py`

Return:

`Get-Content .\logs\diagnostics\b1_client_feedback_source_context.txt`

Do not implement Android feedback before inspecting this result. The audit is
specifically checking whether the current native-stream activity already has
suitable metrics, scheduling and network primitives that can be reused without
creating another hot loop.

## B1.5 active handoff

Install/build/restart B1.5. Launch a game and keep it running until at least two
2-second client-health reports can arrive, then run:

`python .\tools\probe_b1_client_feedback_runtime.py`

Return:
`Get-Content .\logs\diagnostics\b1_client_feedback_runtime.txt`

## B1.6 active handoff

B1.5 client feedback transport is runtime validated. Decoder classification is
not yet accepted because the rule may be overly sensitive to stale-output
drops.

Keep a known-good game running and execute:

`python .\tools\probe_b1_decoder_stale_semantics.py`

Return:

`Get-Content .\logs\diagnostics\b1_decoder_stale_semantics.txt`

Do not patch the decoder/streaming path. The probe compares receive/render
cadence, stale share, decoder drops, overflow, queue depth, timing and FEC across
multiple feedback intervals. No threshold or classifier change is applied by the
probe.

## B1.7 active handoff

B1.6 established that stale outputs alone are not decoder-local failure.

Install B1.7, restart the companion so the updated health model is loaded, keep
a known-good game running, then execute:

`python .\tools\probe_b1_decoder_classifier_runtime.py`

Return:

`Get-Content .\logs\diagnostics\b1_decoder_classifier_runtime.txt`

Expected stale-only intervals:
- decoder health healthy;
- event `VIDEO-DECODER-LOW-LATENCY-SHEDDING`.

Direct decoder-local drop/overflow rules remain degraded and are covered by
deterministic fixtures.

## B1.8 active handoff

B1.7 decoder classifier validation passed.

Run:

`python .\tools\probe_b1_gui_retention_context.py`

Return:

`Get-Content .\logs\diagnostics\b1_gui_retention_context.txt`

The audit does not delete anything. It identifies the exact Android GUI
integration surface, confirms the health endpoint/self-test inputs, and measures
which runtime diagnostic directories actually need bounded retention before the
production GUI/retention patch.

## B1.9 active handoff

Install/build the Diagnostics GUI + retention foundation.

On onn:
1. open PrivyHub Settings;
2. choose Diagnostics;
3. confirm the screen loads;
4. press REFRESH;
5. press RUN SELF-TEST.

On host, run the B1.9 runtime probe and retention dry-run. Return:

`Get-Content .\logs\diagnostics\b1_gui_retention_runtime.txt`

and

`Get-Content .\logs\diagnostics\b1_retention_plan.txt`

No retention apply should be run yet. Review the actual candidates before any
deletion.


## B1.10 active handoff

B1.9 GUI is runtime validated. Do not change or re-debug the GUI unless new evidence appears.

Retention B1.9 dry-run: forward 322.048 MiB -> only 8.870 MiB eligible -> projected 313.178 MiB with `blocked=True`; reverse/debug-bundle families are below cap. Do not run retention `--apply`.

Run B1.10 protected-footprint audit and return only:
`Get-Content .\logs\diagnostics\b1_retention_blocker.txt`

Use its raw reason/extension/size measurements to define the next policy.

## B1.11 active handoff

Install the retention-rule refinement and run the dry-run validation.

Return:

`Get-Content .\logs\diagnostics\b1_retention_rule_runtime.txt`

and

`Get-Content .\logs\diagnostics\b1_retention_plan.txt`

Do not use `--apply` yet. Expected: forward retention is no longer blocked and
at least one old `pktmon_full.txt` is eligible while newest-minimum protection
remains intact.

## B1/B2 completion-gap audit active

B1.12 retention apply succeeded with zero failures.

Run:

`python .\tools\probe_b1_b2_completion_gaps.py`

Return:

`Get-Content .\logs\diagnostics\b1_b2_completion_gaps.txt`

Do not start B3 until this audit confirms which roadmap requirements remain.

## B1/B2 exact completion source-context active

Run:

`python .\tools\probe_b1_b2_completion_source_context.py`

Return:

`Get-Content .\logs\diagnostics\b1_b2_completion_source_context.txt`

The probe is diagnostic-only and redacts address-like values from emitted source
context. Use the result to design one coherent B1/B2 completion patch without
duplicating already-generic Self-Test coverage.

## B1.13 completion implementation active

Install/build/restart and validate the B1/B2 completion patch.

Expected new APIs:
- GET `/diagnostics/health` includes bounded `event_history`;
- POST `/diagnostics/self-test`;
- POST `/diagnostics/bundle`.

On onn:
- Diagnostics REFRESH should show Recent Events;
- RUN SELF-TEST should include storage/ADB/emulator_runtime dedicated checks;
- COLLECT DIAGNOSTICS should create `SHARE_ME.zip`.

Return:
`Get-Content .\logs\diagnostics\b1_b2_completion_runtime.txt`

If runtime validation passes, record B1/B2 complete and begin B3
Sunshine/Moonlight dependency inventory.

## B2 GUI action-feedback polish pending visual validation

B1/B2 diagnostics correctness is runtime validated.

Install/build the UI-only action-feedback polish, then press:
- RUN SELF-TEST: button should immediately show `RUNNING...`;
- COLLECT DIAGNOSTICS: button should immediately show `COLLECTING...`;
- REFRESH: button should immediately show `REFRESHING...`.

Normal labels must return on completion/failure.

Return:
`Get-Content .\logs\diagnostics\b1_b2_gui_action_feedback.txt`
plus whether the immediate label change was visible on the onn.

## B3 Sunshine/Moonlight dependency inventory

Run `python .\tools\probe_b3_sunshine_moonlight_inventory.py` and return `Get-Content .\logs\diagnostics\b3_sunshine_moonlight_inventory.txt`. This is read-only and performs no deletion or system-state change.

## B3.1 active legacy-edge trace

Run:
`python .\tools\probe_b3_active_legacy_edge_trace.py`

Return:
`Get-Content .\logs\diagnostics\b3_active_legacy_edge_trace.txt`

The probe is read-only and focuses on:
- exact `games.py -> StreamManager` method calls and enclosing functions;
- exact Android Moonlight/com.limelight functions and call sites;
- manifest package query;
- current-tree references to legacy setup/runtime artifacts;
- grouped runtime/download/script footprint;
- previous B3 zero system-state evidence.

Do not start B4 removal until this focused trace is inspected.

## B4.1 exact Games source-context audit

The prior B4.1 installer failed before modification because one generated
multi-line text anchor did not match exact local `games.py` formatting.

Install/run the diagnostic-only exact-context probe and return:

`Get-Content .\logs\diagnostics\b4_1_games_source_context.txt`

Do not retry the previous B4.1 removal ZIP.

The next B4.1 production patch must be generated from the captured AST spans and
exact context rather than inferred anchors.

## B4.1 v2 AST-span server-edge removal

Install B4.1 v2 only; do not use the original B4.1 ZIP.

After install:
1. restart companion;
2. launch one normal representative game from the onn;
3. keep the native stream active;
4. confirm picture/audio/controller;
5. run:
   `python .\tools\probe_b4_1_server_legacy_edge_runtime.py --require-active`
6. return:
   `Get-Content .\logs\diagnostics\b4_1_server_legacy_edge_runtime.txt`

`stream_manager.py` and Sunshine artifacts are intentionally retained through
this test.

## B4.2 exact Android source-context audit

B4.1 passed runtime validation.

Install/run the diagnostic-only B4.2 context probe and return:

`Get-Content .\logs\diagnostics\b4_2_android_source_context.txt`

No Android build occurs in the context probe. No production source changes.

The next production patch will be generated from exact MainActivity function
blocks/call sites and exact AndroidManifest context.

## B4.2 Android edge runtime validation

After installing/building B4.2, launch one representative game normally from
the onn. Confirm native fullscreen, picture, audio and controller input, and
confirm there is no Moonlight/Streaming Host prompt.

While the game is active run:
`python .\tools\probe_b4_2_android_legacy_edge_runtime.py --require-active`

Return:
`Get-Content .\logs\diagnostics\b4_2_android_legacy_edge_runtime.txt`

Then run an orphan-reference audit before artifact deletion.

## B4.3 orphan-reference audit

B4.2 runtime validation passed.

Install/run the diagnostic-only B4.3 probe and return:

`Get-Content .\logs\diagnostics\b4_3_orphan_reference_audit.txt`

Do not remove helper definitions, stream_manager.py, Sunshine/Moonlight
runtime/downloads, or scripts until this result is reviewed.

## B4.4 code-orphan cleanup

Install B4.4, then run the standard Android build/install. Restart the companion
after `stream_manager.py` deletion to prove clean startup without the legacy
module.

Launch one representative game, confirm picture/audio/controller and native
fullscreen, leave it active, then run:

`python .\tools\probe_b4_4_code_orphan_cleanup_runtime.py --require-active`

Return:
`Get-Content .\logs\diagnostics\b4_4_code_orphan_cleanup_runtime.txt`

If confirmed, next capture exact hashes for physical legacy artifact groups.

## B4.5 physical legacy hash manifest

B4.4 runtime validation passed.

Install/run the diagnostic-only B4.5 probe and return:
`Get-Content .\logs\diagnostics\b4_5_physical_legacy_hash_manifest.txt`

The full per-file deletion predecessor is:
`logs/diagnostics/b4_5_physical_legacy_hash_manifest.json`

Do not delete remaining legacy artifacts until this evidence is reviewed.

## B4.6 physical legacy cleanup

Install B4.6, launch one representative game and keep it active, then run `python .\tools\probe_b4_6_physical_legacy_cleanup_runtime.py --require-active` and return `Get-Content .\logs\diagnostics\b4_6_physical_legacy_cleanup_runtime.txt`. If ADB remains unavailable, device Moonlight verification remains pending before/with B5.

## B4.6 v2 correction

B4.6 v1 failed before modification because its local manifest helper encoded
canonical separators differently from B4.5.

Use only:
`privyhub_b4_6_physical_legacy_cleanup_02_2026-09-11.zip`

No new B4.5 evidence capture is required.

## B4.6 v3 correction

B4.6 v1 and v2 both failed before modification.

v1: canonical hash separator mismatch.
v2: known RetroArch non-target regexes were over-escaped.

Use only:
`privyhub_b4_6_physical_legacy_cleanup_03_2026-09-11.zip`

No new B4.5 probe is required because neither failed installer modified state.

## B4.7 device Moonlight package check

B4.6 project cleanup is runtime confirmed.

Run the diagnostic-only B4.7 package check. It privately resolves the existing
paired onn using the same recovery pattern as build_install_onn.ps1, verifies
PrivyHub is present, then checks only `com.limelight`.

Return:
`Get-Content .\logs\diagnostics\b4_7_device_moonlight_package_check.txt`

If absent, proceed directly to B5. If installed, remove only that package and
verify absence before B5.

## B4.8 device Moonlight removal

B4.7 confirmed `com.limelight` is installed on the correct paired onn.

Run:
`python .\tools\remove_b4_8_device_moonlight_package.py`

Return:
`Get-Content .\logs\diagnostics\b4_8_device_moonlight_removal.txt`

Success requires Moonlight absent afterward and PrivyHub still present.
Then begin B5 native-only regression.

## B4.8 final verification correction

The Moonlight uninstall command succeeded and the first action observed
Moonlight absent, but its `pm path` verifier falsely mapped missing-package exit
status to `PACKAGE_QUERY_FAILED`.

Do not uninstall again.

Install/run the B4.8 final verifier and return:
`Get-Content .\logs\diagnostics\b4_8_device_moonlight_final_verify.txt`

If it confirms PrivyHub present + Moonlight absent, B4 is complete and B5 begins.

## B5 native-only regression

B4 is complete.

Install/run the B5 interactive regression harness. Use one representative game.
The harness records objective stream/source/save-state/teardown evidence and asks
for explicit confirmation of picture, audio, controller, pause/resume, Load,
and one known cheat/mod/profile path.

On PASS it writes durable B5 evidence and advances memory to B6.

Return:
`Get-Content .\logs\games\b5_native_only_regression.txt`

## B6 next

B5 is runtime validated after classifier correction. No gameplay rerun is
required.

The B5 false negative was limited to the over-strict post-profile native-active
gate. Session diagnostics proved full decoder continuity through the native
client lifetime and clean final teardown.

Proceed with B6 clean-native repository audit/checkpoint/push.

## B6 repository audit

B5 is runtime validated. Install/run the B6 diagnostic-only repository audit.
Do not stage or commit anything yet.

Return:
`Get-Content .\logs\diagnostics\b6_clean_native_repository_audit.txt`

If classified ready, build the final B6 checkpoint package from the exact
reported status list, update root ROADMAP.md, validate, stage exact scope,
commit and push.

## B6 audit v2

B6 audit v1 failed before modification on an over-strict working ROADMAP hash
gate. No audit log was produced because the probe was never installed/run.

Use only `privyhub_b6_clean_native_repository_audit_02_2026-09-11.zip`.

Return:
`Get-Content .\logs\diagnostics\b6_clean_native_repository_audit.txt`

## Phase C handoff

Phase B is complete/checkpointed/pushed.

Current Games streaming baseline:
Windows Graphics Capture -> H.264 NVENC -> RTP-sized UDP + 8+1 XOR FEC ->
Android hardware AVC decode.

Sunshine/Moonlight are not active product dependencies. B5 native-only
regression and B6 repository/build audit are complete.

Next: C1 explicit stream profiles. Preserve the validated 720p60 behavior while
making the currently implicit stream constants named and inspectable.


## Accepted roadmap after Phase B

Phase C remains next; start with C1 explicit stream profiles.

Future sequence is now:
D media/VOD/Live TV cleanup -> E Linux migration -> F Linux PS1-and-below
optimization/resource characterization -> G user-content import + N64/GameCube/
PS2 -> H home/client/plugin expansion -> I local/optional-cloud intelligence.

The HP EliteDesk 805 G6 is the Linux reference prototype, not the minimum target.
Prototype 2 is selected only after Phase F evidence.

OpenBIOS is retired from the roadmap. Required game firmware/content is
user-supplied through the future G0 import boundary.

Live TV is not considered finished: Phase D includes channel normalization,
identity/deduplication, EPG matching/cache/timezone diagnostics, and guide UX.

AI/home work stays local-first. External API providers are explicit opt-in and
subject to data minimization, no-silent-fallback, and local action validation.
