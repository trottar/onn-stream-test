---
memory_schema: 1
as_of: 2026-09-24
status: C3.L3a PART 2 R2 — the 2026-09-24 smoke session RECORDED (first run of the fixed probe on the adopted build): telemetry settling MEASURED (within one to two client reports), transition cost MEASURED (gap 125-211 ms, codec 7-11 ms), picture 9/9/9 acceptable; one report defect FIXED (Phase B windows anchored on fire + offset); smoke kept out of the pool; NOT a gate observation — rerun pre-registration unchanged, awaiting the user; C3.L4 stays BLOCKED
---

# C3-L3A-P2R2 — the smoke session, recorded; one report defect fixed

Task: `handoffs/C3-L3A-P2R2_TASK.md` (authorized by the user 2026-09-24).
Patch: `patches/C3-L3A-P2R2_PHASE_B_WINDOW_ANCHOR.md`. Evidence:
`c3_l3a_p2r2_2026-09-24/`, SHA-256 of every file in
`c3_l3a_p2r2_2026-09-24/sha256_manifest.txt`. Predecessor record:
`C3_L3A_P2R1_PROBE_DEFECTS_AND_RESCORE_2026-09-23.md`.

**Tools and documentation only**: one fix in
`tools/probe_c3_l3a_gameplay_acceptance.py`. No companion, client, profile,
route or environment change; no stream or session started; the companion
not restarted. The state file and the decoder session were read, never
written (SHA-256 identical before and after, `inputs_sha256_{before,after}.txt`).

## The session

The user ran the fixed probe once on the adopted build as a smoke session,
`--traversals 2 --dwell-min 40 --dwell-max 50`, Phase B included, and
finalized it. Run **`20260924_000330`**, seed 1502366457, state schema
`_v2`, primary W 5.0 s; 1 jump + 1 ramp, 4 Phase-A transitions, 2 decoys,
Phase A 103.472 s; parks 6000 / 5500 / 5000 × 45 s; restore 5000 → 7000.
Game: *The Emperor's New Groove* (PS1). Preflight read telemetry fresh,
`sample_interval_ms` 2000.

Decoder session `native_decoder_20260924_041256_754.json` (received
04:12:56Z, 479.0 s, client profiler 0.12.3, **8 SSRC changes = 8 expected**:
4 Phase A + 3 parks + 1 restore; the Phase-A restore correctly did not fire,
the stream was already at 7000). The finalize auto-selected it (earliest of
1 candidate with `ssrc_changes` ≥ 8).

**Operationally:** the first "finalize" attempt was the run command typed
again (`c3_l3a_smoke_20260924_001320.log`); preflight refused it — stream not
active, FEC / audio / controller not active, **telemetry not fresh** — and
wrote nothing. The preflight worked as intended. The real finalize ran six
minutes later (`c3_l3a_smoke_finalize.log`). The run log shows the rating
anchors printed right after each y/N prompt with no newline between: the
answers are not echoed into a teed log, so the anchors appear on the
question's line. Cosmetic; the answers are in the state.

## The fix — every per-transition window anchors on its matched SSRC change

P2R1's decoder view started each transition's 1 s slow-event window at
`fire + offset`, for Phase A and — in a v2 state, which records park and
restore fire times — for Phase B too. `fire + offset` misses the decoder's
restart by the row's residual. The 6000 park's SSRC change came **0.227 s
before** that point, so the row printed **72 ms** where the largest gap
inside `[ssrc, ssrc + 1 s]` is **211 ms** (at ssrc + 41 ms; the session's
`max_output_gap_ms`), and the 5500 park printed "–" for **166 ms**. Now every
row — Phase A, parks, restore — anchors on its own matched `ssrc_change`;
the fire time and residual stay beside it; the row also carries the largest
gap's `codec_ms` and its offset after the SSRC change; the report says so.
(Correction to the task's premise: P2R1 anchored Phase A on `fire + offset`
too, not on the SSRC change; on both runs the Phase-A values come out
unchanged.)

**Re-finalized after the fix** (`after_fix/20260924_000330.{json,txt}`):

| transition | to | fire s | SSRC ms | resid s | jump pk | 1st IDR ms | max gap in 1 s (ms) | at + ms | codec ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| jump 0 | 5000 | 0.000 | 13,865 | +0.023 | 0 | 18 | **125** | 35 | 9 |
| ramp 1 rung 1 | 5500 | 42.594 | 56,558 | +0.122 | 0 | 16 | **198** | 33 | 10 |
| ramp 1 rung 2 | 6000 | 47.920 | 61,739 | −0.023 | 0 | 35 | **154** | 51 | 9 |
| ramp 1 rung 3 | 7000 | 53.094 | 66,906 | −0.030 | 0 | 26 | **187** | 41 | 8 |
| park 6000 | 6000 | 103.482 | 117,097 | −0.227 | 0 | 22 | **211** (was 72) | 41 | 11 |
| park 5500 | 5500 | 149.455 | 163,266 | −0.031 | 0 | 2 | **166** (was –) | 19 | 9 |
| park 5000 | 5000 | 195.629 | 209,451 | −0.020 | 0 | 23 | **203** | 38 | 8 |
| restore | 7000 | 241.812 | 255,642 | −0.012 | 0 | 1 | **189** | 16 | 7 |

