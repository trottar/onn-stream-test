---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Decision Log

| ID | Date | Status | Decision | Evidence / rationale |
| --- | --- | --- | --- | --- |
| D-001 | 2026-08-25 | Active | Keep PrivyHub local-first with IoT clients isolated from the trusted host network. | Core project goal and threat-model direction. |
| D-002 | 2026-08-26 | Active | Separate control and media planes; use live request-derived client endpoint rather than a second hard-coded client address. | Proven prototype architecture and privacy preference. |
| D-003 | 2026-09-07 | Deferred | Do not tune product buffering around the Prototype 1 UDP burst/gap/duplication pathology; replay diagnostics on representative Linux/network hardware. | Bidirectional synthetic and production evidence localized transformation outside normal application pacing. |
| D-004 | 2026-09-09 | Active | A4 audio lifecycle uses normal Games shutdown and crash-safe session-volume recovery; do not create parallel shutdown logic. | Runtime validation of TV audio, PC duplicate suppression, helper restoration. |
| D-005 | 2026-09-09 | Active | A8 gameplay mapping belongs after canonical PHI1/ViGEm semantics and uses session-only RetroArch overrides. | Boundary probes and gameplay validation. |
| D-006 | 2026-09-10 | Active | `25e9a14` is the immutable pre-four-player baseline; four-player extension precedes A9. | Clean checkpoint and user direction. |
| D-007 | 2026-09-10 | Active / transport-enumeration runtime validated | Preserve PHI1 v1/36-byte format for the four-player extension; generalize the canonical player-count/state layer to four before touching A8 P3/P4 mapping. | Exact-local audit found no packet-format blocker; base slots, real Android assignment, and fresh RetroArch ports 1-4 are now runtime validated without XInput fallback. A8/gameplay validation remains. |
| D-008 | 2026-09-10 | Active | `docs/memory` is the durable project memory/communication layer; old docs remain evidence but newer status must carry freshness/provenance. | Documentation audit found stale top-level status mixed with newer runtime evidence. |
| D-009 | 2026-09-10 | Active / development patch | Keep input-profile schema 1 while expanding A8 supported players from P1/P2 to P1-P4; treat missing legacy P3/P4 maps as default autoconfiguration and derive Android editor players from companion capabilities. | Backend normalization/generation already iterates the player tuple, so this is the narrowest backward-compatible extension and avoids resetting existing user profiles. |
| D-010 | 2026-09-10 | Active / development patch | Reuse the existing per-game controller override store for PS1 multitap topology and apply it through RetroArch native content-specific core-option files; do not enable multitap globally. | Four-player host routing is proven, active Beetle options explicitly disable both multitap ports, and native `.opt` overrides isolate accessory topology per game while preserving other core settings. |

### D-008 — Roll back first PS1 multitap patch for causal isolation

**Status:** Active diagnostic decision (2026-09-10)

The first game-specific multitap patch made Crash Bash expose four human players but immediately coincided with loss of physical P2-P4 input/controller connectivity during the active game stream. Controllers are charged. Restore the exact pre-patch `emulator_manager.py` and `controller_overrides.json` from the install backup and remove the generated Crash Bash `.opt`; then repeat the four-controller assignment probe. Do not make another production multitap change until that comparison is known.

### D-009 — Re-enable PS1 multitap; separate controller-connectivity investigation

**Status:** Active (2026-09-10)

The exact rollback removed multitap but P4 still failed at the physical Android assignment boundary while P1-P3 remained clean. This weakens D-008's causal suspicion of the multitap implementation. Reapply the same game-specific Crash Bash Port-1 multitap implementation and continue the controller-connectivity investigation independently, beginning with a different physical controller.

### D-009 — Accept game-specific PS1 multitap and separate controller-specific dropout

**Status:** Accepted (2026-09-10)

The exact rollback did not restore P4, while a replacement controller restored exact P1-P4 assignment with the same multitap implementation re-enabled. Final Crash Bash four-player gameplay then passed. Therefore keep game-specific Port-1 multitap and do not treat the earlier dropout as a software regression. Preserve the dropout as a hardware/pairing/transient observation and reopen only on representative reproduction.

### D-009 — PS1 multitap is a Port-1-only On/Off per-game flag

**Status:** Accepted 2026-09-10.

