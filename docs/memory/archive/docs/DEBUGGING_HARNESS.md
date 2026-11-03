# PrivyHub Debugging Harness

## Purpose

This harness reduces debugging to one entry command and one shareable output.

It reuses the diagnostic/logging infrastructure already present in PrivyHub instead of asking for a sequence of ad-hoc commands.

## Game/video reproduction

```powershell
.\tools\run_privyhub_debug.ps1 -Mode GameSmear
```

The script records a start timestamp, asks you to reproduce the problem in the normal PrivyHub app, waits for ENTER, runs the existing `collect_game_session_diagnostics.py`, selects the relevant fresh logs, redacts network-address-like data, and creates one ZIP.

At the end it prints one `SHARE_ME.zip` path. Share only that ZIP.

## Audio baseline history

```powershell
.\tools\run_privyhub_debug.ps1 -Mode AudioHistory
```

This mode answers one specific A4 question:

> When did RetroArch's pre-suppression Windows audio-session volume first become low, and does the immediately preceding retained helper log support an abnormal stop?

It scans every retained:

```text
logs\games\audio_timing\*.json
```

and extracts only safe historical fields such as:

- `local_output.original_volumes`
- `local_output.original_mutes`
- suppression factor / compensation
- `final`
- `restored`
- error text
- compensated peak
- packets sent / send errors

It reports one of:

- `LOW_BASELINE_TRANSITION_FOUND`
- `LOW_BASELINE_FROM_EARLIEST_RETAINED_LOG`
- `NO_LOW_BASELINE_FOUND`
- `INSUFFICIENT_HISTORY`

If a transition is found, it evaluates the immediately preceding retained log:

- `PRECEDING_ABNORMAL_STOP_SUPPORTED`
- `PRECEDING_HELPER_RESTORED_CLEANLY`
- `PRECEDING_STOP_STATE_INDETERMINATE`

The diagnostic deliberately does **not** assume that a 1% baseline was caused by PrivyHub.

The resulting `SHARE_ME.zip` contains:

- `SHARE_ME.txt`
- `audio_baseline_history.json`
- a few redacted audio-timing JSON files around the transition
- a SHA-256 manifest

Share only that ZIP.

## Other modes

```powershell
.\tools\run_privyhub_debug.ps1 -Mode CollectLatest
```

Packages the latest game-stream evidence immediately.

```powershell
.\tools\run_privyhub_debug.ps1 -Mode TransportHistory
```

Packages the latest privacy-safe summaries from the existing forward, reverse, and Android-loopback transport probes.

## Privacy

The harness does not ask for IP addresses.

Shareable bundles redact IPv4, IPv6-like, and MAC-like strings from text/JSON evidence.

Raw `pktmon_full.txt`, ETL captures, and raw packet CSVs are never part of a normal share bundle.

## Address architecture

Production PrivyHub does **not** depend on a permanently hard-coded onn address.

- Android persists the companion host.
- Android calls the companion over the control API.
- The companion obtains the onn/client address from the live HTTP request.
- The games/native-stream path receives that live client address and uses it for PC-to-onn native streaming.

Standalone UDP laboratory tools that accept an explicit address are diagnostic exceptions, not the production architecture.

## Debugging workflow

Use:

**one narrow hypothesis → one targeted diagnostic/probe → fresh log → inspect evidence → one coherent patch**

If a recurring diagnostic is needed, extend this harness so future runs remain one-command/one-bundle.
