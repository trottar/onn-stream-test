# B92 — design, written before code (2026-11-11, after HOME-12U; the user: "H6 only has a few quick fixes so let's do that then into h7")

HOME-12U's three items for B, settled first:

1. **The list's yellow (C56, the user's requirement):** "the buttons that are changed are yellow on the controller image
   but also in the list they should be". **Built here (client).**
2. **The SNES cheat's effect (C57):** settled on the bench, no code: a synthetic LoROM that copies a ROM byte into work
   RAM every frame; one staged cheat per run, enabled, apply-at-load on; the hub's snes9x core. **Every code form the
   hub's SNES lists use is applied** — raw `addr:val`, raw `addr=val`, Pro Action Replay `aaaaaavv`, for a ROM byte
   (bank 00 and its mirror 80) and a RAM byte (`snes_forms_results.jsonl`; the file's own count 0 for both). The title's
   three lists are the same region; the picked code came from the Action Replay list; one list's tags equal the game
   file's exactly. So the hub path is sound and the miss is most likely that code on this copy of the game. **No code;**
   the next TV check picks a cheat from the list whose name matches the game file (RAM writes).
3. **`GET active-cheats` 400 every second:** the journal's polls all come from loopback; the onn's source has no such
   call; A's earlier watcher copies used GET (the HOME-12U copy was corrected to POST at 05:47Z). **Not a defect; no
   code.**

## The rule (item 1)

- With the picture on (`debug.privyhub.mapping_picture` absent), a row whose control differs from the profile's
  default (`working[target] != default[target]`, trimmed, case-folded) shows its text in **the picture's accent colour
  (#FFC107)**; unchanged rows keep the theme's colour; **a row needing attention stays red** (red wins).
- One pure function `MappingPicture.changedRows(mapping, default): Set<String>` (targets), the editor colours from it.
- The property `0` → today's editor (no picture → no colouring change; the row code unchanged on that path).

## Tests (JVM)

`changedRows` for the default (empty), the bottom / right swap (`a`, `b`), the many-button remap (its 12 targets), a
blank source counted as changed, case / spaces ignored; the picture's highlighted controls and the yellow rows agree
(every changed row's source or its default's source is a highlighted control); the switch. Then the APK (queue AG's +
B92), pinned, NOT installed; a short TV check sketched for A (the list's yellow; an SNES cheat from the matching list).
