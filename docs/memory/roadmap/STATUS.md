---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: e65e8f89604ce325e6e3e0537d0287070b8996c5
---

# Authoritative Roadmap Status — 2026-09-10

This file is the compact status companion to `docs/ROADMAP.md` v2.

| Phase | Status | Immediate meaning |
|---|---|---|
| **A — Emulator Subsystem** | **COMPLETE / PUSHED** | Checkpoint `e65e8f89` |
| **B — Diagnostics & Clean Native Baseline** | **NEXT** | Unified diagnostics first, then Sunshine/Moonlight removal |
| **C — Adaptive Streaming Architecture** | PLANNED | Explicit profiles, telemetry, adaptive bitrate/FEC, 1080p, source abstraction |
| **D — Media Library / VOD UX** | PLANNED | Recursive poster art, local-first metadata/library polish |
| **E — Resource Scaling / Linux** | PLANNED | Formal workloads, Windows benchmark, cheap Linux tiers, capability scaling |
| **F — Open Platform / Firmware** | OPTIONAL / PARALLEL | OpenBIOS evaluation with compatibility fallback |
| **G — Smart-Home & Client Expansion** | FUTURE | Cameras, devices, storage, remote PC game relay, handheld clients |

## Phase A coverage note

SNES and PS1 have runtime coverage. NES and Genesis had zero local fixtures
during A9 and remain explicitly not runtime validated. This is a coverage gap,
not an active regression.

## Immediate sequence

```text
B1 diagnostic inventory
→ unified schema / health snapshot
→ GUI diagnostics / self-test / sanitized bundle
→ Sunshine/Moonlight inventory/removal
→ native-only regression
→ clean-native checkpoint
→ Phase C
```

## Adaptive-streaming rule

For local streams, adapt to measured PC→isolated-LAN/Wi-Fi→client path health,
not router Internet/WAN throughput. Start with bitrate-only adaptation while
holding resolution/60 fps stable. Consider FEC adaptation only after bitrate
control is independently measurable.

## OpenBIOS rule

OpenBIOS is a portability/customization/debuggability candidate, not a promised
performance optimization. Keep the validated compatibility BIOS path available
until an explicit compatibility matrix justifies otherwise.

## Phase B1.1 active

**B1.1 Existing diagnostics inventory: ACTIVE.**

The current hypothesis is that most low-level telemetry already exists and the
missing architectural layer is a common event/health schema plus aggregator.
This must be confirmed from the exact local tree/log inventory before B1.2.

No production streaming/controller/audio behavior changes in B1.1.

## B1.1 completed / B1.2 active

B1.1 runtime inventory confirmed:
- strong existing telemetry/probe/bundle infrastructure;
- no common health/event contract;
- no unified GUI diagnostics;
- meaningful local diagnostic storage growth.

B1.2 is now the pure unified health/resource model foundation. It reuses
existing host telemetry and adds no new sampling overhead. API/GUI integration
waits for a real runtime snapshot.

## B1.2 validated / B1.3 active

B1.2 unified health/resource model passed real idle-state runtime validation and
reused existing last-session host telemetry.

B1.3 exposes that exact model as a read-only companion endpoint. Resource
collection remains zero-additional-overhead. Client decoder/network path
feedback remains the next observability gap before GUI diagnostics and adaptive
streaming.

## B1.3 validated / B1.4 audit active

The read-only health endpoint is runtime validated, including correct
`latest_history` → `last_session` resource provenance after companion restart.

B1.4 now audits the onn-side decoder/network metric and request cadence before
client feedback is implemented. This is both diagnostics work and early Phase
C/E optimization infrastructure: the eventual feedback contract should serve
health reporting, adaptive bitrate and resource characterization without
duplicate sampling loops.

## B1.4 complete / B1.5 active

Client metric/cadence audit confirmed reuse is possible. B1.5 adds low-rate
client feedback without a new timer or persistent sample history. After runtime
validation, B1 continues with GUI Diagnostics/Self-Test/support-bundle
integration and bounded retention.

## B1.5 feedback transport validated / B1.6 classifier audit active

Android→companion client health is now operational with a measured 631-byte
payload every 2 seconds and no duplicate sampling loop. The network path can be
classified from client evidence.

The first decoder classifier is intentionally under review: one interval showed
9 stale-output drops despite ~59.7 receive FPS, healthy network/FEC state and no
queue overflow.

B1.6 measures stale-output semantics before GUI diagnostics consumes this health
state. This avoids baking a noisy classifier into later adaptive-bitrate or
resource-optimization decisions.

## B1.6 evidence complete / B1.7 classifier correction active

Multi-interval evidence showed that stale-output shedding is normal enough in
the current low-latency decoder path that `stale > 0` is not a useful failure
rule.

B1.7 makes the health model subsystem-accurate without changing streaming:
stale-only shedding is informational; decoder-local drops, queue overflow and
hardware-decoder failure remain degraded.

