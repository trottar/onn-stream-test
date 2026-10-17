---
memory_schema: 1
as_of: 2026-10-17
status: TASK HANDOFF — G8-S2 (session B, unattended, after session A's smoke has exited): the stream's start rung — today a session starts at 7000 (about 8.25 Mbit/s on the wire) and under G8-S1's cap profiles never reached PLAYING (§5 of the final record). Behind `PRIVYHUB_START_RUNG=<floor|cap|kbps>` (absent = today, byte for byte): a session starts low and the ladder's own increase rule brings it up. Proved in process against the shim's cap profiles and by replay; the live re-run of the cap cells is a later session-A task
---

# G8-S2 — the start rung

Read first: `G8_S1_ADVERSE_NETWORK_ENVELOPE_2026-10-17.md` §5 (the cap cells: input 8.04–8.26 Mbit/s at every start, output pinned at the cap, drop fractions 0.27 / 0.45, rendering stopping after 9–27 frames, no PLAYING; the three readings; G8-P1's steady-source proof) and §2c (the on-the-wire ratio: 7000 kbit/s video → ~8.25 Mbit/s with FEC 8+1 and audio), `C3_L4_…` (where the session's first target is set; the increase rule and its hysteresis; the validated lists), `G5_S3_…` (the remote list 4000–7000, `path_class`), `G5_S4_…` (the cap and its clamp), `G8_P1_…` §2 (the in-process cap proof: how the synthetic source and the FEC sender were driven — reuse it), `D_BASE_P6_…` (the 90,000-byte frame cap: a start burst is also a per-frame burst).

## 1. The design (in the record §1 before the code, hashed)

- **The flag.** `PRIVYHUB_START_RUNG=floor` → the session's first target is the lowest rung of the active list (5000 on the LAN; 4000 on a remote path with G5-S3); `=cap` → the G5-S4 cap if set, else `floor`; `=<kbps>` → that rung if it is in the active list, else logged once and `floor`. Absent → today's first target, byte for byte. Invalid values logged once and ignored.
- **The climb.** Nothing new: the ladder's existing increase rule (and R5's hysteresis when G5-S2 is on) steps up from the start rung one rung at a time. The record states, from the ladder's constants, how long a clean session takes to reach 7000 from each start (the hysteresis window × the number of rungs) — stated as arithmetic.
- **The wire arithmetic, written before the proof:** the measured ratio wire / video at 7000 (8.25 / 7.0 ≈ 1.18, from §2c and E2-S1) applied to each rung: 5000 → ~5.9, 4500-cap headroom none at 4000 → ~4.7 (> 4500: still over the cap by ~4 %), 4000 under cap-6000 → fine. So `cap-4500` is **not** expected to pass even at 4000 — say so beforehand; that is a finding about the floor, not a bug to hide.
- **Recorded:** the start rung, its source (`floor` / `cap` / value / absent) and the active list in the session's first `decisions.jsonl` row; every later step as today.
- **Not in this task:** any change to the ladder's increase or decrease rules, the FEC, the frame cap, or the client.

## 2. The code and the proof

- A guarded hook where the first target is chosen (one `if`, a patch) and a small module for the parsing; unit tests (absent, `floor`, `cap` with and without G5-S4, a value in and out of the list, LAN vs remote lists).
- **Flag absent, byte for byte:** the handler comparison of the first-target path; G5-S2's and G5-S3's replays re-run identical.
- **In process, against the shim's cap profiles** (G8-P1's proof extended — the synthetic source driven at the rung's wire rate, *and* the real encoder's recorded start burst if a capture of one exists in the evidence tree; say which): for `cap-6000` and `cap-4500`, at starts of 7000 (today), 5000 and 4000: the shim's drop fraction, the FEC sender's recovered / unrecoverable groups, and the G5-S1 class — a table. The prediction: 5000 under cap-6000 drops ~0; 4000 under cap-4500 drops ~4 %. No claim that the client would reach PLAYING: that is the live test.
- **Replay:** G4-S1's run 1 and run 2 and the G8-S1 cells 6, 7, 12 with the flag at `floor`: the start rung, when the ladder would have climbed, where it would have been at each cell's first rules action — tabulated, no claim of improvement.
- The suites green; the redactor.

## 3. The record

`evidence/G8_S2_START_RUNG_2026-10-17.md` + `g8_s2_2026-10-17/` (design + hash, the diff, the test output, the proof tables, `redact_check.txt`, `manifest.sha256`); ROADMAP §G8 ("start rung built behind a flag; the cap cells' live re-run pending"); `patches/G8-S2_…md`; `logs/g8_s2_git_status.txt`. **Proposed next (not run):** G8-S3 — the four cap cells re-run with `PRIVYHUB_START_RUNG=floor` (and once with `=cap`, cap 4000, under cap-4500), the driver's scaffolding, ~1 h. Then `SESSION_B_DONE_2026-10-17B.md` (ten lines). Nothing adopted; nothing committed.
