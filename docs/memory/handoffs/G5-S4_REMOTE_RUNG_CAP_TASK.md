---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G5-S4 (session B, unattended): a user-set bitrate cap for remote sessions, a data saver — `PRIVYHUB_REMOTE_RUNG_CAP=<kbps>` (absent = today, byte for byte). The user's choice, never automatic. Proved in process and by replay; no stream
---

# G5-S4 — the remote rung cap

Read first: `G5-S3_REMOTE_LADDER_TASK.md` and its record (the context's `path_class`; the remote list `4000–7000`), `C3_L4_…` (the ladder's increase rule and its hold-downs), `G4_S1_…` §9 (5.1 GB/hour at 7000, 2.3 at 4000 — the reason).

## 1. The design (in the record §1 before the code, hashed)

- **The flag** carries a rung in kbit/s. It is valid only if it names a rung in the remote list G5-S3 defines (`4000 / 5000 / 5500 / 6000 / 7000`); any other value is logged once and ignored (today's behaviour). It depends on G5-S3: with `PRIVYHUB_REMOTE_LADDER` absent the cap does nothing and says so once in the log.
- **Effect, remote path only** (`path_class` `remote`): the ladder's chosen target is clamped to the cap — a session starts at the cap or below, an increase never exceeds it, step-downs are the ladder's own. On the LAN: no effect. The cap never lowers the floor and never forces a step-down by itself.
- **Recorded:** every clamp in `decisions.jsonl` (`source: remote_cap`, the ladder's wish, the capped target).
- **Not in this task:** a client-side setting (the field would be G3's Settings dialog, session A's APK work; the flag is the hub-side switch the user sets by a drop-in for now); a data counter.

## 2. The code and the proof

- A small module or a guarded clamp in the ladder's target selection (one `if`, a patch); unit tests (absent, invalid, valid at each rung; LAN unaffected; the interaction with G5-S2's suggestions: a `floor_4000` under a 5000 cap still lands on 4000).
- **Flag absent, byte for byte:** the handler comparison; the G5-S2 replay identical.
- **Flag present, replay:** G4-S1's runs 1 and 2 with the cap at 4000 and at 5000: the target per tick, the clamps, the wire rate the rung implies (from C5-M3's and E2-S1's measured rates) against the measured 11.42 Mbit/s — the data per hour at each cap stated as arithmetic, not as a result.
- The suites green; the redactor.

## 3. The record

`evidence/G5_S4_REMOTE_RUNG_CAP_2026-10-17.md` + `g5_s4_2026-10-17/`; `docs/WAN_ADAPTATION_RULES.md` (a line under R3: the cap, the user's); ROADMAP §G5; `patches/G5-S4_…md`; `logs/g5_s4_git_status.txt`. "Pending on the stream": the first off-site run with the cap at 4000 — the user judges the picture, not a record. Nothing adopted.
