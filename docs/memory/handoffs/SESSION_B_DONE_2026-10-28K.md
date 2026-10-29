# SESSION B — done, 2026-10-28 K (QUEUE_2026-10-28K: B28, B29, B30, B31, in order; run 03:01-03:35Z; baseline 42a2ab6, the tree clean. Only the companion + `privyhub-link-n1` active, checked first. Nothing committed, nothing adopted, nothing installed, no stream, no companion restart, no adb)

1. **B28 BUILT: `PRIVYHUB_REMOTE=1`, G4-S4's four WAN lines in one, each acting only on a remote-class session.**
   - **Settled: as written the four are not LAN-neutral.** `PRIVYHUB_START_RUNG=floor` starts a LAN session at
     **5000** (the LAN list's floor; G8-S2's own test says so). The ladder adds `path_class` to every row, the cap
     writes a config row, and the telemetry writes `wan_sessions` rows and `wan` fields. G4-S4 never showed it: its
     five sessions under the four were all over the overlay.
   - **Built** (`companion/remote_umbrella.py`, `plugins/games.py` +12):
     - at each stream start, before it, the class from B23's readers (the overlay address, then the provider's path);
     - **remote** (direct / relayed / unknown): the umbrella's ladder, cap 7000, start rung `floor` and telemetry
       go into today's module globals, which is G4-S4's four exactly;
     - **LAN:** those globals None, today's code path byte for byte;
     - `remote-unknown` counts as remote for the start rung (chosen at the spawn, before the path is read; the floor
       is the safe start);
     - an explicit line wins; one `remote_config` row per session.
   - **Tests:** 10 green (the real start and a real ladder controller); 2 mutations caught; 33 / 33 `tests/` suites.
   - **The replay:** G4-S4 13 / 13 the same; the home LAN 16 / 16 today's 7000 (the four explicit would have given
     5000). Absent = today PROVEN.
   - **Not changed, for the user:** away from home every new session (a Home return too) starts at 4000 and climbs
     ~3 min a rung: ~12-15 min below 7000 (G4-S4 §3).
   - **G-A9 PREPARED, not applied:** `patches/G-A9_REMOTE_ADOPTION_PREPARED.md` (`REMOTE`, `ADOPTED` to thirteen,
     `drop_in_remote`, `remote.conf`). Record: `evidence/B28_REMOTE_UMBRELLA_2026-10-28.md`.
2. **B29 BUILT (the client): a guard hold is not a stall; the cap on the hold's own clock.**
   - **Settled:**
     - a hold ages the decoder's output exactly as a link stall does, so B7's monitor sent stalls and the host
       paused, saved and rewound at 400 (CL-B15: 9 holds);
     - **the "685 ms past the cap" was the episode's drop-to-IDR span** (`loss_guard_max_wait_ms`, as B10 defines
       it), not a late cap. The hold ended at the cap, and 7 corrupted frames passed before the IDR.
   - **Built:**
     - while the guard holds, the stall monitor decides on the time since the last frame received: suppressed, and
       a real stall inside a hold still goes out. **The host is unchanged:** it acts at 400 ms of no frames arriving;
     - the cap is checked by the controller loop's ~8-ms tick; a new report key, `loss_guard_max_hold_ms`;
     - `loss_guard=0` and `stall_signal=0` still turn each off.
   - JVM **161 / 161** (7 new; B7 / B10 / B27's unedited); the mutation fails 2; the guard off = today's monitor,
     byte for byte, PROVEN.
   - **APK (B5 … B27 + B29) `9719ea822ed5f7d13799ff7e02ba814cd0a2abe79b8a2e3d631d0aecb13c0110`**, 9,639,374 B:
     offline, a rebuild gives the same bytes; same signer as `8b0fbb74…`; only `classes3.dex` differs. **Pinned, NOT
     installed** (copy: `/tmp/b_q28k29_scratch/apk/app-debug.apk`). `8b0fbb74…` stays CONFIRMED.
   - **Stated:** a hold whose next good IDR is > 600 ms away (two IDRs lost in a row) still times out by design.
     Record: `evidence/B29_GUARD_QUIET_STALL_2026-10-28.md`.
3. **B30 BUILT: `tools/trip_log_keeper.py` and `tools/trip_check.py`** (new; nothing existing changed).
   - **The keeper:**
     - every 5 min, G4-S4's logs plus `wan_sessions` / `session_audit` / the journal / the game logs / the decoder
       reports into new, never-overwritten chunk files by file and rotation, redacted, with a growing
       `manifest.sha256`;
     - every 60 s, the overlay (path, online peers by count) and session state;
     - `status.txt`, STOP, the cap; it holds nothing open, so it survives a companion restart.
   - **The check:** six plain lines (adopted, apk, overlay, routing, band, log-keeper), redacted.
   - **Tests:** 12 + 8 green ×3; 2 keeper mutations caught. One `--once` smoke run into /tmp, read-only: the real
     redactor found 0 left.
   - `trip_check` was not run live (it reads adb). Record: `evidence/B30_TRIP_LOG_KEEPER_2026-10-28.md`.
4. **B31 WRITTEN: `handoffs/TRIP_RUNBOOK_2026-10-30.md`**, the user's steps A-F, placeholders only (`<hub-tailnet-name>`,
   `<home-value>`, `<friend-5ghz-network>`), with the paragraph on what the log-keeper collects and the one-line read
   afterwards ("read the trip").
