---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# Unified Diagnostics Architecture

## B1 foundation

The B1.1 inventory established that PrivyHub already has substantial telemetry,
targeted probes and a redacted support-bundle harness. The missing layer is a
stable cross-subsystem health/event contract.

B1 therefore uses an adapter/aggregator architecture:

```text
existing subsystem status / telemetry
              ↓
safe normalization adapters
              ↓
privyhub_diagnostics_health_v1
              ↓
CLI probe / companion endpoint / GUI / support bundle
```

Existing detailed telemetry remains authoritative evidence. The health model is
a summary/classifier and must never destroy or overwrite raw measurements.

## Health component contract

Each normalized component contains:

- `subsystem`
- `component`
- `health`: healthy / degraded / unavailable / idle / unknown
- `severity`: info / warning / error
- `event_code`
- `summary`
- `measurements`
- `classification.classifier`
- `classification.basis`

Unknown is not automatically failure. For example, end-to-end network health is
unknown until client feedback exists.

## Resource contract

`privyhub_resource_snapshot_v1` is designed now so Phase E resource testing can
reuse the same contract.

Initial measurements reuse the existing bounded native host telemetry sampler:

- capture-process CPU;
- encoder/FFmpeg CPU;
- capture working set/private memory;
- encoder working set/private memory;
- WGC copy/write timing and frame counters;
- logical CPU count;
- sample cadence/count.

No second resource sampler is introduced in B1.

Metrics not currently measured remain explicit `unavailable_metrics`, including:

- GPU utilization;
- encoder-engine utilization;
- host total/available RAM;
- storage I/O rate;
- end-to-end network goodput.

Hardware capacity and profile fit remain `unclassified`; no hardware-tier
thresholds are valid until Phase E benchmark evidence exists.

## Privacy

Normalized health output intentionally omits:

- network addresses;
- ports;
- process IDs;
- window/game titles;
- filesystem paths;
- raw helper payloads.

Detailed local evidence may retain operational fields where needed, but the
health/GUI/support surface should minimize them.

## Retention

B1.1 showed that some transport artifact directories already exceed hundreds of
MB. B1 must add directory-level retention before broadening always-on telemetry.

Retention should preserve:
- newest/failing evidence;
- curated checkpoint evidence;
- explicit investigation captures.

Routine rolling history should be bounded by age/count/bytes.

## B1.2 runtime validation

The first real snapshot returned `B1_HEALTH_MODEL_SNAPSHOT_CAPTURED` and
classified the idle system correctly. Existing last-session resource telemetry
was recovered with 41 samples at a 2-second cadence.

This validates the separation between:
- live component health;
- last-session resource evidence;
- unmeasured resource fields;
- future benchmark classification.

## B1.3 read-only endpoint

Expose the validated model at:

`GET /diagnostics/health`

The endpoint is a view over existing status/telemetry and starts no new sampler.

A small runtime adapter is responsible for:
1. obtaining the current Games plugin status directly in-process;
2. resolving the current host-telemetry file only under
   `logs/games/host_telemetry`;
3. falling back to the newest valid host-telemetry history file after a
   companion restart, so last-session optimization evidence remains available;
4. passing only normalized data to the health model.

The endpoint must not expose addresses, ports, PIDs, paths, game/window titles
or raw helper payloads.

This endpoint becomes the common consumer contract for later CLI support bundle,
Android GUI diagnostics and Phase C/E measurements.

## B1.3 runtime validation

`GET /diagnostics/health` returned `B1_HEALTH_ENDPOINT_CONFIRMED` after companion
restart. It recovered the 41-sample host telemetry file through
`latest_history`, correctly labeled the resource scope `last_session`, started
no sampler, and passed the endpoint privacy checks.

## B1.4 client-feedback source audit

Before adding Android→companion diagnostic traffic, inspect the exact current
Android native-stream source.

The question is intentionally narrow:

> Can client decoder/network health reuse an existing metric cadence and Android
> request primitive, or would a new periodic sender be required?

The preferred design is zero duplicate measurement work and the lowest
reasonable feedback cadence. The audit must identify:

- existing decoder/render/FEC/receive-rate counters;
- existing scheduler/cadence mechanisms;
- existing HTTP/JSON request infrastructure;
- lifecycle start/stop boundaries;
- current diagnostic/session-report paths;
- exact source hashes.

