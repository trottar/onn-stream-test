---
memory_schema: 1
as_of: 2026-10-15
status: TASK HANDOFF — SESSION B (runs in parallel with session A's QUEUE_2026-10-15.md; touches none of the stream, none of A's files). Two parts: E4-C1, the E4 close-out record and ROADMAP's E4/E7 lines; E5-S1, the capability model drafted from E4's measurements and the first capability probe of the reference host (host-only reads: /proc, lscpu, free, lsblk, vainfo, ffmpeg's encoders, ip link — no stream, no change). Nothing adopted; nothing committed
---

# Session B — E4-C1 (close-out) and E5-S1 (capability probe)

**Parallel-session rules.** Session A owns the stream, the companion
unit, `docs/KNOWN_ISSUES.md`, `CURRENT_HANDOFF.md` and **`CURRENT.md`**
— session B never writes those. Session B owns `docs/ROADMAP.md` (E4,
E5, E7 sections only), its two records and directories, and
`tools/capability_probe.py`. Session B starts no stream, launches no game,
restarts nothing, reads the companion's status endpoint only. Both
sessions see a dirty tree on purpose (baseline `7331184` +
E4-S1..S5C + A's work as it lands): **touch nothing of it**. B's
prompt file is `_cowork_prompt_b.txt`; B never writes `_cowork_prompt.txt`.
`logs/e4_c1_git_status.txt`, `logs/e5_s1_git_status.txt`. No sudo, no
nft, the Opal read-only, no addresses or identifiers; nothing fetched.

## Part 1 — E4-C1, the E4 close-out

Read: ROADMAP §E4 (the tables there), every `E4_S*` record, `E3_A2`,
`E3_A3B`, `E3_S6A` (the adoptions), `D_BASE_CLOSEOUT_…` (the loss row and
its reference), `LINK_L1` / `LINK_L2`, `E2_S1`.

Write `evidence/E4_CLOSEOUT_2026-10-15.md` — one record a reader can
take to E6 without opening another file:

1. **The reference** (E4-S1): the table per row (host CPU, stack cores,
   memory, watts, fps), and what changed since E2 and why.
2. **The floors**, both tables final: CPU-time per row and the stack
   (400 % today; 150 % with deferral), memory swap-off per row and the
   stack (streams ≤ 384M, META 1G, CONC 1.5G), each with its peak figures
   and the caveats (CPU-time ≠ slow-core; cgroup ≠ host).
3. **The recommended alpha**, two columns (today / with deferral), with
   the margins stated, and "optional higher tier" from C5's 1080p rung.
4. **Adopted in E3/E4** (live ladder, guide index, Snes9x, recovery v2;
   the SNES capture fix pending session A's E4-S5D — write "adopted
   2026-10-15" only if `e4_s5d_2026-10-15/state_at_end.json` exists and
   says five lines when you get there; else "in adoption, session A").
   **Not adopted and why**: grab priority, malloc_trim, direct node,
   frame/frame_spin pacing, grab network pacing, grab deferral (works on
   the host; stream quality unjudged — the link).
5. **The link**: every stream run's loss/min since 10-09 in one table
   against D-BASE's 8.4 reference; the statement that no run has met the
   loss row since; the stalled session of 10-10 (five days, no watch);
   the watch now running (session A) as the open item.
6. **E7's acceptance list**, item by item: met / not / where.

Then ROADMAP: §E4's status line and tables updated to this close-out (one
link to it), §E7's acceptance items marked, §E5 gets the status line from
Part 2. `logs/e4_c1_git_status.txt`.

## Part 2 — E5-S1, the capability model and the first probe

Read ROADMAP §E5 (the seven classes), E4-S2/S3B (the floors), C5
(stream profiles validated), E3-S4 (emulator tiers: Snes9x vs the
heavier core), E2-S1.

1. **`docs/CAPABILITY_MODEL.md`** (new): for each of E5's seven classes,
   what is measured, how (the command or file), the thresholds **taken
   from E4's numbers** (e.g. CPU: cores × speed class vs the 150 % /
   400 % floors; memory: free ≥ 1.5 GB for the stack with 8 GB system;
   encode: VAAPI H.264 present at 720p60 → the live ladder; emulator
   tiers: PS1 4x needs X, SNES needs Y from E3-S4/E4-S1; concurrency:
   grabs-with-stream needs 400 %, else deferral; network: the loss row)
   and **what each class enables or disables** in PrivyHub. Where E4
   has no number, say "not measured; E5-S2". No invented figures.
2. **`tools/capability_probe.py`** (new): reads the host and prints the
   seven classes as JSON — CPU model / cores / threads / max MHz
   (`lscpu`, `/proc/cpuinfo`), RAM and swap (`/proc/meminfo`), storage
   (`lsblk -J`, free space of the media root), GPU/iGPU (`lspci`-free:
   `/sys/class/drm`, `vainfo` if present), hardware encode/decode
   (`vainfo` profiles; `ffmpeg -hide_banner -encoders` filtered to
   vaapi), validated stream profiles (from the companion's profile table
   in the repo, not measured), emulator tiers (the cores present under
   RetroArch's core dir), concurrency headroom (cores vs the floors), the
   network interface's link speed and type (`/sys/class/net/*/speed`,
   wireless yes/no — **no MAC, no IP, no SSID printed**; the redactor
   over the output). Classification per `CAPABILITY_MODEL.md`, with the
   threshold each verdict used printed beside it.
3. **Run it once on the reference host** (host reads only; the stream
   may be live under session A — that is fine, say so):
   `evidence/E5_S1_CAPABILITY_PROBE_2026-10-15.md` + `e5_s1_2026-10-15/`
   (`probe.json`, the console, `redact_check.txt`, `manifest.sha256`).
   The reference host must classify as "known-good" on every class with
   a number; any class that does not is a model bug to fix, not a host
   finding. `logs/e5_s1_git_status.txt`.
4. ROADMAP §E5: status line "model DRAFTED, probe v1 runs on the
   reference; E5-S2: run on a second machine (the user's choice) and on
   the alpha candidate".

Stop there. Do not write `CURRENT.md`; leave
`docs/memory/handoffs/SESSION_B_DONE_2026-10-15.md` (ten lines: what was
written, what the probe said, the git status) for session A / the user.
