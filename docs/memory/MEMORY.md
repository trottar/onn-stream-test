---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Curated Project Memory

## Mission

PrivyHub is a local-first, privacy-preserving, modular smart-home/media experiment. The current prototype uses a Windows companion/server and an inexpensive onn Android TV client on an isolated secondary network. The design is intended to evolve toward inexpensive Linux-capable server hardware and additional clients without mandatory cloud, subscriptions, or proprietary infrastructure.

## Current baseline

`e65e8f89` is the clean, pushed checkpoint completing the Phase A
emulator subsystem.

Phase A is closed absent regression evidence. SNES and extensive PS1 behavior
are runtime validated. NES and Genesis had zero local A9 fixtures and remain
supported/configured but explicitly not runtime validated until real content is
added.

`docs/ROADMAP.md` v2 is the authoritative post-Phase-A roadmap. Phase B
Diagnostics & Clean Native Baseline is next.

## Stable Games path

Native game streaming uses Windows Graphics Capture, H.264 NVENC, 720p60, 7 Mbps, short GOP, RTP-sized packets, 8+1 XOR FEC, process-specific game audio, Android hardware AVC decoding, and a separate UDP controller transport. These working paths are preservation boundaries until evidence says otherwise.

RetroArch is the managed emulator frontend. Current cores: FCEUmm (NES), bsnes (SNES), BlastEm (Genesis), and Beetle PSX HW (PS1).

## Controller architecture

Current validated two-player path:

`Android controller state -> PHI1 UDP full-state packet -> Windows NativeControllerBridge -> persistent ViGEm VX360 devices -> RetroArch ports`.

The PHI1 packet is 36 bytes and carries one player index per packet. The exact-local source audit on 2026-09-10 classified the protocol as reusable for P3/P4: the two-player limits were sender/receiver counts and literal bookkeeping arrays, not packet structure. The four-player base patch preserves PHI1 v1 while generalizing Android assignment/sending and Windows ViGEm state to four players. Its isolated runtime probe confirmed four XInput slots, exact synthetic P1-P4 routing, 120/120 packets with zero loss/rejection/bad packets, neutral release, and clean slot teardown. Real Android four-controller assignment is runtime validated: four distinct physical controllers reached XInput slots 1-4 exactly in first-touch order, with isolated A presses, confirmed releases, four-slot continuity, and a neutral final state. RetroArch P1-P4 enumeration is also runtime validated: a fresh normal game startup configured Xbox 360 Controller in ports 1-4 with the xinput driver and no startup fallback.

All intended virtual controllers must exist before RetroArch initializes input. The A8 controller-preflight ordering fix is proven and must remain intact.

## A8 mapping

A8 sits after canonical XUSB/ViGEm semantics and before RetroArch/libretro gameplay bindings. It uses named reusable profiles and session-only RetroArch overrides. Save/Load/Pause/End are meta controls outside gameplay remapping. The editor is Xbox-oriented and enforces a complete one-to-one mapping per player.

The P3/P4 extension keeps input-profile schema 1 for backward compatibility. Existing P1/P2 profiles normalize to Player 1-4 with empty P3/P4 mappings, preserving RetroArch default autoconfiguration until those players are explicitly edited. New/reset profiles can carry complete mappings for all four players, and the Android editor derives supported players from companion capabilities. Runtime validation of this extension is complete. The live schema stayed at 1; every inspected profile exposed P1-P4 keys; legacy P1/P2 data normalized to four; generated P3/P4 bindings and four-port analog-D-pad settings were present; the Android editor exposed all four player actions and copy-from-another-player; and the user successfully synchronized custom mappings across all four players.

## Closed work

A1 controller/analog, A2 Save/Load, A3 pause/resume, A4 host coexistence/audio lifecycle, A5 direct-launch UX, A6 organization/metadata/art, A7 cheats/mods, and A8 input mapping are closed absent regression evidence.

The severe prototype UDP burst/gap/duplication investigation is deferred to representative Linux/network infrastructure unless it again becomes a blocker.

## Post-Phase-A roadmap