Do not create a second decoder sampler merely to populate the common health
schema. Future adaptive bitrate should consume the same bounded client feedback
contract that diagnostics uses.

## B1.4/B1.5 client feedback

Exact source inspection confirmed that `NativeStreamActivity` already owns a
500 ms metrics tick and all required receive/FEC/decoder counters. B1.5 adds no
second sampler. A 2-second `privyhub_client_health_v1` report is triggered from
that existing cadence.

The companion exposes `POST /diagnostics/client-health`, validates a strict
<=8 KiB JSON body, and stores only latest state plus one prior baseline for
counter deltas. The periodic request log is suppressed so this path does not
create address-bearing console log spam.

`GET /diagnostics/health` consumes fresh client feedback. Initial health rules
use direct categorical state and new unrecovered/drop events only; no arbitrary
latency/FPS thresholds are introduced. Phase C may tune cadence/rules from
impairment evidence. Phase E may quantify overhead from reported cadence and
payload bytes.

## B1.5 runtime result

Client feedback is operational and low-overhead in the measured run:
631-byte payloads at a 2-second cadence, no additional Android metrics timer,
no new host resource sampler, no persistent client-health sample log.

The network path resolved to healthy. The decoder classifier resolved degraded
because the initial rule treats any stale-output delta as degradation.

That classifier is now under review. One observed interval had:
- ~59.7 receive FPS;
- no FEC unrecoverable groups;
- no network dropped-frame delta reported by the B1.5 probe;
- no decoder queue-overflow drops;
- 9 stale-output drops.

Do not convert that observation into an arbitrary tolerated stale-drop threshold.

## B1.6 stale-output semantics audit

Collect multiple consecutive client-health intervals and compare:
- received FPS versus configured target;
- rendered-frame delta / interval;
- stale-output delta and stale share of decoder outputs;
- ordinary decoder drops;
- queue-overflow drops;
- queue depth;
- receive→decode timing;
- output-gap timing;
- network/FEC impairment.

The purpose is to determine whether stale-output drops are:
1. a meaningful visible decoder degradation;
2. a low-latency catch-up mechanism that can coexist with target render cadence;
3. or a mixed signal that needs rate/context-sensitive classification.

No classifier rule changes until this evidence is captured.

## B1.6 stale-output semantics result

Eight intervals established that stale-output shedding is a recurring low-
latency behavior rather than a sufficient decoder-failure signal.

Measured:
- 50 stale outputs across 8 intervals;
- 913 rendered frames;
- 0 ordinary decoder drops;
- 0 queue-overflow drops;
- queue depth remained 0;
- median receive rate ~59.8 FPS;
- median rendered estimate ~57.25 FPS;
- seven intervals retained healthy network state.

The only materially impaired interval coincided with upstream network/FEC
evidence.

## B1.7 decoder classifier rule

The decoder classifier is subsystem-local:

Degraded:
- hardware acceleration unavailable; or
- ordinary decoder frame-loss delta > 0; or
- decoder queue-overflow delta > 0.

Healthy / informational shedding:
- hardware acceleration available;
- ordinary decoder drops = 0;
- queue-overflow drops = 0;
- stale-output delta > 0.

Event:
`VIDEO-DECODER-LOW-LATENCY-SHEDDING`

Stale-output count remains visible in measurements. No numerical tolerance is
encoded because B1.6 did not establish one.

Upstream FEC/network impairment belongs to the network component and should not
automatically duplicate as a decoder fault.

## B1.7 runtime validation

The decoder classifier is now runtime validated across six stale-only intervals.
Decoder remained healthy/info under low-latency shedding, and an independently
degraded network interval did not incorrectly degrade the decoder.

This establishes a key GUI rule: present subsystem-local health and preserve
measurement context separately.

## B1.8 GUI/Self-Test + retention context

Before adding UI, inspect the exact current Android navigation structure.

Preferred architecture, if current source confirms it:
- standalone `DiagnosticsActivity` under the diagnostics package;
- MainActivity receives only a narrow navigation entry;
- activity reads `GET /diagnostics/health`;
- GUI is a presentation layer, never the health source of truth;
- self-test invokes bounded existing checks and reports measured results;
- sanitized support bundle remains available outside the GUI as well.

