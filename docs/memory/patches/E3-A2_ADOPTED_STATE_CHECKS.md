---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: e553673
durable_memory_updated: true
---

# E3-A2: the adopted state's checks expect Snes9x (frame_spin added, then reverted by the bar) (tools only) + the drop-ins (host, outside git)

## Purpose

E3-A2 (`handoffs/E3-A2_FRAME_SPIN_AND_SNES9X_ADOPTION_TASK.md`, record
`evidence/E3_A2_FRAME_SPIN_AND_SNES9X_ADOPTION_2026-10-07.md`) adopts
E3-S5C's `frame_spin` and E3-S4's Snes9x core. The user, 2026-10-07:
"Adopt frame_spin if you think helps"; after the look, "Sure it ran
smoothly from what I can tell". **Snes9x STANDS; `frame_spin` was
REVERTED by the verification bar** (one run's underruns 24 > 20). The
companion's environ is now exactly three `PRIVYHUB_*` lines: live, the
index, Snes9x.

## Change

**On the host (not in git)**, in
`~/.config/systemd/user/privyhub-companion.service.d/` (copies in
`evidence/e3_a2_2026-10-07/`):

- `audio-pacing.conf`: `[Service]` / `Environment=PRIVYHUB_AUDIO_SENDER_PACING=frame_spin`
  (written 22:52:28Z; **removed at the revert, 01:05Z 10-08**)
- `snes-core.conf`: `[Service]` / `Environment=PRIVYHUB_SNES_CORE=snes9x` (stays)

`adaptive.conf`, `epg-index.conf`, the unit file and `emulators.json`
are untouched.

**Tools** (adoption-time diff, hashed in the pre-registration:
`evidence/e3_a2_2026-10-07/e3_a2_state_checks.diff`; **after the revert:
`e3_a2_state_checks_final.diff`**, which is what the tree carries):

- `tools/e1_suite.py`:
  - `SNES_CORE`; `ADOPTED` = live, index, Snes9x (`PACING` was in it
    from 22:53Z to the revert);
  - the preflight also checks that `snes-core.conf` is listed;
  - **the SNES row's counter override moves to `config/Snes9x/`**, the
    adopted core's corename dir; under bsnes it was `config/bsnes/`.
- `tools/e3_state.py`: its docstring only; it reads through the
  preflight.
- `tools/d7_regression.py`: `ADOPTED_E3` (index, Snes9x). The boot row
  accepts them beside the live default; any other name counts as
  "other".
- `tools/c3_l4_nft_night.py`: the same `ADOPTED_E3`.
  - `env_baseline_refusal` accepts the three names.
  - `setup()`'s check compares the environ minus those names with the
    live default.
  - The harness never sets or unsets them.
- `tools/test_c3_l4_nft_night.py`: one test for the adopted names (and
  that `frame_spin` is refused like any other flag).

## Validation

- `e1_suite.py --self-test` OK; `test_c3_l4_nft_night` 33/33;
  `py_compile` of `d7_regression.py`.
- `e3_state.py` `ok: true` on the four-line state (22:53:02Z) and on the
  three-line state after the revert (01:05:05Z); the tests 33/33 both
  times.
- The verification runs passed preflight, teardown and the final state
  through these checks.

## Rollback

Per item, with its kill switch (`TOOLS.md`): delete the drop-in,
`daemon-reload`, restart, and take its name out of `ADOPTED` /
`ADOPTED_E3`. For Snes9x, also move `SMW`'s override back to
`config/bsnes/`. Or reverse the whole diff.