Phase B first unifies diagnostics/self-test/support bundles, then removes
Sunshine/Moonlight and proves a clean native-only baseline. Phase C makes stream
profiles explicit and adds end-to-end telemetry, adaptive bitrate, optional
adaptive FEC, 1080p60 characterization and generalized native sources. Phase D
adds local-first VOD artwork/metadata UX. Phase E performs formal resource/Linux
hardware characterization and replays the deferred UDP acceptance suite. Phase
F is an optional OpenBIOS/open-platform portability track; Phase G is broader
smart-home/client expansion.

For local adaptive streaming, use measured LAN/Wi-Fi path health rather than
router WAN/Internet capability. Preserve 60 fps/resolution initially and adapt
bitrate first.

## Durable project rules

Canonical ROMs and normal save namespaces are protected. Cheat/mod profiles remain isolated. Diagnostics should trust raw measurements over incorrect classifiers. Runtime/log/user-content directories stay separate from source control. New work should reuse proven paths rather than create parallel implementations.

## Four-player regression closure

The post-extension 1P regression is runtime validated. In a normal PS1 session, P1 physical A reached only XInput slot 1, gameplay remained normal, no other controller took over Player 1, RetroArch stayed on xinput without fallback, and normal End/Exit removed all session XInput slots. The active regression boundary is now 2P, then representative 4P gameplay.

## Post-extension 2P regression

The 2P regression is runtime validated. In a normal Crash Bash PS1 session, P1 physical A reached only slot 1 and P2 physical A reached only slot 2; both players worked independently, P3/P4 did not interfere, RetroArch remained on xinput with no fallback, and normal End/Exit removed all session XInput slots. The only gameplay-specific gate before A9 is representative 4P gameplay.

## Representative 4P host-routing result

The Crash Bash four-player gameplay probe proved exact P1->1, P2->2, P3->3, and P4->4 routing in a normal session with RetroArch ports 1-4 present and no XInput fallback. Crash Bash nevertheless greyed out Players 3 and 4 and no explicit Beetle PSX HW multitap option was found under the managed RetroArch data tree. Therefore the active blocker is above the validated PrivyHub transport/device/A8 stack: PS1 multitap/core-option session configuration. Do not reopen lower controller layers without contradictory new evidence.

## PS1 multitap core-option storage

The active RetroArch nightly writes Beetle PSX HW options to `runtime/emulators/retroarch-nightly-20260907/config/Beetle PSX HW/Beetle PSX HW.opt`; Port-1 and Port-2 multitap are explicitly disabled. `emulator_manager.py` currently has no core-options path/game-specific options/global core-options/max-player handling. Preserve global PS1 topology; the intended fix must be session/game-specific.

## PS1 multitap architecture

Representative four-player Crash Bash host routing is runtime validated, but the game initially exposed only two players because the active Beetle PSX HW core options explicitly disabled multitap on both physical PS1 ports. The chosen architecture reuses `data/games/retroarch/controller_overrides.json`: a per-game `ps1_multitap` mode controls native content-specific Beetle core options. The generated `<game>.opt` preserves every existing game/core option and changes only `beetle_psx_hw_enable_multitap_port1` / `port2`. Managed sessions explicitly enable RetroArch content-specific core options. Ordinary PS1 sessions preserve their prior two explicit libretro-device assignments; a multitap-enabled session assigns the selected PS1 device to users 1-4. Crash Bash is the first `port1` validation record.

## PS1 multitap rollback finding

The first game-specific multitap patch made Crash Bash expose Players 3 and 4, so the core-option concept is functionally relevant. However, the same post-patch runtime had four host XInput/RetroArch ports present while physical P2-P4 produced no XInput activity, and the user observed only 2-3 charged controllers remaining connected during the active PrivyHub/game-stream session while all four stayed connected with the session off. Treat this as a causal regression candidate, not as proof of Bluetooth mechanism. The authoritative next step is exact rollback plus repeat of the previously validated four-controller assignment probe before redesigning multitap.

## Multitap rollback comparison

Exact rollback removed Crash Bash multitap as expected but did not restore four physical controllers: P1-P3 still mapped cleanly while P4 produced no host input. This weakens the causal case against the multitap implementation. The game-specific multitap path can be restored for continued 4P testing, but physical-controller stability during the active Android game-stream session remains an independent unresolved issue.

## Final four-player acceptance

