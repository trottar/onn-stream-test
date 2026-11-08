---
memory_schema: 1
as_of: 2026-11-08
status: PS2-R1 READ (session B, read-only, 2026-11-08 ~16:25-16:50Z; A's HOME-5 files present and untouched). The user's PS2 play between the HOME-4+ close (~08:30Z) and HOME-5's start (16:08Z) is ONE session of title P2, 20.3 min (08:36:10-08:56:28Z), plus, beside it as context, HOME-4+'s own PS2 cells of title P1 (six sessions, 20.2 min, 07:34-08:07Z). 1 hitch second in the window (network), 0.5 / 10 min. Nothing restarted, adopted or committed; the keeper only read
---

# PS2-R1: the long PS2 session, read

Task: `handoffs/PS2-R1_LONG_SESSION_READ_TASK.md`. Everything is in `ps2_r1_2026-11-08/`:
- `sessions.csv`: every PS2 session 07:30-09:00Z, numbers only;
- `session7_output_gaps.csv`: the client's 16 longest output gaps in the window session, with the encoder's frames and
  the loss around each;
- `views/pm60s_085527Z.md`: ±60 s around the one hitch second;
- `reference.json`: the PS1 LAN reference and H3-P2's T1 / T2;
- `LABELS.txt`, `redact_check.txt`, `manifest.sha256`.

The tool's output is `reads/diag_ps2_20261108T162747Z.md` (`tools/diag_read.py "2026-11-08 07:30..09:00" --live`,
the tree's code with B50's PS2 label; the pad hashes and the movie's id replaced by labels). Times are UTC. Titles are
P1 / P2, pads padA / padB.

The user's words: "I had a prolonged ps2 session last night playing. Ran really well with only a few stutters."

## 0. The evening

**What was played.** In the task's window (after the HOME-4+ close ~08:30Z, before HOME-5's 16:08Z) the hub ran **one
PS2 launch**:
- **title P2**, launched 08:36:03, streamed **08:36:10 → 08:56:28 (20.3 min)**, exited 08:57:53;
- one player (P1 = padA); **player 2 did not play** (slot 1: 0 pad changes).

Just before the close, HOME-4+'s own PS2 cells (C11 / C12) ran **title P1** on four launches, six stream sessions,
07:34 → 08:07Z, **20.2 min**, two players. The user's "last night" (US Eastern, ~02:30-04:00 local) covers both. They
are given beside the window session, marked context. **Together: 40.5 min of PS2 in seven sessions.** Nothing else was
streamed in the window. The 08:09-08:14Z rows are a movie (M1), not a game.

**Every session:**
- path `lan`; 5 GHz (read by HOME-4+ at its start and by HOME-5 at its start; the logs carry no band);
- the APK `cfe0211c…` (installed and CONFIRMED by HOME-4+, read back by HOME-5, nothing installed between);
- **the rung 7000 from start to end** (start = median = minimum, no ladder transition);
- RSSI −67…−64 dBm;
- 0 stall-signal rows, 0 uplink silences, 0 client self-restarts, 0 encoder restarts, 0 step-in-place splices, 0
  `surface_lost`;
- every exit `sigterm` (0.5-0.6 s) after the user's Back + Stop.

## 1. The session table (G4-S4's form; `sessions.csv`)

| # | scope | title | start → end | min | players chosen / claims | ports | rung start / med / min | pauses in play (Back → Resume) | saves / loads | hitch s (R/C/G/L) | per 10 min | loss post-FEC | fps med (min) | underruns / starvation | pad changes slot 0 / 1 | exit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | context | P1 | 07:34:08 → 07:37:48 | 3.7 | 2 / 2 | 2, no tap (metadata) | 7000 / 7000 / 7000 | — | 0 / 0 | 0 | 0.0 | 15 | 60.0 (58.1) | 21 / 0 | 16 / 2 | Back (the same launch resumed) |
| 2 | context | P1 | 07:38:03 → 07:40:55 | 2.9 | 2 / 2 | 2, no tap (metadata) | 7000 ×3 | 1 (14.2 s, hotkey) | 0 / 0 | 0 | 0.0 | 4 | 60.0 (57.7) | 4 / 1 | 665 / 12 | sigterm 0.6 s |
| 3 | context | P1 | 07:50:57 → 07:57:47 | 6.8 | 2 / 2 | 2, no tap (launch) | 7000 ×3 | — | 0 / 0 | 0 | 0.0 | 13 | 60.0 (58.2) | 23 / 1 | 435 / 159 | sigterm 0.6 s |
| 4 | context | P1 | 07:59:13 → 08:00:28 | 1.2 | 2 / 2 | 2, no tap (launch) | 7000 ×3 | — | 0 / 0 | 0 | 0.0 | 5 | 60.0 (58.1) | 5 / 0 | 30 / 2 | Back (resumed) |
| 5 | context | P1 | 08:01:37 → 08:04:28 | 2.9 | 2 / 2 | 2, no tap (launch) | 7000 ×3 | 1 (69.3 s, hotkey) | 0 / 0 | 0 | 0.0 | 19 | 60.0 (58.6) | 11 / 1 | 14 / 2 | sigterm 0.6 s |
| 6 | context | P1 | 08:04:49 → 08:07:23 | 2.6 | — / 0 | 2, no tap (launch) | 7000 ×3 | — | 0 / 0 | 0 | 0.0 | 2 | 60.0 (55.5) | 13 / 1 | — | sigterm 0.5 s |
| **7** | **window** | **P2** | **08:36:10 → 08:56:28** | **20.3** | **1 / 1** | 2, no tap (metadata) | 7000 ×3 | **0** | **0 / 0** | **1 (0/0/0/1)** | **0.5** | 136 | 60.0 (56.7) | 31 / 3 | 12,773 / 0 | sigterm 0.6 s (84.5 s after the Back) |

