---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: e65e8f89604ce325e6e3e0537d0287070b8996c5
---

# Current Development State

## Checkpoint

- Branch: `main`
- Current pushed checkpoint: `e65e8f89604ce325e6e3e0537d0287070b8996c5`
- Commit message: `Checkpoint: complete Phase A emulator subsystem`
- Working tree after checkpoint: clean
- Phase A: COMPLETE / pushed

## Current runtime coverage

Runtime validated:
- SNES normal Games path;
- extensive PS1 path;
- 1P/2P/4P controller routing;
- Crash Bash and CTR Port-1-only multitap;
- Save/Load;
- pause/resume/frozen preview;
- host coexistence/audio lifecycle;
- cheats/mods/input profiles;
- native streaming and teardown;
- persistent wireless-ADB recovery.

Declared no-fixture gaps:
- NES: zero local games at A9; supported/configured, not runtime validated.
- Genesis: zero local games at A9; supported/configured, not runtime validated.

## Active roadmap

`docs/ROADMAP.md` v2 is authoritative for post-Phase-A sequencing.

Next phase: **Phase B — Diagnostics & Clean Native Baseline**.

Immediate next work:
1. inventory existing production telemetry/probes;
2. define a unified diagnostic event/health schema;
3. add GUI Diagnostics / Self-Test / sanitized support bundle;
4. inventory and remove Sunshine/Moonlight legacy;
5. run focused native-only regression;
6. checkpoint the clean-native architecture.

Subsequent roadmap:
- Phase C: adaptive native streaming, explicit profiles, path telemetry,
  bitrate adaptation, 1080p60 and generalized sources;
- Phase D: VOD/media-library artwork and metadata UX;
- Phase E: resource benchmarking, inexpensive Linux tiers and capability scaling;
- Phase F: optional OpenBIOS/open-platform portability track;
- Phase G: broader smart-home, storage, remote-PC-game and handheld expansion.

## Preservation boundaries

Do not reopen or refactor validated Phase A paths without evidence:
- WGC native game capture;
- H.264 NVENC low-latency path;
- native process audio;
- UDP/FEC transport;
- Android hardware AVC decode;
- PHI1/ViGEm P1-P4 controller chain;
- Save/Load/Pause/End lifecycle;
- A8 profiles;
- PS1 Port-1-only multitap.

## Debugging rule

Use:
**one narrow hypothesis -> one targeted diagnostic/probe -> fresh evidence ->
inspect raw measurements -> one coherent patch**.

Never ask for or log network addresses.

## Phase B1.1 — diagnostics inventory active

B1 begins with an inventory-only probe. Do not build a new diagnostics framework
until the exact current production telemetry, live/final state, targeted probes,
shareable-bundle behavior, privacy handling, schemas, retention behavior and GUI
surfaces are measured from the current local tree.

Existing pushed evidence already establishes that PrivyHub has a strong base:
`run_privyhub_debug.ps1`, `privyhub_debug_bundle.py`, structured decoder-session
JSON, host telemetry, audio timing, capture diagnostics and transport summaries.
The active question is consolidation: what should become the common event/health
contract, and what should remain subsystem-specific.

Run `tools/probe_b1_diagnostics_inventory.py` and inspect
`logs/diagnostics/b1_diagnostics_inventory.txt` before any B1 production change.

## B1.1 result and B1.2 active state

Fresh B1.1 inventory confirmed `DESIGN_COMMON_SCHEMA_AND_HEALTH_AGGREGATOR`.

The existing debugging harness and raw telemetry are retained. B1.2 now adds a
pure health/resource normalization module and a runtime probe without changing
the service API or native streaming behavior.

Resource/optimization preparation begins here: the new resource schema consumes
the existing host telemetry sampler and exposes observed capture/encoder CPU,
memory and WGC timing. GPU, encoder-engine, host RAM, storage I/O and network
capacity remain explicitly unavailable; hardware/profile classification remains
`unclassified` until Phase E benchmarking.

Next evidence:
`logs/diagnostics/b1_health_snapshot.txt`.

## B1.2 runtime validated / B1.3 active

The real B1.2 snapshot returned `B1_HEALTH_MODEL_SNAPSHOT_CAPTURED` with overall
healthy idle state, 11 components and valid last-session resource telemetry.

