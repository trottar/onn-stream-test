---
memory_schema: 1
as_of: 2026-10-22
baseline_commit: 144e5c7 (+ B5-B7 / B1b in the tree, uncommitted; lan_loss_rule.py's predecessor is HEAD's)
---

# LAN-R2 — the loss rule rethought on the four real cells: loss alone cannot be told from random loss; the rule becomes "step down when the link is bidirectionally bad"

**Classification:**
- **READ:** on the data on file no host signal tells Sunday's pre-burst loss from 1 % random loss.
- **BUILT:** `PRIVYHUB_LAN_LOSS_RULE=bidir` (unrec AND the uplink's own silences), labelled `lan_bidir`.
- **REPLAYED** through the real controller: 0 asks in BENCH-R1 cells 1-4, every clean window and last night; Sunday's
  first step at 05:06:09Z.
- `=1` (LAN-R1) and absent are unchanged (AST identical, LAN-R1's 21 tests untouched). 10 new tests.
- **NOT ADOPTED; no live run; nothing committed.**

Design `lan_r2_2026-10-22/design_written_before_code.md`, sha256 `2c16b60c…5aa6`, hashed **06:08:49Z**. It came after
the analysis and before any code.

## 1. The question, per minute (`per_minute.md`, `signals.json`)

**The sources:**
- LAN-R1's inputs (the evenings, the eight CL windows, G4-S3);
- BENCH-R1's own logs (`logs_bench/`, read only; cells 1-4 by their client sessions);
- the host's control-gap logs: frozen copies of the live `logs/games/native_stream_ctrl_gaps.log*` in `inputs/`.

**Each ladder sample gets:**
- the nearest heartbeat (LAN-R1's join: 99-100 %);
- the uplink silences ≥ 250 ms that started in its 2-s interval.

| minutes | unrec / min | up ≥ 250 / min | min with an up ≥ 400 | client out-gap max (median) | audio arrival gap max (median) |
| --- | ---: | ---: | ---: | ---: | ---: |
| cell 1 (`loss-1`) | 24.2 | 0.67 | 3 of 12 | 47 | 192 |
| cell 2 (`loss-1`) | 14.7 | 1.69 | 2 of 13 | 50 | 115 |
| cell 3 (`loss-5`) | 270.7 | 3.92 | 5 of 12 | 69 | 223 |
| cell 4 (`burst-50x20`) | 61.2 | 6.15 | 9 of 13 | 61 | 214 |
| **Sunday's step 04:56-05:05** | 8.3 | 3.8 | 7 of 10 | 68 | 187 |
| **Sunday's bursts** (05:06, 05:09-11, 05:20-21) | 36.3 | **23.8** | 6 of 6 | 88 | **831** |
| Sunday's clean minutes | 5.9 | 1.4 | 7 of 34 | 63 | 122 |
| last night's clean minutes | 5.9 | 0.26 | 0 of 31 | 58 | 128 |
| the CL windows (8) | 2.1-4.6 | 0.3-7.9 | 0-9 of 11 | 36-54 | 99-138 |

**Read:**
- Random downlink loss on the bench brings audio arrival gaps and unrec clusters comparable to Sunday's step.
- The client's output gap separates nothing in the step minutes.
- **The bench's random loss raises the uplink's own silences too:** cells 3-4 had 3.9-6.2 / min against the clean
  CL-B7 0.3-3.5. So the uplink is not a pure "other direction" signal.
- Sunday's bursts stand out on the uplink (23.8 / min) and on the audio gap. Its pre-burst step does not.

## 2. The search, and the answer (`rule_search.md`, `rule_search_extended.md`)

**The bar:**
- LAN-R1's base (unrec T 4 K 2) AND one second term;
- 0 in cells 1-2, the clean windows and last night's clean minutes;
- Sunday before 05:06.

**No pair passes:** 34 in the first search, and 96 in the extended one, declared after the first found nothing (the
term over both windows, the term in each window, T 3 K 3, T 3 K 2).
- The closest is `uplink ≥ 250 ms ×3 in a window`: cell 2 has 1 episode, and Sunday fires at 05:03:05.
- One step stricter, Sunday's first firing is 05:06.
- **Stated, as the queue asked: on the data on file, Sunday's pre-burst loss cannot be told from 1 % random loss by
  any host signal.**
- LAN-R1's 05:03 step rested on the unrecoverable groups alone. On these reports they fire in cells 1-2 just the
  same: 20 and 10 episodes. BENCH-R1 saw it live: steps 54-90 s in.

**What separates is the bidirectional burst.** 31 rules give 0 in **all four** cells, the clean windows and last
night, and fire in Sunday's burst minutes.

**So the rule's purpose is renamed: step down when the link is bidirectionally bad.**

## 3. What was built (`lan_r2.diff`)

**`PRIVYHUB_LAN_LOSS_RULE=bidir`:**
- `1` is LAN-R1's rule, byte for byte; absent is today;
- the condition: LAN-R1's two 10-s windows each hold **≥ 4 unrecoverable groups AND ≥ 2 uplink silences
  ≥ 400 ms**;
- from the passing set: T 4 K 2, the term in each window; Sunday at 05:06:13 in the analysis, every burst minute;
- an edge cell, in sample (`≥ 1 in each` fails; `≥ 500 ms` is later);
- everything else is LAN-R1's: one rung, floor 5000, every ladder gate, asks only on a quiet tick;
- **labelled `lan_bidir`**, with the uplink windows in its row.

**The code:**
- **`lan_loss_rule.py`:** `LanBidirRule` (a subclass: `windows()` appends the uplink count in step, and its asks are
  relabelled), `UplinkSilences` (a bounded, locked ring), `UPLINK`, and one guarded statement in `from_environ`.
  LAN-R1's code is not edited.
- **`native_session_io.py`:** one guarded statement notes each controller silence ≥ 250 ms at the packet that ends
  it. There is a class attribute and a setter.
- **`plugins/games.py`:**
  - a guarded block sets the ladder's own `LAN_LOSS_RULE` global for `bidir`. **`adaptive_bitrate_live.py` is
    untouched:** LAN-R1's test pins its one guarded import.
  - one guarded wire statement for the bridge.
- **The uplink count per evaluated report:** the silences ≥ 400 ms that **ended** since the previous evaluated
  report. The analysis attributed by start; the replay runs this code's own semantics.

## 4. The replay as LAN-R1's (`lan_r2_replay.py` → `replay_lan_r2.md` / `.json`, `replay_console.txt`)

**Through the real controller** (G5-S2's harness via LAN-R1's replay). The uplink sink is fed from the frozen gap
logs, and the rule's clock is each report's own time.

**Flag absent:**
- Sunday 41 sessions / 505 events and last night 12 / 318: **exact**, HEAD = tree, identical;
- BENCH-R1 cell 1 (the flag absent live): **exact**, identical (456 rows).
- Cells 2-4 ran with `=1` live, so their flag-absent replay rightly differs.
  - Through LAN-R1's rule, cell 2 reproduces except one row-order difference (`lan_loss_rule` vs `transition` at
    the same report).
  - **Cells 3-4 diverge from their first heavy-loss samples, before any ask.** That is the harness's sample-built
    telemetry under 5 % / burst loss. Disclosed: their rows below are a replay, not a reproduction.
  - The `bidir` condition (unrec + the gap log) does not depend on that divergence, and the analysis's own count
    for cells 3-4 is also 0.

**The false-trigger table (asks; must be 0):**

| span | `=1` (LAN-R1) | **`=bidir`** |
| --- | ---: | ---: |
| CL-B5 A / B / L, CL-B6 1 / 2, CL-B7 ×3, G4-S3 | 0 each | **0 each** |
| **BENCH-R1 cell 1 (`loss-1`)** | **9** (steps 7000→5000) | **0** |
| **BENCH-R1 cell 2 (`loss-1`)** | **6** (→5000) | **0** |
| last night | 2 (refused by the age guard) | **0** |
| *shown:* cell 3 (`loss-5`) / cell 4 (`burst-50x20`) | 15 / 15 | 0 / 0 |
| *shown:* G8-S1's loss cells (8) | 0-15 each | **0 in 7; 4 asks in `burst-50x20 off`** |

- **Sunday, `=bidir`:** first ask **05:06:09**. Steps: 05:06:09 7000→6000, 05:10:52 →5500, 05:20:52 7000→6000 (a new
  session). LAN-R1's first was 05:03:05.
- **G8-S1 `burst-50x20 off` (10-17 00:44-00:58Z), disclosed:** 4 asks, 2 steps (00:49:33, 00:52:44).
  - The room's uplink that quarter-hour was flapping: 93.7 silences ≥ 250 ms per 10 min, 61 ≥ 400 ms, the longest
    3.7 s, against 0.7-7.7 in the other G8 cells except `loss-5 on`'s 64.
  - So by its own definition the link was bad in both directions, though the downlink loss was the shim's. It is
    not in the queue's must-be-0 set, and it is reported.

**What a step buys:** a lower rate on a link bad in both directions. It does not prevent a drop (LAN-R1 / UX-R3). The
hold, the rewind and the stall handle drops. Whether 6000 helps Sunday's bursts is BENCH-R2's to see.

## 5. Tests and proof

- **`tests/lan_loss_rule_bidir`: 10 OK:**
  - the flag (`bidir` / `1` / others);
  - both terms fire, labelled `lan_bidir`, with the windows `[5, 4]` (the 9th bad report, as T 4);
  - unrec alone does not fire (LAN-R1 does, on the same reports); the uplink alone does not;
  - the boundaries: 399 ms never; one ≥ 400 per window not enough; two fire;
  - end-attribution and the ring's bound;
  - the real receive loop notes a 0.6-s silence through B1's gate;
  - a fresh process imports nothing and sets no sink;
  - the hook shapes (the ladder module untouched);
  - through the real `LiveController` and its actuator: `[6000]`, `transition lan_bidir`.
- **LAN-R1's `tests/lan_loss_rule`: 21 OK, unchanged.**
- **The regression set in the copy:** all OK (with B2-B7's suites); C3-F1's pre-existing error, and the golden
  fixture the copy lacks.
- **`proof_flag_absent.md`:** **3 modules identical** with LAN-R2's items removed.

## 6. For BENCH-R2 (session A)

- **The loss cells** (`loss-1@post-fec,seed=1`, `loss-5@post-fec,seed=1`, `burst-50x20@post-fec,seed=1`) with
  `PRIVYHUB_LAN_LOSS_RULE=bidir`: expected 0 `lan_bidir` steps unless the room's uplink flaps.
  - Read the `lan_loss_rule` rows' `uplink_windows`, and the control-gap log.
- **The `@both` blackout cells with `=bidir`:** each 4-s blackout is a single silence, ≥ 2 per window will not be
  met, so expect no step.
- **A user's evening on the LAN with `=bidir`:** steps only where both directions are bad.

## 7. Files

**`lan_r2_2026-10-22/`:**
- `baseline_head.txt`, `git_status_at_start.txt`, `predecessors/`, `predecessor_sha256.txt`, `after_sha256.txt`;
- `inputs/` (the frozen gap logs, `copied_at.txt`, `inputs_sha256.txt`);
- `lan_r2_analysis.py`, `per_minute.md`, `signals.json`, `rule_search.md` / `.json`;
- `lan_r2_extended.py`, `rule_search_extended.md` / `.json`;
- `design_written_before_code.md`, `design.sha256`, `design_hashed_at.txt`;
- `lan_r2.diff`;
- `proof_flag_absent.py` / `.md`;
- `lan_r2_replay.py`, `replay_lan_r2.md` / `.json`, `replay_console.txt`;
- `tests_lan_loss_rule_bidir.txt`, `tests_regression.txt`;
- `redact_check.py`, `redact_check.txt`, `manifest.sha256`.

**Elsewhere:** `companion/lan_loss_rule.py`, `companion/native_session_io.py`, `companion/plugins/games.py`,
`tests/lan_loss_rule_bidir/test_lan_loss_rule_bidir.py` (new); `patches/LAN_R2_LOSS_RULE_RETHOUGHT.md`;
`logs/lan_r2_git_status.txt`.

The rules held:
- no stream, no restart, no adb, no sudo, no nft;
- the Opal untouched;
- nothing fetched, nothing deleted;
- A's logs read only.
