---
memory_schema: 1
as_of: 2026-09-10
baseline_commit: 25e9a1492a684dbaeebede90ea7ca4abd3eab1fb
---

# Durable Learnings

## State and patching

Git history is not a substitute for the actual validated working tree. A previous A8 installer reconstructed expected bytes from Git and rejected the correct local state. Prefer exact local receipts/hashes when they exist.

A failed installer can still have side effects before a production write. Always distinguish project-file modification state from other runtime cleanup actions.

## Validation

Never equate “planned validation” with “validation passed.” A previous package hit a permission failure before synthetic compilation but was initially described as compiled; that must not recur.

Validate the exact generated output, not only the generator. Validate the exact command-construction path, not merely the intended command.

## PowerShell/Windows compatibility

The prototype uses a Windows PowerShell/.NET environment where newer APIs may not exist. `[System.IO.Path]::GetRelativePath` caused a real installer failure. Prefer compatible path logic. PowerShell syntax must be parsed before execution; multiline boolean formatting previously caused a parser failure.

Use absolute paths in installer/staging logic where relative .NET process working directories can diverge. A documentation-bootstrap command also demonstrated that a `finally` block cannot be pasted after its `try/catch` has already executed; user-facing PowerShell blocks must keep cleanup inside one syntactically complete construct or perform cleanup explicitly after the guarded command.

## Android UI

`AlertDialog` paths using both message content and selectable item lists repeatedly hid the list on the Android TV UI. Probes must test the actual reachability/failure condition, not merely source-string presence.

## Terminology

“A/B swap” is ambiguous. Say whether the operation is physical BUTTON A/B remapping, internal RetroPad A/B mapping, or Player 1/Player 2 assignment.

## Diagnostics

Know the lifecycle of each diagnostic artifact. A live status file and a final session-history file are not interchangeable. One A4 probe falsely failed because it required a final audio timing log before shutdown.

When a classifier contradicts raw measurements, investigate the raw measurements first.

## Scope control

Working subsystems should not be “improved” during unrelated fixes. This project has benefited most from contained probes, reversible patches, and stopping feature polish after runtime success.

## Negative results are results

Durable memory records what failed as well as what worked. A record that keeps
only successes teaches nothing and invites repeated attempts down paths already
known to be dead. Rejected candidates, rolled-back installers, wrong-state
rejections and probes that could not run are all results and are written down in
the same work that produced them.

State explicitly when a run was clean. An absent failure section must mean "none
occurred", never "none were recorded". The 2026-09-18 C1/C2 checkpoint recorded
a bare `PASS` with no measurements and no failure section, leaving the Linux
baseline outside the repository entirely; `C3.L0` had to reconstruct it.

## Compression must not destroy measurements

Memory maintenance that shortens active files must first verify the canonical
evidence record holds the detail. The 2026-09-18 checkpoint reduced `CURRENT.md`,
`roadmap/STATUS.md`, `investigations/ACTIVE.md`, the dated file and
`patches/PATCH_INDEX.md` to single-line assertions. `PATCH_INDEX.md` lost its
index of roughly seventy patch records that still existed on disk.

Prefer a generated index over a hand-transcribed one where the source of truth is
a directory. Transcription is the failure mode; generation plus validation is
not.

## Cross-platform evidence does not transfer by default

Windows-era C3 measured a 0.84-0.95 s RTP interruption for a video-only encoder
restart and rejected it for automatic adaptation. That figure is a property of
the Windows two-process topology (WGC bridge feeding FFmpeg over an inherited
pipe), not of the actuator strategy. Linux runs a single FFmpeg process with
x11grab as an input format.

Carry the *strategy* and the *capability model* across platforms. Re-measure the
*numbers*. A validated ladder from one backend is a hypothesis on another.

## Audit the client when auditing a stream parameter

Stream parameters can be owned jointly by host and client without any
negotiation between them. Resolution and FPS are FFmpeg arguments on the
companion *and* independent compile-time constants in the Android activity, with
the decoder ignoring `INFO_OUTPUT_FORMAT_CHANGED`. A host-only audit would have
classified them as restart-mutable; they are actually APK-mutable, and the two
sides can silently diverge.

Conversely, check whether a wire format is self-describing before assuming a
parameter is pinned. FEC group size looked like a fixed constant on both ends
but is carried per-group in the header and validated by the receiver.

## Inspect the repository's own validators before rewriting what they validate

