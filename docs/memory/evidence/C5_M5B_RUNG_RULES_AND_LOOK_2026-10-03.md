---
memory_schema: 1
as_of: 2026-10-04
baseline_commit: a402272
status: C5-M5B DONE — behind flags, NOTHING ADOPTED. Selection (pre-registered, written before code) - ENTRY E415 (>= 415 of 450; 8 of 10 real-input holds within 20 min); LEAVE none qualified (S1's 80 lost/min was one 183-packet burst; n1r C3's loss began 587-714 s in), the mild bar kept. Build - tests 120/120, mutations 14/14, stop rule 0 differences over 386 series. S1b injection PASSES (348/346 ms; the leave row not applicable as worded). S2b daytime NOT RUNG SHOWN (recovery paused the game at 4.4 min; the window met 415 at 15.1 min on a frozen picture; the guards refused 448 entry decisions). S3b night DOES NOT WORK AS A RUNG by its rows - one entry by its own rule at 15.1 min (434 of 450), 104.9 min at 1080p, no leave, 0 recovery, fps 60.18, loss 2.82/min, but the session's spikes 317.9/min vs < 200 (the onn's known 1080p decode rate) and the entry switch's gap 649 ms. Look - session options file mechanism (smoke 2048^2), adopted .opt/.cfg byte-identical in 14 sessions; cost table - dither off, bilinear / 3-point / SABR, PGXP and the full preset HOLD 60 at 720p, xBR and JINC2 miss, MSAA not offered (Vulkan-only); remaster (4x + bilinear + dither off + PGXP) offered behind PRIVYHUB_PS1_LOOK, remaster-1080p not offered (one dropped frame at the rung); tools/ps1_look.sh fake-run 8/8. Flags unset and absent; live default intact; APK de072762...835e; nothing committed
---

# C5-M5B — the rung's rules from the data, and the look

Task: `handoffs/C5-M5B_RUNG_RULES_AND_LOOK_TASK.md`, run unattended under
`handoffs/QUEUE_2026-09-29B.md`'s rules, from 2026-10-03 12:17 EDT.
Evidence: `c5_m5b_2026-10-03/`.

**The pre-registration** (`c5_m5b_preregistration.txt`, sha256 `6ba1e522…`)
was written at 12:21 EDT (16:21Z), before any replay, code change or
session. It holds the candidate grids, the strictness order, both
selection rules, the sessions' rows and the look's rules.

## 1. The entry, from the data (`c5_m5b_replays.txt`, `tools/c5_m5b_replay.py`)

**SELECTED: E415**, ≥ 415 of the last 450 reports clean (N stays 450).
The selection (`c5_m5b_selection.txt`, sha256 `01152549…`) was written
at 16:30Z, before the companion was touched.

| candidate | real-input holds entered within 20 min (of 10) | proxies (of 10) |
| --- | ---: | ---: |
| E435 (as built) | 0 | 5 |
| E430 | 0 | 9 |
| E425 | 1 | 10 |
| E420 | 4 | 10 |
| E300 (280 of 300) | 5 | 10 |
| **E415** | **8** | 10 |
| E410 | 9 | 10 |
| E405 | 9 | 10 |

- The rule: the strictest candidate that enters within 20 minutes on at
  least 7 of the 10 real-input holds. E415 enters on 8, at 15.0-16.9 min,
  so the window filled in each.
- It misses LINK-L2 H3 (best 409 of 450 by 20 min) and H5 (best 396).
- **Unclean after the replayed entry:** on the same holds' own later 720p
  reports, 4.3-15.7 % (median about 8 %). That is a preview, not a 1080p
  measurement.
- C5-M5's S2 and S3's 7000 stretch would each have entered at 15.0-15.1
  min.

## 2. The leave, from the data

**NO CANDIDATE MEETS THE THREE HARD CONDITIONS. The mild bar is kept, and
the user decides.**

| candidate | (1) leaves S1's stretch within 60 s | (2) leaves n1r C3 within 120 s | (3) no leave on S3 | fires on k of 13 |
| --- | --- | --- | --- | ---: |
| mild bar (as built) | no | no (739.4 s) | yes | 1 |
| L-A ≥ 100 lost on 2 of 10 | no | no (714.2 s) | yes | 3 |
| L-B ≥ 300 lost in 15 | no | no (587.1 s) | yes | 5 |
| L-C ≥ 50 lost on 3 of 10 | no | no (587.1 s) | yes | 2 |
| L-D L-A or stale ≥ 5 | no | no (714.2 s) | yes | 4 |

