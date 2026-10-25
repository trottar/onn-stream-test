---
memory_schema: 1
as_of: 2026-10-24
baseline_commit: 13ccff5 (+ B21 + B22; B23 uncommitted)
---

# B23 — the stack's thresholds on a WAN path: H 450 / stall 200 on the overlay's direct path, the LAN's and the rest as wired

**Classification: BUILT** behind `PRIVYHUB_LINK_RECOVERY_WAN=1` (host only). It ran because
`WAN_R1_OFFSITE_GAP_DISTRIBUTION_2026-10-24.md` existed when B reached it: A's record, written 17:58Z with its
manifest, read at ~18:12Z (sha256 in `b23_2026-10-24/wan_r1_read_sha256.txt`).
- **Tests:** `tests/link_recovery_wan` **22 green** in the tree (2 of them read the evidence copies and skip in the
  `/tmp` copy). Every `tests/` suite green.
- **The replay of G4-S4's control-gap log: 0 false holds at H 950 and at H 450** (3 holds, all real drops ≥ 3 s).
- **Proof:** AST identical with B23's 4 items removed. **PROVEN.**
- **Designed twice, each hashed before its code:**
  - the design at 18:15:45Z;
  - **addendum 1** at 18:18:39Z, after the first replay showed a session that starts direct and leaves it (G4-S1
    run 2).
- NOT ADOPTED; no live run; nothing committed.

## 0. From WAN-R1 to the values

- **WAN-R1 §3, for ≤ 1 false fire / 10 min:**
  - direct (113 min): H ≥ 250, the stall ≥ 200;
  - relayed: not answerable (0.5 min);
  - the LAN binds first (H 550 each / 300 pooled; the stall 350).
- **The stack's constraint on H:** `rewind_cores.parse_state_at` puts B9 / B12's silence save at min(400, H − 50).
  - CL-B12 benched it as save (~400) → hold (950).
  - **H 450 is the lowest H that keeps the save at 400, 50 ms before the hold.**
  - The direct H is therefore max(250, 450) = **450**.
- **The stall:** B16's stall save fires at `age >= threshold_ms` per datagram, so it follows the threshold. The direct
  stall is WAN-R1's **200**.

| set | when | H | stall | why (logged) |
| --- | --- | --- | --- | --- |
| `lan` | not an overlay address | as wired (950) | as wired (400) | the LAN's, unchanged |
| `remote-direct` | an overlay address and the overlay's path `direct` | **450** | **200** | WAN-R1 direct; H clamped to keep the save at 400 |
| `remote-relayed` | path `relayed` | as wired | as wired | WAN-R1: relayed not answerable (0.5 min) |
| `remote-unknown` | `no-peer` / `none` / the provider absent, unread or pending; or the guard tripped | as wired | as wired | no WAN-R1 class / not known / the guard |

## 1. Built (`b23.diff`)

**`companion/link_recovery_wan.py` (new):**
- **The path class:**
  - remote / lan from G5-S3's `remote_ladder.routing_evidence_of(client_ip)` (G3's overlay address test; only the
    class is kept, never the address);
  - direct / relayed from `overlay.select_provider(os.environ).state().path`, the classification WAN-R1's data used.
    It is read on a daemon thread, never in the request (it spawns `tailscale status`).
  - Until the path is read the session runs `remote-unknown`. A late answer for an older session is ignored.
- **At every `native-stream-start`** (today's and B22's), after the bookkeeping, the set is applied to:
  - B2's detector (`hold_s`, and B6's `Tuning.hold_ms`);
  - B7's `StallSignal.threshold_ms`, whichever is wired.
  - Nothing else changes (the save point, the caps, the rewind cap, the client).
