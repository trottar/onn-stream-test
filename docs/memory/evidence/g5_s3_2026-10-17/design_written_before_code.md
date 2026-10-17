# G5-S3 — the remote ladder: the design (written before the code)

Baseline `1dab25d`. Session B, unattended. Task:
`handoffs/G5-S3_REMOTE_LADDER_TASK.md`. Read before writing: the G5-S2 record
§1 (findings 1 and 2), `docs/WAN_ADAPTATION_RULES.md` R3.2 / R5,
`companion/adaptive_bitrate_live.py` (`LiveController._ctx`, `LivePolicy._decide`,
`_write`), `companion/diagnostics/c3_linux_actuator_probe.py`
(`LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS`, `_run_c3_linux_bitrate_cycle`),
`companion/native_stream.py` (`adaptive_level_transition`,
`recovery_restart_encoder`), `companion/plugins/games.py` (`native-stream-start`,
the ladder's bind), `companion/session_identity.py` (read only: `RoutingClassifier`,
`client_target`), C5-M3 (720p/4000: transport screened only).

## 0. What the code says before the design (a correction to the handoff, disclosed)

The handoff says "at session setup the games plugin already has G3's
`routing_evidence`". It does not, as a field. What it has is the `client_ip`
argument of `native-stream-start`. With identity v2 on, that is
`SESSION_IDENTITY.client_target(handler)`: the gate's declared media target
**whose class matches the request's routing class** (G3-S3: an overlay source
gets the signed `overlay_host`, a LAN source the signed `media_host`; a mismatch
is refused `endpoint-class-mismatch`). Without identity it is the request's source.

G3's `routing_evidence` for a request is `RoutingClassifier.classify(source)`:
`overlay` iff the address is in G3's `OVERLAY_NETWORKS`. So the class of the
target the plugin is handed, under G3's own overlay test, **is** the stream-start
request's routing evidence (overlay vs not), by G3-S3's class-match rule. That is
what this design uses. It is not a heuristic on the address: it is G3's test over
the endpoint G3 chose for that routing class. The networks are built from
integers as G3-S1 / G5-S2 do (no literal), and a test asserts they equal G3's.
No address is stored, logged or recorded — only the class.

The alternative (carry `routing_evidence` from the gate to the plugin as a field)
needs `session_identity.py` or the service's dispatch — not this session's files.
Listed for the user, not done.

## 1. The flag and the module

- **`PRIVYHUB_REMOTE_LADDER=1`** (exactly `1`; anything else = absent). Absent =
  today, byte for byte: no new import, no context key, no row field, the
  actuator's validated list unchanged.
