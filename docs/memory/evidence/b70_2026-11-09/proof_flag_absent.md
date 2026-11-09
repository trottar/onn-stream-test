# B70 — the off switches give today's behaviour, hunk by hunk (`b70.diff`)

**Host.** B70's host change is **default on**, as the queue specifies: the stream no longer draws the hub's X pointer.
**`PRIVYHUB_CAPTURE_POINTER=1` = today's argv, byte for byte.** That is proven by `tests/b70_capture_pointer`
`test_one_keeps_today_byte_for_byte`: the full argv equals C5-M1's pinned golden string. M1 / M2 are caught.

**Client.** Also default on. **`debug.privyhub.pointer_hide=0` = today:** `PointerGuard(false)` consumes nothing, sets
no icon and asks no capture (`B70PointerTest.offIsToday`; M2 caught).

| file | hunk | with the off switch |
| --- | --- | --- |
| `companion/native_stream.py` | `CAPTURE_POINTER_ENV`, `_capture_pointer_args()` | `=1` → `[]` |
| | `*_capture_pointer_args()` in the Linux builder's input options | an empty splat: the argv is today's |
| `PrivyHub/.../PointerGuard.kt` | new | every method returns false / does nothing when `enabled` is false |
| `PrivyHub/.../NativeStreamActivity.kt` | `import android.view.PointerIcon` | an import |
| | `pointerGuard`, `pointerRoot`, `pointerHost` fields | `pointerRoot` set; the host is never called when off |
| | after `setContentView`: `pointerRoot = root`, `pointerGuard.onAttach(pointerHost)` | `onAttach` does nothing when off |
| | `onWindowFocusChanged`: `pointerGuard.onFocus(...)` | nothing when off |
| | `dispatchKeyEvent` / `dispatchGenericMotionEvent`: the guard's check first | false when off → today's method body |
| | `dispatchTouchEvent` / `dispatchTrackballEvent` overrides (new) | false when off → `super`, which is what the activity did with no override |
| `tests/b70_capture_pointer/`, `B70PointerTest.kt` | new | the suites |
| `tools/test_c5_m1_profile_selector.py`, `tools/test_adaptive_bitrate_live.py` | the pinned pre-B70 argv compared under `PRIVYHUB_CAPTURE_POINTER=1` | **disclosed:** these two suites pin today's exact argv. They now read it through the knob that keeps it; B70's own suite reads the default |

**Disclosed (found after the first diff):**
- `tools/test_adaptive_bitrate_live.py` pins a golden argv file that exists only in the tree (`docs/memory/evidence/`).
  So in the build copies this test errors as in the baseline copy. In the tree it failed on `-draw_mouse 0` until the
  fix above.
- Every host suite was then run on two full exports of HEAD, one plain and one with B70-B72
  (`b72_2026-11-09/tests_host_full_export_*.txt`).

**What changes for every session at the companion's next restart (no drop-in):** the hub's pointer is no longer in the
picture. No other argument moves. The level-sized rung and the encoder-rate path carry the same option, because all of
them use the one builder.
