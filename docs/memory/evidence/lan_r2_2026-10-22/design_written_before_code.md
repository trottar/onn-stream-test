# LAN-R2 — the loss rule rethought on the four real cells: design (hashed before any LAN-R2 code)

Queue `handoffs/QUEUE_2026-10-22C.md` item LAN-R2, session B. Predecessors:
- `lan_loss_rule.py` (HEAD, LAN-R1's);
- `native_session_io.py` and `plugins/games.py` (B7 / B1b in the tree).

**The data came first:** `lan_r2_analysis.py` → `per_minute.md`, `rule_search.md`, `signals.json`; then
`lan_r2_extended.py` → `rule_search_extended.md`, declared after the first search found nothing.

## 1. What the data says

**Per minute** (`per_minute.md`):
- the uplink silences ≥ 250 ms, from the host's control-gap log (frozen copies in `inputs/`);
- the client's output gap;
- the client's audio arrival gap;
- the FEC-unrecoverable groups and their clustering.

These are shown across BENCH-R1 cells 1-4, Sunday's step and burst minutes, Sunday's and last night's clean minutes,
and the eight CL windows + G4-S3.
- **Random downlink loss on the bench also brings audio arrival gaps and unrec clusters,** comparable to Sunday's
  pre-burst step: cells 1-4 audio-gap medians 115-223 ms; Sunday's step 187; the clean minutes 122-128.
- **The client's output gap** separates nothing in the step minutes (median 68 ms).
- **The uplink silences:**
  - the clean CL windows: 0.3-7.9 per minute;
  - Sunday's step: 3.8;
  - its bursts: 23.8;
  - cells 3-4: 3.9-6.2. The bench's random downlink loss raises the uplink's own silences, so the uplink is not a
    pure "other direction" signal.

**The search** (base: LAN-R1's T 4 K 2 on unrec, AND one second term; must give 0 in cells 1-2, the clean windows
and last night's clean minutes, and fire on Sunday before 05:06): **no pair passes, in 34 + 96 tried.**
- The closest is `uplink ≥ 250 ms ×3 in a window`: cell 2 has 1 episode and Sunday fires at 05:03:05. One step
  stricter, Sunday's first firing moves to 05:06.
- **So, stated: on the data on file, Sunday's pre-burst loss (04:56-05:05) cannot be told from 1 % random loss by any
  host signal.**
- LAN-R1's 05:03 step was the unrecoverable groups alone, and they fire on cells 1-2 just the same: 20 and 10
  episodes on these reports.

**What does separate: the bidirectional burst.** 31 rules give **0 in all four cells**, the clean windows and last
night, and fire in Sunday's burst minutes.

## 2. The rule, renamed to its purpose: step down when the link is bidirectionally bad

**`PRIVYHUB_LAN_LOSS_RULE=bidir`** (a new value of LAN-R1's flag):
- `1` = LAN-R1's rule byte for byte (its 21 tests unchanged);
- absent = today;
- anything else = off.

**The source / reason label: `lan_bidir`.**

**The condition, on each evaluated report:** LAN-R1's windows (K 2 non-overlapping 5-evaluated-report windows, session
age ≥ 60 s):
- each holds **≥ 4 unrecoverable groups**, LAN-R1's T, AND
- each holds **≥ 2 uplink silences ≥ 400 ms**.

- **Chosen** from the passing set (`rule_search_extended.md`, T 4 K 2, `uplink ≥ 400 ms, ≥ 2 in EACH window`):
  - Sunday first at **05:06:13**, firing in every burst minute (05:06, 05:10, 05:20, 05:21);
  - LAN-R1's base kept;
  - the term per window, as LAN-R1's.
- **An edge cell, in sample:** `≥ 1 in each` fails, and `≥ 500 ms` fires later (05:06:55; 05:06 and 05:21 only).
  The live test is the out-of-sample check.

**Everything else is LAN-R1's:**
- one rung (`capacity_mild`'s target), floor 5000;
- every gate of the ladder (the hold-downs, the blackout, the 60-s age, the guards, the rate limit);
- asks only on a tick with no decision and nothing pending;
- windows cleared at a session reset, a blackout re-arm, after each ask;
- one `lan_loss_rule` row per ask, with `source: lan_bidir`, the unrec windows and the uplink windows.

**What a step buys, said as LAN-R1 / UX-R3 did:** a lower rate on a link that is bad in both directions. It does not
prevent a drop. Whether it helps Sunday's bursts is BENCH-R2's question; the hold / rewind / stall handle the drops.

## 3. The uplink term, live

- **The receive loop:** one guarded statement where a packet arrives after a silence ≥ 250 ms (the previous
  `_last_any_packet_at`): `self._uplink_silences.note(start, end)`. A class attribute `_uplink_silences = None` and a
  setter. **Absent = today.**
- **`lan_loss_rule.UplinkSilences`:** a bounded ring of (start, end) on the monotonic clock.
- **The rule's count per evaluated report:** silences ≥ 400 ms that **ended** since the previous evaluated report.
  - A silence is known only at its end. The analysis attributed by start (± one 2-s report). **The replay drives this
    code's own semantics**, so its table is the code's.
- **Wiring:** `plugins/games.py`, one guarded statement. With `PRIVYHUB_LAN_LOSS_RULE=bidir`, the controller bridge
  gets `lan_loss_rule.UPLINK`. The rule built by `from_environ` reads the same object.

## 4. Proof and tests

- **The replay as LAN-R1's** (G5-S2's harness through the real controller, with the uplink sink fed from the frozen gap
  logs on the sample clock):
  - **flag absent and `=1`:** exact / identical, as LAN-R1's;
  - **`=bidir`:** asks and taken steps per span; the **false-trigger table with cells 1-4 added**, the clean windows,
    last night; Sunday's first step.
- **Tests (`tests/lan_loss_rule_bidir/`):**
  - the flag table;
  - the condition (both terms, each window, the ≥ 400 ms / ≥ 2 boundary);
  - end-attribution;
  - the ring's bound;
  - the receive loop notes a silence ≥ 250 ms (the real loop, B1's helper);
  - absent: nothing imported, nothing noted;
  - `=1`: LAN-R1's behaviour, its suite unchanged.
- The AST proof per changed module.
