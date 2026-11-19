---
memory_schema: 1
as_of: 2026-11-19
status: TASK — session G6, docs only. Records the user's answers to G6-HM1a, re-checks the layout with L1 / L2 side by side, and pre-registers the placement test (which is also G6-HM3's re-run), hashed before the run. Nothing adopted; nothing committed.
---

# G6-HM1b — the answers to G6-HM1a, the shoulder re-check, and the placement test's pre-registration

**Docs only.** You read code and logs and never change them. Nothing under `PrivyHub/`, `companion/` or `tools/` is
edited: no build, no APK, no adb, no stream, no service restart, nothing fetched. Touch no other session's files.

## 1. The user's answers (2026-11-19), verbatim choices

Write them to `docs/memory/evidence/g6_hm1a_2026-11-19/user_answers_2026-11-19.md`. The amendment `2272705f…` is not
edited.

| Q | Answer |
|---|---|
| Q-B4 | **(a)**: in handheld mode only, the main app's catalog uses 2 columns when the screen is upright; the cards keep their size |
| Q-B5 | **(c)**: the grip and placement test first. (a), (b) and (d) are decided after its result |
| Q-L2 | **(b)**: L1 and L2 side by side on the edge at the same height, **L2 on the outside**; R1 and R2 mirror them, R2 on the outside |
| Q-L1 | **(a)**: the right stick above the face buttons, as in the amendment's §3 |
| Q-HM3 | **(a)**: re-run G6-HM3 once, as pre-registered, as the placement test's first minute (Cowork's reading of the user's "placement test first", which their pick says doubles as the re-run) |
| Q-PAD | not asked; Cowork's default **(b)**: the takeover is tested by its JVM tests at G6-HM4 and live at G6-S4. The user may change it |

## 2. The shoulder re-check (Q-L2 (b))

1. Copy `layout_check.py` to `layout_check_b.py` in the same folder.
2. Change only the four shoulder rectangles. L1 and L2 sit side by side at one height on each edge, with L2 on the
   outside. Keep each at least 1 cm by 2 cm, at least 1 cm from the screen edge's gesture strip (if the design names
   one), and clear of the D-pad's and the right stick's press areas.
3. Pick the height that brings both within about 4–5 cm of the thumb base, which is the amendment's assumed (side
   edge, y 1042).
4. Run it, and keep `layout_check_b_output.txt`.
5. Write `layout_addendum_b.md` with the four new rectangles, each control's distance from the thumb base, and the
   redrawn sketch.
6. Hash both new files (`layout_addendum_b.sha256`).

If no position meets every check, say so and give the closest alternatives. Do not loosen a check.

## 3. The placement test's pre-registration (written and hashed before the run)

Write `docs/memory/evidence/g6_place_2026-11-19/preregistration.md` and its sha256. The APK is still the candidate
`1d658a3f…` on the tablet, and nothing new is built.

**Before both minutes (the user):**
- the tablet on the **travel router's 5 GHz network** (its name redacted in this copy), not the home Wi-Fi;
- Settings → Location → Location services → **Wi-Fi scanning off** (and Bluetooth scanning off);
- the handheld screen on;
- the same PS2 game both times;
- no other session running, the onn not streaming, and outside 03:45–05:30Z.

**Minute P1, G6-HM3's re-run:**
- the tablet **flat on a table within about 1 m of the travel router**, screen up;
- the user's steps are G6-HM3's five steps exactly. No touching except to start, the drawn-button taps and End. Try
  Back once, so c7's Back part is tested too.
- Scored with G6-HM3's c1–c7, unchanged (pre-registration `bcbeff14…`). The verdict rule is G6-HM3's: met when c1–c6
  are met and c7 is met for End.
- G6-HM3's first run stays on record as NOT MET. P1 adds a second, scored run beside it.

**Minute P2, the grip:**
- the tablet **held upright in both hands at the user's usual seat**, at least 60 s, then End;
- no cells. These are recorded figures for the user's Q-B5 decision.

**Recorded for both minutes**, from `privyhub-diag`'s heartbeat link rows and the decoder report:
- the RSSI median and [min..max];
- the rows at −72 dBm or below;
- the tx median and the rows at 54 Mb/s or below;
- the band;
- `link_notice_shown`, with the reading that tripped it;
- the sequence resyncs (count, and their times into the session);
- the stall signals;
- `lost_packets` and `lost_packets_in_resyncs`;
- `max_output_gap_ms`.

**The ~48–50 s pattern.** G6-HM3's first run showed resyncs at about 6.9, 57.0, 104.8 and 154.0 s. Pre-register this
reading:
- **If** P1 and P2, with Wi-Fi scanning off, show no resyncs at a ~48–50 s spacing, the user's Q-B5 note says the
  pattern went with the setting. No cause is claimed beyond that.
- **If** the pattern is still there, the note says the setting did not remove it.

## Files and gates

- `docs/memory/handoffs/G6-HM1B_ANSWERS_SHOULDERS_PLACEMENT_TASK.md`: this task, copied in from
  `Claude outputs/G6_tablet/G6-HM1B_ANSWERS_SHOULDERS_PLACEMENT_TASK.md`.
- §1, §2 and §3's files as named. Update the plan's dated line and `CURRENT.md`'s G6 line: "the placement test
  pre-registered; the user's run next".
- `logs/g6_hm1b_git_status.txt`: this task's files only.

**Gates:** `tools/check_memory_health.py` passes; `git diff --check` is clean; the redaction check is clean; and
nothing of this task's is under `PrivyHub/`, `companion/` or `tools/`. No address, serial, token or pairing code;
device ids as 4 hex digits and "…"; no game title.

Your last reply begins "YOU, now: commit", then:
- the addendum's four shoulder positions and their distances, with the check result;
- the pre-registration's sha256;
- the user's steps for the two minutes, numbered, as plain as you can make them.