Observed last-session resource evidence:
- 41 samples at 2-second cadence;
- capture CPU host avg/max 6.382/7.846%;
- encoder CPU host avg/max 9.05/11.395%;
- capture working set avg/max 82.362/86.469 MiB;
- encoder working set avg/max 125.815/132.656 MiB.

GPU/encoder-engine/system-RAM metrics remain unavailable and capacity/profile
classification remains unclassified.

B1.3 now integrates the validated model as read-only
`GET /diagnostics/health`. It adds no resource sampler and does not touch native
streaming behavior.

## B1.3 runtime validated / B1.4 active

The read-only health endpoint returned `B1_HEALTH_ENDPOINT_CONFIRMED` after
companion restart. It recovered 41 samples from `latest_history`, reported
`last_session`, started no resource sampler, and exposed no forbidden
privacy/network identifiers.

B1.4 is now a diagnostic-only Android client-feedback source-context audit.
Before adding any new telemetry traffic, identify exact existing decoder/network
metrics, cadence/scheduler primitives, HTTP/JSON request paths and lifecycle
boundaries in the current local Android source.

The goal is to reuse existing measurement/cadence infrastructure so diagnostics,
future adaptive bitrate and later low-resource clients share one efficient
feedback path.

## B1.4 result / B1.5 client feedback active

B1.4 confirmed the existing Android metric/network/scheduler primitives are
sufficient. B1.5 therefore reuses the existing 500 ms metrics tick and adds no
new metrics timer or resource sampler.

A privacy-minimized `privyhub_client_health_v1` report is emitted every 2 seconds
with at most one request in flight. The companion retains only the latest report
plus one prior counter baseline for deltas; no persistent per-sample
client-health history is added.

Cadence and payload bytes are exposed as measurements so later Phase E work can
quantify diagnostics overhead. The same client feedback is intended to feed
future Phase C adaptive bitrate rather than a second telemetry protocol.

## B1.5 transport validated / B1.6 classifier audit active

B1.5 returned `B1_CLIENT_FEEDBACK_CONFIRMED`.

The feedback mechanism itself is validated:
- 2-second cadence;
- sequence advanced to 56;
- 631-byte payload;
- ~59.7 receive FPS / ~8.08 Mbps;
- no extra Android timer;
- no new resource sampler;
- no persistent client-health log;
- endpoint privacy clean;
- network path resolved healthy.

The decoder component reported degraded solely because the current conservative
rule treats any stale-output delta as degradation. The observed interval had 9
stale drops, zero queue-overflow drops, no FEC unrecoverable groups, and healthy
network state.

B1.6 is diagnostic-only. Measure rendered-frame cadence versus stale-output
drops over multiple intervals before changing the classifier.

## B1.6 complete / B1.7 classifier correction active

B1.6 captured 8 intervals and disproved the current `stale > 0 => degraded`
decoder rule as a useful subsystem classifier.

Across the run:
- 50 stale outputs;
- 913 rendered frames;
- 0 ordinary decoder drops;
- 0 queue-overflow drops;
- queue depth 0 throughout;
- 7/8 intervals had healthy network state;
- the one materially poor interval coincided with FEC/network impairment.

B1.7 changes only the health classifier. Stale-only low-latency shedding becomes
healthy/info with its own event. Direct decoder-local faults remain degraded.
No stale/FPS threshold is added.

## B1.7 runtime validated / B1.8 GUI-retention context audit active

B1.7 returned `B1_DECODER_CLASSIFIER_CONFIRMED`.

Six stale-only intervals all remained decoder healthy with
`VIDEO-DECODER-LOW-LATENCY-SHEDDING`; one interval independently showed degraded
network health without being double-counted as decoder degradation.

The underlying health pipeline is now suitable for user-facing diagnostics.

Before modifying Android UI or deleting any logs, B1.8 performs one
diagnostic-only context audit:
- exact MainActivity/navigation and existing diagnostic-activity anchors;
- health endpoint shape available to the GUI;
- existing self-test/debug-bundle inputs;
- current per-family diagnostic storage pressure;
- existing retention mechanisms.

No retention deletion occurs in B1.8.

## B1.8 complete / B1.9 Diagnostics GUI + retention foundation active

