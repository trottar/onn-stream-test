---
memory_schema: 1
as_of: 2026-11-06
baseline_commit: 795d80d4 (the tree clean; B41 built in /tmp/b_q06n_b41, not applied by this worker)
---

# B41 — the player prompt: "Player N — press any button", up to the title's player count, on top of stable slots

**Classification: SETTLED + BUILT**, client behind `debug.privyhub.player_prompt=1` (opt-in), with a host key on
request.
- **Tests:**
  - JVM `PlayerPromptTest` 10 green, the whole JVM suite 205 / 205 (195 + 10), three runs;
  - host `tests/player_prompt` 11 green ×3;
  - every host suite as the queue-N baseline plus the new one;
  - 3 mutations caught (4 runs).
- **Proof:** absent = `0132b944…`'s behaviour, PROVEN (`proof_flag_absent.md`).
- NOT installed; NOT ADOPTED; no live run; nothing committed.

Design `b41_2026-11-06/design_written_before_code.md`, sha256 `5dbc2a6f…24d3`, hashed **17:55:46Z, before any B41
code**. Precondition (the coordinator's): only the companion and `privyhub-diag` active; the tree clean.

## 0. Settled: how the host knows a title's player count, and how the client learns it

- **No per-title "players" field exists.** The host has three reads:
  - the matched metadata's `max_players` (`games/metadata_importer.py:692`);
  - the library's `player_mode` (`single` / `multi`), manual or suggested from `max_players` (`_decorate_game`,
    `player_mode_source`);
  - for PS1, the per-title multitap (`EmulatorManager.ps1_multitap`, `port1` / `off`; D087 / D087R1): ports 1-4 with
    it, 1-2 without.
- **The rule, `companion/player_count.py`:**

  | the title | `players` | `players_source` |
  | --- | --- | --- |
  | `player_mode` `single` (manual or metadata) | 1 | `manual` / `metadata` |
  | PS1 with the multitap on, `max_players` 0 / ≥ 4 | 4 | `multitap` |
  | PS1 with the multitap on, `max_players` 3 | 3 | `multitap` |
  | `max_players` ≥ 2 without a multitap (any system) | min(2, max) | `metadata` |
  | unknown / no metadata | **2** | `default` |
  | any read fails | 2 | `default` |

  - A 4-player SNES title reads 2: this hub has no SNES multitap path.
- **The client learns it from the `native-stream-start` response:** `players` + `players_source`, **only when the start
  query carries `player_prompt=1`**.
  - Without the key the response is today's byte for byte.
  - The client parses the response with `JSONObject.opt*`, which ignores unknown keys; an old host gives no key, and
    the prompt assumes 2.

## 1. Built (`b41.diff`, 9 files)

**Client, `streaming/PlayerPrompt.kt` (new, pure Kotlin) on B34 / B38's `PadSlots`:**
- **`PlayerPromptFlag`:** only `1` turns it on; absent / empty / anything else = off = today.
- **The prompt implies stable slots:** the activity's slot object is created with `pad_slots=stable` **or**
  `player_prompt=1` (one line, an OR). `PadSlotsFlag`'s parse is untouched (B42 owns it). With B42's default the OR
  is a no-op.
- **At a start** (the sender's `start`): no pre-assignment by controller number. Pads already in the map (from earlier
  in this process) keep their slots as `claimed_by: stable`.
- **The claim:**
  - an unclaimed eligible pad (B38's test) pressing a face button (A / B / X / Y) or **Start** takes the lowest open
    slot below `players`, and the badge **"P*n*"** shows for 2 s;
  - open = no holder, or a holder that is not connected (a gone pad keeps its slot only until someone claims it);
  - **the press also reaches the game** on that slot: the prompt never blocks input;
  - an unclaimed pad's other keys and its sticks are dropped until it claims.
- **A pad already in the map** gets its badge on its first press of the session. Beyond the title's count (a third pad
  on a 2-player title) the press falls back to B34's lowest free slot, still badged.
- **The prompt line:** **"Player *n* — press any button"**, bottom-centre, while an open slot below `players` exists
  **and** a connected eligible pad has no slot. So it shows at the start and when a new pad appears; a solo player is
  not nagged once their pad holds P1.
- **A 1-player title** (`players` 1): no prompt and no claims; B34's assignment runs as built.
- **The release:**
  - a claimed pad holding **Select + Start for 2 s** (the 200-ms UI tick) frees its slot, the badge reads "**P*n*
    released**", and the prompt asks for that player again;
  - Select and Start still reach the game while held;
  - to swap, both release, then press in the new order.
- **Rows:** `&player_prompt=1&pad_claims=<slot:p|s,…>` on the start, `&pad_claims=…` on every heartbeat (beside B34's
  `pad_slots`), and the report's `players` and `pad_claims` (`[{slot, claimed_by}]`).
- **`PadSlots.kt`:** five additive methods (`slotOf`, `slotOfKey`, `holderOf`, `claim`, `release`).
- **`NativeControllerSender.kt`:** a `playerPrompt` field; the start, key and motion lookups take the prompt only when
  it is set.
- **`NativeStreamActivity.kt`:** the flag object, the two TextViews (prompt 18 sp, badge 22 sp, white on 80 % black,
  bottom-centre), the tick, the query keys, `setPlayers(json.optInt("players", 2))` after the start response, and the
  report keys. Every hunk is guarded.

