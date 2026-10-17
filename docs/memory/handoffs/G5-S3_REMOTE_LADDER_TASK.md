---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G5-S3 (session B, unattended): the live ladder learns the session's routing class and, on a remote path only, can actuate the 720p/4000 rung — the two gaps G5-S2 disclosed (findings 1 and 2). Behind `PRIVYHUB_REMOTE_LADDER=1` (absent = today, byte for byte). Proved by replay and in process; no stream
---

# G5-S3 — the remote ladder

Read first: `G5_S2_…` §1 (the two findings: no `path_class` in the ladder's context; the actuator refuses 4000), `docs/WAN_ADAPTATION_RULES.md` (R3.2, R5: "remote" and the floor), `C3_L4_…` (the live ladder: context, `_decide`, the actuator, `LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS`), `C5_M3_…` (720p/4000: what was screened — transport only — and what was not), `G3_S1_…` / `G3_S3_…` (`routing_evidence` at `token_issued` and in the session: where the games plugin knows it), `G4_S1_…` §3 (run 1's 7000-rung loss on the overlay: the case this is for).

## 1. The design (in the record §1 before the code, hashed)

- **The class into the context.** At session setup the games plugin already has G3's `routing_evidence` (`overlay` / `lan`). With the flag, the ladder's context gains `path_class` = `remote` when the evidence is `overlay`, `lan` otherwise; set once at session start, updated if the session's routing evidence changes (a re-setup), never guessed from an address. Without the flag the context is as today and G5-S2's default (`lan`) stands. One guarded hook in the games plugin, one in the ladder's context builder (a patch each).
- **The 4000 rung, remote only.** With the flag **and** `path_class` `remote`, the actuator's validated list is `4000 / 5000 / 5500 / 6000 / 7000` (720p60 at 4000 kbit/s: the rung C5-M3 screened). On the LAN, or without the flag, the list is today's `5000–7000` and 4000 is refused as today. The ladder's own step-down and G5-S2's `floor_4000` can then land on 4000; **nothing goes below 4000** (no rule suggests it; the actuator refuses it).
- **Recorded:** every actuation to 4000 in `decisions.jsonl` with `path_class`, the rule or trigger, and the result; `path_class` in every decision row when the flag is on.
- **Not in this task:** any change to the rungs' encoder parameters (4000 uses the encoder's existing bitrate control as 5000 does), the R5 strictness question, a cap (G5-S4).

## 2. The code and the proof

- The module / hooks; unit tests (context with and without the flag; the actuator's list by flag × class; the refusal of 4000 on the LAN and of anything below 4000 anywhere).
- **Flag absent, byte for byte:** the in-process handler comparison of the ladder and the actuator; the replay harness from G5-S2 over its four recorded runs with the new code present and the flag absent — the decisions identical to the recorded ones.
- **Flag present, replay:** the same four runs plus G4-S1's run 1 and run 2 (`g4_s1_2026-10-16/runs/…`: telemetry, status_poll, path.jsonl — `path_class` from the launch's routing evidence, `remote`), with G5-S2's rules on and off: per run, whether and when the ladder would have reached 4000, by which rule or trigger, and how long it would have stayed there under R5 — **tabulated, no claim that it would have played better** (that is G4-S2's job).
- The G1/G3/G5-S1/G5-S2 suites and the ladder's own tests green; the redactor.

## 3. The record

`evidence/G5_S3_REMOTE_LADDER_2026-10-17.md` + `g5_s3_2026-10-17/` (design + hash, the diffs, the test output, the replay tables, `redact_check.txt`, `manifest.sha256`); `docs/WAN_ADAPTATION_RULES.md` status lines (R3.2's floor "actuatable behind `PRIVYHUB_REMOTE_LADDER=1`, unvalidated live"); ROADMAP §G5; `patches/G5-S3_…md`; `logs/g5_s3_git_status.txt`. "Pending on the stream": the LAN smoke (the flag on, `path_class` reads `lan`, the ladder unchanged) and G4-S2. Nothing adopted.
