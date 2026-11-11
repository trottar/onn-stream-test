---
memory_schema: 1
as_of: 2026-11-11
status: BUILT, NOT INSTALLED (session B, queue AH — H6's last quick fixes after HOME-12U) — the mapping list's changed rows yellow, as the picture's changed controls (the user's C56 requirement); HOME-12U's other two items settled without code: the hub applies every SNES code form its lists use (bench), and the GET active-cheats 400s were A's own watcher. In APK ca53df0d… (pinned, NOT installed). Switch: debug.privyhub.mapping_picture=0 = today's editor. Nothing committed. No title, serial, code name, path or identifier in this record
---

# B92 — the mapping list's changed rows yellow; HOME-12U's other items settled (2026-11-11)

**Why:** HOME-12U's items for B: (1) C56's "the buttons that are changed are yellow on the controller image but also in
the list they should be"; (2) C57's SNES cheat staged, loaded and reported on, its effect not seen; (3) `GET
active-cheats` answered 400 every second during a game. The user: "H6 only has a few quick fixes so let's do that then
into h7". **Baseline:** HEAD `af063475` (HOME-12U committed). **Design** hashed before code (`b92_2026-11-11/design.sha256`).

## Settled

- **(2) SNES code forms — the hub is sound (bench, B61's form):** a synthetic LoROM copies a ROM byte into work RAM every
  frame; one staged cheat per run, enabled, apply-at-load on, the hub's snes9x core. **Every form applies:** raw
  `addr:val` and `addr=val`, Pro Action Replay `aaaaaavv`, for a ROM byte (bank 00 and its mirror 80) and a RAM byte
  (`snes_forms_results.jsonl`, `scripts/snes_forms_probe.py`; no RetroArch left). The title's three lists are one region
  (an Action Replay list, a Game Genie list, a plain list); the pick was the Action Replay list's first code, a ROM
  patch; the plain list's name matches the game file exactly and holds RAM writes. So the miss is most likely that code
  on this copy of the game, not the hub. **No code.** Next TV check: a cheat from the matching list.
- **(3) `GET active-cheats`:** every such line in the journal comes from loopback; the onn's source has no such call;
  A's earlier watcher copies called it with GET (HOME-12U's copy was switched to POST at 05:47Z). **Not a defect.**

## Built (`b92.diff`, client only)

- `MappingPicture.changedRows(mapping, default)` — the rows (targets) whose control differs from the default (trimmed,
  case-folded; a blank control counts as changed); `CHANGED_COLOR` = the picture's accent (#FFC107).
- `MainActivity.kt` (the mapping editor's `refreshRows`): with the picture on, a changed row's text in that colour; a
  row needing attention stays red (red wins); unchanged rows the theme's colour.

## Switch

`debug.privyhub.mapping_picture=0` → no picture → `changedRows` empty → today's colours (the row code unchanged on that
path).

## Tests (`B92ChangedRowsTest.kt`, 5, JVM)

The default → none; the swap → `a`, `b`; the many-button remap → its 12 rows; blank / case / spaces; the list and the
picture agree (every yellow row's control, or its default's, is lit on the picture); the colour; the switch. 3 runs
(`tests_x3.txt`, with B91 / B89 / B86 green); full JVM 312 / 312 (`tests_jvm_work_full.txt`); mutations **4 / 4 caught**
(`tests_mutations_jvm.txt`). The editor's own colouring line is Android UI code (not run on the JVM): C58 at the TV.

## The APK (`apk_sha256.txt`, `apksigner.txt`, `apk_source_diff.txt`, `tests_jvm_apk_copy.txt`)

**`ca53df0dac787607af749492393b5f343e3df775cd4581d44342a1a81ecd590d`** (9,773,224 B, 945 entries) = queue AG's APK tree
(`218d9a82…`, CONFIRMED at HOME-12U) + B92; built offline twice → the same bytes; the baseline rebuilds `218d9a82…`
byte for byte; the signer `455bde4e…`; JVM 301 / 301 in the APK tree. Pinned at
`PrivyHub/app/build/queue_ah_built/app-debug.apk`, **NOT installed** (`218d9a82…` stays on the onn).

## Files

`b92_2026-11-11/`: start files, the design + hash, `b92.diff`, `diff_check.txt`, `snes_forms_results.jsonl`, the test and
APK files, `scripts/`, redact / title checks, `manifest.sha256`. Patch note: `patches/B92_MAPPING_LIST_CHANGED_ROWS.md`.
