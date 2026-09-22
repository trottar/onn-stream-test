---
memory_schema: 1
as_of: 2026-09-22
status: PROPOSAL — a checkpoint description written by `M1`. **Nothing is staged and nothing is committed.** The commit is the user's decision.
---

# Checkpoint proposal, 2026-09-22

`M1` (`handoffs/M1_DOCS_RECONCILE_TASK.md`) is documentation only. **No
`git add`, no `git commit`, no `git push` was run.** This file describes
the tree as it stands so the commit can be made with one command if the
user wants it.

## The tree

`git status --short | wc -l` → **143** entries, of which one is this
file. With `--untracked-files=all` it is **557**, because that expands the
untracked evidence harness directories into their individual files.

**Nothing is staged.** `git diff --cached --name-only` is empty.

### Source changed (9 files)

| file | what changed, and the record |
| --- | --- |
| `companion/native_stream_profiles.py` | `max_frame_size_bytes` added as a profile field, 90,000 on `native_game_720p60_reference` — `D-BASE-P6a` |
| `companion/native_stream.py` | encoder overrides, `_effective_max_frame_size()`, argv logged at launch, NVENC ignore-and-log — `D-BASE-P6`/`P6a` |
| `companion/native_fec_relay.py` | per-frame packet **and** payload-byte counters, 1 Hz writer thread — `D-BASE-P5`/`P6` |
| `companion/plugins/games.py` | `frame_series=1` gate on the frame ring; the ten audio keys added to the heartbeat whitelist — `D-BASE-P5`/`P7` |
| `companion/games/decoder_session_log.py`, `native_session_io.py`, `emulator_manager.py`, `diagnostics/retention.py` | supporting changes across the `D-BASE` chain |
| `PrivyHub/app/src/main/java/streaming/NativeAudioReceiver.kt` | `maxArrivalGapMs`, session and window atomics, lock-free `updateMax()` — `D-BASE-P7` |
| `PrivyHub/app/src/main/java/streaming/NativeStreamActivity.kt` | `audioQuery()` emitting the ten audio fields, omitted entirely when the receiver is absent — `D-BASE-P7` |
| `PrivyHub/app/src/main/java/streaming/RtpH264Receiver.kt`, `AvcLowLatencyDecoder.kt`, `MainActivity.kt` | `D-BASE-R1`/`R2`/`R4`/`R5` counters and report fields |

### New source (6 files, untracked)

`PrivyHub/app/src/main/java/streaming/ThermalSampler.kt` (`T1`);
`companion/games/{native_stream_heartbeat,link_drop_recovery,log_rotation,host_resource_sampling}.py`
(`R2`/`R4`, `R3`/`R3a`, `R4`, `T1`); `tools/host_resource_sampler.py`.

### Top-level documentation changed by `M1` (5 files)

`README.md`, `docs/README.md`, `docs/PROJECT_STATUS.md`,
`docs/ROADMAP.md`, `docs/KNOWN_ISSUES.md`.

### Durable memory

**27 evidence records** and **18 patch records** added or changed, plus
**439 harness files** under the dated `evidence/<item>_<date>/`
directories (samplers, analysis scripts, redactors and raw redacted
output, each hashed in its record). `CURRENT.md`, `MEMORY.md`,
`TOOLS.md`, `LEARNINGS.md`, `CURRENT_HANDOFF.md`,
`investigations/{ACTIVE,DEFERRED,BASELINE_STREAM_HEALTH}.md`,
`evidence/RUNTIME_VALIDATION.md`, `patches/PATCH_INDEX.md` and the dated
files for 2026-09-20, -21 and -22.

### `.gitignore`

One addition: `/docs_flat/`, a local-only flattened convenience copy.

## Content safety check

- **No ROM, ISO, BIOS, firmware, key or savestate file** is tracked,
  staged, or untracked-and-unignored. Checked by extension
  (`.iso .bin .cue .chd .img .pbp .nes .sfc .smc .gen .z64 .n64 .gcm
  .nkit .rvz .key .pem .p12 .jks .keystore .ips .bps .ups`) and by
  directory (`roms/ isos/ bios/ keys/ saves/ states/`): **none**.
- **`logs/` is ignored** (`.gitignore:2`). `git ls-files logs/` is empty
  and `git status --porcelain logs/` is empty — nothing under it is
  tracked or staged.
- Every evidence and memory file written during this chain was passed
  through a redactor before landing under `docs/`; no address, MAC, SSID,
  serial, credential or device identifier is in any of them.

**Two untracked paths the user should decide about — `M1` did not touch
either:**

- **`.claude/`** — holds `settings.local.json`, this tool's own local
  settings. Untracked and **not ignored**. It is almost certainly meant to
  be ignored rather than committed.
- **`_prel2b/`** — three `.kt` files (`AvcLowLatencyDecoder.kt`,
  `NativeStreamActivity.kt`, `RtpH264Receiver.kt`), a pre-`C3.L2b`
  rollback copy kept beside the tree. Untracked and **not ignored**.
  Either ignore it or delete it; committing it would put a second copy of
  three client files in the repository.

## Proposed commit message

```
D-BASE: the loss column, closed — frame cap adopted, soaked and documented

The wireless-hop packet loss is explained and fixed. `D-BASE-P5` excluded
the onn's receive path (0 socket drops of 4,349) and correlated the loss
with the frame-size tail; `D-BASE-P6` then established the cause by
intervention rather than inference — capping the encoder's largest frame
removed 100 % of the >= 80-packet frames and 7-9x of the packet loss,
twice, with achieved bitrate, fps, encoder CPU and GPU power unchanged.
`D-BASE-P6a` adopted `max_frame_size_bytes = 90,000` as a declared field
of `native_game_720p60_reference` after the user's own perceptual check,
and `D-BASE-S3` held it for three hours: 5.4 losses/min, zero resyncs,
zero client socket drops, and a residual that correlates with nothing
measured. The loss column is closed at this level.

Also in this checkpoint: `O1` read the router's view of the air read-only
and excluded both the air and the Opal; `D-BASE-P7` named the last unknown
counter — `prolonged_starvation_events` is an audio arrival-gap counter
measuring jitter, not loss — and put ten audio fields on heartbeat schema
v3; `H2-PREP` inventoried the host's display, session and boot path
read-only before the headless cutover, and found no SSH server and no
autologin; and `M1` brought README.md, docs/PROJECT_STATUS.md,
docs/ROADMAP.md, docs/KNOWN_ISSUES.md and docs/README.md level with the
evidence, splitting the old single UDP entry into the still-paused
synthetic pathology and the now-resolved in-session loss.

Records: docs/memory/evidence/D_BASE_P5_WHICH_QUEUE_2026-09-21.md,
D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md,
D_BASE_P6A_CAP_ADOPTED_2026-09-22.md, D_BASE_S3_CAP_SOAK_2026-09-22.md,
D_BASE_P7_STARVATION_COUNTER_2026-09-22.md,
O1_OPAL_AIR_VIEW_2026-09-21.md,
H2_PREP_HOST_DISPLAY_INVENTORY_2026-09-22.md; decision
docs/memory/decisions/D-BASE-P6A_FRAME_CAP_ADOPTED.md.
```

To use it, after deciding what to do about `.claude/` and `_prel2b/`:

```bash
git add -A && git commit -F docs/memory/CHECKPOINT_PROPOSAL_2026-09-22.md
```

— noting that `-F` would take this whole file as the message, so the
message block above should be copied into its own file first, or the
commit written by hand.