B1.8 returned `B1_GUI_SELF_TEST_RETENTION_CONTEXT_CAPTURED`.

Architecture:
- standalone Diagnostics activity preferred;
- health endpoint ready;
- existing debug harness/bundle retained;
- MainActivity should receive navigation only.

Measured retention pressure:
- forward transport 322.048 MiB high;
- reverse transport 125.393 MiB high;
- debug bundles 23.728 MiB moderate.

B1.9 adds the standalone Android Diagnostics/Self-Test surface and a manual
dry-run-first retention utility. It does not automatically delete runtime logs.
The retention policy excludes durable-memory evidence and patch backups and
requires an exact policy hash for future apply.

Next runtime evidence:
`logs/diagnostics/b1_gui_retention_runtime.txt` plus manual confirmation that
Settings -> Diagnostics -> Refresh / Run Self-Test renders correctly on the onn.


## B1.9 runtime validated / B1.10 retention blocker audit active

B1.9 returned `B1_GUI_RETENTION_FOUNDATION_CONFIRMED` and the user manually confirmed the Diagnostics GUI renders correctly. The health endpoint remains 11-component schema v1 and no new resource sampler starts.

Retention remained dry-run with zero deletions. Reverse transport and debug bundles are already under their provisional limits. Forward transport is blocked: 322.048 MiB total, 15 eligible files remove only 8.870 MiB, leaving 313.178 MiB because 43/58 files are protected.

Do not apply the B1.9 retention policy. B1.10 is a diagnostic-only audit of the forward protected footprint by reason, extension and size. Next evidence: `logs/diagnostics/b1_retention_blocker.txt`.

## B1.10 complete / B1.11 retention rule refinement active

B1.10 identified the blocker precisely: five old `pktmon_full.txt` raw packet
capture dumps (~51.8–51.9 MiB each) are protected only because the B1.9 policy
treats every `.txt` as summary evidence. A sixth newest full dump is protected by
the newest-minimum rule.

B1.11 changes only retention classification. `pktmon_full.txt` becomes an
explicit raw-name override for extension protection. Newest-eight and
failure-name protections remain unchanged; `.txt` remains protected generally.

No retention apply is performed by B1.11. The runtime probe must show the
forward plan can reach <=256 MiB without touching durable memory or patch
backups before deletion is considered.

## B1.12 retention apply complete / B1-B2 completion audit active

The first explicit retention apply succeeded:
- 8 reviewed raw forward-transport files deleted;
- 112,619,830 bytes freed;
- 0 failures;
- forward transport now 214.645 MiB, below 256 MiB;
- reverse transport 125.393 MiB, below 128 MiB;
- debug bundles 23.728 MiB, below 64 MiB;
- all managed families candidate_count=0 and blocked=false;
- durable memory and patch backups remained outside scope.

Retention is runtime validated in manual mode. Automatic retention remains off.

Before B3, audit the roadmap against the actual B1/B2 implementation so bounded
common event history, GUI support-bundle access, and Self-Test requirements are
not accidentally skipped.

## B1/B2 gap audit complete / exact completion source-context active

The completion-gap audit returned `B1_B2_COMPLETION_GAPS_CAPTURED`.

Confirmed roadmap gaps:
- bounded common diagnostic event history absent;
- GUI `Collect Diagnostics` action absent;
- dedicated storage-writability Self-Test absent;
- dedicated ADB/development Self-Test absent.

The token audit also reported audio/controller/RetroArch not visible to
Self-Test, but those may already be covered generically by the common component
loop. Do not add duplicate explicit checks until exact `formatSelfTest` context
is inspected.

Next: diagnostic-only exact source-context audit for the minimal B1/B2
completion implementation. B3 remains gated.

## B1/B2 exact context complete / B1.13 completion implementation active

Exact source context confirms the remaining completion work can be isolated from
the stable stream/session path.

Do not duplicate audio/controller checks: the GUI Self-Test already iterates all
health components. However, the current health model has no explicit RetroArch
runtime-prerequisite component; `game_session` is lifecycle state only. Add one
bounded emulator/runtime prerequisite check.

