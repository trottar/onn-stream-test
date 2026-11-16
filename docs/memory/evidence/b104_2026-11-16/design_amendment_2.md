# B104 — design amendment 2 (written after the first run of B102's unchanged tests on the new code; before any run
# on the real pictures)

**What the first run showed:** B102's `test_moved_pictures_read_with_the_search` failed on one case (6 px to the
right): the screen read as the screen at once (median rank distance 0.0009 — the median of a mostly flat screen hardly
moves when it shifts), its tally `unknown`; the search ran but could not beat 0.0009 on the median, so the found
alignment was not kept.

**The change — the search's objective only:** the search ranks its candidates by the **mean** |rank − the screen
reference| over the screen mask (it moves with every edge that shifts), and keeps the best candidate when its
**median** (the screen test, unchanged) is under the screen threshold and its mean is smaller than the mean at the
current alignment. When to search (not the screen, or the screen but `unknown`; at most once per 10 s), the grid and
the screen test are unchanged. The read's `distances.screen` stays the median.