A replacement physical controller restored exact Android P1-P4 -> XInput 1-4 assignment while multitap was enabled. The final Crash Bash Battle Mode probe confirmed four human-player exposure and independent in-game control for all four controllers, no cross-control, RetroArch ports 1-4 on xinput without fallback, and clean normal teardown. The prior dropout persisted once with multitap rolled back and did not reproduce with the replacement controller, so it is not evidence of a PrivyHub multitap/software regression. Preserve it as a controller-specific/pairing/transient Bluetooth observation unless it reproduces with representative devices.

## 2026-09-10 A9 installer v1 preflight correction

`privyhub_phase_a_a9_regression_probe_01_2026-09-10` correctly returned **FAILED BEFORE MODIFICATION** before installing anything because its runtime-evidence preflight compared exact reconstructed chat-log bytes to the authoritative Windows log bytes. The visible successful measurements were unchanged; the gate was too strict about byte representation. A9 v2 replaces that check with semantic validation of the required classifications and raw measurements while leaving the A9 runtime probe itself unchanged.

## PS1 four-player accessory policy

PrivyHub's supported local-player ceiling is four. For PS1, the only user-facing multitap state is On/Off. On maps to Beetle PSX HW Port-1 multitap enabled with Port-2 explicitly disabled. Port-2/Both are not product options. Metadata may recommend multitap for titles with more than two local players, but recommendations are advisory; behavior remains Off until explicitly enabled for that game. This prevents metadata errors from silently changing controller topology.

## PS1 multitap product rule

PrivyHub's PS1 local-player ceiling is four. The supported user-facing multitap control is therefore On/Off only. On always means Beetle PSX HW Port 1 multitap enabled and Port 2 disabled. Port 2/Both are not valid PrivyHub modes. Multitap is a manual per-game setting because the 2026-09-10 audit found zero `max_players > 2` candidates across 80 PS1 entries, including known four-player CTR and Crash Bash. Do not auto-enable from current metadata.

## Wireless ADB build-tool rule

`tools/build_install_onn.ps1` must not assume a paired wireless-debugging device is already present in `adb devices`. Wireless ADB discovery/reconnection is an expected transient lifecycle. The build/install tool should eventually own bounded recovery using ADB-supported mDNS/server state, without asking the user for or logging network addresses. Do not persist or expose discovered endpoints.

## ADB diagnostic rule

Do not infer that ADB is absent from the 2026-09-10 v1 wireless-recovery probe
failure. That probe failed to parse `PrivyHub/local.properties` because its
`sdk.dir` regex was double-escaped. The PowerShell build script had already
located ADB in the same session. Use the corrected non-regex parser in audit
v2 and preserve the v1 event as a diagnostic-tool failure.

## Wireless ADB recovery rule

Do not fail immediately when `adb devices` is empty. The validated failure state
had healthy ADB/mDNS but zero services/transports despite intact pairing.

Recovery order:
1. private last-known target from LocalAppData;
2. existing online physical transport;
3. ADB mDNS TLS-connect discovery;
4. `adb reconnect offline`;
5. one local ADB-server restart plus bounded retry;
6. one user-assisted Wireless debugging Off/On retry, preserving pairing.

Network-bearing target data stays outside the repository under LocalAppData and
must never be printed, logged, or copied into durable memory.

## Wireless ADB recovery validated state

The 2026-09-10 persistent wireless-ADB recovery patch is runtime validated:
post-patch audit classified `ADB_TARGET_ALREADY_ONLINE`, with one TLS-connect
service, one online transport, and no offline/unauthorized transports. Treat
`tools/build_install_onn.ps1` cached-target/mDNS/reconnect recovery as the
current authoritative build/install path. Reopen only if the new path itself
fails in a future representative run.

## CTR Multitap validation

`PS1_MULTITAP_ONOFF_CTR_CONFIRMED` on 2026-09-10 establishes that the manual
PS1 Multitap On/Off feature works beyond Crash Bash. CTR launched with Port 1
enabled, Port 2 disabled, all four XInput slots live, Players 3/4 exposed, and
four independent controllers. The feature is COMPLETE/runtime validated.
Metadata-driven recommendation remains deferred.

## A9 identification rule

