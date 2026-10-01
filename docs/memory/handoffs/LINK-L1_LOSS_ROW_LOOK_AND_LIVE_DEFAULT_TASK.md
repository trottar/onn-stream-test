---
memory_schema: 1
as_of: 2026-09-30
status: TASK HANDOFF — LINK-L1 then C3-L4-D1, one prompt, authorized by the user 2026-09-30 ("do the loss row look first and then the live default"). Part A: has the adopted 720p's post-FEC loss row moved, or is it time of day? — every adopted-profile hold since D-BASE tabled by hour with its air figures, the Opal's air view re-read (read-only), and six pre-registered 20-min holds spread over one day, adaptive OFF. Part B, only after A is recorded: live adaptive bitrate ON BY DEFAULT through the systemd drop-in named in the C3.L4 close, verified by an injection session and a 30-min hold, harness preflights updated, decision record written. Nothing committed
---

# LINK-L1 — the loss row, looked at; then C3-L4-D1 — live by default

Baseline commit `4e45a4f` (2026-09-30). Both parts run under
`handoffs/QUEUE_2026-09-29B.md`'s rules. Part A takes about a day; Part B
about an hour after it. **Part A's holds run with adaptive OFF** — they
measure the adopted profile as adopted — which is why B waits for A.

Read first: `investigations/ACTIVE.md` ("Open, for the user" under C5
follow-ups), `evidence/D_BASE_CLOSEOUT_2026-09-23.md`,
`evidence/O1_OPAL_AIR_VIEW_2026-09-21.md` (the read-only air view and its
tools), `evidence/D_BASE_P4_AIR_TELEMETRY_2026-09-21.md` and
`D_BASE_T2_STREAMING_ACCUMULATION_2026-09-23.md` (the T2 sampler and what
the radio counters can and cannot say), `evidence/C5_M2_1080P60_FOLLOWUP_2026-09-29.md`
(retries vs loss, and the correction), `evidence/C5_M3_LOW_RUNG_SCREENING_2026-09-29.md`,
`evidence/CL_B1_APK_ADOPTION_2026-09-30.md` (the newest paired holds),
`decisions/C3-L4_LIVE_AUTHORIZATION_2026-09-28.md` (the 2026-09-30 close:
"The persistent change", "What would show", "Turning it back off"),
`TOOLS.md` (the kill switches, the harness preflights), `CURRENT.md`.

## Part A — LINK-L1: the loss row

### A0. Pre-registration, written before any new data

`evidence/link_l1_2026-10-01/link_l1_preregistration.txt`, hashed. The
question: **on the adopted profile with adaptive off, does post-FEC
video loss < 10/min still hold, and if not, does it depend on the time of
day?** Rules, not to be changed after data:

- **The new holds.** Six 20-minute attract-mode holds on the adopted
  profile at 7000, adaptive off, `any_override` false, T2 on, the Opal's
  read-only counters sampled beside them, spaced about 4 hours apart over
  one day (≥ 30 min idle before each), so that every 4-hour block of the
  clock gets one. Record each hold's UTC start and the host's local hour
  (`timedatectl`). Score each by the close-out table; the loss row and the
  max output gap are the rows in question; the other rows are reported.
- **Classification of the day:**
  - **STILL MET** — ≥ 5 of 6 holds meet loss < 10/min;
  - **TIME OF DAY** — the holds that meet and the holds that miss
    separate cleanly by clock (every miss inside one contiguous ≤ 12-hour
    window, every meet outside it), with ≥ 2 meets and ≥ 2 misses;
  - **MOVED** — ≤ 1 of 6 meets;
  - **MIXED** — anything else; reported with the table, no conclusion
    drawn.
- **The history table** (A1) is descriptive; it does not enter the
  classification.
- **Air view.** Reported beside the holds; no rule on it.

### A1. The history, from the records already on disk

One table of **every ≥ 15-minute hold on the adopted profile with
adaptive off or silent since D-BASE closed** (the close-out's cold and
warm holds; S3; the L1/L2/N1/N2 holds — N2's was live but silent;
C5-M1/M2/M3's B holds; CL-B1's N1 and O1): date, UTC start, local hour,
minutes, loss/min, max gap, spikes, fps, and where T2 samples exist the
onn's link rate and RSSI, the Opal's signal, tx retries per hold, and
channel utilization. Then loss/min bucketed by local 4-hour block
(median, min, max, n) and by date. Say in one paragraph what the table
shows and what it cannot show (the sample is evenings-heavy; retries did
not predict loss across nights — C5-M2's correction).

### A2. The Opal's air view, read-only

As O1 did over `ssh opal` (read-only; nothing changed on the router):
the channel and width in use, channel utilization, the count of
neighbouring BSSIDs on the same channel and on the adjacent ones (**counts
only — no SSIDs, no BSSIDs written**), noise floor, the client's link
rate / MCS / RSSI, tx retries and rx drops, sampled once at the start of
each of the six holds and once between. Compare with O1's 2026-09-21
survey: what is on the channel now that was not then, as counts.

### A3. The six holds

C5's harness (`c5_m2_night.sh` / `c5_m2_run.sh` from `cl_b1_apk_2026-09-30/`,
which already expects the adopted APK `de072762…835e`), one hold per
block, adaptive off, no flags. T2 sampler on. Teardown after each: no
flags, stream 7000, no game, 0 banners.

