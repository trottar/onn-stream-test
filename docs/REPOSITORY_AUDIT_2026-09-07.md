# Repository audit — 2026-09-07

## Scope

This audit was performed against the pushed stable checkpoint at commit:

`5ff6da02b9f6443ea189ba2fbf01452aa97ba98d`

and reconciled with the transport diagnostics added locally after that checkpoint.

The goal is not to refactor mature code before the next push. The goal is to identify source/reproducibility risks, record technical debt, and make the upcoming checkpoint understandable from a fresh clone.

## High-level tree

The pushed baseline is organized around:

- `PrivyHub/` — Android TV application;
- `companion/` — Windows companion/control/media/native-stream host code;
- `scripts/` — runtime/setup helpers;
- `tools/` — build/install and diagnostic helpers;
- generated/runtime directories excluded through `.gitignore`.

Before this documentation checkpoint there was no repository-level README or durable `docs/` tree.

## Stable source areas

### Android

The native-stream implementation is separated under:

`PrivyHub/app/src/main/java/com/safeiot/privyhub/streaming/`

Key responsibilities include:

- AVC decode;
- RTP/H.264 receive and FEC handling;
- native PCM audio receive/playback;
- controller sending;
- native stream Activity/session lifecycle.

The TV/catalog code remains larger and more mature; avoid combining structural UI refactors with network/streaming experiments without a separate reason.

### Companion native streaming

Tracked source includes:

- `companion/native_stream.py`;
- `companion/native_session_io.py`;
- `companion/native_fec_relay.py`;
- `companion/native_wgc_bridge.py`;
- `companion/native_host_telemetry.py`;
- `companion/process_audio/Program.cs` and its project file.

The production host currently assumes Windows for WGC/WASAPI/NVENC integration. That is expected for Prototype 1, not the final portable architecture.

## Findings

### A1 — Durable project documentation was missing

**Severity:** medium for maintainability.
**Action in this checkpoint:** addressed by adding the root README and `docs/` tree.

A long-running experimental project needs decisions and rejected experiments recorded outside chat/patch history.

### A2 — `companion/games/` application source unintentionally ignored

**Severity:** high for reproducibility.
**Status:** root cause identified; ignore rule corrected in this checkpoint.

`companion/plugins/games.py` imports:

- `games.emulator_manager`;
- `games.stream_manager`;
- `games.decoder_session_log`.

The companion is launched from `companion/privyhub_service.py`, so the `games` package resolves from `companion/games/`. A direct local import-resolution check confirmed:

- `games` -> `companion/games/__init__.py`;
- `games.emulator_manager` -> `companion/games/emulator_manager.py`;
- `games.stream_manager` -> `companion/games/stream_manager.py`;
- `games.decoder_session_log` -> `companion/games/decoder_session_log.py`.

These files existed locally but were hidden from Git because `.gitignore` contained the unanchored pattern `games/`. That pattern matched `companion/games/` as well as the intended repository-root game-content directory.

The correction is deliberately narrow:

- keep repository-root `/games/` ignored for ROMs and user-owned game content;
- replace only the broad unanchored `games/` rule with anchored `/games/`;
- allow `companion/games/` Python source to be tracked normally.

Before committing, verify that `companion/games/*.py` appears in the staged source set and that no repository-root `/games/` content is staged.

### A3 — diagnostic source must be distinguished from diagnostic output

**Severity:** medium.

The transport investigation created useful Android/Python/PowerShell diagnostic source that should survive the Linux transition. Raw captures and generated logs should not be committed.

Expected source includes forward, loopback, and reverse UDP probes. `logs/` and other generated diagnostic output remain ignored.

Before push, ensure diagnostic **source** is tracked while ETL/text/JSON run output remains ignored.

### A4 — Sunshine/Moonlight scaffolding remains

**Severity:** low now; medium for future clarity.

Tracked scripts still include Sunshine setup/firewall/UI helpers and a Moonlight installer. More importantly, the Games plugin still creates a legacy `StreamManager`, exposes legacy stream status/actions, and attempts `ensure_running()` around game launch.

Native streaming has superseded this path for the current experiment. Remove it in a dedicated cleanup change after the diagnostic checkpoint, not mixed into this documentation/push.

### A5 — ignored runtime dependencies reduce clean-machine reproducibility

**Severity:** expected prototype debt.

The native host depends on project-local runtime pieces such as compatible FFmpeg and the Windows Graphics Capture Python runtime under ignored runtime directories. RetroArch has a tracked bootstrap script, but the complete native streaming runtime/bootstrap path is not represented as a single clean-clone setup flow in the pushed baseline.

This is acceptable for the current experiment but should be resolved as part of Linux portability work.

### A6 — automated test/CI coverage is minimal

**Severity:** low for the current experiment, higher before productization.

The pushed tree contains Android scaffold tests but no substantial repository-level automated regression/CI suite. The new transport probes are valuable manual acceptance tools and should eventually inform automated network-independent tests where practical.

### A7 — production and diagnostics should remain separate

**Severity:** architectural guardrail.

The UDP investigation repeatedly benefited from standalone diagnostic Activities/scripts instead of modifying stable production receive/playback code. Preserve this separation. Experimental network flags, capture modes, and synthetic packet formats should not leak into production APIs unless independently justified.

## Pre-push checklist

Run `tools/audit_repo_checkpoint.ps1` and review:

- Git diff whitespace errors;
- staged diff whitespace errors;
- required source files that exist but are not tracked;
- `companion/games/` imported modules that are missing/untracked;
- generated runtime/log/data artifacts accidentally tracked;
- game-content candidates accidentally tracked;
- diagnostic source that exists but is not tracked;
- remaining Sunshine/Moonlight references.

Then inspect the actual staged file list before committing.

## Checkpoint policy

For the upcoming push:

- include source code required to reproduce current behavior;
- include diagnostic source worth preserving;
- include these docs;
- exclude runtime binaries, ROMs, captures, logs, backups, IP addresses, and local machine secrets;
- do not combine unrelated Sunshine cleanup or production transport redesign into the same checkpoint unless separately reviewed.