The first A9 full regression passed all user/runtime stages except NES and
Genesis machine identification. Those two titles were `<unknown>` because the
probe relied on `/plugins/games/status` providing a game id/system before
locating the RetroArch log. Corrected A9 identification may fall back to the
newest fresh RetroArch game log whose `System:` field matches the expected
family, then validate port-1 XInput autoconfig and no startup fallback.
Do not require users to repeat already-passed A9 stages merely to repair this
diagnostic gap.

## Runtime-test evidence integrity

Never treat a yes/no gameplay prompt as runtime evidence when no game was
actually launched. On 2026-09-10 the user clarified that no NES or Genesis games
were installed during the A9 attempts; those yes responses are invalidated.

A9 is coverage-aware: a family with zero current library entries may be
`SKIPPED_NO_LOCAL_FIXTURE`, but that family remains explicitly **not runtime
validated**. When a game is later added, run its normal launch/input/teardown
regression before upgrading its runtime status.

Current coverage:
- SNES: runtime exercised in A9;
- PS1: runtime exercised broadly, including 1P/2P/4P, lifecycle, profiles,
  cheats, and multitap;
- NES: configured/development path present; no current runtime fixture;
- Genesis: configured/development path present; no current runtime fixture.

## Repository evidence boundary

Commit source, configuration, durable engineering memory, reusable diagnostics,
and curated evidence. Keep operational/user/runtime data out of Git.

`docs/memory/evidence/raw/` is a local working-evidence store and is ignored.
At major checkpoints, create a sanitized immutable compressed snapshot under
`docs/memory/evidence/snapshots/` with a manifest containing per-file SHA-256
and byte size. Snapshot construction fails closed on detected network
identifiers/secrets or excessive size.

Do not commit ROMs/ISOs, saves/states, emulator runtime trees, media libraries,
ordinary logs, patch backups, APK/build output, private ADB target cache, or
other user/runtime data.

## Phase A checkpoint acceptance

A9 final state is `PHASE_A_A9_CHECKPOINT_READY_WITH_NO_FIXTURE_SKIPS`.
Available-library regression is complete. NES and Genesis have zero local
fixtures and remain explicitly not runtime validated. SNES and PS1 have actual
runtime coverage; PS1 includes validated 1P/2P/4P routing, lifecycle, profiles,
cheats/mods, Crash Bash/CTR Port-1 multitap, and teardown.

## Diagnostics architecture direction

Existing subsystem probes/logs should converge on a structured diagnostic
event/health model with stable codes, raw measurements kept separate from
classifiers, bounded local history, GUI Diagnostics/Self-Test, and a one-click
sanitized bundle. This is the next architectural foundation because adaptive
streaming will require explainable state changes.

## VOD artwork direction

VOD artwork should be recursive and local-first. Prefer sidecar
`<video-stem>`/`poster`/`folder` images, then optional cached metadata-provider
art, then local thumbnail/generic fallback. Playback must never depend on an
external metadata service.

## OpenBIOS direction

OpenBIOS is attractive for redistribution, region independence, source-level
inspection/customization, and future appliance portability. It is not expected
to materially improve normal game frame rate or stream latency. Keep the
current compatibility BIOS path and evaluate OpenBIOS through an explicit
compatibility/save/boot matrix before any broader default.

## B1 diagnostics architecture

B1.1 runtime inventory confirmed that low-level instrumentation already exists.
The architectural gap is a cross-subsystem health/event model, not missing raw
logs.

Use an adapter/aggregator approach. Preserve detailed subsystem telemetry as
evidence and classify it separately. Stable component fields are `subsystem`,
`component`, `health`, `severity`, `event_code`, `summary`, `measurements` and
classifier/basis metadata. `unknown` is not synonymous with failure.

Resource/optimization infrastructure begins in B1. Reuse the existing bounded
2-second native host telemetry sampler instead of creating a second sampler.
Expose capture/encoder CPU and memory plus WGC timing in a stable resource
snapshot. Keep GPU/encoder-engine/system RAM/storage/network capacity explicit
as unavailable until implemented. Do not classify hardware tiers or stream
profile fit until Phase E representative benchmarks establish thresholds.

B1.1 also measured substantial local diagnostic growth (transport history
already hundreds of MB). Directory-level retention is therefore a required B1
item before expanding always-on history.

## B1.2 validated resource snapshot

