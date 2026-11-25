---
memory_schema: 1
as_of: 2026-11-25
baseline_commit: c7750afc (this repo)
---

# B224 — a template's synthetic glyph is valid as a test variant is (queue BU)

**Result:** `evidence/B224_TEMPLATE_VALIDITY_2026-11-25.md`.

- **Files:**
  - `tools/party_steps.py`:
    - `paste_cut`, new: one draw of the paste and its three validity conditions. It is `test_variants`' code, moved
      out; `test_variants` calls it, unchanged in effect.
    - `synthetic_glyphs`, the template stream, keeps only valid draws: it redraws from the same stream up to
      `VARIANT_DRAWS`, `SYN_PER_GLYPH` needed, fewer recorded.
    - `score_gates` records made / thrown away by symbol in train's page.
  - Tests: `tests/b224_template_validity/` (new).
  - The diff: `evidence/b224_2026-11-25/b224.diff`; predecessor sha256 `58ca1259…81bb5`.
- **Switch:** none. A title with no draw thrown away is byte for byte the predecessor's. The test variants, the once
  rule, gate 1, the margins, `BARS`, the letters path and `companion/` are unchanged.
- **Live:** at the next `train` of a score title. T92's real rules are not retrained by this change.
- **Rollback:** `git apply -R evidence/b224_2026-11-25/b224.diff`.
