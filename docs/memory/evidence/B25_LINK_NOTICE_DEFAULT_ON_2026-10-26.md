---
memory_schema: 1
as_of: 2026-10-26
baseline_commit: da48629 (clean; B24 already committed in f114dee)
---

# B25 — the 2.4-GHz link notice on by default (`debug.privyhub.link_notice`: absent / empty / junk = ON, `0` off); the replay MET; the APK `fcd924c2…` built, NOT installed

**Classification: BUILT**, as B13 did for `link_report` and B19 for `stall_signal` / `restart_guard`. This follows the
user's decision of 2026-10-26 (verbatim "Yes"): G-A5's precondition read at 02:59Z found the onn on 2.4 GHz (2412 MHz)
although CL-B13 closed on 5 GHz, nobody had touched the band, and nothing told anyone.
- **The replay, run first:** B14's rule over every heartbeat with the link keys since G-A3, 45 sessions.
  - **All 3 sessions on 2.4 GHz show the notice; none of the 42 on 5 GHz does.**
  - The port matches the real client's own `link_notice` bits in CL-B10 (9 sessions, 0 disagreements).
- **Tests:** `LinkNoticeDefaultOnTest` 4; JVM **150 / 150**. A mutation back to B14's flag fails 5 tests.
- **Proof** `proof_zero_is_today.md`: **PROVEN**. Only the flag object's parse and catch changed, and `0` gives B14's
  absent.
- **The APK** (B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19 + B22 + B25; B24 made no client change):
  **`fcd924c2…9b96`**, pinned, **NOT installed.**
- NOT ADOPTED; no live run; nothing committed.

Design `b25_2026-10-26/design_written_before_code.md`, sha256 `b75e96e6…92635d`, hashed **03:53:39Z**, before the
replay ran and before any B25 code.

## 1. The replay (`replay_link_notice.py`, `replay_output.json`, `replay_table.md`)

**Method:**
- B14's `LinkNotice.update()` ported line for line.
- Each heartbeat's `link_rssi_dbm` / `link_tx_mbps` / `link_frequency_mhz` is held until the next heartbeat, and the
  rule ticks every 500 ms on the host's `received_at_utc`.
- A new session starts when `sequence` restarts or after a gap of more than 30 s.

**Inputs:**
- G-A3, CL-B10 c1-c4, CL-B11 c1-c3, CL-B12 c1-c3, G-A4, G4-S4 (off-site), CL-B13 (c1a, c1, c2, c3a, c3b), G-A5. Each
  file's sha256 is in `replay_table.md`.
- The live `logs/games/native_stream_heartbeat.log` (read-only) as a supplement. Its 16 sessions are all already in an
  evidence file, so it added 0.

**Results:**

| | sessions | would show |
| --- | --- | --- |
| **2.4 GHz** | 3 (all CL-B10 cell 4, 2026-10-24 03:53-04:04Z) | **3 / 3**: reason band, at the first tick (0.0 s), shown for the whole session (45 / 3 / 583 s) |
| **5 GHz** | 42 (G-A3, CL-B10..CL-B13, G-A4, G-A5, G4-S4) | **0 / 42** |

**Checks:**
- **The port's check:** CL-B10's sessions carry the real client's own `link_notice` bits (cell 4 ran with
  `link_notice=1`): `[1]` on 2.4 GHz, `[0]` on 5 GHz. **0 disagreements** in 9 sessions.
- **No 2.4-GHz session has run since CL-B10 cell 4.** G-A5's 2.4-GHz reads (02:59Z) came before any stream. Its
  session (03:10Z) ran on 5 GHz. Had a game started at 02:59Z, the notice (default-on) would have shown at the first
  tick.
- **Before G-A3, for reference only** (outside the gate): BENCH-R3's 11 sessions on 2.4 GHz all show (UX-R4's copy is
  the same evening). LINK-R1's session on 5 GHz does not.