- **S1's stretch.** C5-M5 described it as "80 lost per minute". That figure
  is **one report of 183 lost packets**: a sequence resync's jump, 40 s
  after the entry. The other 68 reports lost 0-3.
  - No candidate's bar is met anywhere on the stretch, with or without
    the gates (the "raw bar" column of the replay).
  - So no loss rule could have left S1. Its loss was a single burst, not
    a sustained rate.
- **n1r C3.** Its loss begins 587-714 s into the hold, in clusters of
  reports with 112-1,428 lost each.
  - The earliest candidate leave is L-B or L-C, at 587.1 s. That is
    152 s before the mild bar and 468 s after the hold-down first
    permits a decrease (t_permit, 118.8 s).
- **The clock of the bounds.** The pre-registration reads the bounds from
  t_permit, because the post-entry hold-down (about 126 s) alone exceeds
  both bounds when they are read from the stretch's start. The selection
  is NONE under either reading, so that interpretation does not decide
  it.

**What it means.** On the recorded 1080p series this link's loss arrives
as rare, large bursts: single reports of hundreds of packets. The
burst-count candidates fire on 2-5 of 13 series, never on S3, but never
early enough on the two named series. The four rules as pre-registered
do not give the rung a faster leave than the mild bar on the data there
is.

**The build that follows.**

- The entry threshold changes from 435 to 415, behind the same flag.
- No `rung_loss` trigger is built, and no `RUNG_LOSS` injection class:
  nothing was selected.
- **S1b** injects the entry and then the kept leave, `CAPACITY_MILD`. Its
  row "inject the loss leave's bar" is recorded as NOT APPLICABLE AS
  WORDED.

## 3. The build, tests, mutations, the stop rule (`../patches/C5-M5B_RUNG_ENTRY_AND_PS1_LOOK.md`)

- **The entry**: `RUNG_CLEAN_NEEDED` is now 415 (from 435). That is the
  only policy change: `companion_patch.diff`; pre/post hashes.
- **Tests**:
  - `test_adaptive_bitrate_live.py` **120 / 120**. The boundary is 415
    fires / 414 does not. A new test spreads 35 / 36 unclean reports
    through the window.
  - The shadow 21, nft harness 32, selector 14, source contract 7.
  - `test_c3_f1` 7/8: its pre-existing error, unchanged.
  - The shadow is byte-identical (`d66211b3…`).
- **Mutations: 14 of 14 caught** on the first run (`mutation_check.txt`).
  They are C5-M5's ten, with the threshold's now 415 → 414, 415 → 416,
  back to 435, `>=` → `>`, and the window not required full.
- **The stop rule: PASS**, 0 differences (`c5_m5b_stop_rule.txt`). With the
  flag absent, the built policy was compared against `5005615`'s closed
  controller (loaded from git) on 386 series, 137,766 reports and 69,006
  events. That is nine more series than C5-M5's 377: the live log now
  holds C5-M5's own sessions.

## 4. Sessions

Every session ran through `c5_m5b_hold.sh` (C5-M5's, plus `PRIVYHUB_PS1_LOOK`
among the flags it unsets, and the adopted PS1 files hashed at the start
and at the teardown).

### S1b, injection (`s1b/`, `s1b_rows.txt`, `s1b_score.txt`), 2026-10-03 16:28-16:34Z

- The flags were `TOP=1080p` and `INJECT=1` for the session only, on the
  built companion (entry 415).
- **PASSES on its rows**, with one row not applicable as worded:
  - **Entry by the policy path**: `INCREASE_1080P` at 90 s gave 7000 →
    12600, reason `increase_1080p`, acted.
  - **The leave**: no `rung_loss` was selected (§2), so there was no loss
    leave to inject. The KEPT leave `CAPACITY_MILD` was injected 140 s
    later and gave 12600 → 7000, reason `capacity_mild`, acted. The row
    "inject the loss leave's bar (not the mild bar)" is **NOT APPLICABLE
    AS WORDED**.
  - Exactly two transitions, and one SSRC change each.
  - `native-stream-status` and every SurfaceFlinger capture read
    1920×1080 after the entry and 1280×720 after the leave.
  - **Gaps 348 ms (entry) and 346 ms (leave)**, within 450.
  - `any_override` false at PLAYING and at the end; after BACK 7000 /
    1280×720.