PrivyHub targets a maximum of four local players. Do not expose Port 2 or Both in the product. `Multitap: On` maps to Beetle PSX HW Port 1 enabled and Port 2 disabled. Metadata/checker output is recommendation-only; unknown or unconfigured games remain Off.

### D-009 — PS1 multitap is manual On/Off, Port 1 only

**Status:** Accepted (2026-09-10)

PrivyHub supports at most four local players. Expose only `Multitap: On/Off` for PS1 games. On maps to Beetle PSX HW Port 1; Port 2 is always disabled and Port 2/Both are rejected as product modes. Do not auto-enable from current `max_players` metadata because the live 80-game PS1 audit identified zero candidates, including CTR and Crash Bash.

### D-010 — Persist wireless ADB recovery in the build/install tool

**Status:** Accepted (2026-09-10)

Wireless-debugging pairing can remain intact while the ONN disappears from both
`adb devices` and ADB mDNS discovery. `build_install_onn.ps1` therefore owns
bounded recovery.

A successful target is cached privately under LocalAppData and never logged.
The final human action, only after automatic recovery is exhausted, is toggling
Wireless debugging Off/On. Pairing is preserved and no address is requested.

### D-010 validation update — wireless ADB recovery

**Runtime status:** Validated (2026-09-10)

The post-patch ADB audit returned `ADB_TARGET_ALREADY_ONLINE` and measured one
online transport plus recovered TLS-connect discovery. The cached-target/mDNS/
reconnect recovery strategy remains accepted and is now runtime validated.

### D-009 validation update — manual PS1 Multitap On/Off

**Runtime status:** Validated (2026-09-10)

CTR joined Crash Bash as a representative four-player PS1 runtime success.
Port 1 was enabled, Port 2 disabled, Players 3/4 exposed, and all four
controllers independent. Manual On/Off remains authoritative; metadata auto
recommendation remains deferred.

### D-011 — A9 is coverage-aware; no-fixture systems are skipped, not faked

**Status:** Accepted (2026-09-10)

A regression prompt is valid only when a real game session exists. If an
emulator family has zero installed game entries, A9 records
`SKIPPED_NO_LOCAL_FIXTURE` and does not ask gameplay questions. This skip may
coexist with a Phase A checkpoint, but the skipped family remains explicitly
not runtime validated until a real fixture is added.

### D-012 — Durable memory in Git; raw runtime evidence local; checkpoint snapshots committed

**Status:** Accepted (2026-09-10)

Keep `docs/memory/` versioned because it is the durable development bridge.
Keep `docs/memory/evidence/raw/` local and ignored. At major checkpoints,
produce one sanitized compressed evidence snapshot with a machine-readable
manifest. The snapshot is immutable checkpoint evidence, not a general runtime
data store.

Do not use Git/Git LFS as PrivyHub user/runtime storage.

### D-013 — Post-Phase-A roadmap prioritizes observability before adaptation

**Status:** Accepted (2026-09-10)

Build a unified diagnostic/health/self-test layer before Sunshine/Moonlight
cleanup and before adaptive streaming. Adaptive local streaming is controlled by
measured end-to-end LAN/Wi-Fi path health, not the router's Internet/WAN speed.
Begin with bitrate-only adaptation while holding resolution and 60 fps stable.

VOD artwork/metadata is a separate local-first media-library phase. OpenBIOS is
a non-blocking portability/customization experiment and must preserve a
compatibility BIOS fallback.

### D-014 — Unified diagnostics adapts existing telemetry and is resource-aware

**Status:** Accepted (2026-09-10)

B1.1 proved that PrivyHub already has extensive subsystem diagnostics but no
common health/event contract. B1 will therefore add a thin normalization and
aggregation layer rather than a second logging stack.

The health contract is resource-aware from its first version. It reuses the
existing 2-second bounded native host telemetry for capture/encoder CPU, memory
and WGC timing; it does not add a duplicate sampler. GPU/encoder-engine/system
RAM/storage/network-capacity fields remain explicitly unavailable until measured.

No hardware tier or stream-profile-fit thresholds will be encoded before the
formal Phase E benchmark suite produces representative evidence.

### D-015 — Health model becomes a read-only companion endpoint

**Status:** Accepted (2026-09-10)

After real B1.2 runtime validation, expose the common health/resource model at
`GET /diagnostics/health`.

