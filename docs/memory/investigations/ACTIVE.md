---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Active Investigations

## A9 emulator-focused regression/checkpoint

Status: ACTIVE.

All A1-A8 work plus the four-player extension and representative Crash Bash 4P gameplay are runtime validated. Run one final regression across NES, SNES, Genesis, and an ordinary non-Crash-Bash PS1 title; recheck 2P/analog, direct launch, pause/resume, frozen preview, Save/Load, End, host coexistence, one cheat session, one mod session, one custom A8 input profile, and repository diff hygiene.

If the A9 runtime probe passes, inspect the repository audit it records, update final durable evidence, and create/push the clean Phase A checkpoint.

The earlier controller dropout is not active software work. It persisted once with multitap removed and did not reproduce with a replacement controller. Reopen only if representative controllers reproduce the failure.

## PS1 multitap library generalization

Status: ACTIVE. Crash Bash Port-1 multitap is validated; CTR demonstrates that one hard-coded game override is insufficient for a larger library. Target: per-game On/Off selector, Port 1 only, Port 2 always disabled, advisory checker from existing `max_players` metadata, no automatic activation. Exact source/candidate audit precedes production change.

## A9 NES/Genesis fresh-log identification

Status: ACTIVE but secondary. First A9 run marked NES and Genesis `<unknown>` despite user-confirmed normal direct launch/gameplay/analog/coexistence/End. Treat as probe-detection issue unless runtime evidence contradicts it. Fix/re-run after the PS1 multitap product gap is closed.

## Active: PS1 library-wide multitap usability

Current metadata cannot identify known four-player PS1 titles, so the checker is deferred. Production work is limited to a manual On/Off flag with Port 1 only. CTR is the next representative runtime validation. A9 remains pending after this product gap and the separate NES/Genesis probe-identification misses.

## Active: persistent wireless ADB target disappearance

Observed 2026-09-10 while installing the PS1 Multitap On/Off Android build: `build_install_onn.ps1` built the APK but failed at `[2/4]` because `adb devices` contained no online physical target. This failure has occurred before. Narrow hypothesis: the build tool lacks recovery for a previously paired Android TV whose `_adb-tls-connect._tcp` service is discoverable but not yet attached to the ADB server. Diagnostic-only audit captures exact local build-script hash/context, ADB version/server mDNS state, service-type counts, and device-state counts with all serials/endpoints redacted.

## ADB recovery audit v1 probe defect

The v1 diagnostic did not answer the wireless-ADB question because it failed
while locating ADB. Root cause is internal to the probe's double-escaped
`sdk.dir` regex. Corrected audit v2 is required before changing
`build_install_onn.ps1`. Persistent tooling hypothesis remains unchanged:
the build script currently lacks bounded mDNS/reconnect recovery when the ONN
transport drops from `adb devices`.

## Wireless ADB recovery — production patch active

The server-restart comparison still showed no mDNS TLS service and no transport.
Persistent recovery is therefore implemented in the build/install tool rather
than left as a manual setup step. Runtime validation of the patched script is
the active gate.

## Wireless ADB recovery investigation — CLOSED

Post-patch runtime classification `ADB_TARGET_ALREADY_ONLINE` with one online
transport and recovered mDNS service. The build/install recovery path is
validated. Reopen only on a new failure of the patched recovery logic.

## PS1 multitap library generalization — CLOSED

CTR runtime validation passed with manual Multitap On. Port 1 enabled, Port 2
disabled, all four controllers independent. Manual On/Off is sufficient for the
current four-player product ceiling. Metadata recommendation remains deferred
until metadata quality improves.

## A9 NES/Genesis fresh-log identification — ACTIVE / final Phase A gate

First A9 run already passed all other substantive stages. Fix only the
identification logic: when live status lacks usable game id/system/title, locate
the newest fresh RetroArch log whose `System:` line matches the expected family,
parse Game ID/Title/System from that log, and apply the existing XInput/fallback
checks. Rerun NES and Genesis only via finish mode.

## A9 NES/Genesis identity investigation — CLOSED AS INVALID TEST SETUP

The repeated `<unknown>` measurements did not come from launched NES/Genesis
sessions. The user clarified no games for those systems are currently installed
and the prompts were answered without launches. Therefore the prior identity
investigation was based on an invalid test setup, not a production failure.

Replacement: coverage-aware A9 finalizer. Zero library entries are skipped and
not claimed runtime validated.

## Phase A A9 — CLOSED / CHECKPOINT READY

Coverage-aware A9 returned
`PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS`.
All available-library regression requirements passed. NES and Genesis have no
local fixtures and remain declared unvalidated runtime coverage gaps.