B1.13 completion scope:
- 128-entry common diagnostic event ring attached to health snapshots;
- component state transitions plus nonzero FEC/drop/stale measurement pulses;
- GUI `COLLECT DIAGNOSTICS` action;
- companion bundle bridge that reuses `tools/privyhub_debug_bundle.py`;
- bundle augmentation with current health/event history and runtime-version
  metadata, manifest/hash update, then ZIP revalidation;
- bounded storage temporary write/delete check;
- ADB readiness via `adb devices` only: no connect/recovery and no target
  identifiers returned/logged;
- RetroArch executable/configured-core/config-parent readiness from
  `companion/games/config/emulators.json`.

No capture/encoder/decoder/audio/controller/game-session behavior changes.
B3 remains gated on runtime validation of this completion patch.

## B1/B2 runtime complete / B2 action-feedback polish active

B1/B2 completion runtime validation passed with
`B1_B2_COMPLETION_RUNTIME_CONFIRMED`. Health/event history, dedicated Self-Test,
sanitized bundle, privacy constraints and no-new-sampler/no-stream-change
requirements are runtime validated.

Manual GUI use confirmed Diagnostics works. One bounded usability issue remains:
the action buttons keep their normal labels while an asynchronous Self-Test or
bundle collection is running, making it difficult to tell that the button press
registered on TV.

Apply UI-only feedback:
- REFRESH -> REFRESHING...
- RUN SELF-TEST -> RUNNING...
- COLLECT DIAGNOSTICS -> COLLECTING...
while busy, restoring normal labels on success/failure.

No companion/API/diagnostic behavior changes. B3 can begin after this visual
polish is manually confirmed.

## B1/B2 complete / B3 Sunshine-Moonlight inventory active

B1/B2 diagnostics are complete and runtime/manual validated. The final Diagnostics action-feedback polish was manually confirmed on the onn.

B3 is active as a diagnostic-only dependency inventory. Do not delete Sunshine/Moonlight infrastructure yet. Inventory source/config/docs, services/processes, firewall rules, scheduled tasks, install/removal tooling, Android package/intents, StreamManager references, Games references, UI remnants, and portable runtime/configuration.

## B3 inventory captured / B3.1 active-edge trace active

The broad B3 inventory completed successfully. Windows has no matching active
Sunshine/Moonlight process, service, scheduled task, firewall rule, or installed
software registration.

Do not interpret the 236 broad ACTIVE classifications literally. The inventory
included historical archives, vendored Sunshine runtime files, and
legacy-name/path matches. Those are not equivalent to live execution edges.

Current high-value signals:
- `companion/plugins/games.py` still imports/constructs `StreamManager`;
- `companion/games/stream_manager.py` remains the Sunshine host manager;
- Android MainActivity still contains Moonlight/com.limelight launch logic;
- AndroidManifest still exposes com.limelight package visibility;
- native WGC/NVENC/FEC/audio/controller/game paths remain MUST PRESERVE.

B3.1 now traces only current production call edges and groups legacy artifacts so
B4 can use a small exact cut set.

## B4.1 previous installer rejected / exact Games source-context audit active

The first B4.1 production installer was rejected before modification with exit
code 2. The failure came from an exact transformation-anchor mismatch in
`games.py`; the runtime probe was therefore never installed and no B4.1
production change occurred.

This exposed a workflow regression: the attempted patch inferred multi-line
source anchors from B3.1 trace output rather than first capturing the exact
surrounding local source text.

Realigned workflow:
1. keep B3.1 as the authoritative cut-set evidence;
2. capture exact current `games.py` BOM/newline/AST spans and surrounding source
   blocks;
3. rebuild B4.1 using structural node spans plus the exact current hash;
4. deterministically validate generated output before delivery;
5. only then run the live native-session validation.

Do not retry the previous B4.1 ZIP.

## B4.1 exact source captured / AST-span removal patch pending runtime validation

The exact source-context audit passed and confirmed the authoritative Games
source is CRLF, no BOM, SHA
`3fe502bda2f85706855e6f4e2f38ae0421f7c5de63136efae908d32393c30c77`.

B4.1 v2 uses AST semantics rather than hand-authored multi-line anchors. Before
writing, the installer must select exact counts for:
- one `games.stream_manager` import;
- one `self._stream` constructor;
- one `games_stream_host` catalog dict;
- four `stream_host` payload assignments;
- one `stream_warning` payload assignment and one None initializer;
- one each stream-status/start/stop action;
- one nested launch Try with a direct `StreamHostError` handler;
- one outer `(EmulatorError, StreamHostError)` handler.