Retention is a separate policy layer over runtime logs. It must never target:
- curated `docs/memory/evidence/`;
- checkpoint snapshots;
- local raw durable-memory evidence used by active investigations.

Retention should be based on measured family pressure and preserve failure/newest
evidence before deleting routine rolling history.

## B1.8 result / B1.9 GUI foundation

B1.8 confirmed a standalone activity is preferable to adding diagnostic UI
logic to the 14k-line MainActivity.

B1.9 uses:
- one narrow `Diagnostics` action in PrivyHub Settings;
- standalone `.diagnostics.DiagnosticsActivity`;
- existing `GET /diagnostics/health`;
- no parallel classifier or sampler.

The GUI renders health plus event/measurement context. In particular,
`VIDEO-DECODER-LOW-LATENCY-SHEDDING` remains healthy/info while its stale and
rendered deltas remain visible.

`RUN SELF-TEST` evaluates the existing health contract rather than inventing
performance thresholds. Current health/event classifications remain owned by the
companion.

## Retention foundation

The first retention policy is intentionally manual and dry-run-first.

Allowlisted runtime families:
- `logs/transport_probe`;
- `logs/transport_reverse`;
- `logs/debug_bundles`.

Never-touch scope:
- `docs/memory/`;
- `archive/patch_backups/`.

Provisional manual caps:
- forward transport: 256 MiB;
- reverse transport: 128 MiB;
- debug bundles: 64 MiB.

These are storage bounds, not hardware capability classes. Phase E may make
budgets capability-driven later.

Safety:
- newest eight files in each family are protected;
- `.txt`, `.json`, `.md` summaries are protected;
- failure/error/degraded/unrecoverable/loss/latest-name evidence is protected;
- symlinks/out-of-family paths are ineligible;
- default mode is dry-run;
- apply requires the exact policy SHA-256;
- no automatic retention is enabled in B1.9.

If protected evidence prevents reaching a cap, the plan reports
`blocked_by_protected_evidence` instead of deleting protected files.


## B1.9 runtime validation and blocked-retention rule

The standalone Diagnostics activity is runtime validated. It remains a thin consumer of `/diagnostics/health`.

Retention has an additional fail-closed invariant: a family with `blocked_by_protected_evidence=True` must never be applied merely to perform the partial eligible deletion. First audit the protected footprint and make an evidence-based policy decision.

## B1.10 blocker result / B1.11 policy refinement

The B1.9 policy incorrectly conflated `.txt` extension with summary semantics.
B1.10 measured five old `pktmon_full.txt` files consuming ~259 MiB while
protected solely by the extension rule.

Retention protection precedence is now:

1. newest-minimum protection;
2. explicit raw-name override check;
3. summary-extension protection;
4. failure/evidence-name protection.

`pktmon_full.txt` is the only initial raw-name override. This is intentionally
narrow; do not broaden to all `.txt` or guess other raw types without evidence.

B1.11 remains dry-run-first. A successful unblocked plan is required before any
explicit apply decision.

## B1.12 retention apply

Manual retention is runtime validated. Eight reviewed raw forward-transport
artifacts were removed with zero failures. All managed families are now under
cap and unblocked. Automatic retention remains disabled.

## B1/B2 completeness boundary

Before legacy streaming cleanup, validate the roadmap rather than inferring
completion from feature count.

Specifically distinguish:
- current health snapshot from bounded diagnostic event history;
- existing command-line sanitized bundle tooling from GUI one-click bundle
  access;
- component-derived Self-Test status from dedicated non-destructive checks such
  as storage writability or development/ADB readiness.

B3 should begin only after remaining B1/B2 requirements are either implemented
and runtime validated or explicitly deferred by decision.

## B1/B2 completion source-context rule

The completion-gap audit is a feature-presence check, not sufficient source
context for patching.

Before the completion production patch:
- determine whether Self-Test already loops the full common component model;
- reuse the existing sanitized-bundle implementation rather than creating a
  second bundler;
- reuse existing ADB readiness tooling if a bounded check already exists;
- keep storage writability non-destructive;
- integrate event history into existing health/event producers rather than
  creating another sampler.

B3 stays gated until this exact-context decision is resolved.

## B1.13 completion architecture

### Bounded event history

