---
memory_schema: 1
as_of: 2026-11-06
baseline_commit: 795d80d4
---

# B41 — the player prompt ("Player N — press any button")

**Result: SETTLED + BUILT; JVM 205 / 205 (10 new), host `tests/player_prompt` 11 green ×3, every suite as the
baseline, 3 mutations caught; absent = `0132b944…`'s behaviour PROVEN; no live run.** Record:
`evidence/B41_PLAYER_PROMPT_2026-11-06.md`. Diff: `evidence/b41_2026-11-06/b41.diff`. Nothing committed.

- **Settled:** no per-title players field exists. `player_count.py`'s rule:
  - `single` → 1;
  - else the ports (4 for PS1 with the multitap, else 2), capped by the metadata's `max_players` when ≥ 2;
  - unknown → 2.
- **Built (client, `debug.privyhub.player_prompt=1`, opt-in):**
  - `PlayerPrompt.kt` over the stable slots (the prompt implies them);
  - the first unclaimed real pad pressing a face button or Start claims the next player, with a 2-s "P*n*" badge;
    the prompt shows up to the title's count; none for 1 player; input never blocked;
  - Select + Start 2 s releases;
  - `pad_claims` on the start, heartbeat and report.
- **Built (host):**
  - `players` / `players_source` in the start response only for `player_prompt=1`;
  - `claimed_by` on each `pad_slots` row entry only with `pad_claims`.
- **Apply:** `git apply evidence/b41_2026-11-06/b41.diff` from the repo root (the coordinator merges it with B42 /
  B43). The host part acts only for a client sending the keys; the client part only with the property.
- **Rollback:** the property empty (today); or `git apply -R` the diff.