The real B1.2 idle snapshot recovered 41 last-session resource samples at a
2-second cadence. Capture/encoder CPU and memory observations are useful
optimization evidence, but remain descriptive rather than tier thresholds.
`current_session` versus `last_session` provenance must remain explicit.

The common health model is approved for read-only API integration.

## B1.3 health endpoint runtime validation

`GET /diagnostics/health` is runtime validated. After companion restart it
correctly recovers existing host telemetry as `latest_history` /
`last_session`, starts no new sampler, and passes the normalized privacy
contract.

Before adding client telemetry, audit exact Android metrics/cadence/network
source. Reuse existing client measurement machinery where possible; do not add
a duplicate hot loop.

## B1.5 client-health contract

Reuse Android's existing native-stream metrics tick. Initial client-health
cadence is 2 seconds with one in-flight request maximum. The companion validates
a strict numeric/boolean whitelist and stores latest state plus one previous
baseline only.

Do not add a duplicate decoder/resource sampler or persistent client-health
sample log. Expose cadence/payload size so diagnostics overhead is measurable.
This contract is the intended future input for adaptive bitrate.

## B1.5 runtime feedback result / classifier caution

The client-health transport is runtime validated at a measured 631-byte payload
every 2 seconds with no duplicate sampler. A single B1.5 interval reported 9
decoder stale-output drops while receive FPS remained ~59.7, network health was
healthy, FEC unrecoverable delta was zero, and queue overflow was zero.

Do not equate any nonzero stale-output count with product-visible degradation
without rendered-cadence/context evidence. During classifier investigations,
trust the raw measurements over the classifier.

## B1.6 decoder classifier evidence

Multi-interval runtime evidence established that stale-output shedding alone is
not a decoder-local fault. Direct decoder-local health remains based on hardware
decode availability, ordinary decoder drops and queue overflow. Preserve stale
counts as measurements and do not invent a numerical stale/FPS tolerance.

## B1.7 classifier runtime validation

The corrected decoder classifier is runtime validated. Stale-only low-latency
shedding remains healthy/info, including when the network component is
independently degraded. This avoids cross-subsystem double-counting.

The health substrate is ready to become a GUI consumer contract. The GUI should
show health plus measurement context rather than hiding informational shedding.

Before applying retention, inventory exact current log-family size/count and
existing cleanup mechanisms. Never automatically delete curated
`docs/memory/evidence/` or local raw durable-memory evidence as part of normal
runtime log retention.

## B1.8/B1.9 GUI and retention

The validated health model is now suitable for a thin user-facing Diagnostics
activity. Keep classification in the companion; the Android screen renders
health, event codes and measurement context and performs only structural/current
health Self-Test checks.

MainActivity is already 14,437 lines, so add navigation only and keep diagnostics
in its own activity.

Runtime retention must be allowlisted and dry-run-first. Initial scope is
forward transport, reverse transport and debug bundles. Never include
`docs/memory/` or patch backups. Automatic deletion remains disabled until the
real candidate plan is inspected. Phase E can later scale budgets by host
storage/capability.


## B1.9 runtime result / retention safety rule

The standalone Diagnostics GUI is runtime validated on the onn and consumes the common health model without a parallel sampler/classifier.

The first retention dry-run failed closed rather than deleting evidence: forward transport remained above its cap after all eligible files because 43/58 files were protected. Never apply a retention plan whose family reports `blocked_by_protected_evidence=True`. Audit protected bytes/reasons first and change protection semantics only from measured evidence. Reverse transport and debug bundles were already below their provisional caps.

## B1.10 retention blocker semantics

Do not treat file extension alone as evidence semantics. `pktmon_full.txt` is a
raw packet capture despite its `.txt` suffix.

Retention rule: explicit raw-name classification may override blanket summary
extension protection, but newest-minimum protection remains higher priority.
Do not globally unprotect `.txt`.

Any retention-rule change must first be validated by a new dry-run plan. Do not
apply deletion while a plan reports blocked-by-protected-evidence.

## B1.12 retention apply

Manual diagnostic retention has completed one real apply successfully under the
reviewed policy. The post-apply plan is empty and unblocked for every managed
family. Keep automatic retention disabled until a later explicit product
decision.

Do not consider B1/B2 globally complete merely because health, GUI, and
retention are validated. Compare implementation to the roadmap requirements
before beginning Sunshine/Moonlight removal work.

