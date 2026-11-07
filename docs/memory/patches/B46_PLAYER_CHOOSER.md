---
memory_schema: 1
as_of: 2026-11-07
baseline_commit: ea40a93f
---

# B46 — the player chooser at every start and every unpause (`player_prompt` on by default; `0` / `off` none)

**Result: SETTLED + BUILT; JVM 15 (B41's 10 replaced), 224 / 224 in the item's copy, 228 / 228 integrated; host 13 new;
3 mutations caught; `0` / `off` = `8ba4d996…`'s absent PROVEN; NOT ADOPTED (no host line: the host keys on the
client's `players_chosen`); no live run.** Record: `evidence/B46_PLAYER_CHOOSER_2026-11-07.md`. Nothing committed.

- **Built:** the user's "Player one press any button by default also", "every game … 1 player, 2 player, and multitap",
  HOME-3 C6's "every time a game is active or unpaused".
  - The client: the chooser `Players:  1  /  2  /  multitap (3-4)` → `Player N — press any button` up to the pick
    (capped by the session's ports); fresh presses only (C6's held-Start fix).
  - The host: `players_chosen` on the launch sets the PS1 port-1 multitap `.opt`, the `--device` ports, and SNES's
    port-2 multitap (257), at launch only. `ports_set` goes in the start response; `players_chosen` / `label` go on
    the `pad_slots` rows.
- **Files:**
  - `PlayerPrompt.kt` (rewritten), `PlayerChoiceStoreAndroid.kt` (new), `PadSlots.kt` (`clearAll`);
  - `NativeControllerSender.kt` (`repeatCount`), `NativeStreamActivity.kt`, `MainActivity.kt` (the launch key);
  - `PlayerPromptTest.kt`;
  - `companion/players_session.py` (new), `games/emulator_manager.py`, `plugins/games.py`, `pad_slots.py`,
    `games/native_stream_heartbeat.py`;
  - `tests/players_session/` (new).
- **Apply:** `git apply evidence/b46_2026-11-07/b46.diff` from the repo root (integrated by queue O's
  `queue_o_combined.diff`).
- **Rollback:**
  - on the onn, `setprop debug.privyhub.player_prompt 0` (today's absent);
  - or reverse `b46.diff`. A title a pick launched keeps a managed `.opt` until its next launch (the stale guard rewrites
    it off when no pick and no metadata value are given).
