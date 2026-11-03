---
memory_schema: 1
as_of: 2026-11-02
status: DOCS-AUDIT (session C, docs only, READ-ONLY) — the inventory of every README, docs page, memory file, handoff, patch note, scratch file and leftover against the real state, and the cleanup plan FOR THE USER'S APPROVAL. Nothing applied, nothing moved, renamed or deleted; this file is the only file written. The apply pass is a later prompt, after approval, when no A or B session is running
---

# DOCS-AUDIT 2026-11-02 — what the repo says vs what is true

Task: `handoffs/DOCS-AUDIT_2026-11-02_TASK.md`. All reads used `cat` / `sed` / `grep` / `wc` / `ls` / `git log` / `git ls-files` / `git grep` only. No code, no tests, no stream, no restart, no adb. No `logs/` file was written.
Dates are 2026 and give the file's last commit (`git log -1 --date=short`). "untracked" means the file has never been committed. Sizes are bytes (`wc -c`).
Verdicts:
- **true**: what it says about today holds.
- **stale**: it says something about today that is false.
- **duplicate**: the same content is held elsewhere.
- **done**: a closed record of finished work.
- **superseded**: a later file replaced it.
- **held**: written and never run.
- **live**: current work.

## 0. The real state (what everything below is judged against)

**Adopted lines: fourteen**, in `tools/e1_suite.py` `ADOPTED`. Each comes from its own drop-in under the companion unit. The off switch is the same for every line: delete the line's drop-in, `daemon-reload`, then restart the companion.

| # | Line | Drop-in | Gate |
|---|---|---|---|
| 1 | `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` | `adaptive.conf` | C3-L4 |
| 2 | `PRIVYHUB_EPG_GUIDE_INDEX=cached` | `epg-index.conf` | E3-S6A |
| 3 | `PRIVYHUB_SNES_CORE=snes9x` | `snes-core.conf` | E3-A2 |
| 4 | `PRIVYHUB_RECOVERY_TRIGGER=v2` | `recovery.conf` | E3-A3B |
| 5 | `PRIVYHUB_SNES_CAPTURE_FIX=output_rate` | `snes-capture.conf` | E4-S5D |
| 6 | `PRIVYHUB_OVERLAY_PROVIDER=tailscale` | `overlay.conf` | G-A1 |
| 7 | `PRIVYHUB_SESSION_IDENTITY=v2` | `session-identity.conf` | G-A1 |
| 8 | `PRIVYHUB_AUDIO_CODEC=opus` | `audio-codec.conf` | G-A2 |
| 9 | `PRIVYHUB_LINK_REPORT=1` | `link-report.conf` | G-A3 |
| 10 | `PRIVYHUB_LINK_RECOVERY=1` | `link-recovery.conf` | G-A4 |
| 11 | `PRIVYHUB_RESTART_FAST=1` | `restart-fast.conf` | G-A5 |
| 12 | `PRIVYHUB_RESTART_FAST_UNLOCK=1` | `restart-fast-unlock.conf` | G-A7 |
| 13 | `PRIVYHUB_REMOTE=1` | `remote.conf` | G-A9 |
| 14 | `PRIVYHUB_STEP_IN_PLACE=1` | `step-in-place.conf` | G-A10 |

- **Lines 1–13** are committed.
- **Line 14** (G-A10) is the user's decision of 2026-11-02. At audit time, session A had it applied in the working tree, uncommitted: `tools/e1_suite.py` lists fourteen, `patches/G-A10_STEP_IN_PLACE_ADOPTION.md` is APPLIED, and `evidence/g_a10_2026-11-02/` is being written. Its record, `evidence/G_A10_STEP_IN_PLACE_ADOPTION_2026-11-02.md`, did not exist yet.
- **Line 10** implies six sub-lines.
- **Line 13** acts only on a remote-class session. It replaced the per-run WAN flags in `e3_flag.conf`.

