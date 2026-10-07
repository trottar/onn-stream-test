---
memory_schema: 1
as_of: 2026-10-07
baseline_commit: ccee2f5
---

# E3-S6A — the cached guide index, adopted

**Classification: ADOPTION STANDS.** Every pre-registered clause holds on
the adopted state (`e3_s6a_verdict.json`). **The companion's default
environment now carries `PRIVYHUB_EPG_GUIDE_INDEX=cached`** through its
own drop-in, beside the live default. This is the first E3 adoption.

- The user's words, 2026-10-07: **"1. Adopt"**.
- What is adopted: E3-S6's memory half (MEMORY ACCEPTED). Its STREAM half
  was REJECTED and is **not** claimed. Grabs during a stream are roughly
  half as damaging, not fixed; tonight's CONC run confirms that.
- Nothing else adopted; nothing committed.

**Context:**

- Task: `handoffs/E3-S6A_GUIDE_INDEX_ADOPTION_TASK.md`, item 1 of
  `handoffs/QUEUE_2026-10-07.md`.
- **Baseline commit: `ccee2f5`**, the user's queue-B commit.
- Files: `e3_s6a_2026-10-07/`.
- Timeline (UTC, 2026-10-07):

  | time | what |
  | --- | --- |
  | 04:15:37 | preconditions held (E2's final state; `precondition.json`) |
  | **04:15:49** | **the drop-in written, `daemon-reload`, the unit restarted**; environ the two lines |
  | 04:16:03 | the state check patched; `e3_state.py` ok on the adopted state |
  | 04:16:16-04:16:48 | the smoke: six forced refreshes; the index built on the first |
  | **04:17:45** | **pre-registration hashed** (`ac6593f3…d448`) |
  | 04:17:51-05:29:47 | PS1-STREAM, META, CONC; all OK (PS1-STREAM reached PLAYING on its second tap, as usual) |

## 1. The adoption

- **The drop-in**, separate from `adaptive.conf` (copy `epg-index.conf`,
  sha256 `5f99559a…e08c`):

  ```ini
  # ~/.config/systemd/user/privyhub-companion.service.d/epg-index.conf
  [Service]
  Environment=PRIVYHUB_EPG_GUIDE_INDEX=cached
  ```

  `adaptive.conf` and the unit file are untouched. `daemon-reload`, then a
  restart of the unit.
- **Verified:**
  - the environ before was the live default only (`environ_before.txt`);
  - after, it is **exactly** `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` and
    `PRIVYHUB_EPG_GUIDE_INDEX=cached` (`environ_after.txt`);
  - the manager carries none;
  - `systemctl --user cat` lists both drop-ins.
- **The index file.** `data/epg/metadata/guides_index.json` was absent
  at the restart. The first grab built it (`smoke.jsonl`):
  - the file's mtime is 0.57 s after that grab started;
  - that grab took 5.7 s in all; the next five took 2.9-8.1 s;
  - **3,268,095 bytes, sha256 `65644985…681b`, 13,555 channels**, keyed
    to the metadata file's size and mtime;
  - the companion's PSS went 28 → 62 MB through the build. Each run's
    restart then started from the saved file.
- **The six forced refreshes** were all ok (84 / 82 / 64 / 43 / 37 / 34
  programmes).
- **Candidates** (`cands_check.py` → `cands_check.json`; offline, in its
  own process). The adopted index's candidates are **identical** for all
  six channels to:
  - a fresh parse of today's metadata file;
  - E3-S6's smoke dump, by both of its paths.
- **The state check** (`patches/E3-S6A_GUIDE_INDEX_ADOPTION_STATE_CHECK.md`,
  `e3_s6a_state_check.diff`). In `tools/e1_suite.py`, the preflight, the
  teardown, the post-restart check and the final state now expect
  `ADOPTED = [live, index]`. The preflight also checks that the index
  drop-in is listed. `tools/e3_state.py` reads through it.
  - `tools/d7_regression.py` and `tools/c3_l4_nft_night.py` were not
    changed. They still accept only the live default and would refuse the
    adopted environ; each needs the same one-name extension before its
    next use.
- **Kill switch** (`TOOLS.md`): delete `epg-index.conf`, then
  `daemon-reload`, then restart. The index file may stay; it is rebuilt
  on demand. With the drop-in gone, grabs use today's parse again, byte
  for byte.

## 2. Verification on the adopted state

No flag was set for these runs; the adopted default ran.

| | PS1-STREAM | META | CONC | E3-S6 control | E3-S6 META r1 | E3-S6 CONC r1 / r2 | E2 PS1-STREAM | E2 META | E2 CONC r1 / r2 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| host CPU % | **10.4** | **10.6** | 22.2 | 11.5 | 10.2 | 22.2 / 21.4 | 11.7 | 9.8 | 20.5 / 21.9 |
| companion CPU, % of a core | 23.9 | **0.23** | 26.5 | 24.8 | 0.22 | 26.0 / 24.5 | 24.3 | 7.6 | 33.1 / 33.5 |
| companion PSS first → last MB | 36.7 → 38.4 | **32.5 → 33.6** | **43.0 → 47.0** | 35.8 → 41.9 | 32.5 → 33.6 | 43.5 → 49.2; 43.3 → 47.2 | 36.3 → 40.2 | 133.7 → 161.0 | 147 → 158; 193 → 200 |
| PSS last-15-min growth % | 8.6 | **4.0** | 2.7 | 12.9 | 3.8 | 7.4 / 3.0 | 9.2 | 22.0 | −9.1 / 0 |
| grabs ok / failed, median s | — | **257 / 0, 5.1** | **230 / 0, 5.6** | — | 248 / 0, 4.8 | 217 / 0, 5.9; 222 / 0, 5.8 | — | 228 / 0, 5.2 | 208 / 0, 5.9; 214 / 0, 5.8 |
| rendered fps | **59.98** | — | 57.64 | 59.97 | — | 58.65 / 57.64 | 59.81 | — | 56.5 / 56.6 |
| video loss/min | 2.8 | — | 1,312 | 4.8 | — | 773 / 1,273 | 32 | — | 1,622 / 1,602 |
| resyncs | 0 | — | 52 | 0 | — | 14 / 27 | 0 | — | 199 / 204 |
| audio underruns | 15 | — | 11 | 10 | — | 10 / 10 | 11 | — | 448 / 312 |
| socket W | 21.3 | 16.1 | 27.0 | 20.5 | 15.4 | 25.4 / 25.4 | 20.4 | 14.9 | 25.9 / 25.3 |

From `e3_s6a_table.md` (`tools/e3_table.py`) and `e3_s6a_verdict.json`
(`e3_s6a_analysis.py`).

| clause | needed | got | holds |
| --- | --- | --- | --- |
| m1. META PSS at end; growth | ≤ 60 MB; ≤ 5 % | 33.6 MB; 4.0 % | yes |
| m2. META grabs | failed 0, ok ≥ 205, median ≤ 6.8 s | 0, 257, 5.1 s | yes |
| m3. the guide serves | 6 channels; 327-361 programmes (344 ± 5 %) | 6; 346 | yes |
| m4. META host CPU | ≤ 11.8 | 10.57 | yes |
| c1. CONC PSS at end | ≤ 60 MB | 47.0 | yes |
| c2. CONC grabs failed | 0 | 0 (230 ok) | yes |
| p1. PS1-STREAM in E1's bands of E2 | CPU 9.69-13.69; fps 59.31-60.31 | 10.45; 59.98 | yes |

**Verdict: ADOPTION STANDS.**

**Read beside the bar:**

- **Plain streaming is untouched.** PS1-STREAM sits on E3-S6's control
  and on E2: companion 23.9 % and 38 MB, sender 12.7 %, loss 2.8/min.
- **META repeats E3-S6's flagged runs to the decimal:** 33.6 MB, 0.23 %
  of a core, 257 grabs (E2: 161 MB, 7.6 %, 228).
- **CONC (reported, not gated)** lands on E3-S6's second CONC run:
  1,312 loss/min, 57.64 fps, 11 underruns. Its 52 resyncs are more than
  the earlier 14 / 27.
  - The aligned frame (`aligned/e2_conc.md`, this run's PS1-STREAM as
    baseline): **16.3 / 26.9 / 28.7 lost packets/s at +0 / +1 / +2 s**
    (E3-S6: 21-28 at +1 s; E2: 56-65). The busiest core peaks at 75 %
    at +1 s.
  - **The grabber child's share remains, as E3-S6 found.** The stream
    half stays open: a precompiled grabber, or a remembered source per
    channel.
- **The index file was reloaded, not rebuilt,** at each of the three
  runs' restarts: its mtime (04:16:16.723Z) and sha256 (`65644985…681b`)
  are unchanged at the end. The metadata file's TTL (06:20:41Z) did not
  expire during the runs, so no re-download happened. The first grab
  after it will re-download the file and rebuild the index once
  (~1 s, the companion's PSS ~60 MB until the next restart).

## 3. State at the end — the adopted state

- **Final state** (`runs/final_state.json`, 05:29:47Z):
  - manager none;
  - environ exactly the two lines;
  - the e3 drop-in absent;
  - no game, RetroArch or encoder;
  - the PS1 files identical; **APK CONFIRMED**.
- The guide read after: 6 channels, 346 programmes.
- The index file stays (3,268,095 bytes, `65644985…681b`).
- No `nft`, no real `sudo`, the Opal untouched.
- Files (`e3_s6a_2026-10-07/`):
  - `precondition.json`, `environ_before.txt`, `environ_after.txt`,
    `adopted_at_utc.txt`, `epg-index.conf`;
  - `e3_s6a_state_check.diff`;
  - `smoke.sh`, `smoke.jsonl`, `cands_check.py`, `cands_check.json`;
  - `guide_read_before.json`, `guide_read_after.json`;
  - the pre-registration and its `.sha256`;
  - `runs/` (3 runs, `manifest.sha256`, `--check` OK in `runs/check.txt`);
  - `e3_s6a_analysis.py`, `e3_s6a_table.md/.json`, `e3_s6a_verdict.json`,
    `aligned/`, `runs_console.log`, `redact_check.txt`.
- Git status: `logs/e3_s6a_git_status.txt`.
