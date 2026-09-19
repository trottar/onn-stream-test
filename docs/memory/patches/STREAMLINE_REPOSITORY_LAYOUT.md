---
memory_schema: 1
as_of: 2026-09-18
baseline_commit: 588181444ce144dae2adaa02998a6dab7d8b45ab
durable_memory_updated: true
---

# STREAMLINE — repository and memory layout

## Purpose

Four structural problems found by the 2026-09-18 audit, fixed together because
they are one concern: the repository's shape.

1. dated history lived in two directories, with two different files claiming the
   same date;
2. a duplicate handoff pointer sat at the memory root beside the real one;
3. Windows-era tools filled `tools/` on a Linux-only host;
4. `.gitignore` repeated six rules and still missed the directories that keep
   turning up untracked.

Structural only. No companion, Android or tool source content is edited.

## Expected predecessor

`588181444ce144dae2adaa02998a6dab7d8b45ab`

Every moved and deleted file is verified by SHA-256 before anything is touched,
and the installer refuses a partially applied state rather than guessing.

## Changed scope

**Moved, 15 files.**

Windows-era tools out of the tracked tree, into `archive/windows_tools/`, which
`.gitignore` already covers:

```text
tools/build_install_onn.ps1
tools/audit_repo_checkpoint.ps1
tools/run_privyhub_debug.ps1
tools/run_udp_transport_probe.ps1
tools/run_udp_reverse_transport_probe.ps1
tools/run_udp_loopback_probe.ps1
tools/probe_a4_minimize_wgc.py
tools/probe_a4_occluded_background_wgc.py
tools/a4_audio_mute_probe/            (2 files)
tools/a4_audio_float_attenuation_probe/  (2 files)
```

Dated history up one level:

```text
docs/memory/memory/2026-09-10.md -> docs/memory/2026-09-10.md
docs/memory/memory/2026-09-11.md -> docs/memory/2026-09-11.md
docs/memory/memory/2026-09-14.md -> docs/memory/2026-09-14.md
```

**Deleted, 2 files.** `docs/memory/CURRENT_HANDOFF.md`, a pointer duplicating
`docs/memory/handoffs/CURRENT_HANDOFF.md`, which is the file `MAINTENANCE.md`
and `tools/check_memory_health.py` recognize. And
`docs/memory/memory/2026-09-15.md`, whose content is preserved in the merge
below. `docs/memory/memory/` is then removed.

**Replaced, 6 files.** `.gitignore`; `docs/KNOWN_ISSUES.md`;
`docs/memory/AGENTS.md`; `docs/memory/TOOLS.md`;
`docs/memory/2026-09-15.md` (merged); `docs/memory/2026-09-18.md`.

**Added:** this record. **Generated:** `docs/memory/patches/PATCH_INDEX.md`.

## The 2026-09-15 merge

Two files, same date, different work, neither a superset:

- the memory root's 7,335 bytes recorded the Phase D Linux baseline — Debian
  13.7, Renoir VAAPI, x11grab exact-window capture, PulseAudio isolation, uinput
  four-pad support, the staged RetroArch runtime — and patches D-076 through
  D-078;
- the nested 21,146 bytes recorded the first integrated Linux/onn E2E diagnosis,
  the idle UDP tests in both directions, the Opal router branch through D-083,
  the ADB wireless recovery work and the D4 handoff realignment.

Both bodies are carried verbatim into `docs/memory/2026-09-15.md` under their
original titles, with a header stating the consolidation. 28,847 bytes out
against 28,481 in; the difference is the header. Nothing was summarized,
reordered or dropped, which is the rule `MAINTENANCE.md` sets for compression.

## Intentionally unchanged scope

`CURRENT.md`, `PHASE_C_CONTEXT.md`, `MEMORY.md`, `LEARNINGS.md`,
`MAINTENANCE.md`, `roadmap/STATUS.md`, `handoffs/CURRENT_HANDOFF.md`, and every
decision, evidence and investigation record. The roadmap does not move.

Deliberately **not** archived, with reasons:

- `tools/run_opal_*.sh` and `tools/analyze_opal_*.py` — POSIX shell and Python
  that run on this host. D-083 paused the branch but allows re-entry for one
  bounded measurement that would change a product or roadmap decision.
- `companion/native_wgc_bridge.py`, `companion/process_audio/`,
  `companion/diagnostics/c3_actuator_probe.py` and
  `companion/diagnostics/c3_fixed_bitrate_probe.py` — Windows-only, but
  production dispatch selects them by platform and they fail closed on Linux.
  Moving them would risk a working path for cosmetic gain.

`_patches/`, `_probes/` and `Claude outputs/` are now ignored but are **left on
disk**. Deleting a user's directories is not an installer's decision.

## .gitignore

The previous file listed `logs/`, `archive/`, `runtime/`, `data/`,
`__pycache__/` and `*.pyc` twice each and carried three overlapping `privyhub_*`
patterns. It is regrouped with each rule once and adds `_patches/`, `_probes/`
and `Claude outputs/` — the gap `C3.L0` recorded in `docs/KNOWN_ISSUES.md`,
which this patch closes. No existing rule's effect is removed.

## Negative results

- The duplicate `2026-09-15.md` could not be resolved by choosing one file;
  both had unique content, so the honest fix was a merge and the patch is
  larger for it.
- The Windows tools are archived rather than deleted. Deletion would have been
  smaller, but `archive/` keeps them one `ls` away, and git history holds them
  either way.
- The `.gitignore` gap was recorded by `C3.L0` on 2026-09-18 and went unfixed
  through six subsequent patches because each one correctly refused to make an
  unrelated change. It needed a patch whose purpose was repository shape.

## Validation performed

- installer Python compile;
- installer self-test against a fixture built from the real predecessor bytes:
  wrong pre-state returning `FAILED BEFORE MODIFICATION` with a byte-identical
  snapshot before and after; clean install; every move landing with no source
  left behind and byte-identical content; delete targets removed; emptied
  directory removed; the merged dated file carrying both original titles;
  `.gitignore` covering the three previously uncovered directories with no
  duplicated rule; backups written; idempotent reinstall changing nothing;
  memory-health gate failure and forced validation failure each returning
  `ROLLED BACK` with every moved and deleted file restored;
- `tools/check_memory_health.py` executed as a post-write gate;
- payload and installed SHA-256 verification;
- LF line endings and trailing newline preserved on every touched file;
- `git diff --check` and ZIP integrity executed by the delivery block.

No runtime validation applies; this patch changes no executable behavior.

## Result

Recorded on install.
