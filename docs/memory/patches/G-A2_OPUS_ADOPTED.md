---
memory_schema: 1
as_of: 2026-10-19
baseline_commit: 263c26d
---

# G-A2 — `PRIVYHUB_AUDIO_CODEC=opus` adopted: the eighth line

**Result: INSTALLED SUCCESSFULLY** (applied directly in session A, 2026-10-19, `handoffs/G-A2_OPUS_ADOPTION_TASK.md`;
record `evidence/G_A2_OPUS_ADOPTION_2026-10-19.md`). The user's decision.

- **The drop-in (outside the repo):** `~/.config/systemd/user/privyhub-companion.service.d/audio-codec.conf` =
  `[Service]` / `Environment=PRIVYHUB_AUDIO_CODEC=opus`, written at 01:48:30Z, then daemon-reload and restart. The
  environ read eight lines.
- **The small patches** (`evidence/g_a2_2026-10-19/tools.diff`, `docs.diff`, `predecessors/`):

  | # | file | predecessor sha256 (16) | after (16) | edit |
  | --- | --- | --- | --- | --- |
  | 1 | `tools/e1_suite.py` | `6d0fd284aabe0bf6` | `656653531a1dd778` | `AUDIO_CODEC` in `ADOPTED` (eight); the preflight's `drop_in_audio_codec` |
  | 2 | `tools/e3_state.py` | `e1bf678c2530ff3e` | `31bc54b44942eac7` | the docstring ("eight"); the logic is e1_suite's |
  | 3 | `tools/e1_remote.py` | `892893d549839e29` | `4f8dbd54430d0375` | `preflight_remote` also requires the adopted set its callers pass |
  | 4 | `tools/test_e1_remote.py` | `b16337d1629fb2bf` | `ae6fca193f6bead7` | +1 test (the adopted set required) |
  | 5 | `docs/REMOTE_TRUST.md` | `c9d0910aca0cb58d` | `61e3f9b8c642b10d` | §9: the audio codec, an old client refused, how to turn it off |
  | 6 | `docs/CAPABILITY_MODEL.md` | `c8b6ca88f6fb8a87` | `4ee0fc896a09e990` | the wire-rate note (PCM-based threshold kept) |

- **Listed, not changed:**
  - the `"adopted7 ok"` strings in past evidence drivers (G8-S1, G8-S3, G4-S2): records, under their manifests;
  - `ADOPTED_E3` in `tools/d7_regression.py` and `tools/c3_l4_nft_night.py` (four lines, stale since G-A1).
- **Validation:**
  - `test_e1_remote` 21, `test_c3_l4_nft_night` 33, the `e1_suite --self-test`, and overlay 17 / session_identity
    88 / audio_codec 20: all OK;
  - `git diff --check` clean;
  - `--check` ok on eight lines;
  - the confirmation run valid, host gates held, Opus on by the drop-in alone.
- **Revert (written, not applied):**
  1. Delete `audio-codec.conf`.
  2. Run `systemctl --user daemon-reload && systemctl --user restart privyhub-companion`.
  3. Copy the predecessors back (#1-#4; #5-#6 are documentation).
