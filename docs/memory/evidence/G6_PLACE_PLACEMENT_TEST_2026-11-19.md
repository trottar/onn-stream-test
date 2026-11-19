---
memory_schema: 1
as_of: 2026-11-19
status: RECORD — the grip and placement test. P1 (G6-HM3's re-run, the tablet flat near the travel router) MET by G6-HM3's rule; P2 (held upright at the usual seat) recorded, no cells. The ~48–50 s pattern present in P2 with Wi-Fi scanning off. Nothing adopted; nothing built.
---

# G6-PLACE — the grip and placement test, scored (2026-11-19)

**Pre-registration:** `g6_place_2026-11-19/preregistration.md`, sha256 `b47a8093…`, hashed 16:53:57Z. It checks OK
before scoring. G6-HM3's cells are from `g6_hm3_2026-11-19/preregistration.md` (`bcbeff14…`).

**APK:** the G6-HM3 candidate `1d658a3f…` on the tablet. Nothing new was built.

**The user's statements** (not in the logs): the travel router's 5 GHz network, with Wi-Fi scanning and Bluetooth
scanning off, the same PS2 game both times, and "Done".

**Matching the sessions (verified):** P1 and P2 are the first two tablet sessions after the hash. Both decoder reports
read `OMX.Exynos.avc.dec` and carry a `handheld` block.
- **P1:** recovery-log session 14, `session_started` 16:59:19.4Z → `session_end_bye` 17:04:14.8Z (295.4 s PLAYING).
  Decoder report `native_decoder_20261119_170414_871.json` (`ea413e83…`).
- **P2:** session 15, 17:04:53.5Z → 17:08:35.5Z (222.0 s PLAYING). Report `native_decoder_20261119_170835_621.json`
  (`b99cb025…`).
- **Before the hash, not counted:** session 13 (ps2), 16:46:58–16:47:51Z. It ended without a bye and left no decoder
  report. Its one `link_notice_shown` read −74 dBm at 15 Mb/s (16:47:25Z).

Figures as extracted: `g6_place_2026-11-19/figures_read.txt`. The link rows are `privyhub-diag`'s heartbeat copies
plus the live log, deduplicated by receipt time.

## P1 — G6-HM3's re-run (the tablet flat, screen up, within about 1 m of the travel router)

| Cell | Value | Bound | Verdict |
|---|---|---|---|
| c1 decode | `OMX.Exynos.avc.dec`, hardware true, low latency true | hardware, low latency | **MET** |
| c2 rate | `recent_fps` 58.88 | ≥ 58 | **MET** |
| c3 drops | decoder 5 / 17951 = 0.03 %; video 0 / 17951 = 0 % | each ≤ 1 % | **MET** |
| c4 latency | `max_rx_to_decode_ms` 56; `max_output_gap_ms` **64** | ≤ 100; ≤ 250 | **MET** |
| c5 the box | `portrait`, `1200x675`, `1200x1325` | as G6-HM3 | **MET** |
| c6 the inert pad | `touch_live` false, `touch_events` 119, `touch_writes` 0, `touch_slot` −1, `pointer_exempted_events` 124 | as G6-HM3 | **MET** |
| c7 Back and End | `back_swallowed` **5** (Back tried; the game kept running), `end_presses` 1, one bye after 295.4 s | ≥ 1; 1; one bye after ≥ 60 s | **MET** (Back and End) |

**Verdict by G6-HM3's rule: MET.** G6-HM3's first run (15:44Z) stays on record as NOT MET (c4 936 ms). This re-run
sits beside it.

## The recorded figures (both minutes)

| Figure | P1 (flat, ~1 m from the router) | P2 (held upright, usual seat) |
|---|---|---|
| play time (`duration_ms`) | 299.4 s | 226.0 s |
| heartbeat link rows | 148 | 112 |
| band | 5180 MHz | 5180 MHz |
| RSSI median [min..max] | **−32 dBm** [−33..−28] | **−70 dBm** [−73..−67] |
| rows at −72 dBm or below | 0 | 9 |
| tx median [min..max]; rows ≤ 54 Mb/s | **780 Mb/s** [390..866]; 0 | **97 Mb/s** [58..130]; 0 |
| `link_notice_shown` | none (the report's count 0) | none (the report's count 0). The 9 weak rows were never held 10 s |
| sequence resyncs (s into the session) | **0** | **6**: 47.5, 95.4, 96.4, 144.0, 144.7, 192.5 (jumps 425 / 128 / 357 / 154 / 180 / 504 packets) |
| stall signals sent / ends; recovery `client_stall` rows | 0 / 0; 0 | 93 / 20; 6 |
| `lost_packets` (of which in resyncs) | 0 (0) | 1915 (1748); `fec_unrecoverable_groups` 5 |
| `max_output_gap_ms` | 64 | 918 (at 47.4 s, with the first resync) |

## The ~48–50 s pattern (the pre-registered reading)

- **P1: absent.** No resync in 299.4 s (≥ 110 s).
- **P2: present.** Merged resyncs at 47.5, 95.4, 144.0 and 192.5 s, spaced **47.9, 48.5 and 48.6 s**, each within
  45–55 s.
- **The note for the user's Q-B5, as pre-registered:** "turning Wi-Fi scanning off did not remove the ~48–50 s
  pattern."

**Not claimed:** a cause.

**Seen and recorded:** the pattern appeared in the weaker-link minute (−70 dBm, 97 Mb/s) and not in the strong one
(−32 dBm, 780 Mb/s). The two minutes differ in distance **and** grip together, so the test does not separate them.
Both were on the travel router, while G6-HM3's first run and the earlier tablet sessions were on the home network.

## For the user's Q-B5 (G6-HM1a §5; still the user's choice: (a), (b), (d), or none)

- **(a) A tablet-specific threshold.**
  - Against it: at the usual seat (P2) the notice was not shown, yet the link still dropped out every ~48 s.
  - A lower threshold changes nothing here: the notice did not fire in either minute.
- **(b) The notice as a line in the button area.**
  - Neither minute showed the notice on the travel router.
  - Earlier it showed on the home network (G6-HM1a §5's table).
- **(d) A faster clear.**
  - Nothing to clear in either minute.
- **What the figures do support:** the tablet's link at the usual seat is the issue, not the notice.
  - At about 1 m from the router: no loss, no resync and a 64 ms worst gap.
  - At the seat: the 48-s drop-outs and 1915 lost packets.
  - A grip-only check (held upright, 1 m from the router), or the router moved closer to the seat, would separate
    grip from distance. That is a new test for the user to choose, not part of this pre-registration.

## The user's remark after the test (2026-11-19, verbatim)

> "It seems like that message went away after the location settings change"

**What the logs show beside it (verified; no cause claimed):**
- **The notice did not show in P1 or P2** (both after the hash, with Wi-Fi and Bluetooth scanning off by the user's
  statement).
- **It did show in session 13 (16:47:25Z), just before the test**, with reasons 6 (weak and slow). Its heartbeat rows
  read −67…−69 dBm and 87–130 Mb/s at first, then from 16:47:17Z −74…−77 dBm and 14–30 Mb/s, held past the 10-s rule.
  **The user (2026-11-19): "I changed it when you asked so before run 1/2".** The ask came with the test's steps, after the pre-registration's hash (16:53:57Z), so session 13 (16:47Z) ran **with scanning on**, and P1 / P2 with it off.
- **P2's readings mostly stayed just above the notice's line:** −70 median; 9 of 112 rows at −72 or below, never held
  10 s. P2 had no stretch like session 13's −74…−77 dBm and ≤ 30 Mb/s.
- **The network also changed** (the home network before; the travel router for P1 / P2), so the setting is not the
  only difference.
- **The ~48 s drop-outs stayed in P2 with scanning off.**

**So session 13 is the "scanning on" picture.** There, the notice showed when the link really fell (−74…−77 dBm, 14–30 Mb/s, held over 10 s). With scanning off (P1, P2), the link never fell that far and the notice never showed.

**Consistent with the remark, but not shown by it:** that the setting removed the notice. A same-place, same-network
pair with scanning on and then off would show it; that is a new test, only if the user wants it.

## Corrections and the user's answers (2026-11-19, after the test)

**P2's condition, corrected.** The user: **"It was laying down in both instances."** So P2 was the tablet **lying
down at the usual seat**, not held upright as pre-registered.
- **Effect on P2:** P2 had no cells, so no score changes. Its figures stand, but they describe placement only.
- **Effect on the comparison:** grip did not differ between the minutes, only the place (about 1 m from the travel
  router vs the usual seat).
- **The ~48 s pattern:** it went with the seat position, lying down, with scanning off. No cause is claimed.
- **Wording above:** where this record and the plan say "held upright", read "lying down at the usual seat".

**Q-B5, the weak-signal notice: "Nothing in the app".** PrivyHub is unchanged. Wi-Fi scanning and Bluetooth scanning
stay off on the tablet (an Android setting, part of the tablet's handheld setup).

**Q-L2b, the shoulders: not re-asked.** The user: "I already discussed this with chat? They did a whole ergonomic
research check."
- The user's choice stands: Q-L2 (b), side by side with L2 on the outside (`g6_hm1a_2026-11-19/user_answers_2026-11-19.md`).
- The geometry check found that this cannot sit within 4–5 cm of the thumb unless other controls move
  (`g6_hm1a_2026-11-19/layout_addendum_b.md`: B0 / B1 / B2).
- That result goes back to the chat that did the ergonomic research, to settle against its own findings before
  G6-HM4. It is not asked of the user again here.