`C3.L0` rewrote `docs/memory/CURRENT.md` wholesale without first reading
`tools/check_memory_health.py`, which requires seven exact section headings, each
present exactly once. The rewrite used different names and casing, so the
checker still reported `maintenance_required` after a patch whose stated purpose
included memory reconciliation.

The pre-existing 182-byte `CURRENT.md` had no headings at all and was already
failing the same check, so `C3.L0` did not introduce the regression. It
inherited it and failed to fix it, which is worse in one specific way: the patch
looked like it had addressed memory health.

The project instruction to inspect existing tools and probes before creating
anything new applies to validators too, not only to diagnostics. A validator in
the repository is a specification of the file it checks.

## A validation step that is only documented is not a gate

`MAINTENANCE.md` already listed running `tools/check_memory_health.py` as step 9
of the maintenance procedure. It was documented and still skipped, because
nothing enforced it and the installer's own validation did not include it.

Where a repository ships a checker for state a patch modifies, the installer
runs it and treats a reported problem as a post-write validation failure with
rollback. Documented intent does not survive; executed gates do.

## A counter baseline must be taken after the thing it measures has stopped

The `C3.L1` probe measured "time until video resumed" by watching the FEC relay
packet counter rise above a baseline. It took that baseline from a status
snapshot read during precondition checks, several milliseconds before the old
encoder was killed. At roughly 770 packets per second, those milliseconds were
enough for the old encoder to push the counter past the baseline on its own, so
the first poll after spawning the replacement succeeded instantly and reported
process spawn time as video resume time.

When measuring the resumption of a stream, take the baseline after the old
producer is dead and reaped, and report the residue so a reader can judge
whether the baseline was clean. Do not delay the restart to drain the queue:
that lengthens the very interruption being measured.

The tell was in the data. Spawn and resume were 0.010 ms apart while the poll
loop slept 10 ms between checks. Two timings that cannot legitimately be that
close are a defect signature, not a fast result.

## Prefer the measurement the component under test cannot influence

The `C3.L1` conclusion survived a defective host-side measurement only because
`decoder_max_output_gap_ms` is measured on the Android receiver, independently
of the host probe. The independent measurement was the one worth trusting, and
it was already being collected.

When a probe measures its own effect, look for a second measurement taken by
something that has no stake in the result, and prefer it for the conclusion.

## A regression test must be shown to fail against the defect

The first attempt at a regression guard for the baseline defect asserted that
the corrected probe slept at least once before reporting resume. It passed
against the defective probe too, because the sleep counter also counted the
post-resume stability window.

The test that actually discriminated was constructed from the failure's
meaning: a cycle where the replacement produces no video at all. A stale
baseline reports success for a dead stream; a correct baseline raises. Every
regression test is run against the unfixed code and shown to fail before it is
trusted.

## Check the premise of the strongest lead before authorizing work on it

`C3.L1R1` recorded "request an immediate IDR on the replacement encoder" as the
strongest lead for shrinking the 287-318 ms actuator gap, reasoning from
`max_resync_to_idr_ms` of 191-241 ms being approximately one GOP. The reasoning
was sound; the premise was not checked. A freshly launched FFmpeg RTP stream
already emits in-band parameter sets and an IDR access unit as its first output,
so there was nothing to request. The lead named a remedy for a cause nobody had
established.

A magnitude that matches a plausible mechanism is not evidence that the
mechanism is present. Before authorizing work on a lead, state the mechanism it
assumes and confirm that assumption against source or measurement. Otherwise the
first patch of the next work item changes something that was already doing what
the patch would ask of it.

## A whole-session maximum is not a per-event measurement

`max_resync_to_idr_ms` and `packets_dropped_waiting_for_idr` are cumulative
session figures. Both `C3.L1` sessions recorded two sequence resyncs against a
single SSRC change, so the session maximum may belong to the other resync
entirely. Attributing it to the actuator cycle is an inference, and it was
carried forward through three records as though it were a measurement.

Related: measurements taken from different origins do not sum. Spawn 115 ms, RTP
silence ~152 ms and decoder output gap 287 ms overlap in time; adding the resync
term to the silence term exceeds the gap they are supposed to explain, which is
the tell.

Check whether a reported figure is per-event or per-session before building an
explanation on it, and say which it is wherever it is cited.

## A bounded diagnostic buffer discards exactly the event you went looking for

