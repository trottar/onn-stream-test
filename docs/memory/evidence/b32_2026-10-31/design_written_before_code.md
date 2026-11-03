# B32 (client) — the stream survives a brief loss of the screen; every foreground loss logged; pad system keys kept — design, written before code

Queue: `handoffs/QUEUE_2026-10-31L.md` §B32 (client half). Facts: `evidence/TRIP_R2_FRIDAY_GAMEPLAY_2026-10-31.md` §1.
Baseline HEAD `1904fe8`. Flag: `debug.privyhub.surface_hold` (CL-B7P's convention, read once per activity through
reflection like `restart_guard`). **Absent / empty / `0` / junk = today: no object, no listener, no key, no row.**

## 0. Settled from the code (what took the foreground, and what the client can say about it)

- **Today the client logs nothing about it.** `onPause` stores one time (`RestartGuard.notePause`, B11), so a
  restart's report says `paused_before_loss_ms` and `away_ms`, nothing else. No key, no focus, no device event is kept.
- **Android gives no "pause reason".** What the activity can observe, and will log under the flag:
  - `onWindowFocusChanged(false)`: another window took input focus (a system panel, the TV side panel, a dialog,
    the notification shade) — the activity may stay visible and resumed;
  - `onTopResumedActivityChanged(false)` (API 29+; the override is inert below): another activity became the
    top resumed one (a launcher, an assistant, a settings panel activity);
  - `onUserLeaveHint()`: the leave was the user's own navigation (Home, or a launch from a notification); a system
    panel or an activity started by something else does not call it;
  - `onPause` / `onStop` / `surfaceDestroyed` with their times; `PowerManager.isInteractive` at the loss (screen off,
    HDMI-CEC standby);
  - `InputManager.InputDeviceListener`: a device added / removed / changed (a Bluetooth pad dropping and
    reconnecting, a second pad joining) with its source class only (pad / remote / other), never a name or id;
  - keys at `dispatchKeyEvent` with their key code and source class. **What can never be seen there:** the keys the
    window-manager policy intercepts before dispatch (`KEYCODE_HOME`, `KEYCODE_APP_SWITCH`, `KEYCODE_POWER`, and on
    most builds `KEYCODE_ASSIST` / `KEYCODE_ALL_APPS` / `KEYCODE_NOTIFICATION`). A pad's Home that the platform
    maps to `KEYCODE_HOME` therefore shows only as `user_leave` with no key; a pad's guide button that maps to
    `KEYCODE_BUTTON_MODE` (most pads' "PS" / "Xbox" / "Home" button under the generic key layout) does reach the
    activity — today it is not mapped by the sender (`NativeControllerSender.handleKeyEvent` returns false) and goes
    to `super.dispatchKeyEvent`, i.e. to the system's default handling.
- **Which of the six it was cannot be settled from the code** (the record has no such row; the onn's event log needs
  adb). Inference only: `paused_before_loss_ms` 0.8-4.5 s before the surface went is a pause then a stop, which is
  what an activity coming on top (a panel activity or the launcher) does; a Home press stops within ~0.5 s. The rows
  below settle it at the next loss.
- **The restart path itself** (B15/B17/B24): `surfaceDestroyed` → `stopLocalPipeline()` (sender, audio, receiver,
  decoder) → the next `surfaceCreated` → `startSession` → `native-stream-start&guard_end=1` → the host ends the old
  session (`session_ended`) and starts a new one at the start rung.

## 1. The hold (`SurfaceHold.kt`, new; the activity calls it)

- **Bound: 12,000 ms** (`debug.privyhub.surface_hold=1`; an integer 10000-30000 = that bound; anything else = off).
  The five restarts with a report were away (surface lost → surface back) 1,039 / 1,188 / 1,787 / 2,027 / 8,582 ms;
  the sixth (05:19:35) has no report, so no bound can be proven to cover it. 10 s covers the five with 1.4 s over
  the kart's 8.6 s; **12 s** is chosen for margin (3.4 s) and still sits below the 15-s test case. The hold counts
  from `surfaceDestroyed`, not from the pause (the activity keeps its surface while only paused, and the pipeline
  runs then today too).
- **`surfaceDestroyed`, a session started, the activity not finishing, the flag on:**
  1. the session report is cached (the decoder's counters while it still exists — today's same call);
  2. the controller sender's state is set neutral (no button held, sticks centred) and it **keeps sending**; the
     audio receiver and the RTP receiver **keep running**;
  3. **the decoder is closed and set null** (its `close()` joins the codec's thread, so the codec lets go of the
     surface before `surfaceDestroyed` returns — a codec left rendering into a destroyed surface errors). The
     decoder cannot be kept: `MediaCodec.setOutputSurface` needs a live target, and there is none until
     `surfaceCreated`. Access units arriving with no decoder are dropped by today's `decoder?.queueAccessUnit`;
  4. the receiver's parameter-set callback, with the flag, builds a decoder only on a live surface (none now);
  5. a one-shot expiry is posted at the bound;
  6. `sessionStarted` stays true; no `RestartGuard.onSurfaceLost`, no pending.
- **During the hold** the stall signal (B7, on by default) is fed the output age as `age at the loss + time since
  the loss` (the decoder is gone, so its own age is -1, which the monitor reads as "no frame yet" and would end a
  stall). So from ~150 ms the host's stall path pauses the game (and takes its scratch save) exactly as it does at a
  link stall today — the game does not run unseen. No heartbeat goes while no decoder exists (today's early return);
  the uplink keeps flowing, so the host sees no silence and no `input_hold`.
- **`surfaceCreated` within the bound:** the expiry is cancelled; the new surface is recorded; **no `startSession`,
  no `native-stream-start`, no `guard_end`, no `session_ended`, no rung reset.** The next in-band SPS/PPS (every IDR:
  the host's GOP is 15 frames, ≤ 250 ms) builds a new decoder on the new surface; the stall signal's synthetic age
  runs until that decoder renders its first frame, then the real age ends the stall (`stall_end`) and the host
  releases as it does after a link stall. No keyframe request is needed (the next IDR is ≤ 250 ms away; B10's
  finding: the host has no runtime IDR anyway).
- **Past the bound** (the expiry runs with no surface): today's path, deferred — `RestartGuard.onSurfaceLost` with
  the report cached at the loss, `stopLocalPipeline()`, `sessionStarted = false`. The next `surfaceCreated` is
  today's restart (`trigger: surface`, `guard_end=1`). `away_ms` in that restart's cause counts from the expiry; the
  `surface_lost` row carries the true away time.
- **The activity finishing during the hold** (`onDestroy`): the expiry is cancelled, and today's `stopSession`
  runs (the session is still started, so its report and `native-stream-stop` are posted as at any exit). A
  recreation during the hold is today's B15 hand-over (`sessionLive` true).
- **Report:** `surface_hold` object — `bound_ms`, `losses`, `held`, `restarted`, `ended_in_hold`,
  `decoders_built`, `rendered_before_reattach` (the closed decoders' rendered frames: a held session's decoder
  counters restart at the re-attach; this keeps the total readable), `pad_system_keys_consumed`,
  `system_keys_passed`, `rows_queued`, `rows_sent`.

## 2. The `surface_lost` row

One per loss, queued when its outcome is known (`held` at the re-attach, `restarted` at the expiry), at most 8
queued (older dropped, counted), **one per heartbeat** as `&surface_lost=<url-encoded compact JSON>` (the heartbeat
needs a decoder, so a held row goes on the first heartbeat after the picture is back; a restarted row on the new
session's first heartbeat). Fields (numbers, booleans, fixed words; no text from the system, no device name or id):
`seq`, `outcome` (`held` / `restarted`), `reason` (below), `bound_ms`, `away_ms` (surface lost → back, or → expiry),
`paused_before_ms` (pause → loss, -1 none), `focus_lost_before_ms`, `top_lost_before_ms`, `user_leave` (bool),
`interactive` (bool / null), `keys` (≤ 8, the 2 s before the loss: `"<keycode>:<pad|remote|other>:<c|p>"`, c =
consumed, p = passed on), `devices` (≤ 4, the 2 s before: `"<added|removed|changed>:<class>:<ms before>"`),
`first_frame_ms` (re-attach → first frame, held only, -1 if not yet).

`reason`, the first that applies: `pad_system_key` (a system-class key from a pad in the 2 s) / `remote_system_key`
/ `user_leave` / `screen_off` / `input_device` (a device event in the 2 s) / `top_lost` / `focus_lost` / `unknown`.

**Host** (`companion/plugins/games.py` heartbeat handler, `companion/surface_lost_row.py` new): only when the
heartbeat carries `surface_lost`, the module is imported, the value parsed (≤ 1,024 chars, whitelisted keys and
types, anything else dropped) and one recovery-log row `{"event": "surface_lost", ...}` written with the heartbeat's
sequence. No key = nothing imported, nothing written: today byte for byte. The heartbeat log row itself is unchanged
(the key is not in its whitelist).

## 3. Pad system keys

With the flag, in `dispatchKeyEvent` before anything else: a key-down/up of the system class — `KEYCODE_BUTTON_MODE`,
`KEYCODE_GUIDE`, `KEYCODE_MENU`, `KEYCODE_SEARCH`, `KEYCODE_SETTINGS`, `KEYCODE_HOME`, `KEYCODE_ALL_APPS`,
`KEYCODE_ASSIST`, `KEYCODE_VOICE_ASSIST`, `KEYCODE_NOTIFICATION`, `KEYCODE_APP_SWITCH` — **from a device whose
sources include `SOURCE_GAMEPAD` or `SOURCE_JOYSTICK`** is consumed (returns true: neither the sender nor the system
sees it); from any other source (the onn remote) it is passed on as today. Every key is noted (code, class,
consumed or not) in a 2-s ring for the rows; the consumed / passed counts go in the report. The ones the policy
intercepts never arrive (§0) and so cannot be consumed; the row says so by their absence plus `user_leave`.
`KEYCODE_BACK` keeps today's handling (the user's exit).

## 4. Absent = today

`surfaceHold` is a `by lazy` null without the flag; every hook is `surfaceHold?.…` or `if (surfaceHold != null)`,
and the parameter-set callback's today branch is unchanged text under `else if (decoder == null)`. No listener is
registered, no key is added, no report field. Host: the block runs only with the key present; nothing imported.

## 5. Tests

JVM (B15's style: the activity's calls modelled against the real classes; the real `RtpH264Receiver` on loopback,
the real `NativeControllerSender` sending to a loopback socket, a fake host transport counting starts):
- a 3-s loss → one session: no start, the sender's datagrams never stop (a gap < 100 ms across the loss), the
  receiver alive, the row `held` with `away_ms` ≈ 3,000, the stall age growing through the hold and ending at the
  new decoder's first frame;
- a 15-s loss → the expiry runs today's path: the guard's pending set, the next surface's start is a restart
  (`guard_end`), the row `restarted`;
- a pad `BUTTON_MODE` consumed, the remote's passed, both noted; the reason order;
- the flag's parse (absent / empty / `0` / junk = off; `1` = 12,000; a valid number; out of range = off);
- the row's encoding (≤ 1,024, no free text) and the 8-row cap.
Host (`tests/surface_lost/`): the key → one `surface_lost` recovery row with the whitelisted fields; junk / overlong
→ no row; no key → no import, no row (a fresh process); the hook's shape in `games.py`.
Mutations: the hold not taken (surfaceDestroyed falls through) → the 3-s test fails; the consume ignoring the source
→ the remote test fails.
