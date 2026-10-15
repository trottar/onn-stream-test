---
memory_schema: 1
as_of: 2026-10-10
baseline_commit: 7331184 (plus the uncommitted E4-S1/S2 work)
---

# E4-S4 — grab deferral while streaming

**Classification: REJECTED by the pre-registered bar** — clause (a)
fails and clause (d) is link-INCONCLUSIVE. **The deferral did exactly
what it says (b, c and e hold).** What failed is the stream's quality on
tonight's lossy link, part of it on thresholds the control itself
misses. Not adopted (nothing is); the flag is absent.

| clause | holds | what decided it |
| --- | --- | --- |
| comparability: the control within E1's bands of E4-S1's PS1-STREAM | yes | host CPU 11.84 (10.9 ± 2); rendered 59.385 (59.53 ± 0.5) |
| (a) CONC + flag ×2: loss ≤ 3 × control and ≤ 100; rendered ≥ 59.5; resyncs ≤ 10; host CPU ± 2 | **no** | r1: loss 530 (> 443 and > 100), rendered 58.60, resyncs 26. r2: loss 364 (≤ 443 but > 100), rendered 58.92, resyncs 5. **The control itself: loss 148, rendered 59.38.** Host CPU +0.55 / −0.14 (holds) |
| (b) the deferral did what it says (3 runs) | yes | **0 grabs and 0 grabber samples** in every window; the queue at 6 (240 deferred calls per window); drains 6/6 ok, 0 failed, in 32.7 / 33.4 / 35.7 s (limit 63.6); `cap_fired` 0 |
| (c) the guide serves after each drain | yes | 6/6 channels; 301 / 301 / 302 programmes against 301 pre-run |
| (d) CONC + flag at `CPUQuota=150%` passes E4-S2's rule | **INCONCLUSIVE** (link) | every host-side gate passes: RetroArch 59.999, capture 59.993, dup+drop 0.1/min, spikes 111, stale 2.9, **0 s throttled at 0.96 cores**. Only rendered failed (58.07, loss 817/min) |
| (e) the companion's CPU ± 2 of the control's | yes | 25.32 / 25.74 vs 25.28 |

**What this means.**

- **With the flag, a CONC run is a plain stream** to the host. Its host
  CPU, companion CPU and CPU used match the control.
  - At 150 % it is never throttled. In E4-S2, CONC needed 400 % and was
    throttled 21 s even at 400 %.
  - **So on host-side evidence the stack's CPU-time floor under
    deferral is a stream's, 150 %.** That is what (d) was to show.
- The stream-quality clauses (a) and (d)'s rendered fps were judged on
  the link.
  - The link was poor all night: PS1-STREAM lost 92-353/min in E4-S3's
    five windows and 148/min here.
  - With no grab running in any flagged window, nothing in the change
    can add loss. CPU is flat and there are no children.
  - **But the bar is the bar.** r1's loss (3.6 × the control) and its
    26 resyncs fail even the relative parts of (a), and nothing here
    separates that from the link.
- **A clean night would settle it.** The same four runs on a link where
  the control meets D-BASE's loss row (< 10/min).

**Context:**

- Task: `handoffs/E4-S4_GRAB_DEFERRAL_TASK.md`, under
  `QUEUE_2026-10-10.md`.
- **Baseline: `7331184` plus the uncommitted E4-S1/S2 work**, untouched.
- Files: `e4_s4_2026-10-10/`.
- **Timeline (UTC, 2026-10-10):**

  | time | what |
  | --- | --- |
  | 02:20 | the change applied (staged while E4-S3 ran: the companion restarts at every ladder run, so nothing was changed until E4-S3 ended) |
  | 02:21-02:23 | smoke |
  | 02:24:01 | pre-run guide read (301 programmes); **pre-registration hashed** (`d04b385f…df8b`) |
  | 02:24-04:02 | control, CONC + flag ×2, CONC + flag at 150 % |

## 1. The change

The diff is `e4_s4_change.diff`; the hashes are in `change_sha256.txt`.
It is behind **`PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`** (absent = today).

**`companion/plugins/epg.py`:**

- **`DeferredGrabs`:**
  - While the games plugin's recovery state is PLAYING,
    PAUSED_RECOVERING or PAUSED_SAVED, a forced grab is queued, one
    entry per channel. That covers both the refresh endpoint and the
    background warmer.
  - It is answered with the cached guide marked
    **`"refresh_deferred": true`**, `"deferred_reason": "stream_live"`.
    The toolchain-preparing path already returns that marker, so clients
    tolerate it.
  - When the state is ENDED, the queue drains in order, one grab at a
    time. A running grab is not touched.
  - A deferral older than 60 min runs anyway (`cap_fired`).
- The EPG status gains `"deferred"` (pending, channels, requests, drained
  ok / failed, `cap_fired`, `last_drain`), and only with the flag set.
- The recovery state is read through the plugin registry at call time;
  `plugins/__init__.py` is unchanged.

**`tools/e1_suite.py`:**

- The CONC cycle records a `deferred` row and waits 5 s instead of
  re-asking at once.
- With the flag, the teardown waits for the drain, records it, and reads
  the guide.
- See `patches/E4-S4_GRAB_DEFERRAL_FLAG.md`.

**The smoke** (`smoke.jsonl`):

