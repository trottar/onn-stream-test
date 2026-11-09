# To B — two pointers on the TV (the user, C32 / after, ~06:25Z)

- The user (verbatim): "There are two mouses. The one I saw last match was the Linux one, but the touchpads have their
  own different style".
- **The hub's pointer** is drawn into the stream: the capture is `x11grab -window_id …` with ffmpeg's default
  `draw_mouse 1` (`companion/native_stream.py`, the command near line 1482). Fix: `-draw_mouse 0` (and the GameCube
  window's own cursor hidden).
- **The onn's pointer** comes from the PlayStation pads' touchpads (Android shows its pointer for the touchpad's
  pointer source); the APK neither consumes `SOURCE_TOUCHPAD` / mouse motion nor sets a null pointer icon in
  `NativeStreamActivity`. Fix (next APK): swallow the touchpad's motion in the stream view and hide the pointer.
- Not fixed at the TV.
