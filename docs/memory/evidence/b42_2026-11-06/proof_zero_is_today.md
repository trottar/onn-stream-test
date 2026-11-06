# B42 — `0` / `off` = the CONFIRMED build's absent: PROVEN

- `proof_zero_is_today_output.txt` (from `proof_zero_is_today.py predecessors <copy>/…/streaming`): every changed line
  of `SurfaceHold.kt` (11) and `PadSlots.kt` (5) lies inside `object SurfaceHoldFlag` / `object PadSlotsFlag` or is one
  comment line of the header above it; 0 elsewhere. `NativeStreamActivity.kt` is byte-equal to the base.
- The consumers are the activity's two lazies (listed in the output). Each builds its object only from a non-null bound /
  `true`.
- `HoldAndSlotsDefaultOnTest.theOffWordsGiveTodaysAbsent` carries `0132b944…`'s two parses verbatim: for `0` and `off`
  the new parses return what the old returned for absent (null / false). So with `0` / `off` there is no `SurfaceHold` and
  no `PadSlots`: today's paths, byte for byte.
- Every value the old parses turned on (`1`, 10000-30000, `stable`) gives the same value.