**The 5-GHz margin.** No 5-GHz session would show, so no threshold change is needed. These are the numbers for the
user; nothing was changed:
- **RSSI:**
  - The lowest RSSI any 5-GHz session held for 10 s is **−70 dBm** (G-A4, CL-B12 c1, G-A5). That is **2 dB** above
    B14's −72.
  - The loosest threshold that keeps every one of these sessions quiet is **−71 dBm** ("≤ −71 held 10 s"). At **−70**,
    G-A4, CL-B12 c1 and G-A5 would show the weak-signal notice.
  - B14's **−72** stays. It still catches a link 2 dB weaker than this house's worst 5-GHz minute.
- **tx:**
  - The lowest tx held for 10 s on 5 GHz is **130 Mbps**, against B14's 54.
  - Single-heartbeat dips (65 in G-A5, 97 in CL-B12 c1 / CL-B13 c1a) never held 10 s.
  - On 2.4 GHz, tx ≤ 54 held 10 s is common (CL-B10 c4: 9 Mbps; BENCH-R3: 54). The band reason already covers it.
- **The method's bias:** the replay sees one 1-s sample per 2-s heartbeat. A reading that held ≤ T for 10 s in the
  client's samples also held ≤ T in the heartbeats, so for the 5-GHz-quiet claim the replay can only over-count, never
  miss a show.
- **Reasons stay as shown:** the reasons recorded are those at the moment of the show (B14 keeps them until the clear).
  CL-B10 c4's slow tx (9 Mbps held 10 s) came after the band show and does not re-show.

## 2. Built (`b25.diff`)

| property value | B14 | **B25** |
| --- | --- | --- |
| absent / empty / junk (`on`, `true`, `2`) | off | **ON** |
| `1` | on | on |
| `0` (trimmed) | off | **off = B14's absent** |
| a failed read | off | **ON** (`parse(null)`) |

- **`LinkNotice.kt`:** only `LinkNoticeFlag.parse` (`value?.trim() != "0"`) and `fromSystem`'s catch (`parse(null)`)
  change, plus comments.
- **Unchanged, as B14 built them:**
  - the conditions: 2.4 GHz at once; RSSI ≤ −72 held 10 s; tx ≤ 54 held 10 s;
  - the wording: "Wi-Fi: 2.4 GHz / Use your router's 5 GHz Wi-Fi for this box.";
  - once a session unless the band changes; the 30-s clear; the 500-ms tick.
- **No other file changes:** `NativeStreamActivity.kt` and `DiagnosticsActivity.kt` are byte-identical. Two comments
  in them still read "only with debug.privyhub.link_notice=1"; they were left as hashed (the design said those files
  stay untouched).
- **The cost when on:**
  - one `TextView`, GONE until shown;
  - one `update()` per 500-ms UI tick: integer compares on the sample B3's sampler already takes (≤ 1 read/s, no
    network call);
  - `&link_notice=<bits>` in each heartbeat (~15 B per 2 s);
  - `link_notice_shown` / `link_notice_last_reasons` in the report;
  - one line on the diagnostics page ("Link notice: none shown" or the last text).
  - **No pause, no stream change.**
