---
memory_schema: 1
as_of: 2026-10-23
status: TASK HANDOFF — UX-R4 (session A, read-only, now, while the user may still be playing: copies only, no restart, no run, no adb beyond `getprop`): the user hit "severe lag" tonight (2026-10-23, after BENCH-R3's record, US Eastern evening) and pressed Save State at the spot — the game log's "Saving state" line is the mark. Find it, build the per-second view ±60 s around it with every instrument, say what each saw, and what was in force (the APK bf5114a2…, the adopted eight lines, every stack flag absent, the link report OFF because its properties were cleared at the bench's close). Nothing committed
---

# UX-R4 — the lag the user marked with a Save State

**The user (2026-10-23):** "playing and just had severe lag I saved at the spot".

Read first: `UX_R3_FIND_THE_DEATHS_2026-10-21.md` §1 (the per-second view and the hitch definition; `ux_r3_seconds.py`), `BENCH_R3_SNES_STACK_AND_LOSS_GUARD_2026-10-23.md` §7 (the link: the onn on 2.4 GHz channel 1 at −68 dBm; the uplink-silence cluster coinciding with the tx link rate falling to 27-81 Mbps; the Opal's 5-GHz radio listing no station), `UX_R2_…` §2 (the pause / save probe: how a Save State shows in the game log, the recovery log and the control-gap log), `B10_…` (the counter `frames_after_dropped_reference` is in the report only with the property set — state whether it was).

## 0. Preserve first, then what was in force

- `evidence/ux_r4_2026-10-23/session/`: copies of everything covering 2026-10-22 21:53Z (BENCH-R3's close) → now: the companion journal, every ladder log incl. `stream_log_archive/`, the frame-size log and archive, the heartbeat / recovery / control-gap / host-sampler / audio logs, every decoder report in the span, the game logs, the audit rows; `manifest.sha256`; copies only, nothing moved. **If the user is still playing, read the live files once and say so; do not wait for the session to end.**
- **In force during the play, from the files:** the APK on the onn (`bf5114a2…`, CONFIRMED); the environ (eight lines — no stack flag, no `LINK_REPORT`, no `LOSS_GUARD`); the properties (`getprop` of the four — expected empty, so **no RSSI and no corrupted-frame counter in this session**: say it plainly); which fixture / core; the ladder's rung; the onn's uptime if a report carries it (no adb beyond `getprop`).

## 1. The mark and the ±60 s

- **The mark:** every "Saving state" line in tonight's game log(s), with its UTC time; the one nearest the user's message is the mark (list all; the user can say which). Beside it: the pause / save probe's rows (the client session end and restart, as UX-R2 §2 showed — a Save State is a trip through the Pause menu).
- **The per-second view from mark − 60 s to mark + 10 s**, every instrument at its real resolution (UX-R3's script): rendered frames per interval, post-FEC loss, FEC-recovered, unrecoverable groups, every control gap with start and length, underruns and concealed, the audio arrival gap, the frame-size log's packets / max / frames ≥ 40, the ladder's state and decisions, the recovery rows, the report's output gaps and spikes where they cover it. **The hitch score per second, ranked; the longest run before the mark.**
- **The whole session the same way** (per 10 min: hitch seconds, the longest run, silences ≥ 250 ms, loss), so the mark sits in context: was it one event or the end of a bad stretch?
- **The shape:** uplink-only (control gaps, downlink fine), downlink-only (output gaps / loss, input flowing), both (the death's shape), or host-side (the encoder, a recovery, a rung change) — stated from the columns, with the second it began.

## 2. Against what we have built, by the record

For the seconds that scored: what each flagged mechanism **would have done, by its record's measured behaviour** (not by design) — the hold at H 950 (BENCH-R2 / R3: fires at 0.95-1.05 s of uplink silence; no rewind confirmed on either core by B4's method); the PS1 `state` path (BENCH-R3 D: saved at 0.40 s, loaded and playing, net 24 frames); the stall signal at 400 (BENCH-R3 B: the pause at 420-484 ms after the last frame); the loss guard (BENCH-R3 E: holds every corrupted frame, ≤ 0.5-s freezes); the bidirectional loss rule. One line each: would it have fired here, and what it would have cost the player instead. **No change is made; nothing is proposed as adopted.**

## 3. Record

`evidence/UX_R4_SAVED_AT_THE_LAG_2026-10-23.md` + `ux_r4_2026-10-23/` (the copies, the per-second table, `redact_check.txt`, `manifest.sha256`); `docs/KNOWN_ISSUES.md`'s top item (one line: the mark, the shape); `logs/ux_r4_git_status.txt`; `CURRENT.md` Next Action (the user's commit; **two things for the user's say-so: the 2.4-GHz finding — the onn's band is the user's hand change on the Opal or the onn; and leaving the link report on during play — `PRIVYHUB_LINK_REPORT=1` as a ninth adopted line (diagnostics only, no behaviour) plus `setprop debug.privyhub.link_report 1` after each onn boot, so the next lag carries its RSSI**). Exit.

No sudo, no nft, the Opal read-only, adb only for `getprop`, no addresses or identifiers; nothing fetched, deleted or moved; no restart, no power-cycle, no run; no change outside `docs/`, `logs/` and the evidence directory; nothing adopted; nothing committed.