**Host:**
- `companion/player_count.py` (new): the rule above; it never raises.
- `plugins/games.py` +9:
  - the start handler's `if self._first(query, "player_prompt") == "1":` with a lazy import and `payload.update`;
  - B34's two `SlotsLog` calls pass `claims=` only with `pad_claims`.
- `companion/pad_slots.py`: `parse_claims` / `with_claims`, and `SlotsLog.start` / `heartbeat` gain
  `claims=None`. Each slot entry of the `pad_slots` rows (the start row, the change row, the heartbeat row's list)
  carries **`claimed_by: prompt | stable`**. A malformed value adds nothing; a change of claims is a change row.

## 2. Tests (`tests_jvm.txt`, `tests_player_prompt_x3.txt`, `tests_mutations.txt`, `tests_regression_after.txt`)

**JVM, `PlayerPromptTest` (B38's fake onn: the virtual remote, pads A = controller 2, B = controller 3):**
- **B presses first → B is slot 0 with "P1"**; the prompt then reads "Player 2 — press any button"; A presses Start →
  slot 1, "P2"; the prompt is gone; the badge is gone after 2 s; claims `0:p,1:p`.
- **A 1-player title:** no prompt, B34's controller-number slots, claims `0:s,1:s`, no badge.
- **The release and re-claim:** Select + Start 2 s → "P1 released", the prompt "Player 1 — press any button"; both
  release, A presses first → A is P1 and B is P2.
- **A short hold** (1.4 s, a tick inside it) releases nothing.
- **A second start in the process:** both pads keep their slots as `stable`, no prompt, and a pad's badge shows on its
  first press.
- **A stick never claims;** a non-claim key from an unclaimed pad is dropped.
- **The virtual remote never claims,** and no prompt shows with no eligible pad.
- **A third pad** on a 2-player title gets P3 (B34's fallback) with its badge and no prompt.
- **The flag** is opt-in. **Absent:** `PadSlots` alone pre-assigns as built.

**Host, `tests/player_prompt`:**
- unknown → 2 `default`; `single` → 1; PS1 + multitap → 4 (3 for a 3-player title); without the multitap → 2; a
  4-player SNES title → 2; no game or a failing read → 2;
- without the key, or with `=0`, no `players`;
- claims on the start, heartbeat and change rows; a re-claim is a change row; no claims = B34's row; malformed adds
  nothing;
- a fresh process without the key imports neither module.

**Mutations (`/tmp/b_q06n_b41_scratch/`):**
- **M1**, `beginStart` pre-assigns again: 4 JVM fail;
- **M2**, the release threshold 0: 1 failed, then 2 after the short-hold test gained a tick inside the hold;
- **M3**, the host always 2: 2 host fail.

## 3. For HOME-3 (cell C6, the prompt)

- **Set:** `adb shell setprop debug.privyhub.player_prompt 1`; two pads paired; a 2-player PS1 title (multitap off).
- **Do:**
  1. start; the prompt reads **"Player 1 — press any button"**;
  2. pad B presses X → **"P1"** for 2 s; the prompt reads **"Player 2 — press any button"**;
  3. pad A presses X → **"P2"**; the prompt is gone;
  4. pad B holds Select + Start 2 s → **"P1 released"**, then "Player 1 — press any button"; pad B presses again →
     P1;
  5. a 1-player title → no prompt at all.
- **Pass:**
  - the start response carries `players` 2 (`players_source` per the title);
  - the recovery log's `"event": "pad_slots", "when": "start"` has the map with **`claimed_by`** on each claimed entry;
  - a `"when": "change"` row has slot 0 `claimed_by: prompt` for pad B, then slot 1 for pad A;
  - the heartbeat rows' `pad_slots` carry `claimed_by`; `updates_by_player` (B38) rises on the pressed pad's slot only;
  - the exit report has `players` and `pad_claims`;
  - **the game ran throughout** (no pause at the prompt; the claim press reached the game).
  - A 1-player title: the start response `players` 1, no prompt, claims `stable` only.
- **Off:** `adb shell setprop debug.privyhub.player_prompt ""` → no `players` in the response, no `pad_claims` /
  `claimed_by`, no prompt.

## 4. Files

- **`b41_2026-11-06/`:**
  - `started_at.txt`, `baseline_head.txt`, `git_status_at_start.txt`, `units_at_start.txt`;
  - `predecessors/` (5 files) + `predecessor_sha256.txt`, `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b41.diff` (`git apply --check` OK on the tree and on the APK base with B27 / B29 reversed);
  - `proof_flag_absent.py` / `.md` / `_output.txt`;
  - `tests_jvm.txt`, `tests_player_prompt_x3.txt`, `tests_mutations.txt`, `tests_regression_after.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `patches/B41_PLAYER_PROMPT.md`.
- **Left in /tmp:** `b_q06n_b41` (the copy), `b_q06n_b41_scratch/` (`m1`-`m3`, consoles), `b_q06n_b41_gradle*.txt`.
- **The rules held:**
  - no stream, no companion restart, no adb, no sudo, no nft; `privyhub-diag` and `~/privyhub_diag/` untouched;
  - nothing of A's touched; nothing fetched, deleted, adopted or committed;
  - the live tree's code not edited (the coordinator applies).
