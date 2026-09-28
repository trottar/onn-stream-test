---
memory_schema: 1
as_of: 2026-09-24
status: TASK HANDOFF — D6-R1: replay the preserved synthetic UDP transport suite (forward and reverse) on the representative post-B2 path — host wired to the Opal, onn on its 5 GHz — and classify the Windows-era burst/gap/duplication pathology per the roadmap's D6; runtime, no code change, Opal read-only; authorized by the user 2026-09-24 for the weekend queue
---

# D6-R1 — replay the deferred UDP suite on the production path

**Why.** `docs/ROADMAP.md` D6 and D8 require the saved forward/reverse
transport acceptance suite rerun on the representative Linux + home Opal
+ onn path and the old pathology classified (specific to the old
environment / reproduced on the representative path / broader). Every
run of the suite so far was on the pre-`B2` topology through the Windows
PC (`investigations/DEFERRED.md`: "Linux + home Opal + onn UDP transport
root cause — PAUSED"; `M1` paused it; `CURRENT.md`: "never seen post-B2").
`B2` (2026-09-21) moved the host onto the Opal. The replay has not been
done since. It is the one D8 acceptance item that is pure measurement.

Read first: `investigations/DEFERRED.md` (the paused entry and its
reopen conditions — condition 2 is met: the suite can now run on a
different path), `evidence/D_LINUX_UDP_EGRESS_2026-09-15.md`,
`evidence/D_LINUX_ONN_STREAM_DIAGNOSIS_2026-09-15.md`,
`decisions/D083_NETDEV_DIAGNOSTIC_CLOSEOUT_2026-09-15.md`,
`evidence/B2_HOST_ON_OPAL_2026-09-21.md` (the gate checks that prove the
topology), `companion/diagnostics/udp_transport_probe.py` and
`udp_reverse_transport_probe.py` (the suite as preserved; how each is
started, what the client side needs, what they classify), `TOOLS.md`.

**Scope.** Runtime only, with the probes as preserved — **no code
change** to them (if one cannot run as-is on this path, record why and
run the other). No companion, client or profile change; the Opal is
read-only (`ssh opal` reads only, as `O1`/`T2` did). No game session
during the suite (the suite is idle-path by design; run it with the
stream inactive, then once more beside a plain 20-minute hold if the
preserved suite has a with-load arm — and only then). Never overlap with
another task's session.

## Do

1. **Gate the topology** exactly as `B2` did (default route interface,
   gateway identified by the same banners, host and onn on one subnet,
   adb reachable) and record the result without any address.
2. **Run the suite** as preserved, forward (host → onn) and reverse
   (onn → host), the same parameters and durations as the last valid
   pre-`B2` run (`D082` per `DEFERRED.md`); the same outputs it wrote
   then, into `evidence/d6_r1_<date>/`. Repeat each direction **three
   times** spaced ≥ 5 minutes apart (the old pathology was intermittent).
3. **Classify, pre-registered:** for each direction, the suite's own
   metrics (burst/gap transformation, same-stamp duplication, reorder,
   loss) beside the last pre-`B2` values. **NOT REPRODUCED** if none of
   the three runs shows the pathology's signature above the suite's own
   noise floor (state that floor from the suite's clean-run definition or
   from its own control arm); **REPRODUCED** if ≥ 2 of 3 runs show it in
   a direction; **INDETERMINATE** if 1 of 3 or the suite could not run
   as preserved. Then the roadmap's three-way classification follows:
   NOT REPRODUCED → "specific to the old environment"; REPRODUCED →
   "reproduced on the representative path" (and `DEFERRED.md`'s pause
   stays, with the reopen condition met and the new evidence attached);
   broader-transport claims are made only if both directions reproduce.
4. **Beside it, the in-session view** already on disk: the close-out
   and `S1` hold sessions show 0 resyncs and 5-9 lost/min post-FEC with
   no duplication counter raised — cite those rows as the with-load
   reference; do not rerun them.

## Record and memory

`evidence/D6_R1_UDP_SUITE_REPLAY_<date>.md` (topology gate, six runs, the
classification with numbers, what remains), evidence dir with the suite's
raw outputs and a manifest; `investigations/DEFERRED.md` (the paused
entry: reopened for this replay, outcome, and whether it stays paused);
`docs/ROADMAP.md` D6 line and D8 acceptance row; `docs/PROJECT_STATUS.md`;
`docs/KNOWN_ISSUES.md` if reproduced; `CURRENT.md` one line;
`investigations/ACTIVE.md`; the daily file. No addresses, MACs, SSIDs or
device identifiers in any file (the suite's raw outputs are redacted
before they are copied; `h2_prep_redact.py --check`). Nothing committed.
