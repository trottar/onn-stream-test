# B25 — design, written and hashed before any B25 code (and before the replay is run)

Baseline: HEAD `da48629` (clean). B24 was already done and committed (`f114dee`, its record and dir present); B25 is
this run's only build. The APK today: `6bddafc0…a927` (B5 … B19 + B22), CONFIRMED.

## 1. The change (client only)

`debug.privyhub.link_notice`, as B13 did for `link_report` and B19 for `stall_signal` / `restart_guard`:

| value | before (B14) | after (B25) |
| --- | --- | --- |
| absent (`null`) | off | **ON** |
| empty `""` | off | **ON** |
| junk (`on`, `true`, `2`, …) | off | **ON** |
| `1` | on | on |
| `0` (after trim) | off | **off** = today's absent |
| a failed read (no `SystemProperties`, any throw) | off | **ON** (`parse(null)`) |

- Only `LinkNoticeFlag.parse` (`value?.trim() != "0"`) and `LinkNoticeFlag.fromSystem`'s catch (`parse(null)`) change,
  plus their comments. Nothing else in `LinkNotice.kt`; nothing in `NativeStreamActivity.kt` /
  `DiagnosticsActivity.kt` (they already follow the flag: the object, the view, the heartbeat key, the report keys, the
  diagnostics line).
- **Unchanged, as B14 built them:** the conditions (2.4 GHz at once; RSSI ≤ −72 dBm held 10 s; tx ≤ 54 Mbps held
  10 s), the wording (`LinkNoticeText`), once a session unless the band changes, the 30-s clear, the 500-ms UI tick,
  the sampler (B3's, 1 read/s at most, or the notice's own if `link_report=0`).