- **Addendum 1:**
  - the path is re-read **every 10 s** during a remote session; a change logs a row (nothing new → no row);
  - **the guard:** on `remote-direct`, the first hold whose silence ends in < 3 s (a non-drop silence ≥ 450 ms; none in
    WAN-R1's 113 direct min) reverts the session to the wired values. The re-read does not re-apply direct in that
    session.
  - The guard reads B2's detector's own `release` event: its emit is wrapped, the original called first and
    unchanged. The revert runs off the receive loop.
- **The rows:**
  - at the wire, `link_recovery_wan_config`: the four sets with values and reasons, the wired (LAN) values;
  - **at each set applied, `link_recovery_config`**, with `at` `session` and `wan` {`set`, `path_class`, `path`,
    `hold_ms`, `stall_ms`, `why`}, plus B21's umbrella fields when the umbrella is on.
  - B21's wire-time row is unchanged.
  - **Disclosed:** in a session row, `at` reads `session`, where B21's own row reads `import` (as the design wrote it).

**`plugins/games.py`:** the import, the wire (after every threshold's own wire: B2 / B6 / B7 / B8 / B12), and
`note_stream_start(client_ip)` after `self._recovery.note_stream_start()`.

## 2. Tests (`tests_link_recovery_wan.txt`)

- **The fake path class** (the address test and the overlay's path injected; the real B2 detector with B6's `Tuning`,
  the real B7 `StallSignal`; a fake recovery):
  - `lan` → **950 / 400**;
  - **`remote-direct` → 450 / 200** (rows `remote-unknown` pending, then `remote-direct`);
  - `remote-relayed`, `no-peer`, `none`, `unread`, and a raising provider → 950 / 400;
  - sessions in turn lan → direct → lan → direct: 950/400, 450/200, 950/400, 450/200;
  - a late overlay answer for an older session: ignored;
  - only what is wired is set (no hold → the stall only; neither → `ignored`);
  - the rows with the umbrella (B21's fields beside `wan`);
  - with no `PRIVYHUB_OVERLAY_PROVIDER` the default reader returns `unread` and spawns nothing.
- **The thresholds act:**
  - the real `StallSignal.handle` with a 250-ms stall → `client_stall` on direct, nothing on the LAN;
  - the real detector with a 600-ms silence → one hold on direct, none on the LAN.
- **Addendum 1:**
  - the re-read follows direct → no-peer (950 / 400) → direct (450 / 200), with no row when nothing is new;
  - the loop ends when its session does;
  - **a 600-ms silence on direct → a hold, the release, then 950 / 400** (`WHY_GUARD`, `guard_trips` 1). The re-read
    does not bring 450 back; a new session does;
  - a 5-s real drop does not trip the guard; the guard never acts on the LAN.
- **The replay** (the real detector, 10-ms quiet checks, the recorded silences):
  - G4-S4 (inline rows, equal to the log): **3 real / 0 false at 950, at 450 and at 450 + guard**;
  - G4-S1 run 2 (from the evidence copy): **0 / 1 at 950, 0 / 18 at 450, 0 / 2 with the guard**.
- Absent: nothing imported. The flag reads exactly `1`.
- **Every `tests/` suite** (`tests_regression_after_b23.txt`): the same outcomes as the baseline, plus
  `restart_fast` and `link_recovery_wan`.

## 3. The replay over every log WAN-R1 read (`replay_holds.py` → `replay_holds.md` / `.json`)

Whole logs, **no 10-s edge exclusion (stricter than WAN-R1)**; a hold on a gap ≥ 3 s is real. The first run, before
addendum 1, is kept as `replay_holds_before_addendum.md`.

| log | class | silences ≥ 250 | H 950 false | H 450 false | H 450 + guard false |
| --- | --- | ---: | ---: | ---: | ---: |
| **G4-S4** | direct | 3 (all ≥ 3 s) | **0** | **0** | **0** |
| G4-S1 run 1 | direct | 2 | 0 | 0 | 0 |
| G4-S1 run 2 (incl. the no-peer span after the toggle) | direct + no-peer | 54 | 1 | **18** | **2** |
| G4-S2 run 1 | direct | 2 | 0 | 0 | 0 |
| G4-S3 | direct | 1 | 0 | 0 | 0 |
| LINK-R1 / G-A3 / CL-B10 c1 / CL-B12 c1 | lan | 0 / 0 / 2 / 2 | 0 | 0 | 0 |
| CL-B11 cell 1 | lan | 7 | 0 | **2** (540, 564) | 1 |
| CL-B10 cell 4 (2.4 GHz, reference) | lan | 221 | 10 | **59** | 10 |

- The LAN rows are what 450 *would* do there; **the LAN keeps 950.** That is why the set is per class.
- **On direct, 450 adds no false hold in any log.** The guard limits a session that leaves the direct path to one
  false hold before it reverts (the re-read then holds it at the wired values).

## 4. For CL-B13 (A): the remote class on the bench

The shim's WAN profile (the remote ladder's bench) with `PRIVYHUB_LINK_RECOVERY_WAN=1` beside the umbrella. **The
remote class needs an overlay address as the client's** (the onn over the overlay); on the bench LAN the class reads
`lan`, and the row says so.

Rows:
- `link_recovery_wan_config` (the sets);
- per session, `link_recovery_config` `wan.set` `remote-direct` with `hold_ms` 450 / `stall_ms` 200, after a
  `remote-unknown` / `pending` row;
- the hold's pause at ~450 ms (`desync_pause` `input_hold` `age_ms` ≈ 450) and the silence save before it (~400 ms);
- a `@down` blackout's stall pause from ~200 ms;
- **0 false holds outside the blackouts;**
- on the LAN, the same cell reads `lan` / 950 / 400.

## 5. Files

- **`b23_2026-10-24/`:**
  - `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/` (+ note), `predecessor_sha256.txt`,
    `after_sha256.txt`, `wan_r1_read_sha256.txt`;
  - the design + `design.sha256` + `design_hashed_at.txt`;
  - `design_addendum_1.md` + `.sha256` + `_hashed_at.txt`;
  - `b23.diff`, `proof_flag_absent.py` / `.md`;
  - `replay_holds.py`, `replay_holds.md` / `.json`, `replay_holds_before_addendum.md` / `.json`;
  - `tests_link_recovery_wan.txt`, `tests_regression_after_b23.txt`;
  - `redact_check.py` / `.txt`, `manifest.sha256`.
- **Elsewhere:** `companion/link_recovery_wan.py` (new), `companion/plugins/games.py`, `tests/link_recovery_wan/`
  (new); `patches/B23_LINK_RECOVERY_WAN_THRESHOLDS.md`; `logs/b23_git_status.txt`.
- **The rules held:** no stream, no restart, no adb, no sudo, no nft; the Opal untouched; nothing of
  `privyhub-link-n1` touched; WAN-R1's files read only; nothing fetched, deleted, adopted or committed.
