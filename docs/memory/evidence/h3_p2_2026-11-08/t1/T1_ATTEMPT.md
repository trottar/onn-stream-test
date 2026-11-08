# T1, the attempt (2026-11-08 02:12-02:14Z)

The user (verbatim): "Game didn't start, said game stream isn't ready".

**What the logs show** (the PS2 game log, the recovery log, the heartbeat log, the client reports, the audio timing
file; raw copies stay in the gitignored logs):
- 02:12:07.8Z `PS2 launch: pcsx2 players=2 multitap=false adapter=named`; PCSX2's window found on the started PID.
- 02:12:09.4Z `PS2 pause: sigstop` (1.6 s after the launch: the paused handoff; PINE did not answer, so SIGSTOP).
- 02:12:09.7Z the stream's start: `remote_config` lan, `pad_slots` (two Sony pads, slots 0 / 1), 02:12:15.5Z the
  `ps2_session` row (`ps2_mode: true`, `save_states: off`); `ps2_mode` on every heartbeat row.
- The video reached the onn at ~60 fps (rendered frames +~121 per 2-s heartbeat), the picture frozen (PCSX2 stopped).
- **Audio: 0 packets for the whole session** (heartbeat `audio_rx_packets` 0; the audio timing file `packets_sent` 0,
  the capture backend `pulseaudio_managed_sink_monitor` on the PCSX2 PID, nothing captured).
- **No `session_started`, no `PS2 resume`:** the gameplay was never released; the client's report shows
  `fast_ready_releases` 0; the onn showed its stabilization failure ("Game stream isn't ready").
- 02:13:15.6Z the user's Back (`session_end_bye`); a second start 02:13:18Z (the same: `ps2_session`, no release,
  no audio); 02:13:35.6Z Back; 02:13:40.1Z `PS2 exit: sigterm 0.5s` (Stop). No `AppRun` or FUSE helper left.

**The reading:** the launch's paused handoff stops PCSX2 1.6 s after its window appears, before PCSX2 opens its
PulseAudio stream (H3-P1's P0c found that sink-input at ~12 s). The session's audio is found by the PID's sink-input
(exactly one, by `application.process.id`), so there is none to move into the session's sink, the audio never starts,
and the release never comes. A RetroArch session has its audio stream open by the time its window shows, so the
RetroArch path does not meet this. **A B49 defect: the PS2 paused handoff must come after the PID's sink-input exists
(or the audio match must wait for it), and a SIGSTOP freezes a PCSX2 that has not finished starting.** A retry gives
the same result (the second start did).

**The rows:** P7b **NOT MET** (no game picture: the frozen first frame, no release within 90 s); `PS2 launch` line
and `ps2_session` row present. P7c-P7g not measurable (no gameplay). P7h: `PS2 exit: sigterm 0.5s`, nothing left
(met; the next PS1 launch not tried, the user's decision). P7i: the user's line above. **Valid** (the pads on the onn;
no stream restart: the stream never released).