**The client app:**
- APK **`fcd924c2…` is CONFIRMED** on the onn. It is CL-B14's build: the client loss guard is out and the link notice is on by default.
- `554ccf61…` is NOT CONFIRMED (HOME-1's C5 was invalid). It is kept in the APK build output.
- The seven client properties are empty and `identity_v2` is on.

**Units:**
- `privyhub-companion` and **`privyhub-diag`** are running. `privyhub-diag` is the B36 diagnostics keeper, read with `tools/diag_read.py` and `tools/diag_check.py`.
- `privyhub-link-n1` (the nightly watch) ended 2026-10-31.
- `privyhub-trip-log` (the trip keeper) ended 2026-11-01.

**Built and live, not adopted:**
- **B33 is live** inside line 10: a short release with no loss resumes without a state load. Its off switch is `PRIVYHUB_REWIND_NEEDS_LOSS=0`.
- G-A6 is shelved.
- G-A8 (the loss guard) was prepared and never applied; the guard is out.
- B27 and B29 are not in the confirmed APK.
- B32, B34 and B35 are in the tree behind flags that default to off.

**Phases and queues:**
- Phase E is active: E1 frozen, E2 measured, E3 and E4 closed. The G track is under way.
- Phase C, D-BASE and the D series are closed. HOME-1 is done (2026-11-02).
- Live work:
  - A: `handoffs/G-A10_STEP_IN_PLACE_ADOPTION_TASK.md`.
  - B: `handoffs/QUEUE_2026-11-02M.md`. B stopped at its precondition at 2026-11-03T02:27Z UTC because G-A10's record did not exist yet.
  - C: this audit.

**The records:** `docs/memory/evidence/`, 15,311 tracked files, 2.9 GB. They are never moved.

## 1. Inventory

### 1.1 READMEs

| Path | Date | Bytes | What it claims | Verdict | Action |
|---|---|---:|---|---|---|
| `README.md` | 09-22 | 6,023 | Local-first hub (Linux companion + onn). Phase D active, C suspended, D-BASE current. No how-to-run | **stale** | rewrite (§2.2) |
| `docs/README.md` | 09-22 | 3,189 | Docs map + authority order; "newest evidence" = D-BASE 09-20..22. Map lacks REMOTE_TRUST / CAPABILITY_MODEL / WAN_ADAPTATION_RULES | **stale** (authority order still true) | rewrite |
| `docs/memory/README.md` | 09-17 | 1,816 | Memory index, authority order, startup, health check, "ZIP invariant" | **stale** (ZIP-era; omits LEARNINGS / TOOLS / USER / REPOSITORY_POLICY / templates / repository) | small rewrite |
| `docs/memory/history/README.md` | 09-17 | 1,245 | Superseded-history trust order; only the 09-17 bootstrap listed | true, incomplete (4 later files unlisted) | add rows |
| `docs/memory/evidence/snapshots/README.md` | 09-10 | 376 | Sanitized snapshots of the ignored `evidence/raw/` | true (`raw/` absent on disk) | keep |
| `docs_flat/README.md` | untracked (ignored) | 1,660 | Older copy of `docs/README.md` | **duplicate** | none in git (see §1.8) |
| `companion/`, `tools/`, `tests/`, `PrivyHub/`, `scripts/` | — | — | **No README in any** | — | new READMEs in `companion/`, `tools/`, `tests/` and `PrivyHub/`; `scripts/` is archived (§1.8) |

### 1.2 `docs/` pages

| Path | Date | Bytes | What it claims | Verdict | Action |
|---|---|---:|---|---|---|
| `docs/A4_AUDIO_RECOVERY.md` | 09-10 | 7,802 | Windows A4 audio lifecycle fix (WASAPI, v3–v5) | done (Windows era) | archive, pointer in `docs/README.md` |
| `docs/A8_INPUT_PROFILES.md` | 09-16 | 18,299 | Input profiles A8.1–A8.4; Linux udev D-pad fix; A8.3 "UI validation required" | **stale** status block | keep; fix "Status", fold the v3–v8 patch history |
| `docs/CAPABILITY_MODEL.md` | 11-02 | 12,522 | E5 capability thresholds; §7 says G-A3 "prepared", G-A4 "prepared, not adopted", an old APK hash | **stale** (§7 rows) | mark §7 rows; point to the adopted table |
| `docs/DEBUGGING_HARNESS.md` | 09-10 | 3,264 | One-command `.ps1` harness (the script no longer exists) | **stale** | archive, pointer to the diag keeper and support bundle |
| `docs/DEBUGGING_MEMORY.md` | 09-10 | 35,117 | Windows-era durable rules; the old drive tree authoritative | **stale**, duplicates `memory/MEMORY.md` | archive, pointer |
| `docs/DIAGNOSTICS.md` | 09-07 | 4,513 | UDP probe `.ps1` wrappers (missing); Linux acceptance tests A–D (never run on today's topology) | **stale** | rewrite: `privyhub-diag`, `diag_read` / `diag_check`, self-test, support bundle; the probes as a subsection |
| `docs/KNOWN_ISSUES.md` | 11-02 | 170,753 | Open/fixed log, 52 headings, no index. The "2026-10-21 LAN-R1" section has absorbed ~395 lines of B-queue chronology (old APK pins, "G-A8 … thirteen lines") | **stale** in ~18 sections (§2.3) | rewrite as an open-items index on top; closed sections to the archive with a pointer. **A and B write this file** |
| `docs/PROJECT_STATUS.md` | 09-30 | 26,018 | "Project status — 2026-09-28": C3.L4 built, live off by default, Phase D | **stale** (every section) | archive, pointer to CURRENT.md and ROADMAP §0 |
| `docs/REMOTE_TRUST.md` | 10-29 | 19,666 | G0 trust model; G-A2..G-A9 sections; "thirteenth line"; §4–§6, §8 "not adopted / not installed" | **stale** in §4–§6, §8 and §14 | mark sections; add G-A1 and G-A10 (A adds G-A10 now). **A writes this file** |
| `docs/REPOSITORY_AUDIT_2026-09-07.md` | 09-07 | 6,885 | Pre-push audit; companion described as Windows | done | archive, pointer |
| `docs/ROADMAP.md` | 11-02 | 140,984 | Roadmap v3, phases A–J. §0 marker 10-05 ("E3 next", "Phase D ACTIVE"); G4 / G8 counts "ten…thirteen lines"; the trip keeper "runs to 11-01" | **stale** (§0, §1, the Phase D / E / G status lines, G1 / G3 "NOT ADOPTED", G4 / G8 counts and APK pins) | refresh §0 / §1; mark the superseded sections. **A and B write this file** |
| `docs/WAN_ADAPTATION_RULES.md` | 10-17 | 7,784 | G5 rules R1–R5; REMOTE_LADDER "NOT ADOPTED, off-site pending" | **stale** header and §3 (the ladder, floor and cap act via line 13) | mark the status header and §3. `PRIVYHUB_WAN_ADAPTATION` itself is still not adopted (true) |
| `docs/investigations/2026-09-07-udp-transport.md` | 09-07 | 10,236 | Windows synthetic-UDP study, deferred until reproduced on Linux | true (dated; the issue is still paused) | keep |

### 1.3 `docs/memory/` top level (37 files; `README.md` is in §1.1)

| Path | Date | Bytes | What it claims | Verdict | Action |
|---|---|---:|---|---|---|
| `CURRENT.md` | 11-02 | **97,688 / 1,295 lines** | Active state. `as_of` 10-29; "THIRTEEN lines" (×4); "Ten adoptions stand"; "exactly eight drop-ins"; "Nothing committed since <old commit>"; trip-log and link-n1 "running"; old APKs (`93d29b4a…`, `59f736d2…`) presented as installed; Current Work Item = G-A1 / CL-B3 (10-16); References stop at 10-16 | **stale**; **4.77× the hard byte limit** | rewrite + history to the archive (§2.4). **A writes this file now** (G-A10's fourteen lines) |
| `MEMORY.md` | 09-23 | 35,818 / 660 lines | Durable facts. "Phase C is SUSPENDED" (line 4); no Phase E / G facts | **stale**; 22 B under the 35 KiB soft limit | rewrite: closed-phase detail (e.g. the 142-line loss-column section) to history; promote 3–5 KB of E / G facts |
| `AGENTS.md` | 09-19 | 6,926 | Operating rules; patches ship as ZIPs; launch by `python3 …privyhub_service.py`; daily `YYYY-MM-DD.md` logs | **stale** (ZIP delivery, launch, daily logs) | small rewrite (stays: required by the health check) |
| `MAINTENANCE.md` | 09-18 | 8,837 | Memory policy; thresholds match `check_memory_health.py` | true; does not define `memory_schema` | add a schema section (§2.6) |
| `COMMUNICATION.md` | 09-17 | 2,950 | Cross-session protocol | true except 2 lines (dated log, ZIP manifest) | trim 2 lines |
| `LEARNINGS.md` | 09-22 | 21,466 | Durable lessons | true (PowerShell section Windows-era) | keep |
| `TOOLS.md` | 10-09 | 105,784 | Proven tools and kill switches; `as_of` 09-22; only 4 of 14 drop-ins | **stale** | rewrite: one drop-in / off-switch table + the live tools; history split to the archive |
| `USER.md` | 09-10 | 1,288 | Collaboration preferences | true (one "deliver patch ZIPs" line stale) | trim 1 line |
| `REPOSITORY_POLICY.md` | 09-10 | 1,472 | What to commit vs keep local | true | keep |
| `manifest.json` | 09-17 | 59,001 | ZIP-era hash manifest, 314 files, `current_step` D-127 | **stale** | archive (read only by two September probes; see §2.8) |
| `CHECKPOINT_PROPOSAL_2026-09-22.md` | 09-22 | 6,691 | M1's proposed commit of an uncommitted tree | done | archive |
| `PHASE_C_CONTEXT.md` | 09-19 | 20,929 | Phase C resume context | done (Phase C closed 10-05) | archive |

**The 25 daily files:**
- Dates: `2026-09-10`, `09-11`, `09-14`, `09-15`, `09-16`, `09-17`, `09-18`, `09-19`, `09-20`, `09-21`, `09-22`, `09-23`, `09-24`, `09-28`, `09-29`, `09-30`, `10-01`, `10-02`, `10-03`, `10-05`, `10-06`, `10-07`, `10-08`, `10-09`, `10-10`.
- Committed 09-17 → 10-15; 471,043 B total (2.6–82 KB each).
- They are the session chronology, ending 10-10. Four (09-11, 09-16, 09-18, 10-10) have no front matter.
- Verdict: **done**. Nothing after 10-10 writes them; the chronology lives in `evidence/` now.
- Action: archive → `archive/memory/daily/`.

### 1.4 `docs/memory/` subdirectories (94 files; `history/README.md` is in §1.1)

**`architecture/` (13):**

| File | Date | Bytes | Claims | Verdict | Action |
|---|---|---:|---|---|---|
| ADAPTIVE_BITRATE.md | 10-05 | 69,787 | C3 controller design; header "Production adaptive bitrate: NOT IMPLEMENTED" | **stale** header (live is line 1) | fix header; keep (named in code) |
| CONTROLLERS.md | 09-16 | 15,198 | Two-player path via the Windows driver | **stale** | status header + Linux pointer |
| DIAGNOSTICS.md | 09-11 | 23,670 | B1 unified diagnostics design | **stale** (no `privyhub-diag`) | pointer header |
| E1_WORKLOAD_SUITE.md | 10-05 | 11,808 | Frozen E1 suite | true | keep (named in `tools/e1_suite.py`) |
| GAMES.md | 09-14 | 7,877 | Cores incl. bsnes | **stale** (Snes9x, capture fix) | small rewrite |
| NATIVE_SOURCE_CONTRACT.md | 09-28 | 7,181 | C6 source contract | true | keep (named in code) |
| NETWORK.md | 09-14 | 3,255 | Router trust boundary | **stale** (no overlay) | rewrite / point to REMOTE_TRUST |
| REMOTE_ACCESS.md | 09-14 | 3,732 | "PLANNED — Phase G" | **stale** | rewrite / point to REMOTE_TRUST |
| STREAMING.md | 09-14 | 6,820 | Windows capture / NVENC / PCM pipeline | **stale** (Linux x11grab / VAAPI, Opus) | rewrite |
| STREAM_TELEMETRY.md | 09-14 | 6,811 | C2 telemetry contract | **stale** in part (no link report / WAN telemetry) | pointer header |
| SYSTEM.md | 09-14 | 2,108 | Role boundaries; "future Linux hub" | **stale** wording | minor rewrite |
| TV_MEDIA.md | 09-16 | 17,239 | TV / IPTV / media architecture | true | keep |
| TV_STATE_SYNC.md | 09-17 | 9,884 | TV state sync contract | true | keep |

**`decisions/` (21):**

| File(s) | Dates | Bytes | Claims | Verdict | Action |
|---|---|---:|---|---|---|
| DECISION_LOG.md | 09-16 | 56,790 | Ledger to D-1xx; "Active" | **stale** (stops 09-16) | header: "later decisions are in `evidence/G_A*` / `decisions/`" |
| D083_NETDEV_DIAGNOSTIC_CLOSEOUT_2026-09-15.md | 09-15 | (in 15,240 below) | Says "Status: Active" | **stale** status line | fix the one line |
| D-BASE_BASELINE_BEFORE_ADAPTATION, D-BASE-P6A_FRAME_CAP_ADOPTED, D-BASE-P9_AUDIO_CUSHION, D-BASE-P10_AUDIO_REDUNDANCY, D-BASE-R3C_RECOVERY_NEVER_INTO_LIVE_CORE (5) | 09-22/23 | 19,567 | Profile values (cap 90 KB, cushion 12/17, redundancy 2/4), recovery rule | true | keep |
| C3-L2_LINUX_ACTUATOR_CLASSIFICATION, C3-L4_LIVE_AUTHORIZATION_2026-09-28, C3-L4_LIVE_DEFAULT_2026-10-01, C4_ADAPTIVE_FEC_2026-09-24, C5_1080P60_CAPABILITY_2026-09-28, C5-M4_PS1_4X_SOURCE_ADOPTION_2026-10-01, CL-B1_APK_ADOPTION_2026-09-30 (7) | 09-28→10-05 | 64,466 | Phase C decisions | true / done | keep (one is named in code) |
| D-101_BROWSER_CAMERA_C6_RECLASSIFICATION, D-102_D5_TV_ACCEPTANCE_SYNC_OWNERSHIP, D110_EPG_LINUX_ACQUISITION_SEAM, D111_ANDROID_COMPANION_EPG_PRIORITY, D114_STREAM_IDENTITY_POLICY, D115_TV_STATE_AUTHORITY_CONTRACT, D116_ANDROID_TV_STATE_SYNC_POLICY (7) + D083 | 09-15→09-17 | 15,240 | D5 / EPG / TV decisions | done | keep |

**`history/` (4 + README):**
- Files: ACTIVE_INVESTIGATIONS_SUPERSEDED_THROUGH_2026-09-11 (20,924), HANDOFF_SECTIONS_THROUGH_2026-09-22 (5,136), MEMORY_SECTIONS_MOVED_2026-09-23 (7,597), MEMORY_SUPERSEDED_THROUGH_2026-09-11 (38,295).
- Verdict: done. Action: keep, list them in the history README.

**`investigations/` (48):**

| File(s) | Dates | Bytes | Claims | Verdict | Action |
|---|---|---:|---|---|---|
| ACTIVE.md | 10-15 | 105,814 | "PHASE E — ACTIVE", E4 as of 10-10; no G track | **stale** | rewrite to a short index (read by an old probe; see §2.8) |
| CLOSED.md | 09-16 | 4,077 | D4 parity, multitap, controllers closed | true | keep |
| DEFERRED.md | 09-28 | 7,759 | Deferred-by-design items | true | keep |
| BASELINE_STREAM_HEALTH (24,588), LINK_DROP_RECOVERY_DESIGN (17,715), SEAMLESS_LOCAL_PLAY_TEST_BATTERY (19,897), C5_RESYNC_IDR_ACCEPTANCE_READ_2026-09-20 (15,829) | 09-22→09-24 | 78,029 | D-BASE family | done | keep (two are named by code / README) |
| D_LINUX_UDP_EGRESS_2026-09-15 (17,215), EXPRESSVPN_WINDOWS_BRIDGE_2026-09-16 (1,974) | 09-15/16 | 19,189 | UDP egress (paused), VPN bridge (deferred) | true (still paused / deferred) | keep |
| D5 family (31): D103_D5_EPG_INGESTION_PROBE, D105_D5_EPG_LOCAL_SOURCE_VIABILITY, D106_D5_EPG_PROVIDER_IDENTITY, D107_D5_EPG_FEED_IDENTITY, D108_D5_EPG_LOCAL_GRABBER_VIABILITY, D109_D5_EPG_PORTABLE_NODE_GRABBER, D110_D5_LINUX_EPG_SERVICE_SEAM, D111_D5_ANDROID_COMPANION_EPG_INTEGRATION, D113_D5_STREAM_IDENTITY_INTEGRITY, D115_D5_LINUX_TV_STATE_AUTHORITY, D116_D5_ANDROID_TV_STATE_SYNC, D117_D5_LINUX_AUTHORITY_PULL_VALIDATION, D119_D5_TV_ENTRY_SYNC_TRIGGER, D120_D5_TV_STATE_SYNC_DIAGNOSTICS, D121_D5_TV_STATE_CONFLICT_DIAGNOSTICS, D122_D5_TV_MEDIA_REGRESSION_GATE, D123_TV_EPG_PERFORMANCE_AND_GUIDE_UX, D124_TV_EPG_LATENCY_PROBE, D125_EPG_NONBLOCKING_BACKGROUND_WARMER, D126_ANDROID_EPG_PREFETCH_INTEGRATION, D127_INCORRECT_GUIDE_INTENT, D128_GUIDE_STYLE_CATEGORY_PRESENTATION, D129_SINGLE_COLUMN_TV_GUIDE, D130_TV_ENTRY_LATENCY, D131_NONBLOCKING_TV_ENTRY_STATE_SYNC, D132_FAVORITES_EPG_COVERAGE, D133_EPG_STATUS_ACCURACY, D134_FAVORITES_LOAD_LATENCY, D135_TV_STATE_EXECUTOR_ISOLATION, D136_FOCUSED_TV_MEDIA_REGRESSION, D137_TV_STATE_PROBE_V2_PROJECTION | 09-16→09-18 | 69,262 | EPG / guide / TV-state probes; many still say "validation pending" | done (D5 closed at D-139) | archive → `archive/memory/investigations/` |
| C3 family (5): C3_BIDIRECTIONAL_ACTUATOR (2,769), C3_BITRATE_ACTUATOR (2,616), C3_FIXED_BITRATE_CHARACTERIZATION (7,888), C3_LINUX_ACTUATOR_BOUNDARY (33,022), C3_STARTUP_STABILIZATION (2,832) | 09-14→09-19 | 49,127 | Actuator boundary / characterization | done (Phase C closed) | archive |
| ADB_STALE_CACHE_NATIVE_ERROR_2026-09-14 (2,659), B1_DIAGNOSTICS_INVENTORY (1,712), D4_PS1_MULTITAP_LINUX_2026-09-16 (1,994; says "active", CLOSED.md has it closed) | 09-11→09-16 | 6,365 | ADB cache fix, B1 inventory, multitap | done | archive |

**`repository/` (3):**
- AUDIT_2026-09-10.md (09-10, 7,536): done. Archive.
- CODE_MAP.md (09-17, 1,838): **stale** ("avoid MainActivity refactor while D5 closing"). Rewrite.
- DEBT.md (09-15, 1,886): **stale** ("Windows stack → Phase D"). Rewrite.

**`roadmap/` (2):**
- D5_MEDIA_SERVER_SUBSTEPS.md (09-18, 17,604): done. Archive.
- STATUS.md (09-20, 7,046): **stale** ("Phase C SUSPENDED"); duplicates `docs/ROADMAP.md`. Archive (read by an old probe, §2.8).

**`templates/` (2):**
- MEMORY_UPDATE.md (09-17, 910): **stale** (ZIP line). Rewrite 2 lines.
- SESSION_LOG.md (09-10, 669): done (the daily convention ended). Archive.

**`chats/` (1):**
- CHAT_INDEX.md (09-15, 3,215): done. Archive.

**`handoffs/CURRENT_HANDOFF.md`:** 14,010 B / 224 lines, last commit 10-16.
- Size: 1.71× the 8 KiB soft limit, 91 % of the 15 KiB hard limit.
- No front matter. Its newest section is 10-16 (G-A1, "seven lines", old APK).
- Verdict: **stale**. It is required in place by `tools/check_memory_health.py`.
- Action: rewrite to about 1 KB (a pointer to CURRENT.md plus the live task and queue files); old sections → `history/HANDOFF_SECTIONS_THROUGH_2026-10-16.md`.

### 1.5 `docs/memory/handoffs/` (246 tracked + 1 untracked)

**Tally:**

| Verdict | Count | Files |
|---|---:|---|
| DONE | 230 | — |
| SUPERSEDED | 10 | C3-L4-L2B…NO_COPY, the four COWORK_HANDOFF_*, G4-S1 .draft, TRIP-R1, PLAN_WEEK, QUEUE_09-28B, QUEUE_09-29 |
| HELD | 2 | QUEUE_2026-10-19B, QUEUE_2026-10-19N |
| LIVE | 5 | G-A10 task, QUEUE_2026-11-02M, DOCS-AUDIT task, SESSION_B_STATUS.txt, CURRENT_HANDOFF.md (living file, stale) |

Proposed groups go under `archive/handoffs/<group>/`. **keep** means it stays in place.

| File | Date | Bytes | What / evidence | Verdict | Group |
|---|---|---:|---|---|---|
| B4_INPUT_HOLD_REWIND_TASK.md | 10-22 | 7,014 | rewind on hold release → B4_INPUT_HOLD_REWIND_2026-10-22 | DONE | bench |
| BENCH-R1_BLACKOUT_AND_LOSS_CELLS_TASK.md | 10-21 | 6,659 | → BENCH_R1_…_2026-10-22 | DONE | bench |
| BENCH-R2_LOCK_HOLD_STALL_CELLS_TASK.md | 10-22 | 9,583 | → BENCH_R2_…_2026-10-23 | DONE | bench |
| BENCH-R3_SNES_STACK_AND_LOSS_GUARD_TASK.md | 10-22 | 10,320 | → BENCH_R3_…_2026-10-23 | DONE | bench |
| C3-L3A-P2R1_TASK.md | 09-24 | 12,801 | → C3_L3A_P2R1_…_2026-09-23 | DONE | phase-c |
| C3-L3A-P2R2_TASK.md | 09-24 | 8,320 | → C3_L3A_P2R2_SMOKE_SESSION_2026-09-24 | DONE | phase-c |
| C3-L3A-P2R3_TASK.md | 09-24 | 4,567 | → C3_L3A_P2R3_POOLING_RULE_2026-09-24 | DONE | phase-c |
| C3-L3A-R1_TASK.md | 09-28 | 8,684 | → C3_L3A_R1_SESSION1_2026-09-24 | DONE | phase-c |
| C3-L3A-R2B_TASK.md | 09-28 | 6,038 | → C3_L3A_R2B_REPORT_CAP_2026-09-24 | DONE | phase-c |
| C3-L3A-R2_TASK.md | 09-28 | 5,413 | → C3_L3A_R2_SESSION2_2026-09-24 | DONE | phase-c |
| C3-L3A-R3_TASK.md | 09-28 | 4,583 | → C3_L3A_R3_SESSION3_2026-09-24 | DONE | phase-c |
| C3-L3A-R4_GATE_RECORD_TASK.md | 09-30 | 7,835 | → C3_L3A_R4_SESSION4_2026-09-28 | DONE | phase-c |
| C3-L3A-S1_TRANSITION_SOAK_TASK.md | 09-24 | 10,564 | → C3_L3A_S1_TRANSITION_SOAK_2026-09-24 | DONE | phase-c |
| C3-L4-L1_LIVE_CONTROLLER_TASK.md | 09-30 | 8,411 | → C3_L4_L1_LIVE_CONTROLLER_2026-09-28 | DONE | phase-c |
| C3-L4-L2B_NFT_HARNESS_NO_COPY_TASK.md | 09-30 | 4,727 | withdrawn for the ONE_WINDOW variant | SUPERSEDED | phase-c |
| C3-L4-L2B_NFT_HARNESS_ONE_WINDOW_TASK.md | 09-30 | 5,549 | → L2B section of C3_L4_L2_…_2026-09-29 | DONE | phase-c |
| C3-L4-L2_INCREASE_RULE_AND_NFT_HARNESS_TASK.md | 09-30 | 10,153 | → C3_L4_L2_INCREASE_RULE_2026-09-29 | DONE | phase-c |
| C3-L4-N1_NFT_NIGHT1_SCORE_AND_CAPACITY_TRIGGER_TASK.md | 09-30 | 8,700 | → C3_L4_N1 + C3_L4_NFT_NIGHT1 | DONE | phase-c |
| C3-L4-N2_NFT_NIGHT2_SCORE_AND_MILD_CAPACITY_TASK.md | 09-30 | 8,253 | → C3_L4_N2 + C3_L4_NFT_NIGHT2 | DONE | phase-c |
| C3-L4-N3_NFT_NIGHT3_SCORE_AND_C3L4_CLOSE_TASK.md | 09-30 | 8,611 | → C3_L4_NFT_NIGHT3_2026-09-30 | DONE | phase-c |
| C3-L4-S1_SHADOW_CONTROLLER_TASK.md | 09-28 | 10,298 | → C3_L4_S1_SHADOW_CONTROLLER_2026-09-24 | DONE | phase-c |
| C4-D1_ADAPTIVE_FEC_EVIDENCE_TASK.md | 09-28 | 5,649 | → C4_D1_FEC_EVIDENCE_2026-09-24 | DONE | phase-c |
| C4-M1_FEC_MEASURED_ARM_TASK.md | 09-28 | 6,420 | → C4_M1_FEC_ARM_2026-09-25 | DONE | phase-c |
| C5-CLOSE-A_LOOK3_AMEND_TASK.md | 10-05 | 3,604 | → C5_CLOSE_2026-10-05 (amended) | DONE | phase-c |
| C5-CLOSE_PHASE_C_CLOSE_TASK.md | 10-05 | 6,314 | → C5_CLOSE_2026-10-05 | DONE | phase-c |
| C5-M1_1080P60_PROFILE_TASK.md | 09-30 | 8,410 | → C5_M1_…_2026-09-28 | DONE | phase-c |
| C5-M2_1080P60_FOLLOWUP_ARMS_TASK.md | 09-30 | 6,276 | → C5_M2_…_2026-09-29 | DONE | phase-c |
| C5-M3_LOW_RUNG_SCREENING_TASK.md | 09-30 | 5,499 | → C5_M3_…_2026-09-29 | DONE | phase-c |
| C5-M4A_PS1_4X_SOURCE_ADOPTION_TASK.md | 10-01 | 5,575 | → C5_M4A_…_2026-10-01 | DONE | phase-c |
| C5-M4_PS1_NATIVE_1080P_SOURCE_TASK.md | 10-01 | 10,109 | → C5_M4_…_2026-10-01 | DONE | phase-c |
| C5-M5_1080P_RUNG_TASK.md | 10-03 | 9,911 | → C5_M5_1080P_RUNG_2026-10-03 | DONE | phase-c |
| C5-M5B_RUNG_RULES_AND_LOOK_TASK.md | 10-04 | 10,147 | → C5_M5B_…_2026-10-03 | DONE | phase-c |
| C6-D1_SOURCE_ABSTRACTION_DESIGN_TASK.md | 09-28 | 4,829 | → C6_D1_SOURCE_CONTRACT_2026-09-25 | DONE | phase-c |
| CL-B10_PART2_ATTENDED_TASK.md | 10-24 | 8,365 | → CL_B10_…_2026-10-23 | DONE | cl-b |
| CL-B11_GUARD_AND_FAST_READY_TASK.md | 10-24 | 8,022 | → CL_B11_…_2026-10-24 | DONE | cl-b |
| CL-B12_DEFAULTS_AND_UMBRELLA_TASK.md | 10-24 | 8,531 | → CL_B12_…_2026-10-24 | DONE | cl-b |
| CL-B13_RESTART_FAST_AND_WAN_CLASS_TASK.md | 10-25 | 9,991 | → CL_B13_…_2026-10-25 | DONE | cl-b |
| CL-B14_RESTART_UNLOCK_AND_NOTICE_DEFAULT_TASK.md | 10-26 | 7,026 | → CL_B14_…_2026-10-26 (`fcd924c2…` confirmed) | DONE | cl-b |
| CL-B15_LOSS_GUARD_DEFAULT_TASK.md | 10-27 | 6,125 | → CL_B15_…_2026-10-27 | DONE | cl-b |
| CL-B16_REMOTE_UMBRELLA_AND_QUIET_GUARD_TASK.md | 10-29 | 8,701 | → CL_B16_…_2026-10-29 | DONE | cl-b |
| CL-B1_APK_ADOPTION_TASK.md | 09-30 | 6,705 | → CL_B1_APK_ADOPTION_2026-09-30 | DONE | cl-b |
| CL-B2_IDENTITY_APK_INSTALL_AND_LAN_SMOKE_TASK.md | 10-16 | 3,067 | → CL_B2_…_2026-10-16 | DONE | cl-b |
| CL-B4_APK_OPUS_DECODE_TASK.md | 10-18 | 4,890 | → CL_B4_…_2026-10-18 | DONE | cl-b |
| CL-B5_OPUS_DECODE_THREAD_AND_AB_TASK.md | 10-18 | 4,461 | → CL_B5_…_2026-10-18 | DONE | cl-b |
| CL-B6_AB_REPEAT_AFTER_RESTART_TASK.md | 10-19 | 4,445 | → CL_B6_…_2026-10-19 | DONE | cl-b |
| CL-B7_OPUS_CLIENT_THREADS_AB_TASK.md | 10-21 | 7,752 | → CL_B7_…_2026-10-19 | DONE | cl-b |
| CL-B7P_OPUS_CLIENT_COST_TASK.md | 10-19 | 6,260 | → CL_B7P_…_2026-10-19 | DONE | cl-b |
| COWORK_HANDOFF_2026-09-22.md | 09-23 | 6,836 | cowork context 09-20..22; replaced by 09-23 | SUPERSEDED | cowork |
| COWORK_HANDOFF_2026-09-23.md | 09-23 | 6,549 | replaced by 09-29 | SUPERSEDED | cowork |
| COWORK_HANDOFF_2026-09-29.md | 09-30 | 7,133 | replaced by 10-05 | SUPERSEDED | cowork |
| COWORK_HANDOFF_2026-10-05.md | 10-05 | 7,739 | state duplicated by CURRENT.md and the records. **Its "how we work" section (the prompt-file bridge, the stage words, verify from raw artifacts) is the only full write-up of the user's working rules: carry it into `COMMUNICATION.md` before archiving** | SUPERSEDED | cowork |
| CTRL-L1_CONTROLLER_LOSS_LOCATION_TASK.md | 09-28 | 4,920 | → CTRL_L1_…_2026-09-24 | DONE | phase-c |
| CURRENT_HANDOFF.md | 10-16 | 14,010 | see §1.4 | LIVE (stale) | **keep** |
| D6-R1_UDP_SUITE_REPLAY_TASK.md | 09-28 | 4,560 | → D6_R1_…_2026-09-24 | DONE | phase-c |
| D7-R1_LINUX_REGRESSION_TASK.md | 09-28 | 4,858 | → D7_R1_…_2026-09-25 (named in a tool docstring) | DONE | phase-c |
| D-BASE-B2_TASK.md | 09-22 | 4,535 | → B2_HOST_ON_…_2026-09-21 | DONE | d-base |
| D-BASE-C5A_TASK.md | 09-22 | 3,690 | → C5A_IDR_REJECTION_COUNT_2026-09-21 | DONE | d-base |
| D-BASE-C5_TASK.md | 09-22 | 4,145 | → investigations/C5_RESYNC_…_2026-09-20 | DONE | d-base |
| D-BASE-CLOSE_TASK.md | 09-23 | 5,781 | → D_BASE_CLOSEOUT_2026-09-23 | DONE | d-base |
| D-BASE-H2_TASK.md | 09-22 | 11,173 | → H2_HEADLESS_CUTOVER_2026-09-22 | DONE | d-base |
| D-BASE-N05_CLOSE_TASK.md | 09-23 | 2,463 | → N05 section of D_BASE_R3D_HAND_RUNS | DONE | d-base |
| D-BASE-O1_TASK.md | 09-22 | 6,941 | → O1_…_AIR_VIEW_2026-09-21 | DONE | d-base |
| D-BASE-P10_TASK.md | 09-23 | 7,162 | → D_BASE_P10_…_2026-09-23 | DONE | d-base |
| D-BASE-P1_TASK.md | 09-22 | 5,173 | → D_BASE_P1_…_2026-09-20 | DONE | d-base |
| D-BASE-P2A_TASK.md | 09-22 | 3,450 | → D_BASE_P2A_…_2026-09-21 | DONE | d-base |
| D-BASE-P2B_TASK.md | 09-22 | 3,207 | → D_BASE_P2B_…_2026-09-21 | DONE | d-base |
| D-BASE-P2_TASK.md | 09-22 | 4,675 | → D_BASE_P2_…_2026-09-20 | DONE | d-base |
| D-BASE-P3_TASK.md | 09-22 | 5,081 | → D_BASE_P3_…_2026-09-21 | DONE | d-base |
| D-BASE-P4_TASK.md | 09-22 | 5,171 | → D_BASE_P4_…_2026-09-21 | DONE | d-base |
| D-BASE-P5_TASK.md | 09-22 | 6,153 | → D_BASE_P5_…_2026-09-21 | DONE | d-base |
| D-BASE-P6A_TASK.md | 09-22 | 7,095 | → D_BASE_P6A_CAP_ADOPTED_2026-09-22 | DONE | d-base |
| D-BASE-P6_TASK.md | 09-22 | 7,794 | → D_BASE_P6_…_2026-09-21 | DONE | d-base |
| D-BASE-P7_TASK.md | 09-22 | 5,954 | → D_BASE_P7_…_2026-09-22 | DONE | d-base |
| D-BASE-P8_TASK.md | 09-22 | 5,115 | → D_BASE_P8_…_2026-09-22 | DONE | d-base |
| D-BASE-P9A_TASK.md | 09-23 | 5,938 | → D_BASE_P9A_…_2026-09-23 | DONE | d-base |
| D-BASE-P9_TASK.md | 09-23 | 5,483 | → D_BASE_P9_…_2026-09-23 | DONE | d-base |
| D-BASE-R3A_TASK.md | 09-22 | 5,022 | → D_BASE_R3A_…_2026-09-20 | DONE | d-base |
| D-BASE-R3B_TASK.md | 09-22 | 7,075 | → D_BASE_R3B_…_2026-09-22 | DONE | d-base |
| D-BASE-R3C2_TASK.md | 09-23 | 7,630 | → D_BASE_R3C2_…_2026-09-23 | DONE | d-base |
| D-BASE-R3C_TASK.md | 09-22 | 7,707 | → D_BASE_R3C_… (part 2 via R3C2) | DONE | d-base |
| D-BASE-R3D_TASK.md | 09-23 | 6,368 | → D_BASE_R3D_HAND_RUNS_2026-09-22 | DONE | d-base |
| D-BASE-R3_TASK.md | 09-22 | 5,522 | → D_BASE_R3_…_2026-09-20 | DONE | d-base |
| D-BASE-R4_TASK.md | 09-22 | 5,063 | → D_BASE_R4_…_2026-09-20 | DONE | d-base |
| D-BASE-R5_TASK.md | 09-22 | 3,431 | → D_BASE_R5_…_2026-09-21 | DONE | d-base |
| D-BASE-S1_TASK.md | 09-22 | 4,754 | → D_BASE_S1_…_2026-09-21 | DONE | d-base |
| D-BASE-S2_TASK.md | 09-22 | 3,286 | → D_BASE_S2_…_2026-09-21 | DONE | d-base |
| D-BASE-S3_TASK.md | 09-22 | 4,801 | → D_BASE_S3_…_2026-09-22 | DONE | d-base |
| D-BASE-T1_TASK.md | 09-22 | 5,735 | → D_BASE_T1_…_2026-09-21 | DONE | d-base |
| D-BASE-T2_TASK.md | 09-23 | 7,907 | → D_BASE_T2_…_2026-09-23 | DONE | d-base |
| D-BASE-T3_TASK.md | 09-23 | 6,146 | → D_BASE_T3_…_2026-09-23 | DONE | d-base |
| E1-S1_WORKLOAD_SUITE_FREEZE_TASK.md | 10-05 | 8,249 | → E1_S1_…_2026-10-05 | DONE | phase-e |
| E2-S1_WHOLE_SYSTEM_MEASUREMENTS_TASK.md | 10-05 | 8,905 | → E2_S1_…_2026-10-06 | DONE | phase-e |
| E3-A2_FRAME_SPIN_AND_SNES9X_ADOPTION_TASK.md | 10-07 | 5,960 | → E3_A2_…_2026-10-07 | DONE | phase-e |
| E3-A3B_RECOVERY_V2_READOPTION_TASK.md | 10-09 | 4,573 | → E3_A3B_…_2026-10-09 | DONE | phase-e |
| E3-A3_RECOVERY_V2_ADOPTION_TASK.md | 10-09 | 6,911 | → E3_A3_… (reverted, redone by A3B) | DONE | phase-e |
| E3-R1_RECOVERY_FALSE_PAUSE_TASK.md | 10-08 | 7,036 | → E3_R1_…_2026-10-08 | DONE | phase-e |
| E3-R2_RECOVERY_PAUSE_EXIT_TASK.md | 10-08 | 6,889 | → E3_R2_…_2026-10-08 | DONE | phase-e |
| E3-S1_EPG_GRAB_PRIORITY_TASK.md | 10-06 | 4,355 | → E3_S1_…_2026-10-06 | DONE | phase-e |
| E3-S2_COMPANION_GUIDE_RETENTION_TASK.md | 10-06 | 3,333 | → E3_S2_…_2026-10-06 | DONE | phase-e |
| E3-S3_GRABBER_COST_TASK.md | 10-06 | 3,227 | → E3_S3_…_2026-10-06 | DONE | phase-e |
| E3-S4_SNES_LIGHTER_CORE_TASK.md | 10-06 | 3,661 | → E3_S4_…_2026-10-06/07 | DONE | phase-e |
| E3-S5_AUDIO_SENDER_COST_TASK.md | 10-06 | 3,407 | → E3_S5_…_2026-10-06 | DONE | phase-e |
| E3-S5B_AUDIO_SENDER_PACING_DECISIVE_TASK.md | 10-07 | 4,484 | → E3_S5B_…_2026-10-06 | DONE | phase-e |
| E3-S5C_AUDIO_SENDER_PACING_SPIN_TASK.md | 10-07 | 4,286 | → E3_S5C_…_2026-10-07 | DONE | phase-e |
| E3-S6A_GUIDE_INDEX_ADOPTION_TASK.md | 10-07 | 4,381 | → E3_S6A_…_2026-10-07 | DONE | phase-e |
| E3-S6_GUIDE_INDEX_TASK.md | 10-07 | 5,823 | → E3_S6_…_2026-10-07 | DONE | phase-e |
| E3-S7B_GRAB_PACING_SHORT_TASK.md | 10-08 | 3,748 | → E3_S7B_…_2026-10-08 | DONE | phase-e |
| E3-S7_CONC_GRAB_SPAWN_TASK.md | 10-08 | 4,689 | → E3_S7_…_2026-10-08 | DONE | phase-e |
| E4-C1_CLOSEOUT_AND_E5_S1_CAPABILITY_PROBE_TASK.md | 10-15 | 5,786 | → E4_CLOSEOUT + E5_S1_…_2026-10-15 | DONE | phase-e |
| E4-S1_REFERENCE_ON_ADOPTED_STATE_TASK.md | 10-09 | 3,237 | → E4_S1_…_2026-10-09 | DONE | phase-e |
| E4-S2_CPU_MEMORY_FLOOR_TASK.md | 10-09 | 5,932 | → E4_S2_…_2026-10-09 | DONE | phase-e |
| E4-S3B_MEMORY_FLOOR_1G_SWAPOFF_TASK.md | 10-15 | 3,789 | → E4_S3B_…_2026-10-10 | DONE | phase-e |
| E4-S3_MEMORY_FLOOR_CLOSE_TASK.md | 10-15 | 3,426 | → E4_S3_…_2026-10-10 | DONE | phase-e |
| E4-S4B_GRAB_DEFERRAL_CLEAN_LINK_TASK.md | 10-15 | 3,990 | → E4_S4B_…_2026-10-10 | DONE | phase-e |
| E4-S4C_LINK_WATCH_AND_DEFERRAL_TASK.md | 10-15 | 6,440 | → E4_S4C_LINK_WATCH_2026-10-16 (ran via S4D) | DONE | phase-e |
| E4-S4C_WATCH_RECORD_TASK.md | 10-16 | 1,468 | → E4_S4C_LINK_WATCH_2026-10-16 | DONE | phase-e |
| E4-S4D_LINK_WATCH_DETACHED_TASK.md | 10-15 | 3,728 | → E4_S4D_…_LAUNCH_2026-10-15 | DONE | phase-e |
| E4-S4_GRAB_DEFERRAL_TASK.md | 10-15 | 5,093 | → E4_S4_…_2026-10-10 | DONE | phase-e |
| E4-S5B_SNES_CAPTURE_PROBE_BENCH_TASK.md | 10-15 | 4,835 | → E4_S5B_…_2026-10-10 | DONE | phase-e |
| E4-S5C_SNES_CAPTURE_PROBE_BENCH_CFR_TASK.md | 10-15 | 3,972 | → E4_S5C_…_2026-10-10 | DONE | phase-e |
| E4-S5D_SNES_CAPTURE_FIX_ADOPTION_TASK.md | 10-15 | 2,621 | → E4_S5D_…_2026-10-15 | DONE | phase-e |
| E4-S5_SNES_CAPTURE_59FPS_TASK.md | 10-15 | 4,810 | → E4_S5_…_2026-10-10 | DONE | phase-e |
| DOCS-AUDIT_2026-11-02_TASK.md | untracked | 4,687 | this audit | LIVE | archive after the apply pass |
| G1-S1_TRUST_TOPOLOGY_AND_OVERLAY_PROVIDER_TASK.md | 10-16 | 4,748 | → G1_S1_…_2026-10-15 | DONE | g-track |
| G1-S2_OVERLAY_PROVIDER_LIVE_SMOKE_TASK.md | 10-16 | 2,331 | → G1_S2_…_2026-10-16 | DONE | g-track |
| G3-S1_SESSION_IDENTITY_HOST_SIDE_TASK.md | 10-16 | 5,337 | → G3_S1_…_2026-10-15 | DONE | g-track |
| G3-S2_SESSION_IDENTITY_CLIENT_SIDE_TASK.md | 10-16 | 4,946 | → G3_S2_…_2026-10-16 | DONE | g-track |
| G3-S3_HARDENING_AND_HUB_HOST_TASK.md | 10-16 | 4,806 | → G3_S3_…_2026-10-16 | DONE | g-track |
| G4-P1_OFFSITE_TEST_PREP_TASK.md | 10-16 | 4,689 | → G4_P1_…_2026-10-16 | DONE | g-track |
| G4-P2_REMOTE_ROW_GATE3_TASK.md | 10-17 | 2,522 | → G4_P2_…_2026-10-17 | DONE | g-track |
| G4_RUNBOOK_HOTSPOT.md | 10-16 | 5,180 | G4-S1's hotspot choreography; G4-S1 ran. **Its §A (one-time overlay onboarding on the onn) goes into the new RUNBOOK** | DONE | g-track |
| G4-S1_OFFSITE_FIRST_SESSION_TASK.draft.md | 10-16 | 6,189 | draft of the final task | SUPERSEDED | g-track |
| G4-S1_OFFSITE_FIRST_SESSION_TASK.md | 10-16 | 7,444 | → G4_S1_…_2026-10-16 | DONE | g-track |
| G4-S2_OFFSITE_REMOTE_LADDER_TASK.md | 10-18 | 7,346 | → G4_S2_…_2026-10-17 | DONE | g-track |
| G4-S3_OFFSITE_4000_OPUS_TASK.md | 10-19 | 8,156 | → G4_S3_…_2026-10-19 | DONE | g-track |
| G4-S4_OFFSITE_FREE_PLAY_TASK.md | 10-24 | 5,947 | → G4_S4_…_2026-10-24 | DONE | g-track |
| G4-W1_WIRE_OVERHEAD_BREAKDOWN_TASK.md | 10-18 | 3,916 | → G4_W1_…_2026-10-18 | DONE | g-track |
| G4-W2_OPUS_AUDIO_PATH_TASK.md | 10-18 | 3,613 | → G4_W2_…_2026-10-18 | DONE | g-track |
| G5-S1_WAN_TELEMETRY_CLASSIFICATION_TASK.md | 10-16 | 4,878 | → G5_S1_…_2026-10-16 | DONE | g-track |
| G5-S2_WAN_ADAPTATION_RULES_TASK.md | 10-16 | 4,145 | → G5_S2_…_2026-10-16 | DONE | g-track |
| G5-S3_LAN_SMOKE_TASK.md | 10-17 | 3,490 | → G5_S3_LAN_SMOKE_2026-10-17 | DONE | g-track |
| G5-S3_REMOTE_LADDER_TASK.md | 10-17 | 3,867 | → G5_S3_REMOTE_LADDER_2026-10-17 | DONE | g-track |
| G5-S4_REMOTE_RUNG_CAP_TASK.md | 10-17 | 2,636 | → G5_S4_…_2026-10-17 | DONE | g-track |
| G8-P1_IMPAIRMENT_SHIM_TASK.md | 10-16 | 4,112 | → G8_P1_…_2026-10-16 | DONE | g-track |
| G8-S1_ADVERSE_NETWORK_ENVELOPE_TASK.md | 10-16 | 5,597 | → G8_S1_…_2026-10-17 | DONE | g-track |
| G8-S1_FINAL_RECORD_TASK.md | 10-17 | 7,389 | → G8_S1_…_2026-10-17 | DONE | g-track |
| G8-S1_RESUME_TASK.md | 10-17 | 3,577 | → G8_S1_RESUME_2026-10-17 | DONE | g-track |
| G8-S1_STOP_AND_PARTIAL_RECORD_TASK.md | 10-16 | 4,987 | → G8_S1_… partial 2026-10-16 | DONE | g-track |
| G8-S2_START_RUNG_TASK.md | 10-17 | 4,681 | → G8_S2_…_2026-10-17 | DONE | g-track |
| G8-S3_CAP_CELLS_START_RUNG_TASK.md | 10-17 | 5,154 | → G8_S3_LAUNCH_2026-10-17 | DONE | g-track |
| G8-S3_RECORD_TASK.md | 10-17 | 4,870 | → G8_S3_…_2026-10-17 | DONE | g-track |
| G8-S4_ENCODER_RATE_HEADROOM_TASK.md | 10-18 | 4,545 | → G8_S4_…_2026-10-18 | DONE | g-track |
| G8-S5_CAP_CELL_ENCODER_RC_TIGHT_TASK.md | 10-19 | 7,287 | → G8_S5_…_2026-10-19 | DONE | g-track |
| G-A10_STEP_IN_PLACE_ADOPTION_TASK.md | 11-02 | 4,583 | A running now; record pending | LIVE | **keep** |
| G-A1_ADOPTION_AND_CL-B3_TASK.md | 10-16 | 4,551 | → G_A1_…_2026-10-16 + CL_B3_… | DONE | g-track |
| G-A2_OPUS_ADOPTION_TASK.md | 10-18 | 4,177 | → G_A2_…_2026-10-19 | DONE | g-track |
| G-A3_AND_CL-B10_TASK.md | 10-23 | 6,976 | → G_A3_…_2026-10-23 + CL_B10_… | DONE | g-track |
| G-A4_LINK_RECOVERY_ADOPTION_TASK.md | 10-24 | 3,021 | → G_A4_…_2026-10-24 | DONE | g-track |
| G-A5_RESTART_FAST_ADOPTION_TASK.md | 10-25 | 4,713 | → G_A5_…_2026-10-26 | DONE | g-track |
| G-A7_RESTART_FAST_UNLOCK_ADOPTION_TASK.md | 10-27 | 4,399 | → G_A7_…_2026-10-27 | DONE | g-track |
| H1_VERIFY_TASK.md | 09-22 | 3,941 | → H1_VERIFY_…_2026-09-22 | DONE | overnight |
| H2_CLOSE_TASK.md | 09-23 | 4,473 | → H2_HEADLESS_CUTOVER_2026-09-22 | DONE | overnight |
| H2_PREP_TASK.md | 09-22 | 5,452 | → H2_PREP_…_2026-09-22 | DONE | overnight |
| H3_COMPANION_AUTOSTART_TASK.md | 09-23 | 5,709 | → H3_…_DESIGN_2026-09-23 | DONE | overnight |
| HOME-1_TRIP_CLOSE_AND_QUEUE_L_CELLS_TASK.md | 11-02 | 9,401 | → HOME_1_…_2026-11-02 | DONE | trip |
| LAN-R1_LOSS_STEPDOWN_REPLAY_AND_DESIGN_TASK.md | 10-21 | 6,720 | → LAN_R1_…_2026-10-21 | DONE | ux-reads |
| LINK-L1_LOSS_ROW_LOOK_AND_LIVE_DEFAULT_TASK.md | 10-01 | 10,162 | → LINK_L1_… + C3_L4_D1_… | DONE | phase-c |
| LINK-L2_LOSS_ROW_AT_40MHZ_TASK.md | 10-01 | 5,312 | → LINK_L2_…_2026-10-02 | DONE | phase-c |
| LINK-R1_5GHZ_CHECK_AND_NIGHTLY_WATCH_TASK.md | 10-23 | 7,669 | → LINK_R1_… + LINK_N1_LAUNCH (watch ended 10-31; no nights record found) | DONE | ux-reads |
| M1_DOCS_RECONCILE_TASK.md | 09-22 | 5,126 | → CHECKPOINT_PROPOSAL_2026-09-22 | DONE | overnight |
| ML-R1_HITCH_EARLY_WARNING_TASK.md | 10-22 | 8,225 | → ML_R1_…_2026-10-23 | DONE | ux-reads |
| OVERNIGHT_2026-09-22_QUEUE.md | 09-22 | 2,725 | P6A, S3, P7, H2-PREP, M1 records | DONE | overnight |
| OVERNIGHT_2026-09-23B_QUEUE.md | 09-23 | 2,407 | N05, R3C2, H3 records | DONE | overnight |
| OVERNIGHT_2026-09-23_QUEUE.md | 09-22 | 2,328 | P8, R3C records | DONE | overnight |
| OVERNIGHT_2026-09-24_QUEUE.md | 09-24 | 3,373 | C3_L3A_S1 record | DONE | overnight |
| PHASE_C_PRECONDITIONS_2026-09-25_TASK.md | 09-28 | 13,026 | C3_F1, D7_R1 §R2, CL_B1 | DONE | phase-c |
| PLAN_WEEK_2026-09-21.md | 09-22 | 3,627 | week plan, overtaken | SUPERSEDED | overnight |
| PREPUSH_AUDIT_TASK.md | 10-05 | 2,989 | → PREPUSH_AUDIT_2026-10-05 | DONE | phase-c |
| QUEUE_2026-09-28B.md | 09-30 | 2,338 | replaced by QUEUE_09-29 | SUPERSEDED | queues |
| QUEUE_2026-09-28.md | 09-30 | 2,134 | C3_L3A_R4, C5_M1 | DONE | queues |
| QUEUE_2026-09-29B.md | 09-30 | 1,533 | C3_L4_N1, C5_M2, C5_M3 | DONE | queues |
| QUEUE_2026-09-29.md | 09-30 | 1,920 | replaced by 09-29B | SUPERSEDED | queues |
| QUEUE_2026-10-06B.md | 10-07 | 2,096 | E3_S5B, E3_S6 | DONE | queues |
| QUEUE_2026-10-06.md | 10-06 | 3,924 | E3_S1..S5 | DONE | queues |
| QUEUE_2026-10-07.md | 10-07 | 2,675 | E3_S4, S5C, S6A | DONE | queues |
| QUEUE_2026-10-08B.md | 10-08 | 1,623 | E3_R2, S7B | DONE | queues |
| QUEUE_2026-10-08.md | 10-08 | 2,191 | E3_R1, S7 | DONE | queues |
| QUEUE_2026-10-09.md | 10-09 | 1,764 | E4_S1, S2 | DONE | queues |
| QUEUE_2026-10-10B.md | 10-15 | 2,692 | E4_S3B, S4B, S5B | DONE | queues |
| QUEUE_2026-10-10C.md | 10-15 | 3,116 | E4_S4C, S5C | DONE | queues |
| QUEUE_2026-10-10.md | 10-15 | 2,269 | E4_S3, S4, S5 | DONE | queues |
| QUEUE_2026-10-15B.md | 10-16 | 2,698 | → SESSION_B_DONE_2026-10-15B | DONE | queues |
| QUEUE_2026-10-15.md | 10-15 | 2,510 | → SESSION_B_DONE_2026-10-15 + E4_S5D | DONE | queues |
| QUEUE_2026-10-16B.md | 10-16 | 2,946 | → SESSION_B_DONE_2026-10-16B | DONE | queues |
| QUEUE_2026-10-16C.md | 10-16 | 2,867 | → SESSION_B_DONE_2026-10-16C2 | DONE | queues |
| QUEUE_2026-10-16.md | 10-16 | 3,158 | CL_B2, E4_S4C, G1_S2 | DONE | queues |
| QUEUE_2026-10-17.md | 10-17 | 3,595 | → SESSION_B_DONE_2026-10-17 | DONE | queues |
| QUEUE_2026-10-18.md | 10-18 | 3,320 | → SESSION_B_DONE_2026-10-18 | DONE | queues |
| **QUEUE_2026-10-19B.md** | 10-21 | 5,635 | M-2 memory maintenance + G9-D1 checkpoint draft; **never run** (no report, draft, logs or DONE file) — see §2.7 | HELD | queues |
| **QUEUE_2026-10-19N.md** | 10-21 | 7,323 | A night driver: G8-S6 (three paired cap-6000 cells, control vs `PRIVYHUB_ENCODER_RC=tight`) + G5-S2-L (first live LAN smoke of the WAN adaptation rules); **never run** (no launch, record or unit; CURRENT.md: "HELD until the user says"); its preconditions ("the eight lines") are stale. Both questions are still open: carry them to KNOWN_ISSUES / CURRENT "Open, not blocking" before archiving | HELD | queues |
| QUEUE_2026-10-22B.md | 10-21 | 8,524 | → SESSION_B_DONE_2026-10-22 | DONE | queues |
| QUEUE_2026-10-22C.md | 10-22 | 10,398 | → SESSION_B_DONE_2026-10-22C | DONE | queues |
| QUEUE_2026-10-22D.md | 10-22 | 7,958 | → SESSION_B_DONE_2026-10-22D | DONE | queues |
| QUEUE_2026-10-23E.md | 10-23 | 8,413 | → SESSION_B_DONE_2026-10-23E | DONE | queues |
| QUEUE_2026-10-24F.md | 10-24 | 6,446 | → SESSION_B_DONE_2026-10-24F | DONE | queues |
| QUEUE_2026-10-24G.md | 10-24 | 7,826 | → SESSION_B_DONE_2026-10-24G | DONE | queues |
| QUEUE_2026-10-24H.md | 10-24 | 5,935 | → SESSION_B_DONE_2026-10-24H | DONE | queues |
| QUEUE_2026-10-26I.md | 10-25 | 7,053 | → SESSION_B_DONE_2026-10-26I | DONE | queues |
| QUEUE_2026-10-27J.md | 10-27 | 5,248 | → SESSION_B_DONE_2026-10-27J | DONE | queues |
| QUEUE_2026-10-28K.md | 10-27 | 9,453 | → SESSION_B_DONE_2026-10-28K | DONE | queues |
| QUEUE_2026-10-31L.md | 11-02 | 12,235 | → SESSION_B_DONE_2026-10-31L | DONE | queues |
| QUEUE_2026-11-02M.md | 11-02 | 5,874 | B's queue; stopped at its precondition (G-A10 record) | LIVE | **keep** |
| SESSION_B_DONE_2026-10-15B.md | 10-16 | 2,051 | closes QUEUE_10-15B | DONE | session-b-done |
| SESSION_B_DONE_2026-10-15.md | 10-15 | 1,579 | closes QUEUE_10-15 (B part) | DONE | session-b-done |
| SESSION_B_DONE_2026-10-16B.md | 10-16 | 2,227 | closes QUEUE_10-16B | DONE | session-b-done |
| SESSION_B_DONE_2026-10-16C2.md | 10-16 | 2,512 | closes QUEUE_10-16C | DONE | session-b-done |
| SESSION_B_DONE_2026-10-16C.md | 10-16 | 2,457 | closes G3-S3 | DONE | session-b-done |
| SESSION_B_DONE_2026-10-16.md | 10-16 | 1,708 | closes G3-S2 | DONE | session-b-done |
| SESSION_B_DONE_2026-10-17B.md | 10-17 | 2,388 | closes G8-S2 | DONE | session-b-done |
| SESSION_B_DONE_2026-10-17.md | 10-17 | 2,531 | closes QUEUE_10-17 | DONE | session-b-done |
| SESSION_B_DONE_2026-10-18.md | 10-18 | 2,513 | closes QUEUE_10-18 | DONE | session-b-done |
| SESSION_B_DONE_2026-10-19.md | 10-19 | 2,680 | closes CL-B7P (not 19B) | DONE | session-b-done |
| SESSION_B_DONE_2026-10-21.md | 10-21 | 2,999 | closes LAN-R1 | DONE | session-b-done |
| SESSION_B_DONE_2026-10-22B.md | 10-22 | 3,484 | closes B4 | DONE | session-b-done |
| SESSION_B_DONE_2026-10-22C.md | 10-22 | 5,216 | closes QUEUE_10-22C | DONE | session-b-done |
| SESSION_B_DONE_2026-10-22D.md | 10-22 | 6,534 | closes QUEUE_10-22D | DONE | session-b-done |
| SESSION_B_DONE_2026-10-22.md | 10-21 | 4,168 | closes QUEUE_10-22B | DONE | session-b-done |
| SESSION_B_DONE_2026-10-23E.md | 10-23 | 6,516 | closes QUEUE_10-23E | DONE | session-b-done |
| SESSION_B_DONE_2026-10-24F.md | 10-24 | 6,770 | closes QUEUE_10-24F | DONE | session-b-done |
| SESSION_B_DONE_2026-10-24G.md | 10-24 | 8,275 | closes QUEUE_10-24G | DONE | session-b-done |
| SESSION_B_DONE_2026-10-24H.md | 10-25 | 8,998 | closes QUEUE_10-24H | DONE | session-b-done |
| SESSION_B_DONE_2026-10-26I.md | 10-26 | 7,783 | closes QUEUE_10-26I | DONE | session-b-done |
| SESSION_B_DONE_2026-10-27J.md | 10-27 | 9,962 | closes QUEUE_10-27J | DONE | session-b-done |
| SESSION_B_DONE_2026-10-28K.md | 10-29 | 11,844 | closes QUEUE_10-28K | DONE | session-b-done |
| SESSION_B_DONE_2026-10-31L.md | 11-02 | 17,078 | closes QUEUE_10-31L; holds HOME-1's strings that queue M's HOME-2 builds on | DONE | **keep until queue M's DONE exists**, then session-b-done |
| SESSION_B_STATUS.txt | 11-02 | 24,780 / 43 lines | B's append-only step log, 10-22 → 11-03 UTC; one uncommitted line | LIVE | **keep** (B writes it) |
| TRIP-PREP_2026-10-29_TASK.md | 10-29 | 7,080 | → TRIP_PREP_2026-10-29 | DONE | trip |
| TRIP-R1_MULTIPLAYER_BLITZ_READ_TASK.md | 11-02 | 6,601 | folded into TRIP-R2, never run | SUPERSEDED | trip |
| TRIP-R2_FRIDAY_GAMEPLAY_READ_TASK.md | 11-02 | 7,102 | → TRIP_R2_…_2026-10-31 | DONE | trip |
| TRIP_RUNBOOK_2026-10-30.md | 10-29 | 6,012 | the user's trip steps A–F; the trip ran and was closed by HOME-1 | DONE | trip (after `docs/RUNBOOK.md` exists) |
| UX-R1_EXTENDED_SESSION_REGRESSION_READ_TASK.md | 10-21 | 8,347 | → UX_R1_…_2026-10-20 | DONE | ux-reads |
| UX-R2_SECOND_EVENING_READ_TASK.md | 10-21 | 5,455 | → UX_R2_…_2026-10-21 | DONE | ux-reads |
| UX-R3_FIND_THE_DEATHS_TASK.md | 10-21 | 5,594 | → UX_R3_…_2026-10-21 | DONE | ux-reads |
| UX-R4_SAVED_AT_THE_LAG_TASK.md | 10-23 | 5,344 | → UX_R4_…_2026-10-23 | DONE | ux-reads |
| WAN-R1_OFFSITE_GAP_DISTRIBUTION_TASK.md | 10-24 | 2,507 | → WAN_R1_…_2026-10-24 | DONE | ux-reads |
| WEEKEND_2026-09-24_QUEUE.md | 09-28 | 3,799 | all five records exist | DONE | overnight |
| WEEKEND_2026-09-25_QUEUE.md | 09-28 | 3,478 | C4_M1, C6_D1, D7_R1 | DONE | overnight |

### 1.6 `docs/memory/patches/` (237 tracked + 1 untracked)

**Tally:**

| Verdict | Count | Files |
|---|---:|---|
| APPLIED | 227 | — |
| PREPARED-UNAPPLIED | 1 | G-A8 |
| SUPERSEDED | 8 | — |
| INDEX / PROTOCOL | 2 | — |

**Keep in place:** `PATCH_INDEX.md`, `PATCH_PROTOCOL.md`, `G-A8_LOSS_GUARD_ADOPTION_PREPARED.md` (the only live candidate), and `G-A10_STEP_IN_PLACE_ADOPTION.md` (untracked, A's; until it is committed). Archive the other 234.

**`PATCH_INDEX.md` (10-15, 7,151) is stale:**
- Its header says "Records: 152" but it lists 167 entries.
- Nothing after E4 is in it: 69 of 236 notes are missing (all B1–B36, all G-A1–G-A10, all G1–G8, CL-B2–CL-B7P, LAN-R1/R2).
- Rewrite it as the status index of every note and its archived path.

**Status lines that are wrong today:**

| Note | Says | Truth |
|---|---|---|
| G-A4 | PREPARED | adopted (line 10) |
| G-A9 | PREPARED | adopted (line 13) |
| E4-S5 | "REJECTED, dormant" | adopted via E4-S5D |
| E3-R1, E3-R2 | "dormant" | adopted via E3-A3B |
| C3-L2C-R1 | "decision pending" | in the tree |
| most B / G notes | "nothing committed" | since committed |

Do not edit the notes. Record each truth in PATCH_INDEX.

**No note exists for:** B31, B37 (a read), G-A6 (shelved), CL-B6, CL-B8–CL-B16, E4-S5D.

| File(s) | Dates | Bytes | Claimed | Verdict | Group |
|---|---|---|---|---|---|
| PATCH_INDEX.md | 10-15 | 7,151 | generated index | INDEX (stale) | **keep, rewrite** |
| PATCH_PROTOCOL.md | 09-18 | 3,038 | workflow | PROTOCOL | **keep** |
| ADB_ENDPOINT_DEBUG_PROBE_V1_2026-09-15, ADB_ENDPOINT_DEBUG_WATCH_PORT_V1_2026-09-15, ADB_EPHEMERAL_PORT_RECOVERY_PROBE_V2_2026-09-15, ADB_RECOVERY_PROBE_LINUX_PARITY_2026-09-15 | 09-16 | 732 / 653 / 1,111 / 1,380 | dev diagnostic, validation pending | APPLIED | adb |
| ADB_EPHEMERAL_PORT_RECOVERY_PROBE_2026-09-15 | 09-16 | 1,292 | runtime pending | SUPERSEDED (by V2) | adb |
| D-074_LINUX_NATIVE_VIDEO_BACKEND, D-075R1_LINUX_NATIVE_AUDIO_RT_PACER, D-076_LINUX_UINPUT_CONTROLLER_BACKEND, D-076R1_LINUX_AUTOCONFIG_SESSION_PATH, D-076R2_LINUX_AUTOCONFIG_SYS_IMPORT, D-077_LINUX_PLATFORM_RUNTIME_SELECTION, D-078_LINUX_COMPANION_MEDIA_SERVER_STARTUP, D4_LINUX_GAME_HANDOFF_FIX_01_2026-09-15 (8) | 09-15/16 | 829–4,553 | host validated / dev patch | APPLIED | d-series |
| D-075_LINUX_NATIVE_AUDIO_BACKEND | 09-15 | 1,971 | original cadence rejected | SUPERSEDED (by D-075R1) | d-series |
| D-084_LINUX_A8_PLATFORM_ADAPTER, D-085_LINUX_UDEV_HAT_MAPPING, D-086_CONTROLLER_PARITY_CHECKPOINT, D-087_LINUX_PS1_MULTITAP_CONFIG_PATH, D-087R1_LINUX_PS1_MULTITAP_METADATA_PATH, D-088R1_MULTITAP_RUNTIME_VALIDATION, D-089_D5_EXTERNAL_VOD_STORAGE_CONSTRAINT, D-090_D4_LINUX_GAMES_ACCEPTANCE, D-091_D5_MEDIA_BASELINE_AND_CLIENT_BOUNDARY_PROBE, D-092_DYNAMIC_VOD_SYMLINK_HEALTH, D-093R2_D5_EXTERNAL_VOD_RUNTIME_VALIDATION, D-094_D5_EXTERNAL_STORAGE_REMOUNT_EVIDENCE, D-096_CONFIGURABLE_VOD_STORAGE_BOUNDARY, D-096R1_STORAGE_DEVICE_DISCOVERY, D-096R2R1_PROBE_INSTALLER_PRESTATE, D-096R3_PROBE_LISTENER_LIFECYCLE, D-097_VOD_APPLIANCE_MODE, D-098_ABSENT_VOD_CATALOG_RESILIENCE, D-099_NONBLOCKING_VOD_PRESENCE, D-099R1_PRESTATE_RECEIPT_ORDER, D-100_D5_EXTERNAL_VOD_HOTPLUG_RUNTIME_ACCEPTANCE, D-101R1_BROWSER_CAMERA_C6_RECLASSIFICATION (22) | 09-16 | 402–1,736 | no status line / checkpoint | APPLIED | d-series |
| D-103_D5_EPG_INGESTION_PROBE, D-104R2_D5_EPG_GZIP_SOURCE_SUPPORT, D-105_D5_EPG_LOCAL_SOURCE_VIABILITY_PROBE, D-106_D5_EPG_PROVIDER_IDENTITY_PROBE, D-107_D5_EPG_FEED_IDENTITY_PROBE, D-108_D5_EPG_LOCAL_GRABBER_VIABILITY_PROBE, D-109_D5_EPG_PORTABLE_NODE_GRABBER_PROBE, D-110_D5_LINUX_EPG_SERVICE_SEAM, D-111_D5_ANDROID_COMPANION_EPG_INTEGRATION, D-112_D5_PROGRAM_GUIDE_NEWLINE_POLISH, D-113_D5_STREAM_IDENTITY_AUDIT, D-114_D5_STREAM_IDENTITY_POLICY_CHECKPOINT (12) | 09-16 | 781–2,773 | type: diagnostic / seam | APPLIED | d-series |
| D-115_D5_LINUX_TV_STATE_AUTHORITY, D-116_D5_ANDROID_TV_STATE_SYNC, D-117_D5_LINUX_AUTHORITY_PULL_PROBE, D-118_D5_PULL_CLASSIFIER_ACCEPTANCE_CHECKPOINT, D-119_D5_TV_ENTRY_SYNC_TRIGGER_PROBE, D-120_D5_TV_STATE_SYNC_DIAGNOSTICS, D-121_D5_TV_STATE_CONFLICT_DIAGNOSTICS_PROBE, D-122_D5_TV_MEDIA_REGRESSION_GATE, D-123_D54_CLOSURE_TV_UX_FOLLOWUP, D-124_TV_EPG_LATENCY_PROBE, D-124A_TV_EPG_LATENCY_PROBE_SPLIT_DB_FIX, D-125_EPG_NONBLOCKING_BACKGROUND_WARMER, D-126_ANDROID_EPG_PREFETCH_INTEGRATION, D-127_D5_INCORRECT_GUIDE_INTENT, D-128_GUIDE_STYLE_CATEGORY_PRESENTATION, D-129_SINGLE_COLUMN_TV_GUIDE, D-130_TV_ENTRY_LATENCY_PROBE, D-131_NONBLOCKING_TV_ENTRY_STATE_SYNC, D-132_FAVORITES_EPG_COVERAGE_PROBE, D-133_EPG_STATUS_ACCURACY, D-134_FAVORITES_LOAD_LATENCY_PROBE, D-135_TV_STATE_EXECUTOR_ISOLATION, D-136_FOCUSED_TV_MEDIA_REGRESSION, D-137_TV_STATE_PROBE_V2_PROJECTION, D-138_D136_AUTOMATED_REGRESSION_ACCEPTANCE, D-139_D5_TV_MEDIA_CLOSEOUT (26) | 09-17/18 | 607–1,760 | runtime accepted / closeout (D-127, D-128 "validation pending") | APPLIED (D5 closed) | d-series |
| D4_MEMORY_RECONCILIATION_2026-09-16 | 09-16 | 1,570 | memory reconcile | APPLIED | d-series |
| D-BASE_BASELINE_STREAM_HEALTH, D-BASE-C5A_IDR_REJECTION_COUNTERS, D-BASE-P1_STALE_THRESHOLD_PROBE_KNOB, D-BASE-P2_AUDIO_TICK_SERIES_PROBE, D-BASE-P2A_AUDIO_STARTUP_HOLD, D-BASE-P3_FEC_RELAY_SENDER_PACING, D-BASE-P5_RELAY_FRAME_SIZE_COUNTERS, D-BASE-P6_FRAME_BYTE_COUNTERS_AND_ENCODER_KNOBS, D-BASE-P6A_FRAME_CAP_PROFILE_DEFAULT, D-BASE-P7_AUDIO_HEARTBEAT_COUNTERS, D-BASE-P8_AUDIO_HOLE_RING, D-BASE-P9_AUDIO_CUSHION_SETTING, D-BASE-P10_AUDIO_REDUNDANCY, D-BASE-R1_GROUP_A_LIVE_AND_RESYNC_LOSS_COUNTER, D-BASE-R2_STALL_VISIBILITY_AND_LAUNCHER_RECONCILE, D-BASE-R3_LINK_DROP_SELF_RECOVERY, D-BASE-R3A_RESTART_FALLBACK_AND_TRIGGER_FRESHNESS, D-BASE-R3C2_RECOVERY_FLOW, D-BASE-R4_SESSION_REPORT_VISIBILITY, D-BASE-R5_HEARTBEAT_LOSS_COUNTERS, D-BASE-T1_THERMAL_TELEMETRY, D-BASE-T2_P0_AUDIO_CUSHION_ADOPTED (22) | 09-20→09-23 | 1,697–9,579 | installed / validated | APPLIED | d-base |
| C3-CTX_PHASE_C_CONTINUATION_CONTEXT, C3-F1_RECOVERY_RESTART_LADDER, C3-HO_PHASE_C_HANDOFF_SYNC, C3-L0_LINUX_ACTUATOR_BOUNDARY_MEMORY_RECONCILIATION, C3-L0R1_CURRENT_STRUCTURE_AND_HEALTH_GATE, C3-L1_LINUX_ACTUATOR_CONTINUITY_PROBE, C3-L1R1_RTP_BASELINE_MEASUREMENT_CORRECTION, C3-L2_LINUX_ACTUATOR_CLASSIFICATION, C3-L2A-E2_ACTUATOR_IDR_RESOLVED, C3-L2B_DECODER_REPORT_CYCLE_RETENTION, C3-L2C-R1_LOW_LATENCY_DECODE_REINSTATED, C3-L3_LINUX_FIXED_BITRATE_PORT, C3-L3R1_CHARACTERIZATION_CORRECTION, C3-L3R2_GATE_DEFINITION_AND_DECISION_SYNC, C3-L3A-P1_LINUX_VALIDATED_LADDER_TRANSITION, C3-L3A-P1R1_LADDER_RUNTIME_EVIDENCE, C3-L3A-P2_GAMEPLAY_ACCEPTANCE_PROBE, C3-L3A-P2R1_PROBE_DEFECTS_AND_RESCORE, C3-L3A-P2R2_PHASE_B_WINDOW_ANCHOR, C3-L3A-P2R3_POOLING_RULE, C3-L3A-R1_SPLIT_SESSION_FINALIZE, C3-L3A-R2B_DECODER_REPORT_CAP, C3-L4-D1_LIVE_DEFAULT_PREFLIGHTS, C3-L4-L1_LIVE_CONTROLLER, C3-L4-L2_INCREASE_RULE_AND_SAMPLES, C3-L4-L2B_NFT_HARNESS_ONE_WINDOW, C3-L4-N1_CAPACITY_TRIGGER_AND_BACKSTOP, C3-L4-N2_MILD_CAPACITY, C3-L4-S1_SHADOW_CONTROLLER (29) | 09-18→10-01 | 2,745–9,302 | installed / working | APPLIED | phase-c |
| C3-L2C_LOW_LATENCY_DECODE_ENABLE | 09-19 | 5,273 | rolled back | SUPERSEDED (by C3-L2C-R1) | phase-c |
| C3-L2A-E1_FIRST_IDR_EVIDENCE_PASS | 09-18 | 4,445 | question unanswered | SUPERSEDED (by L2A-E2) | phase-c |
| C4-M1_FEC_XOR8_2_ARM, C5-M1_1080P60_CANDIDATE_PROFILE, C5-M2_1080P60_FOLLOWUP_PROFILES, C5-M3_LOW_RUNG_PROFILES, C5-M5_1080P_RUNG, C5-M5B_RUNG_ENTRY_AND_PS1_LOOK, C5-CLOSE_RUNG_WINDOW_RULE_AND_ATTRACT_FIX, C6-D1_SOURCE_CONTRACT (8) | 09-28→10-05 | 1,325–6,174 | built behind flags | APPLIED | phase-c |
| E1-S1_WORKLOAD_SUITE_RUNNER_AND_SAMPLER, E2-S1_SAMPLER_THREADS_ENCODER_AND_VOD_ROW, E3-A2_ADOPTED_STATE_CHECKS, E3-A3B_RECOVERY_V2_READOPTION, E3-R1_RECOVERY_TRIGGER_V2, E3-R2_RECOVERY_PAUSE_EXIT, E3-S1_EPG_GRAB_PRIORITY, E3-S2_EPG_MALLOC_TRIM, E3-S3_EPG_DIRECT_NODE, E3-S4_SNES_CORE_FLAG, E3-S5_AUDIO_SENDER_PACING, E3-S5B_AUDIO_SEND_TRACE, E3-S5C_AUDIO_SENDER_FRAME_SPIN, E3-S6_GUIDE_INDEX, E3-S6A_GUIDE_INDEX_ADOPTION_STATE_CHECK, E3-S7_GRAB_NET_PACED, E3-S7B_GRAB_DELAY_VALUE, E4-S2_CONSTRAINT_DROPIN_AND_CGROUP_RUNNER, E4-S3_SWAP_AND_MEMORY_READINGS_RUNNER, E4-S3B_RUNNER_REFRESH_BACKOFF, E4-S4_GRAB_DEFERRAL_FLAG, E4-S5_SNES_CAPTURE_OUTPUT_RATE_FLAG (22) | 10-05→10-15 | 1,075–2,946 | tools only / adopted / dormant | APPLIED | phase-e |
| E3-A3_RECOVERY_V2_ADOPTION | 10-09 | 1,899 | adopted then reverted | SUPERSEDED (by E3-A3B) | phase-e |
| E3-S4_SNES_CORE_RUNNER_SUPPORT | 10-06 | 1,065 | prepared, not applied | SUPERSEDED (by E3-S4_SNES_CORE_FLAG) | phase-e |
| CL-B1_DECODER_REPORT_BODY, CL-B2_IDENTITY_APK_HASH, CL-B3_HARDENED_APK_HASH, CL-B4_OPUS_APK_HASH, CL-B5_DECODE_THREAD_APK_HASH, CL-B7_LEAN_APK_HASH, CL-B7P_OPUS_DRAIN_LEAN_FLAG (7) | 09-28→10-21 | 1,536–2,902 | installed / built | APPLIED (APK pins since replaced) | cl-b |
| G1-S1_OVERLAY_PROVIDER_BOUNDARY, G3-S1_SESSION_IDENTITY_HOST_SIDE, G3-S2_SESSION_IDENTITY_CLIENT_SIDE, G3-S3_HARDENING_AND_HUB_HOST, G4-P1_E1_SUITE_REMOTE_ROW, G4-P2_REMOTE_ROW_GATE3, G4-W2_OPUS_AUDIO_PATH, G5-S1_WAN_TELEMETRY_CLASSIFICATION, G5-S2_WAN_ADAPTATION_RULES, G5-S3_REMOTE_LADDER, G5-S4_REMOTE_RUNG_CAP, G8-P1_IMPAIRMENT_SHIM, G8-S1_SHIM_NONE_PROFILE, G8-S2_START_RUNG, G8-S4_ENCODER_RATE_HEADROOM (15) | 10-16→10-18 | 1,052–3,899 | built behind flag | APPLIED | g-track |
| G-A1_OVERLAY_AND_IDENTITY_ADOPTED, G-A2_OPUS_ADOPTED, G-A3_LINK_REPORT_ADOPTED, G-A4_LINK_RECOVERY_ADOPTION_PREPARED (status stale), G-A5_RESTART_FAST_ADOPTION, G-A7_RESTART_FAST_UNLOCK_ADOPTION, G-A9_REMOTE_ADOPTION_PREPARED (status stale) (7) | 10-16→10-29 | 2,047–9,116 | applied / prepared | APPLIED | g-track |
| G-A3_LINK_REPORT_ADOPTION_PREPARED | 10-23 | 8,489 | prepared | SUPERSEDED (by G-A3_…_ADOPTED) | g-track |
| G-A8_LOSS_GUARD_ADOPTION_PREPARED | 10-27 | 8,977 | prepared, nothing applied | **PREPARED-UNAPPLIED** | **keep** |
| G-A10_STEP_IN_PLACE_ADOPTION | untracked | 7,504 | APPLIED (A, today) | APPLIED, uncommitted | **keep** until committed, then g-track |
| B1_SHIM_BLACKOUT_BOTH, B1B_SHIM_GATE, B2_INPUT_HOLD, B3_CLIENT_LINK_REPORT, B4_INPUT_HOLD_REWIND, B5_CLIENT_WIFI_LOCK, B6_INPUT_HOLD_TRIGGER, B7_CLIENT_STALL_SIGNAL, B8_HOLD_STALL_OWNERSHIP, B9_STALL_THRESHOLD_AND_REWIND_CORES, B10_CLIENT_LOSS_GUARD, B11_CLIENT_RESTART_GUARD, B12_STATE_FOR_ALL_AND_STALL_RESUME, B13_LINK_REPORT_DEFAULT_ON, B14_LINK_NOTICE, B15_RESTART_GUARD_ALL_PATHS, B16_STALL_RESUME_SPEED, B17_GUARD_AUDIO_ORDER, B18_NO_SAVE_AT_SESSION_END, B19_CLIENT_DEFAULTS_ON, B20_LINK_RECOVERY_UMBRELLA, B21_LINK_RECOVERY_CONFIG_LOG, B22_RESTART_FAST, B23_LINK_RECOVERY_WAN_THRESHOLDS, B24_RESTART_FAST_UNLOCK, B25_LINK_NOTICE_DEFAULT_ON, B26_RELAY_STOP_STRAY_PACKET, B27_LOSS_GUARD_DEFAULT_ON (in tree, not in the confirmed APK), B28_REMOTE_UMBRELLA, B29_GUARD_QUIET_STALL (in tree, not in the confirmed APK), B30_TRIP_LOG_KEEPER, B32_SURFACE_HOLD_AND_STEP_IN_PLACE, B33_NO_REWIND_WITHOUT_LOSS, B34_STABLE_PAD_SLOTS, B35_VOD_RETRY, B36_DIAG_KEEPER (36) | 10-21→11-02 | 1,012–3,927 | built / settled / not adopted | APPLIED | b-series |
| MEMORY_NORMALIZATION_2026-09-15 | 09-15 | 1,719 | normalized, checkpoint pending | SUPERSEDED (by MEMORY_MAINTENANCE_09-17) | memory |
| MEMORY_MAINTENANCE_2026-09-17, MEM-TOOLS_LINUX_TOOL_INVENTORY_REFRESH | 09-17/18 | 1,306 / 3,779 | applied | APPLIED | memory |
| ANDROID-FLAT_SOURCE_LAYOUT, BUDGET_EXECUTION_BUDGET_AND_TIERING, STREAMLINE_REPOSITORY_LAYOUT, LAN-R1_LOSS_STEPDOWN_RULE, LAN_R2_LOSS_RULE_RETHOUGHT (5) | 09-18→10-22 | 1,623–6,220 | recorded on install / built | APPLIED | misc |

### 1.7 `docs/memory/evidence/` (count and size only; records never move)

| What | Count | Size |
|---|---:|---:|
| Tracked files | 15,311 | 2.9 GB on disk (2,987,474,704 B) |
| On-disk files | 15,690 | — |

The 379 files on disk that are not tracked:
- the untracked `g_a10_2026-11-02/` (30 files, 4.4 MB, A's, in progress);
- ignored `__pycache__/` dirs, ignored copied logs and the ignored savestates.

| Part | Count | Notes |
|---|---:|---|
| Top-level dated records (`*.md`) | 357 | first record 09-10, latest 11-02 |
| Record directories | 212 | — |
| `reads/` | 1 file, 72 KB | `tools/diag_read.py` writes here (one HOME-1 read) |
| `snapshots/` | 3 files, 56 KB | — |
| `raw/` | absent on disk | ignored by `.gitignore` |
| `MEMORY_MAINTENANCE_REPORT_2026-09-17.md` | 922 B, 09-17 | the only maintenance report: the 09-17 cut (CURRENT 73,815 → 3,772 B). True as history, false as the present (CURRENT is now larger than before that cut). Keep |

### 1.8 Memory schema, scratch, leftovers, untracked

**The memory schema** (`memory_schema:` front matter):
- It is **defined nowhere**: not in MAINTENANCE.md, AGENTS.md, README.md or the templates, and `check_memory_health.py` ignores it.
- The de facto keys are `memory_schema`, `as_of`, optional `status` / `baseline_commit`.
- Two values coexist. **`2`** is in AGENTS.md, `memory/README.md`, COMMUNICATION.md, `history/README.md`, CODE_MAP.md and manifest.json (from the 09-17 ZIP era). **`1`** is in about 727 files (every record, handoff and patch since). Nothing says what differs.
- `as_of` is often stale (CURRENT.md says 10-29; TOOLS.md says 09-22).

**Root and leftover items:**

| Path | Date | Size | What / claims | Verdict | Action |
|---|---|---:|---|---|---|
| `_cowork_prompt.txt` | 11-02 | 2,940 | A's prompt: run G-A10 | **live** | keep (the user writes it) |
| `_cowork_prompt_b.txt` | 11-02 | 2,699 | B's prompt: run queue M | **live** | keep |
| `_cowork_prompt_c.txt` | untracked | 2,176 | this audit's prompt | **live** | keep; commit or archive with the apply pass |
| `_cowork_prompt_offsite.txt` | 10-24 | 3,937 | A's G4-S4 off-site prompt ("TEN lines", per-run `e3_flag.conf`) | done (historical) | archive → `archive/prompts/` |
| `STOP` (repo root) | 10-16 | 0 B | empty stop-file committed with the G8-S1 launch; today's keepers use their own `~/…/STOP`; no tool reads a repo-root STOP | done (leftover) | archive → `archive/scratch/` |
| `scripts/` (4 PowerShell files: setup_retroarch_portable, start_browser, start_camera, start_server) | 09-11 | 28 KB | Windows-era start scripts | **stale** | archive → `archive/windows-scripts/` (or a "Windows reference only" README; user's choice) |
| `logs/*_git_status.txt` | ignored | 154 files (of 198 in `logs/`, 352 MB) | per-task git status snapshots | done (local) | none (ignored; A may be writing `logs/`) |
| `docs_flat/` | ignored | 399 files, 2.6 MB | flat copy of `docs/` from 2026-09-20 | **duplicate**, stale | none in git; the user may delete it locally (this audit deletes nothing) |
| `archive/` (repo root) | ignored | 1,444 files, 62 MB | old patch backups / installers / staging / app backups (to 09-20) | done (local) | none |
| `_prel2b/` | ignored | 3 Kotlin files, 152 KB, 09-20 | pre-change source copies | done (local) | none |
| `Claude outputs/` | ignored | 1 file, 12 KB, 09-20 | an old D-BASE-R3 prompt | done (local) | none |

**Untracked right now** (`git status`):
- `_cowork_prompt_c.txt`, `handoffs/DOCS-AUDIT_2026-11-02_TASK.md` (this audit);
- `evidence/g_a10_2026-11-02/` and `patches/G-A10_STEP_IN_PLACE_ADOPTION.md` (A's);
- modified by A: `tools/e1_suite.py`, `e3_state.py`, `e1_remote.py`, `test_e1_remote.py`;
- modified by B: `handoffs/SESSION_B_STATUS.txt`;
- this file.

## 2. The plan (for approval; nothing applied)

### 2.1 Archive by `git mv` (never deletion) into `docs/memory/archive/<group>/`

**Prerequisite, found in this audit.** `.gitignore` line 26 is `archive/` with no leading slash. It ignores **every** directory named `archive`, including `docs/memory/archive/` (`git check-ignore` confirms it). So the first change of the apply pass is that line → `/archive/`, which still ignores only the repo-root `archive/`. Without it, the new index file cannot be added.

| Archive group | Files | What |
|---|---:|---|
| `archive/handoffs/<group>/` | **241** | groups: phase-c, d-base, phase-e, cl-b, g-track, bench, trip, ux-reads, queues, session-b-done, overnight, cowork. Every DONE, SUPERSEDED and HELD handoff in §1.5. **Stay in place:** CURRENT_HANDOFF.md, SESSION_B_STATUS.txt, G-A10 task, QUEUE_2026-11-02M, SESSION_B_DONE_2026-10-31L (until queue M's DONE exists), DOCS-AUDIT task (untracked; archive after the apply pass) |
| `archive/patches/<family>/` | **234** | families: d-series 70, d-base 22, phase-c 39, phase-e 24, cl-b 7, g-track 23, b-series 36, adb 5, memory 3, misc 5. **Stay in place:** PATCH_INDEX, PATCH_PROTOCOL, G-A8, G-A10 |
| `archive/docs/` | **5** | A4_AUDIO_RECOVERY, DEBUGGING_HARNESS, DEBUGGING_MEMORY, PROJECT_STATUS, REPOSITORY_AUDIT_2026-09-07; pointer lines in `docs/README.md` |
| `archive/memory/` | **72** | the 25 daily files (`daily/`); CHECKPOINT_PROPOSAL_2026-09-22, PHASE_C_CONTEXT, manifest.json; investigations: the 31 D5 + 5 C3 + ADB_STALE_CACHE, B1_DIAGNOSTICS_INVENTORY, D4_PS1_MULTITAP (39); repository/AUDIT_2026-09-10; roadmap/D5_MEDIA_SERVER_SUBSTEPS and roadmap/STATUS; templates/SESSION_LOG; chats/CHAT_INDEX |
| `archive/prompts/` | **1** | `_cowork_prompt_offsite.txt` |
| `archive/scratch/` | **1** | root `STOP` |
| `archive/windows-scripts/` | **4** | `scripts/*.ps1` |
| **Total moved** | **558** | — |

**New `docs/memory/archive/INDEX.md`:**
- one line per moved file: old path → new path, verdict, one-line reason;
- a section **"open items carried out"**: QUEUE_19N's G8-S6 and G5-S2-L, LINK-N1's nights not written up, G4_RUNBOOK §18's overlay-down check never scored;
- each of these also goes into KNOWN_ISSUES' open index.

**What a move breaks, and the choice it needs from the user.**
- 418 evidence records link to `handoffs/<file>`, and 289 link to `patches/<file>`. Only 47 of the 246 handoffs and 107 of the 237 patch notes are linked by no record.
- Records are never edited, so after a move those links resolve only through `archive/INDEX.md` (the file names are unchanged).
- Two options:
  - **(a) the move as planned**, plus a one-line `handoffs/README.md` and `patches/README.md`: "a file named in a record and not here is under `../archive/…`; see `archive/INDEX.md`". **Recommended.** It is the cleanup the user asked for, and the old names stay unique and greppable.
  - **(b) the cleanup without moving handoffs/ or patches/.** Status indexes in place (`handoffs/README.md` and the rewritten `PATCH_INDEX.md`), with the done files left where the records point. 475 fewer moves; every record link stays live.

### 2.2 Rewrite

**Rewrites (37 existing files):**

| Group | Files | What changes |
|---|---|---|
| `README.md` | 1 | What PrivyHub is today:<br>• the Linux hub (`privyhub-companion` user unit) streaming games / TV / VOD to the onn app;<br>• LAN play and away-from-home play over the overlay (session identity v2; line 13 makes remote sessions use the remote ladder);<br>• the 14 adopted lines as drop-ins, with the one off switch;<br>• the diagnostics (`privyhub-diag`, `diag_read`, `diag_check`, self-test, support bundle);<br>• how to run: the units, the tests in `tests/`, building the APK, the confirmed-APK rule;<br>• where the records are (`docs/memory/CURRENT.md`, `docs/memory/evidence/`, ROADMAP, KNOWN_ISSUES, `docs/RUNBOOK.md`);<br>• the ports and principles sections kept. Placeholders only. |
| READMEs | 3 | `docs/README.md` (map incl. REMOTE_TRUST / CAPABILITY_MODEL / WAN_ADAPTATION_RULES / RUNBOOK / archive); `docs/memory/README.md` (drop the ZIP invariant; list every file); `docs/memory/history/README.md` (list its 4 files + the new handoff history) |
| docs pages | 7 | ROADMAP.md (§0 / §1 refreshed; superseded sections get a one-line "superseded by … (date)" marker, nothing deleted); KNOWN_ISSUES.md (an "Open items" index on top; closed sections moved verbatim to `archive/docs/KNOWN_ISSUES_CLOSED_2026-11-02.md` with a pointer; the misfiled LAN-R1 chronology moved with them); REMOTE_TRUST.md (§4–§6, §8 marked adopted by G-A1; a G-A1 section; G-A10 kept as A writes it; §14's link-n1 window removed); CAPABILITY_MODEL.md (§7 rows); WAN_ADAPTATION_RULES.md (header and §3); DIAGNOSTICS.md (rewritten round the keeper); A8_INPUT_PROFILES.md (status block) |
| memory core | 8 | CURRENT.md (§2.4); MEMORY.md (Phase E / G durable facts in, closed-phase detail to `history/`, kept under the soft limit); AGENTS.md (git, not ZIPs; the companion as a unit; chronology in `evidence/`); TOOLS.md (one 14-row drop-in / off-switch table + the live tools; the rest to `archive/memory/TOOLS_HISTORY_2026-11-02.md`); MAINTENANCE.md (the schema section, §2.6); COMMUNICATION.md (the 2 stale lines; the user's working rules from COWORK_HANDOFF_2026-10-05 carried in); USER.md (1 line); handoffs/CURRENT_HANDOFF.md (to ~1 KB, history to `history/HANDOFF_SECTIONS_THROUGH_2026-10-16.md`) |
| memory sub-files | 17 | patches/PATCH_INDEX.md (every note, its status today, its archived path); investigations/ACTIVE.md (short index); decisions/DECISION_LOG.md (header); decisions/D083 (status line); architecture: ADAPTIVE_BITRATE, CONTROLLERS, DIAGNOSTICS, GAMES, NETWORK, REMOTE_ACCESS, STREAMING, STREAM_TELEMETRY, SYSTEM (a status-as-of header and pointer each; a body rewrite only for GAMES, NETWORK, REMOTE_ACCESS, STREAMING); repository/CODE_MAP, repository/DEBT; templates/MEMORY_UPDATE |
| `.gitignore` | 1 | line 26 → `/archive/` |

**New files (8):**
- `companion/README.md`, `tools/README.md`, `tests/README.md`, `PrivyHub/README.md` (each lists the files that exist: the entry point and feature modules; the live tools vs the ~70 historical `probe_*`; the per-feature test dirs; the Gradle project and the APK pin rule);
- `docs/RUNBOOK.md`;
- `docs/memory/archive/INDEX.md`;
- `docs/memory/archive/current/CURRENT_HISTORY_2026-11-02.md`;
- `docs/memory/history/HANDOFF_SECTIONS_THROUGH_2026-10-16.md`.

Plus the maintenance report `evidence/MEMORY_MAINTENANCE_REPORT_<apply date>.md` (§2.7).

### 2.3 Sections in KNOWN_ISSUES / ROADMAP marked superseded (found in §1.2)

**KNOWN_ISSUES closed or superseded:**
- CL-B13 / G-A6 shelved
- CL-B4 off-site fixed
- G3 ports addressed
- SNES capture fixed
- the runner EPG refresh fixed
- D-BASE 09-20 open faults
- the 09-16 Phase-D override
- C3.L0 / L2a / L2b / L3
- the decoder report mitigated
- the 09-22 / 09-23 open-after-close lists
- the 09-20 link-drop requirement (now owned)
- the 10-08 recovery pauses fixed
- the 10-18 wire rate addressed
- the remote row counter closed

**ROADMAP superseded:**
- §0 and §1
- the Phase D / E / G status lines
- G1 / G3 "NOT ADOPTED"
- G4-P1's per-run `--remote` flags
- the G4 / G8 line counts
- B27 "on by default"
- the three old APK pins
- "G-A8 … the thirteenth line"
- the trip keeper "runs to 11-01"
- "Immediate sequence"
- Gates 1–4
- D-072

### 2.4 CURRENT.md under its limit

**Today:** 97,688 B / 1,295 lines against the hard limit of 20 KiB / 400 lines (soft 10 KiB / 200). That is 4.77× in bytes and 3.2× in lines. About 12 KB is live and about 85 KB is history. All seven required headings are present, so only the size fails.

**Proposed structure, about 9.5 KB / about 170 lines.** Headings are kept exactly; the health check requires them.

| Heading | Contents | Est. size |
|---|---|---:|
| front matter | `memory_schema: 1`, `as_of`, the baseline commit; one line pointing to the history file | 0.3 KB |
| `## Active Objective` | Phase E active (E1 frozen, E2 measured, E3 / E4 closed); the G track; HOME-1 done; G-A10 the fourteenth | 0.6 KB |
| `## Current Work Item` | what is running (A / B / queue file names) | 0.6 KB |
| `## Verified State` | see the list below | 4.2 KB |
| `## Next Action` | one numbered list (the user's commit; B's queue M → HOME-2; then the G-A11..13 questions; later, the guard's return) | 1.0 KB |
| `Open, not blocking` (a sub-list under Next Action) | G8-S6, G5-S2-L, the reconnect read, the overlay-down LAN row, the handheld | 0.8 KB |
| `## Success Criteria` | the Phase E rules + the G adoption rule (pre-registered window, every row met, the user's word) | 0.5 KB |
| `## Do Not Reopen Without New Evidence` | the existing list condensed, plus G-A6 | 1.3 KB |
| `## Relevant References` | an index: G-A1..G-A10 records, CL-B14 / CL-B16, TRIP-R2, HOME-1, ROADMAP, KNOWN_ISSUES, REMOTE_TRUST, RUNBOOK, PATCH_INDEX, the history file | 1.2 KB |

**`## Verified State` contains:**
- **the 14-line table** as in §0, with each line's record;
- the one off-switch procedure;
- the client: `fcd924c2…` CONFIRMED, `554ccf61…` not, the properties empty, `identity_v2`;
- the units (companion + `privyhub-diag`; link-n1 and trip-log ended);
- B33 live and its off line;
- the built-not-adopted list (G-A6 shelved, G-A8 prepared, WAN adaptation, ENCODER_RC, the 1080p rung, PS1 look, the dormant E3 / E4 flags);
- the profile (cap 90 KB, cushion 12/17, redundancy 2/4);
- the baseline and the E4 reference, one line each;
- the ABSENT list.

**History.** Lines 23–71, 87–113, the detail of 120–137 and 144–222, and all of 257–1227 move verbatim, newest first, to `docs/memory/archive/current/CURRENT_HISTORY_2026-11-02.md`. Its header names the commit the text came from. Every block there already cites its evidence record.

**Alternative.** MAINTENANCE.md and `history/README.md` prefer git history over copying large files. The history file could instead be a ~6 KB index (block title, date, record, line range, the source commit). The user's choice; **the verbatim move is recommended**, because it is what the task asked and the file is not read by any tool.

**Done when:** `tools/check_memory_health.py` reports CURRENT.md OK (no SOFT / HARD), all headings present, and MEMORY.md and CURRENT_HANDOFF.md under their soft limits.

### 2.5 `docs/RUNBOOK.md` (from TRIP_RUNBOOK_2026-10-30, generalized; placeholders only)

| Section | Contents |
|---|---|
| **At home** | The onn on the home 5-GHz Wi-Fi, Hub host = `<home-value>`, start a game. What the 2.4-GHz notice means. |
| **Away (first time)** | Carried from G4_RUNBOOK_HOTSPOT §A: install and sign in to the overlay app on the onn, allow the VPN. |
| **Away (each time)** | HDMI and power; `<away-5ghz-network>`; overlay Connect; Hub host = `<hub-overlay-name>`, with the DNS fallback; start a game. The remote behaviour comes from the adopted REMOTE line alone; no per-run flags. Re-check the climb-time wording against today's ladder and step in place. |
| **Playing with people** | Trip D. Re-check against B34 / B38 once adopted. |
| **If it breaks** | Trip E: a drop auto-pauses and comes back (B33: a short drop resumes without a load); Home or app switch; past 30 s BACK and relaunch; the list won't load → the overlay and Hub host; type nothing into Code unless asked. |
| **Going home** | Trip F: Disconnect; Hub host back to `<home-value>`; home Wi-Fi. |
| **The one-line reads** | `tools/diag_check.py` (the six lines and what each means; replaces `trip_check.py`) and `tools/diag_read.py "<range>"` (e.g. `today`, `"last night"`; writes to `evidence/reads/`; replaces "read the trip"). The `privyhub-diag` keeper replaces the trip keeper (30-day retention, redacted). |

**Dropped:**
- the dates and the pack list;
- the line counts and APK hashes;
- the trip's "guard out" note;
- the trip keeper unit;
- every network or device name.

TRIP_RUNBOOK and G4_RUNBOOK_HOTSPOT are archived after RUNBOOK.md exists.

### 2.6 The memory schema

Add one short section to MAINTENANCE.md:
- `memory_schema: 1`; `as_of` required; `status` and `baseline_commit` optional;
- `as_of` is the date the content is true for.

Mark the six schema-2 files as legacy, normalizing them when they are rewritten anyway (AGENTS, `memory/README`, COMMUNICATION, `history/README`, CODE_MAP). `manifest.json` is archived. Records are not retrofitted.

### 2.7 What of QUEUE_2026-10-19B's memory maintenance still applies

| Item | Still applies? |
|---|---|
| **M-2: CURRENT.md under its limit with nothing lost** | **Yes, and worse** (then 477 lines, now 1,295). §2.4 does it. The queue's specific instructions ("the newest two blocks are CL-B7 and G8-S5", "the eight lines") are overtaken. What still applies: the headings unchanged, "Do Not Reopen" kept whole, nothing deleted. |
| **The same pass for MEMORY.md and CURRENT_HANDOFF.md** | **Yes, at the soft level:** MEMORY.md is 22 B under 35 KiB; CURRENT_HANDOFF is 1.71× its 8 KiB soft limit. In §2.2. |
| **Preserve the predecessors (copies + sha256) and write a report in the 09-17 shape** | **Yes, never done.** The apply pass writes `evidence/MEMORY_MAINTENANCE_REPORT_<apply date>.md`: before / after bytes and lines, the predecessor commit, the sha256 of each predecessor file, `check_memory_health` before and after. The predecessors live in git; the archive keeps the verbatim history. |
| **"Write nothing new into Next Action"** | Overtaken (that night only). |
| **G9-D1, the G9 checkpoint draft** | **Still wanted, but not part of this cleanup; propose it as its own later task.** Its content has moved on:<br>• the off-site sessions now include G4-S4 and the trip;<br>• the remote ladder / cap / start rung are adopted through line 13;<br>• G5-S2's rules were never smoked live (G5-S2-L never ran);<br>• the adverse-envelope silence question is open (G8-S6 never ran);<br>• reconnect over the overlay has candidate evidence (G-A4, G4-S4, the trip) but needs a read;<br>• the handheld is pending;<br>• Steam / external compute is deferred;<br>• "local operation with the overlay down" has no scored row;<br>• the clean checkpoint waits on the commits of A and B. |
| **ROADMAP §G9 status line, the logs** | Apply with G9-D1, not here. |

### 2.8 Risks

**1. Files other sessions write. Run the apply pass only when A and B are idle and their work is committed.**

| Writer | Files |
|---|---|
| **A (G-A10, running now)** | `docs/memory/CURRENT.md`, `docs/ROADMAP.md`, `docs/REMOTE_TRUST.md`, `docs/KNOWN_ISSUES.md`, `patches/G-A10_…`, `evidence/G_A10_…` + `evidence/g_a10_2026-11-02/`, `logs/g_a10_git_status.txt`, `tools/e1_suite.py`, `e3_state.py`, `e1_remote.py`, `test_e1_remote.py` |
| **B (queue M, waiting on A's record)** | `docs/KNOWN_ISSUES.md` (insertions), `docs/ROADMAP.md`, `handoffs/SESSION_B_STATUS.txt`, a new `handoffs/SESSION_B_DONE_2026-11-02M.md`, new `patches/B38_…`/`B39_…`/`B40_…`, new `evidence/B38..B40_…` + dirs, `logs/b38_..b40_git_status.txt`, `companion/`, `PrivyHub/`, `tests/` |
| **The user** | the `_cowork_prompt*.txt` files |

The overlaps are CURRENT.md, ROADMAP.md, KNOWN_ISSUES.md, REMOTE_TRUST.md and SESSION_B_STATUS.txt. Precondition: G-A10's record exists; queue M's DONE file exists; the user has committed both; `git status` shows only the prompt files.

**2. Code that reads doc paths.**

Read by a live tool. None of these are moved; CURRENT.md's headings are kept.

| Tool | Reads |
|---|---|
| `tools/check_memory_health.py` | `docs/memory/CURRENT.md` (limits + the seven required headings), `handoffs/CURRENT_HANDOFF.md`, `MEMORY.md` (limits), `AGENTS.md`, `MAINTENANCE.md` (required to exist) |
| `tools/capability_probe.py` | `MODEL_DOC = "docs/CAPABILITY_MODEL.md"` (named in its output) |
| `tools/diag_read.py` | `evidence/reads/`, `evidence/trip_2026-10-30`, `evidence/trip_r2_2026-10-31/scripts/` |
| `tools/trip_check.py`, `tools/trip_log_keeper.py` | `evidence/trip_2026-10-30` |

Read by **September probes only**, which no test runs:
- `tools/probe_b5_native_only_regression.py` reads `memory/manifest.json`, `CURRENT.md`, `MEMORY.md`, `handoffs/CURRENT_HANDOFF.md`, `investigations/ACTIVE.md`, `roadmap/STATUS.md`, and `docs/memory/memory/2026-09-11.md` (that path is already missing).
- `tools/probe_b6_clean_native_repository_audit.py` reads `docs/ROADMAP.md` (against a September baseline) and `memory/manifest.json`.
- Archiving `manifest.json` and `roadmap/STATUS.md` breaks a re-run of these two probes. They are already broken by today's content, so this is accepted. Alternative: leave those two files in place.

**Comment / docstring pointers to handoffs that would move.** No runtime effect; they resolve through the index. Do not edit them; they are code files.
- `tools/test_adaptive_bitrate_live.py` names C3-L4-L1, C3-L4-N1, C3-L4-N2 and C5-M5 task files.
- `tools/test_adaptive_bitrate_shadow.py` names C3-L4-S1.
- `tools/test_c5_m1_profile_selector.py` names C5-M2 and C5-M3.
- `tools/d7_regression.py` names D7-R1.

**Pointers that stay valid** (none of these are moved):
- the `companion/` docstrings to `architecture/ADAPTIVE_BITRATE.md`, `architecture/NATIVE_SOURCE_CONTRACT.md`, `investigations/LINK_DROP_RECOVERY_DESIGN.md`, `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, `docs/WAN_ADAPTATION_RULES.md` and `docs/KNOWN_ISSUES.md`;
- `MainActivity.kt` → `docs/REMOTE_TRUST.md`;
- `tools/e1_suite.py` → `architecture/E1_WORKLOAD_SUITE.md`;
- `tools/host_resource_sampler.py` → `docs/memory/TOOLS.md`;
- every code / test pointer into `evidence/`.

**No code reads `docs/memory/patches/`** (`grep "patches/"` over tools / tests / companion / scripts: 0 hits).

**3. Other risks.**
- **Links in the records:** §2.1 (418 + 289 linking records; option a or b).
- **`.gitignore` `archive/`:** §2.1. It must change first.
- **CURRENT.md's history move:** done verbatim with the source commit named. Nothing is lost; the "Do Not Reopen" list is kept whole.
- **`docs_flat/`** is an ignored, stale copy that can mislead a reader. Local only; the user decides.
- **`SESSION_B_DONE_2026-10-31L`** stays until queue M's DONE exists, because queue M's HOME-2 sketch builds on it.

### 2.9 Estimate

| Measure | Count |
|---|---|
| Files moved | **558** by `git mv` (241 handoffs, 234 patch notes, 5 docs pages, 72 memory files, 1 prompt, 1 STOP, 4 scripts). With option (b): **83** |
| Files rewritten | **37** existing |
| Files created | **8** new + 1 maintenance report |
| Files untouched | every record under `evidence/` (bar the one new report); every code file |

**The apply pass, one session, about 2½–3 h, unattended except for the user's final commit**, in five steps:
1. The precondition (A and B idle, the tree committed); `check_memory_health` before; `.gitignore`; the moves + `archive/INDEX.md` + the two pointer READMEs (~45 min, mostly the index).
2. CURRENT.md + its history file, CURRENT_HANDOFF, MEMORY.md; `check_memory_health` after (~45 min).
3. README.md, the four directory READMEs, `docs/README.md`, `docs/RUNBOOK.md` (~35 min).
4. ROADMAP / KNOWN_ISSUES / REMOTE_TRUST / CAPABILITY_MODEL / WAN_ADAPTATION_RULES / DIAGNOSTICS / A8 markers; TOOLS.md; PATCH_INDEX; the small memory files (~45 min).
5. The maintenance report, `git diff --stat`, `git status`; exit for the user's commit (~10 min).

No code, no tests, no stream, no restart, no adb.

## 3. Counts

| Measure | Count | Breakdown |
|---|---:|---|
| Files inventoried one by one | **645** | 6 READMEs + 13 `docs/` pages + 37 `docs/memory/` top-level + 94 in its subdirectories + 247 handoffs + 238 patch notes + 1 maintenance report + 4 prompt files + STOP + 4 scripts |
| Inventoried by count | — | the records (15,311 tracked files), `logs/*_git_status.txt` (154), and the ignored `docs_flat/`, `archive/`, `_prel2b/`, `Claude outputs/` |
| Stale | **48** | 3 READMEs + 10 `docs/` pages + 6 memory top-level + 17 memory sub-files + CURRENT_HANDOFF + 6 patch notes with wrong status lines + PATCH_INDEX + 4 Windows scripts |
| To archive | **558** | — |
| To rewrite | **37** | plus 8 new files |