The Android decoder session report keeps its slow-event rows in a 128-entry
ring. The `C3.L1R1` session produced more than 128 slow events after the
actuator cycle, so by the time the report was written the cycle's row was gone
and only the last 29 s of a 65 s session survived. The cumulative
`max_output_gap_ms` still named the event; nothing remained to explain it.

The probe was well designed, the run was clean, the evidence was collected, and
the answer was still unavailable. No amount of re-running the same probe would
have changed that.

Before running a diagnostic, check the retention of every buffer the answer will
come from, and confirm that the event of interest survives until the report is
written. A report that states its own retention — this one exposes
`slow_event_retained` and `slow_event_capacity` — is telling you whether to
trust an absence; read those fields first.

The same caution applies to log tails. The game diagnostic bundle carries the
last 500 lines of the native video host log, so a missing encoder restart banner
is not evidence that no restart occurred.

## Measure the baseline before attributing a cost to the change

`C3.L1` and `C3.L1R1` reported a 287-318 ms decoder output gap for the actuator
cycle and compared it against Windows. Nobody compared it against the same
session's ordinary gameplay, where output gaps of 238 ms and 200 ms occurred
with no actuator involved, caused by decoder time on a single frame.

An interruption figure means little without the distribution it sits in. Before
attributing a cost to an intervention, take the same measurement while the
intervention is not happening. The comparison that matters is usually against
the system's own baseline, not against another platform.

## A decision record is a source, not a summary

The project rule "prefer current local source and fresh measured evidence over
stale summaries" was applied rigorously to numbers and not at all to prose.

On 2026-09-19 a correction patch re-derived every figure it wrote from raw
decoder JSON — and wrote the phrase "`C3.L4` is BLOCKED; gate is a focused
gameplay acceptance" into six files without once opening
`decisions/C3-L2_LINUX_ACTUATOR_CLASSIFICATION.md`, the record that defines
that gate. Had it been opened, reason 3 was sitting there in plain text: the
gameplay observation had already been performed on 2026-09-18 and already
ruled insufficient. Instead the undefined phrase propagated, and the next
session proposed exactly the observation that had been rejected — costing a
round trip to discover something the repository already knew.

A summary is a pointer, not a citation. Before restating what a decision,
gate, classification or constraint says, open the record that defines it.
Copying a phrase from `CURRENT.md` into five more files does not make it
true five more times; it makes it harder to correct.

## When a result falsifies a premise, the decisions that rest on it are in scope

`C3.L2a` E2 falsified the 287-318 ms actuator cost. Its patch updated
`CURRENT.md`, `MEMORY.md`, `PHASE_C_CONTEXT.md`, the roadmap, the handoff, two
investigation files, the dated record and `KNOWN_ISSUES.md` — nine files — and
did not touch `decisions/`. The decision that had reasoned from the falsified
figure kept asserting it for a day, while every other file said it was wrong.

Evidence files record what was measured; decision files record what was
*concluded from* it. A result that invalidates an input invalidates the
conclusions built on that input, and those live in `decisions/`. When a patch
falsifies something, grep the memory tree for the figure or claim it kills and
put every file that cites it in the changed scope — including, especially, the
ones that are hard to change because they are load-bearing.

Strike the falsified reasoning in place rather than deleting it, mark the
current state authoritative, and say explicitly which of the remaining reasons
still carry the decision. A decision with one reason struck and three intact
is a different object from a decision that was never examined.

## Teardown is part of the test, and the client is part of the teardown

The first fully autonomous session on 2026-09-20 did everything the
instruction listed — BACK to post the report, `stop` the game, kill the
companion, verify no host process remained — and still left the onn showing
"NOW PLAYING … PAUSED". The host was clean; the client was not. The launcher
clears that banner only when its own END control runs or when an `onResume`
poll gets `active: false`, and the companion was already dead when the
launcher next asked.

"Leave the host as you found it" is half the rule. The client keeps its own
view of the session, and that view is updated by the companion answering,
not by the companion existing. End the game through the client, or make the
client re-poll while the companion is still up, and verify what the client
shows before the last process is stopped. A teardown checklist that only
lists host processes will pass while the user's screen is wrong.

## An instrumentation threshold is tuned to the fault it was built for

`AvcLowLatencyDecoder` records a slow event only when a frame's
receive-to-output latency reaches 50 ms. That was the right trigger for the
fault the corpus showed — a codec that held frames — because a long output
gap and a long latency were the same event.

