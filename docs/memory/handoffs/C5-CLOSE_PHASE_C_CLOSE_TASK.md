---
memory_schema: 1
as_of: 2026-10-05
status: TASK HANDOFF — C5-CLOSE: record the user's picture look of 2026-10-04/05 in their words; close C5 on the user's reading (1080p rung built and characterized, NOT ADOPTED — no visible gain on PS1 at the TV; the 4x source stays adopted; the remaster preset not adopted); the rung-window rule (skip reports while recovery is not PLAYING) built and replayed; the look helper's --attract path fixed from its own log; the C7 checkpoint updated and Phase C CLOSED; CURRENT.md to Phase E. No sessions beyond one fake-run and one short injection check; nothing else adopted; nothing committed
---

# C5-CLOSE — the user's look, C5 closed, Phase C closed

**The user's look, 2026-10-04/05, their words** (record verbatim in the
daily file and the decision): Look 1 (the adopted 4x source, 720p
stream) and Look 3 (the same at the 1080p rung) *"looked the best,
little difference between them"*; Look 2 (the `remaster` preset)
*"was the worst, a bit less smooth"*. Also: the helper's `--attract`
path left the TV app without a NOW PLAYING / RESUME; the user used the
plain route (helper without `--attract`, the game started from the TV)
and that worked.

**The user's decisions, 2026-10-05** ("Yep agreed"):

1. **The 1080p rung: NOT ADOPTED.** Built, validated mechanically
   (C5-M5/M5B: no client change for the size switch; 287-649 ms per
   switch; the entry at 415/450; 105 min at 1080p overnight), and
   characterized as buying nothing visible on PS1 at the TV while
   costing ~1.8× the wire rate, the switch gaps and the onn's 1080p
   decode jitter (~300 spikes ≥ 20 ms/min). It stays behind
   `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p`, off, kept for a source with
   1080p detail (PS2-class, Phase H).
2. **The `remaster` preset: NOT ADOPTED.** The levers stay available per
   session behind `PRIVYHUB_PS1_LOOK` for later cores.
3. **The 4x PS1 source stays adopted** (C5-M4A), unchanged.
4. **Phase C closes** on this reading.

Read first: `evidence/C5_M5B_RUNG_RULES_AND_LOOK_2026-10-03.md` (§4
S2b's paused-window finding, §5, §6), `C5_M5_1080P_RUNG_2026-10-03.md`,
`decisions/C5_1080P60_CAPABILITY_2026-09-28.md`, `C7_D8_CHECKPOINT_2026-09-30.md`,
`docs/ROADMAP.md` (C5, C7, "Checkpoint discipline", Phase E),
`tools/ps1_look.sh`, `companion/games/ps1_look.py`,
`logs/games/ps1_look_sessions.jsonl` and the helper's own log of the
user's three looks, `TOOLS.md`, `CURRENT.md`.

## 1. The rung-window rule (the user's call: yes)

While link-drop recovery holds the game paused (`desync_pause` →
`resumed` / `gave_up_saved`), the rung window **does not count those
reports** — a frozen picture streams clean and overstates the link
(S2b: 448 entry decisions refused by `game_not_paused` /
`recovery_playing` on a window filled during a pause). Built in
`adaptive_bitrate_live.py` behind the same flag; the window is reset
or the reports skipped, whichever the existing structure makes simplest,
documented. Tests: a paused stretch inside an otherwise clean window
neither counts nor qualifies; the window survives the pause once PLAYING
returns per the rule chosen; mutations caught. **Stop rule**: flag
absent → 0 differences against the closed controller on every series.
Replay S2b: the window must not qualify during its pause. One short
injection check (`INJECT=1`, flag on): the rule's status field visible;
teardown flags absent.

## 2. The helper's `--attract` path

From the helper's log and `ps1_look_sessions.jsonl` for the user's first
attempt: what `--attract` did (launch via the games plugin; the app
open/wake/RESUME step as `TOOLS.md`'s host-shell operation describes
it) and where it stopped — most likely the RESUME PLAYING tap or the
launcher's NOW PLAYING refresh. Fix it so `--attract` ends with the
stream PLAYING on the TV, or if the app genuinely needs a hand, make the
helper say exactly what to press on the TV and wait. Fake-run tests
updated; one real `--attract` dry pass to PLAYING and back with `4x`
(no flags beyond the look's), teardown verified. Note the plain route as
the documented default.

## 3. Close C5, update C7, close Phase C

- **`decisions/C5_1080P60_CAPABILITY_2026-09-28.md`**: append the close —
  the user's words, the four decisions, what exists (the rung, its
  flag, the look presets, the 4x source), what was learned (the limit on
  1080p is the onn's decode jitter and the frame-size tail on this hop;
  the link's loss is bursty and time-of-day; 40 MHz did not help), and
  what would reopen it (a 1080p-detail source, a different client).
- **`docs/ROADMAP.md`**: C5's status paragraph rewritten to the close;
  the C7 table's 1080p row ✓ with the records; the "adaptive bitrate"
  row unchanged (closed 2026-09-30); **Phase C: CLOSED 2026-10-05** at
  the section head with one sentence on what it delivered; the Phase E
  section marked as next, E1 first, not started.
- **`evidence/C7_D8_CHECKPOINT_2026-09-30.md`**: append 2026-10-05 — the
  C7 rows re-read after C5's close; "clean checkpoint/push" pending the
  user's commit of this run.
- `architecture/ADAPTIVE_BITRATE.md` (the rung's rule; the flag's
  status); `investigations/ACTIVE.md` (C5 and the look closed; the
  open-not-blocking list carried: max output gap, `host_link`, thermal,
  `CTRL-L1`, the slow-event ring, the mild step's ~120 s bound, the
  onn's 1080p decode jitter as a client item for later);
  `evidence/RUNTIME_VALIDATION.md`; `TOOLS.md` (the helper's fixed
  `--attract`; the rung flag's new rule); `handoffs/CURRENT_HANDOFF.md`;
  `patches/` + `PATCH_INDEX.md`; the daily file;
  `check_memory_health.py`; the redactor `--check`; `git status --short`
  and `git diff --stat` to `logs/c5_close_git_status.txt`.
- **`CURRENT.md` last** — Active Objective: **Phase C CLOSED
  2026-10-05**; Phase E next (E1, the workload suite frozen first) on the
  user's word. Next Action 1: the user's commit; 2: the user's go for
  Phase E; the open-not-blocking list. Verified State: live adaptive
  bitrate by default (ladder 5000-7000 at 720p), the 4x PS1 source, APK
  `de072762…835e`, the rung and look flags off.

Nothing else adopted; flags absent at the end; no `nft`, no real `sudo`,
the Opal read-only; no addresses, MACs, SSIDs, ADB endpoints, serials or
credentials anywhere. Nothing committed.