## B1/B2 completion gate

The roadmap gap audit is authoritative for missing B1.3/B2 features, but
token-level absence is not sufficient to infer missing semantic coverage.
Inspect the exact Self-Test loop before duplicating audio/controller/emulator
checks.

Before implementing event history or GUI bundle collection, inspect exact local
service/health/client-feedback/debug-bundle integration points. GitHub may be
behind the local authoritative tree.

## B1/B2 completion implementation rules

The Self-Test GUI is a consumer of the companion diagnostic contract. Keep
audio/controller/decoder classifications in the existing health model rather
than duplicating them.

`game_session` is not a complete emulator prerequisite check. A bounded
Self-Test may verify configured RetroArch executable, cores and config location
without launching or changing an emulator session.

ADB Self-Test is development-only readiness. It may resolve adb and run
`adb devices`, but must never connect/recover a target, return target
identifiers, or log network addresses.

The common event history is bounded in memory at 128 records. Record component
classification transitions and meaningful nonzero client-feedback pulses; keep
raw measurements distinct from classification. Do not start another timer or
sampler.

The GUI bundle action must reuse the existing sanitized bundler. The bridge may
append generated safe diagnostic context/version metadata, update manifest
hashes and rebuild/revalidate the ZIP, but must not include raw packet captures.

## Diagnostics GUI action feedback

For Android TV asynchronous diagnostics actions, status text alone is not
sufficiently visible feedback. The active button should change its own label
immediately while the request is in flight, while all action buttons remain
disabled against duplicate execution.

This is presentation-only. Do not alter companion endpoints, classifiers,
sampling, bundle semantics or stream/session behavior for this polish.

## B3 legacy-streaming inventory rule

Begin Sunshine/Moonlight removal with evidence, not deletion. Treat executable production references conservatively as active until traced. Keep documentation/history separate from runtime dependencies. Keep install/firewall/task remnants distinct from production code. A legacy reference inside a validated native-path file never makes the whole file removable; preserve the file and remove only a proven-obsolete reference in B4.

## B3 inventory interpretation

Broad static term counts are not removal authority. Archive backups, files
inside a vendored runtime tree, and unrelated name collisions can inflate
ACTIVE classifications.

For B4 authority, prefer:
1. current production call edges;
2. current source/config references;
3. grouped legacy runtime/setup artifacts;
4. system-state evidence.

Known non-target name collisions:
- RetroArch `moonlight_libretro.info`;
- RetroArch `stellabialek-moonlight-sillyness` shaders;
- B3 diagnostic package filenames.

Do not delete these merely because they contain the word `moonlight`.

## Production patch source-context rule

A current-file SHA plus isolated trace lines is not enough to author brittle
multi-line text anchors. Before a production transform that removes several
blocks from a large file, capture exact local source context for every modified
AST/span.

Prefer semantic AST selection + exact source spans over hand-authored whitespace
anchors. Preserve the original BOM/newline convention and reject if the exact
predecessor hash changes.

If an installer fails with code 2 before modification, treat it as a preflight
rejection, not a runtime failure; do not continue to runtime probes that were
supposed to be installed by that package.

## AST-span production transformation pattern

When exact source context is available, production edits to large Python files
should use AST semantics to identify whole removable statements/blocks, then
apply line-span changes against the exact hashed predecessor.

For B4.1 specifically, distinguish the nested Sunshine launch Try from the
outer request Try by requiring the selected Try to have a direct
`except StreamHostError` handler. The outer handler is a tuple
`(EmulatorError, StreamHostError)` and is rewritten, not deleted.

Generated source must preserve the original CRLF convention and compile before
any write.

## B4.1 runtime fact

The current normal Games path no longer reaches Sunshine. A live representative
game remained active with `windows_graphics_capture`, `h264_nvenc` and
`rtp_udp_xor_fec`; no Sunshine process was running.

`stream_manager.py` remains only as a physically retained orphan candidate until
later artifact cleanup.

## B4.2 boundary

Android Moonlight removal is an independent edge. Capture exact current function
bodies/callers and manifest query before editing. Do not combine Android UI
removal with runtime/download/setup artifact deletion.

## B4.2 Android cut rule

