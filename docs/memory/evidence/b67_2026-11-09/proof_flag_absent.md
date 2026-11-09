# B67 — off = before (the client knobs), item by item

- **`debug.privyhub.player_prompt=0`:**
  - no `PlayerPrompt` object, so none of items 2-4 run;
  - the card's view is created only with the prompt, so item 1 is never shown;
  - the heartbeat's `promptJoinedQuery(null)` → "" as before (no prompt → no key, as today).
- **`debug.privyhub.start_gate_rearm=0`:** `StartGateRearm.onTimeout` returns false, so `failStabilization` runs at 15
  s as before.
- **An old host** (no `capable`, no `game.system`): `PortsSet.capable` null, so today's note and store; no card.
- **The build without B67 reproduces `9aa00ba2…` byte for byte** (`apk_sha256.txt`): the APK's only source change is
  B67's five files (`apk_source_diff.txt`).
- **JVM:** 240 / 240 in the working tree; **229 / 229** in the APK tree (queue T's 217 + B67's 12; B27 / B29's tests
  out).
