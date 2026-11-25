# B219 — a once-seen symbol's threshold (queue BR): the decision before any code

Read line 2026-11-25T00:26:17Z; limit 01:11:17Z. Written after B219 item 1 (nothing changed) and before any code;
sha256 in `design.sha256`.

Item 1 took every valid test variant read "?" apart with today's reader rule (`why_not_read.py`, scratch, read only):

- T92's 6 (T92's real folder as it stands, scratch copy): 2 of 8 read "?". **Both failed on the threshold and on the
  margin** (distance 0.8572 / 0.8462 to their nearest template, 5; threshold 0.5223; margin 0.0097 / 0.0285 against
  0.1968).
- T90's 8 (BQ's answers): 4 of 8 read "?". **Three failed on the margin alone** (0.2190, 0.2033, 0.2116 against
  0.2345; distance under the threshold 0.5432); one on the threshold and the margin.
- Separable failed for none.

**The queue's item 2: "Only if they failed on the threshold (if any failed on the margin or on separable, change
nothing, report and go to B220 as the code stands)."** Five of the six failed on the margin. **So no code is
written:** no calibration stream, no widened threshold, no new tests, no mutations; B220 runs on the code as
committed (`4af23eb4`).

Reported beside it (never a gate): each once-seen symbol's verdict under the title's seed and four others with
today's code (`seeds.py`); and, for T92's two "?" 6s, what the valid cut held (`variant_parts.py`).
