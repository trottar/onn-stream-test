---
memory_schema: 1
as_of: 2026-10-16
baseline_commit: 3107fb5 (plus the uncommitted G1-S1 / G3-S1 / G3-S2 work and session A's CL-B2 work)
---

# G5-S1 — WAN telemetry classification

*(§1 was written before any G5-S1 code; the later sections were written
after the tests.)*

## 1. The thresholds, with their sources (written before the code)

**The window** is 5 consecutive client reports, i.e. 10 s at the 2-s
cadence. That is the live ladder's own evidence window: `WINDOW_REPORTS =
5`, "10 s of evidence for a decrease" (`companion/adaptive_bitrate.py`). A
per-minute row from a record is applied to a window **scaled to its
duration** (a rate, not a new number).

**The inputs per report** are the ones the ladder already reads:

- `fps` = `receiver.recent_fps`;
- `queue` = `decoder.queue_depth`;
- `gap` = `latency.output_gap_ms`;
- `lost` = `receiver.lost_packets_delta`, the client's **post-FEC** lost
  video packets ("RTP sequence gaps after FEC reconstruction",
  `adaptive_bitrate_live.py`, C3-L4-N1).

| class | the rule (per 10-s window) | source |
| --- | --- | --- |
| `lossy` | post-FEC loss rate ≥ 10 / min (window lost × 60 / window s ≥ 10) | D-BASE close-out: "lost packets / min — video, post-FEC < 10" (`D_BASE_CLOSEOUT_2026-09-23.md`) |
| `starved` | stale output drops ≥ 20 / min (scaled) | D-BASE close-out: "stale output drops / min < 20" |
| `capacity-limited` | **either** fps < 50 on all 5 **and** lost ≥ 50 on ≥ 3 of 5 (FALLBACK `capacity`), **or** fps < 57 on ≥ 4 of 5 **and** lost ≥ 50 on ≥ 3 of 5 (ROUTINE `capacity_mild`) | C3-L4-N1 / N2: `CAPACITY_*`, `CAPACITY_MILD_*` (`adaptive_bitrate_live.py`; `C3_L4_N1_CAPACITY_TRIGGER_2026-09-29.md`, `C3_L4_N2_MILD_CAPACITY_2026-09-29.md`) |
| `latency-limited` | queue ≥ 1 on ≥ 3 of 5 (ROUTINE's queue clause), **or** output gap > 250 ms on ≥ 2 of 5 (FALLBACK's gap clause). That is the ladder's `fps_queue_gap` evidence without its fps clause: runaway latency shows as a queue or a gap, whatever the fps | `adaptive_bitrate.py`: `ROUTINE_QUEUE_*`, `FALLBACK_GAP_*`; D-BASE: "inside the 250 ms verdict bound" |
| `path-changed` | an event in the window: an overlay path transition (G1-S1 provider), a recovery pause / resume (`recovery.jsonl`), or a ladder transition (`acted`) | event-based, no threshold. ROADMAP §G5: "reconnect/path-change events" |
| `clean` | none of the above | — |

- **The window's primary class** follows ROADMAP §G5's priority order:
  `path-changed` (1. "control/session correctness") > `latency-limited`
  (2. "runaway latency") > `starved` > `capacity-limited` (3. "capacity
  tightens") > `lossy` (4. "loss characteristics") > `clean`. The window
  also lists every class it meets.
- **The session's class** uses the same rows over the whole session:
  - `path-changed` if any path event;
  - `capacity-limited` / `latency-limited` if any window met that rule
    (the ladder acts on one window);
  - `starved` / `lossy` by the D-BASE row on the session's whole duration;
  - else `clean`.

  The per-class window counts are reported beside it.
- **Not classified (G5-S2), because no record gives a number:**
  - RTT (`latency.control_round_trip_ms` is carried and reported);
  - jitter (`receiver.interarrival_jitter_ms` is carried and reported);
  - goodput as a class;
  - FEC recovered / unrecoverable as a class;
  - MTU / fragmentation;
  - audio starvation (`audio_prolonged_starvation_events`; D-BASE gives no
    target).

  Each is **measured and reported** with its source field. G5-S2 sets the
  bar.

**The eleven measures (ROADMAP §G5) and their source fields:**

| measure | source field(s) | where |
| --- | --- | --- |
| delivered goodput | `receiver.recent_mbps` (→ kbit/s, window mean); live also `sender.sent_bytes_delta` | stream telemetry (`diagnostics/stream_telemetry.py`) |
| packet loss, post-FEC | `receiver.lost_packets_delta` | the same |
| packet loss, pre-FEC | post-FEC + `fec.recovered_packets_delta` (live) or `fec_recovered_packets` deltas (the heartbeat log) | stream telemetry / `native_stream_heartbeat.py` |
| FEC recovered / unrecoverable | `fec.recovered_packets_delta`, `fec.unrecoverable_groups_delta`; heartbeat `fec_recovered_packets`, `fec_unrecoverable_groups` | the same |
| jitter / inter-arrival | `receiver.interarrival_jitter_ms` (the client's running estimate; p50 / p95 of it per window). **No per-packet arrival times are carried** | stream telemetry |
| RTT / echo latency | `latency.control_round_trip_ms` (the client's control round trip; **an echo exists**) | stream telemetry |
| sender pacing | `sender.send_call_avg_us`, `send_call_max_us`, `send_errors_delta` (live only; the recorded runs did not keep the sender block) | stream telemetry |
| queue / buffer depth and trend | `decoder.queue_depth` (max, last − first), `decoder.queue_depth_delta` | stream telemetry |
| decoder starvation / stale drops | `decoder.stale_output_drops_delta`, `receiver.waiting_for_idr`; heartbeat `audio_prolonged_starvation_events` | stream telemetry / heartbeat |
| overlay path | the G1-S1 provider's `state()`: path direct / relayed / no-peer / none; without a provider, `none` | `companion/overlay/` |
| MTU / fragmentation symptoms | the provider's `mtu`; **no oversize-drop counter exists** → "not observed" | `companion/overlay/` |
| reconnect / path-change events | overlay path transitions; recovery pauses / resumes (`recovery.jsonl` / the recovery state); ladder transitions (`acted`, `stream_kbps` changes); heartbeat `stream_resyncs` deltas | the respective logs |

## 2. Classification

**BUILT behind `PRIVYHUB_WAN_TELEMETRY=1`; verified by unit tests and by
replaying three recorded runs; NOT ADOPTED.** The flag is absent on the
running companion, and **the companion was not restarted**. It runs
session A's `e3_flag.conf` (`PRIVYHUB_SESSION_IDENTITY=v2`), which this
session did not touch. A restart would load these edits, inert without the
flag. **The live smoke** (`/status` and `/diagnostics/stream-telemetry`
with the flag on, during a stream) is **pending on the stream**: session A,
after CL-B2 closes.

- Task: `handoffs/G5-S1_WAN_TELEMETRY_CLASSIFICATION_TASK.md`, queue
  `QUEUE_2026-10-16B.md` item 1. Session B, overnight and unattended.
- **Baseline `3107fb5`**, plus the uncommitted work
  (`g5_s1_2026-10-16/git_status_at_start.txt`).
- §1 was hashed at **03:40:50Z**, before the module was written
  (`design_written_before_code.sha256`).

## 3. What was built

- **`companion/wan_telemetry.py`** (new):
  - `report_from_telemetry` reads the stream-telemetry schema (live, and the
    recorded rows alike).
  - `classify_window` applies §1's rules to 5 reports.
  - `SessionClassifier` gives the per-window and per-session classes and the
    eleven `measures` (each `{value, source}`; "not recorded" /
    "not classified; G5-S2" where §1 says so).
  - `WanTelemetry` is the live object. It is fed once per client health
    report. It turns ladder transitions (a `bitrate_kbps` change), overlay
    path transitions and recovery-state changes into events. At a session's
    end (when the elapsed clock goes back) it writes the session summary to
    `logs/wan_sessions.jsonl`. Its `status_field()` returns nothing unless a
    report came within one window.
  - **It never acts.**
- **`companion/privyhub_service.py`**: predecessor `32a7d2ea…` (the G1-S1 /
  G3-S1 state), after `ddfaf5fa…`. Four edits, each inert without the flag;
  `g5_s1.diff` shows them against the predecessor, which was reconstructed
  and matched to its saved hash:
  1. `WAN_TELEMETRY` is built only when the flag is set, with the import
     inside that `if`;
  2. the client-health handler calls `observe` after the ladder's own
     `observe`, inside the existing never-raise `try`;
  3. `GET /diagnostics/stream-telemetry` adds `wan` under the flag;
  4. `/status` adds `wan` through a guarded module-level wrapper around
     `CONTROLLER.status`, so the status method itself is unchanged (§4).
- **`docs/WAN_ADAPTATION_RULES.md`** (new): §G5's five priorities as rules
  R1-R5 against these classes, each number quoted from its record, plus a
  list of what no record sets. **Written, not implemented** (G5-S2).
- **Two deviations from the task's wording:**
  - **"The session report."** That is the client's own end-of-session
    document, written by the games plugin. Adding to it would have meant
    editing that plugin, which tonight's rules forbid (a new module or a
    guarded import only). The host's `wan` object therefore goes on
    `/diagnostics/stream-telemetry` and `/status`, and the per-session
    summary goes to `logs/wan_sessions.jsonl`.
  - **Recovery events live:** the hook passes no recovery state yet
    (`recovery_state=None`). The replay takes them from `recovery.jsonl`.
    Feeding the games plugin's recovery state live is G5-S2's, with the
    plugin edit.
- **"Jitter p50 / p95":** the client carries `interarrival_jitter_ms`, a
  running estimate, not per-packet arrival times. So the percentiles are
  of that estimate, and the record says so. **RTT: an echo exists**
  (`latency.control_round_trip_ms`); it is reported, and not classified
  (no record sets a bar).

## 4. Verification

**`tests/wan_telemetry/` → 18 / 18 OK** (`tests_output.txt`):

- **Classes (6):** each one triggered by its §1 rule. Loss: 1 packet in a
  window is clean, 2 is lossy (10/min scaled). Stale: 3 is clean, 4 is
  starved. Capacity: N1, N2, and a near-miss. Latency: the queue clause,
  the gap clause, and gap 250 not > 250. Path-change wins the priority.
- **Measures (2):** all eleven present, each with a source (pre-FEC = post +
  recovered); stale reports skipped, repeats deduplicated.
- **Replays (3)** (`replay_*.json`: the session and every window):

| run | recorded loss / min | replayed | session class | classes met | windows by primary class |
| --- | --- | --- | --- | --- | --- |
| E4-S4B run3 (lossy) | 649.94 | **649.94** | path-changed | path-changed (4 ladder transitions), capacity-limited, lossy | lossy 53, clean 59, path 4, starved 2 |
| E4-S4B run2 (cleanest) | 60.93 | **60.93** | **lossy** | lossy | lossy 64, clean 50, starved 4 |
| CL-B2 flag run1 (tonight) | 663.98 | **663.98** | path-changed | path-changed (a recovery pause at ~942 s), capacity-limited, lossy | lossy 61, clean 51, capacity 2, starved 2, path 1 |

  - **No run is clean**, which is what those nights earned: every one failed
    D-BASE's < 10 row (E4-S4B §1, CL-B2's window).
  - The loss figures equal the records' (`e1_suite.telemetry_figures`, the
    same rows).
  - CL-B2's fixture carries the heartbeat's deltas: FEC recovered 372,
    unrecoverable groups 269, stream resyncs 49, audio starvation events
    305. Pre-FEC loss is therefore 682.63 / min. The 10-10 runs predate the
    heartbeat log's oldest line, so their FEC is "not recorded".
- **Live (2):** the flag; observe → ladder and overlay-path events,
  freshness, and a session summary written at the session's end.
- **The flag absent, byte for byte (5):**
  - tonight's `status()` (a golden kept before the edit) against the
    edited one: identical;
  - the guarded wrapper adds only `wan`, and only with the flag;
  - the request handler (tonight's class, kept as a golden) against the
    edited one on `GET /status`, `GET /diagnostics/stream-telemetry`,
    `POST /diagnostics/client-health` and D-BASE / D6-R1's two games GETs
    → **5 / 5 identical**, access-log lines too (`handler_byte_comparison.md`);
  - with the flag, `stream-telemetry` gains `wan` and the client-health
    handler feeds `observe`;
  - the AST shows the import only under the flag.
- **Earlier suites still pass** (`tests_regression_g1_g3.txt`): G1-S1
  overlay 17 / 17, G3-S1 session identity 38 / 38.

**Two first-try failures, both disclosed:**

1. **A test expectation was wrong.** My hand fixture put 3 FEC-recovered
   packets on each of 5 reports. Pre-FEC is (2 + 15) in 10 s = 102 / min,
   which the module computed; the test said 30. The expectation was
   corrected.
2. **The first `/status` hook broke G1-S1's tests.** It sat inside
   `status()`, and G1-S1's tests run that method with a namespace that has
   no `WAN_TELEMETRY` (2 errors). G1-S1's files may not be touched, so the
   hook moved to the guarded wrapper (§3). The overlay suite went back to
   17 / 17.

## 5. Pending; for the user

- **The live smoke** (session A, after CL-B2):
  1. a `PRIVYHUB_WAN_TELEMETRY=1` drop-in and a restart;
  2. one PS1-STREAM: `/status` and `/diagnostics/stream-telemetry` carry
     `wan`, and `logs/wan_sessions.jsonl` gets one line at the session's
     end;
  3. remove the drop-in.
- **G5-S2:** implement `docs/WAN_ADAPTATION_RULES.md` behind its own flag;
  set the bars no record has yet (RTT, jitter, a relayed cap, FEC as a
  class, the persistence before 720p/4000); feed the recovery state live.
- Not adopted; the flag is absent.

## 6. Files; disclosures

- **Files** (`g5_s1_2026-10-16/`):
  - `baseline_commit.txt`, `git_status_at_start.txt`,
    `predecessor_sha256.txt`, `after_sha256.txt`,
    `design_written_before_code.sha256`;
  - `make_fixtures.py` (the redaction boundary: counters only);
  - `g5_s1.diff`;
  - `tests_output.txt`, `tests_regression_g1_g3.txt`;
  - `replay_*.json` (3), `handler_byte_comparison.md`;
  - `redact_check.txt`, `manifest.sha256`.
- **Fixtures** (`tests/wan_telemetry/fixtures/`): three runs (counters and
  elapsed times only; no timestamp, address or identifier) and tonight's two
  goldens.
- **Patch:** `patches/G5-S1_WAN_TELEMETRY_CLASSIFICATION.md`.
- **The redactor** (`redact_check.txt`): 26 files OK, 0 HIT (this directory, the fixtures, the module, the tests, the record, the patch, the rules, `REMOTE_TRUST.md`, ROADMAP).
- **Not touched:** `e3_flag.conf`, `paired_devices.json`, the session audit
  log, `cl_b2_2026-10-16/` (read only, to build its fixture) and
  `companion/session_identity.py`.
- The tests left temporary directories under the system temp directory, and
  `__pycache__/` (gitignored). Nothing was deleted.
- No sudo, no nft, the Opal untouched; nothing fetched; no stream, no game,
  no adb, no restart. Git status: `logs/g5_s1_git_status.txt`.