The endpoint performs no new sampling. It calls existing in-process status
providers and reuses current or newest-valid host telemetry. If the companion is
restarted, historical resource evidence may be labeled `last_session`; it must
not be presented as live telemetry.

The normalized endpoint remains privacy-minimized and carries no hardware-tier
thresholds until Phase E benchmarks justify them.

### D-016 — Audit client-feedback cadence before adding Android telemetry traffic

**Status:** Accepted (2026-09-10)

The B1.3 health endpoint is runtime validated. Before implementing client
decoder/network feedback, inspect the exact Android native-stream source to
determine whether existing metrics, timers and HTTP/JSON primitives can be
reused.

Do not add a parallel hot loop or duplicate decoder sampler. Diagnostics and
future adaptive bitrate should consume the same low-rate client-health contract.

### D-017 — Reuse existing client metrics tick for bounded health feedback

**Status:** Accepted (2026-09-10)

Publish `privyhub_client_health_v1` every 2 seconds from the existing 500 ms
metrics tick. Add no timer/sampler. Store latest state plus one delta baseline
only. Expose cadence/payload bytes for future optimization. Reuse this contract
for later adaptive bitrate rather than inventing another client telemetry path.

### D-018 — Do not classify any stale output as decoder degradation without rate context

**Status:** Provisional / evidence required (2026-09-10)

B1.5 successfully transported live client telemetry, but its first conservative
decoder rule marks any stale-output delta degraded.

A real interval showed 9 stale outputs while receive cadence was ~59.7 FPS,
network health was clean, FEC unrecoverable groups were zero, and decoder queue
overflow was zero.

Do not replace this with a guessed tolerance. First measure rendered cadence,
stale share, ordinary decoder drops, queue depth and output-gap timing across
multiple intervals. Raw measurements override the classifier during this
investigation.

### D-019 — Stale-output shedding is informational unless decoder-local failure is present

**Status:** Accepted (2026-09-10)

B1.6 measured stale-output drops in every interval while ordinary decoder drops,
queue overflow and queue depth remained zero. Seven of eight intervals had
healthy network state; the one poor interval aligned with upstream FEC/network
impairment.

Therefore nonzero stale-output shedding alone is not decoder degradation.

Decoder degradation remains tied to direct decoder-local evidence:
hardware-decoder unavailability, ordinary decoder drops, or queue overflow.
Stale-only intervals use `VIDEO-DECODER-LOW-LATENCY-SHEDDING` at healthy/info.

No stale-count or FPS tolerance is introduced.

### D-020 — GUI diagnostics is a thin standalone consumer; retention requires measured family scope

**Status:** Provisional pending B1.8 source audit (2026-09-10)

The backend health substrate is runtime validated. Prefer a standalone Android
Diagnostics activity instead of expanding the already-large MainActivity if the
exact UI/manifest context supports it.

The GUI must consume the existing health contract rather than reimplement
classifiers.

Do not apply blanket log cleanup. Measure current log-family pressure first and
exclude durable-memory evidence/checkpoint snapshots from normal retention.

### D-021 — Diagnostics GUI is standalone; retention is manual dry-run-first

**Status:** Accepted (2026-09-10)

B1.8 measured MainActivity at 14,437 lines and confirmed three existing
standalone diagnostics activities plus a ready 11-component health endpoint.

Add a standalone `DiagnosticsActivity`; MainActivity receives navigation only.
The GUI consumes the health contract and does not own performance classifiers.

Retention initially applies only to the measured high/moderate runtime families.
It is not automatic. Default execution is dry-run and future apply requires the
exact policy hash. Durable-memory evidence and patch backups are excluded.

Initial storage caps are provisional operational bounds and may later become
capability-driven during Phase E.


### D-022 — Never apply a blocked retention family

**Status:** Accepted (2026-09-10)

B1.9 dry-run proved the forward family could not reach its cap using eligible files: 322.048 MiB total, 8.870 MiB deletable, 313.178 MiB projected, `blocked=True`. A blocked family is diagnostic evidence, not permission to perform partial cleanup. Audit protected bytes/reasons first; no `--apply` while blocked.

### D-022 — `pktmon_full.txt` is raw capture, not summary evidence

**Status:** Accepted (2026-09-10)

B1.10 measured five old `pktmon_full.txt` files at ~51.8–51.9 MiB each,
protected solely by the blanket `.txt` summary-extension rule.

