---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: e65e8f89604ce325e6e3e0537d0287070b8996c5
---

# Current Handoff

Continue PrivyHub from pushed commit `e65e8f89604ce325e6e3e0537d0287070b8996c5` on `main`. Treat
`L:\Projects\onn-stream-test` as authoritative between checkpoints.

Phase A emulator work is COMPLETE and checkpointed. The working tree was clean
after push.

## Runtime state to preserve

- native game capture/encode/transport/decode is stable;
- process-specific game audio is stable;
- PHI1 v1 and four ViGEm/XInput slots are runtime validated;
- Android P1-P4 assignment and RetroArch ports 1-4 are runtime validated;
- 1P/2P regressions passed;
- Crash Bash and CTR four-player PS1 Port-1 multitap passed;
- A8 named input profiles work for Players 1-4;
- Save/Load/Pause/Resume/End, cheats/mods and library behavior passed;
- wireless ADB recovery is runtime validated.

NES and Genesis had no local A9 fixtures. They are supported/configured but not
runtime validated and should be tested when real content is later added.

## Authoritative next roadmap

Use `docs/ROADMAP.md` v2.

Immediate sequence:

```text
Phase B1 existing-diagnostics inventory
        ↓
unified diagnostic schema + health snapshot
        ↓
GUI Diagnostics / Self-Test / sanitized bundle
        ↓
Sunshine/Moonlight dependency inventory
        ↓
legacy removal
        ↓
native-only regression
        ↓
clean-native checkpoint
```

Then Phase C adds explicit stream profiles and adaptive bitrate driven by
end-to-end path measurements, not GL-iNet WAN speed for local streaming.

VOD cover art/metadata is Phase D. Resource/Linux work is Phase E. OpenBIOS is a
non-blocking Phase F portability experiment and must preserve the current
compatibility BIOS path. Broader smart-home/client expansion is Phase G.

## Engineering rules

Never ask for IP addresses. Prefer durable diagnostics. Raw measurements beat
incorrect classifiers. Preserve stable subsystems. Fail closed. Update
`docs/memory/` with every meaningful result.
