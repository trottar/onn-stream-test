# Stage 2's answers (B's calls on loopback, no client; whitelisted fields only — the full answers carry the title and paths and stay off the repo)

- **launch** `POST /plugins/games/launch?id=<id>` (`-m 120`, waited) sent 2026-11-16T15:07:55.474Z, answered 2026-11-16T15:07:57.468Z: [200] 1.985017s; ok True, active True, **paused True** (game_session.action `pause`, retroarch_state `PAUSED`), native_stream.active False; `launch_orphaned` 2 → 2.
- **native-stream-start** `POST /plugins/games/native-stream-start`: [503] 0.010937s; `{"ok": false, "error": "audio codec opus is required by this host (PRIVYHUB_AUDIO_CODEC) and the client did not declare it in session/setup"}`
- **native-stream-ready** `POST /plugins/games/native-stream-ready`: [503] 0.007396s; `{"ok": false, "error": "Native stream is not active; gameplay remains paused."}`
- **h7-start?keep=1** (15:08:47.414Z, to read the watcher's own answer with no stream): 400 `{"ok": false, "error": "the stream is not up"}` — refused before any load or keep folder (`h7_minigame.py:219-220`); no `.state8`, no folder.
- **stop** `POST /plugins/games/stop` sent 15:08:53.653Z: [200] 0.679025s; ok True, active False; then status active false, stream false, `h7-result` `no_game`.
