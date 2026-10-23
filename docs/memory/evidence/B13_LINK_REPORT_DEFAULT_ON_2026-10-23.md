---
memory_schema: 1
as_of: 2026-10-23
baseline_commit: 3eb900c (+ B11 / B12 uncommitted)
---

# B13 — the link report on by default in the client; the ninth adopted line prepared, not applied

**Classification: BUILT (client) + PREPARED (host).**
- **The client:** `debug.privyhub.link_report` absent now means **ON**; `0` turns it off.
  - The JVM suite is 107 / 107. B3's two flag tests were changed to the new meaning (disclosed).
  - **The APK** (B5 + B7 + B10 + B11 + B13) `df185d25…5d63` is pinned, NOT installed. B14's rebuild supersedes it.
- **The host:** `PRIVYHUB_LINK_REPORT` stays a flag. The adoption is written **only** as
  `docs/memory/patches/G-A3_LINK_REPORT_ADOPTION_PREPARED.md`:
  - the drop-in's content;
  - the tools' diff, tested on a scratch copy; `git apply --check` OK against the tree, not applied;
  - G-A3, sketched for A.
  - **No drop-in written, the tree's `tools/` unchanged, no restart.**
- NOT ADOPTED; no live run; nothing committed.

Design `b13_2026-10-23/design_written_before_code.md`, sha256 `ad1515ae…78d5a`, hashed **17:27:58Z, before any B13
code**.

## 1. Why

- LINK-R1: on 5 GHz, 0 uplink silences and 0 hitch seconds per 10 min. On 2.4 GHz, 16-22 and 20 in every room.
- The onn was on 2.4 GHz at −68 dBm all month, and no report carried it. UX-R4's two events, the nights that
  mattered, have no link beside them.
- The link report is diagnostics only (B3). Off by default, it was absent exactly when needed.

## 2. The client (`b13.diff`, `proof_change_client.md`)

- **`LinkReportFlag.parse`:** `== "1"` became `!= "0"`.
- **`fromSystem()`:** a failed read is treated as absent, so on.
- These two lines and the doc comment are the whole change. The activity's sampler already follows `fromSystem()`.
- **The cost, stated:**
  - one `WifiManager.getConnectionInfo()` at most once a second (`LinkSampler`), shared by the two 2-s report threads
    (the heartbeat and the client-health post), never on the receive path;
  - ≤ 5 integer keys (~80 bytes) per heartbeat, and a `link` object per client-health post.
- **No permission changes:** `ACCESS_WIFI_STATE` is already declared (a normal permission, no prompt). No SSID, BSSID,
  MAC or address is read or sent (B3).
- **Tests:** the new flag table (absent / empty / `1` / `true` → on; `0`, ` 0 ` → off) and the off-device read = on.
  B3's other 4 tests are unchanged.
- **The APK:** `df185d25e05841ec1c80361509cdef0a9caf0c707a5a60e0f0ff0387eb9f5d63`, 9,619,714 B.
  - Built offline in `/tmp/b_q23e/PrivyHub` with `--no-configuration-cache`, only `privyhub-companion` and
    `privyhub-link-n1` active; 0 tree files newer than the marker.
  - The same signer and the same 944 entries as `bf5114a2…`; only `classes3.dex` differs.
  - NOT installed.

## 3. The host: G-A3 prepared (`patches/G-A3_LINK_REPORT_ADOPTION_PREPARED.md`)

- **The drop-in content** (`link-report.conf`: `Environment=PRIVYHUB_LINK_REPORT=1`): not written.
- **`tools/e1_suite.py`:** `LINK_REPORT` in `ADOPTED` (nine); the preflight's `drop_in_link_report` and its `ok` term.
- **`tools/e3_state.py`'s docstring;** the "eight" comments in `e1_remote.py` / `test_e1_remote.py`.
- **Tested on a scratch copy** (`ga3_tools.diff`, `ga3_tests_before_after.txt`):
  - `e1_suite --self-test` OK before and after; `len(ADOPTED)` 8 → 9;
  - `test_e1_remote` shows the same docs-fixture error on both sides;
  - `git apply --check` OK against the tree.
- **The readers that count eight are listed, not changed:** the stale `ADOPTED_E3`; past drivers; the nightly watch,
  which loads `e1_suite` once and reads no `ADOPTED`.

## 4. What the ladder could do with the link keys (not built; for later)

**A rung cap on a weak link.**
- The data says the band is most of the flapping:
  - 2.4 GHz: 16-22 uplink silences and 20 hitch seconds per 10 min in every room;
  - 5 GHz: 0 and 0 (LINK-R1);
  - BENCH-R3's 42-silence cluster sat where the tx rate fell to 27-81 Mbps.
- So when the heartbeat's `link_frequency_mhz` reads 2.4 GHz, or `link_tx_mbps` ≤ 54 for most of a window, the ladder
  could cap the top rung (7000 → 6000, say). No rule today reads a fact about the link before the loss arrives.
- **The caution:** LAN-R2 found a lower rate buys nothing against *random* loss. A cap on a weak link is only worth
  building if the cap measurably cuts the uplink silences or hitch seconds at 2.4 GHz.
  - That would be a bench pair: 2.4 GHz at 7000 against 6000, the link report on.
  - It may well show the rate is not the lever (the uplink silences are the radio's, not the bitrate's). In that case
    the right response is the notice (B14), not the ladder.

**A `lan_bidir` second term from the tx rate.**
- LAN-R2's `bidir` rule asks for unrecoverable FEC groups and uplink silences together. That second term is a lagging
  symptom: the silences have already happened.
- The client's tx link rate is a leading, physical one: BENCH-R3 read ≤ 54 Mbps on 52 % of heartbeats inside the
  cluster, and 0.9 % elsewhere.
- So a second term "tx ≤ 54 Mbps in ≥ 3 of the window's 5 heartbeats" could replace or join the silence term. It
  would fire on the link's own report rather than on its damage.
- **The cost:** it depends on the client reporting (B13 makes that the default), and on one rule threshold read from
  two windows.
- It should be replayed on BENCH-R3, LINK-R1 and the nightly watch's rows before anything is built. The replay should
  require 0 false asks on 5 GHz.

## 5. Files

- **`b13_2026-10-23/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `b13.diff`, `proof_change_client.md`, `tests_jvm.txt`;
  - `build_console.txt`, `apk_sha256.txt`;
  - `ga3_tools.diff`, `ga3_tests_before_after.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:**
  - `PrivyHub/app/src/main/java/streaming/LinkReport.kt`, `PrivyHub/app/src/test/java/streaming/LinkReportTest.kt`;
  - `docs/memory/patches/G-A3_LINK_REPORT_ADOPTION_PREPARED.md`, `docs/memory/patches/B13_LINK_REPORT_DEFAULT_ON.md`;
  - `logs/b13_git_status.txt`.
- **The rules held:**
  - no stream, no restart, no adb, no sudo, no nft; the Opal untouched;
  - nothing of `privyhub-link-n1` touched;
  - the drop-in directory untouched;
  - nothing fetched, deleted, adopted or committed.