Remove the exact captured Moonlight/com.limelight launcher/query and the stale
stream_host response/UI fallback paths that became unreachable after B4.1.

Do not infer deletion safety for helper definitions whose exact bodies were not
captured. Audit them after B4.2 runtime validation.

Preserve MainActivity CRLF and AndroidManifest LF.

## B4.2 runtime fact

The Android Moonlight/com.limelight client edge is removed and runtime
validated. MainActivity and manifest are clean, B4.1 games.py is unchanged, and
native streaming remained active.

Before deleting legacy files, distinguish:
- active production references;
- orphan helper definitions;
- maintenance/setup scripts;
- diagnostic/historical tool references;
- physical runtime/download payloads;
- RetroArch Moonlight-name collisions, which remain non-targets.

## Legacy cleanup staging rule

B4.3 proves code orphans separately from physical artifact groups.

It is safe to remove the two exact-hash Android helper functions and
`stream_manager.py` as one code-orphan patch.

Do not delete Sunshine/Moonlight runtime/download/setup groups from only a
path/size inventory. Capture exact per-file/hash manifest first, then use it as
the predecessor for physical deletion.

## B4.4 runtime fact

The product starts and streams normally after physical deletion of
`stream_manager.py` and removal of both orphan Android stream-host helpers.

Physical legacy cleanup still requires an exact content manifest. Include
machine-level Sunshine state and already-connected Android Moonlight package
presence so cleanup cannot strand firewall rules or the installed temporary
client.

## B4.5 physical deletion rule

Use the B4.5 canonical group digest (sorted project-relative path + bytes + per-file SHA-256) as deletion authority. Back up all targeted bytes under archive/patch_backups before delete and verify rollback against the original digests. Project cleanup does not imply Android package cleanup when ADB state is unavailable.

## Canonical physical-manifest implementation rule

B4.5/B4.6 group hashing uses actual separator bytes:
- NUL `b"\0"`
- newline `b"\n"`

Do not substitute literal backslash-character sequences `b"\\0"` or
`b"\\n"`. B4.6 v1 did so and correctly failed closed before modification.
Cross-version manifest-equivalence fixtures are required for this cleanup path.

## Legacy name-collision classification rule

The B4.5 non-target matcher is authoritative:
- `^runtime/emulators/.*/moonlight_libretro\.info$`
- `^runtime/emulators/.*/stellabialek-moonlight-sillyness\.`

When these are represented as Python raw regex strings, use a single regex
escape before the literal dot (`\.` in regex notation), not a doubled
backslash that would require an actual backslash in the path.

The installer must additionally treat the exact B4.5 non-target path list as a
hard preservation allowlist and verify every path still exists after cleanup.

## Android package verification rule

Do not interpret `ADB_UNAVAILABLE` from a PATH-only probe as proof that project
ADB tooling is unavailable.

For device cleanup verification, reuse the established build/install ADB
discovery path:
- PATH;
- ANDROID_SDK_ROOT / ANDROID_HOME;
- PrivyHub/local.properties sdk.dir;
- private cached target recovery;
- mDNS recovery.

Never log the cached target, serial, network address, or mDNS instance.
Confirm the resolved device contains the PrivyHub package before querying
`com.limelight`.

## Device package cleanup rule

When removing the obsolete Moonlight Android client:
1. privately resolve the paired onn;
2. verify `com.safeiot.privyhub` is present;
3. verify `com.limelight` is present;
4. uninstall only `com.limelight`;
5. immediately verify PrivyHub remains present;
6. immediately verify Moonlight is absent;
7. never log the target identifier or network address.

Do not proceed to B5 until the final package state is verified.

## Android package absence verification rule

Do not use `adb shell pm path <package>` as the sole absence verifier. Some
Android builds return a nonzero shell status when the package does not exist,
which can turn a valid absence into a false query failure.

For final package-state verification use:
1. `pm list packages <package>`; or
2. `cmd package list packages <package>` as fallback.

A successful command with no exact `package:<name>` line means the package is
absent. B4.8 first action exposed this distinction after a successful uninstall.

## B4 clean-native predecessor

B4 is complete as of 2026-09-11.

