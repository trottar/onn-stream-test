---
memory_schema: 1
as_of: 2026-11-17
status: BUILT (session B, queue AT) — the recognition window under a cheat setup, behind PRIVYHUB_H7=1. The rule: a watch begun with the load under a cheat setup settles recognised false after 15.0 s (RECOGNISE_SETUP_S); every other watch 8.0 s as today; true at the first start read as before. Margin: the slowest start seen under a setup 9.00 s (T88 in the board's order) — 6.0 s inside. Cost: a wrong screen under a setup says false 7.0 s later (15 s after the load instead of 8 s). Replay on H7-D1's four folders (T89 cut by B129): T88 early true at 9.0 s (false at 8.0 today), T88 late 4.0, T89 early 2.0, T89 late 1.2; never-the-start runs (synthetic, three of H7-V2's live fight stretches, H7-D1's T89 desktop reads) false at 15.0 s, never true; H7-C2's slot 1 true at 7.02 s under both. Tests 4 (3 runs), mutation 1 / 1. Nothing adopted; nothing committed
---

# B130 — the recognition window under a cheat setup

Queue: `handoffs/QUEUE_2026-11-17AT.md` §B130. The directory is `b130_2026-11-17/`: the design + `.sha256` (hashed
06:22:46Z, before any code), `replay_results.jsonl` (B129's `scripts/b129_b130_offline.py`, part `b130`) + its empty
`.err`, `b130.diff`, `tests_mutations.txt`, the checks, `manifest.sha256`. Patch: `patches/B130_H7_RECOGNISE_UNDER_SETUP.md`.
No title, id or path; no picture in git.

## The rule (`companion/h7_minigame.py`)

**`recognised` settles `false` after `RECOGNISE_SETUP_S` = 15.0 s when the watch began with the load under a cheat
setup** (the session's `cheat_session.profile_id` set — B127's `session_profile_id`); **8.0 s (`RECOGNISE_S`) for every
other watch, as today.** The settle rule itself unchanged: `true` at the first read naming the start class, `false` at
the first read (or picture failure) at or after the watch's window. The watch keeps its own window; the `watching`
row's `recognise_s` is that window (15.0 only under a setup; every other row as today); the party layer gives the mini
game up on the watch's own `false`, as before.

- **Margin:** the slowest start seen under a setup — **T88 in the board's order, 9.00 s** after the load (RetroArch's
  notices: the cheat applied, the pads configured, the state loaded) — **6.0 s inside 15.0 s (1.67 ×)**; H7-C2's 6.97 s
  8 s inside; T89 2.0 s (B129's cut).
- **Cost:** **a wrong screen under a setup now says `false` 15.0 s after the load instead of 8.0 s — 7.0 s later.** The
  party mini game is then given up and the board comes back after the end's hand-over (~1-3.5 s, B115): the users see
  the board again ~17-19 s after the title's launch instead of ~10-12 s — before anyone can have played a match, and
  inside the hub's 30-s start limit. Without a setup nothing changes.
- **Not chosen:** counting from the first read without notices (a notice detector — a new reader, more to prove); a
  longer window for every load (not needed without a setup; earlier answers would move).

## Proved — replay of the watcher's settle rule (`replay_results.jsonl`)

| run | reads | at 15.0 s (under a setup) | at 8.0 s (today) |
| --- | --- | --- | --- |
| H7-D1 T88 early (the board's order) | the watcher's own | **true at 9.0 s** | false at 8.0 s (H7-V5's miss) |
| H7-D1 T88 late | the watcher's own | **true at 4.0 s** | true at 4.0 s |
| H7-D1 T89 early | B129's cut | **true at 2.0 s** | true at 2.0 s |
| H7-D1 T89 late | B129's cut | **true at 1.2 s** | true at 1.2 s |
| synthetic, never the start (`other` / `unknown`) | — | **false at 15.0 s** | false at 8.0 s |
| H7-D1 T89 early as the watcher read it (the stale rectangle) | the watcher's own | false at 15.0 s | false at 8.0 s |
| H7-V2's live fights from 49.0 s / 281.0 s / 321.0 s (30 reads each, the T88 spec) | read here | **false at 15.03 / 15.02 / 15.02 s, never true** | false at ~8.0 s |
| H7-C2's T88 cheat slot 1 (from its load) | read here | true at 7.02 s | true at 7.02 s |

All four H7-D1 folders `true` under the new rule; every never-the-start run `false` at the new time and never `true`;
the answers that were `true` before are `true` at the same second.

**Tests** (`tests/b130_h7_recognise_setup/`, 4; B129's harness, B103's scripted pictures; the windows scaled —
`recognise_s` 0.8 s, the setup's 1.5 s, one read every 0.1 s): the constants 8.0 / 15.0; under a (fake) setup a picture
covered for 1.0 s then the start → **`true` at > 0.8 s** (the plain window would have said false); never the start →
**`false` at ≥ 1.5 s**, not before, never true; without a setup → `false` at ≥ 0.8 s and the covered start `false`, as
today; the `watching` rows' `recognise_s` 1.5 / 0.8. The flag absent → HEAD's answers (B129's flag test: the module is
not imported). **Mutation:** the setup's window = the plain one → tests 1 and 2 fail. **Runs:** 3 green
(`b131_2026-11-17/tests_x3.txt`).
