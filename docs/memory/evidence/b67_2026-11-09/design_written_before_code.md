# B67 — design, written before any B67 code (the next APK's client items)

Queue: `handoffs/QUEUE_2026-11-09X.md` §B67, plus **item 5 from B65's evidence** (disclosed). Built after B66 in
`/tmp/b_q16x_work` (the diff against the after-B66 snapshot). Client only. Default-on;
`debug.privyhub.player_prompt=0` removes items 1-4 together with the prompt (as before), and item 5 has its own
`debug.privyhub.start_gate_rearm=0`. The APK: queue T's composition (B5 … + B54) + B67; B27 / B29 out; built offline
with `--no-configuration-cache`, pinned in `PrivyHub/app/build/queue_x_built/`, **not installed**. `9aa00ba2…` stays
CONFIRMED.

## 0. Settled (read in the client sources)

- **The note:** `PlayerPrompt.join` says "No multitap on this system — <n> players" when a hold needs a port beyond
  `ports.players` and `!ports.multitapAvailable`. `PortsSet` parses `players` / `multitap` / `multitap_available` /
  `source`, but not B63's `capable`.
- **The stored count:** `join` stores the highest joined count per title (`PrefsPlayerChoiceStore`,
  `privyhub_players_joined`), and the launch sends it as `players_joined`. Nothing caps it, so T1 kept its 3.
- **B64's order:**
  - the sender's start calls `PlayerPrompt.beginStart`, but the map is cleared only in `onStartResponse`;
  - meanwhile the heartbeat's `players_joined` (`promptJoinedQuery()` = the live map's size) reports the last game's
    joins, which is HOME-7's 14-of-14 seq-1 row.
- **The start's game:** `native-stream-start`'s response carries `game_session.game` (`id`, `system`). The activity
  already reads the id for the prompt's key.
- **The overlays:** promptView / promptBadgeView, TextViews added to the root FrameLayout. Key events pass through
  `dispatchKeyEvent` (surface hold, Back, the prompt's join keys, then the gate).
- **The start gate** (B65's cause): a start whose 15-s `STABILIZATION_TIMEOUT_MS` passes calls `failStabilization`,
  which latches "Game stream isn't ready". Only a recovery re-arms.

## 1. Built

1. **The N64 layout card** (`N64LayoutCard.kt`, pure logic + one TextView):
   - shown once per onn, at the first start response whose `game.system` is `n64`, while the prompt is on;
   - the text: "A = ✕, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2";
   - **the glyphs only if the font draws them** (`Paint.hasGlyph` for ✕ □ △ ○); else "A = Cross, B = Square,
     C-buttons = right stick (also Triangle = C-up, Circle = C-right), Z = L2";
   - remembered in a private preference (`privyhub_n64_layout`, `shown`), written when shown;
   - **dismissed by the first key-down from any pad or the remote.** The key is not consumed: it goes on to the
     join / gate as today, so one hold both dismisses and joins;
   - centred over the picture.
2. **"This game supports 2 players":**
   - `PortsSet` gains `capable: Boolean?` (absent key → null);
   - `join`'s note reads "This game supports <n> players" when `capable == false`, else today's words.
3. **The stored count capped:**
   - `join` never stores above `ports.players` when `capable == false`;
   - `onStartResponse` with `capable == false` lowers a stored count above `ports.players` to it. **This is the onn's
     migration:** T1's 3 becomes 2 at its first start.
4. **B64's order:**
   - `beginStart` marks the prompt `awaitingStart`, and `onStartResponse` clears it;
   - while it holds, the heartbeat sends **no** `players_joined` (`joinedForHeartbeat()` = null). The relaunch query
     keeps `joined`;
   - so the host never sees the last game's count before the map is cleared.
5. **The start gate re-arms (B65):**
   - a *start* (not a recovery) whose 15-s window ends while the decoder has rendered new frames since the window
     began gets a new window, up to **3 re-arms (60 s in all)**; then it fails as today;
   - no new frames → it fails at 15 s, as today;
   - logic in `StartGateRearm.kt`; `debug.privyhub.start_gate_rearm=0` = today.

**Absent / off:**
- `player_prompt=0` → no `PlayerPrompt` object, so items 1-4 are unreachable and the build is the CONFIRMED one's
  behaviour;
- `start_gate_rearm=0` → `failStabilization` at 15 s as today;
- an old host (no `capable`, no `system`) → null / no card, today's words.

## 2. Tests (JVM, fake pads as `PlayerPromptTest`'s)

- **The card:**
  - `shouldShow` only for n64, enabled, not yet shown;
  - the glyph text when every glyph draws, else the letters (one missing → letters);
  - the store marks it once.
- **The note:** `capable=false` → "This game supports 2 players", no relaunch asked; `capable` null / true → today's
  words and relaunch rules.
- **The cap:** a join on 2 ports with `capable=false` stores ≤ 2; a stored 3 → 2 at `onStartResponse`; a capable
  title keeps 3.
- **The order:** after `beginStart` → `joinedForHeartbeat()` null even with an old map; after `onStartResponse` →
  0; after a join → 1.
- **The re-arm:**
  - new frames → re-arm, up to 3, then fail;
  - no new frames → fail;
  - disabled → fail;
  - a recovery → not this path.
- **`PortsSet.parse`** with and without `capable`.
- **Every existing JVM test green** (217 in queue T's APK copy, B27 / B29's out).
- **Mutations:** the capable branch of the note removed; the store cap removed; `awaitingStart` ignored; the re-arm
  limit removed.

## 3. The APK

- `/tmp/b_q16x_apk`: the after-B67 sources, with `b29.diff` / `b27.diff` reversed on the client paths.
- `./gradlew :app:assembleDebug --offline --rerun-tasks --no-configuration-cache`, pinned to
  `PrivyHub/app/build/queue_x_built/app-debug.apk` (+ sha256); `apksigner verify`.
- **Reproducibility:** the same tree without B67 rebuilds `9aa00ba2…` byte for byte (else disclosed). A second build
  of the new APK gives the same bytes.
- **Not installed.**