It then removes only those full line spans, rewrites the outer exception header
to EmulatorError, preserves CRLF, reparses/compiles the generated complete
source and verifies all required NativeStreamManager paths before installation.

`stream_manager.py`, native_stream.py, Android and all Sunshine artifacts remain
unchanged pending live runtime validation.

## B4.1 runtime confirmed / B4.2 Android source-context audit active

B4.1 is runtime validated:
- normal game active through native path;
- WGC/NVENC/UDP-FEC ready and active;
- legacy server import/reference/status surface gone;
- no Sunshine process;
- stream_manager.py and native_stream.py unchanged.

B4.2 now targets only the Android Moonlight edge. Before editing, capture exact
current `MainActivity.kt` and AndroidManifest context for:
- `buildGameCatalogMessage`;
- `openGameStreamClient`;
- every direct caller of those functions;
- Sunshine/Moonlight/com.limelight occurrences;
- the `<queries>` com.limelight manifest entry.

Do not remove Moonlight/Sunshine runtime/download/setup artifacts yet.

## B4.2 exact context captured / Android edge removal pending runtime validation

B4.1 is runtime validated. B4.2 exact Android context identified the remaining
Moonlight launcher/query plus stale `stream_host` response/UI fallback paths.

The B4.2 production patch removes only those evidenced edges from MainActivity
and AndroidManifest, preserves the native launch/fullscreen path, and runs a
real Kotlin compile before success.

`buildStreamHostMessage` and `setGameStreamHost` definitions are intentionally
left for a post-B4.2 orphan-reference audit. Sunshine/Moonlight
runtime/download/setup artifacts are also unchanged.

## B4.2 runtime confirmed / B4.3 orphan-reference audit active

B4.2 is runtime validated. MainActivity/manifest contain no Moonlight,
Sunshine/com.limelight client edge, B4.1 games.py remains unchanged, and the
representative native game session remained active on WGC/NVENC/UDP-FEC.

B4.3 is diagnostic-only. Classify:
- `buildStreamHostMessage`;
- `setGameStreamHost`;
- `companion/games/stream_manager.py`;
- Sunshine/Moonlight setup/firewall/install scripts;
- Sunshine runtime and Sunshine/Moonlight downloads;
- remaining production/script/tool references.

Do not delete anything until the focused audit is reviewed.

## B4.3 confirms orphans / B4.4 code-orphan cleanup pending runtime validation

B4.3 disposition:
`B4_3_ORPHANS_CONFIRMED_PREPARE_CLEANUP_PATCH`.

Exact code orphans:
- `buildStreamHostMessage`: zero call sites, exact body hash captured;
- `setGameStreamHost`: zero call sites, exact body hash captured;
- `companion/games/stream_manager.py`: zero importers outside itself and exact
  file hash captured.

B4.4 removes only those three code orphans. Physical Sunshine/Moonlight
runtime/download/script groups remain unchanged because B4.3 did not capture
their exact content hashes.

After B4.4 runtime validation, run a hash-manifest probe for the physical legacy
groups before deleting them.

## B4.4 runtime confirmed / B4.5 physical legacy hash manifest active

B4.4 is runtime validated after a fresh companion restart. `stream_manager.py`
and both orphan Android helpers are physically absent; native game streaming
remains active on WGC/NVENC/UDP-FEC; Sunshine is not running.

B4.5 is diagnostic-only. Capture exact sorted per-file SHA-256 manifests for the
remaining Sunshine/Moonlight runtime/download/data/script groups. Also verify
process/service/task/firewall state and whether `com.limelight` remains
installed on already-connected Android targets. Do not log identifiers or make
an ADB connection attempt.

## B4.5 manifest reviewed / B4.6 physical project cleanup pending runtime validation

B4.5 authorizes exact deletion of nine project legacy groups (143 files / 101,408,884 bytes). Windows legacy system state is zero and nine RetroArch name-collision non-targets must be preserved.

B4.6 recomputes every canonical group digest, creates a verified backup archive, deletes only those groups, and runtime-validates the native path. Android `com.limelight` package state remains separate because B4.5 had ADB unavailable.

