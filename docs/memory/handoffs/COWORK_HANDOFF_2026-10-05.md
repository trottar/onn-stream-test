---
memory_schema: 1
as_of: 2026-10-05
status: COWORK HANDOFF — written by the Cowork chat that ran 2026-09-29 → 2026-10-05 (C3.L4 close through Phase C's close and Phase E's E1; E2 queued and running); the next Cowork chat reads this first, then CURRENT.md
---

# Cowork handoff, 2026-10-05

## How we work (the user's rules; keep every one)

- The user is **remote**: a Windows PC, PowerShell, SSH into the Linux
  host. They cannot paste into Claude Code from the PC. Cowork writes task
  handoffs into `docs/memory/handoffs/<NAME>_TASK.md` through the file
  bridge and the one-line prompt into `_cowork_prompt.txt` at the repo
  root. **Commit the prompt under a new local file name each time, then
  re-stage and `cmp` both files back from the host before telling the
  user it's ready.** The user types `Read _cowork_prompt.txt in the repo
  root and follow it as my prompt.` into Claude Code; later says "Code is
  done". Cowork then **verifies from the raw artifacts** (evidence dir,
  manifest `sha256sum -c` on the staged subset, pre-registration hashes,
  the score/summary JSONs recomputed where cheap, the tool copy against
  the evidence copy) before telling the user anything is true, and gives
  the commit line from the `logs/<task>_git_status.txt` Code writes.
  Commits and pushes are the user's; Code commits nothing.
- Hand steps: numbered, **one paste-ready block each**, where they are
  (**the PowerShell SSH window on the PC**), what they should see, and
  **what a reply must contain to count** (the Look-3 lesson: a `curl`
  that answered `refused` was taken as success because the steps did not
  say to check). Prefer a helper script Code wrote over multi-step hand
  routes. Nothing pasted from the user to Cowork; outputs go to files
  under `logs/` that Code reads. **Never ask for anything findable in
  `docs/memory/`.** Keep replies short; the user has said "Stop wasting
  my tokens" and "these instructions are not clear at all" — both were
  fair.
- **Never write down or ask for an IP, MAC, SSID, BSSID, ADB endpoint,
  serial or credential** — placeholders only. The Opal router is
  **read-only** over `ssh opal`; its width/channel are **hand changes by
  the user** (admin page → Wireless → 5G → Modify). ROMs/BIOS/keys/logs/
  savestates/APKs/the 4x clips stay out of git (all ignored). **Claude
  Code cannot run `nft` or real `sudo`**; the user runs
  `tools/c3_l4_nft_night.py` themselves. Pre-registered rules and
  selection criteria are written before data and never changed after.
  **Nothing perceptual is a gate** — the user's own look is recorded as
  their words and is what decides adoption. **Never hand the user a run
  to start while a Claude Code queue is running.** Nothing is adopted by
  Code without the user's explicit authorization in chat; when they give
  it, the task says so verbatim.
- Cowork's own mistakes this chat, so the next one doesn't repeat them:
  (1) read "1080p characterized ✓" as closed and pointed at Phase E — the
  user corrected it: Phase C exists to make higher rungs usable; (2)
  argued the 40 MHz width would help — it didn't (LINK-L2); say so
  plainly when a prediction fails; (3) hand steps without checks (above).

## Where things stand (2026-10-05)

- **Phase C CLOSED 2026-10-05** on the user's decisions. Live adaptive
  bitrate is **on by default** (systemd drop-in
  `privyhub-companion.service.d/adaptive.conf`,
  `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`; ladder 5000/5500/6000/7000 at
  720p; rules: queue/gap FALLBACK, strict capacity, the recovery
  backstop, `capacity_mild`, the blend increase; validated on three
  `nft` nights). **The PS1 source renders at 1920×1080 / Beetle PSX HW
  internal resolution 4x** (adopted 2026-10-01; per-core override +
  core options, the six per-title `.opt` copies carry the line). **APK
  `de072762…835e`** adopted (CL-B1 body-POST report). **The 1080p rung**
  is built behind `PRIVYHUB_ADAPTIVE_BITRATE_TOP=1080p` (entry ≥ 415 of
  450 clean from 7000; leave on the mild bar; the window skips reports
  while recovery is not PLAYING) — **NOT ADOPTED**: the user looked at
  real 1080p on the TV (verified in the logs) and saw no difference from
  4x/720p; cost ~1.8× wire rate, 287–649 ms switches, the onn's 1080p
  decode jitter (~300 spikes ≥ 20 ms/min vs < 200). The `remaster` look
  preset (bilinear + dither off + PGXP, behind `PRIVYHUB_PS1_LOOK`) —
  NOT ADOPTED ("a bit less smooth"). `tools/ps1_look.sh` works (`4x`,
  `remaster`, `--attract` fixed).
- **The link** (LINK-L1/L2): the adopted 720p's post-FEC loss row
  (< 10/min) is a coin flip at any hour on 80 MHz (3/6) and no better on
  40 MHz (2/6, back at 80 now); the 00:00–08:00 local window met on all
  four holds across both days. Loss is single-report bursts; neighbours
  on the secondaries were not the cause; retries don't predict it. The
  levers left are the user's (DFS channel 52–64, onn placement, a wired
  hop). Screening nights go overnight.
- **Phase E, E1 FROZEN** (`architecture/E1_WORKLOAD_SUITE.md`; runner
  `tools/e1_suite.py`, sampler `tools/e1_sampler.py`): 7 runnable rows,
  6/7 repeatable; ABSENT: NES/Genesis (no fixtures), camera, power
  meter, Live TV (no unattended start). E1's findings: **EPG grabs wreck
  the stream** (loss 2,300–2,800/min, ladder down to 5500, fps 54; the
  Node grabber child ~83 % of a core); **bsnes costs ~4 cores** and the
  SNES stream renders 58.5–58.9 fps; **the companion grows 37 → 172 MB
  at the first EPG grab**; idle 4 W, PS1 streamed 18–20 W, 1080p 23–27 W.
- **Running now: E2-S1** (`handoffs/E2-S1_WHOLE_SYSTEM_MEASUREMENTS_TASK.md`,
  6–7 h): the VOD row joins the suite by E1's rule (the drive is attached;
  the 1080p row stays, the user's call), then 20-min whole-system
  measurements on every row, the contended rows twice, per-thread /
  per-core instrumentation aligned on the EPG grab bodies and on bsnes,
  the companion's memory by mapping class, and an **ordered E3 candidate
  list** for the user to pick from. Nothing optimized or adopted.
- Last pushed: after the PREPUSH audit (11 commits, 316 MB, clean).
  Committed since: E1-S1. Baseline for E2: the E1-S1 commit.

## When the user says "Code is done" (E2-S1)

1. Verify from the raw files: `evidence/E2_S1_WHOLE_SYSTEM_<date>.md`,
   `e2_s1_<date>/` (pre-registration hash, manifest, the summaries behind
   the table, the aligned CONC/SNES frames), the E1 amendment for VOD,
   `logs/e2_s1_git_status.txt`, `CURRENT.md`.
2. Give the user the short version: the E2 table's headline numbers, the
   three answers (grabs, bsnes, memory), the E3 candidate list in
   impact order, and the commit line.
3. The user picks the first E3 item; write `E3-S1_<ITEM>_TASK.md` as the
   ROADMAP's loop (measured bottleneck → one narrow hypothesis → one
   change behind a flag or reversible → fresh benchmark on the frozen
   suite row → accept/reject by a pre-registered bar). One change per
   task. Likely first: the EPG grabber's contention with the stream
   (scheduling/priority or a pause-while-streaming policy), then the
   SNES core, then the companion's memory.

## Open, not blocking

The transport's max output gap (≤ 100 row, open since D-BASE);
`host_link` / CTRL-L1; thermal flag proposal; the client's slow-event
ring (~12 min at 7000); the controller log's chatty state lines; the
mild step's ~120 s bound; the onn's 1080p decode jitter (a client item);
the app's on-screen "720" is a constant (`NativeStreamActivity.kt`, a
one-line fix for a later APK); the pre-existing `test_c3_f1` ERROR
(a stale source-text search); NES/Genesis fixtures, a power meter, Live
TV's unattended start — the user's, when they like.
