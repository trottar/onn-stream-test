---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: f302f8a8
---

# B108 — the board game (PrivyParty, Godot) as a launch the hub can stream, pause and end, behind `PRIVYHUB_PARTY=1`

**Result:** `evidence/B108_PARTY_LAUNCH_2026-11-16.md`.

- **Files:** `companion/party_session.py` (new), `companion/games/emulator_manager.py` (the `godot` launch kind: launch,
  pause / resume, stop, the seven state refusals, the controller-profile bypass, status fields — every hook behind
  `_party is not None`), `companion/plugins/games.py` (the system listed, its entry scanned, the stream start's
  `party_mode` row), `tests/b108_party_launch/test_b108.py` (new); `evidence/b108_2026-11-16/b108.diff` (applies on
  `f302f8a8`).
- **Switch:** `PRIVYHUB_PARTY=1` → a system "PrivyParty" with one game; the onn launches it as any game (no APK change);
  absent / `0` = today — proved byte for byte through the real HTTP routes against `f302f8a8`'s companion (sources,
  systems, a system's games, details, status with its counters masked, a PS1 launch and stop).
- **Needs:** a config file off the repo (`PRIVYHUB_PARTY_CONFIG`, else `$XDG_CONFIG_HOME/privyhub/party.json`):
  `{"godot", "project", "pictures", "renderer"}`; `xdotool` and `pactl` (both already used by the stream).
- **Live:** not adopted. PP-H2 sets the flag for its sitting only (a nineteenth line).
- **Rollback:** `git apply -R b108.diff`; `logs/games/party.jsonl` and `logs/games/*-party.log` are git-ignored.
