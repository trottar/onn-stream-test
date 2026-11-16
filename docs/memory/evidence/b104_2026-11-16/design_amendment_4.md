# B104 — design amendment 4 (written after the second run on the real pictures, which I stopped; disclosed)

**What the second run showed** (`run2_before_amendment4_stopped.jsonl`, 41 lines, kept): after amendment 3 every
arrangement learnt as expected (1a, 1b, 3 every class separable, nothing read as a wrong class; 2a / 2b `unknown`
where their data cannot tell), and in arrangement 4a (learnt on the first halves of both sources, tone changes on the
held-out second halves) gains 0.8-1.2, gammas 0.8-1.25, offsets −30 to +10 and their pairs changed no reading — but:

1. **Offsets of +20 and +30 turned the window's black bars grey** (0 → 20 / 30, above the fixed `BAR_MAX` 16), so the
   bars were not cut and 111 held-out live screens read `unknown` (never another class, never a fight as the screen).
   In a real window the bars are the window's, drawn black whatever the game's tone, but the area rule should not
   rely on that: it is not tone-independent.
2. **Gamma 1.25 with −30: one held-out fight read as the screen (`unknown`)** — `other_read_as_screen` 1, which must be
   0. That spec's screen threshold was 0.149, set halfway past its worst own screen frame (0.120), one of the boundary
   pictures amendment 3 already keeps from setting a class's threshold.

**The changes:**

- **The bars, relative to the picture's own darkest value:** an edge column / row is a window's bar when its brightest
  pixel is at most **the picture's darkest pixel + 16** (was: at most 16). The rest of the rule (per axis the smaller
  side, one axis, ≥ 5 %, leaves at least half) unchanged. A screenshot's own dark border (22 when nothing is darker) is
  then counted, and still not cut: its smaller side is 2.5 % of the height.
- **A labelled frame unlike its label sets neither its class's threshold nor the screen's:** the screen's worst own is
  the worst screen distance among the screen-class frames that are nearest their own class's reference (as amendment 3
  for the classes). The `other` side stays strict (the least screen distance of any `other` frame).

Nothing else changes. Then the whole evaluation is run again from the start, once, on the tool's code.
