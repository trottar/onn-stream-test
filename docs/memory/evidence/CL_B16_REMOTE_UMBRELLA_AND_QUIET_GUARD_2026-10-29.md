---
memory_schema: 1
as_of: 2026-10-29
baseline_commit: 4b89d5b (queue K committed; "Queue K done; CL-B16 handoff"; nothing committed by this session)
---

# CL-B16 — the remote umbrella at home (B28), and the quiet guard (B29): 3 / 3 cells valid; `9719ea82…` CONFIRMED; R3 and S1 not met → back to B

**Classification: MEASURED. 3 / 3 cells valid. APK `9719ea82…0110` (B5 … B27 + B29) CONFIRMED and pinned.** Every
client property was EMPTY and no `setprop` was run. The onn was on 5 GHz (5180 MHz) in every band read (85 / 96 / 86).
- **The umbrella on the LAN (cell 1): U1-U3 met.** The LAN session is today's: 7000 from the first argv, no
  `path_class` / `start_rung` / `remote_cap_config`, no `wan_sessions` row, no `wan` in `/status`. **U4 not met:** this
  evening's LAN was ~3× lossier than CL-B15 cell C's, with 8 stall pauses against C's 0.
- **The umbrella over the overlay (cell 2): R1, R2, R4, R5 (`/status`), R6 met. R3 not met.** It started at 4000
  (`floor`) and the 7000 cap was in force, but the ladder took 2 steps in 13.6 min, not ≥ 3. A client stall with a
  333-ms uplink silence at 21:18:36Z put the ladder in `HOLD_DOWN` (`blackout`) and restarted its clean-report count.
