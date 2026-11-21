# SESSION B — done, 2026-11-21 BI (QUEUE_2026-11-21BI: B185 overtime; B186 a digit one save shows; B187 the ask to the user; B188 the task's words; B189 T90 from its seven kept saves; run ~00:20Z-03:00Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; T90's second record committed (`45e8ec97`).

**BG's exception: not used.** The picture source never ran. T90's pictures in the tool's folder were made from exactly
its seven kept states, so a scratch copy of that folder served label and learn. Register's library lookup asked the
companion for the title's entry (a read), the title taken from the binding copy in process.

**Rules kept:**
- No stream, no restart, no flag set, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the
  drive.
- Read only: the real T90 folder, the rules folder, the user's slots and in-game saves, the kept H7 folders.
- No bar in `BARS` lowered; `winner` / `places` and T88's / T89's rules unchanged; the sum check, the two readings and
  the last look stay.
- The app and the board's repo not touched.
- No title, team, id, path or picture in any record (the three checks).

**Another session worked in this tree meanwhile** (the app's handheld sources, G6 tests, records and task files,
`CURRENT.md`, `PATCH_INDEX.md`, `_cowork_prompt_g6.txt`). Not mine, not touched; `logs/b185_git_status.txt` lists both.
Mine: `tools/h7_endscreen.py`, `tools/party_add_game.py`, `tests/b178_score_kind/test_b178.py`,
`tests/b181_every_digit/test_b181.py`, `tests/b185_overtime/`, `docs/KNOWN_ISSUES.md`, `docs/ROADMAP.md`,
`handoffs/ADD_GAME_TASK.md`, `handoffs/SESSION_B_STATUS.txt`, this file, the B185 record + dir, the B185 patch.

Nothing adopted; nothing committed in either repo.

## B185 — BUILT

- A column only one save fills (overtime) is learnt from that save.
- Read by a reader learnt without that save, its filled cells are **"shown only here"**: never a misread, never read
  again, never sent to the user.
- **A save whose rows add up is never refused for which columns it fills.**

**What the hub does with an overtime final now:** it reads the finals only, at the FINAL column every screen shares —
as any other match. T90's overtime save through the spec learnt from all seven: `[35, 28]` within 2.0 s.

## B186 — BUILT (the numbers support it)

**T90's five end saves:**
- the same digit at most **0.401** apart across saves, **0.418** within one save (means 0.260 / 0.299);
- two different digits at least 0.656 apart;
- two pictures of one save identical.

**The rule:** a digit counts as learnt when two saves show it, or one save shows it at least twice and:
- each of its glyphs is read back by that save's other glyphs (never itself);
- the title's across-save spread is at most its within-save spread + 0.05.

**What still gets through:**
- a digit only one save shows, misread as another digit only that save shows, in every glyph, with the sums still
  adding up — only the last look guards it;
- a one-save digit the game draws differently in other matches — seen only through the title's other digits' spread.

## B187 — BUILT

**When the user is asked:** only when a save's two readings differ twice, or its sum fails twice. Never for a missing
sample. A read-back contradiction twice: the line says to take it back to Cowork, nothing to the user, no new match.

**What the user sees, through the session:** the match named plainly — who won, the final as read (at run time only,
never written down), "in overtime", when and where it was saved. Then the cells in doubt (e.g. "player 1's Q4"). Then:
"YOU, now: ask Cowork to show you the picture of that match; then reply with its scores."
- Cowork shows `logs/add_game_ask/<code>_<role>.png`: git-ignored (`.gitignore:2:logs/`), that one picture only, removed
  by close.
- The answer goes in the line score's form; a final alone is refused.

## B188 — DONE

`ADD_GAME_TASK.md`:
- the overtime rule;
- the ask line as B187;
- learn's every-digit words. learn's own line now ends "<n> digits are still short (…); if one is still short after
  that match, learn asks for one more", and the session says so — never that one match is enough.

The template unchanged (`aadccb04…`).

## B189 — T90 (scratch, no new save)

| stage | verdict |
| --- | --- |
| register (no `--collect`) | **PASS** (8 cells) |
| label, my five readings | FAIL on the last look only (22 of 23): end_P1_2's 7s and OT cells, end_P2_3's 4s and 6s "shown only here", every other number read back exactly, every sum met |
| the last look | `look=all` — I checked every tile |
| label | **PASS** (23 cells) |
| learn | **PASS** (27 cells) |

My readings, checked against both pictures of each save, are the record's, every cell. In learn:
- 7 was learnt from end_P1_2's nine glyphs, 6 and 4 from end_P2_3's three and two;
- the spread was 0.4009 across saves against 0.4183 within one;
- all five left-out cells were met.

**learn passes: stopped there.** Bench and solo are session A's with you.

**Tests:**
- B185 9 ×3; B181 7 ×2; B178 23 ×2; B157-B176 and the touched suites green;
- mutations 5 of 5 caught;
- disclosed: B178's / B181's assertions changed; two mutations of two changes each; the made-up font's seed-dependence
  (HEAD too), so B185's tests pin their seeds.

## What I would change (not done — the queue is the task)

1. **The ask's time.** T90's saves were collected before B187, so an ask about them says "kept at …", not "saved at …
   to slot n". From now on register keeps the slot and its time. A new `--collect` of the same slot would fill it in.
2. **The made-up font in B178 / B181's tests** has thresholds so tight that some noise seeds miss its 5s and 8s. Its
   noise could be pinned per picture, rather than relying on test order.
3. **A `sum` ask names every cell of the side**, blank ones included. It could name only the filled cells and the
   final, with "and any other cell that shows a number".

## Files

- **Code:** `tools/party_add_game.py`, `tools/h7_endscreen.py`.
- **Tests:** `tests/b185_overtime/` (new); `tests/b178_score_kind/`, `tests/b181_every_digit/` (disclosed).
- **Handoffs:** `ADD_GAME_TASK.md`, `SESSION_B_STATUS.txt` (one line), this file.
- **Record:** `evidence/B185_OVERTIME_ONE_SAVE_ASK_2026-11-21.md` + `b185_2026-11-21/`:
  - the design and its addendum, hashed; `t90_spread.txt`; `t90/`;
  - tests, mutations, the three checks, `scripts/`;
  - `b185.diff`, `apply_check.txt`, `check_ignore.txt`, `manifest.sha256`.
- **Patch:** `patches/B185_OVERTIME_ONE_SAVE_ASK.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line inserted), `docs/ROADMAP.md` (one paragraph).
- **Logs:** `logs/b185_git_status.txt`.

## T90 now

**It passes learn on its seven kept saves — no new match.** That pass was in a scratch: the real T90 folder still holds
the second run's label record. So session A runs:
- register (no `--collect`);
- label with the five line-score readings;
- the last look;
- learn — then bench and solo with you.

**The one line you type in session A:**

```
Read docs/memory/handoffs/ADD_GAME_PROMPT_TEMPLATE.txt, put T90 where it says ____, and follow it as my prompt.
```

At the questions, answer "who won is shown how" as before: the scores of each side on the final stats screen, the
winner the side with more.