- **Reported**: one stale drop in the second report after the entry, as in
  C5-M5's R0. 109 packets lost in the session. The six sized switches
  recorded so far cost 287-403 ms.

### S2b, the 30-min daytime hold (`s2b/`, `s2b_session_score.txt`), 16:44:39-17:14:39Z (12:44 EDT)

**NOT RUNG SHOWN. Link-drop recovery paused the game 4.4 min in. The new
threshold was then met, but the guards refused the entry for the rest of
the hold.**

- **16:49:02.8Z, recovery `desync_pause`**, trigger `controller_silence`
  (age 1,002 ms). The client's heartbeat that second arrived 3 s after
  the previous one instead of 2.
  - At 16:51:03.1Z recovery reached `gave_up_saved`. The attract loop
    stayed frozen until BACK.
  - No host request reached the companion around 16:49: the journal
    holds client heartbeats only. The helper's fake-run tests in that
    minute used stubbed `systemctl` / `curl` / `adb`.
- **The rung window was full and ≥ 415 clean from 16:59:42.9Z** (15.1 min,
  the first moment it was full).
  - **All 448 entry decisions** from then to the end were refused by
    `game_not_paused` + `recovery_playing`.
  - The best window was 432 of 450, but 25.6 of the 30 minutes were a
    paused, static picture. **Those clean counts are not a gameplay
    measurement.**
- **By the pre-registered rows**: no entry (the scorer's wording is "ENTRY
  NOT REACHED"), and **1 recovery cycle**. So it is not RUNG SHOWN. A row
  that failed is not re-run (the two-retry limit covers start failures
  only).
- **Client rows over the hold** were met:
  - spikes 91.6/min, fps 59.83, stale 1.79/min, underruns 1.19/min.
- **Loss and gap**: 20.3/min post-FEC (14/min before the pause, 21/min
  paused); max gap 248 ms. All at 7000, for 30.0 min.

### S3b, the 2-h night (`s3b/`, `s3b_session_score.txt`), 2026-10-04 05:00:56-07:00:56Z (01:00-03:00 EDT)

**DOES NOT WORK AS A RUNG by its pre-registered rows. The miss is the
client's spike row.** Every transition row holds.

- **One transition**: at **15.1 min** (05:16:00Z), 7000 → 12600,
  `increase_1080p`, by its own rule.
  - The window read **434 of 450**, one short of C5-M5's 435: the old
    threshold would not have entered here.
  - It was named, and spaced as the hold-downs allow.
- **No leave** in the remaining **104.9 min at 1080p**. No oscillation
  hold, and **0 recovery events**.
- **Per level** (C2 telemetry):

  | level | minutes | fps | stale / min | loss / min | largest per-report gap |
  | --- | ---: | ---: | ---: | ---: | ---: |
  | 7000 / 1280×720 | 15.1 | 60.35 | 0.13 | 3.05 | 72 ms |
  | 12600 / 1920×1080 | 104.9 | 60.18 | 0.70 | 2.82 | 74 ms |

- **The session** (decoder report): **spikes ≥ 20 ms 317.9/min (bar
  < 200): MISSED.**
  - The other rows were met: fps 59.97, stale 0.79/min, underruns
    1.09/min.
  - Loss was 2.87/min, with one SSRC change and no resyncs beyond it.
- **Why the spikes.** The 1080p decode on the onn runs at this spike rate
  in every recorded 1080p hold:
  - C5-M4's c_1x / c_2x / c_4x: 328.5 / 364.6 / 607.0 per min, against
    31.8-46.2 at 720p on the same sources;
  - C5-M1: 517-529.
  - 8.8 % of S3b's frames took ≥ 20 ms from receive to output (720p:
    0.7-0.9 %), nearly all in 20-40 ms. Spikes ≥ 50 ms numbered 248 in
    120 min, ≥ 250 ms 6.
  - C5-M5's S3 passed this row only because its 8.5 min at 1080p were
    diluted over 120 min (session 50.3/min).
  - The report holds spikes as session totals only, so a per-level split
    is not measured.
- **The max gap, 649 ms, is the entry switch itself** (the SSRC change at
  15.17 min; codec 198 ms, 8 frames in flight). It is the largest of the
  seven sized switches recorded (287-649 ms) and above the 450 ms the
  injection sessions are held to. Outside the switch the largest gap was
  177 ms.
- **Teardown**: FLAGS UNSET AND ABSENT, live, 7000 / 1280×720, ADOPTED PS1
  FILES BYTE-IDENTICAL, APK `de072762…835e` confirmed. A stale banner was
  cleared (0).