Confirmed: **125 / 198 / 154 / 187 / 211 / 166 / 203 / 189 ms, every one
with `codec_ms` ≤ 12** (7-11). Slow events retained 96 of 128 (32 marked +
64 recent) — not saturated, the whole session covered.

**The 2026-09-20 copy re-finalized** (`--state` / `--decoder` on
`c3_l3a_p2r1_2026-09-23/`): the per-transition values are **unchanged** — 12
not covered, 68 partial, 182 / 212 / 227, Phase B 241 / 164 / 181 / 223; every
other analysis key identical except the decoder path. One boundary moved:
ramp 6 rung 1's partial window now begins 0.551 s after its SSRC change, not
0.593 s after `fire + offset` (the anchor moved by the row's +0.041 s
residual). The new column shows that run's worst gaps carried **174-258 ms
of `codec_ms`** in the fully covered rows (78 in the partial one) — the task's
"190-260" is corrected to that.

## Keeping the smoke out of the pool

The regenerated `c3_l3a_runs/20260924_000330.{json,txt}` were moved into
`after_fix/` and are no longer in `logs/streaming/c3_l3a_runs/`; the
as-finalized pair (before the fix) is in `as_finalized/`.

**`--aggregate` after the move does not report 0 poolable runs. It pools
one: `20260920_010023`** (`aggregate_after_move.txt`). The skip keys on the
*analysis* schema, and P2R1's re-finalize rewrote that run file as
`privyhub_c3_l3a_analysis_v2` — from a `_v1` state, primary W 2.5, 8
traversals, dwell 30-75 s, none of it the pre-registration. P2R1's records
("skips pre-v2 run files by name") were accurate about the schema key and
wrong about the effect; that is P2R1's defect, found here. Left as the task
says: the 2026-09-20 files stay where P2R1 put them, and no second code
change was made. **It must be resolved before the rerun is pooled**, or the
pooled table will include a pre-cap session scored at W 2.5 — either move
`20260920_010023.{json,txt}` out of `c3_l3a_runs/` (evidence already holds
copies) or make `--aggregate` pool only runs whose state is `_v2` and whose
config matches the pre-registration. The user's decision.

## What the smoke measured

**Telemetry settling — measured for the first time.** 2 of 2 sequences:
**2.006 s** (jump) and **1.504 s** (ramp) after the sequence's last
transition returned, each by two distinct snapshots at a **2,007 ms**
cadence (`sample_interval_ms` 2000; budget 6 intervals). The first fresh
report after a transition already read 59.85 fps (jump) / 59.89 fps (ramp)
at the new bitrate (5.12 / 6.18 Mbps), `waiting_for_idr` false, queue depth
0, output gap ≤ 21 ms; no sample in either sequence failed the rule. The
first snapshot read in the jump's settling was pre-transition
(`session_elapsed_ms` 12,561, before the SSRC change at 13,865) — the rule
that the first read never counts excluded exactly the snapshot it exists to
exclude. **The resolution is one client interval, and the rule needs two
distinct reports, so the measured values are the rule's floor: telemetry
settled within one to two client reports (≤ ~4 s).** Not a sub-second
number, and not a recovery curve — the restart never showed in a 2 s
report.

**Transition cost on the adopted build.** All 8 SSRC changes aligned with a
fire: Phase A offset **13.842 s**, spread **0.152 s**, max residual
**0.122 s**; parks and restore residuals −0.227 to −0.012 s. `jump_packets`
0 on all 8; first IDR **1-35 ms**; the largest output gap in the second
after each **125-211 ms**, with `codec_ms` **7-11**. On 2026-09-20 the same
windows held 164-241 ms gaps carrying 174-258 ms of codec time; now the gap
is the restart's own RTP silence: `rtp_silence_after_spawn_ms` **152-153**
on all four Phase-A cycles, spawn 266-416 ms, first RTP resume 419-569 ms,
host verified 1,172-1,323 ms. **That silence is the floor of
`video_only_restart`**: a new encoder process emits nothing for ~150 ms, so
every transition costs one gap of that order at the decoder, whatever the
client does. A fact about the actuator, not a claim about perception.

**Marks: 0** in 103.5 s of Phase A (1 jump, 1 ramp, 2 decoys). At n = 1 per
shape this is one observation, not a rate; no detection rate is computed
from it. Decoy slack **6.2 s at W 8** (11.7 at W 2.5) — the P2R1 placement
rule held at runtime; both decoys fired on time (`late_s` 0.0).

