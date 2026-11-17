# B122 — design amendment 1 (hashed before the real-picture runs that are recorded; after the synthetic tests showed it)

1. **The place distance is the mean, not the median**, of |rank − reference| over the glyph mask (as B102's outcome
   distance). The synthetic seven-segment digits showed why: where most of a cell's glyph pixels look the same in two
   places (shared segments, the digit's dark box), the median is 0 for both and nothing separates them; the real
   digits hid it. The mean weighs every pixel that tells places apart. (A covered digit — the pointer over M2's "1" —
   still reads `unread` and never wrong: checked on the real pictures in the recorded run.)
2. **The start / end class is learnt with the place cells left out of its outcome mask.** The end screen's reference
   averages the training rows' digits, so a row never seen whole pulled a results picture past the end threshold
   (`unknown` before the places were read). Which places show must not decide whether it is the results screen: the
   learner runs today's `learn_arrays` a second time with every column's cell (± the read's search + 1 px, at 160 ×
   120) excluded from the outcome mask; the screen mask is the same in both passes (checked).
