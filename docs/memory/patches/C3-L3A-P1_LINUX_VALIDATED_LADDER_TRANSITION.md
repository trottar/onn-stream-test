---
memory_schema: 1
as_of: 2026-09-19
baseline_commit: 4987cc6fa48e4c9a7153b62659aabc873c61e3b5
durable_memory_updated: true
---

# C3-L3A-P1 — Linux validated-ladder transition

## Purpose

`C3.L3a` needs several bitrate transitions inside one gameplay session.
`run_c3_linux_fixed_bitrate_cycle` permits exactly one: it requires the
stream to be at the 7000 kbps reference and will not target 7000, so after a
single cycle the session is parked off-reference with no legal next move.
That is why every `C3.L3` run used a fresh session per bitrate.

This patch ports the existing D-069 validated-ladder seam to Linux. It is
Part 1 of two; Part 2 is the gameplay acceptance probe and is not built here.

**Development patch.** Not runtime validated. The gate is below.

## Expected predecessor

`4987cc6fa48e4c9a7153b62659aabc873c61e3b5`

Per-file SHA-256 is enforced by the installer.

## What the source audit changed

The design in `architecture/ADAPTIVE_BITRATE.md` called for a new
`ladder_transition` flag, a new `diagnostic_c3_l3a_ladder_transition()`
method and a new `POST /plugins/games/c3-l3a-ladder-transition` route, on the
understanding that the Windows `validated_transition` work was "untouched and
historical" and only its *shape* could be reused.

Reading the source first found otherwise. Already present:

- `run_c3_validated_bitrate_transition()` and
  `VALIDATED_ADAPTIVE_BITRATES_KBPS` in `c3_fixed_bitrate_probe.py`;
- `NativeStreamManager.diagnostic_c3_validated_bitrate_transition()` in
  `native_stream.py`;
- the loopback-only route in `plugins/games.py`, allowlisting
  `{5500, 6000, 7000}`;
- `BIDIRECTIONAL_SCHEMA` and `BIDIRECTIONAL_MODE`.

The dispatch called the Windows implementation unconditionally, so on Linux
it failed the same way the fixed-bitrate cycles did before `C3.L3`. The seam
was built for D-069 and never ported. Adding a parallel flag beside it would
have been a second implementation of an existing path.

**Result: no new method, no new route, no new schema string.** Three files,
all small.

## Changed scope

`companion/diagnostics/c3_linux_actuator_probe.py`

- `run_c3_linux_fixed_bitrate_cycle` becomes
  `_run_c3_linux_bitrate_cycle(..., validated_transition: bool = False)`,
  mirroring the Windows `_run_c3_fixed_bitrate_cycle` split;
- two public wrappers: `run_c3_linux_fixed_bitrate_cycle(manager, target,
  **kw)` keeps its exact existing call shape and behaviour, and
  `run_c3_linux_validated_bitrate_transition(manager, *,
  target_bitrate_kbps, **kw)` matches the Windows keyword-only signature;
- new constants `BIDIRECTIONAL_SCHEMA`, `BIDIRECTIONAL_MODE` and
  `LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS = (5000, 5500, 6000, 7000)`, the
  first two identical to the Windows values;
- guards under `validated_transition=True` reuse the Windows error strings
  verbatim: `unsupported_validated_bitrate`,
  `validated_transition_requires_validated_start`, `bitrate_transition_noop`.

`companion/native_stream.py`

- `diagnostic_c3_validated_bitrate_transition` gains platform dispatch,
  mirroring `diagnostic_c3_actuator_continuity_cycle`. The Windows branch
  calls exactly what the method called before. Non-Linux, non-`nt` hosts now
  raise a clear `NativeStreamError` instead of importing a Windows module.

`companion/plugins/games.py`

- the route allowlist becomes `{5000, 5500, 6000, 7000}` and its error
  message follows.

Memory: `architecture/ADAPTIVE_BITRATE.md` (the design corrected to what
shipped, plus the Part 2 session design), `CURRENT.md`, `PHASE_C_CONTEXT.md`,
`investigations/ACTIVE.md`, `roadmap/STATUS.md`, `2026-09-19.md`, this
record. Generated: `patches/PATCH_INDEX.md`.

Unchanged: the Windows implementation, the `C3.L3` characterization path and
its preconditions, all probe scripts, all evidence, `MEMORY.md`, the
`C3.L2` classification, and every roadmap state.

## What does not relax

`manager.BITRATE_KBPS` and `MAX_BITRATE_KBPS` must still be 7000 in both
modes. That asserts the configured reference profile is untampered, which is
a different claim from where the stream currently sits. Only
`_active_bitrate_kbps` relaxes, and only under `validated_transition=True`.

Restart mechanics are untouched in both modes: kill, RTP baseline after the
kill, spawn, poll for resume, 0.75 s stability window.

## Ladder divergence from Windows, deliberate

Linux `(5000, 5500, 6000, 7000)`; Windows `(5500, 6000, 7000)`. 5000 kbps has
three valid Linux characterization samples from `C3.L3` and none on Windows.
The shared route allowlists the union; each platform's implementation rejects
what it has not characterized, so a 5000 kbps request on Windows fails closed
with `unsupported_validated_bitrate`. Recorded here because a shared route
with divergent platform ladders is a real asymmetry, not an oversight.

## Runtime gate before Part 2

One manual round trip, chained, both directions, ending at reference:

    7000 -> 6000 -> 5500 -> 5000 -> 5500 -> 6000 -> 7000

Six transitions. Chaining and upward movement have never run on Linux and
must not debut inside a blinded gameplay session. Acceptance: every
transition returns `ok`, `from_bitrate_kbps` matches the previous target,
FEC/audio/controller deltas are zero throughout, and the session ends at
7000 with the emulator and audio alive.

## Negative results

- **The design this patch implements was wrong about the repository, and the
  design document said so confidently.** It specified a new method and a new
  route that already existed. Reading `native_stream.py` and `games.py`
  before building is what caught it. The design section is corrected in
  place rather than deleted.
- **Nothing is runtime validated here.** A compile is not runtime validation.
  Chained transitions, upward transitions and returning to 7000 have never
  run on this host.
- **No Part 2 code exists.** The probe, the shared checkout module and the
  mark-capture loop are not in this patch.
- **The 5000 kbps asymmetry is not tested on Windows.** Windows is outgoing
  and no Windows host is available; the failure mode is argued from source,
  not observed.
- **`SUPPORTED_FIXED_BITRATES_KBPS` still excludes 7000** on the
  characterization path. That is deliberate — a characterization cycle to the
  reference would be a no-op — but it means the only way back to 7000 is the
  validated-transition path this patch adds.

## Validation performed

- installer Python compile;
- `py_compile` on all three changed source files;
- every repository caller of `run_c3_linux_fixed_bitrate_cycle` located and
  checked against the wrapper's signature — three call sites in
  `native_stream.py`, all passing `target_bitrate_kbps` as a keyword, all
  compatible;
- payload and installed SHA-256 verification per file, with wrong-state
  rejection before modification;
- generated index regenerated and verified after writing;
- LF line endings and trailing newline on every written file;
- `tools/check_memory_health.py` as a post-write gate with exact-byte
  rollback; `CURRENT.md` re-measured under both soft limits;
- ZIP integrity.

**Deliberately not performed:** no self-test, no synthetic fixture, no mock
manager, no sandbox install. Tier 1 per `patches/PATCH_PROTOCOL.md`. The
guard logic is decided by the runtime gate above, not by a fake manager here.

## Privacy

No network addresses appear in this patch or in any file it writes. The route
remains loopback-only.

## Result

Recorded on install.
