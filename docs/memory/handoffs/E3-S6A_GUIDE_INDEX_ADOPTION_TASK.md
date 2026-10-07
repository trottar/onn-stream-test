---
memory_schema: 1
as_of: 2026-10-07
status: TASK HANDOFF — E3-S6A, queue item 1 (the user's authorization in chat, 2026-10-07: "1. Adopt"): adopt E3-S6's cached guide index as the companion's default through its own systemd drop-in; verify the adopted state on the suite (META, CONC, PS1-STREAM, one run each); update the state check, TOOLS.md's kill switches, ROADMAP and CURRENT.md. Nothing else adopted; nothing committed
---

# E3-S6A — adopting the cached guide index

**What is adopted.** E3-S6's one change, MEMORY ACCEPTED on its
pre-registered bar (`evidence/E3_S6_GUIDE_INDEX_2026-10-07.md`): with
`PRIVYHUB_EPG_GUIDE_INDEX=cached` the EPG plugin reads a slim channel →
source index (3.7 MB, built once per metadata file size+mtime, saved as
`data/epg/metadata/guides_index.json`) instead of parsing the 25.6 MB
metadata file per grab. Measured: companion PSS ~34 MB through a grab
cycle (not ~160), grab-cycle CPU 0.22 % (not 7.6 %), grabs ~0.4 s
faster, candidates identical, the guide serves the same. Its STREAM half
was REJECTED and is **not** claimed by this adoption: grabs during a
stream are roughly half as damaging, not fixed.

**The user's words, verbatim, 2026-10-07:** "1. Adopt".

Read first: the E3-S6 record and `e3_s6_2026-10-07/` (the diff, the
smoke, `index_cost.json`), `TOOLS.md` (the live-default drop-in and its
kill switches, "The E3 flags"), `C3_L4_D1_LIVE_DEFAULT_2026-10-01.md`
(how the last adoption through a drop-in was recorded), the suite's
final-state check.

## 1. The adoption

- A **separate** drop-in,
  `~/.config/systemd/user/privyhub-companion.service.d/epg-index.conf`,
  with exactly `[Service]` and
  `Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached`. `adaptive.conf` and the
  unit file untouched. `daemon-reload`; restart the unit.
- Verify: the companion's environ carries exactly the two `PRIVYHUB_*`
  lines; the manager none; `guides_index.json` absent until the first
  grab, then present with its size and sha256 recorded; one forced
  refresh of each of the six channels ok with candidates identical to
  E3-S6's smoke dump.
- **The state check** (the suite's teardown/precondition code and
  `tools/e3_state.py` if that is it): the expected environ becomes the
  two lines above; everything else unchanged. Recorded as a patch.
- **Kill switches**, in `TOOLS.md` beside the live default's: delete
  `epg-index.conf` + `daemon-reload` + restart (off; the index file may
  stay or be deleted, it is rebuilt on demand). The flag's absent value
  is today's parse, byte for byte, as E3-S6 showed.

## 2. Verification on the adopted state (pre-registered, hashed before the runs)

No flag is set for these runs: the adopted default is what runs.

- **Runs**: E1-PS1-STREAM ×1, E1-META ×1, E1-CONC ×1 (E2's windows and
  gaps).
- **Bar, the adoption stands if all hold** (otherwise the drop-in is
  removed, the state check reverted, and the record says **ADOPTION
  REVERTED** with the failing clause):
  - META: companion PSS at the window's end ≤ 60 MB and not growing
    (≤ 5 % over the last 15 min); grabs failed 0, ok ≥ 205, median ≤
    6.8 s; the guide serves (6 channels; programmes ± 5 % of a pre-run
    read); host CPU ≤ 11.8;
  - CONC: companion PSS at the end ≤ 60 MB; grabs failed 0; the stream
    rows **reported** (loss, rendered, resyncs, underruns, the aligned
    frame) beside E3-S6's two CONC runs and E2's — not gated, E3-S6's
    STREAM verdict stands;
  - PS1-STREAM: within E1's bands of E2's PS1-STREAM (host CPU 11.7 ± 2;
    rendered 59.81 ± 0.5), companion PSS and CPU reported — the index
    must not touch plain streaming.
- **Reported:** the index build (when, how long), its reload on the
  restart, the file's size and sha256 at the end.

## 3. The record

`evidence/E3_S6A_GUIDE_INDEX_ADOPTION_<date>.md` + `e3_s6a_<date>/`
(the drop-in's text, the environ dumps before/after, the candidate dump
diff, the pre-registration + `.sha256`, 3 runs, `manifest.sha256`,
`--check`, table, verdict, `redact_check.txt`); `patches/` (the state
check) + `PATCH_INDEX.md`; `TOOLS.md` (the drop-in, the kill switch,
the index file); `docs/ROADMAP.md` (E3: first adoption); the daily file;
`logs/e3_s6a_git_status.txt`. **The final state at the end is the
adopted state** (two environ lines, no other flag, no game, PS1 files
identical, APK CONFIRMED); then queue item 2.