### A4. The record

`evidence/LINK_L1_LOSS_ROW_2026-10-01.md`: the classification with its
rows; the history table and buckets; the air view then and now; and
**what each classification would mean for the user, as options, not a
decision**: STILL MET → nothing to do, the recent evenings were the
outliers; TIME OF DAY → schedule screening nights in the quiet window
(name it) and read INCONCLUSIVE (link) nights against it; MOVED → the
baseline needs re-establishing before any further arm is judged, and the
levers are the user's (the Opal's channel or width — read-only to Code;
the onn's placement; a wired hop), each with what the air view says about
it. `investigations/ACTIVE.md`: the item updated with the classification.
Evidence dir with manifest, `--check` (the redactor is
`evidence/h2_prep_2026-09-22/h2_prep_redact.py`).

## Part B — C3-L4-D1: live adaptive bitrate on by default

Only after A4 is written and A's flags are confirmed absent. **The user
authorized this on 2026-09-30.**

### B1. The change, exactly as the close describes

- Write `~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`
  with `[Service]` and `Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`;
  `systemctl --user daemon-reload && systemctl --user restart
  privyhub-companion`. The unit file itself is not edited. No
  `set-environment`.
- Verify and log: `systemctl --user cat privyhub-companion` lists the
  drop-in; the new MainPID's environ carries exactly one `PRIVYHUB_*`
  name, this one; `native-stream-status` reads `adaptive_bitrate.mode
  live`, `configured_mode live`, `acts true`; `any_override` false;
  profile adopted at 7000; the shadow untouched; `PRIVYHUB_FEC_SCHEME` and
  the profile selector absent.
- Keep a copy of the drop-in in the evidence dir and in `TOOLS.md`, with
  both kill switches beside it (delete the drop-in + daemon-reload +
  restart → off; `POST /plugins/games/adaptive-bitrate/disable` → shadow
  for one session).

### B2. The preflights that assumed "no PRIVYHUB_*" or "mode off"

Find every check in `tools/` (and its tests) that asserts zero
`PRIVYHUB_*` in the manager or the environ, or `adaptive_bitrate mode
off` at teardown — `c3_l4_nft_night.py` and its test at least — and make
each allow exactly this one name with the value `live` as the new
baseline, still refusing any other `PRIVYHUB_*` and still confirming
`set-environment` left nothing behind. The `nft` harness's own
`live_on` / teardown steps: it must no longer `unset-environment` the
mode into "off" at the end — the end state is the default (live). Tests
pass; the fake-sudo FULL run passes with the new end state. **Evidence
copies of older scripts are history, not edited**; `TOOLS.md` says so.

### B3. Proof it acts from the default, then a hold

- **Injection session** (as `C3-L4-L1` did, with
  `PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1` set for that session only and
  unset after): one injected decrease and its reset, on the default-live
  companion with no mode flag set. Pre-registered: one FALLBACK on the
  injection, `ssrc_change`, `any_override` false, BACK → 7000, the inject
  flag absent afterwards.
- **A 30-minute attract hold** on the default (no flags at all, T2 on).
  Pre-registered: **SILENT** if 0 transitions / would_act / hold /
  refused and the client rows (spikes, fps, stale, audio) met; the loss
  row and the gap reported against Part A's classification (if A said
  TIME OF DAY, say which window this hold fell in). Anything that fires
  on a clean link is recorded with its samples and the rule stays as
  approved — the user decides (the stop rule, unchanged).
- Teardown: no `set-environment` residue; mode live from the drop-in;
  stream 7000; no game; 0 banners; APK `de072762…835e` confirmed.

### B4. Record and memory

- `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`: the user's authorization
  (2026-09-30, "do the loss row look first and then the live default"),
  the drop-in verbatim, what the status shows, the kill switches, what
  the injection session and the hold showed, and the one open point
  carried over (the mild step's ~120 s bound).
- `evidence/C3_L4_D1_LIVE_DEFAULT_2026-10-01.md` and
  `c3_l4_d1_2026-10-01/` (manifest, `--check`).
- `CURRENT.md` Verified State "Installed": companion live by default
  through the drop-in, since 2026-10-01; `TOOLS.md`; `docs/ROADMAP.md` C3
  and the C7 row; `architecture/ADAPTIVE_BITRATE.md` (one line: default
  live since 2026-10-01); `investigations/ACTIVE.md`;
  `evidence/RUNTIME_VALIDATION.md`; `handoffs/CURRENT_HANDOFF.md`;
  `patches/PATCH_INDEX.md` if `tools/` changed; the daily files.
- `python3 tools/check_memory_health.py` healthy; the redactor `--check`
  over every text file written; `git status --short` and `git diff
  --stat` into `logs/link_l1_d1_git_status_2026-10-01.txt`.
- `CURRENT.md` last — Next Action 1: the user's commit (Cowork gives the
  line); 2: Part A's options if it was TIME OF DAY or MOVED, for the
  user; 3: Phase E per the ROADMAP, not started.

No addresses, MACs, SSIDs, BSSIDs, ADB endpoints, serials or credentials
anywhere; the Opal read-only; `nft` and real `sudo` never; the adopted
profile and APK throughout; the two retries limit; pre-registered rules
never tightened or loosened after data. Nothing committed.
