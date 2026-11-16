# B104 — design amendment 1 (written before any code; hashed before code)

**Ranks with a tolerance that scales with the picture's own contrast.** A plain mid-rank breaks every tie by picture
noise: a flat area of a screen (a panel, a background) has its pixels scattered at random across the whole band of
ranks it occupies, frame to frame — the screen mask would lose every flat area (on synthetic screens, nearly all of
it) and flat areas would add noise to every distance.

So the rank of a value v is **the share of the mask's pixels darker than v − τ, plus half the share within ±τ of v**,
with **τ = 2 % of the picture's own contrast** (its 2nd-98th percentile spread over the screen mask; at least ¼ grey
level). A gain scales the spread and τ alike and an offset moves neither, so the ranks stay unchanged by gain and
offset (up to the ¼-level quantisation and clipping) and by a mild curve nearly so; noise smaller than τ no longer
reorders a flat area. Two levels closer than τ count as one — the measure's resolution is 2 % of the picture's
contrast (stated with the limits). Still one histogram and one cumulative sum per read (O(n)).

Everything else in the design is unchanged. `"measure": "rank-against-screen-mask"` with `"tol": 0.02` in the spec.