## 5. The look: levers, cost table, presets (`look_smoke/`, `look/`, `look_rung/`, `c5_m4_host_table_look.txt`, `c_full_rung_rung_score.txt`)

**The mechanism** (`companion/games/ps1_look.py`): a session options file
written from the adopted `.opt`, plus `global_core_options` /
`core_options_path` in that launch's session cfg (patch record).

- **The smoke** (`b_smoke2x`, 17:16Z): `measure-smoke-2x` sets internal
  resolution 2x.
  - RetroArch logged **"Initializing HW render (2048x2048)"** (4096² at
    the adopted 4x), so it loaded the session file.
  - The end record read removed: true, rewritten: {}.
  - The adopted files were byte-identical and the flag unset.
- **Every hold below** has:
  - its `PS1 look (C5-M5B):` line and the render target 4096² in the
    RetroArch log (`look_check_<hold>.txt`);
  - the session file removed at BACK, with **no key rewritten by
    RetroArch**: every value is one this build accepts;
  - the teardown's **ADOPTED PS1 FILES BYTE-IDENTICAL (8 of 8)** and
    FLAGS UNSET AND ABSENT.
- **xBR is offered.** `strings` missed it in the inventory only because
  it is three characters long.
- **MSAA is NOT OFFERED**: the core describes it as Vulkan-only, and this
  core runs OpenGL. No hold was run.

**The cost table.** C5-M4's method and bar. 5-min Tekken 3 attract holds on
the adopted 7000 stream, 17:18-18:21Z, in the pre-registered order.

| hold | lever | HOLDS 60 | RA fps | longest 256-fr ms (bar 4,278.7) | enc fps / dup+drop | GPU busy mean / p95 | GPU W | RA / enc % of a core | Tctl max | largest frame p50 / p90 B | cap hits s/min | client fps / stale / loss per min |
| --- | --- | --- | ---: | ---: | --- | --- | ---: | --- | ---: | --- | ---: | --- |
| `b_base4x` | the adopted config | **yes** | 59.999 | 4,272 | 60.0 / 0 | 21.4 / 26 | 23.0 | 33.0 / 35.9 | 60.1 | 47,088 / 86,340 | 6.2 | 59.77 / 3.5 / 26.4 |
| `b_dither_off` | dither disabled | **yes** | 59.999 | 4,273 | 60.0 / 0 | 22.3 / 27 | 23.3 | 32.5 / 35.7 | 59.9 | 47,889 / 86,950 | 6.6 | 59.82 / 4.3 / 8.1 |
| `b_filter_xbr` | xBR | **no** | **55.162** | **5,723** | 60.0 / 50 | **55.1 / 91** | 29.2 | 31.6 / 42.9 | 68.2 | 52,654 / 86,001 | 6.0 | 59.28 / 4.1 / 95.5 |
| `b_filter_sabr` | SABR | **yes** | 59.999 | 4,273 | 60.0 / 0 | 25.3 / 38 | 24.1 | 33.9 / 36.9 | 62.4 | 46,877 / 86,603 | 6.4 | 59.67 / 5.6 / 50.7 |
| `b_filter_bilinear` | bilinear | **yes** | 59.998 | 4,274 | 60.0 / 0 | **23.8 / 32** | 24.2 | 33.7 / 35.6 | 61.9 | 47,335 / 86,495 | 6.2 | 59.70 / 2.5 / 54.1 |
| `b_filter_3point` | 3-point | **yes** | 59.999 | 4,271 | 60.0 / 0 | 24.8 / 34 | 24.0 | 32.6 / 37.3 | 62.9 | 47,564 / 86,330 | 6.4 | 59.81 / 2.7 / 21.5 |
| `b_filter_jinc2` | JINC2 | **no** | **59.464** | **4,859** | 60.0 / 52 | **47.8 / 85** | 28.0 | 32.7 / 37.4 | 68.0 | 49,118 / 85,910 | 6.8 | 59.74 / 0.8 / 42.7 |
| `b_pgxp` | PGXP: memory only + texture + vertex | **yes** | 59.999 | 4,275 | 60.0 / 0 | 20.2 / 25 | 23.3 | **40.6** / 36.6 | 62.0 | 46,954 / 86,340 | 6.6 | 59.85 / 3.7 / 7.6 |
| `b_full` | **4x + bilinear + dither off + PGXP** | **yes** | 59.999 | 4,276 | 60.0 / 0 | 25.2 / 34 | 24.4 | 38.5 / 35.7 | 62.5 | 47,886 / 86,495 | 6.4 | 59.86 / 2.1 / 4.5 |

