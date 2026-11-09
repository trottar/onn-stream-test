---
memory_schema: 1
as_of: 2026-11-09
baseline_commit: a5c51e37
---

# B74 — the disc change made safe: the sequence settled (unchanged), a set starts on disc 1, the warning, "Start on disc…" (NOT adopted; default on)

**Result:** `evidence/B74_DISC_CHANGE_SAFE_2026-11-09.md` (what Beetle and a console do on a lid cycle, RetroArch's disk
index record, tests, mutations, proof, the APK).

- **Apply:** `git apply evidence/b74_2026-11-09/b74.diff`, after `b73.diff`. Applied to the tree second, uncommitted.
- **Live:**
  - the host: at the companion's next restart. Every library launch of a multi-disc PS1 set starts on disc 1, or on
    the disc asked with `disc=j`; RetroArch's record is set before it starts. `launched_disc` goes on `disc_swap` /
    `launch_ports`, and `discs` on a set's details. Every other game is today's;
  - the client: with the APK `85220f99…4864` (the warning once per onn, the line after a change, Extras → "Start on
    disc…" for sets).
- **Off:**
  - the host: `PRIVYHUB_DISC_SWAP=0` (B71's knob: no disc session, nothing written, today's launch call);
  - the client: `debug.privyhub.disc_safe=0` (B71's flow).
- **Writes outside the code:** RetroArch's own `saves/<core>/<set>.ldci` for a set's launch, only when it differs.
  It is never deleted.
- **Rollback:** `git apply -R` in the order 74, 73. A record the host set stays as written; RetroArch rewrites it at the
  next close.
