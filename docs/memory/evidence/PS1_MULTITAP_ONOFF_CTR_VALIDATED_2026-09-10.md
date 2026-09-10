---
memory_schema: 1
as_of: 2026-09-10
---

# PS1 Multitap On/Off CTR runtime validation

Classification: `PS1_MULTITAP_ONOFF_CTR_CONFIRMED`.

CTR - Crash Team Racing is the second representative four-player PS1 title
validated after Crash Bash.

Measured:
- per-game override `ps1_multitap: port1`;
- game-specific Beetle PSX HW options file present;
- Port 1 multitap enabled;
- Port 2 multitap disabled;
- live XInput slots 1-4;
- Players 3/4 exposed in CTR;
- all four physical controllers independently normal;
- backend, Games API, and Android On/Off implementation markers present.

Status: **COMPLETE / runtime validated**.

The current metadata catalog remains unsuitable for automatic multitap
recommendations because the prior 80-game audit found zero >2-player candidates.
Manual per-game On/Off remains authoritative.
