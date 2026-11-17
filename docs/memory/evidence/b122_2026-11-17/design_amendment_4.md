# B122 — design amendment 4 (hashed before the recorded real-picture runs; after the synthetic tests showed it)

**A searched alignment is adopted only when the moved picture is as close to a screen as that screen's own pictures
were.** The alignment search (~250 shifts and scales, when a picture matches no screen) found, for one synthetic fight
picture, a shift that brought it under the end screen's threshold (halfway to the nearest foreign picture) — read as
the end screen with its places unread (`unknown`, never a place). A version-3 spec keeps each screen's worst own
distance (`own_worst`); after a search the picture is taken as that screen only if its distance is at most `own_worst`
(the unmoved picture is held to the threshold as before). The game's window does not move, so on the window pictures the
search is rarely needed; it stays for a capture of another size.
