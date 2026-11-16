---
memory_schema: 1
as_of: 2026-11-16
baseline_commit: d61f9b56
---

# B104 — H7's end-screen reader made independent of tone (`tools/h7_endscreen.py`, spec version 2)

**Result:** `evidence/B104_H7_TONE_INDEPENDENT_READ_2026-11-16.md`.

- **Files:** `tools/h7_endscreen.py` (changed), `tests/b104_h7_tone/test_b104.py` (new);
  `evidence/b104_2026-11-16/b104.diff` (applies on `d61f9b56`).
- **Switch:** none — a tool, not the companion. The companion's watcher (B103, behind `PRIVYHUB_H7=1`) reads through
  it, so the new measure is what any later sitting uses. **A version-1 spec is refused** ("this end-screen spec was
  learnt with the old measure (absolute grey levels): learn it again"): every kept spec must be learnt again with
  this tool before a sitting.
- **New:** the game's area found inside a window by the tool (bars relative to the picture's darkest + 16, one axis,
  ≥ 5 %); ranks against the picture's own screen-mask tone (tolerance 2 % of its contrast); learning from several
  sources (`learn <runs> <labels> [<runs> <labels> …] <out>`), the outcome mask only from class pairs seen together in
  a source, frames unlike their label kept from setting thresholds, a minimum gap 0.05; `replay <run folder> <spec>
  [--k K] [--labels L]`.
- **Live:** not adopted; nothing on the hub changes until a spec is learnt and put in the rules folder (A's step).
- **Rollback:** `git apply -R b104.diff` (then version-2 specs are refused by the old tool: learn again with it).