`C3.L2c` removed the hold, and the trigger went blind precisely where it was
needed. On the low-latency build the worst output gap of a session ends with
a frame that arrived late but decoded fast, so it never qualifies: in two of
three sessions the buffer had spare capacity and the worst gap still had no
row, and `slow_event_retained_marked` was 0 in all three despite five
sequence resyncs — the `C3.L2b` cycle window protected nothing because
nothing qualified to protect.

The absence was readable only because the retention counters were in the
report: `recent 21/64` says "not overflowed", which turns "the event is
missing" from a retention question into a threshold one, and that is what
made the attribution possible at all.

When a change is expected to move where time is spent, check whether the
instrumentation's trigger still fires on the new shape before reading its
silence as good news. Record a counter alongside every bounded list so a
later reader can tell eviction from non-qualification.

## A rollback is a result that can itself be wrong

`C3.L2c` was rolled back on 2026-09-19 on one number — `max_output_gap_ms`
385 against a 359 ms baseline — while the same session showed a 20x
improvement in receive-to-output spikes. The rollback was recorded honestly,
with its measurement, as the negative-result policy requires. It was still
the wrong call: the 385 ms was an arrival gap and the 359 ms was a codec
hold, so the two numbers were never the same quantity, and re-running it
three times showed the improvement holds across the distribution.

The negative-result policy keeps failures from being lost. It does not make
them correct. A recorded rollback deserves the same scepticism as a recorded
success — especially a rollback decided by a single sample of a metric whose
meaning the change itself altered. Before citing "we tried that and it
failed", check what the deciding number measured on each side of the change.

## A background start hides the failure that matters most

`nohup python3 ./companion/privyhub_service.py &` looked identical whether it
started or not. On 2026-09-20 it did not start — an older companion still
held port 8765 — and the bind error went into a redirected log nobody read.
The old process answered every request, so the shell, the game launch, the
stream and the session report all behaved normally, and a validation session
ran to completion against code that predated the patch it was validating.

What caught it was the check itself: the new endpoint answered "Unknown
Games plugin POST action". A check that only confirmed the expected outcome
would have passed on the strength of the *old* code's behaviour.

The project already had the rule — D-068, restart the companion whenever
companion Python changes, stale-process behavior is not evidence. The rule
was followed and the restart still did not happen. So the rule needs its
verification attached: after starting a service in the background, confirm
the pid you started is the one serving, not merely that something answers.
"Started" and "running" are different claims, and `&` reports neither.

## Fix the stale assertion in both directions

`D-BASE-R2` piece 3 existed because the launcher kept saying "NOW PLAYING"
when it could no longer confirm a session. The first implementation replaced
that with a status line reading "Companion unreachable" — and nothing ever
cleared it. The companion came back, the poll succeeded, and the line went
on asserting the opposite of the truth for the rest of the session.

A notice about a lost dependency is itself a claim about the present. It
needs the same treatment as the claim it replaced: whatever sets it must
also retire it when the condition ends. Writing only the failure branch
swaps one stale assertion for another and feels like progress because the
original bug is gone.

## A substitute fault must reproduce the mechanism, not the symptom

`C5a` needed a sequence resync — 128+ consecutive RTP packets missing — and
the authorized substitute for the unavailable nftables injection was a
0.3 s SIGSTOP of the encoder. Three sessions produced zero resyncs, and the
reason is that the substitute cannot produce one *in principle*: a stopped
encoder emits nothing, so it burns no sequence numbers, and on SIGCONT the
sequence resumes contiguous. It makes a gap in **time**; the test needed a
gap in **sequence**.

The premise had propagated. `D-BASE-R3a` recorded 720/984/480-packet jumps
during SIGSTOP runs, and the next task cited them as evidence that the
pulses cause jumps. They did not: those jumps came from encoder *restarts*
the recovery fired during longer holds, which mint a new SSRC and a fresh
sequence base. A correlation inside one record became a causal claim in the
next, and a session's worth of runs was spent before the data contradicted
it — `max_forward_gap_packets` 47 against a 128 threshold.

Two habits would have caught it earlier. State the causal chain from the
injection to the metric before running, in one sentence, and check each
link: "SIGSTOP stops the encoder → the encoder sends no packets → ... → the
receiver sees a sequence jump" fails at the third arrow on inspection
alone. And run the positive control first: exercise the new counter through
*any* path that must trip it, so a zero result is known to mean "nothing
happened" rather than "nothing was measured". The C5a control session did
exactly that, and it was what separated a sound probe from a broken one.