Introduce a single explicit raw-name override for `pktmon_full.txt`. Keep
newest-minimum protection higher priority, so the newest full packet capture
remains retained. Keep `.txt` protection for all other text evidence.

Do not apply retention until the revised policy produces a reviewed, unblocked
dry-run plan.

### D-023 — Manual retention validated; B3 gated on explicit B1/B2 roadmap audit

**Status:** Accepted (2026-09-10)

The first real retention apply deleted 8 reviewed raw artifacts / 112,619,830
bytes with zero failures and left all managed families below cap.

Automatic retention remains disabled.

Do not start Sunshine/Moonlight inventory/removal merely because Diagnostics GUI
and retention work. First compare the implementation to B1/B2 roadmap
requirements, especially bounded common event history and GUI support-bundle
access.

### D-024 — Completion-gap audit requires semantic source context before implementation

**Status:** Accepted (2026-09-10)

The B1/B2 audit confirmed four explicit roadmap gaps, but token-level results for
audio/controller/RetroArch may under-report generic component-loop coverage.

Do not patch from token counts alone. Inspect exact local Self-Test, service,
health/client-feedback and sanitized-bundle integration context first, then make
one coherent completion patch.

### D-025 — Complete B1/B2 with bounded companion checks and existing bundle path

**Status:** Accepted (2026-09-10)

Use the existing common health model for audio/controller/decoder. Do not
duplicate those checks in the GUI.

Add one dedicated emulator/runtime prerequisite check because `game_session`
does not establish RetroArch executable/core readiness.

Use a 128-entry in-memory event ring; no new sampler.

ADB readiness may execute `adb devices` only. No connect/recovery and no target
identifier output.

The GUI `Collect Diagnostics` action must invoke the existing sanitized bundle
tool, then add safe health/event/version context and revalidate the bundle. Do
not create a second evidence collector.

### D-026 — Diagnostics actions use button-local in-progress labels

**Status:** Accepted (2026-09-10)

B1/B2 runtime validation passed, but TV GUI use showed status-text-only busy
feedback is too easy to miss.

Use the existing `setBusy()` gate to change only the active button label while
a request is running. Keep all action buttons disabled while busy and restore
normal labels when the request completes or fails.

No companion/API behavior change.

### D-027 — B3 is a conservative read-only legacy dependency inventory

**Status:** Accepted (2026-09-10)

Do not start Sunshine/Moonlight cleanup by deleting files. Production execution references remain active until traced. Validated native-path files are MUST PRESERVE even if a specific legacy reference inside them may later be removed.

### D-028 — B4 cut set comes from current call edges, not B3 raw counts

**Status:** Accepted (2026-09-10)

The broad B3 inventory intentionally over-classified uncertain text/path matches
as active. Do not delete from the 236-count set.

Before B4, trace current Games `StreamManager` calls and Android Moonlight
function/caller edges. Group Sunshine runtime/download/setup trees as artifacts.
Treat archive content and RetroArch moonlight-named metadata/shaders as
non-targets unless separate evidence proves otherwise.

### D-030 — Rebuild B4.1 from AST spans, not inferred text anchors

**Status:** Accepted (2026-09-11)

The first B4.1 installer was correctly rejected before modification because a
hand-authored multi-line `games.py` anchor did not match the authoritative local
source.

Do not weaken the hash gate and do not retry. Capture exact source context, then
rebuild the same narrow server-edge cut using semantic AST selection and exact
source spans. The B3.1 architectural cut set remains valid.

### D-031 — B4.1 v2 uses exact AST-selected whole-line spans

**Status:** Accepted (2026-09-11)

The exact source-context audit resolved the earlier preflight failure. Rebuild
B4.1 with structural AST selection against the exact hashed CRLF source.

The installer must compile and reparse the complete generated games.py before
modification and again after installation. Any count mismatch or overlap fails
closed.

### D-032 — Validate server cut before Android client cut

**Status:** Accepted (2026-09-11)

B4.1 runtime validation proved the native Games path works with no Sunshine
process after removing `GamesPlugin -> StreamManager`.

Proceed to Android Moonlight removal as a separate patch. First capture exact
function bodies, callers and manifest context. Artifact cleanup remains a later
step.

### D-033 — Remove evidenced Android edge, audit helpers afterward

