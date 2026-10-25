# B23 — the stack's thresholds on a WAN path: design, written before any B23 code

Baseline HEAD 13ccff5 + B21 + B22 (uncommitted). Queue: `handoffs/QUEUE_2026-10-24H.md` §B23. **Condition met:**
`evidence/WAN_R1_OFFSITE_GAP_DISTRIBUTION_2026-10-24.md` exists (A's, 17:58Z, with its manifest; sha256 in
`wan_r1_read_sha256.txt`).

## 0. WAN-R1's numbers (§3 of its record, `wan_r1_tables.json`)

| class | streaming min | silences ≥ 250 / 10 | would hold (≥ 950) / 10 | would stall (output ≥ 400) / 10 | H for ≤ 1 / 10 (each / pooled) | stall for ≤ 1 / 10 (each / pooled) |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| direct (WAN) | 113.0 | 0.0 | 0.0 | 0.0 | 250 / 250 | 200 / 200 |
| relayed (WAN) | 0.5 | — | — | — | not answerable | not answerable |
| no-peer (off the overlay) | 3.0 | 120.0 | 0.0 | 0.0 | 700 / 700 | 250 / 250 |
| lan (5 GHz) | 47.1 | 1.27 | 0.0 | 0.23 | 550 / 300 | 350 / 350 |

- **direct:** 0 non-drop silences ≥ 250 ms in 113 min and 0 output gaps ≥ 400 ms. H's 250 is the grid's floor (no
  silence to bind it); the stall's 200 is bound by the output gaps ≥ 200 ms (0-0.1 / min).
- **relayed:** no data in play. **no-peer** is the flapping regime after a hotspot toggle, not a WAN class.

## 1. The stack's own constraints on the values

