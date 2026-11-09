---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 9e77af1e (B67 built after B66 in /tmp/b_q16x_work; its diff against the after-B66 snapshot; applied to the tree third, uncommitted)
---

# B67 — the client items: the N64 layout card, "This game supports 2 players", the stored count capped, B64's order, the start gate's re-arm (B65)

**Classification: BUILT**, client, default-on (`debug.privyhub.player_prompt=0` = none of items 1-4;
`debug.privyhub.start_gate_rearm=0` = item 5 off).
- **JVM:** **240 / 240** in the working tree, **229 / 229** in the APK tree (B27 / B29's out). 4 mutations caught
  (M2 replaced after a finding).
- **The APK `5f72af4b65ebf4bf434668f4ef26c52885be02fb8f5400d63e7b4e548bcdca32`**, pinned at
  `PrivyHub/app/build/queue_x_built/app-debug.apk`; **NOT installed**. `9aa00ba2…` stays CONFIRMED.

Design `b67_2026-11-09/design_written_before_code.md`, sha256 `3199b4b0…fd9fabc1`, hashed **00:45:54Z, before any
B67 code**. **Item 5 is an addition to the queue's four, from B65's evidence; disclosed in the design.**

## 1. Built (`b67_2026-11-09/b67.diff`, 5 client files)

1. **The N64 layout card** (`N64LayoutCard.kt` + one centred TextView):
   - at the first start response whose `game_session.game.system` is `n64`, once per onn (a private preference,
     written when shown), with the prompt on;
   - "A = ✕, B = □, C-buttons = right stick (also △ = C-up, ○ = C-right), Z = L2". The glyphs appear only if
     `Paint.hasGlyph` says the font draws all four; else "A = Cross, B = Square, … Triangle … Circle …";
   - dismissed by the first key-down. The key is not consumed, so one hold dismisses and joins.
2. **"This game supports <n> players"** when `ports_set.capable` is false (`PortsSet.capable`, absent → null), in
   place of "No multitap on this system — <n> players".
3. **The stored joined count capped:**
   - at a start response with `capable == false`, a stored count above `ports.players` is lowered to it. **This is
     the onn's migration: T1's 3 → 2 at its first start.**
   - **Disclosed:** the design also capped `join`'s store. That line was dead (a join never exceeds
     `ports.players`), M2 showed it, and it was removed.
4. **B64's order:** `beginStart` marks `awaitingStart` and `onStartResponse` clears it. Meanwhile the heartbeat sends
   no `players_joined` (`joinedForHeartbeat()`), so the last game's count is never reported.
5. **The start gate re-arms** (`StartGateRearm.kt`):
   - a start whose 15-s window ends while the decoder rendered new frames gets a new window, at most 3 (60 s), then
     fails as before;
   - no new frames → fails at 15 s;
   - a recovery is not affected.

## 2. Tests (`B67ClientTest`, 12 JVM tests; fake pads)

- **The card:** only n64, prompt on, not yet shown; the glyph text vs the letters (one missing glyph → letters).
- **The note:** an incapable title's third hold → "This game supports 2 players", no relaunch; an old host → today's
  words; a capable title → the relaunch asked.
- **The cap:** a stored 3 → 2 at the start; joins on an incapable title store ≤ 2; a capable / old host keeps 3.
- **The order:** after `beginStart` → null (the old map still 2); after the response → 0; after a join → 1.
- **The re-arm:** 3 re-arms then fail; no new frames → fail; stopped frames → fail; off → fail; the property parse.
- **`PortsSet.capable`.**
- **Mutations** (`tests_mutations.txt`): the note's capable branch; the store cap (M2 survived: the dead line; M2b the
  start-response cap → caught); `awaitingStart` ignored; the re-arm limit removed.

## 3. The APK

- **The tree:** the after-B67 sources with `b29.diff` / `b27.diff` reversed on the client paths (queue O / T's
  composition: B5 … + B54 + **B67**; B27 / B29 out).
- **The build:** `:app:assembleDebug --offline --rerun-tasks --no-configuration-cache`, **twice → the same bytes**
  `5f72af4b…cdca32` (9,706,184 B, 945 entries).
- **Reproducibility:** the baseline client with B29 / B27 reversed rebuilds **`9aa00ba2…` byte for byte**. The only
  source difference is B67's five files (`apk_source_diff.txt`).
- **`apksigner verify`:** Verifies (v2), the same signer certificate as `9aa00ba2…`'s (`apksigner.txt`, digests
  truncated).
- **Not installed.**

## 4. Files

`b67_2026-11-09/`:
- the start files; the design + hash;
- `b67.diff`, `applied_to_tree_at.txt`, `diff_check.txt`, `proof_flag_absent.md`;
- `tests_jvm.txt`, `tests_jvm_apk_copy.txt`, `tests_mutations.txt`, `tests_in_the_tree.txt` (host);
- `apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`;
- `redact_check` / `title_check` + `.txt`, `manifest.sha256`.

Patch note: `patches/B67_CLIENT_STRINGS.md`.

**One line for the user:**
- the first N64 game shows the button layout once;
- a two-player PS1 game now says "This game supports 2 players";
- the onn forgets the "3 players" it remembered for that game;
- a start no longer gives up while the picture is still coming.
