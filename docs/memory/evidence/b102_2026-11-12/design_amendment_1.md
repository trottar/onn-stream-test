# B102 — design amendment 1 (written before the first test or evaluation run; hashed)

The design (hashed 15:42:47Z) searches the alignment only when a read is not the screen. The look before the design
showed a 2-4 px shift at 640 wide still reads as the screen (median distance ~3) while the outcome distance climbs to
21-47 — so a slightly-off picture would read `unknown` and never be searched. **Amended:** the search also runs when a
read is the screen but its class is `unknown` (same 10 s floor; a fresh `Reader` at once); its best alignment is
adopted only if it is under the screen threshold and closer than the current one, and the read is made again there.
Everything else as designed.
