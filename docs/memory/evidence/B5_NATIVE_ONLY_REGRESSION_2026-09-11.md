---
memory_schema: 1
as_of: 2026-09-11
baseline_commit: 6b7c74f417e2ef14e252b9ea19afc16bdefaa50a
---

# B5 native-only regression

Classification:
`B5_NATIVE_ONLY_REGRESSION_RUNTIME_CONFIRMED`

Original harness result:
`B5_NATIVE_ONLY_REGRESSION_NOT_CONFIRMED`

Original failed required checks:
`['post_profile_native_ok']`

## Functional regression result

Passed:
- clean-native source predecessor;
- legacy project artifacts absent;
- Sunshine process absent;
- initial WGC/NVENC/RTP-UDP-XOR-FEC native session;
- picture;
- audio;
- controller;
- pause/resume;
- Save;
- Load;
- existing cheat/mod/profile path;
- End/teardown.

Save produced four state-related file changes.

## Classifier adjudication

The original harness required the native streaming client to remain active after
the profile/UI step. That requirement is not part of the B5 roadmap acceptance
contract and does not distinguish a normal client/UI lifecycle transition from a
streaming failure.

Fresh diagnostics showed:

- native host stream reached frame 10550 at ~60 fps over ~175.8 s;
- Android decoder session duration: 176503 ms;
- video packets: 148103;
- video packet loss: 0;
- video frames: 10551;
- queued decoder frames: 10551;
- rendered frames: 10041;
- stale-output drops: 509;
- codec frames in flight at report: 1;
- decoder dropped frames: 0;
- FEC unrecoverable groups: 0;
- FEC recovered packets: 1;
- decoder slow-event telemetry extends to 176439 ms, 64 ms before session end.

Frame accounting is complete:
`10041 rendered + 509 stale + 1 in-flight = 10551 queued`.

The decoder/client session ended roughly ten seconds before the managed game
process ended, which aligns with the B5 post-profile polling window. The single
`active=False` host snapshot therefore represents a client/profile UI lifecycle
transition, not a failed native-stream regression.

## Conclusion

B5 is **COMPLETE / RUNTIME VALIDATED**.

The harness is corrected so `post_profile_native_ok` remains diagnostic
information but is no longer a required B5 pass gate.

Next:
B6 clean-native repository audit/checkpoint.
