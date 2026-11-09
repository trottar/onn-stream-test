---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: 94c05e4a
---

# B72 — the small readings: the N64 card's place, `fps (min)`, B66 on the dolphin kind, `gc_frames`' 20 class, SDL off the virtual pads, one slot-9 save per stall, `state_reply` rows (NOT adopted)

**Result:** `evidence/B72_SMALL_READINGS_2026-11-09.md`.

- **Apply:** `git apply evidence/b72_2026-11-09/b72.diff`, after B70 and B71. It is applied to the tree third,
  uncommitted.
- **Live:**
  - (a) with the APK `64d02f31…85dd`;
  - (b) / (c) / (d) are tools, run by hand;
  - (e) / (f) apply to GameCube sessions and (g) to every SAVE / LOAD, at the companion's next restart.
- **Off:**
  - (a) `debug.privyhub.n64_card_top=0`;
  - (e) `PRIVYHUB_GC_SDL_PADS=1`;
  - (g) `PRIVYHUB_STATE_REPLY_ROWS=0`;
  - (b) / (c) / (d) / (f) are scoped so that what they do not touch is today's (`evidence/b72_2026-11-09/proof_flag_absent.md`).
- **Rollback:** `git apply -R evidence/b72_2026-11-09/b72.diff` first (then 71, 70 if wanted).
