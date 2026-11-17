# B122 — design amendment 2 (hashed before the recorded real-picture runs; after fold M1 of a first run showed it)

**Version 3 learns one screen per screen class** (supersedes amendment 1's item 2). Today's learner wants one screen
whose pixels are steady across the start and the end pictures together. T88's start and end share one layout; **T89's
do not** (the start is the character select, the end the results screen), and what stays steady across both is mostly
the window's black bands (right and bottom of the 960 × 720 window: game_area cuts bars on one axis only, and only
symmetric ones) — which every picture shares, fights included. A first run's fold M1 showed it: the screen threshold
0.004 against a best foreign 0.0052, and 7 fight pictures read as the screen (`unknown`, no place read).

Now, for each of `start` and `end` (version 3 only): **its own mask** = B102's steady-pixel mask on that class's
pictures **minus the pixels it shares with the `other` pictures** (where half or more of them rank within 0.1 of the
class's reference — the window's bands); its reference; **its threshold** halfway between its worst own distance and
the best foreign one (the `other` pictures and the other screen class). A read: the median rank distance to each
screen; the class is the screen under its threshold (both under: the smaller share of its threshold); none → `other`;
the alignment search, when nothing matched, moves the picture to the screen nearest by the mean. **The places read
against the end screen's mask** (ranks at 320 × 240). On all of T89's pictures (scratch look, numbers only): start —
own worst 0.010, foreign best 0.170; end — own worst 0.016, foreign best 0.181. No outcome mask or class references in
a version-3 spec. Version 2 (T88) unchanged.
