---
memory_schema: 1
as_of: 2026-09-28
status: TASK HANDOFF — C5-M2: the 1080p60 follow-up arms C5-M1 named — a screening night over three candidates (parity bitrate with the adopted 90 KB cap; 80 % bitrate with a scaled cap; 80 % bitrate with the 90 KB cap) against the adopted 720p60, then a confirmation night on the best-screening arm by the C5-M1 rules; capability-gated outcome; nothing adopted; the adopted profile and APK untouched; authorized by the user 2026-09-28
---

# C5-M2 — 1080p60, the follow-up arms

**Why.** `C5_M1_1080P60_PROFILE_2026-09-28.md`: at bits-per-pixel parity
(15,750 kbps, cap 200,000 B) 1080p60 was NOT CAPABLE (stream) — spikes
517-529/min, post-FEC loss 123-181/min, gap bound breached twice — while
the client decoded it and the host encoded it with room to spare. The
loss arrived as whole bursts of 94-111 packets: `P6`'s per-frame burst on
the wireless hop, at 2.25× the frame size (~150 frames/min of ≥ 80
packets; the capped 720p stream has none). The record named three levers,
none run. The user's reason for running them now (2026-09-28): today's
titles do not render at 1080p, but PS2, GameCube and N64 tests and the
remote transport will need it, and a 1080p that runs well makes native
720p the safer bet. So the question is the transport's, not the picture's:
**can the wireless hop carry a 1080p60 stream inside the close-out rows
if the per-frame burst is bounded?**

Read first: the C5-M1 record (§ design, § the shape, § what adoption
would mean) and its `c5_m1_design.txt`, `c5_m1_score.py`, `c5_m1_run.sh`,
`c5_m1_night.sh` (reuse the harness and the scorer; extend, do not
rewrite); `evidence/D_BASE_P6_FRAME_TAIL_CONTROL_2026-09-21.md` and
`D_BASE_P6A_CAP_ADOPTED_2026-09-22.md` (the cap's mechanism and what it
did to IDRs at 720p); `native_stream_profiles.py` (the candidate constant
and the selector as built); `evidence/D_BASE_CLOSEOUT_2026-09-23.md`;
`TOOLS.md`.

**Scope.** Companion: the selector stays as built; the candidate
constants become a small table of named 1080p profiles (ids below), each
1920×1080 @ 60, GOP 15, bframes 0, FEC 8, audio cushion 12/17 and
redundancy 2/4 copied unchanged; none is ever the default; the golden
test (selector unset → today's argv byte-for-byte) stays and is re-run
before and after. No client change (C5-M1: none needed); the adopted APK
stays installed, hash confirmed before and after. No encoder flag change
beyond width/height/bitrate/cap. GOP stays 15 in every arm (the recovery
contract: an IDR every 250 ms) — a larger GOP is noted as a later lever,
not tried here. The source window is not changed (that is a games-config
change, out of scope; noted). No `nft`. Attract mode, no controller in
any mode, the shadow/live flag and `PRIVYHUB_FEC_SCHEME` unset.

## The arms

| id | bitrate kbps | cap B | what it tests |
| --- | --- | --- | --- |
| `native_game_1080p60_c1_parity_cap90` | 15,750 | 90,000 | the burst bounded exactly as on 720p (≤ 75 packets); the bitrate unchanged |
| `native_game_1080p60_c2_80pct_cap160` | 12,600 | 160,000 | the bitrate lever alone (cap scaled by the same ratio as C5-M1's) |
| `native_game_1080p60_c3_80pct_cap90` | 12,600 | 90,000 | both levers |

Reported for every 1080p hold, not gated: cap hits per minute (frames at
≥ 95 % of the cap), IDR size p50/p90/max, frames of ≥ 80 packets per
minute, on-air Mbps, host/GPU load, T2 thermal, decoder queue depth,
`codec_ms`. The cap-hit rate is what the user's later picture check will
be read against (a cap below the IDR size trades burst for IDR quality —
`P6A` measured that at 720p; at 1080p it is unmeasured).

## Night 1 — screening (about 3 h)

Seven 20-minute attract-mode holds: **B, c1, B, c2, B, c3, B** — adopted
between every arm, companion restarted through its unit before each with
the selector set or unset, `T2` on, `any_override` recorded at PLAYING,
first hold ≥ 40 min after the last `session_ended`. One thing on the host
at a time.

**Pre-registered screening rule** (written before the night; not changed
after): an arm **passes screening** if its hold meets spikes < 200/min,
post-FEC video loss < 10/min, max output gap ≤ 250 ms, rendered fps ≥ 59.5,
stale drops < 20/min. Among passing arms the **confirmation candidate**
is the one with the lowest post-FEC loss; ties broken by higher bitrate.
If no arm passes: **NOT CAPABLE (all arms)**, night 2 is NOT RUN, and the
record gives each arm's rows and burst figures. The four B holds must
meet the baseline; if two or more miss, the night is **INCONCLUSIVE (link)**
and is re-run once the following night before anything else is decided.

## Night 2 — confirmation (about 2½ h)

Six holds **B / A / B / A / B / A** with the confirmation candidate,
exactly as C5-M1 ran and scored: **CAPABLE** if every close-out row meets
its target on all three A holds and the B holds meet the baseline;
**CAPABLE WITH COST** if all A holds meet the targets but a cost row is
worse than noise by the `S1` rule (named); **NOT CAPABLE** if any A hold
misses any row (named). The first hold ≥ 40 min after night 1's last
`session_ended`.

## Teardown (both nights)

Selector unset and confirmed absent in the manager and the companion's
environ, companion under systemd, profile adopted, adopted APK
`f31b1c18…8ae7` hash confirmed, stream at 7000, game inactive, banner
cleared, samplers stopped.

## Record and memory

`evidence/C5_M2_1080P60_FOLLOWUP_<date>.md` (the arms as built, the
golden checks, night 1's seven holds and the screening outcome, night 2's
six holds and the rule outcome, the burst and cap-hit figures side by
side with C5-M1's, what adoption would mean — a capability gate reading
per arm, and the picture check the user would still owe on any CAPABLE
arm); evidence dir with harness, scorer, reports, heartbeats, thermal,
manifest; `patches/C5-M2_*.md`; `PATCH_INDEX.md`;
`decisions/C5_1080P60_CAPABILITY_2026-09-28.md` (append the outcome per
arm; adoption pending the user); `docs/ROADMAP.md` C5; `docs/PROJECT_STATUS.md`;
`CURRENT.md`; `investigations/ACTIVE.md`; `TOOLS.md` (the profile ids;
never leave the selector set); the daily file;
`evidence/RUNTIME_VALIDATION.md`. No addresses or device identifiers.
Nothing adopted. Nothing committed.