5. **A — CL-B16 (Wednesday evening; the user at the TV once, for cell 2's hand step):**
   - **Setup:**
     - pre-register the rows below, hashed, before the install;
     - preserve `8b0fbb74…` (`PrivyHub/app/build/cl_b15_installed/`); copy B29's APK to
       `PrivyHub/app/build/cl_b16_installed/`, then `adb install -r`; read back
       `9719ea822ed5f7d13799ff7e02ba814cd0a2abe79b8a2e3d631d0aecb13c0110`, paired;
     - **every client property EMPTY**, read back empty; the onn on 5 GHz (read the band first);
     - `e3_state.py --check` ok on twelve, outside the watch's 04:30-05:30Z (`privyhub-link-n1` ends
       2026-10-31T06:00Z).
     - Each cell's drop-in restart loads the tree's B28 (it acts only with the line).
   - **Cell 1 — the LAN with the umbrella:** drop-in `PRIVYHUB_REMOTE=1` + `PRIVYHUB_IMPAIRMENT=none@post-fec,seed=1`,
     E1-SNES-STREAM, ~10 min, the onn on the LAN. Rows:
     - **U1** `remote_umbrella_config` at the start (the four `implied`; the cap's config: active, 7000; it
       applies only on a remote path);
     - **U2** one `remote_config` per client session, `class` `lan`, all four `in_force` false;
     - **U3** the LAN unchanged:
       - the encoder's first argv at 7000 (`-b:v 7000k`); no `start_rung` and no `path_class` in any ladder row;
       - no `remote_cap_config` row; no new `logs/wan_sessions.jsonl` row; no `wan` in `/status`;
     - **U4** silences, hitch seconds and the guard's freezes as G-A7's window / CL-B15 cell C (the clean LAN with
       the B29 client): ~3 freezes a minute, 0 stall pauses.
   - **Cell 2 — the overlay at home (as CL-B13 stage 3):** drop-in `PRIVYHUB_REMOTE=1` only, E1-SNES-STREAM, ~12 min.
     - **The hand step, plainly to the user:** "On the onn: Tailscale → Connect; PrivyHub → SETTINGS → Hub host =
       `<hub-tailnet-name>` → Save; then start the game when I say. After the cell: Hub host back to the home value,
       Tailscale → Disconnect."
     - **R1** `remote_config` `class` **`remote-direct`** (record it if `remote-relayed` / `remote-unknown`), all
       four `in_force` true; the newest `token_issued` `overlay`;
     - **R2** the first sample row's `start_rung` = `{"kbps": 4000, "source": "floor", "active_list": [4000, 5000,
       5500, 6000, 7000], "path_class": "remote"}`; the encoder's first argv `-b:v 4000k`;
     - **R3** the ladder climbing: `transition` 4000 → 5000 ~3 min 07 s in (G4-S4), ≥ 3 steps in 12 min, no
       decrease; `path_class` `remote` on the ladder rows;
     - **R4** `remote_cap_config` once in the ladder log (active, `cap_kbps` 7000); 0 `remote_cap` clamps;
     - **R5** `wan` in `/status` while streaming. The session's `logs/wan_sessions.jsonl` row is written at the next
       session's start: cell 3's (a LAN session) flushes it. Read it after cell 3's start;
     - **R6** the stack's WAN exposure as G4-S4: 0 false holds.
   - **Cell 3 — the 1 % loss cell with the B29 client:** CL-B15 cell L's drop-in exactly,
     `PRIVYHUB_IMPAIRMENT=loss-1@post-fec,seed=1` + `PRIVYHUB_LOSS_GUARD=1`, E1-PS1-STREAM, ~11.5 min, the LAN. Rows:
     - **S1** **0 `client_stall` / `desync_pause` rows drawn by guard holds** (CL-B15: 9). Any `client_stall`:
       record its age and whether a hold was open;
     - **S2** `loss_guard_timeouts` (0 expected where no two IDRs in a row are lost; each one's frames stated);
     - **S3** `loss_guard_frames_held` = `frames_after_dropped_reference` but the frames after a timeout;
     - **S4** **`loss_guard_max_hold_ms` ≤ 616** (the cap + two loops); `loss_guard_max_wait_ms` stated (the
       episode);
     - **S5** the cost (freezes a minute, hitch seconds, rendered fps) against CL-B15 cell L (27.7 / 37.2 / 55.75).
6. **A — the close and the CONFIRMED rule (CL-B7 §6):**
   - **The close:** properties empty, the drop-in removed, twelve lines, `e3_state.py --check` ok, `flags_absent`, the
     onn back on the LAN (Hub host home value, Tailscale off).
   - **The rule:** if the cells are valid with today's behaviours where no flag was set (B29's intended difference
     aside), **`9719ea82…0110` is CONFIRMED** and the pin moves: `tools/e1_suite.py` `EXPECT_APK`,
     `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256` and its test. Otherwise `8b0fbb74…3f4e` goes back on.
   - **Then G-A9 is the user's question:** "Adopt `PRIVYHUB_REMOTE=1` as the thirteenth line? Away from home it turns
     on the four settings G4-S4 used (start at 4000 and climb, the remote ladder, the 7000 cap, the WAN telemetry)
     by itself; at home nothing changes." If U1-U3 and R1-R4 are met → yes or no. Otherwise back to B with the rows.
7. **A — Thursday 2026-10-29:**
   - **G-A9, on the user's yes:**
     - apply `patches/G-A9_REMOTE_ADOPTION_PREPARED.md`: the drop-in `remote.conf` (`Environment=PRIVYHUB_REMOTE=1`)
       and the diff, with `<date>` replaced;
     - `systemctl --user daemon-reload`, then restart outside 04:30-05:30Z;
     - `e3_state.py --check` ok on thirteen.
   - **The log-keeper:**
     `systemd-run --user --unit privyhub-trip-log --property=WorkingDirectory=/home/privyhub/Projects/onn-stream-test python3 -B tools/trip_log_keeper.py --out docs/memory/evidence/trip_2026-10-30 --cap 2026-11-01T23:59Z`.
     - **State the cap: Sunday 2026-11-01T23:59Z.** It ends by itself; early: `touch
       docs/memory/evidence/trip_2026-10-30/STOP`.
     - Read `status.txt` (phase `running`, copies 0 until 5 min).
   - **The trip check:** `python3 tools/trip_check.py`, its six lines into the record. At home expect:
     - `adopted: 13 lines; host check ok`;
     - `apk: on the pin <short>`;
     - `overlay: connected yes, path no-peer, peers 0` (the onn not on the overlay at home);
     - `routing: newest token_issued lan`;
     - `band: 5 GHz (5180 MHz)`;
     - `log-keeper: … running …; unit active`.
   - **The runbook final:** check `handoffs/TRIP_RUNBOOK_2026-10-30.md` against what was adopted; the placeholders
     stay; tell the user where it is.
8. **Files:**
   - **Records + dirs** (redact_check, manifest): `B28_REMOTE_UMBRELLA_2026-10-28.md` / `b28_2026-10-28/`,
     `B29_GUARD_QUIET_STALL_2026-10-28.md` / `b29_2026-10-28/`, `B30_TRIP_LOG_KEEPER_2026-10-28.md` /
     `b30_2026-10-28/`.
   - **Patches:** `B28_REMOTE_UMBRELLA.md`, `G-A9_REMOTE_ADOPTION_PREPARED.md`, `B29_GUARD_QUIET_STALL.md`,
     `B30_TRIP_LOG_KEEPER.md`.
   - **The runbook:** `handoffs/TRIP_RUNBOOK_2026-10-30.md`.
   - **The rest:** KNOWN_ISSUES (inserted: B28 under G4-S4's Home / floor item, B29 under CL-B15's); ROADMAP (queue K
     after CL-B15); `logs/b28_|b29_|b30_|b31_git_status.txt` (taken at the queue's end); SESSION_B_STATUS.txt.
   - **Left in /tmp:** `b_q28k` (the copy), `b_q28k_scratch/` (the baseline regress, the mutation copies, `ga9/`,
     `keeper_smoke/`, the docs before the insertions), `b_q28k29` (the build copy) + `b_q28k29_scratch/`, the
     `b_q28k*` scripts.
   - **The host suites' run left a `logs/` dir in the copy,** as before.
