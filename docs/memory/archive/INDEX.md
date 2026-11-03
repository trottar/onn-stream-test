---
memory_schema: 1
as_of: 2026-11-03
status: INDEX — every file archived by DOCS-APPLY on 2026-11-03 (git mv, nothing deleted), per evidence/DOCS_AUDIT_2026-11-02.md option (b), from commit b20729b8
---

# docs/memory/archive — index

Archived files are moved with `git mv`, never deleted; `git log --follow <new path>` gives their history. The records
under `evidence/` are never archived. Option (b) of the audit: `handoffs/` and `patches/` stay in place, indexed by
`handoffs/README.md` and `patches/PATCH_INDEX.md`. A record that links an old path below finds the file at its new path.

Other archive files written on 2026-11-03 (verbatim moves out of live files, not `git mv`):
- `current/CURRENT_HISTORY_2026-11-02.md` — CURRENT.md's history (1,270 lines).
- `memory/TOOLS_HISTORY_2026-11-02.md` — TOOLS.md's history.
- `docs/KNOWN_ISSUES_CLOSED_2026-11-02.md` — KNOWN_ISSUES.md's closed sections.
- In `docs/memory/history/`: `HANDOFF_SECTIONS_THROUGH_2026-10-16.md`, `MEMORY_SECTIONS_MOVED_2026-11-03.md`,
  `ACTIVE_INVESTIGATIONS_THROUGH_2026-10-15.md`.

## Open items carried out

These were open when their files were archived or indexed. Each is also in `docs/KNOWN_ISSUES.md`'s open index.
- **G8-S6** — three paired cap-6000 cells, control vs `PRIVYHUB_ENCODER_RC=tight` (does `tight` keep a capped stream
  from going silent?). Queued in `handoffs/QUEUE_2026-10-19N.md` (HELD), never run.
- **G5-S2-L** — the WAN adaptation rules' first live LAN smoke. Same queue, never run.
- **LINK-N1** — the nightly link watch ran to 2026-10-31; only its launch record exists. Its nights are not written up.
- **G4_RUNBOOK_HOTSPOT step 18** — "local behaviour unchanged with the overlay absent" was never scored.
- **QUEUE_2026-10-19B's G9-D1** — the G9 checkpoint draft, still wanted, as its own task. Its memory-maintenance half
  was done by DOCS-APPLY (`evidence/MEMORY_MAINTENANCE_REPORT_2026-11-03.md`).

## Moved files (83)