No active emulator investigation remains for the Phase A checkpoint.

## Phase B1.1 — existing diagnostics inventory

Status: **ACTIVE**.

Narrow hypothesis: PrivyHub already has most required subsystem instrumentation,
but lacks one stable cross-subsystem event/health contract and aggregator.

Inventory before implementation:
- production telemetry producers;
- live-state vs final-session history;
- targeted probes;
- shareable bundle harness;
- privacy/redaction behavior;
- structured schema identifiers and key shapes;
- local artifact counts/retention pressure;
- Android diagnostic activities and any user-facing diagnostics surface;
- presence/absence of common `subsystem`, `severity`, `event_code`, `health`,
  measurement and classifier fields.

Do not change production behavior in B1.1. Fresh output:
`logs/diagnostics/b1_diagnostics_inventory.txt` plus JSON peer.

## Phase B1.2 — unified health/resource model foundation

Status: **ACTIVE**.

Implement the cross-subsystem model as a new, currently unintegrated companion
diagnostics module plus runtime probe. Do not modify native streaming behavior.

The first model must:
- consume existing `/status` and Games status;
- normalize existing stream/capture/audio/input/FEC state;
- reuse existing host telemetry for resource measurements;
- omit addresses, ports, PIDs, paths and titles from normalized output;
- keep unknown network/client-decoder coverage explicit;
- apply no Phase E hardware thresholds.

Fresh output:
`logs/diagnostics/b1_health_snapshot.txt` and JSON peer.

Only after the model is validated against real runtime state should it be wired
into the companion API and Android GUI.

## Phase B1.3 — read-only health endpoint

Status: **ACTIVE**.

Integrate the validated B1.2 model into the companion API without changing
streaming/session behavior.

Endpoint:
`GET /diagnostics/health`

Requirements:
- Games status obtained in-process;
- current host telemetry used when available;
- newest valid historical host telemetry may be used as `last_session` after
  companion restart;
- host-telemetry paths constrained under `logs/games/host_telemetry`;
- no new resource sampling;
- no addresses/ports/PIDs/paths/titles in normalized response;
- no capacity/profile-fit thresholds;
- runtime probe validates schema/components/privacy/resource provenance.

Next after endpoint validation: add client decoder/network feedback contract,
then GUI diagnostics.

## Phase B1.4 — Android client-feedback source context

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Narrow hypothesis: Android already computes most decoder/network measurements
needed by the unified diagnostics and future adaptive bitrate, and may already
contain a suitable scheduling/network primitive to publish a low-rate health
snapshot.

Probe exact current source for:
- native-stream metric counters;
- scheduler/cadence mechanisms;
- HTTP/JSON primitives;
- safe endpoint literals;
- lifecycle methods;
- exact hashes of Android/client and companion health source.

No production behavior changes. No new telemetry traffic.

## Phase B1.5 — Android client-health feedback

Status: **ACTIVE / DEVELOPMENT PATCH**.

Reuse the existing Android metrics tick; do not add another timer. Publish every
2 seconds with one in-flight request maximum. Server state is latest-only plus
one delta baseline. Runtime validation must prove fresh advancing feedback,
decoder/network normalization, bounded payload size, no privacy leakage, no new
resource sampler, and no persistent sample log.

## Phase B1.6 — decoder stale-output semantics

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Hypothesis:
The B1.5 rule `stale_output_drops > 0 => degraded` may be too sensitive because
stale-output rejection can be part of a low-latency decoder policy.

Targeted diagnostic:
capture at least 8 unique 2-second client-health intervals while a known-good
game runs, measuring rendered-frame delta, stale-output delta/share, receive
FPS, ordinary decoder drops, queue overflow/depth, receive→decode delay,
output-gap timing, FEC unrecoverable state and network dropped-frame state.

Do not invent a tolerated stale-drop count. Use the measured pattern to decide
whether the health classifier should distinguish low-latency shedding from
actual render degradation.

## Phase B1.7 — decoder classifier correction

Status: **ACTIVE / DEVELOPMENT PATCH**.

Change only the health classifier:
- stale-only shedding is informational;
- hardware-decoder absence remains degraded;
- ordinary decoder drops remain degraded;
- queue overflow remains degraded;
- stale counts/rendered/queued deltas remain measurements;
- no arbitrary threshold;
- no Android/client-feedback/network changes.

Runtime validation must observe at least one stale-only interval and confirm the
new event/health classification.

## Phase B1.8 — GUI/Self-Test + retention context audit

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Hypothesis:
The validated health endpoint is sufficient for a thin standalone Android
Diagnostics activity, while runtime diagnostic retention can be applied to
specific log families without touching curated/durable evidence.

