---
memory_schema: 1
as_of: 2026-09-10
---

# PS1 multitap On/Off source/library audit

Classification: `PS1_MULTITAP_FLAG_SOURCE_CONTEXT_CAPTURED_NO_CANDIDATES`.

The authoritative local audit found 80 PS1 catalog entries but zero entries with `max_players > 2`. CTR and Crash Bash were both absent from the candidate set despite runtime evidence that each supports four local players when a PlayStation Multitap is enabled.

Therefore the current metadata is not trustworthy enough to drive automatic multitap enablement or even a recommendation badge. The production decision is to expose a manual per-game `Multitap: On/Off` selector for PS1 titles.

Product rules:
- maximum supported local players remains four;
- `On` maps only to Beetle PSX HW Port 1 multitap;
- Port 2 is always forced disabled;
- existing Crash Bash `port1` storage remains compatible and displays as On;
- Off is stored explicitly after a user disables a previously enabled title so stale game-specific core options are rewritten with both multitap ports off;
- controller profile and multitap fields must coexist in the same per-game override record.

The metadata checker/recommendation layer is deferred until library metadata can reliably identify known four-player PS1 titles.