**Status:** Accepted (2026-09-11)

B4.2 removes only the exact captured Moonlight/com.limelight launcher/query and
stale stream_host response/UI branches. Uncaptured helper definitions and
physical legacy artifacts require a later orphan-reference audit.

### D-034 — Orphan-reference audit gates physical legacy cleanup

**Status:** Accepted (2026-09-11)

B4.1 and B4.2 are both runtime validated. Do not immediately delete
stream_manager.py, Android helper definitions, setup scripts, downloads or the
Sunshine runtime.

First prove which items have zero current product callers/importers and separate
diagnostic/historical references from product execution. Cleanup follows that
focused evidence.

### D-035 — Split code-orphan cleanup from physical artifact cleanup

**Status:** Accepted (2026-09-11)

B4.3 proves two Android helpers and stream_manager.py are orphans with exact
hashes. Remove them in B4.4.

Sunshine/Moonlight runtime/download/setup groups have only inventory size/path
evidence. Do not delete them until a separate exact hash-manifest diagnostic is
captured.

### D-036 — Hash physical artifacts and external legacy state before deletion

**Status:** Accepted (2026-09-11)

Before deleting Sunshine/Moonlight runtime/download/data/script artifacts,
capture exact per-file SHA-256 manifests. Also check Sunshine
process/service/task/firewall state and the temporary Moonlight Android package
on already-connected targets.

### D-036 — B4.6 deletes exact B4.5 project groups; device package state stays separate

**Status:** Accepted (2026-09-11)

B4.5 provides exact hashes for nine project legacy groups and clean Windows system state. B4.6 may delete those groups after exact revalidation and backup. ADB unavailability means installed `com.limelight` state remains unverified.

### D-037 — Reuse validated private ADB recovery for device cleanup verification

**Status:** Accepted (2026-09-11)

The B4.6 PATH-only ADB check was insufficient. B4.7 reuses the established
build/install ADB discovery and private cached-target/mDNS recovery pattern.

The diagnostic verifies PrivyHub on the resolved target before checking
`com.limelight`, logs no identifier/address, and performs no uninstall.

### D-038 — Remove only com.limelight before B5

**Status:** Accepted (2026-09-11)

B4.7 confirms the temporary Moonlight client remains installed on the correct
paired onn. Remove only `com.limelight`.

B5 begins only after re-query proves PrivyHub remains present and Moonlight is
absent. Device identifiers and addresses remain private.

### D-039 — Verify B4.8 removal with package-list semantics

**Status:** Accepted (2026-09-11)

The first B4.8 action returned adb uninstall success, preserved PrivyHub, and
observed no Moonlight package path, but `pm path` nonzero status caused a false
`PACKAGE_QUERY_FAILED`.

Do not uninstall again. Re-verify with `pm list packages` / `cmd package list
packages` and accept absence only when the query itself succeeds and no exact
Moonlight package line is returned.

### D-040 — B5 is one focused post-removal session regression

**Status:** Accepted (2026-09-11)

Do not rerun every exploratory Phase A probe.

B5 uses one representative session and combines objective runtime evidence with
explicit operator confirmation for picture/audio/input behaviors not provable
from current server telemetry. A known isolated cheat/profile path is sufficient
for the roadmap's representative cheat/mod/profile regression.

### D-041 — Audit exact Phase B tree before staging

**Status:** Accepted (2026-09-11)

B6 uses a diagnostic-only repository audit before any staging. The final
checkpoint allowlist must be generated from the reviewed local status result,
not inferred from package history and not produced by `git add .`.

Root ROADMAP.md remains at the pushed v2 baseline during the audit and is
updated only in the final checkpoint change.

### D-041 — Evidence-backed inert B6 legacy-text exception

**Status:** Accepted (2026-09-11)

The B6 scanner found one `stream_host` textual occurrence at MainActivity line
7683. The exact source hash already passed B4 Android-edge/orphan cleanup and
the complete B5 native-only regression. Treat only this exact
path/line/pattern/hash tuple as inert text. Any drift fails the audit.

### D-042 — Durable-memory manifest does not self-hash

**Status:** Accepted (2026-09-11)

Remove `manifest.json` from its own `files` list. A conventional final-file
SHA-256/byte-count self-entry is recursive. Continue exact validation of every
other durable-memory entry.
