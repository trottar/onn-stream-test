---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: aa884a3 (UX-R3 / LAN-R1 committed; the tree carried the two user prompts, the queue and BENCH-R1's task file, not touched)
---

# B1 — the shim's blackout, both directions (reproduce UX-R3's death on the bench)

**Classification: BUILT behind `PRIVYHUB_IMPAIRMENT` (G8-P1's flag); proved in process; flag absent = today
(AST-identical hooked functions, not imported); NOT ADOPTED; no stream; nothing committed.**

Queue `handoffs/QUEUE_2026-10-22B.md` item B1, session B. Design `b1_2026-10-22/design_written_before_code.md`,
sha256 `61387efb…a8d0`, hashed **00:32:13Z, before any code edit**.

**What it reproduces** (`UX_R3_FIND_THE_DEATHS_2026-10-21.md`, 04:54:55-04:54:59Z): the link dead both ways for 3-4 s.
The host had no input and no heartbeat, the downlink froze, and the game ran on.

## 1. What was built

**The grammar** (`companion/impairment.py`):
```
blackout-<D>s@both[,every=<P>s][,first=<F>s][,seed=N]     the downlink (@post-fec) AND the uplink
blackout-<D>s@down[,every=<P>s][,first=<F>s][,seed=N]     the downlink only (@post-fec)
```
- D is 0.1-60 s. P defaults to 120 and must exceed D; F defaults to P.
- It combines by `+` with the table's profiles.
- `@both` / `@down` / `every=` / `first=` without a blackout name are refused.
- Today's specs parse as before (tested).

**One scheduler:** `Blackout` (pure: dark while `(now − epoch − F) mod P < D`) and `shared_blackout(profile)`, one
object per process.
- The downlink shim and the three uplink gates read the same object, with its epoch at the first use: the companion's
  import of a hooked module.
- Blackouts fall at epoch + F + k·P on the companion's monotonic clock, independent of stream starts. It is the link,
  not the stream.

**The downlink:** `Impairer.offer` has a new first stage: in a dark span the packet is dropped and counted
`dropped_blackout`.

**The uplink:** `UplinkGate.drop(kind)` exists only for `@both`; it counts by kind and in total, as `uplink_dropped`.
The shim's per-second line and `status()` carry `uplink_dropped`, and `status()` also gives the drops by kind.

| receive point | file | hook (one guarded statement) | effect in a dark span |
| --- | --- | --- | --- |
| controller packets (UDP 48102, client → host) | `native_session_io.py`, `NativeControllerBridge._receive_loop` | inside the `try`, after `recvfrom`: `if _impairment_uplink is not None and _impairment_uplink.drop("controller"): raise socket.timeout` | the datagram never arrived: the loop runs its own timeout branch (neutralize after 250 ms, recovery's silence callback once per episode, the gap log) |
| the heartbeat (HTTP, every 2 s) | `plugins/games.py`, `native-stream-heartbeat` | first statement: drop → `{ok: false, impairment: uplink_blackout}` | nothing appended to the heartbeat log; recovery's `note_heartbeat` not called |
| the client-health report (HTTP, every 2 s) | `privyhub_service.py`, `POST /diagnostics/client-health` | after the body is read: `if (_gate := globals().get("_impairment_uplink")) is not None and _gate.drop("client_health"):` → 503 | no snapshot, no stream telemetry, no ladder observe, no WAN classify for that report |

**Why the controller hook raises `socket.timeout` and does not `continue`:** a `continue` would leave `recvfrom` never
timing out during a blackout. The silence checks live in the timeout branch, so the host would never notice.
- **Disclosed:** here the branch runs at each dropped packet (~430 / s), not every 50 ms as on a dead link. It is
  idempotent (once per episode), so the outcome is the same.

**Disclosed, against the design:**
- **The client-health hook looks the gate up** (`globals().get`) instead of naming the module global. G5-S1's
  flag-absent test executes the request-handler class outside its module, where a bare global raised NameError (the
  first regression run: `tests/wan_telemetry` 2 FAIL). With the lookup: 18 OK.
- **On the heartbeat / health side, the client gets an immediate answer,** where a dead link would hang its POST up to
  the 1.5-s read timeout. The client ignores the answer either way, and sends the next one on its own 2-s tick.
- Other uplink requests (start, stop, ready, desync) pass.

## 2. The proof in process (`b1_2026-10-22/proof.py` → `proof_tables.md`, `proof.json`, `proof_console.txt`; run against `/tmp/b_q22`, a copy of `companion/`, `tools/`, `tests/`)

| case (60 s each, loopback) | result | tolerance |
| --- | --- | --- |
| **A. downlink** `blackout-4s@down,every=20s,first=10s`, G8-P1's synthetic 60 fps × 12 packets | sent 43,200, received 34,560, **20.0 %** dropped (`dropped_blackout` 8,640); dark spans start **9.984 / 29.984 / 49.984 s**, each 4.008 s | 3 spans at 10 / 30 / 50 s ± 2 frames, 4 s + 1 frame ± 2 frames, 20 % ± 0.5: **MET** |
| A. the default `blackout-4s@both`, 60 s | 0 dropped | nothing before 120 s: **MET** |
| **B. uplink**: the real `NativeControllerBridge` receive loop (its socket, its 50-ms timeout), 430 controller packets / s; gamepads stubbed | applied-packet gaps **9.998 / 30.000 / 49.998 s, each 4.002-4.004 s**, no other gap > 60 ms; **recovery's silence callback 3 calls** at 11.0 / 31.0 / 51.0 s (1,000 ms threshold); neutralize at +250 ms each; `uplink_dropped` 5,161 against the schedule's 5,160 | **MET** |
| **C. both on one clock** (one shared `Blackout`) | downlink dark from 9.985 / 29.986 / 49.985 s, uplink from 9.999 s on: **within 13-14 ms** | ≤ 20 ms + 2 frames: **MET** |
| D. the HTTP gates (heartbeat, client_health) at 5 / 10.5 / 13.9 / 14.1 / 31 s | pass / drop / drop / pass / drop, counted by kind | **MET** |
| **E. flag absent**: the function holding each hook, AST with **every guarded B1-B3 statement** removed (the queue's three flags absent), against HEAD (git) | `_receive_loop`, `handle_post_request`, `do_POST`: **identical** | **MET** |
| E. a fresh process with no flag, importing `native_session_io` | `impairment` not imported; the gate `None` | **MET** |
| E. a downlink-only profile (`loss-1@post-fec`) | the gate `None`: today's profiles leave the loops ungated (a unit test) | — |

The 60.26-s neutralize calls in B are the end of the run (the sender stopped, then the loop's exit), not a
blackout.

**The proof was run three times; the tables are from the third:**
1. **First, B1 alone:** all MET.
2. **Second, after B2 was in the copy:** E read DIFFERS for `_receive_loop`. B2's hooks sat in the function, and the
   check stripped only B1's.
3. **Third, the check strips every B1-B3 guarded statement:** all MET, with the same A-D numbers.

B2's tests also found a stub bug in B1's helper: `_neutralize()` with no player at the loop's exit. The stub is fixed
(`tests/impairment/test_blackout.py`); the third run used it.

**The cost:**
- the gate: **121 ns a call** outside a blackout, so 0.005 % of a core at 430 packets / s;
- the heartbeat / health gates: once per 2 s;
- the shim thread in A: 1.9-2.1 % of a core. G8-P1 reported 2.1-7.0 % and its cost bar not met; that is stated
  again, not re-litigated.

## 3. Tests (`tests_impairment.txt`, `tests_regression.txt`)

- **`tests/impairment`: 29 OK.** That is G8-P1's 14, unchanged, plus a new `test_blackout.py` with 15:
  - the grammar and its errors; the scheduler's span edges;
  - one shared object; the gate only for `@both`;
  - the downlink drops in the dark only; the gate counts by kind; the counters' new fields;
  - the hooks' shape and guarded imports; flag absent not imported; a downlink profile ungated;
  - a 6.5-s run of the real receive loop: 2 gaps of 1 s, 2 silence calls.
- **The regression set, in the copy, all OK:**
  - overlay 17, session_identity 88, audio_codec 20, encoder_rc 16, wan_adaptation 23, wan_telemetry 18,
    remote_ladder 26, remote_cap 16, start_rung 17, lan_loss_rule 21;
  - **the recovery suite (E3-R2's, run against the copy) 17**;
  - adaptive_bitrate_shadow 21, native_source_contract 7, c5_m1 14;
  - **adaptive_bitrate_live 126**, its golden test run from the tree read-only; **fec_xor8_2 9**, from the tree
    read-only (it reads `logs/games/a1_sample.h264`).
- **`test_c3_f1_recovery_restart` 1 error, pre-existing.** It looks for `restart_encoder=(`, which HEAD's
  `games.py` has never had; recorded on 10-18.
- `git diff --check` clean. `git status` was unchanged across the read-only runs.

## 4. For BENCH-R1 (session A)

- The drop-in: `Environment=PRIVYHUB_IMPAIRMENT=blackout-4s@both,every=120s` (the death), and
  `PRIVYHUB_IMPAIRMENT=blackout-4s@down,every=120s` (the A/B: is it the missing input that kills).
- **The first blackout falls 120 s after the companion's restart**, then every 120 s. A 10-min window after a
  restart-plus-start sees 4-5.
- Read the shim's `uplink_dropped` (and by kind in `status()`), the host's ctrl-gap log (it should show ~4-s gaps),
  the heartbeat log's ~4-s holes, recovery's rows and the hitch metric.

## 5. Files

**`b1_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `b1.diff`, `diffstat.txt`;
- `proof.py`, `proof_tables.md`, `proof.json`, `proof_console.txt`;
- `tests_impairment.txt`, `tests_regression.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:**
- `companion/impairment.py`, `native_session_io.py`, `plugins/games.py`, `privyhub_service.py`;
- `tests/impairment/test_blackout.py` (new);
- `patches/B1_SHIM_BLACKOUT_BOTH.md`;
- `logs/b1_git_status.txt`.

**Outside the tree:** `/tmp/b_q22` (the copy; it holds `tests/recovery_ext/`, E3-R2's suite pointed at the copy).

No stream, no companion restart, no adb, no sudo, no nft, the Opal untouched, nothing fetched, nothing deleted.
`systemctl --user` showed no `privyhub-*` unit but the companion before each run. Nothing of A's touched.