`runtime_health.build_live_health_snapshot()` remains the health-snapshot entry
point and feeds a singleton `DiagnosticEventHistory(capacity=128)`.

Records contain:
- timestamp;
- safe session identifier when available;
- subsystem/component;
- severity and stable event code;
- human summary;
- sanitized raw measurements;
- classification result/classifier;
- causal predecessor event id for the same component;
- remediation hint;
- explicit privacy classification.

The ring records initial/transition events. For client-feedback metrics, nonzero
FEC recovery/unrecoverable, decoder/network drop and stale/overflow deltas are
also recorded as measurement-pulse events once per feedback sequence. No new
timer/sampler is created.

### Bounded Self-Test

POST `/diagnostics/self-test` reuses the current health snapshot and adds:
- storage temporary write/fsync/delete under `logs/diagnostics`;
- ADB development readiness (`adb devices` only; no connect/recovery);
- RetroArch configured executable/core/config-parent readiness.

The GUI still loops every health component, so audio/controller/decoder checks
remain source-of-truth health-model checks.

### GUI sanitized support bundle

POST `/diagnostics/bundle` invokes the existing
`tools/privyhub_debug_bundle.py --mode latest` path. The bridge does not
reimplement evidence selection/redaction.

After the validated bundler succeeds, the bridge adds
`diagnostics_context.json` containing the current sanitized health/event snapshot
and runtime-version metadata, updates `manifest.json`/`SHARE_ME.txt`, rebuilds
`SHARE_ME.zip`, and validates ZIP integrity/required entries.

All `/diagnostics/` HTTP request logging is suppressed to avoid introducing
address-bearing diagnostic request logs.

## Android Diagnostics busy-state feedback

`DiagnosticsActivity.setBusy()` owns the action-button busy state. Keep the
existing single busy gate and status text, but also make the active action
visible at the button itself:
- refresh -> `REFRESHING...`;
- self-test -> `RUNNING...`;
- bundle -> `COLLECTING...`.

The active-action label is transient and reset whenever `setBusy(false, ...)`
runs, including success/failure paths. This avoids introducing a new progress
timer or state machine.

## B3 dependency-inventory boundary

B3 is read-only. Separate live execution/configuration edges, dead compatibility references, install/uninstall residue, documentation/history, safely unreferenced dedicated artifacts, and native files that must be preserved. System-state checks must not capture network addresses.

## B3.1 focused cut-set tracing

B4 removal decisions must be based on current execution edges, not broad term
counts.

Server trace:
- AST-parse current `companion/plugins/games.py`;
- enumerate import, construction and method calls on `self._stream`;
- enumerate corresponding `self._native_stream` calls for separation;
- preserve native stream manager paths.

Android trace:
- map Sunshine/Moonlight/com.limelight references to enclosing MainActivity
  functions and direct call sites;
- record manifest package visibility.

Artifact trace:
- group Sunshine runtime/download/setup assets by root;
- do not classify every vendored file as an independent active dependency;
- exclude archive/history and known RetroArch moonlight name collisions.

This evidence becomes the B4 predecessor.

## Large-file removal transform discipline

For large files such as `companion/plugins/games.py`, multi-block removal should
be driven by syntax structure and exact current line spans, not reconstructed
whitespace.

The diagnostic source-context stage should record:
- exact file SHA;
- encoding/BOM and newline style;
- AST-selected node spans;
- exact surrounding context;
- per-context hashes.

The production installer should then re-parse the same exact predecessor and
apply only those structurally identified edits, compile the generated result,
and reject any ambiguous span selection before modification.

## B4.1 exact AST edit set

Delete structurally selected complete statements/blocks:
- `from games.stream_manager ...`;
- `self._stream = StreamManager(...)`;
- `games_stream_host` dict;
- all payload assignments with key `stream_host`;
- payload key `stream_warning`;
- `stream_warning = None`;
- stream-status/start/stop If nodes;
- the nested launch Try whose direct exception handler is `StreamHostError`.

Rewrite only the outer tuple exception header from
`except (EmulatorError, StreamHostError) as exc:` to
`except EmulatorError as exc:`.

Reject any selection-count mismatch or overlapping deletion span.

## B4.2 Android edge isolation

B4.1 proved the server legacy edge is gone. Android still contains a separate
Moonlight client compatibility edge.

