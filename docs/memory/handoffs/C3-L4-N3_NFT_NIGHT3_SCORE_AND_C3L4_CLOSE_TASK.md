---
memory_schema: 1
as_of: 2026-09-30
status: TASK HANDOFF — C3-L4-N3: (1) score the user's nft night 3 (run c3_l4_nft_night_20260930_131404Z, --only F1) against its pre-registration (sha256 cf0ce814…), read-only; (2) if WORKS UNDER LOSS, close C3.L4 — the decision record (live authorized as built; live stays behind its flag, off by default, adoption the user's call), docs/ROADMAP.md, architecture; (3) the C7 / D8 checkpoint record with git status written to a file for the user's commit; (4) CURRENT.md. No APK build, no session, nothing adopted, nothing committed
---

# C3-L4-N3 — night 3 scored, the C3.L4 close, the C7 / D8 checkpoint

**Why.** The user ran night 3 on 2026-09-30 (13:14-13:36Z, run dir
`logs/streaming/c3_l4_nft_night_20260930_131404Z/`, `--only F1`, the
pre-registration hashed to `cf0ce814…` as written, not amended). Cowork's
read of the raw files, to be confirmed or corrected by §1: the cap was
calibrated at 856 kbytes/s; the capacity FALLBACK 7000 → 5000 came 15.6 s
after the cap (one transition); INCREASE 5000 → 5500 at +222 s (111
reports after the FALLBACK), INCREASE 5500 → 6000 93 reports later;
`capacity_mild` met its bar 44 s into 6000 and was refused `hold_down`
twice (13:26:20, 13:27:22), then acted 6000 → 5500 at 13:27:38 — 122.5 s
after arriving at 6000 (61 reports; inside the pre-registered "no sooner
than 60 reports, within 150 s"); the next increase attempt at 13:30:45,
93 reports later and 14 s after the cap came off, was the third direction
change 496 s after the first (13:22:29) → **HOLD `oscillation` at 5500**
for the rest of the session. `rate_limited` never true; 0
`escalation_armed`; 0 recovery cycles (the recovery log holds only
`session_started` / `session_ended`); BACK reset the level to 7000;
teardown clean: no `privyhub_fault` table, flag absent from the manager
and the environ, stream 7000, no game, 0 banners; APK `f31b1c18…8ae7` at
preflight. This is the shape night 3 was pre-registered to show.

Read first: the run dir (every file), its `preregistration.txt`,
`evidence/C3_L4_N2_MILD_CAPACITY_2026-09-29.md` (§5 the rows and the
flagged deviation), `evidence/C3_L4_NFT_NIGHT2_2026-09-29.md` (the record
shape; reuse `c3_l4_n2_2026-09-29/c3_l4_n2_score_night2.py` where it fits),
`decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md`, `docs/ROADMAP.md`
(C3, C7, D8, "Checkpoint discipline"), `architecture/ADAPTIVE_BITRATE.md`,
`CURRENT.md`, `TOOLS.md`.

## 1. Score night 3 (read-only, first)

Against the night-3 pre-registration row by row — F1a, F1b, F1c, F1d,
F1e, F1f, F1g, the all-sessions rows — from the run dir only. For each
row: met / not met / not applicable, with the sample rows that say why.
Expected (confirm or correct): F1a MET (+15.6 s, one `ssrc_change`); F1b
MET on the HOLD branch — name each transition, its spacing in reports,
and the mild step's delay from arriving at 6000 (the two `hold_down`
refusals are the rule working as built, not failures); F1c MET (4
transitions inside one 10-min window, allowed; no two closer than the
hold-down table; no ramp); F1d MET (nothing after removal because HOLD;
BACK → 7000); F1e MET (backstop did not fire); F1f MET (0 cycles); F1g
reported (time at 6000 under the cap: 13:25:37 → 13:27:38, its per-report
figures — Cowork's quick read: fps median ~59.7 over the whole window,
lost median ~52 per report; the bar was met in the last 5 from 44 s on;
give the real table). Classification per the pre-registration. Also
state, as in night 2, whether the `session_ended_reset` rows (5) are the
harmless duplicates and whether the status `level` after BACK now reads
7000 (the N2 fix). Close-out rows per session reported only.

Write `evidence/C3_L4_NFT_NIGHT3_2026-09-30.md`; copy the run dir into
`evidence/c3_l4_nft_night3_2026-09-30/` (redacted, `--check`,
`source_sha256_before_copy.txt`, `sha256_manifest.txt`, `README.txt`); the
scorer and its output under `evidence/c3_l4_n3_2026-09-30/`.

## 2. If night 3 is WORKS UNDER LOSS: close C3.L4