- **"Pauses in play"** are the user's Back → Resume while the game stayed launched (the stream's time out). Every
  pause and resume, the start handoffs included, went by **PCSX2's hotkey confirmed through PINE** (none by SIGSTOP).
  The start handoffs took 4.4-7.0 s from the paused launch to the release.
- **Saves / loads:** none in any of these sessions. The only measured PS2 save is HOME-5's (16:13:58Z, `file complete
  0.5s`), outside the window.

## 2. The hitch measure (UX-R3's tool and definition)

| | minutes | hitch s | per 10 min |
| --- | --- | --- | --- |
| **window: P2, session 7** | 20.3 | 1 (L) | **0.5** |
| context: P1, sessions 1-6 | 20.2 | 0 | 0.0 |
| both together | 40.5 | 1 | 0.25 |
| H3-P2 T1 / T2 (2026-11-08) | 10 / 10 | 0 / 6.2 | 0.0 / 6.2 |
| **PS1 LAN, the keeper's last 30 days**, all sessions (n 28) | — | — | median **0.0**, best 0.0, worst 83.8 |
| PS1 LAN, sessions ≥ 5 min (n 2) | 20.8 | 34 | median 14.95 (2.2 / 27.7), pooled 16.4 |

- **The reference is thin:** the keeper's `sessions.jsonl` holds 46 rows since 2026-11-02, most of them short.
- **16 PS2 rows were taken out of the "PS1" set:** the keeper labels every PS2 session as PS1 (§4), so they were removed
  by their PCSX2 run windows from the `-ps2.log` files.
- **The PS2 window ran at or below PS1's typical LAN rate.**

## 3. Every stutter located (`views/pm60s_085527Z.md`, `session7_output_gaps.csv`)

**The one UX-R3 hitch second, 08:55:27Z (session 7, 61 s before the Back): network.**
- 72 packets lost in that heartbeat interval (the L rule, ≥ 30);
- fps 56.7, the output gap 18 ms, no control gap, no silence;
- the rung 7000, no step;
- the encoder sending its 60 frames; RSSI −67;
- no `PS2 pause / resume` within ±60 s (the Back came at +61 s).

**The client's longer freezes below the hitch line** are probably the "few stutters" felt. The client report's slowest
output gaps: 16 between 94 and 145 ms, 7 of them ≥ 100 ms (each a 6-9-frame freeze, under UX-R3's 200-ms G line).
**At every one the encoder sent 60 frames that second with normal frame sizes, so PCSX2 and the host kept producing.**
Counted as events, the two seconds at 08:44:39-40 being one:

| class | count | evidence (one line) |
| --- | --- | --- |
| **network** | **3** | 08:44:39-40 (145 / 100 ms), 08:52:10 (124 ms), 08:55:26 (133 ms, the hitch second): packets lost within ±2 s (3 / 1 / 72), audio starvation beside each |
| **client** | **2** | 08:37:01 (103 ms), 08:42:31 (125 ms): no loss, no control gap, the encoder steady: the onn's decode / output (its report: max codec 119 ms, max output gap 145 ms) |
| start-up | 1 | 08:36:07 (109 ms): the stream's first second (55 frames sent) |
| drive | 0 shown | not attributable: PCSX2's own log for this run no longer exists (below). A disc wait would freeze PCSX2's picture (static, small frames); the frame sizes show none |
| host | 0 | no stall-signal row, no step, the encoder at 60 every second |
| save | 0 | no save in the window |
| unexplained | 0 | — |

**PCSX2's log for this run is gone.**
- PCSX2 rewrites `emulog.txt` at every start, and HOME-5's two launches (16:11, 16:16Z) replaced it.
- The game log (`-ps2.log`) holds only PrivyHub's lines; the keeper copied neither (§4).
- So **the drive's `Read Abort` / slow-read count, `Invalid binding` and the card lines for 08:36-08:57Z cannot be
  read.** The game log's `PS2 memcards: Mcd001.ps2=kept Mcd002.ps2=kept` says the formatted cards were in place.

## 4. The margins across the evening

- **Rungs:** 7000 for 100 % of the streamed time; no transition.
- **Stall-signal rows:** 0. **Uplink silences:** 0 (0 per 10 min; one user silence at a Back in session 1 / 4).
- **Holds:** one `input_hold_skipped_paused` at session 7's Back (08:56:28; skipped because the game was paused). No
  `surface_lost`.
- **Audio:**
  - underruns 31 and starvation events 3 in session 7 (1.5 / min, ~0.15 / min);
  - P1's sessions 4-29 underruns each;
  - the starvation events sat beside the network-class freezes.
- **Loss post-FEC:** 136 in session 7 (6.7 / min), 58 across P1's 20 min. RSSI was −67 dBm throughout: weaker than the
  −51…−58 of the trip reads, and consistent with the loss.
- **Pads:** P1's sessions had both slots claimed and both changing (slot 1: 2-159 changes per session, so player 2
  played little but did press). In P2's session slot 0 changed 12,773 times and slot 1 0 times: **solo play**.
- **Drive:** unread for this run (above). **`Invalid binding`:** unread for this run (HOME-4+: none). **Card lines:**
  `kept` for both slots at every launch.
- **The keeper's label: a B50 item is not live.**
  - The running `privyhub-diag` (started 2026-11-02) has the pre-B50 `diag_read` loaded. So its `sessions.jsonl` rows
    label **every PS2 session `beetle-psx-hw` with no `system`** (all seven here, and HOME-5's four).
  - Its copier still uses the old game-log pattern, so **no `-ps2.log` was copied**.
  - The tree's `diag_read` (B50) labels all seven `PS2` / `pcsx2` correctly (the tool output above).
  - **This needs no code, only the keeper restarted** (an A step at a session's close), and it affects every PS2 read
    until then.

## 5. The reading

- **How long:**
  - after the HOME-4+ close, one solo session of a second PS2 title, **20 minutes**;
  - with HOME-4+'s two-player PS2 cells just before it, **about 40 minutes of PS2** last night, in seven sessions.
- **How smooth:**
  - **1 hitch second in 20 minutes (0.5 per 10 min), and none in the other 20.** That is as smooth as PS1 on the LAN (PS1
    median 0.0 per 10 min over all its sessions; the two longer PS1 sessions read 2.2 and 27.7);
  - the stream never left the top rung;
  - there were no stalls, no restarts and no freezes of the game.
- **The few stutters:** seven short freezes of 0.1-0.15 s:
  - **3 network** (brief packet loss on the onn's Wi-Fi at −67 dBm, with an audio dropout beside each);
  - **2 on the onn itself** (decode / output, no loss);
  - 1 at the stream's start;
  - **none from the drive, the host, PCSX2 or a save** as far as the logs show. The drive cannot be ruled out entirely
    for this run, because PCSX2's own log was overwritten.
- **To fix:** nothing in PS2 itself (§To B).
- **Surprising:**
  - the keeper still files PS2 as PS1 (B50's fix is not running in it);
  - PCSX2's own log does not survive the next launch;
  - the onn's signal was weaker than usual all evening (−67 dBm).

## To B

**Nothing to fix in PS2 streaming:** the stutters are the usual network class at PS1's rate, plus two client-side
freezes; none is drive, host or save. **Two small diagnostics items:**
1. **Keep PCSX2's log per launch.** Pass `-logfile data/games/ps2/logs/<launch time>-pcsx2.log` (or copy `emulog.txt` at
   exit), and have the keeper copy it. Then a read can count `Read Abort` / slow reads, `Invalid binding` and the card
   lines per session. That is the evidence the drive read-ahead (H3-P1 option 2) would need before anyone builds it.
2. **Not B, A:** restart `privyhub-diag` (no code) so its `sessions.jsonl` labels PS2 sessions `ps2` and copies the
   `-ps2.log` (B50 is in the tree but not in the running keeper).