B4.2 should remove only:
- Moonlight/com.limelight launch behavior;
- user-facing Sunshine/Moonlight wording that is now obsolete;
- manifest package visibility required only for com.limelight.

Preserve the current native stream launch/session path. Do not delete external
runtime/download/setup artifacts in the same patch.

## B4.2 Android compatibility cut

After B4.1 the native server path is authoritative. B4.2 removes Android
Moonlight/com.limelight launch/visibility and stale stream_host UI/response
fallbacks.

Expected native path remains:
`launchGameOnCompanion -> completeGameLaunchHandoff -> openNativeGameStream`.

Helper definitions and legacy runtime assets are not removed without a separate
orphan-reference proof.

## B4.3 orphan classification

Legacy cleanup must not be driven by broad text counts.

Classify current references by execution role:
1. product production source;
2. maintenance/setup scripts;
3. diagnostics/tools;
4. physical runtime/download payloads;
5. historical/archive or RetroArch name-collision non-targets.

Only proven orphan helpers/artifacts enter the cleanup patch.

## B4.4 cleanup split

Cleanup is split by evidence quality.

Exact-hash code orphans can be removed now. Physical legacy payloads/scripts
have only path/count/size evidence, so deletion is deferred until a content hash
manifest is captured.

This keeps predecessor verification strong instead of weakening deletion gates.

## B4.5 physical deletion gate

Physical legacy deletion requires an exact sorted per-file hash manifest for
every target group, not only path/count/size. The gate also checks
process/service/task/firewall state and `com.limelight` on already-connected
Android targets. ADB probing must not connect to an address or log identifiers.

## B4.6 exact physical cleanup

Recompute B4.5 canonical group digests before deletion; reject mismatches/symlinks/new targets. Create and verify a backup ZIP before modification. Rollback must restore target bytes and original group digests.

## B4.7 private ADB package check

The B4.7 device package check uses the established private ADB recovery model
instead of PATH-only discovery.

A target is accepted only when:
- it resolves through the existing physical-onn recovery flow; and
- `com.safeiot.privyhub` is present.

Only then is `com.limelight` queried. Device identifiers and network addresses
must never be emitted to logs.

## B4.8 package-only removal

B4.8 is a device cleanup action, not an Android source patch.

The action reuses B4.7 private ADB resolution, verifies the target contains
PrivyHub, uninstalls only `com.limelight`, and re-queries both package states.

A successful adb return alone is insufficient; final package absence is the
authoritative result.

## Android package presence semantics

`pm path` is useful for positive presence but is not portable as an absence
query because missing packages may yield nonzero shell status.

For presence/absence classification prefer exact parsing of
`package:<package-name>` from a successful package-list command. Empty successful
output is valid absence.

## B5 focused regression evidence

B5 separates objective and operator-observed evidence.

Objective:
- exact production source hashes;
- B4 legacy artifact absence;
- initial active native stream identity/backend/encoder/transport;
- Sunshine process absence;
- savestate file delta after Save;
- cheat-profile storage presence;
- post-profile native host status retained as informational lifecycle evidence;
- inactive game/native stream after End.

Operator-confirmed:
- visible decoded picture;
- audible game audio;
- controller response;
- pause/resume behavior;
- Load restored the expected state;
- known cheat/mod/profile behavior worked.

PASS requires every required objective and operator assertion.

## B6 repository audit boundary

The B6 audit scans production source for active legacy edges but intentionally
excludes tools, durable history/evidence and RetroArch metadata/shader name
collisions. Historical diagnostics are allowed to describe Sunshine/Moonlight;
production runtime code is not.

Repository readiness and runtime health are separate measurements. B5 supplies
runtime proof; B6 supplies source-control and architecture-boundary proof.

## B6 final audit semantics

The B6 legacy scanner records one exact-hash inert MainActivity text hit rather
than treating every raw token match as an active dependency. The exception is
valid only for source hash
`394d2b839fdb01f2988a0054b42e139e419e02207728f914e1713287992733cc`,
line 7683, pattern `legacy_stream_host`.

Durable-memory manifest validation does not validate `manifest.json` against a
conventional self-entry. The checkpoint removes that self-entry; all other
non-raw entries remain hash/byte validated.
