---
memory_schema: 1
as_of: 2026-10-01
baseline_commit: 4e45a4f
status: C3-L4-D1 DONE — live adaptive bitrate ON BY DEFAULT since 2026-10-01 13:07Z through the unit drop-in privyhub-companion.service.d/adaptive.conf (the user's authorization 2026-09-30). B1 verified (environ exactly PRIVYHUB_ADAPTIVE_BITRATE_MODE=live, manager none, mode live / configured live / acts true, any_override false, unit file and shadow unchanged). B2 tools/ preflights updated (nft harness + d7 boot row; 32/32, mutations 4/4, fake-sudo FULL and ABORT PASS with the new end state). B3a injection session NOT PASS AS PRE-REGISTERED — the controller acted as intended (one FALLBACK 7000 → 5000, client ssrc_changes 1, 3-report blackout, level reset to 7000 at BACK, inject flag gone, route 403), but two clauses failed as worded: I1's "ssrc_change row" (never emitted for the controller's own transition) and I3's "stream 7000" (read 0.3 s before the client's native-stream-stop). B3b 30-min hold SILENT (0 transitions / refused / HOLD over 901 reports; client rows met; loss 7.59/min, max gap 447 ms). Teardown clean; nothing committed
---

# C3-L4-D1 — live adaptive bitrate on by default

Task: `handoffs/LINK-L1_LOSS_ROW_LOOK_AND_LIVE_DEFAULT_TASK.md`, Part B,
run after Part A was recorded (`LINK_L1_LOSS_ROW_2026-10-01.md`, MIXED),
with A's flags confirmed absent (0 `PRIVYHUB_*` in the manager and the
environ, 13:06Z).

- The user's authorization, 2026-09-30: "do the loss row look first and
  then the live default".
- Decision: `decisions/C3-L4_LIVE_DEFAULT_2026-10-01.md`.
- Evidence: `c3_l4_d1_2026-10-01/` (manifest).
- **The pre-registration** (`c3_l4_d1_preregistration.txt`, sha256
  `5331dac2…`) was written before the drop-in and before any session.

## B1 — the change (`b1_dropin.log`, `adaptive.conf`)

At 13:07Z the drop-in was written, then `daemon-reload` and a restart of
the unit:

`~/.config/systemd/user/privyhub-companion.service.d/adaptive.conf`

```ini
[Service]
Environment=PRIVYHUB_ADAPTIVE_BITRATE_MODE=live
```

**Verified:**

- `systemctl --user cat` lists the drop-in, and `DropInPaths` names it.
- The new MainPID serves 8765. Its environ carries **exactly one**
  `PRIVYHUB_*`, `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`; the user manager
  carries **none**.
- `native-stream-status`: `adaptive_bitrate.mode live`, `configured_mode
  live`, `acts true`, level 7000.
- `any_override` **false**. The profile is
  `native_game_720p60_reference` at 7000; cap, cushion and redundancy are
  from the profile.
- `fec_scheme_override` and `profile_id_override` are none; the selection
  is `default`. The inject route answers 403.
- **The unit file is unchanged** (sha256 `00d5fe50…` before and after).
- **The shadow is unchanged** (`adaptive_bitrate.py` `d66211b3…`). The
  13 `companion/*.py` files match `companion_sha256_before.txt` at the
  end; no companion code changed.

## B2 — the preflights (`tools_patch.diff`, `harness_tests.txt`, `mutation_check.txt`, `fake_tests.txt`)

**What assumed "no `PRIVYHUB_*`" or "mode off".** A search of `tools/`
(probes included) found two:

- `tools/c3_l4_nft_night.py`: the preflight, setup, teardown and
  `finish()`;
- `tools/d7_regression.py`: the boot row.

Patch record: `patches/C3-L4-D1_LIVE_DEFAULT_PREFLIGHTS.md`.

**What changed in the nft harness:**

- **Accepted:** exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live` in the
  companion's environ, and nothing in the manager.
- **Still refused:** any other `PRIVYHUB_*`, any manager residue, and
  `set-environment` left behind.
- **The baseline** found at preflight (live with the drop-in, off
  without it) is what the teardown restores. The teardown no longer
  `unset-environment`s the mode into off: the unset clears manager
  residue only, and the drop-in is never touched.
- **Found while editing:** `finish()` tore down only when the harness had
  set the flag itself. On the default-live companion it never sets it, so
  the old code would have **skipped the teardown entirely**. It now keys
  on "setup ran".

**Results:**

- Tests: **32/32** (24 + 8 new); mutations **4/4 caught**; the live and
  shadow controller tests 123/123.
- **Fake-sudo runs** on the default-live companion (`d1_fake_tests.sh`,
  `d1_check.py`; run dirs in `logs/streaming/c3_l4_d1_tests/`):
  - **FULL** (F1, F2, F3, K, `--fast`): exit 0, **PASS**;
  - **ABORT** (`--only F1`, an exception at F1's cap): exit 4, **PASS**;
  - in both, live came up by default (no `set-environment`). The teardown
    was clean against the baseline, and afterwards the manager was empty,
    the environ held the one name, and the mode was live.
- **Evidence copies of older scripts are history and were not edited**
  (`TOOLS.md`).

## B3a — the injection session (`runs/*_I*`, `d1_score.txt`)

**How it ran.**

- `PRIVYHUB_ADAPTIVE_BITRATE_INJECT=1` was set in the manager for this
  session only, and the companion restarted. Its environ then held
  `INJECT=1` and the drop-in's `MODE=live`; no mode flag was set
  anywhere.
- PLAYING at 13:31:13Z. One `inject?class=FALLBACK` at 13:33:13Z; the
  hold ran 120 s past it, plus 60 s; then BACK.

**What happened:**

- **One FALLBACK, acted**: `transition` (`decrease_fallback`) 7000 →
  5000, then `transition_done` in 1,237 ms (`injected: true`).
- The client's report: **`ssrc_changes` 1**, one discontinuity
  (`ssrc_change` at 126,996 ms).
- The controller's **3 blackout samples** followed. The level held at
  5000 for the rest of the session: 1 transition, no second decision.
- `any_override` false at PLAYING and at the end.
- **BACK**: `session_ended_reset` with "before" 1 transition at 5000, and
  level 7000. The status after BACK read level 7000, 0 transitions,
  REFERENCE.
- **After the session:**
  - the inject flag was unset and the companion restarted;
  - the manager was empty, and the environ held exactly the one name;
  - the inject route answered **403**.

**By the pre-registered rows: NOT PASS AS PRE-REGISTERED.** I2 and I4
PASS; I1 and I3 FAIL as worded. The rows stand. The diagnosis below was
written after the data and does not change them.

- **I1** asked for an "`ssrc_change` row" in the decision log.
  - The live controller emits that row only from
    `note_recovery_restart` (recovery's restarts, as on the `nft`
    nights). It never emits it for its own transition: L1's injection
    session had none either.
  - The SSRC change the handoff means is on the client (L1's B1 measured
    it there), and it is there: exactly one.
  - So **the pre-registration named the wrong place to look**. Every
    other part of I1 held.
- **I3** asked for "the stream 7000" after BACK.
  - The harness's post-BACK read (09:36:16 local) came 0.3 s **before**
    the client's `native-stream-stop` reached the companion (09:36:17,
    `companion_I.log`). It read the still-active session: `active true`,
    `bitrate_kbps` 5000.
  - The stop path resets the active bitrate to the profile's 7000
    (`companion/native_stream.py`, `stop`: `_active_bitrate_kbps =
    BITRATE_KBPS`), and a full start resets to 7000 too.
  - But **no read was taken between the stop and the restart**, so the
    stream clause is unmeasured, not shown to fail. The level clause
    held.
  - L1's harness has the same read timing; night 3 judged "BACK → 7000"
    on the level.

**Client rows (reported):** 5.2 min, loss 13.97/min, max gap 202 ms,
spikes 47.3/min, fps 59.77.

## B3b — the 30-minute hold on the default (`runs/*_H*`, `d1_score.txt`)

**How it ran.**

- PLAYING 14:07:16Z, 10:07 local, more than 30 min after Session I's
  `session_ended`.
- No flags at all: the manager was empty and the environ held only the
  drop-in's name.
- Mode live, configured live, `any_override` false; T2 on.

**SILENT, by the pre-registered rule:**

- The decision log for the session: 901 `sample` rows (842 clean), 108
  `state` rows (REFERENCE ↔ PRESSURE), **0 `transition`, 0 `would_act`,
  0 `refused`, 0 `hold`, 0 HOLD states**, 0 rows acted.
- Client rows, all met: spikes 59.9/min (< 200), fps 59.93 (≥ 59.5),
  stale 0.56/min (< 20), underruns 0.70/min (< 5).

**Reported against Part A:**

- Loss **7.59/min**, which meets < 10.
- Max output gap **447 ms**, which misses ≤ 100. That is the day's
  largest; on the client report, with 0 SSRC changes and 33
  unrecoverable FEC groups.
- Part A was MIXED, so there is no window to place the hold in. It ran
  at 10:07 local, in the 08-12 block, where Part A's H6 missed (16.78).
- **The radio** (T2): the onn's link was 195, the Opal's signal −78 dBm,
  and 84 % of samples were at MCS 1, with 7.0 % retries.
  - The hold met the loss row anyway. This is one more case against the
    post-hoc MCS ordering in Part A's record.
  - The signal is 3-6 dB weaker than during Part A's holds.

## Teardown (the night's, 14:38Z)

- The manager PRIVYHUB_* was empty, so no `set-environment` residue.
- The environ held exactly `PRIVYHUB_ADAPTIVE_BITRATE_MODE=live`, and the
  mode was live, configured live, acts true, from the drop-in.
- The stream was 7000, with no game.
- The inject route answered 403.
- The APK `de072762…835e` was confirmed.
- One stale NOW PLAYING banner was cleared by one force-stop and
  relaunch, leaving 0.

## Files (`c3_l4_d1_2026-10-01/`)

- **Pre-registration:** `c3_l4_d1_preregistration.txt` (+ `.sha256`).
- **B1:** `adaptive.conf` (the drop-in, verbatim), `b1_dropin.log`,
  `unit_file_sha256_before.txt`, `companion_sha256_before.txt`.
- **B2:** `tools_patch.diff`, `harness_tests.txt`,
  `controller_tests.txt`, `mutation_check.txt`, `d1_fake_tests.sh`,
  `d1_check.py`, `fake_tests.txt`.
- **B3:**
  - the harness: `c3_l4_d1_night.sh`, `c3_l4_d1_run.sh` (derived from
    L1's), `t2_sample.py`;
  - logs and samples: `c3_l4_d1_night.log`, `t2_samples.jsonl`,
    `t2_sampler.log`;
  - `runs/` (per session: `armcheck`, `status`, `status_end`, `report`,
    `decision_log`, `abr_series`, `frames`, `heartbeat`, `companion`
    (redacted), `inject1_I.json`; `index.txt`, `clock_H.txt`);
  - scores: `d1_score.py` → `d1_score.txt` / `.json`.
- **Checks:** `sha256_manifest.txt`, `redact_check.txt`.