Audit:
- exact MainActivity and diagnostics-activity source hashes;
- manifest diagnostic activities/export state;
- GUI/navigation token line numbers;
- live health endpoint schema/component shape;
- existing one-command debug harness and sanitized bundle;
- log-family counts/bytes/age;
- existing retention/cleanup markers.

No production behavior changes and no files are deleted.

## Phase B1.9 — Diagnostics GUI + retention foundation

Status: **ACTIVE / DEVELOPMENT PATCH**.

Production:
- standalone Android Diagnostics activity;
- one Settings navigation action;
- no new health endpoint/classifier/sampler;
- Android Self-Test consumes current health contract.

Retention:
- allowlisted families only;
- dry-run default;
- no automatic deletion;
- exact policy SHA required for future apply;
- durable memory and patch backups excluded;
- actual candidate plan must be reviewed before apply.

Runtime validation requires Android build/install, manual GUI check, health
endpoint probe, and retention dry-run. No runtime artifacts are deleted during
validation.


## B1.10 — Forward retention protected-footprint audit

Status: **ACTIVE / DIAGNOSTIC-ONLY**.

Hypothesis: the forward retention cap is unreachable because file-level protection is overbroad for one or more large raw transport artifacts.

Probe only the measured blocker: protected bytes grouped by reason/extension plus largest protected paths and raw-like/large files protected solely by summary extension. No deletions; production unchanged.

## Phase B1.11 — retention raw-name refinement

Status: **ACTIVE / DEVELOPMENT PATCH**.

One rule change:
- `pktmon_full.txt` bypasses summary-extension protection because B1.10 measured
  it as the dominant raw-capture storage class;
- newest-minimum protection still wins;
- all other `.txt` summary protection remains;
- failure-name protection remains;
- no automatic retention and no deletion during validation.

Success requires an unblocked forward dry-run projected at or below 256 MiB.

## B1/B2 completion-gap audit

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Question:
Which explicit B1/B2 roadmap requirements remain unimplemented after the
validated health endpoint, client feedback, Diagnostics GUI/Self-Test and manual
retention work?

Audit:
- common bounded event/ring history;
- GUI access to the sanitized diagnostics bundle;
- Self-Test coverage for storage/ADB where applicable;
- exact current source hashes.

No production source is changed and no logs are deleted.

## B1/B2 completion source-context audit

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Question:
What exact existing hooks should be reused to close the remaining B1/B2 roadmap
gaps without adding duplicate checks or parallel diagnostics infrastructure?

Inspect:
- Diagnostics activity button/layout/Self-Test methods;
- companion diagnostics routes;
- health-model/runtime-health/client-feedback integration points;
- existing sanitized bundle CLI/outputs;
- local ADB/storage-check candidates;
- event-history candidates.

No production source changes.

## Phase B1.13 — B1/B2 completion implementation

Status: **ACTIVE / DEVELOPMENT PATCH**.

One coherent diagnostics-only production change:
- bounded event ring;
- dedicated non-destructive Self-Test checks for storage, ADB/development and
  emulator/runtime prerequisites;
- one-click GUI sanitized bundle creation using the existing bundler;
- current health/event/version context included in the support ZIP.

Stable streaming, audio, controllers and game lifecycle are intentionally
untouched.

Runtime validation requires companion restart, Android build/install, host
completion probe and short GUI checks. B3 remains pending.

## B2 GUI action-feedback polish

Status: **ACTIVE / UI-ONLY POLISH**.

Diagnostics functionality is runtime validated. Improve only immediate visual
acknowledgement for asynchronous actions by changing the active button label
while busy and restoring it afterward.

No companion/API/health/event/bundle/retention/streaming changes.

## B3 — Sunshine/Moonlight dependency inventory

Status: **ACTIVE / DIAGNOSTIC ONLY**. Inventory exact current-tree and privacy-safe Windows system-state legacy dependencies/remnants. Classify every occurrence and protect validated native paths. B4 is blocked until this evidence is reviewed.

## B3.1 — Active legacy-edge trace

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Hypothesis:
The true B4 cut set is much smaller than the broad B3 static count and is
centered on Games `StreamManager`, Android Moonlight launch/visibility, and the
legacy artifact groups reachable from those edges.

The focused probe excludes archives/docs/runtime contents from the executable
reference graph, reports exact source hashes, traces `_stream` vs
`_native_stream` calls, maps Android legacy references to enclosing functions
and call sites, and groups Sunshine/Moonlight runtime/download/setup footprint.

