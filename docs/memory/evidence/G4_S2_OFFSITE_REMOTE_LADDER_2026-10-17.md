---
memory_schema: 1
as_of: 2026-10-18
baseline_commit: 49d1667
---

# G4-S2 — off-site with the remote ladder: the record (Part 2)

**Classification: PARTIALLY MEASURED — 1 of 2 runs, valid.**

**Run 1 (capped at 4000)** played over the overlay. The start rung was **4000, source `floor`, `path_class` remote**.
The ladder held 4000 for the whole session: 73 up-moves were refused by `remote_cap`, no clamp was violated, and there
were no transitions.

**Run 2 was not run.** The user stopped it for their phone data (§5). The hotspot showed about 500 MB used after
~8 minutes of run 1.

**The headline is the wire rate.** At the 4000 rung the hub's tailnet interface sent **8.29 Mbit/s** in steady play,
not the ~4.65 Mbit/s that was pre-registered as expected. That is **~62 MB a minute**, about 3.7 GB an hour.

Measurement only; nothing adopted; nothing committed.

**Sources:**
- Task: `handoffs/G4-S2_OFFSITE_REMOTE_LADDER_TASK.md`.
- Part 1: `G4_S2_LAUNCH_2026-10-17.md`.
- Pre-registration: `g4_s2_2026-10-17/g4_s2_preregistration.txt`, sha256 `0090c385…722d`, unchanged at the record.
- Paths keep the task's 2026-10-17 date; the session ran on **2026-10-18** (US Eastern afternoon).

## 1. What ran

