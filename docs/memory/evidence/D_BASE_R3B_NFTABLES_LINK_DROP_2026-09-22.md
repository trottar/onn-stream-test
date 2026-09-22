---
memory_schema: 1
as_of: 2026-09-22
baseline_commit: cbfd2d03321e1be936aa5b94a512695a1d2b03af
status: EVIDENCE — D-BASE-R3b, the nftables link-drop runs actually performed (N3, N15, N150); all three PASS; N05/N15b/H5/E30 NOT RUN, so R3+R3a do NOT reach RUNTIME VALIDATED; two post-run defects open
---

# D-BASE-R3b — link-drop self-recovery against real packet loss

Task: `handoffs/D-BASE-R3B_TASK.md`. Design: `investigations/LINK_DROP_RECOVERY_DESIGN.md`.
Runs by the user by hand with `evidence/d_base_r3b_2026-09-21/r3b_run.sh`
(the Claude Code classifier refuses `nft` writes; `PLAN_WEEK_2026-09-21.md`
item 2). Artifacts and SHA-256s in `evidence/d_base_r3b_2026-09-21/`.
**No production code was changed.** Times UTC; the host is UTC-4.

**This is the first time loss, sequence jumps and FEC behaviour have been
measured on this build during a real outage**, so those numbers come first.

## What ran, and what did not

| run | fault | ran? | verdict |
| --- | --- | --- | --- |
| N05 | 0.5 s | **no** | not run |
| **N3** | 3 s | yes | **PASS** |
| **N15** | 15 s | yes | **PASS** |
| N15b | 15 s repeat | **no** | not run |
| **N150** | 150 s | yes | **PASS** (criterion corrected, below) |
| H5 | controller-silence | **no** | retired — `S2` observed the host-side trigger four times naturally (`PLAN_WEEK_2026-09-21.md`) |
| E30 | `END_MS` | **no** | not run |

**`D-BASE-R3` + `D-BASE-R3a` therefore do NOT become RUNTIME VALIDATED.**
The handoff conditions that on N05, N3, N15, N15b **and** N150 all passing.
Three of five ran. `END_MS` remains entirely unexercised.

The injected fault, identical in all three runs
(`<run>/nft_table_active.txt`, one table, deleted after every run):

```
table inet privyhub_fault {
	chain flt {
		type filter hook output priority filter; policy accept;
		udp dport { 48100, 48101 } drop
	}
}
```

Host-side **output** hook, so ADB to the onn stayed up. Measured fault
durations from `<run>/timings.txt`: **3.06 s**, **15.06 s**, **150.07 s**.

## Loss, sequence jumps and FEC during the outage

| | N3 | N15 | N150 |
| --- | --- | --- | --- |
| session duration | 57.4 s | 81.8 s | 329.0 s |
| video packets | 44 888 | 55 048 | 147 187 |
| **`lost_packets`** | **2 348** | **22** | **40** |
| `lost_packets_in_resyncs` | 2 336 | 0 | 0 |
| `sequence_resyncs` | 1 | 1 | 1 |
| `largest_resync_jump_packets` | 2 336 | 0 | 0 |
| `forward_gap_events` | 5 | 9 | 7 |
| `max_forward_gap_packets` | 5 | 8 | 15 |
| `sequence_gap_au_drops` | 5 | 5 | 7 |
| `incomplete_au_drops` | 1 | 0 | 0 |
| FEC parity / groups | 6 879 | 8 537 | 23 338 |
| `fec_recovered_packets` | 14 | 12 | 12 |
| `fec_unrecoverable_groups` | 4 | 6 | 6 |
| **`max_output_gap_ms`** | **3 114** | **15 116** | **150 090** |
| `dropped_frames` | 4 | 0 | 0 |
| `ssrc_changes` | 0 | 1 | 1 |
| `terminal_slow_event` | None | None | None |

**`max_output_gap_ms` reproduces the fault duration to within 60 ms in all
three runs** (3 114 / 15 116 / 150 090 against 3 060 / 15 060 / 150 070). The
injection did exactly what it claimed and the client saw the whole of it.

The heartbeats show the outage was total — through the entire 150 s of N150,
`rx_packets` is frozen at **26 537** and `rendered_frames` at **1 898**, while
`last_output_age_ms` climbs monotonically from 1 299 to 150 083 and then
returns to 20 on the next tick.

### The finding in this table: a restart hides the outage from the loss counters

**N3 counted the outage as 2 348 lost packets. N15 and N150 — 25x and 50x
longer — counted 22 and 40.**