- **R5's file part, disclosed beforehand:** cell 2's `logs/wan_sessions.jsonl` row was never written (33 lines before
  cell 2, after it, and after cell 3's start and end).
- **The quiet guard at 1 % loss (cell 3): S2, S3, S4 met; S1 not met.**
  - The guard numbers: 0 timeouts; held 3,290 = counter 3,290; `loss_guard_max_hold_ms` 469.
  - **12 stall pauses, with no uplink silence behind any of them** (CL-B15 cell L: 9). 11 of the 12 sit among guard
    episodes in the ±4-s heartbeats.
- **The reading:** U1-U3 met, R1-R4 not all met (R3), so **G-A9 goes back to B as read.** S1 not met, so the quiet
  guard does not stand as read: **back to B with the rows.**
- Nothing adopted; nothing committed.

Task: `handoffs/CL-B16_REMOTE_UMBRELLA_AND_QUIET_GUARD_TASK.md`, session A. B's strings: `SESSION_B_DONE_2026-10-28K.md`
items 5-7. Launch: `CL_B16_LAUNCH_2026-10-29.md`. Files: `cl_b16_2026-10-29/` (`cells.jsonl`, `record_read.json` /
`record_read_console.txt` from `cl_b16_read.py`, `runs/<cell>/`).

## 1. The three launches

| cell | unit | drop-in (lines) | workload, window | launched | PLAYING | session | closed |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `privyhub-cl-b16-c1` | `PRIVYHUB_REMOTE=1` + `none@post-fec,seed=1` (14) | E1-SNES-STREAM, 600 | 20:39:56Z | 20:42:21Z (attempt 1, 4.1 s) | 20:42:21-20:53:54Z, 11.55 min | 20:54:16Z |
| 2 | `privyhub-cl-b16-c2` | `PRIVYHUB_REMOTE=1` (13) | E1-SNES-STREAM, 720 | 21:12:25Z | 21:14:49Z (attempt 1, 3.1 s) | 21:14:49-21:28:22Z, 13.55 min | 21:28:41Z |
| 3 | `privyhub-cl-b16-c3` | `loss-1@post-fec,seed=1` + `PRIVYHUB_LOSS_GUARD=1` (14) | E1-PS1-STREAM, 600 | 21:33:26Z | 21:35:51Z (attempt 1, 4.1 s) | 21:35:51-21:47:24Z, 11.55 min | 21:47:55Z |

- **Validity, every cell `valid`:**
  - the drop-in's lines at the stream and under load (14 / 13 / 14);
  - `flags_absent` true after and at the final read; twelve lines after;
  - the seven properties empty before and after;
  - the routing class at the stream as the cell's: lan / **overlay** / lan;
  - the shim's profile applied: cell 1 0 drops; cell 2 no impairment line and no impairment row; cell 3 0.992 %, no
    other drop;
  - the host gates met: RetroArch 59.999 / 59.999 / 59.999; capture 59.997 / 59.955 / 59.996; dup+drop 0.1 / 0.0 /
    0.1 per min.
- **Before cell 2 (the user's hand step):**
  - the overlay connected, **path `direct`**, `peer_ready`; 2 devices online, 1 direct peer, 0 relayed (counts only);
  - Hub host set; the newest `token_issued` overlay (21:11:28Z).
- **Before cell 3 (the onn put back):**
  - Hub host empty; the newest `token_issued` lan (21:32:45Z);
  - the overlay path `no-peer`, 1 device online (the hub).
- Each cell began with `--check` ok on twelve but the APK (`MISMATCH`, the candidate, as pre-registered).
- The user missed stage 1's stated time ("I missed the time am I still able to do it?"). Cell 1 had closed by itself,
  so nothing was lost.

## 2. Cell 1 — the LAN with `PRIVYHUB_REMOTE=1` (U)

| row | read | beside | |
| --- | --- | --- | --- |
| **U1** `remote_umbrella_config` | 20:39:58.8Z at the restart: the four `implied` (`1` / `floor` / `7000` / `1`); the cap `active` true, 7000, `valid_kbps` 4000-7000; `acts_on` the three remote classes; `lan` "today's, byte for byte" | B28 | **met** |
| **U2** `remote_config` | one, session 1, 20:42:14.8Z: **class `lan`, all four `in_force` false**, "not an overlay address" | B28 | **met** |
| **U3** the LAN unchanged | the encoder's first argv **`-b:v 7000k`** (`-maxrate` / `-bufsize` 7000k, the only encoder); 435 ladder rows, **0 with `path_class`, 0 with `start_rung`**, 0 `remote_cap_config`, 0 clamps; `wan_sessions.jsonl` 33 → 33; **`wan` in 0 / 23** in-game polls of `/status` and of stream-telemetry; the ladder at 7000 throughout (REFERENCE / PRESSURE samples, no transition) | B28's replay: 16 / 16 at 7000 | **met** |
| **U4** the clean-LAN numbers | **86 freezes, 7.4 a minute** (9.8 frames ≈ 0.16 s each); 2 timeouts (held 846 of 848); max hold 604 ms, max wait 656 ms; **8 stall pauses** (`client_stall` at 406-682 ms, each save → pause → 3 frames restored → resume ~153 ms); 1 silence-kind save (a 401.6-ms uplink silence); silences ≥ 250 ms **4.46 / 10 min** (max 402 ms); hitch **15.6 s / 10 min**; rendered 58.78 fps; max output gap 692 ms; 497 packets lost after FEC; `link_notice` 0 in 341 / 341 heartbeats | **CL-B15 cell C: 3.3 freezes a minute, 0 timeouts, 0 stall pauses, silences 0.89, hitch 3.5, 157 packets lost; G-A7's window: 0.0 / 2.6** | **not met** |

- **U4's reading:** the house's own loss this evening was 3.2× cell C's (497 against 157 packets after FEC) and the
  silences 5× (4.46 against 0.89 per 10 min). That is the link, not the umbrella. U3 shows the LAN path is today's
  code path.
- **4 of the 8 stall pauses** had an uplink silence ≥ 250 ms within 2 s (20:43:28-29, 20:46:44-45); the other 4 had
  none. The heartbeats carry no guard counters without the host flag, so whether a guard hold was open is not readable
  here. Cell 3 reads it.

## 3. Cell 2 — the overlay at home with `PRIVYHUB_REMOTE=1` only (R)

| row | read | beside (G4-S4) | |
| --- | --- | --- | --- |
| **R1** class and lines | `remote_config` session 1, 21:14:43.4Z: **class `remote-direct`, all four `in_force` true**; the newest `token_issued` **overlay** (21:14:34Z); the routing class at the stream overlay | G4-S4 ran the four explicit, path direct | **met** |
| **R2** the start rung | the first `sample` row (21:14:45.3Z): `{"kbps": 4000, "source": "floor", "requested": "floor", "active_list": [4000, 5000, 5500, 6000, 7000], "path_class": "remote"}`: **B's string plus a `requested` key**; the encoder's first argv **`-b:v 4000k`** (21:14:48.5Z) | floor 4000, `path_class` remote, the same list | **met** (the extra key disclosed) |
| **R3** the climb | **4000 → 5000 at 21:17:57.3Z (3 min 12 s in)**, **5000 → 5500 at 21:23:48.9Z (5 min 51 s later)**; the session ended at 5500 (13.55 min): **2 steps**, no decrease, 0 refused; `path_class` `remote` on 416 of 417 rows (the one `lan` is the `remote_cap_config` row) | one rung every ~3 min 07 s; 4000 → 7000 in ~12.5 min; 0 stalls in its sessions | **not met** (2 < 3) |
| **R4** the cap | `remote_cap_config` **once** (21:14:43.1Z): `active` true, `cap_kbps` 7000, `valid_kbps` 4000-7000; **0 clamps**. The row itself carries `path_class` `lan`: it is written at the switch to remote, before the ladder's class is set for the session | 0 clamps | **met** (the row's class disclosed) |
| **R5** `wan` | **`wan` in `/status` in 27 / 27** in-game polls and in stream-telemetry in 27 / 27 (absent in the 5 polls before the game). **The `wan_sessions.jsonl` row: NOT written:** 33 lines before cell 2, after cell 2, after cell 3's start (21:35:51Z) and after cell 3's close | — | `/status` **met**; the row **not written** (disclosed beforehand) |
| **R6** the stack's WAN exposure | **0 false holds:** no silence-kind save or hold; 2 silences ≥ 250 ms (1.51 / 10 min, max 333 ms). 5 stall pauses (`client_stall` 433-540 ms, 2-3 frames restored); 1 with a 333-ms uplink silence (21:18:36Z), 4 with none. `link_notice` 0 in 399 / 399 | 0 false holds; 2 holds, both at Home presses | **met** (the stall pauses beside it) |

- **Why R3 missed:** the ladder's samples read `RECOVERY_PROBATION` / `counting_clean_reports` at each rung, and
  `HOLD_DOWN` `blackout` 3 times at 5000 and 3 at 5500. The stall at 21:18:36Z (age 540 ms, a 333-ms uplink silence)
  came 39 s after the first step and restarted the climb's count. So the second step took 5 min 51 s. The ladder
  behaved as built under a real link event. G4-S4's sessions had none.
- Freezes: 61 in 13.6 min (4.5 a minute), 0 timeouts, max hold 527 ms. Hitch 8.1 s / 10 min; rendered 58.96 fps; max
  output gap 547 ms; 299 packets lost after FEC.
- **The `wan_sessions` row:** B (item 5, R5) expected cell 3's start to flush it. It did not:
  - the umbrella's telemetry object writes the row at the next remote session, or at the switch to a LAN session, in
    the same companion process;
  - cell 2's teardown restarted the companion (the drop-in removed), and cell 3 ran without the line;
  - this matches the standing G5-S1 note in `KNOWN_ISSUES.md` (the row is written only when a next session starts).
  - **For the trip:** the last remote session before any companion restart leaves no `wan_sessions` row.

## 4. Cell 3 — 1 % loss + `PRIVYHUB_LOSS_GUARD=1`, the B29 client (S)

| row | read | beside (CL-B15 cell L, `8b0fbb74…`) | |
| --- | --- | --- | --- |
| **S1** stall pauses drawn by guard holds | **12 `client_stall` → `desync_pause`** (ages 402-597 ms; each save → 3 frames restored → resume 147-157 ms); **0 uplink silences ≥ 250 ms in the whole session**, none within 2 s of any; 11 of the 12 have guard frames held in the heartbeats ±4 s (3-47 frames, 1-3 episodes), one (21:39:54.9Z, 525 ms) none | 9 | **not met** |
| **S2** `loss_guard_timeouts` | **0** | 1 | **met** |
| **S3** held = counter | **3,290 = 3,290** (and = in every heartbeat minute, unheld 0) | 2,478 / 2,485 | **met** |
| **S4** `loss_guard_max_hold_ms` ≤ 616 | **469 ms**; `loss_guard_max_wait_ms` 469 ms | (no key); max wait 685 ms | **met** |
| **S5** the cost | **411 freezes, 35.6 a minute** (24-46 per full minute; 8.0 frames ≈ 0.13 s each); hitch **55.6 s / 10 min**; rendered **54.48 fps**; max output gap 605 ms; 1,442 packets lost after FEC | **27.7 / 37.2 / 55.75**; 1,036 lost | stated |

- **S1's reading:**
  - in CL-B15 cell L the 9 pauses came from holds that aged the output past 400 ms; B29 meant to silence those;
  - here none of the 12 has a link silence behind it, and they cluster where the guard is holding;
  - their shape is CL-B15's: save at ~400-600 ms, 3 frames restored, resume ~150 ms.
  - The host's logs cannot say whether a hold was open at the instant of each stall. The client reports only the age.
  - **B29's suppression is not shown on the bench.**
- **For B:**
  - what "the last frame received" counts while the guard holds;
  - why ages reach 597 ms with no uplink silence and a max hold of 469 ms;
  - whether `sequence_gap_au_drops` (481 here) end the "received" clock.
- **S5:** more freezes than CL-B15 L (35.6 against 27.7 a minute), with ~40 % more packets lost this evening (1,442
  against 1,036). The shim's 0.992 % is the same.
- Host side: `loss_guard_config` `ignored` false, `NoRuntimeIdr`, `min_interval_ms` 500; 12 `keyframe_requests` rows
  (per minute). `link_notice` 0 in 341 / 341.

## 5. The CONFIRMED rule (CL-B7 §6, as pre-registered)

- **At the close (21:48:52Z):**
  - the seven properties empty (`adb_reads/properties_close.txt`);
  - the drop-in dir the twelve `.conf` only, no `e3_flag.conf`; `flags_absent` true in all three cells;
  - twelve lines, `--check` ok but the APK before the rule (`check_end_before_rule.json`);
  - the client on the LAN: Hub host empty, the newest `token_issued` lan (21:47:39Z); the band 5180 MHz, RSSI −68;
  - one device, paired (`client_end.json`); units: the companion and `privyhub-link-n1`.
- **Applied:**
  - **the three cells valid.** The client's behaviours where no flag acts are today's:
    - `link_notice` 0 in every heartbeat;
    - every save is `kind` `stall` (with a `client_stall`) or `kind` `silence` (on a real ≥ 400-ms uplink silence),
      with no save or hold without one;
    - every teardown runs `session_end_bye` → `state_save_skipped` `client_bye` → `session_ended`.
  - B29's intended difference: the `loss_guard_max_hold_ms` key is present, and the cap held (469 / 527 / 604 ms).
  - **→ `9719ea822ed5f7d13799ff7e02ba814cd0a2abe79b8a2e3d631d0aecb13c0110` CONFIRMED.**
- **The pin moved** (`cl_b16_pin.diff`; the predecessors in `pin_predecessors/` with `pin_predecessor_sha256.txt`):
  - `tools/e1_suite.py` `EXPECT_APK`; `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`; `tools/test_c3_l4_nft_night.py`;
  - `e1_suite --self-test` OK, `test_c3_l4_nft_night` 33 / 33, `test_e1_remote` 21 / 21, `git diff --check` clean
    (`pin_tests.txt`);
  - **`e3_state.py --check` ok on twelve, APK CONFIRMED** (`check_end.json`).
- **As pre-registered, CONFIRMED is about validity and today's behaviours, not the rows.** Stated plainly for the
  user:
  - S1 shows B29's purpose (no stall pause from a guard hold) is not met on the bench;
  - the stall pauses on this evening's LAN (8 in cell 1, 5 in cell 2) were not seen with `8b0fbb74…` in CL-B15 cell
    C, but that evening's LAN lost a third as many packets;
  - nothing here separates the APK from the link;
  - `8b0fbb74…` is kept at `PrivyHub/app/build/cl_b15_installed/app-debug.apk` if the user wants it back.

## 6. The reading (written beforehand), applied

- **U1-U3 met; R1, R2, R4 met; R3 not met → as read, G-A9 goes back to B with the rows.** It is not the user's
  question as pre-registered.
- **The one row that missed:** the climb was 2 steps in 13.6 min. The cause was a real link event that reset the climb
  count (§3), the ladder's built behaviour. The umbrella's own work was all there:
  - remote-direct, the four in force;
  - the 4000 floor and the remote list, the 7000 cap, 0 clamps;
  - `wan` in `/status`.
- **G-A9, in B's words (for the user, should they decide before B):** "Adopt `PRIVYHUB_REMOTE=1` as the thirteenth
  line? Away from home it turns on the four settings G4-S4 used — start at 4000 and climb, the remote ladder, the 7000
  cap, the WAN telemetry — by itself; at home nothing changes."
  - **The cost away:** every new session, a Home return too, starts at 4000 and needs ~12-15 min to reach 7000, longer
    when the link stalls (this cell: 5500 after 13.6 min).
  - **The off switch:** remove the drop-in `remote.conf` (the line), `systemctl --user daemon-reload`, restart the
    companion outside 04:30-05:30Z.
  - B's patch `patches/G-A9_REMOTE_ADOPTION_PREPARED.md` is NOT applied.
- **S1 not met (S2-S4 met) → the quiet guard does not stand as read; back to B with the rows (§4).**

## 7. State at the exit

- Twelve lines; no `e3_flag.conf`; `--check` ok; **APK `9719ea82…` CONFIRMED** on the onn, paired, on the LAN, 5 GHz;
  the seven properties empty.
- Running: `privyhub-companion` and `privyhub-link-n1` only (the three cell units and the dry unit collected).
- No sudo, no nft. The Opal was untouched. **No `setprop`.** adb was used for the install and state reads only.
- **The overlay hand steps were the user's.** No address or identifier in any kept file (`redact_check.txt`); the
  tailnet name never written. Nothing fetched.
- **Nothing deleted:** the one `__pycache__/` made by a syntax check in this dir was moved to /tmp.
- Nothing adopted. Nothing committed. `logs/cl_b16_git_status.txt`.

## 8. The user's lines, verbatim

1. "Read _cowork_prompt.txt in the repo root and follow it as my prompt."  (~20:32Z; stage 1)
2. "I missed the time am I still able to do it?"  (~21:09Z; a question, not a stage word)
3. "Stage 2"  (~21:11Z)
4. "Stage 3"  (~21:32Z)
