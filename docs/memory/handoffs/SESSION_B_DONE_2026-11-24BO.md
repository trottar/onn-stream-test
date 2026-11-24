# SESSION B — done, 2026-11-24 BO (QUEUE_2026-11-24BO: B205 synthetic training for the score kind; read line 17:10:03Z, limit 18:10:03Z)

**Checked first:**
- only `privyhub-companion` and `privyhub-diag` active;
- `git status --short` empty; queue BN committed (`9dc4cc10`).

**Rules kept:**
- **T92's kept saves and your slots were not touched** (kept saves sha256 the same before and after; no register, no
  label).
- The picture source did not run. `status` and `native-stream-status` showed nothing running.
- No stream, no restart, no adb, no sudo, no nft; nothing fetched or installed; nothing written to the drive; nothing
  deleted by hand.
- The rules folder is unchanged. No bar lowered. No gate counts a synthetic glyph; the proof stays on real pictures.
- No title, id, team name or path in any record (four checks).
- Nothing adopted; nothing committed.

## B205 — BUILT

- **How it trains (B192's way, for digits):**
  - every labelled real glyph — finals, cells, stats — is scaled to each height its group is drawn at, pasted over
    T92's own pictures, from a fixed seed;
  - held-out glyphs are made first, then rounds of training glyphs;
  - **templates only:** every gate is measured on the real glyphs alone.
- **Counts and seconds** (the full spec):
  - 36 held out; 288 trained in 4 rounds; 16.86 s.
  - 25 of 36 held out read when the round cap stopped it (disclosed; training only).
  - learn takes 7 min 10 s, against 4 min 04 s.
- **Disclosed:** a digit's synthetic glyphs weigh at most as much as its real ones. Uncapped, the first trial made end_P2 fast
  but dropped the real margin to 0.0625 (bar 0.0796), so the cap was chosen after the hashed design.
- **Tests:** 3 tests, three runs OK. **The mutation that counts a synthetic glyph toward a cell: caught.** The
  every-time suites, once, all at once: eight of nine OK; **B185 had not finished at the limit** (no result).

## T92 — learn on its six kept saves: FAIL on the 5 only

- **left out end_P2: 2.0 s** (was 14.0; bar 2.0) — **met**.
- Every other cell is met — the margin 0.0882, separable, the replays, left out end_P1 and end_P2_2 — **except the two
  about 5:**
  - left out end_P1_2: its own 5s, not read;
  - every digit 0-5: 5 short.
- **Only end_P1_2 shows a 5,** once at each size (final and cell). Your new match is what learn needs.

## What I would change (not done)

1. **Raise the round cap, or stop on "held out read" no longer rising.** Four rounds left 11 of 36 held out unread.
   More rounds cost seconds per spec, and learn makes about a dozen specs.
2. **Train the left-out specs lighter** (fewer held out), so learn's time does not double.
3. **Settle the weight** — the cap at the real glyphs' count — on a second title before it becomes the rule.

## Files

- **Code:** `tools/h7_endscreen.py`.
- **Tests:** `tests/b205_synthetic_digits/` (new).
- **Handoffs:** `SESSION_B_STATUS.txt`, this file.
- **Record:** `evidence/B205_SYNTHETIC_DIGITS_2026-11-24.md` + `b205_2026-11-24/`, and T92's learn verdict
  (`add_game/T92/learn.*`).
- **Patch:** `patches/B205_SYNTHETIC_DIGITS.md`.
- **Docs:** `docs/KNOWN_ISSUES.md` (one line).
- **Logs:** `logs/b205_git_status.txt`.

## T92 now

Everything but a second 5 is learnt, and end_P2 now reads in time. **Your new match, with a 5 anywhere on its final
screen, is the last thing learn asks for.** Session A collects it from the slot you name, as the role of the player who
won (`end_P1_3` or `end_P2_3`), reads every number on it, and learns. If learn passes: bench, then solo with you.

**The one line you type in session A** (put your slot and the winner in it):

```
Read docs/memory/handoffs/ADD_GAME_TASK.md and continue T92 (score, two players, --max-score 5): my new match is in slot <2 or 3> and P<1 or 2> won — run register T92 … --max-score 5 --collect end_P<the winner>_3=<that slot>, then label T92 with every number on its final screen, the last look, and learn T92.
```
