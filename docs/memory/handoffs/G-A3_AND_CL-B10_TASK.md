---
memory_schema: 1
as_of: 2026-10-23
status: TASK HANDOFF — session A, two parts. PART 1 (unattended, ~45 min): G-A3, the user's adoption of `PRIVYHUB_LINK_REPORT=1` as the NINTH adopted line (the user's decision 2026-10-23: diagnostics only), then CL-B10's install and its two bench cells (the `state` path and the stall resume under the bench blackout). PART 2 (attended, the user at the TV, ~30 min, a later prompt): the 5-GHz window with a Home press for the restart guard, and the 2.4-GHz cell for the notice (the user switches the band by hand, both ways). Measurement only beyond the one adoption; nothing committed
---

# G-A3 and CL-B10

Read first: `SESSION_B_DONE_2026-10-23E.md` items 6-9 (**the exact flags, properties, strings, APK hash and expected rows — use theirs**), `patches/G-A3_LINK_REPORT_ADOPTION_PREPARED.md` (the diff, the drop-in content, the tests), `G_A2_OPUS_ADOPTION_2026-10-19.md` (the adoption pattern), `B11_…`, `B12_…`, `B13_…`, `B14_…`, `LINK_N1_LAUNCH_2026-10-23.md` (the watch samples 04:30-05:30Z; **no companion restart inside that hour**), `CL_B7_…` §6 (the CONFIRMED rule).

**The user's decisions (2026-10-23, verbatim "Yes to both"):** adopt the ninth line; the band may be switched to 2.4 GHz for one cell and back (the user's hand).

## PART 1 — unattended (now)

### 1. G-A3 — the ninth line