- **The best-cost filter**, by the pre-registered rule (the lowest GPU
  busy mean among the filters that held 60), is **bilinear (23.8 %)**.
  3-point read 24.8 % and SABR 25.3 %.
- **xBR and JINC2 miss.**
  - xBR: RetroArch fell to 55.2 fps, with GPU busy p95 91 %.
  - JINC2: 59.46 fps, with one 256-frame interval of 4,859 ms.
  - In both, the capture duplicated about 50 frames to keep the encoder
    at 60.
- **The costs that hold are small.**
  - Dither off is +0.9 GPU points.
  - The holding filters are +2.4-3.9.
  - PGXP is no GPU cost but **+7.6 points of a core for RetroArch** (the
    CPU-side geometry).
  - The full preset is +3.8 GPU points, +5.5 RetroArch and +1.4 W.
- **The encoder's job barely moves.** The per-second largest frame p50 is
  46.9-48.0 KB for every holding lever (52.7 KB under xBR), and cap hits
  6.2-6.8 s/min.
- The client's loss varies 4.5-95 per minute between holds, in no order
  that follows the levers (the adopted config 26.4, the full preset 4.5).
  It is most likely the link over the afternoon. What the host sends is
  flat: frame sizes, cap hits and 7.07-7.09 Mbit/s in every hold.
- **The full preset at the rung** (`c_full_rung`, 18:21-18:29Z):
  - flags `TOP=1080p` and `INJECT=1`; `INCREASE_1080P` at 90 s gave 7000
    → 12600 and 1920×1080 in the status; then 4.8 min at the rung.
  - **It does NOT hold 60.** One 256-frame interval read 4,283 ms
    (4,278.7 bar), 102 s after the entry: one dropped frame in 4.8 min.
    RetroArch read 59.998 fps.
  - R2 was met: encoder 60.0, 0 dup/drop.
  - Reported: GPU 27.4 / 35, 26.3 W, RetroArch 44.4 % and encoder 76.0 %
    of a core, Tctl 65.1. Largest frame p50 63,075 / p90 87,369 B, and
    cap hits 12.8 s/min. Client fps 60.6, stale 0, loss 19.5/min.
- The adopted `.opt` / `.cfg` were byte-identical at the start and the
  teardown of every session (`ADOPTED PS1 FILES BYTE-IDENTICAL`, 14 times).

**The presets** (`PRIVYHUB_PS1_LOOK=`; unset changes nothing anywhere):

- **`4x`**: the adopted config, the same as unset.
- **`remaster`**, OFFERED because the full preset held 60 at 720p. Its
  exact values:
  - `beetle_psx_hw_filter = "bilinear"`;
  - `beetle_psx_hw_dither_mode = "disabled"`;
  - `beetle_psx_hw_pgxp_mode = "memory only"`;
  - `beetle_psx_hw_pgxp_texture = "enabled"`;
  - `beetle_psx_hw_pgxp_vertex = "enabled"`;
  - and everything else as adopted, including internal resolution 4x.
- **`remaster-1080p`** in the helper: **NOT OFFERED.** The full preset
  missed HOLDS 60 at the rung by one interval, so the pre-registered rule
  holds it back. The helper refuses it
  (`ps1_look.REMASTER_AT_RUNG_OFFERED = False`).
  - The 1080p look stays available without the look flag, by C5-M5's
    hand steps (`TOP=1080p` + `INJECT=1`, `inject?class=INCREASE_1080P`).

**The helper** `tools/ps1_look.sh 4x | remaster | remaster-1080p [--attract]`:
fake-run tested (`tools/test_ps1_look_helper.py`, 8 / 8). Its stubbed
`systemctl`, `curl` and `adb` record every call. The tests check:

- the order: set the flags, restart, wait for PLAYING, inject for
  `-1080p` and see 1920×1080, wait for Enter, stop, unset every flag,
  restart, verify;
- that `4x` sets no flag;
- the `--attract` launch;
- the restore when PLAYING never comes;
- the refusals: not offered, and a flag already set.

The real run is the user's.

## 6. What it means — for the user