| | Run 1 (capped) | Run 2 (uncapped, rules on) |
|---|---|---|
| Flags (the drop-in, read back as 11 lines) | `REMOTE_LADDER=1`, `START_RUNG=floor`, `REMOTE_RUNG_CAP=4000`, `WAN_TELEMETRY=1` | not written |
| Idle gap | 17:55:43–18:00:43Z | — |
| PLAYING | 18:00:51Z, 8 s into the wait | — |
| Window (the row's) | 18:02:21–18:12:21Z | — |
| Stream on the wire | 18:00:51–18:08:37Z, with an 11-s stop at 18:02:56Z (§3) | — |
| Endpoint class | **overlay** (hash in the summary) | — |
| Validity | **valid** (overlay, `flags_absent` true) | **not run** (the STOP file, §5) |

**Teardown and driver state:**
- The teardown (18:12:26Z) removed the drop-in, restarted the companion and read `flags_absent` **true**. The
  environ is back to 7 lines.
- The driver closed on "the stop file" and the unit was collected.

**The stream ended before the window did.** The user quit the game at about 18:08:37Z, ~6 min into the 10-min
window. The row's window is a fixed sleep, so it ran on to 18:12:21Z with no stream. All window figures below are
therefore over **~6.3 min of play**: 356 s of heartbeats, two client sessions.

## 2. Gates (host)

| Gate 3 clause (host) | Clause | Run 1 | |
|---|---|---|---|
| RetroArch | ≥ 59.9 fps | **not read** | RetroArch's title had no "FPS / Frames" counter in any of 112 reads, so `titles` is 0 (§6) |
| capture | 60 ± 0.1 | **60.004** | met |
| dup+drop | ≤ 0.2/min | **0.0** | met |
| flags_absent after | true | **true** | met |

**Gate 3 is read off-site for the first time** (G4-P2's remote row): capture and dup+drop are clean. The RetroArch
clause could not be read, so gate 3 as a whole is **not evaluable**. Gates 1-2 (validity: PLAYING over the overlay, `flags_absent` after) are met. This is not a "not met".

## 3. Link side (reported, not gated)

**Start rung** (the ladder's first row carrying `start_rung`, 18:00:50.971Z):
- kbps 4000, source `floor` (requested `floor`), `path_class` **remote**;
- active list 4000-5000-5500-6000-7000.

**Rung path and cap:**
- The rung path is **4000**. There were no acted transitions.
- Native-stream-status read 4000 in every active poll, and the encoder's `-b:v` / `-maxrate` read `4000k` / `4000k`.
- **Clamps:** `remote_cap_config` was active, value 4000.
  - The ladder logged **73 `refused` rows with `source: remote_cap`**, all inside the window. These are its up-wishes,
    held at the cap.
  - No clamp was violated.
- **Rules:** off in run 1 (`PRIVYHUB_WAN_ADAPTATION` absent), so there are no rule rows.

**Loss and frames:**
- Post-FEC loss was **7.75 /min** over the window's heartbeats, with rendered **59.919 fps**.
- Resyncs were 0 in the window. Session 1 had 1, before the window.
- The client's two sessions (from the companion's journal):

| Client session | Lasted | Lost packets | Resyncs | FEC recovered | FEC unrecoverable |
|---|---|---|---|---|---|
| 1 (18:00:50Z) | 121 s | 2,659 | 1 | 3 | 2 |
| 2 (18:03:05Z) | 329 s | **35 (6.4 /min)** | 0 | 7 | 1 |

**Session 1's losses fall where the overlay path changed.** The path went direct → relayed (18:01:15Z) → direct
(18:01:35Z) in the first 45 s. That is a coincidence in time; no cause is claimed.

**The 11-s stop at 18:02:56Z** was the client's own sequence:
1. `native-stream-stop`;
2. `save-state` (18:03:01Z);
3. `native-stream-start` (18:03:05Z);
4. `native-stream-ready` (18:03:08Z).

This is the user's pause / save, not a recovery.

**Timing and the overlay:**
- Telemetry: control RTT median **124 ms**; receive→decode median 10 ms; output gap max 46 ms; the receiver's lost
  packets were 11.68 /min.
- **The overlay path:** 59 reads, 42 direct and 17 relayed, 3 changes in the window. The changes came after the stream
  ended (18:09-18:10Z). Connected throughout.
- **`wan`:** the last class was `clean`. Windows: 26 clean, 3 lossy, 2 starved, 0 capacity-limited, 0 path-changed in
  the last read. The starved windows match the minutes with no stream.
- Audio underruns: 14 (heartbeats).

## 4. The wire rate and the data (A5)

All figures are from the hub's tailnet interface's `tx_bytes`, read every 10 s.

| | Value |
|---|---|
| **At 4000, steady** (session 2, 18:03:10–18:08:30Z, 32 reads) | **median 8,286 kbit/s** (min 8,212, max 8,355) |
| At 4000, every active read in the window | median 8,285 kbit/s (36 reads) |
| The idle gap (no stream) | 0.2 kbit/s; 0.0 MB in 291 s |
| PLAYING → the stream's end (452.6 s) | **458.2 MB**, mean 8.10 Mbit/s |
| The whole run, launch → teardown | 471.5 MB |
| In the row's window (592.6 s, ~6.3 min of it streaming) | 373.6 MB |

**Against the expectation.** The pre-registered expectation was a wire rate near 4.65 Mbit/s at 4000. **Not met: 8.29
Mbit/s, 1.78× that.** At 4000 the rate was 2.07× the encoder's rate.

**Against G4-S1's 7000.** G4-S1 run 1 measured 11.42 Mbit/s at 7000 on the same interface, 1.63× the encoder's rate.

| | Encoder rate | Wire rate | Excess |
|---|---|---|---|
| G4-S1 run 1 | 7000 | 11.42 Mbit/s | **~4.4 Mbit/s** |
| G4-S2 run 1 | 4000 | 8.29 Mbit/s | **~4.3 Mbit/s** |

**Stated, not explained:** the excess over the encoder's rate is nearly the same at both rungs. So the cut from 7000 to
4000 saved only ~27 % of the data, not the ~43 % the rung ratio suggests. The source of a roughly constant ~4.3 Mbit/s
is **not identified**. Candidates for G8-S4 / a wire-overhead task:
- the audio and its redundancy (2/4);
- FEC parity (G8-S3: 0.178 per data packet);
- the overlay's per-packet cost at MTU 1280.

**Data per run at 4000:**
- ~62 MB a minute of play;
- **~715 MB** for a full run (90-s warm-up + 10-min window);
- ~3.7 GB an hour.

The user's hotspot read about 500 MB at ~18:08Z, against 458 MB on the hub's interface to the stream's end. The
phone's count also carries the client's upstream and the hotspot's own traffic.

## 5. Run 2 — why it did not run

At ~18:07Z the user, on phone data, said they could not keep running it. Run 2 would have been another ~700 MB, and
its uncapped climb toward 7000 would have meant more. Code then:
1. touched `~/privyhub_g4_s2/STOP` (18:07:27Z), so run 2 would not start;
2. let run 1's row finish its fixed window and its teardown;
3. did not kill anything.

The user quit the game at ~18:08:37Z. **Run 2's measurements remain open:** the climb from 4000, the ladder and R5 on a
real remote path, and the rules' rows.

## 6. What failed, and where

- **The wire rate at 4000 is ~1.8× the expectation** (§4). For the user this is the headline: the data use made a
  cellular session impractical. (Known issues.)
- **The RetroArch counter was not on the title**, so gate 3's RetroArch clause was not read.
  - The row writes its per-game counter override for the PS1-STREAM fixture, Tekken 3 only. The title read "RetroArch
    Beetle PSX HW …" with no counter all session.
  - Either a different PS1 title was launched, or the override did not take. The launch id is masked in the journal, so
    which one is not determined here. (Known issues.)
- **The row's window runs on after the stream ends.** It is a fixed sleep, so the window figures mix play with no play
  (§1). Reported, not fixed.
- **The task's cap had passed at launch.** It was moved to 19:55Z by the user's choice and disclosed (pre-registration
  A1).
- **`--check` was not ok at both ends, client side only:** adb is off-LAN, so the APK reads MISMATCH. This is G4-S1 §1's
  deviation. At the record (18:09Z, before the teardown) it read 11 environ lines and the drop-in present, as expected
  mid-run. After the teardown the driver read 7 lines, `flags_absent` true.

## 7. Comparison with G4-S1

G4-S1 started at 7000 with no remote ladder.

| | G4-S1 run 1 (7000) | G4-S2 run 1 (4000, capped) |
|---|---|---|
| Loss /min (post-FEC, window) | 2,259 | **7.75** |
| Wire rate (tailnet tx) | 11.42 Mbit/s | **8.29 Mbit/s** |
| Data per 10 min of play | ~857 MB | **~622 MB** |
| Overlay path | relayed | direct mostly (42/59) |

The loss difference is large, but the conditions differ: the path, the day, and how long the run lasted. It is
**stated, not attributed to the rung.** G4-S1 run 2 had the hotspot toggle; there is no G4-S2 counterpart.

## 8. The user's report (recorded as such; nothing perceptual is a gate)

- **Pause/Resume and Save/Load:** the journal shows a save-state with a stream stop / start at 18:03Z. A load-state ran at the launch (18:00:49Z). There was no other save or load; a Pause/Resume is not separately visible on the host.
- **The picture:** the user did not report on the picture at 4000 vs 7000.
- **Data:** the user stopped the session for their data. Their hotspot read ~500 MB.

## 9. Files

**`g4_s2_2026-10-17/`:**
- Part 1's files;
- the driver's outputs: `runs.jsonl`, `g4_s2_state.json`, `driver_console.log`;
- `runs/run1_capped/`: the row's `E1-PS1-STREAM-REMOTE/run1/` (summary, path, telemetry, encoder, title, samples),
  `stream_poll.jsonl`, `wan_poll.jsonl`, `ladder_log.jsonl`, `companion_journal.txt` (ids masked), `suite_console.log`;
- `check_record.json`, `validity.json`, `manifest.sha256`, `redact_check_record.txt`.

**Elsewhere:** `logs/g4_s2_git_status.txt`.

The redactor checked 44 files: 43 OK and one HIT, the row's `title.txt`. That hit is a false positive: the redactor
reads RetroArch's core version `0.9.44.1` as an IPv4 address. G8-S3's three `title.txt` files hit the same way.
`tools/check_memory_health.py` reads `maintenance_required` because `CURRENT.md` is at its hard limit. That was already
so at `49d1667` (302 lines); this record adds 13.

The endpoint appears as class and hash only. The hotspot is `<the hotspot>` and the tailnet `<the tailnet>`.

**Standing rules held:** no sudo, no nft, the Opal not touched, adb not used, nothing fetched, adopted or committed.
The only deletions were the driver's own drop-in teardown and this session's `__pycache__`.
