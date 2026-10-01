---
memory_schema: 1
as_of: 2026-10-01
status: TASK HANDOFF — C5-M4A: apply the PS1 source config C5-M4 proposed — the Beetle PSX HW core override (1920×1080 fullscreen on the headless display) and internal resolution 4x in the base core options and in every per-title .opt copy — authorized by the user 2026-10-01 ("Yes apply the 4x config"). Verify through the companion's own launch path, show the 2D cores untouched, run the PS1 rows of the D7 regression, one 20-min hold on the adopted 7000 stream carrying the 4x source, write the decision record and the revert steps. No 1080p arm, no nights, no Opal change, nothing else adopted
---

# C5-M4A — the PS1 source at 4x, adopted

**Why.** C5-M4 Part 1 measured it: 4x holds 60 fps through the companion
at GPU 21 % and +1 W; the 7000 stream carrying the 4x source scores
+0.035 content SSIM on 3D at the same link cost (no new ≥ 80-packet
frames, cap hits 6-7 s/min). **The user adopted it on 2026-10-01.** This
task applies exactly the proposal in
`evidence/c5_m4_2026-10-01/c5_m4_proposed_source_config.diff`, plus the
per-title copies, and verifies it. Dither mode, texture filter, PGXP,
MSAA, Vulkan and 8x stay as they are: not measured, not proposed; they are
the user's look later.

Read first: `evidence/C5_M4_PS1_NATIVE_1080P_SOURCE_2026-10-01.md` §1
(the keys and where each is set; the six titles with their own `.opt`
copy; the multitap path that seeds the copy and never re-reads the base)
and §4 (the proposal, applying and reverting), `c5_m4_2026-10-01/proposal/`,
`prestate_sha256.txt`, `PS1_MULTITAP_CORE_OPTIONS_AUDIT_2026-09-10.md` and
`D087*`/`D088*` (how the multitap config path writes per-title options —
the 4x line must survive it), `D7_R1_LINUX_REGRESSION_2026-09-25.md` and
`tools/d7_regression.py` (the PS1 rows), `TOOLS.md`, `CURRENT.md`. Live
adaptive bitrate is the default; the APK is `de072762…835e`.

## 1. Pre-registration, before the change

`evidence/c5_m4a_2026-10-01/c5_m4a_preregistration.txt`, hashed. ADOPTED
HOLDS if every row below holds; otherwise revert and record:

- **V1** With no game running, the override file is written and the
  `.opt` line changed in the base file **and in each of the six per-title
  copies** (sha256 of every file before and after; the backups kept in
  the evidence dir). Nothing else in `~/.config/retroarch/` changes
  (`prestate`-style listing before and after, diffed).
- **V2** Launched **through the companion** (the games plugin's own path,
  as a user would: the attract title and one multitap title), the
  RetroArch window is 1920×1080 and the log's render target is 4096²;
  `privyhub-session.cfg` as the companion regenerates it does not
  override `video_fullscreen`; the multitap path leaves the 4x line in
  place after its own write (hash the `.opt` after the session).
- **V3** One SNES title and one other 2D core launched the same way:
  window size and `.opt` unchanged from before (hashes equal).
- **V4** `tools/d7_regression.py`, the PS1 rows (launch, resume, stop,
  the multitap row if scripted): PASS as on 2026-09-25.
- **V5** A 20-min attract hold on the adopted 7000 stream (no flags; live
  by default; T2 on): RetroArch holds 60 by C5-M4's R1 and the capture by
  R2; client rows spikes < 200, fps ≥ 59.5, stale < 20, underruns < 5
  met; loss and max gap **reported** against LINK-L1 (MIXED — not a
  gate); per-second largest frame p50/p90, cap hits s/min and ≥ 80-packet
  frames/min reported beside C5-M4's b_4x; 0 controller transitions
  expected, recorded either way (the stop rule stands).
- **V6** At the end: no game, stream 7000, `any_override` false, selector
  absent, live default intact, APK confirmed, the new config files hashed
  as the adopted PS1 source config.

## 2. Apply, in that order

V1 → V2 → V3 → V4 → V5 → V6. Any failed row: restore every file from the
backups, hash-verify the restore, record which row and why, stop.

## 3. If ADOPTED

- `decisions/C5-M4_PS1_4X_SOURCE_ADOPTION_2026-10-01.md`: the user's
  words, what changed (file by file, with hashes), what it does and does
  not change (the 2D cores; the companion argv; the stream profile), the
  measured cost (C5-M4 §4), the revert steps verbatim, and the open
  picture items (dither mode first).
- `TOOLS.md`: "the adopted PS1 source config" with its hashes and the
  revert; a note that a new PS1 title's seeded `.opt` copy inherits the
  base, so 4x, and that any older copy must carry the line.
- `CURRENT.md` Verified State: the PS1 source at 1920×1080 / 4x since
  2026-10-01; Installed unchanged otherwise. `docs/ROADMAP.md` C5: the
  quick win adopted, the rung next. `investigations/ACTIVE.md`;
  `evidence/RUNTIME_VALIDATION.md`; `handoffs/CURRENT_HANDOFF.md`; the
  daily file.
- The record `evidence/C5_M4A_PS1_4X_SOURCE_ADOPTION_2026-10-01.md`,
  evidence dir with manifest and the redactor `--check`
  (`evidence/h2_prep_2026-09-22/h2_prep_redact.py`);
  `check_memory_health.py` healthy; `git status --short` and `git diff
  --stat` to `logs/c5_m4a_git_status.txt`; `CURRENT.md` last — Next
  Action 1: the user's commit; 2: the user's 40 MHz change on the Opal,
  then the LINK-L1 re-run (same rule, six holds) on the next prompt; 3:
  Part 2, the 1080p rung, after that; the user's picture look at 4x
  (dither mode) whenever they like, TV only, nothing perceptual as a
  gate.

No 1080p arm or selector, no `nft`, no real `sudo`, the Opal read-only,
no addresses, MACs, SSIDs, ADB endpoints, serials or credentials
anywhere. Nothing else adopted. Nothing committed.
