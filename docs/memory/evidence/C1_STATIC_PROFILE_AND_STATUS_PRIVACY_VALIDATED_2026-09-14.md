---
memory_schema: 1
as_of: 2026-09-14
baseline_commit: 0c31c100ec721d687aff6aedbd79bc0cf9343810
---

# C1.1 Static Profile + Native Status Privacy Validation

**Classification:** RUNTIME VALIDATED / CHECKPOINTED / PUSHED

No network addresses or private absolute paths are recorded in this evidence.

## C1.1 static reference profile extraction

Profile:

`native_game_720p60_reference`

Validated runtime values:

- width: 1280;
- height: 720;
- fps: 60;
- target bitrate: 7000 kbps;
- max bitrate: 7000 kbps;
- GOP: 15;
- B-frames: 0;
- FEC group size: 8.

Representative game regression:

- picture: PASS;
- process audio: PASS;
- controller input: PASS;
- Pause/Resume: PASS;
- Save/Load: PASS;
- End/teardown: PASS.

## Native-stream public-status privacy validation

Live endpoint validator:

- helper status present: true;
- network identifier findings: 0;
- absolute path findings: 0;
- unsafe keyed-value findings: 0;
- retained client field redacted: true;
- retained helper log path redacted: true;
- sensitive values printed: no;
- raw helper status modified by validator: no.

The privacy hotfix changes public status serialization only. Raw helper status
remains local for diagnostics.

## Checkpoint

Checkpoint:

`0c31c100ec721d687aff6aedbd79bc0cf9343810`

Commit message:

`Checkpoint: validate C1 static profile and status privacy`