- **With the flag:** a PS1 stream at PLAYING; six forced refreshes all
  answered `refresh_deferred` in ~0 s, pending 1 → 6, no grabber child.
  Stream stopped → the six drained 6/6 ok in 37.2 s; the guide served
  6/6.
- **Without the flag:** six refreshes ran at once, 3.2-6.1 s each, all
  ok; the status had no `deferred` key (today, byte for byte in
  behaviour).

## 2. The runs

| | control (PS1-STREAM, no flag) | CONC + flag r1 | CONC + flag r2 | CONC + flag at 150 % |
| --- | --- | --- | --- | --- |
| window (UTC) | 02:28-02:48 | 02:52-03:12 | 03:16-03:36 | 03:41-04:01 |
| host CPU % | 11.84 | 12.40 | 11.70 | 10.80 |
| companion CPU (% of a core) | 25.28 | 25.32 | 25.74 | 24.95 |
| CPU used by the stack (cores) | 0.97 | 1.02 | 0.99 | 0.96 (**0 s throttled**) |
| rendered fps | 59.38 | 58.60 | 58.92 | 58.07 |
| video loss/min | 148 | 530 | 364 | 817 |
| resyncs; underruns | 5; 14 | 26; 27 | 5; 50 | 47; 32 |
| ladder transitions; lowest kbps | 2; 6000 | 2; 6000 | 1; 5000 | 0; 7000 |
| grabs run / grabber samples in the window | — | **0 / 0** | **0 / 0** | **0 / 0** |
| deferred calls; queue max | — | 240; 6 | 240; 6 | 240; 6 |
| drain after teardown (queued / ok / failed / s) | — | 6 / 6 / 0 / 32.7 | 6 / 6 / 0 / 33.4 | 6 / 6 / 0 / 35.7 |
| client / controller pauses | 0 / 0 | 2 / 0 | 0 / 0 | 2 / 0 |
| gaps > 1 s; max ms | 2; 1,360 | 4; 1,907 | 11; 2,174 | 8; 1,770 |
| socket W | 20.0 | 19.7 | 21.8 | 20.9 |

- Against E4-S2's CONC at 400 %, the change removes:
  - the grab bursts (2.18 cores of CPU used → ~1.0);
  - the throttling (21 s at 400 % → 0 s at 150 %);
  - E4-S1's ~75 % of a core of node.
- **Validity:** 4/4 valid; 0 replaced attempts. The flag was absent after
  every teardown, and the constraint was lifted after the 150 % run
  (`validity.json`). `--check` OK.

## 3. If the user adopts it anyway (the task's §3; not done here)

**One line**, in its own drop-in beside the four:
`~/.config/systemd/user/privyhub-companion.service.d/epg-defer.conf` =
`[Service]` / `Environment=PRIVYHUB_EPG_DEFER_WHILE_STREAMING=1`, then
`daemon-reload` + restart. The state checks' `ADOPTED` list would gain
the name.

**Revert:** delete `epg-defer.conf`, `daemon-reload`, restart.

**The alpha spec restated with the deferral** (E4-S2 §5, E4-S3 §3):

| | without the deferral (today) | with the deferral |
| --- | --- | --- |
| the stack's CPU-time floor | 400 % (CONC) | **150 %** (a stream; E4-S2's PS1-STREAM; CONC + flag at 150 %: 0 throttled) |
| proposed CPU | ≥ 6 cores of this speed class | **4 cores of this speed class** (150 % + Xorg, pulseaudio, OS, an update) |
| the stack's memory | > 768M, ≤ 1G with swap (the grabber) | unchanged: the cycle still runs, between streams (> 768M without swap) |
| proposed memory | 1.5 GB for the stack; 8 GB system | the same |
| the guide | refreshed during play | refreshed when play stops: 6 channels in ~33-37 s |

## 4. State at the end; files

- **Final state** (`runs/final_state.json`, 04:02Z; `state_at_end.json`):
  - the four adopted lines; no `e3_flag.conf`, no `e4_constraint.conf`;
  - no game; the PS1 files identical; **APK CONFIRMED**.
- **The code stays in the tree**, dormant behind the flag, uncommitted,
  as E3's flags did.
- No sudo, no nft, the Opal untouched; nothing fetched; no data deleted.
- E4-S2's pass rule was copied (`e4_s4_passrule.py`, one comment line
  added), not run in its directory.
- **Files** (`e4_s4_2026-10-10/`):
  - `apply_e4_s4.py`, `predecessor_sha256.txt`, `predecessor_*.py.txt`,
    `e4_s4_change.diff`, `change_sha256.txt`;
  - `e4_s4_smoke.py`, `smoke.jsonl`, `smoke_console.log`;
  - `pre_guide.json`;
  - the pre-registration + `.sha256` + `preregistration_hashed_at.txt`,
    `tools_at_preregistration_sha256.txt`;
  - `runs/` (4 runs, `manifest.sha256`, `check.txt`), `runs_console.log`;
  - `e4_s4_analysis.py`, `e4_s4_passrule.py`, `analysis_console.txt`,
    `e4_s4_table.md`, `e4_s4_verdict.json`, `validity.json`;
  - `state_at_end.json`, `redact_check.txt`.
- Git status (cumulative): `logs/e4_s4_git_status.txt`.