| Old path | New path | Verdict — reason |
|---|---|---|
| `docs/A4_AUDIO_RECOVERY.md` | `docs/memory/archive/docs/A4_AUDIO_RECOVERY.md` | done — Windows-era A4 audio lifecycle fix |
| `docs/DEBUGGING_HARNESS.md` | `docs/memory/archive/docs/DEBUGGING_HARNESS.md` | stale — the .ps1 harness no longer exists; see docs/DIAGNOSTICS.md (the diag keeper) |
| `docs/DEBUGGING_MEMORY.md` | `docs/memory/archive/docs/DEBUGGING_MEMORY.md` | stale — Windows-era durable rules, duplicated by docs/memory/MEMORY.md |
| `docs/PROJECT_STATUS.md` | `docs/memory/archive/docs/PROJECT_STATUS.md` | stale — status as of 2026-09-28; see docs/memory/CURRENT.md and docs/ROADMAP.md §0 |
| `docs/REPOSITORY_AUDIT_2026-09-07.md` | `docs/memory/archive/docs/REPOSITORY_AUDIT_2026-09-07.md` | done — the 2026-09-07 pre-push audit |
| `docs/memory/CHECKPOINT_PROPOSAL_2026-09-22.md` | `docs/memory/archive/memory/CHECKPOINT_PROPOSAL_2026-09-22.md` | done — M1's proposed checkpoint, committed long ago |
| `docs/memory/PHASE_C_CONTEXT.md` | `docs/memory/archive/memory/PHASE_C_CONTEXT.md` | done — Phase C resume context (Phase C closed 2026-10-05) |
| `docs/memory/chats/CHAT_INDEX.md` | `docs/memory/archive/memory/chats/CHAT_INDEX.md` | done — chat-period index through 2026-09-15 |
| `docs/memory/2026-09-10.md` | `docs/memory/archive/memory/daily/2026-09-10.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-11.md` | `docs/memory/archive/memory/daily/2026-09-11.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-14.md` | `docs/memory/archive/memory/daily/2026-09-14.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-15.md` | `docs/memory/archive/memory/daily/2026-09-15.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-16.md` | `docs/memory/archive/memory/daily/2026-09-16.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-17.md` | `docs/memory/archive/memory/daily/2026-09-17.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-18.md` | `docs/memory/archive/memory/daily/2026-09-18.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-19.md` | `docs/memory/archive/memory/daily/2026-09-19.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-20.md` | `docs/memory/archive/memory/daily/2026-09-20.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-21.md` | `docs/memory/archive/memory/daily/2026-09-21.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-22.md` | `docs/memory/archive/memory/daily/2026-09-22.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-23.md` | `docs/memory/archive/memory/daily/2026-09-23.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-24.md` | `docs/memory/archive/memory/daily/2026-09-24.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-28.md` | `docs/memory/archive/memory/daily/2026-09-28.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-29.md` | `docs/memory/archive/memory/daily/2026-09-29.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-09-30.md` | `docs/memory/archive/memory/daily/2026-09-30.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-01.md` | `docs/memory/archive/memory/daily/2026-10-01.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-02.md` | `docs/memory/archive/memory/daily/2026-10-02.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-03.md` | `docs/memory/archive/memory/daily/2026-10-03.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-05.md` | `docs/memory/archive/memory/daily/2026-10-05.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-06.md` | `docs/memory/archive/memory/daily/2026-10-06.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-07.md` | `docs/memory/archive/memory/daily/2026-10-07.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-08.md` | `docs/memory/archive/memory/daily/2026-10-08.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-09.md` | `docs/memory/archive/memory/daily/2026-10-09.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/2026-10-10.md` | `docs/memory/archive/memory/daily/2026-10-10.md` | done — daily session chronology (ended 2026-10-10; chronology now lives in evidence/) |
| `docs/memory/investigations/ADB_STALE_CACHE_NATIVE_ERROR_2026-09-14.md` | `docs/memory/archive/memory/investigations/ADB_STALE_CACHE_NATIVE_ERROR_2026-09-14.md` | done — closed investigation |
| `docs/memory/investigations/B1_DIAGNOSTICS_INVENTORY.md` | `docs/memory/archive/memory/investigations/B1_DIAGNOSTICS_INVENTORY.md` | done — closed investigation |
| `docs/memory/investigations/C3_BIDIRECTIONAL_ACTUATOR.md` | `docs/memory/archive/memory/investigations/C3_BIDIRECTIONAL_ACTUATOR.md` | done — Phase C actuator investigation (Phase C closed) |
| `docs/memory/investigations/C3_BITRATE_ACTUATOR.md` | `docs/memory/archive/memory/investigations/C3_BITRATE_ACTUATOR.md` | done — Phase C actuator investigation (Phase C closed) |
| `docs/memory/investigations/C3_FIXED_BITRATE_CHARACTERIZATION.md` | `docs/memory/archive/memory/investigations/C3_FIXED_BITRATE_CHARACTERIZATION.md` | done — Phase C actuator investigation (Phase C closed) |
| `docs/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` | `docs/memory/archive/memory/investigations/C3_LINUX_ACTUATOR_BOUNDARY.md` | done — Phase C actuator investigation (Phase C closed) |
| `docs/memory/investigations/C3_STARTUP_STABILIZATION.md` | `docs/memory/archive/memory/investigations/C3_STARTUP_STABILIZATION.md` | done — Phase C actuator investigation (Phase C closed) |
| `docs/memory/investigations/D103_D5_EPG_INGESTION_PROBE.md` | `docs/memory/archive/memory/investigations/D103_D5_EPG_INGESTION_PROBE.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D105_D5_EPG_LOCAL_SOURCE_VIABILITY.md` | `docs/memory/archive/memory/investigations/D105_D5_EPG_LOCAL_SOURCE_VIABILITY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D106_D5_EPG_PROVIDER_IDENTITY.md` | `docs/memory/archive/memory/investigations/D106_D5_EPG_PROVIDER_IDENTITY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D107_D5_EPG_FEED_IDENTITY.md` | `docs/memory/archive/memory/investigations/D107_D5_EPG_FEED_IDENTITY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D108_D5_EPG_LOCAL_GRABBER_VIABILITY.md` | `docs/memory/archive/memory/investigations/D108_D5_EPG_LOCAL_GRABBER_VIABILITY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D109_D5_EPG_PORTABLE_NODE_GRABBER.md` | `docs/memory/archive/memory/investigations/D109_D5_EPG_PORTABLE_NODE_GRABBER.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D110_D5_LINUX_EPG_SERVICE_SEAM.md` | `docs/memory/archive/memory/investigations/D110_D5_LINUX_EPG_SERVICE_SEAM.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D111_D5_ANDROID_COMPANION_EPG_INTEGRATION.md` | `docs/memory/archive/memory/investigations/D111_D5_ANDROID_COMPANION_EPG_INTEGRATION.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D113_D5_STREAM_IDENTITY_INTEGRITY.md` | `docs/memory/archive/memory/investigations/D113_D5_STREAM_IDENTITY_INTEGRITY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D115_D5_LINUX_TV_STATE_AUTHORITY.md` | `docs/memory/archive/memory/investigations/D115_D5_LINUX_TV_STATE_AUTHORITY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D116_D5_ANDROID_TV_STATE_SYNC.md` | `docs/memory/archive/memory/investigations/D116_D5_ANDROID_TV_STATE_SYNC.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D117_D5_LINUX_AUTHORITY_PULL_VALIDATION.md` | `docs/memory/archive/memory/investigations/D117_D5_LINUX_AUTHORITY_PULL_VALIDATION.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D119_D5_TV_ENTRY_SYNC_TRIGGER.md` | `docs/memory/archive/memory/investigations/D119_D5_TV_ENTRY_SYNC_TRIGGER.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D120_D5_TV_STATE_SYNC_DIAGNOSTICS.md` | `docs/memory/archive/memory/investigations/D120_D5_TV_STATE_SYNC_DIAGNOSTICS.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D121_D5_TV_STATE_CONFLICT_DIAGNOSTICS.md` | `docs/memory/archive/memory/investigations/D121_D5_TV_STATE_CONFLICT_DIAGNOSTICS.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D122_D5_TV_MEDIA_REGRESSION_GATE.md` | `docs/memory/archive/memory/investigations/D122_D5_TV_MEDIA_REGRESSION_GATE.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D123_TV_EPG_PERFORMANCE_AND_GUIDE_UX.md` | `docs/memory/archive/memory/investigations/D123_TV_EPG_PERFORMANCE_AND_GUIDE_UX.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D124_TV_EPG_LATENCY_PROBE.md` | `docs/memory/archive/memory/investigations/D124_TV_EPG_LATENCY_PROBE.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D125_EPG_NONBLOCKING_BACKGROUND_WARMER.md` | `docs/memory/archive/memory/investigations/D125_EPG_NONBLOCKING_BACKGROUND_WARMER.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D126_ANDROID_EPG_PREFETCH_INTEGRATION.md` | `docs/memory/archive/memory/investigations/D126_ANDROID_EPG_PREFETCH_INTEGRATION.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D127_INCORRECT_GUIDE_INTENT.md` | `docs/memory/archive/memory/investigations/D127_INCORRECT_GUIDE_INTENT.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D128_GUIDE_STYLE_CATEGORY_PRESENTATION.md` | `docs/memory/archive/memory/investigations/D128_GUIDE_STYLE_CATEGORY_PRESENTATION.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D129_SINGLE_COLUMN_TV_GUIDE.md` | `docs/memory/archive/memory/investigations/D129_SINGLE_COLUMN_TV_GUIDE.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D130_TV_ENTRY_LATENCY.md` | `docs/memory/archive/memory/investigations/D130_TV_ENTRY_LATENCY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D131_NONBLOCKING_TV_ENTRY_STATE_SYNC.md` | `docs/memory/archive/memory/investigations/D131_NONBLOCKING_TV_ENTRY_STATE_SYNC.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D132_FAVORITES_EPG_COVERAGE.md` | `docs/memory/archive/memory/investigations/D132_FAVORITES_EPG_COVERAGE.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D133_EPG_STATUS_ACCURACY.md` | `docs/memory/archive/memory/investigations/D133_EPG_STATUS_ACCURACY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D134_FAVORITES_LOAD_LATENCY.md` | `docs/memory/archive/memory/investigations/D134_FAVORITES_LOAD_LATENCY.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D135_TV_STATE_EXECUTOR_ISOLATION.md` | `docs/memory/archive/memory/investigations/D135_TV_STATE_EXECUTOR_ISOLATION.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D136_FOCUSED_TV_MEDIA_REGRESSION.md` | `docs/memory/archive/memory/investigations/D136_FOCUSED_TV_MEDIA_REGRESSION.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D137_TV_STATE_PROBE_V2_PROJECTION.md` | `docs/memory/archive/memory/investigations/D137_TV_STATE_PROBE_V2_PROJECTION.md` | done — D5 EPG / guide / TV-state investigation (D5 closed at D-139) |
| `docs/memory/investigations/D4_PS1_MULTITAP_LINUX_2026-09-16.md` | `docs/memory/archive/memory/investigations/D4_PS1_MULTITAP_LINUX_2026-09-16.md` | done — closed investigation |
| `docs/memory/manifest.json` | `docs/memory/archive/memory/manifest.json` | stale — the ZIP-era hash manifest (read only by two September probes) |
| `docs/memory/repository/AUDIT_2026-09-10.md` | `docs/memory/archive/memory/repository/AUDIT_2026-09-10.md` | done — the 2026-09-10 repository / chat audit |
| `docs/memory/roadmap/D5_MEDIA_SERVER_SUBSTEPS.md` | `docs/memory/archive/memory/roadmap/D5_MEDIA_SERVER_SUBSTEPS.md` | done — D5 substeps (D5 closed) |
| `docs/memory/roadmap/STATUS.md` | `docs/memory/archive/memory/roadmap/STATUS.md` | stale — 'Phase C SUSPENDED'; duplicates docs/ROADMAP.md |
| `docs/memory/templates/SESSION_LOG.md` | `docs/memory/archive/memory/templates/SESSION_LOG.md` | done — the daily-log template (convention ended) |
| `_cowork_prompt_offsite.txt` | `docs/memory/archive/prompts/_cowork_prompt_offsite.txt` | done — A's G4-S4 off-site prompt (historical) |
| `STOP` | `docs/memory/archive/scratch/STOP` | done — empty stop-file from the G8-S1 launch; no tool reads a repo-root STOP |
| `scripts/setup_retroarch_portable.ps1` | `docs/memory/archive/windows-scripts/setup_retroarch_portable.ps1` | stale — Windows-era PowerShell start script |
| `scripts/start_browser.ps1` | `docs/memory/archive/windows-scripts/start_browser.ps1` | stale — Windows-era PowerShell start script |
| `scripts/start_camera.ps1` | `docs/memory/archive/windows-scripts/start_camera.ps1` | stale — Windows-era PowerShell start script |
| `scripts/start_server.ps1` | `docs/memory/archive/windows-scripts/start_server.ps1` | stale — Windows-era PowerShell start script |
