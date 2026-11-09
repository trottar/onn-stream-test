# HOME-8: pre-registration (written and hashed before Stage 2, 2026-11-08)

Sources: `handoffs/SESSION_B_DONE_2026-11-08W.md` §A (stage 1, C24-C28, the hub reads, the "You should see" lines and
the replies — used exactly), `handoffs/HOME-8_N64_FIXES_TASK.md`, `B61_…`, `B62_…`, `B63_…`, `B64_…`,
`HOME_7_HOLD_TO_JOIN_N64_2026-11-08.md` (T1 / T6 as labelled there).

**The state:** seventeen adopted lines, `--check` ok; `9aa00ba2…` CONFIRMED on the onn; the eleven properties empty
throughout (no `setprop`); B61-B64 live from the stage-1 restart. Stage 1's reproduction: **running save hangs T6: yes**
(recorded before any cell).

## The cells (B's rows)

**C24 — T6's buttons (B62).** Hub reads: the game log `N64 remap: face_c (players 1-4, 8 binds) verified`; RetroArch's
`[Remap] Core-specific remap found`; `n64_core_check.py --remap` → `matches`; the payload's `n64_session.layout`
`face_c`; `updates_by_player` moving for P1 / P2. You should see the details line "A = ⨉, B = □, C-buttons = right stick
(also △ = C-up, ○ = C-right), Z = L2" (glyphs drawn, or boxes: record which); △ / ○ jump for both players. **Met:** the
user's line, jump on △ (and ○) for each player. **Not met → B:** the remap's two analog values (or the descriptor
reading). **Decides B62.**

**C25 — the N64 Home hold (B61).** Hub reads: at the loss `state_save_skipped` reason "n64: no save into a running core",
core mupen64plus_next (no `state_save_failed`); `desync_pause` with no `pause_error`; at the return `rewind_skipped` "n64:
plain resume (no state)", then `resumed`; no `command_port_silent`, no `stall_resume_failed`; RetroArch's CPU as before
the press. **Met:** the game back and playable (the user's line) and the rows. **Not met → B:** a `command_port_silent`
(with its process reading) or a freeze; stage 1's reproduction beside it. **Decides B61** (with the reproduction: the
trigger per title).

**C26 — T1 with three pads (B63, an incapable title).** Hub reads: the start's `ports_set` players 2, `multitap` false,
`multitap_available` false, `capable` false, `capped_from` 4; the game log `PS1 multitap: off` and `PS1 ports capped: 4
-> 2 (not multitap-capable)`; T1's `.opt` multitap disabled after the launch (B63's migration; before: "enabled"); `--device`
1-2; no `relaunch_ports` row at the third hold. You should see "No multitap on this system — 2 players", no "Setting up 4
players…", player 2 working. **Met:** player 2 works and no relaunch. **Decides B63** (an incapable title; the migration).

**C27 — a multitap-capable PS1 title (B63 keeps the relaunch).** Hub reads: its metadata `ps1_multitap: port1`; the start's
`capable` true; B54's `relaunch_ports` (`ok`, `state loaded`) or, with a stored count ≥ 3, the multitap from the start;
`PS1 multitap: port1`; `--device` 1-4; P3 joined. **Met:** players 1-3 working (the user's line).

**C28 — 10 min of N64, no capture.** `diag_read` over the sitting: the N64 session's UX-R3 hitch s / 10 min beside C26's
or C27's PS1 session; host CPU, Tctl; any Home hold as C25. **Met:** the hitch rate ≤ the PS1 session's + 2, no freeze,
and the user's line. **The N64 hitch reading without the capture.**

**B64** is read on every start: the seq-1 `pad_slots` row `stale: true`.

## Validity

The properties empty throughout; seventeen lines; 5 GHz; the user's actions as described; the user's lines are the gate
on anything on screen; a row's absence is itself the reading; a step the user could not do, or that left the app, is
invalid, not failed. No capture in this sitting.

Nothing to adopt (all inside adopted flags or the default host path); a not-met goes to B; `PRIVYHUB_PS1_MULTITAP_CAPABILITY=0`
is the user's way back for B63. Nothing committed.
