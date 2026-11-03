---
memory_schema: 1
as_of: 2026-10-31
baseline_commit: 1904fe8
---

# B33 — no rewind without loss

**Result: BUILT** inside the adopted `PRIVYHUB_LINK_RECOVERY=1`.
- **Tests:** `tests/rewind_needs_loss` 14 green; every `tests/` suite the same as the baseline; 2 mutations caught.
- **Proof:** absent / `=0` / junk = today, PROVEN, row for row.
- **The replay:** of the trip's 5 stall loads, 4 would have resumed. The 05:28 link loss still loads.
- **Status:** no live run; nothing committed.
- **Record:** `evidence/B33_NO_REWIND_WITHOUT_LOSS_2026-10-31.md`.
- **Diff:** `evidence/b33_2026-10-31/b33.diff`.

**What it does.** At the release (B9's `Cores.release`, the one place a load happens), a stall or silence under 1 s
resumes with no load when there is no loss behind it. "No loss" means:
- a heartbeat was received in [onset − 2.5 s, release];
- in that window, Δ`lost_packets` = 0 and Δ`fec_unrecoverable_groups` = 0;
- in that window, every heartbeat has `audio_max_arrival_gap_ms` < 250;
- the host's controller-sequence loss counter is unchanged.

The release then writes `input_release` with `method` `resume`. Otherwise it is today's load, with `why` (`long` /
`loss` / `dark_span` / `uplink_loss` / `no_heartbeat` / …) on its row. The save still happens.

**Files:**
- `companion/rewind_needs_loss.py` (new);
- `companion/rewind_cores.py`: a class attribute, one guarded branch in `release`, a guarded wire;
- `companion/games/link_drop_recovery.py`: a class attribute, one guarded call in `note_heartbeat`;
- `tests/rewind_needs_loss/` (new).

**Apply:** `git apply docs/memory/evidence/b33_2026-10-31/b33.diff`, from the repo root. It acts at the next
companion restart, because the umbrella is adopted.

**Rollback:**
- `PRIVYHUB_REWIND_NEEDS_LOSS=0` in the service's drop-in gives today, byte for byte;
- or revert the three files and remove the new module and suite.