After runtime validation, proceed to the GUI Diagnostics/Self-Test surface and
bounded diagnostic-retention policy.

## B1.7 validated / B1.8 GUI-retention context active

The end-to-end health pipeline, including Android client feedback and the
decoder/network classifier split, is runtime validated.

B1.8 now audits exact GUI integration anchors and current storage pressure before
building the user-facing Diagnostics/Self-Test surface and bounded retention.
No evidence is deleted by the audit.

This is the final source-context step before the B2-style GUI becomes a normal
product surface.

## B1.8 complete / B1.9 Diagnostics GUI + retention foundation active

B1.8 confirmed the standalone GUI architecture and localized storage pressure to
transport history plus debug bundles.

B1.9 creates the first normal user-facing Diagnostics/Self-Test surface without
duplicating health logic and adds dry-run-first bounded runtime retention.

Automatic retention is intentionally deferred until the real candidate plan is
reviewed. This keeps evidence preservation ahead of storage cleanup.

After B1.9 validation and retention review, finish support-bundle integration /
retention apply policy, then proceed to the Sunshine/Moonlight dependency
inventory and clean-native baseline work.


## B1.9 runtime validated / B1.10 active

Diagnostics GUI/Self-Test foundation: **COMPLETE / runtime validated**.

Retention foundation: **DEVELOPMENT-ONLY / dry-run validated, policy blocked for forward transport**. Reverse transport and debug bundles are within current provisional caps.

B1.10 is the narrow protected-footprint audit required before any retention-policy revision or apply.

## B1.10 complete / B1.11 retention rule refinement active

The GUI/Self-Test surface remains runtime validated.

Retention blocker root cause is now known: raw `pktmon_full.txt` captures were
misclassified as summary evidence by extension. B1.11 corrects only that rule
and re-runs dry-run planning.

If the revised plan is unblocked and preserves evidence as intended, the next
step is an explicit one-time retention apply decision plus post-apply evidence,
not another broad diagnostics redesign.

## B1.12 retention apply complete / B1-B2 completion audit active

Manual retention is now runtime validated: 8 reviewed files removed, zero
failures, and all managed families are under cap with zero pending candidates.

Diagnostics GUI is runtime validated.

Before transitioning to B3, run a completion-gap audit against the original B1
and B2 requirements. Any missing event-history, support-bundle GUI, or bounded
Self-Test requirement must be implemented or explicitly deferred.

## B1/B2 completion gaps confirmed / exact source-context active

B1.3 bounded common event history and B2.2 GUI sanitized-bundle access remain
missing. B2.1 also lacks explicit storage-writability and ADB/development checks
according to the source audit.

Before implementation, inspect exact local code to distinguish true missing
coverage from generic component-loop coverage. B3 remains pending.

## B1.13 — B1/B2 completion implementation active

Exact source context resolved the completion design.

Remaining B1/B2 implementation:
- B1.3 bounded common event history;
- B2.1 storage/ADB/emulator-runtime dedicated readiness checks;
- B2.2 GUI sanitized bundle action reusing the existing bundle tool.

Existing health components already cover companion/control/native
stream/capture/transport/decoder/audio/controller/resource/network state, so no
parallel checks are added.

After B1.13 runtime validation, B1/B2 can be marked complete and B3
Sunshine/Moonlight dependency inventory becomes next.

## B1/B2 runtime validated / final B2 UI polish active

B1/B2 diagnostics behavior is runtime validated with
`B1_B2_COMPLETION_RUNTIME_CONFIRMED`.

Before beginning B3, apply and visually validate one small TV usability polish:
button-local in-progress labels for Refresh, Self-Test and Collect Diagnostics.
No functional diagnostics work remains.

## B1/B2 complete / B3 active

B1/B2 diagnostics, Self-Test, bounded event history, sanitized bundle, retention and final GUI action feedback are runtime/manual validated. B3 Sunshine/Moonlight dependency inventory is now active; no legacy removal occurs until its evidence is reviewed.

## B3.1 focused active-edge trace

Broad B3 inventory is captured. Windows legacy process/service/task/firewall/
installed-software state is zero, but production source still contains
`StreamManager` and Android Moonlight compatibility edges.

Run the focused current-call-graph trace before B4. The goal is an exact small
removal cut set rather than term-based bulk deletion.

## B4.1 source-context recovery

B3.1 remains complete and the server-first cut order remains valid.

The first B4.1 installer made no production change; it failed preflight on an
inferred source-anchor mismatch. B4.1 is temporarily back in diagnostic context
capture so the removal patch can be generated from exact local AST spans.

B4.2 Android removal remains blocked until B4.1 runtime validation passes.

## B4.1 v2 runtime validation

Exact local Games source context is captured. The corrected B4.1 server-edge
patch uses AST-selected spans and preserves native streaming plus all physical
legacy artifacts.

