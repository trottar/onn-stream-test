---
memory_schema: 1
as_of: 2026-11-09
status: H5 CHECKPOINT (session A, 2026-11-09, on the user's "Close H" at HOME-11): Phase H CLOSED — 7 acceptance lines met, 2 met with stated gaps (resource costs, the remote regression), 1 the user's (the commit). Open items listed below. H6 (feature parity) OPEN, waiting for the user's ranking. Nothing adopted; nothing committed
---

# H5 — the extended-emulation checkpoint (2026-11-09)

The user's word: **"Close H"** (HOME-11, `HOME_11_DISC_SAFE_2026-11-09.md`). Each §H5 acceptance line (`docs/ROADMAP.md`
§H5) is read from its own record below, not from B's sketch (`handoffs/SESSION_B_DONE_2026-11-09AA.md`). The state it
closes on: **eighteen lines** (G-A14 PS2, G-A15 N64, G-A16 GameCube among them), APK **`85220f99…` CONFIRMED**
(HOME-11), the companion and `privyhub-diag`. Paths are under `docs/memory/` unless they start with `docs/`. T-labels
only; no title, serial, game id or path.

## The acceptance lines

| §H5 line | where it stands | read from | result |
| --- | --- | --- | --- |
| **Content import pipeline validated** | IMPORT-1 ran slice 1a for real: 72 PS1 candidates (66 cue, 6 m3u), all 72 duplicates, placed 0 / failed 0, the drive's listing hash the same after, idempotent on a second run. B58 (slice 1b: plain folders, SNES / NES / Genesis header checks, the journal) built and tested on fixtures, behind `PRIVYHUB_IMPORT=1`, not adopted. The `.m3u` sets applied (6 sets / 14 discs, "PlayStation (72)" from "(80)", C33 met). **IMPORT-2 (NES / Genesis) deferred by the user**: "I don't really care about the NES and Genesis…" | `IMPORT_1_2026-11-08.md` :39-53; `B58_IMPORT_SLICE_1B_2026-11-08.md` :7-19; `HOME_9_GC_2026-11-09.md` :46-59; `docs/ROADMAP.md` §H0 (IMPORT-2 DEFERRED) | **MET** for PS1 and the in-place lists; NES / Genesis deferred by the user |
| **No project-supplied ROM / ISO / BIOS** | PS1: no BIOS on the drive, the core's built-in OpenBIOS. PS2: the user's own BIOS on the drive ("BIOS Found"), copied once to the hub, never fetched. GameCube: no BIOS needed (Dolphin HLE, `SkipIPL`); an IPL only if the user supplies one. N64: the core needs none; **no record states an N64 BIOS line** (an absence, not a statement). Every game is the user's, read in place or imported from the user's drive | `IMPORT_1_2026-11-08.md` :28-30, :70; `H3_P1_PS2_PROBE_2026-11-07.md` :20, :37; `B49_PS2_LAUNCH_KIND_2026-11-08.md` :68; `architecture/H2_P1_GAMECUBE_PROBE_DESIGN_2026-11-08.md` :81-82; `H2_P1_GAMECUBE_PROBE_2026-11-09.md` :48 | **MET** |
| **N64 characterised** | Play C21, save / load C22 met (HOME-7); C23 (freeze, dead buttons) not met → fixed at HOME-8 (C24 buttons, C25 the Home hold); the hitch bar answered at HOME-9 (C30 Continue 4 ms, C32 bar 0.0 vs PS1 0.0). Adopted G-A15 (`PRIVYHUB_N64=1`). Recovery is a plain resume (no state save into a running core) | `HOME_7_HOLD_TO_JOIN_N64_2026-11-08.md` :53-55; `HOME_8_N64_FIXES_2026-11-08.md` :39-43; `HOME_9_GC_2026-11-09.md` :56-58 | **MET** |
| **GameCube characterised** | H2-P1: both probe titles at full speed, hotkey pause, a state in 0.21 s. HOME-9: launch → picture 10.2 s (C34), SAVE / LOAD after a relaunch and the Home hold, ok 0.9 s (C35), the bar 0.0, 60 / 60 / 60 (C36). Adopted G-A16 (`PRIVYHUB_GAMECUBE=1`) | `H2_P1_GAMECUBE_PROBE_2026-11-09.md` :70-71; `HOME_9_GC_2026-11-09.md` :60-62, :76-91 | **MET** |
| **PS2 characterised** | H3-P2: hitches 0.0 / 6.2 per 10 min, pause 0.04-0.16 s, "It felt really good to play". HOME-4+: two players (C11). HOME-6: SAVE 0.5 s, LOAD `picture ok 0.9s`, 0 TLB Miss (C12'', C14). HOME-7: the hold through PINE (C18), the relaunch 12148 ms (C20). Adopted G-A14 (`PRIVYHUB_PS2=1`) | `H3_P2_PS2_STREAMED_2026-11-08.md` :60-65; `HOME_4_PLUS_2026-11-08.md` :53; `HOME_6_PS2_LOAD_2026-11-08.md` :39-40, :82-85; `HOME_7_…` :50-51 | **MET** (a heavy title's long play: the caveat below) |
| **Incremental resource costs vs Phase F** | **Phase F has not started** (`docs/ROADMAP.md`: its optimisation work ran as Phase E), so the reference is E4's close-out. The table below. **Gaps:** no power reading for any extended system (no power meter on the hub), no N64 GPU reading, no host-% row like-for-like with E4's | `E4_CLOSEOUT_2026-10-15.md` :38-44; the records in the table | **MET with gaps stated** |
| **Local validation, then regression over the Phase G remote contract** where representative hardware is available | Every N64 / GameCube / PS2 sitting was on the LAN (PS2-R1 reads the path `lan`). **No extended-system game has been played off-site or over the overlay**; the trip keeper ended 2026-11-01, before the adoptions; G9 deferred the travel router and the handheld. What was re-run: `test_e1_remote` (21 OK) at each adoption, a unit test, not a remote session | `PS2_R1_LONG_SESSION_2026-11-08.md` :36; `G9_CHECKPOINT_2026-11-07.md` :35; `HOME_6_…` :73; `HOME_9_GC_…` :84 | **Not re-run remotely**; the remote contract is the system-independent G lines, unchanged. Carried open |
| **Compatibility claims limited to tested evidence** | H4's decision on the user's "Keep all games": CORE NES / SNES / Genesis / PS1; EXTENDED + N64; ENHANCED + PS2 + GameCube, every title on the drive offered. **The caveat beside PS2:** a heavy title's long play is unread. Nuance: H3-P1 read the heavy title T2 at its menu only; H3-P2 played it 6.4 min (6.2 hitches / 10 min); PS2-R1's 20.3-min session has no light / heavy class | `docs/ROADMAP.md` §H4; `H3_P1_…` :49; `H3_P2_…` :12, :61, :67; `PS2_R1_…` :4 | **MET** (the caveat written beside the claim) |
| **Base Core hardware independent** | No hardware change in any Phase H record: the same iGPU (RADV RENOIR / Vega 7) throughout; PCSX2 and Dolphin are AppImages, nothing installed system-wide (an absence, not a stated line) | `H2_P1_…` :4, :51; `H3_P1_…` :4; `B59_N64_LAUNCH_2026-11-08.md` :33 | **MET** |
| **Clean checkpoint / push** | The user's commit of HOME-11 with this checkpoint (`logs/home11_git_status.txt`) | — | **The user's** |

## Resource costs beside E4's reference

| row | CPU | GPU | Tctl °C | socket W | source |
| --- | --- | --- | --- | --- | --- |
| E4 IDLE | 1.2 % host | — | — | 5.3 | `E4_CLOSEOUT_2026-10-15.md` :38 |
| E4 PS1-STREAM | 10.9 % host; 95 % of a core (companion + RetroArch + encoder) | — | 61 | 20.1 | :40 |
| E4 SNES-STREAM | 7.4 % host; 60 % of a core | — | 49 | 15.2 | :44 |
| PS2 H3-P1 T1 / T2 (menu) | per-core max 64 / 67 %; EE 31 / 62, 28 / 39 % | median 17 / 23 % | 56 / 62.5 | — | `H3_P1_…` :42 |
| PS2 H3-P2 streamed | no core ≥ 90 % for more than 1 s | 24 / 30 % | 65.4 / 63.6 | — | `H3_P2_…` :63 |
| PS2 HOME-6 T1 | EE mean 42.3 %, max 49.0 %, p95 47.0 % of a core; host ~11 % | — | — | — | `HOME_6_…` :49, :53-54 |
| GameCube H2-P1 | CPU thread max 38-47 % of a core | ≤ 19 % | ≤ 61.5 | — | `H2_P1_…` :117, :174, :181-182 |
| N64 HOME-8 | RetroArch 12-17 % | — | — | — | `HOME_8_…` :40, :43 |

Read: every extended system runs with margin on the same hub (the busiest, PS2's EE thread, under half a core on the
light title, its heavy title's menu peaking at 62 %); none was measured for power.

## What stays open (carried, not blocking the close)

- **A heavy PS2 title's long play** (`HOME_6_…` :57-58; `docs/ROADMAP.md` §H4's caveat).
- **The drive read-ahead**, unbuilt: PS2-R1 found no drive cause in play, but could not rule it out entirely
  (PCSX2's log was overwritten); H3-P2's 643-ms and H3-P1's 552-ms drive reads are on record (`PS2_R1_…` :146-160).
- **NES / Genesis import** deferred by the user (IMPORT-2 written, not run).
- **A real "insert disc N" prompt** untested (no save near one); B74's warning covers an unprompted change
  (`HOME_11_DISC_SAFE_2026-11-09.md`).
- **The remote regression** of N64 / GameCube / PS2 (above), and their power cost.
- **H6, feature parity** (artwork, custom controls, cheats, then mods / disc change / "NEW"): B75's matrix
  `architecture/H6_PARITY_MATRIX_2026-11-09.md`, waiting for the user's ranking.

## Applied where

`docs/ROADMAP.md` §H5 (a CLOSED block after the acceptance list) and §H6 (opened as a pointer to B75's matrix);
§H0 HOME-11's lines; `docs/KNOWN_ISSUES.md` HOME-11's line and section (insertions only); `docs/memory/CURRENT.md`
(Active Objective: Phase H CLOSED, H6 open; Next Action: the user's ranking). **Not edited:** `docs/ROADMAP.md` §0's
marker and the phase table (outside HOME-11's list); the README.
