---
memory_schema: 1
as_of: 2026-10-06
status: TASK HANDOFF — E3-S4, queue item 4 (the user's go, 2026-10-06, "4 lighter core"): the SNES core's cost. One change behind a flag: a lighter SNES core for the suite row, bsnes untouched. Benchmark E1-SNES-STREAM ×2. Accept/reject by the pre-registered bar; the look is the user's, afterwards. Nothing adopted; nothing committed
---

# E3-S4 — a lighter SNES core

**Measured bottleneck (E2-S1 §4).** bsnes runs 27 threads, ~10 of them
at 37-44 % of a core each, 436-517 % of a core in total, varying run to
run (the row is NOT YET REPEATABLE at 20 min: host CPU 43.4 vs 50.0);
PSI cpu 45-103 ms/s. Nothing starves: RetroArch 60.0, capture 60.0,
rendered 59.66 / 59.98.

**Narrow hypothesis (E2's).** The SNES cost is bsnes's own
multi-threaded, partly spinning work; a lighter core removes it. **The
user chose this item knowing it is a fidelity choice; the look is
theirs afterwards; nothing perceptual gates this task.**

## 1. Inventory (before the change)

- The SNES cores RetroArch has installed on this host (the cores dir of
  the installed RetroArch; name, version, sha256 of each `.so`).
- The lighter candidate, in this order of preference, **the first one
  installed**: `snes9x_libretro.so`, then `snes9x2010_libretro.so`,
  then `snes9x2005_plus_libretro.so`. If none is installed, fetch
  **`snes9x_libretro.so` only** from the libretro buildbot for this
  platform into the cores dir (additive; record the URL pattern without
  tokens, the archive's and the `.so`'s sha256, the `.info` file). Fetch
  nothing else. If the fetch fails twice, the task is **NOT RUN (no
  lighter core available)** and the queue goes on.
- How the suite row selects the core today (`config/bsnes/<rom>.cfg`
  counter override; the companion's launch of Super Mario World) and the
  one line that would select another.

## 2. The one change

The suite row's core choice for the SNES fixture, **behind
`PRIVYHUB_SNES_CORE=<core name>`** (absent = bsnes, byte for byte): a
per-title override copy for the lighter core (`config/<core>/<rom>.cfg`),
the same counter override, fullscreen and resolution settings as
bsnes's (879×672 untouched, the 4x PS1 settings untouched), no core
options beyond defaults. bsnes and its files are not modified.

## 3. Pre-registration (hashed before any benchmark run)

- **Runs**: E1-SNES-STREAM ×2 with the flag (E2's window, 600 s gap
  before the pair as E2), the flag only inside those runs, absent after.
  A 3-min smoke first to confirm the core loads, the fixture runs its
  demo loop and the stream reaches PLAYING (if not, after the two-retry
  limit: **REJECTED (broke the row)**).
- **Bar, ACCEPTED only if all hold, both runs:**
  - RetroArch CPU ≤ **150 %** of a core (E2: 436-517);
  - host CPU mean ≤ **20 %** (E2: 43-50);
  - RetroArch fps ≥ 59.9; capture fps 60 ± 0.5; rendered fps ≥ 59.5;
  - the row **REPEATABLE** at 20 min on E1's bands (host CPU ± 2, GPU
    ± 3, RSS ± 5 %, RetroArch ± 0.5, rendered ± 0.5);
  - encoder dup+drop per minute not above E2's (≤ 0.2).
- **Reported:** PSI cpu, socket W, Tctl, the thread count, the core's
  name/version/sha256, video loss/min (the link's), the decoder report
  rows.

## 4. The record

`evidence/E3_S4_SNES_LIGHTER_CORE_<date>.md` + `e3_s4_<date>/` per the
queue, plus **what the user looks at to decide**: the core name, how to
start the SNES fixture with it by hand for a look (the flag line and
`tools/` route, from `TOOLS.md`), and the revert (unset the flag; the
`.so` may stay). `patches/E3-S4_...md`; `logs/e3_s4_git_status.txt`.
Flag absent; E2's final state restored; then queue item 5.