- **`0` = today's absent byte for byte:** with `0` the lazy `linkNotice` is `null` exactly as an absent property made
  it before, so no object, no view, no `&link_notice=` fragment (`linkNotice?.query() ?: ""` = `""`), no report keys,
  no diagnostics line. Proven by a script over the diff (only the flag object's lines change) and a parse table
  (`new("0") == old(null)`, and for every value `new(v) == old(v)` except absent / empty / junk, which flip to on).
- **The cost when on** (stated in the record): one `TextView` (GONE until shown); one `update()` per 500-ms UI tick
  (integer compares) reading the sampler B13 already runs; the heartbeat's `&link_notice=<bits>` (~15 bytes per 2 s);
  `link_notice_shown` / `_last_reasons` in the report; one line on the diagnostics page. No network call, no pause, no
  stream change. The host side (`PRIVYHUB_LINK_REPORT=1`, adopted by G-A3) already records the key and the
  `link_notice_shown` / `_cleared` rows: no host change.

## 2. The replay, run FIRST (read-only, before the default flips)

- **Inputs:** every `native_stream_heartbeat.log` in the tree's evidence since G-A3 that carries the link keys:
  `g_a3_2026-10-23`, `cl_b10_2026-10-23` (4 cells), `cl_b11_2026-10-24` (3), `cl_b12_2026-10-24` (3),
  `cl_b13_2026-10-25` (5 runs, the no-press attempt included), `g_a4_2026-10-24`, `g_a5_2026-10-26`,
  `g4_s4_2026-10-24` (off-site copy). Each input's sha256 is listed in the output. Also, as a supplement only, the
  live `logs/games/native_stream_heartbeat.log` (read-only; 2026-10-24T20:27Z onward) for sessions the evidence does
  not hold — rows already in an evidence file (same `received_at_utc`) are not counted twice. Before-G-A3 logs
  (LINK-R1, BENCH-R3, UX-R4) are listed for reference only, outside the gate.
- **Sessions:** a new session at a heartbeat whose `sequence` is ≤ the previous one's, or after a gap > 30 s.
- **The rule:** B14's `LinkNotice.update()` ported line for line to Python (thresholds −72 / 54, sustain 10 s, clear
  30 s, `band()` mapping, `shownThisSession`, re-arm on a band change, re-arm at a session's start). Each heartbeat's
  `link_rssi_dbm`, `link_tx_mbps`, `link_frequency_mhz` is a reading held until the next heartbeat; the rule is ticked
  every 500 ms on the host's `received_at_utc` clock, as the activity's UI tick. A heartbeat without link keys is a null
  reading (no change).
- **The port's check:** CL-B10 cell 4 ran the real client with `link_notice=1` on 2.4 GHz; its heartbeats carry the
  client's own `link_notice` bits. The replay's shown / reasons per heartbeat are compared with them and the
  disagreements counted (allowed: a ≤ 1-heartbeat offset at a transition, from the 1-s sampler vs the 2-s heartbeat).
- **Per session:** set, start (UTC, minute), heartbeats, the bands seen, RSSI min / median, tx min; would the notice
  show; reasons (band / RSSI / tx); first shown at (s after the first heartbeat); shown for (s, until the clear or the
  session's end); shows; clears.
- **The gate:** every session with a 2.4-GHz reading must show it (reason band). Every 5-GHz session that would show is
  listed with its reason, the readings that drove it, and its duration.
- **If any 5-GHz session would show:** the threshold that keeps every 5-GHz session in these sets quiet, stated as a
  number for the user and NOT changed: the RSSI threshold T = (the lowest RSSI held ≥ 10 s by any such session) − 1,
  and likewise tx; with what each would still catch (the weakest 5-GHz reads, the LINK-R1 / BENCH-R3 references), so
  the user can choose. B14's −72 / 54 stay in the code.
- The replay does not gate the build except: a 2.4-GHz session that would NOT show stops B25 (the rule or the port is
  wrong) and is reported.

## 3. Tests (JVM)

- **New `LinkNoticeDefaultOnTest`:**
  - the table above (absent / empty / junk → on; `1` on; `0` / ` 0 ` off); `fromSystem()` off-device → on (a failed
    read = on);
  - **absent → on:** the object built as the activity's lazy builds it (`if (LinkNoticeFlag.parse(null)) LinkNotice()
    else null`): 2.4 GHz → shown once at t = 0 in 60 s, B14's exact text, `&link_notice=1`; 5 GHz good (−68 dBm,
    195 Mbps) for 60 s → no event, `&link_notice=0` (the key present, 0);
  - **`0` → today's absent:** `parse("0")` = `old absent` = no object, the heartbeat fragment `""`, as before.
- **Moved, disclosed (as B13 / B19 did):** `LinkNoticeTest.flagTable` (absent / empty / junk now on; `0` off;
  `fromSystem()` off-device on) and `ClientDefaultsTest.absentIsOnAndZeroIsOff`'s `link_notice` line (`parse(null)` now
  true, plus `parse("0")` false). Their other lines unchanged.
- The whole JVM suite green (146 + the new tests).

## 4. The APK

B5 + B7 + B10 + B11 + B13 + B14 + B15 + B16 + B17 + B18 + B19 + B22 + B25 (B24 made no client change), built offline in
a fresh `/tmp/b_q26i25/` copy (companion/, tools/, tests/, PrivyHub/ only) with
`./gradlew :app:testDebugUnitTest --rerun :app:assembleDebug --offline --no-configuration-cache`; only the companion
and `privyhub-link-n1` active; 0 tree files newer than a build marker; the signer compared with `6bddafc0…`'s (digests
not printed); `apksigner verify`; entries compared; sha256 pinned; **NOT installed.**

## 5. Then

Record `evidence/B25_LINK_NOTICE_DEFAULT_ON_2026-10-26.md` + this dir (redact_check, manifest), `patches/B25_…md`,
KNOWN_ISSUES (insertions only: the band item), ROADMAP line, `logs/b25_git_status.txt`, SESSION_B_STATUS.txt,
SESSION_B_DONE_2026-10-26I.md (B25 appended; CL-B14 sketched with the new APK). Nothing committed, adopted, installed.
