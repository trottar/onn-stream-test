---
memory_schema: 1
as_of: 2026-11-08
status: TASK HANDOFF — H3-P2 the streamed PS2 session (session A, hardware, attended ~15 min per title; the user at the TV with the onn, the pads paired to the onn over Bluetooth as always — NOTHING on the hub is the user's). `PRIVYHUB_PS2=1` in a bench drop-in for the run only (B49); APK `8ba4d996…` CONFIRMED with every property empty (no chooser: 2 ports, no multitap). The user's decision 2026-11-08: NO PS1 reference game tonight — the hitch comparison comes from the diagnostics keeper's PS1 sessions of the last 30 days. Per `SESSION_B_DONE_2026-11-08P.md` §A with the rows P7a-P7i; measurement only; nothing adopted; nothing committed
---

# H3-P2 — PS2 on the TV, through the stream

Read first: `SESSION_B_DONE_2026-11-08P.md` §A (**the rows, the commands, the drop-in line, the log lines — use B's exactly**), `B49_PS2_LAUNCH_KIND_2026-11-08.md`, `H3_P1_PS2_PROBE_2026-11-07.md` (the T1 / T2 margins; P6's lesson), `tools/diag_read.py` / `DIAGNOSTICS.md` (the keeper's `sessions.jsonl` — per-session hitch seconds), `docs/memory/CURRENT.md`.

**The stage is the user's message.** The read line alone = setup (unattended). "T1 done" + one line = T1's read. "T2" = the heavy title's turn; "T2 done" + one line = its read. "done" = the close. **Every reply begins "YOU, now:" and the one thing the user does next, on the onn or the TV, in plain words. No stage asks the user for anything on the hub.**

**One change from B's sketch, the user's decision:** no PS1 game is played tonight. P7e's reference is the keeper: from `~/privyhub_diag/*/sessions.jsonl` (and `evidence/reads/` if needed), the PS1 sessions of the last 30 days that were LAN, game class, ≥ 10 min — their hitch seconds per 10 min; **the reference = the median of those sessions**, the count and the spread recorded; **P7e passes when T1's hitch seconds per 10 min ≤ that median + 2.** Pre-registered with the number filled in before the drop-in.

## Setup (unattended, ~10 min; no game and no movie running; outside 04:30-05:30Z)

- B's checks: fifteen lines, `--check` ok, `8ba4d996…` CONFIRMED, the eleven properties empty, `privyhub-diag` active, only the two units, HEAD named (**B49 committed** — if `git status --short` shows B49's files uncommitted, stop: "YOU, now: commit B49 first, then send the read line again"), the paths file present (never read into a record), the one AppImage present, the drive's two folders listed (counts and mtimes only).
- The P7e reference computed and the pre-registration hashed (B's rows P7a-P7i with the reference number; the validity rules; the P2 capture at minute 6-7).
- The bench drop-in exactly as B wrote it; the restart; **sixteen** `PRIVYHUB_` lines read back, one `PRIVYHUB_PS2=1`; the journal clean; the "PlayStation 2" node present in the host's list with the folder's distinct-title count (P7a's first half).
- The samplers started (B §A setup 3; `pidstat` attaches once PCSX2 runs).
- Exit: "YOU, now: on the onn, open Games — you should see a new **PlayStation 2** entry. Open it and start the **light** title (the one you named first). Within about 1½ minutes the PS2 logo then the game should appear on the TV, and both pads should work. Play for 10 minutes; a few minutes in, press **Back** once (the picture stops), pick the title again and **Resume** (it continues where it stopped). After 10 minutes press Back, then **Stop**. Then send 'T1 done' with one line on how it felt — smooth, stutters or unplayable, and anything about the controls."

## T1 (attended, ~12 min)

- On "T1 done": P7b (launch → first frame ≤ 90 s, the `PS2 launch` line, the `ps2_session` row), P7c (the user's line on the pads; PCSX2's log naming the four virtual pads and their order), P7d (`PS2 pause` ≤ 3 s after `session_ended`, `PS2 resume` ≤ 3 s before or at `session_started`, method recorded), P7e (T1's hitch seconds per 10 min against the reference), P7f (the minute-6-7 capture through `tools/ps2_p2_frames.py`, the capture's own minute marked), P7g (M2-M6 from the samplers), P7h (`PS2 exit: sigterm`, nothing left), P7i (the line verbatim). Invalid if a pad was not paired to the onn or the stream restarted during the 10 min (then once more, the user told).
- Exit: "YOU, now: if you want the heavy title too, start it the same way and send 'T2' now — then play 10 minutes with the Back / Resume once, Stop, and send 'T2 done' with one line. If not, send 'done'."

## T2 (optional, attended, ~12 min)

- On "T2": the samplers re-armed; the reply "YOU, now: play — 10 minutes, Back and Resume once a few minutes in, then Back, Stop, and 'T2 done' with one line." On "T2 done": the same rows for T2.

## Close (on "done"; unattended)

- `b49-ps2.conf` removed, `daemon-reload`, restart (no game, no movie); **fifteen lines**; `--check` ok; `flags_absent`; the eleven properties empty; `8ba4d996…` CONFIRMED; nothing written to the drive (listing + mtimes before = after); nothing of PCSX2 running.
- **The record** `evidence/H3_P2_PS2_STREAMED_2026-11-08.md` + dir (per title P7a-P7i with margins, the reference's number / count / spread, the user's lines verbatim, the pause method, the pads' order; titles `T1` / `T2` only; `redact_check`); `KNOWN_ISSUES.md` (insertions only); ROADMAP §H3 lines; `logs/h3_p2_git_status.txt`; `CURRENT.md` (headings kept, under its limit, `check_memory_health` after): H3-P2's result one line per title; Next Action — the user's two questions (adopt `PRIVYHUB_PS2=1` as the sixteenth line, or bench-only; PS2 save states through PINE later, yes / no) and HOME-4 (the chooser APK at the TV).
- The reply: "YOU, now: commit, then answer: PS2 always on (the sixteenth line) yes/no; PS2 save states later yes/no" plus per title the rows met / not met with margins in plain words (launch seconds, pause and resume seconds, hitch seconds vs the PS1 reference, fps).

No sudo, no nft, the Opal read-only, adb for state reads only, no `setprop`; the one drop-in named and removed at the close; fifteen lines and no `e3_flag.conf` at every teardown; nothing written to the drive; no address, title, filename or path from the paths file anywhere in git or the reply; nothing fetched, nothing deleted; nothing adopted; nothing committed.