## B4.6 v1 rejected before modification; v2 corrected

The first B4.6 installer attempt failed before modification on
`data/games/sunshine` manifest comparison.

Root cause was a B4.6 package defect, not a project-state change. The v1
canonical manifest helper hashed literal `\\0` and `\\n` character
sequences instead of the actual NUL/newline separator bytes used by B4.5.

B4.6 v2 restores exact B4.5 canonicalization (`b"\0"` / `b"\n"`) and
requires a direct B4.5-vs-B4.6 fixture equivalence test before delivery.

The B4.5 evidence remains authoritative because v1 was
**FAILED BEFORE MODIFICATION**.

## B4.6 v2 also rejected before modification; v3 corrects non-target discovery

B4.6 v2 passed the corrected B4.5 canonical hash comparison but then rejected
the nine RetroArch Moonlight-name files as unexpected legacy targets.

Root cause was again package-local: v2 copied the B4.5 non-target regular
expressions with an extra backslash before the literal dot, so none of the nine
known non-targets matched.

B4.6 v3:
- uses the exact B4.5 non-target regex semantics;
- directly regression-tests B4.5 vs B4.6 discovery over all nine known paths;
- explicitly exempts the authoritative B4.5 non-target list from the
  unexpected-target deletion gate;
- still requires every listed non-target path to remain present.

B4.6 v2 was **FAILED BEFORE MODIFICATION**. B4.5 remains authoritative.

## B4.6 runtime confirmed / B4.7 device package verification active

B4.6 project-side physical cleanup is runtime validated. The product tree is
clean of the nine Sunshine/Moonlight artifact groups, RetroArch name-collision
non-targets remain, and the representative native stream remains healthy.

Remaining B4 item: verify whether `com.limelight` is still installed on the
already-paired onn.

The B4.6 probe's `ADB_UNAVAILABLE` was limited to PATH discovery. B4.7 uses the
same ADB discovery/private cached-target/mDNS recovery pattern as the established
Android build/install tool. It does not require the user to provide an address
and does not log the target identifier.

## B4.7 confirmed Moonlight installed / B4.8 package-only removal active

B4.7 privately resolved the existing paired onn and confirmed:
- PrivyHub package present;
- `com.limelight` installed;
- no network address or device identifier logged.

B4.8 removes only `com.limelight` using the same private ADB resolution path.
Success requires a post-action package check proving PrivyHub still exists and
Moonlight no longer exists.

No project production source or native streaming path changes are authorized.

## B4.8 uninstall succeeded operationally; final verifier correction active

The first B4.8 device action produced a false-negative classification:
- adb uninstall command succeeded;
- PrivyHub remained installed;
- follow-up logic observed Moonlight absent;
- but `pm path` returned nonzero for the now-absent package and was mapped to
  `PACKAGE_QUERY_FAILED`.

Do not uninstall again.

Run the corrected B4.8 final-state verifier. It uses `pm list packages <filter>`
with a `cmd package list packages` fallback, where an absent package is a valid
successful query state.

B4 completes only after the corrected verifier proves:
- PrivyHub present;
- Moonlight absent;
- no query error.

## B4 complete / B5 native-only regression active

B4.8 corrected final-state verification confirms:
- PrivyHub remains installed on the paired onn;
- `com.limelight` is absent;
- no package query error;
- no network address/device identifier logged.

**B4 legacy removal is complete.**

B5 is now active. It is a focused dependency-removal regression, not a repeat
of Phase A exploration. One representative session must prove:

library launch -> native capture/encode/transport/decode -> audio -> controller
-> pause/resume -> Save/Load -> one existing cheat/mod/profile path ->
End/teardown.

Automate objective evidence and use explicit operator confirmations only for
visible/audible/input behavior that current telemetry cannot prove directly.

## B5 runtime validated / B6 active

The first B5 classifier reported a false negative solely because it required
`post_profile_native_ok=True` after the operator exercised profile/UI flow.

Fresh session diagnostics adjudicate the run as PASS:

