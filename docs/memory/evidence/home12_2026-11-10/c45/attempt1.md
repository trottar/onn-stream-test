# C45 attempt 1 (2026-11-10 20:35-20:43Z; the user's "Stage 3" 20:41Z+) — NOT VALID as run; asked once more

The user's line (verbatim): "All worked as expected" / "Stage 3". Before it, at the C44 question: "Yes" / "Yes" / "Yes".

Read on the hub (the companion's request log, labels only; the game logs; the watcher; the profile store):

| time (Z) | what | read |
| --- | --- | --- |
| 07:24-07:59 | a PS2 launch of another title (**T84**), ~13 h before the rest, before the profile existed | game log `PS2 input profile: default overrides=0` |
| 20:35:37 | profile "Swap" created (player 1 = the editor's default) and assigned to T82 | — |
| 20:36:59 | "Swap" edited: player 1's rows **X ← X, Y ← Y** (default X ← Y, Y ← X); A / B rows left at default | in the hub's terms: the **left and top** face buttons swapped, not the bottom and right |
| 20:37:26 | **T82** launched with "Swap" | game log `PS2 input profile: assigned overrides=1`; PCSX2 `[Pad1]` Cross / Circle **unchanged** (FaceSouth / FaceEast, read live); from the profile: Triangle / Square swapped (FaceWest / FaceNorth) |
| 20:39:33 | T82 set back to Default | — |
| 20:40:02 | **T83** assigned another of the user's profiles (not "Swap") | — |
| 20:40:11 | **T83** launched | game log `GC input profile: assigned overrides=1`; `GCPad1` A / X **swapped** (EAST / SOUTH, read live) — from that other profile |
| 20:41:18 / 20:42:55 / 20:43:03 | T83 Default → "Swap" → Default | no launch with "Swap" |

- The onn's mapping editor names the rows with the game's (Nintendo-style) letters and the choices with the pad's
  (Xbox-style) letters: the default reads A ← B, B ← A, X ← Y, Y ← X. A bottom / right swap is **A ← A, B ← B** — the
  letters do not say so (a client usability item, PS1's editor as before; for the record's KNOWN_ISSUES line).
- B77's translation itself read consistent: overrides=1 on both launches; the GameCube launch's A / X swap matches the
  profile it carried; the PS2 launch's bindings match "Swap" as saved (Triangle / Square).
- **Not valid against the pre-registered row:** T83 did not launch with "Swap", T82's Cross / Circle were not swapped,
  and T84's launch preceded the test. Per the validity rule, asked once more in plain words (the editor's rows spelled
  out), with "skip" offered to keep C45 not valid and go on.
- Now: no game carries "Swap" (T82 and T83 both Default).

## Resolved on the user's answers (~20:45Z; confirmed at the wrap-up: "The input profiles work well") — the steps done another way; C45 valid and MET

The user (verbatim, `user_lines.txt`): "I did two different input profiles / I swapped square and triangle for PS2 game
and used the Nintendo profile for [T83] / I deleted that profile because it's not useful / The swap" (the last
line ends there). The pre-registration's validity rule: **a step done another way is recorded and the readings stay
independent of it.** The user chose the swaps on purpose; the hub's readings match what they chose:

- **T82 (PS2), a Square / Triangle swap:** `PS2 input profile: assigned overrides=1`; Cross / Circle unchanged (live);
  **PCSX2's own `PCSX2.ini` written at that launch's exit carries `[Pad1]` Triangle = FaceWest, Square = FaceNorth**
  (stage 1: FaceNorth / FaceWest) — the swap PCSX2 ran with. The user: worked.
- **T83 (GameCube), the user's other profile (a bottom / right swap):** `GC input profile: assigned overrides=1`;
  `GCPad1` A / X = EAST / SOUTH, read live (stage 1: SOUTH / EAST). The user: worked.
- **The other PS2 game (T84):** `default overrides=0`. The user: worked as normal. Its launch was at 07:24Z, before the
  test profile existed (disclosed; a Default game's launch reads no profile either way).
- "Swap" deleted by the user at 20:43:30Z; T82 and T83 on Default. **No game carries a test profile.** PCSX2's
  `[Pad1]` keeps the Square / Triangle swap in its file until the next PS2 launch rewrites the pad sections (read
  again at C48's launch).
- The editor's letters (rows Nintendo-style, choices Xbox-style) stand as a usability item for KNOWN_ISSUES.

**C45: valid and MET → B77** (the profile reached PCSX2 and Dolphin, a swap of the user's choosing on each).
The "not valid" above was A's reading before the user's answer; kept as written.

- "No input profiles worked" (ambiguous, asked a / b) was answered at the wrap-up: **"The input profiles work well but it
  would be much easier to interpret changes if there were a little image of a controller with the current mappings
  showing"** → C45 MET stands. **A requirement for B:** the mapping editor shows a small controller picture with the
  current mapping (it would also answer the letters' confusion above).
