---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: 7fae010856d2e2da5e5c5cdb501a9606b4e41ff4
durable_memory_updated: true
---

# C3-L3A-P2 — gameplay acceptance probe

## Purpose

Build the `C3.L4` gate so it can actually be performed. `C3.L2` reason 3 has
required a gameplay acceptance observation since 2026-09-18 and no tool
existed to take one; two sessions proposed the wrong observation in good
faith before the gate was given a definition.

Part 1 supplied the companion primitive and is runtime validated. This is
tools only.

**Development patch.** The probe has never been run against a live session.

## Expected predecessor

`7fae010856d2e2da5e5c5cdb501a9606b4e41ff4`

## Changed scope

Added:

- `tools/probe_c3_l3a_gameplay_acceptance.py`;
- `tools/manual_checkout.py`;
- this record.

Replaced:

- `docs/memory/CURRENT.md` — work item, next action, and a structural fix
  (below);
- `docs/memory/investigations/ACTIVE.md` — Part 2 state and how to run it;
- `docs/memory/roadmap/STATUS.md`;
- `docs/memory/TOOLS.md` — the new probes, and a stale claim corrected;
- `docs/memory/2026-09-19.md`.

Generated: `docs/memory/patches/PATCH_INDEX.md`.

**Unchanged: all companion source, all existing probes.** Part 1 supplied the
primitive, so no companion change was needed. No existing checkout probe was
migrated to the shared module.

## What the probe does

Three questions, kept separate because they have different answers and
different consequences.

**Phase A, blinded.** A ladder state machine alternates 7000 and 5000. Each
traversal is randomly a **jump** (one cycle, full 2000 kbps delta) or a
**ramp** (three cycles, one rung each, 4 s apart). Shape order is randomized
inside the run. Each dwell carries one **decoy** — a logged moment where
nothing fires.

Per the architecture's own fast-down/slow-up rule, the ramp is what routine
`C3.L4` adaptation would execute; the jump exercises the separately
authorized fallback/recovery case. They are recorded separately and never
pooled.

**Phase B, announced.** Parks at 6000, 5500 and 5000 for a fixed window each,
then asks once per level whether it looked acceptable, plus a 1-5 rating.

**Analysis.** A contingency table: marked / not-marked by jump, ramp and
decoy, plus marks attributed to nothing.

## Design decisions worth preserving

- **Decoys cost no session time.** One per dwell rather than their own slot.
  The decoy sits at a random *fraction* of the dwell remaining after
  telemetry settling, not at a fixed offset — an absolute offset would pin
  every decoy just after settling, placing decoys in a systematically
  different part of the timeline from sequences and biasing the comparison
  the baseline exists to make.
- **Marks are non-blocking**: Enter on the companion terminal, optional digit
  for severity. A blocking prompt would telegraph that something fired, which
  the blinding requirement forbids. This is the one thing the existing
  checkout idiom could not supply.
- **The association window is asymmetric**, `[event, event + 2.5 s]`, because
  a mark always lags the event by reaction time. Decoys are scored through
  the identical window.
- **Primary metric is binary per sequence.** A three-rung ramp inside 8 s may
  reasonably draw one press; mark count is secondary.
- **Always returns to 7000** — on success, on error, on SIGINT. Nothing in
  the repository did this before; a session stayed parked wherever the last
  cycle left it.
- **It is not a controller.** The schedule is generated up front from a seeded
  RNG. The probe never reads telemetry and decides a target. That is the line
  between this and `C3.L4`, and it is stated in the module docstring so a
  future session does not erode it by adding "just one" condition check.

## C3.L4 readiness

The report carries a `C3.L4 READINESS` section, because the gate answer alone
does not make the controller buildable. It records:

- per-transition cost by shape at n>>1 — spawn, first RTP resume,
  host-verified;
- cumulative FEC / audio / controller deltas across the whole session. A
  single transition is known clean; whether thirty are was not;
- **telemetry settling time after a transition**, sampled from
  `/diagnostics/stream-telemetry`. A controller polls that surface to decide;
  inside the settling window it is measuring the restart, not the network.
  Nothing had measured this;
- the minimum rung spacing exercised and the transition count per session;
- an explicit list of what remains unestablished, including that every
  transition here fires from a schedule rather than from a degraded
  condition.

## The shared module

`tools/manual_checkout.py` holds `yes()`, a report writer in the existing
`Classification:` convention, and the mark capture.

**Existing probes are deliberately not migrated.** Their reports are
load-bearing — `first_a9_prior_stages_ok` and `ctr_multitab_evidence_ok` are
checked as literal substrings by other probes — and they are runtime
validated. Migrating them is its own work item with its own predecessor
hashes and its own evidence. This module is additive and has exactly one
caller.

## CURRENT.md restructure

`CURRENT.md` tripped its 10 KB soft limit in four consecutive patches and was
being shaved by hand each time. Its `Verified State` section had grown to
3,729 bytes of per-item history duplicating `investigations/ACTIVE.md`'s
authoritative sub-item table.

That section is now a 1,759-byte live-state summary that points at
`ACTIVE.md` for detail. File total 10,212 -> 8,507 bytes, 195 -> 172 lines.
No fact was deleted; the settled per-item history already existed in
`ACTIVE.md` and the evidence records.

## Negative results

- **The probe has never been run.** Every design decision above is argued,
  not observed. A session may show the schedule is too long, the marking
  ergonomics wrong, or the settling budget too short.
- **`--finalize` and `--aggregate` have not executed against real data.**
  `--plan` was exercised because it is a real shipped path needing no
  network; the analysis paths were not, and no fixture was built to fake one,
  per `patches/PATCH_PROTOCOL.md`. The session state file is written before
  analysis, so a crash in `--finalize` loses no data and can be re-run after
  a fix.
- **`TOOLS.md` was stale by a day.** It described the fixed-characterization
  probes as "Windows-only and fail closed on Linux" after `C3.L3` had run ten
  cycles through them on Linux. Corrected here. That is the fourth stale
  memory claim found this session by reading source before writing.
- **Statistical power is modest and stated in the report rather than hidden.**
  ~20 of each shape estimates a detection rate to roughly +/-11% — enough for
  a large difference, not a subtle one. Pooling across runs is the remedy.
- **Nothing here advances the gate.** Building the instrument is not taking
  the measurement.

## Validation performed

- `py_compile` on both new tools;
- `--plan` executed for 8 and 30 traversals, confirming the schedule builder
  produces balanced shapes, correct rung sequences in both directions, and
  sane duration estimates;
- ladder step derivation checked in both directions: 7000 -> 5000 ramps as
  6000/5500/5000 and 5000 -> 7000 as 5500/6000/7000, jumps as a single cycle;
- payload and installed SHA-256 per file, wrong-state rejection before
  modification;
- generated index regenerated and verified after writing;
- LF line endings and trailing newline on every written file;
- `tools/check_memory_health.py` post-write gate with exact-byte rollback;
- `CURRENT.md` re-measured at 8,507 B / 172 lines;
- ZIP integrity.

**Deliberately not performed:** no self-test, no synthetic session state, no
mock companion. Tier 1.

## Privacy

Loopback only. The probe collects, formats and prints no network address, and
modifies no production file. Both new files state this in their docstrings.

## Result

Recorded on install.