- Precondition: the eight lines, `--check` ok (adb reconnected by hand if needed, the endpoint never printed), no `e3_flag.conf`, no game, one device paired, APK `bf5114a2…` CONFIRMED, no `privyhub-*` unit but the companion and `privyhub-link-n1`, HEAD named (queue E committed), the tree clean but the prompt and this file; the clock outside 04:30-05:30Z.
- `git apply` the prepared patch; `e1_suite --self-test`, `test_e1_remote`, `test_c3_l4_nft_night` from the tree, green; **`~/.config/systemd/user/privyhub-companion.service.d/link-report.conf`** with `Environment=PRIVYHUB_LINK_REPORT=1`; `daemon-reload`; restart; the environ read back **nine lines**; `--check` ok on nine.
- The confirmation window: one E1-SNES-STREAM (snes9x) `--e2 --window 600` with **no `e3_flag.conf`**: every heartbeat carrying `link_*` by the drop-in alone (the client's report is on by default with `da09e154…`; with `bf5114a2…` still installed at this point, the property `link_report` left at 1 by LINK-R1 carries it — state which APK and which path made the keys appear); host gates; silences and hitch seconds per 10 min on 5 GHz (LINK-R1: 0 / 0).
- `evidence/G_A3_LINK_REPORT_ADOPTION_2026-10-23.md` + dir; ROADMAP §G4 / `REMOTE_TRUST.md` where the adopted lines are listed for the user (how to turn it off: delete `link-report.conf`, restart); `logs/g_a3_git_status.txt`; `CURRENT.md`: **the adopted state is NINE lines** (list them).

### 2. CL-B10 — the install and the bench cells

- Preserve `bf5114a2…`; `adb install -r` `da09e154…` (its sha256 checked against B's pin; the signer); read it back; the paired line — "not paired" = stop and tell the user. **The band read first (`dumpsys wifi`): 5 GHz expected.** Properties: `restart_guard 1`, `stall_signal 1`, `link_notice 1` set and read back (`link_report` needs nothing).
- A detached driver (`cl_b10_2026-10-23/cl_b10_driver.py` from `bench_r3_driver.py`; unit `privyhub-cl-b10`; cap launch + 2 h; **no cell may start inside 04:30-05:30Z**): `PRIVYHUB_SNES_CORE=snes9x` and the nine lines in force, each cell's drop-in read back and removed, `flags_absent` after:
  - **cell 2:** `blackout-4s@both,every=120s,seed=1` + `PRIVYHUB_INPUT_HOLD=1 _B6=1 _B8=1 _REWIND=1 PRIVYHUB_STALL_SIGNAL=1 PRIVYHUB_STALL_RESUME=1` — per blackout one `state_saved` (kind silence) ~0.40 s in, one `input_release` method `state` at the resume, playing after; `unattended_frames.py --net` **≈ 24** per blackout (B's stated number for the state path; not ≈ 0); the resume ≤ 1 heartbeat after the return; no second `desync_pause`, no `session_started`;
  - **cell 3:** the same flags with `blackout-4s@down,every=120s,seed=1` — `state_saved` kind stall, the pause 400-460 ms after the client's last frame, **no `encoder_restart`, no `recovery_escalation`**, one `resumed via client_ready_stall` (or `stall_end`) with the load, net ≈ 9-12, `stall_end_late`, no second pause.
- Pre-registration hashed before the install (both cells' rows, the reading: if both meet their rows, **the hold / state / stall stack is a candidate for the user's adoption call on SNES**, costs stated — ~24 frames per two-way drop, a save per stall, the frozen picture while held; if not, back to B with the rows). Launch, confirm cell 2's preflight, **exit**; the record is a later one-line task together with Part 2's.
- `evidence/CL_B10_LAUNCH_2026-10-23.md`, `logs/cl_b10_launch_git_status.txt`.

## PART 2 — attended (the user at the TV; a later prompt)

- **Cell 1, 5 GHz, the restart guard:** E1-SNES-STREAM `none@post-fec,seed=1`, 10 min, the properties as above; the user plays; **~4 min in the user presses Home, waits ~5 s, and returns to the game.** Expected (B item 7): the old report + `session_ended` before the new start, `restart_cause.away_ms` ≈ 5,000, the new session's underruns ≈ the others' (not ~170 /s); 0 notices (`link_notice=0`); silences / hitch s per 10 min against LINK-R1's 0 / 0; the user's one line on what the Home-and-back felt like.
- **Cell 4, the notice:** the user switches the onn to 2.4 GHz by hand (the Opal's 2.4-GHz network, or the onn's Wi-Fi settings) and starts the game; the notice must appear bottom-left within the first seconds ("Wi-Fi: 2.4 GHz / Use your router's 5 GHz Wi-Fi for this box") — **the user's word or a phone photo**, recorded; the heartbeat's `link_notice=1`, one `link_notice_shown` row with reason 1; 10 min; then **the user switches back to 5 GHz** and the stream shows `link_notice_cleared` ~30 s after the band reads 5 GHz. Silences per 10 min on each band in the same hour — the A/B LINK-R1 could not make.
- Then the properties cleared and read back, `--check` ok on nine, the APK on the onn named; the CONFIRMED rule (all cells valid, the property-empty / flag-absent behaviours as today → `da09e154…` CONFIRMED; else `bf5114a2…` reinstalled and the user told).
- The record for both parts: `evidence/CL_B10_RESTART_GUARD_STATE_STALL_NOTICE_2026-10-23.md` + dir, the per-cell tables, the reading applied, `KNOWN_ISSUES.md`, ROADMAP lines, `CURRENT.md` Next Action (the user's commit; the adoption questions — the stack on SNES, the loss guard, the notice as a client default — each with its cost; the nightly watch's first nights).

No sudo (systemd --user is not sudo), no nft, the Opal read-only (the band switch is the user's hand), adb for the install, the pre-registered `setprop`s and state reads only, no addresses or identifiers; nothing fetched, nothing deleted; the nine lines only and no `e3_flag.conf` at every teardown; nothing but the ninth line adopted; nothing committed.
