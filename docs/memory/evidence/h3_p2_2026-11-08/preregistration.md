# H3-P2: pre-registration (written and hashed before the drop-in, 2026-11-08)

Sources: `handoffs/SESSION_B_DONE_2026-11-08P.md` §A (B's rows, commands, drop-in line and log lines, used exactly),
`handoffs/H3-P2_PS2_STREAMED_RUN_TASK.md`, the user's decision of 2026-11-08 (no PS1 game tonight; P7e's reference from
the diagnostics keeper), `B49_PS2_LAUNCH_KIND_2026-11-08.md`, `H3_P1_PS2_PROBE_2026-11-07.md` (P3 / P4 / P5's bars).
Titles are T1 (light) and T2 (heavy, optional). The user plays on the TV through the onn, the pads paired to the onn
over Bluetooth; nothing on the hub is the user's.

**The client:** APK `8ba4d996…605f` CONFIRMED, every property empty: stable slots, no chooser, so no
`players_chosen` is sent and a PS2 title starts with 2 ports and no multitap.
**The host:** fifteen lines plus the bench drop-in `b49-ps2.conf` (`PRIVYHUB_PS2=1`) for the run only, removed at the
close.

**The order (changed by the user):** no PS1 game; T1; then T2 only if the user sends "T2".

**P7e's reference (`setup/p7e_reference.txt`):** the keeper's PS1 sessions since 2026-10-09, LAN, game class, ≥ 10
min: **count 1, median 27.7 hitch s / 10 min** (no spread: one session; G-A10's automated window, 2026-11-03).
**P7e passes when T1's hitch seconds per 10 min ≤ 29.7.**

**The P2 capture's minute:** one 60-s capture at minute 6-7 of T1's play, counted from T1's first `session_started`
(the launch's), B's command exactly:
`ffmpeg -f x11grab -framerate 60000/1001 -window_id <the PID's window> -t 60 -i $DISPLAY -vf format=yuv420p,showinfo -f null - 2> <scratch>/showinfo.txt`,
then `python3 tools/ps2_p2_frames.py <scratch>/showinfo.txt`. If the game is paused (Back) at minute 6, the capture
starts at the first whole minute after the resume. That minute is marked in the hitch count (the capture's own load,
disclosed). The same for T2.

## The rows (P7, B's table, verbatim)

| row | pass when |
| --- | --- |
| P7a the list | "PlayStation 2" on the onn with the drive's titles (count = the folder's distinct titles); the drive's folders unchanged (listing + mtimes) |
| P7b launch | the onn's launch → the first frame on the TV **≤ 90 s**; the game log `PS2 launch` line; `ps2_session` row |
| P7c pads | both pads drive players 1 and 2 (the user's line; PCSX2's log names the four `PrivyHub Virtual Gamepad` devices opened — their order recorded) |
| P7d pause / resume | Back → `PS2 pause` **≤ 3 s** after `session_ended`; Resume → `PS2 resume` **≤ 3 s** before or at `session_started`; the game continues (the user's line); the method recorded (`hotkey` or `sigstop`) |
| P7e hitches | T1's hitch seconds per 10 min **≤ the PS1 session's + 2** (here: ≤ 29.7, the keeper's reference) |
| P7f P2 | `ps2_p2_frames.py`: median **≥ 59**, corrected minimum **≥ 55** |
| P7g M2-M6 | as H3-P1's P3 / P4 / P5 bars, now in play with the stream (no core ≥ 90 % for 30 s, GPU median ≤ 80 %, Tctl ≤ 90 °C, frame-time p95 ≤ 20 ms, no read stall > 500 ms after 60 s) |
| P7h exit | `PS2 exit: sigterm …` (not `sigkill`); nothing of PCSX2 left; the next PS1 launch works |
| P7i feel | the user's line (recorded verbatim; not a pass / fail by A) |

- P7a's count: the folder's distinct titles by B49's list rule (one per folder + stem, `.chd` > `.iso` > `.cue`, a
  `.bin` only through its `.cue`): **115**, read before the drop-in.
- P7g's frame-time p95 is the P2 capture's (its frame intervals); M2 / M3 / M6 from the 1-Hz samplers over the 10
  minutes; M5 from `iostat -x 1` on the drive (`sda`), a stall = a second with r_await > 500 ms.
- P7h's "the next PS1 launch works": no PS1 game is played tonight (the user's decision), so this half is not read;
  recorded as such.
- P7b's first frame: the onn's launch request (the host's log) to the first frame of the session (the client's
  report / the recovery log's `session_started`), whichever the logs give; the method recorded.

## Validity

**Invalid if:** a pad was not paired to the onn (re-pair on the onn, never on the hub), or the stream dropped to a
restart during the 10 minutes (then the 10 minutes once more, the user told). Also recorded, not invalidating: the
pause method (`hotkey` = PINE answered; `sigstop` = it did not).

Nothing adopted; nothing committed.