No deletion or production/system-state change.

## B4.1 exact source-context recovery

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Hypothesis:
The B4.1 design is still correct, but the installer used a brittle inferred
source anchor.

Targeted probe:
- exact current `games.py` SHA/bytes/lines;
- BOM/newline convention;
- AST spans for legacy import, constructor, catalog dict, actions, payload
  assignments, StreamHostError handlers and `_stream` calls;
- merged exact surrounding context blocks with per-block hashes.

No production behavior change.

## B4.1 v2 — AST-span server legacy-edge removal

Status: **DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING**.

The patch severs only GamesPlugin -> legacy StreamManager. Its generator is
driven by the exact B4.1 source-context evidence and semantic AST node selection.

No Android change. No legacy artifact deletion yet.

## B4.2 — Android Moonlight source-context capture

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Question:
What exact current Android functions/callers and manifest query make up the
Moonlight edge after B4.1?

Probe:
- exact MainActivity/manifest SHA, BOM/newline, bytes/lines;
- exact `buildGameCatalogMessage`, `openGameStreamClient`, `showGameDetails`,
  `launchGameOnCompanion` function blocks;
- direct call sites to the two legacy-facing helpers;
- all Sunshine/Moonlight/com.limelight occurrences;
- exact manifest com.limelight context.

No production behavior change.

## B4.2 — Android Moonlight edge

Status: **DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING**.

Remove only the exact captured Android launcher/query and stale legacy response
branches. Preserve native streaming and all physical legacy artifacts until a
post-cut orphan audit.

## B4.3 — Orphan-reference audit

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Question:
After B4.1/B4.2 runtime validation, which legacy helpers/files/scripts are truly
orphaned versus still referenced by current production code?

The audit separates production, scripts, tools and physical artifact groups and
captures exact helper bodies/call sites before cleanup.

## B4.4 — Code-orphan cleanup

Status: **DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING**.

Remove only:
- buildStreamHostMessage;
- setGameStreamHost;
- companion/games/stream_manager.py.

Preserve every physical Sunshine/Moonlight runtime/download/setup artifact until
a separate exact hash manifest exists.

## B4.5 — Physical legacy hash manifest

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Capture exact per-file hashes/group digests, additional non-archive
Sunshine/Moonlight-named artifacts, Windows process/service/task/firewall state,
and com.limelight presence on already-connected Android targets without logging
identifiers or connecting to new targets.

## B4.6 — Physical project legacy cleanup

Status: **DEVELOPMENT PATCH / RUNTIME VALIDATION PENDING**. Delete only the nine B4.5 exact-hash project groups. Preserve all RetroArch Moonlight-name non-targets and keep device package state separate.

## B4.7 — Device Moonlight package verification

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Question:
After project-side cleanup, is the temporary Moonlight Android client still
installed on the already-paired onn?

Use existing private ADB recovery. Do not log target identifiers or addresses.
Do not uninstall anything in this diagnostic.

## B4.8 — Device Moonlight package removal

Status: **ACTIVE / DEVICE ACTION**.

Remove only `com.limelight` from the privately resolved onn. Verify final package
state. Do not change project production source.

## B4.8 — Final device package state

Status: **ACTIVE / VERIFICATION ONLY**.

The package uninstall itself returned success. Resolve only the verifier
false-negative by re-querying final package state with list-packages semantics.

No further package modification is authorized unless the corrected verifier
finds Moonlight still installed.

## B5 — Native-only regression

Status: **ACTIVE / RUNTIME VALIDATION**.

Scope:
- one representative normal library launch;
- native WGC/NVENC/UDP-FEC path;
- picture/audio/controller;
- pause/resume;
- Save/Load;
- one existing cheat/mod/profile path;
- End/teardown.

This is dependency-removal regression only. Do not repeat unrelated Phase A
exploration.

## B5 classifier false negative

**CLOSED / RUNTIME ADJUDICATED.**

Root cause: the B5 harness treated post-profile `native_stream.active=False` as
a product failure even though that state coincided with the native client/UI
lifecycle transition. Decoder evidence showed healthy streaming for the entire
176.5 s client session.

No production defect found. Harness acceptance corrected.

## B6 — Clean-native repository audit

Status: **ACTIVE / DIAGNOSTIC ONLY**.

Question: is the authoritative local tree ready to become the Phase B
clean-native checkpoint without staging unrelated files or preserving active
Sunshine/Moonlight dependencies?

No commit/push in this step.

## Phase B

**COMPLETE / CHECKPOINTED / PUSHED.**

No Phase B investigation remains active.

Next active development area: C1 explicit stream profiles.
