# B13 — the link report on by default in the client, and the ninth adopted line prepared: design, before any B13 code

Baseline HEAD 3eb900c (+ B11 client, B12 host; uncommitted). Queue: `handoffs/QUEUE_2026-10-23E.md` §B13. Data:
LINK-R1 (5 GHz: 0 silences / 0 hitch s per 10 min; RSSI −68 on both bands; tx ≤ 54 Mbps in 0 % of 5-GHz heartbeats
against 1.7 % on 2.4 GHz), BENCH-R3 §7 (the tx rate falling to 27-81 Mbps beside E-on's 42-silence cluster), UX-R4 §3
(no link report on the nights that mattered), B3 (the module, the permission).

## 1. The client: `debug.privyhub.link_report` absent = ON

- `LinkReportFlag.parse`: **`0` → off; anything else, absent / empty included → on.** `fromSystem()`: a failed read is
  treated as absent → on. Two changed lines (plus the doc comment), stated; B3's `LinkReportTest` flag table and its
  "no property is off" test change to the new meaning (disclosed). Nothing else in the client changes: the activity's
  `linkSampler` already follows `fromSystem()`.
- **The cost, stated:** `LinkSampler` reads `WifiManager.getConnectionInfo()` at most once a second, shared by the two
  2-s report threads (the heartbeat and the client-health post), never on the receive path; ≤ 5 integer keys
  (~80 bytes) on each heartbeat and a `link` object on each client-health post. **No permission changes:**
  `ACCESS_WIFI_STATE` is already declared (a normal permission, no prompt); no SSID / BSSID / MAC / address is read or
  sent (B3).
- **The APK** (B5 + B7 + B10 + B11 + B13) built offline in `/tmp/b_q23e` with `--no-configuration-cache`, only the
  companion and `privyhub-link-n1` active, pinned by sha256, NOT installed.

## 2. The host: the ninth line PREPARED, not applied

`PRIVYHUB_LINK_REPORT` stays a flag. The adoption is written as **`docs/memory/patches/G-A3_LINK_REPORT_ADOPTION_PREPARED.md`
only**, the way G-A2 was done:
- the drop-in's content (`~/.config/systemd/user/privyhub-companion.service.d/link-report.conf`: `[Service]` /
  `Environment=PRIVYHUB_LINK_REPORT=1`) — **not written** (that is the adoption, the user's say-so);
- `tools/e1_suite.py`: `LINK_REPORT` in `ADOPTED` (nine), the preflight's `drop_in_link_report`, the `ok` term;
- `tools/e3_state.py`: the docstring (nine);
- `tools/e1_remote.py` / `tools/test_e1_remote.py`: the comments that say eight;
- the readers that count eight, listed (the stale `ADOPTED_E3` in `d7_regression.py` / `c3_l4_nft_night.py`, past
  evidence drivers under their manifests): not changed;
- the diff made in a scratch copy and embedded; its tests (`e1_suite --self-test`, `test_e1_remote`) run on that copy
  before / after; **nothing applied to the tree's tools or to the drop-in directory**;
- G-A3 sketched for A: the write, daemon-reload and restart (the user's go), `--check` on nine, a confirmation window,
  and `adb shell setprop` no longer needed with this APK.

## 3. What the ladder could do with the link keys (not built; one paragraph each in the record)

- a rung cap when the band reads 2.4 GHz or tx ≤ 54 Mbps;
- a `lan_bidir` second term from the tx rate.

## 4. Tests

- JVM: the new flag table (absent / empty / `1` / other → on; `0` → off), off-device read = on; the rest of B3's tests
  unchanged; the suite.
- The G-A3 patch: its diff applies to a scratch copy of `tools/`; `e1_suite --self-test` and `test_e1_remote` there,
  before and after.