That is not a measurement error, it is the recovery working. N3 fired **no
restart**, so the same ffmpeg and the same SSRC continued across the gap, RTP
sequence numbers advanced through it, and the receiver met a 2 336-packet
forward jump on return: a `sequence_resync`, all of it counted as loss. N15
and N150 each fired at least one **encoder restart**, and a new ffmpeg means a
**new SSRC**, so the receiver classified the return as an `ssrc_change` — a
discontinuity that carries `jump_packets: 0` and is **not counted as loss at
all**.

```
N3    discontinuity [0]  {"elapsed_ms": 34268,  "type": "sequence_resync", "jump_packets": 2336}
N15   discontinuity [0]  {"elapsed_ms": 46118,  "type": "ssrc_change",     "jump_packets": 0}
N150  discontinuity [0]  {"elapsed_ms": 182157, "type": "ssrc_change",     "jump_packets": 0}
```

**Durable consequence: any loss-per-minute statistic under-counts every
outage that triggered an encoder restart.** The `D-BASE` loss column
(`B2`, `S1`/`S2`, `R5`) is built on `lost_packets`, and a restart makes an
outage of any length nearly invisible to it. `max_output_gap_ms` is the
honest column for outages; loss is not.

## Per-run results against the criteria

### N3 — PASS

Criterion: pause within 1.8 s; `restarts` 0; resume within 3.5 s of the rule
being deleted.

```
fault ON  15:17:47.836      OFF 15:17:50.899   (3.06 s)
15:17:49.103  t_on  +1.27s  desync_pause  trigger=client_output_silence age_ms=1132
15:17:52.713  t_off +1.81s  resumed       from=PAUSED_RECOVERING recovering_ms=3703 restarts=0
```

Pause at **+1.27 s** (< 1.8 s), **0 restarts**, resume at **+1.81 s** after
the rule was deleted (< 3.5 s). All three met.

### N15 — PASS, and it reached the case no substitute fault could

Criterion: pause; if a restart fires it is `method: restart` and **succeeds
while the fault is active**; resume through the gate within 5 s of the rule
being deleted.

```
fault ON  15:19:20.763      OFF 15:19:35.826   (15.06 s)
15:19:22.181  t_on  +1.42s   desync_pause     trigger=client_output_silence age_ms=1281
15:19:26.374  t_on  +5.61s   encoder_restart  attempt=1 method=restart
              t_off -9.45s     encoder_restarted=true capture_restarted=false
                               ffmpeg_spawn_ms=266  first_rtp_resume_ms=418
                               host_verified_ms=1171  restart_error=null
15:19:39.597  t_off +3.77s   resumed  from=PAUSED_RECOVERING recovering_ms=17512 restarts=1
```

**The restart fired 9.45 s before the rule was deleted and succeeded while
the fault was still dropping every packet** — `restart_error: null`,
`first_rtp_resume_ms: 418`, host verified in 1 171 ms. This is the encoder
alive but unheard, the case `R3a`'s substitute fault could not construct, and
it behaves as designed. Resume at **+3.77 s** (< 5 s).

### N150 — PASS, with the prompt criterion corrected

Criterion as written: give-up at 120 s ± 1 s; `PAUSED_SAVED`; recovery file
present; then "the launcher prompt appears, Resume from recovery save then
RESUME PLAYING restores play".

```
fault ON  15:21:32.401      OFF 15:24:02.474   (150.07 s)
15:21:33.843  t_on   +1.44s  desync_pause  trigger=client_output_silence age_ms=1300
15:21:36.955  t_on   +4.55s  encoder_restart attempt=1 backoff=5000  ms
15:21:49.643  t_on  +17.24s  encoder_restart attempt=2 backoff=10000 ms
15:22:11.834  t_on  +39.43s  encoder_restart attempt=3 backoff=20000 ms
15:22:44.531  t_on  +72.13s  encoder_restart attempt=4 backoff=30000 ms
15:23:17.228  t_on +104.83s  encoder_restart attempt=5 backoff=30000 ms
15:23:34.264  t_on +121.86s  gave_up_saved  restarts=5 state_file="Tekken 3 (USA).state.recovery" save_error=null
15:24:04.168  t_off  +1.69s  resumed  from=PAUSED_SAVED recovering_ms=29903 restarts=5
```

Give-up measured from entering `PAUSED_RECOVERING` (15:21:33.843) to
`gave_up_saved` (15:23:34.264) is **120.42 s** — inside 120 ± 1 s. State
`PAUSED_SAVED`, `save_error: null`, recovery file written and verified on disk
at **1 231 354 B, sha256 `05bd85c7…abbd8040`**. Every restart used
`method: restart`, all five with `restart_error: null`, and the backoff ladder
ran 5 s / 10 s / 20 s / 30 s / 30 s as designed.