- **H and the silence save** (B9 / B12's `state` path): `rewind_cores.parse_state_at` puts the save at
  min(400, H − 50).
  - CL-B12 benched the order save (~400) → pause (H) with ≥ 50 ms between.
  - **H ≥ 450 keeps the save at 400**, i.e. every other module as configured and benched.
  - Below 450 the save point would move (it is computed once at the wire), or the order would flip.
  - **So the direct H is max(WAN-R1's 250, 450) = 450.**
- **The stall threshold and B16's save:** B16's stall save fires at `age >= threshold_ms` (passed per datagram), so it
  follows the threshold. B8's `ignore_stall` and B12's owner take the threshold per call too. The client sends its
  stall datagrams from an output age of 150 (B19's default), below any threshold here. **The direct stall is WAN-R1's
  200.**
- **Both values are set at the wire today** (`det.hold_s` on B2's detector, `Tuning.hold_ms`; `StallSignal.threshold_ms`).
  Setting them per session at the stream's start reaches every reader: the detector reads `hold_s` at each quiet
  check, the stall signal its `threshold_ms` per datagram.

## 2. The design: `PRIVYHUB_LINK_RECOVERY_WAN=1`

New `companion/link_recovery_wan.py`, imported by `plugins/games.py` only when the flag reads exactly `1`.

**The sets** (the LAN's stay as they are):

| set | when | H | stall | why (logged) |
| --- | --- | --- | --- | --- |
| `lan` | the client's address is not the overlay's | as wired (950 with B6) | as wired (400 with B9) | the LAN's, unchanged |
| `remote-direct` | an overlay address, and the overlay provider's `path` is `direct` | **450** | **200** | WAN-R1 direct (113 min: H ≥ 250 / stall ≥ 200 for ≤ 1 false fire / 10 min); H clamped to 450 so the silence save stays at 400, 50 ms before the hold |
| `remote-relayed` | overlay, `path` `relayed` | as wired | as wired | WAN-R1: relayed not answerable (0.5 min) |
| `remote-unknown` | overlay, `path` `no-peer` / `none`, the provider absent or unread (yet) | as wired | as wired | no WAN-R1 class (`no-peer` is the flapping regime) / the path not known |

**The path class:**
- **remote / lan:** G5-S3's `remote_ladder.routing_evidence_of(client_ip)`, G3's overlay address test. A pure
  function, imported without the ladder's flag. Only the class is kept; the address is never stored or logged.
- **direct / relayed:** `overlay.select_provider(os.environ)` (the service's own provider choice,
  `PRIVYHUB_OVERLAY_PROVIDER`), `state().path`. That is the classification WAN-R1's data used: Tailscale's `direct` =
  an online peer with a direct address.
  - The provider spawns `tailscale status --json` (10-s cache, 10-s timeout), so it is read **on a daemon thread after
    the stream's start**, never in the request.
  - Until it answers the session runs `remote-unknown` (as wired). A late answer for an older session is ignored (a
    session counter).

**When:** at every `native-stream-start` (today's start and B22's), after the bookkeeping:
`note_stream_start(client_ip)`:
- `lan` applied synchronously;
- for an overlay address, `remote-unknown` at once, then the thread → `remote-direct` / `-relayed` / `-unknown`.

**Applied:**
- `det.hold_s` and `Tuning.hold_ms` when B2's detector (with B6) is wired;
- `StallSignal.threshold_ms` when B7's signal is wired;
- whichever exists. Nothing else changes: the save point, the cap rules, the rewind cap, the client.

**The config rows (`link_recovery_config` says which set is in force and why):**
- at the wire, `link_recovery_wan_config`: the flag, the four sets with their values and reasons, and the wired (LAN)
  values. B21's wire-time `link_recovery_config` row is unchanged;
- **at each set applied** (the stream's start, and the overlay's answer): one `link_recovery_config` row:
  - B21's fields when the umbrella is on (`config_row`; omitted without it);
  - `at` `session`;
  - `wan`: `set`, `path_class` (`lan` / `remote`), `path` (`direct` / `relayed` / `no-peer` / `none` / `unread` /
    `pending`), `hold_ms`, `stall_ms`, `why`.

**Absent = today, byte for byte:** `link_recovery_wan` imported only under the flag. `plugins/games.py`'s B23 items
are `_link_recovery_wan = None`, the import `if`, the wire's `if _link_recovery_wan is not None:` and the start's
`if _link_recovery_wan is not None and …:`. Proof: the module's AST with them removed = the predecessor's (HEAD + B21
+ B22).

## 3. Tests (`tests/link_recovery_wan/`, new)

- **The fake path class** (the address test and the overlay state injected; the real detector, `Tuning` and
  `StallSignal` objects as each module's wire makes them, with a fake recovery):
  - `lan` → **950 / 400**;
  - `remote-direct` → **450 / 200**;
  - `remote-relayed` → 950 / 400 (why: not answerable);
  - `remote` with `no-peer`, `none`, the provider absent or raising → 950 / 400;
  - **sessions in turn** (lan → direct → lan): restored each time;
  - a late overlay answer for an older session: ignored;
  - the rows: `link_recovery_config` per set applied, with `wan`; and with the umbrella, B21's fields beside it.
- **The stall acts at the set's threshold:** the real `StallSignal.handle` with a fake recovery in PLAYING. A stall
  datagram at age 250 → a pause on `remote-direct`, nothing on `lan`.
- **The hold acts at the set's H:** the real `InputHoldDetector.on_quiet` with an injected clock. A 600-ms silence →
  a hold on `remote-direct`, none on `lan`.
- **The replay** (LAN-R1's form: the real code in process, fed from the recorded logs): the control-gap log's
  silences through the real `InputHoldDetector` at the old H (950) and the new (450). The holds are counted and
  classed real (≥ 3 s, WAN-R1's rule) or false:
  - **G4-S4's log** (the queue's ask; 3 silences) → the false holds at 950 and at 450. In the unit test its 3 rows are
    inline (no address in them);
  - the evidence script `replay_holds.py` over every log WAN-R1 read: G4-S4, G4-S1..S3's copies (s1r2 includes the
    no-peer span after the toggle, shown apart), and CL-B11 cell 1 (LAN). It shows why the LAN keeps 950: its 564-ms
    silence would hold falsely at 450.
- Absent: nothing imported. The flag `0` / `yes` / empty → nothing. Every `tests/` suite green.

## 4. Files

`companion/link_recovery_wan.py` (new), `companion/plugins/games.py`, `tests/link_recovery_wan/` (new). Record
`evidence/B23_LINK_RECOVERY_WAN_THRESHOLDS_2026-10-24.md` + `b23_2026-10-24/` (+ `replay_holds.py` / `.md`);
`patches/B23_LINK_RECOVERY_WAN_THRESHOLDS.md`. Host-side only: no APK.