Authoritative clean-native facts before B5:
- no active Sunshine/Moonlight server dependency;
- no Android Moonlight launch edge;
- no `stream_manager.py`;
- no project Sunshine/Moonlight runtime/download/setup artifacts;
- no Windows Sunshine process/service/task/firewall residue;
- no installed `com.limelight` on the paired onn;
- PrivyHub remains installed;
- native Games streaming is WGC -> NVENC -> RTP-sized UDP + XOR FEC ->
  Android hardware decode.

B5 should validate this architecture as a normal-use session, not reopen B3/B4.

## B5 classifier correction

B5 post-removal regression is runtime validated.

Do not use `post_profile_native_ok` as a required B5 pass gate. Profile/UI
navigation may close the native stream client while leaving the managed game
session active. Keep the post-profile host status as lifecycle evidence only.

For continuity adjudication, prefer decoder/session measurements over a single
host status bit. The validated B5 session had:
- 148103 video packets;
- 0 video packet loss;
- 10551 video frames;
- 10551 queued decoder frames;
- 10041 rendered frames;
- 509 stale-output drops;
- 1 frame in flight;
- 0 decoder drops;
- 0 unrecoverable FEC groups;
- 176503 ms decoder duration.

This exactly supports a healthy stream through the client/profile transition.

## B6 checkpoint rule

Before staging a Phase B checkpoint, run a read-only repository audit and review
the exact local status list. The local working tree remains authoritative.

B6 audit acceptance requires: clean diagnostic evidence chain, no active legacy
production references, no tracked raw evidence, no unexpected status entries,
`git diff --check` PASS, Python syntax PASS, Android Kotlin compile PASS, and
remote main still at the expected predecessor.

Do not let a broad `git add .` decide checkpoint scope. Build the final staging
allowlist from the reviewed B6 audit result.

## Repository-audit ROADMAP rule

Do not exact-hash-gate a working-tree documentation file merely because it was
copied into an earlier package-building environment.

For B6:
- exact-hash production source and durable memory;
- require working `docs/ROADMAP.md` to exist and remain byte-identical across the
  audit installer;
- hash committed `HEAD:docs/ROADMAP.md` separately against the known pushed baseline;
- use Git diff semantics to determine whether the working roadmap has a
  substantive uncommitted change.

This avoids confusing line-ending/local-working-copy differences with invalid
project state while still failing closed on production-state drift.

## Phase B checkpoint

Phase B is complete and pushed.

Validated baseline:
- unified diagnostics/health/Self-Test/support bundle/retention are established;
- Sunshine/Moonlight active architecture and physical project artifacts are
  removed;
- Android `com.limelight` is absent while PrivyHub remains installed;
- Games passed the native-only WGC/NVENC/RTP-UDP-XOR-FEC regression;
- repository scope was audited with zero unexpected/pre-staged paths;
- Python and Android Kotlin compilation passed;
- `docs/ROADMAP.md` advances Phase C to NEXT.

Manifest rule: `manifest.json` is excluded from its own conventional `files`
hash/byte list. All other durable-memory entries remain strictly validated.

Legacy scan rule: the exact MainActivity path/line/pattern/hash tuple recorded by
B6 is inert text. Any additional occurrence, or the same occurrence under a
different source hash, is a regression.


## Roadmap v3 durable direction

The accepted roadmap after the Phase B checkpoint is:

- C: adaptive streaming architecture;
- D: media/VOD plus substantive Live TV channel/EPG cleanup;
- E: Linux migration to the HP EliteDesk 805 G6 reference prototype;
- F: optimize/measure the Linux core with NES/SNES/Genesis/PS1 only, then select
  Prototype 2 from evidence;
- G: user-content import followed by N64/GameCube/PS2 feasibility;
- H: home infrastructure, clients and providers;
- I: deterministic/local intelligence first, optional privacy-aware external AI.

Game-content rule:
PrivyHub does not provide, download, redistribute, or silently substitute ROMs,
ISOs, BIOS/firmware, keys, or equivalent game content. User content is imported
through explicit tooling and remains outside Git/support bundles.

OpenBIOS is no longer a roadmap requirement.

Cloud-AI rule:
external providers such as OpenAI or Anthropic are optional user-configured
providers, never core dependencies. Local failure must never silently become a
cloud upload. Models may request registered PrivyHub actions but do not receive
arbitrary machine/device authority.