- **New module `companion/remote_ladder.py`** (pure apart from a lock): one shared
  `RemoteLadder` per process (`shared_from_environ`), holding the session's
  `routing_evidence` (`overlay` / `lan`) and `path_class` (`remote` / `lan`; the
  default `lan`, G5-S2's default).
  - `note_stream_start(target)` — the class of the target (§0); set at every
    `native-stream-start`, so a re-setup updates it; never from anything else.
  - `apply(policy, ctx)` — `ctx["path_class"]`; the policy's ladder:
    `(4000,) + base` on `remote`, `base` otherwise (`base` = the policy's own:
    5000-7000, or with C5-M5's rung).
  - `actuator_levels()` — `(4000,)` on `remote`, `()` otherwise.
  - `annotate(row)` — `path_class` on every ladder-log row; on a row that moves
    to or from 4000, `remote_rung: true`; on the actuation's result row
    (`transition_done` / `transition_aborted` / `actuator_failed`), the decision's
    `reason`, `trigger` and `wan_rule` copied from its `transition` row (by
    `decision_sequence`), so each 4000 actuation is one readable pair: the
    decision with its rule or trigger, and the result.
  - `floor_actuates(suggestion, policy)` — True for G5-S2's `floor_4000` when the
    policy's ladder holds 4000 (= flag on and remote).

## 2. The hooks (each a guarded `if`, a patch)

1. **`adaptive_bitrate_live.py`**
   - a module global `REMOTE_LADDER`, built only under the flag (the import inside
     the `if`), as G5-S2's `WAN_ADAPTATION`;
   - **the context builder** `LiveController._ctx`: `if REMOTE_LADDER is not None:
     REMOTE_LADDER.apply(self._policy, ctx)` (the dict built as today, then
     returned);
   - **`LiveController._write`**: `if REMOTE_LADDER is not None: base =
     REMOTE_LADDER.annotate(base)`.
   `LivePolicy` is not edited: the 4000 rung is reached by the policy's own code
   because its `ladder` holds it (`capacity_mild`'s "one rung down" from 5000 is
   4000; an increase from 4000 is 5000; at 4000 every step down is `at_floor`).
   `TARGET_KBPS` is unchanged: a strict FALLBACK still names 5000 (at 5000 on a
   remote path it is `at_floor`, as today).
2. **`plugins/games.py`** — at `native-stream-start`, after the stream started:
   `if adaptive_bitrate_live.REMOTE_LADDER is not None:
   adaptive_bitrate_live.REMOTE_LADDER.note_stream_start(client_ip)`. The ladder's
   context builder reads it: that is "the games plugin passes the routing evidence
   into the ladder's context as `path_class`". The plugin's context function and
   the actuator binding are not edited.
3. **`diagnostics/c3_linux_actuator_probe.py`** — a module global `REMOTE_LADDER`
   (import inside the flag's `if`); in `_run_c3_linux_bitrate_cycle` the validated
   list is a local, `LINUX_VALIDATED_ADAPTIVE_BITRATES_KBPS`, extended by one
   `if REMOTE_LADDER is not None:` with `actuator_levels()`. So 4000 is accepted
   by the validated transition (the same path and argv builder 5000 uses: only
   `-b:v / -maxrate / -bufsize` change) and by recovery's same-level restart
   (C3-F1), **only on a remote path with the flag**. Below 4000 nothing is ever
   accepted (3000 stays refused everywhere); on the LAN 4000 is refused
   `unsupported_validated_bitrate` as today. `native_stream.py` is not edited:
   `adaptive_level_transition(4000)` already routes a 720p target to the
   validated transition.
4. **`wan_adaptation.py`** (G5-S2's module; B's) — a module global `REMOTE_LADDER`
   under the flag; in `WanAdaptation.feed`, the forced decrease that today runs
   for `step_down` also runs for `floor_4000` when `REMOTE_LADDER.floor_actuates`.
   It goes through the ladder's own `_decide` (ROUTINE, one rung down = 4000), so
   every gate applies; labelled `wan_rules`, `wan_rule: R3.2`. Without the flag,
   `floor_4000` stays recorded only, as today.

## 3. Recorded

- With the flag, every ladder-log row (and so every row of a run's
  `decisions.jsonl`) carries `path_class`; a change of class is visible as the
  first row with the new value.
- Every decision to 4000 (`transition`, or `refused` with `to_kbps` 4000) and every
  actuation result for it carries `remote_rung: true`, `path_class`, the reason /
  trigger / `wan_rule`, and (result rows) the outcome.

## 4. Not in this task

The rungs' encoder parameters (4000 uses the existing bitrate control as 5000
does); R5's strictness; a cap (G5-S4); a relayed-path cap (R1.3); FEC (R4); the
gate → plugin routing field (§0); any live run.

## 5. The proof (no stream)

- **Unit tests** `tests/remote_ladder/`: the flag (exactly `1`); the class from
  G3's overlay test (equal to G3's networks; a LAN-class and an unparsable target
  read `lan`); the context with and without the flag; the policy's ladder by flag ×
  class; the real `LivePolicy` stepping 5000 → 4000 by `capacity_mild` on remote,
  never on the LAN, `at_floor` at 4000, 4000 → 5000 by the increase rule; the
  actuator (C3-F1's fake manager, the real cycle): 4000 accepted on remote (the
  transition, recovery at 4000, back to 5000), refused on the LAN and without the
  flag, 3000 refused everywhere; `floor_4000` actuated only with the flag and on
  remote; the rows annotated; the guarded imports (AST).
- **Flag absent, byte for byte:** (a) the ladder: HEAD's and the edited
  `LiveController` driven in process over G5-S2's four runs — identical rows; (b)
  the actuator: HEAD's and the edited probe over every (mode × current × target)
  incl. 3000 / 4000 / 12600 with the fake manager — identical results, argvs and
  exceptions; (c) the games plugin: HEAD's and the edited `handle_post_request
  ("native-stream-start")` with the same stubs — identical payloads and stub
  calls; (d) G5-S2's own `replay.py` re-run, unchanged: the four runs' recorded
  decisions exact.
- **Flag present, replay** (`replay.py` here; the controller in process, a
  synchronous actuator, the stream at the level the policy chose): G5-S2's four
  runs (as recorded: `lan`; and read as remote, hypothetical) and G4-S1's run 1
  and run 2 (`path_class` from the session's setup per G4-S1 §2/§4: run 1
  `remote`; run 2 `remote` to the hotspot toggle, `lan` after the LAN setup), each
  with G5-S2's rules off and on: whether and when 4000 is reached, by which rule
  or trigger, and how long it stays under R5. Tabulated; **no claim** that any run
  would have played better.
- The G1 / G3 / G5-S1 / G5-S2 suites, the ladder's own tests, C3-F1's; the
  redactor over every new or edited file.