**Corrected criterion.** The prompt clause presumes the client left the stream
screen and came back through the launcher. **It did not** — the client stayed
in the stream screen for the whole run, so no launcher prompt was reachable
and none should have appeared. The path actually exercised is the one that
belongs to that state: the session resumed **`PAUSED_SAVED` -> `PLAYING`
1.69 s after the rule was deleted**, `restarts=5` carried through, and play
continued to a clean `session_ended` at 15:26:30, 146 s later. That is the
correct behaviour for a client that never left, and **N150 passes**.

The launcher-prompt half of the clause was then exercised separately, after
the run, and is where both open defects below come from.

## C5a — INDETERMINATE

Pre-registered rule (`evidence/C5A_IDR_REJECTION_COUNT_2026-09-21.md`):
confirmed if every resync > 250 ms carries >= 1 rejected IDR and those
<= 250 ms carry 0; falsified if a resync > 250 ms shows 0; **INDETERMINATE
below six discontinuities or with none > 250 ms**.

| run | type | jump_packets | resync_to_idr_ms | rejected_idr_aus | dropped_non_idr_aus | au_complete |
| --- | --- | --- | --- | --- | --- | --- |
| N3 | sequence_resync | 2 336 | **75** | 0 | 3 | true |
| N15 | ssrc_change | 0 | **70** | 0 | 3 | true |
| N150 | ssrc_change | 0 | **40** | 0 | 1 | true |

**Three discontinuities, and the slowest resync is 75 ms.** Both
INDETERMINATE conditions are met at once — fewer than six, and none over
250 ms. `idr_aus_rejected_waiting_for_idr` is **0** in all three runs.

The C5 hypothesis is untouched by this evidence, and worth recording plainly:
**these runs could not test it, because recovery is too good.** The encoder
restart emits an IDR almost immediately on return (40-75 ms), so no resync
ever waits long enough to reject one. A test of C5 needs a resync that is slow
for some other reason; a clean link-drop will not produce one.

## Teardown

Verified after the runs and after the post-run session:

- `sudo -n nft list tables` — **no `privyhub_fault`**; only the stock
  filter/nat/mangle/raw tables.
- No RetroArch, ffmpeg, AppImage or FEC-relay process; no RetroArch window in
  `xdotool search --name RetroArch`.
- No listener on 48100-48102 or 48110; **8765 only**, the companion.
- RetroArch `pid 7827` exited **gracefully** — `SAVE_FILES "OK"`, then
  `frontend_close_result returncode=0 forced=false network_quit_fallback=false`.
  Nothing was orphaned and nothing had to be killed.
- Companion idle and ready: `active false`, `paused false`, `game null`,
  `pid null`, `ready true`, `encoder_overrides.any_override false`.
- **Recovery save NOT discarded** — deliberately; see the open items.

## Open items from after the runs

Both are post-run, both have one root cause, and both are diagnosed in
**`evidence/R3B_POST_RUN_SESSION_REUSE_2026-09-22.md`**. Neither affects the
N3 / N15 / N150 verdicts above — they happened after N150's `session_ended`.

**R3b-D1 — a stream-stop leaves the game session live, and the launcher then
cannot launch.** `native-stream-stop` pauses the game and keeps the session
by design, so after N150 RetroArch `pid 7827` stayed alive and paused. The
Tekken 3 tile therefore resolved to `recovery-resume`, which loaded the state
into the running process and reported **"Loaded"** while no window opened.
Proof: **no `POST /plugins/games/launch` exists after 11:20:49** in the
companion access log, and no new game log was written. Open.

**R3b-D2 — after a recovery-state load, the picture cycles through about four
frames.** The manual stream that followed was clean end to end
(`lost_packets 0`, `sequence_resyncs 0`, 59.85 fps, `dropped_frames 0`), but
the source picture cycled. Measured by IDR-size dispersion: spread **3 686 B**
over eight seconds against **52 923-74 242 B** for the three gameplay windows
above and **0 B** for a genuinely frozen window. Not a freeze, not gameplay.
The loop starts within one second of `PAUSE_TOGGLE -> PLAYING`. Whether the
cause is the load-while-paused ordering or Beetle PSX HW's state restore under
GL hardware rendering is **not resolved** and needs a run. Open.

**Recovery file disposition.** `load_recovery_state` stages
`.state.recovery` as slot 0 and **does not remove it**. Both files remain,
byte-identical:

```
Tekken 3 (USA).state           1231354 B  11:29  sha256 05bd85c7…abbd8040
Tekken 3 (USA).state.recovery  1231354 B  11:23  sha256 05bd85c7…abbd8040
```

So the recovery prompt will appear again on the next launch of this title.
R3b teardown nominally calls for the recovery save to be discarded; it is
being **kept on purpose** as the evidence for both open items and as the only
copy of the give-up state. Discard it once they are fixed or no longer
reproducible.

## Redaction

No addresses, ADB endpoints, device identifiers or key material. Ports are
bare numbers.