- **The host:** no change. `PRIVYHUB_LINK_REPORT=1` (G-A3, adopted) records the key in the heartbeat row and writes
  `link_notice_shown` / `link_notice_cleared` rows (B14's `companion/link_notice.py`).

## 3. Tests (`tests_jvm.txt`, `tests_link_notice_default_on.xml`, `tests_mutations.txt`)

**`LinkNoticeDefaultOnTest`, 4:**
- **the table:** absent / empty / blank / `1` / junk → on; `0`, ` 0 `, `0\n` → off; `fromSystem()` off-device (a
  failed read) → on;
- **absent → 2.4 GHz shown once:** the object built as the activity's lazy builds it shows once at t = 0 in 60 s, with
  B14's exact text and `&link_notice=1`;
- **absent / empty / junk → 5 GHz good is quiet:** no event in 60 s, and `&link_notice=0` (the key present, 0). At
  −70 dBm for 120 s it stays quiet; at −72 held 10 s it shows (B14's rule);
- **`0` → B14's absent:** no object; the heartbeat fragment is `""`; `parse("0")` = B14's `parse(null)`; `1` is
  unchanged.

**Moved, disclosed** (as B13 / B19 did):
- `LinkNoticeTest.flagTable`: absent / empty / junk are now on, `0` off, `fromSystem()` off-device on;
- `ClientDefaultsTest.absentIsOnAndZeroIsOff`: `parse(null)` is now true, and a `parse("0")` false line was added.
- Their other lines are unchanged.

**Results:**
- **JVM 150 / 150** (146 + 4), in the APK's build run.
- **Mutation:** with B14's `== "1"` put back (in the copy only), 5 tests fail. `zeroIsTodaysAbsent` passes, as it must.
- **Host:** unchanged by B25. Every suite under `tests/` was run from the copy as a no-change check: **29 / 29 green**
  (`tests_regression_after_b25.txt`). The four `tools/` tests fail exactly as in B24's baseline run (unrelated, as
  on HEAD).

## 4. The APK (`apk_sha256.txt`, `build_console.txt`)

**`fcd924c28cbf70a85bb9a886caabcb07873eee2d028b6538284fce5a7ae39b96`**, 9,638,234 B.
- **Build:** offline in a fresh `/tmp/b_q26i25/PrivyHub` copy (companion/, tools/, tests/, PrivyHub/ only), with
  `:app:testDebugUnitTest :app:assembleDebug --rerun-tasks --offline --no-configuration-cache`.
  - The first build of the same sources (`--rerun :app:assembleDebug`) gave the same bytes.
  - Only the companion and `privyhub-link-n1` were active.
  - **0 tree files newer than the build marker.**
- **Checks:** signer = `6bddafc0…`'s (digest lines compared, not printed); `apksigner verify` OK; 944 entries; **only
  `classes3.dex` differs** (389,044 → 389,056 B).
- **NOT installed;** `6bddafc0…` stays CONFIRMED on the onn. A copy is at `/tmp/b_q26i25_scratch/apk/`.
- **Disclosed:** the host-suite run left a `logs/` directory (`impairment.jsonl`, written by a test) in the copy, beside
  companion/, tools/, tests/ and PrivyHub/, as in B24's copy. Nothing was deleted.

## 5. For CL-B14 (A)

- Install `fcd924c2…`; read every client property back EMPTY. The default is the test.
- **On 5 GHz with no property:**
  - every heartbeat carries `link_notice=0` (armed, not shown);
  - no `link_notice_shown` row; the report has `link_notice_shown` 0;
  - B14's line is on the diagnostics page ("Link notice: none shown").
- **If the onn is found on 2.4 GHz** (as at G-A5's 02:59Z): the notice at the session's first tick, and one
  `link_notice_shown` (reasons 1). Record it and do not switch the band without the user.
- **The CONFIRMED rule (CL-B7 §6):** every cell valid and today's behaviours where no flag was set → `fcd924c2…`
  CONFIRMED, and the pin moves (`tools/e1_suite.py` `EXPECT_APK`, `tools/c3_l4_nft_night.py` `ADOPTED_APK_SHA256`
  and its test). Otherwise `6bddafc0…` goes back on. The notice being on by default is the one intended change from
  `6bddafc0…`.

## 6. Files

- **`b25_2026-10-26/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `replay_link_notice.py`, `replay_output.json`, `replay_table.md`, `replay_run_at.txt`;
  - `b25.diff`, `proof_zero_is_today.py` / `.md`;
  - `tests_jvm.txt`, `tests_link_notice_default_on.xml`, `tests_mutations.txt`, `tests_regression_after_b25.txt`;
  - `build_console.txt`, `apk_sha256.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `PrivyHub/app/src/main/java/streaming/LinkNotice.kt`;
  - `PrivyHub/app/src/test/java/streaming/LinkNoticeDefaultOnTest.kt` (new), `LinkNoticeTest.kt`,
    `ClientDefaultsTest.kt`;
  - `patches/B25_LINK_NOTICE_DEFAULT_ON.md`, `logs/b25_git_status.txt`.
- **The rules held:**
  - no stream, no restart, no adb, no sudo, no nft; the Opal untouched;
  - nothing of `privyhub-link-n1` touched; nothing of A's touched; G-A6 not touched;
  - nothing fetched, deleted, adopted, installed or committed.