Only on that classification; otherwise stop after §1, record what did
not hold, and leave the rest of this file for the user.

- **Decision record**: append to
  `decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md` the close, dated
  2026-09-30: `C3.L4` live is **VALIDATED UNDER REAL LOSS on three `nft`
  nights** (night 1 NOT — led to the capacity trigger and the backstop;
  night 2 WORKS UNDER LOSS — led to `capacity_mild`; night 3 WORKS UNDER
  LOSS with the pre-registered HOLD shape). The controller **as built** is
  what is authorized: the queue/gap FALLBACK, strict capacity, the
  recovery-escalation backstop, `capacity_mild`, the queue ROUTINE, the
  user's blend increase, the hold-downs, the oscillation guard, the rate
  limit, the guards; recovery unchanged (`C3-F1` level-preserving); the
  shadow byte-identical. **Live stays behind
  `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, off by default.** Making it the
  default is an adoption and the user's call: state in one paragraph the
  exact change that would do it (where the mode is read, the unit / env
  file it would go in, what `any_override` and the status would show, and
  how it is turned back off), and do not make it. Record the one open
  point as open: the mild step's delay is bounded by the 60-report
  reversal hold-down (~120 s), not the 90 s once expected; shortening it
  is a rule change for the user to ask for or not.
- **`docs/ROADMAP.md`**: the C3 section (`C3.L4` closed: validated under
  real loss, live behind its flag, adoption pending the user) and the C7
  table row "adaptive bitrate runtime validated" → ✓ with the three night
  records and the decision. Keep the C3 success-criteria list and say
  which record shows each item (bounded min/max; fast decrease / slow
  increase; hysteresis and hold-down; no oscillation — the guard shown
  on night 3; reason codes; safe fallback; latency before quality).
- **`architecture/ADAPTIVE_BITRATE.md`**: the rules as built, in one
  table (class, trigger, bar, target, precedence, hold-downs), and the
  three nights' outcomes in one paragraph. No new behaviour.
- `investigations/ACTIVE.md`: close the C3.L4 item; keep the open,
  non-blocking items (max output gap; `host_link`; thermal; `CTRL-L1`;
  the client's slow-event ring; the controller log's chatty state lines;
  the ROUTINE hold-down length as the user's open point).

## 3. The C7 / D8 checkpoint record

`evidence/C7_D8_CHECKPOINT_2026-09-30.md`: every C7 acceptance item and
every D8 acceptance item with its status and the record it rests on (the
C7 table in `ROADMAP.md` is the starting point; correct anything it
overstates). "clean checkpoint/push" stays **pending the user's commit** —
Code commits nothing. For that commit:

- run `python3 tools/check_memory_health.py` and
  `python3 tools/h2_prep_redact.py --check` over every text file this task
  wrote; fix what they flag; put their final output in the record;
- write `git status --short` and `git diff --stat` (read-only git) to
  `logs/c7_d8_git_status_2026-09-30.txt`, and list in the record anything
  in the working tree that must **not** be committed (ROMs, saves,
  savestates, keys, logs, the `runtime/c5_m3/` clips, anything
  `.gitignore` misses) with the reason; Cowork gives the user the commit
  line from that file.

Not in this task: **no APK build or install** (the next adopted APK with
`CL-B1` is an adoption — a separate task once the user says); **no
picture check** (no 1080p or low-rung arm reached CAPABLE; none is owed);
no session of any kind; `nft` and real `sudo` never.

## 4. Record and memory

`evidence/C3_L4_NFT_NIGHT3_2026-09-30.md`; the evidence dirs with
manifests; the decision record (append); `docs/ROADMAP.md`;
`architecture/ADAPTIVE_BITRATE.md`; `investigations/ACTIVE.md`;
`evidence/C7_D8_CHECKPOINT_2026-09-30.md`; `evidence/RUNTIME_VALIDATION.md`
(night 3 and the close classified); `TOOLS.md` if anything changed;
the daily file; `CURRENT.md` at the very end — Active Objective: Phase C
`C3.L4` closed (validated under real loss; live behind its flag); Next
Action 1: **the user's commit** (Cowork gives the line from
`logs/c7_d8_git_status_2026-09-30.txt`); 2: the user's two decisions — turn
live on by default or not; the `CL-B1` APK build and install or not; 3:
what `docs/ROADMAP.md` says follows C7 / D8 on the Linux order, in one
line, without starting it. Adopted profile and APK throughout; flags and
selector unset and absent; no addresses, MACs, SSIDs, ADB endpoints,
serials or credentials anywhere. Nothing adopted. Nothing committed.
