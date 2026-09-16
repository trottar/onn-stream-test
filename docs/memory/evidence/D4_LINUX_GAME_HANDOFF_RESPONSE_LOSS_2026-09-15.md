# D4 Linux game handoff response-loss evidence — 2026-09-15

Status: **runtime evidence captured; fix runtime validation pending**

- PS1 launch and selected savestate load reached Linux.
- RetroArch accepted `LOAD_STATE_SLOT 0`; the selected state was loaded and follow-up status remained `PAUSED`.
- Android then reported a control transport failure, so the launch success handoff did not complete and the fail-closed paused state remained.
- Linux reports the legacy Windows host-window policy unsupported; that unsupported policy must not block native-stream auto-open.
- The unchanged Android app subsequently built successfully on the Linux host after the JDK and Android SDK were configured.

Development fix scope is Android only. Runtime/E2E validation remains required.