- **Used for real, the rung meets everything but one client row.** S3b
  sat at 1080p for 104.9 min with fps 60.2, stale 0.7/min, loss 2.8/min,
  no leave and no recovery.
  - But the onn's 1080p decode runs at about 300+ spikes ≥ 20 ms per
    minute, against < 200. Every 1080p hold on record shows the same.
  - So **a rung that is actually used misses the spike row by
    construction.** C5-M5's night only passed because it spent 8.5 min
    there.
  - Whether 20-40 ms frame-time jitter on 9 % of frames is visible on
    the TV is a picture question, and the user's.
  - The entry switch can cost up to 649 ms (S3b).
- **The entry is now reachable on this link.**
  - At 415 of 450 the rung's window fills and qualifies on 8 of the 10
    recorded real-input holds within 20 minutes; at 435 it was 0.
  - S2b showed the threshold met at 15.1 min. Its entry was blocked only
    because recovery had paused the game.
  - The cost: on those holds' own later 720p reports, 4-16 % were
    unclean after the replayed entry. That is a preview; the 1080p's own
    behaviour is S3b's.
- **The leave did not get faster, and the data say why.**
  - This link's 1080p loss is rare, large bursts, not a steady rate. The
    loss-count rules that would catch them (L-B: 300 in 30 s, 5 of 13
    series) do not leave the two named stretches early, because those
    stretches have no early loss.
  - So the rung keeps C5-M5's behaviour: it holds 1080p through bursts,
    and leaves on a sustained shortfall.
  - Whether a burst at 1080p looks worse than 720p is a picture question.
- **The look levers are cheap, except two filters.**
  - Dither off, bilinear / 3-point / SABR and PGXP all hold 60 at 720p
    on this host. The full `remaster` costs +3.8 GPU points and +5.5
    points of a core.
  - xBR and JINC2 do not hold 60.
  - At the rung, the full preset dropped one frame in 4.8 min. Like
    C5-M4's 8x, it is on the edge of the bar, not far over it.
- **A design point for the user.** The rung window counts clean reports
  while recovery holds the game paused (S2b). A paused picture is easy to
  stream, so such a window overstates the link.
  - Skipping reports while recovery is not PLAYING would be a one-line
    rule. It is not built: not pre-registered, and the user's call.
- **Nothing is adopted.**
  - `PRIVYHUB_ADAPTIVE_BITRATE_TOP` and `PRIVYHUB_PS1_LOOK` are off by
    default and nowhere set.
  - The adopted `.opt` / `.cfg` were byte-identical throughout.
  - Live is the default, and the APK is `de072762…835e`.

## Files (`c5_m5b_2026-10-03/`)

- **Pre-registration and selection:** `c5_m5b_preregistration.txt`
  (+ `.sha256`), `c5_m5b_selection.txt` (+ `.sha256`).
- **Replays:** `c5_m5b_replays.txt` / `.json` (`tools/c5_m5b_replay.py`),
  `c5_m5b_stop_rule.txt`.
- **Code:** `companion_patch.diff` (both changes and the new
  `ps1_look.py`), `pre_patch_sha256.txt`, `post_patch_sha256.txt`,
  `c5_m5b_mutation_check.sh`, `mutation_check.txt`.
- **Harness:**
  - `c5_m5b_hold.sh` and `c5_m5_run.sh` (C5-M5's), `c5_m5b_sessions.sh`;
  - `c5_m5b_s1_hook.sh`, `c5_m5b_rung_hook.sh`, `c5_m5b_look.sh`;
  - `t2_sample.py`, `c5_m4_sampler.py`, `c5_m4a_counter.sh`;
  - `adopted_ps1_sha256.txt` (the eight adopted PS1 files, checked at
    every start and teardown).
- **Sessions:**
  - `s1b/`, with `c5_m5_r0_score.py` → `s1b_score.*` and
    `c5_m5b_s1_score.py` → `s1b_rows.txt`;
  - `s2b/` and `s3b/`, with `c5_m5b_session_score.py` →
    `*_session_score.*`;
  - `sessions.log`.
- **The look:**
  - `look_smoke/`, `look/`, `look_rung/` (per hold: the hold files plus
    `look_check_<hold>.txt`, the RetroArch log's look line, the render
    target and the end record), `look.log`;
  - `c5_m4_host_table.py` → `c5_m4_host_table_look.{txt,json}`;
  - `c5_m5b_rung_score.py` → `c_full_rung_rung_score.{txt,json}`.
- `c5_m5b_final_state.sh` → `c5_m5b_final_state.txt`;
  `sha256_manifest.txt`; `redact_check.txt` (`c5_m5_redact_check.py`).

Nothing was adopted, and nothing was committed.