B4.2 remains blocked until B4.1 passes a live native game session with no
Sunshine process.

## B4.1 complete / B4.2 context capture

B4.1 server edge removal is runtime validated.

B4.2 Android Moonlight edge is next. Capture exact current Android source
context before modifying MainActivity or manifest. Then runtime/manual validate
normal game launch before deleting orphaned Sunshine/Moonlight artifacts.

## B4.2 Android Moonlight edge

B4.1 is runtime validated and B4.2 exact Android context is captured.

Apply the narrow Android cut, Kotlin-compile, install on onn, and runtime/manual
validate native game launch. Then audit orphan helpers/artifacts before cleanup.

## B4.3 orphan-reference audit

B4.1 server and B4.2 Android client edges are runtime validated.

Before physical cleanup, run a focused orphan-reference audit over remaining
helper definitions, stream_manager.py, legacy scripts and runtime/download
groups. Then apply one coherent orphan cleanup and run B5 native-only regression.

## B4.4 code-orphan cleanup

B4.1/B4.2 runtime validated. B4.3 confirms code orphans.

B4.4 removes exact-hash code orphans and requires runtime validation after a
fresh companion restart. Then capture exact physical legacy artifact hashes,
delete those artifacts, and run B5 native-only regression.

## B4.5 physical legacy manifest

B4.4 code-orphan cleanup is runtime validated. B4.5 captures exact physical
legacy artifact hashes and external state. Review that evidence, then perform
the final legacy physical cleanup and run B5 native-only regression.

## B4.6 physical legacy cleanup

Delete the nine exact-hash project legacy groups, runtime validate native streaming, resolve any remaining Android Moonlight package verification, then run B5 native-only regression and establish the clean-native checkpoint.

## B4.7 device package verification

B4.6 project-side physical cleanup is runtime validated.

Resolve the remaining device-level ambiguity with a private ADB package check.
If Moonlight is absent, begin B5 native-only regression. If present, remove only
the obsolete package, verify absence, then begin B5.

## B4.8 final legacy device cleanup

B4.6 project cleanup is runtime validated and B4.7 confirms the obsolete
Moonlight client remains installed on the onn.

Remove and verify `com.limelight`. Once confirmed absent, B4 is complete and the
next work is B5 native-only regression.

## B4.8 final device verification

Project cleanup is complete and the Moonlight uninstall command succeeded.
B4 remains open only because the first absence verifier used unsuitable
`pm path` semantics.

Run the corrected package-list verifier. A clean result completes B4 and moves
directly to B5 native-only regression.

## B5 native-only regression

**Status: ACTIVE**

B4 legacy removal is complete, including device Moonlight removal verification.

B5 now proves Games independently in one focused post-removal session:
launch -> native stream -> audio -> controller -> pause/resume -> Save/Load ->
cheat/mod/profile -> End/teardown.

Successful B5 advances directly to B6 clean-native repository audit/checkpoint.

## B5 native-only regression

**COMPLETE / RUNTIME VALIDATED**

The representative post-removal session passed launch/native stream, picture,
audio, controller, pause/resume, Save/Load, profile behavior and teardown.

A harness-only classifier defect was corrected: post-profile native-client
activity is informational because profile/UI navigation can close the stream
Activity before the managed game ends.

**B6 clean-native checkpoint is ACTIVE.**

## B6 clean-native repository audit

**ACTIVE / DIAGNOSTIC ONLY**

B5 is runtime validated. Audit the exact current repository, compile Python and
Android Kotlin, verify active legacy references are gone, verify durable-memory
and source-control boundaries, and compare remote main to the expected baseline.

After review, update root ROADMAP.md to Phase B complete / Phase C next and
perform the exact-scope checkpoint/push.

## Phase B complete

B1-B6 are complete/checkpointed/pushed.

B1/B2 diagnostics and user-facing diagnostics are validated. B3/B4 removed the
Sunshine/Moonlight architecture and artifacts. B5 passed native-only regression.
B6 audited repository/build state and checkpointed the clean-native baseline.

Phase C is NEXT, beginning with C1 explicit stream profiles.


## Roadmap v3 — accepted Linux-first continuation

Current:
- A COMPLETE / PUSHED
- B COMPLETE / PUSHED
- C NEXT

Planned continuation:
- D Media Library / VOD / Live TV UX
- E Linux Migration / Native Linux Baseline
- F Linux Core Resource Characterization & Optimization
- G Extended Emulation & User-Content Import
- H Home Infrastructure / Client / Plugin Expansion
- I Local Intelligence / Voice / Privacy-Aware AI

OpenBIOS/Open Platform is removed as a dedicated phase.

Phase F core sizing is intentionally limited to PS1-and-below.
Phase G adds safe user-content import before N64/GameCube/PS2 work.

Immediate next step: C1 explicit stream profiles.
