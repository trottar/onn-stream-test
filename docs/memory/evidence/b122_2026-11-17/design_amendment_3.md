# B122 — design amendment 3 (hashed before the recorded real-picture runs; after the synthetic tests showed it)

Amendment 2's per-screen mask drops the pixels a screen shares with the `other` pictures. **It must also drop the
pixels it shares with the other screen class**: where the start and the end screens share a frame (the synthetic
pictures do, as T88's real ones do), the start screen's median distance to an end picture was 0 — the shared frame is
more than half of its mask — and the start was "not separable". Now a screen's mask drops a pixel when, **for either
foreign class** (`other`, the other screen), half or more of that class's pictures rank within 0.1 of the screen's
reference there. What is left is what tells this screen from each of the others; its threshold as before (halfway to
the nearest foreign picture).