- initial native stream was WGC / NVENC / RTP-UDP-XOR-FEC;
- picture, audio, controller, pause/resume, Load and profile behavior all passed;
- Save changed four state-related files;
- Sunshine remained absent;
- native host log ran continuously to frame 10550 at ~60 fps for ~175.8 s;
- Android decoder session lasted 176503 ms and received 148103 video packets,
  10551 frames, zero lost video packets, zero decoder drops and zero
  unrecoverable FEC groups;
- 10041 frames rendered, 509 stale outputs were shed, and one codec frame was
  still in flight, accounting for all 10551 queued frames;
- decoder slow-event telemetry extends to 176439 ms, within 64 ms of session end;
- the decoder/client session ended roughly 10 s before the game process ended,
  matching the harness's post-profile polling window;
- End/teardown was clean.

Conclusion: the stream lifecycle transition was real, but the classifier wrongly
made "native client remains open after profile/UI navigation" a B5 acceptance
requirement. The roadmap requires the profile path and clean teardown, not that
the stream Activity remain open across UI navigation.

B5 is **COMPLETE / RUNTIME VALIDATED**.

Next: B6 clean-native repository audit/checkpoint.

## B6 clean-native repository audit active

B5 is complete/runtime validated. B6 begins with a diagnostic-only local
repository audit before any staging, commit or push.

The audit must capture:
- exact working-tree status and approved-vs-unexpected path classification;
- staged-state absence;
- `git diff --check`;
- current production/core hashes;
- active legacy-reference scan over production source only;
- B4 legacy artifact absence and RetroArch non-target preservation;
- B1/B2 + B4 + B5 acceptance evidence presence;
- durable-memory manifest consistency;
- raw evidence remains untracked/ignored;
- Python syntax and Android Kotlin compilation;
- remote `main` still points at the Phase A/roadmap baseline;
- `docs/ROADMAP.md` exact baseline hash so the final checkpoint can update it
  from Phase B NEXT to Phase B COMPLETE / Phase C NEXT.

No staging/commit/push is authorized until this audit is reviewed.

## B6 audit v1 rejected before modification; v2 corrects ROADMAP handling

The first B6 audit installer failed **BEFORE MODIFICATION** because it required
the working-tree `docs/ROADMAP.md` byte hash to equal an external copied baseline.

That precondition was inappropriate for a repository audit: the authoritative
local roadmap is itself part of the state B6 must inspect.

B6 audit v2:
- keeps exact production-source and durable-memory predecessor checks;
- requires `docs/ROADMAP.md` to exist;
- snapshots its current byte hash and proves the installer does not change it;
- verifies committed `HEAD:docs/ROADMAP.md` against the pushed v2 baseline;
- uses `git diff --quiet -- ROADMAP.md` to detect substantive working-tree
  roadmap changes;
- reports substantive roadmap changes as `REVIEW_REQUIRED` rather than refusing
  to run.

No B6 v1 changes were installed and no v1 audit log exists.

## B6 audit v3 — authoritative roadmap path corrected

B6 v1 and v2 both failed **BEFORE MODIFICATION** because the audit packages
assumed a nonexistent repository-root `ROADMAP.md`.

The authoritative roadmap has always been:
`docs/ROADMAP.md`

B6 v3 is rebuilt around the actual repository layout:
- only `docs/ROADMAP.md` is audited;
- root `ROADMAP.md` is explicitly treated as unexpected;
- committed `HEAD:docs/ROADMAP.md` is compared with the known roadmap baseline;
- the working `docs/ROADMAP.md` is preserved byte-for-byte by the installer;
- substantive working roadmap changes are reported by the audit rather than
  blocked by installer preflight.

No v1/v2 production or audit changes were installed.

## Phase B complete / Phase C next

B6 is complete. The repository audit had zero unexpected or pre-staged paths,
clean `git diff --check`, passing Python/Kotlin builds, intact raw-evidence
ignore rules, and the complete Phase B evidence set.

Two audit-model false positives were corrected:
- the sole MainActivity line-7683 `legacy_stream_host` text occurrence is
  accepted only under exact source hash
  `394d2b839fdb01f2988a0054b42e139e419e02207728f914e1713287992733cc`;
  B4/B5 runtime validation establishes that it is not an active legacy
  execution edge;
- `docs/memory/manifest.json` no longer carries a conventional self-hash entry.

Phase B is checkpointed/pushed. Phase C is next.

Next step: C1 explicit stream profiles.
