---
memory_schema: 1
as_of: 2026-11-08
baseline_commit: 6fcd2f23
---

# B63 — the PS1 multitap only for a multitap-capable title (default-on host change; PRIVYHUB_PS1_MULTITAP_CAPABILITY=0 = today)

**Result: SETTLED + BUILT; tests and mutations in `evidence/B63_PS1_MULTITAP_CAPABILITY_2026-11-08.md` §2.**

- **Apply:** `git apply evidence/b63_2026-11-08/b63.diff` — the four diffs in order b61, b62, b63, b64 (each
  against the previous snapshot); applied to the tree, uncommitted.
- **Live:** at the next companion restart (HOME-8 stage 1); no new environment line, nothing to adopt.
- **Rollback:** reverse the diffs in the order b64, b63, b62, b61 (`diff_check.txt`).
- **The knob:** `Environment=PRIVYHUB_PS1_MULTITAP_CAPABILITY=0` in a drop-in restores today (every PS1 title capable); absent = the rule.
