# Why the hub never read the select screen (A, after the user's "You need to diagnose this first"; read only)

**Found: the live picture is uniformly ~13 grey levels darker than the pictures the spec was learnt from.** B102's
distances are absolute grey levels; the live select screen sat at screen distance **19.2-20.2** against a threshold of
**14.66**, so every read was `other` — the start, both end screens and the fights alike.

- **Not the framing:** the live window is 1920 × 1080 with the game centred at 1317 × 999; cut to the spec's aspect and
  reduced, it lines up with the learnt reference (the search kept the identity; a sweep of vertical fits found nothing
  better than 19.1 — `diag_fit.py`). The reduced pictures side by side match in place.
- **The tone** (`diag_tone.py`, `tone_results.txt`, on the first kept picture, the select screen at 00 – 00): live − the
  reference over the screen mask: mean −13.2, median −19.1; **a straight fit live ≈ 0.99 × reference − 12.7**; after
  taking out that gain and offset, the median difference is **7.9** (under the threshold). A training frame reads 0.2.
- **The replay** (`diag_replay.py`, `replay_results.txt`: every one of the 508 kept pictures through B102's own `Reader`
  in order, one a second):
  - **as kept:** 508 / 508 `other`.
  - **with +13 grey levels added:** 03:32:59-03:33:47Z `start` (49), the fight `other` (102), **03:35:30Z `end_P1`
    (117)** — the select screen's first picture after match 1 —, the relaunch `other` (16), `start` (24), the fight
    `other` (97), **03:39:57Z `end_P2` (103)**. **No fight, "wins" line or round intro read as the screen; no `unknown`;
    each end on the side the user named.** With K = 3 that is `ended` ~2 s (M1) and ~3 s (M2) after the select screen
    came back — 5 s and 3 s before the user's "back".
  - **the same result for +8, +10, +16 and +20** (`offset_sweep.txt`) — not a tuned number.
- **Where the darkening comes from — not settled.** The training frames were RetroArch's own `SCREENSHOT` from headless
  runs (H7-V1); the live reads grab the window on the hub's display. Something between the two (the screenshot path vs
  what is drawn, a shader or a colour setting in the live session) shifts the tone. Not checked further in this sitting.
- **The fix belongs to B (B's code not edited here):** read tone-independently (subtract each picture's own offset, or
  normalise each reduced picture before the distances) **and/or** learn the spec from pictures taken the same way the
  watcher reads them — this sitting's 508 kept pictures are exactly that (B's second note). Either is checked on these
  pictures before another sitting.
- **Also found:** after a missed end, `h7-start` refuses ("a mini game is already being watched") until the game stops —
  a second start cannot follow a match the hub missed without the user ending and relaunching.
