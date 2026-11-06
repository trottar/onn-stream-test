# B41 — the player prompt: design, written and hashed before any B41 code

Queue: `handoffs/QUEUE_2026-11-06N.md` §B41. The user, 2026-11-06: "I like your idea of the player 1/2/3/4 prompt
(depending on game)". Baseline 795d80d4; the CONFIRMED client `0132b944…` (B34 + B38 stable slots built, off).

## 0. Settled before the design (the code, read-only)

- **The host's per-title player count.** No "players" field exists. The nearest are:
  - the matched metadata's `max_players` (`games/metadata_importer.py:692`, from the metadata's own field or the
    database's `maxusers`);
  - the library's per-title `player_mode`, either manual (`single` / `multi`, the user's choice) or suggested from
    `max_players` (`plugins/games.py` `_decorate_game`, `player_mode` / `player_mode_source`);
  - for PS1, the per-title multitap (`EmulatorManager.ps1_multitap(game)`, `mode` `port1` / `off`, D087 / D087R1).
    A PS1 without the multitap reads ports 1-2 only, and with it ports 1-4 (FOUR_PLAYER_* / PS1_MULTITAP_*).
- **The rule (host, `companion/player_count.py`):**
  - `player_mode` `single` (manual or suggested; `max_players` 1) → **1**;
  - otherwise ports = **4** if the title is PS1 with the multitap `port1`, else **2**;
  - `players` = `min(ports, max_players)` when `max_players` ≥ 2, else `ports`.
  - So an unknown title is **2** (the queue's default), a 4-player PS1 title with the multitap on is 4, and a 4-player
    SNES title is 2 (no SNES multitap path on this hub).
  - Any read failure → 2 with `players_source: "default"`.
  - The source is in `players_source`: `manual` / `metadata` / `multitap` / `default`.
- **How the client learns it.** In the `native-stream-start` response, a new `players` key (and `players_source`),
  **only when the start query carries `player_prompt=1`**. A client without the prompt sends no such key, so the
  response is today's byte for byte. The client parses the response with `JSONObject.opt*`, which ignores unknown
  keys (`NativeStreamActivity` start thread). An old host gives no key, and the client assumes **2**.
- **The press path.** `dispatchKeyEvent` → `NativeControllerSender.handleKeyEvent` → `playerForDevice` → with stable
  slots `PadSlots.slotFor`. Keys with no mapped bit return false before any slot is taken. Start is `XUSB_START`,
  Select `XUSB_BACK`, the face buttons their bits. Motion goes `handleMotionEvent` → `playerForDevice`.
- **Stable slots today (B34 / B38):** `beginStart` gives every connected eligible pad without a slot the lowest free
  slot in controller-number order, so slots never depend on who presses first. The prompt replaces that pre-assignment
  with "first press claims", and keeps everything else of B34 / B38: the key, the eligibility test (B38's), one map per
  process, and a pad that leaves keeping its slot.

## 1. The design

**Flag:** `debug.privyhub.player_prompt=1` (CL-B7P's convention; read through `android.os.SystemProperties` by
reflection). Absent / empty / anything but `1` = off = today: no object, no view, no tick, no query key, no report
key, no new code path. Opt-in, not default (the queue: "the prompt stays opt-in until measured").

**Composition with `debug.privyhub.pad_slots`:** the prompt needs stable slots under it. With `player_prompt=1` the
activity's slot object is created even when `pad_slots` is not `stable`: the one changed line ORs the two flags. B42
makes stable the default in a parallel copy; with both, the OR is a no-op. `pad_slots`'s own parse is not touched (B42
owns it).

**`PlayerPrompt` (new, pure Kotlin, `streaming/PlayerPrompt.kt`; on top of `PadSlots` and `PadDevice`):**
- `players` (1-4): 2 until the start response; `setPlayers(n, connected)` after it.
  - `players ≤ 1` → inactive for the session: `PadSlots.beginStart` runs as B34 (no prompt, no claims), and every
    mapped slot reads `claimed_by: stable`.
- `beginStart(connected)` (the sender's start, instead of `PadSlots.beginStart`):
  - **no pre-assignment**;
  - the pads already in the map keep their slots, `claimed_by: stable`;
  - the per-session badge set and the release holds cleared.
- `slotForKey(device, keyCode, down, nowMs, connected)`:
  - inactive → `PadSlots.slotFor` (B34);
  - not eligible (B38's test) → null (today's stable behaviour for a remote);
  - **mapped** → its slot. On the pad's first press in this session, a badge "P*n*" for 2 s (the stable pad shows
    its badge). Select / Start downs and ups tracked for the release.
  - **unmapped:**
    - a face button (A / B / X / Y) or Start **down** claims the lowest open slot below `players`. Open = no holder,
      or a holder that is not connected (a gone pad's slot can be claimed; B34's "keeps its slot" holds while no one
      claims it). The badge reads "P*n*" and `claimed_by` `prompt`.
    - The press **also goes to the game** on the new slot: the prompt never blocks input, and the claim is that pad's
      first input.
    - With no open slot below `players` (a third pad on a 2-player title) the claim falls back to `PadSlots.slotFor`
      (the lowest free of four), still `claimed_by: prompt`, still badged. Nothing is refused that B34 would give.
    - Any other key from an unmapped pad → null (dropped, as an unclaimed pad has no player yet).
- `slotForMotion(device, connected)`: inactive → `PadSlots.slotFor`; else the mapped slot or null. A stick does not
  claim.
- **The release:** a mapped pad holding Select + Start ≥ 2,000 ms (`tick(nowMs)`, the activity's 200-ms UI tick)
  frees its slot.
  - The badge reads "P*n* released", the claim is gone, and the prompt shows "Player *n* — press any button" again.
  - Select and Start still reach the game while held (input never blocked); the release is a deliberate 2-s hold.
  - A re-press of a face button / Start by any unmapped pad then claims it. So two people swap by both releasing,
    then pressing in the new order.
- **`view(nowMs, connected)`** → `(prompt: String?, badge: String?)`:
  - the prompt **"Player *n* — press any button"** (n = the lowest open slot + 1) only while the prompt is active, an
    open slot below `players` exists, **and a connected eligible pad has no slot**. So it shows at the start, and
    again when a new pad appears; a solo player on a 2-player title is not nagged once their pad holds P1. Otherwise
    null.
  - the badge while its 2 s run.
- **Rows:**
  - `claimsString()` = `slot:p|s` for each claimed / kept slot (`p` = prompt, `s` = stable), sent as
    `&pad_claims=…` on the start and every heartbeat beside B34's `&pad_slots=…`, plus `&player_prompt=1` on the
    start;
  - in the report, `pad_claims` (`[{slot, claimed_by}]`) and `players`.
- `PadSlots` gains five additive methods (no existing body edited): `slotOf(device)`, `slotOfKey(key)`,
  `holderOf(slot)`, `claim(device, slot)` and `release(slot)`.

**The sender** (`NativeControllerSender`):
- `@Volatile var playerPrompt: PlayerPrompt? = null`;
- at start, `playerPrompt?.beginStart` replaces `padSlots?.beginStart` only when non-null;
- `handleKeyEvent` / `handleMotionEvent` use `slotForKey` / `slotForMotion` only when non-null; null = today's line.

**The activity:**
- the flag object (lazy);
- the OR in the slot object's line;
- two TextViews bottom-centre (the prompt line; the badge above it), added only with the prompt;
- a 200-ms UI tick (posted in `onCreate`, removed in `onDestroy`) calling `tick` + `view`;
- `&player_prompt=1&pad_claims=…` on the start query, `&pad_claims=…` on the heartbeat;
- after the start response, `setPlayers(json.optInt("players", 2), connected)`;
- the report's `pad_claims` / `players`.
- Every hunk is guarded by `playerPrompt?.` / `if (playerPrompt != null)`.

**The host:**
- `companion/player_count.py` (new): `for_start(plugin, game_status)` → `{"players": n, "players_source": src}` by §0's
  rule; never raises.
- `plugins/games.py`, in the start handler before `return payload`: `if self._first(query, "player_prompt") == "1":`
  a lazy import, then `payload.update(...)`.
- B34's two `SlotsLog` call sites pass `claims=` only when `pad_claims` is in the query.
- `companion/pad_slots.py`: `SlotsLog.start` / `heartbeat` gain `claims: str | None = None`. With a value, each slot
  entry gains `claimed_by` (`prompt` / `stable`) from it (a malformed value → no `claimed_by`, the row otherwise as
  B34). None → today's row byte for byte.

## 2. Absent = the CONFIRMED build's behaviour

- **Client, `player_prompt` absent:** `playerPrompt` is null. The sender's two new branches and the activity's hunks
  never run; the OR reduces to `PadSlotsFlag.fromSystem()`; no view; no tick; no query or report key.
- **Host:** a start without `player_prompt=1` → no import of `player_count`, the response unchanged. A heartbeat or
  start without `pad_claims` → `claims=None` → B34 / B38's rows unchanged.
- An old client never sends either key.

## 3. Tests

**JVM** (`PlayerPromptTest`, fake devices as B38's test):
1. Two pads, **B presses first** → B is slot 0 with the badge "P1"; the prompt then reads "Player 2 — press any
   button"; A presses → slot 1, "P2", and the prompt is gone (`players` 2).
2. A **1-player title** (`setPlayers(1)`) → no prompt ever, B34's controller-number assignment, claims `stable`.
3. **The release and re-claim:** P1 holds Select + Start 2 s → "P1 released", slot 0 open, the prompt "Player 1 —
   press any button"; the other pad's press claims slot 0.
4. **A pad already in the map** (a second start in the same process) keeps its slot, shows its badge on its first
   press, `claimed_by` `stable`; a stick move from an unclaimed pad claims nothing.
5. The **virtual remote** (B38's fake) never claims; a held release shorter than 2 s releases nothing.
6. **Absent:** the flag parse (`null` / `""` / `0` / `true` → off); the sender with `playerPrompt` null takes B34's
   path (a `PadSlots`-only run equals the B34 / B38 expectations).

**Host** (`tests/player_prompt/`):
- the start response with `player_prompt=1`: 2 for an unknown title, 1 for `single`, 4 for PS1 + multitap, 2 for a
  4-player title without it; without the key no `players` and no import;
- `SlotsLog` with `claims` → `claimed_by` per entry; without it → B34's row byte for byte; a malformed claims value
  → no `claimed_by`.

**Mutations:**
- `beginStart` pre-assigning again (B presses first would still be slot 1) → test 1 fails;
- the release threshold 0 → test 3 / 5 fail;
- `players` ignored on the host (always 2) → the host test fails.

## 4. Not in scope

- The prompt's default: it stays opt-in, a question for the user after HOME-3.
- B42's `pad_slots` parse.
- Any change to the stable map's key or eligibility.
