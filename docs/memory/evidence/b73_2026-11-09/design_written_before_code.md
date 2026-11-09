# B73 — the paused bar fits (design, written before any B73 code)

## What HOME-10 read

- With CHANGE DISC on a multi-disc set, the user saw **END "~95 % off the screen"** (still reachable by the D-pad).
- B71's bar is fixed widths in one `LinearLayout` row (`now_playing_bar`, `match_parent`):
  - padding 24 dp start, 20 dp end;
  - the title column (weight 1, 0 dp);
  - the status text 280 dp;
  - the preview 184 dp + 8 + 8 margins;
  - SAVE / LOAD / END 104 dp each and CHANGE DISC 150 dp, each with an 8-dp start margin.
- The fixed part is 44 + 280 + 200 + 494 = **1018 dp**. A 1080p Android TV UI is 1920 px at density 2.0 = **960 dp**.
  So END spans 894-998 dp, past the screen's 960 dp.
- "~95 % off" puts the TV's visible right edge at about **899 dp**: the onn's picture is cropped about 61 dp (≈ 6 %)
  on the right, more than Android TV's 48-dp (5 %) overscan guideline.
- The three-button bar (one disc) is 860 dp fixed, so END ends at 940 dp. The user has never reported it cut; it is
  left exactly as it is.

## The design

- **One pure object `PausedBar`** (`streaming/PausedBar.kt`), testable on the JVM. It holds:
  - `plan(fit, fourButtons, screenWidthDp)` → a `Plan`: each button's width, the start margin between buttons, the
    disc button's width and label, the status text's width, and the bar's end padding;
  - `layout(plan, screenWidthDp)` → each child's left / right edge in dp, as `LinearLayout` places them (the weight
    column takes what is left, never below 0; past the right edge = off screen).
- **Three buttons (one disc), or the property off:** today's numbers. SAVE / LOAD / END 104 dp, margin 8, the status
  text 280, end padding 20. With the property off and CHANGE DISC shown, it is B71's bar (CHANGE DISC 150 dp).
- **Four buttons (a multi-disc set), the property on (default):**
  - SAVE · LOAD · **DISC** · END, each **80 dp** with a **6-dp** margin (344 dp);
  - the bar's end padding **80 dp**, so END's right edge is at **880 dp**. That is inside the HOME-10 visible edge
    (≈ 899 dp) and inside the 48-dp guideline (912 dp);
  - the status text gets what is left after a 80-dp minimum for the title column. At 960 dp that is
    960 − 24 − 80 − 200 − 344 − 80 = **232 dp**, never more than 280 and never below 160;
  - **"DISC"**: the bar's status text already carries "Disc 2 of 4" under PAUSED (B71), so it is "DISC" with the disc
    line under it. There is no second row;
  - the start padding (24), the preview, the heights and the text sizes are unchanged.
- **Applying it** (`MainActivity.applyPausedBarPlan(four)`), called from `showGameSessionBannerUi` once the disc
  button's visibility is known:
  - the first time a four-button plan applies, the views' current values are captured (each button's width and
    margin, the disc button's text, the status text's width, the bar's end padding). The plan is then set;
  - whenever the bar is not four buttons (a one-disc banner, media now-playing, the bar hidden, the banner cleared),
    the captured values are put back.
  - **A one-disc session never reaches the setters**, so its views are today's, byte for byte. The same holds with
    the property off or CHANGE DISC off.
- **The property:** `debug.privyhub.paused_bar_fit`, default on; `0` / `off` = B71's bar. With
  `debug.privyhub.disc_change=0` there is no fourth button at all, which is the installed `5f72af4b…`'s bar.

## Tests (JVM, `B73PausedBarTest`)

1. **The onn's density.** At 960 dp (1920 px ÷ 2.0), the four-button plan:
   - every button lies within [48, 880] dp;
   - END's right edge ≤ 880 < 899 (HOME-10's edge) < 912 (the guideline);
   - the title column ≥ 80 dp.
2. **B71's bar reproduced:** END's right edge 998 dp > 960, so it is off screen, as HOME-10 saw.
3. **The labels measured** at the onn's density: 13 sp × 2.0 = 26 px, in DejaVu Sans Bold (wider than the onn's Roboto,
   so an upper bound; the logical sans-serif bold if the file is missing):
   - "SAVE", "LOAD", "DISC", "END" + 2 × 16 dp padding ≤ 80 dp;
   - "CHANGE DISC" + padding > 80 dp, which is why the label is shortened.
4. **Three buttons:** today's numbers exactly. The property off with four buttons: B71's numbers.
5. **Narrow screens:** the status text clamps at 160. END stays inside the screen down to 880 dp.
6. **The property's parse:** absent / "1" → on; "0" / "off" → off.

Mutations to be caught: the end padding back to 20; the label back to "CHANGE DISC"; the one-disc plan changed.

## Not in B73

The status text's own size and lines are as today. Its longest line ("Bitrate: … • FEC: …") may wrap at 232 dp on a
very long value; that is disclosed, not changed.