**Picture, announced (Phase B)**, on the anchored 1-10 scale:

| kbps | 2026-09-24 (adopted build) | 2026-09-20 (pre-cap, unhealthy stream) |
| ---: | --- | --- |
| 6000 | acceptable, **9** | no, 5 of 10 |
| 5500 | acceptable, **9** | no, 3 of 10 |
| 5000 | acceptable, **9** | no, 2 of 10 |

The rungs were never the problem; the stream was. **The 5000-7000 ladder
stands for the rerun.**

**Lifecycle:** 0 FEC / 0 audio / 0 controller-bad-packet deltas over 4
Phase-A transitions; audio underruns **9** for the session, audio lost
**0** (23 recovered by the redundant copy), prolonged starvation **2**.

**Close-out rows for the session — context, not a gate** (7.98 min with 8
deliberate restarts):

| row | target | smoke 2026-09-24 | close-out C / W |
| --- | ---: | ---: | ---: |
| spikes ≥ 20 ms / min | < 200 | **40.46** | 32.8 / 26.0 |
| rendered fps | ≥ 59.5 | **59.77** | 59.90 / 59.91 |
| stale output drops / min | < 20 | **2.38** | 1.14 / 0.80 |
| video loss / min (post-FEC) | < 10 | **1.38** (11 lost, 10 FEC-recovered, 2 unrecoverable groups) | 8.67 / 8.40 |
| max output gap (ms) | ≤ 100 | **211** (a transition, the 6000 park) | 163 / 110 |

Every numeric-target row inside its target; **the baseline stays met** with
8 restarts in the session. The max-gap row is the transitions themselves.

**The user's words**, recorded verbatim as stated 2026-09-24, not a gate:
they did not even notice anything happening; it played incredibly; visual
quality was maybe a little lower sometimes but they could not tell at 720p
playing these older games; the title was *The Emperor's New Groove* (PS1),
which often had performance issues.

**Observed, not investigated (outside this task):** the controller
transport's `lost_packets` — a sequence-gap count on the client's input
datagrams (`native_session_io.py`) — rose **76 → 3,177** between preflight
and the state write (~9 min, ~345 / min); on 2026-09-20 it rose 287 → 498 over
a similar span (~23 / min). `bad_packets` stayed 0 and the user reported
nothing wrong with input. Recorded so it is not lost; no cause is claimed.

## What it does not establish

**Nothing about the gate**: one jump, one ramp and zero marks is not a
detection rate; the pre-registered reading needs ≥ 20 per shape pooled.
**Nothing about behaviour under real network pressure**: every transition
fired from a schedule, not from a degraded condition. The settling figure
says telemetry is clean at the first report after a scheduled transition on
a healthy stream; it says nothing about how fast it reflects a real
degradation.

## The rerun pre-registration — unchanged

As `C3_L3A_P2R1_PROBE_DEFECTS_AND_RESCORE_2026-09-23.md` fixed it: **10
traversals, dwell 55-90 s, primary W 5.0 s** (2.5, 8.0 beside), decoys
through both matched windows, **≥ 4 sessions pooled to ≥ 20 per shape**,
shape order randomized per run, Phase B at 6000 / 5500 / 5000 on the anchored
1-10 scale, each session's close-out rows beside the close-out table. The
user runs them; nothing runs without them. Before `--aggregate`: resolve the
pooling issue above. **`C3.L4` stays BLOCKED on the gate.**

## Validation performed

- `py_compile`; `--finalize --state <smoke state> --decoder <smoke decoder>`
  after the fix reproduces the eight values above with `codec_ms` 7-11;
- `--finalize` on the 2026-09-20 copy: per-transition values unchanged,
  every other analysis key identical but the decoder path;
- `--aggregate` after the move: runs, pools the 2026-09-20 file (above);
- state, decoder, logs and run outputs copied byte for byte (`cmp`); inputs'
  SHA-256 unchanged.

**Not performed:** no session; no second code change.

## Files (`c3_l3a_p2r2_2026-09-24/`)

- `c3_l3a_gameplay_acceptance_state.json` — the smoke state, byte copy;
- `native_decoder_20260924_041256_754.json` — the decoder session;
- `c3_l3a_smoke_20260924_000330.log` (the run), `c3_l3a_smoke_20260924_001320.log`
  (the refused re-run), `c3_l3a_smoke_finalize.log`;
- `as_finalized/20260924_000330.{json,txt}` — before the fix;
- `after_fix/20260924_000330.{json,txt}` — after it (moved out of the pool);
- `aggregate_after_move.txt`;
- `pre_patch_sha256.txt`, `post_patch_sha256.txt`,
  `inputs_sha256_before.txt`, `inputs_sha256_after.txt`;
- `sha256_manifest.txt` — every file above.

## Privacy

Loopback only. No network address or device identifier in any file here.
