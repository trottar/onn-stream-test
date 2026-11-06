# B41 — flag absent = the CONFIRMED build's behaviour (`0132b944…`), PROVEN

**By the lines** (`proof_flag_absent.py /tmp/b_q06n_base /tmp/b_q06n_b41` → `proof_flag_absent_output.txt`): 0
unstated removals, 0 unguarded additions.
- **`PadSlots.kt`:** a pure insertion of five methods. No B34 / B38 path calls them.
- **The sender:** three lines replaced (the start's `beginStart`, the key and motion lookups). Each becomes
  `if (prompt != null) … else <today's line>`, and `prompt` is the `playerPrompt` field, null unless the activity
  sets it.
- **The activity:**
  - the slot object's line ORs `PlayerPromptFlag.fromSystem()`, which is false without the property;
  - the start query appends `if (playerPrompt != null) … else ""`;
  - every other hunk is `playerPrompt?.` / `if (playerPrompt != null)`. `playerPrompt` is a lazy null without the
    property, so there is no view, no tick, no query key and no report key.
- **`games.py`:**
  - the `players` block runs only for `player_prompt == "1"`;
  - B34's two `SlotsLog` calls gain `claims=`, None without `pad_claims`.
- **`pad_slots.py`:** `claims` defaults to None, and `with_claims(slots, None)` returns `slots` itself.

**By behaviour** (tests):
- `test_without_the_key_the_response_is_todays`: no `players` / `players_source` without the key, or with `=0`.
- `test_without_claims_the_rows_are_b34s`: B34's row equal with `claims=None` and without the argument.
- `test_a_fresh_process_without_the_key_imports_nothing`: neither `player_count` nor `pad_slots` imported.
- JVM `theFlagIsOptIn`: `null` / `""` / `0` / `true` / `yes` → off; `fromSystem()` off on the JVM.
- JVM `absentThePadSlotsAloneAreB34AndB38sAsBuilt`: the sender's null-prompt path is `PadSlots` as built.
- **Every other suite unchanged:**
  - JVM 205 / 205 = 195 + B41's 10;
  - host: every suite as the queue-N baseline plus `tests/player_prompt` (`tests_regression_after.txt`);
  - B34's `tests/pad_slots` and B38's `tests/pad_slots_changes` unedited and green.
