---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c (+ B11-B13 uncommitted)
---

# B14 — the "any house" link notice: the client tells the user plainly when its Wi-Fi is 2.4 GHz or weak

**Classification: BUILT** behind `debug.privyhub.link_notice=1` (client). The host logs it on `PRIVYHUB_LINK_REPORT=1`
(B3's flag, the line G-A3 would adopt).
- **Client:** 7 JVM tests on a fake Wi-Fi feed; the suite is **114 / 114**. Property absent = the predecessors: only
  added lines (55 + 15), all in the allowed forms.
- **Host:** 4 tests; B3's 9 unchanged. Flag absent = the predecessors (AST, 2 / 2).
- **The APK** (B5 + B7 + B10 + B11 + B13 + B14) **`da09e154…6cf`**, rebuilt and pinned, **NOT installed**.
- NOT ADOPTED; no live run; nothing committed.

Design `b14_2026-10-23/design_written_before_code.md`, sha256 `c4e1564a…a9b965`, hashed **17:31:46Z, before any B14
code**.

## 1. What it does

- **The input:** the client's own link reading (B3's `LinkSample` from `WifiManager.getConnectionInfo()`, no network
  call). It comes through B3's sampler (on by default since B13), or the notice's own sampler if `link_report=0`. It is
  evaluated on the activity's existing 500-ms UI tick.
- **Shown:**
  - at once when the band reads **2.4 GHz**;
  - or when **RSSI ≤ −72 dBm** or **tx ≤ 54 Mbps** has held **10 s**.
  - The thresholds come from LINK-R1 / BENCH-R3: −68 on both bands is normal for this house. On 5 GHz 0 % of
    heartbeats read tx ≤ 54; on 2.4 GHz 1.7 %, and 52 % inside BENCH-R3's cluster.
- **Cleared:** after **30 s** good (not 2.4 GHz, RSSI > −72, tx > 54).
- **At most once a session unless the band changes.** A band change re-arms it; a new session re-arms it.
- **Where:** a small line at the stream's bottom-left, over the picture, not blocking it. The same text shows as
  "Last link notice: …" at the top of the diagnostics page while the app runs.
- **Nothing about the stream changes:** no pause, no step, no restart, no network call.
- **The heartbeat** carries `link_notice=<bits>` (0 = not shown; 1 band 2.4 GHz, 2 weak RSSI, 4 slow tx). The report
  carries `link_notice_shown` and `link_notice_last_reasons`.
- **The host** (`PRIVYHUB_LINK_REPORT=1`) records `link_notice` in the heartbeat row. On a transition it writes
  **`link_notice_shown`** (reasons, names, band / RSSI / tx) or **`link_notice_cleared`** in the recovery log, so a
  record can say the user was told.

## 2. The wording (the user's to edit: `LinkNotice.kt`, `LinkNoticeText`)

| condition | line 1 (what it sees) | line 2 (the one thing to do) |
| --- | --- | --- |
| 2.4 GHz | `Wi-Fi: 2.4 GHz` | **Use your router's 5 GHz Wi-Fi for this box.** |
| weak, 5 GHz | `Wi-Fi: weak signal (−74 dBm)` | Move this box or the router closer, or use a wired connection. |
| slow, 5 GHz | `Wi-Fi: slow link (48 Mbps)` | Use the 5 GHz network or move closer to the router. |
| several | joined, e.g. `Wi-Fi: 2.4 GHz, weak signal (−74 dBm)` | the 2.4-GHz line wins |

On this house's month (2.4 GHz, −68 dBm) it would have read **"Wi-Fi: 2.4 GHz — Use your router's 5 GHz Wi-Fi for this
box."** at the first tick of every session.

## 3. Tests

**Client, `LinkNoticeTest` (7, readings every 500 ms on a fake clock):**
- the flag table;
- **2.4 GHz → shown at t = 0, once in 60 s**, the exact text;
- **5 GHz good → cleared at 30 s**, not before;
- the band changed (2.4 → 5 → 2.4) → shown again; weak, cleared, then weak again on the same band → not shown; a new
  session → shown;
- **RSSI −72 → shown at 10 s**, not before; −71 never;
- **tx 54 for 9.5 s**, one good reading, then 48 → shown 10 s after the dip (it reset);
- a slow 5-GHz link keeps it up; a null reading changes nothing; the band mapping.
- The suite: **114 / 114**.
- *Fixed during testing, disclosed:* the first version compared the band with the band at the last show, so
  2.4 → 5 → 2.4 did not re-arm. It now re-arms on any band change since.

**Host, `tests/link_notice` (4):**
- the transitions (shown once, cleared once, repeats silent; the reasons' names);
- the heartbeat field only with the link report's flag; an older client's heartbeat unchanged;
- the import follows the flag; the hook shapes.
- **B3's `link_report` 9 are unchanged and green.** The new guards are spelled so B3's shape tests count as before.
- **Regression:** every suite under `tests/` is green from the copy. The four `tools/` tests fail as on HEAD.

**Proofs:**
- `proof_flag_absent_client.md` **PROVEN**: NativeStreamActivity 0 removed / 55 added, DiagnosticsActivity 0 / 15;
- `proof_flag_absent_host.md` **ALL IDENTICAL** (plugins 5 items, heartbeat 1).

## 4. The APK (`apk_sha256.txt`, `build_console.txt`, `tests_jvm.txt`)

**`da09e154bdaf1b159fc90d787333b1090e4723b110cf82ef25b9acd7702ee6cf`**, 9,704,533 B.
- It carries B5 + B7 + B10 + B11 + B13 + B14 and supersedes B13's `df185d25…`.
- Built offline in `/tmp/b_q23e/PrivyHub` with `--no-configuration-cache`, only `privyhub-companion` and
  `privyhub-link-n1` active; **0 tree files newer than the marker**.
- The same signer as `bf5114a2…`; 944 entries; `classes3.dex` / `classes4.dex` differ (the activity and the
  diagnostics page).
- **NOT installed.**

## 5. Checked in CL-B10 (A)

- **With the user's permission to switch the band:** one cell on 2.4 GHz with `setprop debug.privyhub.link_notice 1`.
  Expect:
  - the notice on screen at the session's start (a photo or the user's word);
  - one `link_notice_shown` (reasons 1) in the recovery log, `link_notice=1` in the heartbeats;
  - after switching back to 5 GHz, `link_notice_cleared` ~30 s later.
- **Without that permission:** the fake feed above is the check, plus a 5-GHz cell that must show **no** notice (0
  rows, `link_notice=0`).

## 6. Files

- **`b14_2026-10-23/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b14.diff`, `proof_flag_absent_client.py` / `.md`, `proof_flag_absent_host.py` / `.md`;
  - `tests_jvm.txt`, `tests_link_notice.xml`, `tests_link_notice_host.txt`, `tests_regression.txt`;
  - `build_console.txt`, `apk_sha256.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `PrivyHub/app/src/main/java/streaming/LinkNotice.kt` (new), `NativeStreamActivity.kt`,
    `diagnostics/DiagnosticsActivity.kt`, `PrivyHub/app/src/test/java/streaming/LinkNoticeTest.kt` (new);
  - `companion/link_notice.py` (new), `plugins/games.py`, `games/native_stream_heartbeat.py`, `tests/link_notice/`
    (new);
  - `docs/memory/patches/B14_LINK_NOTICE.md`, `logs/b14_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; nothing fetched, deleted, adopted or committed.
