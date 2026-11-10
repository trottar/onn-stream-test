# B85 addendum 1 — heading rows (written and hashed before the fix)

**Found while testing B85 through the real handler:** the manager's `.cht` reader (`EmulatorManager._read_cheat_source`)
refuses the **whole file** when any entry has an empty code ("Cached cheat file is missing a cheat description or
payload"). RetroArch's lists use such entries as heading rows (a name, `cheatN_code = ""`). On the hub (counts only):
**8 of 18 N64 files and 1 of 13 SNES files** have at least one, so those titles' Cheats lists fail on the onn today
(the cheat tool cached them; the manager refuses them at listing).

**The fix (in B85, behind the same knob):** with `PRIVYHUB_CHEAT_CLEAN` on, an entry with a name and an empty code is
read as a heading (listed with its index, nothing to apply); the cleaner already hides it (`header`). An entry with no
name, or the knob `0` → today's refusal, byte for byte. Nothing else in the reader changes (the count, the sha, the
pre-enabled refusal). A launch that names a heading's index (only possible with `raw=1`) toggles an empty cheat —
RetroArch's own format, nothing written to the game.

**Test:** the fixture's heading row now goes through the real reader; the knob `0` keeps today's refusal on that file.
